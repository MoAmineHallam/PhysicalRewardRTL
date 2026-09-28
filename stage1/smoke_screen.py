"""Bounded on-device smoke jobs, separate from the 100M-token campaign."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import torch
from .experiment import ARMS, configuration
from .train_screen import Settings, train_session


def main():
    p=argparse.ArgumentParser();p.add_argument('--data',required=True);p.add_argument('--out',required=True)
    p.add_argument('--worker',type=int,choices=range(4),required=True);a=p.parse_args()
    out=Path(a.out);out.mkdir(parents=True,exist_ok=False);torch.set_num_threads(4)
    settings=Settings(steps=16,warmup=4,checkpoint_every=8,eval_every=16,
                      eval_tokens=4096,final_eval_tokens=8192)
    rows=[]
    for arm in ARMS[a.worker::4]:
        r=train_session(configuration(arm),settings,a.data,out/arm)
        rows.append(dict(arm=arm,status=r['status'],tokens_per_second=r['training_tokens']/r['train_seconds']))
    if a.worker==0:
        # A full-sized guided decoder exercises optimizer, scheduler, buffers,
        # scaler and sampling state through a real CUDA interruption.
        arm='blockdense_guided'
        s=Settings(steps=8,warmup=2,checkpoint_every=4,eval_every=8,
                   eval_tokens=4096,final_eval_tokens=8192)
        full=out/'resume-full';split=out/'resume-split'
        ra=train_session(configuration(arm),s,a.data,full)
        train_session(configuration(arm),s,a.data,split,stop_after=4)
        rb=train_session(configuration(arm),s,a.data,split,resume=True)
        x=torch.load(full/'last.pt',map_location='cpu',weights_only=True)
        y=torch.load(split/'last.pt',map_location='cpu',weights_only=True)
        max_error=max(float((v-y['model'][k]).abs().max()) for k,v in x['model'].items())
        opt_error=max(float((v-y['optimizer']['state'][k][n]).abs().max())
                      for k,state in x['optimizer']['state'].items() for n,v in state.items())
        if max_error!=0 or opt_error!=0 or ra['sample_chain']!=rb['sample_chain']:
            raise AssertionError(f'CUDA resume differs: model={max_error}, optimizer={opt_error}')
        rows.append(dict(check='cuda_exact_resume',model_max_error=max_error,optimizer_max_error=opt_error,
                         sample_chain=ra['sample_chain']))
    (out/'summary.json').write_text(json.dumps(dict(status='complete',worker=a.worker,settings=asdict(settings),rows=rows),indent=2)+'\n')


if __name__=='__main__':main()
