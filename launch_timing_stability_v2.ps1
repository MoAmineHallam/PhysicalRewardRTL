<# Run the frozen pre-candidate Vivado infrastructure-stability gate. #>
param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repo = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$gate = Join-Path $repo "timing_closure_gate_v2"
$vivado = "C:\Xilinx\Vivado\2023.1\bin\vivado.bat"
$status = Join-Path $gate "stability_launcher.status"
$log = Join-Path $gate "stability_launcher.log"
$notificationLog = Join-Path $gate "stability_notification.log"
$campaign = Join-Path $gate "stability_campaign_001"

Set-Location -LiteralPath $repo
if (-not (Test-Path -LiteralPath $vivado -PathType Leaf)) {
    throw "Vivado 2023.1 launcher is missing: $vivado"
}
git diff --quiet -- .gitattributes launch_timing_stability_v2.ps1 timing_closure_gate_v2
if ($LASTEXITCODE -ne 0) {
    throw "the frozen v2 launcher/package has unstaged changes"
}
git diff --cached --quiet -- .gitattributes launch_timing_stability_v2.ps1 timing_closure_gate_v2
if ($LASTEXITCODE -ne 0) {
    throw "the frozen v2 launcher/package has staged changes"
}
if (Test-Path -LiteralPath $campaign) {
    throw "stability campaign already exists and cannot be overwritten: $campaign"
}
if (Get-Process -Name vivado -ErrorAction SilentlyContinue) {
    throw "another Vivado process is already running"
}
& python -m unittest timing_closure_gate_v2.test_stability *>> $log
if ($LASTEXITCODE -ne 0) { throw "v2 CPU-only tests failed" }
& python (Join-Path $gate "audit_v1_abort.py") --check *>> $log
if ($LASTEXITCODE -ne 0) { throw "v1 failure/abort attestation changed" }
& python (Join-Path $gate "freeze_dependency_baseline.py") --check *>> $log
if ($LASTEXITCODE -ne 0) { throw "raw Vivado dependency baseline changed" }

@(
    "state=RUNNING"
    "started_utc=$([DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ'))"
    "campaign=stability_campaign_001"
    "candidate_rtl_exposed=false"
) | Set-Content -LiteralPath $status -Encoding ascii

$exitCode = 1
$verdict = "ERROR"
try {
    & python (Join-Path $gate "run_stability_gate.py") --vivado $vivado --campaign $campaign *>> $log
    $exitCode = $LASTEXITCODE
    $attestation = Join-Path $campaign "stability_attestation.json"
    if (Test-Path -LiteralPath $attestation -PathType Leaf) {
        $verdict = (Get-Content -LiteralPath $attestation -Raw | ConvertFrom-Json).verdict
    }
}
catch {
    $_ | Out-String | Add-Content -LiteralPath $log -Encoding utf8
}
finally {
    @(
        "state=FINISHED"
        "exit_code=$exitCode"
        "verdict=$verdict"
        "ended_utc=$([DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ'))"
    ) | Add-Content -LiteralPath $status -Encoding ascii
    & ssh adam40 "bash /home/adam/mas/mas/notify_correctness_done.sh" *> $notificationLog
}

exit $exitCode
