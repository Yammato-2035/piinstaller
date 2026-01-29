import React, { useEffect, useState } from 'react'
import { Settings, Wifi, Monitor, Printer, Scan, Keyboard, Globe, Shield, Eye, Laptop, Mouse, Layout, Palette, Link2Off, Bluetooth } from 'lucide-react'
import toast from 'react-hot-toast'
import { motion } from 'framer-motion'
import { fetchApi } from '../api'
import SudoPasswordModal from '../components/SudoPasswordModal'

type ControlCenterSection = 
  | 'wifi'
  | 'bluetooth'
  | 'ssh'
  | 'vnc'
  | 'keyboard'
  | 'locale'
  | 'desktop'
  | 'display'
  | 'printer'
  | 'scanner'
  | 'performance'
  | 'mouse'
  | 'taskbar'
  | 'theme'

interface SectionConfig {
  id: ControlCenterSection
  name: string
  icon: React.ReactNode
  description: string
}

const ControlCenter: React.FC = () => {
  const [activeSection, setActiveSection] = useState<ControlCenterSection>('wifi')
  const [sudoModalOpen, setSudoModalOpen] = useState(false)
  const [pendingAction, setPendingAction] = useState<null | ((sudoPassword: string) => Promise<void>)>(null)
  
  // WiFi State
  const [wifiNetworks, setWifiNetworks] = useState<any[]>([])
  const [wifiConfig, setWifiConfig] = useState<any[]>([])
  const [wifiStatus, setWifiStatus] = useState<{
    connected?: boolean
    ssid?: string | null
    interface?: string
    signal?: number | null
    wifi_enabled?: boolean
  } | null>(null)
  const [newWifiSSID, setNewWifiSSID] = useState('')
  const [newWifiPassword, setNewWifiPassword] = useState('')
  const [wifiSecurity, setWifiSecurity] = useState('WPA2')
  const [wifiSearchTerm, setWifiSearchTerm] = useState('')
  const [scanningNetworks, setScanningNetworks] = useState(false)
  const [wifiDisconnecting, setWifiDisconnecting] = useState(false)
  const [wifiEnabledToggling, setWifiEnabledToggling] = useState(false)
  
  // SSH State
  const [sshEnabled, setSshEnabled] = useState(false)
  const [sshRunning, setSshRunning] = useState(false)
  
  // VNC State
  const [vncEnabled, setVncEnabled] = useState(false)
  const [vncPassword, setVncPassword] = useState('')
  const [vncNetworkInfo, setVncNetworkInfo] = useState<{ ips: string[]; hostname?: string } | null>(null)
  
  // Keyboard State
  const [keyboardLayout, setKeyboardLayout] = useState('de')
  const [keyboardVariant, setKeyboardVariant] = useState('')
  
  // Locale State
  const [locale, setLocale] = useState('de_DE.UTF-8')
  const [timezone, setTimezone] = useState('Europe/Berlin')
  
  // Desktop State (Boot-Ziel)
  const [desktopBootTarget, setDesktopBootTarget] = useState<'graphical' | 'multi-user' | null>(null)
  const [desktopBootTargetSelection, setDesktopBootTargetSelection] = useState<'graphical' | 'multi-user'>('graphical')
  const [desktopBootTargetLoading, setDesktopBootTargetLoading] = useState(false)
  const [desktopBootTargetSaving, setDesktopBootTargetSaving] = useState(false)
  
  // Display State
  const [displayOutputs, setDisplayOutputs] = useState<Array<{ name: string; resolution: string; refresh_rate: number; rotation: string; modes: Array<{ mode: string; rates: number[]; current?: number }> }>>([])
  const [displayFallback, setDisplayFallback] = useState(false)
  const [displaySelectedOutput, setDisplaySelectedOutput] = useState('')
  const [displayMode, setDisplayMode] = useState('')
  const [displayRate, setDisplayRate] = useState<number | ''>('')
  const [displayRotation, setDisplayRotation] = useState<'normal' | 'left' | 'right' | 'inverted'>('normal')
  const [displayLoading, setDisplayLoading] = useState(false)
  const [displaySaving, setDisplaySaving] = useState(false)
  
  const [printers, setPrinters] = useState<Array<{ name: string; status: string }>>([])
  const [printersLoading, setPrintersLoading] = useState(false)
  const [scanners, setScanners] = useState<Array<{ name: string; device: string }>>([])
  const [scannersLoading, setScannersLoading] = useState(false)
  const [scannersError, setScannersError] = useState<string | null>(null)
  const [saneCheck, setSaneCheck] = useState<{
    scanimage: boolean
    scanimage_path: string | null
    sane_find_scanner: boolean
    sane_find_scanner_path: string | null
    packages: Record<string, boolean>
  } | null>(null)
  
  const [performance, setPerformance] = useState<{
    governor: string | null
    governors: string[]
    gpu_mem: string | null
    arm_freq: string | null
    over_voltage: string | null
    force_turbo: boolean | null
    swap_total_mb: number
    swap_used_mb: number
    swap_size_mb: number | null
    swap_editable: boolean
  } | null>(null)
  const [performanceLoading, setPerformanceLoading] = useState(false)
  const [performanceSaving, setPerformanceSaving] = useState(false)
  const [perfForm, setPerfForm] = useState({
    governor: '',
    gpu_mem: '',
    arm_freq: '',
    over_voltage: '',
    force_turbo: false,
    swap_size_mb: '',
  })
  
  const sections: SectionConfig[] = [
    { id: 'wifi', name: 'WLAN', icon: <Wifi />, description: 'WiFi-Netzwerke verwalten' },
    { id: 'ssh', name: 'SSH', icon: <Shield />, description: 'SSH-Zugriff konfigurieren' },
    { id: 'vnc', name: 'VNC', icon: <Eye />, description: 'VNC Remote-Desktop' },
    { id: 'keyboard', name: 'Tastatur', icon: <Keyboard />, description: 'Tastatur-Layout' },
    { id: 'locale', name: 'Lokalisierung', icon: <Globe />, description: 'Sprache & Zeitzone' },
    { id: 'desktop', name: 'Desktop', icon: <Laptop />, description: 'Desktop-Einstellungen' },
    { id: 'display', name: 'Display', icon: <Monitor />, description: 'Bildschirm-Einstellungen' },
    { id: 'printer', name: 'Drucker', icon: <Printer />, description: 'Drucker verwalten' },
    { id: 'scanner', name: 'Scanner', icon: <Scan />, description: 'Scanner verwalten' },
    { id: 'performance', name: 'Performance', icon: <Settings />, description: 'System-Performance' },
    { id: 'mouse', name: 'Maus', icon: <Mouse />, description: 'Maus-Einstellungen' },
    { id: 'taskbar', name: 'Taskleiste', icon: <Layout />, description: 'Taskleiste konfigurieren' },
    { id: 'theme', name: 'Theme', icon: <Palette />, description: 'Erscheinungsbild' },
  ]

  useEffect(() => {
    loadSectionData(activeSection)
  }, [activeSection])

  const loadSectionData = async (section: ControlCenterSection) => {
    try {
      switch (section) {
        case 'wifi':
          await loadWifiConfig()
          await loadWifiStatus()
          break
        case 'bluetooth':
          await loadBluetoothStatus()
          break
        case 'ssh':
          await loadSSHStatus()
          break
        case 'vnc':
          await loadVNCStatus()
          await loadVNCNetworkInfo()
          break
        case 'keyboard':
          await loadKeyboardLayout()
          break
        case 'locale':
          await loadLocale()
          break
        case 'desktop':
          await loadDesktopBootTarget()
          break
        case 'display':
          await loadDisplaySettings()
          break
        case 'printer':
          await loadPrinters()
          break
        case 'scanner':
          await loadScanners()
          break
        case 'performance':
          await loadPerformance()
          break
        case 'mouse':
        case 'taskbar':
        case 'theme':
          break
      }
    } catch (e) {
      console.error('Fehler beim Laden:', e)
    }
  }

  const loadWifiConfig = async () => {
    try {
      const r = await fetchApi('/api/control-center/wifi/config')
      const d = await r.json()
      if (d.status === 'success') {
        setWifiConfig(d.networks || [])
      }
    } catch (e) {
      // Ignore
    }
  }

  const loadWifiStatus = async () => {
    try {
      const r = await fetchApi('/api/control-center/wifi/status')
      const d = await r.json()
      if (d.status === 'success') {
        setWifiStatus({
          connected: d.connected,
          ssid: d.ssid ?? null,
          interface: d.interface,
          signal: d.signal ?? null,
          wifi_enabled: d.wifi_enabled !== false,
        })
      } else {
        setWifiStatus(null)
      }
    } catch (e) {
      setWifiStatus(null)
    }
  }

  const loadBluetoothStatus = async () => {
    try {
      const r = await fetchApi('/api/control-center/bluetooth/status')
      const d = await r.json()
      if (d.status === 'success') {
        setBluetoothStatus({
          enabled: d.enabled !== false,
          connected_devices: d.connected_devices || [],
        })
      } else {
        setBluetoothStatus(null)
      }
    } catch (e) {
      setBluetoothStatus(null)
    }
  }

  const scanBluetoothDevices = async () => {
    setScanningBluetooth(true)
    const doScan = async (sudoPassword: string) => {
      try {
        const body = sudoPassword ? { sudo_password: sudoPassword } : {}
        const r = await fetchApi('/api/control-center/bluetooth/scan', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        })
        const d = await r.json()
        if (d.status === 'success') {
          setBluetoothDevices(d.devices || [])
          toast.success(`${d.devices?.length || 0} Bluetooth-Geräte gefunden`)
        } else {
          toast.error(d.message || 'Fehler beim Scannen')
        }
      } catch (e) {
        toast.error('Fehler beim Bluetooth-Scan')
      } finally {
        setScanningBluetooth(false)
      }
    }
    if (await hasSavedSudoPassword()) {
      await doScan('')
    } else {
      setSudoModalOpen(true)
      setPendingAction(() => async (pwd: string) => {
        await storeSudoPassword(pwd)
        await doScan(pwd)
      })
    }
  }

  const setBluetoothEnabled = async (enabled: boolean) => {
    await requireSudo(
      {
        title: enabled ? 'Bluetooth aktivieren' : 'Bluetooth deaktivieren',
        subtitle: 'Administrator-Rechte erforderlich (rfkill).',
        confirmText: 'Bestätigen',
      },
      async (pwd?: string) => {
        setBluetoothEnabledToggling(true)
        try {
          const body: Record<string, unknown> = { enabled }
          if (pwd) (body as Record<string, string>).sudo_password = pwd
          const r = await fetchApi('/api/control-center/bluetooth/enabled', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
          })
          const d = await r.json()
          if (d.status === 'success') {
            toast.success(d.message || (enabled ? 'Bluetooth aktiviert' : 'Bluetooth deaktiviert'))
            loadBluetoothStatus()
            if (enabled) setBluetoothDevices([])
          } else {
            toast.error(d.message || 'Aktion fehlgeschlagen')
          }
        } catch (e) {
          toast.error('Fehler beim Ändern')
        } finally {
          setBluetoothEnabledToggling(false)
        }
      }
    )
  }

  const scanWifiNetworks = async () => {
    setScanningNetworks(true)
    const doScan = async (sudoPassword: string) => {
      try {
        const r = await fetchApi('/api/control-center/wifi/scan', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ sudo_password: sudoPassword }),
        })
        const d = await r.json()
        if (d.status === 'success') {
          setWifiNetworks(d.networks || [])
          toast.success(`${d.networks?.length || 0} Netzwerke gefunden`)
        } else {
          toast.error(d.message || 'Fehler beim Scannen')
        }
      } catch (e) {
        toast.error('Fehler beim Scannen der Netzwerke')
      } finally {
        setScanningNetworks(false)
      }
    }
    if (await hasSavedSudoPassword()) {
      try {
        const r = await fetchApi('/api/control-center/wifi/scan', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({}),
        })
        const d = await r.json()
        if (d.status === 'success') {
          setWifiNetworks(d.networks || [])
          toast.success(`${d.networks?.length || 0} Netzwerke gefunden`)
        } else if (d.requires_sudo_password) {
          setSudoModalOpen(true)
          setPendingAction(() => async (pwd: string) => {
            await storeSudoPassword(pwd)
            await doScan(pwd)
          })
          return
        } else {
          toast.error(d.message || 'Fehler beim Scannen')
        }
      } catch (e) {
        toast.error('Fehler beim Scannen der Netzwerke')
      } finally {
        setScanningNetworks(false)
      }
      return
    }
    setSudoModalOpen(true)
    setPendingAction(() => async (pwd: string) => {
      await storeSudoPassword(pwd)
      await doScan(pwd)
    })
  }

  const filteredWifiNetworks = wifiNetworks.filter((net) =>
    net.ssid?.toLowerCase().includes(wifiSearchTerm.toLowerCase())
  )

  const loadSSHStatus = async () => {
    try {
      const r = await fetchApi('/api/control-center/ssh/status')
      const d = await r.json()
      if (d.status === 'success') {
        setSshEnabled(d.enabled || false)
        setSshRunning(d.running || false)
      }
    } catch (e) {
      // Ignore
    }
  }

  const loadVNCStatus = async () => {
    try {
      const r = await fetchApi('/api/control-center/vnc/status')
      const d = await r.json()
      if (d.status === 'success') {
        setVncEnabled(d.running || false)
      }
    } catch (e) {
      // Ignore
    }
  }

  const loadVNCNetworkInfo = async () => {
    try {
      const r = await fetchApi('/api/system/network')
      const d = await r.json()
      if (d?.status === 'success' && Array.isArray(d.ips)) {
        setVncNetworkInfo({ ips: d.ips, hostname: d.hostname })
      } else {
        setVncNetworkInfo(null)
      }
    } catch (e) {
      setVncNetworkInfo(null)
    }
  }

  const loadKeyboardLayout = async () => {
    try {
      const r = await fetchApi('/api/control-center/keyboard')
      const d = await r.json()
      if (d.status === 'success') {
        setKeyboardLayout(d.layout || 'de')
        setKeyboardVariant(d.variant || '')
      }
    } catch (e) {
      // Ignore
    }
  }

  const loadLocale = async () => {
    try {
      const r = await fetchApi('/api/control-center/locale')
      const d = await r.json()
      if (d.status === 'success') {
        setLocale(d.locale || 'de_DE.UTF-8')
        setTimezone(d.timezone || 'Europe/Berlin')
      }
    } catch (e) {
      // Ignore
    }
  }

  const loadDesktopBootTarget = async () => {
    setDesktopBootTargetLoading(true)
    try {
      const r = await fetchApi('/api/control-center/desktop/boot-target')
      const d = await r.json()
      if (d.status === 'success' && (d.target === 'graphical' || d.target === 'multi-user')) {
        setDesktopBootTarget(d.target)
        setDesktopBootTargetSelection(d.target)
      } else {
        setDesktopBootTarget(null)
      }
    } catch (e) {
      setDesktopBootTarget(null)
    } finally {
      setDesktopBootTargetLoading(false)
    }
  }

  const loadDisplaySettings = async () => {
    setDisplayLoading(true)
    try {
      const r = await fetchApi('/api/control-center/display')
      const d = await r.json()
      if (d.status === 'success' && Array.isArray(d.outputs) && d.outputs.length > 0) {
        setDisplayOutputs(d.outputs)
        setDisplayFallback(d.fallback === true)
        const o = d.outputs[0]
        setDisplaySelectedOutput(o.name)
        const res = o.resolution || '1920x1080'
        const modes = o.modes || []
        const mr = modes.find((m: { mode: string }) => m.mode === res)
        setDisplayMode(mr ? res : (modes[0]?.mode || res))
        const rate = typeof o.refresh_rate === 'number' ? o.refresh_rate : (mr?.rates?.[0] ?? modes[0]?.rates?.[0])
        setDisplayRate(rate != null ? rate : '')
        const rot = (o.rotation || 'normal').toLowerCase()
        setDisplayRotation((rot === 'left' || rot === 'right' || rot === 'inverted' ? rot : 'normal') as 'normal' | 'left' | 'right' | 'inverted')
      } else {
        setDisplayOutputs([])
        setDisplayFallback(false)
      }
    } catch (e) {
      setDisplayOutputs([])
      setDisplayFallback(false)
    } finally {
      setDisplayLoading(false)
    }
  }

  const loadPrinters = async () => {
    setPrintersLoading(true)
    try {
      const r = await fetchApi('/api/control-center/printers')
      const d = await r.json()
      if (d.status === 'success' && Array.isArray(d.printers)) {
        setPrinters(d.printers)
      } else {
        setPrinters([])
      }
    } catch {
      setPrinters([])
    } finally {
      setPrintersLoading(false)
    }
  }

  const loadPerformance = async () => {
    setPerformanceLoading(true)
    try {
      const r = await fetchApi('/api/control-center/performance')
      const d = await r.json()
      if (d.status === 'success') {
        setPerformance({
          governor: d.governor ?? null,
          governors: Array.isArray(d.governors) ? d.governors : [],
          gpu_mem: d.gpu_mem ?? null,
          arm_freq: d.arm_freq ?? null,
          over_voltage: d.over_voltage ?? null,
          force_turbo: d.force_turbo ?? null,
          swap_total_mb: Number(d.swap_total_mb) || 0,
          swap_used_mb: Number(d.swap_used_mb) || 0,
          swap_size_mb: d.swap_size_mb != null ? Number(d.swap_size_mb) : null,
          swap_editable: !!d.swap_editable,
        })
        setPerfForm({
          governor: d.governor ?? '',
          gpu_mem: String(d.gpu_mem ?? ''),
          arm_freq: String(d.arm_freq ?? ''),
          over_voltage: String(d.over_voltage ?? ''),
          force_turbo: !!d.force_turbo,
          swap_size_mb: d.swap_size_mb != null ? String(d.swap_size_mb) : '',
        })
      } else {
        setPerformance(null)
      }
    } catch {
      setPerformance(null)
    } finally {
      setPerformanceLoading(false)
    }
  }

  const savePerformance = async () => {
    await requireSudo(
      {
        title: 'Performance übernehmen',
        subtitle: 'Governor, GPU-Memory, Overclocking und Swap werden angepasst. Config- und Swap-Änderungen erfordern ggf. einen Neustart.',
        confirmText: 'Übernehmen',
      },
      async (pwd?: string) => {
        setPerformanceSaving(true)
        try {
          const body: Record<string, unknown> = {}
          if (perfForm.governor) body.governor = perfForm.governor
          if (perfForm.gpu_mem !== '') body.gpu_mem = perfForm.gpu_mem
          if (perfForm.arm_freq !== '') body.arm_freq = perfForm.arm_freq
          if (perfForm.over_voltage !== '') body.over_voltage = perfForm.over_voltage
          body.force_turbo = perfForm.force_turbo
          if (performance?.swap_editable && perfForm.swap_size_mb !== '') {
            const n = parseInt(perfForm.swap_size_mb, 10)
            if (!isNaN(n) && n >= 0) body.swap_size_mb = n
          }
          if (pwd) (body as Record<string, string>).sudo_password = pwd
          const r = await fetchApi('/api/control-center/performance', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
          })
          const d = await r.json()
          if (d.status === 'success') {
            toast.success(d.message || 'Performance gespeichert.')
            loadPerformance()
          } else {
            toast.error(d.message || 'Performance konnte nicht gespeichert werden.')
          }
        } catch {
          toast.error('Performance konnte nicht gespeichert werden (Backend nicht erreichbar).')
        } finally {
          setPerformanceSaving(false)
        }
      }
    )
  }

  const loadScanners = async () => {
    setScannersLoading(true)
    setScannersError(null)
    try {
      const r = await fetchApi('/api/control-center/scanners')
      const d = await r.json()
      if (d.sane_check) setSaneCheck(d.sane_check)
      if (d.status === 'success' && Array.isArray(d.scanners)) {
        setScanners(d.scanners)
      } else {
        setScanners([])
        if (d.message) setScannersError(d.message)
      }
    } catch {
      setScanners([])
      setScannersError('Backend nicht erreichbar.')
      setSaneCheck(null)
    } finally {
      setScannersLoading(false)
    }
  }

  const applyDisplaySettings = async () => {
    setDisplaySaving(true)
    try {
      const body: Record<string, unknown> = {
        output: displaySelectedOutput || undefined,
        mode: displayMode || undefined,
        rotation: displayRotation,
      }
      if (typeof displayRate === 'number' && displayRate > 0) body.rate = displayRate
      const r = await fetchApi('/api/control-center/display', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const d = await r.json()
      if (d.status === 'success') {
        toast.success(d.message || 'Display-Einstellungen übernommen.')
        loadDisplaySettings()
      } else {
        toast.error(d.message || 'Display-Einstellungen konnten nicht übernommen werden.')
      }
    } catch (e) {
      toast.error('Display-Einstellungen konnten nicht übernommen werden (Backend nicht erreichbar).')
    } finally {
      setDisplaySaving(false)
    }
  }

  const displaySelectedOutputData = displayOutputs.find((o) => o.name === displaySelectedOutput)
  const displayModes = displaySelectedOutputData?.modes ?? []
  const displayRatesForMode = displayModes.find((m) => m.mode === displayMode)?.rates ?? []

  const applyDesktopBootTarget = async () => {
    await requireSudo(
      {
        title: 'Boot-Ziel speichern',
        subtitle: 'Es wird eingestellt, ob der Pi in den Desktop oder in die Kommandozeile startet. Wirkt nach dem nächsten Neustart.',
        confirmText: 'Übernehmen',
      },
      async (pwd?: string) => {
        setDesktopBootTargetSaving(true)
        try {
          const body: Record<string, string> = { target: desktopBootTargetSelection }
          if (pwd) body.sudo_password = pwd
          const r = await fetchApi('/api/control-center/desktop/boot-target', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
          })
          const d = await r.json()
          if (d.status === 'success') {
            toast.success(d.message || 'Boot-Ziel gespeichert. Wirkt nach dem nächsten Neustart.')
            setDesktopBootTarget(desktopBootTargetSelection)
            loadDesktopBootTarget()
          } else {
            toast.error(d.message || 'Boot-Ziel konnte nicht gespeichert werden.')
          }
        } catch (e) {
          toast.error('Boot-Ziel konnte nicht gespeichert werden (Backend nicht erreichbar).')
        } finally {
          setDesktopBootTargetSaving(false)
        }
      }
    )
  }

  const hasSavedSudoPassword = async () => {
    try {
      const r = await fetchApi('/api/users/sudo-password/check')
      if (!r.ok) return false
      const d = await r.json()
      return d?.status === 'success' && !!d?.has_password
    } catch {
      return false
    }
  }

  const storeSudoPassword = async (sudoPassword: string) => {
    const resp = await fetchApi('/api/users/sudo-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sudo_password: sudoPassword }),
    })
    const data = await resp.json()
    if (data.status !== 'success') {
      throw new Error(data.message || 'Sudo-Passwort konnte nicht gespeichert werden')
    }
  }

  const requireSudo = async (
    opts: { title: string; subtitle?: string; confirmText?: string },
    action: (pwd?: string) => Promise<void>
  ) => {
    if (await hasSavedSudoPassword()) {
      await action()
      return
    }

    setSudoModalOpen(true)
    setPendingAction(() => async (pwd: string) => {
      await storeSudoPassword(pwd)
      await action(pwd)
    })
  }

  const addWifiNetwork = async () => {
    if (!newWifiSSID) {
      toast.error('SSID erforderlich')
      return
    }

    await requireSudo(
      {
        title: 'WiFi-Netzwerk hinzufügen',
        subtitle: 'Für die WiFi-Konfiguration werden Administrator-Rechte benötigt.',
        confirmText: 'Hinzufügen',
      },
      async (pwd?: string) => {
        try {
          const body: Record<string, string> = {
            ssid: newWifiSSID,
            password: newWifiPassword,
            security: wifiSecurity,
          }
          if (pwd) body.sudo_password = pwd
          const r = await fetchApi('/api/control-center/wifi/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
          })
          const d = await r.json()
          if (d.status === 'success') {
            toast.success('WiFi-Netzwerk hinzugefügt')
            setNewWifiSSID('')
            setNewWifiPassword('')
            loadWifiConfig()
            loadWifiStatus()
          } else {
            toast.error(d.message || 'Fehler beim Hinzufügen')
          }
        } catch (e) {
          toast.error('Fehler beim Hinzufügen des WiFi-Netzwerks')
        }
      }
    )
  }

  const disconnectWifi = async () => {
    await requireSudo(
      {
        title: 'WLAN trennen',
        subtitle: 'Administrator-Rechte erforderlich.',
        confirmText: 'Trennen',
      },
      async (pwd?: string) => {
        setWifiDisconnecting(true)
        try {
          const body = pwd ? { sudo_password: pwd } : {}
          const r = await fetchApi('/api/control-center/wifi/disconnect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
          })
          const d = await r.json()
          if (d.status === 'success') {
            toast.success(d.message || 'WLAN getrennt')
            loadWifiStatus()
            loadWifiConfig()
          } else {
            toast.error(d.message || 'Trennen fehlgeschlagen')
          }
        } catch (e) {
          toast.error('Fehler beim Trennen')
        } finally {
          setWifiDisconnecting(false)
        }
      }
    )
  }

  const setWifiEnabled = async (enabled: boolean) => {
    await requireSudo(
      {
        title: enabled ? 'WLAN aktivieren' : 'WLAN deaktivieren',
        subtitle: 'Administrator-Rechte erforderlich (rfkill).',
        confirmText: 'Bestätigen',
      },
      async (pwd?: string) => {
        setWifiEnabledToggling(true)
        try {
          const body: Record<string, unknown> = { enabled }
          if (pwd) (body as Record<string, string>).sudo_password = pwd
          const r = await fetchApi('/api/control-center/wifi/enabled', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
          })
          const d = await r.json()
          if (d.status === 'success') {
            toast.success(d.message || (enabled ? 'WLAN aktiviert' : 'WLAN deaktiviert'))
            loadWifiStatus()
            if (enabled) loadWifiConfig()
          } else {
            toast.error(d.message || 'Aktion fehlgeschlagen')
          }
        } catch (e) {
          toast.error('Fehler beim Ändern')
        } finally {
          setWifiEnabledToggling(false)
        }
      }
    )
  }

  const toggleSSH = async () => {
    await requireSudo(
      {
        title: 'SSH ' + (sshEnabled ? 'deaktivieren' : 'aktivieren'),
        subtitle: 'Für die SSH-Konfiguration werden Administrator-Rechte benötigt.',
        confirmText: 'Bestätigen',
      },
      async () => {
        try {
          const r = await fetchApi('/api/control-center/ssh/set', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enabled: !sshEnabled }),
          })
          const d = await r.json()
          if (d.status === 'success') {
            toast.success(d.message || 'SSH-Status geändert')
            loadSSHStatus()
          } else {
            toast.error(d.message || 'Fehler beim Ändern')
          }
        } catch (e) {
          toast.error('Fehler beim Ändern des SSH-Status')
        }
      }
    )
  }

  const toggleVNC = async () => {
    await requireSudo(
      {
        title: 'VNC ' + (vncEnabled ? 'deaktivieren' : 'aktivieren'),
        subtitle: 'Für die VNC-Konfiguration werden Administrator-Rechte benötigt.',
        confirmText: 'Bestätigen',
      },
      async () => {
        try {
          const r = await fetchApi('/api/control-center/vnc/set', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enabled: !vncEnabled, password: vncPassword }),
          })
          const d = await r.json()
          if (d.status === 'success') {
            toast.success(d.message || 'VNC-Status geändert')
            setVncPassword('')
            loadVNCStatus()
          } else {
            toast.error(d.message || 'Fehler beim Ändern')
          }
        } catch (e) {
          toast.error('Fehler beim Ändern des VNC-Status')
        }
      }
    )
  }

  const saveKeyboardLayout = async () => {
    await requireSudo(
      {
        title: 'Tastatur-Layout speichern',
        subtitle: 'Für die Tastatur-Konfiguration werden Administrator-Rechte benötigt.',
        confirmText: 'Speichern',
      },
      async () => {
        try {
          const r = await fetchApi('/api/control-center/keyboard/set', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              layout: keyboardLayout,
              variant: keyboardVariant,
            }),
          })
          const d = await r.json()
          if (d.status === 'success') {
            toast.success('Tastatur-Layout gespeichert')
          } else {
            toast.error(d.message || 'Fehler beim Speichern')
          }
        } catch (e) {
          toast.error('Fehler beim Speichern')
        }
      }
    )
  }

  const saveLocale = async () => {
    await requireSudo(
      {
        title: 'Lokalisierung speichern',
        subtitle: 'Für die Lokalisierungs-Konfiguration werden Administrator-Rechte benötigt.',
        confirmText: 'Speichern',
      },
      async () => {
        try {
          const r = await fetchApi('/api/control-center/locale/set', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              locale: locale,
              timezone: timezone,
            }),
          })
          const d = await r.json()
          if (d.status === 'success') {
            toast.success('Lokalisierung gespeichert')
          } else {
            toast.error(d.message || 'Fehler beim Speichern')
          }
        } catch (e) {
          toast.error('Fehler beim Speichern')
        }
      }
    )
  }

  const renderSectionContent = () => {
    switch (activeSection) {
      case 'wifi':
        return (
          <div className="space-y-6">
            {/* Status: aktuelles WLAN, Trennen, WLAN deaktivieren */}
            <div className="card">
              <h3 className="text-xl font-bold text-white mb-4">WLAN-Status</h3>
              <div className="space-y-4">
                {wifiStatus && (
                  <div className="p-4 bg-slate-700/30 rounded-lg border border-slate-600">
                    <div className="flex flex-wrap items-center justify-between gap-4">
                      <div>
                        <div className="font-semibold text-white">
                          {wifiStatus.connected && wifiStatus.ssid
                            ? `Verbunden mit ${wifiStatus.ssid}`
                            : 'Nicht verbunden'}
                        </div>
                        <div className="text-sm text-slate-400 mt-1">
                          {wifiStatus.interface && `Interface: ${wifiStatus.interface}`}
                          {wifiStatus.connected && typeof wifiStatus.signal === 'number' && (
                            <span className="ml-2">• Signal: {wifiStatus.signal} %</span>
                          )}
                        </div>
                      </div>
                      {wifiStatus.connected && (
                        <button
                          onClick={disconnectWifi}
                          disabled={wifiDisconnecting}
                          className="px-4 py-2 bg-amber-600/80 hover:bg-amber-500 text-white rounded-lg flex items-center gap-2 disabled:opacity-50"
                        >
                          <Link2Off size={16} />
                          {wifiDisconnecting ? 'Trennen…' : 'WLAN trennen'}
                        </button>
                      )}
                    </div>
                  </div>
                )}
                <label className="flex items-center gap-3 p-3 bg-slate-700/30 rounded-lg border border-slate-600 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={wifiStatus?.wifi_enabled === false}
                    onChange={(e) => setWifiEnabled(!e.target.checked)}
                    disabled={wifiEnabledToggling}
                    className="w-5 h-5 accent-amber-500"
                  />
                  <span className="text-white">WLAN deaktivieren</span>
                  {wifiEnabledToggling && <span className="text-sm text-slate-400">…</span>}
                </label>
                <p className="text-xs text-slate-500">
                  Bei deaktiviertem WLAN sind Scan und Hinzufügen nicht möglich. Aktivieren Sie WLAN wieder, um Netzwerke zu verwalten.
                </p>
              </div>
            </div>

            <div className="card">
              <h3 className="text-xl font-bold text-white mb-4">WiFi-Netzwerke</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Neues Netzwerk hinzufügen</label>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <input
                      type="text"
                      placeholder="SSID"
                      value={newWifiSSID}
                      onChange={(e) => setNewWifiSSID(e.target.value)}
                      className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white"
                    />
                    <input
                      type="password"
                      placeholder="Passwort"
                      value={newWifiPassword}
                      onChange={(e) => setNewWifiPassword(e.target.value)}
                      className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white"
                    />
                    <select
                      value={wifiSecurity}
                      onChange={(e) => setWifiSecurity(e.target.value)}
                      className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white"
                    >
                      <option value="WPA2">WPA2</option>
                      <option value="WPA">WPA</option>
                      <option value="None">Keine Verschlüsselung</option>
                    </select>
                  </div>
                  <button
                    onClick={addWifiNetwork}
                    disabled={wifiStatus?.wifi_enabled === false}
                    className="mt-3 px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Netzwerk hinzufügen
                  </button>
                </div>
                
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-lg font-semibold text-white">Verfügbare Netzwerke</h4>
                    <button
                      onClick={scanWifiNetworks}
                      disabled={scanningNetworks || wifiStatus?.wifi_enabled === false}
                      className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                      <Wifi size={16} className={scanningNetworks ? 'animate-spin' : ''} />
                      {scanningNetworks ? 'Scanne...' : 'Netzwerke scannen'}
                    </button>
                  </div>
                  {wifiNetworks.length > 0 && (
                    <div className="mb-3">
                      <input
                        type="text"
                        placeholder="Netzwerke durchsuchen..."
                        value={wifiSearchTerm}
                        onChange={(e) => setWifiSearchTerm(e.target.value)}
                        className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white"
                      />
                    </div>
                  )}
                  {wifiNetworks.length === 0 ? (
                    <p className="text-slate-400">Keine Netzwerke gescannt. Klicken Sie auf "Netzwerke scannen".</p>
                  ) : (
                    <div className="space-y-2 max-h-96 overflow-y-auto">
                      {filteredWifiNetworks.length === 0 ? (
                        <p className="text-slate-400">Keine Netzwerke gefunden</p>
                      ) : (
                        filteredWifiNetworks.map((net, idx) => (
                          <div
                            key={idx}
                            className="p-3 bg-slate-700/30 rounded-lg border border-slate-600 hover:border-sky-500 cursor-pointer transition-colors"
                            onClick={() => {
                              setNewWifiSSID(net.ssid || '')
                            }}
                          >
                            <div className="flex items-center justify-between">
                              <div>
                                <div className="font-semibold text-white">{net.ssid || 'Unbekannt'}</div>
                                <div className="text-sm text-slate-400">
                                  {net.security || 'Unbekannt'} {net.encrypted ? '• Verschlüsselt' : '• Offen'}
                                  {net.signal_strength !== undefined && ` • Signal: ${net.signal_strength}%`}
                                </div>
                              </div>
                              {net.signal_strength !== undefined && (
                                <div className="flex items-center gap-1">
                                  {[...Array(4)].map((_, i) => (
                                    <div
                                      key={i}
                                      className={`w-1 h-${Math.max(2, Math.floor((net.signal_strength || 0) / 25))} bg-${
                                        (net.signal_strength || 0) > i * 25 ? 'green' : 'slate'
                                      }-500 rounded`}
                                      style={{
                                        height: `${Math.max(4, Math.floor(((net.signal_strength || 0) / 100) * 16))}px`,
                                        width: '4px',
                                        backgroundColor: (net.signal_strength || 0) > i * 25 ? '#10b981' : '#64748b',
                                      }}
                                    />
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  )}
                </div>
                
                <div>
                  <h4 className="text-lg font-semibold text-white mb-2">Konfigurierte Netzwerke</h4>
                  {wifiConfig.length === 0 ? (
                    <p className="text-slate-400">Keine Netzwerke konfiguriert</p>
                  ) : (
                    <div className="space-y-2">
                      {wifiConfig.map((net, idx) => (
                        <div key={idx} className="p-3 bg-slate-700/30 rounded-lg border border-slate-600">
                          <div className="font-semibold text-white">{net.ssid}</div>
                          <div className="text-sm text-slate-400">{net.security || 'Unbekannt'}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )

      case 'bluetooth':
        return (
          <div className="space-y-6">
            {/* Status: Bluetooth aktiviert, verbundene Geräte */}
            <div className="card">
              <h3 className="text-xl font-bold text-white mb-4">Bluetooth-Status</h3>
              <div className="space-y-4">
                {bluetoothStatus && (
                  <div className="p-4 bg-slate-700/30 rounded-lg border border-slate-600">
                    <div className="font-semibold text-white mb-2">
                      {bluetoothStatus.enabled ? 'Bluetooth aktiviert' : 'Bluetooth deaktiviert'}
                    </div>
                    {bluetoothStatus.enabled && bluetoothStatus.connected_devices && bluetoothStatus.connected_devices.length > 0 && (
                      <div className="mt-3">
                        <div className="text-sm text-slate-300 mb-2">Verbundene Geräte:</div>
                        <div className="space-y-2">
                          {bluetoothStatus.connected_devices.map((dev, idx) => (
                            <div key={idx} className="p-2 bg-slate-800/50 rounded border border-slate-600">
                              <div className="font-medium text-white">{dev.name || 'Unbekannt'}</div>
                              <div className="text-xs text-slate-400">{dev.mac}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    {bluetoothStatus.enabled && (!bluetoothStatus.connected_devices || bluetoothStatus.connected_devices.length === 0) && (
                      <div className="text-sm text-slate-400 mt-2">Keine Geräte verbunden</div>
                    )}
                  </div>
                )}
                <label className="flex items-center gap-3 p-3 bg-slate-700/30 rounded-lg border border-slate-600 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={bluetoothStatus?.enabled === false}
                    onChange={(e) => setBluetoothEnabled(!e.target.checked)}
                    disabled={bluetoothEnabledToggling}
                    className="w-5 h-5 accent-amber-500"
                  />
                  <span className="text-white">Bluetooth deaktivieren</span>
                  {bluetoothEnabledToggling && <span className="text-sm text-slate-400">…</span>}
                </label>
                <p className="text-xs text-slate-500">
                  Bei deaktiviertem Bluetooth sind Scan und Verbindung nicht möglich. Aktivieren Sie Bluetooth wieder, um Geräte zu verwalten.
                </p>
              </div>
            </div>

            <div className="card">
              <h3 className="text-xl font-bold text-white mb-4">Bluetooth-Geräte</h3>
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-lg font-semibold text-white">Verfügbare Geräte</h4>
                    <button
                      onClick={scanBluetoothDevices}
                      disabled={scanningBluetooth || bluetoothStatus?.enabled === false}
                      className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                      <Bluetooth size={16} className={scanningBluetooth ? 'animate-spin' : ''} />
                      {scanningBluetooth ? 'Scanne...' : 'Geräte scannen'}
                    </button>
                  </div>
                  {bluetoothDevices.length === 0 ? (
                    <p className="text-slate-400">Keine Geräte gescannt. Klicken Sie auf "Geräte scannen".</p>
                  ) : (
                    <div className="space-y-2 max-h-96 overflow-y-auto">
                      {bluetoothDevices.map((dev, idx) => (
                        <div
                          key={idx}
                          className="p-3 bg-slate-700/30 rounded-lg border border-slate-600"
                        >
                          <div className="font-semibold text-white">{dev.name || 'Unbekannt'}</div>
                          <div className="text-sm text-slate-400">{dev.mac}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )
      
      case 'ssh':
        return (
          <div className="card">
            <h3 className="text-xl font-bold text-white mb-4">SSH-Zugriff</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg border border-slate-600">
                <div>
                  <div className="font-semibold text-white">SSH aktiviert</div>
                  <div className="text-sm text-slate-400">
                    Status: {sshRunning ? 'Läuft' : 'Gestoppt'}
                  </div>
                </div>
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={sshEnabled}
                    onChange={toggleSSH}
                    className="w-5 h-5 accent-sky-500"
                  />
                  <span className="text-sm text-slate-300">{sshEnabled ? 'Aktiviert' : 'Deaktiviert'}</span>
                </label>
              </div>
            </div>
          </div>
        )
      
      case 'vnc':
        return (
          <div className="card">
            <h3 className="text-xl font-bold text-white mb-4">VNC Remote-Desktop</h3>
            <div className="space-y-4">
              <div className="p-3 bg-amber-900/20 border border-amber-700/50 rounded-lg">
                <p className="text-sm text-amber-200">
                  <strong>Hinweis:</strong> Das PI-Installer-Frontend zeigt den grafischen Desktop des Pi <strong>nicht</strong>. 
                  Um den Desktop am Remote-Rechner anzuzeigen, nutzen Sie einen <strong>VNC-Client</strong> (z. B. RealVNC Viewer, TigerVNC) 
                  und verbinden sich mit dem Pi (siehe Verbindungsinfos unten, sobald VNC aktiviert ist).
                </p>
              </div>
              <div className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg border border-slate-600">
                <div>
                  <div className="font-semibold text-white">VNC aktiviert</div>
                  <div className="text-sm text-slate-400">
                    Status: {vncEnabled ? 'Läuft' : 'Gestoppt'}
                  </div>
                </div>
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={vncEnabled}
                    onChange={toggleVNC}
                    className="w-5 h-5 accent-sky-500"
                  />
                  <span className="text-sm text-slate-300">{vncEnabled ? 'Aktiviert' : 'Deaktiviert'}</span>
                </label>
              </div>
              {!vncEnabled && (
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">VNC-Passwort (optional)</label>
                  <input
                    type="password"
                    placeholder="VNC-Passwort"
                    value={vncPassword}
                    onChange={(e) => setVncPassword(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white"
                  />
                </div>
              )}
              {vncEnabled && (
                <div className="p-4 bg-slate-700/30 rounded-lg border border-slate-600 space-y-3">
                  <h4 className="text-sm font-semibold text-white">So verbinden Sie sich vom Remote-Rechner</h4>
                  <p className="text-sm text-slate-400">
                    Installieren Sie einen VNC-Client (z. B. RealVNC Viewer, TigerVNC, Remmina). Verbinden Sie sich mit der Pi-IP und Port 5900.
                  </p>
                  {vncNetworkInfo?.ips && vncNetworkInfo.ips.length > 0 ? (
                    <div className="space-y-2">
                      {vncNetworkInfo.ips.map((ip, idx) => (
                        <div key={idx} className="flex flex-wrap items-center gap-2">
                          <code className="px-2 py-1 bg-slate-800 rounded text-sky-300 font-mono text-sm">
                            {ip}:5900
                          </code>
                          <button
                            type="button"
                            onClick={() => {
                              navigator.clipboard.writeText(`${ip}:5900`)
                              toast.success('Adresse kopiert')
                            }}
                            className="text-xs text-slate-400 hover:text-sky-400"
                          >
                            Kopieren
                          </button>
                          <code className="px-2 py-1 bg-slate-800 rounded text-sky-300 font-mono text-sm">
                            vnc://{ip}
                          </code>
                          <button
                            type="button"
                            onClick={() => {
                              navigator.clipboard.writeText(`vnc://${ip}`)
                              toast.success('vnc://-Link kopiert')
                            }}
                            className="text-xs text-slate-400 hover:text-sky-400"
                          >
                            Kopieren
                          </button>
                        </div>
                      ))}
                      {vncNetworkInfo.hostname && vncNetworkInfo.hostname !== 'unknown' && (
                        <p className="text-xs text-slate-500">Hostname: {vncNetworkInfo.hostname}</p>
                      )}
                    </div>
                  ) : (
                    <p className="text-sm text-slate-500">
                      Keine IP-Adressen ermittelt. Prüfen Sie die Netzwerkverbindung des Pi (/api/system/network).
                    </p>
                  )}
                  <p className="text-xs text-slate-500">
                    Firewall: Falls Verbindung fehlschlägt, ggf. Port 5900 freigeben ({' '}
                    <code className="text-slate-400">sudo ufw allow 5900/tcp</code>
                    ).
                  </p>
                </div>
              )}
            </div>
          </div>
        )
      
      case 'keyboard':
        return (
          <div className="card">
            <h3 className="text-xl font-bold text-white mb-4">Tastatur-Layout</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Layout</label>
                <select
                  value={keyboardLayout}
                  onChange={(e) => setKeyboardLayout(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white"
                >
                  <option value="de">Deutsch</option>
                  <option value="us">Englisch (US)</option>
                  <option value="gb">Englisch (GB)</option>
                  <option value="fr">Französisch</option>
                  <option value="es">Spanisch</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Variante (optional)</label>
                <input
                  type="text"
                  value={keyboardVariant}
                  onChange={(e) => setKeyboardVariant(e.target.value)}
                  placeholder="z.B. nodeadkeys"
                  className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white"
                />
              </div>
              <button
                onClick={saveKeyboardLayout}
                className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-lg"
              >
                Speichern
              </button>
            </div>
          </div>
        )
      
      case 'locale':
        return (
          <div className="card">
            <h3 className="text-xl font-bold text-white mb-4">Lokalisierung</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Sprache/Locale</label>
                <select
                  value={locale}
                  onChange={(e) => setLocale(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white"
                >
                  <option value="de_DE.UTF-8">Deutsch (Deutschland)</option>
                  <option value="en_US.UTF-8">Englisch (USA)</option>
                  <option value="en_GB.UTF-8">Englisch (Großbritannien)</option>
                  <option value="fr_FR.UTF-8">Französisch</option>
                  <option value="es_ES.UTF-8">Spanisch</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Zeitzone</label>
                <select
                  value={timezone}
                  onChange={(e) => setTimezone(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white"
                >
                  <option value="Europe/Berlin">Europa/Berlin</option>
                  <option value="Europe/London">Europa/London</option>
                  <option value="America/New_York">Amerika/New York</option>
                  <option value="America/Los_Angeles">Amerika/Los Angeles</option>
                  <option value="Asia/Tokyo">Asien/Tokyo</option>
                </select>
              </div>
              <button
                onClick={saveLocale}
                className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-lg"
              >
                Speichern
              </button>
            </div>
          </div>
        )
      
      case 'desktop':
        return (
          <div className="card">
            <h3 className="text-xl font-bold text-white mb-4">Desktop-Einstellungen</h3>
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-semibold text-slate-200 mb-2">Boot-Ziel</h4>
                <p className="text-sm text-slate-400 mb-3">
                  Startet der Pi in die grafische Oberfläche (Desktop) oder in die Kommandozeile? Wirkt nach dem nächsten Neustart.
                </p>
                {desktopBootTargetLoading ? (
                  <p className="text-sm text-slate-500">Lade…</p>
                ) : (
                  <>
                    <div className="flex flex-wrap gap-4 mb-4">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="boot-target"
                          checked={desktopBootTargetSelection === 'graphical'}
                          onChange={() => setDesktopBootTargetSelection('graphical')}
                          className="w-4 h-4 accent-sky-500"
                        />
                        <span className="text-white">Desktop</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="boot-target"
                          checked={desktopBootTargetSelection === 'multi-user'}
                          onChange={() => setDesktopBootTargetSelection('multi-user')}
                          className="w-4 h-4 accent-sky-500"
                        />
                        <span className="text-white">Kommandozeile</span>
                      </label>
                    </div>
                    {desktopBootTarget != null && (
                      <p className="text-xs text-slate-500 mb-3">
                        Aktuell: <span className="text-slate-300">{desktopBootTarget === 'graphical' ? 'Desktop' : 'Kommandozeile'}</span>
                      </p>
                    )}
                    <button
                      type="button"
                      onClick={applyDesktopBootTarget}
                      disabled={desktopBootTargetSaving || desktopBootTargetSelection === desktopBootTarget}
                      className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-lg font-medium text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {desktopBootTargetSaving ? 'Speichere…' : 'Übernehmen'}
                    </button>
                  </>
                )}
              </div>
              <p className="text-xs text-slate-500">
                Geplante Features: Hintergrundbild, Theme, Icon-Set, Schriftgröße, Auto-Login.
              </p>
            </div>
          </div>
        )
      
      case 'display':
        return (
          <div className="card">
            <h3 className="text-xl font-bold text-white mb-4">Display-Einstellungen</h3>
            <div className="space-y-4">
              <p className="text-sm text-slate-400">
                Auflösung, Bildwiederholrate und Rotation des angeschlossenen Bildschirms (xrandr). Kein Neustart nötig.
              </p>
              {displayFallback && (
                <div className="p-3 bg-amber-900/20 border border-amber-700/50 rounded-lg">
                  <p className="text-sm text-amber-200">
                    <strong>Standardwerte:</strong> xrandr war nicht erreichbar (z. B. Backend ohne X-Session oder DISPLAY nicht gesetzt).
                    Es werden Fallback-Werte angezeigt. Übernehmen kann trotzdem versucht werden, sofern X auf dem Pi läuft.
                  </p>
                </div>
              )}
              {displayLoading ? (
                <p className="text-sm text-slate-500">Lade…</p>
              ) : displayOutputs.length === 0 ? (
                <p className="text-sm text-slate-500">
                  Kein Display gefunden. Läuft eine grafische Oberfläche (X11)? xrandr muss verfügbar sein.
                </p>
              ) : (
                <>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-1">Ausgabe</label>
                      <select
                        value={displaySelectedOutput}
                        onChange={(e) => {
                          const name = e.target.value
                          setDisplaySelectedOutput(name)
                          const o = displayOutputs.find((x) => x.name === name)
                          if (o) {
                            setDisplayMode(o.resolution || '')
                            setDisplayRate(typeof o.refresh_rate === 'number' ? o.refresh_rate : '')
                            const rot = (o.rotation || 'normal').toLowerCase()
                            setDisplayRotation((rot === 'left' || rot === 'right' || rot === 'inverted' ? rot : 'normal') as 'normal' | 'left' | 'right' | 'inverted')
                          }
                        }}
                        className="w-full bg-slate-800/60 border border-slate-600 rounded-lg px-3 py-2 text-white"
                      >
                        {displayOutputs.map((o) => (
                          <option key={o.name} value={o.name}>
                            {o.name}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-1">Auflösung</label>
                      <select
                        value={displayMode}
                        onChange={(e) => {
                          setDisplayMode(e.target.value)
                          const m = displayModes.find((x) => x.mode === e.target.value)
                          if (m?.rates?.length) setDisplayRate(m.rates[0])
                        }}
                        className="w-full bg-slate-800/60 border border-slate-600 rounded-lg px-3 py-2 text-white"
                      >
                        {displayModes.map((m) => (
                          <option key={m.mode} value={m.mode}>
                            {m.mode}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-1">Bildwiederholrate (Hz)</label>
                      <select
                        value={displayRate}
                        onChange={(e) => setDisplayRate(e.target.value === '' ? '' : Number(e.target.value))}
                        className="w-full bg-slate-800/60 border border-slate-600 rounded-lg px-3 py-2 text-white"
                      >
                        {displayRatesForMode.map((r) => (
                          <option key={r} value={r}>
                            {r} Hz
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-1">Rotation</label>
                      <select
                        value={displayRotation}
                        onChange={(e) => setDisplayRotation(e.target.value as 'normal' | 'left' | 'right' | 'inverted')}
                        className="w-full bg-slate-800/60 border border-slate-600 rounded-lg px-3 py-2 text-white"
                      >
                        <option value="normal">Normal</option>
                        <option value="left">90° links</option>
                        <option value="right">90° rechts</option>
                        <option value="inverted">180°</option>
                      </select>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={applyDisplaySettings}
                    disabled={displaySaving || !displayMode}
                    className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-lg font-medium text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {displaySaving ? 'Übernehme…' : 'Übernehmen'}
                  </button>
                </>
              )}
            </div>
          </div>
        )
      
      case 'printer':
        return (
          <div className="card">
            <h3 className="text-xl font-bold text-white mb-4">Drucker</h3>
            <div className="space-y-4">
              <p className="text-slate-400 text-sm">Unterstützt USB- und <strong>Netzwerkdrucker</strong> (CUPS). Bei Netzwerkgeräten: gleiches Netzwerk, Gerät eingeschaltet.</p>
              <div className="flex items-center gap-3">
                <button
                  onClick={loadPrinters}
                  disabled={printersLoading}
                  className="px-4 py-2 bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white rounded-lg"
                >
                  {printersLoading ? 'Lade…' : 'Drucker aktualisieren'}
                </button>
              </div>
              {printers.length > 0 ? (
                <ul className="divide-y divide-slate-600">
                  {printers.map((p) => (
                    <li key={p.name} className="py-2 flex items-center justify-between">
                      <span className="font-medium text-white">{p.name}</span>
                      <span className={`text-xs px-2 py-0.5 rounded ${
                        p.status === 'idle' ? 'bg-green-900/50 text-green-300' :
                        p.status === 'printing' ? 'bg-amber-900/50 text-amber-300' :
                        p.status === 'disabled' ? 'bg-slate-600 text-slate-400' : 'bg-slate-600 text-slate-300'
                      }`}>
                        {p.status === 'idle' ? 'Bereit' : p.status === 'printing' ? 'Druckt' : p.status === 'disabled' ? 'Deaktiviert' : p.status}
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-slate-400">Keine Drucker gefunden. CUPS installiert? (<code className="text-slate-500">apt install cups</code>)</p>
              )}
            </div>
          </div>
        )
      
      case 'scanner':
        return (
          <div className="card">
            <h3 className="text-xl font-bold text-white mb-4">Scanner</h3>
            <div className="space-y-4">
              <p className="text-slate-400 text-sm">Unterstützt USB- und <strong>Netzwerkscanner</strong> (SANE, eSCL/airscan). Bei Netzwerkgeräten: gleiches Netzwerk, Gerät eingeschaltet. Erkannte Geräte können Flachbett- und ADF-Scanner sein.</p>
              <div className="flex items-center gap-3">
                <button
                  onClick={loadScanners}
                  disabled={scannersLoading}
                  className="px-4 py-2 bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white rounded-lg"
                >
                  {scannersLoading ? 'Lade…' : 'Scanner aktualisieren'}
                </button>
              </div>
              {scannersError && (
                <p className="text-amber-300 text-sm">{scannersError}</p>
              )}
              {saneCheck && (
                <div className="rounded-lg bg-slate-800/60 border border-slate-600 p-3 space-y-2">
                  <p className="text-sm font-medium text-slate-300">SANE &amp; Programme</p>
                  <ul className="text-sm space-y-1">
                    <li className="flex items-center gap-2">
                      {saneCheck.scanimage ? (
                        <span className="text-green-400">✓</span>
                      ) : (
                        <span className="text-amber-400">✗</span>
                      )}
                      <span className={saneCheck.scanimage ? 'text-slate-300' : 'text-amber-300'}>
                        scanimage {saneCheck.scanimage ? `(${saneCheck.scanimage_path || ''})` : '– fehlt'}
                      </span>
                    </li>
                    <li className="flex items-center gap-2">
                      {saneCheck.sane_find_scanner ? (
                        <span className="text-green-400">✓</span>
                      ) : (
                        <span className="text-amber-400">✗</span>
                      )}
                      <span className={saneCheck.sane_find_scanner ? 'text-slate-300' : 'text-amber-300'}>
                        sane-find-scanner {saneCheck.sane_find_scanner ? `(${saneCheck.sane_find_scanner_path || ''})` : '– fehlt'}
                      </span>
                    </li>
                    {['sane-utils', 'sane-airscan'].map((pkg) => (
                      <li key={pkg} className="flex items-center gap-2">
                        {saneCheck.packages?.[pkg] ? (
                          <span className="text-green-400">✓</span>
                        ) : (
                          <span className="text-amber-400">✗</span>
                        )}
                        <span className={saneCheck.packages?.[pkg] ? 'text-slate-300' : 'text-amber-300'}>
                          {pkg} {saneCheck.packages?.[pkg] ? 'installiert' : '– fehlt'}
                        </span>
                        {pkg === 'sane-airscan' && (
                          <span className="text-slate-500 text-xs">(Netzwerk/eSCL)</span>
                        )}
                      </li>
                    ))}
                  </ul>
                  {(!saneCheck.scanimage || !saneCheck.packages?.['sane-utils']) && (
                    <p className="text-xs text-slate-400 mt-2">
                      Installation: <code className="bg-slate-700 px-1 rounded">sudo apt update</code> dann{' '}
                      <code className="bg-slate-700 px-1 rounded">sudo apt install sane-utils</code>.
                      {!saneCheck.packages?.['sane-airscan'] && (
                        <> Für Netzwerk-Scanner ggf. <code className="bg-slate-700 px-1 rounded">sane-airscan</code>.</>
                      )}
                    </p>
                  )}
                </div>
              )}
              {scanners.length > 0 ? (
                <ul className="divide-y divide-slate-600">
                  {scanners.map((s) => (
                    <li key={s.device} className="py-2 flex flex-col gap-0.5">
                      <span className="font-medium text-white">{s.name}</span>
                      <code className="text-xs text-slate-500 break-all">{s.device}</code>
                    </li>
                  ))}
                </ul>
              ) : !scannersLoading && !scannersError ? (
                <p className="text-slate-400">Keine Scanner gefunden. SANE installiert? (<code className="text-slate-500">apt install sane-utils</code>, ggf. <code className="text-slate-500">sane-airscan</code>)</p>
              ) : null}
            </div>
          </div>
        )
      
      case 'performance':
        return (
          <div className="card">
            <h3 className="text-xl font-bold text-white mb-4">Performance</h3>
            <div className="space-y-4">
              {performanceLoading ? (
                <p className="text-slate-400">Lade…</p>
              ) : performance ? (
                <>
                  <p className="text-slate-400 text-sm">CPU-Governor (sofort wirksam), GPU-Memory, Overclocking und Swap (config.txt / dphys-swapfile). Änderungen an Config oder Swap können einen Neustart erfordern.</p>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-1">CPU-Governor</label>
                      <select
                        value={perfForm.governor}
                        onChange={(e) => setPerfForm((f) => ({ ...f, governor: e.target.value }))}
                        className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white"
                        disabled={!performance.governors.length}
                      >
                        {!performance.governors.length && <option value="">—</option>}
                        {performance.governors.map((g) => (
                          <option key={g} value={g}>{g}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-1">GPU-Memory (MB)</label>
                      <input
                        type="text"
                        value={perfForm.gpu_mem}
                        onChange={(e) => setPerfForm((f) => ({ ...f, gpu_mem: e.target.value }))}
                        placeholder="z. B. 64, 128, 256"
                        className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white placeholder-slate-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-1">CPU-Frequenz (MHz)</label>
                      <input
                        type="text"
                        value={perfForm.arm_freq}
                        onChange={(e) => setPerfForm((f) => ({ ...f, arm_freq: e.target.value }))}
                        placeholder="auto, 600–1500"
                        className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white placeholder-slate-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-1">Over-Voltage (-16…8)</label>
                      <input
                        type="text"
                        value={perfForm.over_voltage}
                        onChange={(e) => setPerfForm((f) => ({ ...f, over_voltage: e.target.value }))}
                        placeholder="0"
                        className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white placeholder-slate-500"
                      />
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="perf-force-turbo"
                      checked={perfForm.force_turbo}
                      onChange={(e) => setPerfForm((f) => ({ ...f, force_turbo: e.target.checked }))}
                      className="rounded border-slate-500 bg-slate-800 text-sky-500"
                    />
                    <label htmlFor="perf-force-turbo" className="text-sm text-slate-300">Turbo-Modus erzwingen (max. CPU-Takt)</label>
                  </div>
                  {performance.swap_editable && (
                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-1">Swap-Größe (MB, dphys-swapfile)</label>
                      <input
                        type="text"
                        value={perfForm.swap_size_mb}
                        onChange={(e) => setPerfForm((f) => ({ ...f, swap_size_mb: e.target.value }))}
                        placeholder={performance.swap_size_mb != null ? String(performance.swap_size_mb) : '100'}
                        className="w-full max-w-xs bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white placeholder-slate-500"
                      />
                      <p className="text-xs text-slate-500 mt-1">Aktuell: {performance.swap_total_mb} MB gesamt, {performance.swap_used_mb} MB belegt.</p>
                    </div>
                  )}
                  {!performance.swap_editable && (performance.swap_total_mb > 0 || performance.swap_used_mb > 0) && (
                    <p className="text-sm text-slate-500">Swap: {performance.swap_total_mb} MB gesamt, {performance.swap_used_mb} MB belegt. Größenänderung nur bei dphys-swapfile möglich.</p>
                  )}
                  <div className="flex flex-wrap gap-3 pt-2">
                    <button
                      onClick={savePerformance}
                      disabled={performanceSaving}
                      className="px-4 py-2 bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white rounded-lg font-medium"
                    >
                      {performanceSaving ? 'Speichern…' : 'Übernehmen'}
                    </button>
                    <button
                      onClick={loadPerformance}
                      disabled={performanceLoading}
                      className="px-4 py-2 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 text-white rounded-lg"
                    >
                      Aktualisieren
                    </button>
                  </div>
                  <p className="text-xs text-amber-200/80">Hinweis: Änderungen an GPU-Memory, Overclocking oder Swap werden in config.txt bzw. dphys-swapfile geschrieben. Neustart kann erforderlich sein.</p>
                </>
              ) : (
                <p className="text-slate-400">Performance-Daten konnten nicht geladen werden.</p>
              )}
            </div>
          </div>
        )

      case 'mouse':
        return (
          <div className="card">
            <h3 className="text-xl font-bold text-white mb-4">Maus-Einstellungen</h3>
            <div className="space-y-4">
              <p className="text-slate-400">Maus-Einstellungen werden in einer zukünftigen Version implementiert.</p>
              <p className="text-sm text-slate-500">Geplante Features: Zeigergeschwindigkeit, Rechts-/Linkshänder, Doppelklick-Geschwindigkeit</p>
            </div>
          </div>
        )
      
      case 'taskbar':
        return (
          <div className="card">
            <h3 className="text-xl font-bold text-white mb-4">Taskleiste</h3>
            <div className="space-y-4">
              <p className="text-slate-400">Taskleisten-Einstellungen werden in einer zukünftigen Version implementiert.</p>
              <p className="text-sm text-slate-500">Geplante Features: Position, Autohide, Größe, Applets</p>
            </div>
          </div>
        )
      
      case 'theme':
        return (
          <div className="card">
            <h3 className="text-xl font-bold text-white mb-4">Theme</h3>
            <div className="space-y-4">
              <p className="text-slate-400">Theme-Einstellungen werden in einer zukünftigen Version implementiert.</p>
              <p className="text-sm text-slate-500">Geplante Features: Farbschema, Icon-Theme, Cursor-Theme, Schriftart</p>
            </div>
          </div>
        )
      
      default:
        return (
          <div className="card">
            <p className="text-slate-400">Dieser Bereich wird in einer zukünftigen Version implementiert.</p>
          </div>
        )
    }
  }

  return (
    <div className="space-y-8 animate-fade-in page-transition">
      <SudoPasswordModal
        open={sudoModalOpen}
        title="Sudo-Passwort erforderlich"
        subtitle="Für diese Aktion werden Administrator-Rechte benötigt."
        confirmText="Bestätigen"
        onCancel={() => {
          setSudoModalOpen(false)
          setPendingAction(null)
          setScanningNetworks(false)
        }}
        onConfirm={async (pwd) => {
          try {
            if (!pendingAction) return
            await pendingAction(pwd)
            toast.success('Sudo-Passwort gespeichert (Session)')
            setSudoModalOpen(false)
            setPendingAction(null)
          } catch (e: any) {
            toast.error(e?.message || 'Sudo-Passwort ungültig')
          }
        }}
      />

      <div>
        <h1 className="text-4xl font-bold text-white mb-2 flex items-center gap-3">
          <Settings className="text-purple-500" />
          Control Center
        </h1>
        <p className="text-slate-400">System-Einstellungen verwalten</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Menü */}
        <div className="lg:col-span-1">
          <div className="card">
            <h2 className="text-lg font-bold text-white mb-4">Bereiche</h2>
            <div className="space-y-2">
              {sections.map((section) => (
                <button
                  key={section.id}
                  onClick={() => setActiveSection(section.id)}
                  className={`w-full text-left p-3 rounded-lg transition-colors duration-150 ${
                    activeSection === section.id
                      ? 'bg-sky-600/60 text-white'
                      : 'bg-slate-700/30 text-slate-300 hover:bg-slate-700/50'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <div className="text-sky-400">{section.icon}</div>
                    <div>
                      <div className="font-semibold">{section.name}</div>
                      <div className="text-xs opacity-75">{section.description}</div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Inhalt */}
        <div className="lg:col-span-3">
          <motion.div
            key={activeSection}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.2 }}
          >
            {renderSectionContent()}
          </motion.div>
        </div>
      </div>
    </div>
  )
}

export default ControlCenter
