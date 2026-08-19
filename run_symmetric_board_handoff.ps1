<#
.SYNOPSIS
Upload, execute, retrieve, and provenance-check the symmetric PYNQ-Z2 sweep.

.DESCRIPTION
The script requires the locally built bitstream/HWH pair and refuses both a
pre-existing local result and a pre-existing remote result. It uploads only the
fixed harness, selection metadata, and design-derived golden functions needed
by sweep_catalog.py.
#>
[CmdletBinding()]
param(
    [string]$BoardHost = "192.168.2.99",
    [string]$BoardUser = "xilinx",
    [string]$RemoteRoot = "/home/xilinx/fpga_symmetric_holdout",
    [string]$IdentityFile = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repo = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$board = "$BoardUser@$BoardHost"
$result = Join-Path $repo "rtl\holdout_silicon_symmetric\catalog_fmax.json"
$bit = Join-Path $repo "rtl\holdout_silicon_symmetric\out\system_holdout_symmetric.bit"
$hwh = Join-Path $repo "rtl\holdout_silicon_symmetric\out\system_holdout_symmetric.hwh"
$sels = Join-Path $repo "rtl\holdout_silicon_symmetric\holdout_sels.json"
$selectionManifest = Join-Path $repo "rtl\holdout_silicon_symmetric\selection_manifest.json"
$supportFiles = @("sweep_catalog.py", "clock_sweep_fmax.py", "capture_waveforms.py", "score_candidate.py")
$goldenNames = @(
    "sft_fir26", "grpo_fir26",
    "sft_firr26", "grpo_firr26",
    "sft_poly7", "grpo_poly7",
    "sft_firr36", "grpo_firr36",
    "sft_poly8v6", "grpo_poly8v6",
    "echo8b"
)

foreach ($path in @($bit, $hwh, $sels, $selectionManifest)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Required board input is absent: $path"
    }
}
foreach ($name in $supportFiles) {
    $path = Join-Path $repo $name
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Required board support file is absent: $path"
    }
}
foreach ($name in $goldenNames) {
    $path = Join-Path $repo "rtl_library\$name\golden.py"
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Required design golden is absent: $path"
    }
}
if (Test-Path -LiteralPath $result) {
    throw "Refusing pre-existing local live-board result: $result"
}
if ($RemoteRoot.Contains("'")) {
    throw "RemoteRoot must not contain a single quote"
}

$sshArgs = @("-o", "ConnectTimeout=10")
if ($IdentityFile) {
    if (-not (Test-Path -LiteralPath $IdentityFile -PathType Leaf)) {
        throw "Board SSH identity file not found: $IdentityFile"
    }
    $sshArgs += ("-i", $IdentityFile)
}

function Invoke-Board {
    param([Parameter(Mandatory = $true)][string]$Command, [switch]$Tty)
    $callArgs = @($sshArgs)
    if ($Tty) { $callArgs += "-t" }
    $callArgs += ($board, $Command)
    & ssh @callArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Board command failed with exit code $LASTEXITCODE"
    }
}

function Send-BoardFile {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination
    )
    $callArgs = @($sshArgs)
    $callArgs += ($Source, ("{0}:{1}" -f $board, $Destination))
    & scp @callArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Board upload failed for $Source"
    }
}

$remoteDirs = @(
    "$RemoteRoot/rtl/holdout_silicon_symmetric/out",
    "$RemoteRoot/rtl_library"
) + @($goldenNames | ForEach-Object { "$RemoteRoot/rtl_library/$_" })
$mkdirArgs = $remoteDirs | ForEach-Object { "'$_'" }
$remoteResult = "$RemoteRoot/rtl/holdout_silicon_symmetric/catalog_fmax.json"
Invoke-Board -Command ("set -eu; test ! -e '$remoteResult'; mkdir -p " + ($mkdirArgs -join " "))

foreach ($name in $supportFiles) {
    Send-BoardFile -Source (Join-Path $repo $name) -Destination "$RemoteRoot/$name"
}
Send-BoardFile -Source $bit -Destination "$RemoteRoot/rtl/holdout_silicon_symmetric/out/system_holdout_symmetric.bit"
Send-BoardFile -Source $hwh -Destination "$RemoteRoot/rtl/holdout_silicon_symmetric/out/system_holdout_symmetric.hwh"
Send-BoardFile -Source $sels -Destination "$RemoteRoot/rtl/holdout_silicon_symmetric/holdout_sels.json"
Send-BoardFile -Source $selectionManifest -Destination "$RemoteRoot/rtl/holdout_silicon_symmetric/selection_manifest.json"
foreach ($name in $goldenNames) {
    Send-BoardFile -Source (Join-Path $repo "rtl_library\$name\golden.py") -Destination "$RemoteRoot/rtl_library/$name/golden.py"
}

$sweepCommand = @(
    "set -eu",
    "cd '$RemoteRoot'",
    "sudo -E /usr/local/share/pynq-venv/bin/python3 sweep_catalog.py --bit rtl/holdout_silicon_symmetric/out/system_holdout_symmetric.bit --sels rtl/holdout_silicon_symmetric/holdout_sels.json --lo 20 --hi 260 --step 5 --runs 3 --out rtl/holdout_silicon_symmetric/catalog_fmax.json"
) -join "; "
Invoke-Board -Tty -Command $sweepCommand

$downloadArgs = @($sshArgs)
$downloadArgs += (("{0}:{1}" -f $board, $remoteResult), $result)
& scp @downloadArgs
if ($LASTEXITCODE -ne 0) {
    throw "Board-result download failed"
}

$data = Get-Content -LiteralPath $result -Raw | ConvertFrom-Json
if ($data.schema_version -ne 2 -or $data.measurement_kind -ne "live_pynq_clock_sweep") {
    throw "Downloaded board result has the wrong schema or measurement kind"
}
$expectedHashes = @{
    bitstream_sha256 = (Get-FileHash -LiteralPath $bit -Algorithm SHA256).Hash.ToLowerInvariant()
    hwh_sha256 = (Get-FileHash -LiteralPath $hwh -Algorithm SHA256).Hash.ToLowerInvariant()
    sels_sha256 = (Get-FileHash -LiteralPath $sels -Algorithm SHA256).Hash.ToLowerInvariant()
    selection_manifest_sha256 = (Get-FileHash -LiteralPath $selectionManifest -Algorithm SHA256).Hash.ToLowerInvariant()
}
foreach ($field in $expectedHashes.Keys) {
    if ($data.provenance.$field -ne $expectedHashes[$field]) {
        throw "Downloaded board result has a provenance mismatch for $field"
    }
}
if ($data.sels.PSObject.Properties.Count -ne 11 -or
    $data.raw_runs.Count -ne 3 -or
    -not $data.summary.all_entries_have_fmax) {
    throw "Downloaded board result is incomplete; retain it but do not make a headline claim"
}
Write-Host "Symmetric live-board sweep complete and provenance-checked: $result"
