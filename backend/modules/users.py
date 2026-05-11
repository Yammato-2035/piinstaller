"""
Benutzerverwaltungsmodul
"""

from typing import Dict, Any, List
from .utils import SystemUtils
import subprocess
import secrets


class UserModule:
    """Benutzerverwaltung und Rollenmanagement"""
    
    def __init__(self):
        self.utils = SystemUtils()
        self.roles = {
            "admin": {"sudo": True, "groups": ["sudo", "adm"]},
            "developer": {"sudo": False, "groups": ["docker", "dialout"]},
            "user": {"sudo": False, "groups": []},
        }
    
    async def list_users(self) -> Dict[str, Any]:
        """Alle Benutzer auflisten"""
        result = await self.utils.run_command("getent passwd | cut -d: -f1")
        
        if result["success"]:
            users = result["stdout"].strip().split("\n")
            return {
                "status": "success",
                "users": users,
                "count": len(users)
            }
        
        return {"status": "error", "message": "Konnte Benutzer nicht auflisten"}
    
    async def create_user(self, user_data) -> Dict[str, Any]:
        """Neuen Benutzer erstellen"""
        username = user_data.username
        role = user_data.role
        email = user_data.email
        
        # Validierung
        if not username or len(username) < 3:
            return {"status": "error", "message": "Ungültiger Benutzername"}
        
        if role not in self.roles:
            return {"status": "error", "message": f"Ungültige Rolle: {role}"}
        
        # Benutzer existiert bereits?
        check = await self.utils.run_command(f"id {username}")
        if check["return_code"] == 0:
            return {"status": "error", "message": f"Benutzer {username} existiert bereits"}
        
        # Benutzer erstellen
        cmd = f"useradd -m -s /bin/bash {username}"
        result = await self.utils.run_command(cmd, as_sudo=True)
        
        if not result["success"]:
            return {"status": "error", "message": "Benutzer konnte nicht erstellt werden"}
        
        # Passwort setzen oder generieren
        if user_data.password:
            password = user_data.password
        else:
            password = secrets.token_urlsafe(16)
        
        pwd_cmd = f'echo "{username}:{password}" | chpasswd'
        pwd_result = await self.utils.run_command(pwd_cmd, as_sudo=True)
        
        # Gruppen zuweisen
        groups = self.roles[role]["groups"]
        for group in groups:
            await self.utils.run_command(f"usermod -aG {group} {username}", as_sudo=True)
        
        # Sudo-Rechte
        if self.roles[role]["sudo"]:
            sudo_file = f"/etc/sudoers.d/{username}"
            cmd = f"echo '{username} ALL=(ALL) NOPASSWD:ALL' > {sudo_file}"
            await self.utils.run_command(cmd, as_sudo=True)
            await self.utils.run_command(f"chmod 440 {sudo_file}", as_sudo=True)
        
        # SSH-Key generieren (optional)
        ssh_key = None
        if user_data.create_ssh_key:
            ssh_result = await self._create_ssh_key(username)
            ssh_key = ssh_result.get("public_key")
        
        return {
            "status": "success",
            "message": f"Benutzer {username} erstellt",
            "user": {
                "username": username,
                "role": role,
                "email": email,
                "password": password if not user_data.password else "***",
                "ssh_key": ssh_key,
                "groups": groups
            }
        }
    
    async def delete_user(self, username: str) -> Dict[str, Any]:
        """Benutzer löschen"""
        # Benutzer existiert?
        check = await self.utils.run_command(f"id {username}")
        if check["return_code"] != 0:
            return {"status": "error", "message": f"Benutzer {username} existiert nicht"}
        
        # Benutzer löschen (mit Home-Directory)
        result = await self.utils.run_command(f"userdel -r {username}", as_sudo=True)
        
        if result["success"]:
            return {"status": "success", "message": f"Benutzer {username} gelöscht"}
        
        return {"status": "error", "message": "Benutzer konnte nicht gelöscht werden"}
    
    async def reset_password(self, username: str, new_password: str) -> Dict[str, Any]:
        """Passwort zurücksetzen"""
        cmd = f'echo "{username}:{new_password}" | chpasswd'
        result = await self.utils.run_command(cmd, as_sudo=True)
        
        if result["success"]:
            return {"status": "success", "message": f"Passwort für {username} zurückgesetzt"}
        
        return {"status": "error", "message": "Passwort konnte nicht geändert werden"}
    
    async def change_role(self, username: str, new_role: str) -> Dict[str, Any]:
        """Benutzerrolle ändern"""
        if new_role not in self.roles:
            return {"status": "error", "message": f"Ungültige Rolle: {new_role}"}
        
        # Alte Gruppen entfernen
        result = await self.utils.run_command(f"id {username}")
        if result["return_code"] != 0:
            return {"status": "error", "message": f"Benutzer {username} existiert nicht"}
        
        # Neue Gruppen zuweisen
        groups = self.roles[new_role]["groups"]
        for group in groups:
            await self.utils.run_command(f"usermod -aG {group} {username}", as_sudo=True)
        
        return {
            "status": "success",
            "message": f"Rolle für {username} auf {new_role} geändert"
        }
    
    async def get_user_info(self, username: str) -> Dict[str, Any]:
        """Benutzerinformationen auslesen"""
        result = await self.utils.run_command(f"id {username}")
        
        if result["return_code"] != 0:
            return {"status": "error", "message": f"Benutzer {username} existiert nicht"}
        
        return {
            "status": "success",
            "info": result["stdout"]
        }
    
    # ==================== Private Methoden ====================
    
    async def _create_ssh_key(self, username: str) -> Dict[str, Any]:
        """SSH-Schlüsselpaar generieren"""
        home_dir = f"/home/{username}"
        ssh_dir = f"{home_dir}/.ssh"
        key_path = f"{ssh_dir}/id_rsa"
        
        # .ssh Verzeichnis erstellen
        await self.utils.run_command(f"mkdir -p {ssh_dir}", as_sudo=True)
        
        # SSH-Key generieren
        cmd = f'ssh-keygen -t rsa -b 4096 -f {key_path} -N "" -C "{username}@pi"'
        result = await self.utils.run_command(cmd, as_sudo=True)
        
        if not result["success"]:
            return {"status": "error"}
        
        # Berechtigungen setzen
        await self.utils.run_command(f"chmod 700 {ssh_dir}", as_sudo=True)
        await self.utils.run_command(f"chmod 600 {key_path}", as_sudo=True)
        await self.utils.run_command(f"chown -R {username}:{username} {ssh_dir}", as_sudo=True)
        
        # Öffentlichen Schlüssel auslesen
        pubkey_result = await self.utils.run_command(f"cat {key_path}.pub")
        
        return {
            "status": "success",
            "private_key": "Gespeichert auf dem Server",
            "public_key": pubkey_result.get("stdout", "").strip()
        }
