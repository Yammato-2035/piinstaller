"""
SQLite-Zugriff für Remote-Companion: Pairing, Sessions, Geräteprofile, Audit.
Tokens werden nur gehashed gespeichert (niemals Klartext).
DB-Pfad: optional über init_remote_db(config_dir) gesetzt, sonst Zustandsverzeichnis/remote.db (siehe install_paths).
"""

import hashlib
import os
import sqlite3
from pathlib import Path
from typing import Optional

from core.install_paths import get_state_dir

# Wird von init_remote_db() gesetzt; Fallback für get_remote_db_path()
_remote_db_path: Optional[Path] = None

# Schema-Version für spätere Migrationen
SCHEMA_VERSION = 2


def get_remote_db_path() -> Path:
    """Liefert den Pfad der Remote-SQLite-Datenbank."""
    global _remote_db_path
    if _remote_db_path is not None:
        return _remote_db_path
    env_path = os.environ.get("PI_INSTALLER_REMOTE_DB")
    if env_path and env_path.strip():
        return Path(env_path.strip())
    return get_state_dir() / "remote.db"


def init_remote_db(config_dir: Optional[Path] = None) -> None:
    """
    Setzt den DB-Pfad (wenn config_dir übergeben) und legt Tabellen an.
    config_dir: z. B. CONFIG_PATH.parent aus app.py, damit DB neben config.json liegt.
    """
    global _remote_db_path
    if config_dir is not None:
        _remote_db_path = config_dir / "remote.db"
    path = get_remote_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(str(path)) as conn:
        conn.executescript(_SCHEMA_SQL)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS _schema_version (version INTEGER NOT NULL)"
        )
        cur = conn.execute("SELECT version FROM _schema_version LIMIT 1")
        row = cur.fetchone()
        current = row[0] if row else 0
        if current == 0:
            conn.execute("INSERT INTO _schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
            current = SCHEMA_VERSION
        if current < 2:
            try:
                conn.execute("ALTER TABLE pairing_tickets ADD COLUMN status TEXT NOT NULL DEFAULT 'pending'")
            except sqlite3.OperationalError:
                pass  # Spalte existiert bereits
            conn.execute("UPDATE _schema_version SET version = 2")
        conn.commit()


_SCHEMA_SQL = """
-- Pairing-Tickets (QR): nur Hash des Tokens speichern; status: pending | claimed | expired
CREATE TABLE IF NOT EXISTS pairing_tickets (
    id TEXT PRIMARY KEY,
    ticket_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    device_name TEXT,
    status TEXT NOT NULL DEFAULT 'pending'
);

-- Sessions: nur Hash des Session-Tokens
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    session_token_hash TEXT NOT NULL,
    device_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    refreshed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_sessions_device_id ON sessions(device_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);

-- Gekoppelte Geräte (Profil pro device_id)
CREATE TABLE IF NOT EXISTS remote_device_profiles (
    id TEXT PRIMARY KEY,
    device_id TEXT UNIQUE NOT NULL,
    name TEXT,
    role TEXT NOT NULL DEFAULT 'viewer',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_remote_device_profiles_device_id ON remote_device_profiles(device_id);

-- Audit-Log für Remote-Aktionen
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    device_id TEXT,
    details TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_log_device_id ON audit_log(device_id);
"""


def get_connection() -> sqlite3.Connection:
    """Öffnet eine Verbindung zur Remote-DB. Caller muss conn.close() aufrufen."""
    return sqlite3.connect(str(get_remote_db_path()))


def hash_token(plain: str) -> str:
    """
    Erzeugt einen sicheren Hash des Tokens zur Speicherung.
    Tokens niemals im Klartext persistieren; nur diesen Hash speichern.
    """
    if not plain:
        return ""
    pepper = os.environ.get("PI_INSTALLER_REMOTE_TOKEN_PEPPER", "pi-installer-remote-v1")
    data = f"{pepper}:{plain}".encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def verify_token(plain: str, stored_hash: str) -> bool:
    """Prüft, ob der gegebene Klartext-Token zum gespeicherten Hash passt."""
    if not plain or not stored_hash:
        return False
    return hash_token(plain) == stored_hash


def audit_log_insert(
    event_type: str,
    device_id: Optional[str] = None,
    details: Optional[str] = None,
) -> None:
    """Schreibt einen Eintrag ins Audit-Log (z. B. session_created, session_refreshed, session_revoked)."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO audit_log (event_type, device_id, details, created_at) VALUES (?, ?, ?, ?)",
            (event_type, device_id, details, now),
        )
        conn.commit()
    finally:
        conn.close()
