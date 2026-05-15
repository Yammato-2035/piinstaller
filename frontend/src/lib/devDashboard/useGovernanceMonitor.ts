import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { DashboardPayload, ModuleRow } from '../../pages/DevDashboardBody'
import { buildGovernanceMetaPrompt } from './buildGovernancePrompt'
import { buildCockpitAlerts, buildGovernanceMatrix } from './governanceMatrix'
import { appendGovernanceSnapshot, loadGovernanceHistory, saveGovernanceHistory } from './governanceHistory'
import type { CockpitAlert, CockpitViewMode, GovernanceAreaStatus, GovernanceTimelineEvent } from './governanceTypes'
import { loadDevDashboard } from './loadDevDashboard'
import type { DevDashboardCapabilities, DevDashboardDataSource } from './types'
import { readCockpitRefreshSec } from './cockpitWindow'

function tagAreas(
  areas: GovernanceAreaStatus[],
  changedToGreen: GovernanceAreaStatus[],
  regressed: GovernanceAreaStatus[],
): GovernanceAreaStatus[] {
  const greenIds = new Set(changedToGreen.map((a) => a.id))
  const regIds = new Set(regressed.map((a) => a.id))
  const prevMap = new Map<string, GovernanceAreaStatus>()
  for (const a of [...changedToGreen, ...regressed]) {
    if (a.previousStatus) prevMap.set(a.id, a)
  }
  return areas.map((a) => ({
    ...a,
    previousStatus: prevMap.get(a.id)?.previousStatus,
    changedToGreen: greenIds.has(a.id),
    regressed: regIds.has(a.id),
  }))
}

export function useGovernanceMonitor(statusQuery: string) {
  const [loading, setLoading] = useState(true)
  const [dashboard, setDashboard] = useState<DashboardPayload>(null)
  const [modules, setModules] = useState<ModuleRow[]>([])
  const [source, setSource] = useState<DevDashboardDataSource>('unavailable')
  const [apiReachable, setApiReachable] = useState(false)
  const [capabilities, setCapabilities] = useState<DevDashboardCapabilities>({
    runtimeApi: false,
    workspaceAnalysis: false,
    structureHealth: false,
    roadmap: false,
    promptExport: true,
    runtimeTests: false,
  })
  const [workspaceRoot, setWorkspaceRoot] = useState<string | undefined>()
  const [standaloneMetaPrompt, setStandaloneMetaPrompt] = useState<string | undefined>()
  const [areas, setAreas] = useState<GovernanceAreaStatus[]>([])
  const [alerts, setAlerts] = useState<CockpitAlert[]>([])
  const [timeline, setTimeline] = useState<GovernanceTimelineEvent[]>([])
  const [changedToGreen, setChangedToGreen] = useState<GovernanceAreaStatus[]>([])
  const [regressed, setRegressed] = useState<GovernanceAreaStatus[]>([])
  const [viewMode, setViewMode] = useState<CockpitViewMode>('operations')
  const [refreshSec, setRefreshSec] = useState(readCockpitRefreshSec)
  const prevApiRef = useRef<boolean | undefined>(undefined)

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const result = await loadDevDashboard(statusQuery)
      setDashboard(result.dashboard)
      setModules(result.modules)
      setSource(result.source)
      setApiReachable(result.apiReachable)
      setCapabilities(result.capabilities)
      setWorkspaceRoot(result.workspaceRoot)
      setStandaloneMetaPrompt(result.metaPrompt)

      const matrix = buildGovernanceMatrix({
        dashboard: result.dashboard,
        modules: result.modules,
        source: result.source,
        apiReachable: result.apiReachable,
      })
      const rg = (result.dashboard?.runtime_gate as Record<string, unknown>) || {}
      const store = loadGovernanceHistory()
      const history = appendGovernanceSnapshot(store, {
        source: result.source,
        apiReachable: result.apiReachable,
        areas: matrix,
        runtimeGatePassed: rg.passed === true ? true : rg.passed === false ? false : null,
        previousApiReachable: prevApiRef.current,
      })
      prevApiRef.current = result.apiReachable
      saveGovernanceHistory(history.store)

      const tagged = tagAreas(matrix, history.changedToGreen, history.regressed)
      setAreas(tagged)
      setChangedToGreen(history.changedToGreen)
      setRegressed(history.regressed)
      setTimeline(history.store.timeline)
      setAlerts(
        buildCockpitAlerts(tagged, { apiReachable: result.apiReachable, source: result.source }),
      )
    } finally {
      setLoading(false)
    }
  }, [statusQuery])

  useEffect(() => {
    void refresh()
  }, [refresh])

  useEffect(() => {
    const id = window.setInterval(() => void refresh(), refreshSec * 1000)
    return () => window.clearInterval(id)
  }, [refresh, refreshSec])

  const governancePrompt = useMemo(() => {
    if (!dashboard) return ''
    return buildGovernanceMetaPrompt({
      dashboard,
      workspaceRoot: workspaceRoot || '(unknown)',
      source,
      apiReachable,
      areas,
      changedToGreen,
      regressed,
      timeline,
      basePrompt: standaloneMetaPrompt,
    })
  }, [
    dashboard,
    workspaceRoot,
    source,
    apiReachable,
    areas,
    changedToGreen,
    regressed,
    timeline,
    standaloneMetaPrompt,
  ])

  return {
    loading,
    dashboard,
    modules,
    source,
    apiReachable,
    capabilities,
    workspaceRoot,
    areas,
    alerts,
    timeline,
    changedToGreen,
    regressed,
    viewMode,
    setViewMode,
    refreshSec,
    setRefreshSec,
    refresh,
    governancePrompt,
  }
}
