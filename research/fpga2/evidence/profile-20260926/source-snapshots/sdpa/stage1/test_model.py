"""Independent algebra, gradient, and causal-cache checks for the pilot."""
import unittest
import torch
from torch.nn import functional as F
from .model import Config, Decoder, FFN


class ModelTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(19)
        torch.set_num_threads(2)

    def test_grouped_dense_block_diagonal_equivalence_and_gradient(self):
        c = Config(vocab=43, width=16, heads=4, hidden=24, layers=2, groups=4)
        f = FFN(c).double()
        for p in f.parameters():
            torch.nn.init.normal_(p, std=0.1)
        x = torch.randn(2, 3, 16, dtype=torch.float64, requires_grad=True)
        parts = []
        for i in range(4):
            gate, up = (x[..., i*4:(i+1)*4] @ f.up_gate[i]).chunk(2, -1)
            parts.append((F.silu(gate) * up) @ f.down[i])
        expected = torch.cat(parts, dim=-1)
        actual = f(x)
        torch.testing.assert_close(actual, expected)
        target = torch.randn_like(actual)
        a = torch.autograd.grad((actual * target).sum(), (x, *f.parameters()), retain_graph=True)
        b = torch.autograd.grad((expected * target).sum(), (x, *f.parameters()))
        for g1, g2 in zip(a, b):
            torch.testing.assert_close(g1, g2)

    def test_causality_and_single_and_multi_token_cache(self):
        for groups, shuffle in [(1, False), (4, False), (4, True)]:
            model = Decoder(Config(vocab=43, width=16, heads=4, hidden=24,
                                   layers=2, groups=groups, shuffle=shuffle, context=32)).eval()
            ids = torch.randint(0, 43, (2, 11))
            with torch.no_grad():
                full, _ = model(ids)
                changed = ids.clone(); changed[:, 6:] = (changed[:, 6:] + 3) % 43
                other, _ = model(changed)
                torch.testing.assert_close(full[:, :6], other[:, :6], atol=1e-6, rtol=1e-5)
                _, cache = model(ids[:, :5], use_cache=True)
                multi, _ = model(ids[:, 5:], cache, use_cache=True)
                torch.testing.assert_close(multi, full[:, 5:], atol=1e-6, rtol=1e-5)
                for t in range(5, 11):
                    single, cache = model(ids[:, t:t+1], cache, use_cache=True)
                    torch.testing.assert_close(single, full[:, t:t+1], atol=1e-6, rtol=1e-5)

    def test_shared_initialization_and_weight_count(self):
        a = Decoder(Config(width=16, hidden=24, layers=2, heads=4, vocab=43))
        b = Decoder(Config(width=16, hidden=24, layers=2, heads=4, vocab=43, groups=4))
        for name, p in a.named_parameters():
            if '.ffn.' not in name:
                torch.testing.assert_close(p, dict(b.named_parameters())[name], rtol=0, atol=0)
        self.assertEqual(sum(p.numel() for p in a.blocks[0].ffn.parameters()), 3*16*24)
        self.assertEqual(sum(p.numel() for p in b.blocks[0].ffn.parameters()), 3*16*24//4)

    def test_context_limit(self):
        m = Decoder(Config(width=8, heads=2, hidden=16, layers=1, vocab=43, context=4))
        with self.assertRaises(ValueError):
            m(torch.zeros((1, 5), dtype=torch.long))

    def test_static_cache_matches_full_dynamic_and_reset(self):
        for groups in [1, 4]:
            m = Decoder(Config(width=16, heads=4, hidden=24, layers=2, vocab=43,
                               groups=groups, context=32)).eval()
            x = torch.randint(43, (2, 13))
            cache = m.allocate_cache(2, 20)
            pointers = [(c.key.data_ptr(), c.value.data_ptr()) for c in cache]
            with torch.no_grad():
                full, _ = m(x)
                first, returned = m(x[:, :5], cache, use_cache=True)
                torch.testing.assert_close(first, full[:, :5], atol=1e-6, rtol=1e-5)
                self.assertTrue(all(a is b for a, b in zip(cache, returned)))
                chunk, _ = m(x[:, 5:9], cache, use_cache=True)
                torch.testing.assert_close(chunk, full[:, 5:9], atol=1e-6, rtol=1e-5)
                for i in range(9, 13):
                    one, _ = m(x[:, i:i+1], cache, use_cache=True)
                    torch.testing.assert_close(one, full[:, i:i+1], atol=1e-6, rtol=1e-5)
                self.assertEqual(pointers, [(c.key.data_ptr(), c.value.data_ptr()) for c in cache])
                for c in cache: c.truncate(0)
                fresh = torch.randint(43, (2, 7))
                ref, _ = m(fresh)
                reset, _ = m(fresh, cache, use_cache=True)
                torch.testing.assert_close(reset, ref, atol=1e-6, rtol=1e-5)

    def test_static_cache_invalid_state_and_overflow(self):
        m = Decoder(Config(width=16, heads=4, hidden=24, layers=2, vocab=43, context=16))
        cache = m.allocate_cache(1, 4)
        with self.assertRaises(RuntimeError):
            m(torch.zeros((1, 2), dtype=torch.long), cache, use_cache=True)
        with torch.no_grad():
            m(torch.zeros((1, 3), dtype=torch.long), cache, use_cache=True)
            with self.assertRaises(ValueError):
                m(torch.zeros((1, 2), dtype=torch.long), cache, use_cache=True)
            self.assertEqual([p.length for p in cache], [3, 3])
            with self.assertRaises(ValueError): cache[0].truncate(4)
            cache[0].truncate(2)
            with self.assertRaises(ValueError):
                m(torch.zeros((1, 1), dtype=torch.long), cache, use_cache=True)


if __name__ == '__main__':
    unittest.main()
