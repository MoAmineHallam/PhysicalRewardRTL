"""CPU checks for the Gate-0 student tools.

Run: python -m unittest student.test_student -v
The end-to-end evaluator test additionally needs FPGA_ROOT pointing at the
previous project's checkout (it imports the frozen eval_sealed module) and is
skipped otherwise.
"""

from __future__ import annotations

import importlib
import json
import os
import sys
import tempfile
import unittest
from types import SimpleNamespace

import torch

from student.compress import (CompressionError, DEFAULT_TARGETS, calibration_from_rows,
                              gptq_quantize_model_, gptq_quantize_weight,
                              keep_ids_from_texts, quantize_linear_weights_,
                              quantize_weight, restrict_output_vocabulary_)
from student.footprint import decode_bytes_per_token, decoder_weight_count

QWEN05_CONFIG = {  # Qwen2.5-Coder-0.5B shapes
    "hidden_size": 896, "num_attention_heads": 14, "num_key_value_heads": 2,
    "intermediate_size": 4864, "num_hidden_layers": 24, "vocab_size": 151936,
}


def tiny_qwen(seed: int = 0, vocab: int = 300):
    from transformers import Qwen2Config, Qwen2ForCausalLM
    torch.manual_seed(seed)
    cfg = Qwen2Config(vocab_size=vocab, hidden_size=128, intermediate_size=256,
                      num_hidden_layers=2, num_attention_heads=4,
                      num_key_value_heads=2, max_position_embeddings=128,
                      tie_word_embeddings=True)
    return Qwen2ForCausalLM(cfg).eval()


def tiny_tokenizer():
    from tokenizers import Tokenizer, models, pre_tokenizers, decoders, trainers
    from transformers import PreTrainedTokenizerFast
    tok = Tokenizer(models.BPE())
    tok.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    tok.decoder = decoders.ByteLevel()
    trainer = trainers.BpeTrainer(vocab_size=300, special_tokens=["<eos>"],
                                  initial_alphabet=pre_tokenizers.ByteLevel.alphabet())
    tok.train_from_iterator(["module fir(input clk); assign y = a + b; endmodule"] * 20,
                            trainer)
    return PreTrainedTokenizerFast(tokenizer_object=tok, eos_token="<eos>",
                                   pad_token="<eos>")


class QuantizeWeightTest(unittest.TestCase):
    def test_values_lie_on_group_grid(self):
        torch.manual_seed(1)
        w = torch.randn(8, 256)
        q = quantize_weight(w, bits=4, group_size=128)
        for row in range(8):
            for g in range(2):
                block = w[row, g * 128:(g + 1) * 128]
                scale = block.abs().max() / 7
                codes = q[row, g * 128:(g + 1) * 128] / scale
                self.assertTrue(torch.allclose(codes, codes.round(), atol=1e-4))
                self.assertLessEqual(float(codes.abs().max()), 7 + 1e-4)
                # the largest magnitude in each group is exactly representable
                self.assertAlmostEqual(float(q[row, g * 128:(g + 1) * 128].abs().max()),
                                       float(block.abs().max()), places=5)

    def test_error_shrinks_with_bits_and_is_idempotent(self):
        torch.manual_seed(2)
        w = torch.randn(16, 512)
        errors = [float((quantize_weight(w, b, 128) - w).norm()) for b in (3, 4, 8)]
        self.assertGreater(errors[0], errors[1])
        self.assertGreater(errors[1], errors[2])
        once = quantize_weight(w, 4, 128)
        self.assertTrue(torch.allclose(quantize_weight(once, 4, 128), once, atol=1e-6))

    def test_zero_group_and_dtype_preserved(self):
        w = torch.zeros(2, 128, dtype=torch.float16)
        q = quantize_weight(w, 4, 128)
        self.assertEqual(q.dtype, torch.float16)
        self.assertTrue(torch.equal(q, w))

    def test_rejects_unfaithful_requests(self):
        with self.assertRaises(CompressionError):
            quantize_weight(torch.randn(4, 100), 4, 128)
        with self.assertRaises(CompressionError):
            quantize_weight(torch.randn(4, 128), 1, 128)
        with self.assertRaises(CompressionError):
            quantize_weight(torch.randn(128), 4, 128)


class ModelTransformTest(unittest.TestCase):
    def test_quantizes_only_decoder_projections(self):
        model = tiny_qwen()
        embed = model.get_input_embeddings().weight.detach().clone()
        stats = quantize_linear_weights_(model, bits=4, group_size=64)
        self.assertEqual(stats["n_layers"], 2 * len(DEFAULT_TARGETS))
        self.assertGreater(stats["relative_rms_error"], 0)
        self.assertTrue(torch.equal(model.get_input_embeddings().weight, embed))
        self.assertTrue(torch.equal(model.get_output_embeddings().weight, embed))
        w = model.model.layers[0].mlp.down_proj.weight
        self.assertTrue(torch.allclose(quantize_weight(w, 4, 64), w, atol=1e-6))

    def test_missing_targets_raise(self):
        with self.assertRaises(CompressionError):
            quantize_linear_weights_(torch.nn.Sequential(torch.nn.Linear(128, 128)), 4, 64)

    def test_vocabulary_mask_keeps_kept_logits_exact(self):
        model = tiny_qwen()
        ids = torch.tensor([[1, 5, 9, 12]])
        with torch.no_grad():
            before = model(ids).logits
        keep = [0, 3, 5, 7, 11, 200]
        handle = restrict_output_vocabulary_(model, keep)
        with torch.no_grad():
            after = model(ids).logits
            generated = model.generate(ids, max_new_tokens=12, do_sample=True,
                                       pad_token_id=0)
        self.assertTrue(torch.equal(after[..., keep], before[..., keep]))
        dropped = [i for i in range(after.shape[-1]) if i not in keep]
        self.assertTrue(torch.isneginf(after[..., dropped]).all())
        self.assertTrue(set(generated[0, ids.shape[1]:].tolist()) <= set(keep))
        handle.remove()
        with torch.no_grad():
            self.assertTrue(torch.equal(model(ids).logits, before))

    def test_vocabulary_mask_rejects_bad_ids(self):
        with self.assertRaises(CompressionError):
            restrict_output_vocabulary_(tiny_qwen(), [1, 10_000])
        with self.assertRaises(CompressionError):
            restrict_output_vocabulary_(tiny_qwen(), [])

    def test_keep_ids_cover_corpus_and_ascii(self):
        tok = tiny_tokenizer()
        keep = set(keep_ids_from_texts(tok, ["assign y = a + b;"]))
        corpus_ids = set(tok("assign y = a + b;", add_special_tokens=False)["input_ids"])
        self.assertTrue(corpus_ids <= keep)
        self.assertIn(tok.eos_token_id, keep)
        for char in "Zq7_[":
            self.assertTrue(set(tok(char, add_special_tokens=False)["input_ids"]) <= keep)
        no_fallback = set(keep_ids_from_texts(tok, ["assign"], ascii_fallback=False))
        self.assertLess(len(no_fallback), len(keep))


class GPTQTest(unittest.TestCase):
    def test_identity_hessian_reduces_to_rtn(self):
        torch.manual_seed(3)
        w = torch.randn(16, 256)
        q, _scales = gptq_quantize_weight(w, torch.eye(256), bits=4, group_size=128,
                                          percdamp=0.0)
        self.assertTrue(torch.allclose(q, quantize_weight(w, 4, 128), atol=1e-6))

    def test_beats_rtn_on_correlated_inputs_and_stays_on_grid(self):
        torch.manual_seed(4)
        mix = torch.randn(256, 256) / 16 + torch.eye(256)
        x = torch.randn(2048, 256) @ mix          # correlated activations
        w = torch.randn(32, 256)
        q, scales = gptq_quantize_weight(w, x.T @ x, bits=3, group_size=128)
        rtn = quantize_weight(w, 3, 128)
        gptq_err = float((x @ (w - q).T).pow(2).sum())
        rtn_err = float((x @ (w - rtn).T).pow(2).sum())
        self.assertLess(gptq_err, rtn_err)
        for g in range(2):
            codes = q[:, g * 128:(g + 1) * 128] / scales[:, g:g + 1]
            self.assertTrue(torch.allclose(codes, codes.round(), atol=1e-4))
            self.assertLessEqual(float(codes.abs().max()), 3 + 1e-4)

    def test_first_attempt_unchanged_when_factorization_succeeds(self):
        torch.manual_seed(6)
        x = torch.randn(512, 128)
        info = {}
        q, _ = gptq_quantize_weight(torch.randn(8, 128), x.T @ x, 4, 128, info=info)
        self.assertEqual(info, {"damping": 0.01, "precision": "float32"})

    def test_falls_back_to_float64_and_more_damping(self):
        from unittest import mock
        real = torch.linalg.cholesky
        calls = {"n": 0}

        def flaky(a, *args, **kwargs):
            # fail every float32 attempt and the first float64 attempt
            if a.dtype == torch.float32 or calls["n"] == 0:
                if a.dtype == torch.float64:
                    calls["n"] += 1
                raise torch.linalg.LinAlgError("not positive-definite")
            return real(a, *args, **kwargs)

        torch.manual_seed(7)
        x = torch.randn(512, 128)
        w = torch.randn(8, 128)
        info = {}
        with mock.patch("torch.linalg.cholesky", side_effect=flaky):
            q, scales = gptq_quantize_weight(w, x.T @ x, 4, 128, info=info)
        self.assertEqual(info, {"damping": 0.03, "precision": "float64"})
        codes = q / scales[:, :1]
        self.assertTrue(torch.allclose(codes, codes.round(), atol=1e-4))

    def test_rejects_bad_shapes(self):
        with self.assertRaises(CompressionError):
            gptq_quantize_weight(torch.randn(4, 128), torch.eye(64), 4, 128)
        with self.assertRaises(CompressionError):
            gptq_quantize_weight(torch.randn(4, 100), torch.eye(100), 4, 128)

    def test_model_pass_quantizes_every_target_on_a_grid(self):
        model = tiny_qwen()
        embed = model.get_input_embeddings().weight.detach().clone()
        torch.manual_seed(5)
        calibration = [torch.randint(0, 300, (40,)) for _ in range(6)]
        stats = gptq_quantize_model_(model, calibration, bits=4, group_size=64)
        self.assertEqual(stats["n_layers"], 2 * len(DEFAULT_TARGETS))
        self.assertEqual(stats["n_calibration_tokens"], 240)
        self.assertTrue(torch.equal(model.get_input_embeddings().weight, embed))
        for layer in model.model.layers:
            for name in DEFAULT_TARGETS:
                module = dict(layer.named_modules())[
                    ("self_attn." if name.endswith(("q_proj", "k_proj", "v_proj", "o_proj"))
                     else "mlp.") + name]
                groups = module.weight.reshape(module.weight.shape[0], -1, 64)
                for row in groups[:4]:
                    for group in row:
                        self.assertLessEqual(len(torch.unique(group)), 15)
        with torch.no_grad():
            self.assertTrue(torch.isfinite(model(torch.tensor([[1, 2, 3]])).logits).all())

    def test_calibration_rows_are_seeded_and_leak_checked(self):
        tok = tiny_tokenizer()
        rows = [{"design": f"d{i}", "prompt": f"write module {i}",
                 "completion": "module m; endmodule"} for i in range(10)]
        a = calibration_from_rows(tok, rows, n=4, max_len=8, seed=1)
        b = calibration_from_rows(tok, rows, n=4, max_len=8, seed=1)
        self.assertEqual([t.tolist() for t in a], [t.tolist() for t in b])
        self.assertTrue(all(len(t) <= 8 for t in a))
        with self.assertRaises(CompressionError):
            calibration_from_rows(tok, rows, n=4, max_len=8, seed=1, exclude_designs=["d3"])
        with self.assertRaises(CompressionError):
            calibration_from_rows(tok, rows, n=20, max_len=8, seed=1)


class FootprintTest(unittest.TestCase):
    def test_qwen05_counts(self):
        self.assertEqual(decoder_weight_count(QWEN05_CONFIG), 357_826_560)
        fp16 = decode_bytes_per_token(QWEN05_CONFIG)
        self.assertEqual(fp16["output_head"], 151936 * 896 * 2)
        w4 = decode_bytes_per_token(QWEN05_CONFIG, weight_bits=4, head_rows=4096)
        self.assertAlmostEqual(w4["decoder_weights"], 357_826_560 * (4 + 16 / 128) / 8)
        self.assertEqual(w4["output_head"], 4096 * 896 * 2)
        kv = decode_bytes_per_token(QWEN05_CONFIG, context=1024)["kv_cache"]
        self.assertEqual(kv, 1024 * 24 * 2 * 2 * 64 * 2)


@unittest.skipUnless(os.environ.get("FPGA_ROOT"), "FPGA_ROOT not set")
class EvaluatorTest(unittest.TestCase):
    def test_compressed_run_matches_frozen_schema(self):
        from student import eval_compressed
        sys.path.insert(0, os.environ["FPGA_ROOT"])
        sealed = importlib.import_module("eval_sealed")
        good = "module d1(input clk, output y); assign y = 1'b1; endmodule"
        bad = "module d1(input clk, output y); assign y = 1'b0; endmodule"

        def sample_group(model, tok, prompt, n, temp, max_tokens, device, batch):
            texts = [good, good, bad, "no verilog here"][:n]
            return None, [(None, t) for t in texts]

        def score(rtl, design, n, seed):
            return {"compiled": True, "correct": "1'b1" in rtl}

        deps = SimpleNamespace(sealed=sealed, oracle_score=score,
                               extract=lambda text, _d: text if "module" in text else None,
                               sample_group=sample_group)
        with tempfile.TemporaryDirectory() as tmp:
            base = os.path.join(tmp, "base")
            tiny_qwen().save_pretrained(base)
            tiny_tokenizer().save_pretrained(base)
            split = os.path.join(tmp, "split.json")
            with open(split, "w") as handle:
                json.dump({"schema": "sealed_split/1", "n_designs": 1, "designs": [{
                    "design": "d1", "family": "fir", "regime": "interp",
                    "prompt": "p", "prompt_sha256": sealed.sha256_text("p"),
                    "max_tokens": 16}]}, handle)
            keep = os.path.join(tmp, "keep.json")
            with open(keep, "w") as handle:
                json.dump({"schema": "keep_vocab/1", "keep_ids": list(range(50)),
                           "source": "test"}, handle)
            out = os.path.join(tmp, "out")
            args = eval_compressed.parser().parse_args([
                "--fpga-root", os.environ["FPGA_ROOT"], "--base", base,
                "--split", split, "--policy", "w4", "--generation-seed", "7",
                "--n", "4", "--out-dir", out, "--bits", "4", "--group-size", "64",
                "--keep-vocab", keep, "--allow-cpu"])
            eval_compressed.run(args, deps)
            summary = json.load(open(os.path.join(out, "holdout_summary.json")))["w4"]["d1"]
            self.assertEqual((summary["n"], summary["n_correct"],
                              summary["n_extraction_failed"]), (4, 2, 1))
            manifest = json.load(open(os.path.join(out, "fmax_manifest.json")))
            self.assertEqual([rec["count"] for rec in manifest.values()], [2])
            config = json.load(open(os.path.join(out, "generation_config.json")))
            self.assertEqual(config["compression"]["quantization"]["bits"], 4)
            self.assertEqual(config["compression"]["output_vocabulary"]["kept_rows"], 50)
            self.assertTrue(os.path.isfile(os.path.join(out, "w4__d1__g0.sv")))
            with self.assertRaises(sealed.EvaluationError):
                eval_compressed.run(args, deps)  # never writes into a used directory

            corpus = os.path.join(tmp, "corpus.jsonl")
            with open(corpus, "w") as handle:
                for i in range(8):
                    handle.write(json.dumps({"design": f"t{i}", "prompt": f"spec {i}",
                                             "completion": good}) + "\n")
            gptq_args = eval_compressed.parser().parse_args([
                "--fpga-root", os.environ["FPGA_ROOT"], "--base", base,
                "--split", split, "--policy", "g4", "--generation-seed", "7",
                "--n", "4", "--out-dir", os.path.join(tmp, "out_gptq"), "--bits", "4",
                "--group-size", "64", "--method", "gptq", "--calib", corpus,
                "--calib-n", "8", "--calib-len", "32", "--allow-cpu"])
            eval_compressed.run(gptq_args, deps)
            config = json.load(open(os.path.join(tmp, "out_gptq", "generation_config.json")))
            self.assertEqual(config["compression"]["quantization"]["method"], "gptq")
            self.assertEqual(config["compression"]["quantization"]["n_calibration_sequences"], 8)


if __name__ == "__main__":
    unittest.main()
