# Structured reference attribution

The rectangular Monarch layout in `structured.py` follows the two block-diagonal
factors, intermediate permutation, and output permutation in
[HazyResearch/fly](https://github.com/HazyResearch/fly) (formerly `monarch`), pinned
at commit `6b73449a6b3e228af9e4afe4f153a384e9b537b9` (2023-02-21).

Primary code consulted:

- [MonarchLinear](https://github.com/HazyResearch/fly/blob/6b73449a6b3e228af9e4afe4f153a384e9b537b9/src/models/layers/monarch_linear.py)
- [Block-diagonal butterfly multiplication and references](https://github.com/HazyResearch/fly/blob/6b73449a6b3e228af9e4afe4f153a384e9b537b9/src/models/layers/blockdiag_butterfly_multiply.py)

The upstream license is [Apache-2.0](third_party/fly/LICENSE). Source URLs and
download hashes are in [source.json](third_party/fly/source.json).

This local adaptation uses ordinary autograd/einsum and supports arbitrary leading
dimensions with explicit zero-padding/cropping. It does not import the upstream
custom backward or optimized kernels. Gate/up uses one rectangular projection
with twice the hidden width; down uses a separate rectangular projection. These
choices adapt an established linear operator to our gated causal decoder; they
are not a reproduction of the paper's full network or a new operator claim.

The low-rank control trains two ordinary factors from scratch. It is not SVD-LLM,
whitening-based post-training compression, or a reproduction of SkipCat. Its
shared input basis for the fused gate/up projection is counted explicitly.

`fan_matched` is a disclosed initialization control: factorized first projections
have unit expected variance gain and second projections match the dense
reference's expected projection gain. This differs from the upstream layer's
Kaiming initialization. It matches a variance calculation, not the whole
activation distribution or expressive capacity. Retain legacy-initialization
ablations and inspect gradients/activation statistics before interpreting quality.
