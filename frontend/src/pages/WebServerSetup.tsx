import React, { useState, useEffect } from 'react'
import { Globe, Settings, Lock, Monitor, LayoutDashboard, Sliders } from 'lucide-react'
import toast from 'react-hot-toast'
import { motion } from 'framer-motion'
import { fetchApi } from '../api'
import { usePlatform } from '../context/PlatformContext'

type WebServerTab = 'overview' | 'config'

const WebServerSetup: React.FC = () => {
  const { pageSubtitleLabel } = usePlatform()
  const [activeTab, setActiveTab] = useState<WebServerTab>('overview')
  const [config, setConfig] = useState({
    server_type: 'nginx',
    enable_ssl: true,
    enable_php: false,
    cms_type: null as string | null,
    install_webadmin: true,
    webadmin_type: 'cockpit',
  })

  const [loading, setLoading] = useState(false)
  const [webserverStatus, setWebserverStatus] = useState<any>(null)

  useEffect(() => {
    loadWebserverStatus()
  }, [])

  const loadWebserverStatus = async () => {
    try {
      const response = await fetchApi('/api/webserver/status')
      const data = await response.json()
      setWebserverStatus(data)
      
      // Setze PHP-Status basierend auf tatsächlicher Installation
      if (data.php?.installed) {
        setConfig(prev => ({ ...prev, enable_php: true }))
      }
    } catch (error) {
      console.error('Fehler beim Laden des Webserver-Status:', error)
    }
  }

  const serverTypes = [
    { id: 'nginx', label: '⚡ Nginx', desc: 'Schnell & Leicht' },
    { id: 'apache', label: '🪚 Apache', desc: 'Vollgepackt & Flexibel' },
  ]

  const cms_options = [
    { id: 'wordpress', label: '📰 WordPress', desc: 'Blog & CMS', docsLink: 'https://wordpress.org/documentation/' },
    { id: 'drupal', label: '🌳 Drupal', desc: 'Enterprise CMS', docsLink: 'https://www.drupal.org/docs' },
    { id: 'nextcloud', label: '☁️ Nextcloud', desc: 'Cloud-Speicher', docsLink: 'https://docs.nextcloud.com/' },
    { id: null, label: '❌ Keine CMS', desc: 'Nur Webserver' },
  ]

  const webadmin_options = [
    { id: 'cockpit', label: '🎛️ Cockpit', desc: 'Modern & Einfach (Port 9090)', docsLink: 'https://cockpit-project.org/documentation.html' },
    { id: 'webmin', label: '⚙️ Webmin', desc: 'Umfangreich (Port 10000)', docsLink: 'https://webmin.com/docs.html' },
  ]
  
  const serverDocs = {
    'nginx': 'https://nginx.org/en/docs/',
    'apache': 'https://httpd.apache.org/docs/',
  }

  const applyConfig = async () => {
    // Prüfe ob sudo-Passwort benötigt wird
    const sudoPassword = prompt('Sudo-Passwort eingeben (für Installation/Konfiguration):')
    if (!sudoPassword) {
      toast.error('Sudo-Passwort erforderlich')
      return
    }
    
    setLoading(true)
    try {
      const response = await fetchApi('/api/webserver/configure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...config,
          sudo_password: sudoPassword,
        }),
      })
      const data = await response.json()
      
      if (data.status === 'success') {
        toast.success('Webserver konfiguriert!')
        if (data.results && data.results.length > 0) {
          console.log('Konfigurations-Ergebnisse:', data.results)
        }
        // Status neu laden
        await loadWebserverStatus()
      } else {
        if (data.requires_sudo_password) {
          toast.error('Sudo-Passwort erforderlich')
        } else {
          toast.error(data.message || 'Fehler bei der Konfiguration')
        }
      }
      console.log(data)
    } catch (error) {
      toast.error('Fehler bei der Konfiguration')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const SelectCard = ({ item, selected, onChange, installed, link, docsLink }: any) => {
    const isInstalled = installed === true
    const isDisabled = isInstalled && !selected
    
    return (
      <div className={`p-4 rounded-lg border-2 text-left transition-all ${
        isInstalled
          ? 'bg-green-900/20 border-green-600/50'
          : selected
          ? 'bg-sky-600/20 border-sky-500'
          : 'bg-slate-700/30 border-slate-600 hover:border-slate-500'
      } ${isDisabled ? 'opacity-60 cursor-not-allowed' : ''}`}>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <p className="font-bold text-white">{item.label}</p>
              {isInstalled && (
                <span className="px-2 py-0.5 bg-green-900/50 text-green-300 rounded text-xs">✓ Installiert</span>
              )}
            </div>
            <p className="text-sm text-slate-400 mt-1">{item.desc}</p>
            <div className="flex gap-2 mt-2">
              {isInstalled && link && (
                <a
                  href={link}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="px-3 py-1 bg-sky-600 hover:bg-sky-700 text-white rounded text-xs transition-colors"
                >
                  🔗 Öffnen
                </a>
              )}
              {docsLink && (
                <a
                  href={docsLink}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="px-3 py-1 bg-purple-600 hover:bg-purple-700 text-white rounded text-xs transition-colors"
                >
                  📖 Dokumentation
                </a>
              )}
            </div>
          </div>
          {!isDisabled && (
            <button
              onClick={() => onChange(item.id)}
              className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${
                selected
                  ? 'bg-sky-600 border-sky-600'
                  : 'border-slate-500'
              }`}
            >
              {selected && <span className="text-white font-bold">✓</span>}
            </button>
          )}
        </div>
      </div>
    )
  }

  const CheckboxItem = ({ label, checked, onChange, installed }: any) => {
    const isInstalled = installed === true
    // Für PHP: Checkbox aktivieren, auch wenn installiert (für Konfiguration)
    const isDisabled = false // PHP kann immer aktiviert/deaktiviert werden
    
    return (
      <label className={`flex items-center gap-3 p-4 rounded-lg transition-all ${
        isInstalled
          ? 'bg-green-900/20 border-2 border-green-600/50'
          : 'bg-slate-700/30 hover:bg-slate-700/50'
      } cursor-pointer`}>
        <input
          type="checkbox"
          checked={checked || isInstalled}
          onChange={(e) => {
            onChange(e.target.checked)
          }}
          disabled={isDisabled}
          className="w-5 h-5 accent-sky-600"
        />
        <span className="font-medium flex-1">{label}</span>
        {isInstalled && (
          <span className="px-2 py-0.5 bg-green-900/50 text-green-300 rounded text-xs">✓ Installiert</span>
        )}
      </label>
    )
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <div className="page-title-category mb-2 inline-flex">
          <h1 className="flex items-center gap-3">
            <Globe className="text-purple-500" />
            Webserver Konfiguration
          </h1>
        </div>
        <p className="text-slate-400">Webserver – {pageSubtitleLabel}</p>
      </div>

      {/* Untermenü wie bei Backup & Restore */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="card">
        <div className="flex gap-2 border-b border-slate-700 mb-6">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-4 py-2 font-medium transition-all relative flex items-center gap-2 ${
              activeTab === 'overview' ? 'text-sky-400' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <LayoutDashboard size={18} />
            Übersicht
            {activeTab === 'overview' && (
              <motion.div
                layoutId="webServerActiveTab"
                className="absolute bottom-0 left-0 right-0 h-0.5 bg-sky-400"
                initial={false}
                transition={{ type: 'spring', stiffness: 500, damping: 30 }}
              />
            )}
          </button>
          <button
            onClick={() => setActiveTab('config')}
            className={`px-4 py-2 font-medium transition-all relative flex items-center gap-2 ${
              activeTab === 'config' ? 'text-sky-400' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Sliders size={18} />
            Konfiguration
            {activeTab === 'config' && (
              <motion.div
                layoutId="webServerActiveTab"
                className="absolute bottom-0 left-0 right-0 h-0.5 bg-sky-400"
                initial={false}
                transition={{ type: 'spring', stiffness: 500, damping: 30 }}
              />
            )}
          </button>
        </div>
      </motion.div>

      {/* Tab-Inhalt */}
      <motion.div
        key={activeTab}
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.2 }}
        className="space-y-6"
      >
        {activeTab === 'overview' && !webserverStatus && (
          <div className="card bg-slate-700/50">
            <p className="text-slate-400">Status wird geladen…</p>
          </div>
        )}
        {activeTab === 'overview' && webserverStatus && (
          <div className="card bg-slate-700/50">
            <h2 className="text-2xl font-bold text-white mb-4">Aktuelle Installationen</h2>
              
              <div className="grid md:grid-cols-2 gap-4 mb-4">
                <div className="p-4 bg-slate-800/50 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold">Nginx</span>
                    {webserverStatus.nginx?.installed ? (
                      <span className={`px-2 py-1 rounded text-xs ${
                        webserverStatus.nginx.running 
                          ? 'bg-green-900/50 text-green-300' 
                          : 'bg-yellow-900/50 text-yellow-300'
                      }`}>
                        {webserverStatus.nginx.running ? '✅ Installiert & Läuft' : '⚠️ Installiert (Stoppt)'}
                      </span>
                    ) : (
                      <span className="px-2 py-1 bg-red-900/50 text-red-300 rounded text-xs">❌ Nicht installiert</span>
                    )}
                  </div>
                </div>

                <div className="p-4 bg-slate-800/50 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold">Apache</span>
                    {webserverStatus.apache?.installed ? (
                      <span className={`px-2 py-1 rounded text-xs ${
                        webserverStatus.apache.running 
                          ? 'bg-green-900/50 text-green-300' 
                          : 'bg-yellow-900/50 text-yellow-300'
                      }`}>
                        {webserverStatus.apache.running ? '✅ Installiert & Läuft' : '⚠️ Installiert (Stoppt)'}
                      </span>
                    ) : (
                      <span className="px-2 py-1 bg-red-900/50 text-red-300 rounded text-xs">❌ Nicht installiert</span>
                    )}
                  </div>
                </div>
              </div>

              {webserverStatus.network?.ips && webserverStatus.network.ips.length > 0 && (
                <div className="p-4 bg-slate-800/50 rounded-lg mb-4">
                  <span className="font-semibold block mb-2">IP-Adressen:</span>
                  <div className="flex flex-wrap gap-2">
                    {webserverStatus.network.ips.map((ip: string, i: number) => (
                      <span key={i} className="px-3 py-1 bg-blue-900/50 text-blue-300 rounded text-sm font-mono">
                        {ip}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {webserverStatus.pi_installer && (
                <div className="p-4 bg-slate-800/50 rounded-lg mb-4">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold">🚀 Diese Anwendung</span>
                    <a
                      href={webserverStatus.pi_installer.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-1 bg-sky-600 hover:bg-sky-700 text-white rounded text-sm transition-colors"
                    >
                      🔗 Öffnen
                    </a>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">{webserverStatus.pi_installer.url}</p>
                </div>
              )}

              {webserverStatus.website_names && webserverStatus.website_names.length > 0 && (
                <div className="p-4 bg-slate-800/50 rounded-lg mb-4">
                  <span className="font-semibold block mb-2">🌐 Website-Namen:</span>
                  <div className="flex flex-wrap gap-2">
                    {webserverStatus.website_names.map((name: string, i: number) => (
                      <span key={i} className="px-3 py-1 bg-green-900/50 text-green-300 rounded text-sm">
                        {name}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {webserverStatus.installed_cms && (
                <div className="p-4 bg-slate-800/50 rounded-lg mb-4">
                  <span className="font-semibold block mb-2">Installierte CMS & Apps:</span>
                  <div className="space-y-2">
                    {webserverStatus.installed_cms.wordpress && (
                      <div className="p-2 bg-green-900/20 border border-green-600/50 rounded">
                        <div className="flex items-center justify-between">
                          <span className="text-green-300 font-semibold">📰 WordPress</span>
                          <span className="px-2 py-1 bg-green-900/50 text-green-300 rounded text-xs">✓ Installiert</span>
                        </div>
                        {webserverStatus.installed_cms.wordpress.plugins && webserverStatus.installed_cms.wordpress.plugins.length > 0 && (
                          <div className="mt-2">
                            <p className="text-xs text-slate-400 mb-1">Plugins ({webserverStatus.installed_cms.wordpress.plugins.length}):</p>
                            <div className="flex flex-wrap gap-1">
                              {webserverStatus.installed_cms.wordpress.plugins.slice(0, 5).map((plugin: string, i: number) => (
                                <span key={i} className="px-2 py-0.5 bg-slate-700/50 text-slate-300 rounded text-xs">
                                  {plugin}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                    {webserverStatus.installed_cms.nextcloud && (
                      <div className="p-2 bg-green-900/20 border border-green-600/50 rounded">
                        <span className="text-green-300 font-semibold">☁️ Nextcloud</span>
                        <span className="ml-2 px-2 py-1 bg-green-900/50 text-green-300 rounded text-xs">✓ Installiert</span>
                      </div>
                    )}
                    {webserverStatus.installed_cms.drupal && (
                      <div className="p-2 bg-green-900/20 border border-green-600/50 rounded">
                        <span className="text-green-300 font-semibold">🌳 Drupal</span>
                        <span className="ml-2 px-2 py-1 bg-green-900/50 text-green-300 rounded text-xs">✓ Installiert</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {webserverStatus.websites && webserverStatus.websites.length > 0 && (
                <div className="p-4 bg-slate-800/50 rounded-lg mb-4">
                  <span className="font-semibold block mb-2">Erkannte Websites/Apps:</span>
                  <div className="space-y-1">
                    {webserverStatus.websites.map((site: string, i: number) => (
                      <div key={i} className="p-2 bg-slate-700/30 rounded text-sm font-mono text-slate-300">
                        {site}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {webserverStatus.cockpit && (
                <div className="p-4 bg-slate-800/50 rounded-lg mb-4">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold">🎛️ Cockpit</span>
                    {webserverStatus.cockpit.installed ? (
                      <span className={`px-2 py-1 rounded text-xs ${
                        webserverStatus.cockpit.running 
                          ? 'bg-green-900/50 text-green-300' 
                          : 'bg-yellow-900/50 text-yellow-300'
                      }`}>
                        {webserverStatus.cockpit.running ? '✅ Installiert & Läuft' : '⚠️ Installiert (Stoppt)'}
                      </span>
                    ) : (
                      <span className="px-2 py-1 bg-red-900/50 text-white rounded text-xs">❌ Nicht installiert</span>
                    )}
                  </div>
                  {webserverStatus.cockpit.port && webserverStatus.cockpit.installed && (
                    <div className="mt-2 flex items-center gap-2">
                      <p className="text-xs text-slate-400">Port: {webserverStatus.cockpit.port}</p>
                      {webserverStatus.network?.ips?.[0] && (
                        <a
                          href={`http://${webserverStatus.network.ips[0]}:${webserverStatus.cockpit.port}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="px-2 py-1 bg-sky-600 hover:bg-sky-700 text-white rounded text-xs transition-colors"
                        >
                          🔗 Öffnen
                        </a>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Webmin (Webadmin) – immer anzeigen, Nachinstall/Deinstall */}
              <div className="p-4 bg-slate-800/50 rounded-lg mb-4">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <span className="font-semibold">⚙️ Webmin (Webadmin-Panel)</span>
                  {webserverStatus?.webmin?.installed ? (
                    <span className={`px-2 py-1 rounded text-xs ${
                      webserverStatus.webmin.running 
                        ? 'bg-green-900/50 text-green-300' 
                        : 'bg-yellow-900/50 text-yellow-300'
                    }`}>
                      {webserverStatus.webmin.running ? '✅ Installiert & Läuft' : '⚠️ Installiert (Stoppt)'}
                    </span>
                  ) : (
                    <span className="px-2 py-1 bg-slate-600 text-slate-300 rounded text-xs">Nicht installiert</span>
                  )}
                </div>
                {(webserverStatus?.webmin?.port && webserverStatus?.webmin?.installed) && (
                  <div className="mt-2 flex items-center gap-2 flex-wrap">
                    <p className="text-xs text-slate-400">Port: {webserverStatus.webmin.port}</p>
                    {webserverStatus?.network?.ips?.[0] && (
                      <a
                        href={`http://${webserverStatus.network.ips[0]}:${webserverStatus.webmin.port}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-2 py-1 bg-sky-600 hover:bg-sky-700 text-white rounded text-xs transition-colors"
                      >
                        🔗 Öffnen
                      </a>
                    )}
                  </div>
                )}
                <p className="text-xs text-slate-500 mt-1">Webmin: Systemadministration per Browser (Port 10000). Über „Webadmin auswählen“ unten: Nachinstallieren oder Konfiguration anpassen.</p>
              </div>

              {webserverStatus.webserver_ports && webserverStatus.webserver_ports.length > 0 && (
                <div className="p-4 bg-slate-800/50 rounded-lg mt-4">
                  <span className="font-semibold block mb-2">Webserver Ports:</span>
                  <div className="text-xs text-slate-400 space-y-1">
                    {webserverStatus.webserver_ports.slice(0, 5).map((port: string, i: number) => (
                      <div key={i} className="font-mono">{port}</div>
                    ))}
                  </div>
                </div>
              )}
          </div>
        )}

        {activeTab === 'config' && (
          <div className="grid lg:grid-cols-4 gap-6">
            <div className="lg:col-span-3 space-y-8">
              {/* Server Type Selection */}
              <div className="card">
                <h2 className="text-2xl font-bold text-white mb-4">Webserver Typ</h2>
                <div className="grid md:grid-cols-2 gap-4">
                  {serverTypes.map((server) => (
                    <SelectCard
                      key={server.id}
                      item={server}
                      selected={config.server_type === server.id}
                      onChange={(id: string) => setConfig({ ...config, server_type: id })}
                      docsLink={serverDocs[server.id as keyof typeof serverDocs]}
                    />
                  ))}
                </div>
              </div>

              {/* Security Options */}
              <div className="card">
                <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
                  <Lock size={24} />
                  Sicherheit
                </h2>
                <div className="space-y-3">
                  <CheckboxItem
                    label="🔒 SSL/TLS mit Let's Encrypt"
                    checked={config.enable_ssl}
                    onChange={(v) => setConfig({ ...config, enable_ssl: v })}
                  />
                  <CheckboxItem
                    label="💻 PHP Support"
                    checked={config.enable_php}
                    onChange={(v) => setConfig({ ...config, enable_php: v })}
                    installed={webserverStatus?.php?.installed}
                  />
                  <CheckboxItem
                    label="🎛️ Webadmin Panel"
                    checked={config.install_webadmin}
                    onChange={(v) => setConfig({ ...config, install_webadmin: v })}
                  />
                </div>
              </div>

              {/* CMS Selection */}
              <div className="card">
                <h2 className="text-2xl font-bold text-white mb-4">Content Management System</h2>
                <div className="grid md:grid-cols-2 gap-4">
                  {cms_options.map((cms) => {
                    const isInstalled = cms.id && webserverStatus?.installed_cms?.[cms.id]
                    const link = isInstalled && cms.id === 'wordpress' 
                      ? (webserverStatus?.network?.ips?.[0] ? `http://${webserverStatus.network.ips[0]}` : null)
                      : isInstalled && cms.id === 'nextcloud'
                      ? (webserverStatus?.network?.ips?.[0] ? `http://${webserverStatus.network.ips[0]}/nextcloud` : null)
                      : isInstalled && cms.id === 'drupal'
                      ? (webserverStatus?.network?.ips?.[0] ? `http://${webserverStatus.network.ips[0]}/drupal` : null)
                      : null
                    return (
                      <SelectCard
                        key={cms.id || 'none'}
                        item={cms}
                        selected={config.cms_type === cms.id}
                        onChange={(id: string | null) => setConfig({ ...config, cms_type: id })}
                        installed={isInstalled}
                        link={link}
                        docsLink={cms.docsLink}
                      />
                    )
                  })}
                </div>
              </div>

              {/* Webadmin Selection */}
              {config.install_webadmin && (
                <div className="card">
                  <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
                    <Monitor size={24} />
                    Webadmin Panel
                  </h2>
                  <div className="grid md:grid-cols-2 gap-4">
                    {webadmin_options.map((admin) => {
                      const adminStatus = admin.id === 'cockpit' 
                        ? webserverStatus?.cockpit 
                        : webserverStatus?.webmin
                      const isInstalled = adminStatus?.installed
                      const link = isInstalled && adminStatus?.port
                        ? (webserverStatus?.network?.ips?.[0] 
                            ? `http://${webserverStatus.network.ips[0]}:${adminStatus.port}` 
                            : `http://localhost:${adminStatus.port}`)
                        : null
                      return (
                        <SelectCard
                          key={admin.id}
                          item={admin}
                          selected={config.webadmin_type === admin.id}
                          onChange={(id: string) => setConfig({ ...config, webadmin_type: id })}
                          installed={isInstalled}
                          link={link}
                          docsLink={admin.docsLink}
                        />
                      )
                    })}
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <button
                onClick={applyConfig}
                disabled={loading}
                className="w-full btn-primary text-lg py-3 flex items-center justify-center gap-2"
              >
                {loading ? '⏳ Wird konfiguriert...' : '✓ Konfiguration anwenden'}
              </button>
            </div>

            {/* Info Panel */}
            <div className="space-y-4">
              <div className="card bg-gradient-to-br from-purple-900/30 to-purple-900/10 border-purple-500/50">
                <h3 className="text-lg font-bold text-purple-300 mb-3">🌐 Ports</h3>
                <div className="text-sm text-slate-300 space-y-1">
                  <p><span className="font-semibold">80</span> - HTTP</p>
                  <p><span className="font-semibold">443</span> - HTTPS</p>
                  <p><span className="font-semibold">9090</span> - Cockpit</p>
                  <p><span className="font-semibold">10000</span> - Webmin</p>
                </div>
              </div>

              <div className="card bg-gradient-to-br from-green-900/30 to-green-900/10 border-green-500/50">
                <h3 className="text-lg font-bold text-green-300 mb-3">⚡ Performance</h3>
                <ul className="text-sm text-slate-300 space-y-2">
                  <li>• Nginx ist schneller</li>
                  <li>• Apache ist flexibler</li>
                  <li>• SSL ist wichtig</li>
                  <li>• Let's Encrypt kostenlos</li>
                </ul>
              </div>

              <div className="card bg-gradient-to-br from-blue-900/30 to-blue-900/10 border-blue-500/50">
                <h3 className="text-lg font-bold text-blue-300 mb-3">📝 Nach Installation</h3>
                <ul className="text-sm text-slate-300 space-y-2">
                  <li>✓ Domain konfigurieren</li>
                  <li>✓ SSL-Zertifikat setzen</li>
                  <li>✓ Firewall öffnen</li>
                  <li>✓ Domain DNS zeigen</li>
                </ul>
              </div>

              <div className="card">
                <h3 className="text-lg font-bold text-white mb-3">🔍 URL Beispiele</h3>
                <code className="text-xs bg-slate-800 p-2 rounded block text-slate-300">
                  http://pi.local:8000<br/>
                  https://example.com
                </code>
              </div>
            </div>
          </div>
        )}
      </motion.div>
    </div>
  )
}

export default WebServerSetup
