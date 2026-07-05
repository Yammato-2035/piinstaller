import type { DevDashboardDataSource } from '../../lib/devDashboard/types'
import type { DccCapabilityStatus } from '../../lib/devDashboard/dccLiveStatus'

export type DeveloperTokenState = 'missing' | 'invalid' | 'valid' | 'unknown'

export type DccActionMode = 'read_only' | 'developer_capable' | 'blocked'

export type OperationalActionId = 'deploy' | 'backup' | 'restore'

export type OperationalActionState = 'allowed' | 'blocked'

export type DccOperationalActions = Record<OperationalActionId, OperationalActionState> & {
  reasonKey: string
}

export type DccRuntimeStatusInput = {
  localApiReachable: boolean
  dashboardApiReachable: boolean
  runtimeGatePassed: boolean | null
  runtimeGateStatus?: string
  developerTokenState: DeveloperTokenState
  dataSource: DevDashboardDataSource
  offlineReason?: string
  capability?: DccCapabilityStatus | null
  safeTestModeLocked?: boolean
  workspaceAheadOfRuntime?: boolean
}

export type DccRuntimeStatusAxis = {
  key: string
  labelKey: string
  valueKey: string
  tone: 'green' | 'yellow' | 'red' | 'gray'
  detailKey?: string
}

export type DccRuntimeStatusModel = {
  localApiReachable: boolean
  dashboardApiReachable: boolean
  runtimeGateBlocked: boolean
  developerTokenState: DeveloperTokenState
  actionMode: DccActionMode
  dataSource: DevDashboardDataSource
  offlineReason?: string
  axes: DccRuntimeStatusAxis[]
  operationalActions: DccOperationalActions
  misleadingApiOffline: boolean
}

export function deriveDeveloperTokenState(params: {
  storedTokenPresent: boolean
  capability?: DccCapabilityStatus | null
  statusCode?: string | null
}): DeveloperTokenState {
  if (params.capability?.developer_capability_valid === true) return 'valid'
  if (params.storedTokenPresent && params.capability?.developer_capability_valid === false) return 'invalid'
  if (params.statusCode === 'DEVELOPER_CAPABILITY_REQUIRED') {
    return params.storedTokenPresent ? 'invalid' : 'missing'
  }
  if (!params.storedTokenPresent) return 'missing'
  return 'unknown'
}

export function deriveDccActionMode(input: DccRuntimeStatusInput): DccActionMode {
  if (!input.localApiReachable) return 'blocked'
  if (input.developerTokenState !== 'valid' || !input.dashboardApiReachable) return 'read_only'
  if (input.runtimeGatePassed !== true) return 'read_only'
  return 'developer_capable'
}

export function deriveOperationalActions(input: DccRuntimeStatusInput): DccOperationalActions {
  const blocked = (reasonKey: string): DccOperationalActions => ({
    deploy: 'blocked',
    backup: 'blocked',
    restore: 'blocked',
    reasonKey,
  })

  if (!input.localApiReachable) return blocked('devDashboard.vis.runtime.ops.reason.api_unreachable')
  if (input.developerTokenState !== 'valid' || !input.dashboardApiReachable) {
    return blocked('devDashboard.vis.runtime.ops.reason.read_only')
  }
  if (input.runtimeGatePassed !== true) return blocked('devDashboard.vis.runtime.ops.reason.runtime_gate')
  if (input.safeTestModeLocked) return blocked('devDashboard.vis.runtime.ops.reason.safe_test_mode')
  if (input.workspaceAheadOfRuntime) return blocked('devDashboard.vis.runtime.ops.reason.deploy_required')

  return {
    deploy: 'allowed',
    backup: 'allowed',
    restore: 'allowed',
    reasonKey: 'devDashboard.vis.runtime.ops.reason.allowed',
  }
}

export function buildDccRuntimeStatusModel(input: DccRuntimeStatusInput): DccRuntimeStatusModel {
  const runtimeGateBlocked = input.runtimeGatePassed !== true
  const actionMode = deriveDccActionMode(input)
  const operationalActions = deriveOperationalActions(input)
  const misleadingApiOffline = input.localApiReachable && !input.dashboardApiReachable

  const localApiTone: DccRuntimeStatusAxis['tone'] = input.localApiReachable ? 'green' : 'red'
  const runtimeGateTone: DccRuntimeStatusAxis['tone'] = !input.localApiReachable
    ? 'gray'
    : runtimeGateBlocked
      ? 'red'
      : 'green'
  const tokenTone: DccRuntimeStatusAxis['tone'] =
    input.developerTokenState === 'valid'
      ? 'green'
      : input.developerTokenState === 'missing'
        ? 'yellow'
        : input.developerTokenState === 'invalid'
          ? 'red'
          : 'gray'
  const actionTone: DccRuntimeStatusAxis['tone'] =
    actionMode === 'developer_capable' ? 'green' : actionMode === 'read_only' ? 'yellow' : 'red'

  const axes: DccRuntimeStatusAxis[] = [
    {
      key: 'local_api',
      labelKey: 'devDashboard.vis.runtime.localApi',
      valueKey: input.localApiReachable
        ? 'devDashboard.vis.runtime.localApiReachable'
        : 'devDashboard.vis.runtime.localApiUnreachable',
      tone: localApiTone,
    },
    {
      key: 'runtime_gate',
      labelKey: 'devDashboard.vis.runtime.runtimeGate',
      valueKey: runtimeGateBlocked
        ? 'devDashboard.vis.runtime.runtimeGateBlocked'
        : 'devDashboard.vis.runtime.runtimeGateOk',
      tone: runtimeGateTone,
      detailKey: input.runtimeGateStatus ? undefined : 'devDashboard.vis.runtime.runtimeGateDetail',
    },
    {
      key: 'developer_token',
      labelKey: 'devDashboard.vis.runtime.developerToken',
      valueKey: `devDashboard.vis.runtime.token.${input.developerTokenState}`,
      tone: tokenTone,
    },
    {
      key: 'action_mode',
      labelKey: 'devDashboard.vis.runtime.actionMode',
      valueKey: `devDashboard.vis.runtime.action.${actionMode}`,
      tone: actionTone,
    },
    {
      key: 'data_source',
      labelKey: 'devDashboard.vis.runtime.dataSource',
      valueKey: `devDashboard.vis.runtime.source.${input.dataSource}`,
      tone: input.dataSource === 'runtime_api' ? 'green' : 'yellow',
    },
  ]

  return {
    localApiReachable: input.localApiReachable,
    dashboardApiReachable: input.dashboardApiReachable,
    runtimeGateBlocked,
    developerTokenState: input.developerTokenState,
    actionMode,
    dataSource: input.dataSource,
    offlineReason: input.offlineReason,
    axes,
    operationalActions,
    misleadingApiOffline,
  }
}
