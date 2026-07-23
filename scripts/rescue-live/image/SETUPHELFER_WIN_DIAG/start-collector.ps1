# Auto Windows live collector entry — PI-RS-ASUS-AUTOCAPTURE-BIOS-007
param(
  [string]$RunId = $env:SETUPHELFER_WIN11_RUN_ID,
  [int]$IntervalSec = 30,
  [int]$MaxMinutes = 180
)
$ErrorActionPreference = "Continue"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
& "$here\collect-win11-live-capture.ps1" -RunId $RunId -IntervalSec $IntervalSec -MaxMinutes $MaxMinutes
exit $LASTEXITCODE
