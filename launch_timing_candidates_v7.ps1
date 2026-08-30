<# Run the frozen V7 ten-candidate closure pilot in one hidden-safe process. #>
param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repo = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$study = Join-Path $repo "timing_closure_candidate_v7"
$vivado = "C:\AMD\2026.1\Vivado\bin\vivado.bat"
$results = Join-Path $study "results"
$scratch = "C:\VGC7P001"
$status = Join-Path $study "candidate_launcher.status"
$log = Join-Path $study "candidate_launcher.log"

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
    throw "Vivado 2026.1 launcher is missing: $vivado"
}
git diff --quiet -- launch_timing_candidates_v7.ps1 timing_closure_candidate_v7
if ($LASTEXITCODE -ne 0) { throw "candidate V7 package has unstaged changes" }
git diff --cached --quiet -- launch_timing_candidates_v7.ps1 timing_closure_candidate_v7
if ($LASTEXITCODE -ne 0) { throw "candidate V7 package has staged changes" }
foreach ($path in @($results, $scratch, $status, $log)) {
    if (Test-Path -LiteralPath $path) {
        throw "refusing existing campaign artifact: $path"
    }
}
if (Get-Process -Name vivado -ErrorAction SilentlyContinue) {
    throw "another Vivado process is already running"
}

Invoke-LoggedPython -PythonArgs @(
    "-m", "unittest", "timing_closure_candidate_v7.test_candidate", "-v"
) | Out-Null
Invoke-LoggedPython -PythonArgs @(
    (Join-Path $study "freeze_package.py"), "--check"
) | Out-Null
Invoke-LoggedPython -PythonArgs @(
    (Join-Path $study "validate.py"), "--check-inputs"
) | Out-Null

@(
    "state=RUNNING"
    "started_utc=$([DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ'))"
    "vivado_root=C:\AMD\2026.1\Vivado"
    "results=timing_closure_candidate_v7/results"
    "scratch_root=$scratch"
    "reuses_v1_through_v6_outcomes=false"
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
}

exit $exitCode
