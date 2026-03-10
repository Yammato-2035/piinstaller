import React, { useState, useEffect } from 'react'
import { Code, Package, Database, Terminal } from 'lucide-react'
import toast from 'react-hot-toast'
import { fetchApi } from '../api'
import { usePlatform } from '../context/PlatformContext'

const DevelopmentEnv: React.FC = () => {
  const { pageSubtitleLabel } = usePlatform()
  const [config, setConfig] = useState({
    languages: [] as string[],
    databases: [] as string[],
    tools: [] as string[],
    github_token: '',
  })

  const [loading, setLoading] = useState(false)
  const [devenvStatus, setDevenvStatus] = useState<any>(null)

  useEffect(() => {
    loadDevenvStatus()
  }, [])

  const loadDevenvStatus = async () => {
    try {
      const response = await fetchApi('/api/devenv/status')
      const data = await response.json()
      setDevenvStatus(data)
    } catch (error) {
      console.error('Fehler beim Laden des Dev-Status:', error)
    }
  }

  const languages = [
    { id: 'python', label: '🐍 Python', desc: 'Python 3 + pip', docsLink: 'https://docs.python.org/' },
    { id: 'node', label: '⚡ Node.js', desc: 'Node.js + npm/yarn', docsLink: 'https://nodejs.org/docs/' },
    { id: 'go', label: '🔹 Go', desc: 'Go Programming Language', docsLink: 'https://go.dev/doc/' },
    { id: 'rust', label: '🦀 Rust', desc: 'Rust + Cargo', docsLink: 'https://doc.rust-lang.org/' },
    { id: 'tauri', label: '🖥️ Tauri', desc: 'Tauri 2 – Desktop-Apps (Rust/Web)', docsLink: 'https://v2.tauri.app/' },
    { id: 'c', label: '🔷 C', desc: 'C Compiler (gcc)', docsLink: 'https://gcc.gnu.org/onlinedocs/' },
    { id: 'cpp', label: '🔶 C++', desc: 'C++ Compiler (g++)', docsLink: 'https://gcc.gnu.org/onlinedocs/gcc-13.2.0/gpp/' },
    { id: 'java', label: '☕ Java', desc: 'Java JDK', docsLink: 'https://docs.oracle.com/javase/' },
  ]

  const databases = [
    { id: 'postgres', label: '🐘 PostgreSQL', desc: 'Advanced SQL Database', docsLink: 'https://www.postgresql.org/docs/', adminLink: 'http://localhost:8080/pgadmin' },
    { id: 'mysql', label: '🐬 MySQL/MariaDB', desc: 'Popular SQL Database', docsLink: 'https://mariadb.com/kb/en/documentation/', adminLink: 'http://localhost/phpmyadmin' },
    { id: 'mongodb', label: '🍃 MongoDB', desc: 'NoSQL Document Database', docsLink: 'https://www.mongodb.com/docs/', adminLink: 'http://localhost:8081' },
    { id: 'redis', label: '💾 Redis', desc: 'In-Memory Cache & Queue', docsLink: 'https://redis.io/docs/', adminLink: 'http://localhost:8081' },
  ]

  const tools = [
    { id: 'docker', label: '🐳 Docker', desc: 'Container & Compose', docsLink: 'https://docs.docker.com/' },
    { id: 'git', label: '🔀 Git', desc: 'Version Control', docsLink: 'https://git-scm.com/doc' },
    { id: 'qtqml', label: '🖼️ QT/QML', desc: 'Qt5, QML – GUI-Entwicklung (Desktop/Embedded)', docsLink: 'https://doc.qt.io/qt-5/' },
    { id: 'cursor', label: '🎯 Cursor', desc: 'AI-Powered Code Editor', docsLink: 'https://cursor.sh/docs' },
    { id: 'vscode', label: '📝 VS Code Server', desc: 'Web-Based Editor', docsLink: 'https://code.visualstudio.com/docs' },
  ]

  const toggleItem = (type: 'languages' | 'databases' | 'tools', id: string) => {
    const list = config[type]
    if (list.includes(id)) {
      setConfig({
        ...config,
        [type]: list.filter(item => item !== id),
      })
    } else {
      setConfig({
        ...config,
        [type]: [...list, id],
      })
    }
  }

  const applyConfig = async () => {
    if (config.languages.length === 0 && config.databases.length === 0 && config.tools.length === 0) {
      toast.error('Bitte mindestens eine Option wählen')
      return
    }

    setLoading(true)
    try {
      // AUDIT-FIX (A-01): Endpunkt /api/devenv/configure ist im Backend nicht implementiert.
      // Bis zur Implementierung: Aktion deaktiviert, Nutzer erhält klare Meldung.
      toast.error('Diese Funktion ist derzeit nicht verfügbar. Der Backend-Endpunkt wird noch implementiert.')
    } catch (error) {
      toast.error('Fehler bei der Installation')
    } finally {
      setLoading(false)
    }
  }

  const ItemCard = ({ item, checked, onChange, status }: any) => {
    const isInstalled = status?.installed || false
    const version = status?.version || null
    
    return (
      <div
        className={`p-4 rounded-lg border-2 text-left transition-all ${
          checked
            ? 'bg-sky-600/20 border-sky-500'
            : isInstalled
            ? 'bg-green-900/20 border-green-500'
            : 'bg-slate-700/30 border-slate-600 hover:border-slate-500'
        }`}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <p className="font-bold text-white">{item.label}</p>
              {isInstalled && (
                <span className="px-2 py-0.5 bg-green-900/50 text-green-300 rounded text-xs font-semibold">
                  ✓ Installiert
                </span>
              )}
            </div>
            <p className="text-sm text-slate-400 mt-1">{item.desc}</p>
            {isInstalled && version && (
              <p className="text-xs text-slate-500 mt-1">Version: {version}</p>
            )}
            <div className="flex gap-2 mt-2">
              {item.docsLink && (
                <a
                  href={item.docsLink}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="px-2 py-1 bg-purple-600 hover:bg-purple-700 text-white rounded text-xs transition-colors"
                >
                  📖 Dokumentation
                </a>
              )}
              {isInstalled && item.adminLink && (
                <a
                  href={item.adminLink}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs transition-colors"
                >
                  ⚙️ Admin-Panel
                </a>
              )}
            </div>
          </div>
          {!isInstalled && (
            <button
              onClick={() => onChange(item.id)}
              className={`w-6 h-6 rounded border-2 flex items-center justify-center ${
                checked
                  ? 'bg-sky-600 border-sky-600'
                  : 'border-slate-500'
              }`}
            >
              {checked && <span className="text-white font-bold">✓</span>}
            </button>
          )}
          {isInstalled && (
            <div className="w-6 h-6 rounded border-2 flex items-center justify-center bg-green-600 border-green-600">
              <span className="text-white font-bold">✓</span>
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <div className="page-title-category mb-2 inline-flex">
          <h1 className="flex items-center gap-3">
            <Code className="text-green-500" />
            Entwicklungsumgebung
          </h1>
        </div>
        <p className="text-slate-400">Dev-Umgebung – {pageSubtitleLabel}</p>
      </div>

      <div className="grid lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3 space-y-8">
          {/* Languages */}
          <div className="card">
            <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
              <Terminal size={24} />
              Programmiersprachen
            </h2>
            <div className="grid md:grid-cols-2 gap-4">
              {languages.map((lang) => {
                const statusKey = lang.id === 'python' ? 'python' : lang.id === 'node' ? 'nodejs' : lang.id
                return (
                  <ItemCard
                    key={lang.id}
                    item={lang}
                    checked={config.languages.includes(lang.id)}
                    onChange={() => toggleItem('languages', lang.id)}
                    status={devenvStatus?.[statusKey]}
                  />
                )
              })}
            </div>
          </div>

          {/* Databases */}
          <div className="card">
            <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
              <Database size={24} />
              Datenbanken
            </h2>
            <div className="grid md:grid-cols-2 gap-4">
              {databases.map((db) => {
                const statusKey = db.id === 'postgres' ? 'postgresql' : db.id === 'mysql' ? 'mysql' : db.id
                return (
                  <ItemCard
                    key={db.id}
                    item={db}
                    checked={config.databases.includes(db.id)}
                    onChange={() => toggleItem('databases', db.id)}
                    status={devenvStatus?.[statusKey]}
                  />
                )
              })}
            </div>
          </div>

          {/* Tools */}
          <div className="card">
            <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
              <Package size={24} />
              Entwicklungs-Tools
            </h2>
            <div className="grid md:grid-cols-2 gap-4">
              {tools.map((tool) => {
                let statusKey = tool.id
                if (tool.id === 'vscode') statusKey = 'vscode'
                else if (tool.id === 'cursor') statusKey = 'cursor'
                else if (tool.id === 'qtqml') statusKey = 'qtqml'
                const cursorStatus = tool.id === 'cursor' ? devenvStatus?.cursor : null
                return (
                  <ItemCard
                    key={tool.id}
                    item={tool}
                    checked={config.tools.includes(tool.id)}
                    onChange={() => toggleItem('tools', tool.id)}
                    status={cursorStatus || devenvStatus?.[statusKey]}
                  />
                )
              })}
            </div>
          </div>

          {/* Admin Tools / Konfigurationsoberflächen */}
          <div className="card bg-slate-700/50">
            <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
              <Terminal size={24} />
              Admin-Tools & Konfigurationsoberflächen
            </h2>
            <div className="space-y-3">
              <div className="p-3 bg-slate-800/50 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-semibold text-white">🐘 phpMyAdmin</p>
                    <p className="text-sm text-slate-400">MySQL/MariaDB Web-Interface</p>
                  </div>
                  <div className="flex gap-2">
                    <a
                      href="http://localhost/phpmyadmin"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs transition-colors"
                    >
                      🔗 Öffnen
                    </a>
                    <a
                      href="https://www.phpmyadmin.net/docs/"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-1 bg-purple-600 hover:bg-purple-700 text-white rounded text-xs transition-colors"
                    >
                      📖 Docs
                    </a>
                  </div>
                </div>
              </div>
              
              <div className="p-3 bg-slate-800/50 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-semibold text-white">🐘 pgAdmin</p>
                    <p className="text-sm text-slate-400">PostgreSQL Web-Interface</p>
                  </div>
                  <div className="flex gap-2">
                    <a
                      href="http://localhost:8080/pgadmin"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs transition-colors"
                    >
                      🔗 Öffnen
                    </a>
                    <a
                      href="https://www.pgadmin.org/docs/"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-1 bg-purple-600 hover:bg-purple-700 text-white rounded text-xs transition-colors"
                    >
                      📖 Docs
                    </a>
                  </div>
                </div>
              </div>
              
              <div className="p-3 bg-slate-800/50 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-semibold text-white">🍃 MongoDB Compass / Express</p>
                    <p className="text-sm text-slate-400">MongoDB Web-Interface</p>
                  </div>
                  <div className="flex gap-2">
                    <a
                      href="http://localhost:8081"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs transition-colors"
                    >
                      🔗 Öffnen
                    </a>
                    <a
                      href="https://www.mongodb.com/docs/compass/"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-1 bg-purple-600 hover:bg-purple-700 text-white rounded text-xs transition-colors"
                    >
                      📖 Docs
                    </a>
                  </div>
                </div>
              </div>
              
              <div className="p-3 bg-slate-800/50 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-semibold text-white">💾 Redis Commander (optional)</p>
                    <p className="text-sm text-slate-400">Redis Web-Interface – bei Bedarf separat installieren (z. B. <code className="text-xs bg-slate-700 px-1 rounded">npm install -g redis-commander</code>). Standard-Port 8081.</p>
                  </div>
                  <div className="flex gap-2">
                    <a
                      href="http://localhost:8081"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs transition-colors"
                    >
                      🔗 Öffnen (8081)
                    </a>
                    <a
                      href="https://github.com/joeferner/redis-commander"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-1 bg-purple-600 hover:bg-purple-700 text-white rounded text-xs transition-colors"
                    >
                      📖 Docs
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* GitHub Integration */}
          <div className="card bg-slate-700/50">
            <h3 className="text-xl font-bold text-white mb-4">🔑 GitHub Integration</h3>
            <p className="text-slate-300 mb-3">
              Geben Sie Ihren GitHub Personal Access Token für automatische Authentifizierung ein:
            </p>
            <input
              type="password"
              placeholder="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
              value={config.github_token}
              onChange={(e) => setConfig({ ...config, github_token: e.target.value })}
              className="w-full bg-slate-800 border border-slate-600 rounded px-4 py-2 text-white focus:outline-none focus:border-sky-600 mb-2"
            />
            <p className="text-xs text-slate-400">
              Token wird nicht übertragen und nur lokal gespeichert
            </p>
          </div>

          {/* Install Button */}
          <button
            onClick={applyConfig}
            disabled={loading}
            className="w-full btn-primary text-lg py-3 flex items-center justify-center gap-2"
          >
            {loading ? '⏳ Installiere...' : '🚀 Installation starten'}
          </button>
        </div>

        {/* Info Panel */}
        <div className="space-y-4">
          <div className="card bg-gradient-to-br from-green-900/30 to-green-900/10 border-green-500/50">
            <h3 className="text-lg font-bold text-green-300 mb-3">✨ Features</h3>
            <ul className="text-sm text-slate-300 space-y-2">
              <li>✓ Mehrere Sprachen</li>
              <li>✓ Vorkonfigurierte DBs</li>
              <li>✓ Docker Support</li>
              <li>✓ GitHub Integration</li>
            </ul>
          </div>

          <div className="card bg-gradient-to-br from-blue-900/30 to-blue-900/10 border-blue-500/50">
            <h3 className="text-lg font-bold text-blue-300 mb-3">📚 Dokumentation</h3>
            <div className="text-sm text-slate-300 space-y-2">
              <p>
                Nach der Installation können Sie direkt beginnen:
              </p>
              <code className="text-xs bg-slate-800 p-2 rounded block">
                python3 --version
              </code>
            </div>
          </div>

          <div className="card">
            <h3 className="text-lg font-bold text-white mb-3">💡 Tipps</h3>
            <ul className="text-sm text-slate-300 space-y-2">
              <li>• Python ist vorinstalliert</li>
              <li>• Docker benötigt ~500MB</li>
              <li>• Datenbanken brauchen Speicher</li>
              <li>• Git ist wichtig</li>
            </ul>
          </div>

          <div className="card bg-gradient-to-br from-yellow-900/30 to-yellow-900/10 border-yellow-500/50">
            <h3 className="text-lg font-bold text-yellow-300 mb-3">⚠️ Hinweis</h3>
            <p className="text-sm text-slate-300">
              Die Installation kann 30-60 Minuten dauern, je nach ausgewählten Komponenten.
            </p>
          </div>

          <div className="card">
            <h3 className="text-lg font-bold text-white mb-3">Weitere Sprachen & Tools</h3>
            <p className="text-sm text-slate-300 mb-2">
              Weitere sinnvolle Optionen: Kotlin, Swift (für entsprechende Zielplattformen), Flutter/Dart, .NET (dotnet).
              Fehlende Entwicklungsumgebungen können manuell installiert werden (Snap, Flatpak, direkter Download).
            </p>
            <p className="text-xs text-slate-400">
              QT/QML ist für plattformübergreifende GUIs und Embedded (z. B. Raspberry Pi mit Display) geeignet.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default DevelopmentEnv
