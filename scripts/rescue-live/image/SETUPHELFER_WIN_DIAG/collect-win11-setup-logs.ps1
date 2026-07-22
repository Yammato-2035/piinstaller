# Setuphelfer WinPE — read-only Windows Setup log collector (PowerShell).
# No partitioning, no disk online, no registry changes, no credentials.

param(
    [Parameter(Mandatory = $true)]
    [string]$OutDir
)

$ErrorActionPreference = "Continue"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$index = Join-Path $OutDir "copy_index.txt"

function Copy-TreeSafe([string]$Src, [string]$Dst) {
    if (Test-Path -LiteralPath $Src) {
        New-Item -ItemType Directory -Force -Path $Dst | Out-Null
        Copy-Item -LiteralPath $Src -Destination $Dst -Recurse -Force -ErrorAction SilentlyContinue
        Add-Content -LiteralPath $index -Value "copied_dir $Src"
    }
}

function Copy-FileSafe([string]$Src, [string]$Dst) {
    if (Test-Path -LiteralPath $Src) {
        Copy-Item -LiteralPath $Src -Destination $Dst -Force -ErrorAction SilentlyContinue
        Add-Content -LiteralPath $index -Value "copied_file $Src"
    }
}

# WinPE roots
Copy-TreeSafe "X:\Windows\Panther" (Join-Path $OutDir "from_X_Windows_Panther")
Copy-TreeSafe "X:\`$WINDOWS.~BT\Sources\Panther" (Join-Path $OutDir "from_X_WINDOWS_BT_Panther")
Copy-TreeSafe "X:\Windows\System32\LogFiles" (Join-Path $OutDir "from_X_LogFiles")
Copy-TreeSafe "X:\Windows\Logs\DISM" (Join-Path $OutDir "from_X_DISM")
Copy-TreeSafe "X:\Windows\Logs\CBS" (Join-Path $OutDir "from_X_CBS")

$letters = 67..90 | ForEach-Object { [char]$_ }  # C-Z
foreach ($L in $letters) {
    $root = "${L}:"
    if (-not (Test-Path -LiteralPath "$root\")) { continue }
    Copy-TreeSafe "$root\`$WINDOWS.~BT\Sources\Panther" (Join-Path $OutDir "from_${L}_WINDOWS_BT_Panther")
    Copy-TreeSafe "$root\`$WINDOWS.~BT\Sources\Rollback" (Join-Path $OutDir "from_${L}_WINDOWS_BT_Rollback")
    Copy-TreeSafe "$root\Windows\Panther" (Join-Path $OutDir "from_${L}_Windows_Panther")
    Copy-TreeSafe "$root\Windows\Panther\NewOS" (Join-Path $OutDir "from_${L}_Windows_Panther_NewOS")
    Copy-TreeSafe "$root\Windows\Panther\UnattendGC" (Join-Path $OutDir "from_${L}_Windows_Panther_UnattendGC")
    Copy-TreeSafe "$root\Windows\Logs\DISM" (Join-Path $OutDir "from_${L}_DISM")
    Copy-TreeSafe "$root\Windows\Logs\CBS" (Join-Path $OutDir "from_${L}_CBS")
    Copy-TreeSafe "$root\Windows\Logs\MoSetup" (Join-Path $OutDir "from_${L}_MoSetup")
    Copy-TreeSafe "$root\Windows\Logs\Setup" (Join-Path $OutDir "from_${L}_Setup")
    Copy-TreeSafe "$root\Windows\Logs\SetupDiag" (Join-Path $OutDir "from_${L}_SetupDiag")
    Copy-TreeSafe "$root\Windows\Minidump" (Join-Path $OutDir "from_${L}_Minidump")
    Copy-FileSafe "$root\Windows\INF\setupapi.dev.log" (Join-Path $OutDir "from_${L}_setupapi.dev.log")
    Copy-FileSafe "$root\Windows\INF\setupapi.offline.log" (Join-Path $OutDir "from_${L}_setupapi.offline.log")
    Copy-FileSafe "$root\SetupDiagResults.log" (Join-Path $OutDir "from_${L}_SetupDiagResults.log")
    Copy-FileSafe "$root\SetupDiagResults.xml" (Join-Path $OutDir "from_${L}_SetupDiagResults.xml")
    Copy-FileSafe "$root\Windows\Panther\Setup.etl" (Join-Path $OutDir "from_${L}_Setup.etl")
}

"ps1_collector_done=$(Get-Date -Format o)" | Set-Content -LiteralPath (Join-Path $OutDir "ps1_collector_done.txt")
Write-Host "[setuphelfer] PS1 log collection finished: $OutDir"
