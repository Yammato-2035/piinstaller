#!/usr/bin/env bash
# Read-only helpers for config/runtime_ports.json (shell).
# Source: . "$(dirname "$0")/runtime-ports.sh"  (adjust path)

runtime_ports_repo_root() {
  if [[ -n "${SETUPHELFER_REPO_ROOT:-}" ]]; then
    cd "$SETUPHELFER_REPO_ROOT" && pwd
    return
  fi
  local lib_dir
  lib_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  if [[ -f "$lib_dir/../../config/runtime_ports.json" ]]; then
    cd "$lib_dir/../.." && pwd
    return
  fi
  if [[ -f "$lib_dir/../config/runtime_ports.json" ]]; then
    cd "$lib_dir/.." && pwd
    return
  fi
  echo "/home/volker/piinstaller"
}

runtime_ports_read() {
  local key="${1:-}"
  local root
  root="$(runtime_ports_repo_root)"
  RUNTIME_PORTS_REPO_ROOT="$root" RUNTIME_PORTS_KEY="$key" python3 - <<'PY'
import json, os
from pathlib import Path
root = Path(os.environ["RUNTIME_PORTS_REPO_ROOT"])
key = os.environ.get("RUNTIME_PORTS_KEY", "")
path = root / "config" / "runtime_ports.json"
data = {}
if path.is_file():
    data = json.loads(path.read_text(encoding="utf-8"))
if key == "api_base":
    print(data.get("ports", {}).get("backend_api", {}).get("base_url", "http://127.0.0.1:8000"))
elif key == "web_base":
    print(data.get("ports", {}).get("frontend_ui", {}).get("base_url", "http://127.0.0.1:3001"))
elif key == "lab_proxy_port":
    print(data.get("ports", {}).get("qemu_lab_proxy_host", {}).get("port", 8001))
elif key == "guest_devserver_url":
    print(data.get("ports", {}).get("qemu_guest_devserver", {}).get("base_url", "http://10.0.2.2:8001"))
elif key == "source":
    print(str(path) if path.is_file() else "embedded_defaults")
else:
    print(json.dumps(data))
PY
}
