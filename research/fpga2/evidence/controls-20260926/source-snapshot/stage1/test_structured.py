import unittest
import torch
from torch.nn import functional as F
from .structured import MonarchLinear, LowRankLinear
from .model import Decoder
from .run import configuration


class StructuredTests(unittest.TestCase):
    def setUp(self):
        torch.set_num_threads(2); torch.manual_seed(37)

    def test_monarch_rectangular_padding_dense_equivalence_and_gradients(self):
        for inputs, outputs in [(16, 24), (24, 16), (13, 10)]:
            layer = MonarchLinear(inputs, outputs, 4).double()
            for p in layer.parameters(): torch.nn.init.normal_(p, std=0.1)
            x = torch.randn(2, 3, inputs, dtype=torch.float64, requires_grad=True)
            g, q, p = layer.first.shape; _, s, r = layer.second.shape
            w1 = torch.block_diag(*layer.first.unbind())
            w2 = torch.block_diag(*layer.second.unbind())
            perm = torch.arange(g*q).reshape(r, g).T.reshape(-1)
            out_perm = torch.arange(g*s).reshape(g, s).T.reshape(-1)
            expected = F.linear(F.linear(F.pad(x, (0, g*p-inputs)), w1)[..., perm], w2)
            expected = expected[..., out_perm][..., :outputs]
            actual = layer(x)
            torch.testing.assert_close(actual, expected)
            target = torch.randn_like(actual)
            ga = torch.autograd.grad((actual*target).sum(), (x,*layer.parameters()), retain_graph=True)
            ge = torch.autograd.grad((expected*target).sum(), (x,*layer.parameters()))
            for a,b in zip(ga,ge): torch.testing.assert_close(a,b)

    def test_lowrank_dense_equivalence(self):
        layer = LowRankLinear(16, 24, 4).double()
        for p in layer.parameters(): torch.nn.init.normal_(p)
        x = torch.randn(2, 3, 16, dtype=torch.float64)
        torch.testing.assert_close(layer(x), F.linear(x, layer.second@layer.first))

    def test_fan_matched_keeps_common_tensors_and_monarch_budget(self):
        models = {}
        for arm in ['dense','narrow','grouped','monarch','monarch_dense_match','lowrank']:
            c = configuration(arm); c.layers = 1; c.vocab = 43; c.context = 32
            c.init_policy = 'fan_matched'
            models[arm] = Decoder(c)
        common = dict(models['dense'].named_parameters())
        for arm, m in models.items():
            for name, p in m.named_parameters():
                if '.ffn.' not in name:
                    torch.testing.assert_close(p, common[name], rtol=0, atol=0)
            with torch.no_grad():
                logits,_ = m(torch.randint(43,(2,8)))
                self.assertTrue(torch.isfinite(logits).all())
        count = lambda name: sum(p.numel() for p in models[name].blocks[0].ffn.parameters())
        self.assertEqual(count('monarch'),count('monarch_dense_match'))
        self.assertEqual(count('grouped'),count('narrow'))


if __name__ == '__main__':
    unittest.main()
