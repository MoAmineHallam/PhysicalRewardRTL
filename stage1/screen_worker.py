"""One bounded sequential GPU worker for the September 27 exploratory screen."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from .experiment import ARMS


def main():
    p=argparse.ArgumentParser();p.add_argument('--worker',type=int,choices=range(4),required=True)
    p.add_argument('--data',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
    seed=42 if a.worker<2 else 43
    arms=list(ARMS[a.worker%2::2])
    if seed==43:arms.reverse()
    report=dict(status='running',worker=a.worker,seed=seed,arms=arms,runs=[],
                utc_start=datetime.now(timezone.utc).isoformat())
    def save():
        temp=out/'worker.tmp';temp.write_text(json.dumps(report,indent=2)+'\n');os.replace(temp,out/'worker.json')
    save();chain=None
    for arm in arms:
        dest=out/arm
        cmd=[sys.executable,'-u','-m','stage1.train_screen','--arm',arm,'--data',a.data,
             '--out',str(dest),'--seed',str(seed)]
        start=time.monotonic()
        with (out/(arm+'.log')).open('x') as log:
            process=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=log,
                                     stderr=subprocess.STDOUT,start_new_session=True)
            report['active']=dict(arm=arm,pid=process.pid,command=cmd);save()
            try:code=process.wait(timeout=10800)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGTERM)
                try:process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid,signal.SIGKILL);process.wait()
                code=-1
        row=dict(arm=arm,returncode=code,process_wall_seconds=time.monotonic()-start)
        if code==0:
            result=json.loads((dest/'result.json').read_text())
            if chain is None:chain=result['sample_chain']
            accepted=(result['status']=='complete' and result['steps_completed']==6144
                      and result['training_tokens']==100663296 and result['sample_chain']==chain)
            row.update(accepted=accepted,final=result.get('final'),sample_chain=result['sample_chain'])
            if not accepted:code=-2
        report['runs'].append(row);report['active']=None
        if code!=0:
            report['status']='failed';save();raise RuntimeError('worker failed; preserve logs/checkpoints')
        save()
    report.update(status='complete',utc_end=datetime.now(timezone.utc).isoformat());save()


if __name__=='__main__':main()
