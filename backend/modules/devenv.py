"""
Entwicklungsumgebungsmodul
"""

from typing import Dict, Any, List
from .utils import SystemUtils


class DevEnvModule:
    """Entwicklungsumgebung einrichten und verwalten"""
    
    def __init__(self):
        self.utils = SystemUtils()
        self.language_packages = {
            "python": {
                "packages": ["python3", "python3-pip", "python3-venv"],
                "extras": ["python3-dev", "build-essential"]
            },
            "node": {
                "packages": ["nodejs", "npm"],
                "extras": ["yarn"]
            },
            "go": {
                "packages": ["golang-go"],
                "extras": ["golang-doc"]
            },
            "rust": {
                "packages": ["rustc", "cargo"],
                "extras": ["rust-doc"]
            },
        }
        
        self.databases = {
            "postgres": {
                "packages": ["postgresql", "postgresql-contrib"],
                "service": "postgresql"
            },
            "mysql": {
                "packages": ["mariadb-server", "mariadb-client"],
                "service": "mariadb"
            },
            "mongodb": {
                "packages": ["mongodb"],
                "service": "mongodb"
            },
            "redis": {
                "packages": ["redis-server"],
                "service": "redis-server"
            },
        }
        
        self.tools = {
            "docker": {
                "packages": ["docker.io", "docker-compose"],
                "service": "docker"
            },
            "git": {
                "packages": ["git", "git-lfs"],
                "service": None
            },
            "cursor": {
                "packages": [],
                "service": None,
                "custom": True
            },
            "vscode": {
                "packages": ["code-server"],
                "service": "code-server"
            },
        }
    
    async def configure(self, config) -> Dict[str, Any]:
        """Entwicklungsumgebung konfigurieren"""
        results = {
            "languages": {},
            "databases": {},
            "tools": {},
        }
        
        # Sprachen installieren
        if config.languages:
            for language in config.languages:
                results["languages"][language] = await self.install_language(language)
        
        # Datenbanken installieren
        if config.databases:
            for database in config.databases:
                results["databases"][database] = await self.install_database(database)
        
        # Tools installieren
        if config.tools:
            for tool in config.tools:
                results["tools"][tool] = await self.install_tool(tool)
        
        # GitHub Integration
        if config.github_token:
            results["github"] = await self._configure_github(config.github_token)
        
        return {"status": "success", "results": results}
    
    async def get_status(self) -> Dict[str, Any]:
        """Status der Entwicklungsumgebung"""
        status = {
            "languages": {},
            "databases": {},
            "tools": {},
        }
        
        # Sprachen prüfen
        for lang in self.language_packages.keys():
            status["languages"][lang] = await self._check_language(lang)
        
        # Datenbanken prüfen
        for db in self.databases.keys():
            status["databases"][db] = await self._check_database(db)
        
        # Tools prüfen
        for tool in self.tools.keys():
            status["tools"][tool] = await self._check_tool(tool)
        
        return status
    
    async def install_language(self, language: str) -> Dict[str, Any]:
        """Programmiersprache installieren"""
        if language not in self.language_packages:
            return {"status": "error", "message": f"Unbekannte Sprache: {language}"}
        
        packages = self.language_packages[language]
        all_packages = packages["packages"] + packages.get("extras", [])
        
        results = []
        for package in all_packages:
            result = await self.utils.install_package(package)
            results.append({"package": package, "success": result["success"]})
        
        all_success = all(r["success"] for r in results)
        
        return {
            "status": "success" if all_success else "partial",
            "language": language,
            "packages": results
        }
    
    async def install_database(self, database: str) -> Dict[str, Any]:
        """Datenbank installieren"""
        if database not in self.databases:
            return {"status": "error", "message": f"Unbekannte Datenbank: {database}"}
        
        db_config = self.databases[database]
        packages = db_config["packages"]
        
        # Pakete installieren
        results = []
        for package in packages:
            result = await self.utils.install_package(package)
            results.append({"package": package, "success": result["success"]})
        
        # Service aktivieren und starten
        if db_config.get("service"):
            await self.utils.enable_service(db_config["service"])
            await self.utils.start_service(db_config["service"])
        
        # Datenbank initialisieren
        init_result = await self._initialize_database(database)
        
        return {
            "status": "success",
            "database": database,
            "packages": results,
            "initialized": init_result
        }
    
    async def install_tool(self, tool: str) -> Dict[str, Any]:
        """Entwicklungs-Tool installieren"""
        if tool not in self.tools:
            return {"status": "error", "message": f"Unbekanntes Tool: {tool}"}
        
        tool_config = self.tools[tool]
        
        if tool == "cursor":
            return await self._install_cursor()
        
        # Standardinstallation
        packages = tool_config.get("packages", [])
        results = []
        
        for package in packages:
            result = await self.utils.install_package(package)
            results.append({"package": package, "success": result["success"]})
        
        # Service aktivieren
        if tool_config.get("service"):
            await self.utils.enable_service(tool_config["service"])
            await self.utils.start_service(tool_config["service"])
        
        return {
            "status": "success",
            "tool": tool,
            "packages": results
        }
    
    # ==================== Private Methoden ====================
    
    async def _check_language(self, language: str) -> Dict[str, Any]:
        """Programmiersprache prüfen"""
        packages = self.language_packages[language]["packages"]
        installed = []
        
        for package in packages:
            result = await self.utils.run_command(f"which {package.replace('-', '_')} || dpkg -l | grep {package}")
            installed.append(result["return_code"] == 0)
        
        return {
            "installed": all(installed),
            "details": installed
        }
    
    async def _check_database(self, database: str) -> Dict[str, Any]:
        """Datenbank prüfen"""
        service = self.databases[database].get("service")
        if not service:
            return {"installed": False}
        
        is_active = await self.utils.check_service(service)
        
        return {
            "installed": is_active,
            "active": is_active,
            "service": service
        }
    
    async def _check_tool(self, tool: str) -> Dict[str, Any]:
        """Tool prüfen"""
        packages = self.tools[tool].get("packages", [])
        if not packages:
            return {"installed": False, "message": "Custom installation"}
        
        result = await self.utils.run_command(f"which {packages[0]}")
        return {"installed": result["return_code"] == 0}
    
    async def _initialize_database(self, database: str) -> Dict[str, Any]:
        """Datenbank initialisieren"""
        if database == "postgres":
            return await self._init_postgres()
        elif database == "mysql":
            return await self._init_mysql()
        elif database == "mongodb":
            return await self._init_mongodb()
        elif database == "redis":
            return {"status": "success", "message": "Redis läuft auf Port 6379"}
        
        return {"status": "success"}
    
    async def _init_postgres(self) -> Dict[str, Any]:
        """PostgreSQL initialisieren"""
        result = await self.utils.run_command(
            "sudo -u postgres createdb devdb",
            as_sudo=False
        )
        return {
            "status": "success" if result["success"] else "partial",
            "database": "devdb",
            "port": 5432
        }
    
    async def _init_mysql(self) -> Dict[str, Any]:
        """MySQL/MariaDB initialisieren"""
        result = await self.utils.run_command(
            "mysql_secure_installation",
            as_sudo=True
        )
        return {
            "status": "success" if result["success"] else "partial",
            "port": 3306
        }
    
    async def _init_mongodb(self) -> Dict[str, Any]:
        """MongoDB initialisieren"""
        result = await self.utils.run_command(
            "systemctl start mongodb",
            as_sudo=True
        )
        return {
            "status": "success" if result["success"] else "partial",
            "port": 27017
        }
    
    async def _install_cursor(self) -> Dict[str, Any]:
        """Cursor AI Editor installieren"""
        # Cursor ist ein VSCode Fork und könnte über npm installiert werden
        # oder man kopiert es von cursor.sh
        return {
            "status": "info",
            "message": "Cursor Editor kann von https://www.cursor.com/ heruntergeladen werden",
            "port": 8080
        }
    
    async def _configure_github(self, token: str) -> Dict[str, Any]:
        """GitHub Integration konfigurieren"""
        # Git konfigurieren
        result = await self.utils.run_command(f"git config --global user.name 'PI Developer'")
        
        # Token speichern (sicher)
        result = await self.utils.run_command(
            f'echo "https://{token}@github.com" > ~/.git-credentials && chmod 600 ~/.git-credentials',
            as_sudo=False
        )
        
        # Git credentials helper
        await self.utils.run_command(
            "git config --global credential.helper store",
            as_sudo=False
        )
        
        return {
            "status": "success",
            "message": "GitHub konfiguriert"
        }
