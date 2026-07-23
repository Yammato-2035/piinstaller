# Setuphelfer WinPE / Setup live collector — PI-RS-ASUS-LAB-CONTROL-006
# Copies Panther/Rollback periodically to SETUP_LOGS. No BitLocker mutation. No disk writes to NVMe.
param(
  [string]$RunId = $env:SETUPHELFER_WIN11_RUN_ID,
  [int]$IntervalSec = 30,
  [int]$MaxMinutes = 180,
  [string]$OutRoot = ""
)

$ErrorActionPreference = "Continue"
$TagName = "SETUP_LOGS.TAG"

function Get-SetupLogsRoot {
  param([string]$Preferred)
  if ($Preferred -and (Test-Path -LiteralPath $Preferred)) { return $Preferred }
  foreach ($letter in 65..90 | ForEach-Object { [char]$_ }) {
    $root = "$letter`:"
    if (Test-Path -LiteralPath "$root\$TagName") { return $root }
  }
  try {
    Get-Volume -ErrorAction SilentlyContinue | Where-Object { $_.FileSystemLabel -eq "SETUP_LOGS" } | ForEach-Object {
      if ($_.DriveLetter) { return "$($_.DriveLetter):" }
    }
  } catch {}
  return $null
}

function New-RunId {
  $ts = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
  $suffix = -join ((0..7) | ForEach-Object { "{0:x}" -f (Get-Random -Maximum 16) })
  return "asus-win11-$ts-$suffix"
}

if ([string]::IsNullOrWhiteSpace($RunId) -or $RunId -match "norunid|unknown") {
  $RunId = New-RunId
}

$setupLogs = Get-SetupLogsRoot -Preferred $OutRoot
if (-not $setupLogs) {
  Write-Host "[setuphelfer] ERROR: SETUP_LOGS not found (label/TAG)."
  exit 2
}

$runRoot = Join-Path $setupLogs "asus-win11\$RunId"
@(
  "collector","heartbeats","winpe","panther","rollback","setupdiag",
  "disk-layout","firmware","screenshots","result"
) | ForEach-Object {
  New-Item -ItemType Directory -Force -Path (Join-Path $runRoot $_) | Out-Null
}

# Write probe
$probe = Join-Path $runRoot "collector\write_probe.txt"
"ok $(Get-Date -Format o)" | Set-Content -LiteralPath $probe -Encoding UTF8

$meta = @{
  schema = "setuphelfer.win11_live_capture.v1"
  run_id = $RunId
  setup_logs = $setupLogs
  setup_capture_ready = $true
  started_at = (Get-Date).ToUniversalTime().ToString("o")
  computername = $env:COMPUTERNAME
}
$meta | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runRoot "collector\meta.json") -Encoding UTF8

$sources = @(
  "X:\Windows\Panther",
  "X:\`$WINDOWS.~BT\Sources\Panther",
  "X:\`$WINDOWS.~BT\Sources\Rollback",
  "C:\`$WINDOWS.~BT\Sources\Panther",
  "C:\`$WINDOWS.~BT\Sources\Rollback",
  "C:\Windows\Panther"
)

function Copy-SourceTree {
  param([string]$Src, [string]$DestRoot)
  if (-not (Test-Path -LiteralPath $Src)) { return @{seen=0; copied=0; bytes=0; error=$null} }
  $safe = ($Src -replace "[:\\`$]", "_")
  $dest = Join-Path $DestRoot $safe
  New-Item -ItemType Directory -Force -Path $dest | Out-Null
  $copied = 0; $bytes = 0; $seen = 0; $err = $null
  try {
    Get-ChildItem -LiteralPath $Src -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
      $seen++
      $rel = $_.FullName.Substring($Src.Length).TrimStart("\")
      $target = Join-Path $dest $rel
      $td = Split-Path -Parent $target
      if (-not (Test-Path -LiteralPath $td)) { New-Item -ItemType Directory -Force -Path $td | Out-Null }
      Copy-Item -LiteralPath $_.FullName -Destination $target -Force -ErrorAction Stop
      $copied++
      $bytes += $_.Length
    }
  } catch {
    $err = $_.Exception.Message
  }
  return @{seen=$seen; copied=$copied; bytes=$bytes; error=$err}
}

$deadline = (Get-Date).AddMinutes($MaxMinutes)
$hbIndex = 0
$totalCopied = 0
$totalBytes = 0
$lastError = $null

Write-Host "[setuphelfer] Live capture run_id=$RunId root=$runRoot interval=${IntervalSec}s"

while ((Get-Date) -lt $deadline) {
  $scanned = @()
  $filesSeen = 0
  $filesCopied = 0
  $bytesCopied = 0
  foreach ($src in $sources) {
    $scanned += $src
    # Expand literal $WINDOWS path variants
    $expanded = $src -replace '`\$', '$'
    $r = Copy-SourceTree -Src $expanded -DestRoot (Join-Path $runRoot "panther")
    if ($expanded -match "Rollback") {
      $r = Copy-SourceTree -Src $expanded -DestRoot (Join-Path $runRoot "rollback")
    }
    $filesSeen += [int]$r.seen
    $filesCopied += [int]$r.copied
    $bytesCopied += [int]$r.bytes
    if ($r.error) { $lastError = $r.error }
  }
  $totalCopied += $filesCopied
  $totalBytes += $bytesCopied
  $setupSeen = $false
  try {
    $setupSeen = [bool](Get-Process -Name "setup*" -ErrorAction SilentlyContinue)
  } catch {}

  $hb = @{
    schema_version = 1
    run_id = $RunId
    timestamp = (Get-Date).ToUniversalTime().ToString("o")
    collector_alive = $true
    setup_process_seen = $setupSeen
    sources_scanned = $scanned
    files_seen = $filesSeen
    files_copied = $filesCopied
    bytes_copied = $bytesCopied
    last_copy_error = $lastError
    setup_logs_volume_present = $true
  }
  $hbPath = Join-Path $runRoot ("heartbeats\hb-{0:D5}.json" -f $hbIndex)
  $hb | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $hbPath -Encoding UTF8
  $hbIndex++

  # Single-shot mode when MaxMinutes tiny or env says once
  if ($env:SETUPHELFER_WIN11_CAPTURE_ONCE -eq "1") { break }
  Start-Sleep -Seconds $IntervalSec
}

$result = @{
  run_id = $RunId
  heartbeats = $hbIndex
  files_copied_total = $totalCopied
  bytes_copied_total = $totalBytes
  last_copy_error = $lastError
  finished_at = (Get-Date).ToUniversalTime().ToString("o")
  status = $(if ($totalCopied -gt 0) { "evidence_collected" } else { "insufficient_evidence" })
  definitive_freeze_root_cause_known = $false
}
$result | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runRoot "result\finalize.json") -Encoding UTF8
Write-Host "[setuphelfer] Finalize status=$($result.status) copied=$totalCopied"
exit 0
