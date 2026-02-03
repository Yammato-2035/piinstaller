import React, { useState, useCallback, useMemo, useRef, useEffect } from 'react'
import { Scan, Cpu, Usb, Keyboard, Mouse, Camera, Headphones, ExternalLink, Video, X } from 'lucide-react'
import toast from 'react-hot-toast'
import { motion, AnimatePresence } from 'framer-motion'
import { fetchApi } from '../api'
import { usePlatform } from '../context/PlatformContext'

/** Hinweistexte: Was die Komponente ist, wo sie sitzt, welcher Zustand „normal“ ist. */
const COMPONENT_HINTS: Record<string, { what: string; where: string; normal: string }> = {
  camera: {
    what: 'Webcam bzw. Kamera für Bild/Video.',
    where: 'USB-Anschluss oder integriert (z. B. Laptop).',
    normal: 'Erkannt und funktionsfähig (z. B. mit Cheese oder Browser).',
  },
  keyboard: {
    what: 'Tastatur zur Texteingabe.',
    where: 'USB, Bluetooth oder integriert.',
    normal: 'Erkannt und als Eingabegerät nutzbar.',
  },
  mouse: {
    what: 'Maus als Zeigegerät.',
    where: 'USB oder Bluetooth.',
    normal: 'Erkannt, Cursor bewegt sich und Klicks funktionieren. Für Belegung aller Tasten: xinput, imwheel oder Hersteller-Software (z. B. Logitech Options).',
  },
  touchpad: {
    what: 'Touchpad (Zeigegerät am Notebook).',
    where: 'Integriert (Notebook) oder USB.',
    normal: 'Erkannt als Eingabegerät; Mehrfinger-Gesten ggf. über Einstellungen oder libinput.',
  },
  headset: {
    what: 'Headset / Mikrofon / Lautsprecher (Audio).',
    where: 'USB, Klinke oder Bluetooth.',
    normal: 'Ausgabequelle wählbar unter Musikbox/Einstellungen (PulseAudio/PipeWire). Treiber: ALSA/PulseAudio; Dolby Atmos: herstellerspezifisch (z. B. Dolby Access).',
  },
  gpu: {
    what: 'Grafikkarte (GPU) für Anzeige und ggf. 3D.',
    where: 'PCIe-Steckplatz oder onboard (Raspberry Pi: integriert).',
    normal: 'Treiber geladen; GPU-Temperatur unter Last oft < 85°C (Herstellerangaben beachten).',
  },
  temperature: {
    what: 'CPU-/GPU-Temperatursensoren (thermal_zone, vcgencmd).',
    where: 'Onboard (Raspberry Pi: SoC-Temperatur).',
    normal: 'Raspberry Pi: ca. 40–70°C im Betrieb normal, > 80°C kritisch – Kühlung prüfen.',
  },
  usb: {
    what: 'USB-Geräte (alle angeschlossenen).',
    where: 'USB-Ports (USB-A/USB-C).',
    normal: 'Erkannt und mit passendem Treiber nutzbar.',
  },
  input: {
    what: 'Eingabegeräte (Kernel /dev/input).',
    where: 'Tastatur, Maus, Touchscreen etc.',
    normal: 'In /proc/bus/input/devices gelistet und ansprechbar.',
  },
  drivers: {
    what: 'PCI-Geräte mit zugeordnetem Kernel-Treiber.',
    where: 'Alle PCI(e)-Geräte im System.',
    normal: 'Treiber geladen (nicht „—“) = Gerät vom Kernel unterstützt.',
  },
}

/** Hersteller mit Linux-Treiber-Seiten (für erkannte Hardware). */
const MANUFACTURER_DRIVER_LINKS: { name: string; url: string; keywords: string[] }[] = [
  { name: 'NVIDIA', url: 'https://www.nvidia.com/Download/index.aspx', keywords: ['nvidia', 'geforce', 'quadro', 'tesla'] },
  { name: 'AMD', url: 'https://www.amd.com/en/support', keywords: ['amd', 'radeon', 'ati '] },
  { name: 'Intel', url: 'https://www.intel.com/content/www/us/en/download/785597/intel-graphics-drivers.html', keywords: ['intel', 'graphics', 'uhd', 'iris'] },
  { name: 'Realtek', url: 'https://www.realtek.com/en/downloads', keywords: ['realtek', 'rtl'] },
  { name: 'Broadcom', url: 'https://www.broadcom.com/support', keywords: ['broadcom', 'bcm'] },
  { name: 'Qualcomm', url: 'https://www.qualcomm.com/support', keywords: ['qualcomm', 'atheros'] },
  { name: 'Logitech', url: 'https://support.logitech.com/', keywords: ['logitech'] },
  { name: 'Corsair', url: 'https://github.com/ckb-next/ckb-next', keywords: ['corsair'] },
  { name: 'Lenovo', url: 'https://pcsupport.lenovo.com/', keywords: ['lenovo'] },
  { name: 'Dell', url: 'https://www.dell.com/support/home', keywords: ['dell'] },
  { name: 'HP', url: 'https://support.hp.com/', keywords: ['hewlett', 'hp '] },
]

interface PeripheryScanProps {
  setCurrentPage?: (page: string) => void
}

const STORAGE_KEY = 'pi-installer-periphery-scan-result'

type ScanResult = {
  gpus: { type: string; description: string; driver?: string; driver_hint?: string }[]
  usb: { type: string; description: string }[]
  input_devices: { name: string; handlers: string }[]
  drivers: { device: string; driver: string }[]
}

/** Liefert nur die beim letzten Scan neu hinzugekommenen Komponenten. */
function diffNewComponents(previous: ScanResult | null, current: ScanResult): ScanResult {
  if (!previous) return current
  const keyGpu = (g: { description: string }) => g.description
  const keyUsb = (u: { description: string }) => u.description
  const keyInput = (d: { name: string; handlers?: string }) => `${d.name}|${d.handlers || ''}`
  const keyDriver = (d: { device: string }) => d.device
  const prevGpuSet = new Set(previous.gpus.map(keyGpu))
  const prevUsbSet = new Set(previous.usb.map(keyUsb))
  const prevInputSet = new Set(previous.input_devices.map(keyInput))
  const prevDriverSet = new Set(previous.drivers.map(keyDriver))
  return {
    gpus: current.gpus.filter((g) => !prevGpuSet.has(keyGpu(g))),
    usb: current.usb.filter((u) => !prevUsbSet.has(keyUsb(u))),
    input_devices: current.input_devices.filter((d) => !prevInputSet.has(keyInput(d))),
    drivers: current.drivers.filter((d) => !prevDriverSet.has(keyDriver(d))),
  }
}

function loadStoredResult(): { result: ScanResult; scannedAt: string } | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as { result: ScanResult; scannedAt: string }
    if (parsed?.result && typeof parsed.result === 'object') return parsed
  } catch {}
  return null
}

function saveResult(result: ScanResult) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ result, scannedAt: new Date().toISOString() }))
  } catch {}
}

/** Modal: Kamerastream per getUserMedia anzeigen. */
function CameraStreamModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [active, setActive] = useState(false)
  const startStream = useCallback(async () => {
    setError(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' }, audio: false })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        videoRef.current.play().catch(() => {})
      }
      setActive(true)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e)
      setError(msg || 'Kamera-Zugriff fehlgeschlagen (z. B. Berechtigung oder Gerät belegt).')
    }
  }, [])
  const stopStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop())
      streamRef.current = null
    }
    if (videoRef.current) videoRef.current.srcObject = null
    setActive(false)
    setError(null)
  }, [])
  useEffect(() => {
    if (!open) stopStream()
    return () => { stopStream() }
  }, [open, stopStream])
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="bg-slate-800 border border-slate-600 rounded-xl shadow-xl max-w-2xl w-full overflow-hidden" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between p-3 border-b border-slate-600">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <Video className="text-sky-400" />
            Kamerastream
          </h3>
          <button type="button" onClick={onClose} className="p-2 rounded-lg hover:bg-slate-700 text-slate-400 hover:text-white" aria-label="Schließen">
            <X size={20} />
          </button>
        </div>
        <div className="p-4">
          {error && (
            <p className="text-red-400 text-sm mb-3">{error}</p>
          )}
          {!active && !error && (
            <p className="text-slate-400 text-sm mb-3">Klicke auf „Stream starten“, um das Bild der Webcam anzuzeigen. HTTPS oder localhost erforderlich.</p>
          )}
          <div className="aspect-video bg-slate-900 rounded-lg overflow-hidden flex items-center justify-center min-h-[200px]">
            <video ref={videoRef} autoPlay playsInline muted className="max-w-full max-h-full object-contain" />
            {!active && !error && (
              <span className="text-slate-500 text-sm">Kein Bild – Stream starten</span>
            )}
          </div>
          <div className="flex gap-2 mt-3">
            {!active ? (
              <button type="button" onClick={startStream} className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-lg text-sm font-medium">
                Stream starten
              </button>
            ) : (
              <button type="button" onClick={stopStream} className="px-4 py-2 bg-slate-600 hover:bg-slate-500 text-white rounded-lg text-sm font-medium">
                Stream stoppen
              </button>
            )}
            <button type="button" onClick={onClose} className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm">
              Schließen
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

const PeripheryScan: React.FC<PeripheryScanProps> = ({ setCurrentPage }) => {
  const { pageSubtitleLabel } = usePlatform()
  const [scanning, setScanning] = useState(false)
  const [progress, setProgress] = useState(0)
  const [consoleLines, setConsoleLines] = useState<string[]>([])
  const [consoleVisible, setConsoleVisible] = useState(0)
  const [result, setResult] = useState<ScanResult | null>(() => loadStoredResult()?.result ?? null)
  const [showCameraModal, setShowCameraModal] = useState(false)
  /** Nur beim letzten Scan neu hinzugekommene Komponenten (bei zweitem Scan). */
  const [newSinceLastScan, setNewSinceLastScan] = useState<ScanResult | null>(null)

  const animateConsole = useCallback((lines: string[]) => {
    setConsoleVisible(0)
    let i = 0
    const t = setInterval(() => {
      i += 1
      setConsoleVisible((v) => Math.min(v + 1, lines.length))
      if (i >= lines.length) clearInterval(t)
    }, 120)
    return () => clearInterval(t)
  }, [])

  /** Aus Scan-Ergebnis passende Hersteller ermitteln (GPUs, PCI, USB-Beschreibungen). */
  const detectedManufacturers = useMemo(() => {
    if (!result) return []
    const text: string[] = []
    result.gpus.forEach((g: { description: string }) => text.push((g.description || '').toLowerCase()))
    ;(result.drivers || []).forEach((d: { device: string }) => text.push((d.device || '').toLowerCase()))
    ;(result.usb || []).forEach((u: { description: string }) => text.push((u.description || '').toLowerCase()))
    const combined = text.join(' ')
    return MANUFACTURER_DRIVER_LINKS.filter((m) => m.keywords.some((kw) => combined.includes(kw)))
  }, [result])

  const startAssimilation = async () => {
    setScanning(true)
    setProgress(0)
    setResult(null)
    setConsoleLines([])
    setConsoleVisible(0)
    const duration = 2200
    const step = 40
    const interval = setInterval(() => {
      setProgress((p) => Math.min(p + step, 100))
    }, duration / (100 / step))
    try {
      const response = await fetchApi('/api/peripherals/scan')
      let data: { status?: string; message?: string; detail?: string; gpus?: any[]; usb?: any[]; input_devices?: any[]; drivers?: any[] } = {}
      try {
        data = await response.json()
      } catch {
        toast.error('Ungültige Antwort vom Backend')
        clearInterval(interval)
        setProgress(100)
        setTimeout(() => setScanning(false), 400)
        return
      }
      clearInterval(interval)
      setProgress(100)
      if (response.status === 404) {
        const hint = 'Endpoint /api/peripherals/scan nicht gefunden. Backend im Projektordner neu starten (./start-backend.sh). Prüfen: GET /api/debug/routes listet registrierte Routen.'
        setConsoleLines([`> Fehler: ${data.detail || 'Not found'}. ${hint}`])
        setConsoleVisible(1)
        toast.error('Backend neu starten (siehe Hinweis)')
        setTimeout(() => setScanning(false), 400)
        return
      }
      if (data.status === 'success') {
        const gpus = data.gpus || []
        const usb = data.usb || []
        const input_devices = data.input_devices || []
        const drivers = data.drivers || []
        const newResult: ScanResult = { gpus, usb, input_devices, drivers }
        const previous = loadStoredResult()?.result ?? result
        const newOnly = diffNewComponents(previous, newResult)
        saveResult(newResult)
        setResult(newResult)
        setNewSinceLastScan(
          newOnly.gpus.length > 0 || newOnly.usb.length > 0 || newOnly.input_devices.length > 0 || newOnly.drivers.length > 0
            ? newOnly
            : null
        )
        const lines: string[] = ['> Assimilation gestartet...']
        gpus.forEach((g: any) => lines.push(`  [GPU] ${g.description}${g.driver ? ` (Treiber: ${g.driver})` : ''}`))
        usb.forEach((u: any) => lines.push(`  [USB] ${u.description}`))
        input_devices.forEach((d: any) => lines.push(`  [Eingabe] ${d.name}`))
        if (drivers.length > 0) lines.push(`  [Treiber] ${drivers.length} PCI-Geräte mit Treiber-Info`)
        lines.push('> Assimilation abgeschlossen.')
        setConsoleLines(lines)
        animateConsole(lines)
        toast.success('Assimilation abgeschlossen.')
      } else {
        const errMsg = (data.message && String(data.message).trim()) || (data.detail && String(data.detail).trim()) || 'Scan fehlgeschlagen (keine Fehlermeldung vom Server)'
        setConsoleLines([`> Fehler: ${errMsg}`])
        setConsoleVisible(1)
        toast.error(errMsg)
      }
    } catch (error) {
      clearInterval(interval)
      setProgress(100)
      setConsoleLines(['> Fehler: Backend nicht erreichbar.'])
      setConsoleVisible(1)
      toast.error('Scan fehlgeschlagen – Backend erreichbar?')
    } finally {
      setTimeout(() => setScanning(false), 400)
    }
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <div className="page-title-category mb-2 inline-flex">
          <h1 className="flex items-center gap-3">
            <Scan className="text-emerald-500" />
            Peripherie-Scan (Assimilation)
          </h1>
        </div>
        <p className="text-slate-400">Peripherie-Scan – {pageSubtitleLabel}</p>
      </div>

      {!scanning && !result && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card bg-gradient-to-br from-emerald-900/30 to-slate-800/60 border-emerald-600/40"
        >
          <p className="text-lg font-semibold text-white mb-2">Beginne mit der Assimilation des Systems!</p>
          <p className="text-slate-400 text-sm mb-6">Widerstand ist zwecklos.</p>
          <button
            onClick={startAssimilation}
            className="px-6 py-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-semibold transition-colors flex items-center gap-2"
          >
            <Scan size={20} />
            Assimilation starten
          </button>
        </motion.div>
      )}

      {!scanning && result && (
        <p className="text-slate-400 text-sm">
          Gespeicherte Daten vom letzten Scan. Erneut scannen zeigt unten „Neu bei diesem Scan“ nur für neu hinzugekommene Komponenten.
        </p>
      )}

      <AnimatePresence>
        {scanning && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="card bg-slate-800/80 border border-emerald-600/40"
          >
            <p className="text-lg font-semibold text-white mb-2">Beginne mit der Assimilation des Systems!</p>
            <p className="text-slate-400 text-sm mb-4">Widerstand ist zwecklos.</p>
            <div className="h-3 bg-slate-700 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-emerald-500 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>
            <p className="text-slate-500 text-xs mt-2">{progress} %</p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Konsole: animierte Ausgabe der gefundenen Komponenten */}
      {consoleLines.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="card bg-slate-900 border border-slate-600 font-mono text-sm overflow-hidden"
        >
          <div className="flex items-center gap-2 mb-2 pb-2 border-b border-slate-600">
            <span className="w-3 h-3 rounded-full bg-red-500/80" />
            <span className="w-3 h-3 rounded-full bg-amber-500/80" />
            <span className="w-3 h-3 rounded-full bg-green-500/80" />
            <span className="text-slate-400 ml-2">Assimilation – Konsole</span>
          </div>
          <div className="min-h-[120px] max-h-64 overflow-y-auto">
            {consoleLines.slice(0, consoleVisible).map((line, i) => {
              const isCmd = line.startsWith('>')
              const isGpu = line.startsWith('  [GPU]')
              const isUsb = line.startsWith('  [USB]')
              const isInput = line.startsWith('  [Eingabe]')
              const isDriver = line.startsWith('  [Treiber]')
              const cls = isCmd ? 'text-emerald-400' : isGpu ? 'text-sky-300' : isUsb ? 'text-amber-300' : isInput ? 'text-purple-300' : isDriver ? 'text-green-300' : 'text-slate-300'
              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.15 }}
                  className={`py-0.5 ${cls}`}
                >
                  {line}
                </motion.div>
              )
            })}
          </div>
        </motion.div>
      )}

      {result && !scanning && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          {/* Übersicht: Kamera, Tastatur, Maus – Erkannt Ja/Nein */}
          <div className="card bg-gradient-to-br from-emerald-900/20 to-slate-800/60 border-emerald-600/40">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Scan className="text-emerald-500" />
              Übersicht – Erkannte Peripherie
            </h3>
            <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-4">
              <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-600">
                <div className="flex items-center gap-2 mb-2">
                  <Camera className="text-sky-400" size={20} />
                  <span className="font-semibold text-white">Kamera(s)</span>
                </div>
                {(() => {
                  const cams = result.usb.filter((u: { type: string }) => u.type === 'webcam')
                  const n = cams.length
                  const h = COMPONENT_HINTS.camera
                  return (
                    <>
                      <p className={n > 0 ? 'text-green-400 text-sm font-medium' : 'text-slate-500 text-sm'}>
                        {n > 0 ? `Ja – ${n} erkannt` : 'Nein'}
                      </p>
                      {n > 0 && (
                        <ul className="mt-2 text-xs text-slate-400 space-y-0.5">
                          {cams.map((u: { description: string }, i: number) => (
                            <li key={i} className="truncate" title={u.description}>{u.description}</li>
                          ))}
                        </ul>
                      )}
                      <p className="text-xs text-slate-500 mt-2 border-t border-slate-600 pt-2">
                        <span className="text-slate-400">Hinweis:</span> {h.what} {h.where} Normal: {h.normal}
                      </p>
                    </>
                  )
                })()}
              </div>
              <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-600">
                <div className="flex items-center gap-2 mb-2">
                  <Keyboard className="text-amber-400" size={20} />
                  <span className="font-semibold text-white">Tastatur</span>
                </div>
                {(() => {
                  const keyboards = result.usb.filter((u: { type: string }) => u.type === 'keyboard')
                  const ok = keyboards.length > 0
                  const h = COMPONENT_HINTS.keyboard
                  return (
                    <>
                      <p className={ok ? 'text-green-400 text-sm font-medium' : 'text-slate-500 text-sm'}>
                        {ok ? `Ja – ${keyboards.length}` : 'Nein'}
                      </p>
                      {ok && (
                        <ul className="mt-2 text-xs text-slate-400 space-y-0.5">
                          {keyboards.map((u: { description: string }, i: number) => (
                            <li key={i} className="truncate" title={u.description}>{u.description}</li>
                          ))}
                        </ul>
                      )}
                      <p className="text-xs text-slate-500 mt-2 border-t border-slate-600 pt-2">
                        <span className="text-slate-400">Hinweis:</span> {h.what} {h.where} Normal: {h.normal}
                      </p>
                    </>
                  )
                })()}
              </div>
              <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-600">
                <div className="flex items-center gap-2 mb-2">
                  <Mouse className="text-purple-400" size={20} />
                  <span className="font-semibold text-white">Maus</span>
                </div>
                {(() => {
                  const hasUsb = result.usb.some((u: { type: string }) => u.type === 'mouse')
                  const hasInput = result.input_devices.some((d: { handlers: string }) => d.handlers?.includes('mouse'))
                  const ok = hasUsb || hasInput
                  const h = COMPONENT_HINTS.mouse
                  return (
                    <>
                      <p className={ok ? 'text-green-400 text-sm font-medium' : 'text-slate-500 text-sm'}>
                        {ok ? 'Ja' : 'Nein'}
                      </p>
                      {hasUsb && (
                        <p className="text-xs text-slate-300 mt-1">Welche: {result.usb.filter((u: { type: string }) => u.type === 'mouse').map((u: { description: string }) => u.description).join(', ')}</p>
                      )}
                      {hasUsb && result.usb.filter((u: { type: string }) => u.type === 'mouse').length > 0 && (
                        <ul className="mt-1 text-xs text-slate-400 space-y-0.5">
                          {result.usb.filter((u: { type: string }) => u.type === 'mouse').map((u: { description: string }, i: number) => (
                            <li key={i} className="truncate" title={u.description}>{u.description}</li>
                          ))}
                        </ul>
                      )}
                      <p className="text-xs text-slate-500 mt-2 border-t border-slate-600 pt-2">
                        <span className="text-slate-400">Hinweis:</span> {h.what} {h.where} Normal: {h.normal}
                      </p>
                    </>
                  )
                })()}
              </div>
              <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-600">
                <div className="flex items-center gap-2 mb-2">
                  <Keyboard className="text-slate-400" size={20} />
                  <span className="font-semibold text-white">Eingabegeräte</span>
                </div>
                {result.input_devices.length > 0 ? (
                  <>
                    <p className="text-green-400 text-sm font-medium">Ja – {result.input_devices.length}</p>
                    <ul className="mt-1 text-xs text-slate-400 space-y-0.5 max-h-16 overflow-y-auto">
                      {result.input_devices.slice(0, 5).map((d: { name: string }, i: number) => (
                        <li key={i} className="truncate" title={d.name}>{d.name}</li>
                      ))}
                      {result.input_devices.length > 5 && <li className="text-slate-500">… +{result.input_devices.length - 5}</li>}
                    </ul>
                  </>
                ) : (
                  <p className="text-slate-500 text-sm">Nein</p>
                )}
              </div>
              <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-600">
                <div className="flex items-center gap-2 mb-2">
                  <Cpu className="text-sky-300" size={20} />
                  <span className="font-semibold text-white">Grafik / Treiber</span>
                </div>
                {result.gpus.length > 0 ? (
                  <>
                    <p className="text-green-400 text-sm font-medium">Ja – {result.gpus.length} Grafikkarte(n)</p>
                    <ul className="mt-2 space-y-1 text-xs">
                      {result.gpus.map((g: { description: string; driver?: string; driver_hint?: string }, i: number) => (
                        <li key={i} className="text-slate-300">
                          <span className="font-medium text-white">{g.description}</span>
                          {g.driver ? (
                            <span className="text-green-400 ml-1"> – Treiber: {g.driver} (Kernel/Hersteller)</span>
                          ) : (
                            <span className="text-amber-400 ml-1"> – Hersteller-Treiber prüfen (lspci -k, Hersteller-Linux-Treiber)</span>
                          )}
                        </li>
                      ))}
                    </ul>
                  </>
                ) : (
                  <p className="text-slate-500 text-sm">Keine</p>
                )}
                <p className="text-xs text-slate-500 mt-2 border-t border-slate-600 pt-2">
                  <span className="text-slate-400">Hinweis:</span> {COMPONENT_HINTS.gpu.what} {COMPONENT_HINTS.gpu.where} Normal: {COMPONENT_HINTS.gpu.normal}
                </p>
              </div>
              {/* Touchpad & Headset in gleicher Zeile */}
              <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-600 sm:col-span-2">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <Mouse className="text-slate-400" size={18} />
                      <span className="font-semibold text-white text-sm">Touchpad</span>
                    </div>
                    {(() => {
                      const touchpads = result.input_devices.filter((d: { name: string }) => (d.name || '').toLowerCase().includes('touchpad'))
                      const ok = touchpads.length > 0
                      const h = COMPONENT_HINTS.touchpad
                      return (
                        <>
                          <p className={ok ? 'text-green-400 text-xs font-medium' : 'text-slate-500 text-xs'}>{ok ? `Ja – ${touchpads.length}` : 'Nein'}</p>
                          {ok && <p className="text-xs text-slate-400 mt-0.5">{touchpads.map((t: { name: string }) => t.name).join(', ')}</p>}
                          <p className="text-xs text-slate-500 mt-1"><span className="text-slate-400">Hinweis:</span> {h.what} {h.normal}</p>
                        </>
                      )
                    })()}
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <Headphones className="text-slate-400" size={18} />
                      <span className="font-semibold text-white text-sm">Headset / Audio</span>
                    </div>
                    {(() => {
                      const headsets = result.usb.filter((u: { type: string }) => u.type === 'headset')
                      const ok = headsets.length > 0
                      const h = COMPONENT_HINTS.headset
                      return (
                        <>
                          <p className={ok ? 'text-green-400 text-xs font-medium' : 'text-slate-500 text-xs'}>{ok ? `Ja – ${headsets.length}` : 'Nein'}</p>
                          {ok && <p className="text-xs text-slate-400 mt-0.5">Welche: {headsets.map((u: { description: string }) => u.description).join(', ')}</p>}
                          <p className="text-xs text-slate-500 mt-1"><span className="text-slate-400">Hinweis:</span> Ausgabequelle unter Musikbox/Einstellungen (PulseAudio/PipeWire). {h.normal}</p>
                        </>
                      )
                    })()}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Corsair & Webcams – Linux-Treiber-Infos (Hinweisfarbe) */}
          <div className="card bg-slate-800/50 border border-slate-600">
            <h3 className="text-sm font-bold text-white mb-2">Corsair & Webcams unter Linux</h3>
            <ul className="text-sm text-slate-300 space-y-1.5 list-disc list-inside">
              <li><strong className="text-white">Corsair (Maus, Tastatur, Headset):</strong> Keine offiziellen Linux-Treiber. Community: <a href="https://github.com/ckb-next/ckb-next" target="_blank" rel="noopener noreferrer" className="text-sky-400 hover:underline">ckb-next</a> für Gaming-Tastatur und -Maus (RGB, Makros); ab Kernel 6.13+ Treiber für Corsair Void Headset im Kernel.</li>
              <li><strong className="text-white">Webcams:</strong> Unter Linux reicht der UVC-Standard (Kernel-Modul <code className="bg-slate-700 px-1 rounded text-slate-200">uvcvideo</code>) – in der Regel <strong>kein Hersteller-Treiber nötig</strong>. Im Bereich Kameras kannst du den Kamerastream anzeigen.</li>
            </ul>
          </div>

          {/* Temperatur-Hinweis (Normalbereich) */}
          <div className="card bg-slate-800/50 border border-slate-600">
            <h3 className="text-sm font-bold text-white mb-2 flex items-center gap-2">
              <Cpu className="text-amber-400" size={18} />
              Temperatursensoren – Normalbereich
            </h3>
            <p className="text-xs text-slate-200">
              {COMPONENT_HINTS.temperature.what} {COMPONENT_HINTS.temperature.where} <strong className="text-white">Normal:</strong> {COMPONENT_HINTS.temperature.normal}
            </p>
          </div>

          {/* Nur neue Komponenten bei diesem Scan */}
          {newSinceLastScan && (
            newSinceLastScan.gpus.length > 0 || newSinceLastScan.usb.length > 0 || newSinceLastScan.input_devices.length > 0 || newSinceLastScan.drivers.length > 0 ? (
              <div className="card-info">
                <h3 className="text-lg font-bold mb-3 flex items-center gap-2">
                  <Scan size={20} />
                  Neu bei diesem Scan
                </h3>
                <p className="text-sm mb-3 opacity-90">Nur Komponenten, die im Vergleich zum letzten Scan neu erkannt wurden.</p>
                <div className="grid sm:grid-cols-2 gap-4">
                  {newSinceLastScan.gpus.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold mb-1">Grafikkarten</h4>
                      <ul className="space-y-1 text-sm opacity-90">
                        {newSinceLastScan.gpus.map((g, i) => (
                          <li key={i}>{g.description}{g.driver ? ` (${g.driver})` : ''}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {newSinceLastScan.usb.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold mb-1">USB-Geräte</h4>
                      <ul className="space-y-1 text-sm opacity-90">
                        {newSinceLastScan.usb.map((u, i) => (
                          <li key={i}>{u.description}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {newSinceLastScan.input_devices.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold mb-1">Eingabegeräte</h4>
                      <ul className="space-y-1 text-sm opacity-90">
                        {newSinceLastScan.input_devices.map((d, i) => (
                          <li key={i}>{d.name}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {newSinceLastScan.drivers.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold mb-1">Treiber (PCI)</h4>
                      <ul className="space-y-1 text-sm opacity-90">
                        {newSinceLastScan.drivers.map((d, i) => (
                          <li key={i}>{d.device} → {d.driver}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            ) : null
          )}

          {/* Hersteller – prüfen ob Treiber für erkannte Komponenten existieren */}
          <div className="card bg-gradient-to-br from-sky-900/20 to-slate-800/60 border-sky-600/40">
            <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
              <ExternalLink className="text-sky-400" size={20} />
              Hersteller & Treiber für Linux
            </h3>
            <p className="text-sm text-slate-100 mb-3">
              <strong className="text-white">Die Hersteller prüfen, ob es Treiber für die erkannten Komponenten gibt.</strong> Herstellerlisten und Anbieter von Treibern im Internet suchen und identifizieren – nachfolgend passende Hersteller (z. B. Corsair, ASUS, Logitech, NVIDIA, AMD) mit Links zu Treiber-/Support-Seiten.
            </p>
            <p className="text-xs text-slate-400 mb-4">
              Kameras nur bei Kameras, Maus nur bei Maus (ggf. Touchpad); Eingabegeräte einzeln mit Namen – bei Bedarf gezielt nach Hersteller (Corsair, ASUS, Angetube, …) nach Treibern suchen.
            </p>
            <div className="flex flex-wrap gap-3">
              {(detectedManufacturers.length > 0 ? detectedManufacturers : MANUFACTURER_DRIVER_LINKS.slice(0, 6)).map((m) => (
                <a
                  key={m.name}
                  href={m.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2 bg-slate-700/50 hover:bg-sky-600/30 border border-slate-600 hover:border-sky-500/50 rounded-lg text-sky-300 hover:text-white transition-colors text-sm font-medium"
                >
                  <ExternalLink size={14} />
                  {m.name} – Treiber/Support
                </a>
              ))}
            </div>
            {detectedManufacturers.length > 0 && (
              <p className="text-xs text-slate-500 mt-3">
                {detectedManufacturers.length} Hersteller passen zu deiner erkannten Hardware (GPUs/PCI-Geräte).
              </p>
            )}
          </div>

          {result.gpus.length > 0 && (
            <div className="card">
              <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
                <Cpu className="text-sky-500" />
                Grafikkarten
              </h3>
              <p className="text-xs text-slate-500 mb-3 border-b border-slate-600 pb-2">
                <span className="text-slate-400">Hinweis:</span> {COMPONENT_HINTS.gpu.what} {COMPONENT_HINTS.gpu.where} Normal: {COMPONENT_HINTS.gpu.normal}
              </p>
              <ul className="space-y-2">
                {result.gpus.map((g, i) => (
                  <li key={i} className="p-3 bg-slate-700/30 rounded-lg border border-slate-600">
                    <span className="text-white">{g.description}</span>
                    {g.driver && g.driver !== '—' && (
                      <p className="text-xs text-green-400 mt-1">Treiber: {g.driver}</p>
                    )}
                    {(!g.driver || g.driver === '—') && g.driver_hint && (
                      <p className="text-xs text-slate-500 mt-1">{g.driver_hint}</p>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {result.usb.filter((u: { type: string }) => u.type === 'webcam').length > 0 && (
            <div className="card">
              <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
                <Camera className="text-sky-500" />
                Kamera(s)
              </h3>
              <p className="text-sm text-slate-300 mb-3 border-b border-slate-600 pb-2 bg-slate-800/40 rounded-lg px-3 py-2">
                <span className="text-amber-300 font-medium">Hinweis:</span> Webcams nutzen unter Linux den UVC-Standard – in der Regel ist <strong className="text-white">kein Hersteller-Treiber nötig</strong> (Kernel-Modul <code className="bg-slate-700 px-1 rounded text-slate-200">uvcvideo</code>). Videostream unten starten.
              </p>
              <div className="mb-3">
                <button
                  type="button"
                  onClick={() => setShowCameraModal(true)}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-lg text-sm font-medium"
                >
                  <Video size={18} />
                  Kamerastream anzeigen
                </button>
              </div>
              <ul className="space-y-2">
                {result.usb.filter((u: { type: string }) => u.type === 'webcam').map((u: { description: string }, i: number) => (
                  <li key={i} className="p-3 bg-slate-700/30 rounded-lg border border-slate-600 flex items-center gap-2">
                    <Camera size={18} className="text-slate-400" />
                    <span className="text-white">{u.description}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {/* Kamerastream: Button wenn keine Webcam im Scan, Modal immer wenn Seite mit Ergebnis */}
          {result && result.usb.filter((u: { type: string }) => u.type === 'webcam').length === 0 && (
            <div className="card">
              <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
                <Camera className="text-sky-500" />
                Kamera / Webcam
              </h3>
              <p className="text-sm text-slate-300 mb-3">Keine Webcam im Scan erkannt. Unter Linux reicht meist der UVC-Treiber (uvcvideo) – kein Hersteller-Treiber nötig.</p>
              <button
                type="button"
                onClick={() => setShowCameraModal(true)}
                className="inline-flex items-center gap-2 px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-lg text-sm font-medium"
              >
                <Video size={18} />
                Kamerastream anzeigen
              </button>
            </div>
          )}
          <CameraStreamModal open={showCameraModal} onClose={() => setShowCameraModal(false)} />
          {(result.usb.some((u: { type: string }) => u.type === 'mouse') || result.input_devices.some((d: { name: string }) => (d.name || '').toLowerCase().includes('touchpad'))) && (
            <div className="card">
              <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
                <Mouse className="text-purple-500" />
                Maus / Touchpad
              </h3>
              <p className="text-sm text-slate-300 mb-3 border-b border-slate-600 pb-2 bg-slate-800/40 rounded-lg px-3 py-2">
                <span className="text-amber-300 font-medium">Hinweis:</span> Nur Maus und Touchpad. Bei Corsair, ASUS, Logitech usw. nach Treibern suchen (z. B. ckb-next für Corsair).
              </p>
              <ul className="space-y-2">
                {result.usb.filter((u: { type: string }) => u.type === 'mouse').map((u: { description: string }, i: number) => (
                  <li key={i} className="p-3 bg-slate-700/30 rounded-lg border border-slate-600 flex items-center gap-2">
                    <Mouse size={18} className="text-slate-400" />
                    <span className="text-white">{u.description}</span>
                  </li>
                ))}
                {result.input_devices.filter((d: { name: string }) => (d.name || '').toLowerCase().includes('touchpad')).map((d: { name: string; handlers?: string }, i: number) => (
                  <li key={`tp-${i}`} className="p-3 bg-slate-700/30 rounded-lg border border-slate-600 flex items-center gap-2 text-sm">
                    <Mouse size={18} className="text-slate-400" />
                    <span className="text-white">{d.name}</span>
                    {d.handlers && <span className="text-slate-500 text-xs">{d.handlers}</span>}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {result.input_devices.length > 0 && (
            <div className="card">
              <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
                <Keyboard className="text-slate-400" />
                Eingabegeräte (einzeln mit Namen)
              </h3>
              <p className="text-xs text-slate-500 mb-3 border-b border-slate-600 pb-2">
                <span className="text-slate-400">Hinweis:</span> Jedes Gerät einzeln mit Namen. Bei Corsair, ASUS, Angetube, Logitech usw. nach Treibern suchen.
              </p>
              <ul className="space-y-2">
                {result.input_devices.map((d, i) => (
                  <li key={i} className="p-3 bg-slate-700/30 rounded-lg border border-slate-600 text-sm flex justify-between items-center">
                    <span className="text-white font-medium">{d.name}</span>
                    <span className="text-slate-500 text-xs">{d.handlers}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {result.usb.filter((u: { type: string }) => u.type !== 'webcam' && u.type !== 'mouse').length > 0 && (
            <div className="card">
              <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
                <Usb className="text-amber-500" />
                Weitere USB-Geräte (Tastatur, Headset, …)
              </h3>
              <ul className="space-y-2">
                {result.usb.filter((u: { type: string }) => u.type !== 'webcam' && u.type !== 'mouse').map((u: { type: string; description: string }, i: number) => (
                  <li key={i} className="p-3 bg-slate-700/30 rounded-lg border border-slate-600 flex items-center gap-2">
                    {u.type === 'keyboard' && <Keyboard size={18} className="text-slate-400" />}
                    {u.type === 'headset' && <Headphones size={18} className="text-slate-400" />}
                    <span className="text-white">{u.description}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {result.drivers && result.drivers.length > 0 && (
            <div className="card">
              <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
                <Cpu className="text-purple-500" />
                Sonstige Treiber (PCI / Kernel-Module)
              </h3>
              <p className="text-xs text-slate-500 mb-3 border-b border-slate-600 pb-2">
                <span className="text-slate-400">Hinweis:</span> {COMPONENT_HINTS.drivers.what} {COMPONENT_HINTS.drivers.where} Normal: {COMPONENT_HINTS.drivers.normal}
              </p>
              <ul className="space-y-2 max-h-64 overflow-y-auto">
                {result.drivers.map((d, i) => (
                  <li key={i} className="p-3 bg-slate-700/30 rounded-lg border border-slate-600 flex justify-between items-center">
                    <span className="text-slate-300 text-sm truncate mr-2">{d.device}</span>
                    <span className={`text-sm font-medium shrink-0 ${d.driver === '—' ? 'text-slate-500' : 'text-green-400'}`}>{d.driver}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {(result.gpus.length === 0 && result.usb.length === 0 && result.input_devices.length === 0) && (
            <p className="text-slate-500">Keine Peripherie erkannt (lspci/lsusb nicht verfügbar oder leer).</p>
          )}
          <button
            onClick={startAssimilation}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm"
          >
            Erneut scannen
          </button>
        </motion.div>
      )}
    </div>
  )
}

export default PeripheryScan
