"""
Minimale Anti-Regression-Prüfungen.
Lauf mit: cd backend && python -m unittest tests.test_anti_regression -v

Ergänzt vorhandene Teststruktur; keine neue Architektur.
"""

import unittest
from pathlib import Path

import sys
_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))


class TestConfigPathRegression(unittest.TestCase):
    """
    REGRESSION-RISK: Runtime liest ausschließlich config.json.
    Installer und Doku wurden auf config.json umgestellt (Audit A-03).
    Statische Prüfung: _config_path() darf nur .json referenzieren, nicht .yaml.
    """

    def test_config_path_references_json_not_yaml(self):
        app_file = _backend / "app.py"
        content = app_file.read_text(encoding="utf-8")
        # _config_path soll config.json verwenden, nicht config.yaml
        self.assertIn(
            "config.json",
            content,
            "app.py muss config.json als Config-Pfad verwenden (Anti-Regression)"
        )
        # Wenn config.yaml in _config_path oder CONFIG_PATH vorkommt, wäre das Regression
        def_path_section = ""
        for line in content.splitlines():
            if "def _config_path" in line:
                def_path_section = line
                break
        # Sicherstellen, dass die zentrale Config-Logik nicht auf .yaml umgestellt wurde
        idx = content.find("def _config_path()")
        if idx >= 0:
            snippet = content[idx:idx + 800]
            self.assertIn(
                "config.json",
                snippet,
                "_config_path() muss config.json verwenden (Anti-Regression)"
            )


class TestNoDuplicateBackupVerifyRoute(unittest.TestCase):
    """
    REGRESSION-RISK: POST /api/backup/verify war doppelt definiert (Audit A-02).
    Seit Phase B.8 liegt die Definition in api.routes.backup_execute; der Handler bleibt in
    core.backup_execute_handlers.verify_backup.
    """

    def test_backup_verify_route_defined_only_once(self):
        from app import app

        registered = [
            r
            for r in app.routes
            if getattr(r, "path", "") == "/api/backup/verify"
            and "POST" in (getattr(r, "methods", None) or set())
        ]
        self.assertEqual(
            len(registered),
            1,
            "Route POST /api/backup/verify soll im App-Router genau einmal registriert sein "
            f"(Anti-Regression). Gefunden: {len(registered)}",
        )

        app_file = _backend / "app.py"
        router_file = _backend / "api" / "routes" / "backup_execute.py"
        app_marker = '@app.post("/api/backup/verify")'
        router_marker = '@router.post("/api/backup/verify")'
        definition_count = app_file.read_text(encoding="utf-8").count(app_marker) + router_file.read_text(
            encoding="utf-8"
        ).count(router_marker)
        self.assertEqual(
            definition_count,
            1,
            "Route POST /api/backup/verify soll exakt einmal definiert sein (Anti-Regression). "
            f"Gefunden: {definition_count}",
        )
