"""
Verschlüsselter Session-Store für das sudo-Passwort.
Nutzt Fernet (AES-128 + HMAC); Passwort nie im Klartext im RAM außer bei Entschlüsselung für einen Befehl.
Key-Datei liegt unter Installationsverzeichnis oder XDG, nur für aktuellen Benutzer lesbar.
"""

from pathlib import Path
import os
import time
import logging

logger = logging.getLogger(__name__)

# TTL Standard: 30 Minuten
DEFAULT_TTL_SECONDS = 1800


def _key_file_path() -> Path:
    """Key-Datei: PI_INSTALLER_DIR/.sudo_key oder Repo-Root; Fallback ~/.config/pi-installer/sudo.key wenn nicht schreibbar."""
    candidates = []
    install_dir = os.environ.get("PI_INSTALLER_DIR")
    if install_dir:
        candidates.append(Path(install_dir).resolve() / ".sudo_key")
    # Entwicklung: Repo-Root = backend/core/.. -> backend/.. = Repo
    repo_root = Path(__file__).resolve().parent.parent.parent
    candidates.append(repo_root / ".sudo_key")
    # Fallback: XDG Config (immer schreibbar für aktuellen User)
    xdg = Path.home() / ".config" / "pi-installer" / "sudo.key"
    candidates.append(xdg)
    for p in candidates:
        try:
            if p.exists():
                if os.access(p, os.R_OK):
                    return p
            else:
                p.parent.mkdir(parents=True, exist_ok=True)
                if os.access(p.parent, os.W_OK):
                    return p
        except Exception:
            continue
    return candidates[-1]


def _load_or_create_key(key_path: Path):
    from cryptography.fernet import Fernet
    key_path = key_path.resolve()
    if key_path.exists():
        key = key_path.read_bytes()
    else:
        key = Fernet.generate_key()
        key_path.parent.mkdir(parents=True, exist_ok=True)
        key_path.write_bytes(key)
        try:
            os.chmod(key_path, 0o600)
        except Exception:
            pass
    return Fernet(key)


class EncryptedSudoStore:
    """
    Speichert ein sudo-Passwort verschlüsselt mit TTL.
    Ein Eintrag pro Prozess (key "password"); bei Ablauf oder Fehler wird None zurückgegeben.
    """

    def __init__(self, ttl_seconds: int = DEFAULT_TTL_SECONDS):
        self._ttl = ttl_seconds
        self._entry: dict | None = None  # {"token": str, "expires": float}
        try:
            self._fernet = _load_or_create_key(_key_file_path())
        except Exception as e:
            logger.warning("EncryptedSudoStore: Key konnte nicht geladen werden (%s), Store deaktiviert.", e)
            self._fernet = None

    def store_password(self, password: str, ttl_seconds: int | None = None) -> None:
        """Passwort verschlüsseln und mit TTL speichern."""
        if not password or not self._fernet:
            return
        ttl = ttl_seconds if ttl_seconds is not None else self._ttl
        try:
            token = self._fernet.encrypt(password.encode("utf-8")).decode("ascii")
            self._entry = {
                "token": token,
                "expires": time.time() + ttl,
            }
        except Exception as e:
            logger.warning("EncryptedSudoStore: Speichern fehlgeschlagen: %s", e)

    def get_password(self) -> str | None:
        """Entschlüsseln, nur wenn nicht abgelaufen. Bei Fehler/Ablauf wird der Eintrag gelöscht."""
        if not self._fernet or not self._entry:
            return None
        if time.time() > self._entry["expires"]:
            self.clear()
            return None
        try:
            return self._fernet.decrypt(self._entry["token"].encode("ascii")).decode("utf-8")
        except Exception:
            self.clear()
            return None

    def has_password(self) -> bool:
        """True wenn ein gültiges (nicht abgelaufenes) Passwort gespeichert ist."""
        return self.get_password() is not None

    def clear(self) -> None:
        """Gespeichertes Passwort verwerfen."""
        self._entry = None
