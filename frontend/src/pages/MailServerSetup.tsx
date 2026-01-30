import React, { useState } from 'react'
import { Mail, AlertCircle, CheckCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import { fetchApi } from '../api'

const MailServerSetup: React.FC = () => {
  const [config, setConfig] = useState({
    enable_mail: false,
    domain: '',
    admin_email: '',
    enable_spam_filter: true,
  })

  const [loading, setLoading] = useState(false)

  const applyConfig = async () => {
    if (!config.domain) {
      toast.error('Domain erforderlich')
      return
    }

    setLoading(true)
    try {
      const response = await fetchApi('/api/mail/configure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      })
      const data = await response.json()
      toast.success('Mailserver wird installiert...')
      console.log(data)
    } catch (error) {
      toast.error('Fehler bei der Installation')
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

  const InputField = ({ label, value, onChange, type = 'text', placeholder = '' }: any) => (
    <div>
      <label className="block text-sm font-semibold text-white mb-2">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-sky-600"
      />
    </div>
  )

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <div className="page-title-category mb-2 inline-flex">
          <h1 className="flex items-center gap-3">
            <Mail className="text-orange-500" />
            Mailserver Konfiguration
          </h1>
        </div>
        <p className="text-slate-400">Installieren Sie einen vollständigen E-Mail-Server (Optional)</p>
      </div>

      <div className="grid lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3 space-y-6">
          {/* Enable Mail Server */}
          <div className="card">
            <h2 className="text-2xl font-bold text-white mb-4">Mailserver aktivieren</h2>
            <CheckboxItem
              label="🔧 Mailserver installieren"
              checked={config.enable_mail}
              onChange={(v) => setConfig({ ...config, enable_mail: v })}
            />
            <p className="text-slate-400 text-sm mt-4">
              Ein Mailserver ermöglicht den Versand und Empfang von E-Mails von Ihrem Raspberry Pi.
            </p>
          </div>

          {/* Configuration (wenn aktiviert) */}
          {config.enable_mail && (
            <>
              <div className="card space-y-4">
                <h2 className="text-2xl font-bold text-white mb-4">Konfiguration</h2>

                <InputField
                  label="📍 Domain Name"
                  value={config.domain}
                  onChange={(v: string) => setConfig({ ...config, domain: v })}
                  placeholder="mail.example.com"
                />

                <InputField
                  label="👤 Administrator E-Mail"
                  value={config.admin_email}
                  onChange={(v: string) => setConfig({ ...config, admin_email: v })}
                  type="email"
                  placeholder="admin@example.com"
                />

                <div className="pt-4 border-t border-slate-600">
                  <CheckboxItem
                    label="🛡️ SpamAssassin Spam-Filter"
                    checked={config.enable_spam_filter}
                    onChange={(v) => setConfig({ ...config, enable_spam_filter: v })}
                  />
                </div>
              </div>

              {/* Mail Components */}
              <div className="card">
                <h3 className="text-xl font-bold text-white mb-4">📧 Mailserver Komponenten</h3>
                <div className="space-y-3">
                  <ComponentItem
                    icon="📤"
                    title="Postfix (SMTP)"
                    desc="Versand von E-Mails"
                    port="25, 587, 465"
                  />
                  <ComponentItem
                    icon="📥"
                    title="Dovecot (IMAP/POP3)"
                    desc="Abruf von E-Mails"
                    port="143, 993, 110, 995"
                  />
                  <ComponentItem
                    icon="🛡️"
                    title="SpamAssassin"
                    desc="Spam & Malware Filter"
                    port="Intern"
                  />
                </div>
              </div>

              {/* DNS Requirements */}
              <div className="card bg-yellow-900/20 border border-yellow-600/50">
                <h3 className="text-lg font-bold text-yellow-300 mb-3 flex items-center gap-2">
                  <AlertCircle size={20} />
                  Wichtige DNS-Einträge erforderlich
                </h3>
                <div className="text-sm text-slate-300 space-y-2 font-mono bg-slate-800/50 p-3 rounded">
                  <p><span className="text-yellow-300">MX</span> mail.example.com</p>
                  <p><span className="text-yellow-300">A</span> mail.example.com [IP]</p>
                  <p><span className="text-yellow-300">SPF</span> v=spf1 mx ~all</p>
                  <p><span className="text-yellow-300">DKIM</span> [Konfigurieren nach Installation]</p>
                  <p><span className="text-yellow-300">DMARC</span> [Empfohlen]</p>
                </div>
              </div>

              {/* TLS/SSL */}
              <div className="card">
                <h3 className="text-xl font-bold text-white mb-4">🔒 TLS/SSL-Zertifikate</h3>
                <p className="text-slate-300 mb-4">
                  Nach der Installation werden kostenlose Let's Encrypt Zertifikate installiert.
                </p>
                <div className="bg-slate-700/50 p-4 rounded space-y-2 text-sm text-slate-300">
                  <p><CheckCircle className="inline mr-2 text-green-500" size={16} />Automatische Erneuerung</p>
                  <p><CheckCircle className="inline mr-2 text-green-500" size={16} />STARTTLS Support</p>
                  <p><CheckCircle className="inline mr-2 text-green-500" size={16} />Sichere Verbindung</p>
                </div>
              </div>

              {/* Action Button */}
              <button
                onClick={applyConfig}
                disabled={loading}
                className="w-full btn-primary text-lg py-3 flex items-center justify-center gap-2"
              >
                {loading ? '⏳ Wird installiert...' : '📧 Mailserver installieren'}
              </button>
            </>
          )}

          {/* Info wenn deaktiviert */}
          {!config.enable_mail && (
            <div className="card bg-slate-700/30 border border-slate-600 p-8 text-center">
              <Mail className="text-slate-500 mx-auto mb-3" size={48} />
              <p className="text-slate-400">
                Aktivieren Sie den Mailserver oben, um ihn zu installieren.
              </p>
            </div>
          )}
        </div>

        {/* Info Panel */}
        <div className="space-y-4">
          <div className="card bg-gradient-to-br from-orange-900/30 to-orange-900/10 border-orange-500/50">
            <h3 className="text-lg font-bold text-orange-300 mb-3">ℹ️ Hinweis</h3>
            <ul className="text-sm text-slate-300 space-y-2">
              <li>• Optional - nicht erforderlich</li>
              <li>• Benötigt öffentliche IP</li>
              <li>• Braucht Domain mit MX-Records</li>
              <li>• ~30 Minuten Installation</li>
            </ul>
          </div>

          <div className="card bg-gradient-to-br from-red-900/30 to-red-900/10 border-red-500/50">
            <h3 className="text-lg font-bold text-red-300 mb-3">⚠️ Anforderungen</h3>
            <ul className="text-sm text-slate-300 space-y-2">
              <li>✓ Statische IP-Adresse</li>
              <li>✓ Reverse DNS Setup</li>
              <li>✓ Port 25 offen</li>
              <li>✓ Domain verfügbar</li>
            </ul>
          </div>

          <div className="card bg-gradient-to-br from-blue-900/30 to-blue-900/10 border-blue-500/50">
            <h3 className="text-lg font-bold text-blue-300 mb-3">📚 Nächste Schritte</h3>
            <ol className="text-sm text-slate-300 space-y-2 list-decimal list-inside">
              <li>Installation abwarten</li>
              <li>DNS-Records setzen</li>
              <li>SSL-Zertifikat prüfen</li>
              <li>Tests durchführen</li>
            </ol>
          </div>

          <div className="card">
            <h3 className="text-lg font-bold text-white mb-3">🔐 Ports</h3>
            <div className="text-xs bg-slate-800 p-2 rounded text-slate-300 space-y-1">
              <p>SMTP: 25, 587, 465</p>
              <p>IMAP: 143, 993</p>
              <p>POP3: 110, 995</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

const ComponentItem = ({ icon, title, desc, port }: any) => (
  <div className="p-4 bg-slate-700/30 rounded-lg flex items-start gap-4 hover:bg-slate-700/50 transition-all">
    <span className="text-2xl">{icon}</span>
    <div className="flex-1">
      <p className="font-semibold text-white">{title}</p>
      <p className="text-sm text-slate-400">{desc}</p>
      <p className="text-xs text-slate-500 mt-1">Port: {port}</p>
    </div>
  </div>
)

export default MailServerSetup
