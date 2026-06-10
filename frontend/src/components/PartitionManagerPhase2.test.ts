import React from 'react'
import { describe, expect, it, vi, beforeAll } from 'vitest'
import { renderToStaticMarkup } from 'react-dom/server'
import { I18nextProvider } from 'react-i18next'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import i18n from '../i18n'
import PartitionOverviewCards from './PartitionOverviewCards'
import PartitionGraphicLayout from './PartitionGraphicLayout'
import PartitionSafetyStatusPanel from './PartitionSafetyStatusPanel'
import PartitionHardstopPanel from './PartitionHardstopPanel'
import PartitionRestorePreviewPanel from './PartitionRestorePreviewPanel'
import PartitionDetailTable from './PartitionDetailTable'
import type { DiskInfo, HardstopPreviewResult, ManifestLayoutPreviewResult, RestoreHandoffPreviewResult } from '../api/partitionApi'

beforeAll(async () => {
  await i18n.changeLanguage('de')
})

const sampleDisk: DiskInfo = {
  name: 'sda',
  size_bytes: 2_000_000_000_000,
  size_human: '2 TB',
  vendor: 'Samsung',
  model: '980 Pro',
  display_name: 'Samsung 980 Pro',
  partitions: [
    {
      name: 'sda1',
      size_bytes: 512_000_000,
      size_human: '512 MB',
      fstype: 'vfat',
      mountpoint: '/boot/efi',
      label: 'EFI',
      uuid: 'aaa-bbb',
      parttypename: 'EFI System',
      used_bytes: 100_000_000,
      free_bytes: 412_000_000,
      used_human: '100 MB',
      free_human: '412 MB',
      used_percent: 20,
      is_mounted: true,
      is_system_critical: true,
      display_name: 'EFI',
      fs_info: { name: 'FAT32', beschreibung: '', empfehlung: '', farbe: '#FF9800' },
      children: [],
    },
    {
      name: 'sda2',
      size_bytes: 1_500_000_000_000,
      size_human: '1.5 TB',
      fstype: 'ext4',
      mountpoint: '/',
      label: null,
      uuid: 'ccc-ddd',
      parttypename: 'Linux filesystem',
      used_bytes: 800_000_000_000,
      free_bytes: 700_000_000_000,
      used_human: '800 GB',
      free_human: '700 GB',
      used_percent: 53,
      is_mounted: true,
      is_system_critical: true,
      display_name: 'root',
      fs_info: { name: 'ext4', beschreibung: '', empfehlung: '', farbe: '#4CAF50' },
      children: [],
    },
  ],
}

const hardstopBlocked: HardstopPreviewResult = {
  context: { target_device: '/dev/sda', smart_status: 'ok', write_allowed: false },
  evaluation: {
    status: 'blocked',
    hardstops: [{ code: 'partition.hardstop.target_is_system_disk', message: 'System' }],
    warnings: [{ code: 'partition.info.readonly_phase2', message: 'readonly' }],
    risk_level: 'red',
    write_allowed: false,
    codes: ['partition.hardstop.target_is_system_disk'],
  },
  write_allowed: false,
}

const manifestPreview: ManifestLayoutPreviewResult = {
  status: 'ok',
  source: 'test',
  target_device: '/dev/sdb',
  original_layout: [],
  suggested_layout: [
    { mountpoint: '/boot/efi', fs_type: 'vfat', size: '512M' },
    { mountpoint: '/', fs_type: 'ext4', size: '64G' },
    { mountpoint: '/home', fs_type: 'ext4', size: 'rest' },
  ],
  warnings: [],
  write_allowed: false,
}

const restoreHandoff: RestoreHandoffPreviewResult = {
  status: 'review_required',
  handoff_type: 'partition_restore',
  target_device: '/dev/sdb',
  restore_execution_allowed: false,
  write_allowed: false,
  required_next_gates: ['rescue_stick_gate'],
  codes: [],
}

function wrap(el: React.ReactElement) {
  return renderToStaticMarkup(React.createElement(I18nextProvider, { i18n }, el))
}

describe('PartitionManager Phase 2.1 UI', () => {
  it('zeigt Datenträgerkarten', () => {
    const html = wrap(
      React.createElement(PartitionOverviewCards, {
        disks: [sampleDisk],
        selectedDiskName: 'sda',
        onSelectDisk: vi.fn(),
      }),
    )
    expect(html).toContain('partition-overview-cards')
    expect(html).toContain('Samsung 980 Pro')
    expect(html).toContain('partition-disk-card-sda')
  })

  it('zeigt Hardstop-Panel', () => {
    const html = wrap(
      React.createElement(PartitionHardstopPanel, {
        hardstops: hardstopBlocked.evaluation.hardstops,
        warnings: hardstopBlocked.evaluation.warnings,
      }),
    )
    expect(html).toContain('partition-hardstop-panel')
    expect(html).toContain('partition-hardstop-target_is_system_disk')
  })

  it('zeigt write_allowed=false', () => {
    const html = wrap(
      React.createElement(PartitionSafetyStatusPanel, {
        selectedDevice: '/dev/sda',
        hardstopPreview: hardstopBlocked,
        manifestLayoutPreview: null,
        restoreHandoffPreview: null,
        loading: false,
        error: null,
        onRefresh: vi.fn(),
      }),
    )
    expect(html).toContain('partition-write-allowed-false')
    expect(html).toContain('false')
    expect(html).toContain('partition-write-blocked-banner')
  })

  it('zeigt Restore-Handoff', () => {
    const html = wrap(
      React.createElement(PartitionRestorePreviewPanel, {
        restoreHandoff,
        manifestLayout: manifestPreview,
      }),
    )
    expect(html).toContain('partition-restore-preview-panel')
    expect(html).toContain('restore_execution_allowed=false')
    expect(html).toContain('partition-restore-handoff-status')
  })

  it('zeigt API-Fehler im Sicherheitspanel', () => {
    const html = wrap(
      React.createElement(PartitionSafetyStatusPanel, {
        selectedDevice: '/dev/sda',
        hardstopPreview: null,
        manifestLayoutPreview: null,
        restoreHandoffPreview: null,
        loading: false,
        error: 'Hardstop-Preview fehlgeschlagen: 500',
        onRefresh: vi.fn(),
      }),
    )
    expect(html).toContain('partition-safety-error')
    expect(html).toContain('500')
  })

  it('zeigt Secure-Badge und Sicherheits-Mini-Karten', () => {
    const html = wrap(
      React.createElement(PartitionSafetyStatusPanel, {
        selectedDevice: '/dev/sda',
        hardstopPreview: hardstopBlocked,
        manifestLayoutPreview: null,
        restoreHandoffPreview: null,
        loading: false,
        error: null,
        onRefresh: vi.fn(),
      }),
    )
    expect(html).toContain('partition-secure-badge')
    expect(html).toContain('partition-safety-item-smart')
    expect(html).toContain('partition-safety-item-writeAllowed')
  })

  it('zeigt Restore-Aktualisieren-Button in der Vorschau', () => {
    const html = wrap(
      React.createElement(PartitionRestorePreviewPanel, {
        restoreHandoff,
        manifestLayout: manifestPreview,
        onRefresh: vi.fn(),
      }),
    )
    expect(html).toContain('partition-restore-preview-refresh')
  })

  it('Expertenmodus zeigt technische Details in der Tabelle', () => {
    const html = wrap(
      React.createElement(PartitionDetailTable, {
        disk: sampleDisk,
        selectedPartition: sampleDisk.partitions[0],
        onSelectPartition: vi.fn(),
        experienceLevel: 'advanced',
      }),
    )
    expect(html).toContain('partition-detail-table')
    expect(html).toContain('aaa-bbb')
    expect(html).toContain('/dev/sda1')
  })

  it('Einsteigermodus ohne UUID in der Grafik', () => {
    const html = wrap(
      React.createElement(PartitionGraphicLayout, {
        disk: sampleDisk,
        selectedPartition: sampleDisk.partitions[0],
        onSelectPartition: vi.fn(),
        experienceLevel: 'beginner',
      }),
    )
    expect(html).not.toContain('aaa-bbb')
  })

  it('responsive Layout ohne horizontalen Scroll in Karten', () => {
    const html = wrap(
      React.createElement(PartitionOverviewCards, {
        disks: [sampleDisk],
        selectedDiskName: null,
        onSelectDisk: vi.fn(),
      }),
    )
    expect(html).toContain('partition-overview-cards')
    expect(html).not.toContain('overflow-x-auto')
  })

  it('PartitionManager nutzt 3-Spalten-Grid', () => {
    const src = readFileSync(resolve(__dirname, '../pages/PartitionManager.tsx'), 'utf8')
    expect(src).toContain('partition-manager-three-column')
    expect(src).toContain('xl:grid-cols-12')
  })

  it('PartitionManager enthält keine Schreib-UI-Aufrufe', () => {
    const src = readFileSync(resolve(__dirname, '../pages/PartitionManager.tsx'), 'utf8')
    const forbidden = ['applyQueue', 'ActionQueueBar', 'PartitionWizardModal', 'apply(', 'execute', 'format', 'delete', 'mkfs', 'wipefs', 'sgdisk', 'parted']
    for (const term of forbidden) {
      expect(src.includes(term), `verboten in PartitionManager: ${term}`).toBe(false)
    }
  })
})
