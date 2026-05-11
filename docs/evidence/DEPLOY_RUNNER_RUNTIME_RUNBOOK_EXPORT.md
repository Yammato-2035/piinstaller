# Evidence: Deploy Runner Runtime Runbook Export

## Scope

Nur Export/Buendelung von Runbook-Dokumenten und Templates, keine Runtime-Ausfuehrung.

## Nachweise

- Exportmodul mit Pfadschutz (nur erlaubte Docs-/Evidence-Pfade)
- atomisches Schreiben `.tmp -> replace`
- Master-Runbook, Checklisten, Template, Schema und Acceptance-Forms erzeugt

## Kommandos

```bash
python3 -m py_compile backend/deploy/runner_runtime_runbook_export.py backend/deploy/routes.py
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_runtime_runbook_export_v1 -v
```
