#!/usr/bin/env node
/**
 * Synchronisiert die Versionsnummer aus config/version.json (Projektroot) nach:
 * - frontend/package.json
 * - frontend/src-tauri/tauri.conf.json
 * - frontend/src-tauri/Cargo.toml (nur major.minor.patch, Cargo/Tauri verlangt Semver)
 * - VERSION (Projektroot, für Skripte/Abwärtskompatibilität)
 * - package.json (Projektroot, Metapaket)
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
  v = String(data.project_version || data.version || '').trim() || '0.0.0';
} catch (e) {
  console.warn('[sync-version] config/version.json nicht lesbar:', e.message);
  process.exit(0);
}
// Für Cargo.toml: nur major.minor.patch (Tauri/Cargo verlangt gültiges Semver)
const vCargo = v.replace(/^(\d+\.\d+\.\d+).*$/, '$1');
const vParts = v.split('.');
const patchComponent = vParts.length >= 4 ? parseInt(vParts[3], 10) : 0;
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
    let tauriChanged = false;
    if (tauri.version !== vCargo) {
      tauri.version = vCargo;
      tauriChanged = true;
    }
    if (Object.prototype.hasOwnProperty.call(tauri, 'setuphelferProjectVersion')) {
      delete tauri.setuphelferProjectVersion;
      tauriChanged = true;
    }
    if (tauri.bundle && typeof tauri.bundle === 'object') {
      if (!tauri.bundle.linux) tauri.bundle.linux = {};
      if (!tauri.bundle.linux.deb) tauri.bundle.linux.deb = {};
      const debChangelogPath = path.join(__dirname, 'src-tauri', 'deb-changelog.txt');
      const debChangelogRel = 'deb-changelog.txt';
      const debChangelogText =
        `SetupHelfer (${v}) — project version; Cargo/Tauri semver ${vCargo}; patch W=${patchComponent}.\n\n` +
        `See resources/setuphelfer-version.json for canonical version metadata.\n`;
      try {
        if (!fs.existsSync(debChangelogPath) || fs.readFileSync(debChangelogPath, 'utf8') !== debChangelogText) {
          fs.writeFileSync(debChangelogPath, debChangelogText);
          changed = true;
        }
      } catch (e) {
        console.warn('[sync-version] deb-changelog.txt:', e.message);
      }
      if (tauri.bundle.linux.deb.changelog !== debChangelogRel) {
        tauri.bundle.linux.deb.changelog = debChangelogRel;
        tauriChanged = true;
      }
      // Inline-Text war falsch — Tauri erwartet einen Dateipfad.
      if (
        tauri.bundle.linux.deb.changelog &&
        tauri.bundle.linux.deb.changelog.includes('SetupHelfer ')
      ) {
        tauri.bundle.linux.deb.changelog = debChangelogRel;
        tauriChanged = true;
      }
      const resourceRel = 'resources/setuphelfer-version.json';
      const resources = Array.isArray(tauri.bundle.resources) ? tauri.bundle.resources.slice() : [];
      if (!resources.includes(resourceRel)) {
        resources.push(resourceRel);
        tauri.bundle.resources = resources;
        tauriChanged = true;
      }
    }
    if (tauriChanged) {
      fs.writeFileSync(tauriPath, JSON.stringify(tauri, null, 2) + '\n');
      changed = true;
    }
  }
} catch (e) {
  console.warn('[sync-version] tauri.conf.json:', e.message);
}
const resourceDir = path.join(__dirname, 'src-tauri', 'resources');
const resourcePath = path.join(resourceDir, 'setuphelfer-version.json');
try {
  fs.mkdirSync(resourceDir, { recursive: true });
  const resourcePayload = {
    project_version: v,
    semver_package_version: vCargo,
    patch_component: patchComponent,
  };
  const resourceText = JSON.stringify(resourcePayload, null, 2) + '\n';
  const currentResource = fs.existsSync(resourcePath) ? fs.readFileSync(resourcePath, 'utf8') : '';
  if (currentResource !== resourceText) {
    fs.writeFileSync(resourcePath, resourceText);
    changed = true;
  }
} catch (e) {
  console.warn('[sync-version] setuphelfer-version.json:', e.message);
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
// VERSION-Datei im Projektroot für Skripte/Abwärtskompatibilität mitschreiben
const versionTxtPath = path.join(rootDir, 'VERSION');
try {
  const current = fs.existsSync(versionTxtPath) ? fs.readFileSync(versionTxtPath, 'utf8').trim() : '';
  if (current !== v) {
    fs.writeFileSync(versionTxtPath, v + '\n');
    changed = true;
  }
} catch (e) {
  console.warn('[sync-version] VERSION:', e.message);
}
const rootPkgPath = path.join(rootDir, 'package.json');
try {
  if (fs.existsSync(rootPkgPath)) {
    const pkg = JSON.parse(fs.readFileSync(rootPkgPath, 'utf8'));
    if (pkg.version !== v) {
      pkg.version = v;
      fs.writeFileSync(rootPkgPath, JSON.stringify(pkg, null, 2) + '\n');
      changed = true;
    }
  }
} catch (e) {
  console.warn('[sync-version] root package.json:', e.message);
}
try {
  const lockPath = path.join(__dirname, 'package-lock.json');
  if (fs.existsSync(lockPath)) {
    const lock = JSON.parse(fs.readFileSync(lockPath, 'utf8'));
    let lockChanged = false;
    if (lock.version !== v) {
      lock.version = v;
      lockChanged = true;
    }
    if (lock.packages && lock.packages[''] && lock.packages[''].version !== v) {
      lock.packages[''].version = v;
      lockChanged = true;
    }
    if (lockChanged) {
      fs.writeFileSync(lockPath, JSON.stringify(lock, null, 2) + '\n');
      changed = true;
    }
  }
} catch (e) {
  console.warn('[sync-version] package-lock.json:', e.message);
}
if (changed) {
  console.log('[sync-version] project_version ->', v, '| semver_package_version ->', vCargo);
}
