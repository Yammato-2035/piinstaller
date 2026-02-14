import React, { useEffect, useState } from 'react'
import { Radio, List, Palette, Image, Gauge, Clock, Save } from 'lucide-react'
import toast from 'react-hot-toast'
import { fetchApi } from '../api'

interface Station {
  id: string
  name: string
  stream_url?: string
  url?: string
  logo_url?: string
  region?: string
  genre?: string
}

const DsiRadioSettings: React.FC<{ setCurrentPage?: (page: string) => void }> = ({ setCurrentPage }) => {
  const [favorites, setFavorites] = useState<Station[]>([])
  const [theme, setTheme] = useState('Klavierlack')
  const [showClock, setShowClock] = useState(true)
  const [vuMode, setVuMode] = useState<'led' | 'analog'>('led')
  const [logoSource, setLogoSource] = useState<'url' | 'local'>('url')
  const [logoSize, setLogoSize] = useState<'small' | 'medium' | 'large'>('medium')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const [favRes, themeRes, displayRes, iconsRes] = await Promise.all([
        fetchApi('/api/radio/dsi-config/favorites'),
        fetchApi('/api/radio/dsi-theme'),
        fetchApi('/api/radio/dsi-config/display'),
        fetchApi('/api/radio/dsi-config/icons'),
      ])
      if (favRes.ok) {
        const d = await favRes.json()
        if (Array.isArray(d.favorites)) setFavorites(d.favorites)
      }
      if (themeRes.ok) {
        const d = await themeRes.json()
        if (d.theme) setTheme(d.theme)
      }
      if (displayRes.ok) {
        const d = await displayRes.json()
        setShowClock(d.show_clock !== false)
        if (d.vu_mode === 'analog' || d.vu_mode === 'led') setVuMode(d.vu_mode)
      }
      if (iconsRes.ok) {
        const d = await iconsRes.json()
        setLogoSource(d.logo_source === 'local' ? 'local' : 'url')
        if (['small', 'medium', 'large'].includes(d.logo_size)) setLogoSize(d.logo_size)
      }
    } catch {
      toast.error('Einstellungen konnten nicht geladen werden.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const saveTheme = async () => {
    setSaving(true)
    try {
      const res = await fetchApi('/api/radio/dsi-theme', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ theme }),
      })
      if (res.ok) {
        toast.success('Theme gespeichert.')
      } else toast.error('Theme speichern fehlgeschlagen.')
    } catch {
      toast.error('Theme speichern fehlgeschlagen.')
    } finally {
      setSaving(false)
    }
  }

  const saveDisplay = async () => {
    setSaving(true)
    try {
      const res = await fetchApi('/api/radio/dsi-config/display', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ show_clock: showClock, vu_mode: vuMode }),
      })
      if (res.ok) {
        toast.success('Anzeige-Einstellungen gespeichert.')
      } else toast.error('Speichern fehlgeschlagen.')
    } catch {
      toast.error('Speichern fehlgeschlagen.')
    } finally {
      setSaving(false)
    }
  }

  const saveIcons = async () => {
    setSaving(true)
    try {
      const res = await fetchApi('/api/radio/dsi-config/icons', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ logo_source: logoSource, logo_size: logoSize }),
      })
      if (res.ok) {
        toast.success('Icon-Einstellungen gespeichert.')
      } else toast.error('Speichern fehlgeschlagen.')
    } catch {
      toast.error('Speichern fehlgeschlagen.')
    } finally {
      setSaving(false)
    }
  }

  const saveFavorites = async () => {
    setSaving(true)
    try {
      const res = await fetchApi('/api/radio/dsi-config/favorites', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ favorites }),
      })
      if (res.ok) {
        toast.success('Senderliste gespeichert.')
      } else toast.error('Senderliste speichern fehlgeschlagen.')
    } catch {
      toast.error('Senderliste speichern fehlgeschlagen.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-8">
        <h1 className="text-3xl font-bold text-slate-800 dark:text-slate-100 flex items-center gap-3">
          <Radio className="w-9 h-9 text-sky-500" />
          DSI-Radio Einstellungen
        </h1>
        <p className="text-slate-500 dark:text-slate-400">Lade Einstellungen …</p>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-slate-800 dark:text-slate-100 flex items-center gap-3">
          <Radio className="w-9 h-9 text-sky-500" />
          DSI-Radio Einstellungen
        </h1>
        <p className="text-slate-600 dark:text-slate-400 mt-1">
          Senderliste, Themes und Anzeige-Optionen für die DSI-Radio-App (Freenove-TFT). Änderungen gelten nach Neustart der DSI-Radio-App.
        </p>
      </div>

      {/* Senderliste */}
      <section className="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-6 shadow-sm">
        <h2 className="text-xl font-semibold text-slate-800 dark:text-slate-100 flex items-center gap-2 mb-4">
          <List className="w-5 h-5 text-sky-500" />
          Senderliste (Favoriten)
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
          Maximal 20 Favoriten. Reihenfolge und Liste können Sie hier verwalten; Sender hinzufügen/entfernen geht auch direkt in der DSI-Radio-App.
        </p>
        <div className="max-h-64 overflow-y-auto rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-900 p-3 space-y-1">
          {favorites.length === 0 ? (
            <p className="text-slate-500 dark:text-slate-400 text-sm">Noch keine Favoriten. In der DSI-Radio-App über „Senderliste“ hinzufügen.</p>
          ) : (
            favorites.map((s, i) => (
              <div key={s.id || i} className="flex items-center justify-between py-1.5 px-2 rounded bg-white dark:bg-slate-800">
                <span className="font-medium text-slate-800 dark:text-slate-100">{s.name || '?'}</span>
                <span className="text-xs text-slate-400 truncate max-w-[200px]">{s.region || s.genre || ''}</span>
              </div>
            ))
          )}
        </div>
        <button
          type="button"
          onClick={saveFavorites}
          disabled={saving}
          className="mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-sky-600 hover:bg-sky-700 disabled:opacity-50 text-white font-medium"
        >
          <Save className="w-4 h-4" /> Senderliste übernehmen
        </button>
      </section>

      {/* Theme */}
      <section className="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-6 shadow-sm">
        <h2 className="text-xl font-semibold text-slate-800 dark:text-slate-100 flex items-center gap-2 mb-4">
          <Palette className="w-5 h-5 text-sky-500" />
          Theme
        </h2>
        <div className="flex flex-wrap gap-3">
          {['Klavierlack', 'Classic', 'Hell'].map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setTheme(t)}
              className={`px-4 py-2 rounded-xl font-medium ${theme === t ? 'bg-sky-600 text-white' : 'bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-300 dark:hover:bg-slate-600'}`}
            >
              {t}
            </button>
          ))}
        </div>
        <button
          type="button"
          onClick={saveTheme}
          disabled={saving}
          className="mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-sky-600 hover:bg-sky-700 disabled:opacity-50 text-white font-medium"
        >
          <Save className="w-4 h-4" /> Theme speichern
        </button>
      </section>

      {/* Anzeige: Uhr, VU-Meter */}
      <section className="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-6 shadow-sm">
        <h2 className="text-xl font-semibold text-slate-800 dark:text-slate-100 flex items-center gap-2 mb-4">
          <Gauge className="w-5 h-5 text-sky-500" />
          Anzeige
        </h2>
        <div className="space-y-4">
          <label className="flex items-center gap-3 cursor-pointer">
            <input type="checkbox" checked={showClock} onChange={(e) => setShowClock(e.target.checked)} className="rounded border-slate-300" />
            <Clock className="w-5 h-5 text-slate-500" />
            <span className="text-slate-700 dark:text-slate-300">Uhr (Datum & Zeit) anzeigen</span>
          </label>
          <div>
            <span className="text-slate-700 dark:text-slate-300 block mb-2">VU-Meter:</span>
            <div className="flex gap-3">
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="radio" name="vu_mode" checked={vuMode === 'led'} onChange={() => setVuMode('led')} className="text-sky-600" />
                LED (Digital)
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="radio" name="vu_mode" checked={vuMode === 'analog'} onChange={() => setVuMode('analog')} className="text-sky-600" />
                Analog
              </label>
            </div>
          </div>
        </div>
        <button
          type="button"
          onClick={saveDisplay}
          disabled={saving}
          className="mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-sky-600 hover:bg-sky-700 disabled:opacity-50 text-white font-medium"
        >
          <Save className="w-4 h-4" /> Anzeige speichern
        </button>
      </section>

      {/* Icons */}
      <section className="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-6 shadow-sm">
        <h2 className="text-xl font-semibold text-slate-800 dark:text-slate-100 flex items-center gap-2 mb-4">
          <Image className="w-5 h-5 text-sky-500" />
          Sender-Icons
        </h2>
        <div className="space-y-4">
          <div>
            <span className="text-slate-700 dark:text-slate-300 block mb-2">Logo-Quelle:</span>
            <div className="flex gap-3">
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="radio" name="logo_source" checked={logoSource === 'url'} onChange={() => setLogoSource('url')} className="text-sky-600" />
                URL (Stream/Sender)
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="radio" name="logo_source" checked={logoSource === 'local'} onChange={() => setLogoSource('local')} className="text-sky-600" />
                Lokal (Cache)
              </label>
            </div>
          </div>
          <div>
            <span className="text-slate-700 dark:text-slate-300 block mb-2">Größe:</span>
            <div className="flex gap-3">
              {(['small', 'medium', 'large'] as const).map((s) => (
                <label key={s} className="flex items-center gap-2 cursor-pointer">
                  <input type="radio" name="logo_size" checked={logoSize === s} onChange={() => setLogoSize(s)} className="text-sky-600" />
                  {s === 'small' ? 'Klein' : s === 'medium' ? 'Mittel' : 'Groß'}
                </label>
              ))}
            </div>
          </div>
        </div>
        <button
          type="button"
          onClick={saveIcons}
          disabled={saving}
          className="mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-sky-600 hover:bg-sky-700 disabled:opacity-50 text-white font-medium"
        >
          <Save className="w-4 h-4" /> Icons speichern
        </button>
      </section>
    </div>
  )
}

export default DsiRadioSettings
