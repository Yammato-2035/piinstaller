# Controlled Command Runs Evidence

Dieses Verzeichnis enthält Evidence-Dateien für den internen Controlled Command Runner.

- Schema: `controlled_command_run.schema.json`
- Beispiel: `example_controlled_command_run.json`

Regeln:

- `argv` statt freier Shell-Strings
- `shell=false` als Standard
- stdout/stderr in separaten Logdateien
- Excerpts nur als Zusatz
- `forbidden`-Kommandos werden nie ausgeführt
