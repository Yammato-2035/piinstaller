import React, { useState, useEffect } from 'react'
import { BookOpen, Code, Cpu, Zap, Calculator } from 'lucide-react'
import toast from 'react-hot-toast'
import { motion } from 'framer-motion'

const LearningComputerSetup: React.FC = () => {
  const [config, setConfig] = useState({
    enable_scratch: false,
    enable_python_learning: true,
    enable_robotics: false,
    enable_electronics: false,
    enable_math_tools: false,
  })
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState<any>(null)

  useEffect(() => {
    loadStatus()
  }, [])

  const loadStatus = async () => {
    try {
      const response = await fetch('/api/learning/status')
      const data = await response.json()
      setStatus(data)
    } catch (error) {
      console.error('Fehler beim Laden des Status:', error)
    }
  }

  const applyConfig = async () => {
    const sudoPassword = prompt('Sudo-Passwort eingeben (für Installation):')
    if (!sudoPassword) {
      toast.error('Sudo-Passwort erforderlich')
      return
    }

    setLoading(true)
    try {
      const response = await fetch('/api/learning/configure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...config,
          sudo_password: sudoPassword,
        }),
      })
      const data = await response.json()

      if (data.status === 'success') {
        toast.success('Lerncomputer konfiguriert!')
        if (data.results && data.results.length > 0) {
          data.results.forEach((result: string) => {
            toast.success(result, { duration: 3000 })
          })
        }
        loadStatus()
      } else {
        toast.error(data.message || 'Fehler bei der Konfiguration')
      }
    } catch (error) {
      toast.error('Fehler bei der Konfiguration')
    } finally {
      setLoading(false)
    }
  }

  const learningModules = [
    {
      id: 'scratch',
      label: 'Scratch Programmierung',
      icon: Code,
      description: 'Visuelle Programmierung für Anfänger',
      checked: config.enable_scratch,
      onChange: (v: boolean) => setConfig({ ...config, enable_scratch: v }),
      installed: status?.scratch?.installed,
    },
    {
      id: 'python',
      label: 'Python Lernumgebung',
      icon: BookOpen,
      description: 'Interaktive Python-Programmierung mit Jupyter',
      checked: config.enable_python_learning,
      onChange: (v: boolean) => setConfig({ ...config, enable_python_learning: v }),
      installed: status?.python_learning?.installed,
    },
    {
      id: 'robotics',
      label: 'Robotik & GPIO',
      icon: Cpu,
      description: 'Raspberry Pi GPIO, Sensoren, Motoren',
      checked: config.enable_robotics,
      onChange: (v: boolean) => setConfig({ ...config, enable_robotics: v }),
      installed: status?.robotics?.installed,
    },
    {
      id: 'electronics',
      label: 'Elektronik Grundlagen',
      icon: Zap,
      description: 'Fritzing für Schaltungsdesign',
      checked: config.enable_electronics,
      onChange: (v: boolean) => setConfig({ ...config, enable_electronics: v }),
      installed: status?.electronics?.installed,
    },
    {
      id: 'math',
      label: 'Mathematik-Tools',
      icon: Calculator,
      description: 'Geogebra, NumPy, Matplotlib',
      checked: config.enable_math_tools,
      onChange: (v: boolean) => setConfig({ ...config, enable_math_tools: v }),
      installed: false,
    },
  ]

  return (
    <div className="space-y-8 animate-fade-in page-transition">
      <div>
        <h1 className="text-4xl font-bold text-white mb-2 flex items-center gap-3">
          <BookOpen className="text-orange-500" />
          Lerncomputer für Kinder ab 14
        </h1>
        <p className="text-slate-400">
          Einrichtung einer sicheren Lernumgebung mit Programmier-Tools und Tutorials
        </p>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="card">
            <h2 className="text-2xl font-bold text-white mb-6">Lernmodule</h2>
            <div className="space-y-4">
              {learningModules.map((module, index) => {
                const Icon = module.icon
                return (
                  <motion.div
                    key={module.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.3, delay: index * 0.1 }}
                    className={`p-4 rounded-lg border-2 transition-all ${
                      module.checked
                        ? 'bg-sky-600/20 border-sky-500'
                        : 'bg-slate-700/30 border-slate-600'
                    }`}
                  >
                    <label className="flex items-start gap-4 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={module.checked}
                        onChange={(e) => module.onChange(e.target.checked)}
                        className="mt-1 w-5 h-5 accent-sky-600"
                      />
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-1">
                          <Icon className="text-sky-400" size={24} />
                          <h3 className="font-bold text-white">{module.label}</h3>
                          {module.installed && (
                            <span className="px-2 py-1 bg-green-900/50 text-green-300 text-xs rounded-full">
                              ✓ Installiert
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-slate-400">{module.description}</p>
                      </div>
                    </label>
                  </motion.div>
                )
              })}
            </div>

            <div className="mt-8 flex gap-3">
              <button
                onClick={applyConfig}
                disabled={loading}
                className="btn-primary flex-1"
              >
                {loading ? '⏳ Installiere...' : '🚀 Installation starten'}
              </button>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="card bg-gradient-to-br from-orange-900/30 to-orange-900/10 border-orange-500/50">
            <h3 className="text-lg font-bold text-orange-300 mb-3">📚 Lernressourcen</h3>
            <div className="space-y-2 text-sm text-slate-300">
              <a href="https://scratch.mit.edu" target="_blank" rel="noopener noreferrer" className="block hover:text-orange-400 transition-colors">
                → Scratch Online
              </a>
              <a href="https://www.python.org/about/gettingstarted/" target="_blank" rel="noopener noreferrer" className="block hover:text-orange-400 transition-colors">
                → Python Tutorials
              </a>
              <a href="https://gpiozero.readthedocs.io" target="_blank" rel="noopener noreferrer" className="block hover:text-orange-400 transition-colors">
                → GPIO Zero Docs
              </a>
              <a href="https://fritzing.org/learning/" target="_blank" rel="noopener noreferrer" className="block hover:text-orange-400 transition-colors">
                → Fritzing Tutorials
              </a>
            </div>
          </div>

          <div className="card bg-gradient-to-br from-blue-900/30 to-blue-900/10 border-blue-500/50">
            <h3 className="text-lg font-bold text-blue-300 mb-3">💡 Projektideen</h3>
            <ul className="space-y-2 text-sm text-slate-300">
              <li>• LED-Steuerung mit Python</li>
              <li>• Temperatur-Sensor auslesen</li>
              <li>• Einfacher Roboter</li>
              <li>• Home Automation</li>
              <li>• Musik-Player programmieren</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}

export default LearningComputerSetup
