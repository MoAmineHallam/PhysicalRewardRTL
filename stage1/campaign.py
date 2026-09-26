"""Bounded sequential worker for the frozen September 26 screening protocol."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


ORDERS = {
    42: ['dense', 'narrow', 'grouped', 'shuffle', 'monarch', 'monarch_dense_match', 'lowrank'],
    43: ['shuffle', 'monarch', 'monarch_dense_match', 'lowrank', 'dense', 'narrow', 'grouped'],
    44: ['lowrank', 'monarch_dense_match', 'monarch', 'shuffle', 'grouped', 'narrow', 'dense'],
}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seed', type=int, choices=list(ORDERS), required=True)
    p.add_argument('--data', required=True); p.add_argument('--out', required=True)
    p.add_argument('--legacy-check', action='store_true')
    a = p.parse_args()
    if a.legacy_check and a.seed != 42: p.error('legacy diagnostic is seed 42 only')
    out = Path(a.out); out.mkdir(parents=True, exist_ok=False)
    arms = ['narrow', 'grouped', 'shuffle'] if a.legacy_check else ORDERS[a.seed]
    policy = 'legacy' if a.legacy_check else 'fan_matched'
    report = {'utc_start': datetime.now(timezone.utc).isoformat(), 'seed': a.seed,
              'init_policy': policy, 'arms': arms, 'status': 'running', 'runs': []}
    (out/'worker.json').write_text(json.dumps(report, indent=2)+'\n')
    expected_samples = None
    for arm in arms:
        dest = out/arm
        cmd = [sys.executable, '-u', '-m', 'stage1.run', 'train', '--arm', arm,
               '--init-policy', policy, '--data', a.data, '--out', str(dest),
               '--steps', '1024', '--seed', str(a.seed)]
        started = time.perf_counter()
        with (out/(arm+'.log')).open('x') as log:
            proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=log,
                                    stderr=subprocess.STDOUT, start_new_session=True)
            try:
                code = proc.wait(timeout=1200)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGTERM)
                try: proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL); proc.wait()
                code = -1
        row = {'arm': arm, 'returncode': code, 'process_wall_seconds': time.perf_counter()-started}
        if code == 0 and (dest/'result.json').exists():
            r = json.loads((dest/'result.json').read_text())
            row.update(final=r['final'], skipped_updates=r['skipped_updates'],
                       sample_order_sha256=r['sample_order_sha256'])
            if expected_samples is None: expected_samples = r['sample_order_sha256']
            if r['skipped_updates'] or r['sample_order_sha256'] != expected_samples: code = -2
        else: code = code or -3
        row['accepted'] = code == 0
        report['runs'].append(row)
        report['status'] = 'running' if code == 0 else 'failed'
        (out/'worker.json').write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps(row), flush=True)
        if code != 0: raise RuntimeError('worker stopped; preserve and inspect '+str(dest))
    report['status'] = 'complete'
    report['utc_end'] = datetime.now(timezone.utc).isoformat()
    (out/'worker.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__': main()
