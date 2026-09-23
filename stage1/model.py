"""Causal decoder and explicit FFN controls; no pretrained weights or RFT memory."""
from dataclasses import dataclass
import math
import torch
from torch import nn
from torch.nn import functional as F


@dataclass
class Config:
    vocab: int = 50257
    width: int = 384
    layers: int = 6
    heads: int = 6
    hidden: int = 1024
    context: int = 4096
    groups: int = 1
    shuffle: bool = False

    def __post_init__(self):
        if min(self.vocab, self.width, self.layers, self.heads, self.hidden,
               self.context, self.groups) <= 0:
            raise ValueError('dimensions must be positive')
        if self.width % self.heads or self.width % self.groups or self.hidden % self.groups:
            raise ValueError('incompatible head/group dimensions')


class FFN(nn.Module):
    def __init__(self, c):
        super().__init__()
        self.groups, self.width, self.hidden = c.groups, c.width, c.hidden
        # One fused gate/up projection, including in the dense reference.
        if c.groups == 1:
            self.up_gate = nn.Linear(c.width, 2 * c.hidden, bias=False)
            self.down = nn.Linear(c.hidden, c.width, bias=False)
        else:
            self.up_gate = nn.Parameter(torch.empty(c.groups, c.width // c.groups,
                                                    2 * c.hidden // c.groups))
            self.down = nn.Parameter(torch.empty(c.groups, c.hidden // c.groups,
                                                 c.width // c.groups))
        perm = torch.arange(c.width)
        if c.shuffle:
            perm = perm.reshape(c.groups, -1).T.reshape(-1)
        self.register_buffer('permutation', perm, persistent=True)
        self.shuffle = c.shuffle

    def forward(self, x):
        if self.groups == 1:
            gate, up = self.up_gate(x).chunk(2, dim=-1)
            out = self.down(F.silu(gate) * up)
        else:
            z = x.reshape(*x.shape[:-1], self.groups, self.width // self.groups)
            gate, up = torch.einsum('...gi,gij->...gj', z, self.up_gate).chunk(2, -1)
            out = torch.einsum('...gi,gij->...gj', F.silu(gate) * up, self.down)
            out = out.reshape_as(x)
        return out.index_select(-1, self.permutation) if self.shuffle else out


class Attention(nn.Module):
    def __init__(self, c):
        super().__init__()
        self.heads = c.heads
        self.qkv = nn.Linear(c.width, 3 * c.width, bias=False)
        self.out = nn.Linear(c.width, c.width, bias=False)

    def forward(self, x, past=None, use_cache=False):
        b, t, d = x.shape
        q, k, v = self.qkv(x).reshape(b, t, 3, self.heads, d // self.heads).unbind(2)
        q, k, v = (u.transpose(1, 2) for u in (q, k, v))
        offset = 0 if past is None else past[0].shape[-2]
        if past is not None:
            k = torch.cat((past[0], k), dim=-2)
            v = torch.cat((past[1], v), dim=-2)
        # SDPA's rectangular is_causal mask is upper-left aligned. Cached
        # multi-token decoding needs an explicit offset mask instead.
        mask = None
        if offset and t > 1:
            mask = torch.arange(k.shape[-2], device=x.device)[None, :] <= (
                offset + torch.arange(t, device=x.device)[:, None])
        y = F.scaled_dot_product_attention(q, k, v, attn_mask=mask,
                                           is_causal=(offset == 0), dropout_p=0.0)
        y = self.out(y.transpose(1, 2).contiguous().reshape(b, t, d))
        return y, ((k, v) if use_cache else None)


class Block(nn.Module):
    def __init__(self, c):
        super().__init__()
        self.norm1 = nn.LayerNorm(c.width)
        self.attention = Attention(c)
        self.norm2 = nn.LayerNorm(c.width)
        self.ffn = FFN(c)

    def forward(self, x, past=None, use_cache=False):
        with torch.profiler.record_function('block.attention'):
            y, cache = self.attention(self.norm1(x), past, use_cache)
            x = x + y
        with torch.profiler.record_function('block.ffn'):
            x = x + self.ffn(self.norm2(x))
        return x, cache


class Decoder(nn.Module):
    def __init__(self, c):
        super().__init__()
        self.config = c
        self.tokens = nn.Embedding(c.vocab, c.width)
        self.positions = nn.Embedding(c.context, c.width)
        self.blocks = nn.ModuleList(Block(c) for _ in range(c.layers))
        self.norm = nn.LayerNorm(c.width)
        self.reset_parameters()

    def reset_parameters(self, seed=42):
        # Name-derived seeds give identical shared tensors across FFN arms,
        # independent of FFN shape or the order parameters are constructed.
        import hashlib
        for name, p in self.named_parameters():
            if p.ndim == 1:
                nn.init.ones_(p) if name.endswith('weight') else nn.init.zeros_(p)
            else:
                key = int.from_bytes(hashlib.sha256(f'{seed}:{name}'.encode()).digest()[:8], 'little')
                gen = torch.Generator(device=p.device).manual_seed(key)
                std = 0.02 / math.sqrt(2 * self.config.layers) if (
                    name.endswith('attention.out.weight') or '.ffn.down' in name) else 0.02
                nn.init.normal_(p, std=std, generator=gen)

    def forward(self, ids, past=None, use_cache=False, last_only=False):
        offset = 0 if past is None else past[0][0].shape[-2]
        if ids.shape[1] + offset > self.config.context:
            raise ValueError('requested context exceeds learned position table')
        positions = torch.arange(offset, offset + ids.shape[1], device=ids.device)
        x = self.tokens(ids) + self.positions(positions)
        caches = []
        for i, block in enumerate(self.blocks):
            x, cache = block(x, None if past is None else past[i], use_cache)
            if use_cache:
                caches.append(cache)
        x = self.norm(x[:, -1:] if last_only else x)
        with torch.profiler.record_function('output_head'):
            logits = F.linear(x, self.tokens.weight)
        return logits, (caches if use_cache else None)
