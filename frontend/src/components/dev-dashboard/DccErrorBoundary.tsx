import React, { Component, type ErrorInfo, type ReactNode } from 'react'
import type { DccBootClassification, DccBootProbeResult } from '../../lib/devDashboard/dccBootState'
import { DccBootDiagnosticsPanel } from './DccBootDiagnosticsPanel'

type Props = {
  children: ReactNode
  probe: DccBootProbeResult | null
  baseClassification: DccBootClassification
  onRetry: () => void
}

type State = {
  error: Error | null
  componentStack: string | null
}

export class DccErrorBoundary extends Component<Props, State> {
  state: State = { error: null, componentStack: null }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('[DccErrorBoundary]', error, errorInfo)
    this.setState({ componentStack: errorInfo.componentStack ?? null })
  }

  render() {
    const { error, componentStack } = this.state
    const { children, probe, baseClassification, onRetry } = this.props

    if (error) {
      const classification: DccBootClassification = {
        state: 'frontend_runtime_error',
        shouldShowDcc: false,
        dccExpectedVisible: baseClassification.dccExpectedVisible,
        reason: error.message,
      }
      return (
        <div className="min-h-screen bg-slate-950 text-slate-100" data-testid="dcc-error-boundary">
          <DccBootDiagnosticsPanel
            classification={classification}
            probe={probe}
            onRetry={onRetry}
            runtimeError={{ message: error.message, componentStack }}
          />
          <div className="max-w-lg mx-auto p-8 text-center text-sm text-slate-400">
            <p>
              React-Renderfehler im Cockpit. Kein automatischer Reload. Nutzen Sie „DCC-Status erneut prüfen“ (nur
              Fetch).
            </p>
          </div>
        </div>
      )
    }

    return children
  }
}
