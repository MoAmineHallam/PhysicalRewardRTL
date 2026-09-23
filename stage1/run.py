"""Bounded matched-data pilot and CUDA profiling; no hardware speedup claim."""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import statistics
import time
import numpy as np
import torch
from torch.nn import functional as F
from .model import Config, Decoder


def file_hash(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def environment():
    return {'utc': datetime.now(timezone.utc).isoformat(), 'python': platform.python_version(),
            'torch': torch.__version__, 'cuda': torch.version.cuda,
            'gpu': torch.cuda.get_device_name(0),
            'sources': {p.name: file_hash(p) for p in sorted(Path(__file__).parent.glob('*.py'))}}


def configuration(arm, target=False):
    c = Config(width=768, layers=12, heads=12, hidden=2048) if target else Config()
    if arm == 'narrow':
        c.hidden //= 4
    elif arm in ('grouped', 'shuffle'):
        c.groups = 4; c.shuffle = arm == 'shuffle'
    return c


@torch.no_grad()
def evaluate(model, data, seq, max_tokens=65536):
    model.eval(); total = 0.; count = 0
    stop = min(len(data)-1, max_tokens)
    for start in range(0, stop-seq+1, seq):
        x = torch.from_numpy(data[start:start+seq].astype(np.int64)).unsqueeze(0).cuda()
        y = torch.from_numpy(data[start+1:start+seq+1].astype(np.int64)).unsqueeze(0).cuda()
        with torch.autocast('cuda', dtype=torch.float16):
            logits, _ = model(x)
            loss = F.cross_entropy(logits.flatten(0, 1), y.flatten(), reduction='sum')
        total += loss.item(); count += seq
    if not count:
        raise ValueError('empty evaluation')
    return {'nll': total/count, 'perplexity': math.exp(min(50., total/count)), 'tokens': count,
            'policy': 'nonoverlapping development windows; EOS concatenation; all next-token targets scored'}


def train(a, c, model, out):
    data_root = Path(a.data)
    data_manifest = json.loads((data_root/'manifest.json').read_text())
    for split in ['train', 'validation']:
        if file_hash(data_root/f'{split}.npy') != data_manifest[split]['token_file_sha256']:
            raise ValueError(f'{split} token hash mismatch')
    if data_manifest['vocab'] != c.vocab:
        raise ValueError('tokenizer/model vocabulary mismatch')
    data = np.load(data_root/'train.npy', mmap_mode='r')
    val = np.load(data_root/'validation.npy', mmap_mode='r')
    rng = np.random.default_rng(a.seed + 17000)
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4, betas=(0.9, 0.95), weight_decay=0.1)
    scaler = torch.amp.GradScaler('cuda', init_scale=1024)
    initial = evaluate(model, val, a.seq)
    (out/'initial.json').write_text(json.dumps(initial, indent=2)+'\n')
    print('INITIAL', json.dumps(initial), flush=True)
    started = time.perf_counter(); skipped = 0; sample_digest = hashlib.sha256()
    with (out/'metrics.jsonl').open('w') as log:
        for step in range(a.steps):
            model.train(); optimizer.zero_grad(set_to_none=True); loss_sum = 0.
            warmup = min(1., (step+1)/20)
            decay = 0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * step / max(1, a.steps-1)))
            for group in optimizer.param_groups:
                group['lr'] = 3e-4 * min(warmup, decay)
            for _ in range(a.accum):
                starts = rng.integers(0, len(data)-a.seq, size=a.batch, dtype=np.int64)
                sample_digest.update(starts.astype('<i8').tobytes())
                windows = np.stack([data[s:s+a.seq+1] for s in starts]).astype(np.int64)
                batch = torch.from_numpy(windows).cuda()
                with torch.autocast('cuda', dtype=torch.float16):
                    logits, _ = model(batch[:, :-1])
                    loss = F.cross_entropy(logits.flatten(0, 1), batch[:, 1:].reshape(-1))
                if not torch.isfinite(loss):
                    raise FloatingPointError(f'nonfinite loss at step {step}')
                scaler.scale(loss/a.accum).backward(); loss_sum += loss.item()/a.accum
            scaler.unscale_(optimizer)
            norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            before = scaler.get_scale(); scaler.step(optimizer); scaler.update()
            was_skipped = scaler.get_scale() < before
            skipped += int(was_skipped)
            row = {'step': step+1, 'train_nll': loss_sum, 'gradient_norm': float(norm),
                   'optimizer_step_skipped': was_skipped, 'scale': scaler.get_scale(),
                   'tokens_seen': (step+1)*a.batch*a.seq*a.accum,
                   'elapsed_seconds': time.perf_counter()-started}
            log.write(json.dumps(row)+'\n'); log.flush()
            if (step+1) % 32 == 0 or step == 0:
                print(json.dumps(row), flush=True)
    train_seconds = time.perf_counter()-started
    final = evaluate(model, val, a.seq)
    result = {'status': 'complete', 'arm': a.arm, 'config': asdict(c), 'seed': a.seed,
              'initial': initial, 'final': final, 'steps_attempted': a.steps,
              'optimizer_updates': a.steps-skipped, 'skipped_updates': skipped,
              'training_tokens': a.steps*a.batch*a.seq*a.accum,
              'training_seconds': train_seconds, 'sample_order_sha256': sample_digest.hexdigest(),
              'data_manifest': data_manifest, 'peak_allocated_bytes': torch.cuda.max_memory_allocated(),
              'parameters': sum(p.numel() for p in model.parameters()),
              'interpretation': 'single-seed short development pilot; not preserved-quality evidence'}
    torch.save({'config': asdict(c), 'model': model.state_dict(), 'seed': a.seed}, out/'final.pt')
    (out/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print('RESULT', json.dumps({k:v for k,v in result.items() if k != 'data_manifest'}), flush=True)


@torch.no_grad()
def profile(a, c, model, out):
    model.half().eval(); reports = []
    for length in [512, 2048]:
        ids = torch.randint(c.vocab, (1, length), device='cuda')
        token = ids[:, -1:]
        _, cache = model(ids, use_cache=True, last_only=True)
        for mode in ['prefill', 'decode']:
            def call():
                return model(ids, use_cache=True, last_only=True) if mode == 'prefill' else model(
                    token, past=cache, use_cache=True, last_only=True)
            for _ in range(5): call()
            torch.cuda.synchronize(); times = []
            torch.cuda.reset_peak_memory_stats()
            for _ in range(20):
                start = torch.cuda.Event(enable_timing=True); end = torch.cuda.Event(enable_timing=True)
                start.record(); call(); end.record(); end.synchronize()
                times.append(start.elapsed_time(end))
            with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU,
                                                    torch.profiler.ProfilerActivity.CUDA],
                                        record_shapes=True) as prof:
                for _ in range(3): call()
                torch.cuda.synchronize()
            operations = []
            for e in prof.key_averages():
                if e.key in ['block.attention', 'block.ffn', 'output_head'] or e.self_device_time_total > 0:
                    operations.append({'name': e.key, 'calls': e.count,
                                       'inclusive_cuda_us': e.device_time_total,
                                       'self_cuda_us': e.self_device_time_total})
            d, m, l, g = c.width, c.hidden, c.layers, c.groups
            reports.append({'mode': mode, 'prompt_tokens': length, 'batch': 1,
                            'median_cuda_ms': statistics.median(times), 'samples_cuda_ms': times,
                            'peak_allocated_bytes': torch.cuda.max_memory_allocated(), 'operators': operations,
                            'analytical_not_measured': {
                                'ffn_weight_bytes_fp16': l*3*d*m//g*2,
                                'attention_projection_weight_bytes_fp16': l*4*d*d*2,
                                'embedding_or_tied_head_weight_bytes_fp16': c.vocab*d*2,
                                'kv_live_bytes_at_prompt': 2*l*length*d*2,
                                'kv_read_bytes_single_decode_minimum': 2*l*length*d*2},
                            'scope': 'eager GPU reference; dynamic concatenating KV cache; random weights and ids; last-token logits only; no DRAM byte counters'})
    result = {'config': asdict(c), 'parameters': sum(p.numel() for p in model.parameters()),
              'measurements': reports}
    (out/'profile.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2), flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('mode', choices=['train', 'profile'])
    p.add_argument('--arm', choices=['dense', 'narrow', 'grouped', 'shuffle'], default='dense')
    p.add_argument('--data'); p.add_argument('--out', required=True)
    p.add_argument('--steps', type=int, default=256); p.add_argument('--batch', type=int, default=8)
    p.add_argument('--accum', type=int, default=4); p.add_argument('--seq', type=int, default=256)
    p.add_argument('--seed', type=int, default=42); p.add_argument('--target', action='store_true')
    a = p.parse_args()
    torch.set_num_threads(4); torch.manual_seed(a.seed)
    if not torch.cuda.is_available(): raise RuntimeError('CUDA required for measured runs')
    if a.mode == 'train' and (not a.data or min(a.steps, a.batch, a.accum, a.seq) <= 0):
        raise ValueError('training requires data and positive run dimensions')
    out = Path(a.out); out.mkdir(parents=True, exist_ok=False)
    c = configuration(a.arm, a.target)
    model = Decoder(c); model.reset_parameters(a.seed); model.cuda()
    manifest = {'arguments': vars(a), 'environment': environment(), 'config': asdict(c)}
    (out/'run_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps(manifest), flush=True)
    train(a, c, model, out) if a.mode == 'train' else profile(a, c, model, out)


if __name__ == '__main__':
    main()
