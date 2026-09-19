RF versus SFT: worked RTL example and archived-result reproduction
Mohamed Amine Hallam, Kuo-Kun Tseng, and Wenjie Pei
School of Computer Science and Technology, Harbin Institute of Technology
Contact: 25sf51027@stu.hit.edu.cn
Prepared September 19, 2026

This package accompanies the supplementary material for Physical-Reward
Policy Optimization for Accelerator RTL. It lets a reader inspect two actual
generated FIR implementations, simulate them against the shared reference,
and reproduce the completed post-primary RF versus SFT comparison. The
SHA256SUMS.json manifest protects the packaged inputs against accidental
changes; it is not a signature or independent certification of the experiments.

The analysis uses Python 3.12 and NumPy 2.2.6. No GPU, model download, Vivado
license, network service, or repository checkout is needed after installation.
The optional simulation also requires Icarus Verilog, with both iverilog and
vvp on PATH. The package has been tested on Windows; its Python commands and
temporary-directory simulation flow are also intended for Linux and macOS.
Platform-specific testing is stated in the accompanying validation record.

From the extracted package directory, create an isolated environment with
python -m venv .venv
On Windows, install the dependency and run the analysis with
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python run_demo.py
On Linux or macOS, use .venv/bin/python in both commands instead.
To execute the RTL pair as well, append --simulate to the final command.
No command starts training or a physical implementation job.

Start the walkthrough by opening demo/sft.sv and demo/rf.sv. Both implement
fir13_v6_8b. The SFT candidate stores delayed inputs and computes their weighted
sum before the output register. The RF candidate stores partial weighted sums
in a transposed FIR structure. The simulator compares each candidate with the
same reference on two stimulus streams and repeated reset episodes, allowing
one common latency. This is simulation evidence, not formal equivalence.
demo/specification.json retains the original prompt and design parameters.
demo/demo.json gives the exact source draw, hash, latency, multiplicity, and
physical result for each candidate. demo/reports contains the archived passing
boundary reports. The example is selected after the experiments to explain
the structure: each arm contributes its most frequent passing exact RTL string
on this design, with a hash tie-break. It is not a typical-effect estimate.

run_demo.py checks every input hash, all 1,920 draw identities, all-draw
denominators, the measured physical endpoints, the paired design-bootstrap
interval, and measured best-of-N results. It writes outputs/reproduced.json
and outputs/comparison.csv. With --simulate, outputs/simulation.json retains
the simulation evidence. A successful run prints PASS and the following
rounded values: SFT utility 34.24556213 MHz, 538/960 passing draws; RF utility
81.95118340 MHz, 449/960 passing draws. RF minus SFT is 47.70562127 MHz,
with a checkpoint-conditional interval [29.99689882, 64.12540343] MHz.
The FIR examples measure 52.87195940 MHz for SFT and 230.33430866 MHz for RF.
Expected run times are measured in the accompanying validation record.

data/draws retains every generated draw in the two included arms, including
failures and their raw oracle evidence. data/physical contains the terminal
physical records for every passing candidate required by those draws.
research contains the unchanged shared functional gate, reference oracle, and
catalog code used for simulation. provenance retains the campaign protocol,
original manifest, and the selection/scope record. The complete campaign also
had a DPO arm; this package reproduces only the requested RF versus SFT
contrast and does not establish a comparison with an external method.

The new experiment uses 20 previously used designs, 48 fresh draws per arm
and design, two generation replicates from one SFT checkpoint, and RF training
seeds three and four from the earlier extension. Physical measurements use
Vivado 2026.1 and bounded routed setup-period search. A failed functional or
physical result contributes zero. This endpoint is not full timing signoff.
The bootstrap resamples designs within family and regime; it does not estimate
variation from retraining the entire pipeline. The worked pair illustrates a
structural difference, not invention of an unseen circuit or a causal ablation.

This is archived-output reproducibility with a runnable functional demo.
Model weights, training data needed for full retraining, and the complete raw
Vivado trial directories are outside this package. The main paper's original
primary result uses a different measurement contract and is not recomputed
here. No open-source license has been assigned by the authors in this package.
Package size and file hashes are recorded in the delivery manifest.
