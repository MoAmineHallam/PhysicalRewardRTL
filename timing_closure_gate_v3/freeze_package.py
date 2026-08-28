#!/usr/bin/env python3

import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PROTOCOL = HERE / 'preregistration.json'
MANIFEST = HERE / 'manifest.json'
MANIFEST_SHA = HERE / 'manifest.sha256'
V2_ATTESTATION_SHA = '10625e4104341efcdfb21efd3b2983d5e12ba537cb33743bc95dc8196e061ed0'

PACKAGE_INPUTS = (
    '.gitattributes',
    'launch_timing_stability_v3.ps1',
    'timing_closure_gate_v3/README.md',
    'timing_closure_gate_v3/common.py',
    'timing_closure_gate_v3/dependency_baseline.json',
    'timing_closure_gate_v3/freeze_dependency_baseline.py',
    'timing_closure_gate_v3/freeze_package.py',
    'timing_closure_gate_v3/run_stability_gate.py',
    'timing_closure_gate_v3/stability_common.py',
    'timing_closure_gate_v3/stability_probe.sv',
    'timing_closure_gate_v3/test_stability.py',
    'timing_closure_gate_v3/tempdir_diagnostic/README.md',
    'timing_closure_gate_v3/tempdir_diagnostic/attempt_01_launcher.stderr.log',
    'timing_closure_gate_v3/tempdir_diagnostic/attempt_02_vivado.stderr.log',
    'timing_closure_gate_v3/tempdir_diagnostic/attempt_02_vivado.stdout.log',
    'timing_closure_gate_v3/tempdir_diagnostic/attempt_02_vivado_result.json',
    'timing_closure_gate_v2/stability_campaign_001/stability_attestation.json',
    'timing_closure_gate_v2/stability_campaign_001/stability_attestation.sha256',
    'timing_closure_gate_v1/manifest.json',
    'timing_closure_gate_v1/manifest.sha256',
    'timing_closure_gate_v1/closure_synth.tcl',
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def encoded(value):
    text = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return (text + '\n').encode('utf-8')


def protocol():
    return {
        'schema_version': 3,
        'study_id': 'timing_closure_gate_v3',
        'frozen_date': '2026-08-28',
        'candidate_boundary': {
            'v1_manifest_sha256': '2e0674f96c57be3864a6fab7683b0edc76f732762f78547d5e6a3e8efc17e194',
            'candidate_count': 10,
            'selection_changes': 'none',
            'reuse_v1_or_v2_candidate_outcomes': False,
        },
        'v2_boundary': {
            'attestation_sha256_raw': V2_ATTESTATION_SHA,
            'verdict': 'FAIL after nine valid first attempts; synthetic run 10 could not read a generated realtime Tcl',
            'study2_candidate_rtl_exposed': False,
            'restart_v2': False,
        },
        'unchanged_science': {
            'device': 'xc7z020clg400-1',
            'vivado': '2023.1',
            'closure_tcl': 'timing_closure_gate_v1/closure_synth.tcl',
            'constraints_search_failure_scoring_thresholds': 'identical to v1',
        },
        'infrastructure_amendment': {
            'scratch_root': 'C:/VGT3S001',
            'unique_work_and_temp_directory_per_process': True,
            'explicit_vivado_tempdir': True,
            'candidate_artifacts_remain_under_repository': True,
        },
        'synthetic_gate': {
            'required_consecutive_first_attempts': 20,
            'retry_count': 0,
            'full_synth_place_route': True,
            'dependency_guard_reads_before_and_after': 3,
            'pass_rule': 'all 20 measurements valid with unchanged dependencies',
            'failure_rule': 'freeze FAIL and block every Study-2 candidate',
        },
        'stop_rules': [
            'Do not launch a Study-2 candidate before a frozen v3 PASS attestation.',
            'Do not reuse a v1 or v2 candidate measurement.',
            'Do not overwrite the v3 campaign or scratch root.',
            'Do not change this package after the first v3 synthetic launch.',
        ],
    }


def manifest(protocol_value):
    rows = []
    for relative in PACKAGE_INPUTS:
        path = ROOT / relative
        rows.append({'path': relative, 'bytes': path.stat().st_size,
                     'sha256_raw': sha(path)})
    rows.append({'path': PROTOCOL.relative_to(ROOT).as_posix(),
                 'bytes': len(encoded(protocol_value)),
                 'sha256_raw': hashlib.sha256(encoded(protocol_value)).hexdigest()})
    return {'schema_version': 1, 'study_id': 'timing_closure_gate_v3',
            'hash_domain': 'raw bytes', 'files': rows}


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--write', action='store_true')
    mode.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if sha(ROOT / 'timing_closure_gate_v2/stability_campaign_001/stability_attestation.json') != V2_ATTESTATION_SHA:
        raise RuntimeError('v2 failure attestation changed')
    pvalue = protocol()
    mvalue = manifest(pvalue)
    if args.write:
        if PROTOCOL.exists() or MANIFEST.exists() or MANIFEST_SHA.exists():
            raise RuntimeError('refusing to overwrite frozen v3 package')
        PROTOCOL.write_bytes(encoded(pvalue))
        MANIFEST.write_bytes(encoded(mvalue))
        MANIFEST_SHA.write_bytes((sha(MANIFEST) + '  manifest.json\n').encode('ascii'))
    else:
        if PROTOCOL.read_bytes() != encoded(pvalue):
            raise RuntimeError('v3 preregistration changed')
        if MANIFEST.read_bytes() != encoded(mvalue):
            raise RuntimeError('v3 package manifest changed')
        if MANIFEST_SHA.read_text(encoding='ascii').split()[0] != sha(MANIFEST):
            raise RuntimeError('v3 manifest checksum changed')
    print('PASS v3_manifest_sha256=' + sha(MANIFEST))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
