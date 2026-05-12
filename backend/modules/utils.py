"""
Utility-Funktionen für System-Operationen
"""

import subprocess
import psutil
import os
from typing import Dict, Any, List
from pathlib import Path


class SystemUtils:
    """System-Utilities"""
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Systeminfo auslesen"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu": {
                    "usage": cpu_percent,
                    "count": psutil.cpu_count(),
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.percent,
                },
                "platform": {
                    "system": os.uname().sysname,
                    "release": os.uname().release,
                },
                "uptime": self._get_uptime(),
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _get_uptime(self) -> str:
        """System Uptime"""
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
                hours = int(uptime_seconds // 3600)
                minutes = int((uptime_seconds % 3600) // 60)
                return f"{hours}h {minutes}m"
        except:
            return "N/A"
    
    async def run_command(self, command: str, as_sudo: bool = False) -> Dict[str, Any]:
        """Befehl ausführen"""
        try:
            if as_sudo:
                command = f"sudo {command}"
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Befehl hat zu lange gedauert",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    async def check_service(self, service_name: str) -> bool:
        """Service-Status prüfen"""
        try:
            result = await self.run_command(f"systemctl is-active {service_name}")
            return result["return_code"] == 0
        except:
            return False
    
    async def enable_service(self, service_name: str) -> bool:
        """Service aktivieren"""
        try:
            result = await self.run_command(f"systemctl enable {service_name}", as_sudo=True)
            return result["success"]
        except:
            return False
    
    async def start_service(self, service_name: str) -> bool:
        """Service starten"""
        try:
            result = await self.run_command(f"systemctl start {service_name}", as_sudo=True)
            return result["success"]
        except:
            return False
    
    async def install_package(self, package: str) -> Dict[str, Any]:
        """Paket installieren"""
        try:
            # Update package manager
            await self.run_command("apt-get update", as_sudo=True)
            # Install package
            result = await self.run_command(f"apt-get install -y {package}", as_sudo=True)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def file_exists(self, path: str) -> bool:
        """Datei existiert"""
        return Path(path).exists()
    
    async def create_backup(self, source: str, destination: str) -> Dict[str, Any]:
        """Sicherung erstellen"""
        try:
            result = await self.run_command(
                f"cp -r {source} {destination}",
                as_sudo=True
            )
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
