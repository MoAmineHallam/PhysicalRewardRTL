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

foreach ($directory in $evaluationDirs) {
    $manifest = Join-Path $directory "fmax_manifest.json"
    if (-not (Test-Path -LiteralPath $manifest -PathType Leaf)) {
        throw "Missing sealed manifest: $manifest"
    }
    Write-Host "== Vivado PPA: $directory =="
    $out = Join-Path $directory "ppa.jsonl"
    python run_ppa.py --dir $directory --out $out --clk clk --period 5.0 --vivado $Vivado
    if ($LASTEXITCODE -ne 0) {
        throw "run_ppa.py failed for $directory with exit code $LASTEXITCODE"
    }
}

python verify_sealed_ppa.py --vivado $Vivado --period 5.0 --out sealed_ppa_audit.json
if ($LASTEXITCODE -ne 0) {
    throw "sealed PPA audit failed with exit code $LASTEXITCODE"
}

Write-Host "Sealed Vivado stage complete. Push the PPA rows and audit back to the server."
