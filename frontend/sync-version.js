#!/usr/bin/env node
/**
 * Synchronisiert die Versionsnummer aus config/version.json (Projektroot) nach:
 * - frontend/package.json
 * - frontend/src-tauri/tauri.conf.json
 * - frontend/src-tauri/Cargo.toml (nur major.minor.patch, Cargo/Tauri verlangt Semver)
 * Wird bei „npm run prebuild“ ausgeführt. Einzige Quelle: config/version.json.
 */
const fs = require('fs');
const path = require('path');
const rootDir = path.join(__dirname, '..');
const vPath = path.join(rootDir, 'config', 'version.json');
const pkgPath = path.join(__dirname, 'package.json');
const tauriPath = path.join(__dirname, 'src-tauri', 'tauri.conf.json');
const cargoPath = path.join(__dirname, 'src-tauri', 'Cargo.toml');
let v;
try {
  const raw = fs.readFileSync(vPath, 'utf8');
  const data = JSON.parse(raw);
  v = String(data.version || '').trim() || '0.0.0';
} catch (e) {
  console.warn('[sync-version] config/version.json nicht lesbar:', e.message);
  process.exit(0);
}
// Für Cargo.toml: nur major.minor.patch (Tauri/Cargo verlangt gültiges Semver)
const vCargo = v.replace(/^(\d+\.\d+\.\d+).*$/, '$1');
let changed = false;
try {
  const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));
  if (pkg.version !== v) {
    pkg.version = v;
    fs.writeFileSync(pkgPath, JSON.stringify(pkg, null, 2) + '\n');
    changed = true;
  }
} catch (e) {
  console.warn('[sync-version] package.json:', e.message);
}
try {
  if (fs.existsSync(tauriPath)) {
    const tauri = JSON.parse(fs.readFileSync(tauriPath, 'utf8'));
    if (tauri.version !== vCargo) {
      tauri.version = vCargo;
      fs.writeFileSync(tauriPath, JSON.stringify(tauri, null, 2) + '\n');
      changed = true;
    }
  }
} catch (e) {
  console.warn('[sync-version] tauri.conf.json:', e.message);
}
try {
  if (fs.existsSync(cargoPath)) {
    let cargo = fs.readFileSync(cargoPath, 'utf8');
    const versionMatch = cargo.match(/^version\s*=\s*"([^"]+)"/m);
    if (versionMatch && versionMatch[1] !== vCargo) {
      cargo = cargo.replace(/^version\s*=\s*"[^"]+"/m, `version = "${vCargo}"`);
      fs.writeFileSync(cargoPath, cargo);
      changed = true;
    }
  }
} catch (e) {
  console.warn('[sync-version] Cargo.toml:', e.message);
}
if (changed) {
  console.log('[sync-version] version ->', v);
}
