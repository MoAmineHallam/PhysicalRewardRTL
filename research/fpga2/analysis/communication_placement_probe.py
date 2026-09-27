"""Check the proposed FFN equations, not language quality or hardware speed.

Run from the FPGA2 repository root with --output <json path>.
CPU float64 only; no downloaded data, training, or accelerator access.
"""

import argparse
import json
from pathlib import Path

import torch
from torch.nn.functional import silu


def probe(seed):
    generator = torch.Generator().manual_seed(seed)
    d, m, groups, rank = 12, 18, 3, 2
    dg, mg = d // groups, m // groups

    def rand(*shape):
        return torch.randn(*shape, generator=generator, dtype=torch.float64) / 2

    a, u, down = rand(groups, mg, dg), rand(groups, mg, dg), rand(groups, dg, mg)
    p, b = rand(groups, rank, dg), rand(groups, mg, rank)
    r, q = rand(groups, rank, mg), rand(groups, dg, rank)
    x = rand(d)

    def before(value):
        chunks = value.reshape(groups, dg)
        z = torch.einsum('grd,gd->r', p, chunks)
        gate = torch.einsum('gmd,gd->gm', a, chunks) + torch.einsum('gmr,r->gm', b, z)
        local_value = torch.einsum('gmd,gd->gm', u, chunks)
        return torch.einsum('gdm,gm->gd', down, silu(gate) * local_value).flatten()

    def after(value):
        chunks = value.reshape(groups, dg)
        hidden = silu(torch.einsum('gmd,gd->gm', a, chunks)) * torch.einsum('gmd,gd->gm', u, chunks)
        z = torch.einsum('grm,gm->r', r, hidden)
        return (torch.einsum('gdm,gm->gd', down, hidden) + torch.einsum('gdr,r->gd', q, z)).flatten()

    expected = 3 * d * m // groups + rank * (d + m)
    counts = [sum(t.numel() for t in matrices) for matrices in [(a, u, down, p, b), (a, u, down, r, q)]]
    assert counts == [expected, expected]
    jac = torch.autograd.functional.jacobian(before, x)
    chunks = x.reshape(groups, dg)
    z = torch.einsum('grd,gd->r', p, chunks)
    gate = a[0] @ chunks[0] + b[0] @ z
    gate_derivative = torch.sigmoid(gate) * (1 + gate * (1 - torch.sigmoid(gate)))
    analytic = down[0] @ torch.diag((u[0] @ chunks[0]) * gate_derivative) @ b[0] @ p[1]
    cross = jac[:dg, dg:2 * dg]
    error = (analytic - cross).abs().max().item()
    cross_rank = torch.linalg.matrix_rank(cross, atol=1e-10, rtol=0).item()
    assert error < 1e-12 and cross_rank <= rank
    hessian_before = torch.autograd.functional.hessian(lambda value: before(value)[:dg].sum(), x)
    hessian_after = torch.autograd.functional.hessian(lambda value: after(value)[:dg].sum(), x)
    mixed_before = hessian_before[:dg, dg:2 * dg].abs().max().item()
    mixed_after = hessian_after[:dg, dg:2 * dg].abs().max().item()
    assert mixed_before > 1e-8 and mixed_after < 1e-12
    zero_local = x.clone()
    zero_local[:dg] = 0
    before_zero = before(zero_local)[:dg].abs().max().item()
    after_zero = after(zero_local)[:dg].abs().max().item()
    assert before_zero == 0 and after_zero > 1e-8
    return dict(seed=seed, dimensions=dict(d=d, m=m, groups=groups, rank=rank),
                parameters_each=expected, cross_jacobian_rank=cross_rank,
                analytic_jacobian_max_error=error,
                mixed_hessian_max_before=mixed_before, mixed_hessian_max_after=mixed_after,
                zero_local_input_output_max_before=before_zero,
                zero_local_input_output_max_after=after_zero)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    rows = []
    for d, m, g, r in [(768, 2048, 2, 64), (768, 2048, 4, 64), (384, 1024, 4, 36), (384, 1024, 4, 72)]:
        count = 3 * d * m // g + r * (d + m)
        rows.append(dict(d=d, m=m, groups=g, rank=r, weights=count,
                         dense_hidden_equivalent=count / (3 * d)))
    result = dict(scope='Isolated bias-free FFN after normalization; random CPU float64 numerical checks only.',
                  limitations='No trained model, quantized arithmetic, hardware implementation, performance or novelty evidence.',
                  torch_version=torch.__version__, checks=[probe(seed) for seed in (7, 19, 31)], counts=rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
