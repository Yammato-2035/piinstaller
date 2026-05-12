"""
AES-256-GCM Verschlüsselung für Backup-Archive (offline, cryptography-Bibliothek).
Schlüsselmaterial wird NICHT in das Archiv oder Manifest geschrieben.
Optional: Schlüssel als 32-Byte-Datei von externem Medium laden.
"""

from __future__ import annotations

import secrets
from pathlib import Path
from typing import Tuple

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from core.backup_recovery_i18n import K_CRYPTO_FAILED, K_CRYPTO_KEY_MISSING, tr

MAGIC = b"SHB1\x01"
NONCE_LEN = 12
KEY_LEN = 32


def load_key_from_file(path: str | Path) -> bytes:
    """Lädt genau 32 Bytes Schlüsselmaterial (kein Klartext-Passwort im Archiv)."""
    p = Path(path)
    raw = p.read_bytes()
    if len(raw) != KEY_LEN:
        raise ValueError(tr(K_CRYPTO_KEY_MISSING))
    return raw


def generate_key() -> bytes:
    return secrets.token_bytes(KEY_LEN)


def encrypt_file_plain(
    input_path: str | Path,
    output_path: str | Path,
    key: bytes,
) -> Tuple[bool, str | None]:
    """Verschlüsselt Datei nach output_path. Schlüssel nur im Speicher / extern."""
    msg = tr(K_CRYPTO_KEY_MISSING)
    if len(key) != KEY_LEN:
        return False, msg
    try:
        data = Path(input_path).read_bytes()
        nonce = secrets.token_bytes(NONCE_LEN)
        aes = AESGCM(key)
        ct = aes.encrypt(nonce, data, associated_data=MAGIC)
        out = MAGIC + nonce + ct
        Path(output_path).write_bytes(out)
        return True, None
    except Exception as e:
        return False, f"{tr(K_CRYPTO_FAILED)}: {e!s}"


def decrypt_file_to_path(
    encrypted_path: str | Path,
    output_path: str | Path,
    key: bytes,
) -> Tuple[bool, str | None]:
    if len(key) != KEY_LEN:
        return False, tr(K_CRYPTO_KEY_MISSING)
    try:
        raw = Path(encrypted_path).read_bytes()
        if not raw.startswith(MAGIC):
            return False, tr(K_CRYPTO_FAILED)
        nonce = raw[len(MAGIC) : len(MAGIC) + NONCE_LEN]
        ct = raw[len(MAGIC) + NONCE_LEN :]
        aes = AESGCM(key)
        pt = aes.decrypt(nonce, ct, associated_data=MAGIC)
        Path(output_path).write_bytes(pt)
        return True, None
    except Exception as e:
        return False, f"{tr(K_CRYPTO_FAILED)}: {e!s}"


def encrypt_bytes(data: bytes, key: bytes) -> bytes:
    """Rohe Bytes verschlüsseln (gleiches Format wie Datei ohne Dateisystem)."""
    if len(key) != KEY_LEN:
        raise ValueError(tr(K_CRYPTO_KEY_MISSING))
    nonce = secrets.token_bytes(NONCE_LEN)
    aes = AESGCM(key)
    ct = aes.encrypt(nonce, data, associated_data=MAGIC)
    return MAGIC + nonce + ct


def decrypt_bytes(blob: bytes, key: bytes) -> bytes:
    if len(key) != KEY_LEN:
        raise ValueError(tr(K_CRYPTO_KEY_MISSING))
    if not blob.startswith(MAGIC):
        raise ValueError(tr(K_CRYPTO_FAILED))
    nonce = blob[len(MAGIC) : len(MAGIC) + NONCE_LEN]
    ct = blob[len(MAGIC) + NONCE_LEN :]
    aes = AESGCM(key)
    return aes.decrypt(nonce, ct, associated_data=MAGIC)
