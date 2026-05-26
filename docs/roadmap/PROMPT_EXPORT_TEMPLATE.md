# STRICT MODE – {{TITLE_DE}}

## Ziel
{{REASON_DE}}

## Nicht-Ziele
{{NON_GOALS}}

## Sicherheitsregeln
{{SAFETY_RULES}}

## Phase 0 Runtime-/Repo-Gate
1. `git status --short`
2. `git branch --show-current`
3. `git rev-parse --short HEAD`
4. `./scripts/check-runtime-deploy-gate.sh` falls vorhanden, sonst `./scripts/check-backend-version-gate.sh`
5. `GET /api/version`
6. `GET /api/dev-dashboard/status` falls verfügbar

Wenn das Runtime-Gate fehlschlägt:
- keine Runtime-Tests gegen Port 8000
- keine API-Abnahme behaupten
- Abschlussbericht muss `runtime_gate_blocked_static_or_ui_work_only` enthalten

## Konkrete Aufgaben
{{PROMPT_TEXT}}

## Erlaubte Dateien/Bereiche
{{ALLOWED_PATHS}}

## Verbotene Aktionen
{{FORBIDDEN_ACTIONS}}

## Tests
{{TESTS}}

## Doku / FAQ / i18n
{{DOCUMENTATION_TARGETS}}

## Abschlussbericht
{{EXPECTED_OUTPUTS}}
