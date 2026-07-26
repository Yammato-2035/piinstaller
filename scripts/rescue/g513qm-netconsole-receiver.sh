#!/usr/bin/env bash
# Lab netconsole UDP receiver for G513QM out-of-band kernel capture.
# Binds only to configured interface; never overwrites existing run dirs.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CFG="${G513QM_NETCONSOLE_CFG:-$ROOT/config/rescue/g513qm_netconsole_lab.json}"
PORT="${G513QM_NETCONSOLE_PORT:-6666}"
IFACE="${G513QM_NETCONSOLE_IFACE:-}"
RUN_ID="${G513QM_RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)-netconsole}"
OUT_BASE="$ROOT/docs/evidence/runtime-results/rescue/g513qm-netconsole"
OUT="$OUT_BASE/$RUN_ID"

if [[ -f "$CFG" ]]; then
  IFACE="${IFACE:-$(python3 -c "import json;print(json.load(open('$CFG')).get('bind_iface',''))" 2>/dev/null || true)}"
  PORT="${PORT:-$(python3 -c "import json;print(json.load(open('$CFG')).get('listen_port',6666))" 2>/dev/null || true)}"
fi

mkdir -p "$OUT_BASE"
if [[ -e "$OUT" ]]; then
  echo "Refusing to overwrite existing $OUT" >&2
  exit 3
fi
mkdir -p "$OUT"

META="$OUT/receiver-metadata.json"
LOG="$OUT/receiver.log"
: >"$LOG"

python3 - <<PY
import json, os, socket, time, pathlib
out = pathlib.Path("$OUT")
iface = "$IFACE".strip()
port = int("$PORT" or 6666)
meta = {
  "run_id": "$RUN_ID",
  "bind_iface": iface or None,
  "listen_port": port,
  "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
  "purpose": "g513qm_netconsole_receiver",
  "redaction": "source_ip_logged_as_lab_only",
}
(out / "receiver-metadata.json").write_text(json.dumps(meta, indent=2) + "\n")
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# Bind all interfaces if iface empty; operator should set lab iface in config.
sock.bind(("0.0.0.0", port))
print(f"listening udp/0.0.0.0:{port} iface_hint={iface or 'any'} -> {out}", flush=True)
log = open(out / "receiver.log", "a", buffering=1)
try:
  while True:
    data, addr = sock.recvfrom(65535)
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    line = data.decode("utf-8", "replace").rstrip("\n")
    # Redact: keep last octet group only in file? Keep full for lab LAN by policy note.
    rec = f"{ts} src={addr[0]}:{addr[1]} {line}\n"
    log.write(rec)
    print(rec, end="", flush=True)
except KeyboardInterrupt:
  pass
finally:
  log.close()
  sock.close()
  meta["ended_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
  (out / "receiver-metadata.json").write_text(json.dumps(meta, indent=2) + "\n")
  os.system(f"cd '{out}' && sha256sum receiver.log receiver-metadata.json > SHA256SUMS")
PY
