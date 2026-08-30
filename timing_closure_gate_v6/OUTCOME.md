# V6 outcome

V6 is permanently **FAIL**.  The first isolated in-memory project completed
the full constrained synth/place/route flow with WNS 7.501 ns, 51 setup paths,
zero unconstrained paths, clean routing, and clean project/file boundaries.
During synthesis of the second isolated project, Vivado's ABC stage then
failed to open an internal realtime `genlib` temporary path.  The parent exited
with code 3; no second result was published.  The full raw dependency guards
before and after the session matched the frozen baseline.

The persistent-parent architecture therefore does not repair this host.  No
Study-2 candidate RTL was exposed, and V6 must not be rerun or amended into a
pass.  The raw attestation SHA-256 is
`de502c2e9d6e7832f222a5555986a9eddabf442a87ed4e1f8c562bd501339eca`.
