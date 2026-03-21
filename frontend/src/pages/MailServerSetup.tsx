import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Mail, AlertCircle, CheckCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import { fetchApi } from '../api'
import RiskWarningCard from '../components/RiskWarningCard'
import { getPageRisk } from '../config/riskLevels'
import { usePlatform } from '../context/PlatformContext'

const MailServerSetup: React.FC = () => {
  const { t } = useTranslation()
  const { pageSubtitleLabel } = usePlatform()
  const [config, setConfig] = useState({
    enable_mail: false,
    domain: '',
    admin_email: '',
    enable_spam_filter: true,
  })

  const [loading, setLoading] = useState(false)

  const applyConfig = async () => {
    if (!config.domain) {
      toast.error(t('mailServer.toast.domainRequired'))
      return
    }

    setLoading(true)
    try {
      // AUDIT-FIX (A-01): Endpunkt /api/mail/configure ist im Backend nicht implementiert.
      // Bis zur Implementierung: Aktion deaktiviert, Nutzer erhält klare Meldung.
      toast.error(t('mailServer.toast.notAvailable'))
    } catch (error) {
      toast.error(t('mailServer.toast.installError'))
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
            {t('mailServer.pageTitle')}
          </h1>
        </div>
        <p className="text-slate-400">{t('mailServer.pageSubtitle', { label: pageSubtitleLabel })}</p>
      </div>

      {(() => {
        const risk = getPageRisk('mailserver', t)
        return risk?.warningText ? (
          <RiskWarningCard level={risk.level}>{risk.warningText}</RiskWarningCard>
        ) : null
      })()}

      <div className="grid lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3 space-y-6">
          {/* Enable Mail Server */}
          <div className="card">
            <h2 className="text-2xl font-bold text-white mb-4">{t('mailServer.section.enableTitle')}</h2>
            <CheckboxItem
              label={t('mailServer.checkbox.install')}
              checked={config.enable_mail}
              onChange={(v) => setConfig({ ...config, enable_mail: v })}
            />
            <p className="text-slate-400 text-sm mt-4">{t('mailServer.intro')}</p>
          </div>

          {/* Configuration (wenn aktiviert) */}
          {config.enable_mail && (
            <>
              <div className="card space-y-4">
                <h2 className="text-2xl font-bold text-white mb-4">{t('mailServer.config.title')}</h2>

                <InputField
                  label={t('mailServer.field.domain')}
                  value={config.domain}
                  onChange={(v: string) => setConfig({ ...config, domain: v })}
                  placeholder="mail.example.com"
                />

                <InputField
                  label={t('mailServer.field.adminEmail')}
                  value={config.admin_email}
                  onChange={(v: string) => setConfig({ ...config, admin_email: v })}
                  type="email"
                  placeholder="admin@example.com"
                />

                <div className="pt-4 border-t border-slate-600">
                  <CheckboxItem
                    label={t('mailServer.checkbox.spam')}
                    checked={config.enable_spam_filter}
                    onChange={(v) => setConfig({ ...config, enable_spam_filter: v })}
                  />
                </div>
              </div>

              {/* Mail Components */}
              <div className="card">
                <h3 className="text-xl font-bold text-white mb-4">{t('mailServer.components.title')}</h3>
                <div className="space-y-3">
                  <ComponentItem
                    icon="📤"
                    title={t('mailServer.component.postfix.title')}
                    desc={t('mailServer.component.postfix.desc')}
                    port={t('mailServer.component.postfix.ports')}
                  />
                  <ComponentItem
                    icon="📥"
                    title={t('mailServer.component.dovecot.title')}
                    desc={t('mailServer.component.dovecot.desc')}
                    port={t('mailServer.component.dovecot.ports')}
                  />
                  <ComponentItem
                    icon="🛡️"
                    title={t('mailServer.component.spam.title')}
                    desc={t('mailServer.component.spam.desc')}
                    port={t('mailServer.component.spam.ports')}
                  />
                </div>
              </div>

              {/* DNS Requirements */}
              <div className="card bg-yellow-900/20 border border-yellow-600/50">
                <h3 className="text-lg font-bold text-yellow-300 mb-3 flex items-center gap-2">
                  <AlertCircle size={20} />
                  {t('mailServer.dns.title')}
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
                <h3 className="text-xl font-bold text-white mb-4">{t('mailServer.tls.title')}</h3>
                <p className="text-slate-300 mb-4">{t('mailServer.tls.body')}</p>
                <div className="bg-slate-700/50 p-4 rounded space-y-2 text-sm text-slate-300">
                  <p><CheckCircle className="inline mr-2 text-green-500" size={16} />{t('mailServer.tls.autoRenew')}</p>
                  <p><CheckCircle className="inline mr-2 text-green-500" size={16} />{t('mailServer.tls.starttls')}</p>
                  <p><CheckCircle className="inline mr-2 text-green-500" size={16} />{t('mailServer.tls.secure')}</p>
                </div>
              </div>

              {/* Action Button */}
              <button
                onClick={applyConfig}
                disabled={loading}
                className="w-full btn-primary text-lg py-3 flex items-center justify-center gap-2"
              >
                {loading ? t('mailServer.action.installing') : t('mailServer.action.install')}
              </button>
            </>
          )}

          {/* Info wenn deaktiviert */}
          {!config.enable_mail && (
            <div className="card bg-slate-700/30 border border-slate-600 p-8 text-center">
              <Mail className="text-slate-500 mx-auto mb-3" size={48} />
              <p className="text-slate-400">{t('mailServer.disabled.hint')}</p>
            </div>
          )}
        </div>

        {/* Info Panel */}
        <div className="space-y-4">
          <div className="card bg-gradient-to-br from-orange-900/30 to-orange-900/10 border-orange-500/50">
            <h3 className="text-lg font-bold text-orange-300 mb-3">{t('mailServer.panel.hint.title')}</h3>
            <ul className="text-sm text-slate-300 space-y-2">
              <li>{t('mailServer.panel.hint.li1')}</li>
              <li>{t('mailServer.panel.hint.li2')}</li>
              <li>{t('mailServer.panel.hint.li3')}</li>
              <li>{t('mailServer.panel.hint.li4')}</li>
            </ul>
          </div>

          <div className="card bg-gradient-to-br from-red-900/30 to-red-900/10 border-red-500/50">
            <h3 className="text-lg font-bold text-red-300 mb-3">{t('mailServer.panel.req.title')}</h3>
            <ul className="text-sm text-slate-300 space-y-2">
              <li>{t('mailServer.panel.req.li1')}</li>
              <li>{t('mailServer.panel.req.li2')}</li>
              <li>{t('mailServer.panel.req.li3')}</li>
              <li>{t('mailServer.panel.req.li4')}</li>
            </ul>
          </div>

          <div className="card bg-gradient-to-br from-blue-900/30 to-blue-900/10 border-blue-500/50">
            <h3 className="text-lg font-bold text-blue-300 mb-3">{t('mailServer.panel.next.title')}</h3>
            <ol className="text-sm text-slate-300 space-y-2 list-decimal list-inside">
              <li>{t('mailServer.panel.next.li1')}</li>
              <li>{t('mailServer.panel.next.li2')}</li>
              <li>{t('mailServer.panel.next.li3')}</li>
              <li>{t('mailServer.panel.next.li4')}</li>
            </ol>
          </div>

          <div className="card">
            <h3 className="text-lg font-bold text-white mb-3">{t('mailServer.panel.ports.title')}</h3>
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
