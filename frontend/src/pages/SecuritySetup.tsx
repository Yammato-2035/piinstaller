import React, { useState, useEffect } from 'react'
import { Shield, CheckCircle, AlertCircle, Settings } from 'lucide-react'
import toast from 'react-hot-toast'
import { fetchApi } from '../api'

const SecuritySetup: React.FC = () => {
  const [config, setConfig] = useState({
    enable_firewall: true,
    enable_fail2ban: true,
    enable_auto_updates: true,
    enable_ssh_hardening: true,
    enable_audit_logging: true,
    open_ports: '22,80,443',
  })

  const [loading, setLoading] = useState(false)
  const [scanResults, setScanResults] = useState<any>(null)
  const [securityConfig, setSecurityConfig] = useState<any>(null)
  const [installedPackages, setInstalledPackages] = useState<any>(null)
  const [firewallRules, setFirewallRules] = useState<string>('')
  const [showRuleEditor, setShowRuleEditor] = useState(false)
  const [newRule, setNewRule] = useState({ rule: '', direction: 'allow' })

  useEffect(() => {
    loadSecurityStatus()
    loadInstalledPackages()
  }, [])

  const handleChange = (field: string, value: any) => {
    setConfig({
      ...config,
      [field]: value,
    })
  }

  const handlePortsChange = (value: string) => {
    setConfig({
      ...config,
      open_ports: value,
    })
  }

  const loadSecurityStatus = async () => {
    try {
      console.log('🔄 Lade Security-Status...')
      const response = await fetchApi('/api/system/security-config')
      const data = await response.json()
      console.log('📋 Security-Config geladen:', data.config)
      console.log('🔥 UFW Status:', data.config?.ufw)
      
      // Wenn UFW-Status nicht abgerufen werden konnte, versuche aus dem Status-String zu ermitteln
      if (data.config?.ufw) {
        const newUfwStatus = data.config.ufw
        const currentUfwStatus = securityConfig?.ufw
        
        // Prüfe ob der Status-String Hinweise auf "active" enthält, auch wenn active: false ist
        const statusText = newUfwStatus.status || ""
        const hasActiveInStatus = statusText.toLowerCase().includes("active") || 
                                  statusText.toLowerCase().includes("aktiv") ||
                                  statusText.includes("ENABLED=yes") ||
                                  statusText.includes("via systemctl") ||
                                  statusText.includes("wahrscheinlich")
        
        // Wenn der Status-String "active" enthält, aber active: false ist, korrigiere es
        if (hasActiveInStatus && !newUfwStatus.active && newUfwStatus.installed) {
          console.log('⚠️ Status-String zeigt "active", aber active: false. Korrigiere zu active: true')
          setSecurityConfig({
            ...data.config,
            ufw: {
              ...newUfwStatus,
              active: true, // Korrigiere basierend auf Status-String
            }
          })
          return
        }
        
        // Wenn der neue Status "Nicht aktiv" ist, aber der alte Status "active: true" war,
        // und der Status-String leer oder "Nicht aktiv" ist, behalte den alten Status
        if (
          currentUfwStatus?.active === true &&
          newUfwStatus.active === false &&
          (newUfwStatus.status === "Nicht aktiv" || newUfwStatus.status === "" || newUfwStatus.status.includes("Fehler"))
        ) {
          console.log('⚠️ UFW-Status konnte nicht abgerufen werden, behalte alten Status (active: true)')
          // Überschreibe nur den UFW-Status, behalte active: true
          setSecurityConfig({
            ...data.config,
            ufw: {
              ...newUfwStatus,
              active: true, // Behalte den aktiven Status
            }
          })
          return
        }
      }
      
      setSecurityConfig(data.config)
    } catch (error) {
      console.error('Fehler beim Laden der Security-Config:', error)
    }
  }

  const loadFirewallRules = async () => {
    try {
      const response = await fetchApi('/api/security/firewall/rules')
      const data = await response.json()
      if (data.status === 'success') {
        setFirewallRules(data.rules || data.verbose || '')
      }
    } catch (error) {
      console.error('Fehler beim Laden der Firewall-Regeln:', error)
    }
  }

  const addFirewallRule = async () => {
    if (!newRule.rule.trim()) {
      toast.error('Bitte eine Regel eingeben')
      return
    }

    const sudoPassword = prompt('Sudo-Passwort eingeben:')
    if (!sudoPassword) return

    try {
      // Erstelle UFW-Command: allow/deny/reject + Regel
      // z.B. "allow 22/tcp" oder "deny from 192.168.1.0/24"
      const ruleCommand = `${newRule.direction} ${newRule.rule.trim()}`
      const response = await fetchApi('/api/security/firewall/rules/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sudo_password: sudoPassword,
          rule: ruleCommand,
        }),
      })
      const data = await response.json()
      if (data.status === 'success') {
        toast.success('Regel hinzugefügt!')
        setNewRule({ rule: '', direction: 'allow' })
        await loadFirewallRules()
        await loadSecurityStatus()
      } else {
        toast.error(data.message || 'Fehler beim Hinzufügen der Regel')
      }
    } catch (error) {
      toast.error('Fehler beim Hinzufügen der Regel')
    }
  }

  const deleteFirewallRule = async (ruleNumber: number) => {
    if (!confirm(`Regel ${ruleNumber} wirklich löschen?`)) return

    const sudoPassword = prompt('Sudo-Passwort eingeben:')
    if (!sudoPassword) return

    try {
      const response = await fetchApi(`/api/security/firewall/rules/${ruleNumber}`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sudo_password: sudoPassword }),
      })
      const data = await response.json()
      if (data.status === 'success') {
        toast.success('Regel gelöscht!')
        await loadFirewallRules()
        await loadSecurityStatus()
      } else {
        toast.error(data.message || 'Fehler beim Löschen der Regel')
      }
    } catch (error) {
      toast.error('Fehler beim Löschen der Regel')
    }
  }

  const loadInstalledPackages = async () => {
    try {
      const response = await fetchApi('/api/system/installed-packages')
      const data = await response.json()
      setInstalledPackages(data.packages)
    } catch (error) {
      console.error('Fehler beim Laden der Pakete:', error)
    }
  }

  const runSecurityScan = async () => {
    setLoading(true)
    try {
      const response = await fetchApi('/api/security/scan', {
        method: 'POST',
      })
      const data = await response.json()
      setScanResults(data)
      toast.success('Sicherheits-Scan abgeschlossen')
    } catch (error) {
      toast.error('Fehler beim Scan')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const applySecurity = async () => {
    // Prüfe ob sudo-Passwort benötigt wird
    const sudoPassword = prompt('Sudo-Passwort eingeben (für Sicherheitskonfiguration):')
    if (!sudoPassword) {
      toast.error('Sudo-Passwort erforderlich')
      return
    }
    
    setLoading(true)
    try {
      const payload = {
        config: {
          ...config,
          open_ports: config.open_ports.split(',').map(p => parseInt(p.trim())),
          custom_ports: undefined,
        },
        sudo_password: sudoPassword,
      }

      const response = await fetchApi('/api/security/configure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const data = await response.json()
      
      if (data.status === 'success') {
        toast.success('Sicherheitskonfiguration angewendet')
        // Zeige Ergebnisse
        if (data.results && data.results.length > 0) {
          data.results.forEach((result: string) => {
            if (result.includes('⚠️') || result.includes('Fehler')) {
              toast.error(result, { duration: 5000 })
            } else {
              toast.success(result, { duration: 3000 })
            }
          })
        }
        // Lade Status neu
        loadSecurityStatus()
        loadInstalledPackages()
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

  const CheckboxItem = ({ label, checked, onChange }: any) => (
    <label className="flex items-center gap-3 p-4 bg-slate-700/30 rounded-lg hover:bg-slate-700/50 cursor-pointer transition-all">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="w-5 h-5 accent-sky-600"
      />
      <span className="font-medium">{label}</span>
    </label>
  )

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <div className="page-title-category mb-2 inline-flex">
          <h1 className="flex items-center gap-3">
            <Shield className="text-red-500" />
            Sicherheit & Härtung
          </h1>
        </div>
        <p className="text-slate-400">Konfigurieren Sie die Sicherheitseinstellungen für Ihren Raspberry Pi</p>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Configuration Panel */}
        <div className="lg:col-span-2 space-y-6">
          <div className="card">
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
              <Settings size={24} />
              Konfigurationsoptionen
            </h2>

            <div className="space-y-3">
              <CheckboxItem
                label="🔥 Firewall (UFW) aktivieren"
                checked={config.enable_firewall}
                onChange={(v) => handleChange('enable_firewall', v)}
              />
              <CheckboxItem
                label="⚔️ Fail2Ban (Brute-Force Schutz)"
                checked={config.enable_fail2ban}
                onChange={(v) => handleChange('enable_fail2ban', v)}
              />
              <CheckboxItem
                label="🔄 Automatische Sicherheitsupdates"
                checked={config.enable_auto_updates}
                onChange={(v) => handleChange('enable_auto_updates', v)}
              />
              <CheckboxItem
                label="🔐 SSH Härtung"
                checked={config.enable_ssh_hardening}
                onChange={(v) => handleChange('enable_ssh_hardening', v)}
              />
              <CheckboxItem
                label="📝 Audit Logging"
                checked={config.enable_audit_logging}
                onChange={(v) => handleChange('enable_audit_logging', v)}
              />
            </div>

            <div className="mt-8 pt-6 border-t border-slate-600">
              <label className="block mb-2">
                <span className="font-bold text-white">Offene Ports (Komma-getrennt)</span>
                <p className="text-sm text-slate-400 mt-1">z.B.: 22,80,443</p>
              </label>
              <input
                type="text"
                value={config.open_ports}
                onChange={(e) => handlePortsChange(e.target.value)}
                className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-sky-600"
              />
            </div>

            <div className="mt-8 flex gap-3">
              <button
                onClick={runSecurityScan}
                disabled={loading}
                className="btn-secondary flex-1"
              >
                🔍 Scan durchführen
              </button>
              <button
                onClick={applySecurity}
                disabled={loading}
                className="btn-primary flex-1"
              >
                {loading ? '⏳ Wird angewendet...' : '✓ Anwenden'}
              </button>
            </div>
          </div>

          {/* Aktuelle Installationen */}
          {securityConfig && (
            <div className="card bg-slate-700/50">
              <h3 className="text-xl font-bold text-white mb-4">Aktuelle Sicherheitseinstellungen</h3>
              <div className="space-y-3">
                <div className="p-3 bg-slate-800/50 rounded">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold">Fail2Ban</span>
                    {securityConfig.fail2ban?.installed && securityConfig.fail2ban?.running ? (
                      <span className="px-2 py-1 bg-green-900/50 text-green-300 rounded text-xs">
                        ✅ Installiert & Aktiv
                      </span>
                    ) : securityConfig.fail2ban?.installed ? (
                      <span className="px-2 py-1 bg-yellow-900/50 text-yellow-300 rounded text-xs">
                        ⚠️ Installiert (Inaktiv)
                      </span>
                    ) : (
                      <span className="px-2 py-1 bg-red-900/50 text-white rounded text-xs">❌ Nicht installiert</span>
                    )}
                  </div>
                  {securityConfig.fail2ban?.status && securityConfig.fail2ban.status !== "Nicht aktiv" && (
                    <div className="mt-2 text-xs text-slate-400">
                      <p className="font-semibold mb-1">Status:</p>
                      <p className="font-mono">{securityConfig.fail2ban.status.substring(0, 200)}</p>
                    </div>
                  )}
                </div>
                
                <div className="p-3 bg-slate-800/50 rounded">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold">UFW Firewall</span>
                    {securityConfig.ufw?.active ? (
                      <span className="px-2 py-1 bg-green-900/50 text-green-300 rounded text-xs">✅ Aktiv</span>
                    ) : securityConfig.ufw?.installed ? (
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-1 bg-red-900/50 text-white rounded text-xs">❌ Inaktiv</span>
                        <button
                          onClick={async () => {
                            const sudoPassword = prompt('Sudo-Passwort eingeben:')
                            if (sudoPassword) {
                              try {
                                console.log('🚀 Starte Firewall-Aktivierung...')
                                const response = await fetchApi('/api/security/firewall/enable', {
                                  method: 'POST',
                                  headers: { 'Content-Type': 'application/json' },
                                  body: JSON.stringify({ sudo_password: sudoPassword }),
                                })
                                console.log('📡 Response Status:', response.status, response.statusText)
                                
                                const data = await response.json()
                                console.log('📦 Response Data:', data)
                                
                                if (data.status === 'success') {
                                  console.log('✅ Firewall erfolgreich aktiviert!')
                                  console.log('📊 Security Config aus Response:', data.security_config?.ufw)
                                  toast.success('Firewall aktiviert!')
                                  
                                  // Setze Security-Config direkt aus der Response (falls vorhanden)
                                  if (data.security_config) {
                                    console.log('🔄 Setze Security-Config direkt aus Response')
                                    setSecurityConfig(data.security_config)
                                    
                                    // Nur neu laden, wenn UFW in der Response aktiv ist
                                    // (um sicherzustellen, dass der Status korrekt ist)
                                    if (data.security_config.ufw?.active) {
                                      // Warte kurz, dann lade Security-Config neu (um andere Komponenten zu aktualisieren)
                                      setTimeout(async () => {
                                        console.log('🔄 Lade Security-Config nach Verzögerung...')
                                        await loadSecurityStatus()
                                        // Prüfe ob die geladene Config korrekt ist
                                        const response = await fetchApi('/api/system/security-config')
                                        const reloadData = await response.json()
                                        console.log('📋 Neu geladene Security-Config:', reloadData.config?.ufw)
                                        // Wenn die neu geladene Config UFW als aktiv zeigt, verwende sie
                                        if (reloadData.config?.ufw?.active) {
                                          setSecurityConfig(reloadData.config)
                                        }
                                        // Ansonsten behalte die Config aus der Response
                                      }, 1000)
                                    }
                                  }
                                  
                                  // Scan neu ausführen
                                  setTimeout(async () => {
                                    await runSecurityScan()
                                  }, 1000)
                                } else {
                                  console.error('❌ Firewall-Aktivierung fehlgeschlagen!')
                                  console.error('Status:', data.status)
                                  console.error('Message:', data.message)
                                  
                                  // Zeige ALLE Debug-Informationen
                                  if (data.debug) {
                                    console.error('🔍 Debug-Informationen:')
                                    console.error('Full Debug Object:', data.debug)
                                    if (data.debug.command_result) {
                                      console.error('Command Result:', JSON.stringify(data.debug.command_result, null, 2))
                                    }
                                    if (data.debug.status_check) {
                                      console.error('Status Check:', JSON.stringify(data.debug.status_check, null, 2))
                                    }
                                    if (data.debug.status_check_retry) {
                                      console.error('Status Check Retry:', JSON.stringify(data.debug.status_check_retry, null, 2))
                                    }
                                    if (data.debug.retry_result) {
                                      console.error('Retry Result:', JSON.stringify(data.debug.retry_result, null, 2))
                                    }
                                    if (data.debug.ufw_path) {
                                      console.error('UFW Path:', data.debug.ufw_path)
                                    }
                                    if (data.debug.is_active !== undefined) {
                                      console.error('Is Active:', data.debug.is_active)
                                    }
                                  }
                                  
                                  if (data.requires_sudo_password) {
                                    toast.error('Sudo-Passwort erforderlich')
                                  } else if (data.requires_installation) {
                                    toast.error('UFW ist nicht installiert')
                                  } else {
                                    toast.error(data.message || 'Fehler', {
                                      duration: 5000,
                                    })
                                  }
                                }
                              } catch (error) {
                                console.error('💥 Exception beim Aktivieren:', error)
                                toast.error('Fehler beim Aktivieren')
                              }
                            }
                          }}
                          className="px-3 py-1 bg-sky-600 hover:bg-sky-700 text-white rounded text-xs transition-colors"
                        >
                          Aktivieren
                        </button>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-1 bg-red-900/50 text-white rounded text-xs">❌ Nicht installiert</span>
                        <button
                          onClick={async () => {
                            const sudoPassword = prompt('Sudo-Passwort eingeben:')
                            if (sudoPassword) {
                              try {
                                const response = await fetchApi('/api/security/firewall/install', {
                                  method: 'POST',
                                  headers: { 'Content-Type': 'application/json' },
                                  body: JSON.stringify({ sudo_password: sudoPassword }),
                                })
                                const data = await response.json()
                                if (data.status === 'success') {
                                  toast.success('UFW installiert!')
                                  // Security-Config neu laden
                                  await loadSecurityStatus()
                                  // Scan neu ausführen
                                  await runSecurityScan()
                                } else {
                                  if (data.requires_sudo_password) {
                                    toast.error('Sudo-Passwort erforderlich')
                                  } else {
                                    toast.error(data.message || 'Fehler')
                                  }
                                }
                              } catch (error) {
                                toast.error('Fehler beim Installieren')
                              }
                            }
                          }}
                          className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white rounded text-xs transition-colors"
                        >
                          Installieren
                        </button>
                      </div>
                    )}
                  </div>
                  {securityConfig.ufw?.active && securityConfig.ufw?.status && (
                    <div className="mt-2 text-xs text-slate-400">
                      <p className="font-semibold mb-1">Firewall-Status:</p>
                      <div className="space-y-1 max-h-32 overflow-y-auto font-mono bg-slate-900/50 p-2 rounded">
                        {securityConfig.ufw.status.split('\n').slice(0, 10).map((line: string, i: number) => (
                          <div key={i}>{line}</div>
                        ))}
                      </div>
                    </div>
                  )}
                  {securityConfig.ufw?.rules && securityConfig.ufw.rules.length > 0 && (
                    <div className="mt-2 text-xs text-slate-400">
                      <p className="font-semibold mb-1">Firewall-Regeln:</p>
                      <div className="space-y-1 max-h-32 overflow-y-auto font-mono bg-slate-900/50 p-2 rounded">
                        {securityConfig.ufw.rules.slice(0, 10).map((rule: string, i: number) => (
                          <div key={i}>{rule}</div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {securityConfig.ufw?.active && (
                    <div className="mt-3 pt-3 border-t border-slate-700">
                      <button
                        onClick={() => {
                          setShowRuleEditor(!showRuleEditor)
                          if (!showRuleEditor) {
                            loadFirewallRules()
                          }
                        }}
                        className="px-3 py-1.5 bg-sky-600 hover:bg-sky-700 text-white rounded text-xs transition-colors mb-2"
                      >
                        {showRuleEditor ? '🔒 Editor schließen' : '✏️ Regeln bearbeiten'}
                      </button>
                      
                      {showRuleEditor && (
                        <div className="mt-2 space-y-3">
                          <div>
                            <label className="block text-xs text-slate-300 mb-1">Neue Regel hinzufügen:</label>
                            <div className="flex gap-2">
                              <select
                                value={newRule.direction}
                                onChange={(e) => setNewRule({ ...newRule, direction: e.target.value })}
                                className="px-2 py-1 bg-slate-700 text-slate-200 rounded text-xs"
                              >
                                <option value="allow">Allow</option>
                                <option value="deny">Deny</option>
                                <option value="reject">Reject</option>
                              </select>
                              <input
                                type="text"
                                value={newRule.rule}
                                onChange={(e) => setNewRule({ ...newRule, rule: e.target.value })}
                                placeholder="z.B. 22/tcp, 80/tcp, from 192.168.1.0/24"
                                className="flex-1 px-2 py-1 bg-slate-700 text-slate-200 rounded text-xs"
                              />
                              <button
                                onClick={addFirewallRule}
                                className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white rounded text-xs"
                              >
                                Hinzufügen
                              </button>
                            </div>
                            <p className="text-xs text-slate-500 mt-1">
                              Beispiele: <code className="bg-slate-900 px-1 rounded">22/tcp</code>, <code className="bg-slate-900 px-1 rounded">80,443/tcp</code>, <code className="bg-slate-900 px-1 rounded">from 192.168.1.0/24</code>
                            </p>
                          </div>
                          
                          <div>
                            <label className="block text-xs text-slate-300 mb-1">Aktuelle Regeln:</label>
                            <div className="max-h-48 overflow-y-auto font-mono bg-slate-900/50 p-2 rounded text-xs">
                              {firewallRules ? (
                                firewallRules.split('\n').map((line: string, i: number) => {
                                  // Parse Regel-Nummer für Löschen-Button
                                  const match = line.match(/^\[(\d+)\]/)
                                  const ruleNum = match ? parseInt(match[1]) : null
                                  return (
                                    <div key={i} className="flex items-start gap-2 py-1">
                                      <span className="text-slate-400 flex-shrink-0">{line}</span>
                                      {ruleNum !== null && (
                                        <button
                                          onClick={() => deleteFirewallRule(ruleNum)}
                                          className="ml-auto px-2 py-0.5 bg-red-600 hover:bg-red-700 text-white rounded text-xs flex-shrink-0"
                                          title="Regel löschen"
                                        >
                                          🗑️
                                        </button>
                                      )}
                                    </div>
                                  )
                                })
                              ) : (
                                <p className="text-slate-500">Lade Regeln...</p>
                              )}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                <div className="p-3 bg-slate-800/50 rounded">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold">SSH Härtung</span>
                    {securityConfig.ssh_hardening?.enabled ? (
                      <span className="px-2 py-1 bg-green-900/50 text-green-300 rounded text-xs">
                        ✅ Aktiviert
                      </span>
                    ) : (
                      <span className="px-2 py-1 bg-red-900/50 text-white rounded text-xs">❌ Nicht aktiviert</span>
                    )}
                  </div>
                  {securityConfig.ssh_hardening?.checks && securityConfig.ssh_hardening.checks.length > 0 && (
                    <div className="mt-2 text-xs text-slate-400">
                      <p className="font-semibold mb-1">Aktivierte Maßnahmen:</p>
                      <ul className="list-disc list-inside">
                        {securityConfig.ssh_hardening.checks.map((check: string, i: number) => (
                          <li key={i}>{check}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
                
                <div className="p-3 bg-slate-800/50 rounded">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold">Audit Logging</span>
                    {securityConfig.audit_logging?.enabled ? (
                      <span className="px-2 py-1 bg-green-900/50 text-green-300 rounded text-xs">
                        ✅ Aktiviert
                      </span>
                    ) : securityConfig.audit_logging?.installed ? (
                      <span className="px-2 py-1 bg-yellow-900/50 text-yellow-300 rounded text-xs">
                        ⚠️ Installiert (Inaktiv)
                      </span>
                    ) : (
                      <span className="px-2 py-1 bg-red-900/50 text-white rounded text-xs">❌ Nicht installiert</span>
                    )}
                  </div>
                  {securityConfig.audit_logging?.rules_configured && (
                    <div className="mt-2 text-xs text-slate-400">
                      <p className="font-semibold mb-1">Status:</p>
                      <p>Audit-Regeln konfiguriert</p>
                    </div>
                  )}
                </div>
                
                <div className={`p-3 rounded ${
                  !securityConfig.auto_updates?.installed 
                    ? 'bg-red-900/20 border border-red-600/50' 
                    : 'bg-slate-800/50'
                }`}>
                  <div className="flex items-center justify-between mb-2">
                    <span className={`font-semibold ${
                      !securityConfig.auto_updates?.installed ? 'text-white' : 'text-slate-300'
                    }`}>
                      Auto-Updates
                    </span>
                    {securityConfig.auto_updates?.installed && securityConfig.auto_updates?.enabled ? (
                      <span className="px-2 py-1 bg-green-900/50 text-green-300 rounded text-xs">✅ Installiert & Aktiviert</span>
                    ) : securityConfig.auto_updates?.installed ? (
                      <span className="px-2 py-1 bg-yellow-900/50 text-yellow-300 rounded text-xs">⚠️ Installiert (Nicht aktiviert)</span>
                    ) : (
                      <span className="px-2 py-1 bg-red-900/50 text-white rounded text-xs">❌ Nicht installiert</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Scan Results */}
          {scanResults && (
            <div className="card bg-slate-700/50">
              <h3 className="text-xl font-bold text-white mb-4">Scan Ergebnisse</h3>
              <div className="space-y-2">
                {scanResults.fail2ban && (
                  <div className="p-3 bg-slate-800/50 rounded mb-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-semibold">Fail2Ban Status</span>
                      {scanResults.fail2ban.installed ? (
                        <span className="px-2 py-1 bg-green-900/50 text-green-300 rounded text-xs">
                          {scanResults.fail2ban.running ? '✅ Installiert & Aktiv' : '⚠️ Installiert (Inaktiv)'}
                        </span>
                      ) : (
                        <span className="px-2 py-1 bg-red-900/50 text-red-300 rounded text-xs">❌ Nicht installiert</span>
                      )}
                    </div>
                    {scanResults.fail2ban.status && (
                      <p className="text-xs text-slate-400 mt-1">{scanResults.fail2ban.status.substring(0, 150)}...</p>
                    )}
                  </div>
                )}
                
                {scanResults.open_ports && scanResults.open_ports.length > 0 && (
                  <div className="p-3 bg-slate-800/50 rounded mb-3">
                    <span className="font-semibold block mb-2">Offene Ports:</span>
                    <div className="flex flex-wrap gap-2">
                      {scanResults.open_ports.map((port: string, i: number) => (
                        <span key={i} className="px-2 py-1 bg-blue-900/50 text-blue-300 rounded text-xs">{port}</span>
                      ))}
                    </div>
                  </div>
                )}

                {scanResults.closed_ports && scanResults.closed_ports.length > 0 && (
                  <div className="p-3 bg-slate-800/50 rounded mb-3">
                    <span className="font-semibold block mb-2">Geschlossene Ports (UFW):</span>
                    <div className="text-xs text-slate-400 space-y-1">
                      {scanResults.closed_ports.slice(0, 5).map((rule: string, i: number) => (
                        <div key={i}>{rule}</div>
                      ))}
                    </div>
                  </div>
                )}

                {scanResults.updates && scanResults.updates.total > 0 && (
                  <div className="p-3 bg-slate-800/50 rounded mb-3">
                    <span className="font-semibold block mb-2">Verfügbare Updates ({scanResults.updates.total}):</span>
                    <div className="grid grid-cols-4 gap-2 text-xs">
                      {scanResults.updates.categories.security > 0 && (
                        <div className="p-2 bg-red-900/30 border border-red-600/50 rounded">
                          <span className="font-semibold text-red-300">🔒 Sicherheit</span>
                          <p className="text-white mt-1">{scanResults.updates.categories.security}</p>
                        </div>
                      )}
                      {scanResults.updates.categories.critical > 0 && (
                        <div className="p-2 bg-orange-900/30 border border-orange-600/50 rounded">
                          <span className="font-semibold text-orange-300">⚠️ Kritisch</span>
                          <p className="text-white mt-1">{scanResults.updates.categories.critical}</p>
                        </div>
                      )}
                      {scanResults.updates.categories.necessary > 0 && (
                        <div className="p-2 bg-yellow-900/30 border border-yellow-600/50 rounded">
                          <span className="font-semibold text-yellow-300">📦 Notwendig</span>
                          <p className="text-white mt-1">{scanResults.updates.categories.necessary}</p>
                        </div>
                      )}
                      {scanResults.updates.categories.optional > 0 && (
                        <div className="p-2 bg-blue-900/30 border border-blue-600/50 rounded">
                          <span className="font-semibold text-blue-300">📋 Optional</span>
                          <p className="text-white mt-1">{scanResults.updates.categories.optional}</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {Object.entries(scanResults.checks || {}).map(([key, value]: any) => (
                  <div key={key} className={`flex items-center justify-between p-3 rounded ${
                    typeof value === 'object' && value !== null && value.installed === false
                      ? 'bg-red-900/20 border border-red-600/50'
                      : 'bg-slate-800/50'
                  }`}>
                    <span className={`capitalize ${
                      typeof value === 'object' && value !== null && value.installed === false
                        ? 'text-white font-semibold'
                        : 'text-slate-300'
                    }`}>
                      {key.replace(/_/g, ' ')}
                    </span>
                    {typeof value === 'object' && value !== null ? (
                      <div className="flex items-center gap-2">
                        {value.installed !== undefined && (
                          <span className={`px-2 py-1 rounded text-xs ${
                            value.installed 
                              ? 'bg-green-900/50 text-green-300' 
                              : 'bg-red-900/50 text-white'
                          }`}>
                            {value.installed ? 'Installiert' : 'Nicht installiert'}
                          </span>
                        )}
                        {value.running !== undefined && (
                          <span className={`px-2 py-1 rounded text-xs ${
                            value.running ? 'bg-green-900/50 text-green-300' : 'bg-yellow-900/50 text-yellow-300'
                          }`}>
                            {value.running ? 'Läuft' : 'Stoppt'}
                          </span>
                        )}
                        {value.active !== undefined && (
                          <span className={`px-2 py-1 rounded text-xs ${
                            value.active ? 'bg-green-900/50 text-green-300' : 'bg-yellow-900/50 text-yellow-300'
                          }`}>
                            {value.active ? 'Aktiv' : 'Inaktiv'}
                          </span>
                        )}
                      </div>
                    ) : (
                      value ? (
                        <CheckCircle className="text-green-500" size={20} />
                      ) : (
                        <AlertCircle className="text-yellow-500" size={20} />
                      )
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Info Panel */}
        <div className="space-y-4">
          <div className="card bg-gradient-to-br from-red-900/30 to-red-900/10 border-red-500/50">
            <h3 className="text-lg font-bold text-red-300 mb-3 flex items-center gap-2">
              <AlertCircle size={20} />
              Wichtig
            </h3>
            <ul className="text-sm text-slate-300 space-y-2">
              <li>• Sicherungsoptionen sind standard empfohlen</li>
              <li>• SSH-Schlüssel sind sicherer als Passwörter</li>
              <li>• Firewall blockiert alle Eingänge außer offenen Ports</li>
              <li>• Updates werden automatisch nachts ausgeführt</li>
            </ul>
          </div>

          <div className="card bg-gradient-to-br from-sky-900/30 to-sky-900/10 border-sky-500/50">
            <h3 className="text-lg font-bold text-sky-300 mb-3">Empfohlene Einstellungen</h3>
            <ul className="text-sm text-slate-300 space-y-2">
              <li>✓ Alle Optionen aktivieren</li>
              <li>✓ Standard Ports (22, 80, 443)</li>
              <li>✓ Nur notwendige Ports öffnen</li>
              <li>✓ Regelmäßige Sicherheit-Scans</li>
            </ul>
          </div>

          <div className="card">
            <h3 className="text-lg font-bold text-white mb-3">Port-Referenz</h3>
            <div className="text-sm text-slate-300 space-y-1">
              <p><span className="font-semibold">22</span> - SSH</p>
              <p><span className="font-semibold">80</span> - HTTP</p>
              <p><span className="font-semibold">443</span> - HTTPS</p>
              <p><span className="font-semibold">3306</span> - MySQL</p>
              <p><span className="font-semibold">5432</span> - PostgreSQL</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SecuritySetup
