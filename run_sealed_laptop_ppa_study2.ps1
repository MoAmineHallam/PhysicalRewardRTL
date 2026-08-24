param(
    [string]$Vivado = "C:\Xilinx\Vivado\2023.1\bin\vivado.bat"
)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

if (-not (Test-Path -LiteralPath $Vivado -PathType Leaf)) {
    throw "Vivado executable not found: $Vivado"
}

$evaluationDirs = @(
    "rtl/sealed_sft",
    "rtl/sealed_rf_s1",
    "rtl/sealed_rf_s2",
    "rtl/sealed_rf_mid_s1",
    "rtl/sealed_rf_mid_s2",
    "rtl/sealed_mlp_s1",
    "rtl/sealed_mlp_s2",
    "rtl/sealed_corr_s1"
)

if (Test-Path -LiteralPath "sealed_ppa_audit_study2.json") {
    throw "Refusing pre-existing Study 2 PPA audit"
}
foreach ($directory in $evaluationDirs) {
    $manifest = Join-Path $directory "fmax_manifest.json"
    $out = Join-Path $directory "ppa.jsonl"
    if (-not (Test-Path -LiteralPath $manifest -PathType Leaf)) {
        throw "Missing sealed manifest: $manifest"
    }
    if (Test-Path -LiteralPath $out) {
        throw "Refusing pre-existing PPA output: $out"
    }
}

foreach ($directory in $evaluationDirs) {
    Write-Host "== Study 2 Vivado PPA: $directory =="
    $out = Join-Path $directory "ppa.jsonl"
    python run_ppa.py --dir $directory --out $out --clk clk --period 5.0 --vivado $Vivado
    if ($LASTEXITCODE -ne 0) {
        throw "run_ppa.py failed for $directory with exit code $LASTEXITCODE"
    }
}

python verify_sealed_ppa.py --vivado $Vivado --period 5.0 --out sealed_ppa_audit_study2.json
if ($LASTEXITCODE -ne 0) {
    throw "Study 2 sealed PPA audit failed with exit code $LASTEXITCODE"
}

Write-Host "Study 2 Vivado stage complete. Return the PPA rows to the server."

