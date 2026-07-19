#!/usr/bin/env bash
# After MSI Phase A boot: evaluate evidence; on success restore Discovery + GRUB Lab-Auto.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SETUP_LOGS="${SETUP_LOGS:-}"
ESP_MOUNT="${ESP_MOUNT:-}"
EXECUTE=false
FORCE_RESTORE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --execute) EXECUTE=true; shift ;;
    --force-restore-discovery) FORCE_RESTORE=true; shift ;;
    --setup-logs) SETUP_LOGS="$2"; shift 2 ;;
    --esp) ESP_MOUNT="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 [--setup-logs PATH] [--esp PATH] [--force-restore-discovery] --execute" >&2
      exit 0
      ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$SETUP_LOGS" ]]; then
  for cand in /media/*/SETUP_LOGS /media/*/SETUP_LOGS2 /run/media/*/SETUP_LOGS*; do
    [[ -d "$cand" ]] && SETUP_LOGS="$cand" && break
  done
fi
[[ -n "$SETUP_LOGS" ]] || { echo "ERROR: SETUP_LOGS not mounted" >&2; exit 1; }

EVAL_JSON="$(bash "${REPO_ROOT}/scripts/rescue/evaluate-phase-a-physical-e2e.sh" "$SETUP_LOGS" || true)"
echo "$EVAL_JSON"
OK="$(python3 -c 'import json,sys; d=json.loads(sys.argv[1]); print("1" if d.get("ok") else "0")' "$EVAL_JSON")"
CODE="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1]).get("code") or "")' "$EVAL_JSON")"

if [[ "$OK" != "1" && "$FORCE_RESTORE" != true ]]; then
  echo "Phase A not passed (code=$CODE) — Discovery/GRUB bleiben unverändert." >&2
  exit 3
fi

[[ "$EXECUTE" == true ]] || { echo "Plan only — use --execute to restore Discovery/GRUB"; exit 0; }

args=(--setup-logs "$SETUP_LOGS" --execute)
[[ -n "$ESP_MOUNT" ]] && args+=(--esp "$ESP_MOUNT")
bash "${REPO_ROOT}/scripts/rescue/restore-stick-discovery-lab-auto.sh" "${args[@]}"
