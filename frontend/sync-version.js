#!/usr/bin/env node
/** Synchronisiert package.json version mit VERSION (Backend). */
const fs = require('fs');
const path = require('path');
const vPath = path.join(__dirname, '..', 'VERSION');
const pkgPath = path.join(__dirname, 'package.json');
try {
  const v = fs.readFileSync(vPath, 'utf8').trim() || '0.0.0';
  const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));
  if (pkg.version !== v) {
    pkg.version = v;
    fs.writeFileSync(pkgPath, JSON.stringify(pkg, null, 2) + '\n');
    console.log('[sync-version] package.json version ->', v);
  }
} catch (e) {
  console.warn('[sync-version] skip:', e.message);
}
