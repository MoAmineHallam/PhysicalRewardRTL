<# Run the frozen Vivado-2026.1 infrastructure-stability gate V7. #>
param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repo = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$gate = Join-Path $repo "timing_closure_gate_v7"
$vivadoRoot = "C:\AMD\2026.1\Vivado"
$vivado = Join-Path $vivadoRoot "bin\vivado.bat"
$preflight = Join-Path $gate "preflight.tcl"
$status = Join-Path $gate "stability_launcher.status"
$log = Join-Path $gate "stability_launcher.log"
$notificationLog = Join-Path $gate "stability_notification.log"
$preflightStdout = Join-Path $gate "preflight.stdout.log"
$preflightStderr = Join-Path $gate "preflight.stderr.log"
$campaign = Join-Path $gate "stability_campaign_001"
$scratch = "C:\VGT7S001"
$preflightTemp = "C:\VGT7PFT"

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
    throw "Vivado 2026.1 launcher is missing: $vivado"
}
if (-not (Test-Path -LiteralPath 'C:\Xilinx\Vivado\2023.1' -PathType Container)) {
    throw "the retained side-by-side Vivado 2023.1 installation is missing"
}
git diff --quiet -- .gitattributes launch_timing_stability_v7.ps1 timing_closure_gate_v7 timing_closure_gate_v1/closure_synth.tcl timing_closure_gate_v4/stability_common.py timing_closure_gate_v4/stability_probe.sv timing_closure_gate_v5 timing_closure_gate_v6
if ($LASTEXITCODE -ne 0) {
    throw "the frozen V7 launcher/package has unstaged changes"
}
git diff --cached --quiet -- .gitattributes launch_timing_stability_v7.ps1 timing_closure_gate_v7 timing_closure_gate_v1/closure_synth.tcl timing_closure_gate_v4/stability_common.py timing_closure_gate_v4/stability_probe.sv timing_closure_gate_v5 timing_closure_gate_v6
if ($LASTEXITCODE -ne 0) {
    throw "the frozen V7 launcher/package has staged changes"
}
if (Test-Path -LiteralPath $campaign) {
    throw "V7 stability campaign already exists and cannot be overwritten: $campaign"
}
if (Test-Path -LiteralPath $scratch) {
    throw "V7 scratch root already exists and cannot be overwritten: $scratch"
}
if (Test-Path -LiteralPath $preflightTemp) {
    throw "V7 preflight temp root already exists: $preflightTemp"
}
if (Get-Process -Name vivado -ErrorAction SilentlyContinue) {
    throw "another Vivado process is already running"
}

Invoke-LoggedPython -PythonArgs @("-m", "unittest", "timing_closure_gate_v7.test_stability", "-v")
Invoke-LoggedPython -PythonArgs @((Join-Path $gate "freeze_package.py"), "--check")
Invoke-LoggedPython -PythonArgs @((Join-Path $gate "freeze_dependency_baseline.py"), "--check")

New-Item -ItemType Directory -Path $preflightTemp -ErrorAction Stop | Out-Null
$previousErrorAction = $ErrorActionPreference
try {
    $ErrorActionPreference = "Continue"
    & $vivado -mode batch -nojournal -nolog -notrace -tempDir $preflightTemp -source $preflight 1> $preflightStdout 2> $preflightStderr
    $preflightExit = $LASTEXITCODE
}
finally {
    $ErrorActionPreference = $previousErrorAction
}
if ($preflightExit -ne 0) {
    throw "Vivado 2026.1 non-synthesis preflight failed with exit code $preflightExit"
}
$preflightText = Get-Content -LiteralPath $preflightStdout -Raw
if ($preflightText -notmatch 'V7_PREFLIGHT_PASS version=2026\.1') {
    throw "Vivado 2026.1 preflight did not emit the frozen pass marker"
}
Invoke-LoggedPython -PythonArgs @((Join-Path $gate "freeze_dependency_baseline.py"), "--check")

@(
    "state=RUNNING"
    "started_utc=$([DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ'))"
    "vivado_root=$vivadoRoot"
    "vivado_version=2026.1"
    "preflight=PASS"
    "campaign=stability_campaign_001"
    "scratch_root=$scratch"
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
