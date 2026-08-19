<#
.SYNOPSIS
Fail-closed operational handoff for the preregistered sealed study.

.DESCRIPTION
This wrapper does not change any scientific decision rule. It transfers the
frozen server outputs, invokes the frozen laptop PPA script, and returns only
the completed PPA rows before invoking the frozen analysis. Each stage refuses
missing remote completion markers and pre-existing destination artifacts.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("Fetch", "Ppa", "ReturnAndAnalyze")]
    [string]$Stage,

    [string]$RemoteHost = "10.249.42.229",
    [string]$RemoteUser = "adam",
    [string]$RemoteRoot = "/home/adam/mas/mas/fpga",
    [string]$IdentityFile = "$env:USERPROFILE\.ssh\adam_rsa",
    [string]$Vivado = "C:\Xilinx\Vivado\2023.1\bin\vivado.bat"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repo = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$remote = "$RemoteUser@$RemoteHost"
$evaluationDirs = @(
    "sealed_sft",
    "sealed_rf_s1",
    "sealed_rf_s2",
    "sealed_rf_mid_s1",
    "sealed_rf_mid_s2",
    "sealed_mlp_s1",
    "sealed_mlp_s2",
    "sealed_corr_s1"
)
$serverFiles = @(
    "sealed_training_audit.json",
    "rf_training_candidates.json",
    "rf_training_contract.json"
)

if (-not (Test-Path -LiteralPath $IdentityFile -PathType Leaf)) {
    throw "SSH identity file not found: $IdentityFile"
}
if ($RemoteRoot.Contains("'")) {
    throw "RemoteRoot must not contain a single quote"
}

$sshArgs = @(
    "-i", $IdentityFile,
    "-o", "BatchMode=yes",
    "-o", "ConnectTimeout=10"
)

function Invoke-Remote {
    param([Parameter(Mandatory = $true)][string]$Command)
    $output = & ssh @sshArgs $remote $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Remote command failed with exit code $LASTEXITCODE"
    }
    return $output
}

function Invoke-ScpFromRemote {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination,
        [switch]$Recursive
    )
    $scpArgs = @($sshArgs)
    if ($Recursive) { $scpArgs += "-r" }
    $scpArgs += (("{0}:{1}" -f $remote, $Source), $Destination)
    & scp @scpArgs
    if ($LASTEXITCODE -ne 0) {
        throw "scp download failed for $Source"
    }
}

function Invoke-ScpToRemote {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination
    )
    $scpArgs = @($sshArgs)
    $scpArgs += ($Source, ("{0}:{1}" -f $remote, $Destination))
    & scp @scpArgs
    if ($LASTEXITCODE -ne 0) {
        throw "scp upload failed for $Source"
    }
}

if ($Stage -eq "Fetch") {
    foreach ($name in $evaluationDirs) {
        $target = Join-Path $repo "rtl\$name"
        if (Test-Path -LiteralPath $target) {
            throw "Refusing pre-existing local sealed directory: $target"
        }
    }
    foreach ($name in $serverFiles) {
        $target = Join-Path $repo $name
        if (Test-Path -LiteralPath $target) {
            throw "Refusing pre-existing local sealed artifact: $target"
        }
    }
    $transferManifest = Join-Path $repo "sealed_server_transfer.sha256"
    if (Test-Path -LiteralPath $transferManifest) {
        throw "Refusing pre-existing transfer manifest: $transferManifest"
    }

    $remotePaths = @($evaluationDirs | ForEach-Object { "rtl/$_" }) + $serverFiles
    $remoteTests = @(
        "grep -Fq 'SERVER STAGE COMPLETE' '/home/adam/mas/mas/launch_sealed_server_stage.log'"
    )
    foreach ($name in $evaluationDirs) {
        $remoteTests += "test -f 'rtl/$name/fmax_manifest.json'"
    }
    foreach ($name in $serverFiles) {
        $remoteTests += "test -f '$name'"
    }
    $findPaths = $remotePaths -join " "
    $remoteCommand = @(
        "set -euo pipefail",
        "cd '$RemoteRoot'",
        ($remoteTests -join "; "),
        "find $findPaths -type f -print0 | sort -z | xargs -0 sha256sum"
    ) -join "; "
    $remoteManifest = @(Invoke-Remote -Command $remoteCommand)
    if ($remoteManifest.Count -eq 0) {
        throw "Remote transfer manifest was empty"
    }

    $tempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    $staging = Join-Path $tempRoot ("fpga-sealed-" + [guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Path (Join-Path $staging "rtl") | Out-Null
    try {
        foreach ($name in $evaluationDirs) {
            Invoke-ScpFromRemote -Recursive -Source "$RemoteRoot/rtl/$name" -Destination (Join-Path $staging "rtl")
        }
        foreach ($name in $serverFiles) {
            Invoke-ScpFromRemote -Source "$RemoteRoot/$name" -Destination $staging
        }

        $localManifest = @(
            Get-ChildItem -LiteralPath $staging -Recurse -File | ForEach-Object {
                $relative = [IO.Path]::GetRelativePath($staging, $_.FullName).Replace("\", "/")
                $hash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
                "$hash  $relative"
            } | Sort-Object
        )
        $remoteSorted = @($remoteManifest | ForEach-Object { $_.Trim() } | Sort-Object)
        $difference = @(Compare-Object -ReferenceObject $remoteSorted -DifferenceObject $localManifest)
        if ($difference.Count -ne 0) {
            throw "Remote/local SHA-256 manifests differ; no files were installed"
        }

        foreach ($name in $evaluationDirs) {
            Move-Item -LiteralPath (Join-Path $staging "rtl\$name") -Destination (Join-Path $repo "rtl\$name")
        }
        foreach ($name in $serverFiles) {
            Move-Item -LiteralPath (Join-Path $staging $name) -Destination (Join-Path $repo $name)
        }
        $remoteSorted | Set-Content -LiteralPath $transferManifest -Encoding ascii
    }
    finally {
        $resolvedStaging = [IO.Path]::GetFullPath($staging)
        if ($resolvedStaging.StartsWith($tempRoot, [StringComparison]::OrdinalIgnoreCase) -and
            (Test-Path -LiteralPath $resolvedStaging)) {
            Remove-Item -LiteralPath $resolvedStaging -Recurse -Force
        }
    }
    Write-Host "Fetch complete; every transferred file matches the L40 SHA-256 manifest."
    Write-Host "Next: .\run_sealed_handoff.ps1 -Stage Ppa"
    exit 0
}

if ($Stage -eq "Ppa") {
    foreach ($name in $evaluationDirs) {
        $manifest = Join-Path $repo "rtl\$name\fmax_manifest.json"
        if (-not (Test-Path -LiteralPath $manifest -PathType Leaf)) {
            throw "Missing fetched sealed manifest: $manifest"
        }
    }
    if (-not (Test-Path -LiteralPath $Vivado -PathType Leaf)) {
        throw "Vivado executable not found: $Vivado"
    }
    & (Join-Path $repo "run_sealed_laptop_ppa.ps1") -Vivado $Vivado
    if ($LASTEXITCODE -ne 0) {
        throw "Frozen laptop PPA stage failed with exit code $LASTEXITCODE"
    }
    Write-Host "PPA complete and audited."
    Write-Host "Next: .\run_sealed_handoff.ps1 -Stage ReturnAndAnalyze"
    exit 0
}

foreach ($name in $evaluationDirs) {
    $ppa = Join-Path $repo "rtl\$name\ppa.jsonl"
    if (-not (Test-Path -LiteralPath $ppa -PathType Leaf)) {
        throw "Missing completed local PPA file: $ppa"
    }
}
$localAudit = Join-Path $repo "sealed_ppa_audit.json"
if (-not (Test-Path -LiteralPath $localAudit -PathType Leaf)) {
    throw "Missing local sealed PPA audit: $localAudit"
}
$localResult = Join-Path $repo "sealed_results_v3.json"
if (Test-Path -LiteralPath $localResult) {
    throw "Refusing pre-existing local analysis result: $localResult"
}

$absenceTests = @(
    "test ! -e 'sealed_ppa_audit.json'",
    "test ! -e 'sealed_results_v3.json'"
)
foreach ($name in $evaluationDirs) {
    $absenceTests += "test ! -e 'rtl/$name/ppa.jsonl'"
}
$guardCommand = @(
    "set -euo pipefail",
    "cd '$RemoteRoot'",
    ($absenceTests -join "; ")
) -join "; "
Invoke-Remote -Command $guardCommand | Out-Null

foreach ($name in $evaluationDirs) {
    Invoke-ScpToRemote -Source (Join-Path $repo "rtl\$name\ppa.jsonl") -Destination "$RemoteRoot/rtl/$name/ppa.jsonl"
}
$analysisCommand = @(
    "set -euo pipefail",
    "cd '$RemoteRoot'",
    "export PATH='/home/adam/mas/mas/env_fpga/bin':`$PATH",
    "export PYTHONNOUSERSITE=1",
    "bash run_sealed_analysis.sh"
) -join "; "
Invoke-Remote -Command $analysisCommand
Invoke-ScpFromRemote -Source "$RemoteRoot/sealed_results_v3.json" -Destination $localResult
Write-Host "Frozen analysis complete; result copied to $localResult"
