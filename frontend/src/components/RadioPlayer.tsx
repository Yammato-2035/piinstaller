import React, { useState, useEffect, useRef } from 'react'
import { Play, Pause, Volume2, Monitor, ChevronLeft, ChevronRight, X } from 'lucide-react'
import { fetchApi, getApiBase } from '../api'
import html2canvas from 'html2canvas'
import toast from 'react-hot-toast'

const FAVORITES_PER_PAGE = 9
const COLS = 3
const TOTAL_FAVORITE_SLOTS = 36

/** 10 LEDs: unten grün (6), dann gelb (2), oben rot (2). Leuchten von unten nach oben. */
function LedStrip({ value }: { value: number }) {
  const lit = Math.min(10, Math.round((value / 100) * 10.99))
  const off = '#1e293b'
  const green = '#22c55e'
  const yellow = '#eab308'
  const red = '#dc2626'
  // Mit flex-col-reverse: erstes DOM-Element = unten. Reihenfolge: grün (unten), gelb, rot (oben).
  const segments = [
    { i: 0, color: green }, { i: 1, color: green }, { i: 2, color: green }, { i: 3, color: green }, { i: 4, color: green }, { i: 5, color: green },
    { i: 6, color: yellow }, { i: 7, color: yellow },
    { i: 8, color: red }, { i: 9, color: red },
  ]
  return (
    <div className="flex flex-col-reverse gap-0.5 w-4 h-20">
      {segments.map(({ i, color }) => {
        const on = i < lit
        return (
          <div key={i} className="w-full h-1.5 rounded-sm transition-colors" style={{ backgroundColor: on ? color : off }} />
        )
      })}
    </div>
  )
}

/** VU (L/R): Skala 0 links bis 180° rechts, nur die Skala (Bogen), unterhalb keine Anzeige. */
function AnalogGaugeVu({ value, size = 56 }: { value: number; size?: number }) {
  const r = size / 2 - 2
  const cx = size / 2
  const cy = size / 2
  const needleLen = r - 6
  const toRad = (deg: number) => (deg * Math.PI) / 180
  // 0 % = links (180°), 100 % = rechts (0°) – Skala verläuft über 180°
  const angleFor = (pct: number) => 180 - (pct / 100) * 180
  const arcOnly = () => {
    const left = cx - r
    const right = cx + r
    return `M ${left} ${cy} A ${r} ${r} 0 1 1 ${right} ${cy}`
  }
  const arcSegment = (startPct: number, endPct: number) => {
    const a0 = toRad(angleFor(startPct))
    const a1 = toRad(angleFor(endPct))
    return `M ${cx + r * Math.cos(a0)} ${cy + r * Math.sin(a0)} A ${r} ${r} 0 0 0 ${cx + r * Math.cos(a1)} ${cy + r * Math.sin(a1)}`
  }
  const displayValue = value >= 95 ? value : Math.min(value, 79)
  const angle = angleFor(displayValue)
  const x2 = cx + needleLen * Math.cos(toRad(angle))
  const y2 = cy + needleLen * Math.sin(toRad(angle))

  return (
    <svg width={size} height={size} className="overflow-visible" style={{ background: '#1e293b' }}>
      <path d={arcOnly()} fill="none" stroke="#94a3b8" strokeWidth={1.5} />
      <path d={arcSegment(80, 100)} fill="none" stroke="#dc2626" strokeWidth={2} strokeLinecap="round" />
      {[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100].map((pct) => {
        const a = toRad(angleFor(pct))
        const inner = r - 4
        const outer = r
        return (
          <line
            key={pct}
            x1={cx + inner * Math.cos(a)}
            y1={cy + inner * Math.sin(a)}
            x2={cx + outer * Math.cos(a)}
            y2={cy + outer * Math.sin(a)}
            stroke={pct >= 80 ? '#dc2626' : '#64748b'}
            strokeWidth={pct % 20 === 0 ? 1.5 : 1}
          />
        )
      })}
      <line x1={cx} y1={cy} x2={x2} y2={y2} stroke="#dc2626" strokeWidth={2} strokeLinecap="round" />
      <circle cx={x2} cy={y2} r={2} fill="#fff" stroke="#dc2626" strokeWidth={0.5} />
      <text x={cx} y={size - 4} textAnchor="middle" fill="#64748b" fontSize={8} fontWeight="bold">VU</text>
    </svg>
  )
}

/** Signal: Skala 0 links bis 180° rechts; rot 0–20 %, weiss 20–75 %, grün 75–100 %; nur Bogen, nichts unterhalb. */
function AnalogGaugeSignal({ value, size = 56 }: { value: number; size?: number }) {
  const r = size / 2 - 2
  const cx = size / 2
  const cy = size / 2
  const needleLen = r - 6
  const toRad = (deg: number) => (deg * Math.PI) / 180
  const angleFor = (pct: number) => 180 - (pct / 100) * 180
  const arcOnly = () => `M ${cx - r} ${cy} A ${r} ${r} 0 1 1 ${cx + r} ${cy}`
  const arcSegment = (startPct: number, endPct: number) => {
    const a0 = toRad(angleFor(startPct))
    const a1 = toRad(angleFor(endPct))
    return `M ${cx + r * Math.cos(a0)} ${cy + r * Math.sin(a0)} A ${r} ${r} 0 0 0 ${cx + r * Math.cos(a1)} ${cy + r * Math.sin(a1)}`
  }
  const angle = angleFor(value)
  const x2 = cx + needleLen * Math.cos(toRad(angle))
  const y2 = cy + needleLen * Math.sin(toRad(angle))

  return (
    <svg width={size} height={size} className="overflow-visible" style={{ background: '#1e293b' }}>
      <path d={arcOnly()} fill="none" stroke="#94a3b8" strokeWidth={1.5} />
      <path d={arcSegment(0, 20)} fill="none" stroke="#dc2626" strokeWidth={2} strokeLinecap="round" />
      <path d={arcSegment(20, 75)} fill="none" stroke="#94a3b8" strokeWidth={1} />
      <path d={arcSegment(75, 100)} fill="none" stroke="#22c55e" strokeWidth={2} strokeLinecap="round" />
      {[0, 10, 20, 30, 40, 50, 60, 70, 75, 80, 90, 100].map((pct) => {
        const a = toRad(angleFor(pct))
        const inner = r - 4
        const outer = r
        const red = pct <= 20
        const green = pct >= 75
        return (
          <line
            key={pct}
            x1={cx + inner * Math.cos(a)}
            y1={cy + inner * Math.sin(a)}
            x2={cx + outer * Math.cos(a)}
            y2={cy + outer * Math.sin(a)}
            stroke={red ? '#dc2626' : green ? '#22c55e' : '#64748b'}
            strokeWidth={pct % 20 === 0 || pct === 75 ? 1.5 : 1}
          />
        )
      })}
      <line x1={cx} y1={cy} x2={x2} y2={y2} stroke="#0f172a" strokeWidth={2} strokeLinecap="round" />
      <circle cx={x2} cy={y2} r={2} fill="#fff" stroke="#0f172a" strokeWidth={0.5} />
      <text x={cx} y={size - 4} textAnchor="middle" fill="#64748b" fontSize={7} fontWeight="bold">Sig</text>
    </svg>
  )
}

/** Zweizeilige Beschriftung: max 2 Zeilen, Platz gut nutzen, sinnvolle Worttrennung. */
function twoLineLabel(name: string, maxCharsPerLine = 12): [string, string] {
  const n = name.trim()
  if (!n) return ['', '']
  if (n.length <= maxCharsPerLine) return [n, '']
  const parts = n.split(/\s+/)
  if (parts.length <= 1) {
    const mid = Math.ceil(n.length / 2)
    return [n.slice(0, mid), n.slice(mid)]
  }
  let line1 = ''
  let line2 = ''
  for (const p of parts) {
    const next = line1 ? line1 + ' ' + p : p
    if (next.length <= maxCharsPerLine) {
      line1 = next
    } else {
      line2 = line2 ? line2 + ' ' + p : p
    }
  }
  if (!line1) line1 = parts[0]
  if (!line2) line2 = parts.slice(1).join(' ')
  return [line1, line2]
}

export interface RadioStation {
  id: string
  name: string
  streamUrl: string
  logoUrl?: string
  region?: string
  genre?: string
}

/** Geprüfte Wikipedia-Commons-Logos (512px), damit alle Sender korrekt angezeigt werden. */
const WIKI = {
  einslive: 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/fb/WDR_1LIVE_Logo_2016.svg/512px-WDR_1LIVE_Logo_2016.svg.png',
  wdr2: 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/7b/WDR_2_Logo.svg/512px-WDR_2_Logo.svg.png',
  wdr4: 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/60/WDR_4_logo_2012.svg/512px-WDR_4_logo_2012.svg.png',
  wdr5: 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/WDR_5_Logo.svg/512px-WDR_5_Logo.svg.png',
  ndr: 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/33/NDR_Logo.svg/512px-NDR_Logo.svg.png',
  bayern3: 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/Bayern3_Logo.svg/512px-Bayern3_Logo.svg.png',
  bayern1: 'https://api.ardmediathek.de/image-service/images/urn:ard:image:b366004f6196d70c?w=512',
  dlf: 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Deutschlandfunk_logo.svg/512px-Deutschlandfunk_logo.svg.png',
  mdrjump: 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/MDR_Jump_Logo.svg/512px-MDR_Jump_Logo.svg.png',
  hr3: 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/HR3_Logo.svg/512px-HR3_Logo.svg.png',
  swr3: 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/SWR3_Logo.svg/512px-SWR3_Logo.svg.png',
  radiosaw: 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Radio_SAW_Logo_2018.svg/512px-Radio_SAW_Logo_2018.svg.png',
  antennebayern: 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Antenne_Bayern_Logo.svg/512px-Antenne_Bayern_Logo.svg.png',
  '104.6rtl': 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/3d/104.6_RTL_Logo.svg/512px-104.6_RTL_Logo.svg.png',
  radioeins: 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2d/Radio_Eins_Logo.svg/512px-Radio_Eins_Logo.svg.png',
  wdrcosmo: 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/8b/WDR_Cosmo_Logo.svg/512px-WDR_Cosmo_Logo.svg.png',
  br2: 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2a/Bayern_2_Logo.svg/512px-Bayern_2_Logo.svg.png',
  swr1bw: 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/7d/SWR1_Logo.svg/512px-SWR1_Logo.svg.png',
  swr4: 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/SWR4_Logo.svg/512px-SWR4_Logo.svg.png',
  hr1: 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/HR1_Logo.svg/512px-HR1_Logo.svg.png',
}
/** Senderliste inkl. SAW Musikwelt + weitere Sender; Logos über Backend-Proxy (Wikipedia 512px). */
export const RADIO_STATIONS: RadioStation[] = [
  { id: 'einslive', name: '1Live', streamUrl: 'https://wdr-1live-live.icecastssl.wdr.de/wdr/1live/live/mp3/128/stream.mp3', logoUrl: WIKI.einslive, region: 'NRW', genre: 'Pop' },
  { id: 'wdr2', name: 'WDR 2', streamUrl: 'https://wdr-wdr2-rheinruhr.icecastssl.wdr.de/wdr/wdr2/rheinruhr/mp3/128/stream.mp3', logoUrl: WIKI.wdr2, region: 'NRW', genre: 'Pop' },
  { id: 'wdr4', name: 'WDR 4', streamUrl: 'https://wdr-wdr4-live.icecastssl.wdr.de/wdr/wdr4/live/mp3/128/stream.mp3', logoUrl: WIKI.wdr4, region: 'NRW', genre: 'Schlager' },
  { id: 'wdr5', name: 'WDR 5', streamUrl: 'https://wdr-wdr5-live.icecastssl.wdr.de/wdr/wdr5/live/mp3/128/stream.mp3', logoUrl: WIKI.wdr5, region: 'NRW', genre: 'Kultur' },
  { id: 'ndr2', name: 'NDR 2', streamUrl: 'https://icecast.ndr.de/ndr/ndr2/hamburg/mp3/128/stream.mp3', logoUrl: WIKI.ndr, region: 'Nord', genre: 'Pop' },
  { id: 'ndr1', name: 'NDR 1 Nds', streamUrl: 'https://icecast.ndr.de/ndr/ndr1niedersachsen/hannover/mp3/128/stream.mp3', logoUrl: WIKI.ndr, region: 'Nord', genre: 'Schlager' },
  { id: 'bayern3', name: 'Bayern 3', streamUrl: 'https://dispatcher.rndfnk.com/br/br3/live/mp3/mid', logoUrl: WIKI.bayern3, region: 'Bayern', genre: 'Pop' },
  { id: 'bayern1', name: 'Bayern 1', streamUrl: 'https://dispatcher.rndfnk.com/br/br1/obb/mp3/mid', logoUrl: WIKI.bayern1, region: 'Bayern', genre: 'Schlager' },
  { id: 'dlf', name: 'Deutschlandfunk', streamUrl: 'https://st01.sslstream.dlf.de/dlf/01/128/mp3/stream.mp3', logoUrl: WIKI.dlf, region: 'Bundesweit', genre: 'Info' },
  { id: 'dlfkultur', name: 'DLF Kultur', streamUrl: 'https://st02.sslstream.dlf.de/dlf/02/128/mp3/stream.mp3', logoUrl: WIKI.dlf, region: 'Bundesweit', genre: 'Kultur' },
  { id: 'mdrjump', name: 'MDR Jump', streamUrl: 'http://mdr-284320-0.cast.mdr.de/mdr/284320/0/mp3/high/stream.mp3', logoUrl: WIKI.mdrjump, region: 'Mitte', genre: 'Pop' },
  { id: 'mdraktuell', name: 'MDR Aktuell', streamUrl: 'http://mdr-284350-0.cast.mdr.de/mdr/284350/0/mp3/high/stream.mp3', logoUrl: 'https://www.mdr.de/apple-touch-icon.png', region: 'Mitte', genre: 'Nachrichten' },
  { id: 'hr3', name: 'HR3', streamUrl: 'http://hr-hr3-live.cast.addradio.de/hr/hr3/live/mp3/128/stream.mp3', logoUrl: WIKI.hr3, region: 'Hessen', genre: 'Pop' },
  { id: 'swr3', name: 'SWR3', streamUrl: 'https://liveradio.swr.de/sw282p3/swr3/play.mp3', logoUrl: WIKI.swr3, region: 'Südwest', genre: 'Pop' },
  { id: 'radiosaw', name: 'Radio SAW', streamUrl: 'https://stream.radiosaw.de/saw/mp3-128/', logoUrl: WIKI.radiosaw, region: 'Sachsen-Anhalt', genre: 'Schlager' },
  { id: 'saw70er', name: 'SAW 70er', streamUrl: 'https://stream.radiosaw.de/saw-70er/mp3-192/', logoUrl: WIKI.radiosaw, region: 'Sachsen-Anhalt', genre: '70er' },
  { id: 'saw80er', name: 'SAW 80er', streamUrl: 'https://stream.radiosaw.de/saw-80er/mp3-192/', logoUrl: WIKI.radiosaw, region: 'Sachsen-Anhalt', genre: '80er' },
  { id: 'saw90er', name: 'SAW 90er', streamUrl: 'https://stream.radiosaw.de/saw-90er/mp3-192/', logoUrl: WIKI.radiosaw, region: 'Sachsen-Anhalt', genre: '90er' },
  { id: 'saw2000er', name: 'SAW 2000er', streamUrl: 'https://stream.radiosaw.de/saw-2000er/mp3-192/', logoUrl: WIKI.radiosaw, region: 'Sachsen-Anhalt', genre: '2000er' },
  { id: 'rockland', name: 'Rockland', streamUrl: 'https://stream.radiosaw.de/rockland/mp3-192/', logoUrl: WIKI.radiosaw, region: 'Sachsen-Anhalt', genre: 'Rock' },
  { id: 'sawparty', name: 'SAW Party', streamUrl: 'https://stream.radiosaw.de/saw-party/mp3-192/', logoUrl: WIKI.radiosaw, region: 'Sachsen-Anhalt', genre: 'Party' },
  { id: 'sawschlagerparty', name: 'SAW Schlagerparty', streamUrl: 'https://stream.radiosaw.de/saw-schlagerparty/mp3-192/', logoUrl: WIKI.radiosaw, region: 'Sachsen-Anhalt', genre: 'Schlager' },
  { id: 'antennebayern', name: 'Antenne Bayern', streamUrl: 'https://antennebayern.cast.addradio.de/antennebayern/live/mp3/128/stream.mp3', logoUrl: WIKI.antennebayern, region: 'Bayern', genre: 'Pop' },
  { id: '104.6rtl', name: '104.6 RTL', streamUrl: 'https://stream.104.6rtl.com/rtl', logoUrl: WIKI['104.6rtl'], region: 'Berlin', genre: 'Top 40' },
  { id: 'radioeins', name: 'radioeins', streamUrl: 'http://rbb-radioeins-live.cast.addradio.de/rbb/radioeins/live/mp3/128/stream.mp3', logoUrl: WIKI.radioeins, region: 'Berlin/Brandenburg', genre: 'Rock' },
  { id: 'bremenzwei', name: 'Bremen Zwei', streamUrl: 'https://icecast.radiobremen.de/rb/bremenzwei/live/mp3/128/stream.mp3', logoUrl: 'https://www.bremenzwei.de/static/img/favicons/apple-touch-icon-180.png', region: 'Bremen', genre: 'Kultur' },
  { id: 'rockantenne', name: 'Rock Antenne', streamUrl: 'https://stream.rockantenne.de/rockantenne/stream/mp3', logoUrl: 'https://www.rockantenne.de/logos/station-rock-antenne/apple-touch-icon.png', region: 'Bayern', genre: 'Rock' },
  { id: 'radiobob', name: 'Radio Bob', streamUrl: 'https://streams.radiobob.de/bob-national/mp3-192/', logoUrl: 'https://www.radiobob.de/favicon.ico', region: 'Bundesweit', genre: 'Rock' },
  { id: 'wdrcosmo', name: 'WDR Cosmo', streamUrl: 'https://wdr-wdrcosmo-live.icecastssl.wdr.de/wdr/wdrcosmo/live/mp3/128/stream.mp3', logoUrl: WIKI.wdrcosmo, region: 'NRW', genre: 'World' },
  { id: 'ndrkultur', name: 'NDR Kultur', streamUrl: 'https://icecast.ndr.de/ndr/ndrkultur/live/mp3/128/stream.mp3', logoUrl: WIKI.ndr, region: 'Nord', genre: 'Kultur' },
  { id: 'br2', name: 'BR-Klassik', streamUrl: 'https://dispatcher.rndfnk.com/br/br2/live/mp3/mid', logoUrl: WIKI.br2, region: 'Bayern', genre: 'Klassik' },
  { id: 'swr1bw', name: 'SWR1 BW', streamUrl: 'https://liveradio.swr.de/sw282p3/swr1bw/play.mp3', logoUrl: WIKI.swr1bw, region: 'Südwest', genre: 'Schlager' },
  { id: 'swr4', name: 'SWR4', streamUrl: 'https://liveradio.swr.de/sw282p3/swr4bw/play.mp3', logoUrl: WIKI.swr4, region: 'Südwest', genre: 'Schlager' },
  { id: 'hr1', name: 'HR1', streamUrl: 'http://hr-hr1-live.cast.addradio.de/hr/hr1/live/mp3/128/stream.mp3', logoUrl: WIKI.hr1, region: 'Hessen', genre: 'Schlager' },
  { id: 'rbb888', name: 'rbb 88.8', streamUrl: 'http://rbb-888-live.cast.addradio.de/rbb/888/live/mp3/128/stream.mp3', logoUrl: 'https://www.rbb88-8.de/apple-touch-icon.png', region: 'Berlin', genre: 'Info' },
  { id: 'energy', name: 'Energy', streamUrl: 'https://stream.energy.de/energy.mp3', logoUrl: 'https://www.energy.de/favicon.ico', region: 'Bundesweit', genre: 'Charts' },
]

interface StreamMetadata {
  title?: string
  artist?: string
  song?: string
  bitrate?: number
  server_name?: string
  show?: string
}

interface RadioPlayerProps {
  compact?: boolean
  dsi?: boolean
  /** Zeige Button "Auf DSI anzeigen" (nur wenn nicht schon DSI-View) */
  showDsiButton?: boolean
}

const RadioPlayer: React.FC<RadioPlayerProps> = ({ compact = false, dsi = false, showDsiButton = false }) => {
  const previewMode = compact && !dsi
  const textClass = (dsi || previewMode) ? 'text-white' : 'text-slate-800 dark:text-slate-100'
  const mutedClass = (dsi || previewMode) ? 'text-slate-200' : 'text-slate-500 dark:text-slate-400'
  const cardClass = (dsi || previewMode)
    ? 'bg-gradient-to-b from-slate-900 to-slate-800 border-2 border-slate-500 shadow-inner'
    : 'bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700'
  const [station, setStation] = useState<RadioStation>(RADIO_STATIONS[0])
  const [playing, setPlaying] = useState(false)
  const [metadata, setMetadata] = useState<StreamMetadata | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [logoError, setLogoError] = useState(false)
  const [favoritesPage, setFavoritesPage] = useState(0)
  const [vuL, setVuL] = useState(0)
  const [vuR, setVuR] = useState(0)
  const [vuSignal, setVuSignal] = useState(0)
  const [vuMode, setVuMode] = useState<'led' | 'analog'>('led')
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const switchIdRef = useRef(0)
  const stationIdRef = useRef(station.id)
  const playAttemptRef = useRef<number | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const levelLoopRef = useRef<number | null>(null)
  const containerRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const audio = new Audio()
    audio.addEventListener('error', () => {
      if (!audio.src) return
      if (playAttemptRef.current !== null && playAttemptRef.current === switchIdRef.current) {
        setPlaying(false)
        setError('Stream konnte nicht abgespielt werden (z. B. Proxy/CORS oder Codec).')
      }
    })
    audioRef.current = audio
    return () => {
      if (audioRef.current) {
        audioRef.current.pause()
        audioRef.current.src = ''
        audioRef.current = null
      }
    }
  }, [])

  useEffect(() => {
    stationIdRef.current = station.id
  }, [station])

  /** Echte Pegel aus Stream (Web Audio API): bei Play starten, bei Pause stoppen. */
  const startLevelLoop = (audio: HTMLAudioElement) => {
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {})
      audioContextRef.current = null
    }
    if (levelLoopRef.current) {
      cancelAnimationFrame(levelLoopRef.current)
      levelLoopRef.current = null
    }
    const ctx = new (window.AudioContext || (window as any).webkitAudioContext)()
    const source = ctx.createMediaElementSource(audio)
    const analyser = ctx.createAnalyser()
    analyser.fftSize = 256
    analyser.smoothingTimeConstant = 0.35
    source.connect(analyser)
    analyser.connect(ctx.destination)
    audioContextRef.current = ctx
    analyserRef.current = analyser
    const data = new Uint8Array(analyser.fftSize)
    const tick = () => {
      if (!analyserRef.current || !audioRef.current) return
      analyser.getByteTimeDomainData(data)
      let sum = 0
      for (let i = 0; i < data.length; i++) {
        const n = (data[i] - 128) / 128
        sum += n * n
      }
      const rms = Math.sqrt(sum / data.length)
      const vol = Math.max(0, Math.min(1, audioRef.current.volume))
      const pct = Math.min(100, Math.round(rms * 380 * (vol || 1)))
      setVuL(pct)
      setVuR(pct)
      setVuSignal(pct)
      levelLoopRef.current = requestAnimationFrame(tick)
    }
    levelLoopRef.current = requestAnimationFrame(tick)
  }
  const stopLevelLoop = () => {
    if (levelLoopRef.current) {
      cancelAnimationFrame(levelLoopRef.current)
      levelLoopRef.current = null
    }
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {})
      audioContextRef.current = null
    }
    analyserRef.current = null
  }
  useEffect(() => {
    if (!playing) {
      stopLevelLoop()
      setVuL(0)
      setVuR(0)
      setVuSignal(metadata?.bitrate ? Math.min(100, metadata.bitrate) : 0)
      return
    }
    setVuSignal(metadata?.bitrate ? Math.min(100, metadata.bitrate) : 0)
    return () => { stopLevelLoop() }
  }, [playing, metadata?.bitrate])

  useEffect(() => {
    let cancelled = false
    const curId = station.id
    const fallbackMeta = { title: 'Live', show: '', artist: '', song: '' as string | undefined, bitrate: undefined as number | undefined, server_name: '' }
    const fetchMeta = async () => {
      try {
        const res = await fetchApi(`/api/radio/stream-metadata?url=${encodeURIComponent(station.streamUrl)}`)
        if (!cancelled && stationIdRef.current !== curId) return
        if (res.ok) {
          const data = await res.json().catch(() => ({}))
          const title = data?.title || data?.artist || data?.song ? (data.title ?? 'Live') : 'Live'
          const show = data?.show ?? data?.server_name ?? ''
          setMetadata({
            title,
            artist: data?.artist ?? '',
            song: data?.song ?? '',
            bitrate: data?.bitrate,
            server_name: data?.server_name ?? '',
            show,
          })
        } else {
          setMetadata(fallbackMeta)
        }
      } catch {
        if (!cancelled && stationIdRef.current === curId) setMetadata(fallbackMeta)
      }
    }
    if (playing) {
      fetchMeta()
      const t = setInterval(fetchMeta, 15000) // 15 Sekunden (reduziert Last auf Backend)
      return () => {
        cancelled = true
        clearInterval(t)
      }
    } else {
      setMetadata(null)
    }
  }, [station, playing])

  const play = async (forStationId?: string) => {
    if (!audioRef.current) return
    const sid = forStationId ?? station.id
    switchIdRef.current += 1
    const mySwitch = switchIdRef.current
    setError(null)
    playAttemptRef.current = switchIdRef.current
    setLoading(true)
    if (audioRef.current.src) {
      audioRef.current.pause()
      audioRef.current.src = ''
      audioRef.current.load()
    }
    if (mySwitch !== switchIdRef.current || stationIdRef.current !== sid) return
    const s = RADIO_STATIONS.find(x => x.id === sid) ?? station
    const base = getApiBase() || (typeof window !== 'undefined' ? window.location.origin : '')
    const proxyUrl = base ? `${base}/api/radio/stream?url=${encodeURIComponent(s.streamUrl)}` : null
    const tryPlay = async (url: string) => {
      audioRef.current!.src = url
      await audioRef.current!.play()
    }
    try {
      try {
        await tryPlay(s.streamUrl)
      } catch {
        if (proxyUrl) await tryPlay(proxyUrl)
        else throw new Error('Direct failed')
      }
      if (mySwitch !== switchIdRef.current || stationIdRef.current !== sid) {
        audioRef.current?.pause()
        audioRef.current!.src = ''
        return
      }
      playAttemptRef.current = null
      setPlaying(true)
      setError(null)
      startLevelLoop(audioRef.current!)
    } catch (e) {
      if (mySwitch === switchIdRef.current) {
        setError('Stream fehlgeschlagen. Prüfen: Backend läuft, Audio-Ausgabe in Einstellungen → Sound.')
        setPlaying(false)
      }
    } finally {
      if (mySwitch === switchIdRef.current) setLoading(false)
    }
  }

  const pause = () => {
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current.src = ''
    }
    setPlaying(false)
  }

  const handleStationChange = (s: RadioStation) => {
    const wasPlaying = playing
    switchIdRef.current += 1
    pause()
    setStation(s)
    setLogoError(false)
    if (wasPlaying) setTimeout(() => play(s.id), 120)
  }

  const getLogoSrc = () => {
    if (!station.logoUrl || logoError) return null
    const base = getApiBase()
    const prefix =
      base ||
      (typeof window !== 'undefined' && window.location?.origin && window.location.origin !== 'null'
        ? window.location.origin
        : 'http://127.0.0.1:8000')
    return `${prefix.replace(/\/$/, '')}/api/radio/logo?url=${encodeURIComponent(station.logoUrl)}`
  }

  const dsiRadioUrl = (() => {
    // Immer aktuelle Origin nutzen (Tauri-Dev: 5173, Browser/Vite: 3001 oder aktueller Port)
    const base = typeof window !== 'undefined' ? window.location.origin : 'http://127.0.0.1:5173'
    return `${String(base).replace(/\/$/, '')}/?view=dsi-radio`
  })()

  /** Screenshot-Funktion: Erfasst die Radio-App und kopiert sie in den Zwischenspeicher */
  const takeScreenshot = async () => {
    if (!containerRef.current) return
    
    try {
      const canvas = await html2canvas(containerRef.current, {
        backgroundColor: null,
        scale: 1,
        logging: false,
        useCORS: true,
      })
      
      canvas.toBlob((blob) => {
        if (!blob) {
          toast.error('Fehler beim Erstellen des Screenshots')
          return
        }
        
        const item = new ClipboardItem({ 'image/png': blob })
        navigator.clipboard.write([item]).then(() => {
          toast.success('Screenshot wurde in den Zwischenspeicher kopiert')
        }).catch((err) => {
          console.error('Fehler beim Kopieren in den Zwischenspeicher:', err)
          toast.error('Fehler beim Kopieren in den Zwischenspeicher')
        })
      }, 'image/png')
    } catch (error) {
      console.error('Fehler beim Erstellen des Screenshots:', error)
      toast.error('Fehler beim Erstellen des Screenshots')
    }
  }

  /** F10 Tastenkürzel für Screenshot */
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'F10') {
        event.preventDefault()
        takeScreenshot()
      }
    }
    
    window.addEventListener('keydown', handleKeyDown)
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [])

  return (
    <div ref={containerRef} className={compact ? 'space-y-4' : 'space-y-6'}>
      <p className={`text-sm ${mutedClass}`}>
        Sound über System-Ausgabegerät (Standard: Gehäuse-Lautsprecher).
      </p>

      {/* DSI-Vorschau / Anzeige: Logo + Sender + LED-Meter + Now Playing */}
      <div
        className={`rounded-2xl border overflow-hidden ${cardClass} relative ${
          compact ? 'p-4 sm:p-5' : 'p-6'
        }`}
        style={compact ? { minWidth: 320, maxHeight: '220px' } : { maxHeight: '240px' }}
      >
        {/* X-Button oben rechts zum Beenden (nur im DSI-Modus) */}
        {dsi && (
          <button
            type="button"
            onClick={() => {
              if (typeof window !== 'undefined') {
                window.location.href = window.location.pathname
              }
            }}
            className="absolute top-2 right-2 z-10 w-8 h-8 flex items-center justify-center rounded-lg bg-red-600 hover:bg-red-700 text-white shadow-lg transition-colors"
            title="Radio beenden"
          >
            <X className="w-5 h-5" strokeWidth={2.5} />
          </button>
        )}
        
        <div className="flex flex-col sm:flex-row items-center gap-3 sm:gap-4 pr-8">
          <div className={`w-16 h-16 sm:w-18 sm:h-18 rounded-xl flex items-center justify-center shrink-0 overflow-hidden p-0.5 ${(dsi || previewMode) ? 'bg-slate-700 ring-2 ring-slate-500' : 'bg-white dark:bg-slate-700 shadow-lg'}`}>
            {getLogoSrc() ? (
              <img
                src={getLogoSrc()!}
                alt={station.name}
                className="w-full h-full object-contain"
                onError={() => setLogoError(true)}
              />
            ) : (
              <div className="w-full h-full rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
                <span className="text-lg sm:text-xl font-bold text-white">
                  {station.name.slice(0, 2).toUpperCase()}
                </span>
              </div>
            )}
          </div>
          <div className="flex-1 text-center sm:text-left min-w-0 space-y-0.5">
            <h3 className={`text-xl sm:text-2xl font-bold ${textClass}`}>
              {station.name}
            </h3>
            {(station.region || station.genre) && (
              <p className={`text-xs ${mutedClass}`}>
                {[station.region, station.genre].filter(Boolean).join(' · ')}
              </p>
            )}
            {(metadata?.show ?? metadata?.server_name) && (
              <p className={`text-xs ${mutedClass} truncate`} title={metadata.show ?? metadata.server_name}>
                Sendung: {(metadata.show ?? metadata.server_name ?? '').slice(0, 50)}{(metadata.show ?? metadata.server_name ?? '').length > 50 ? '…' : ''}
              </p>
            )}
            {metadata?.title && (
              <p className={`text-base font-medium truncate ${(dsi || previewMode) ? 'text-emerald-300' : 'text-emerald-600 dark:text-emerald-400'}`} title={metadata.title}>
                Jetzt: {metadata.artist && metadata.song ? `${metadata.artist} – ${metadata.song}` : metadata.title}
              </p>
            )}
            {metadata?.bitrate && (
              <p className={`text-xs ${mutedClass}`}>{metadata.bitrate} kbps</p>
            )}
            {!metadata?.title && (
              <p className={`text-base ${mutedClass}`}>
                {playing ? 'Stream läuft…' : 'Pause'}
              </p>
            )}
          </div>
        </div>

        {/* Aussteuerung: wahlweise LED (7 vertikal: 5 grün, 2 rot) oder analoges Rundinstrument */}
        {(previewMode || dsi) && (
          <div className="mt-4 flex items-end gap-3 flex-wrap">
            <div className="flex gap-1">
              {(['L', 'R', 'Signal'] as const).map((label) => {
                const value = label === 'L' ? vuL : label === 'R' ? vuR : vuSignal
                return (
                  <div key={label} className="flex flex-col items-center gap-0.5">
                    <span className="text-[10px] text-slate-400">{label}</span>
                    {vuMode === 'analog' ? (
                      label === 'Signal' ? (
                        <AnalogGaugeSignal value={value} size={44} />
                      ) : (
                        <AnalogGaugeVu value={value} size={44} />
                      )
                    ) : (
                      <LedStrip value={value} />
                    )}
                  </div>
                )
              })}
            </div>
            <button
              type="button"
              onClick={() => setVuMode((m) => (m === 'led' ? 'analog' : 'led'))}
              className="text-[10px] text-slate-400 hover:text-slate-300 px-1"
              title={vuMode === 'led' ? 'Analog anzeigen' : 'LED anzeigen'}
            >
              {vuMode === 'led' ? 'Analog' : 'LED'}
            </button>
          </div>
        )}
      </div>

      {error && (
        <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
      )}

      {/* Senderauswahl: Vorschau 3×3, 9 pro Seite, 3 Seiten, zweizeilig, Rand genutzt */}
      <div className="space-y-2">
        {previewMode ? (
          <>
            <div className="grid grid-cols-3 gap-2 w-full">
              {RADIO_STATIONS.slice(
                favoritesPage * FAVORITES_PER_PAGE,
                favoritesPage * FAVORITES_PER_PAGE + FAVORITES_PER_PAGE
              ).map((s) => {
                const [line1, line2] = twoLineLabel(s.name)
                return (
                  <button
                    key={s.id}
                    type="button"
                    onClick={() => handleStationChange(s)}
                    className={`min-h-[4rem] sm:min-h-[4.25rem] px-2 py-2.5 rounded-lg text-[12px] sm:text-[13px] font-medium transition-colors flex flex-col items-center justify-center gap-0.5 leading-tight overflow-hidden ${
                      station.id === s.id
                        ? 'bg-emerald-600 text-white ring-2 ring-emerald-400'
                        : 'bg-slate-700 text-slate-200 hover:bg-slate-600 border-2 border-slate-500'
                    }`}
                    title={s.name}
                  >
                    <span className="block text-center w-full" style={{ wordBreak: 'break-word' }}>{line1}</span>
                    {line2 ? <span className="block text-center w-full text-[11px] sm:text-xs opacity-90" style={{ wordBreak: 'break-word' }}>{line2}</span> : null}
                  </button>
                )
              })}
            </div>
            {RADIO_STATIONS.length > FAVORITES_PER_PAGE && (
              <div className="flex justify-center">
                <button
                  type="button"
                  onClick={() => setFavoritesPage((p) => (p + 1) % Math.ceil(RADIO_STATIONS.length / FAVORITES_PER_PAGE))}
                  className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs bg-slate-600 hover:bg-slate-500 text-slate-200"
                  title="Seite wechseln"
                >
                  {favoritesPage > 0 && <ChevronLeft className="w-3.5 h-3.5 shrink-0" />}
                  <span>{favoritesPage + 1}/{Math.ceil(RADIO_STATIONS.length / FAVORITES_PER_PAGE)}</span>
                  {favoritesPage < Math.ceil(RADIO_STATIONS.length / FAVORITES_PER_PAGE) - 1 && <ChevronRight className="w-3.5 h-3.5 shrink-0" />}
                </button>
              </div>
            )}
          </>
        ) : (
          <div className="flex flex-wrap gap-2">
            {RADIO_STATIONS.map((s) => (
              <button
                key={s.id}
                type="button"
                onClick={() => handleStationChange(s)}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors ${
                  station.id === s.id
                    ? 'bg-emerald-600 text-white ring-2 ring-emerald-400'
                    : dsi
                      ? 'bg-slate-700 text-slate-200 hover:bg-slate-600 border-2 border-slate-500'
                      : 'bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-300 dark:hover:bg-slate-600'
                }`}
              >
                {s.name}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Play/Pause */}
      <div className="flex items-center gap-4">
        <button
          type="button"
          onClick={playing ? pause : play}
          disabled={loading}
          className="flex items-center gap-2 px-6 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white font-medium"
        >
          {playing ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
          {loading ? 'Starte…' : playing ? 'Pause' : 'Abspielen'}
        </button>
        {playing && (
          <span className="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400 text-sm">
            <Volume2 className="w-4 h-4" /> Live
          </span>
        )}
        {showDsiButton && !dsi && (
          <span className="flex flex-col gap-1">
            <a
              href={dsiRadioUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-600 hover:bg-slate-500 text-white text-sm font-medium"
            >
              <Monitor className="w-4 h-4" /> Auf DSI anzeigen
            </a>
            <span className="text-xs text-slate-500 dark:text-slate-400">
              Tipp: Wenn die Seite nicht lädt oder das Fenster auf HDMI erscheint, auf dem Pi die native App nutzen: Desktop-Icon „DSI Radio“ oder <code className="bg-slate-200 dark:bg-slate-700 px-1 rounded">./scripts/start-dsi-radio.sh</code> (PyQt6, kein Frontend nötig).
            </span>
          </span>
        )}
      </div>
    </div>
  )
}

export default RadioPlayer
