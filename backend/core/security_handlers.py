"""
Security API handlers (Phase E.14) — scan, firewall, configure.

Extracted from app.py; delegates via security_runtime adapters.
"""

from __future__ import annotations

from fastapi import Request

from core import security_runtime as rt

async def security_scan():
    """Sicherheits-Scan durchführen"""
    try:
        running_services = rt.get_running_services()
        installed_apps = rt.get_installed_apps()
        
        # Prüfe offene Ports
        ports_result = rt.run_command("ss -tuln | grep LISTEN")
        open_ports = []
        if ports_result["success"]:
            for line in ports_result["stdout"].split("\n"):
                if line.strip():
                    # Parse Port aus Zeile
                    parts = line.split()
                    if len(parts) >= 5:
                        addr = parts[4]
                        if ":" in addr:
                            port = addr.split(":")[-1]
                            open_ports.append(port)
        
        # Prüfe geschlossene Ports (UFW) - verwende die gleiche Logik wie rt.get_security_config()
        ufw_status = rt.run_command("ufw status")
        if not ufw_status["success"] and rt.sudo_store().get_password():
            ufw_status = rt.run_command("ufw status", sudo=True, sudo_password=rt.sudo_store().get_password())
        
        # Falls immer noch nicht erfolgreich, versuche "ufw status verbose" mit sudo
        if not ufw_status["success"] and rt.sudo_store().get_password():
            ufw_status = rt.run_command("ufw status verbose", sudo=True, sudo_password=rt.sudo_store().get_password())
        
        closed_ports = []
        firewall_active = False
        status_output = ""
        
        if ufw_status["success"]:
            status_output = ufw_status.get("stdout", "")
            if "Status: active" in status_output or "Status: aktiv" in status_output:
                firewall_active = True
                # Parse UFW Rules
                for line in status_output.split("\n"):
                    if "DENY" in line or "REJECT" in line:
                        closed_ports.append(line.strip())
        else:
            # Alternative Methoden wie in rt.get_security_config()
            # Prüfe UFW-Konfigurationsdatei
            try:
                ufw_config_check = rt.run_command("grep -E '^ENABLED=' /etc/ufw/ufw.conf 2>/dev/null")
                if ufw_config_check["success"]:
                    config_line = ufw_config_check.get("stdout", "").strip()
                    if "ENABLED=yes" in config_line:
                        firewall_active = True
                        status_output = "Status: active (via /etc/ufw/ufw.conf)"
            except:
                pass
            
            # Prüfe systemd-Status
            if not firewall_active:
                systemd_status = rt.run_command("systemctl is-active ufw 2>/dev/null")
                if systemd_status["success"] and "active" in systemd_status.get("stdout", ""):
                    firewall_active = True
                    status_output = "Status: active (via systemctl)"
                else:
                    ufw_enabled = rt.run_command("systemctl is-enabled ufw 2>/dev/null")
                    if ufw_enabled["success"] and "enabled" in ufw_enabled.get("stdout", ""):
                        firewall_active = True
                        status_output = "Status: active (wahrscheinlich, service enabled)"
        
        # Prüfe fail2ban Status & Installation
        fail2ban_status = rt.run_command("fail2ban-client status")
        fail2ban_installed = rt.check_installed("fail2ban")
        fail2ban_running = running_services.get("fail2ban", False)
        
        # Updates kategorisieren
        updates_info = rt.get_updates_categorized()
        
        return {
            "status": "success",
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "running_services": running_services,
            "installed_packages": installed_apps,
            "open_ports": list(set(open_ports))[:20],  # Unique Ports
            "closed_ports": closed_ports[:10],
            "firewall": {
                "active": firewall_active,
                "ufw_installed": rt.check_installed("ufw"),
                "ufw_status": ufw_status.get("stdout", "") if ufw_status["success"] else "Nicht aktiv",
            },
            "fail2ban": {
                "installed": fail2ban_installed,
                "running": fail2ban_running,
                "active": fail2ban_installed and fail2ban_running,
                "status": fail2ban_status.get("stdout", "Nicht aktiv") if fail2ban_status["success"] else "Nicht installiert",
            },
            "updates": updates_info,
            "checks": {
                "firewall": {
                    "active": firewall_active,
                    "ufw_installed": rt.check_installed("ufw"),
                },
                "ssh": {
                    "running": running_services.get("sshd", False),
                    "installed": rt.check_installed("ssh"),
                },
                "nginx": {
                    "running": running_services.get("nginx", False),
                    "installed": installed_apps.get("nginx", False),
                },
                "apache": {
                    "running": running_services.get("apache2", False),
                    "installed": installed_apps.get("apache", False),
                },
                "fail2ban": {
                    "installed": fail2ban_installed,
                    "running": fail2ban_running,
                    "active": fail2ban_installed and fail2ban_running,
                },
                "updates_available": updates_info["total"] > 0,
            },
            "message": "Scan abgeschlossen"
        }
    except Exception as e:
        rt.http_exception(status_code=500, detail=str(e))


async def security_status():
    """Sicherheitsstatus"""
    try:
        return {
            "running_services": rt.get_running_services(),
            "installed_apps": rt.get_installed_apps(),
            "security_config": rt.get_security_config(),
        }
    except Exception as e:
        rt.http_exception(status_code=500, detail=str(e))


async def enable_firewall(request: Request):
    """Firewall aktivieren"""
    try:
        try:
            data = await request.json()
        except:
            data = {}
        
        sudo_password = data.get("sudo_password", "") or (rt.sudo_store().get_password() or "")
        
        # Speichere sudo-Passwort im Store für spätere Verwendung
        if sudo_password and not rt.sudo_store().has_password():
            rt.sudo_store().store_password(sudo_password)
            rt.logger().info("💾 Sudo-Passwort im Store gespeichert")
        
        rt.logger().info("🔥 Firewall-Aktivierung gestartet")
        
        # Prüfe ob UFW verfügbar ist (mehrere Methoden)
        ufw_installed = rt.check_installed("ufw")
        ufw_which = rt.run_command("which ufw")
        ufw_dpkg = rt.run_command("dpkg -l | grep '^ii' | grep -E '\\bufw\\b'")
        
        # Wenn keine Methode UFW findet, prüfe ob es installiert werden kann
        if not ufw_installed and not ufw_which["success"] and not ufw_dpkg["success"]:
            return rt.json_response(
                status_code=200,
                content={
                    "status": "error",
                    "message": "UFW ist nicht installiert. Bitte installieren Sie es zuerst mit: sudo apt install ufw",
                    "requires_installation": True,
                    "debug": {
                        "rt.check_installed": ufw_installed,
                        "which_result": ufw_which.get("stdout", ""),
                        "dpkg_result": ufw_dpkg.get("stdout", "")
                    }
                }
            )
        
        # Prüfe ob sudo-Passwort vorhanden ist
        if not sudo_password:
            sudo_test = rt.run_command("sudo -n true", sudo=False)
            if not sudo_test["success"]:
                return rt.json_response(
                    status_code=200,
                    content={
                        "status": "error",
                        "message": "Sudo-Passwort erforderlich",
                        "requires_sudo_password": True
                    }
                )
        
        # UFW aktivieren - versuche es direkt, auch wenn rt.check_installed False war
        # Verwende absoluten Pfad falls which ufw funktioniert hat
        ufw_path = "/usr/sbin/ufw"
        if ufw_which["success"]:
            ufw_path = ufw_which["stdout"].strip()
        
        # UFW aktivieren - verwende explizit den absoluten Pfad
        rt.logger().info(f"🔧 Versuche UFW zu aktivieren mit Pfad: {ufw_path}")
        result = rt.run_command(f"{ufw_path} --force enable", sudo=True, sudo_password=sudo_password)
        rt.logger().info(f"📊 Command Result: success={result.get('success')}, returncode={result.get('returncode')}, stdout={result.get('stdout', '')[:100]}, stderr={result.get('stderr', '')[:100]}")
        
        # Warte kurz, damit UFW den Status aktualisieren kann
        import time
        time.sleep(0.5)
        
        # Debug: Prüfe ob Command wirklich erfolgreich war
        # Prüfe den Status mit sudo (falls nötig)
        status_check = rt.run_command(f"{ufw_path} status", sudo=False)
        # Falls ohne sudo nicht funktioniert, versuche mit sudo
        if not status_check["success"]:
            status_check = rt.run_command(f"{ufw_path} status", sudo=True, sudo_password=sudo_password)
        
        status_output = status_check.get("stdout", "")
        is_actually_active = "Status: active" in status_output or "Status: aktiv" in status_output
        rt.logger().info(f"📋 Status Check: success={status_check.get('success')}, is_active={is_actually_active}, output={status_output[:200]}")
        
        if not result["success"]:
            rt.logger().error(f"❌ UFW Command fehlgeschlagen: {result.get('stderr', '')}")
            error_msg = result.get("stderr", result.get("error", "Unbekannter Fehler"))
            stdout_msg = result.get("stdout", "")
            
            return rt.json_response(
                status_code=200,
                content={
                    "status": "error",
                    "message": f"UFW-Befehl fehlgeschlagen: {error_msg}",
                    "debug": {
                        "command_result": result,
                        "status_check": status_check,
                        "ufw_path": ufw_path,
                        "stdout": stdout_msg,
                        "stderr": error_msg,
                    }
                }
            )
        
        # Wenn der Command erfolgreich war, aber Status nicht aktiv ist
        if result["success"] and not is_actually_active:
            rt.logger().warning("⚠️ Command erfolgreich, aber Firewall nicht aktiv. Versuche Retry...")
            # Versuche es nochmal ohne --force
            retry_result = rt.run_command(f"{ufw_path} enable", sudo=True, sudo_password=sudo_password)
            rt.logger().info(f"🔄 Retry Result: success={retry_result.get('success')}, returncode={retry_result.get('returncode')}, stdout={retry_result.get('stdout', '')[:100]}, stderr={retry_result.get('stderr', '')[:100]}")
            time.sleep(0.5)
            
            # Prüfe Status nochmal
            status_check_retry = rt.run_command(f"{ufw_path} status", sudo=False)
            if not status_check_retry["success"]:
                status_check_retry = rt.run_command(f"{ufw_path} status", sudo=True, sudo_password=sudo_password)
            
            status_output_retry = status_check_retry.get("stdout", "")
            is_actually_active_retry = "Status: active" in status_output_retry or "Status: aktiv" in status_output_retry
            rt.logger().info(f"📋 Retry Status Check: success={status_check_retry.get('success')}, is_active={is_actually_active_retry}, output={status_output_retry[:200]}")
            
            if not is_actually_active_retry:
                rt.logger().error(f"❌ Firewall konnte auch nach Retry nicht aktiviert werden. Status: {status_output_retry[:200]}")
                return rt.json_response(
                    status_code=200,
                    content={
                        "status": "error",
                        "message": f"UFW-Befehl wurde ausgeführt, aber Firewall ist nicht aktiv. Status-Output: {status_output_retry[:200]}",
                        "debug": {
                            "command_result": result,
                            "retry_result": retry_result,
                            "status_check": status_check,
                            "status_check_retry": status_check_retry,
                            "ufw_path": ufw_path,
                            "is_active": is_actually_active_retry,
                        }
                    }
                )
            
            # Prüfe ob UFW wirklich nicht gefunden wurde
            if "nicht gefunden" in error_msg.lower() or "not found" in error_msg.lower() or "command not found" in error_msg.lower():
                return rt.json_response(
                    status_code=200,
                    content={
                        "status": "error",
                        "message": "UFW ist nicht installiert. Bitte installieren Sie es zuerst mit: sudo apt install ufw",
                        "requires_installation": True,
                        "debug": {
                            "error": error_msg,
                            "stdout": result.get("stdout", ""),
                            "stderr": result.get("stderr", "")
                        }
                    }
                )
            
            if "password" in error_msg.lower() or "authentication" in error_msg.lower() or "sudo" in error_msg.lower():
                return rt.json_response(
                    status_code=200,
                    content={
                        "status": "error",
                        "message": "Sudo-Passwort falsch oder erforderlich",
                        "requires_sudo_password": True
                    }
                )
            return rt.json_response(
                status_code=200,
                content={
                    "status": "error",
                    "message": f"Firewall konnte nicht aktiviert werden: {error_msg}",
                    "debug": {
                        "stdout": result.get("stdout", ""),
                        "stderr": result.get("stderr", "")
                    }
                }
            )
        
        # Status abrufen (kann fehlschlagen, aber das ist OK)
        # Verwende sudo für status verbose, falls nötig
        status_result = rt.run_command(f"{ufw_path} status verbose", sudo=False)
        if not status_result["success"]:
            status_result = rt.run_command(f"{ufw_path} status verbose", sudo=True, sudo_password=sudo_password)
        
        rules_result = rt.run_command(f"{ufw_path} status numbered", sudo=False)
        if not rules_result["success"]:
            rules_result = rt.run_command(f"{ufw_path} status numbered", sudo=True, sudo_password=sudo_password)
        
        # Erstelle Security-Config direkt aus dem erfolgreichen Status-Check
        # (nicht aus rt.get_security_config(), da das möglicherweise den falschen Status zurückgibt)
        status_output = status_result.get("stdout", "") if status_result["success"] else ""
        is_active = "Status: active" in status_output or "Status: aktiv" in status_output or result["success"]
        
        # Hole die vollständige Security-Config, aber überschreibe UFW-Status mit dem korrekten Wert
        try:
            security_config = rt.get_security_config()
            # Überschreibe UFW-Status mit dem korrekten Wert
            security_config["ufw"] = {
                "installed": True,
                "active": is_active,
                "status": status_output if status_result["success"] else "Aktiviert",
                "rules": status_output.split("\n") if status_result["success"] else [],
            }
        except Exception as config_error:
            rt.logger().warning(f"⚠️ rt.get_security_config() fehlgeschlagen, verwende direkte Config: {config_error}")
            # Wenn rt.get_security_config fehlschlägt, verwende direkte Config
            security_config = {
                "ufw": {
                    "installed": True,
                    "active": is_active,
                    "status": status_output if status_result["success"] else "Aktiviert",
                    "rules": status_output.split("\n") if status_result["success"] else [],
                },
                "ssh": {"installed": False, "running": False, "config": ""},
                "fail2ban": {"installed": False, "running": False, "active": False, "status": "", "jails": []},
                "auto_updates": {"installed": False, "enabled": False},
            }
        
        rt.logger().info(f"✅ Firewall erfolgreich aktiviert! Security-Config UFW active: {security_config['ufw']['active']}")
        return {
            "status": "success",
            "message": "Firewall aktiviert",
            "firewall_status": status_output if status_result["success"] else "Aktiviert",
            "firewall_rules": rules_result.get("stdout", "").split("\n") if rules_result["success"] else [],
            "security_config": security_config,
        }
    except Exception as e:
        rt.logger().error(f"💥 Exception beim Aktivieren der Firewall: {str(e)}", exc_info=True)
        return rt.json_response(
            status_code=200,
            content={
                "status": "error",
                "message": f"Fehler beim Aktivieren der Firewall: {str(e)}"
            }
        )


async def install_firewall(request: Request):
    """UFW Firewall installieren"""
    try:
        try:
            data = await request.json()
        except:
            data = {}
        
        sudo_password = data.get("sudo_password", "") or (rt.sudo_store().get_password() or "")
        
        # Prüfe ob sudo-Passwort vorhanden ist
        if not sudo_password:
            sudo_test = rt.run_command("sudo -n true", sudo=False)
            if not sudo_test["success"]:
                return rt.json_response(
                    status_code=200,
                    content={
                        "status": "error",
                        "message": "Sudo-Passwort erforderlich",
                        "requires_sudo_password": True
                    }
                )
        
        # UFW installieren
        result = rt.run_command("apt-get install -y ufw", sudo=True, sudo_password=sudo_password)
        
        if not result["success"]:
            error_msg = result.get("stderr", result.get("error", "Unbekannter Fehler"))
            if "password" in error_msg.lower() or "authentication" in error_msg.lower() or "sudo" in error_msg.lower():
                return rt.json_response(
                    status_code=200,
                    content={
                        "status": "error",
                        "message": "Sudo-Passwort falsch oder erforderlich",
                        "requires_sudo_password": True
                    }
                )
            return rt.json_response(
                status_code=200,
                content={
                    "status": "error",
                    "message": f"UFW konnte nicht installiert werden: {error_msg}"
                }
            )
        
        return {
            "status": "success",
            "message": "UFW erfolgreich installiert"
        }
    except Exception as e:
        return rt.json_response(
            status_code=200,
            content={
                "status": "error",
                "message": str(e)
            }
        )


async def get_firewall_rules():
    """Firewall-Regeln abrufen"""
    try:
        sudo_password = (rt.sudo_store().get_password() or "")
        
        # UFW Status mit Regeln abrufen
        ufw_path = "/usr/sbin/ufw"
        ufw_which = rt.run_command("which ufw")
        if ufw_which["success"]:
            ufw_path = ufw_which["stdout"].strip()
        
        status_result = rt.run_command(f"{ufw_path} status numbered")
        if not status_result["success"] and sudo_password:
            status_result = rt.run_command(f"{ufw_path} status numbered", sudo=True, sudo_password=sudo_password)
        
        verbose_result = rt.run_command(f"{ufw_path} status verbose")
        if not verbose_result["success"] and sudo_password:
            verbose_result = rt.run_command(f"{ufw_path} status verbose", sudo=True, sudo_password=sudo_password)
        
        return {
            "status": "success",
            "rules": status_result.get("stdout", "") if status_result["success"] else "",
            "verbose": verbose_result.get("stdout", "") if verbose_result["success"] else "",
        }
    except Exception as e:
        return rt.json_response(
            status_code=200,
            content={
                "status": "error",
                "message": str(e)
            }
        )


async def add_firewall_rule(request: Request):
    """Firewall-Regel hinzufügen"""
    try:
        try:
            data = await request.json()
        except:
            data = {}
        
        sudo_password = data.get("sudo_password", "") or (rt.sudo_store().get_password() or "")
        rule = data.get("rule", "").strip()
        
        if not rule:
            return rt.json_response(
                status_code=200,
                content={
                    "status": "error",
                    "message": "Regel erforderlich"
                }
            )
        
        if not sudo_password:
            sudo_test = rt.run_command("sudo -n true", sudo=False)
            if not sudo_test["success"]:
                return rt.json_response(
                    status_code=200,
                    content={
                        "status": "error",
                        "message": "Sudo-Passwort erforderlich",
                        "requires_sudo_password": True
                    }
                )
        
        ufw_path = "/usr/sbin/ufw"
        ufw_which = rt.run_command("which ufw")
        if ufw_which["success"]:
            ufw_path = ufw_which["stdout"].strip()
        
        # Die Regel kommt bereits als vollständiger UFW-Command (z.B. "allow 22/tcp")
        # Füge nur den ufw-Pfad hinzu
        cmd = f"{ufw_path} {rule}"
        result = rt.run_command(cmd, sudo=True, sudo_password=sudo_password)
        
        if not result["success"]:
            error_msg = result.get("stderr", result.get("error", "Unbekannter Fehler"))
            return rt.json_response(
                status_code=200,
                content={
                    "status": "error",
                    "message": f"Regel konnte nicht hinzugefügt werden: {error_msg}"
                }
            )
        
        return {
            "status": "success",
            "message": "Regel hinzugefügt",
            "output": result.get("stdout", "")
        }
    except Exception as e:
        return rt.json_response(
            status_code=200,
            content={
                "status": "error",
                "message": str(e)
            }
        )


async def delete_firewall_rule(rule_number: int, request: Request):
    """Firewall-Regel löschen"""
    try:
        try:
            data = await request.json()
        except:
            data = {}
        
        sudo_password = data.get("sudo_password", "") or (rt.sudo_store().get_password() or "")
        
        if not sudo_password:
            sudo_test = rt.run_command("sudo -n true", sudo=False)
            if not sudo_test["success"]:
                return rt.json_response(
                    status_code=200,
                    content={
                        "status": "error",
                        "message": "Sudo-Passwort erforderlich",
                        "requires_sudo_password": True
                    }
                )
        
        ufw_path = "/usr/sbin/ufw"
        ufw_which = rt.run_command("which ufw")
        if ufw_which["success"]:
            ufw_path = ufw_which["stdout"].strip()
        
        # UFW-Regel löschen: ufw delete <number>
        cmd = f"{ufw_path} delete {rule_number}"
        result = rt.run_command(cmd, sudo=True, sudo_password=sudo_password)
        
        if not result["success"]:
            error_msg = result.get("stderr", result.get("error", "Unbekannter Fehler"))
            return rt.json_response(
                status_code=200,
                content={
                    "status": "error",
                    "message": f"Regel konnte nicht gelöscht werden: {error_msg}"
                }
            )
        
        return {
            "status": "success",
            "message": "Regel gelöscht",
            "output": result.get("stdout", "")
        }
    except Exception as e:
        return rt.json_response(
            status_code=200,
            content={
                "status": "error",
                "message": str(e)
            }
        )


async def configure_security(request: Request):
    """Sicherheitskonfiguration anwenden"""
    try:
        try:
            data = await request.json()
        except:
            data = {}
        
        sudo_password = data.get("sudo_password", "") or (rt.sudo_store().get_password() or "")
        config = data.get("config", {})
        
        # Speichere sudo-Passwort im Store für spätere Verwendung
        if data.get("sudo_password") and not rt.sudo_store().has_password():
            rt.sudo_store().store_password(data.get("sudo_password") or "")
            rt.logger().info("💾 Sudo-Passwort im Store gespeichert (via security/configure)")
        
        # Prüfe ob sudo-Passwort vorhanden ist
        if not sudo_password:
            sudo_test = rt.run_command("sudo -n true", sudo=False)
            if not sudo_test["success"]:
                return rt.json_response(
                    status_code=200,
                    content={
                        "status": "error",
                        "message": "Sudo-Passwort erforderlich",
                        "requires_sudo_password": True
                    }
                )
        
        results = []
        
        # Firewall aktivieren
        if config.get("enable_firewall"):
            # Prüfe ob UFW installiert ist
            ufw_installed = rt.check_installed("ufw")
            if not ufw_installed:
                # Installiere UFW
                install_result = rt.run_command("apt-get install -y ufw", sudo=True, sudo_password=sudo_password)
                if install_result["success"]:
                    results.append("UFW installiert")
                else:
                    return rt.json_response(
                        status_code=200,
                        content={
                            "status": "error",
                            "message": f"UFW konnte nicht installiert werden: {install_result.get('stderr', 'Unbekannter Fehler')}"
                        }
                    )
            else:
                results.append("UFW bereits installiert")
            
            # Prüfe ob UFW bereits aktiv ist
            ufw_status_check = rt.run_command("ufw status", sudo=False)
            if not ufw_status_check["success"]:
                ufw_status_check = rt.run_command("ufw status", sudo=True, sudo_password=sudo_password)
            
            is_already_active = False
            if ufw_status_check["success"]:
                status_output = ufw_status_check.get("stdout", "")
                is_already_active = "Status: active" in status_output or "Status: aktiv" in status_output
            
            # Aktiviere UFW nur wenn nicht bereits aktiv
            if not is_already_active:
                enable_result = rt.run_command("ufw --force enable", sudo=True, sudo_password=sudo_password)
                if enable_result["success"]:
                    results.append("Firewall aktiviert")
                else:
                    results.append(f"Firewall-Aktivierung fehlgeschlagen: {enable_result.get('stderr', 'Unbekannter Fehler')}")
            else:
                results.append("Firewall bereits aktiv")
        
        # Fail2Ban installieren/aktivieren
        if config.get("enable_fail2ban"):
            fail2ban_installed = rt.check_installed("fail2ban")
            if not fail2ban_installed:
                install_result = rt.run_command("apt-get install -y fail2ban", sudo=True, sudo_password=sudo_password)
                if install_result["success"]:
                    results.append("Fail2Ban installiert")
            else:
                results.append("Fail2Ban bereits installiert")
            
            # Prüfe ob Fail2Ban bereits läuft
            fail2ban_running = rt.get_running_services().get("fail2ban", False)
            
            # Fail2Ban starten nur wenn nicht bereits aktiv
            if not fail2ban_running:
                start_result = rt.run_command("systemctl enable --now fail2ban", sudo=True, sudo_password=sudo_password)
                if start_result["success"]:
                    results.append("Fail2Ban aktiviert")
                else:
                    results.append(f"Fail2Ban-Aktivierung fehlgeschlagen: {start_result.get('stderr', 'Unbekannter Fehler')}")
            else:
                results.append("Fail2Ban bereits aktiv")
        
        # Auto-Updates aktivieren
        if config.get("enable_auto_updates"):
            auto_updates_installed = rt.check_installed("unattended-upgrades")
            if not auto_updates_installed:
                install_result = rt.run_command("apt-get install -y unattended-upgrades", sudo=True, sudo_password=sudo_password)
                if install_result["success"]:
                    results.append("Auto-Updates installiert")
            else:
                results.append("Auto-Updates bereits installiert")
            
            # Prüfe ob Auto-Updates bereits aktiviert sind
            auto_updates_enabled = rt.run_command("systemctl is-enabled unattended-upgrades 2>/dev/null")
            if not auto_updates_enabled["success"]:
                enable_result = rt.run_command("systemctl enable unattended-upgrades", sudo=True, sudo_password=sudo_password)
                if enable_result["success"]:
                    results.append("Auto-Updates aktiviert")
                else:
                    results.append(f"Auto-Updates-Aktivierung fehlgeschlagen: {enable_result.get('stderr', 'Unbekannter Fehler')}")
            else:
                results.append("Auto-Updates bereits aktiviert")
        
        # SSH Härtung
        if config.get("enable_ssh_hardening"):
            try:
                ssh_config_file = "/etc/ssh/sshd_config"
                ssh_backup_file = "/etc/ssh/sshd_config.backup"
                
                # Erstelle Backup
                backup_result = rt.run_command(f"cp {ssh_config_file} {ssh_backup_file}", sudo=True, sudo_password=sudo_password)
                if not backup_result["success"]:
                    results.append("⚠️ SSH Backup konnte nicht erstellt werden")
                else:
                    results.append("SSH Backup erstellt")
                
                # SSH-Konfiguration härten
                ssh_hardening_commands = [
                    # Deaktiviere Root-Login
                    f"sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' {ssh_config_file}",
                    # Deaktiviere Passwort-Authentifizierung (nur Key-basiert)
                    f"sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' {ssh_config_file}",
                    # Aktiviere Public Key Authentication
                    f"sed -i 's/^#*PubkeyAuthentication.*/PubkeyAuthentication yes/' {ssh_config_file}",
                    # Deaktiviere leere Passwörter
                    f"sed -i 's/^#*PermitEmptyPasswords.*/PermitEmptyPasswords no/' {ssh_config_file}",
                    # Max Auth Tries begrenzen
                    f"sed -i 's/^#*MaxAuthTries.*/MaxAuthTries 3/' {ssh_config_file}",
                    # Client Alive Interval setzen
                    f"sed -i 's/^#*ClientAliveInterval.*/ClientAliveInterval 300/' {ssh_config_file}",
                    f"sed -i 's/^#*ClientAliveCountMax.*/ClientAliveCountMax 2/' {ssh_config_file}",
                    # Deaktiviere X11 Forwarding (falls nicht benötigt)
                    f"sed -i 's/^#*X11Forwarding.*/X11Forwarding no/' {ssh_config_file}",
                ]
                
                # Führe alle SSH-Härtungsbefehle aus
                ssh_hardening_success = True
                for cmd in ssh_hardening_commands:
                    result = rt.run_command(cmd, sudo=True, sudo_password=sudo_password)
                    if not result["success"]:
                        ssh_hardening_success = False
                        rt.logger().warning(f"SSH Härtung Befehl fehlgeschlagen: {cmd}")
                
                # Füge zusätzliche Sicherheitseinstellungen hinzu, falls sie nicht existieren
                additional_settings = [
                    "Protocol 2",
                    "PermitRootLogin no",
                    "PasswordAuthentication no",
                    "PubkeyAuthentication yes",
                    "PermitEmptyPasswords no",
                    "MaxAuthTries 3",
                    "ClientAliveInterval 300",
                    "ClientAliveCountMax 2",
                    "X11Forwarding no",
                ]
                
                for setting in additional_settings:
                    key = setting.split()[0]
                    # Prüfe ob die Einstellung bereits existiert
                    check_cmd = f"grep -q '^{key}' {ssh_config_file} || echo '{setting}' >> {ssh_config_file}"
                    rt.run_command(check_cmd, sudo=True, sudo_password=sudo_password)
                
                # Teste SSH-Konfiguration
                test_result = rt.run_command("sshd -t", sudo=True, sudo_password=sudo_password)
                if test_result["success"]:
                    # SSH-Service neu laden
                    reload_result = rt.run_command("systemctl reload sshd", sudo=True, sudo_password=sudo_password)
                    if reload_result["success"]:
                        results.append("SSH Härtung erfolgreich angewendet")
                    else:
                        results.append("⚠️ SSH Härtung angewendet, aber Service konnte nicht neu geladen werden")
                else:
                    results.append(f"⚠️ SSH-Konfiguration fehlerhaft: {test_result.get('stderr', 'Unbekannter Fehler')}")
                    # Stelle Backup wieder her
                    restore_result = rt.run_command(f"cp {ssh_backup_file} {ssh_config_file}", sudo=True, sudo_password=sudo_password)
                    if restore_result["success"]:
                        results.append("SSH-Konfiguration aus Backup wiederhergestellt")
            except Exception as e:
                rt.logger().error(f"Fehler bei SSH Härtung: {e}")
                results.append(f"SSH Härtung fehlgeschlagen: {str(e)}")
        
        # Audit Logging
        if config.get("enable_audit_logging"):
            try:
                # Installiere auditd falls nicht vorhanden
                auditd_installed = rt.check_installed("auditd")
                if not auditd_installed:
                    rt.logger().info("🔧 Versuche Auditd zu installieren...")
                    # PackageKit stoppen, um Konflikte zu vermeiden
                    rt.ensure_packagekit_stopped(sudo_password)
                    # Führe apt-get update separat aus (kann länger dauern)
                    update_result = rt.run_command("apt-get update", sudo=True, sudo_password=sudo_password)
                    if not update_result["success"]:
                        rt.logger().warning(f"⚠️ apt-get update fehlgeschlagen: {update_result.get('stderr', '')[:200]}")
                    
                    # Installiere auditd
                    install_result = rt.run_command("apt-get install -y auditd audispd-plugins", sudo=True, sudo_password=sudo_password)
                    if install_result["success"]:
                        results.append("Auditd installiert")
                        rt.logger().info("✅ Auditd erfolgreich installiert")
                    else:
                        error_msg = install_result.get("stderr", install_result.get("error", "Unbekannter Fehler"))
                        stdout_msg = install_result.get("stdout", "")
                        rt.logger().error(f"❌ Auditd Installation fehlgeschlagen. Stderr: {error_msg[:200]}, Stdout: {stdout_msg[:200]}")
                        results.append(f"⚠️ Auditd konnte nicht installiert werden: {error_msg[:100]}")
                        # Versuche es mit einem einfacheren Befehl
                        rt.logger().info("🔧 Versuche Auditd mit einfacherem Befehl zu installieren...")
                        simple_install = rt.run_command("apt-get install -y auditd", sudo=True, sudo_password=sudo_password)
                        if simple_install["success"]:
                            results.append("Auditd installiert (ohne Plugins)")
                            rt.logger().info("✅ Auditd erfolgreich installiert (ohne Plugins)")
                        else:
                            simple_error = simple_install.get("stderr", simple_install.get("error", "Unbekannter Fehler"))
                            rt.logger().error(f"❌ Auditd Installation auch mit einfachem Befehl fehlgeschlagen: {simple_error[:200]}")
                            return rt.json_response(
                                status_code=200,
                                content={
                                    "status": "error",
                                    "message": f"Auditd konnte nicht installiert werden. Fehler: {simple_error[:200]}. Bitte manuell installieren mit: sudo apt-get install -y auditd",
                                    "results": results,
                                    "debug": {
                                        "stderr": error_msg[:500],
                                        "stdout": stdout_msg[:500],
                                        "simple_stderr": simple_error[:500]
                                    }
                                }
                            )
                else:
                    results.append("Auditd bereits installiert")
                
                # Aktiviere auditd Service
                enable_result = rt.run_command("systemctl enable --now auditd", sudo=True, sudo_password=sudo_password)
                if enable_result["success"]:
                    results.append("Auditd Service aktiviert")
                else:
                    results.append("⚠️ Auditd Service konnte nicht aktiviert werden")
                
                # Konfiguriere Audit-Regeln
                audit_rules_file = str(rt.audit_rules_path())
                audit_rules = [
                    "# Setuphelfer Audit Rules",
                    "# Überwache alle Systemaufrufe",
                    "-a always,exit -F arch=b64 -S adjtimex -S settimeofday -k time-change",
                    "-a always,exit -F arch=b32 -S adjtimex -S settimeofday -S stime -k time-change",
                    "-a always,exit -F arch=b64 -S clock_settime -k time-change",
                    "-a always,exit -F arch=b32 -S clock_settime -k time-change",
                    "-w /etc/localtime -p wa -k time-change",
                    "",
                    "# Überwache Benutzer- und Gruppenänderungen",
                    "-w /etc/group -p wa -k identity",
                    "-w /etc/passwd -p wa -k identity",
                    "-w /etc/gshadow -p wa -k identity",
                    "-w /etc/shadow -p wa -k identity",
                    "-w /etc/security/opasswd -p wa -k identity",
                    "",
                    "# Überwache Netzwerkänderungen",
                    "-a always,exit -F arch=b64 -S sethostname -S setdomainname -k system-locale",
                    "-a always,exit -F arch=b32 -S sethostname -S setdomainname -k system-locale",
                    "-w /etc/issue -p wa -k system-locale",
                    "-w /etc/issue.net -p wa -k system-locale",
                    "-w /etc/hosts -p wa -k system-locale",
                    "-w /etc/sysconfig/network -p wa -k system-locale",
                    "",
                    "# Überwache Login/Logout",
                    "-w /var/log/faillog -p wa -k logins",
                    "-w /var/log/lastlog -p wa -k logins",
                    "-w /var/log/tallylog -p wa -k logins",
                    "",
                    "# Überwache Sudo-Befehle",
                    "-w /usr/bin/sudo -p x -k actions",
                    "-w /etc/sudoers -p wa -k actions",
                    "-w /etc/sudoers.d/ -p wa -k actions",
                    "",
                    "# Überwache Dateisystemänderungen",
                    "-w /etc -p wa -k etc",
                    "-w /usr/bin -p wa -k bin",
                    "-w /usr/sbin -p wa -k sbin",
                    "",
                    "# Überwache privilegierte Befehle",
                    "-a always,exit -F arch=b64 -S mount -S umount2 -k mount",
                    "-a always,exit -F arch=b32 -S mount -S umount -k mount",
                ]
                
                # Schreibe Audit-Regeln
                rules_content = "\n".join(audit_rules) + "\n"
                write_cmd = f"cat > {audit_rules_file} << 'EOF'\n{rules_content}EOF"
                write_result = rt.run_command(write_cmd, sudo=True, sudo_password=sudo_password)
                
                if write_result["success"]:
                    results.append("Audit-Regeln konfiguriert")
                    
                    # Lade Audit-Regeln neu
                    reload_result = rt.run_command("augenrules --load", sudo=True, sudo_password=sudo_password)
                    if reload_result["success"]:
                        results.append("Audit-Regeln geladen")
                    else:
                        results.append("⚠️ Audit-Regeln konnten nicht geladen werden")
                    
                    # Starte auditd neu
                    restart_result = rt.run_command("systemctl restart auditd", sudo=True, sudo_password=sudo_password)
                    if restart_result["success"]:
                        results.append("Auditd neu gestartet")
                else:
                    results.append(f"⚠️ Audit-Regeln konnten nicht geschrieben werden: {write_result.get('stderr', 'Unbekannter Fehler')}")
                    
            except Exception as e:
                rt.logger().error(f"Fehler bei Audit Logging: {e}")
                results.append(f"Audit Logging fehlgeschlagen: {str(e)}")
        
        # Wenn keine Ergebnisse, aber Konfiguration wurde angewendet, füge Info hinzu
        if not results:
            # Prüfe welche Features bereits aktiviert sind
            active_features = []
            if config.get("enable_firewall"):
                ufw_installed = rt.check_installed("ufw")
                if ufw_installed:
                    ufw_status_check = rt.run_command("ufw status", sudo=False)
                    if not ufw_status_check["success"] and sudo_password:
                        ufw_status_check = rt.run_command("ufw status", sudo=True, sudo_password=sudo_password)
                    if ufw_status_check["success"]:
                        status_text = ufw_status_check.get("stdout", "")
                        if "Status: active" in status_text or "Status: aktiv" in status_text:
                            active_features.append("Firewall bereits aktiv")
            
            if config.get("enable_fail2ban"):
                fail2ban_installed = rt.check_installed("fail2ban")
                fail2ban_running = rt.get_running_services().get("fail2ban", False)
                if fail2ban_installed and fail2ban_running:
                    active_features.append("Fail2Ban bereits aktiv")
            
            if config.get("enable_auto_updates"):
                auto_updates_installed = rt.check_installed("unattended-upgrades")
                auto_updates_enabled = rt.run_command("systemctl is-enabled unattended-upgrades 2>/dev/null")
                if auto_updates_installed and auto_updates_enabled["success"]:
                    active_features.append("Auto-Updates bereits aktiviert")
            
            if config.get("enable_ssh_hardening"):
                # Prüfe ob SSH bereits gehärtet ist
                ssh_backup_exists = rt.run_command("test -f /etc/ssh/sshd_config.backup")
                if ssh_backup_exists["success"]:
                    active_features.append("SSH Härtung bereits angewendet")
            
            if config.get("enable_audit_logging"):
                auditd_installed = rt.check_installed("auditd")
                auditd_running = rt.get_running_services().get("auditd", False)
                if auditd_installed and auditd_running:
                    active_features.append("Audit Logging bereits aktiv")
            
            if active_features:
                results.extend(active_features)
            else:
                results.append("Alle ausgewählten Features sind bereits konfiguriert")
        
        return {
            "status": "success",
            "message": "Konfiguration angewendet",
            "results": results
        }
    except Exception as e:
        return rt.json_response(
            status_code=200,
            content={
                "status": "error",
                "message": str(e)
            }
        )
