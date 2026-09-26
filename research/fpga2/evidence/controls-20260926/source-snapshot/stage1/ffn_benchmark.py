"""Dense eager versus Inductor FFN control, including compile cost and parity.

One isolated layer with warm weights is a kernel diagnostic, not model latency.
"""
import argparse
import json
from pathlib import Path
import time
import torch
from .model import Decoder
from .run import configuration, environment
from .profile_v2 import measure


@torch.inference_mode()
def main():
    p = argparse.ArgumentParser(); p.add_argument('--out', required=True); a = p.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(4)
    c = configuration('dense', target=True)
    c.layers = 1; c.vocab = 1
    model = Decoder(c).cuda().half().eval()
    ffn = model.blocks[0].ffn
    report = {'environment': environment(), 'measurements': [],
              'scope': 'isolated dense FFN; warm weights; one layer; not full-model or FPGA speedup'}
    for tokens in [1, 512]:
        x = torch.randn(1, tokens, c.width, device='cuda', dtype=torch.float16)
        reference = ffn(x)
        for backend in ['eager', 'inductor']:
            row = {'tokens': tokens, 'backend': backend}
            try:
                started = time.perf_counter()
                fn = ffn if backend == 'eager' else torch.compile(ffn, fullgraph=True)
                y = fn(x); torch.cuda.synchronize()
                row['first_call_seconds_including_compile'] = time.perf_counter()-started
                torch.testing.assert_close(y, reference, rtol=.025, atol=.005)
                row['max_abs_error'] = float((y-reference).abs().max())
                for _ in range(5): fn(x)
                row['eager_launch'] = measure(lambda: fn(x), lambda: None, 100)
                stream = torch.cuda.Stream(); stream.wait_stream(torch.cuda.current_stream())
                with torch.cuda.stream(stream):
                    for _ in range(3): fn(x)
                torch.cuda.current_stream().wait_stream(stream); torch.cuda.synchronize()
                graph = torch.cuda.CUDAGraph()
                with torch.cuda.graph(graph): captured = fn(x)
                graph.replay(); torch.cuda.synchronize()
                torch.testing.assert_close(captured, reference, rtol=.025, atol=.005)
                row['fixed_shape_graph'] = measure(graph.replay, lambda: None, 100)
                row['status'] = 'ok'
                del graph, captured
            except Exception as error:
                row.update(status='failed', error=str(error)[:4000])
            report['measurements'].append(row)
            (out/'result.json').write_text(json.dumps(report, indent=2)+'\n')
            print(json.dumps({k:v for k,v in row.items() if k not in ('eager_launch','fixed_shape_graph')}), flush=True)
    (out/'COMPLETE').write_text('completed\n')


if __name__ == '__main__': main()
