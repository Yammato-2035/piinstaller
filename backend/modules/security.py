"""
Sicherheitsmodul - Härtung des Raspberry Pi
"""

from typing import Dict, Any, List
from .utils import SystemUtils
import subprocess


class SecurityModule:
    """Sicherheitskonfiguration und Härtung"""
    
    def __init__(self):
        self.utils = SystemUtils()
    
    async def scan_system(self) -> Dict[str, Any]:
        """Sicherheits-Scan durchführen"""
        scan_results = {
            "timestamp": self._get_timestamp(),
            "checks": {
                "ssh_config": await self._check_ssh(),
                "firewall": await self._check_firewall(),
                "auto_updates": await self._check_auto_updates(),
                "fail2ban": await self._check_fail2ban(),
                "password_policy": await self._check_password_policy(),
                "sudo_config": await self._check_sudo_config(),
            }
        }
        return scan_results
    
    async def configure(self, config) -> Dict[str, Any]:
        """Sicherheitskonfiguration anwenden"""
        results = {}
        
        # Sicherheitsupdates
        if config.enable_auto_updates:
            results["auto_updates"] = await self._enable_auto_updates()
        
        # SSH Hardening
        if config.enable_ssh_hardening:
            results["ssh_hardening"] = await self._harden_ssh()
        
        # Firewall
        if config.enable_firewall:
            results["firewall"] = await self._configure_firewall(config.open_ports or [22, 80, 443])
        
        # Fail2Ban
        if config.enable_fail2ban:
            results["fail2ban"] = await self._install_fail2ban()
        
        # Audit Logging
        if config.enable_audit_logging:
            results["audit_logging"] = await self._enable_audit_logging()
        
        return {"status": "success", "results": results}
    
    async def get_status(self) -> Dict[str, Any]:
        """Status aller Sicherheitskomponenten"""
        return await self.scan_system()
    
    # ==================== Private Methoden ====================
    
    async def _check_ssh(self) -> Dict[str, Any]:
        """SSH-Konfiguration prüfen"""
        checks = {
            "password_auth": await self._grep_sshd_config("PasswordAuthentication no"),
            "root_login": await self._grep_sshd_config("PermitRootLogin no"),
            "empty_passwords": await self._grep_sshd_config("PermitEmptyPasswords no"),
        }
        return {
            "status": all(checks.values()),
            "details": checks
        }
    
    async def _check_firewall(self) -> Dict[str, Any]:
        """Firewall-Status"""
        result = await self.utils.run_command("ufw status")
        is_active = "active" in result.get("stdout", "").lower()
        return {
            "status": is_active,
            "details": result.get("stdout", "")
        }
    
    async def _check_auto_updates(self) -> Dict[str, Any]:
        """Auto-Updates prüfen"""
        result = await self.utils.run_command("apt-get install -y unattended-upgrades")
        return {
            "status": result["success"],
            "message": "unattended-upgrades" if result["success"] else "Nicht installiert"
        }
    
    async def _check_fail2ban(self) -> Dict[str, Any]:
        """Fail2Ban prüfen"""
        is_installed = await self.utils.check_service("fail2ban")
        return {
            "status": is_installed,
            "message": "Installiert und aktiv" if is_installed else "Nicht installiert"
        }
    
    async def _check_password_policy(self) -> Dict[str, Any]:
        """Passwort-Policy prüfen"""
        # Prüfe auf libpam-pwquality
        result = await self.utils.run_command("dpkg -l | grep libpam-pwquality")
        is_installed = result["return_code"] == 0
        return {
            "status": is_installed,
            "details": "libpam-pwquality installiert" if is_installed else "Nicht installiert"
        }
    
    async def _check_sudo_config(self) -> Dict[str, Any]:
        """Sudo-Konfiguration prüfen"""
        result = await self.utils.run_command("sudo -l")
        return {
            "status": result["return_code"] == 0,
            "message": "Sudo konfiguriert"
        }
    
    async def _harden_ssh(self) -> Dict[str, Any]:
        """SSH Konfiguration verhärten"""
        ssh_config_changes = {
            "PasswordAuthentication": "no",
            "PermitRootLogin": "no",
            "PermitEmptyPasswords": "no",
            "X11Forwarding": "no",
            "MaxAuthTries": "3",
            "ClientAliveInterval": "300",
            "ClientAliveCountMax": "2",
        }
        
        # Sicherung erstellen
        await self.utils.run_command(
            "cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup",
            as_sudo=True
        )
        
        # Konfigurationen schreiben
        for key, value in ssh_config_changes.items():
            cmd = f'sed -i "s/^#{key}/{key}/" /etc/ssh/sshd_config'
            await self.utils.run_command(cmd, as_sudo=True)
        
        # SSH neustarten
        result = await self.utils.run_command(
            "systemctl restart sshd",
            as_sudo=True
        )
        
        return {
            "status": result["success"],
            "message": "SSH gehärtet",
            "changes": ssh_config_changes
        }
    
    async def _configure_firewall(self, ports: List[int]) -> Dict[str, Any]:
        """Firewall (UFW) konfigurieren"""
        # UFW installieren und aktivieren
        await self.utils.install_package("ufw")
        
        # Deny all incoming, allow all outgoing
        await self.utils.run_command("ufw default deny incoming", as_sudo=True)
        await self.utils.run_command("ufw default allow outgoing", as_sudo=True)
        
        # Ports öffnen
        for port in ports:
            await self.utils.run_command(f"ufw allow {port}", as_sudo=True)
        
        # UFW aktivieren
        result = await self.utils.run_command("ufw --force enable", as_sudo=True)
        
        return {
            "status": result["success"],
            "message": f"Firewall konfiguriert mit Ports: {ports}",
            "ports": ports
        }
    
    async def _install_fail2ban(self) -> Dict[str, Any]:
        """Fail2Ban installieren und konfigurieren"""
        # Installation
        result = await self.utils.install_package("fail2ban")
        
        if not result["success"]:
            return {"status": False, "message": "Installation fehlgeschlagen"}
        
        # Service aktivieren und starten
        await self.utils.enable_service("fail2ban")
        await self.utils.start_service("fail2ban")
        
        return {
            "status": True,
            "message": "Fail2Ban installiert und aktiviert"
        }
    
    async def _enable_audit_logging(self) -> Dict[str, Any]:
        """Audit-Logging aktivieren"""
        # auditd installieren
        result = await self.utils.install_package("auditd audispd-plugins")
        
        if result["success"]:
            await self.utils.enable_service("auditd")
            await self.utils.start_service("auditd")
        
        return {
            "status": result["success"],
            "message": "Audit-Logging aktiviert"
        }
    
    async def _enable_auto_updates(self) -> Dict[str, Any]:
        """Automatische Sicherheitsupdates aktivieren"""
        # unattended-upgrades installieren
        result = await self.utils.install_package("unattended-upgrades apt-listchanges")
        
        if result["success"]:
            # Konfiguration aktivieren
            await self.utils.run_command(
                "dpkg-reconfigure -plow unattended-upgrades",
                as_sudo=True
            )
        
        return {
            "status": result["success"],
            "message": "Automatische Updates aktiviert"
        }
    
    async def _grep_sshd_config(self, pattern: str) -> bool:
        """In sshd_config suchen"""
        result = await self.utils.run_command(f"grep -q '{pattern}' /etc/ssh/sshd_config")
        return result["return_code"] == 0
    
    def _get_timestamp(self) -> str:
        """Aktueller Timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
