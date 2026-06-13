"""
Webserver Service Discovery Core — canonical read-only webserver/service discovery.

Phase G.11: logic extracted from ``app.py``; no API changes, no new discovery rules.
"""

from __future__ import annotations

import subprocess
from typing import Any

from core.network_discovery import detect_frontend_port

WEBSERVER_SERVICE_DISCOVERY_VERSION = 1


def _shell_run(cmd: str, *, timeout: int = 10) -> dict[str, Any]:
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timeout", "stdout": "", "stderr": ""}
    except Exception as exc:  # noqa: BLE001
        return {"success": False, "error": str(exc), "stdout": "", "stderr": ""}


def run_command(cmd: str, *, timeout: int = 10) -> dict[str, Any]:
    return _shell_run(cmd, timeout=timeout)


# --- check_installed (extracted from app.py) ---
def check_installed(package):
    """Prüfe ob Paket installiert ist"""
    # Spezielle Prüfung für bestimmte Pakete
    if package == "ufw":
        # UFW spezifisch prüfen
        result = run_command("which ufw")
        if result["success"]:
            return True
        # Alternativ: dpkg prüfen
        result = run_command("dpkg -l | grep '^ii' | grep -E '^ii\\s+ufw\\s'")
        return result["success"] and "ufw" in result.get("stdout", "")
    
    if package == "nginx":
        # Nginx spezifisch prüfen - mehrere Methoden
        # Methode 1: which nginx
        result = run_command("which nginx")
        if result["success"]:
            return True
        # Methode 2: dpkg prüfen
        result = run_command("dpkg -l | grep '^ii' | grep -E '\\snginx\\s'")
        if result["success"] and "nginx" in result.get("stdout", ""):
            return True
        # Methode 3: Prüfe ob nginx-Binary existiert
        result = run_command("test -f /usr/sbin/nginx || test -f /usr/bin/nginx")
        if result["success"]:
            return True
        # Methode 4: Prüfe ob nginx-Config existiert
        result = run_command("test -d /etc/nginx")
        if result["success"]:
            return True
        return False
    
    if package == "apache2" or package == "apache":
        # Apache spezifisch prüfen
        result = run_command("which apache2")
        if result["success"]:
            return True
        result = run_command("dpkg -l | grep '^ii' | grep -E '\\sapache2\\s'")
        if result["success"] and "apache2" in result.get("stdout", ""):
            return True
        result = run_command("test -f /usr/sbin/apache2 || test -d /etc/apache2")
        if result["success"]:
            return True
        return False
    
    # Grafana: which, dpkg, Binary-Pfade, systemd-Unit, Snap
    if package == "grafana":
        if run_command("which grafana-server 2>/dev/null")["success"]:
            return True
        r = run_command("dpkg -l 2>/dev/null | grep -E '^ii\\s+grafana'")
        if r.get("success") and (r.get("stdout") or "").strip():
            return True
        if run_command("test -f /usr/sbin/grafana-server 2>/dev/null")["success"]:
            return True
        if run_command("test -f /usr/bin/grafana-server 2>/dev/null")["success"]:
            return True
        if run_command("test -f /usr/share/grafana/bin/grafana-server 2>/dev/null")["success"]:
            return True
        if run_command("systemctl list-unit-files 2>/dev/null | grep -q 'grafana-server'")["success"]:
            return True
        if run_command("systemctl list-units --all 2>/dev/null | grep -q grafana")["success"]:
            return True
        if run_command("snap list 2>/dev/null | grep -q grafana")["success"]:
            return True
        if run_command("test -f /snap/bin/grafana-server 2>/dev/null")["success"]:
            return True
        # Docker-Container (auch wenn kein Zugriff auf Socket)
        if run_command("docker ps --format '{{.Names}}' 2>/dev/null | grep -q grafana")["success"]:
            return True
        if run_command("docker ps -a --format '{{.Names}}' 2>/dev/null | grep -q grafana")["success"]:
            return True
        # Port 3000 prüfen (Grafana-Standard-Port)
        if run_command("ss -tlnp 2>/dev/null | grep -q ':3000 '")["success"] or run_command("netstat -tlnp 2>/dev/null | grep -q ':3000 '")["success"]:
            return True
        return False

    # Standard-Prüfung
    result = run_command(f"which {package} || dpkg -l | grep '^ii' | grep -E '\\s{package}\\s'")
    return result["success"]


# --- get_installed_apps (extracted from app.py) ---
def get_installed_apps():
    """Erkenne installierte Web-Apps"""
    apps = {
        "wordpress": check_installed("wordpress"),
        "nextcloud": check_installed("nextcloud"),
        "drupal": check_installed("drupal"),
        "nginx": check_installed("nginx"),
        "apache": check_installed("apache2"),
        "php": check_installed("php") or check_installed("php-fpm") or check_installed("libapache2-mod-php"),
        "mysql": check_installed("mysql"),
        "postgresql": check_installed("postgresql"),
        "docker": check_installed("docker"),
        "python": check_installed("python3"),
        "nodejs": check_installed("nodejs"),
        "git": check_installed("git"),
        "cursor": False,  # Wird separat geprüft
        "qtqml": check_installed("qt5-default") or check_installed("qtbase5-dev") or run_command("which qmake 2>/dev/null")["success"] or run_command("dpkg -l 2>/dev/null | grep -q 'qt5'")["success"],
        "cockpit": check_installed("cockpit"),
        "webmin": check_installed("webmin"),
        # NAS
        "samba": check_installed("samba") or check_installed("samba-common"),
        "nfs": check_installed("nfs-kernel-server") or check_installed("nfs-common"),
        "ftp": check_installed("vsftpd") or check_installed("proftpd"),
        # Home Automation
        "homeassistant": check_installed("homeassistant") or run_command("docker ps | grep homeassistant")["success"],
        "openhab": check_installed("openhab"),
        "nodered": check_installed("node-red") or run_command("npm list -g node-red 2>/dev/null")["success"],
        # Music Box
        "mopidy": check_installed("mopidy"),
        "volumio": check_installed("volumio") or run_command("test -f /opt/volumio/bin/volumio")["success"],
        "plex": check_installed("plexmediaserver") or run_command("dpkg -l | grep plex")["success"],
    }
    
    # Cursor AI prüfen (kann in verschiedenen Pfaden sein)
    cursor_paths = [
        "/usr/bin/cursor",
        "/usr/local/bin/cursor",
        "/opt/cursor/cursor",
        "~/.local/bin/cursor",
    ]
    for path in cursor_paths:
        result = run_command(f"test -f {path} || which cursor")
        if result["success"]:
            apps["cursor"] = True
            break
    
    # WordPress Plugins prüfen
    wp_plugin_paths = [
        "/var/www/html/wp-content/plugins",
        "/var/www/wordpress/wp-content/plugins",
        "~/wordpress/wp-content/plugins",
    ]
    for path in wp_plugin_paths:
        result = run_command(f"test -d {path} && ls {path} 2>/dev/null | head -5")
        if result["success"] and result["stdout"]:
            plugins = [p.strip() for p in result["stdout"].split("\n") if p.strip()]
            apps["wordpress_plugins"] = plugins
            break
    
    # Websites/Apps erkennen (Webroot prüfen)
    webroots = ["/var/www/html", "/var/www", "/home/*/public_html"]
    websites = []
    for root in webroots:
        result = run_command(f"ls -d {root}/* 2>/dev/null | head -10")
        if result["success"]:
            for site in result["stdout"].split("\n"):
                if site.strip():
                    websites.append(site.strip())
    
    apps["websites"] = websites[:10]  # Erste 10
    
    return apps


# --- get_running_services (extracted from app.py) ---
def get_running_services():
    """Laufen Services"""
    services = [
        "nginx", "apache2", "mysql", "mariadb", "postgresql",
        "docker", "fail2ban", "sshd", "postfix", "dovecot",
        "mopidy", "grafana-server", "plexmediaserver",
    ]
    running = {}
    for service in services:
        result = run_command(f"systemctl is-active {service}")
        running[service] = result["success"]
    return running


# --- get_website_names (extracted from app.py) ---
def get_website_names():
    """Extrahiere Website-Namen aus Webserver-Konfigurationen"""
    websites = []
    
    # Nginx Konfigurationen
    nginx_sites = []
    nginx_result = run_command("find /etc/nginx/sites-enabled /etc/nginx/conf.d -name '*.conf' 2>/dev/null | head -10")
    if nginx_result["success"]:
        for conf_file in nginx_result["stdout"].strip().split("\n"):
            if conf_file.strip():
                server_name_result = run_command(f"grep -E 'server_name|server_name_' {conf_file} 2>/dev/null | head -5")
                if server_name_result["success"]:
                    for line in server_name_result["stdout"].split("\n"):
                        if "server_name" in line:
                            # Extrahiere Domain-Namen
                            parts = line.split()
                            for part in parts[1:]:
                                part = part.strip(';')
                                if part and part not in ['localhost', '_', 'default_server'] and '.' in part:
                                    nginx_sites.append(part)
    
    # Apache Konfigurationen
    apache_sites = []
    apache_result = run_command("find /etc/apache2/sites-enabled /etc/apache2/conf-enabled -name '*.conf' 2>/dev/null | head -10")
    if apache_result["success"]:
        for conf_file in apache_result["stdout"].strip().split("\n"):
            if conf_file.strip():
                server_name_result = run_command(f"grep -E 'ServerName|ServerAlias' {conf_file} 2>/dev/null | head -5")
                if server_name_result["success"]:
                    for line in server_name_result["stdout"].split("\n"):
                        parts = line.split()
                        if len(parts) >= 2:
                            domain = parts[1].strip()
                            if domain and domain not in ['localhost', '*'] and '.' in domain:
                                apache_sites.append(domain)
    
    # Kombiniere und entferne Duplikate
    all_sites = list(set(nginx_sites + apache_sites))
    return all_sites[:20]  # Maximal 20



def discover_running_services() -> dict[str, bool]:
    running = get_running_services()
    return running if isinstance(running, dict) else {}


def discover_frontend_port() -> int:
    return int(detect_frontend_port() or 3001)


def discover_installed_web_services() -> dict[str, Any]:
    installed = get_installed_apps()
    return installed if isinstance(installed, dict) else {}


def discover_webserver_stack() -> dict[str, Any]:
    """Ports and CMS-related stack probe (legacy webserver/status shape inputs)."""
    running = discover_running_services()
    installed = discover_installed_web_services()
    webserver_ports: list[str] = []
    ports_result = run_command("ss -tuln | grep -E ':80|:443|:8000|:8080|:9090|:10000'")
    if ports_result.get("success"):
        stdout = ports_result.get("stdout") or ""
        webserver_ports = stdout.strip().split("\n") if stdout.strip() else []
    cockpit_port = run_command("ss -tuln | grep ':9090'")
    webmin_port = run_command("ss -tuln | grep ':10000'")
    return {
        "running": running,
        "installed": installed,
        "webserver_ports": webserver_ports,
        "website_names": get_website_names(),
        "cockpit_port_probe": cockpit_port,
        "webmin_port_probe": webmin_port,
        "nginx_running": bool(running.get("nginx")),
        "apache_running": bool(running.get("apache2")),
        "cockpit_running": bool(running.get("cockpit")) or check_installed("cockpit"),
        "webmin_running": bool(running.get("webmin")) or check_installed("webmin"),
        "cockpit_port_open": bool(cockpit_port.get("success")),
        "webmin_port_open": bool(webmin_port.get("success")),
    }


def build_webserver_service_diagnostics() -> dict[str, Any]:
    return {
        "discovery_version": WEBSERVER_SERVICE_DISCOVERY_VERSION,
        "discovery_module": "core.webserver_service_discovery",
        "public_functions": [
            "discover_running_services",
            "discover_frontend_port",
            "discover_webserver_stack",
            "discover_installed_web_services",
            "build_webserver_service_diagnostics",
        ],
        "delegates_from_app_wrappers": [
            "check_installed",
            "get_installed_apps",
            "get_running_services",
            "get_website_names",
            "run_command",
        ],
        "frontend_port_via_network_discovery": True,
        "read_only": True,
        "writes_allowed": False,
    }
