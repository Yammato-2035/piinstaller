#!/usr/bin/env node
/**
 * Synchronisiert die Versionsnummer aus VERSION (Projektroot) nach:
 * - frontend/package.json
 * - frontend/src-tauri/tauri.conf.json
 * Wird bei „npm run prebuild“ ausgeführt. Einzige Quelle: VERSION.
 */
const fs = require('fs');
const path = require('path');
const rootDir = path.join(__dirname, '..');
const vPath = path.join(rootDir, 'VERSION');
const pkgPath = path.join(__dirname, 'package.json');
const tauriPath = path.join(__dirname, 'src-tauri', 'tauri.conf.json');
let v;
try {
  v = fs.readFileSync(vPath, 'utf8').trim() || '0.0.0';
} catch (e) {
  console.warn('[sync-version] VERSION nicht lesbar:', e.message);
  process.exit(0);
}
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
    if (tauri.version !== v) {
      tauri.version = v;
      fs.writeFileSync(tauriPath, JSON.stringify(tauri, null, 2) + '\n');
      changed = true;
    }
  }
} catch (e) {
  console.warn('[sync-version] tauri.conf.json:', e.message);
}
if (changed) {
  console.log('[sync-version] version ->', v);
}
