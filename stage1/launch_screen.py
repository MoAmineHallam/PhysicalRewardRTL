"""Launch two bounded workers only after matching-source GPU prerequisites pass."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from .train_screen import source_hashes


def main():
    p=argparse.ArgumentParser();p.add_argument('--label',choices=['v100a','v100b'],required=True)
    p.add_argument('--revision',required=True);a=p.parse_args()
    if not re.fullmatch('[0-9a-f]{40}',a.revision):raise ValueError('full source commit required')
    root=Path.cwd();expected=source_hashes()
    for host in ['v100a','v100b']:
        audit=json.loads((root/f'{host}-audit.json').read_text())
        if len(audit['rows'])!=24 or any(not r['gradients_finite'] or r['fp16_relative_rms_error']>.02 for r in audit['rows']):
            raise RuntimeError('GPU precision prerequisite failed')
        for name in ['model.py','communication.py','prior_controls.py','experiment.py','structured.py']:
            if audit['environment']['sources'][name]!=expected[name]:raise RuntimeError('operator changed after precision audit')
    for worker in range(4):
        directory=root/f'smoke-deterministic-{worker}'
        summary=json.loads((directory/'summary.json').read_text())
        if summary['status']!='complete':raise RuntimeError('smoke incomplete')
        for row in summary['rows']:
            if 'arm' in row:
                result=json.loads((directory/row['arm']/'result.json').read_text())
                if result['status']!='complete' or result['source_hashes']!=expected:
                    raise RuntimeError('smoke source/result mismatch')
            elif row.get('check')=='cuda_exact_resume':
                if row['model_max_error']!=0 or row['optimizer_max_error']!=0:raise RuntimeError('resume failed')
        if worker==0 and not any(row.get('check')=='cuda_exact_resume' for row in summary['rows']):
            raise RuntimeError('missing exact GPU resume test')
    ids=[0,1] if a.label=='v100a' else [2,3]
    used=subprocess.check_output(['nvidia-smi','--query-gpu=index,memory.used','--format=csv,noheader,nounits'],text=True)
    memory=dict(tuple(map(int,line.split(','))) for line in used.strip().splitlines())
    for gpu,worker in enumerate(ids):
        if memory.get(gpu,99999)>128:raise RuntimeError(f'GPU {gpu} is not idle')
        if (root/f'campaign-{worker}').exists() or (root/f'campaign-{worker}.log').exists():
            raise FileExistsError('campaign worker output already exists')
    receipts=[]
    for gpu,worker in enumerate(ids):
        env=os.environ.copy();env.update(CUDA_VISIBLE_DEVICES=str(gpu),OMP_NUM_THREADS='4',
                                         PYTHONUNBUFFERED='1',CUBLAS_WORKSPACE_CONFIG=':4096:8')
        cmd=[sys.executable,'-u','-m','stage1.screen_worker','--worker',str(worker),
             '--data',str(root/'data'),'--out',str(root/f'campaign-{worker}')]
        with (root/f'campaign-{worker}.log').open('x') as log:
            proc=subprocess.Popen(cmd,cwd=root,env=env,stdin=subprocess.DEVNULL,
                                  stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        receipt=dict(label=a.label,gpu=gpu,worker=worker,pid=proc.pid,revision=a.revision,
                     utc=datetime.now(timezone.utc).isoformat(),sources=expected,command=cmd)
        (root/f'campaign-{worker}-launch.json').write_text(json.dumps(receipt,indent=2)+'\n')
        receipts.append(receipt)
    print(json.dumps(receipts,indent=2))


if __name__=='__main__':main()
