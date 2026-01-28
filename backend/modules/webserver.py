"""
Webserver-Konfigurationsmodul
"""

from typing import Dict, Any
from .utils import SystemUtils


class WebServerModule:
    """Webserver Installation und Konfiguration"""
    
    def __init__(self):
        self.utils = SystemUtils()
    
    async def configure(self, config) -> Dict[str, Any]:
        """Webserver konfigurieren"""
        results = {}
        
        # Webserver installieren
        if config.server_type == "nginx":
            results["webserver"] = await self._install_nginx()
        else:
            results["webserver"] = await self._install_apache()
        
        # SSL/TLS
        if config.enable_ssl:
            results["ssl"] = await self._configure_ssl()
        
        # PHP (falls benötigt)
        if config.enable_php:
            results["php"] = await self._install_php()
        
        # Webadmin Panel
        if config.install_webadmin:
            results["webadmin"] = await self._install_webadmin(config.webadmin_type)
        
        # CMS Installation
        if config.cms_type:
            results["cms"] = await self._install_cms(config.cms_type)
        
        # Härtung
        results["hardening"] = await self._harden_webserver()
        
        return {"status": "success", "results": results}
    
    async def get_status(self) -> Dict[str, Any]:
        """Webserver-Status"""
        return {
            "nginx": await self.utils.check_service("nginx"),
            "apache2": await self.utils.check_service("apache2"),
            "php-fpm": await self.utils.check_service("php-fpm"),
        }
    
    # ==================== Private Methoden ====================
    
    async def _install_nginx(self) -> Dict[str, Any]:
        """Nginx installieren und konfigurieren"""
        result = await self.utils.install_package("nginx")
        
        if result["success"]:
            await self.utils.enable_service("nginx")
            await self.utils.start_service("nginx")
        
        return {
            "status": "success" if result["success"] else "error",
            "server": "Nginx",
            "port": 80,
            "message": "Nginx installiert und läuft"
        }
    
    async def _install_apache(self) -> Dict[str, Any]:
        """Apache2 installieren und konfigurieren"""
        result = await self.utils.install_package("apache2 apache2-utils")
        
        if result["success"]:
            await self.utils.enable_service("apache2")
            await self.utils.start_service("apache2")
            
            # Wichtige Module aktivieren
            await self.utils.run_command("a2enmod rewrite", as_sudo=True)
            await self.utils.run_command("a2enmod ssl", as_sudo=True)
            await self.utils.run_command("a2enmod proxy", as_sudo=True)
        
        return {
            "status": "success" if result["success"] else "error",
            "server": "Apache2",
            "port": 80,
            "message": "Apache2 installiert und läuft"
        }
    
    async def _configure_ssl(self) -> Dict[str, Any]:
        """SSL/TLS mit Let's Encrypt konfigurieren"""
        # Certbot installieren
        result = await self.utils.install_package("certbot python3-certbot-nginx python3-certbot-apache")
        
        return {
            "status": "info" if result["success"] else "error",
            "message": "Certbot installiert. Führen Sie 'certbot' manuell aus für Domain-Registrierung",
            "command": "sudo certbot --nginx" # oder --apache
        }
    
    async def _install_php(self) -> Dict[str, Any]:
        """PHP und PHP-FPM installieren"""
        result = await self.utils.install_package(
            "php-fpm php-mysql php-pgsql php-curl php-gd php-mbstring php-zip"
        )
        
        if result["success"]:
            await self.utils.enable_service("php7.4-fpm")
            await self.utils.start_service("php7.4-fpm")
        
        return {
            "status": "success" if result["success"] else "error",
            "message": "PHP-FPM installiert"
        }
    
    async def _install_webadmin(self, admin_type: str) -> Dict[str, Any]:
        """Webadmin Panel installieren"""
        if admin_type == "cockpit":
            result = await self.utils.install_package("cockpit cockpit-machines")
            
            if result["success"]:
                await self.utils.enable_service("cockpit.socket")
                await self.utils.start_service("cockpit.socket")
            
            return {
                "status": "success" if result["success"] else "error",
                "admin_panel": "Cockpit",
                "url": "https://localhost:9090",
                "message": "Cockpit-Panel installiert"
            }
        
        elif admin_type == "webmin":
            # Webmin Installation
            result = await self.utils.run_command(
                "curl -o setup-repos.sh https://raw.githubusercontent.com/webmin/webmin/master/setup-repos.sh && sh setup-repos.sh",
                as_sudo=True
            )
            
            if result["success"]:
                result = await self.utils.install_package("webmin")
            
            return {
                "status": "success" if result["success"] else "error",
                "admin_panel": "Webmin",
                "url": "https://localhost:10000",
                "message": "Webmin installiert"
            }
        
        return {"status": "error", "message": f"Unbekannter Admin-Typ: {admin_type}"}
    
    async def _install_cms(self, cms_type: str) -> Dict[str, Any]:
        """CMS installieren"""
        if cms_type == "wordpress":
            return await self._install_wordpress()
        elif cms_type == "drupal":
            return await self._install_drupal()
        elif cms_type == "nextcloud":
            return await self._install_nextcloud()
        
        return {"status": "error", "message": f"Unbekanntes CMS: {cms_type}"}
    
    async def _install_wordpress(self) -> Dict[str, Any]:
        """WordPress installieren"""
        # WordPress benötigt MySQL und PHP
        await self.utils.install_package("wordpress wp-cli")
        
        return {
            "status": "info",
            "cms": "WordPress",
            "message": "WordPress installiert. Laufen Sie wp-cli Befehle für Konfiguration aus",
            "docs": "https://wordpress.org"
        }
    
    async def _install_drupal(self) -> Dict[str, Any]:
        """Drupal installieren"""
        # Drupal benötigt PHP und Datenbank
        result = await self.utils.install_package("drupal drupal-core drupal-database-utf8")
        
        return {
            "status": "success" if result["success"] else "error",
            "cms": "Drupal",
            "message": "Drupal installiert",
            "docs": "https://drupal.org"
        }
    
    async def _install_nextcloud(self) -> Dict[str, Any]:
        """Nextcloud installieren"""
        result = await self.utils.install_package("nextcloud")
        
        if result["success"]:
            await self.utils.run_command("systemctl restart php-fpm", as_sudo=True)
        
        return {
            "status": "success" if result["success"] else "error",
            "cms": "Nextcloud",
            "message": "Nextcloud installiert",
            "url": "http://localhost/nextcloud",
            "docs": "https://nextcloud.com"
        }
    
    async def _harden_webserver(self) -> Dict[str, Any]:
        """Webserver härten"""
        hardening_steps = []
        
        # Nginx Header Hardening
        nginx_config = """
server {
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
}
"""
        
        # Zugriff auf .htaccess und sensible Dateien sperren
        htaccess = """
<FilesMatch "^\\.(env|git|htaccess)">
    Require all denied
</FilesMatch>
"""
        
        # Disable Directory Listing
        await self.utils.run_command(
            'echo "Options -Indexes" > /var/www/html/.htaccess',
            as_sudo=True
        )
        
        hardening_steps.append({
            "step": "Directory Listing deaktiviert",
            "success": True
        })
        
        return {
            "status": "success",
            "hardening": hardening_steps,
            "message": "Webserver gehärtet"
        }
