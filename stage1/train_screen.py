"""Resumable, source/data-pinned exploratory LM training with shuffled blocks.

Only train/validation arrays are opened; reserved test is not read. Checkpoints
include optimizer, scaler, sampling permutation/cursor and Python/torch RNG.
After a crash, a new attempt log preserves uncommitted older work for audit.
"""
import argparse
from contextlib import nullcontext
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import random
import time

import numpy as np
import torch
from torch.nn import functional as F
from .experiment import ARMS, configuration
from .model import Decoder
from .prepare_data import digest
from .prior_controls import deployed_parameters, set_guidance


@dataclass
class Settings:
    seed: int = 42
    steps: int = 6144
    seq: int = 512
    batch: int = 8
    accum: int = 4
    lr: float = 3e-4
    warmup: int = 200
    checkpoint_every: int = 256
    eval_every: int = 1024
    eval_tokens: int = 131072
    final_eval_tokens: int = 1048576
    deterministic: bool = True


class BlockSampler:
    def __init__(self, tokens, seq, seed):
        self.seq = seq
        self.blocks = (tokens - 1) // seq
        if self.blocks < 1: raise ValueError('training stream too short')
        self.rng = np.random.default_rng(seed)
        self.order = self.rng.permutation(self.blocks)
        self.cursor = self.epoch = self.samples = 0
        self.chain = bytes(32)

    def next(self, batch):
        chunks = []; needed = batch
        while needed:
            if self.cursor == self.blocks:
                self.order = self.rng.permutation(self.blocks)
                self.cursor = 0; self.epoch += 1
            take = min(needed, self.blocks-self.cursor)
            chunks.append(self.order[self.cursor:self.cursor+take])
            self.cursor += take; needed -= take
        starts = np.concatenate(chunks).astype('<i8') * self.seq
        self.chain = hashlib.sha256(self.chain + starts.tobytes()).digest()
        self.samples += batch
        return starts

    def state_dict(self):
        return dict(seq=self.seq, blocks=self.blocks, order=torch.from_numpy(self.order.copy()),
                    cursor=self.cursor, epoch=self.epoch, samples=self.samples,
                    rng=self.rng.bit_generator.state, chain=self.chain.hex())

    def load_state_dict(self, state):
        if state['seq'] != self.seq or state['blocks'] != self.blocks:
            raise ValueError('sampler shape mismatch')
        self.order = state['order'].cpu().numpy().copy()
        self.cursor, self.epoch, self.samples = state['cursor'], state['epoch'], state['samples']
        self.rng.bit_generator.state = state['rng']
        self.chain = bytes.fromhex(state['chain'])


def autocast(device):
    return torch.autocast('cuda', dtype=torch.float16) if device.type == 'cuda' else nullcontext()


@torch.no_grad()
def evaluate(model, data, seq, tokens, device):
    model.eval(); total = 0.; count = 0
    stop = min(len(data)-1, tokens)
    for start in range(0, stop-seq+1, seq):
        ids = torch.from_numpy(np.array(data[start:start+seq+1], dtype=np.int64)).to(device).unsqueeze(0)
        with autocast(device):
            logits, _ = model(ids[:, :-1])
            nll = F.cross_entropy(logits.flatten(0, 1), ids[:, 1:].flatten(), reduction='sum')
        total += float(nll); count += seq
    if count == 0: raise ValueError('empty evaluation')
    return dict(nll=total/count, perplexity=math.exp(min(50., total/count)), tokens=count,
                path='deployment graph; no dense training guides')


def source_hashes():
    names = ['train_screen.py', 'experiment.py', 'model.py', 'communication.py',
             'structured.py', 'prior_controls.py', 'prepare_data.py']
    return {name: digest(Path(__file__).parent/name) for name in names}


def atomic_save(obj, path):
    temporary = path.with_suffix('.tmp')
    torch.save(obj, temporary)
    os.replace(temporary, path)


def train_session(c, settings, data_root, out, device='cuda', resume=False, stop_after=None):
    if min(settings.steps, settings.seq, settings.batch, settings.accum,
           settings.checkpoint_every, settings.eval_every) <= 0:
        raise ValueError('positive run dimensions required')
    if settings.seq > c.context: raise ValueError('sequence exceeds position table')
    device = torch.device(device); data_root, out = Path(data_root), Path(out)
    if settings.deterministic:
        os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
        torch.use_deterministic_algorithms(True)
        torch.backends.cudnn.benchmark = False
        # Volta's memory-efficient SDPA backward can differ even before a
        # checkpoint. Use the same deterministic math path for every arm.
        if device.type == 'cuda':
            torch.backends.cuda.enable_flash_sdp(False)
            torch.backends.cuda.enable_mem_efficient_sdp(False)
            torch.backends.cuda.enable_math_sdp(True)
    else:
        torch.use_deterministic_algorithms(False)
    manifest = json.loads((data_root/'manifest.json').read_text())
    if manifest['vocab'] != c.vocab: raise ValueError('vocabulary mismatch')
    arrays = {}
    for split in ('train', 'validation'):
        path = data_root/f'{split}.npy'
        if digest(path) != manifest[split]['token_file_sha256']:
            raise ValueError(f'{split} hash mismatch')
        arrays[split] = np.load(path, mmap_mode='r')
    identity = dict(config=asdict(c), settings=asdict(settings), sources=source_hashes(),
                    data_manifest_sha256=digest(data_root/'manifest.json'),
                    runtime=dict(torch=str(torch.__version__),device_type=device.type,
                                 gpu=torch.cuda.get_device_name(device) if device.type=='cuda' else None))
    if resume:
        previous = json.loads((out/'run_manifest.json').read_text())
        if previous['identity'] != identity: raise ValueError('resume contract/source/data changed')
    else:
        out.mkdir(parents=True, exist_ok=False)
        (out/'run_manifest.json').write_text(json.dumps(dict(identity=identity,
            utc=datetime.now(timezone.utc).isoformat(), torch=torch.__version__,
            device=str(device), gpu=torch.cuda.get_device_name(device) if device.type == 'cuda' else None,
            data_manifest=manifest), indent=2)+'\n')
    random.seed(settings.seed); torch.manual_seed(settings.seed)
    model = Decoder(c); model.reset_parameters(settings.seed); model.to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=settings.lr, betas=(0.9, 0.95), weight_decay=0.1)
    scaler = torch.amp.GradScaler('cuda', enabled=device.type == 'cuda', init_scale=1024)
    sampler = BlockSampler(len(arrays['train']), settings.seq, settings.seed+17000)
    step = 0; train_seconds = 0.; initial = None
    if resume:
        state = torch.load(out/'last.pt', map_location='cpu', weights_only=True)
        if state['identity'] != identity: raise ValueError('checkpoint identity mismatch')
        model.load_state_dict(state['model']); optimizer.load_state_dict(state['optimizer'])
        scaler.load_state_dict(state['scaler']); sampler.load_state_dict(state['sampler'])
        step = state['step']; train_seconds = state['train_seconds']; initial = state['initial']
        random.setstate(state['python_rng']); torch.set_rng_state(state['torch_rng'])
        if device.type == 'cuda': torch.cuda.set_rng_state_all(state['cuda_rng'])
    else:
        initial = evaluate(model, arrays['validation'], settings.seq, settings.eval_tokens, device)
        (out/'initial.json').write_text(json.dumps(initial, indent=2)+'\n')
    limit = settings.steps if stop_after is None else min(settings.steps, stop_after)
    if limit < step: raise ValueError('stop step precedes checkpoint')
    attempt = len(list(out.glob('attempt-*.jsonl')))

    def checkpoint():
        atomic_save(dict(identity=identity, model=model.state_dict(), optimizer=optimizer.state_dict(),
                         scaler=scaler.state_dict(), sampler=sampler.state_dict(), step=step,
                         train_seconds=train_seconds, initial=initial, python_rng=random.getstate(),
                         torch_rng=torch.get_rng_state(),
                         cuda_rng=torch.cuda.get_rng_state_all() if device.type == 'cuda' else []), out/'last.pt')

    with (out/f'attempt-{attempt:03d}.jsonl').open('x') as log:
        log.write(json.dumps(dict(event='start', restored_step=step, attempt=attempt))+'\n'); log.flush()
        while step < limit:
            started = time.perf_counter(); model.train(); set_guidance(model, step, settings.steps)
            optimizer.zero_grad(set_to_none=True)
            warmup = min(1., (step+1)/max(1, settings.warmup))
            decay = .1 + .9*.5*(1+math.cos(math.pi*step/max(1, settings.steps-1)))
            for group in optimizer.param_groups: group['lr'] = settings.lr * min(warmup, decay)
            loss_sum = 0.
            for _ in range(settings.accum):
                starts = sampler.next(settings.batch)
                windows = np.stack([arrays['train'][s:s+settings.seq+1] for s in starts]).astype(np.int64)
                ids = torch.from_numpy(windows).to(device)
                with autocast(device):
                    logits, _ = model(ids[:, :-1])
                    loss = F.cross_entropy(logits.flatten(0, 1), ids[:, 1:].reshape(-1))
                if not torch.isfinite(loss): raise FloatingPointError(f'nonfinite loss step {step+1}')
                scaler.scale(loss/settings.accum).backward(); loss_sum += float(loss.detach())/settings.accum
            scaler.unscale_(optimizer)
            norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scale = scaler.get_scale(); scaler.step(optimizer); scaler.update()
            skipped = scaler.get_scale() < scale
            if skipped or not torch.isfinite(norm):
                (out/'failure.json').write_text(json.dumps(dict(step=step+1, skipped=skipped,
                                                               gradient_norm=float(norm)))+'\n')
                raise FloatingPointError('nonfinite gradient/skipped update; preserve failure')
            step += 1; train_seconds += time.perf_counter()-started
            row = dict(step=step, train_nll=loss_sum, gradient_norm=float(norm),
                       tokens_seen=step*settings.batch*settings.accum*settings.seq,
                       train_seconds=train_seconds, sample_chain=sampler.chain.hex(), skipped=False)
            if step % settings.eval_every == 0:
                row['validation'] = evaluate(model, arrays['validation'], settings.seq, settings.eval_tokens, device)
            log.write(json.dumps(row)+'\n'); log.flush()
            if step == 1 or step % 128 == 0: print(json.dumps(row), flush=True)
            if step % settings.checkpoint_every == 0: checkpoint()
        checkpoint()
    complete = step == settings.steps
    result = dict(status='complete' if complete else 'paused', config=asdict(c), settings=asdict(settings),
                  steps_completed=step, training_tokens=step*settings.batch*settings.accum*settings.seq,
                  train_seconds=train_seconds, sample_chain=sampler.chain.hex(), initial=initial,
                  parameters_training=sum(p.numel() for p in model.parameters()),
                  parameters_deployed=deployed_parameters(model), source_hashes=identity['sources'])
    if complete:
        result['final'] = evaluate(model, arrays['validation'], settings.seq, settings.final_eval_tokens, device)
        # Deployment exports omit training-only dense guidance parameters.
        deployed_config = asdict(c)
        if c.ffn_kind == 'blockdense_guided': deployed_config['ffn_kind'] = 'blockdense'
        atomic_save(dict(config=deployed_config,
                         model={k:v for k,v in model.state_dict().items() if not k.endswith('.guide')}), out/'final.pt')
    (out/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print('RESULT', json.dumps(result), flush=True)
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--arm', choices=ARMS, required=True); p.add_argument('--data', required=True)
    p.add_argument('--out', required=True); p.add_argument('--resume', action='store_true')
    p.add_argument('--stop-after', type=int); p.add_argument('--device', default='cuda')
    p.add_argument('--seed', type=int, default=42); p.add_argument('--steps', type=int, default=6144)
    a = p.parse_args(); torch.set_num_threads(4)
    train_session(configuration(a.arm), Settings(seed=a.seed, steps=a.steps), a.data, a.out,
                  device=a.device, resume=a.resume, stop_after=a.stop_after)


if __name__ == '__main__': main()
