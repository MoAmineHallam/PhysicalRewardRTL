<# Fail-closed transfer, laptop PPA, and return wrapper for Study 2. #>
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
    "sealed_sft", "sealed_rf_s1", "sealed_rf_s2", "sealed_rf_mid_s1",
    "sealed_rf_mid_s2", "sealed_mlp_s1", "sealed_mlp_s2", "sealed_corr_s1"
)
$serverFiles = @(
    "sealed_training_audit_study2.json",
    "rf_reward_eligible_manifest_study2.json",
    "rf_reward_eligible_contract_study2.json"
)

if (-not (Test-Path -LiteralPath $IdentityFile -PathType Leaf)) {
    throw "SSH identity file not found: $IdentityFile"
}
if ($RemoteRoot.Contains("'")) { throw "RemoteRoot must not contain a single quote" }
$sshArgs = @("-i", $IdentityFile, "-o", "BatchMode=yes", "-o", "ConnectTimeout=10")

function Invoke-Remote {
    param([Parameter(Mandatory = $true)][string]$Command)
    $output = & ssh @sshArgs $remote $Command
    if ($LASTEXITCODE -ne 0) { throw "Remote command failed: $LASTEXITCODE" }
    return $output
}

function Copy-FromRemote {
    param([string]$Source, [string]$Destination, [switch]$Recursive)
    $args = @($sshArgs)
    if ($Recursive) { $args += "-r" }
    $args += (("{0}:{1}" -f $remote, $Source), $Destination)
    & scp @args
    if ($LASTEXITCODE -ne 0) { throw "scp download failed for $Source" }
}

function Copy-ToRemote {
    param([string]$Source, [string]$Destination)
    $args = @($sshArgs) + @($Source, ("{0}:{1}" -f $remote, $Destination))
    & scp @args
    if ($LASTEXITCODE -ne 0) { throw "scp upload failed for $Source" }
}

if ($Stage -eq "Fetch") {
    foreach ($name in $evaluationDirs) {
        if (Test-Path -LiteralPath (Join-Path $repo "rtl\$name")) {
            throw "Refusing pre-existing local evaluation directory: $name"
        }
    }
    foreach ($name in $serverFiles) {
        if (Test-Path -LiteralPath (Join-Path $repo $name)) {
            throw "Refusing pre-existing local Study 2 artifact: $name"
        }
    }
    $transferManifest = Join-Path $repo "sealed_server_transfer_study2.sha256"
    if (Test-Path -LiteralPath $transferManifest) {
        throw "Refusing pre-existing Study 2 transfer manifest"
    }

    $remotePaths = @($evaluationDirs | ForEach-Object { "rtl/$_" }) + $serverFiles
    $tests = @("grep -Fq 'SERVER STAGE STUDY2 COMPLETE' 'launch_sealed_server_stage_study2.log'")
    foreach ($name in $evaluationDirs) { $tests += "test -f 'rtl/$name/fmax_manifest.json'" }
    foreach ($name in $serverFiles) { $tests += "test -f '$name'" }
    $command = @(
        "set -euo pipefail", "cd '$RemoteRoot'", ($tests -join "; "),
        ("find {0} -type f -print0 | sort -z | xargs -0 sha256sum" -f ($remotePaths -join " "))
    ) -join "; "
    $remoteManifest = @(Invoke-Remote -Command $command)
    if ($remoteManifest.Count -eq 0) { throw "Remote transfer manifest was empty" }

    $tempBase = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    $staging = Join-Path $tempBase ("fpga-study2-" + [guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Path (Join-Path $staging "rtl") | Out-Null
    try {
        foreach ($name in $evaluationDirs) {
            Copy-FromRemote -Recursive -Source "$RemoteRoot/rtl/$name" -Destination (Join-Path $staging "rtl")
        }
        foreach ($name in $serverFiles) {
            Copy-FromRemote -Source "$RemoteRoot/$name" -Destination $staging
        }
        $localManifest = @(
            Get-ChildItem -LiteralPath $staging -Recurse -File | ForEach-Object {
                $rel = [IO.Path]::GetRelativePath($staging, $_.FullName).Replace("\", "/")
                $hash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
                "$hash  $rel"
            } | Sort-Object
        )
        $remoteSorted = @($remoteManifest | ForEach-Object { $_.Trim() } | Sort-Object)
        if (@(Compare-Object $remoteSorted $localManifest).Count -ne 0) {
            throw "Remote/local Study 2 SHA-256 manifests differ"
        }
        foreach ($name in $evaluationDirs) {
            Move-Item -LiteralPath (Join-Path $staging "rtl\$name") -Destination (Join-Path $repo "rtl\$name")
        }
        foreach ($name in $serverFiles) {
            Move-Item -LiteralPath (Join-Path $staging $name) -Destination (Join-Path $repo $name)
        }
        $remoteSorted | Set-Content -LiteralPath $transferManifest -Encoding ascii
    } finally {
        $resolved = [IO.Path]::GetFullPath($staging)
        if ($resolved.StartsWith($tempBase, [StringComparison]::OrdinalIgnoreCase) -and (Test-Path $resolved)) {
            Remove-Item -LiteralPath $resolved -Recurse -Force
        }
    }
    Write-Host "Study 2 fetch complete and hash-verified. Next: -Stage Ppa"
    exit 0
}

if ($Stage -eq "Ppa") {
    & (Join-Path $repo "run_sealed_laptop_ppa_study2.ps1") -Vivado $Vivado
    if ($LASTEXITCODE -ne 0) { throw "Study 2 laptop PPA failed: $LASTEXITCODE" }
    Write-Host "Study 2 PPA complete. Next: -Stage ReturnAndAnalyze"
    exit 0
}

foreach ($name in $evaluationDirs) {
    if (-not (Test-Path -LiteralPath (Join-Path $repo "rtl\$name\ppa.jsonl") -PathType Leaf)) {
        throw "Missing completed PPA rows for $name"
    }
}
if (Test-Path -LiteralPath (Join-Path $repo "sealed_results_study2.json")) {
    throw "Refusing pre-existing local Study 2 result"
}
$tests = @("test ! -e 'sealed_ppa_audit_study2.json'", "test ! -e 'sealed_results_study2.json'")
foreach ($name in $evaluationDirs) { $tests += "test ! -e 'rtl/$name/ppa.jsonl'" }
Invoke-Remote -Command (@("set -euo pipefail", "cd '$RemoteRoot'", ($tests -join "; ")) -join "; ") | Out-Null
foreach ($name in $evaluationDirs) {
    Copy-ToRemote -Source (Join-Path $repo "rtl\$name\ppa.jsonl") -Destination "$RemoteRoot/rtl/$name/ppa.jsonl"
}
$analysis = @(
    "set -euo pipefail", "cd '$RemoteRoot'",
    "export FPGA_ENV_BIN='/home/adam/mas/mas/env_fpga/bin'",
    "bash run_sealed_analysis_study2.sh"
) -join "; "
Invoke-Remote -Command $analysis
$localResult = Join-Path $repo "sealed_results_study2.json"
Copy-FromRemote -Source "$RemoteRoot/sealed_results_study2.json" -Destination $localResult
Write-Host "Study 2 analysis complete; result copied to $localResult"
