<# Run the frozen V6 persistent-parent Vivado infrastructure gate. #>
param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$repo = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$gate = Join-Path $repo "timing_closure_gate_v6"
$vivado = "C:\Xilinx\Vivado\2023.1\bin\vivado.bat"
$status = Join-Path $gate "stability_launcher.status"
$log = Join-Path $gate "stability_launcher.log"
$notificationLog = Join-Path $gate "stability_notification.log"
$campaign = Join-Path $gate "stability_campaign_001"
$scratch = "C:\VGT6P001"

function Invoke-LoggedPython {
    param([string[]]$PythonArgs)
    $previousErrorAction = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        & python @PythonArgs *>> $log
        $nativeExit = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorAction
    }
    if ($nativeExit -ne 0) {
        throw "python $($PythonArgs -join ' ') failed with exit code $nativeExit"
    }
}

Set-Location -LiteralPath $repo
if (-not (Test-Path -LiteralPath $vivado -PathType Leaf)) {
    throw "Vivado 2023.1 launcher is missing: $vivado"
}
git diff --quiet -- .gitattributes launch_timing_stability_v6.ps1 timing_closure_gate_v6
if ($LASTEXITCODE -ne 0) {
    throw "the frozen V6 launcher/package has unstaged changes"
}
git diff --cached --quiet -- .gitattributes launch_timing_stability_v6.ps1 timing_closure_gate_v6
if ($LASTEXITCODE -ne 0) {
    throw "the frozen V6 launcher/package has staged changes"
}
if (Test-Path -LiteralPath $campaign) {
    throw "V6 campaign already exists and cannot be overwritten: $campaign"
}
if (Test-Path -LiteralPath $scratch) {
    throw "V6 scratch root already exists and cannot be overwritten: $scratch"
}
if (Get-Process -Name vivado -ErrorAction SilentlyContinue) {
    throw "another Vivado process is already running"
}
Invoke-LoggedPython -PythonArgs @("-m", "unittest", "timing_closure_gate_v6.test_stability")
Invoke-LoggedPython -PythonArgs @((Join-Path $gate "freeze_package.py"), "--check")
Invoke-LoggedPython -PythonArgs @((Join-Path $gate "freeze_dependency_baseline.py"), "--check")

@(
    "state=RUNNING"
    "started_utc=$([DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ'))"
    "campaign=stability_campaign_001"
    "scratch_root=$scratch"
    "parent_processes=1"
    "requested_in_memory_projects=40"
    "candidate_rtl_exposed=false"
) | Set-Content -LiteralPath $status -Encoding ascii

$exitCode = 1
$verdict = "ERROR"
try {
    Invoke-LoggedPython -PythonArgs @((Join-Path $gate "run_stability_gate.py"), "--vivado", $vivado, "--campaign", $campaign, "--scratch-root", $scratch)
    $exitCode = 0
    $attestation = Join-Path $campaign "stability_attestation.json"
    if (Test-Path -LiteralPath $attestation -PathType Leaf) {
        $verdict = (Get-Content -LiteralPath $attestation -Raw | ConvertFrom-Json).verdict
    }
}
catch {
    $_ | Out-String | Add-Content -LiteralPath $log -Encoding utf8
    $attestation = Join-Path $campaign "stability_attestation.json"
    if (Test-Path -LiteralPath $attestation -PathType Leaf) {
        $verdict = (Get-Content -LiteralPath $attestation -Raw | ConvertFrom-Json).verdict
    }
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
