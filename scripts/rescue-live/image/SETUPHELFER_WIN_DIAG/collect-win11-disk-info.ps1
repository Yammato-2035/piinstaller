# Setuphelfer WinPE — read-only disk inventory (PowerShell).
# Captures Get-Disk / Get-PhysicalDisk / Get-Partition / Get-Volume when available.
# NEVER runs Online-Disk, Initialize-Disk, Clear-Disk, Format-Volume, or partition create.

param(
    [Parameter(Mandatory = $true)]
    [string]$OutDir
)

$ErrorActionPreference = "Continue"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

function Save-Cmd([string]$Name, [scriptblock]$Block) {
    $path = Join-Path $OutDir $Name
    try {
        & $Block | Out-File -FilePath $path -Encoding utf8
    } catch {
        "ERROR: $($_.Exception.Message)" | Out-File -FilePath $path -Encoding utf8
    }
}

Save-Cmd "get_disk.txt" { Get-Disk | Format-List * }
Save-Cmd "get_physicaldisk.txt" { Get-PhysicalDisk | Format-List * }
Save-Cmd "get_partition.txt" { Get-Partition | Format-List * }
Save-Cmd "get_volume.txt" { Get-Volume | Format-List * }

# UniqueId / serial / location / bus / health when Storage module present
Save-Cmd "storage_identity_summary.txt" {
    Get-Disk | Select-Object Number, FriendlyName, SerialNumber, UniqueId, Location, BusType, PartitionStyle, Size, HealthStatus, OperationalStatus, IsOffline, IsReadOnly | Format-List
}
Save-Cmd "physicaldisk_identity_summary.txt" {
    Get-PhysicalDisk | Select-Object FriendlyName, SerialNumber, UniqueId, BusType, MediaType, HealthStatus, OperationalStatus, Size, FirmwareVersion | Format-List
}

"NOTE: No partitioning commands were executed." | Set-Content -LiteralPath (Join-Path $OutDir "disk_info_note.txt")
Write-Host "[setuphelfer] PS1 disk info written to $OutDir"
