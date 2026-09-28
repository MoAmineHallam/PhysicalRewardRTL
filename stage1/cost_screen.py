"""Analytical FFN cost ledger; illustrative limits, never measured speedups."""
import argparse
import json
import math
from pathlib import Path
from .experiment import ARMS, configuration
from .model import Decoder
from .prior_controls import deployed_parameters


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args()
    rows=[]
    for arm in ARMS:
        c=configuration(arm);c.vocab=43;c.context=32;c.layers=1
        model=Decoder(c);ffn=model.blocks[0].ffn
        weights=deployed_parameters(ffn)
        # Counts equal leading MACs here because every stored deployment weight
        # participates once per token; no sparse routing/padding in these graphs.
        collective=None
        if arm.startswith('communication_'):collective=(c.groups-1)*c.rank*(32+16)
        if arm=='grouped':collective=0
        dense_partition=(4-1)*c.width*(16+32) if arm.startswith('dense') else None
        row=dict(arm=arm,ffn_weights=weights,leading_macs_per_token=weights,
                 hidden_nonlinearity_elements=c.hidden,
                 illustrative_cold_weight_bytes_int8=weights,
                 message_collective_link_bits=collective,
                 dense_four_cluster_collective_link_bits=dense_partition,
                 illustrative_256_mac_per_cycle_cycles=math.ceil(weights/256),
                 optimistic_cold_ffn_seconds={str(gbps):max(weights/(gbps*1e9),math.ceil(weights/256)/150e6)
                                             for gbps in [1,2,4]})
        rows.append(row)
    report=dict(scope='Analytical first-FFN ledger, not FPGA measurements or a cycle schedule.',
                assumptions={'clock_hz':150000000,'macs_per_cycle':256,'weight_bits':8,
                             'activation_message_bits':16,'reduction_bits':32,
                             'ddr_gigabytes_per_second_sweep':[1,2,4]},
                limitations=['Numerical formats and bandwidth are illustrative, not quality-validated or board-measured.',
                             'Cold weights streamed once per FFN invocation; assumes perfect compute/transfer overlap.',
                             'Lower bounds omit nonlinearities, scales, alignment, banking, control, DMA setup and other transformer operations.',
                             'Link bits describe one group topology. An optimized dense mapping may avoid that topology.',
                             'Prior controls require their own detailed collective/buffer schedules; null is unknown, not zero.',
                             'Equal-budget narrow dense and message FFNs have equal ideal cold-weight bandwidth floors.'],rows=rows)
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists():raise FileExistsError(out)
    out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
