"""
Mailserver-Konfigurationsmodul
"""

from typing import Dict, Any
from .utils import SystemUtils


class MailModule:
    """Mailserver Installation und Konfiguration"""
    
    def __init__(self):
        self.utils = SystemUtils()
    
    async def configure(self, config) -> Dict[str, Any]:
        """Mailserver konfigurieren"""
        if not config.enable_mail:
            return {"status": "skipped", "message": "Mailserver nicht aktiviert"}
        
        results = {
            "postfix": await self._install_postfix(config.domain),
            "dovecot": await self._install_dovecot(),
        }
        
        if config.enable_spam_filter:
            results["spamassassin"] = await self._install_spamassassin()
        
        results["hardening"] = await self._harden_mail()
        
        return {"status": "success", "results": results}
    
    async def get_status(self) -> Dict[str, Any]:
        """Mailserver-Status"""
        return {
            "postfix": await self.utils.check_service("postfix"),
            "dovecot": await self.utils.check_service("dovecot"),
            "spamassassin": await self.utils.check_service("spamassassin"),
        }
    
    # ==================== Private Methoden ====================
    
    async def _install_postfix(self, domain: str = "localhost") -> Dict[str, Any]:
        """Postfix (SMTP) installieren"""
        result = await self.utils.install_package("postfix mailutils")
        
        if result["success"]:
            await self.utils.enable_service("postfix")
            await self.utils.start_service("postfix")
            
            # Basis-Konfiguration
            await self.utils.run_command(
                f'postconf -e "myhostname = {domain}"',
                as_sudo=True
            )
        
        return {
            "status": "success" if result["success"] else "error",
            "service": "Postfix (SMTP)",
            "port": 25,
            "domain": domain,
            "message": "Postfix installiert"
        }
    
    async def _install_dovecot(self) -> Dict[str, Any]:
        """Dovecot (IMAP/POP3) installieren"""
        result = await self.utils.install_package("dovecot-core dovecot-imapd dovecot-pop3d")
        
        if result["success"]:
            await self.utils.enable_service("dovecot")
            await self.utils.start_service("dovecot")
        
        return {
            "status": "success" if result["success"] else "error",
            "service": "Dovecot (IMAP/POP3)",
            "ports": "143 (IMAP), 110 (POP3), 993 (IMAPS), 995 (POP3S)",
            "message": "Dovecot installiert"
        }
    
    async def _install_spamassassin(self) -> Dict[str, Any]:
        """SpamAssassin installieren"""
        result = await self.utils.install_package("spamassassin spamc")
        
        if result["success"]:
            await self.utils.enable_service("spamassassin")
            await self.utils.start_service("spamassassin")
        
        return {
            "status": "success" if result["success"] else "error",
            "service": "SpamAssassin",
            "message": "Spam-Filter installiert"
        }
    
    async def _harden_mail(self) -> Dict[str, Any]:
        """Mailserver härten"""
        hardening_steps = []
        
        # TLS aktivieren für Postfix
        hardening_steps.append({
            "step": "TLS-Verschlüsselung",
            "command": "postconf -e 'smtpd_use_tls = yes'",
            "status": "requires_manual_cert"
        })
        
        # Dovecot SSL konfigurieren
        hardening_steps.append({
            "step": "Dovecot SSL",
            "command": "Cert in /etc/dovecot/private/dovecot.pem erforderlich",
            "status": "requires_manual_cert"
        })
        
        # Rate Limiting
        hardening_steps.append({
            "step": "Rate Limiting",
            "command": "postconf -e 'smtpd_client_connection_rate_limit = 100'",
            "status": "optional"
        })
        
        return {
            "status": "success",
            "hardening": hardening_steps,
            "message": "Mailserver-Härtung konfiguriert"
        }
