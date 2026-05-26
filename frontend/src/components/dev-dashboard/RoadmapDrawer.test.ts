import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { RoadmapDrawer } from './RoadmapDrawer'

const messages: Record<string, string> = {
  'devDashboard.roadmap.title': 'Roadmap',
  'devDashboard.roadmap.subtitle': 'Belastbare Meilensteine, Blocker, Evidence und der nächste sinnvolle Prompt.',
  'devDashboard.roadmap.runtimeOverlay': 'Runtime-Overlay',
  'devDashboard.roadmap.overallStatus': 'Gesamtstatus',
  'devDashboard.roadmap.greenCount': 'Green',
  'devDashboard.roadmap.partialGreenCount': 'Partial green',
  'devDashboard.roadmap.blockedCount': 'Blocked',
  'devDashboard.roadmap.deferredCount': 'Deferred',
  'devDashboard.roadmap.recommendedPrompt': 'Empfohlener nächster Prompt',
  'devDashboard.roadmap.restoreDeferredTitle': 'Restore zurückgestellt',
  'devDashboard.roadmap.diagnosticsPartialTitle': 'Diagnostik teilweise vorhanden',
  'devDashboard.roadmap.diagnosticsProgressTitle': 'Diagnostics-Fortschritt',
  'devDashboard.roadmap.diagnosticsProgressSubtitle': 'Teilbereiche, gelernte Fehler und Evidence für die reproduzierbare Teststrecke.',
  'devDashboard.roadmap.nextTestFocus': 'Nächster Testfokus',
  'devDashboard.roadmap.learnedDiagnostics': 'Gelernte Diagnosecodes',
  'devDashboard.roadmap.diagnosticsProgress.catalog_status': 'Katalog',
  'devDashboard.roadmap.diagnosticsProgress.matcher_status': 'Matcher',
  'devDashboard.roadmap.diagnosticsProgress.api_status': 'API',
  'devDashboard.roadmap.diagnosticsProgress.ui_status': 'UI',
  'devDashboard.roadmap.diagnosticsProgress.evidence_status': 'Evidence',
  'devDashboard.roadmap.diagnosticsProgress.test_track_status': 'Teststrecke',
  'devDashboard.roadmap.diagnosticsProgress.rescue_build_diagnostics_status': 'Rescue Build Diagnostics',
  'devDashboard.roadmap.diagnosticsProgress.backup_diagnostics_status': 'Backup Diagnostics',
  'devDashboard.roadmap.diagnosticsProgress.restore_diagnostics_status': 'Restore Diagnostics',
  'devDashboard.roadmap.diagnosticsProgress.runtime_diagnostics_status': 'Runtime / Deploy Diagnostics',
  'devDashboard.roadmap.diagnosticsProgress.notification_diagnostics_status': 'Notification Diagnostics',
  'devDashboard.roadmap.diagnosticsProgress.architecture_diagnostics_status': 'Architecture Diagnostics',
  'devDashboard.roadmap.showPrompt': 'Prompt anzeigen',
  'devDashboard.roadmap.copyPrompt': 'Prompt kopieren',
  'devDashboard.roadmap.exportPrompt': 'Prompt als Text exportieren',
  'devDashboard.roadmap.unlocks': 'Schaltet frei',
  'devDashboard.roadmap.blockers': 'Blocker',
  'devDashboard.roadmap.notBlocked': 'Aktuell nicht blockiert',
  'devDashboard.roadmap.copyPromptSuccess': 'Prompt kopiert',
  'devDashboard.roadmap.exportPromptSuccess': 'Prompt exportiert',
  'devDashboard.roadmap.columnItem': 'Bereich / Meilenstein / Aufgabe',
  'devDashboard.roadmap.columnStatus': 'Status',
  'devDashboard.roadmap.columnProgress': 'Fortschritt',
  'devDashboard.roadmap.columnEvidenceLevel': 'Evidence-Level',
  'devDashboard.roadmap.columnBlockers': 'Blocker',
  'devDashboard.roadmap.columnNextStep': 'Nächster Schritt',
  'devDashboard.roadmap.columnPlannedRange': 'Geplanter Zeitraum',
  'devDashboard.roadmap.columnCompletedAt': 'Erledigt am',
  'devDashboard.roadmap.reasonTitle': 'Begründung',
  'devDashboard.roadmap.decisions': 'Entscheidungen',
  'devDashboard.roadmap.notes': 'Notizen',
  'devDashboard.roadmap.evidence': 'Evidence',
  'devDashboard.roadmap.linkedNextPrompt': 'Verknüpfter Next Prompt',
  'devDashboard.roadmap.noLinkedPrompt': 'Kein verknüpfter Prompt',
  'devDashboard.roadmap.none': 'Keine',
  'devDashboard.noData': 'Keine Daten',
  'devDashboard.standalone.unavailable': 'UNAVAILABLE',
}

const t = (key: string) => messages[key] || key

const dashboard = {
  roadmap: {
    summary: {
      overall_status: 'yellow',
      status_counts: {
        green: 0,
        partial_green: 2,
        blocked: 1,
        red: 0,
        deferred: 1,
      },
    },
    runtime_overlay: {
      runtime_gate_status: 'green',
    },
    recommended_prompt: {
      id: 'DIAGNOSTICS_TEST_TRACK',
      title_de: 'Diagnostics Evidence Test Track',
      reason_de: 'Diagnostik braucht echte Fehlerfälle, UI-Auswertung und Evidence.',
      blocked_by: [],
      unlocks: ['Diagnostik-Evidence', 'Bessere Prompt-Auswahl'],
      prompt_text: 'STRICT MODE – Diagnostics',
    },
    next_prompts: [
      {
        id: 'DIAGNOSTICS_TEST_TRACK',
        title_de: 'Diagnostics Evidence Test Track',
      },
    ],
    areas: [
      {
        id: 'restore',
        title_de: 'Restore',
        description_de: 'Restore bleibt bis zu sicherem Rettungsmedium und Testziel zurückgestellt.',
        status: 'deferred',
        evidence_level: 'planning_only',
        next_recommended_action: 'Nicht-produktives Testziel definieren.',
        decisions: [
          {
            id: 'restore-e2e-deferred',
            decision_de: 'Zurückgestellt, weil kein bootfähiges Rettungsmedium und kein nicht-produktives Zielsystem verfügbar waren.',
          },
        ],
        blockers: [],
        notes: [],
        authoritative_evidence: ['docs/evidence/runtime-results/rescue/rescue_build_next_steps_matrix_latest.json'],
        next_prompt_id: 'RESTORE_E2E_PREPARATION',
        milestones: [
          {
            id: 'restore-m1',
            title_de: 'Restore-E2E sicher vorbereiten',
            status: 'deferred',
            progress_percent: 10,
            tasks: [
              {
                id: 'restore-t1',
                title_de: 'Bootfähiges Rettungsmedium bereitstellen',
                status: 'deferred',
                progress_percent: 0,
                blocker_refs: [],
                evidence_links: [],
                next_action_de: 'Nur vorbereiten, nicht ausführen.',
              },
            ],
          },
        ],
      },
      {
        id: 'diagnostics',
        title_de: 'Diagnostics',
        description_de: 'Teilweise vorhanden, aber echte Fehlerfall-Teststrecke, UI-Auswertung und Evidence-Matrix fehlen.',
        status: 'partial_green',
        evidence_level: 'unit_tested',
        next_recommended_action: 'Fehlerfälle und UI-Evidence ergänzen.',
        decisions: [
          {
            id: 'diag-d1',
            decision_de: 'Teilweise vorhanden, aber echte Fehlerfall-Teststrecke, UI-Auswertung und Evidence-Matrix fehlen.',
          },
        ],
        blockers: [],
        notes: [],
        authoritative_evidence: ['docs/evidence/runtime-results/rescue/rescue_build_diagnostics_mapping_latest.json'],
        next_prompt_id: 'DIAGNOSTICS_TEST_TRACK',
        diagnostics_progress: {
          catalog_status: 'partial_green',
          matcher_status: 'partial_green',
          api_status: 'partial_green',
          ui_status: 'partial_green',
          evidence_status: 'partial_green',
          test_track_status: 'partial_green',
          rescue_build_diagnostics_status: 'partial_green',
          backup_diagnostics_status: 'yellow',
          restore_diagnostics_status: 'deferred',
          runtime_diagnostics_status: 'yellow',
          notification_diagnostics_status: 'partial_green',
          architecture_diagnostics_status: 'partial_green',
          learned_error_codes: ['RESCUE-BUILD-ROOT-001', 'NOTIFICATION-EMAIL-PROVIDER-001'],
          next_test_focus: 'RESCUE_ISO_MANUAL_OPERATOR_TERMINAL_BUILD',
          evidence_files: [
            'docs/evidence/diagnostics/DIAGNOSTICS_TEST_TRACK_LATEST.json',
            'docs/evidence/diagnostics/DIAGNOSTICS_UI_EVALUATION_LATEST.json',
          ],
        },
        milestones: [],
      },
      {
        id: 'future-test-tracks',
        title_de: 'Future Test Tracks',
        description_de: 'Zukünftige Teststrecken bleiben sichtbar.',
        status: 'yellow',
        evidence_level: 'planning_only',
        next_recommended_action: 'Tracks priorisieren.',
        decisions: [],
        blockers: [],
        notes: [],
        authoritative_evidence: ['docs/testing/HARDWARE_TEST_MATRIX.md'],
        next_prompt_id: 'DIAGNOSTICS_TEST_TRACK',
        milestones: [
          {
            id: 'future-m1',
            title_de: 'Tracks',
            status: 'yellow',
            progress_percent: 30,
            tasks: [
              {
                id: 'track-pi5',
                title_de: 'Raspberry Pi 5',
                status: 'yellow',
                progress_percent: 20,
                blocker_refs: [],
                evidence_links: [],
                next_action_de: 'Track sichtbar halten.',
              },
            ],
          },
        ],
      },
    ],
  },
}

describe('RoadmapDrawer', () => {
  it('renders roadmap registry panel and next prompt card', () => {
    const html = renderToStaticMarkup(React.createElement(RoadmapDrawer, { dashboard, t, apiReachable: false }))
    expect(html).toContain('data-testid="dev-dashboard-roadmap-panel"')
    expect(html).toContain('Empfohlener nächster Prompt')
    expect(html).toContain('Prompt anzeigen')
    expect(html).toContain('Prompt kopieren')
    expect(html).toContain('Prompt als Text exportieren')
  })

  it('shows restore and diagnostics hints', () => {
    const html = renderToStaticMarkup(React.createElement(RoadmapDrawer, { dashboard, t, apiReachable: false }))
    expect(html).toContain('Restore zurückgestellt')
    expect(html).toContain('kein bootfähiges Rettungsmedium')
    expect(html).toContain('Diagnostik teilweise vorhanden')
    expect(html).toContain('Evidence-Matrix fehlen')
  })

  it('renders diagnostics progress with learned codes and evidence', () => {
    const html = renderToStaticMarkup(React.createElement(RoadmapDrawer, { dashboard, t, apiReachable: false }))
    expect(html).toContain('Diagnostics-Fortschritt')
    expect(html).toContain('Rescue Build Diagnostics')
    expect(html).toContain('RESCUE-BUILD-ROOT-001')
    expect(html).toContain('RESCUE_ISO_MANUAL_OPERATOR_TERMINAL_BUILD')
    expect(html).toContain('DIAGNOSTICS_TEST_TRACK_LATEST.json')
  })

  it('renders future test tracks without execute actions', () => {
    const html = renderToStaticMarkup(React.createElement(RoadmapDrawer, { dashboard, t, apiReachable: false }))
    expect(html).toContain('Future Test Tracks')
    expect(html).toContain('Raspberry Pi 5')
    expect(html).not.toContain('Backup starten')
    expect(html).not.toContain('Restore ausführen')
  })
})
