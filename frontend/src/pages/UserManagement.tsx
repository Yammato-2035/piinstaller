import React, { useState, useEffect } from 'react'
import { Users, Plus, Trash2, Lock, Settings } from 'lucide-react'
import toast from 'react-hot-toast'
import { fetchApi } from '../api'

const UserManagement: React.FC = () => {
  const [users, setUsers] = useState<string[]>([])
  const [showNewUserForm, setShowNewUserForm] = useState(false)
  const [loading, setLoading] = useState(false)
  const [newUser, setNewUser] = useState({
    username: '',
    email: '',
    role: 'user',
    create_ssh_key: false,
    password: '',
    sudo_password: '',
  })
  const [requiresSudoPassword, setRequiresSudoPassword] = useState(false)
  const [sudoPasswordSaved, setSudoPasswordSaved] = useState(false)
  const [sudoSkipTest, setSudoSkipTest] = useState(false)

  // Prüfe ob sudo-Passwort bereits gespeichert ist
  useEffect(() => {
    const saved = sessionStorage.getItem('sudo_password_saved')
    if (saved === 'true') {
      setSudoPasswordSaved(true)
    }
  }, [])

  useEffect(() => {
    loadUsers()
  }, [])

  const loadUsers = async () => {
    try {
      const response = await fetchApi('/api/users')
      const data = await response.json()
      // Sortiere Benutzer alphabetisch
      const sortedUsers = (data.users || []).sort((a: string, b: string) => 
        a.localeCompare(b, 'de', { sensitivity: 'base' })
      )
      setUsers(sortedUsers)
    } catch (error) {
      toast.error('Fehler beim Laden der Benutzer')
    }
  }

  const saveSudoPassword = async (forceSkipTest = false) => {
    if (!newUser.sudo_password) {
      toast.error('Bitte geben Sie das sudo-Passwort ein')
      return
    }

    setLoading(true)
    try {
      const response = await fetchApi('/api/users/sudo-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sudo_password: newUser.sudo_password,
          skip_test: forceSkipTest || sudoSkipTest,
        }),
      })
      let data: { status?: string; message?: string; detail?: string } = {}
      try {
        data = await response.json()
      } catch {
        toast.error('Ungültige Antwort vom Backend. Läuft es auf Port 8000?')
        return
      }
      if (data.status === 'success') {
        toast.success('Sudo-Passwort für diese Session gespeichert')
        setSudoPasswordSaved(true)
        sessionStorage.setItem('sudo_password_saved', 'true')
        setRequiresSudoPassword(false)
      } else {
        toast.error(data.message || data.detail || 'Sudo-Passwort konnte nicht gespeichert werden.')
      }
    } catch (error) {
      toast.error('Fehler beim Speichern – Backend erreichbar? (Port 8000)')
      console.error('saveSudoPassword:', error)
    } finally {
      setLoading(false)
    }
  }

  const createUser = async () => {
    if (!newUser.username) {
      toast.error('Benutzername erforderlich')
      return
    }

    if (requiresSudoPassword && !newUser.sudo_password) {
      toast.error('Sudo-Passwort erforderlich')
      return
    }

    setLoading(true)
    try {
      const response = await fetchApi('/api/users/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newUser),
      })
      const data = await response.json()
      
      if (data.status === 'success') {
        toast.success(`Benutzer ${newUser.username} erstellt`)
        // Sudo-Passwort für Session speichern (Passwort bereits durch Erstellung validiert)
        if (newUser.sudo_password) {
          await saveSudoPassword(true)
        }
        setNewUser({ username: '', email: '', role: 'user', create_ssh_key: false, password: '', sudo_password: '' })
        setRequiresSudoPassword(false)
        setShowNewUserForm(false)
        loadUsers()
      } else {
        if (data.requires_sudo_password) {
          setRequiresSudoPassword(true)
          toast.error('Sudo-Passwort erforderlich')
        } else {
          toast.error(data.message || 'Fehler bei der Erstellung')
        }
      }
    } catch (error) {
      toast.error('Fehler bei der Erstellung')
    } finally {
      setLoading(false)
    }
  }

  const deleteUser = async (username: string) => {
    if (!window.confirm(`Möchten Sie ${username} wirklich löschen?`)) return

    // Prüfe ob sudo-Passwort gespeichert ist
    const savedPassword = sessionStorage.getItem('sudo_password_saved')
    let sudoPassword = ''
    
    if (savedPassword !== 'true') {
      sudoPassword = prompt('Sudo-Passwort eingeben:')
      if (!sudoPassword) {
        toast.error('Sudo-Passwort erforderlich')
        return
      }
    } else {
      // Verwende gespeichertes Passwort aus dem State
      sudoPassword = newUser.sudo_password || ''
      if (!sudoPassword) {
        sudoPassword = prompt('Sudo-Passwort eingeben:')
        if (!sudoPassword) {
          toast.error('Sudo-Passwort erforderlich')
          return
        }
      }
    }

    setLoading(true)
    try {
      const response = await fetchApi(`/api/users/${username}`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sudo_password: sudoPassword }),
      })
      const data = await response.json()
      
      if (data.status === 'success') {
        toast.success(`Benutzer ${username} gelöscht`)
        loadUsers()
      } else {
        if (data.requires_sudo_password) {
          toast.error('Sudo-Passwort erforderlich')
        } else {
          toast.error(data.message || 'Fehler beim Löschen')
        }
      }
    } catch (error) {
      toast.error('Fehler beim Löschen')
    } finally {
      setLoading(false)
    }
  }

  const getRoleColor = (role: string) => {
    const colors: any = {
      'admin': 'bg-red-900/50 text-red-300',
      'developer': 'bg-blue-900/50 text-blue-300',
      'user': 'bg-slate-700 text-slate-300',
    }
    return colors[role] || colors['user']
  }

  const getRoleLabel = (role: string) => {
    const labels: any = {
      'admin': '👑 Administrator',
      'developer': '👨‍💻 Entwickler',
      'user': '👤 Benutzer',
    }
    return labels[role] || role
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="text-4xl font-bold text-white mb-2 flex items-center gap-3">
          <Users className="text-blue-500" />
          Benutzerverwaltung
        </h1>
        <p className="text-slate-400">Verwalten Sie Systembenutzer und deren Rollen</p>
      </div>

      <div className="grid lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3 space-y-6">
          {/* Users List */}
          <div className="card">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-white">Systembenutzer</h2>
              <button
                onClick={() => setShowNewUserForm(!showNewUserForm)}
                className="btn-primary flex items-center gap-2"
              >
                <Plus size={20} />
                Neuer Benutzer
              </button>
            </div>

            {/* New User Form */}
            {showNewUserForm && (
              <div className="mb-6 p-4 bg-slate-700/50 rounded-lg border border-slate-600 space-y-4">
                <div className="grid md:grid-cols-2 gap-4">
                  <input
                    type="text"
                    placeholder="Benutzername"
                    value={newUser.username}
                    onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                    className="bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white focus:outline-none focus:border-sky-600"
                  />
                  <input
                    type="email"
                    placeholder="E-Mail (optional)"
                    value={newUser.email}
                    onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                    className="bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white focus:outline-none focus:border-sky-600"
                  />
                </div>

                <div className="grid md:grid-cols-2 gap-4">
                  <select
                    value={newUser.role}
                    onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                    className="bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white focus:outline-none focus:border-sky-600"
                  >
                    <option value="user">👤 Benutzer</option>
                    <option value="developer">👨‍💻 Entwickler</option>
                    <option value="admin">👑 Administrator</option>
                  </select>

                  <input
                    type="password"
                    placeholder="Passwort (optional, wird generiert)"
                    value={newUser.password}
                    onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                    className="bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white focus:outline-none focus:border-sky-600"
                  />
                </div>

                {(requiresSudoPassword || !sudoPasswordSaved) && (
                  <div className="p-3 bg-yellow-900/30 border border-yellow-600/50 rounded-lg">
                    <label className="block text-yellow-300 font-semibold mb-2">
                      🔐 Sudo-Passwort {sudoPasswordSaved ? 'gespeichert' : 'erforderlich'}
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="password"
                        placeholder="Ihr sudo-Passwort eingeben"
                        value={newUser.sudo_password}
                        onChange={(e) => setNewUser({ ...newUser, sudo_password: e.target.value })}
                        className="flex-1 bg-slate-800 border border-yellow-600 rounded px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                      />
                      {!sudoPasswordSaved && (
                        <button
                          onClick={saveSudoPassword}
                          disabled={loading || !newUser.sudo_password}
                          className="btn-secondary whitespace-nowrap"
                        >
                          Für Session speichern
                        </button>
                      )}
                    </div>
                    <p className="text-xs text-yellow-400 mt-1">
                      {sudoPasswordSaved 
                        ? '✅ Passwort für diese Session gespeichert - Sie müssen es nicht erneut eingeben'
                        : 'Das Passwort wird nur für diese Session gespeichert und nicht dauerhaft gesichert.'}
                    </p>
                    {!sudoPasswordSaved && (
                      <label className="mt-2 flex items-center gap-2 cursor-pointer text-yellow-400/90 text-xs">
                        <input
                          type="checkbox"
                          checked={sudoSkipTest}
                          onChange={(e) => setSudoSkipTest(e.target.checked)}
                          className="rounded border-yellow-600 bg-slate-800"
                        />
                        Ohne Prüfung speichern (Standard; beim ersten Einsatz wird geprüft)
                      </label>
                    )}
                  </div>
                )}

                <label className="flex items-center gap-2 text-slate-300">
                  <input
                    type="checkbox"
                    checked={newUser.create_ssh_key}
                    onChange={(e) => setNewUser({ ...newUser, create_ssh_key: e.target.checked })}
                    className="w-4 h-4 accent-sky-600"
                  />
                  SSH-Schlüsselpaar generieren
                </label>

                <div className="flex gap-2">
                  <button
                    onClick={createUser}
                    disabled={loading}
                    className="btn-primary flex-1"
                  >
                    {loading ? '⏳ Erstelle...' : '✓ Erstellen'}
                  </button>
                  <button
                    onClick={() => setShowNewUserForm(false)}
                    className="btn-secondary flex-1"
                  >
                    Abbrechen
                  </button>
                </div>
              </div>
            )}

            {/* Users Table */}
            <div className="space-y-2">
              {users
                .filter(u => !['root', 'sync', 'bin', 'sys', 'daemon', 'mail', 'www-data', 'backup', 'list', 'irc', 'gnats', 'syslog', 'messagebus'].includes(u))
                .sort((a, b) => a.localeCompare(b, 'de', { sensitivity: 'base' }))
                .map((user) => (
                <div
                  key={user}
                  className="p-4 bg-slate-700/30 rounded-lg hover:bg-slate-700/50 flex items-center justify-between transition-all group"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-gradient-to-br from-sky-400 to-sky-600 rounded-full flex items-center justify-center text-white font-bold">
                      {user.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <p className="font-semibold text-white">{user}</p>
                      <p className="text-xs text-slate-400">/home/{user}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button className="p-2 hover:bg-slate-600 rounded transition-all">
                      <Settings size={18} className="text-slate-300" />
                    </button>
                    {user !== 'root' && (
                      <button
                        onClick={() => deleteUser(user)}
                        className="p-2 hover:bg-red-600/50 rounded transition-all"
                      >
                        <Trash2 size={18} className="text-red-400" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {users.length === 0 && (
              <div className="text-center py-8 text-slate-400">
                Keine Benutzer gefunden
              </div>
            )}
          </div>
        </div>

        {/* Info Panel */}
        <div className="space-y-4">
          <div className="card bg-gradient-to-br from-blue-900/30 to-blue-900/10 border-blue-500/50">
            <h3 className="text-lg font-bold text-blue-300 mb-3">Rollen</h3>
            <div className="space-y-3">
              <div>
                <p className="font-semibold text-white">👑 Administrator</p>
                <p className="text-xs text-slate-400">Volle Kontrolle, sudo Zugriff</p>
              </div>
              <div>
                <p className="font-semibold text-white">👨‍💻 Entwickler</p>
                <p className="text-xs text-slate-400">Zugriff auf Dev-Tools</p>
              </div>
              <div>
                <p className="font-semibold text-white">👤 Benutzer</p>
                <p className="text-xs text-slate-400">Begrenzte Rechte</p>
              </div>
            </div>
          </div>

          <div className="card bg-gradient-to-br from-green-900/30 to-green-900/10 border-green-500/50">
            <h3 className="text-lg font-bold text-green-300 mb-3">SSH-Schlüssel</h3>
            <p className="text-sm text-slate-300 mb-3">
              Generieren Sie SSH-Schlüsselpaare für sichere Authentifizierung ohne Passwort.
            </p>
            <button className="w-full btn-secondary text-sm">
              🔐 Schlüssel verwalten
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default UserManagement
