/**
 * Pairing-Seite: Token aus QR eingeben und Claim; oder (am Gerät/Linux) Create und QR-Code anzeigen.
 * Mobile-first. QR-Code-Rendering auf allen Plattformen (Pi, Linux-Desktop).
 */

import React, { useState } from 'react'
import { QRCodeSVG } from 'qrcode.react'
import toast from 'react-hot-toast'
import { useRemoteStore } from '../store/remoteStore'
import * as remoteClient from '../api/remoteClient'

export default function PairPage() {
  const [pairToken, setPairToken] = useState('')
  const [loading, setLoading] = useState(false)
  const [createPayload, setCreatePayload] = useState<remoteClient.PairingCreateResponse | null>(null)
  const setSessionToken = useRemoteStore((s) => s.setSessionToken)

  const handleClaim = async () => {
    const token = pairToken.trim()
    if (!token) {
      toast.error('Bitte Token aus dem QR-Code eingeben')
      return
    }
    setLoading(true)
    try {
      const res = await remoteClient.pairingClaim(token)
      if (res.success && res.session_token) {
        setSessionToken(res.session_token)
        toast.success('Gerät gekoppelt')
        setPairToken('')
      } else {
        toast.error(res.message || 'Kopplung fehlgeschlagen')
      }
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Fehler beim Koppeln')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async () => {
    setLoading(true)
    setCreatePayload(null)
    try {
      const res = await remoteClient.pairingCreate()
      setCreatePayload(res)
      toast.success('QR-Code erstellt – am Smartphone scannen')
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Erstellen fehlgeschlagen')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-4 max-w-md mx-auto space-y-6">
      <h1 className="text-xl font-bold text-slate-800 dark:text-white">Linux Companion koppeln</h1>

      <section className="rounded-xl bg-slate-100 dark:bg-slate-800 p-4">
        <h2 className="text-sm font-medium text-slate-600 dark:text-slate-300 mb-2">Token aus QR-Code</h2>
        <p className="text-xs text-slate-500 dark:text-slate-400 mb-3">
          QR-Code am Linux-Gerät scannen und Token hier eingeben.
        </p>
        <input
          type="text"
          value={pairToken}
          onChange={(e) => setPairToken(e.target.value)}
          placeholder="pair_token aus QR"
          className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400"
          autoComplete="off"
        />
        <button
          type="button"
          onClick={handleClaim}
          disabled={loading}
          className="mt-3 w-full py-2.5 rounded-lg bg-sky-600 text-white font-medium hover:bg-sky-700 disabled:opacity-50"
        >
          {loading ? 'Koppeln…' : 'Koppeln'}
        </button>
      </section>

      <section className="rounded-xl bg-slate-100 dark:bg-slate-800 p-4">
        <h2 className="text-sm font-medium text-slate-600 dark:text-slate-300 mb-2">Neues Pairing (am Linux-Gerät)</h2>
        <p className="text-xs text-slate-500 dark:text-slate-400 mb-3">
          Erzeugt einen neuen QR-Code zum Scannen mit dem Smartphone.
        </p>
        <button
          type="button"
          onClick={handleCreate}
          disabled={loading}
          className="w-full py-2.5 rounded-lg border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-200 font-medium hover:bg-slate-200 dark:hover:bg-slate-700 disabled:opacity-50"
        >
          {loading ? 'Erstellen…' : 'QR-Code erstellen'}
        </button>
        {createPayload != null && (
          <div className="mt-4 flex flex-col items-center gap-3">
            <div className="p-3 rounded-lg bg-white dark:bg-slate-900 inline-flex">
              <QRCodeSVG
                value={JSON.stringify(createPayload.payload)}
                size={200}
                level="M"
                includeMargin={true}
              />
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              QR-Code mit dem Smartphone scannen oder Token manuell eingeben:
            </p>
            <code className="text-xs px-2 py-1 rounded bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 break-all">
              {createPayload.payload.pair_token}
            </code>
          </div>
        )}
      </section>
    </div>
  )
}
