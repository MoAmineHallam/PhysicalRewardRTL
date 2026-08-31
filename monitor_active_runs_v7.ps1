<# Notify the user when each active V7 candidate and the final campaign finish. #>
param(
    [string]$Repo = $PSScriptRoot,
    [int]$PollSeconds = 30
)

$ErrorActionPreference = "Continue"
Set-StrictMode -Version Latest

$results = Join-Path $Repo "timing_closure_candidate_v7\results"
$status = Join-Path $Repo "timing_closure_candidate_v7\candidate_launcher.status"
$log = Join-Path $Repo "timing_closure_candidate_v7\candidate_progress_notifications.log"
$notify = "/home/adam/mas/mas/notify_correctness_done.sh"
$seen = @{}

function Write-MonitorLog {
    param([string]$Message)
    $line = "$([DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ')) $Message"
    Add-Content -LiteralPath $log -Value $line -Encoding utf8
}

function Send-RunNotification {
    param([string]$Message)
    $safe = $Message.Replace("'", "")
    & ssh -o BatchMode=yes -o ConnectTimeout=15 adam40 `
        "bash $notify '$safe'" *>> $log
    Write-MonitorLog "notification_attempted: $safe"
}

# Results that predate this monitor are the baseline and are not announced again.
Get-ChildItem -LiteralPath $results -Recurse -Filter closure_result.json `
        -ErrorAction SilentlyContinue | ForEach-Object {
    $seen[$_.FullName] = $true
}
Write-MonitorLog "monitor_started baseline_candidates=$($seen.Count)"

while ($true) {
    $finals = @(Get-ChildItem -LiteralPath $results -Recurse `
        -Filter closure_result.json -ErrorAction SilentlyContinue)
    foreach ($file in $finals | Sort-Object FullName) {
        if ($seen.ContainsKey($file.FullName)) { continue }
        try {
            $record = Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json
            $mhz = [double]$record.closure_fmax_mhz
            Send-RunNotification (
                "Vivado V7 candidate $($record.candidate_id) finished: " +
                "$($record.status), $($mhz.ToString('F3')) MHz; " +
                "$($finals.Count)/10 candidates published"
            )
        }
        catch {
            Write-MonitorLog "candidate_parse_error path=$($file.FullName) error=$_"
        }
        $seen[$file.FullName] = $true
    }

    $states = @()
    if (Test-Path -LiteralPath $status -PathType Leaf) {
        $states = @(Get-Content -LiteralPath $status |
            Select-String '^state=' | ForEach-Object { $_.Line.Substring(6) })
    }
    if ($states.Count -gt 0 -and $states[-1] -eq "FINISHED") {
        $verdictLine = Get-Content -LiteralPath $status |
            Select-String '^verdict=' | Select-Object -Last 1
        $verdict = if ($verdictLine) {
            $verdictLine.Line.Substring(8)
        } else {
            "UNKNOWN"
        }
        Send-RunNotification (
            "Vivado V7 all-ten candidate campaign finished: verdict $verdict; " +
            "$($finals.Count)/10 results published"
        )
        Write-MonitorLog "monitor_finished verdict=$verdict candidates=$($finals.Count)"
        break
    }
    Start-Sleep -Seconds $PollSeconds
}
