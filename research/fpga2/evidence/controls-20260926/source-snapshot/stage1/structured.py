"""Established rectangular Monarch and ordinary low-rank projection controls.

Monarch organization follows HazyResearch/fly revision
6b73449a6b3e228af9e4afe4f153a384e9b537b9 (Apache-2.0); see THIRD_PARTY.md.
This is a local PyTorch implementation, not a reproduction of their full model,
training recipe, custom backward kernel, or reported speedups.
"""
import math
import torch
from torch import nn
from torch.nn import functional as F


class MonarchLinear(nn.Module):
    def __init__(self, inputs, outputs, blocks=4):
        super().__init__()
        if min(inputs, outputs, blocks) <= 0:
            raise ValueError('projection dimensions must be positive')
        self.inputs, self.outputs, self.blocks = inputs, outputs, blocks
        p, s = math.ceil(inputs/blocks), math.ceil(outputs/blocks)
        middle = min(p, s)
        self.first = nn.Parameter(torch.empty(blocks, middle, p))
        self.second = nn.Parameter(torch.empty(blocks, s, middle))

    def forward(self, x):
        g, q, p = self.first.shape
        _, s, r = self.second.shape
        z = F.pad(x, (0, g*p-self.inputs)).reshape(-1, g, p)
        # Block-diagonal first factor, interleaved intermediate routing, then
        # a second block-diagonal factor and interleaved output ordering.
        z = torch.einsum('bgp,gqp->bgq', z, self.first)
        z = z.reshape(-1, r, g).transpose(1, 2)
        y = torch.einsum('bgr,gsr->bsg', z, self.second)
        return y.reshape(*x.shape[:-1], s*g)[..., :self.outputs]


class LowRankLinear(nn.Module):
    def __init__(self, inputs, outputs, rank):
        super().__init__()
        if not 0 < rank <= min(inputs, outputs):
            raise ValueError('invalid low rank')
        self.inputs, self.outputs, self.rank = inputs, outputs, rank
        self.first = nn.Parameter(torch.empty(rank, inputs))
        self.second = nn.Parameter(torch.empty(outputs, rank))

    def forward(self, x):
        return F.linear(F.linear(x, self.first), self.second)
