#!/usr/bin/env node
/**
 * Erhöht die Feature-Version (Z) in VERSION (X.Y.Z.W) um 1 und setzt W auf 0.
 * Verwendung bei neuen Features (z. B. neuer Bereich wie Kino/Streaming).
 * Aufruf: node scripts/bump-feature.js
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
  console.error('VERSION muss X.Y.Z.W sein (z. B. 1.0.1.17):', v);
  process.exit(1);
}
parts[2] += 1;  // Z erhöhen (3. Stelle)
parts[3] = 0;   // W auf 0 setzen
const newVersion = parts.join('.');
fs.writeFileSync(vPath, newVersion + '\n');
console.log('VERSION (Feature-Bump):', v, '->', newVersion);
execSync('node sync-version.js', { cwd: path.join(rootDir, 'frontend'), stdio: 'inherit' });
console.log('Changelog in frontend/src/pages/Documentation.tsx ergänzen.');
