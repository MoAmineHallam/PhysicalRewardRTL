"""Separate kernel attribution, eager launch latency, and fixed-shape CUDA graphs.

No GPU timing or analytical byte count is an FPGA/ASIC result. Run hardware
counters separately, never while collecting latency samples.
"""
import argparse
from collections import defaultdict
from dataclasses import asdict
import json
from pathlib import Path
import statistics
import time
import torch
from .model import Decoder
from .run import configuration, environment


REGIONS = {'attention.qkv', 'attention.cache_update', 'attention.sdpa',
           'attention.output_projection', 'ffn.core', 'output_head',
           'block.attention', 'block.ffn'}


def attribute_events(events):
    """Each CPU event contributes only its own kernels, to its nearest region.

    GPU activity events and parent inclusive durations are excluded from these
    totals; this avoids the duplicate names in the v1 profiler export.
    """
    by_region = defaultdict(float); by_op = defaultdict(float); gpu = defaultdict(float)
    counts = defaultdict(int)
    for event in events:
        device = event.device_type.name
        counts[device] += 1
        if device == 'CUDA':
            if not getattr(event, 'is_user_annotation', False) and event.name not in REGIONS:
                gpu[event.name] += event.self_device_time_total
            continue
        if device != 'CPU': continue
        own = event.self_device_time_total
        if own < -1e-4:
            raise ValueError('negative self device duration in profiler')
        if own <= 0: continue
        parent = event
        while parent is not None and parent.name not in REGIONS:
            parent = parent.cpu_parent
        name = parent.name if parent is not None else 'other'
        by_region[name] += own
        by_op[event.name] += own
    total = sum(by_region.values())
    return {'device_event_counts': dict(counts), 'attributed_kernel_us': total,
            'region_kernel_us': dict(by_region), 'operator_self_kernel_us': dict(by_op),
            'region_kernel_fraction': {k: v / total if total else None for k, v in by_region.items()},
            'device_activity_us_excluding_annotations': sum(gpu.values()),
            'device_kernel_names': sorted(gpu),
            'note': 'fractions of attributed kernel time, not fractions of elapsed request latency'}


def measure(call, prepare, repeats):
    samples = []
    begin = torch.cuda.Event(enable_timing=True); end = torch.cuda.Event(enable_timing=True)
    for _ in range(repeats):
        prepare(); torch.cuda.synchronize()
        wall = time.perf_counter(); begin.record(); result = call(); end.record(); end.synchronize()
        samples.append({'cuda_event_ms': begin.elapsed_time(end),
                        'synchronized_wall_ms': 1000*(time.perf_counter()-wall)})
        del result
    return {'median_cuda_event_ms': statistics.median(s['cuda_event_ms'] for s in samples),
            'median_synchronized_wall_ms': statistics.median(s['synchronized_wall_ms'] for s in samples),
            'samples': samples}


@torch.inference_mode()
def correctness(model):
    # Batch > 1 and both multi-token and one-token continuation catch offset-mask
    # mistakes that a single fixed-context performance call would miss.
    ids = torch.randint(model.config.vocab, (2, 19), device='cuda')
    full, _ = model(ids)
    cache = model.allocate_cache(2, 24)
    pieces = []
    for start, stop in [(0, 7), (7, 13), (13, 14), (14, 19)]:
        out, _ = model(ids[:, start:stop], cache, use_cache=True)
        pieces.append(out)
    static = torch.cat(pieces, 1)
    torch.testing.assert_close(static, full, rtol=0.025, atol=0.005)
    return {'max_abs_logit_error': float((static-full).abs().max()),
            'tolerance': {'rtol': 0.025, 'atol': 0.005}, 'dtype': str(full.dtype)}


@torch.inference_mode()
def run(a):
    torch.manual_seed(a.seed); torch.set_num_threads(4)
    c = configuration(a.arm, target=True)
    model = Decoder(c).cuda().half().eval()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=False)
    meta = {'environment': environment(), 'config': asdict(c), 'arguments': vars(a),
            'parameters': sum(p.numel() for p in model.parameters()), 'correctness': correctness(model)}
    (out/'manifest.json').write_text(json.dumps(meta, indent=2)+'\n')
    rows = []
    for length in a.lengths:
        ids = torch.randint(c.vocab, (1, length), device='cuda')
        token = ids[:, -1:]
        for kind in ['dynamic', 'static']:
            for mode in ['prefill', 'decode']:
                cache = model.allocate_cache(1, length+a.generate) if kind == 'static' else None
                if mode == 'decode':
                    _, cache = model(ids, cache, use_cache=True, last_only=True)

                def prepare():
                    if kind == 'static':
                        for layer in cache: layer.truncate(0 if mode == 'prefill' else length)

                def call():
                    return model(ids if mode == 'prefill' else token,
                                 past=cache, use_cache=True, last_only=True)

                model.set_profiling(False)
                for _ in range(5): prepare(); call()
                eager = measure(call, prepare, a.repeats)
                torch.cuda.reset_peak_memory_stats(); prepare(); call(); torch.cuda.synchronize()
                peak = torch.cuda.max_memory_allocated()
                model.set_profiling(True)
                with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU,
                                                        torch.profiler.ProfilerActivity.CUDA],
                                            record_shapes=True) as prof:
                    for _ in range(3): prepare(); call()
                    torch.cuda.synchronize()
                attribution = attribute_events(prof.events())
                model.set_profiling(False)
                # Graph replay isolates device work at a fixed shape. Cache
                # offsets are captured constants, so this is NOT a growing
                # autoregressive generation benchmark.
                graph_result = None; captured = None; graph = None
                try:
                    stream = torch.cuda.Stream(); stream.wait_stream(torch.cuda.current_stream())
                    with torch.cuda.stream(stream):
                        for _ in range(3): prepare(); call()
                    torch.cuda.current_stream().wait_stream(stream); torch.cuda.synchronize()
                    prepare(); graph = torch.cuda.CUDAGraph()
                    with torch.cuda.graph(graph): captured = call()
                    graph.replay(); torch.cuda.synchronize()
                    replay_logits = captured[0].clone()
                    prepare(); reference = call()[0]
                    torch.testing.assert_close(replay_logits, reference, rtol=0.025, atol=0.005)
                    graph_result = {'status': 'ok', **measure(graph.replay, lambda: None, a.repeats),
                                    'max_abs_logit_error': float((replay_logits-reference).abs().max())}
                    del reference, replay_logits
                except (RuntimeError, AssertionError) as error:
                    graph_result = {'status': 'failed', 'error': str(error)[:1500]}
                row = {'length': length, 'batch': 1, 'cache': kind, 'mode': mode,
                       'eager': eager, 'fixed_shape_cuda_graph': graph_result,
                       'profiler': attribution, 'peak_allocated_bytes': peak,
                       'logical_not_dram_bytes': {
                           'ffn_weights': c.layers*3*c.width*c.hidden//c.groups*2,
                           'kv_valid_prefix': 2*c.layers*length*c.width*2,
                           'old_kv_copy_read_plus_write_decode': 4*c.layers*length*c.width*2 if kind == 'dynamic' else 0}}
                rows.append(row)
                (out/'profile.json').write_text(json.dumps(rows, indent=2)+'\n')
                print(json.dumps({'length': length, 'mode': mode, 'cache': kind,
                                  'eager_ms': eager['median_cuda_event_ms'],
                                  'graph_ms': graph_result.get('median_cuda_event_ms'),
                                  'kernel_fractions': attribution['region_kernel_fraction']}), flush=True)
                del captured, graph, cache
                torch.cuda.empty_cache()
        # Actual growing cache: teacher-forced tokens, ordinary eager execution;
        # model-only latency includes prompt + all output-head evaluations.
        requests = []
        continuation = torch.randint(c.vocab, (1, a.generate), device='cuda')
        for kind in ['dynamic', 'static']:
            storage = model.allocate_cache(1, length+a.generate) if kind == 'static' else None
            def prep_request():
                if storage is not None:
                    for layer in storage: layer.truncate(0)
            def request():
                logits, state = model(ids, storage, use_cache=True, last_only=True)
                for i in range(a.generate):
                    logits, state = model(continuation[:, i:i+1], state,
                                          use_cache=True, last_only=True)
                return logits
            prep_request(); request()
            requests.append({'length': length, 'cache': kind, 'decode_steps': a.generate,
                             **measure(request, prep_request, 5)})
            del storage
        (out/f'requests-{length}.json').write_text(json.dumps(requests, indent=2)+'\n')
    (out/'COMPLETE').write_text('completed\n')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--out', required=True); p.add_argument('--seed', type=int, default=42)
    p.add_argument('--arm', choices=['dense', 'narrow', 'grouped', 'shuffle'], default='dense')
    p.add_argument('--lengths', type=int, nargs='+', default=[512, 2048])
    p.add_argument('--repeats', type=int, default=20); p.add_argument('--generate', type=int, default=32)
    a = p.parse_args()
    if min(a.lengths + [a.repeats, a.generate]) < 1 or max(a.lengths)+a.generate > 4096:
        p.error('positive dimensions and context <= 4096 required')
    run(a)


if __name__ == '__main__':
    main()
