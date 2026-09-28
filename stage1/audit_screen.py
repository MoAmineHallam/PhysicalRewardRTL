"""Bounded GPU initialization/precision audit for the new experiment arms."""
import argparse
import json
from pathlib import Path
import torch
from .experiment import ARMS, configuration
from .model import Decoder
from .prior_controls import deployed_parameters
from .run import environment


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args()
    out=Path(a.out)
    if out.exists():raise FileExistsError(out)
    torch.set_num_threads(4);rows=[]
    for seed in [42,43]:
        for arm in ARMS:
            c=configuration(arm);model=Decoder(c);model.reset_parameters(seed);model.cuda().eval()
            torch.manual_seed(seed+9000);x=torch.randn(4,128,c.width,device='cuda')
            ffn=model.blocks[0].ffn
            with torch.no_grad():reference=ffn(x)
            with torch.autocast('cuda',dtype=torch.float16):
                actual=ffn(x);loss=actual.float().square().mean()*1024
            loss.backward()
            error=float((actual.float()-reference).square().mean().sqrt()/reference.square().mean().sqrt())
            gradients={name:float(p.grad.abs().sum()) for name,p in ffn.named_parameters()
                       if not name.endswith('.guide') and name!='guide' and p.grad is not None}
            if error>.02 or not torch.isfinite(actual).all():raise FloatingPointError(arm)
            for name,p in ffn.named_parameters():
                if name.endswith('.guide') or name=='guide':continue
                if p.grad is None or not torch.isfinite(p.grad).all():raise FloatingPointError(name)
                if 'message_' in name and gradients[name]==0:raise FloatingPointError('zero message gradient')
            row=dict(arm=arm,seed=seed,output_rms=float(reference.square().mean().sqrt()),
                     fp16_relative_rms_error=error,gradients_finite=True,
                     parameters_training=sum(p.numel() for p in model.parameters()),
                     parameters_deployed=deployed_parameters(model),gradient_l1=gradients)
            rows.append(row);print(json.dumps({k:v for k,v in row.items() if k!='gradient_l1'}),flush=True)
            del model,ffn,x,actual,reference,loss
    out.write_text(json.dumps(dict(environment=environment(),rows=rows,
        scope='Synthetic first-FFN precision and initialization audit; no language-quality measurement.'),indent=2)+'\n')


if __name__=='__main__':main()
