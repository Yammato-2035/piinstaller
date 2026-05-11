import React, { useState } from 'react'
import { RefreshCw, Database } from 'lucide-react'
import { useTranslation } from 'react-i18next'

import { fetchApi } from '../api'

type ClassificationBlock = {
  system_type?: string
  confidence?: number
  indicators?: string[]
  risk_level?: string
}

type AdvicePathItem = {
  code?: string
  priority?: string
  requires_confirmation?: boolean
}

type AdviceBlock = {
  recommended_paths?: AdvicePathItem[]
}

type WriteSafetyTarget = {
  device?: string
  size?: string
  classification?: string
  write_allowed?: boolean
  reason_code?: string
  risk_level?: string
}

type WriteSafetySummary = {
  policy_code?: string
  targets?: WriteSafetyTarget[]
}

type InspectResult = {
  system?: Record<string, unknown>
  storage?: Record<string, unknown>
  filesystems?: Record<string, unknown>
  boot?: Record<string, unknown>
  network?: Record<string, unknown>
  capabilities?: Record<string, unknown>
  warnings?: Array<Record<string, unknown>>
  errors?: Array<Record<string, unknown>>
  source_modules?: string[]
  classification?: ClassificationBlock
  advice?: AdviceBlock
  write_safety_summary?: WriteSafetySummary
}

type PreflightSource = {
  source_id?: string
  path?: string
  kind?: string
  code?: string
  warnings?: string[]
}

type PreflightPreview = {
  code?: string
  plan_id?: string | null
  confirmation_token?: string | null
  target_device?: string
  target_reason?: string
  requires_confirmation?: boolean
  sources?: PreflightSource[]
}

type PreflightExecute = {
  code?: string
  plan_id?: string
  archive_path?: string
  backup_code?: string
  verify_code?: string
  target_reason?: string
}

type RescuePreviewResponse = {
  code?: string
  preview_id?: string
  confirmation_token?: string | null
  target?: Record<string, unknown>
  backup?: Record<string, unknown>
  safety?: Record<string, unknown>
  verify?: Record<string, unknown>
  preview?: Record<string, unknown>
  preflight?: Record<string, unknown>
  warnings?: string[]
  errors?: string[]
}

const InspectRun: React.FC = () => {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(false)
  const [errorCode, setErrorCode] = useState<string | null>(null)
  const [data, setData] = useState<InspectResult | null>(null)

  const [preflightLoading, setPreflightLoading] = useState(false)
  const [preflightCode, setPreflightCode] = useState<string | null>(null)
  const [preflightSources, setPreflightSources] = useState<PreflightSource[]>([])
  const [selectedTarget, setSelectedTarget] = useState<string>('')
  const [preview, setPreview] = useState<PreflightPreview | null>(null)
  const [tokenInput, setTokenInput] = useState('')
  const [allowEmptyTarget, setAllowEmptyTarget] = useState(false)
  const [executeResult, setExecuteResult] = useState<PreflightExecute | null>(null)

  const [rescueBackupPath, setRescueBackupPath] = useState('')
  const [rescueTargetDevice, setRescueTargetDevice] = useState('')
  const [rescueTargetPath, setRescueTargetPath] = useState('')
  const [rescueTokenInput, setRescueTokenInput] = useState('')
  const [rescuePreview, setRescuePreview] = useState<RescuePreviewResponse | null>(null)
  const [rescueExecuteResult, setRescueExecuteResult] = useState<Record<string, unknown> | null>(null)
  const [rescueLoading, setRescueLoading] = useState(false)
  const [recoveryPlanResult, setRecoveryPlanResult] = useState<Record<string, unknown> | null>(null)
  const [recoverySelectedSteps, setRecoverySelectedSteps] = useState<string[]>([])
  const [recoverySessionResult, setRecoverySessionResult] = useState<Record<string, unknown> | null>(null)
  const [recoveryExecuteResult, setRecoveryExecuteResult] = useState<Record<string, unknown> | null>(null)
  const [recoveryActivationResult, setRecoveryActivationResult] = useState<Record<string, unknown> | null>(null)
  const [recoveryActivationSelectedSteps, setRecoveryActivationSelectedSteps] = useState<string[]>([])
  const [recoveryActivationSessionResult, setRecoveryActivationSessionResult] = useState<Record<string, unknown> | null>(null)
  const [recoveryActivationExecuteResult, setRecoveryActivationExecuteResult] = useState<Record<string, unknown> | null>(null)
  const [recoveryActivationSshPublicKey, setRecoveryActivationSshPublicKey] = useState('')
  const [recoveryActivationAllowLanBind, setRecoveryActivationAllowLanBind] = useState(false)
  const [repairActionCode, setRepairActionCode] = useState('')
  const [repairSessionId, setRepairSessionId] = useState('')
  const [repairToken, setRepairToken] = useState('')
  const [repairExecuteResult, setRepairExecuteResult] = useState<Record<string, unknown> | null>(null)
  const [deployPlanResult, setDeployPlanResult] = useState<Record<string, unknown> | null>(null)
  const [deployPlanLoading, setDeployPlanLoading] = useState(false)
  const [deploySelectedProfile, setDeploySelectedProfile] = useState('')
  const [deploySessionResult, setDeploySessionResult] = useState<Record<string, unknown> | null>(null)
  const [deployExecuteResult, setDeployExecuteResult] = useState<Record<string, unknown> | null>(null)
  const [deployPreviewResult, setDeployPreviewResult] = useState<Record<string, unknown> | null>(null)
  const [deployPrepLoading, setDeployPrepLoading] = useState(false)
  const [deployOsSourceType, setDeployOsSourceType] = useState('local_image')
  const [deployOsSourceName, setDeployOsSourceName] = useState('ubuntu-server-lts')
  const [deployOsSourceUrl, setDeployOsSourceUrl] = useState('')
  const [deployOsSourceChecksum, setDeployOsSourceChecksum] = useState('')
  const [deploySourcesResult, setDeploySourcesResult] = useState<Record<string, unknown> | null>(null)
  const [deploySourceSelectedId, setDeploySourceSelectedId] = useState('')
  const [deploySourceEvalResult, setDeploySourceEvalResult] = useState<Record<string, unknown> | null>(null)
  const [deployCachePlanResult, setDeployCachePlanResult] = useState<Record<string, unknown> | null>(null)
  const [deployCacheSessionResult, setDeployCacheSessionResult] = useState<Record<string, unknown> | null>(null)
  const [deployCacheExecuteResult, setDeployCacheExecuteResult] = useState<Record<string, unknown> | null>(null)
  const [deployImageInspectResult, setDeployImageInspectResult] = useState<Record<string, unknown> | null>(null)
  const [deployWritePlanResult, setDeployWritePlanResult] = useState<Record<string, unknown> | null>(null)
  const [deployWriteSessionResult, setDeployWriteSessionResult] = useState<Record<string, unknown> | null>(null)
  const [deployWriteExecuteResult, setDeployWriteExecuteResult] = useState<Record<string, unknown> | null>(null)
  const [deployFinalConfirmationResult, setDeployFinalConfirmationResult] = useState<Record<string, unknown> | null>(null)
  const [deployFinalCheckResult, setDeployFinalCheckResult] = useState<Record<string, unknown> | null>(null)
  const [deployHarnessTargetPath, setDeployHarnessTargetPath] = useState('/tmp/setuphelfer-deploy-test/target.img')
  const [deployHarnessSessionResult, setDeployHarnessSessionResult] = useState<Record<string, unknown> | null>(null)
  const [deployHarnessExecuteResult, setDeployHarnessExecuteResult] = useState<Record<string, unknown> | null>(null)
  const [deployHardwareGateResult, setDeployHardwareGateResult] = useState<Record<string, unknown> | null>(null)
  const [deployHardwareProtocolResult, setDeployHardwareProtocolResult] = useState<Record<string, unknown> | null>(null)

  const runInspect = async () => {
    setLoading(true)
    setErrorCode(null)
    try {
      const response = await fetchApi('/api/inspect/run')
      if (!response.ok) {
        setErrorCode(`inspect.http.${response.status}`)
        return
      }
      const payload = (await response.json()) as InspectResult
      setData(payload)
      if (!selectedTarget && (payload.write_safety_summary?.targets ?? []).length > 0) {
        const first = payload.write_safety_summary?.targets?.[0]?.device
        if (first) setSelectedTarget(first)
      }
      if (!rescueTargetDevice && (payload.write_safety_summary?.targets ?? []).length > 0) {
        const firstRescue = payload.write_safety_summary?.targets?.[0]?.device
        if (firstRescue) setRescueTargetDevice(firstRescue)
      }
    } catch {
      setErrorCode('inspect.network.unreachable')
    } finally {
      setLoading(false)
    }
  }

  const loadPreflightSources = async () => {
    setPreflightLoading(true)
    setPreflightCode(null)
    try {
      const r = await fetchApi('/api/preflight/sources')
      if (!r.ok) {
        setPreflightCode(`preflight.http.${r.status}`)
        return
      }
      const payload = (await r.json()) as { code?: string; sources?: PreflightSource[] }
      setPreflightCode(payload.code ?? null)
      setPreflightSources(payload.sources ?? [])
    } catch {
      setPreflightCode('preflight.network.unreachable')
    } finally {
      setPreflightLoading(false)
    }
  }

  const createPreview = async () => {
    if (!selectedTarget) {
      setPreflightCode('preflight.target.missing')
      return
    }
    setPreflightLoading(true)
    setExecuteResult(null)
    try {
      const r = await fetchApi('/api/preflight/backup/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_device: selectedTarget }),
      })
      const payload = (await r.json()) as PreflightPreview
      setPreview(payload)
      setPreflightCode(payload.code ?? `preflight.http.${r.status}`)
      if (payload.confirmation_token) {
        setTokenInput(payload.confirmation_token)
      }
    } catch {
      setPreflightCode('preflight.network.unreachable')
    } finally {
      setPreflightLoading(false)
    }
  }

  const executePreflightBackup = async () => {
    if (!preview?.plan_id) {
      setPreflightCode('preflight.plan.missing')
      return
    }
    setPreflightLoading(true)
    try {
      const r = await fetchApi('/api/preflight/backup/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          plan_id: preview.plan_id,
          confirmation_token: tokenInput,
          allow_empty_target: allowEmptyTarget,
        }),
      })
      const payload = (await r.json()) as PreflightExecute
      setExecuteResult(payload)
      setPreflightCode(payload.code ?? `preflight.http.${r.status}`)
    } catch {
      setPreflightCode('preflight.network.unreachable')
    } finally {
      setPreflightLoading(false)
    }
  }

  const runRescuePreview = async () => {
    if (!rescueBackupPath || !rescueTargetDevice) {
      setRescuePreview({ code: 'RESCUE_PREVIEW_FAILED', errors: ['RESCUE_UNKNOWN_ERROR'] })
      return
    }
    setRescueLoading(true)
    try {
      const r = await fetchApi('/api/rescue/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          backup_path: rescueBackupPath,
          target_device: rescueTargetDevice,
          preflight_plan_id: preview?.plan_id ?? '',
        }),
      })
      const payload = (await r.json()) as RescuePreviewResponse
      setRescuePreview(payload)
      setRescueExecuteResult(null)
      if (payload.confirmation_token) setRescueTokenInput(String(payload.confirmation_token))
    } catch {
      setRescuePreview({ code: 'RESCUE_PREVIEW_FAILED', errors: ['RESCUE_UNKNOWN_ERROR'] })
    } finally {
      setRescueLoading(false)
    }
  }

  const runRescueExecute = async () => {
    if (!rescuePreview?.preview_id) return
    setRescueLoading(true)
    try {
      const r = await fetchApi('/api/rescue/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          preview_id: rescuePreview.preview_id,
          confirmation_token: rescueTokenInput,
          backup_path: rescueBackupPath,
          target_device: rescueTargetDevice,
          target_path: rescueTargetPath,
          preflight_plan_id: preview?.plan_id ?? '',
        }),
      })
      const payload = (await r.json()) as Record<string, unknown>
      setRescueExecuteResult(payload)
    } catch {
      setRescueExecuteResult({ code: 'RESCUE_EXECUTE_FAILED' })
    } finally {
      setRescueLoading(false)
    }
  }

  const createRepairSession = async () => {
    const rp = (rescueExecuteResult?.boot_repair_plan ?? {}) as Record<string, unknown>
    if (!repairActionCode || !rescueTargetPath) return
    setRescueLoading(true)
    try {
      const r = await fetchApi('/api/boot/repair/session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_path: rescueTargetPath,
          selected_action_code: repairActionCode,
          inspect: data ?? {},
          post_verify: (rescueExecuteResult?.post_verify ?? {}) as Record<string, unknown>,
          boot_capability: (rescueExecuteResult?.boot_capability ?? {}) as Record<string, unknown>,
          boot_repair_plan: rp,
        }),
      })
      const payload = (await r.json()) as Record<string, unknown>
      setRepairSessionId(String(payload.repair_session_id ?? ''))
      setRepairToken(String(payload.confirmation_token ?? ''))
      setRepairExecuteResult(payload)
    } catch {
      setRepairExecuteResult({ code: 'BOOT_REPAIR_EXECUTE_FAILED' })
    } finally {
      setRescueLoading(false)
    }
  }

  const runRepairExecute = async () => {
    if (!repairSessionId || !repairToken || !repairActionCode || !rescueTargetPath) return
    setRescueLoading(true)
    try {
      const r = await fetchApi('/api/boot/repair/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repair_session_id: repairSessionId,
          confirmation_token: repairToken,
          action_code: repairActionCode,
          target_path: rescueTargetPath,
        }),
      })
      const payload = (await r.json()) as Record<string, unknown>
      setRepairExecuteResult(payload)
    } catch {
      setRepairExecuteResult({ code: 'BOOT_REPAIR_EXECUTE_FAILED' })
    } finally {
      setRescueLoading(false)
    }
  }


  const runRecoveryMinimalPlan = async () => {
    if (!rescueTargetPath) return
    setRescueLoading(true)
    try {
      const r = await fetchApi('/api/recovery/minimal/plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_path: rescueTargetPath,
          inspect_result: data ?? {},
          boot_capability: (rescueExecuteResult?.boot_capability ?? {}) as Record<string, unknown>,
          post_restore: (rescueExecuteResult?.post_verify ?? {}) as Record<string, unknown>,
          safety_summary: data?.write_safety_summary ?? {},
        }),
      })
      const payload = (await r.json()) as Record<string, unknown>
      setRecoveryPlanResult(payload)
    } catch {
      setRecoveryPlanResult({ code: 'RECOVERY_MINIMAL_PLAN_NOT_APPLICABLE' })
    } finally {
      setRescueLoading(false)
    }
  }


  const createRecoveryMinimalSession = async () => {
    if (!rescueTargetPath || !recoveryPlanResult || recoverySelectedSteps.length === 0) return
    setRescueLoading(true)
    try {
      const r = await fetchApi('/api/recovery/minimal/session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_path: rescueTargetPath,
          selected_steps: recoverySelectedSteps,
          plan: (recoveryPlanResult.plan ?? {}) as Record<string, unknown>,
        }),
      })
      const payload = (await r.json()) as Record<string, unknown>
      setRecoverySessionResult(payload)
    } catch {
      setRecoverySessionResult({ code: 'RECOVERY_MINIMAL_PLAN_INVALID' })
    } finally {
      setRescueLoading(false)
    }
  }

  const executeRecoveryMinimalPrep = async () => {
    const sid = String(recoverySessionResult?.session_id ?? '')
    const tok = String(recoverySessionResult?.confirmation_token ?? '')
    if (!sid || !tok || !recoveryPlanResult) return
    setRescueLoading(true)
    try {
      const r = await fetchApi('/api/recovery/minimal/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sid,
          confirmation_token: tok,
          target_path: rescueTargetPath,
          plan: (recoveryPlanResult.plan ?? {}) as Record<string, unknown>,
        }),
      })
      const payload = (await r.json()) as Record<string, unknown>
      setRecoveryExecuteResult(payload)
    } catch {
      setRecoveryExecuteResult({ code: 'RECOVERY_MINIMAL_EXECUTE_BLOCKED' })
    } finally {
      setRescueLoading(false)
    }
  }


  const runRecoveryActivationPlan = async () => {
    if (!rescueTargetPath) return
    setRescueLoading(true)
    try {
      const r = await fetchApi('/api/recovery/activation/plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_path: rescueTargetPath,
          inspect_result: data ?? {},
          post_restore: (rescueExecuteResult?.post_verify ?? {}) as Record<string, unknown>,
          boot_capability: (rescueExecuteResult?.boot_capability ?? {}) as Record<string, unknown>,
          recovery_minimal_plan: (recoveryPlanResult?.plan ?? {}) as Record<string, unknown>,
          safety_summary: data?.write_safety_summary ?? {},
        }),
      })
      const payload = (await r.json()) as Record<string, unknown>
      setRecoveryActivationResult(payload)
    } catch {
      setRecoveryActivationResult({ code: 'RECOVERY_ACTIVATION_PLAN_NOT_APPLICABLE' })
    } finally {
      setRescueLoading(false)
    }
  }


  const createRecoveryActivationSession = async () => {
    if (!rescueTargetPath || !recoveryActivationResult || recoveryActivationSelectedSteps.length === 0) return
    setRescueLoading(true)
    try {
      const r = await fetchApi('/api/recovery/activation/session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_path: rescueTargetPath,
          selected_steps: recoveryActivationSelectedSteps,
          plan: (recoveryActivationResult.plan ?? {}) as Record<string, unknown>,
        }),
      })
      const payload = (await r.json()) as Record<string, unknown>
      setRecoveryActivationSessionResult(payload)
    } catch {
      setRecoveryActivationSessionResult({ code: 'RECOVERY_ACTIVATION_PLAN_INVALID' })
    } finally {
      setRescueLoading(false)
    }
  }

  const executeRecoveryActivationPrep = async () => {
    const sid = String(recoveryActivationSessionResult?.activation_session_id ?? '')
    const tok = String(recoveryActivationSessionResult?.confirmation_token ?? '')
    if (!sid || !tok || !recoveryActivationResult) return
    setRescueLoading(true)
    try {
      const r = await fetchApi('/api/recovery/activation/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          activation_session_id: sid,
          confirmation_token: tok,
          target_path: rescueTargetPath,
          plan: (recoveryActivationResult.plan ?? {}) as Record<string, unknown>,
          ssh_public_key: recoveryActivationSshPublicKey,
          allow_lan_backend_bind: recoveryActivationAllowLanBind,
        }),
      })
      const payload = (await r.json()) as Record<string, unknown>
      setRecoveryActivationExecuteResult(payload)
    } catch {
      setRecoveryActivationExecuteResult({ code: 'RECOVERY_ACTIVATION_EXECUTE_BLOCKED' })
    } finally {
      setRescueLoading(false)
    }
  }

  const osHints = (data?.capabilities?.os_hints ?? {}) as Record<string, unknown>
  const classification = data?.classification
  const advicePaths = (data?.advice?.recommended_paths ?? []) as AdvicePathItem[]
  const safetyTargets = (data?.write_safety_summary?.targets ?? []) as WriteSafetyTarget[]

  const trSystemType = (code: string) =>
    t(`system_type.${code}`, { defaultValue: code })
  const trRisk = (code: string) =>
    t(`risk_level.${code}`, { defaultValue: code })
  const trAdvice = (fullCode: string) => t(fullCode, { defaultValue: fullCode })
  const trPriority = (code: string) =>
    t(`advice.priority.${code}`, { defaultValue: code })

  const labelSafetyState = (c: string) => {
    const x = String(c || '').toLowerCase()
    if (x === 'allowed') return t('safety.state.allowed')
    if (x === 'warning') return t('safety.state.warning')
    if (x === 'blocked') return t('safety.state.blocked')
    return c || '-'
  }

  const trSafetyReason = (code: string) =>
    t(`safety.reason.${code}`, { defaultValue: code })

  const trDeployCode = (code: string | null | undefined) =>
    code ? t(`deploy.codes.${code}`, { defaultValue: code }) : '-'

  const trDeployPlanStatus = (st: string) =>
    t(`deploy.plan.status.${st}`, { defaultValue: st })

  const trDeployHwClass = (prefix: string, v: string) =>
    t(`${prefix}.${v}`, { defaultValue: v })

  const runDeployPlan = async () => {
    if (!data) return
    setDeployPlanLoading(true)
    setDeployPlanResult(null)
    setDeploySessionResult(null)
    setDeployExecuteResult(null)
    setDeployPreviewResult(null)
    try {
      const r = await fetchApi('/api/deploy/plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          inspect_result: data as unknown as Record<string, unknown>,
          safety_summary: (data.write_safety_summary ?? {}) as Record<string, unknown>,
          classification: (data.classification ?? {}) as Record<string, unknown>,
        }),
      })
      const payload = (await r.json()) as Record<string, unknown>
      setDeployPlanResult(payload)
      const planObj = (payload.plan ?? {}) as Record<string, unknown>
      const rec = (planObj.recommended_profile ?? {}) as Record<string, unknown>
      if (typeof rec.code === 'string' && rec.code) {
        setDeploySelectedProfile(String(rec.code))
      } else {
        setDeploySelectedProfile('')
      }
    } catch {
      setDeployPlanResult({ code: 'DEPLOY_PLAN_NOT_APPLICABLE' })
    } finally {
      setDeployPlanLoading(false)
    }
  }

  const createDeploySession = async () => {
    if (!deployPlanResult || !rescueTargetDevice || !deploySelectedProfile) return
    setDeployPrepLoading(true)
    setDeploySessionResult(null)
    try {
      const r = await fetchApi('/api/deploy/session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_device: rescueTargetDevice,
          selected_profile: deploySelectedProfile,
          plan: (deployPlanResult.plan ?? {}) as Record<string, unknown>,
        }),
      })
      const payload = (await r.json()) as Record<string, unknown>
      setDeploySessionResult(payload)
    } catch {
      setDeploySessionResult({ code: 'DEPLOY_PLAN_INVALID' })
    } finally {
      setDeployPrepLoading(false)
    }
  }

  const executeDeployPrep = async () => {
    const sid = String(deploySessionResult?.deploy_session_id ?? '')
    const tok = String(deploySessionResult?.confirmation_token ?? '')
    if (!sid || !tok || !deployPlanResult || !deploySelectedProfile || !rescueTargetDevice) return
    setDeployPrepLoading(true)
    setDeployExecuteResult(null)
    try {
      const r = await fetchApi('/api/deploy/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          deploy_session_id: sid,
          confirmation_token: tok,
          target_device: rescueTargetDevice,
          selected_profile: deploySelectedProfile,
          plan: (deployPlanResult.plan ?? {}) as Record<string, unknown>,
        }),
      })
      const payload = (await r.json()) as Record<string, unknown>
      setDeployExecuteResult(payload)
    } catch {
      setDeployExecuteResult({ code: 'DEPLOY_EXECUTE_BLOCKED' })
    } finally {
      setDeployPrepLoading(false)
    }
  }

  const runDeployPreview = async () => {
    const sid = String(deploySessionResult?.deploy_session_id ?? '')
    const tok = String(deploySessionResult?.confirmation_token ?? '')
    if (!sid || !tok || !deployPlanResult || !deploySelectedProfile || !rescueTargetDevice) return
    setDeployPrepLoading(true)
    setDeployPreviewResult(null)
    try {
      const r = await fetchApi('/api/deploy/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          deploy_session_id: sid,
          confirmation_token: tok,
          target_device: rescueTargetDevice,
          selected_profile: deploySelectedProfile,
          plan: (deployPlanResult.plan ?? {}) as Record<string, unknown>,
          os_source: {
            type: deployOsSourceType,
            name: deployOsSourceName,
            url: deployOsSourceUrl,
            checksum: deployOsSourceChecksum,
          },
        }),
      })
      const payload = (await r.json()) as Record<string, unknown>
      setDeployPreviewResult(payload)
    } catch {
      setDeployPreviewResult({ code: 'DEPLOY_PREVIEW_FAILED' })
    } finally {
      setDeployPrepLoading(false)
    }
  }

  const loadDeploySources = async () => {
    setDeployPrepLoading(true)
    try {
      const r = await fetchApi('/api/deploy/sources')
      const payload = (await r.json()) as Record<string, unknown>
      setDeploySourcesResult(payload)
      const reg = (payload.registry ?? {}) as Record<string, unknown>
      const srcs = Array.isArray(reg.sources) ? (reg.sources as Record<string, unknown>[]) : []
      if (srcs.length > 0) {
        setDeploySourceSelectedId(String(srcs[0].source_id ?? ''))
      }
    } catch {
      setDeploySourcesResult({ code: 'DEPLOY_SOURCE_REGISTRY_FAILED' })
    } finally {
      setDeployPrepLoading(false)
    }
  }

  const evaluateDeploySource = async () => {
    if (!deploySourceSelectedId || !data || !deployPlanResult) return
    setDeployPrepLoading(true)
    try {
      const r = await fetchApi('/api/deploy/source/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_id: deploySourceSelectedId,
          inspect_result: data as unknown as Record<string, unknown>,
          deploy_plan: (deployPlanResult.plan ?? {}) as Record<string, unknown>,
        }),
      })
      const payload = (await r.json()) as Record<string, unknown>
      setDeploySourceEvalResult(payload)
    } catch {
      setDeploySourceEvalResult({ code: 'DEPLOY_SOURCE_EVALUATED', errors: ['DEPLOY_SOURCE_EVALUATION_FAILED'] })
    } finally {
      setDeployPrepLoading(false)
    }
  }

  const runDeployCachePlan = async () => {
    if (!deploySourceEvalResult || !deployPlanResult || !data) return
    setDeployPrepLoading(true)
    try {
      const src = (deploySourceEvalResult.source ?? {}) as Record<string, unknown>
      const r = await fetchApi('/api/deploy/cache/plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source: src,
          deploy_plan: (deployPlanResult.plan ?? {}) as Record<string, unknown>,
          inspect_result: data as unknown as Record<string, unknown>,
        }),
      })
      const payload = (await r.json()) as Record<string, unknown>
      setDeployCachePlanResult(payload)
      setDeployCacheSessionResult(null)
      setDeployCacheExecuteResult(null)
    } catch {
      setDeployCachePlanResult({ code: 'DEPLOY_CACHE_PLAN_NOT_APPLICABLE' })
    } finally {
      setDeployPrepLoading(false)
    }
  }

  const createDeployCacheSession = async () => {
    if (!deployCachePlanResult || !deploySourceEvalResult) return
    setDeployPrepLoading(true)
    try {
      const r = await fetchApi('/api/deploy/cache/session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source: (deploySourceEvalResult.source ?? {}) as Record<string, unknown>,
          cache_plan: (deployCachePlanResult.plan ?? {}) as Record<string, unknown>,
        }),
      })
      const payload = (await r.json()) as Record<string, unknown>
      setDeployCacheSessionResult(payload)
    } catch {
      setDeployCacheSessionResult({ code: 'DEPLOY_CACHE_PLAN_INVALID' })
    } finally {
      setDeployPrepLoading(false)
    }
  }

  const executeDeployCacheLocal = async () => {
    const sid = String(deployCacheSessionResult?.cache_session_id ?? '')
    const tok = String(deployCacheSessionResult?.confirmation_token ?? '')
    if (!sid || !tok || !deployCachePlanResult || !deploySourceEvalResult) return
    setDeployPrepLoading(true)
    try {
      const r = await fetchApi('/api/deploy/cache/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          cache_session_id: sid,
          confirmation_token: tok,
          source: (deploySourceEvalResult.source ?? {}) as Record<string, unknown>,
          cache_plan: (deployCachePlanResult.plan ?? {}) as Record<string, unknown>,
        }),
      })
      const payload = (await r.json()) as Record<string, unknown>
      setDeployCacheExecuteResult(payload)
    } catch {
      setDeployCacheExecuteResult({ code: 'DEPLOY_CACHE_EXECUTE_FAILED' })
    } finally {
      setDeployPrepLoading(false)
    }
  }

  const inspectDeployImage = async () => {
    if (!deploySourceEvalResult) return
    setDeployPrepLoading(true)
    try {
      const src = (deploySourceEvalResult.source ?? {}) as Record<string, unknown>
      const localPath = String(src.local_path ?? '')
      const ext = localPath.split('.').pop() || 'unknown'
      const r = await fetchApi('/api/deploy/image/inspect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image_path: localPath,
          expected_checksum: String(src.checksum ?? ''),
          expected_architecture: String(src.architecture ?? 'unknown'),
          expected_type: ext === 'img' || ext === 'iso' || ext === 'qcow2' ? ext : 'unknown',
        }),
      })
      const payload = (await r.json()) as Record<string, unknown>
      setDeployImageInspectResult(payload)
    } catch {
      setDeployImageInspectResult({ code: 'DEPLOY_IMAGE_INSPECT_FAILED' })
    } finally {
      setDeployPrepLoading(false)
    }
  }

  const runDeployWritePlan = async () => {
    if (!deploySessionResult || !deployPreviewResult || !deployImageInspectResult || !data) return
    setDeployPrepLoading(true)
    try {
      const r = await fetchApi('/api/deploy/write/plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          deploy_session: deploySessionResult,
          deploy_preview: deployPreviewResult,
          image_inspect: deployImageInspectResult,
          inspect_result: data,
          safety_summary: data.write_safety_summary ?? {},
        }),
      })
      const payload = (await r.json()) as Record<string, unknown>
      setDeployWritePlanResult(payload)
    } catch {
      setDeployWritePlanResult({ code: 'DEPLOY_WRITE_PLAN_NOT_APPLICABLE' })
    } finally {
      setDeployPrepLoading(false)
    }
  }

  const createDeployWriteSession = async () => {
    if (!deployWritePlanResult || !deployImageInspectResult || !deploySessionResult) return
    setDeployPrepLoading(true)
    try {
      const plan = (deployWritePlanResult.plan ?? {}) as Record<string, unknown>
      const conf = Array.isArray(plan.required_confirmations) ? (plan.required_confirmations as string[]) : []
      const r = await fetchApi('/api/deploy/write/session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_device: String(deploySessionResult.target_device ?? ''),
          selected_profile: String(deploySessionResult.selected_profile ?? ''),
          image_inspect: deployImageInspectResult,
          write_plan: plan,
          confirmations: conf,
        }),
      })
      const payload = (await r.json()) as Record<string, unknown>
      setDeployWriteSessionResult(payload)
    } catch {
      setDeployWriteSessionResult({ code: 'DEPLOY_WRITE_SESSION_BLOCKED' })
    } finally {
      setDeployPrepLoading(false)
    }
  }

  const runDeployWriteExecuteDryrun = async () => {
    if (!deployWriteSessionResult || !deployWritePlanResult || !deploySessionResult) return
    setDeployPrepLoading(true)
    try {
      const plan = (deployWritePlanResult.plan ?? {}) as Record<string, unknown>
      const img = (plan.image ?? {}) as Record<string, unknown>
      const r = await fetchApi('/api/deploy/write/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          write_session_id: String(deployWriteSessionResult.write_session_id ?? ''),
          confirmation_token: String(deployWriteSessionResult.confirmation_token ?? ''),
          target_device: String(deploySessionResult.target_device ?? ''),
          selected_profile: String(deploySessionResult.selected_profile ?? ''),
          image_path: String(img.path ?? ''),
          write_plan: plan,
        }),
      })
      const payload = (await r.json()) as Record<string, unknown>
      setDeployWriteExecuteResult(payload)
    } catch {
      setDeployWriteExecuteResult({ code: 'DEPLOY_WRITE_EXECUTE_BLOCKED' })
    } finally {
      setDeployPrepLoading(false)
    }
  }

  const createFinalConfirmationSession = async () => {
    if (!deployWriteExecuteResult || !deployWritePlanResult || !data) return
    setDeployPrepLoading(true)
    try {
      const r = await fetchApi('/api/deploy/final-confirmation/session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          write_execute_result: deployWriteExecuteResult,
          write_plan: (deployWritePlanResult.plan ?? {}) as Record<string, unknown>,
          inspect_result: data,
          confirmations: [
            'CONFIRM_ALL_DATA_WILL_BE_DESTROYED',
            'CONFIRM_TARGET_DEVICE_AGAIN',
            'CONFIRM_NO_SYSTEM_DISK',
            'CONFIRM_NO_WINDOWS_DUALBOOT',
            'CONFIRM_IMAGE_AND_PROFILE_MATCH',
            'CONFIRM_FINAL_DEPLOY_DRYRUN',
          ],
        }),
      })
      const payload = (await r.json()) as Record<string, unknown>
      setDeployFinalConfirmationResult(payload)
    } catch {
      setDeployFinalConfirmationResult({ code: 'DEPLOY_FINAL_CONFIRMATION_INVALID' })
    } finally {
      setDeployPrepLoading(false)
    }
  }

  const runFinalConfirmationCheck = async () => {
    if (!deployFinalConfirmationResult) return
    setDeployPrepLoading(true)
    try {
      const r = await fetchApi('/api/deploy/final-confirmation/check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          final_confirmation_id: String(deployFinalConfirmationResult.final_confirmation_id ?? ''),
          confirmation_token: String(deployFinalConfirmationResult.confirmation_token ?? ''),
          target_snapshot: (deployFinalConfirmationResult.target_snapshot ?? {}) as Record<string, unknown>,
        }),
      })
      const payload = (await r.json()) as Record<string, unknown>
      setDeployFinalCheckResult(payload)
    } catch {
      setDeployFinalCheckResult({ code: 'DEPLOY_FINAL_CONFIRMATION_BLOCKED' })
    } finally {
      setDeployPrepLoading(false)
    }
  }

  const createHarnessSession = async () => {
    if (!deployFinalCheckResult || !deployImageInspectResult) return
    setDeployPrepLoading(true)
    try {
      const r = await fetchApi('/api/deploy/write/harness/session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          final_confirmation_result: deployFinalCheckResult,
          image_inspect: deployImageInspectResult,
          test_target_path: deployHarnessTargetPath,
        }),
      })
      const payload = (await r.json()) as Record<string, unknown>
      setDeployHarnessSessionResult(payload)
    } catch {
      setDeployHarnessSessionResult({ code: 'DEPLOY_WRITE_HARNESS_BLOCKED' })
    } finally {
      setDeployPrepLoading(false)
    }
  }

  const runHarnessExecute = async () => {
    if (!deployHarnessSessionResult || !deployWritePlanResult) return
    setDeployPrepLoading(true)
    try {
      const wp = (deployWritePlanResult.plan ?? {}) as Record<string, unknown>
      const img = (wp.image ?? {}) as Record<string, unknown>
      const r = await fetchApi('/api/deploy/write/harness/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          harness_session_id: String(deployHarnessSessionResult.harness_session_id ?? ''),
          confirmation_token: String(deployHarnessSessionResult.confirmation_token ?? ''),
          image_path: String(img.path ?? ''),
          test_target_path: deployHarnessTargetPath,
          max_bytes: 1024 * 1024,
        }),
      })
      const payload = (await r.json()) as Record<string, unknown>
      setDeployHarnessExecuteResult(payload)
    } catch {
      setDeployHarnessExecuteResult({ code: 'DEPLOY_WRITE_HARNESS_FAILED' })
    } finally {
      setDeployPrepLoading(false)
    }
  }

  const runHardwareGateReport = async () => {
    if (!data || !rescueTargetDevice) return
    setDeployPrepLoading(true)
    try {
      const r = await fetchApi('/api/deploy/hardware-gate/report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_device: rescueTargetDevice,
          inspect_result: data,
          safety_summary: data.write_safety_summary ?? {},
          write_harness_result: deployHarnessExecuteResult ?? {},
          final_confirmation_result: deployFinalCheckResult ?? {},
          real_write_guard_result: { code: 'DEPLOY_REAL_WRITE_READY' },
        }),
      })
      const payload = (await r.json()) as Record<string, unknown>
      setDeployHardwareGateResult(payload)
    } catch {
      setDeployHardwareGateResult({ code: 'DEPLOY_HARDWARE_GATE_BLOCKED' })
    } finally {
      setDeployPrepLoading(false)
    }
  }

  const runHardwareOperatorProtocol = async () => {
    if (!rescueTargetDevice) return
    setDeployPrepLoading(true)
    try {
      const r = await fetchApi('/api/deploy/hardware-gate/operator-protocol', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_device: rescueTargetDevice,
          hardware_gate_report: (deployHardwareGateResult?.report ?? {}) as Record<string, unknown>,
        }),
      })
      const payload = (await r.json()) as Record<string, unknown>
      setDeployHardwareProtocolResult(payload)
    } catch {
      setDeployHardwareProtocolResult({ code: 'DEPLOY_HARDWARE_GATE_BLOCKED' })
    } finally {
      setDeployPrepLoading(false)
    }
  }

  const trPreflightCode = (code: string | null) =>
    code ? t(`preflight.code.${code}`, { defaultValue: code }) : '-'

  const trRescueCode = (code: string | null | undefined) =>
    code ? t(`rescue.codes.${code}`, { defaultValue: code }) : '-'

  const rescueSafetyAllowed = Boolean((rescuePreview?.safety as Record<string, unknown> | undefined)?.allowed)
  const rescueHasPreview = rescuePreview?.code === 'RESCUE_PREVIEW_CREATED' && Boolean(rescuePreview?.preview_id)
  const rescueNeedsPreflight = (rescuePreview?.errors ?? []).includes('RESCUE_PREFLIGHT_REQUIRED')
  const rescueCanExecute = rescueHasPreview && rescueSafetyAllowed && !rescueNeedsPreflight && rescueTokenInput.length > 0

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Database className="text-sky-400" size={24} />
            {t('inspect.page.title')}
          </h1>
          <p className="text-slate-400 text-sm">
            {t('inspect.page.subtitle')}
            {' '}
            {t('inspect.page.phase2_note')}
          </p>
        </div>
        <button
          type="button"
          onClick={runInspect}
          disabled={loading}
          className="px-4 py-2 bg-sky-600 hover:bg-sky-500 disabled:opacity-60 text-white rounded-lg text-sm font-medium inline-flex items-center gap-2"
        >
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          {loading ? t('inspect.page.running') : t('inspect.page.run')}
        </button>
      </div>

      {errorCode ? (
        <div className="card border border-red-700/60 bg-red-950/30">
          <p className="text-red-300 text-sm">code: {errorCode}</p>
        </div>
      ) : null}

      {data ? (
        <>
          {classification ? (
            <div className="card bg-slate-800/60 border border-slate-700 space-y-3">
              <h2 className="text-base font-semibold text-white">{t('inspect.page.classification')}</h2>
              <p className="text-xs text-slate-500">{t('inspect.page.classification_disclaimer')}</p>
              <dl className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm text-slate-300">
                <div>
                  <dt className="text-slate-500">{t('inspect.page.system_type')}</dt>
                  <dd className="font-medium text-white">
                    {trSystemType(String(classification.system_type ?? 'UNKNOWN'))}
                  </dd>
                </div>
                <div>
                  <dt className="text-slate-500">{t('inspect.page.confidence')}</dt>
                  <dd>
                    {typeof classification.confidence === 'number'
                      ? `${Math.round(classification.confidence * 100)} %`
                      : '-'}
                  </dd>
                </div>
                <div>
                  <dt className="text-slate-500">{t('inspect.page.risk_level')}</dt>
                  <dd>{trRisk(String(classification.risk_level ?? 'unknown'))}</dd>
                </div>
              </dl>
              <div>
                <h3 className="text-sm font-medium text-slate-400 mb-1">{t('inspect.page.indicators')}</h3>
                <ul className="list-disc list-inside text-xs text-slate-300 space-y-0.5">
                  {(classification.indicators ?? []).length ? (
                    (classification.indicators as string[]).map((ind) => (
                      <li key={ind} className="font-mono">
                        {ind}
                      </li>
                    ))
                  ) : (
                    <li className="text-slate-500">{t('inspect.page.no_indicators')}</li>
                  )}
                </ul>
              </div>
            </div>
          ) : null}

          {advicePaths.length ? (
            <div className="card bg-slate-800/60 border border-amber-900/40 space-y-2">
              <h2 className="text-base font-semibold text-amber-100">{t('inspect.page.advice')}</h2>
              <p className="text-xs text-amber-200/80">{t('inspect.page.advice_disclaimer')}</p>
              <ul className="space-y-2 text-sm text-slate-200">
                {advicePaths.map((p, i) => (
                  <li
                    key={`${p.code ?? 'path'}-${i}`}
                    className="border border-slate-600/80 rounded-md px-3 py-2 bg-slate-900/40"
                  >
                    <div className="font-medium text-white">
                      {trAdvice(String(p.code ?? ''))}
                    </div>
                    <div className="text-xs text-slate-400 mt-1">
                      {t('inspect.page.advice_priority_label')}:{' '}
                      {trPriority(String(p.priority ?? ''))}
                      {' · '}
                      {p.requires_confirmation
                        ? t('inspect.page.advice_confirmation_required')
                        : t('inspect.page.advice_confirmation_not_required')}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {safetyTargets.length ? (
            <div className="card bg-slate-800/60 border border-emerald-900/30 space-y-3">
              <h2 className="text-base font-semibold text-emerald-100">{t('inspect.page.writeSafetyTitle')}</h2>
              <p className="text-xs text-slate-500">{t('inspect.page.writeSafetyDisclaimer')}</p>
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left text-slate-300">
                  <thead>
                    <tr className="border-b border-slate-600 text-slate-400">
                      <th className="py-2 pr-3">{t('inspect.page.writeSafetyColDevice')}</th>
                      <th className="py-2 pr-3">{t('inspect.page.writeSafetyColSize')}</th>
                      <th className="py-2 pr-3">{t('inspect.page.writeSafetyColState')}</th>
                      <th className="py-2">{t('inspect.page.writeSafetyColReason')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {safetyTargets.map((row) => (
                      <tr key={String(row.device)} className="border-b border-slate-700/80">
                        <td className="py-2 pr-3 font-mono text-xs">{row.device}</td>
                        <td className="py-2 pr-3">{String(row.size ?? '-')}</td>
                        <td className="py-2 pr-3">
                          {row.write_allowed ? (
                            <span className="text-emerald-400">{t('safety.allowed')}</span>
                          ) : (
                            <span className="text-amber-400">{t('safety.blocked')}</span>
                          )}
                          <span className="text-slate-500 text-xs ml-2">
                            ({labelSafetyState(String(row.classification ?? ''))})
                          </span>
                        </td>
                        <td className="py-2 text-xs font-mono">
                          {trSafetyReason(String(row.reason_code ?? ''))}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : null}

          <div className="card bg-slate-800/60 border border-violet-900/40 space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <h2 className="text-base font-semibold text-violet-100">{t('deploy.plan.title')}</h2>
                <p className="text-xs text-slate-500">{t('deploy.plan.subtitle')}</p>
              </div>
              <button
                type="button"
                onClick={runDeployPlan}
                disabled={deployPlanLoading || !data}
                className="px-3 py-2 rounded bg-violet-700 hover:bg-violet-600 text-white text-sm disabled:opacity-60"
              >
                {deployPlanLoading ? t('deploy.plan.running') : t('deploy.plan.run')}
              </button>
            </div>
            <p className="text-xs text-amber-200/90">{t('deploy.plan.disclaimer')}</p>
            {deployPlanResult ? (
              <div className="space-y-2 text-xs text-slate-300">
                <div>
                  <span className="text-slate-500">{t('deploy.plan.api_code')}:</span>{' '}
                  {trDeployCode(String(deployPlanResult.code ?? ''))}
                </div>
                {(() => {
                  const pl = (deployPlanResult.plan ?? {}) as Record<string, unknown>
                  const st = String(pl.plan_status ?? '')
                  if (!st) return null
                  return (
                    <div className="text-slate-200">
                      {t('deploy.plan.plan_status')}: {trDeployPlanStatus(st)}
                      {pl.requires_manual_review ? ` · ${t('deploy.plan.manual_review')}` : ''}
                    </div>
                  )
                })()}
                {(() => {
                  const pl = (deployPlanResult.plan ?? {}) as Record<string, unknown>
                  const hw = (pl.hardware_summary ?? {}) as Record<string, unknown>
                  if (!hw || Object.keys(hw).length === 0) return null
                  return (
                    <div className="border border-slate-700 rounded p-2 bg-slate-900/40 space-y-1">
                      <div className="text-violet-200">{t('deploy.plan.hardware')}</div>
                      <div>
                        CPU: {trDeployHwClass('deploy.hw.cpu_class', String(hw.cpu_class ?? ''))}
                        {' · '}
                        RAM: {trDeployHwClass('deploy.hw.ram_class', String(hw.ram_class ?? ''))}
                        {' · '}
                        {t('deploy.plan.storage')}: {trDeployHwClass('deploy.hw.storage_class', String(hw.storage_class ?? ''))}
                      </div>
                      <div>
                        {t('deploy.plan.network')}:{' '}
                        {t(`deploy.hw.network.${String(hw.network_available ?? 'unknown')}`, {
                          defaultValue: String(hw.network_available ?? ''),
                        })}
                      </div>
                    </div>
                  )
                })()}
                {(() => {
                  const pl = (deployPlanResult.plan ?? {}) as Record<string, unknown>
                  const profs = Array.isArray(pl.deploy_profiles) ? (pl.deploy_profiles as Record<string, unknown>[]) : []
                  if (!profs.length) return null
                  return (
                    <div>
                      <div className="text-violet-200 mb-1">{t('deploy.plan.profiles')}</div>
                      <ul className="space-y-1 list-disc list-inside text-slate-400">
                        {profs.map((p) => (
                          <li key={String(p.code)}>
                            {t(`deploy.profile.${String(p.code ?? '')}`, { defaultValue: String(p.code) })}
                            {' '}
                            ({p.suitable ? t('deploy.plan.suitable_yes') : t('deploy.plan.suitable_no')})
                          </li>
                        ))}
                      </ul>
                    </div>
                  )
                })()}
                {(() => {
                  const pl = (deployPlanResult.plan ?? {}) as Record<string, unknown>
                  const rec = pl.recommended_profile as Record<string, unknown> | undefined
                  if (!rec || !rec.code) {
                    return <div className="text-slate-500">{t('deploy.plan.no_recommended')}</div>
                  }
                  return (
                    <div className="text-sky-200">
                      {t('deploy.plan.recommended')}:{' '}
                      {t(`deploy.profile.${String(rec.code)}`, { defaultValue: String(rec.code) })}
                    </div>
                  )
                })()}
                {(() => {
                  const pl = (deployPlanResult.plan ?? {}) as Record<string, unknown>
                  const profs = Array.isArray(pl.deploy_profiles) ? (pl.deploy_profiles as Record<string, unknown>[]) : []
                  if (!profs.length) return null
                  const suitable = profs.filter((p) => Boolean(p.suitable))
                  return (
                    <div className="space-y-2 border border-slate-700 rounded p-2 bg-slate-900/40">
                      <label className="text-xs text-slate-300 block">{t('deploy.session.select_profile')}</label>
                      <select
                        value={deploySelectedProfile}
                        onChange={(e) => setDeploySelectedProfile(e.target.value)}
                        className="w-full rounded bg-slate-900 border border-slate-700 text-slate-200 px-2 py-1 text-xs"
                      >
                        <option value="">{t('deploy.session.no_profile')}</option>
                        {suitable.map((p) => {
                          const code = String(p.code ?? '')
                          return (
                            <option key={code} value={code}>
                              {t(`deploy.profile.${code}`, { defaultValue: code })}
                            </option>
                          )
                        })}
                      </select>
                      <div className="text-xs text-slate-500">
                        {t('deploy.session.target_device')}:{' '}
                        <span className="font-mono">{rescueTargetDevice || '-'}</span>
                      </div>
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={createDeploySession}
                          disabled={deployPrepLoading || !deploySelectedProfile || !rescueTargetDevice}
                          className="px-2 py-1 rounded bg-indigo-700 hover:bg-indigo-600 text-white text-xs disabled:opacity-60"
                        >
                          {t('deploy.session.create')}
                        </button>
                        <button
                          type="button"
                          onClick={executeDeployPrep}
                          disabled={deployPrepLoading || !deploySessionResult?.deploy_session_id}
                          className="px-2 py-1 rounded bg-amber-700 hover:bg-amber-600 text-white text-xs disabled:opacity-60"
                        >
                          {t('deploy.execute.prepare')}
                        </button>
                        <button
                          type="button"
                          onClick={runDeployPreview}
                          disabled={deployPrepLoading || !deploySessionResult?.deploy_session_id}
                          className="px-2 py-1 rounded bg-cyan-700 hover:bg-cyan-600 text-white text-xs disabled:opacity-60"
                        >
                          {t('deploy.preview.run')}
                        </button>
                      </div>
                      <label className="text-xs text-slate-300 block">{t('deploy.preview.os_source_type')}</label>
                      <select
                        value={deployOsSourceType}
                        onChange={(e) => setDeployOsSourceType(e.target.value)}
                        className="w-full rounded bg-slate-900 border border-slate-700 text-slate-200 px-2 py-1 text-xs"
                      >
                        <option value="local_image">local_image</option>
                        <option value="remote_image">remote_image</option>
                        <option value="official_installer">official_installer</option>
                      </select>
                      <input
                        value={deployOsSourceName}
                        onChange={(e) => setDeployOsSourceName(e.target.value)}
                        className="w-full rounded bg-slate-900 border border-slate-700 text-slate-200 px-2 py-1 text-xs font-mono"
                        placeholder={t('deploy.preview.os_name_placeholder')}
                      />
                      {deployOsSourceType === 'remote_image' ? (
                        <>
                          <input
                            value={deployOsSourceUrl}
                            onChange={(e) => setDeployOsSourceUrl(e.target.value)}
                            className="w-full rounded bg-slate-900 border border-slate-700 text-slate-200 px-2 py-1 text-xs font-mono"
                            placeholder="https://example/image.img"
                          />
                          <input
                            value={deployOsSourceChecksum}
                            onChange={(e) => setDeployOsSourceChecksum(e.target.value)}
                            className="w-full rounded bg-slate-900 border border-slate-700 text-slate-200 px-2 py-1 text-xs font-mono"
                            placeholder="sha256:..."
                          />
                        </>
                      ) : null}
                      <div className="text-xs text-slate-400">{t('deploy.security.no_install')}</div>
                      <div className="text-xs text-slate-400">{t('deploy.security.no_partition')}</div>
                      <div className="text-xs text-slate-400">{t('deploy.security.no_image_write')}</div>
                      <div className="text-xs text-slate-400">{t('deploy.security.no_changes')}</div>
                      <div className="text-xs text-slate-400">{t('deploy.security.no_download')}</div>
                      <div className="pt-2 border-t border-slate-700/80 space-y-2">
                        <div className="text-cyan-200">{t('deploy.sources.title')}</div>
                        <div className="flex gap-2">
                          <button
                            type="button"
                            onClick={loadDeploySources}
                            disabled={deployPrepLoading}
                            className="px-2 py-1 rounded bg-slate-700 hover:bg-slate-600 text-white text-xs disabled:opacity-60"
                          >
                            {t('deploy.sources.load')}
                          </button>
                          <button
                            type="button"
                            onClick={evaluateDeploySource}
                            disabled={deployPrepLoading || !deploySourceSelectedId || !deployPlanResult}
                            className="px-2 py-1 rounded bg-slate-700 hover:bg-slate-600 text-white text-xs disabled:opacity-60"
                          >
                            {t('deploy.sources.evaluate')}
                          </button>
                        </div>
                        {deploySourcesResult ? (
                          <>
                            <div className="text-xs text-slate-500">
                              {trDeployCode(String(deploySourcesResult.code ?? ''))}
                            </div>
                            {(() => {
                              const reg = (deploySourcesResult.registry ?? {}) as Record<string, unknown>
                              const srcs = Array.isArray(reg.sources) ? (reg.sources as Record<string, unknown>[]) : []
                              if (!srcs.length) return null
                              return (
                                <div className="space-y-1">
                                  <select
                                    value={deploySourceSelectedId}
                                    onChange={(e) => setDeploySourceSelectedId(e.target.value)}
                                    className="w-full rounded bg-slate-900 border border-slate-700 text-slate-200 px-2 py-1 text-xs"
                                  >
                                    {srcs.map((s) => (
                                      <option key={String(s.source_id)} value={String(s.source_id)}>
                                        {String(s.name)} · {t(`deploy.source.architecture.${String(s.architecture ?? 'unknown')}`, { defaultValue: String(s.architecture) })}
                                      </option>
                                    ))}
                                  </select>
                                  <ul className="space-y-0.5 text-xs text-slate-400">
                                    {srcs.map((s) => (
                                      <li key={`src-${String(s.source_id)}`} className="font-mono">
                                        {String(s.source_id)} · {t(`deploy.source.status.${String(s.status ?? 'metadata_only')}`, { defaultValue: String(s.status) })}
                                        {' · '}
                                        {t(`deploy.source.risk.${String(s.risk_level ?? 'medium')}`, { defaultValue: String(s.risk_level) })}
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )
                            })()}
                          </>
                        ) : null}
                        {deploySourceEvalResult ? (
                          <div className="text-xs text-slate-300 space-y-1">
                            <div>{trDeployCode(String(deploySourceEvalResult.code ?? ''))}</div>
                            {(() => {
                              const cmp = (deploySourceEvalResult.compatibility ?? {}) as Record<string, unknown>
                              if (!Object.keys(cmp).length) return null
                              return (
                                <div className="font-mono">
                                  {Boolean(cmp.compatible)
                                    ? t('deploy.source.compatibility.compatible')
                                    : t('deploy.source.compatibility.incompatible')}
                                  {' · '}
                                  {t(`deploy.source.risk.${String(cmp.risk_level ?? 'medium')}`, { defaultValue: String(cmp.risk_level) })}
                                </div>
                              )
                            })()}
                            <pre className="overflow-auto max-h-40 text-xs bg-slate-900/50 p-2 rounded">
                              {JSON.stringify(deploySourceEvalResult, null, 2)}
                            </pre>
                            <button
                              type="button"
                              onClick={runDeployCachePlan}
                              disabled={deployPrepLoading}
                              className="px-2 py-1 rounded bg-slate-700 hover:bg-slate-600 text-white text-xs disabled:opacity-60"
                            >
                              {t('deploy.cache.run_plan')}
                            </button>
                            <button
                              type="button"
                              onClick={inspectDeployImage}
                              disabled={deployPrepLoading}
                              className="px-2 py-1 rounded bg-slate-700 hover:bg-slate-600 text-white text-xs disabled:opacity-60"
                            >
                              {t('deploy.image.inspect.run')}
                            </button>
                          </div>
                        ) : null}
                        {deployImageInspectResult ? (
                          <div className="text-xs text-slate-300 space-y-1">
                            <div>{trDeployCode(String(deployImageInspectResult.code ?? ''))}</div>
                            {(() => {
                              const img = (deployImageInspectResult.image ?? {}) as Record<string, unknown>
                              const ver = (deployImageInspectResult.verification ?? {}) as Record<string, unknown>
                              return (
                                <div className="font-mono text-slate-400">
                                  {String(img.path ?? '-')} · {String(img.extension ?? '-')} · {String(img.size_bytes ?? 0)}B
                                  {' · '}
                                  {t('deploy.image.verification.checksum_status')}: {String(ver.code ?? '-')}
                                </div>
                              )
                            })()}
                            <div className="text-xs text-slate-500">{t('deploy.image.inspect.no_content_analysis')}</div>
                            <div className="text-xs text-slate-500">{t('deploy.image.inspect.no_mount')}</div>
                            <button
                              type="button"
                              onClick={runDeployWritePlan}
                              disabled={deployPrepLoading || !deploySessionResult?.deploy_session_id || !deployPreviewResult?.preview_id}
                              className="px-2 py-1 rounded bg-rose-700 hover:bg-rose-600 text-white text-xs disabled:opacity-60"
                            >
                              {t('deploy.write_plan.run')}
                            </button>
                            <pre className="overflow-auto max-h-40 text-xs bg-slate-900/50 p-2 rounded">
                              {JSON.stringify(deployImageInspectResult, null, 2)}
                            </pre>
                          </div>
                        ) : null}
                        {deployWritePlanResult ? (
                          <div className="text-xs text-slate-300 space-y-1 border border-rose-800/60 rounded p-2">
                            <div>{trDeployCode(String(deployWritePlanResult.code ?? ''))}</div>
                            {(() => {
                              const p = (deployWritePlanResult.plan ?? {}) as Record<string, unknown>
                              const tgt = (p.target ?? {}) as Record<string, unknown>
                              const img = (p.image ?? {}) as Record<string, unknown>
                              const ops = Array.isArray(p.simulated_operations) ? (p.simulated_operations as Record<string, unknown>[]) : []
                              const conf = Array.isArray(p.required_confirmations) ? (p.required_confirmations as string[]) : []
                              return (
                                <div className="space-y-1">
                                  <div className="text-rose-300">{t('deploy.write_plan.target')}</div>
                                  <div className="font-mono text-slate-400">{String(tgt.target_device ?? '-')}</div>
                                  <div className="text-rose-300">{t('deploy.write_plan.image')}</div>
                                  <div className="font-mono text-slate-400">{String(img.path ?? '-')}</div>
                                  <div className="text-rose-300">{t('deploy.write_plan.operations')}</div>
                                  <ul className="font-mono text-slate-400">
                                    {ops.map((op) => (
                                      <li key={String(op.code)}>
                                        {String(op.code)}
                                        {Boolean(op.destructive) ? ` · ${t('deploy.write_plan.destructive')}` : ''}
                                      </li>
                                    ))}
                                  </ul>
                                  <div className="text-rose-300">{t('deploy.write_plan.confirmations')}</div>
                                  <ul className="font-mono text-slate-400">
                                    {conf.map((c) => (
                                      <li key={c}>{t(`deploy.write_plan.confirmations.${c}`, { defaultValue: c })}</li>
                                    ))}
                                  </ul>
                                </div>
                              )
                            })()}
                            <div className="text-xs text-slate-500">{t('deploy.write_plan.no_write_note')}</div>
                            <div className="flex gap-2">
                              <button
                                type="button"
                                onClick={createDeployWriteSession}
                                disabled={deployPrepLoading}
                                className="px-2 py-1 rounded bg-purple-700 hover:bg-purple-600 text-white text-xs disabled:opacity-60"
                              >
                                {t('deploy.write_execute.session.create')}
                              </button>
                              <button
                                type="button"
                                onClick={runDeployWriteExecuteDryrun}
                                disabled={deployPrepLoading || !deployWriteSessionResult?.write_session_id}
                                className="px-2 py-1 rounded bg-purple-900 hover:bg-purple-800 text-white text-xs disabled:opacity-60"
                              >
                                {t('deploy.write_execute.run_dryrun')}
                              </button>
                            </div>
                            <div className="text-xs text-slate-500">{t('deploy.write_execute.note.no_write')}</div>
                            <div className="text-xs text-slate-500">{t('deploy.write_execute.note.simulation_only')}</div>
                            <div className="text-xs text-slate-500">{t('deploy.write_execute.note.no_image_write')}</div>
                            <div className="text-xs text-slate-500">{t('deploy.write_execute.note.no_format')}</div>
                            <div className="text-xs text-slate-500">{t('deploy.write_execute.note.no_mount')}</div>
                            <pre className="overflow-auto max-h-40 text-xs bg-slate-900/50 p-2 rounded">
                              {JSON.stringify(deployWritePlanResult, null, 2)}
                            </pre>
                          </div>
                        ) : null}
                        {deployWriteSessionResult ? (
                          <pre className="overflow-auto max-h-40 text-xs bg-slate-900/50 p-2 rounded">
                            {JSON.stringify(deployWriteSessionResult, null, 2)}
                          </pre>
                        ) : null}
                        {deployWriteExecuteResult ? (
                          <div className="text-xs text-slate-300 space-y-1">
                            <div>{trDeployCode(String(deployWriteExecuteResult.code ?? ''))}</div>
                            {(() => {
                              const steps = Array.isArray(deployWriteExecuteResult.simulated_execution)
                                ? (deployWriteExecuteResult.simulated_execution as Record<string, unknown>[])
                                : []
                              if (!steps.length) return null
                              return (
                                <ul className="font-mono text-slate-400">
                                  {steps.map((s) => (
                                    <li key={String(s.code)}>
                                      {String(s.code)}
                                      {' · '}
                                      {String(s.status ?? 'simulated')}
                                      {Boolean(s.would_write) ? ` · ${t('deploy.write_plan.destructive')}` : ''}
                                    </li>
                                  ))}
                                </ul>
                              )
                            })()}
                            <pre className="overflow-auto max-h-40 text-xs bg-slate-900/50 p-2 rounded">
                              {JSON.stringify(deployWriteExecuteResult, null, 2)}
                            </pre>
                            <button
                              type="button"
                              onClick={createFinalConfirmationSession}
                              disabled={deployPrepLoading}
                              className="px-2 py-1 rounded bg-red-800 hover:bg-red-700 text-white text-xs disabled:opacity-60"
                            >
                              {t('deploy.final_confirmation.session.create')}
                            </button>
                          </div>
                        ) : null}
                        {deployFinalConfirmationResult ? (
                          <div className="text-xs text-slate-300 space-y-1 border border-red-700/70 rounded p-2">
                            <div>{trDeployCode(String(deployFinalConfirmationResult.code ?? ''))}</div>
                            {(() => {
                              const snap = (deployFinalConfirmationResult.target_snapshot ?? {}) as Record<string, unknown>
                              return (
                                <div className="font-mono text-slate-400">
                                  {String(snap.target_device ?? '-')}
                                  {' · '}
                                  {String(snap.fingerprint ?? '-')}
                                </div>
                              )
                            })()}
                            <div className="text-red-300">{t('deploy.final_confirmation.warning.data_destroyed')}</div>
                            <div className="text-red-300">{t('deploy.final_confirmation.warning.dryrun_only')}</div>
                            <div className="text-red-300">{t('deploy.final_confirmation.warning.no_data_written')}</div>
                            <button
                              type="button"
                              onClick={runFinalConfirmationCheck}
                              disabled={deployPrepLoading || !deployFinalConfirmationResult.final_confirmation_id}
                              className="px-2 py-1 rounded bg-red-900 hover:bg-red-800 text-white text-xs disabled:opacity-60"
                            >
                              {t('deploy.final_confirmation.check.run')}
                            </button>
                            <pre className="overflow-auto max-h-40 text-xs bg-slate-900/50 p-2 rounded">
                              {JSON.stringify(deployFinalConfirmationResult, null, 2)}
                            </pre>
                          </div>
                        ) : null}
                        {deployFinalCheckResult ? (
                          <div className="text-xs text-slate-300 space-y-1">
                            <div>{trDeployCode(String(deployFinalCheckResult.code ?? ''))}</div>
                            {(() => {
                              const ops = Array.isArray(deployFinalCheckResult.destructive_operations)
                                ? (deployFinalCheckResult.destructive_operations as string[])
                                : []
                              return (
                                <ul className="font-mono text-slate-400">
                                  {ops.map((op) => (
                                    <li key={op}>{op}</li>
                                  ))}
                                </ul>
                              )
                            })()}
                            <pre className="overflow-auto max-h-40 text-xs bg-slate-900/50 p-2 rounded">
                              {JSON.stringify(deployFinalCheckResult, null, 2)}
                            </pre>
                            <div className="space-y-1">
                              <label className="text-slate-400">{t('deploy.write_harness.test_target_path')}</label>
                              <input
                                type="text"
                                value={deployHarnessTargetPath}
                                onChange={(e) => setDeployHarnessTargetPath(e.target.value)}
                                className="w-full px-2 py-1 rounded bg-slate-900 border border-slate-700 font-mono text-xs"
                              />
                            </div>
                            <div className="flex gap-2">
                              <button
                                type="button"
                                onClick={createHarnessSession}
                                disabled={deployPrepLoading}
                                className="px-2 py-1 rounded bg-emerald-700 hover:bg-emerald-600 text-white text-xs disabled:opacity-60"
                              >
                                {t('deploy.write_harness.create_session')}
                              </button>
                              <button
                                type="button"
                                onClick={runHarnessExecute}
                                disabled={deployPrepLoading || !deployHarnessSessionResult?.harness_session_id}
                                className="px-2 py-1 rounded bg-emerald-900 hover:bg-emerald-800 text-white text-xs disabled:opacity-60"
                              >
                                {t('deploy.write_harness.run_execute')}
                              </button>
                            </div>
                            <div className="text-xs text-slate-400">{t('deploy.write_harness.security.only_test_file')}</div>
                            <div className="text-xs text-slate-400">{t('deploy.write_harness.security.no_blockdevice')}</div>
                            <div className="text-xs text-slate-400">{t('deploy.write_harness.security.max_bytes_limited')}</div>
                            <div className="text-xs text-slate-400">{t('deploy.write_harness.security.not_production')}</div>
                          </div>
                        ) : null}
                        {deployHarnessSessionResult ? (
                          <pre className="overflow-auto max-h-40 text-xs bg-slate-900/50 p-2 rounded">
                            {JSON.stringify(deployHarnessSessionResult, null, 2)}
                          </pre>
                        ) : null}
                        {deployHarnessExecuteResult ? (
                          <pre className="overflow-auto max-h-40 text-xs bg-slate-900/50 p-2 rounded">
                            {JSON.stringify(deployHarnessExecuteResult, null, 2)}
                          </pre>
                        ) : null}
                        <div className="space-y-2 border border-red-900/60 rounded p-2">
                          <div className="text-red-300 text-xs">{t('deploy.hardware_gate.warning.no_real_write')}</div>
                          <div className="text-red-300 text-xs">{t('deploy.hardware_gate.warning.no_device_modification')}</div>
                          <div className="text-red-300 text-xs">{t('deploy.hardware_gate.warning.test_media_only')}</div>
                          <div className="flex gap-2">
                            <button
                              type="button"
                              onClick={runHardwareGateReport}
                              disabled={deployPrepLoading || !rescueTargetDevice}
                              className="px-2 py-1 rounded bg-red-800 hover:bg-red-700 text-white text-xs disabled:opacity-60"
                            >
                              {t('deploy.hardware_gate.run_report')}
                            </button>
                            <button
                              type="button"
                              onClick={runHardwareOperatorProtocol}
                              disabled={deployPrepLoading || !deployHardwareGateResult}
                              className="px-2 py-1 rounded bg-red-900 hover:bg-red-800 text-white text-xs disabled:opacity-60"
                            >
                              {t('deploy.hardware_gate.run_protocol')}
                            </button>
                          </div>
                          {deployHardwareGateResult ? (
                            <div className="text-xs text-slate-300 space-y-1">
                              <div>{trDeployCode(String(deployHardwareGateResult.code ?? ''))}</div>
                              {(() => {
                                const report = (deployHardwareGateResult.report ?? {}) as Record<string, unknown>
                                const di = (report.device_identity ?? {}) as Record<string, unknown>
                                return (
                                  <div className="font-mono text-slate-400">
                                    {t('deploy.hardware_gate.device_class')}: {String(di.device_class ?? '-')}
                                    {' · '}
                                    {t('deploy.hardware_gate.readiness')}: {String(report.readiness_level ?? '-')}
                                  </div>
                                )
                              })()}
                              <pre className="overflow-auto max-h-40 text-xs bg-slate-900/50 p-2 rounded">
                                {JSON.stringify(deployHardwareGateResult, null, 2)}
                              </pre>
                            </div>
                          ) : null}
                          {deployHardwareProtocolResult ? (
                            <pre className="overflow-auto max-h-40 text-xs bg-slate-900/50 p-2 rounded">
                              {JSON.stringify(deployHardwareProtocolResult, null, 2)}
                            </pre>
                          ) : null}
                        </div>
                        {deployCachePlanResult ? (
                          <div className="text-xs text-slate-300 space-y-1">
                            <div>{trDeployCode(String(deployCachePlanResult.code ?? ''))}</div>
                            {(() => {
                              const p = (deployCachePlanResult.plan ?? {}) as Record<string, unknown>
                              const cache = (p.cache ?? {}) as Record<string, unknown>
                              const verification = (p.verification ?? {}) as Record<string, unknown>
                              const steps = Array.isArray(p.required_steps) ? (p.required_steps as Record<string, unknown>[]) : []
                              return (
                                <div className="space-y-1">
                                  <div className="text-cyan-200">{t('deploy.cache.cache_targets')}</div>
                                  <ul className="font-mono text-slate-400">
                                    {(Array.isArray(cache.cache_targets) ? (cache.cache_targets as string[]) : []).map((x) => (
                                      <li key={x}>{x}</li>
                                    ))}
                                  </ul>
                                  <div className="text-cyan-200">{t('deploy.cache.verification')}</div>
                                  <div className="font-mono text-slate-400">
                                    {t('deploy.cache.verification.checksum_required')}: {String(verification.checksum_required ?? false)}
                                    {' · '}
                                    {t('deploy.cache.verification.algorithm')}: {String(verification.checksum_algorithm ?? '-')}
                                  </div>
                                  <div className="text-cyan-200">{t('deploy.cache.required_steps')}</div>
                                  <ul className="font-mono text-slate-400">
                                    {steps.map((s) => (
                                      <li key={String(s.code)}>
                                        {String(s.code)}
                                        {' · '}
                                        {Boolean(s.would_network) ? t('deploy.cache.would_network') : t('deploy.cache.no_network')}
                                        {' · '}
                                        {Boolean(s.would_write_cache) ? t('deploy.cache.would_write_cache') : t('deploy.cache.no_cache_write')}
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )
                            })()}
                            <pre className="overflow-auto max-h-40 text-xs bg-slate-900/50 p-2 rounded">
                              {JSON.stringify(deployCachePlanResult, null, 2)}
                            </pre>
                            <div className="flex gap-2">
                              <button
                                type="button"
                                onClick={createDeployCacheSession}
                                disabled={deployPrepLoading}
                                className="px-2 py-1 rounded bg-indigo-700 hover:bg-indigo-600 text-white text-xs disabled:opacity-60"
                              >
                                {t('deploy.cache.session.create')}
                              </button>
                              <button
                                type="button"
                                onClick={executeDeployCacheLocal}
                                disabled={deployPrepLoading || !deployCacheSessionResult?.cache_session_id}
                                className="px-2 py-1 rounded bg-amber-700 hover:bg-amber-600 text-white text-xs disabled:opacity-60"
                              >
                                {t('deploy.cache.execute.run')}
                              </button>
                            </div>
                            <div className="text-xs text-slate-400">{t('deploy.cache.security.local_only')}</div>
                            <div className="text-xs text-slate-400">{t('deploy.cache.security.no_mount')}</div>
                            <div className="text-xs text-slate-400">{t('deploy.cache.security.no_install')}</div>
                            <div className="text-xs text-slate-400">{t('deploy.cache.security.no_download')}</div>
                          </div>
                        ) : null}
                        {deployCacheSessionResult ? (
                          <pre className="overflow-auto max-h-40 text-xs bg-slate-900/50 p-2 rounded">
                            {JSON.stringify(deployCacheSessionResult, null, 2)}
                          </pre>
                        ) : null}
                        {deployCacheExecuteResult ? (
                          <pre className="overflow-auto max-h-40 text-xs bg-slate-900/50 p-2 rounded">
                            {JSON.stringify(deployCacheExecuteResult, null, 2)}
                          </pre>
                        ) : null}
                        <div className="text-xs text-slate-500">{t('deploy.sources.no_download')}</div>
                        <div className="text-xs text-slate-500">{t('deploy.sources.no_images_included')}</div>
                        <div className="text-xs text-slate-500">{t('deploy.sources.no_install')}</div>
                      </div>
                    </div>
                  )
                })()}
                {(() => {
                  const pl = (deployPlanResult.plan ?? {}) as Record<string, unknown>
                  const risks = Array.isArray(pl.risks) ? (pl.risks as string[]) : []
                  if (!risks.length) return null
                  return (
                    <div>
                      <div className="text-rose-200/90 mb-1">{t('deploy.plan.risks')}</div>
                      <ul className="space-y-0.5 font-mono text-slate-400">
                        {risks.map((c) => (
                          <li key={c}>{t(`deploy.risks.${c}`, { defaultValue: c })}</li>
                        ))}
                      </ul>
                    </div>
                  )
                })()}
                {(() => {
                  const pl = (deployPlanResult.plan ?? {}) as Record<string, unknown>
                  const blocked = Array.isArray(pl.blocked_steps) ? (pl.blocked_steps as string[]) : []
                  if (!blocked.length) return null
                  return (
                    <div>
                      <div className="text-amber-200/90 mb-1">{t('deploy.plan.blocked')}</div>
                      <ul className="space-y-0.5 font-mono text-slate-400">
                        {blocked.map((c) => (
                          <li key={c}>{t(`deploy.blocked.${c}`, { defaultValue: c })}</li>
                        ))}
                      </ul>
                    </div>
                  )
                })()}
                <pre className="overflow-auto max-h-48 text-xs bg-slate-900/50 p-2 rounded">
                  {JSON.stringify(deployPlanResult, null, 2)}
                </pre>
                {deploySessionResult ? (
                  <pre className="overflow-auto max-h-48 text-xs bg-slate-900/50 p-2 rounded">
                    {JSON.stringify(deploySessionResult, null, 2)}
                  </pre>
                ) : null}
                {deployExecuteResult ? (
                  <pre className="overflow-auto max-h-48 text-xs bg-slate-900/50 p-2 rounded">
                    {JSON.stringify(deployExecuteResult, null, 2)}
                  </pre>
                ) : null}
                {deployPreviewResult ? (
                  <div className="space-y-1">
                    <pre className="overflow-auto max-h-48 text-xs bg-slate-900/50 p-2 rounded">
                      {JSON.stringify(deployPreviewResult, null, 2)}
                    </pre>
                    {(() => {
                      const steps = Array.isArray(deployPreviewResult.simulated_steps) ? (deployPreviewResult.simulated_steps as Record<string, unknown>[]) : []
                      if (!steps.length) return null
                      return (
                        <div className="text-xs text-slate-300 space-y-1">
                          <div className="text-cyan-200">{t('deploy.preview.simulated_steps')}</div>
                          {steps.map((s) => (
                            <div key={String(s.code)} className="font-mono">
                              {String(s.code)} · {Boolean(s.would_write) ? t('deploy.preview.would_write') : t('deploy.preview.read_only')}
                            </div>
                          ))}
                        </div>
                      )
                    })()}
                  </div>
                ) : null}
              </div>
            ) : null}
          </div>

          <div className="card bg-slate-800/60 border border-cyan-900/40 space-y-3">
            <h2 className="text-base font-semibold text-cyan-100">{t('preflight.title')}</h2>
            <p className="text-xs text-slate-400">{t('preflight.description')}</p>

            <div className="grid md:grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-slate-400 block mb-1">{t('target.select')}</label>
                <select
                  value={selectedTarget}
                  onChange={(e) => setSelectedTarget(e.target.value)}
                  className="w-full rounded bg-slate-900 border border-slate-700 text-slate-200 px-2 py-2 text-sm"
                >
                  <option value="">{t('target.none')}</option>
                  {safetyTargets.map((tgt) => (
                    <option key={String(tgt.device)} value={String(tgt.device)}>
                      {String(tgt.device)} - {trSafetyReason(String(tgt.reason_code ?? ''))}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex items-end gap-2">
                <button
                  type="button"
                  onClick={loadPreflightSources}
                  disabled={preflightLoading}
                  className="px-3 py-2 rounded bg-slate-700 hover:bg-slate-600 text-white text-sm disabled:opacity-60"
                >
                  {t('preflight.load_sources')}
                </button>
                <button
                  type="button"
                  onClick={createPreview}
                  disabled={preflightLoading || !selectedTarget}
                  className="px-3 py-2 rounded bg-cyan-700 hover:bg-cyan-600 text-white text-sm disabled:opacity-60"
                >
                  {t('preflight.preview')}
                </button>
              </div>
            </div>

            {preflightCode ? (
              <div className="text-xs text-cyan-200">{trPreflightCode(preflightCode)}</div>
            ) : null}

            {preflightSources.length ? (
              <div>
                <h3 className="text-sm text-slate-300 mb-1">{t('preflight.sources')}</h3>
                <ul className="space-y-1 text-xs text-slate-300">
                  {preflightSources.map((s) => (
                    <li key={String(s.source_id)} className="font-mono">
                      {s.path} - {t(`source.kind.${String(s.kind ?? '')}`, { defaultValue: String(s.kind ?? '') })} - {trPreflightCode(String(s.code ?? ''))}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            {preview?.plan_id ? (
              <div className="space-y-2 border border-slate-700 rounded p-3 bg-slate-900/40">
                <div className="text-xs text-slate-300">{t('preflight.plan_id')}: <span className="font-mono">{preview.plan_id}</span></div>
                <div className="text-xs text-slate-300">{t('preflight.target_reason')}: <span className="font-mono">{trSafetyReason(String(preview.target_reason ?? ''))}</span></div>
                <label className="text-xs text-slate-400 block">{t('confirmation.token')}</label>
                <input
                  value={tokenInput}
                  onChange={(e) => setTokenInput(e.target.value)}
                  className="w-full rounded bg-slate-950 border border-slate-700 text-slate-200 px-2 py-1 text-xs font-mono"
                  placeholder="token"
                />
                <label className="inline-flex items-center gap-2 text-xs text-slate-400">
                  <input
                    type="checkbox"
                    checked={allowEmptyTarget}
                    onChange={(e) => setAllowEmptyTarget(e.target.checked)}
                  />
                  {t('confirmation.allow_empty_target')}
                </label>
                <div>
                  <button
                    type="button"
                    onClick={executePreflightBackup}
                    disabled={preflightLoading || !tokenInput}
                    className="px-3 py-2 rounded bg-amber-700 hover:bg-amber-600 text-white text-sm disabled:opacity-60"
                  >
                    {t('preflight.execute')}
                  </button>
                </div>
              </div>
            ) : null}

            {executeResult ? (
              <div className="text-xs text-slate-300 space-y-1">
                <div>{trPreflightCode(String(executeResult.code ?? ''))}</div>
                {executeResult.archive_path ? <div className="font-mono">{executeResult.archive_path}</div> : null}
                {executeResult.verify_code ? <div className="font-mono">{executeResult.verify_code}</div> : null}
              </div>
            ) : null}
          </div>

          <div className="card bg-slate-800/60 border border-indigo-900/40 space-y-3">
            <h2 className="text-base font-semibold text-indigo-100">{t('rescue.preview.title')}</h2>
            <p className="text-xs text-slate-400">{t('rescue.preview.description')}</p>
            <div className="grid md:grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-slate-400 block mb-1">{t('rescue.preview.backup_path')}</label>
                <input
                  value={rescueBackupPath}
                  onChange={(e) => setRescueBackupPath(e.target.value)}
                  className="w-full rounded bg-slate-900 border border-slate-700 text-slate-200 px-2 py-2 text-xs font-mono"
                  placeholder="/path/to/backup.tar.gz"
                />
              </div>
              <div>
                <label className="text-xs text-slate-400 block mb-1">{t('rescue.preview.target_device')}</label>
                <select
                  value={rescueTargetDevice}
                  onChange={(e) => setRescueTargetDevice(e.target.value)}
                  className="w-full rounded bg-slate-900 border border-slate-700 text-slate-200 px-2 py-2 text-sm"
                >
                  <option value="">{t('target.none')}</option>
                  {safetyTargets.map((tgt) => (
                    <option key={String(tgt.device)} value={String(tgt.device)}>
                      {String(tgt.device)} - {trSafetyReason(String(tgt.reason_code ?? ''))}
                    </option>
                  ))}
                </select>
                <label className="text-xs text-slate-400 block mb-1 mt-2">{t('rescue.execute.target_path')}</label>
                <input
                  value={rescueTargetPath}
                  onChange={(e) => setRescueTargetPath(e.target.value)}
                  className="w-full rounded bg-slate-900 border border-slate-700 text-slate-200 px-2 py-2 text-xs font-mono"
                  placeholder="/mnt/setuphelfer-restore-live/..."
                />
              </div>
            </div>
            <div>
              <button
                type="button"
                onClick={runRescuePreview}
                disabled={rescueLoading || !rescueBackupPath || !rescueTargetDevice}
                className="px-3 py-2 rounded bg-indigo-700 hover:bg-indigo-600 text-white text-sm disabled:opacity-60"
              >
                {rescueLoading ? t('rescue.preview.running') : t('rescue.preview.run')}
              </button>
            </div>
            {rescuePreview ? (
              <div className="text-xs text-slate-300 space-y-2">
                <div>{trRescueCode(rescuePreview.code)}</div>
                <label className="text-xs text-slate-400 block">{t('rescue.execute.confirmation_token')}</label>
                <input
                  value={rescueTokenInput}
                  onChange={(e) => setRescueTokenInput(e.target.value)}
                  className="w-full rounded bg-slate-950 border border-slate-700 text-slate-200 px-2 py-1 text-xs font-mono"
                />
                <p className="text-xs text-amber-300">{t('rescue.execute.warning')}</p>
                <button
                  type="button"
                  onClick={runRescueExecute}
                  disabled={rescueLoading || !rescueCanExecute}
                  className="px-3 py-2 rounded bg-red-700 hover:bg-red-600 text-white text-sm disabled:opacity-60"
                >
                  {rescueLoading ? t('rescue.execute.running') : t('rescue.execute.run')}
                </button>
                <pre className="overflow-auto max-h-56 text-xs text-slate-300 bg-slate-900/50 p-2 rounded">
                  {JSON.stringify(rescuePreview, null, 2)}
                </pre>
              </div>
            ) : null}
            <div className="border border-cyan-700/40 rounded p-2 bg-cyan-950/20 space-y-2">
              <div className="text-cyan-200">{t('recovery.minimal.title')}</div>
              <button
                type="button"
                onClick={runRecoveryMinimalPlan}
                disabled={rescueLoading || !rescueTargetPath}
                className="px-2 py-1 rounded bg-cyan-700 hover:bg-cyan-600 text-white text-xs disabled:opacity-60"
              >
                {t('recovery.minimal.run_plan')}
              </button>
              {recoveryPlanResult ? (
                <div className="space-y-2">
                  {(() => {
                    const plan = (recoveryPlanResult.plan ?? {}) as Record<string, unknown>
                    const steps = Array.isArray(plan.required_steps) ? (plan.required_steps as Record<string, unknown>[]) : []
                    return (
                      <>
                        <div className="text-xs text-slate-300">{t('recovery.minimal.session.select_steps')}</div>
                        <div className="space-y-1">
                          {steps.map((st) => {
                            const code = String(st.code ?? '')
                            const applicable = Boolean(st.applicable)
                            const checked = recoverySelectedSteps.includes(code)
                            return (
                              <label key={code} className="flex items-center gap-2 text-xs text-slate-300">
                                <input
                                  type="checkbox"
                                  checked={checked}
                                  disabled={!applicable}
                                  onChange={(e) => {
                                    if (e.target.checked) setRecoverySelectedSteps((prev) => [...prev, code])
                                    else setRecoverySelectedSteps((prev) => prev.filter((x) => x !== code))
                                  }}
                                />
                                <span>{t(`recovery.minimal.steps.${code}`, { defaultValue: code })}</span>
                              </label>
                            )
                          })}
                        </div>
                        <div className="flex gap-2">
                          <button
                            type="button"
                            onClick={createRecoveryMinimalSession}
                            disabled={rescueLoading || recoverySelectedSteps.length === 0}
                            className="px-2 py-1 rounded bg-indigo-700 hover:bg-indigo-600 text-white text-xs disabled:opacity-60"
                          >
                            {t('recovery.minimal.session.create')}
                          </button>
                          <button
                            type="button"
                            onClick={executeRecoveryMinimalPrep}
                            disabled={rescueLoading || !recoverySessionResult?.session_id}
                            className="px-2 py-1 rounded bg-amber-700 hover:bg-amber-600 text-white text-xs disabled:opacity-60"
                          >
                            {t('recovery.minimal.execute.prepare')}
                          </button>
                        </div>
                        <pre className="overflow-auto max-h-56 text-xs text-slate-300 bg-slate-900/50 p-2 rounded">
                          {JSON.stringify(recoveryPlanResult, null, 2)}
                        </pre>
                        {recoverySessionResult ? (
                          <pre className="overflow-auto max-h-56 text-xs text-slate-300 bg-slate-900/50 p-2 rounded">
                            {JSON.stringify(recoverySessionResult, null, 2)}
                          </pre>
                        ) : null}
                        {recoveryExecuteResult ? (
                          <pre className="overflow-auto max-h-56 text-xs text-slate-300 bg-slate-900/50 p-2 rounded">
                            {JSON.stringify(recoveryExecuteResult, null, 2)}
                          </pre>
                        ) : null}
                        <button
                          type="button"
                          onClick={runRecoveryActivationPlan}
                          disabled={rescueLoading || !recoveryPlanResult}
                          className="px-2 py-1 rounded bg-emerald-700 hover:bg-emerald-600 text-white text-xs disabled:opacity-60"
                        >
                          {t('recovery.activation.run_plan')}
                        </button>
                        {recoveryActivationResult ? (
                          <div className="space-y-2">
                            {(() => {
                              const plan = (recoveryActivationResult.plan ?? {}) as Record<string, unknown>
                              const steps = Array.isArray(plan.required_steps) ? (plan.required_steps as Record<string, unknown>[]) : []
                              return (
                                <>
                                  <div className="text-xs text-slate-300">{t('recovery.activation.session.select_steps')}</div>
                                  <div className="space-y-1">
                                    {steps.map((st) => {
                                      const code = String(st.code ?? '')
                                      const applicable = Boolean(st.applicable)
                                      const checked = recoveryActivationSelectedSteps.includes(code)
                                      return (
                                        <label key={code} className="flex items-center gap-2 text-xs text-slate-300">
                                          <input
                                            type="checkbox"
                                            checked={checked}
                                            disabled={!applicable}
                                            onChange={(e) => {
                                              if (e.target.checked) setRecoveryActivationSelectedSteps((prev) => [...prev, code])
                                              else setRecoveryActivationSelectedSteps((prev) => prev.filter((x) => x !== code))
                                            }}
                                          />
                                          <span>{t(`recovery.activation.steps.${code}`, { defaultValue: code })}</span>
                                        </label>
                                      )
                                    })}
                                  </div>
                                  <div className="flex gap-2">
                                    <button
                                      type="button"
                                      onClick={createRecoveryActivationSession}
                                      disabled={rescueLoading || recoveryActivationSelectedSteps.length === 0}
                                      className="px-2 py-1 rounded bg-indigo-700 hover:bg-indigo-600 text-white text-xs disabled:opacity-60"
                                    >
                                      {t('recovery.activation.session.create')}
                                    </button>
                                    <button
                                      type="button"
                                      onClick={executeRecoveryActivationPrep}
                                      disabled={rescueLoading || !recoveryActivationSessionResult?.activation_session_id}
                                      className="px-2 py-1 rounded bg-amber-700 hover:bg-amber-600 text-white text-xs disabled:opacity-60"
                                    >
                                      {t('recovery.activation.execute.prepare')}
                                    </button>
                                  </div>
                                  <label className="block text-xs text-slate-300 space-y-1">
                                    <span>{t('recovery.activation.ssh.public_key_label')}</span>
                                    <textarea
                                      value={recoveryActivationSshPublicKey}
                                      onChange={(e) => setRecoveryActivationSshPublicKey(e.target.value)}
                                      rows={3}
                                      className="w-full rounded bg-slate-900 border border-slate-700 text-slate-200 px-2 py-1 font-mono"
                                      placeholder={t('recovery.activation.ssh.public_key_placeholder')}
                                    />
                                  </label>
                                  <label className="flex items-center gap-2 text-xs text-amber-200">
                                    <input
                                      type="checkbox"
                                      checked={recoveryActivationAllowLanBind}
                                      onChange={(e) => setRecoveryActivationAllowLanBind(e.target.checked)}
                                    />
                                    <span>{t('recovery.activation.backend.allow_lan_bind')}</span>
                                  </label>
                                  {recoveryActivationAllowLanBind ? (
                                    <div className="text-xs text-amber-300">{t('recovery.activation.backend.lan_bind_warning')}</div>
                                  ) : null}
                                  <div className="text-xs text-slate-400">{t('recovery.activation.security.no_ssh_enabled')}</div>
                                  <div className="text-xs text-slate-400">{t('recovery.activation.security.no_user_created')}</div>
                                  <div className="text-xs text-slate-400">{t('recovery.activation.security.no_services_started')}</div>
                                  <div className="text-xs text-slate-400">{t('recovery.activation.security.no_ports_opened')}</div>
                                  <div className="text-xs text-slate-400">{t('recovery.activation.security.no_password_login')}</div>
                                  <div className="text-xs text-slate-400">{t('recovery.activation.security.no_root_login')}</div>
                                  <div className="text-xs text-slate-400">{t('recovery.activation.security.no_host_changes')}</div>
                                  <div className="text-xs text-slate-400">{t('recovery.activation.security.no_full_remote_guarantee')}</div>
                                  <pre className="overflow-auto max-h-56 text-xs text-slate-300 bg-slate-900/50 p-2 rounded">
                                    {JSON.stringify(recoveryActivationResult, null, 2)}
                                  </pre>
                                  {recoveryActivationSessionResult ? (
                                    <pre className="overflow-auto max-h-56 text-xs text-slate-300 bg-slate-900/50 p-2 rounded">
                                      {JSON.stringify(recoveryActivationSessionResult, null, 2)}
                                    </pre>
                                  ) : null}
                                  {recoveryActivationExecuteResult ? (
                                    <pre className="overflow-auto max-h-56 text-xs text-slate-300 bg-slate-900/50 p-2 rounded">
                                      {JSON.stringify(recoveryActivationExecuteResult, null, 2)}
                                    </pre>
                                  ) : null}
                                </>
                              )
                            })()}
                          </div>
                        ) : null}
                      </>
                    )
                  })()}
                </div>
              ) : null}
            </div>

            {rescueExecuteResult ? (
              <div className="text-xs text-slate-300 space-y-2">
                <div>{trRescueCode(String(rescueExecuteResult.code ?? ''))}</div>
                {(() => {
                  const pv = (rescueExecuteResult.post_verify ?? {}) as Record<string, unknown>
                  const st = String(pv.status ?? '')
                  if (!st) return null
                  return (
                    <div className="border border-slate-700 rounded p-2 bg-slate-900/40">
                      <div className="text-slate-300">{t('post_restore.title')}</div>
                      <div className="text-xs text-slate-400">{t(`post_restore.status.${st}`, { defaultValue: st })}</div>
                      {Boolean((pv.boot ?? {}) && ((pv.boot as Record<string, unknown>).boot_repair_recommended)) ? (
                        <div className="text-xs text-amber-300">{t('post_restore.boot_repair_recommended')}</div>
                      ) : null}
                    </div>
                  )
                })()}
                {(() => {
                  const bc = (rescueExecuteResult.boot_capability ?? {}) as Record<string, unknown>
                  const st = String(bc.status ?? '')
                  if (!st) return null
                  const hints = Array.isArray(bc.boot_type_hints) ? (bc.boot_type_hints as string[]) : []
                  const recs = Array.isArray(bc.recommendations) ? (bc.recommendations as string[]) : []
                  return (
                    <div className="border border-indigo-700/50 rounded p-2 bg-indigo-950/20 space-y-1">
                      <div className="text-indigo-200">{t('boot.capability.title')}</div>
                      <div className="text-xs text-slate-300">{t(`boot.status.${st}`, { defaultValue: st })}</div>
                      {hints.length > 0 ? (
                        <div className="text-xs text-slate-400">
                          {hints.map((h) => t(`boot.hints.${h}`, { defaultValue: h })).join(' | ')}
                        </div>
                      ) : null}
                      {recs.length > 0 ? (
                        <div className="text-xs text-amber-300">
                          {recs.map((r) => t(`boot.recommendations.${r}`, { defaultValue: r })).join(' | ')}
                        </div>
                      ) : null}
                    </div>
                  )
                })()}
                {(() => {
                  const rp = (rescueExecuteResult.boot_repair_plan ?? {}) as Record<string, unknown>
                  const pst = String(rp.plan_status ?? '')
                  if (!pst) return null
                  const issues = Array.isArray(rp.issues) ? (rp.issues as string[]) : []
                  const risks = Array.isArray(rp.risks) ? (rp.risks as string[]) : []
                  const actions = Array.isArray(rp.proposed_actions) ? (rp.proposed_actions as Record<string, unknown>[]) : []
                  return (
                    <div className="border border-amber-700/40 rounded p-2 bg-amber-950/20 space-y-1">
                      <div className="text-amber-200">{t('boot.repair_plan.title')}</div>
                      <div className="text-xs text-slate-300">{t(`boot.repair_plan.status.${pst}`, { defaultValue: pst })}</div>
                      {issues.length > 0 ? <div className="text-xs text-slate-400">{issues.map((x) => t(`boot.repair_issues.${x}`, { defaultValue: x })).join(' | ')}</div> : null}
                      {actions.length > 0 ? <div className="text-xs text-sky-300">{actions.map((a) => t(`boot.repair_actions.${String(a.code ?? '')}`, { defaultValue: String(a.code ?? '') })).join(' | ')}</div> : null}
                      {risks.length > 0 ? <div className="text-xs text-rose-300">{risks.map((r) => t(`boot.repair_risks.${r}`, { defaultValue: r })).join(' | ')}</div> : null}
                      {actions.length > 0 ? (
                        <div className="pt-1 space-y-1">
                          <select
                            value={repairActionCode}
                            onChange={(e) => setRepairActionCode(e.target.value)}
                            className="w-full rounded bg-slate-900 border border-slate-700 text-slate-200 px-2 py-1 text-xs"
                          >
                            <option value="">{t('boot.repair_execute.select_action')}</option>
                            {actions.map((a) => {
                              const code = String(a.code ?? '')
                              const applicable = Boolean(a.applicable)
                              return (
                                <option key={code} value={code} disabled={!applicable}>
                                  {t(`boot.repair_actions.${code}`, { defaultValue: code })} {!applicable ? '(blocked)' : ''}
                                </option>
                              )
                            })}
                          </select>
                          <button
                            type="button"
                            onClick={createRepairSession}
                            disabled={rescueLoading || !repairActionCode}
                            className="px-2 py-1 rounded bg-indigo-700 hover:bg-indigo-600 text-white text-xs disabled:opacity-60"
                          >
                            {t('boot.repair_session.create')}
                          </button>
                          <input
                            value={repairToken}
                            onChange={(e) => setRepairToken(e.target.value)}
                            className="w-full rounded bg-slate-900 border border-slate-700 text-slate-200 px-2 py-1 text-xs font-mono"
                            placeholder={t('boot.repair_session.token')}
                          />
                          <button
                            type="button"
                            onClick={runRepairExecute}
                            disabled={rescueLoading || !repairSessionId || !repairToken || !repairActionCode}
                            className="px-2 py-1 rounded bg-red-700 hover:bg-red-600 text-white text-xs disabled:opacity-60"
                          >
                            {t('boot.repair_execute.run')}
                          </button>
                        </div>
                      ) : null}
                    </div>
                  )
                })()}
                {(() => {
                  const rr = (rescueExecuteResult.rescue_report ?? {}) as Record<string, unknown>
                  const st = String(rr.report_status ?? '')
                  if (!st) return null
                  const sections = Array.isArray(rr.sections) ? (rr.sections as Record<string, unknown>[]) : []
                  const risks = Array.isArray(rr.risks) ? (rr.risks as string[]) : []
                  const steps = Array.isArray(rr.next_steps) ? (rr.next_steps as string[]) : []
                  const blocked = Array.isArray(rr.blocked_actions) ? (rr.blocked_actions as string[]) : []
                  return (
                    <div className="border border-emerald-700/40 rounded p-2 bg-emerald-950/20 space-y-1">
                      <div className="text-emerald-200">{t('rescue.report.title')}</div>
                      <div className="text-xs text-slate-300">{t(`rescue.report.status.${st}`, { defaultValue: st })}</div>
                      {sections.length > 0 ? <div className="text-xs text-slate-400">{sections.map((x) => t(`rescue.report.sections.${String(x.code ?? '')}`, { defaultValue: String(x.code ?? '') })).join(' | ')}</div> : null}
                      {risks.length > 0 ? <div className="text-xs text-rose-300">{risks.map((r) => t(`rescue.report.risks.${r}`, { defaultValue: r })).join(' | ')}</div> : null}
                      {steps.length > 0 ? <div className="text-xs text-sky-300">{steps.map((n) => t(`rescue.report.next_steps.${n}`, { defaultValue: n })).join(' | ')}</div> : null}
                      {blocked.length > 0 ? <div className="text-xs text-amber-300">{blocked.map((b) => t(`rescue.report.blocked_actions.${b}`, { defaultValue: b })).join(' | ')}</div> : null}
                    </div>
                  )
                })()}
                <pre className="overflow-auto max-h-56 text-xs text-slate-300 bg-slate-900/50 p-2 rounded">
                  {JSON.stringify(rescueExecuteResult, null, 2)}
                </pre>
                {repairExecuteResult ? (
                  <pre className="overflow-auto max-h-56 text-xs text-slate-300 bg-slate-900/50 p-2 rounded">
                    {JSON.stringify(repairExecuteResult, null, 2)}
                  </pre>
                ) : null}
              </div>
            ) : null}
          </div>

          <div className="grid lg:grid-cols-2 gap-4">
            <div className="card bg-slate-800/60 border border-slate-700">
              <h2 className="text-base font-semibold text-white mb-2">{t('inspect.page.storage')}</h2>
              <pre className="text-xs text-slate-300 overflow-auto max-h-72">
                {JSON.stringify(data.storage ?? {}, null, 2)}
              </pre>
            </div>
            <div className="card bg-slate-800/60 border border-slate-700">
              <h2 className="text-base font-semibold text-white mb-2">{t('inspect.page.filesystems')}</h2>
              <pre className="text-xs text-slate-300 overflow-auto max-h-72">
                {JSON.stringify(data.filesystems ?? {}, null, 2)}
              </pre>
            </div>
            <div className="card bg-slate-800/60 border border-slate-700">
              <h2 className="text-base font-semibold text-white mb-2">{t('inspect.page.boot')}</h2>
              <pre className="text-xs text-slate-300 overflow-auto max-h-72">
                {JSON.stringify(data.boot ?? {}, null, 2)}
              </pre>
            </div>
            <div className="card bg-slate-800/60 border border-slate-700">
              <h2 className="text-base font-semibold text-white mb-2">{t('inspect.page.network')}</h2>
              <pre className="text-xs text-slate-300 overflow-auto max-h-72">
                {JSON.stringify(data.network ?? {}, null, 2)}
              </pre>
            </div>
          </div>

          <div className="card bg-slate-800/60 border border-slate-700">
            <h2 className="text-base font-semibold text-white mb-2">{t('inspect.page.osHints')}</h2>
            <pre className="text-xs text-slate-300 overflow-auto">{JSON.stringify(osHints, null, 2)}</pre>
          </div>

          <div className="card bg-slate-800/60 border border-slate-700">
            <h2 className="text-base font-semibold text-white mb-2">{t('inspect.page.sources')}</h2>
            <pre className="text-xs text-slate-300 overflow-auto max-h-48">
              {JSON.stringify(
                {
                  source_modules: data.source_modules ?? [],
                  warnings: data.warnings ?? [],
                  errors: data.errors ?? [],
                  system: data.system ?? {},
                },
                null,
                2,
              )}
            </pre>
          </div>
        </>
      ) : null}
    </div>
  )
}

export default InspectRun
