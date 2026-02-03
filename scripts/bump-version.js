#!/usr/bin/env node
/**
 * Erhöht die Patch-Version (W) in VERSION (X.Y.Z.W) um 1.
 * Verwendung bei Bugfixes und kleinen Ergänzungen (ohne neues Feature).
 * Bei neuem Feature: node scripts/bump-feature.js (erhöht Z, setzt W auf 0).
 * Aufruf: node scripts/bump-version.js
 * Danach: Changelog in Documentation.tsx ergänzen.
 */
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const rootDir = path.join(__dirname, '..');
const vPath = path.join(rootDir, 'VERSION');
let v;
try {
  v = fs.readFileSync(vPath, 'utf8').trim() || '0.0.0';
} catch (e) {
  console.error('VERSION nicht lesbar:', e.message);
  process.exit(1);
}
const parts = v.split('.').map(Number);
if (parts.length < 4 || parts.some(isNaN)) {
  console.error('VERSION muss X.Y.Z.W sein (z. B. 1.0.1.13):', v);
  process.exit(1);
}
parts[3] += 1;
const newVersion = parts.join('.');
fs.writeFileSync(vPath, newVersion + '\n');
console.log('VERSION:', v, '->', newVersion);
execSync('node sync-version.js', { cwd: path.join(rootDir, 'frontend'), stdio: 'inherit' });
console.log('Changelog in frontend/src/pages/Documentation.tsx ergänzen.');
