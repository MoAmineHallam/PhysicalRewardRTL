<# Operational wrapper for the frozen timing_closure_gate_v1 pilot. #>
param(
    [switch]$Resume,
    [switch]$PreflightOnly
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repo = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$gate = Join-Path $repo "timing_closure_gate_v1"
$status = Join-Path $gate "pilot_launcher.status"
$log = Join-Path $gate "pilot_launcher.log"
$notificationLog = Join-Path $gate "pilot_notification.log"
$vivado = "C:\Xilinx\Vivado\2023.1\bin\vivado.bat"
$frozenCommit = "b9f419f0f42b69d1488eaeffe26de845509b0997"
$frozenManifest = "2e0674f96c57be3864a6fab7683b0edc76f732762f78547d5e6a3e8efc17e194"

Set-Location -LiteralPath $repo

if (-not (Test-Path -LiteralPath $vivado -PathType Leaf)) {
    throw "Vivado 2023.1 launcher is missing: $vivado"
}
if ((git cat-file -t $frozenCommit 2>$null) -ne "commit") {
    throw "Frozen timing-gate commit is unavailable: $frozenCommit"
}
git diff --quiet $frozenCommit -- timing_closure_gate_v1
if ($LASTEXITCODE -ne 0) {
    throw "timing_closure_gate_v1 differs from frozen commit $frozenCommit"
}
git diff --cached --quiet $frozenCommit -- timing_closure_gate_v1
if ($LASTEXITCODE -ne 0) {
    throw "staged timing_closure_gate_v1 changes exist"
}

$manifestLine = (Get-Content -LiteralPath (Join-Path $gate "manifest.sha256") -Raw).Trim()
if ($manifestLine -ne "$frozenManifest  manifest.json") {
    throw "Frozen manifest line changed: $manifestLine"
}

& python (Join-Path $gate "generate_manifest.py") --check *>> $log
if ($LASTEXITCODE -ne 0) { throw "manifest verification failed" }
& python (Join-Path $gate "run_preflight.py") --check *>> $log
if ($LASTEXITCODE -ne 0) { throw "synthetic Vivado preflight verification failed" }

if (-not $Resume -and (Test-Path -LiteralPath (Join-Path $gate "results"))) {
    throw "results already exist; use -Resume only after auditing the partial ledger"
}
if (Get-Process -Name vivado -ErrorAction SilentlyContinue) {
    throw "another Vivado process is already running"
}
if ($PreflightOnly) {
    Write-Output "PRECHECK PASS: $frozenManifest"
    exit 0
}

@(
    "state=RUNNING"
    "started_utc=$([DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ'))"
    "pid=$PID"
    "frozen_commit=$frozenCommit"
    "manifest_sha256=$frozenManifest"
) | Set-Content -LiteralPath $status -Encoding ascii

$runExit = 1
$validatorExit = 2
$verdict = "INCOMPLETE"
try {
    & python (Join-Path $gate "run_closure.py") --vivado $vivado *>> $log
    $runExit = $LASTEXITCODE
    if ($runExit -eq 0) {
        & python (Join-Path $gate "validate_gate.py") --scope pilot *>> $log
        $validatorExit = $LASTEXITCODE
        $gateResult = Join-Path $gate "results\pilot_gate.json"
        if (Test-Path -LiteralPath $gateResult -PathType Leaf) {
            $verdict = (Get-Content -LiteralPath $gateResult -Raw | ConvertFrom-Json).verdict
        }
    }
}
catch {
    $_ | Out-String | Add-Content -LiteralPath $log -Encoding utf8
}
finally {
    @(
        "state=FINISHED"
        "run_exit_code=$runExit"
        "validator_exit_code=$validatorExit"
        "verdict=$verdict"
        "ended_utc=$([DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ'))"
    ) | Add-Content -LiteralPath $status -Encoding ascii

    & ssh adam40 "bash /home/adam/mas/mas/notify_correctness_done.sh" *> $notificationLog
}

if ($runExit -ne 0) { exit $runExit }
exit $validatorExit
