"""Causal decoder and explicit FFN controls; no pretrained weights or RFT memory."""
from dataclasses import dataclass
from contextlib import nullcontext
import math
import torch
from torch import nn
from torch.nn import functional as F


def region(enabled, name):
    return torch.profiler.record_function(name) if enabled else nullcontext()


class StaticKV:
    """Inference-only storage for one layer; only the valid prefix is attended.

    Reset invalidates all entries without clearing memory. Truncate supports
    repeated fixed-context benchmarks; it cannot expose previously invalid slots.
    """
    def __init__(self, batch, heads, capacity, head_dim, device, dtype):
        if min(batch, heads, capacity, head_dim) <= 0:
            raise ValueError('cache dimensions must be positive')
        self.key = torch.empty(batch, heads, capacity, head_dim, device=device, dtype=dtype)
        self.value = torch.empty_like(self.key)
        self.length = 0

    @property
    def capacity(self):
        return self.key.shape[-2]

    def truncate(self, length=0):
        if not 0 <= length <= self.length:
            raise ValueError('cannot expose uninitialized cache entries')
        self.length = length

    def append(self, key, value):
        if torch.is_grad_enabled():
            raise RuntimeError('StaticKV is inference-only; use no_grad/inference_mode')
        if (key.shape != value.shape or key.shape[:2] != self.key.shape[:2]
                or key.shape[-1] != self.key.shape[-1]):
            raise ValueError('cache batch/head dimensions do not match')
        if any(t.dtype != self.key.dtype or t.device != self.key.device for t in (key, value)):
            raise ValueError('cache dtype/device does not match projected K/V')
        end = self.length + key.shape[-2]
        if end > self.capacity:
            raise ValueError('KV cache capacity exceeded')
        self.key[:, :, self.length:end].copy_(key)
        self.value[:, :, self.length:end].copy_(value)
        self.length = end
        return self.key[:, :, :end], self.value[:, :, :end]


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
        self.trace_regions = False

    def forward(self, x, past=None, use_cache=False):
        b, t, d = x.shape
        with region(self.trace_regions, 'attention.qkv'):
            q, k, v = self.qkv(x).reshape(b, t, 3, self.heads, d // self.heads).unbind(2)
        q, k, v = (u.transpose(1, 2) for u in (q, k, v))
        offset = 0 if past is None else (past.length if isinstance(past, StaticKV) else past[0].shape[-2])
        with region(self.trace_regions, 'attention.cache_update'):
            if isinstance(past, StaticKV):
                k, v = past.append(k, v)
            elif past is not None:
                k = torch.cat((past[0], k), dim=-2)
                v = torch.cat((past[1], v), dim=-2)
        # SDPA's rectangular is_causal mask is upper-left aligned. Cached
        # multi-token decoding needs an explicit offset mask instead.
        mask = None
        if offset and t > 1:
            mask = torch.arange(k.shape[-2], device=x.device)[None, :] <= (
                offset + torch.arange(t, device=x.device)[:, None])
        with region(self.trace_regions, 'attention.sdpa'):
            y = F.scaled_dot_product_attention(q, k, v, attn_mask=mask,
                                               is_causal=(offset == 0), dropout_p=0.0)
        with region(self.trace_regions, 'attention.output_projection'):
            y = self.out(y.transpose(1, 2).contiguous().reshape(b, t, d))
        cache = past if isinstance(past, StaticKV) else (k, v)
        return y, (cache if use_cache else None)


class Block(nn.Module):
    def __init__(self, c):
        super().__init__()
        self.norm1 = nn.LayerNorm(c.width)
        self.attention = Attention(c)
        self.norm2 = nn.LayerNorm(c.width)
        self.ffn = FFN(c)
        self.trace_regions = False

    def forward(self, x, past=None, use_cache=False):
        with region(self.trace_regions, 'block.attention'):
            y, cache = self.attention(self.norm1(x), past, use_cache)
            x = x + y
        with region(self.trace_regions, 'block.ffn'):
            normalized = self.norm2(x)
            with region(self.trace_regions, 'ffn.core'):
                y = self.ffn(normalized)
            x = x + y
        return x, cache


class Decoder(nn.Module):
    def __init__(self, c):
        super().__init__()
        self.config = c
        self.tokens = nn.Embedding(c.vocab, c.width)
        self.positions = nn.Embedding(c.context, c.width)
        self.blocks = nn.ModuleList(Block(c) for _ in range(c.layers))
        self.norm = nn.LayerNorm(c.width)
        self.trace_regions = False
        self.reset_parameters()

    def set_profiling(self, enabled):
        """Annotations are off during latency measurements and training."""
        for module in self.modules():
            if hasattr(module, 'trace_regions'):
                module.trace_regions = enabled

    def allocate_cache(self, batch, capacity=None):
        c = self.config
        capacity = c.context if capacity is None else capacity
        if not 0 < capacity <= c.context:
            raise ValueError('invalid KV cache capacity')
        p = self.tokens.weight
        return [StaticKV(batch, c.heads, capacity, c.width // c.heads, p.device, p.dtype)
                for _ in self.blocks]

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
        if past is not None and len(past) != len(self.blocks):
            raise ValueError('one cache entry required per layer')
        static = past is not None and isinstance(past[0], StaticKV)
        offset = 0 if past is None else (past[0].length if static else past[0][0].shape[-2])
        if static:
            if not use_cache or torch.is_grad_enabled():
                raise RuntimeError('static cache requires use_cache=True and disabled gradients')
            if any(not isinstance(p, StaticKV) or p.length != offset for p in past):
                raise ValueError('inconsistent per-layer static cache state')
            if any(offset + ids.shape[1] > p.capacity for p in past):
                raise ValueError('KV cache capacity exceeded')
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
        with region(self.trace_regions, 'output_head'):
            logits = F.linear(x, self.tokens.weight)
        return logits, (caches if use_cache else None)
