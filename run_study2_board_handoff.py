#!/usr/bin/env python3
"""Upload, run, retrieve, and provenance-check the sealed Study 2 board sweep.

The SSH password is read from ``PYNQ_PASSWORD`` (or prompted) and is never
written to an artifact.  The script refuses pre-existing local or remote result
files, uploads the exact sealed inputs, and verifies every downloaded hash.
"""

from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
import pathlib
import posixpath
import shlex
import sys

import paramiko


ROOT = pathlib.Path(__file__).resolve().parent
LOCAL = ROOT / "rtl" / "sealed_study2_board"
REMOTE_DEFAULT = "/home/xilinx/fpga_study2_board"
SUPPORT = (
    "sweep_catalog.py",
    "clock_sweep_fmax.py",
    "capture_waveforms.py",
    "score_candidate.py",
)


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def remote_quote(path: str) -> str:
    return shlex.quote(path)


def exec_checked(client: paramiko.SSHClient, command: str, stream: bool = False) -> str:
    _, stdout, stderr = client.exec_command(command, get_pty=stream)
    if stream:
        chunks = []
        for line in iter(stdout.readline, ""):
            print(line, end="", flush=True)
            chunks.append(line)
        error = stderr.read().decode("utf-8", errors="replace")
        if error:
            print(error, file=sys.stderr, end="")
    else:
        chunks = [stdout.read().decode("utf-8", errors="replace")]
        error = stderr.read().decode("utf-8", errors="replace")
    code = stdout.channel.recv_exit_status()
    if code:
        raise RuntimeError(
            f"remote command failed ({code}): {command}\n{error.strip()}"
        )
    return "".join(chunks)


def mkdirs(sftp: paramiko.SFTPClient, path: str) -> None:
    current = "/" if path.startswith("/") else ""
    for part in path.strip("/").split("/"):
        current = posixpath.join(current, part)
        try:
            sftp.stat(current)
        except OSError:
            sftp.mkdir(current)


def put(sftp: paramiko.SFTPClient, source: pathlib.Path, destination: str) -> None:
    if not source.is_file():
        raise RuntimeError(f"required local input is absent: {source}")
    mkdirs(sftp, posixpath.dirname(destination))
    sftp.put(str(source), destination)


def verify_local() -> tuple[dict, dict, pathlib.Path, pathlib.Path, pathlib.Path]:
    manifest_path = LOCAL / "selection_manifest.json"
    sels_path = LOCAL / "study2_board_sels.json"
    bit = LOCAL / "out" / "system_study2_board.bit"
    hwh = LOCAL / "out" / "system_study2_board.hwh"
    result = LOCAL / "catalog_fmax.json"
    for path in (manifest_path, sels_path, bit, hwh):
        if not path.is_file():
            raise RuntimeError(f"required local input is absent: {path}")
    if result.exists():
        raise RuntimeError(f"refusing pre-existing local board result: {result}")
    manifest = read_json(manifest_path)
    sels = read_json(sels_path)
    if manifest.get("schema") != "study2_board_selection/1":
        raise RuntimeError("unexpected Study 2 selection-manifest schema")
    if len(manifest.get("selections", [])) != 10 or len(sels) != 11:
        raise RuntimeError("Study 2 board inputs are not ten paired DUTs plus canary")
    outputs = manifest.get("generated_outputs", {})
    for key in ("dut_top", "build_tcl", "sels"):
        record = outputs.get(key, {})
        path = ROOT / record.get("path", "__missing__")
        if not path.is_file() or sha256(path) != record.get("sha256"):
            raise RuntimeError(f"sealed generated-output mismatch: {key}")
    for row in manifest["selections"]:
        for field, hash_field in (
            ("copied_rtl", "copied_rtl_sha256"),
            ("golden", "golden_sha256"),
        ):
            path = ROOT / row["provenance"][field]
            if not path.is_file() or sha256(path) != row["provenance"][hash_field]:
                raise RuntimeError(f"sealed selection mismatch: {row['entry']}/{field}")
    return manifest, sels, bit, hwh, result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="192.168.2.99")
    parser.add_argument("--user", default="xilinx")
    parser.add_argument("--remote-root", default=REMOTE_DEFAULT)
    parser.add_argument("--password-env", default="PYNQ_PASSWORD")
    args = parser.parse_args()
    password = os.environ.get(args.password_env) or getpass.getpass(
        f"Password for {args.user}@{args.host}: "
    )

    manifest, sels, bit, hwh, result = verify_local()
    remote = args.remote_root.rstrip("/")
    remote_result = posixpath.join(remote, "rtl/sealed_study2_board/catalog_fmax.json")
    remote_bit = posixpath.join(
        remote, "rtl/sealed_study2_board/out/system_study2_board.bit"
    )
    remote_hwh = posixpath.splitext(remote_bit)[0] + ".hwh"
    remote_sels = posixpath.join(
        remote, "rtl/sealed_study2_board/study2_board_sels.json"
    )
    remote_manifest = posixpath.join(
        remote, "rtl/sealed_study2_board/selection_manifest.json"
    )

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        args.host,
        username=args.user,
        password=password,
        timeout=10,
        look_for_keys=False,
        allow_agent=False,
    )
    try:
        exec_checked(client, f"test ! -e {remote_quote(remote_result)}")
        sftp = client.open_sftp()
        try:
            for name in SUPPORT:
                put(sftp, ROOT / name, posixpath.join(remote, name))
            put(sftp, bit, remote_bit)
            put(sftp, hwh, remote_hwh)
            put(sftp, LOCAL / "study2_board_sels.json", remote_sels)
            put(sftp, LOCAL / "selection_manifest.json", remote_manifest)
            for meta in sels.values():
                golden = ROOT / meta["golden"]
                put(sftp, golden, posixpath.join(remote, meta["golden"]))
        finally:
            sftp.close()

        measurement = manifest["measurement"]
        command = " ".join(
            (
                "set -eu; cd", remote_quote(remote), "; sudo -n",
                "/usr/local/share/pynq-venv/bin/python3 sweep_catalog.py",
                "--bit", remote_quote(posixpath.relpath(remote_bit, remote)),
                "--sels", remote_quote(posixpath.relpath(remote_sels, remote)),
                "--lo", str(measurement["lo_mhz"]),
                "--hi", str(measurement["hi_mhz"]),
                "--step", str(measurement["step_mhz"]),
                "--runs", str(measurement["runs"]),
                "--depth", str(measurement["depth"]),
                "--n-score", str(measurement["n_score"]),
                "--max-shift", str(measurement["max_shift"]),
                "--threshold", str(measurement["similarity_threshold"]),
                "--canary-margin", str(measurement["canary_margin_mhz"]),
                "--out", remote_quote(posixpath.relpath(remote_result, remote)),
            )
        )
        exec_checked(client, command, stream=True)
        sftp = client.open_sftp()
        try:
            sftp.get(remote_result, str(result))
        finally:
            sftp.close()
    finally:
        client.close()

    data = read_json(result)
    expected_hashes = {
        "bitstream_sha256": sha256(bit),
        "hwh_sha256": sha256(hwh),
        "sels_sha256": sha256(LOCAL / "study2_board_sels.json"),
        "selection_manifest_sha256": sha256(LOCAL / "selection_manifest.json"),
    }
    if data.get("schema_version") != 2 or data.get("measurement_kind") != "live_pynq_clock_sweep":
        raise RuntimeError("downloaded result has the wrong schema or measurement kind")
    for key, expected in expected_hashes.items():
        if data.get("provenance", {}).get(key) != expected:
            raise RuntimeError(f"downloaded board provenance mismatch: {key}")
    complete = (
        len(data.get("sels", {})) == 11
        and len(data.get("raw_runs", [])) == manifest["measurement"]["runs"]
        and data.get("summary", {}).get("all_entries_have_fmax") is True
    )
    print(f"provenance-checked live result: {result}")
    if not complete:
        print("RESULT INCOMPLETE: retain the artifact but make no silicon headline claim")
        return 2
    print("Study 2 live-board sweep is complete; scientific gates still require audit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
