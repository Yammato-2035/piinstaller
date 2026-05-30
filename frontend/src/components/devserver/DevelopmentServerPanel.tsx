import React, { useCallback, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import {
  fetchDevServerHealth,
  fetchDevServerNodes,
  fetchDevServerSummary,
  runDevServerCollectBoot,
  runDevServerCollectInventory,
  runDevServerCollectStorage,
  runDevServerSshCheck,
  type DevServerHealth,
  type DevServerNode,
  type DevServerSummary,
} from '../../api/devServerApi'
import { DevelopmentServerPanelView } from './DevelopmentServerPanelView'

export function DevelopmentServerPanel({ refreshSec = 15 }: { refreshSec?: number }) {
  const { t } = useTranslation()
  const [health, setHealth] = useState<DevServerHealth | null>(null)
  const [summary, setSummary] = useState<DevServerSummary | null>(null)
  const [nodes, setNodes] = useState<DevServerNode[]>([])
  const [busyNode, setBusyNode] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const loadData = useCallback(async () => {
    setError(null)
    const [h, s, n] = await Promise.all([
      fetchDevServerHealth(),
      fetchDevServerSummary(),
      fetchDevServerNodes(),
    ])
    setHealth(h)
    setSummary(s)
    setNodes(n)
    if (!h) setError(t('devDashboard.devServer.fetchError'))
  }, [t])

  useEffect(() => {
    void loadData()
    const id = window.setInterval(() => void loadData(), refreshSec * 1000)
    return () => window.clearInterval(id)
  }, [loadData, refreshSec])

  const sshAllowed = Boolean(health?.enabled && health?.ssh_allowed)

  const runAction = async (
    nodeId: string,
    action: 'check' | 'inventory' | 'storage' | 'boot',
  ) => {
    if (!sshAllowed) {
      toast.error(t('devDashboard.devServer.sshDisabled'))
      return
    }
    setBusyNode(nodeId)
    try {
      let result = null
      if (action === 'check') result = await runDevServerSshCheck(nodeId)
      else if (action === 'inventory') result = await runDevServerCollectInventory(nodeId)
      else if (action === 'storage') result = await runDevServerCollectStorage(nodeId)
      else result = await runDevServerCollectBoot(nodeId)
      if (result?.code === 'DEV_SERVER_SSH_ACTION_SUCCESS') {
        toast.success(t('devDashboard.devServer.actionSuccess'))
      } else {
        toast.error(t('devDashboard.devServer.actionFailed'))
      }
      await loadData()
    } finally {
      setBusyNode(null)
    }
  }

  return (
    <DevelopmentServerPanelView
      health={health}
      summary={summary}
      nodes={nodes}
      busyNode={busyNode}
      error={error}
      onRunAction={(nodeId, action) => void runAction(nodeId, action)}
    />
  )
}
