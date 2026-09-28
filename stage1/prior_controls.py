"""Local equation-based prior-work controls, not complete paper reproductions.

GroupBERT-style dense expansion/grouped contraction/dense mixing is adapted to
SwiGLU. BlockDense uses a block-diagonal first factor and dense second factor;
optional dense self-guidance follows the deterministic cosine-half-run recipe.
No third-party implementation source is incorporated.
"""
import hashlib
import math
import torch
from torch import nn
from torch.nn import functional as F


PRIOR_KINDS = ('groupbert_pattern', 'blockdense', 'blockdense_guided')


def normal(parameter, std, seed, name):
    key = int.from_bytes(hashlib.sha256(f'{seed}:{name}'.encode()).digest()[:8], 'little')
    nn.init.normal_(parameter, std=std,
                    generator=torch.Generator(device=parameter.device).manual_seed(key))


class BlockDenseLinear(nn.Module):
    def __init__(self, inputs, outputs, groups, rank, guided=False):
        super().__init__()
        if min(inputs, outputs, groups, rank) <= 0 or inputs % groups or rank % groups:
            raise ValueError('invalid BlockDense dimensions')
        self.inputs, self.outputs = inputs, outputs
        self.first = nn.Parameter(torch.empty(groups, rank // groups, inputs // groups))
        self.second = nn.Parameter(torch.empty(outputs, rank))
        self.register_parameter('guide', nn.Parameter(torch.empty(outputs, inputs)) if guided else None)
        self.register_buffer('alpha', torch.tensor(0.0))

    def matrix(self):
        return self.second @ torch.block_diag(*self.first.unbind())

    def forward(self, x):
        g, _, p = self.first.shape
        local = x.reshape(*x.shape[:-1], g, p)
        hidden = torch.einsum('...gp,grp->...gr', local, self.first).flatten(-2)
        structured = F.linear(hidden, self.second)
        # Guidance is a training device. Eval always scores the deployment graph.
        if self.training and self.guide is not None:
            return (1-self.alpha) * structured + self.alpha * F.linear(x, self.guide)
        return structured


class PriorFFN(nn.Module):
    def __init__(self, c):
        super().__init__()
        if c.init_policy != 'fan_matched':
            raise ValueError('prior controls require fan_matched initialization')
        self.c = c
        if c.ffn_kind == 'groupbert_pattern':
            self.up_gate = nn.Linear(c.width, 2*c.hidden, bias=False)
            self.down = nn.Parameter(torch.empty(c.groups, c.hidden//c.groups, c.width//c.groups))
            self.mix = nn.Linear(c.width, c.width, bias=False)
        else:
            guide = c.ffn_kind == 'blockdense_guided'
            self.up_gate = BlockDenseLinear(c.width, 2*c.hidden, c.factor_blocks, c.rank, guide)
            self.down = BlockDenseLinear(c.hidden, c.width, c.factor_blocks, c.rank, guide)
        self.reset_parameters()

    @torch.no_grad()
    def reset_parameters(self, seed=42, prefix=''):
        c = self.c
        a = 0.02 * math.sqrt(c.width)
        b = 0.02 * math.sqrt(8*c.width/3) / math.sqrt(2*c.layers)
        for name, p in self.named_parameters():
            gain = b if name.startswith('down') else a
            if c.ffn_kind == 'groupbert_pattern':
                std = 1/math.sqrt(c.width) if name == 'mix.weight' else gain/math.sqrt(
                    p.shape[-2] if p.ndim == 3 else p.shape[-1])
            else:
                std = 1/math.sqrt(p.shape[-1]) if name.endswith('first') else gain/math.sqrt(p.shape[-1])
            normal(p, std, seed, f'{prefix}.{name}' if prefix else name)
        for module in self.modules():
            if isinstance(module, BlockDenseLinear) and module.guide is not None:
                module.guide.copy_(module.matrix())
                module.alpha.fill_(1)

    def forward(self, x):
        gate, value = self.up_gate(x).chunk(2, -1)
        hidden = F.silu(gate) * value
        if self.c.ffn_kind == 'groupbert_pattern':
            local = hidden.reshape(*x.shape[:-1], self.c.groups, self.c.hidden//self.c.groups)
            out = torch.einsum('...gi,gij->...gj', local, self.down).reshape_as(x)
            return self.mix(out)
        return self.down(hidden)


def set_guidance(model, step, total_steps):
    alpha = 0.5 * (1 + math.cos(math.pi * min(1.0, step / max(1, total_steps*0.5))))
    for module in model.modules():
        if isinstance(module, BlockDenseLinear):
            module.alpha.fill_(alpha)


def deployed_parameters(model):
    return sum(p.numel() for name, p in model.named_parameters() if not name.endswith('.guide'))
