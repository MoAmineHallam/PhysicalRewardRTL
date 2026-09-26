"""Launch two bounded jobs on idle GPUs; explicit host label avoids collisions."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--label', required=True, choices=['v100a', 'v100b'])
    a = p.parse_args()
    root = Path.cwd()
    if not (root/'data/manifest.json').is_file():
        raise RuntimeError('data preparation not complete')
    arms = ['dense', 'grouped'] if a.label == 'v100a' else ['narrow', 'shuffle']
    status = subprocess.check_output(['nvidia-smi', '--query-gpu=index,memory.used',
                                      '--format=csv,noheader,nounits'], text=True)
    used = dict(tuple(map(int, line.split(','))) for line in status.strip().splitlines())
    for gpu in range(2):
        if used.get(gpu, 99999) > 128:
            raise RuntimeError(f'GPU {gpu} not idle: {used.get(gpu)} MiB')
    # Refuse a partial relaunch before touching any outputs.
    for arm in arms:
        if (root/f'{arm}.log').exists() or (root/f'{arm}-seed42').exists():
            raise FileExistsError(f'run already exists: {arm}')
    launches = []
    for gpu, arm in enumerate(arms):
        env = os.environ.copy()
        env.update(CUDA_VISIBLE_DEVICES=str(gpu), OMP_NUM_THREADS='4', PYTHONUNBUFFERED='1')
        cmd = [sys.executable, '-u', '-m', 'stage1.run', 'train', '--arm', arm,
               '--data', str(root/'data'), '--out', str(root/f'{arm}-seed42')]
        with (root/f'{arm}.log').open('x') as log:
            proc = subprocess.Popen(cmd, cwd=root, env=env, stdin=subprocess.DEVNULL,
                                    stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        receipt = {'label': a.label, 'gpu': gpu, 'arm': arm, 'pid': proc.pid,
                   'utc': datetime.now(timezone.utc).isoformat(), 'command': cmd}
        (root/f'{arm}-launch.json').write_text(json.dumps(receipt, indent=2)+'\n')
        launches.append(receipt)
    print(json.dumps(launches, indent=2))


if __name__ == '__main__':
    main()
