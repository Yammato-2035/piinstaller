import { describe, expect, it } from 'vitest'
import {
  buildDccRuntimeStatusModel,
  deriveDeveloperTokenState,
  deriveDccActionMode,
  deriveOperationalActions,
} from './runtimeStatusModel'

describe('runtimeStatusModel', () => {
  it('distinguishes local API reachable from dashboard blocked', () => {
    const model = buildDccRuntimeStatusModel({
      localApiReachable: true,
      dashboardApiReachable: false,
      runtimeGatePassed: false,
      developerTokenState: 'missing',
      dataSource: 'snapshot',
      offlineReason: 'developer_token_required',
    })
    expect(model.localApiReachable).toBe(true)
    expect(model.dashboardApiReachable).toBe(false)
    expect(model.misleadingApiOffline).toBe(true)
    expect(model.actionMode).toBe('read_only')
    expect(model.axes.find((a) => a.key === 'local_api')?.tone).toBe('green')
    expect(model.axes.find((a) => a.key === 'runtime_gate')?.tone).toBe('red')
  })

  it('blocks actions when local API is down', () => {
    const mode = deriveDccActionMode({
      localApiReachable: false,
      dashboardApiReachable: false,
      runtimeGatePassed: false,
      developerTokenState: 'missing',
      dataSource: 'unavailable',
    })
    expect(mode).toBe('blocked')
  })

  it('derives developer token missing vs invalid', () => {
    expect(
      deriveDeveloperTokenState({ storedTokenPresent: false, statusCode: 'DEVELOPER_CAPABILITY_REQUIRED' }),
    ).toBe('missing')
    expect(
      deriveDeveloperTokenState({
        storedTokenPresent: true,
        statusCode: 'DEVELOPER_CAPABILITY_REQUIRED',
        capability: { developer_capability_valid: false },
      }),
    ).toBe('invalid')
    expect(
      deriveDeveloperTokenState({ storedTokenPresent: true, capability: { developer_capability_valid: true } }),
    ).toBe('valid')
  })

  it('blocks deploy backup restore when runtime gate red', () => {
    const ops = deriveOperationalActions({
      localApiReachable: true,
      dashboardApiReachable: true,
      runtimeGatePassed: false,
      developerTokenState: 'valid',
      dataSource: 'runtime_api',
    })
    expect(ops.deploy).toBe('blocked')
    expect(ops.backup).toBe('blocked')
    expect(ops.restore).toBe('blocked')
    expect(ops.reasonKey).toBe('devDashboard.vis.runtime.ops.reason.runtime_gate')
  })

  it('exposes operational actions on model', () => {
    const model = buildDccRuntimeStatusModel({
      localApiReachable: true,
      dashboardApiReachable: false,
      runtimeGatePassed: false,
      developerTokenState: 'missing',
      dataSource: 'snapshot',
      offlineReason: 'developer_token_required',
    })
    expect(model.operationalActions.deploy).toBe('blocked')
  })
})
