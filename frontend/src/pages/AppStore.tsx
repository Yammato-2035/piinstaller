import React, { useEffect, useMemo, useState } from 'react'
import { Package, Download, Settings, Search, Monitor, Sparkles } from 'lucide-react'
import HelpTooltip from '../components/HelpTooltip'
import PageHeader from '../components/layout/PageHeader'
import { PandaCompanion, PandaRail } from '../components/companions'
import type { ExperienceLevel } from '../components/Sidebar'
import BeginnerGuidanceMarker from '../beginner/BeginnerGuidanceMarker'
import { getAppStoreBeginnerMeta, MODULE_DEFINITIONS } from '../beginner/moduleModel'
import toast from 'react-hot-toast'
import { fetchApi } from '../api'

interface AppItem {
  id: string
  name: string
  description: string
  category: string
  size?: string
  icon?: string
}

interface AppStatus {
  installed: boolean
  version?: string
}

const CATEGORIES = ['Alle', 'Smart Home', 'Media', 'Cloud', 'Tools', 'Entwicklung']

interface AppStoreProps {
  freenoveDetected?: boolean
  setCurrentPage?: (page: string) => void
  experienceLevel?: ExperienceLevel
}

interface AppStoreAppCardProps {
  app: AppItem
  statuses: Record<string, AppStatus>
  installing: string | null
  onInstall: (id: string) => void
  setCurrentPage?: (page: string) => void
  isBeginner: boolean
}

const AppStoreAppCard: React.FC<AppStoreAppCardProps> = ({
  app,
  statuses,
  installing,
  onInstall,
  setCurrentPage,
  isBeginner,
}) => {
  const status = statuses[app.id]
  const isInstalled = status?.installed
  const isInstalling = installing === app.id
  const meta = getAppStoreBeginnerMeta(app.id)
  const emphasize = isBeginner && meta.tier === 'recommended'

  return (
    <div
      className={`rounded-2xl border bg-white dark:bg-slate-800 p-6 shadow-sm hover:shadow-md transition-shadow ${
        emphasize
          ? 'border-emerald-500/70 ring-2 ring-emerald-500/25 dark:border-emerald-500/50'
          : 'border-slate-200 dark:border-slate-700'
      }`}
    >
      <div className="flex items-start gap-4">
        <div
          className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 ${
            emphasize ? 'bg-emerald-200 dark:bg-emerald-900/50' : 'bg-emerald-100 dark:bg-emerald-900/30'
          }`}
        >
          <Package className="w-6 h-6 text-emerald-600" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-semibold text-lg text-slate-800 dark:text-slate-100">{app.name}</h3>
            {isBeginner && meta.tier === 'recommended' && (
              <span className="text-[10px] font-bold uppercase tracking-wide px-2 py-0.5 rounded-md bg-emerald-600 text-white">Empfohlen</span>
            )}
            {isBeginner && meta.tier === 'advanced_later' && (
              <>
                <BeginnerGuidanceMarker kind="later" compact />
                <BeginnerGuidanceMarker kind="advanced" compact />
              </>
            )}
            {isBeginner && meta.tier === 'standard' && <BeginnerGuidanceMarker kind="advanced" compact />}
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5 line-clamp-2">{app.description}</p>
          {isBeginner && meta.note && (
            <p className="text-xs text-amber-700 dark:text-amber-200/90 mt-2 leading-snug">{meta.note}</p>
          )}
          {app.size && <p className="text-xs text-slate-400 dark:text-slate-500 mt-2">{app.size}</p>}
        </div>
      </div>
      <div className="mt-4 flex gap-2">
        {isInstalled ? (
          <button
            type="button"
            onClick={() =>
              app.id === 'dsi-radio-setup' ? setCurrentPage?.('dsi-radio-settings') : toast('Einstellungen öffnen – Coming soon', { icon: '⚙️' })
            }
            className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 font-medium hover:bg-slate-300 dark:hover:bg-slate-600"
          >
            <Settings className="w-4 h-4" /> Einstellungen
          </button>
        ) : (
          <button
            type="button"
            disabled={isInstalling}
            onClick={() => onInstall(app.id)}
            className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white font-medium"
          >
            {isInstalling ? (
              <>Wird installiert...</>
            ) : (
              <>
                <Download className="w-4 h-4" /> Installieren
              </>
            )}
          </button>
        )}
      </div>
    </div>
  )
}

const APPS_MOCK: AppItem[] = [
  { id: 'home-assistant', name: 'Home Assistant', description: 'Smart Home zentral steuern – Geräte, Automatisierungen, Dashboards.', category: 'Smart Home', size: '~500 MB' },
  { id: 'nextcloud', name: 'Nextcloud', description: 'Eigene Cloud für Dateien, Kalender, Kontakte und mehr.', category: 'Cloud', size: '~400 MB' },
  { id: 'pi-hole', name: 'Pi-hole', description: 'Werbung und Tracker im gesamten Netzwerk blockieren.', category: 'Tools', size: '~200 MB' },
]

const AppStore: React.FC<AppStoreProps> = ({ freenoveDetected = false, setCurrentPage, experienceLevel = 'beginner' }) => {
  const [apps, setApps] = useState<AppItem[]>(APPS_MOCK)
  const [statuses, setStatuses] = useState<Record<string, AppStatus>>({})
  const [category, setCategory] = useState('Alle')
  const [search, setSearch] = useState('')
  const [installing, setInstalling] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const res = await fetchApi('/api/apps')
        if (res.ok) {
          const data = await res.json()
          if (data.apps && Array.isArray(data.apps) && data.apps.length > 0) {
            if (!cancelled) setApps(data.apps)
          }
        }
      } catch {
        /* keep APPS_MOCK */
      }
    })()
    return () => { cancelled = true }
  }, [])

  useEffect(() => {
    let cancelled = false
    const appList = apps
    const load = async () => {
      const st: Record<string, AppStatus> = {}
      for (const app of appList) {
        try {
          const res = await fetchApi(`/api/apps/${app.id}/status`)
          if (res.ok) {
            const data = await res.json()
            st[app.id] = { installed: data.installed === true, version: data.version }
          } else {
            st[app.id] = { installed: false }
          }
        } catch {
          st[app.id] = { installed: false }
        }
      }
      if (!cancelled) setStatuses(st)
    }
    load()
    return () => { cancelled = true }
  }, [apps])

  const filtered = apps.filter(app => {
    const matchCat = category === 'Alle' || app.category === category
    const matchSearch = !search || app.name.toLowerCase().includes(search.toLowerCase()) || app.description.toLowerCase().includes(search.toLowerCase())
    return matchCat && matchSearch
  })

  const isBeginnerAppStore = experienceLevel === 'beginner'

  const sortedForDisplay = useMemo(() => {
    if (!isBeginnerAppStore) return filtered
    const order: Record<string, number> = { recommended: 0, standard: 1, advanced_later: 2 }
    return [...filtered].sort((a, b) => {
      const ta = getAppStoreBeginnerMeta(a.id).tier
      const tb = getAppStoreBeginnerMeta(b.id).tier
      return (order[ta] ?? 1) - (order[tb] ?? 1)
    })
  }, [filtered, isBeginnerAppStore])

  const recommendedApps = useMemo(() => {
    if (!isBeginnerAppStore) return []
    return sortedForDisplay.filter(a => getAppStoreBeginnerMeta(a.id).tier === 'recommended')
  }, [sortedForDisplay, isBeginnerAppStore])

  const otherApps = useMemo(() => {
    if (!isBeginnerAppStore) return sortedForDisplay
    return sortedForDisplay.filter(a => getAppStoreBeginnerMeta(a.id).tier !== 'recommended')
  }, [sortedForDisplay, isBeginnerAppStore])

  const handleInstall = async (id: string) => {
    if (statuses[id]?.installed) {
      toast('App ist bereits installiert. Einstellungen öffnen.', { icon: '⚙️' })
      return
    }
    setInstalling(id)
    try {
      const res = await fetchApi(`/api/apps/${id}/install`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      })
      if (res.ok) {
        const data = await res.json()
        if (data.installed) {
          setStatuses(prev => ({ ...prev, [id]: { installed: true, version: data.version } }))
          toast.success(`${apps.find(a => a.id === id)?.name} wurde installiert.`)
        } else {
          toast.success(data.message || 'Installation gestartet.')
        }
      } else {
        const errData = await res.json().catch(() => ({}))
        const msg = errData.message || 'Installation fehlgeschlagen. Docker installiert? Sudo-Passwort nötig?'
        toast.error(msg, { duration: 6000 })
      }
    } catch {
      toast.error('Huch, das hat nicht geklappt. Die Ein-Klick-Installation kommt in Kürze – bis dahin: Einstellungen oder Dokumentation nutzen.', { duration: 5000 })
    } finally {
      setInstalling(null)
    }
  }

  return (
    <div className="space-y-8">
      <PageHeader
        visualStyle="tech-panel"
        tone="appstore"
        title="App Store"
        subtitle={
          isBeginnerAppStore
            ? `${MODULE_DEFINITIONS['app-store'].subtitle} Zuerst die empfohlenen Apps – andere sind sortiert und gekennzeichnet.`
            : 'Wähle eine App und installiere sie mit wenigen Klicks.'
        }
        status={
          <span className="inline-flex items-center gap-2 flex-wrap">
            {MODULE_DEFINITIONS['app-store'].warningText}
            <HelpTooltip text="Wähle eine App und klicke auf „Installieren“. Die Ein-Klick-Installation wird in einer späteren Version aktiviert." />
          </span>
        }
      />
      {isBeginnerAppStore && (
        <div className="rounded-xl border border-emerald-500/35 bg-emerald-950/20 dark:bg-emerald-950/30 px-4 py-3 text-sm text-emerald-100/95">
          <p className="font-semibold text-emerald-50 flex items-center gap-2">
            <Sparkles className="w-4 h-4 shrink-0 text-emerald-400" aria-hidden />
            Einsteiger-Reihenfolge
          </p>
          <p className="text-xs text-emerald-200/80 mt-1 leading-relaxed">
            Nicht jede App ist für den ersten Tag gleich wichtig. Abschnitt „Empfohlen“ zuerst; „Weitere Apps“ können mehr Vorbereitung brauchen oder sind für später markiert.
          </p>
        </div>
      )}
      {experienceLevel === 'beginner' && (
        <PandaRail>
          <PandaCompanion
            type="tutorial"
            size="sm"
            surface="dark"
            frame={false}
            showTrafficLight
            trafficLightPosition="bottom-right"
            status="info"
            title="App-Begleiter"
            subtitle="Ich sortiere passende Apps nach Einsteiger-Reihenfolge – achte auf die Badges an den Karten."
          />
        </PandaRail>
      )}

      {freenoveDetected && (
        <div className="rounded-2xl border border-emerald-200 dark:border-emerald-800 bg-emerald-50/50 dark:bg-emerald-900/20 p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center shrink-0">
              <Monitor className="w-6 h-6 text-emerald-600" />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-lg text-slate-800 dark:text-slate-100">Freenove 4,3″ TFT Display</h3>
              <p className="text-sm text-slate-600 dark:text-slate-400 mt-0.5">
                Gehäuse-Display erkannt. Dashboard, Radio, Wecker und mehr – direkt auf dem Touchscreen.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setCurrentPage?.('tft')}
              className="px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-medium"
            >
              TFT Display öffnen
            </button>
          </div>
        </div>
      )}

      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
          <input
            type="text"
            placeholder="Suche nach App..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 placeholder-slate-400"
          />
        </div>
        {!isBeginnerAppStore && (
          <div className="flex flex-wrap gap-2">
            {CATEGORIES.map(cat => (
              <button
                key={cat}
                onClick={() => setCategory(cat)}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors ${
                  category === cat
                    ? 'bg-emerald-600 text-white'
                    : 'bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-300 dark:hover:bg-slate-600'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        )}
        {isBeginnerAppStore && (
          <div className="flex items-center">
            <span className="text-xs text-slate-500 dark:text-slate-400 px-2">
              Kategorien ausgeblendet – Fokus auf empfohlene Reihenfolge. Suche nutzen oder in den Einstellungen auf Fortgeschritten wechseln.
            </span>
          </div>
        )}
      </div>

      {isBeginnerAppStore && recommendedApps.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-emerald-600 dark:text-emerald-400 uppercase tracking-wide">Empfohlen zum Einstieg</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {recommendedApps.map(app => (
              <AppStoreAppCard
                key={app.id}
                app={app}
                statuses={statuses}
                installing={installing}
                onInstall={handleInstall}
                setCurrentPage={setCurrentPage}
                isBeginner
              />
            ))}
          </div>
        </div>
      )}

      {isBeginnerAppStore && otherApps.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Weitere Apps</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {otherApps.map(app => (
              <AppStoreAppCard
                key={app.id}
                app={app}
                statuses={statuses}
                installing={installing}
                onInstall={handleInstall}
                setCurrentPage={setCurrentPage}
                isBeginner
              />
            ))}
          </div>
        </div>
      )}

      {!isBeginnerAppStore && (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {sortedForDisplay.map(app => (
          <AppStoreAppCard
            key={app.id}
            app={app}
            statuses={statuses}
            installing={installing}
            onInstall={handleInstall}
            setCurrentPage={setCurrentPage}
            isBeginner={false}
          />
        ))}
      </div>
      )}

      {filtered.length === 0 && (
        <p className="text-center text-slate-500 dark:text-slate-400 py-8">
          Keine Apps gefunden. Suche oder Kategorie anpassen.
        </p>
      )}
    </div>
  )
}

export default AppStore
