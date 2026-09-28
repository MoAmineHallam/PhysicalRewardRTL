from contextlib import redirect_stdout
from dataclasses import asdict
import io
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
import torch
from torch.nn import functional as F

from .experiment import ARMS, configuration
from .model import Config, Decoder
from .prepare_data import digest, text_hash
from .prepare_fineweb import assign_split
from .prior_controls import BlockDenseLinear, deployed_parameters, set_guidance
from .train_screen import BlockSampler, Settings, train_session


class ScreenTests(unittest.TestCase):
    def setUp(self):
        torch.set_num_threads(2); torch.manual_seed(37)

    def test_blockdense_dense_matrix_and_guidance(self):
        layer = BlockDenseLinear(12, 18, 3, 6, guided=True).double()
        for p in layer.parameters(): torch.nn.init.normal_(p, std=.2)
        x = torch.randn(2, 3, 12, dtype=torch.float64, requires_grad=True)
        layer.alpha.fill_(.37)
        actual = layer(x)
        expected = F.linear(x, .63*layer.matrix()+.37*layer.guide)
        torch.testing.assert_close(actual, expected)
        ga = torch.autograd.grad(actual.square().sum(), (x,*layer.parameters()), retain_graph=True)
        ge = torch.autograd.grad(expected.square().sum(), (x,*layer.parameters()))
        for a,b in zip(ga,ge): torch.testing.assert_close(a,b)
        layer.eval()
        torch.testing.assert_close(layer(x), F.linear(x, layer.matrix()))

    def test_groupbert_pattern_and_prior_parameter_matches(self):
        counts = {}
        for arm in ['groupbert_pattern','dense896','blockdense','blockdense_guided','dense232']:
            c = configuration(arm); c.layers=1; c.vocab=43; c.context=32
            model = Decoder(c); f = model.blocks[0].ffn
            counts[arm] = deployed_parameters(model)
            x = torch.randn(2, 3, c.width)
            if arm == 'groupbert_pattern':
                gate, value = f.up_gate(x).chunk(2,-1)
                dense_down = torch.block_diag(*f.down.transpose(1,2).unbind())
                reference = f.mix(F.linear(F.silu(gate)*value, dense_down))
                torch.testing.assert_close(f(x), reference)
            elif arm == 'blockdense_guided':
                f.train(); initial = f(x); f.eval()
                torch.testing.assert_close(initial, f(x), rtol=1e-4, atol=1e-6)
                set_guidance(model, 5, 10)
                self.assertEqual(float(f.up_gate.alpha), 0.)
        self.assertEqual(counts['groupbert_pattern'],counts['dense896'])
        self.assertEqual(counts['blockdense'],counts['dense232'])
        self.assertEqual(counts['blockdense_guided'],counts['dense232'])

    def test_sampler_no_replacement_and_resume_across_epoch(self):
        sampler = BlockSampler(57,8,91)
        a = sampler.next(4); state = sampler.state_dict(); b = sampler.next(5)
        restored = BlockSampler(57,8,91); restored.load_state_dict(state)
        np.testing.assert_array_equal(restored.next(5),b)
        self.assertEqual(restored.chain,sampler.chain)
        self.assertEqual(sorted(np.concatenate([a,b[:3]]).tolist()),list(range(0,56,8)))
        self.assertEqual(sampler.epoch,1)
        # Whitespace-equivalent documents cannot be assigned different splits.
        self.assertEqual(assign_split(text_hash('hello  world')),assign_split(text_hash('hello\nworld')))

    def test_exact_training_resume_and_deployment_export(self):
        with tempfile.TemporaryDirectory() as directory, redirect_stdout(io.StringIO()):
            root=Path(directory);data=root/'data';data.mkdir()
            manifest={'vocab':43}
            for split in ['train','validation']:
                np.save(data/f'{split}.npy',np.random.default_rng(7).integers(0,43,513,dtype=np.uint16))
                manifest[split]={'token_file_sha256':digest(data/f'{split}.npy')}
            (data/'manifest.json').write_text(json.dumps(manifest))
            s=Settings(steps=4,seq=8,batch=2,accum=2,warmup=2,checkpoint_every=2,
                       eval_every=2,eval_tokens=16,final_eval_tokens=32)
            for kind in ['communication_gate','blockdense_guided']:
                c=Config(vocab=43,width=12,hidden=24,heads=3,layers=1,context=32,
                         groups=3 if kind=='communication_gate' else 1,factor_blocks=3,
                         rank=6,ffn_kind=kind,init_policy='fan_matched')
                full=root/(kind+'-full');resumed=root/(kind+'-resumed')
                a=train_session(c,s,data,full,device='cpu')
                train_session(c,s,data,resumed,device='cpu',stop_after=2)
                b=train_session(c,s,data,resumed,device='cpu',resume=True)
                self.assertEqual(a['sample_chain'],b['sample_chain'])
                self.assertEqual(a['final'],b['final'])
                sa=torch.load(full/'last.pt',weights_only=True)
                sb=torch.load(resumed/'last.pt',weights_only=True)
                for key in sa['model']:
                    torch.testing.assert_close(sa['model'][key],sb['model'][key],atol=0,rtol=0)
                for key in sa['optimizer']['state']:
                    for name,value in sa['optimizer']['state'][key].items():
                        torch.testing.assert_close(value,sb['optimizer']['state'][key][name],atol=0,rtol=0)
                export=torch.load(resumed/'final.pt',weights_only=True)
                deployed=Decoder(Config(**export['config']));deployed.load_state_dict(export['model'])
                self.assertFalse(any(name.endswith('.guide') for name,_ in deployed.named_parameters()))
                changed=Settings(**{**asdict(s),'lr':1e-3})
                with self.assertRaises(ValueError):
                    train_session(c,changed,data,resumed,device='cpu',resume=True)


if __name__ == '__main__': unittest.main()
