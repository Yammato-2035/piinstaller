#!/usr/bin/env node
/**
 * Erzeugt frontend/public/dev-dashboard.snapshot.json für Browser-Standalone (ohne Tauri).
 * Aufruf aus Repo-Root: node scripts/generate-dev-dashboard-snapshot.mjs
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { execSync } from 'node:child_process'

const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')

function readJson(rel) {
  const p = path.join(repo, rel)
  if (!fs.existsSync(p)) return null
  return JSON.parse(fs.readFileSync(p, 'utf8'))
}

function git(cmd) {
  try {
    return execSync(`git -C ${repo} ${cmd}`, { encoding: 'utf8' }).trim()
  } catch {
    return null
  }
}

const gatesDir = path.join(repo, 'docs/evidence/release-gates')
const gateNames = [
  'test_inventory.json',
  'current_failures.json',
  'release_readiness_gate.json',
  'backup_restore_release_gate.json',
]
const evidence_files = {}
for (const name of gateNames) {
  const p = path.join(gatesDir, name)
  evidence_files[name] = {
    path: `docs/evidence/release-gates/${name}`,
    exists: fs.existsSync(p),
    status: fs.existsSync(p) ? 'ok' : 'missing',
    data: readJson(`docs/evidence/release-gates/${name}`),
  }
}

const modulesDir = path.join(repo, 'docs/dev-dashboard/modules')
const modules = []
if (fs.existsSync(modulesDir)) {
  for (const f of fs.readdirSync(modulesDir).filter((x) => x.endsWith('.json'))) {
    const data = readJson(`docs/dev-dashboard/modules/${f}`)
    if (data) modules.push({ ...data, source: `docs/dev-dashboard/modules/${f}` })
  }
}

const matrixPath = path.join(repo, 'docs/roadmap/STATUS_MATRIX.md')
const matrixText = fs.existsSync(matrixPath) ? fs.readFileSync(matrixPath, 'utf8') : undefined

const scan = {
  workspace_root: repo,
  warnings: [],
  version: readJson('config/version.json'),
  frontend_package: readJson('frontend/package.json'),
  git: {
    git_head: git('rev-parse HEAD'),
    git_branch: git('rev-parse --abbrev-ref HEAD'),
    git_dirty_count: (git('status --porcelain') || '').split('\n').filter(Boolean).length,
    git_recent: (git('log --oneline -5') || '').split('\n'),
  },
  evidence_files,
  matrix: {
    path: 'docs/roadmap/STATUS_MATRIX.md',
    exists: fs.existsSync(matrixPath),
    lines: matrixText?.split('\n').length,
    text: matrixText,
  },
  modules,
}

const out = path.join(repo, 'frontend/public/dev-dashboard.snapshot.json')
fs.mkdirSync(path.dirname(out), { recursive: true })
fs.writeFileSync(out, JSON.stringify(scan, null, 2))
console.log('Wrote', out)
