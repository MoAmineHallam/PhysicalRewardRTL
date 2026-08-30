<# Run the frozen V5 post-restart Vivado infrastructure-stability gate. #>
param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repo = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$gate = Join-Path $repo "timing_closure_gate_v5"
$vivado = "C:\Xilinx\Vivado\2023.1\bin\vivado.bat"
$status = Join-Path $gate "stability_launcher.status"
$log = Join-Path $gate "stability_launcher.log"
$notificationLog = Join-Path $gate "stability_notification.log"
$campaign = Join-Path $gate "stability_campaign_001"
$scratch = "C:\VGT5S001"
$maximumStartupUptimeSeconds = 14400

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
$bootLine = systeminfo | Select-String -Pattern '^System Boot Time:' | Select-Object -First 1
if ($null -eq $bootLine) {
    throw "could not determine Windows boot time from systeminfo"
}
$bootText = ($bootLine.Line -split ':', 2)[1].Trim()
$bootTime = [DateTime]::Parse(
    $bootText,
    [Globalization.CultureInfo]::CurrentCulture,
    [Globalization.DateTimeStyles]::AssumeLocal
)
$uptimeSeconds = [Math]::Floor(([DateTime]::Now - $bootTime).TotalSeconds)
if ($uptimeSeconds -lt 0) {
    throw "parsed Windows uptime is negative: $uptimeSeconds seconds"
}
if ($uptimeSeconds -gt $maximumStartupUptimeSeconds) {
    throw "V5 must start within $maximumStartupUptimeSeconds seconds of Windows boot; observed uptime is $uptimeSeconds seconds"
}
if (-not (Test-Path -LiteralPath $vivado -PathType Leaf)) {
    throw "Vivado 2023.1 launcher is missing: $vivado"
}
git diff --quiet -- .gitattributes launch_timing_stability_v5.ps1 timing_closure_gate_v5 timing_closure_gate_v4/closure_synth_single_thread.tcl timing_closure_gate_v4/stability_probe.sv
if ($LASTEXITCODE -ne 0) {
    throw "the frozen V5 launcher/package has unstaged changes"
}
git diff --cached --quiet -- .gitattributes launch_timing_stability_v5.ps1 timing_closure_gate_v5 timing_closure_gate_v4/closure_synth_single_thread.tcl timing_closure_gate_v4/stability_probe.sv
if ($LASTEXITCODE -ne 0) {
    throw "the frozen V5 launcher/package has staged changes"
}
if (Test-Path -LiteralPath $campaign) {
    throw "V5 stability campaign already exists and cannot be overwritten: $campaign"
}
if (Test-Path -LiteralPath $scratch) {
    throw "V5 scratch root already exists and cannot be overwritten: $scratch"
}
if (Get-Process -Name vivado -ErrorAction SilentlyContinue) {
    throw "another Vivado process is already running"
}
Invoke-LoggedPython -PythonArgs @("-m", "unittest", "timing_closure_gate_v5.test_stability")
Invoke-LoggedPython -PythonArgs @((Join-Path $gate "freeze_package.py"), "--check")
Invoke-LoggedPython -PythonArgs @((Join-Path $gate "freeze_dependency_baseline.py"), "--check")

@(
    "state=RUNNING"
    "started_utc=$([DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ'))"
    "windows_uptime_seconds_at_start=$uptimeSeconds"
    "maximum_startup_uptime_seconds=$maximumStartupUptimeSeconds"
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
