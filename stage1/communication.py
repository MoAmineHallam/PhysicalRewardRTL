"""Experimental FFNs with one logical global reduction/broadcast.

These are mathematical PyTorch references, not optimized kernels. See
research/fpga2/RESEARCH_PROPOSAL_20260927.md for prior art and hypothesis.
All tensors use (group, input, output) order. There are no biases.
"""
import hashlib
import math

import torch
from torch import nn
from torch.nn import functional as F


COMMUNICATION_KINDS = ('communication_gate', 'communication_value', 'communication_post')


class CommunicationFFN(nn.Module):
    def __init__(self, c):
        super().__init__()
        if c.ffn_kind not in COMMUNICATION_KINDS:
            raise ValueError('expected a communication FFN kind')
        if c.init_policy != 'fan_matched' or c.shuffle:
            raise ValueError('communication references require fan_matched and no shuffle')
        if (min(c.width, c.hidden, c.layers, c.groups, c.rank) <= 0
                or c.groups < 2 or c.width % c.groups or c.hidden % c.groups
                or c.rank > min(c.width, c.hidden)):
            raise ValueError('invalid communication dimensions')
        self.width, self.hidden, self.groups, self.rank = c.width, c.hidden, c.groups, c.rank
        self.layers, self.placement = c.layers, c.ffn_kind.removeprefix('communication_')
        dg, mg = c.width // c.groups, c.hidden // c.groups
        self.up_gate = nn.Parameter(torch.empty(c.groups, dg, 2 * mg))
        self.down = nn.Parameter(torch.empty(c.groups, mg, dg))
        read_width, write_width = (mg, dg) if self.placement == 'post' else (dg, mg)
        self.message_read = nn.Parameter(torch.empty(c.groups, read_width, c.rank))
        self.message_write = nn.Parameter(torch.empty(c.groups, c.rank, write_width))
        self.reset_parameters()

    @torch.no_grad()
    def reset_parameters(self, seed=42, prefix=''):
        """Match projection second moments; nonlinear output moments are empirical.

        Sum G partial messages at initialization with variance gain one. Split
        variance equally between local/global additive paths. Both factors start
        nonzero. A name-derived seed preserves pairing and non-FFN initialization.
        """
        dg, mg = self.width // self.groups, self.hidden // self.groups
        up_gain = 0.02 * math.sqrt(self.width)
        down_gain = 0.02 * math.sqrt(8 * self.width / 3) / math.sqrt(2 * self.layers)
        post = self.placement == 'post'
        stds = {
            'up_gate': up_gain / math.sqrt(dg),
            'down': down_gain / math.sqrt(mg * (2 if post else 1)),
            'message_read': 1 / math.sqrt(self.hidden if post else self.width),
            'message_write': (down_gain if post else up_gain) / math.sqrt(2 * self.rank),
        }
        for name, parameter in self.named_parameters():
            full_name = f'{prefix}.{name}' if prefix else name
            key = int.from_bytes(hashlib.sha256(f'{seed}:{full_name}'.encode()).digest()[:8], 'little')
            generator = torch.Generator(device=parameter.device).manual_seed(key)
            nn.init.normal_(parameter, std=stds[name], generator=generator)
        if self.placement == 'gate':
            self.up_gate[..., :mg].div_(math.sqrt(2))
        elif self.placement == 'value':
            self.up_gate[..., mg:].div_(math.sqrt(2))

    def _message(self, local):
        # The g index is reduced as well as the local input index.
        summary = torch.einsum('...gi,gir->...r', local, self.message_read)
        return torch.einsum('...r,gro->...go', summary, self.message_write)

    def forward(self, x):
        if x.shape[-1] != self.width:
            raise ValueError('FFN input width mismatch')
        local = x.reshape(*x.shape[:-1], self.groups, self.width // self.groups)
        gate, value = torch.einsum('...gi,gij->...gj', local, self.up_gate).chunk(2, -1)
        if self.placement == 'gate':
            gate = gate + self._message(local)
        elif self.placement == 'value':
            value = value + self._message(local)
        hidden = F.silu(gate) * value
        out = torch.einsum('...gi,gij->...gj', hidden, self.down)
        if self.placement == 'post':
            out = out + self._message(hidden)
        return out.reshape_as(x)
