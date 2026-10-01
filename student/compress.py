"""Deployment-faithful compression transforms for an RTL-generating student.

Two transforms are provided, both applied to an already-merged FP16 model so
that the evaluated network is exactly the network a weight-streaming decoder
would execute:

* ``quantize_linear_weights_``: symmetric round-to-nearest (RTN) weight-only
  quantization in groups along the input dimension, then dequantization back
  to the model dtype ("fake quantization").  Every value the model multiplies
  by is representable as ``int_b * scale`` with one scale per group, which is
  what an integer weight store plus per-group scales implements in hardware.
  Activations and the KV cache stay in the model dtype.

* ``restrict_output_vocabulary_``: adds a fixed mask to the output logits so
  that only a declared token set can be sampled.  Logits of kept tokens are
  unchanged, so sampling is identical to sampling from a head whose matrix
  contains only the kept rows (vocabulary trimming); the physical saving is
  accounted analytically from the kept-row count.

Neither transform consults a design, a policy outcome, or a measurement.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Sequence

import torch
from torch import nn


DEFAULT_TARGETS = ("q_proj", "k_proj", "v_proj", "o_proj",
                   "gate_proj", "up_proj", "down_proj")


class CompressionError(ValueError):
    """A requested transform cannot be applied faithfully."""


def quantize_weight(weight: torch.Tensor, bits: int, group_size: int) -> torch.Tensor:
    """Return the RTN fake-quantized copy of a 2-D weight ``[out, in]``.

    Each row is split into contiguous groups of ``group_size`` input columns.
    A group's scale is ``max|w| / qmax`` with ``qmax = 2**(bits-1) - 1``;
    integers are clamped to ``[-qmax, qmax]`` (symmetric, no zero point).
    """
    if weight.dim() != 2:
        raise CompressionError(f"expected a 2-D weight, got shape {tuple(weight.shape)}")
    if not 2 <= bits <= 8:
        raise CompressionError(f"bits must be in [2, 8], got {bits}")
    out_features, in_features = weight.shape
    if group_size <= 0 or in_features % group_size:
        raise CompressionError(
            f"input width {in_features} is not divisible by group size {group_size}")
    qmax = 2 ** (bits - 1) - 1
    w = weight.detach().to(torch.float32).reshape(out_features, -1, group_size)
    scale = w.abs().amax(dim=-1, keepdim=True) / qmax
    scale = torch.where(scale > 0, scale, torch.ones_like(scale))
    q = torch.clamp(torch.round(w / scale), -qmax, qmax)
    return (q * scale).reshape(out_features, in_features).to(weight.dtype)


def _target_linears(model: nn.Module, targets: Sequence[str]) -> List[tuple]:
    found = []
    for name, module in model.named_modules():
        if isinstance(module, nn.Linear) and name.rsplit(".", 1)[-1] in targets:
            found.append((name, module))
    return found


@torch.no_grad()
def quantize_linear_weights_(model: nn.Module, bits: int, group_size: int = 128,
                             targets: Sequence[str] = DEFAULT_TARGETS) -> Dict[str, object]:
    """Fake-quantize every targeted ``nn.Linear`` in place; return statistics.

    Raises if no target is found, so a renamed architecture cannot silently
    produce an uncompressed "quantized" model.  The output head and embeddings
    are deliberately untouched; report them separately.
    """
    layers = _target_linears(model, targets)
    if not layers:
        raise CompressionError(f"no linear layers named {tuple(targets)} were found")
    n_weights = 0
    sq_err = 0.0
    sq_ref = 0.0
    for _name, module in layers:
        original = module.weight.data
        quantized = quantize_weight(original, bits, group_size)
        diff = quantized.to(torch.float32) - original.to(torch.float32)
        sq_err += float(diff.pow(2).sum())
        sq_ref += float(original.to(torch.float32).pow(2).sum())
        n_weights += original.numel()
        module.weight.data.copy_(quantized)
    return {
        "bits": bits,
        "group_size": group_size,
        "targets": list(targets),
        "n_layers": len(layers),
        "n_weights": n_weights,
        "relative_rms_error": (sq_err / sq_ref) ** 0.5 if sq_ref else 0.0,
    }


def keep_ids_from_texts(tokenizer, texts: Iterable[str],
                        always_keep: Iterable[int] = (),
                        ascii_fallback: bool = True) -> List[int]:
    """Token ids that occur in ``texts`` plus ``always_keep`` and EOS/PAD.

    Use completions (generated RTL) from training data only, never evaluation
    designs, so the kept set is fixed before any outcome is observed.  With
    ``ascii_fallback`` every printable ASCII character's own token is kept, so
    an unseen identifier (a new design or port name) can still be spelled.
    """
    keep = set(int(i) for i in always_keep)
    for special in (tokenizer.eos_token_id, tokenizer.pad_token_id):
        if special is not None:
            keep.add(int(special))
    if ascii_fallback:
        for code in range(32, 127):
            keep.update(int(i) for i in
                        tokenizer(chr(code), add_special_tokens=False)["input_ids"])
        for char in ("\n", "\t"):
            keep.update(int(i) for i in tokenizer(char, add_special_tokens=False)["input_ids"])
    for text in texts:
        keep.update(int(i) for i in tokenizer(text, add_special_tokens=False)["input_ids"])
    return sorted(keep)


def restrict_output_vocabulary_(model: nn.Module, keep_ids: Sequence[int]):
    """Mask every logit outside ``keep_ids``; return the hook handle.

    The mask is a fixed additive tensor on the output head, so it composes with
    any sampler.  Kept logits are bit-identical to the unrestricted model.
    """
    head = model.get_output_embeddings()
    if head is None:
        raise CompressionError("model has no output embedding layer")
    vocab = head.weight.shape[0]
    keep = torch.as_tensor(sorted(set(int(i) for i in keep_ids)), dtype=torch.long)
    if keep.numel() == 0:
        raise CompressionError("keep_ids is empty")
    if int(keep.min()) < 0 or int(keep.max()) >= vocab:
        raise CompressionError(f"keep_ids fall outside the head's {vocab} rows")
    mask = torch.full((vocab,), float("-inf"), dtype=head.weight.dtype,
                      device=head.weight.device)
    mask[keep.to(mask.device)] = 0

    # Head rows beyond the tokenizer's vocabulary (Qwen pads its head) are never
    # in keep_ids and are therefore masked as well.
    def _hook(_module, _inputs, output):
        return output + mask.to(output.dtype)

    return head.register_forward_hook(_hook)
