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
    expect(catalog.codes.length).toBeGreaterThanOrEqual(17)
    for (const entry of catalog.codes) {
      expect(entry.write_action_allowed).toBe(false)
    }
  })
})
