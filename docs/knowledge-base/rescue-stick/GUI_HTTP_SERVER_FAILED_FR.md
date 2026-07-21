# Echec serveur HTTP GUI (KB)

**Task:** PI-RS-BVR-GUI-DCC-001  
**Code:** `http_server_failed` (watchdog/legacy) · Cause: `SyntaxError` Python inline

## Symptome

- Pas de GUI visible pendant l'E2E auto
- `rescue-ui-launch.log` : `SyntaxError: bytes can only contain ASCII literal characters`
- `rescue-ui-status.json` : `reason=http_server_failed` ou sortie du processus
- BVR continue → `passed_with_gui_fallback`

## Cause (baseline)

Le launcher demarrait un serveur HTTP Python inline via heredoc. Un caractere non-ASCII (`…`, U+2026) dans un litteral `b'...'` provoquait un arret immediat.

Run de reference : `e2e-rescue-msi-20260721-232222-ba58c7a7`.

## Correctif (implemente, retest physique en attente)

1. Serveur dedie : `setuphelfer-rescue-ui-http-server` (ASCII-safe)
2. Readiness via `GET /health.json` avant Chromium
3. Preflight des locales pour la page de progression
4. Payload cible : **1.10.1.1**

## Diagnostic

```bash
grep -E 'SyntaxError|rescue\.gui\.' SETUP_LOGS/setuphelfer/logs/boot/rescue-ui-launch.log
curl -fsS http://127.0.0.1:8765/health.json
```

## Codes `rescue.gui.*`

Voir le contrat [RESCUE_GUI_HTTP_RUNTIME_CONTRACT.md](../../architecture/RESCUE_GUI_HTTP_RUNTIME_CONTRACT.md).

## Voir aussi

- [GUI_HTTP_ROOT_CAUSE_ANALYSIS.md](../../evidence/rescue/bvr-gui-dcc-001/GUI_HTTP_ROOT_CAUSE_ANALYSIS.md)
