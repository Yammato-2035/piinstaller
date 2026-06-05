import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const repoRoot = resolve(__dirname, '../../../../')

describe('windows inspect schema artifacts', () => {
  it('sample JSON has required top-level keys', () => {
    const sample = JSON.parse(
      readFileSync(resolve(repoRoot, 'docs/evidence/windows-rescue/windows_inspect_sample.json'), 'utf8'),
    )
    expect(sample.schema_version).toBe(1)
    expect(sample.source).toBe('setuphelfer_rescue_inspect')
    expect(sample.safety.write_actions_allowed).toBe(false)
    expect(sample.backup_selection.dry_run_only).toBe(true)
  })

  it('diagnostic catalog has write_action_allowed false for all codes', () => {
    const catalog = JSON.parse(
      readFileSync(resolve(repoRoot, 'docs/evidence/windows-rescue/windows_inspect_diagnostic_codes.json'), 'utf8'),
    )
    expect(catalog.codes.length).toBeGreaterThanOrEqual(30)
    for (const entry of catalog.codes) {
      expect(entry.write_action_allowed).toBe(false)
    }
    const bitlockerCodes = catalog.codes.filter((c: { code: string }) => /^WIN-BITLOCKER-00[1-6]$/.test(c.code))
    expect(bitlockerCodes.length).toBe(6)
  })

  it('telemetry schema sample has required envelope fields', () => {
    const sample = JSON.parse(
      readFileSync(resolve(repoRoot, 'docs/evidence/windows-rescue/windows_rescue_telemetry_sample.json'), 'utf8'),
    )
    expect(sample.schema_version).toBe('1.0.0')
    expect(sample.source).toBe('rescue_stick')
    expect(sample.payload_kind).toBe('windows_rescue_inspect')
    expect(sample.privacy_level).toBe('diagnostic_metadata')
    expect(sample.contains_personal_data).toBe(false)
    expect(sample.telemetry_transport.status).toBe('queued_local')
    const json = JSON.stringify(sample)
    expect(json).not.toMatch(/password|file_content|private_key/i)
  })

  it('telemetry sample has no file contents or secrets', () => {
    const sample = JSON.parse(
      readFileSync(resolve(repoRoot, 'docs/evidence/windows-rescue/windows_rescue_telemetry_sample.json'), 'utf8'),
    )
    const forbidden = ['file_content', 'document_content', 'cookie', 'token', 'password', 'ssh_key']
    const json = JSON.stringify(sample).toLowerCase()
    for (const key of forbidden) {
      expect(json).not.toContain(`"${key}"`)
    }
  })

  it('operator readonly sample validates structure', () => {
    const sample = JSON.parse(
      readFileSync(resolve(repoRoot, 'docs/evidence/windows-rescue/windows_inspect_operator_readonly_sample.json'), 'utf8'),
    )
    expect(sample.schema_version).toBe(2)
    expect(sample.hardware.nvme_devices.length).toBe(2)
    expect(sample.bitlocker.access_allowed).toBe(false)
    expect(sample.backup_selection.dry_run_only).toBe(true)
  })
})
