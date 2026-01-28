"""
Backup-Modul mit Cloud-Upload und Verschlüsselung
"""

from typing import Dict, Any, Optional, Tuple, Callable
from pathlib import Path
import subprocess
import shlex
import json
import tempfile
import os


class BackupModule:
    """Backup-Funktionalität mit Cloud-Upload und Verschlüsselung"""
    
    def __init__(self, run_command_fn: Optional[Callable] = None):
        """
        Args:
            run_command_fn: Funktion zum Ausführen von Befehlen (wie run_command aus app.py)
        """
        self.run_command = run_command_fn
        self.supported_providers = {
            "seafile_webdav": "WebDAV (Seafile)",
            "webdav": "WebDAV (Allgemein)",
            "nextcloud_webdav": "WebDAV (Nextcloud)",
            "s3": "Amazon S3",
            "s3_compatible": "S3-kompatibel (MinIO, etc.)",
            "google_cloud": "Google Cloud Storage",
            "azure": "Azure Blob Storage",
        }
    
    def upload_to_cloud(
        self,
        local_file: str,
        provider: str,
        config: Dict[str, Any],
        sudo_password: str = ""
    ) -> Tuple[bool, str]:
        """Backup zu Cloud hochladen (synchron)"""
        if provider in ("seafile_webdav", "webdav", "nextcloud_webdav"):
            return self._upload_webdav(local_file, config, sudo_password)
        elif provider in ("s3", "s3_compatible"):
            return self._upload_s3(local_file, config, sudo_password)
        elif provider == "google_cloud":
            return self._upload_gcs(local_file, config, sudo_password)
        elif provider == "azure":
            return self._upload_azure(local_file, config, sudo_password)
        else:
            return False, f"Unbekannter Provider: {provider}"
    
    def _upload_webdav(
        self,
        local_file: str,
        config: Dict[str, Any],
        sudo_password: str
    ) -> Tuple[bool, str]:
        """WebDAV Upload (Seafile, Nextcloud, etc.)"""
        url = (config.get("webdav_url") or "").strip().rstrip("/")
        user = (config.get("username") or "").strip()
        pw = (config.get("password") or "").strip()
        remote_path = (config.get("remote_path") or "").strip().strip("/")
        
        if not url or not user or not pw:
            return False, "WebDAV-Settings fehlen (URL/User/Passwort)"
        
        base = f"{url}/{remote_path}" if remote_path else url
        if not base.endswith("/"):
            base += "/"
        remote = f"{base}{Path(local_file).name}"
        
        if not self.run_command:
            return False, "run_command Funktion nicht verfügbar"
        
        upload_timeout = 7200  # 2 h für große Backups / langsame Verbindungen
        # Parent-Collection per MKCOL anlegen (409 bei PUT vermeiden)
        if remote_path:
            parts = [p for p in remote_path.strip("/").split("/") if p]
            mkcol_base = url.rstrip("/") + "/"
            for seg in parts:
                mkcol_base = mkcol_base.rstrip("/") + "/" + seg + "/"
                mc = self.run_command(
                    f"curl -sS -o /dev/null -w '%{{http_code}}' -u {shlex.quote(user)}:{shlex.quote(pw)} -X MKCOL {shlex.quote(mkcol_base)}",
                    sudo=False,
                    timeout=60,
                )
                c = None
                try:
                    c = int((mc.get("stdout") or "").strip()) if (mc.get("stdout") or "").strip() else None
                except Exception:
                    pass
                if c not in (200, 201, 204, 405):
                    pass  # 409 etc. – weitermachen, PUT evtl. trotzdem ok
        
        # PUT mit Overwrite: T (409 bei existierender Datei vermeiden)
        cmd = (
            f"curl -sS -o /dev/null -w '%{{http_code}}' "
            f"-u {shlex.quote(user)}:{shlex.quote(pw)} -H 'Overwrite: T' -T {shlex.quote(local_file)} {shlex.quote(remote)}"
        )
        result = self.run_command(cmd, sudo=False, timeout=upload_timeout)
        put_code = None
        try:
            put_code = int((result.get("stdout") or "").strip()) if (result.get("stdout") or "").strip() else None
        except Exception:
            pass
        if not result.get("success"):
            err = (result.get("stderr") or result.get("error") or "Upload fehlgeschlagen")[:300]
            if (result.get("error") or "").strip() == "Command timeout":
                # Evtl. Upload fertig, Server antwortet nur langsam – prüfen ob Datei in Cloud
                rv = self.run_command(
                    f"curl -sS -o /dev/null -w '%{{http_code}}' -u {shlex.quote(user)}:{shlex.quote(pw)} -X PROPFIND -H 'Depth: 0' {shlex.quote(remote)}",
                    sudo=False,
                    timeout=30,
                )
                try:
                    cv = int((rv.get("stdout") or "").strip() or "0")
                except Exception:
                    cv = 0
                if rv.get("success") and cv in (200, 201, 204, 207):
                    return True, remote  # Datei existiert → Upload war ok
                err = "Upload-Zeitüberschreitung (Timeout) – Verbindung oder Server zu langsam?"
            return False, err
        if put_code not in (200, 201, 204):
            return False, f"Upload fehlgeschlagen (HTTP {put_code or '—'})"
        
        # Verifizierung (optional; 404 bei manchen Servern ignoriert)
        cmd_v = (
            f"curl -sS -o /dev/null -w '%{{http_code}}' "
            f"-u {shlex.quote(user)}:{shlex.quote(pw)} "
            "-X PROPFIND -H 'Depth: 0' "
            f"{shlex.quote(remote)}"
        )
        vr = self.run_command(cmd_v, sudo=False, timeout=120)
        code_str = (vr.get("stdout") or "").strip()
        try:
            code = int(code_str) if code_str else None
        except Exception:
            code = None
        if vr.get("success") and code in (200, 201, 204, 207):
            return True, remote
        if put_code in (200, 201, 204):
            return True, remote  # PUT ok, PROPFIND 404 ignoriert
        return False, f"Remote Verifizierung fehlgeschlagen (HTTP {code or '—'})"
    
    def _upload_s3(
        self,
        local_file: str,
        config: Dict[str, Any],
        sudo_password: str
    ) -> Tuple[bool, str]:
        """S3 Upload (AWS S3 oder S3-kompatibel)"""
        if not self.run_command:
            return False, "run_command Funktion nicht verfügbar"
        
        # Prüfe ob aws-cli installiert ist
        check = self.run_command("which aws", sudo=False)
        if not check.get("success"):
            # Versuche aws-cli zu installieren
            install_result = self.run_command(
                "pip3 install awscli --break-system-packages || pip3 install awscli",
                sudo=True,
                sudo_password=sudo_password
            )
            if not install_result.get("success"):
                return False, "aws-cli konnte nicht installiert werden"
        
        bucket = config.get("bucket") or ""
        key = config.get("key_prefix", "") + Path(local_file).name
        endpoint = config.get("endpoint_url")  # Für S3-kompatibel
        access_key = config.get("access_key_id") or ""
        secret_key = config.get("secret_access_key") or ""
        region = config.get("region") or "us-east-1"
        
        if not bucket or not access_key or not secret_key:
            return False, "S3-Settings fehlen (Bucket/Access-Key/Secret-Key)"
        
        # AWS CLI konfigurieren (temporär)
        env = os.environ.copy()
        env["AWS_ACCESS_KEY_ID"] = access_key
        env["AWS_SECRET_ACCESS_KEY"] = secret_key
        env["AWS_DEFAULT_REGION"] = region
        
        s3_path = f"s3://{bucket}/{key}"
        cmd = ["aws", "s3", "cp", local_file, s3_path]
        if endpoint:
            cmd.extend(["--endpoint-url", endpoint])
        
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=3600
        )
        
        if result.returncode != 0:
            return False, f"S3 Upload fehlgeschlagen: {result.stderr[:300]}"
        
        # Verifizierung
        cmd_check = ["aws", "s3", "ls", s3_path]
        if endpoint:
            cmd_check.extend(["--endpoint-url", endpoint])
        
        check_result = subprocess.run(
            cmd_check,
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if check_result.returncode != 0:
            return False, "S3 Verifizierung fehlgeschlagen"
        
        return True, s3_path
    
    def _upload_gcs(
        self,
        local_file: str,
        config: Dict[str, Any],
        sudo_password: str
    ) -> Tuple[bool, str]:
        """Google Cloud Storage Upload"""
        if not self.run_command:
            return False, "run_command Funktion nicht verfügbar"
        
        # Prüfe ob gsutil installiert ist
        check = self.run_command("which gsutil", sudo=False)
        if not check.get("success"):
            # Installiere gsutil
            install_result = self.run_command(
                "pip3 install gsutil --break-system-packages || pip3 install gsutil",
                sudo=True,
                sudo_password=sudo_password
            )
            if not install_result.get("success"):
                return False, "gsutil konnte nicht installiert werden"
        
        bucket = config.get("bucket") or ""
        key = config.get("key_prefix", "") + Path(local_file).name
        service_account_file = config.get("service_account_file") or ""
        
        if not bucket:
            return False, "GCS-Settings fehlen (Bucket)"
        
        gcs_path = f"gs://{bucket}/{key}"
        
        # Service Account Key setzen
        env = os.environ.copy()
        if service_account_file and Path(service_account_file).exists():
            env["GOOGLE_APPLICATION_CREDENTIALS"] = service_account_file
        
        cmd = ["gsutil", "cp", local_file, gcs_path]
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=3600
        )
        
        if result.returncode != 0:
            return False, f"GCS Upload fehlgeschlagen: {result.stderr[:300]}"
        
        # Verifizierung
        cmd_check = ["gsutil", "ls", gcs_path]
        check_result = subprocess.run(
            cmd_check,
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if check_result.returncode != 0:
            return False, "GCS Verifizierung fehlgeschlagen"
        
        return True, gcs_path
    
    def _upload_azure(
        self,
        local_file: str,
        config: Dict[str, Any],
        sudo_password: str
    ) -> Tuple[bool, str]:
        """Azure Blob Storage Upload"""
        # Prüfe ob azure-cli installiert ist
        check = self.run_command("which az", sudo=False)
        if not check.get("success"):
            # Installiere azure-cli
            install_result = self.run_command(
                "curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash",
                sudo=True,
                sudo_password=sudo_password
            )
            if not install_result.get("success"):
                return False, "Azure CLI konnte nicht installiert werden"
        
        account_name = config.get("account_name") or ""
        container = config.get("container") or ""
        key = config.get("key_prefix", "") + Path(local_file).name
        account_key = config.get("account_key") or ""
        
        if not account_name or not container or not account_key:
            return False, "Azure-Settings fehlen (Account-Name/Container/Account-Key)"
        
        # Azure Login (mit Account Key)
        env = os.environ.copy()
        env["AZURE_STORAGE_ACCOUNT"] = account_name
        env["AZURE_STORAGE_KEY"] = account_key
        
        blob_path = f"{container}/{key}"
        cmd = ["az", "storage", "blob", "upload", "--file", local_file, "--container-name", container, "--name", key, "--account-name", account_name, "--account-key", account_key]
        
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=3600
        )
        
        if result.returncode != 0:
            return False, f"Azure Upload fehlgeschlagen: {result.stderr[:300]}"
        
        return True, f"azure://{account_name}/{blob_path}"
    
    def encrypt_backup(
        self,
        backup_file: str,
        encryption_key: Optional[str] = None,
        encryption_method: str = "gpg",
        sudo_password: str = ""
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Backup verschlüsseln
        
        Returns:
            (success, encrypted_file_path, error_message)
        """
        if encryption_method == "gpg":
            return self._encrypt_gpg(backup_file, encryption_key, sudo_password)
        elif encryption_method == "openssl":
            return self._encrypt_openssl(backup_file, encryption_key, sudo_password)
        else:
            return False, backup_file, f"Unbekannte Verschlüsselungsmethode: {encryption_method}"
    
    def _encrypt_gpg(
        self,
        backup_file: str,
        encryption_key: Optional[str],
        sudo_password: str
    ) -> Tuple[bool, str, Optional[str]]:
        """GPG Verschlüsselung"""
        if not self.run_command:
            return False, backup_file, "run_command Funktion nicht verfügbar"
        
        # Prüfe ob gpg installiert ist
        check = self.run_command("which gpg", sudo=False)
        if not check.get("success"):
            install_result = self.run_command(
                "apt-get install -y gnupg2",
                sudo=True,
                sudo_password=sudo_password
            )
            if not install_result.get("success"):
                return False, backup_file, "GPG konnte nicht installiert werden"
        
        encrypted_file = f"{backup_file}.gpg"
        
        encrypted_file = f"{backup_file}.gpg"
        
        if encryption_key:
            # Verschlüsselung mit Passphrase
            proc = subprocess.Popen(
                ["gpg", "--batch", "--yes", "--passphrase-fd", "0", "--cipher-algo", "AES256", "--compress-algo", "1", "-c", backup_file],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = proc.communicate(input=encryption_key, timeout=3600)
            success = proc.returncode == 0
        else:
            # Verschlüsselung ohne Passphrase (nur komprimiert)
            proc = subprocess.Popen(
                ["gpg", "--batch", "--yes", "--cipher-algo", "AES256", "--compress-algo", "1", "-c", backup_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = proc.communicate(timeout=3600)
            success = proc.returncode == 0
        
        if not success:
            return False, backup_file, f"GPG Verschlüsselung fehlgeschlagen: {stderr[:200] if stderr else 'Unbekannter Fehler'}"
        
        if not Path(encrypted_file).exists():
            return False, backup_file, "Verschlüsselte Datei wurde nicht erstellt"
        
        # Lösche die ursprüngliche unverschlüsselte Datei nach erfolgreicher Verschlüsselung
        try:
            if Path(backup_file).exists():
                Path(backup_file).unlink()
        except Exception as e:
            # Warnung, aber nicht kritisch - verschlüsselte Datei existiert
            pass
        
        return True, encrypted_file, None
    
    def _encrypt_openssl(
        self,
        backup_file: str,
        encryption_key: Optional[str],
        sudo_password: str
    ) -> Tuple[bool, str, Optional[str]]:
        """OpenSSL Verschlüsselung (AES-256-CBC)"""
        if not self.run_command:
            return False, backup_file, "run_command Funktion nicht verfügbar"
        
        # Prüfe ob openssl installiert ist
        check = self.run_command("which openssl", sudo=False)
        if not check.get("success"):
            install_result = self.run_command(
                "apt-get install -y openssl",
                sudo=True,
                sudo_password=sudo_password
            )
            if not install_result.get("success"):
                return False, backup_file, "OpenSSL konnte nicht installiert werden"
        
        encrypted_file = f"{backup_file}.enc"
        
        if not encryption_key:
            return False, backup_file, "OpenSSL benötigt einen Verschlüsselungsschlüssel"
        
        # Verschlüsselung mit AES-256-CBC (mit sudo wenn Passwort vorhanden, um Permission denied zu vermeiden)
        cmd = f"openssl enc -aes-256-cbc -salt -pbkdf2 -in {shlex.quote(backup_file)} -out {shlex.quote(encrypted_file)} -pass pass:{shlex.quote(encryption_key)}"
        run_kw = dict(sudo=bool(sudo_password), sudo_password=sudo_password or None, timeout=3600)
        result = self.run_command(cmd, **run_kw) if self.run_command else {"success": False, "stderr": "run_command nicht verfügbar"}
        
        if not result.get("success"):
            return False, backup_file, f"OpenSSL Verschlüsselung fehlgeschlagen: {result.get('stderr', '')[:200]}"
        
        if not Path(encrypted_file).exists():
            return False, backup_file, "Verschlüsselte Datei wurde nicht erstellt"
        
        # Lösche die ursprüngliche unverschlüsselte Datei nach erfolgreicher Verschlüsselung
        try:
            if Path(backup_file).exists() and self.run_command:
                del_cmd = f"rm -f {shlex.quote(backup_file)}"
                self.run_command(del_cmd, sudo=bool(sudo_password), sudo_password=sudo_password or None)
        except Exception:
            pass
        
        return True, encrypted_file, None
    
    def decrypt_backup(
        self,
        encrypted_file: str,
        encryption_key: Optional[str] = None,
        encryption_method: str = "gpg",
        output_file: Optional[str] = None,
        sudo_password: str = ""
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Backup entschlüsseln
        
        Returns:
            (success, decrypted_file_path, error_message)
        """
        if encryption_method == "gpg":
            return self._decrypt_gpg(encrypted_file, encryption_key, output_file, sudo_password)
        elif encryption_method == "openssl":
            return self._decrypt_openssl(encrypted_file, encryption_key, output_file, sudo_password)
        else:
            return False, encrypted_file, f"Unbekannte Verschlüsselungsmethode: {encryption_method}"
    
    def _decrypt_gpg(
        self,
        encrypted_file: str,
        encryption_key: Optional[str],
        output_file: Optional[str],
        sudo_password: str
    ) -> Tuple[bool, str, Optional[str]]:
        """GPG Entschlüsselung"""
        if not self.run_command:
            return False, output_file or encrypted_file, "run_command Funktion nicht verfügbar"
        
        if not output_file:
            output_file = encrypted_file.replace(".gpg", "")
        
        if encryption_key:
            # Entschlüsselung mit Passphrase
            with open(output_file, 'wb') as out:
                proc = subprocess.Popen(
                    ["gpg", "--batch", "--yes", "--passphrase-fd", "0", "-d", encrypted_file],
                    stdin=subprocess.PIPE,
                    stdout=out,
                    stderr=subprocess.PIPE,
                    text=False
                )
                stdout, stderr = proc.communicate(input=encryption_key.encode(), timeout=3600)
                success = proc.returncode == 0
        else:
            # Entschlüsselung ohne Passphrase
            with open(output_file, 'wb') as out:
                proc = subprocess.Popen(
                    ["gpg", "--batch", "--yes", "-d", encrypted_file],
                    stdout=out,
                    stderr=subprocess.PIPE,
                    text=False
                )
                stdout, stderr = proc.communicate(timeout=3600)
                success = proc.returncode == 0
        
        if not success:
            return False, output_file, f"GPG Entschlüsselung fehlgeschlagen: {stderr.decode('utf-8', errors='ignore')[:200] if stderr else 'Unbekannter Fehler'}"
        
        if not Path(output_file).exists():
            return False, output_file, "Entschlüsselte Datei wurde nicht erstellt"
        
        return True, output_file, None
    
    def _decrypt_openssl(
        self,
        encrypted_file: str,
        encryption_key: Optional[str],
        output_file: Optional[str],
        sudo_password: str
    ) -> Tuple[bool, str, Optional[str]]:
        """OpenSSL Entschlüsselung"""
        if not self.run_command:
            return False, output_file or encrypted_file, "run_command Funktion nicht verfügbar"
        
        if not output_file:
            output_file = encrypted_file.replace(".enc", "")
        
        if not encryption_key:
            return False, output_file, "OpenSSL benötigt einen Verschlüsselungsschlüssel"
        
        cmd = f"openssl enc -aes-256-cbc -d -pbkdf2 -in {shlex.quote(encrypted_file)} -out {shlex.quote(output_file)} -pass pass:{shlex.quote(encryption_key)}"
        result = self.run_command(cmd, sudo=False)
        
        if not result.get("success"):
            return False, output_file, f"OpenSSL Entschlüsselung fehlgeschlagen: {result.get('stderr', '')[:200]}"
        
        if not Path(output_file).exists():
            return False, output_file, "Entschlüsselte Datei wurde nicht erstellt"
        
        return True, output_file, None
