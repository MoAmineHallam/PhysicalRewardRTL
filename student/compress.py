"""Deployment-faithful compression transforms for an RTL-generating student.

All transforms are applied to an already-merged FP16 model so that the
evaluated network is exactly the network a weight-streaming decoder would
execute:

* ``quantize_linear_weights_``: symmetric round-to-nearest (RTN) weight-only
  quantization in groups along the input dimension, then dequantization back
  to the model dtype ("fake quantization").  Every value the model multiplies
  by is representable as ``int_b * scale`` with one scale per group, which is
  what an integer weight store plus per-group scales implements in hardware.
  Activations and the KV cache stay in the model dtype.

* ``gptq_quantize_model_``: the same integer format, but each layer's integers
  are chosen by GPTQ (Frantar et al., ICLR 2023) to minimise the layer's output
  error on calibration activations.  Decoder layers are processed in order, so
  each layer is calibrated on inputs produced by the already-quantized layers
  before it, as in the reference algorithm.

* ``restrict_output_vocabulary_``: adds a fixed mask to the output logits so
  that only a declared token set can be sampled.  Logits of kept tokens are
  unchanged, so sampling is identical to sampling from a head whose matrix
  contains only the kept rows (vocabulary trimming); the physical saving is
  accounted analytically from the kept-row count.

No transform consults an evaluation design, a policy outcome, or a measurement.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Sequence, Tuple

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
        "method": "rtn",
        "bits": bits,
        "group_size": group_size,
        "targets": list(targets),
        "n_layers": len(layers),
        "n_weights": n_weights,
        "relative_rms_error": (sq_err / sq_ref) ** 0.5 if sq_ref else 0.0,
    }


def gptq_quantize_weight(weight: torch.Tensor, hessian: torch.Tensor, bits: int,
                         group_size: int, percdamp: float = 0.01,
                         block_size: int = 128) -> Tuple[torch.Tensor, torch.Tensor]:
    """GPTQ-quantize a 2-D weight ``[out, in]`` given ``H = X^T X`` over its inputs.

    Uses the same symmetric per-group integer format as ``quantize_weight``.
    A group's scale is fixed from the error-compensated weights when the group
    starts.  Returns ``(dequantized_weight, scales[out, in // group_size])``.
    """
    if weight.dim() != 2:
        raise CompressionError(f"expected a 2-D weight, got shape {tuple(weight.shape)}")
    if not 2 <= bits <= 8:
        raise CompressionError(f"bits must be in [2, 8], got {bits}")
    rows, cols = weight.shape
    if group_size <= 0 or cols % group_size:
        raise CompressionError(
            f"input width {cols} is not divisible by group size {group_size}")
    if hessian.shape != (cols, cols):
        raise CompressionError(f"Hessian shape {tuple(hessian.shape)} != ({cols}, {cols})")
    block_size = max(group_size, (block_size // group_size) * group_size)
    qmax = 2 ** (bits - 1) - 1

    W = weight.detach().to(torch.float32).clone()
    H = hessian.detach().to(torch.float32).clone()
    dead = torch.diag(H) == 0
    H[dead, dead] = 1
    W[:, dead] = 0
    H += percdamp * torch.mean(torch.diag(H)) * torch.eye(cols, device=H.device)
    Hinv = torch.linalg.cholesky(torch.cholesky_inverse(torch.linalg.cholesky(H)),
                                 upper=True)

    Q = torch.zeros_like(W)
    scales = torch.zeros(rows, cols // group_size, device=W.device)
    for i1 in range(0, cols, block_size):
        i2 = min(i1 + block_size, cols)
        W1 = W[:, i1:i2].clone()
        Err1 = torch.zeros_like(W1)
        Hinv1 = Hinv[i1:i2, i1:i2]
        for i in range(i2 - i1):
            col = i1 + i
            if col % group_size == 0:
                group = W1[:, i:i + group_size]
                scale = group.abs().amax(dim=1) / qmax
                scale = torch.where(scale > 0, scale, torch.ones_like(scale))
                scales[:, col // group_size] = scale
            w = W1[:, i]
            q = torch.clamp(torch.round(w / scale), -qmax, qmax) * scale
            Q[:, col] = q
            err = (w - q) / Hinv1[i, i]
            W1[:, i:] -= err.unsqueeze(1) @ Hinv1[i, i:].unsqueeze(0)
            Err1[:, i] = err
        W[:, i2:] -= Err1 @ Hinv[i1:i2, i2:]
    return Q.to(weight.dtype), scales


class _StopForward(Exception):
    pass


def _decoder_layers(model: nn.Module) -> nn.ModuleList:
    inner = getattr(model, "model", None)
    layers = getattr(inner, "layers", None)
    if not isinstance(layers, nn.ModuleList) or not len(layers):
        raise CompressionError("expected a decoder with model.model.layers")
    return layers


@torch.no_grad()
def gptq_quantize_model_(model: nn.Module, calibration: Sequence[torch.Tensor],
                         bits: int, group_size: int = 128, percdamp: float = 0.01,
                         targets: Sequence[str] = DEFAULT_TARGETS) -> Dict[str, object]:
    """GPTQ-quantize every targeted linear layer in place, one decoder layer at a time.

    ``calibration`` holds 1-D token-id tensors.  For decoder layer ``k`` the
    calibration set is re-run through layers ``0..k`` (already quantized) and
    stopped there, so layer ``k`` sees the inputs it will see at deployment.
    """
    if not calibration:
        raise CompressionError("GPTQ needs calibration sequences")
    layers = _decoder_layers(model)
    device = next(model.parameters()).device
    was_caching = getattr(model.config, "use_cache", None)
    model.config.use_cache = False
    n_layers = n_weights = 0
    sq_err = sq_ref = 0.0
    try:
        for layer in layers:
            linears = [(name, module) for name, module in layer.named_modules()
                       if isinstance(module, nn.Linear)
                       and name.rsplit(".", 1)[-1] in targets]
            if not linears:
                continue
            hessians = {name: torch.zeros(m.in_features, m.in_features,
                                          device=device, dtype=torch.float32)
                        for name, m in linears}
            handles = []
            for name, module in linears:
                def _collect(_m, inputs, _name=name):
                    x = inputs[0].detach().reshape(-1, inputs[0].shape[-1]).to(torch.float32)
                    hessians[_name] += x.T @ x
                handles.append(module.register_forward_pre_hook(_collect))

            def _stop(_m, _i, _o):
                raise _StopForward

            handles.append(layer.register_forward_hook(_stop))
            try:
                for ids in calibration:
                    try:
                        model(ids.reshape(1, -1).to(device))
                    except _StopForward:
                        pass
            finally:
                for handle in handles:
                    handle.remove()
            for name, module in linears:
                original = module.weight.data
                quantized, _scales = gptq_quantize_weight(
                    original, hessians[name], bits, group_size, percdamp)
                diff = quantized.to(torch.float32) - original.to(torch.float32)
                sq_err += float(diff.pow(2).sum())
                sq_ref += float(original.to(torch.float32).pow(2).sum())
                n_weights += original.numel()
                module.weight.data.copy_(quantized)
                n_layers += 1
            del hessians
    finally:
        if was_caching is not None:
            model.config.use_cache = was_caching
    if not n_layers:
        raise CompressionError(f"no linear layers named {tuple(targets)} were found")
    return {
        "method": "gptq",
        "bits": bits,
        "group_size": group_size,
        "percdamp": percdamp,
        "targets": list(targets),
        "n_layers": n_layers,
        "n_weights": n_weights,
        "n_calibration_sequences": len(calibration),
        "n_calibration_tokens": int(sum(int(t.numel()) for t in calibration)),
        "relative_rms_weight_change": (sq_err / sq_ref) ** 0.5 if sq_ref else 0.0,
    }


def calibration_from_rows(tokenizer, rows: Sequence[dict], n: int, max_len: int,
                          seed: int, exclude_designs: Iterable[str] = ()) -> List[torch.Tensor]:
    """Token-id sequences rendered exactly as SFT saw them: chat prompt + completion.

    ``rows`` are corpus records with ``prompt``/``completion`` (and ``design``).
    Rows naming an excluded design raise, so evaluation designs cannot leak
    into calibration.  Selection is a seeded shuffle; it never looks at outcomes.
    """
    import random
    excluded = set(exclude_designs)
    leaks = sorted({row.get("design") for row in rows if row.get("design") in excluded})
    if leaks:
        raise CompressionError(f"calibration corpus contains evaluation designs: {leaks}")
    order = list(range(len(rows)))
    random.Random(seed).shuffle(order)
    out = []
    for index in order[:n]:
        row = rows[index]
        if getattr(tokenizer, "chat_template", None):
            prompt = tokenizer.apply_chat_template(
                [{"role": "user", "content": row["prompt"]}],
                tokenize=False, add_generation_prompt=True)
        else:
            prompt = row["prompt"] + "\n"
        text = prompt + row["completion"].rstrip() + (tokenizer.eos_token or "")
        ids = tokenizer(text, add_special_tokens=False)["input_ids"][:max_len]
        out.append(torch.tensor(ids, dtype=torch.long))
    if len(out) < n:
        raise CompressionError(f"requested {n} calibration rows, corpus has {len(out)}")
    return out


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
