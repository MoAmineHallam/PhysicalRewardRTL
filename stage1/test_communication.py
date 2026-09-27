"""Independent dense-matrix references and decoder checks for message placement."""
from dataclasses import asdict
import io
import unittest

import torch
from torch.nn import functional as F

from .communication import COMMUNICATION_KINDS, CommunicationFFN
from .model import Config, Decoder


def config(kind, **overrides):
    values = dict(vocab=43, width=12, heads=3, hidden=24, layers=2, context=32,
                  groups=3, rank=2, ffn_kind=kind, init_policy='fan_matched')
    values.update(overrides)
    return Config(**values)


def dense_reference(layer, x):
    gate, value = layer.up_gate.chunk(2, -1)
    gate = torch.block_diag(*gate.transpose(1, 2).unbind())
    value = torch.block_diag(*value.transpose(1, 2).unbind())
    down = torch.block_diag(*layer.down.transpose(1, 2).unbind())
    read = layer.message_read.reshape(-1, layer.rank).T
    write = layer.message_write.transpose(1, 2).reshape(-1, layer.rank)
    a, v = F.linear(x, gate), F.linear(x, value)
    if layer.placement == 'gate':
        a = a + F.linear(x, write @ read)
    elif layer.placement == 'value':
        v = v + F.linear(x, write @ read)
    hidden = F.silu(a) * v
    out = F.linear(hidden, down)
    return out + F.linear(hidden, write @ read) if layer.placement == 'post' else out


class CommunicationTests(unittest.TestCase):
    def setUp(self):
        torch.set_num_threads(2)
        torch.manual_seed(29)

    def test_dense_equivalence_and_all_parameter_gradients(self):
        for kind in COMMUNICATION_KINDS:
            layer = CommunicationFFN(config(kind)).double()
            # Stronger scales than decoder initialization expose mapping errors.
            for parameter in layer.parameters():
                torch.nn.init.normal_(parameter, std=0.3)
            x = torch.randn(2, 3, 12, dtype=torch.float64, requires_grad=True)
            actual, expected = layer(x), dense_reference(layer, x)
            torch.testing.assert_close(actual, expected, atol=1e-12, rtol=1e-10)
            objective = torch.randn_like(actual)
            ga = torch.autograd.grad((actual * objective).sum(), (x, *layer.parameters()), retain_graph=True)
            ge = torch.autograd.grad((expected * objective).sum(), (x, *layer.parameters()))
            for a, e in zip(ga, ge):
                torch.testing.assert_close(a, e, atol=1e-12, rtol=1e-10)
            # Non-contiguous inputs and arbitrary leading dimensions are supported.
            transposed = x.transpose(0, 1)
            torch.testing.assert_close(layer(transposed), dense_reference(layer, transposed))
            torch.testing.assert_close(layer(x[0, 0]), dense_reference(layer, x[0, 0]))

    def test_exact_budget_and_shared_initialization(self):
        models = [Decoder(config(kind, width=384, heads=6, hidden=1024, groups=4, rank=36,
                                 layers=1)) for kind in COMMUNICATION_KINDS]
        dense = Decoder(config('standard', width=384, heads=6, hidden=300, groups=1, layers=1))
        common = dict(dense.named_parameters())
        for model in models:
            self.assertEqual(sum(p.numel() for p in model.parameters()), sum(p.numel() for p in dense.parameters()))
            self.assertEqual(sum(p.numel() for p in model.blocks[0].ffn.parameters()), 345600)
            for name, parameter in model.named_parameters():
                if '.ffn.' not in name:
                    torch.testing.assert_close(parameter, common[name], atol=0, rtol=0)
            saved = {name: p.clone() for name, p in model.named_parameters()}
            model.reset_parameters(42)
            for name, parameter in model.named_parameters():
                torch.testing.assert_close(parameter, saved[name], atol=0, rtol=0)
        # The same local random draws are scaled according to placement.
        g, v, post = [model.blocks[0].ffn for model in models]
        torch.testing.assert_close(g.up_gate[..., :256] * 2**0.5, post.up_gate[..., :256])
        torch.testing.assert_close(v.up_gate[..., 256:] * 2**0.5, post.up_gate[..., 256:])

    def test_optimizer_step_message_gradients_and_checkpoint(self):
        for kind in COMMUNICATION_KINDS:
            model = Decoder(config(kind))
            ids = torch.randint(43, (2, 9))
            logits, _ = model(ids[:, :-1])
            loss = F.cross_entropy(logits.flatten(0, 1), ids[:, 1:].reshape(-1))
            loss.backward()
            for name, parameter in model.named_parameters():
                self.assertIsNotNone(parameter.grad, name)
                self.assertTrue(torch.isfinite(parameter.grad).all(), name)
                if 'message_' in name:
                    self.assertGreater(parameter.grad.abs().sum().item(), 0, name)
            torch.optim.AdamW(model.parameters(), lr=3e-4).step()
            stream = io.BytesIO()
            torch.save(dict(config=asdict(model.config), model=model.state_dict()), stream)
            stream.seek(0)
            saved = torch.load(stream, weights_only=True)
            restored = Decoder(Config(**saved['config']))
            restored.load_state_dict(saved['model'])
            torch.testing.assert_close(model(ids)[0], restored(ids)[0], atol=0, rtol=0)

    def test_causality_and_both_cache_paths(self):
        for kind in COMMUNICATION_KINDS:
            model = Decoder(config(kind)).eval()
            ids = torch.randint(43, (2, 11))
            with torch.no_grad():
                full, _ = model(ids)
                changed = ids.clone(); changed[:, 6:] = (changed[:, 6:] + 7) % 43
                torch.testing.assert_close(full[:, :6], model(changed)[0][:, :6])
                _, dynamic = model(ids[:, :5], use_cache=True)
                static = model.allocate_cache(2)
                model(ids[:, :5], static, use_cache=True)
                for start, end in [(5, 8), (8, 9), (9, 11)]:
                    out, dynamic = model(ids[:, start:end], dynamic, use_cache=True)
                    cached, _ = model(ids[:, start:end], static, use_cache=True)
                    torch.testing.assert_close(out, full[:, start:end], atol=1e-6, rtol=1e-5)
                    torch.testing.assert_close(cached, out, atol=1e-6, rtol=1e-5)

    def test_invalid_configurations(self):
        for kwargs in [dict(rank=0), dict(rank=13), dict(groups=1), dict(groups=5),
                       dict(shuffle=True), dict(init_policy='legacy')]:
            with self.assertRaises(ValueError):
                config('communication_gate', **kwargs)


if __name__ == '__main__':
    unittest.main()
