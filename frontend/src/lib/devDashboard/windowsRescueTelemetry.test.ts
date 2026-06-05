import { describe, expect, it } from 'vitest'
import {
  canAccessWindowsFiles,
  canRunBackup,
  classifyBitLockerCodes,
  evaluateInspectCompletion,
  isRepartitionBlocked,
  privacyGuardBlocksTelemetry,
} from './windowsRescueTelemetry'

describe('windowsRescueTelemetry BitLocker', () => {
  const open: Parameters<typeof canAccessWindowsFiles>[0] = {
    bitlocker_active: 'no',
    device_encryption_active: 'no',
    volume_lock_status: 'unlocked',
    recovery_key_required: 'no',
    windows_partition_encrypted: false,
    data_partition_encrypted: false,
    user_profiles_accessible: true,
  }

  it('allows file access when BitLocker inactive and unlocked', () => {
    expect(canAccessWindowsFiles(open)).toBe(true)
    expect(classifyBitLockerCodes(open)).toContain('WIN-BITLOCKER-001')
  })

  it('blocks file access when BitLocker unknown', () => {
    const unknown = { ...open, bitlocker_active: 'unknown' as const, volume_lock_status: 'unknown' as const }
    expect(canAccessWindowsFiles(unknown)).toBe(false)
    expect(classifyBitLockerCodes(unknown)).toContain('WIN-BITLOCKER-005')
  })

  it('blocks backup when volume locked', () => {
    const locked = {
      ...open,
      bitlocker_active: 'yes' as const,
      volume_lock_status: 'locked' as const,
      recovery_key_required: 'yes' as const,
      user_profiles_accessible: false,
    }
    expect(canRunBackup(locked)).toBe(false)
    expect(classifyBitLockerCodes(locked)).toContain('WIN-BITLOCKER-002')
    expect(classifyBitLockerCodes(locked)).toContain('WIN-BITLOCKER-004')
  })

  it('blocks file access when BitLocker suspended', () => {
    const suspended = { ...open, volume_lock_status: 'suspended' as const }
    expect(canAccessWindowsFiles(suspended)).toBe(false)
    expect(classifyBitLockerCodes(suspended)).toContain('WIN-BITLOCKER-006')
  })
})

describe('windowsRescueTelemetry transport', () => {
  it('stays yellow without ACK', () => {
    const r = evaluateInspectCompletion(true, {
      telemetry_status: 'queued_local',
      server_ack_id: null,
      server_ack_at: null,
      payload_hash_sha256: 'abc',
      server_confirmed_hash_sha256: null,
      retry_count: 1,
      last_error: 'TELEMETRY-NETWORK-001',
    })
    expect(r.ampel).toBe('yellow')
    expect(r.classification).toBe('telemetry_not_delivered')
  })

  it('is green with ACK and matching hash', () => {
    const r = evaluateInspectCompletion(true, {
      telemetry_status: 'acknowledged',
      server_ack_id: 'ack-1',
      server_ack_at: '2026-06-05T12:00:00Z',
      payload_hash_sha256: 'deadbeef',
      server_confirmed_hash_sha256: 'deadbeef',
      retry_count: 0,
      last_error: null,
    })
    expect(r.ampel).toBe('green')
  })

  it('is red on hash mismatch', () => {
    const r = evaluateInspectCompletion(true, {
      telemetry_status: 'acknowledged',
      server_ack_id: 'ack-1',
      server_ack_at: '2026-06-05T12:00:00Z',
      payload_hash_sha256: 'aaa',
      server_confirmed_hash_sha256: 'bbb',
      retry_count: 0,
      last_error: null,
    })
    expect(r.ampel).toBe('red')
    expect(r.classification).toBe('telemetry_hash_mismatch')
  })
})

describe('windowsRescueTelemetry privacy and repartition', () => {
  it('blocks telemetry with forbidden content keys', () => {
    expect(privacyGuardBlocksTelemetry({ file_content: 'secret' })).toBe('TELEMETRY-PRIVACY-001')
  })

  it('queues telemetry on network failure stays yellow', () => {
    const r = evaluateInspectCompletion(true, {
      telemetry_status: 'blocked_no_network',
      server_ack_id: null,
      server_ack_at: null,
      payload_hash_sha256: 'abc',
      server_confirmed_hash_sha256: null,
      retry_count: 1,
      last_error: 'TELEMETRY-NETWORK-001',
      queue_depth: 1,
    })
    expect(r.ampel).toBe('yellow')
    expect(r.classification).toBe('telemetry_not_delivered')
  })

  it('blocks repartition without backup and telemetry ack', () => {
    const bitlocker = {
      bitlocker_active: 'no' as const,
      device_encryption_active: 'no' as const,
      volume_lock_status: 'unlocked' as const,
      recovery_key_required: 'no' as const,
      windows_partition_encrypted: false,
      data_partition_encrypted: false,
      user_profiles_accessible: true,
    }
    expect(
      isRepartitionBlocked(false, {
        telemetry_status: 'queued_local',
        server_ack_id: null,
        server_ack_at: null,
        payload_hash_sha256: null,
        server_confirmed_hash_sha256: null,
        retry_count: 0,
        last_error: null,
      }, bitlocker),
    ).toBe(true)
  })

  it('blocks repartition when BitLocker unknown even with ack', () => {
    const bitlocker = {
      bitlocker_active: 'unknown' as const,
      device_encryption_active: 'unknown' as const,
      volume_lock_status: 'unknown' as const,
      recovery_key_required: 'unknown' as const,
      windows_partition_encrypted: null,
      data_partition_encrypted: null,
      user_profiles_accessible: null,
    }
    expect(
      isRepartitionBlocked(true, {
        telemetry_status: 'acknowledged',
        server_ack_id: 'ack-1',
        server_ack_at: '2026-06-05T12:00:00Z',
        payload_hash_sha256: 'deadbeef',
        server_confirmed_hash_sha256: 'deadbeef',
        retry_count: 0,
        last_error: null,
      }, bitlocker),
    ).toBe(true)
  })
})
