<# Run the frozen V3 ten-candidate closure pilot in one hidden-safe process. #>
param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repo = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$study = Join-Path $repo "timing_closure_candidate_v3"
$vivado = "C:\Xilinx\Vivado\2023.1\bin\vivado.bat"
$results = Join-Path $study "results"
$scratch = "C:\VGC3P001"
$status = Join-Path $study "candidate_launcher.status"
$log = Join-Path $study "candidate_launcher.log"
$notificationLog = Join-Path $study "candidate_notification.log"

function Invoke-LoggedPython {
    param([string[]]$PythonArgs, [switch]$AllowScientificFail)
    $previousErrorAction = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        & python @PythonArgs *>> $log
        $nativeExit = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorAction
    }
    if ($nativeExit -ne 0 -and -not $AllowScientificFail) {
        throw "python $($PythonArgs -join ' ') failed with exit code $nativeExit"
    }
    return $nativeExit
}

Set-Location -LiteralPath $repo
if (-not (Test-Path -LiteralPath $vivado -PathType Leaf)) {
    throw "Vivado 2023.1 launcher is missing: $vivado"
}
git diff --quiet -- launch_timing_candidates_v3.ps1 timing_closure_candidate_v3
if ($LASTEXITCODE -ne 0) { throw "candidate V3 package has unstaged changes" }
git diff --cached --quiet -- launch_timing_candidates_v3.ps1 timing_closure_candidate_v3
if ($LASTEXITCODE -ne 0) { throw "candidate V3 package has staged changes" }
foreach ($path in @($results, $scratch, $status, $log, $notificationLog)) {
    if (Test-Path -LiteralPath $path) { throw "refusing existing campaign artifact: $path" }
}
if (Get-Process -Name vivado -ErrorAction SilentlyContinue) {
    throw "another Vivado process is already running"
}

Invoke-LoggedPython -PythonArgs @("-m", "unittest", "timing_closure_candidate_v3.test_candidate", "-v") | Out-Null
Invoke-LoggedPython -PythonArgs @((Join-Path $study "freeze_package.py"), "--check") | Out-Null
Invoke-LoggedPython -PythonArgs @((Join-Path $study "validate.py"), "--check-inputs") | Out-Null

@(
    "state=RUNNING"
    "started_utc=$([DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ'))"
    "results=timing_closure_candidate_v3/results"
    "scratch_root=$scratch"
    "reuses_v1_v2_outcomes=false"
) | Set-Content -LiteralPath $status -Encoding ascii

$exitCode = 1
$verdict = "ERROR"
try {
    Invoke-LoggedPython -PythonArgs @(
        (Join-Path $study "run_candidates.py"),
        "--vivado", $vivado, "--results", $results, "--scratch-root", $scratch
    ) | Out-Null
    $validationExit = Invoke-LoggedPython -PythonArgs @(
        (Join-Path $study "validate.py"), "--scope", "pilot", "--results", $results
    ) -AllowScientificFail
    $gate = Join-Path $results "pilot_gate.json"
    if (Test-Path -LiteralPath $gate -PathType Leaf) {
        $verdict = (Get-Content -LiteralPath $gate -Raw | ConvertFrom-Json).verdict
    }
    $exitCode = $validationExit
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
