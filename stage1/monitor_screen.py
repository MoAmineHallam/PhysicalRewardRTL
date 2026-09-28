"""Read-only screen progress; safe to stop without affecting training workers."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time


def snapshot(root):
    lines = []; total_done = 0
    for i in range(4):
        host = 'V100a' if i < 2 else 'V100b'
        folder = root / f'campaign-{i}'
        try:
            worker = json.loads((folder/'worker.json').read_text())
            done = sum(bool(row.get('accepted', False)) for row in worker['runs'])
            total_done += done
            active = worker.get('active')
            arm = active['arm'] if active else '-'
            step = 0; updated = None; target = None
            if active:
                run = folder/arm
                manifest_path = run/'run_manifest.json'
                if manifest_path.exists():
                    target = json.loads(manifest_path.read_text())['identity']['settings']['steps']
                for log in sorted(run.glob('attempt-*.jsonl')):
                    updated = log.stat().st_mtime
                    for line in log.read_text().splitlines():
                        try:
                            row = json.loads(line)
                        except json.JSONDecodeError:
                            continue  # An actively appended final row may be incomplete.
                        if row.get('event') == 'start':
                            step = row.get('restored_step', step)
                        elif 'step' in row:
                            step = row['step']
            progress = f'{step}/{target} ({100*step/target:.1f}%)' if target else '-'
            age = f'{max(0, int(time.time()-updated))}s ago' if updated is not None else '-'
            lines.append(f'{host} GPU{i % 2}: {worker["status"]:8} | {done}/{len(worker["arms"])} done | '
                         f'{arm:22} | {progress:21} | log: {age}')
        except (OSError, ValueError, KeyError, TypeError) as error:
            lines.append(f'{host} GPU{i % 2}: waiting/unreadable ({type(error).__name__})')
    return lines, total_done


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--interval', type=float, default=15)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    if args.interval <= 0:
        parser.error('--interval must be positive')
    try:
        while True:
            lines, completed = snapshot(args.root)
            if sys.stdout.isatty() and not args.once:
                print('\033[2J\033[H', end='')
            print(datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'))
            print('\n'.join(lines))
            print(f'\nCompleted experiments: {completed}/24')
            print('Status comes from worker files; log age helps identify stalled updates.')
            if args.once: break
            print('Refresh every %.0fs. Ctrl+C stops only this monitor.' % args.interval, flush=True)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print('\nMonitor stopped. Training workers are unaffected.')


if __name__ == '__main__':
    main()
