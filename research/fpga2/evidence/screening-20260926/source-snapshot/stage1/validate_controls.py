"""Pre-training numerical and initialization audit on synthetic activations."""
import argparse
import json
from pathlib import Path
import torch
from .model import Decoder
from .run import configuration, environment


ARMS = ['dense', 'narrow', 'grouped', 'shuffle', 'monarch', 'monarch_dense_match', 'lowrank']


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--out', required=True)
    a = p.parse_args()
    out = Path(a.out)
    if out.exists(): raise FileExistsError(out)
    torch.set_num_threads(4)
    rows = []
    for policy in ['legacy', 'fan_matched']:
        for seed in [42, 43, 44]:
            for arm in ARMS:
                c = configuration(arm); c.init_policy = policy
                model = Decoder(c); model.reset_parameters(seed); model.cuda()
                torch.manual_seed(seed+9000)
                x = torch.randn(4, 256, c.width, device='cuda')
                ffn = model.blocks[0].ffn
                with torch.no_grad():
                    reference = ffn(x)
                with torch.autocast('cuda', dtype=torch.float16):
                    actual = ffn(x)
                    loss = actual.float().square().mean()
                loss.backward()
                if not torch.isfinite(actual).all(): raise FloatingPointError(arm)
                if not all(p.grad is not None and torch.isfinite(p.grad).all() for p in ffn.parameters()):
                    raise FloatingPointError('missing/nonfinite gradient: '+arm)
                err = (actual.float()-reference).square().mean().sqrt()/reference.square().mean().sqrt()
                if err > .02: raise AssertionError('FP16 relative RMS error exceeds 2%: '+arm)
                rows.append({'arm': arm, 'seed': seed, 'init_policy': policy,
                             'ffn_parameters_per_layer': sum(p.numel() for p in ffn.parameters()),
                             'parameters': sum(p.numel() for p in model.parameters()),
                             'output_rms': float(reference.square().mean().sqrt()),
                             'fp16_relative_rms_error': float(err), 'finite_gradients': True})
                del model, ffn, actual, reference, loss, x
    out.write_text(json.dumps({'environment': environment(), 'rows': rows,
                              'scope': 'synthetic unit-variance inputs, first FFN; not quality evidence'}, indent=2)+'\n')
    print(out, flush=True)


if __name__ == '__main__': main()
