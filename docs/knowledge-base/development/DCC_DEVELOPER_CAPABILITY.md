# DCC Developer Capability

## Kurz

DCC ist auf Developer-/Lab-Profilen **nur** mit gültigem `DCC_DEVELOPER_TOKEN` erreichbar. Release-Systeme bleiben ohne Token blockiert.

## Operator-Setup (Developer-System)

```bash
# Beispiel — Token-Wert lokal setzen, nicht committen
sudo install -d -m 0750 /etc/setuphelfer
sudo sh -c 'umask 077; printf "%s\n" "YOUR_DCC_TOKEN" > /etc/setuphelfer/developer.dcc.token'
sudo chmod 0640 /etc/setuphelfer/developer.dcc.token
export SETUPHELFER_INSTALL_PROFILE=developer
export DCC_DEVELOPER_TOKEN='YOUR_DCC_TOKEN'   # alternativ zur Datei
# Backend-Restart nur mit Operator-Freigabe
```

Frontend/API-Requests:

```http
X-Setuphelfer-Developer-Token: YOUR_DCC_TOKEN
```

oder

```http
Authorization: Bearer YOUR_DCC_TOKEN
```

## Diagnose

`GET /api/version` → `dcc_allowed`, `developer_capability_*` (ohne Secret).

## Nächster Schritt

Runtime-Smoke: Prompt `DEVELOPER_DCC_CAPABILITY_OPERATOR_SMOKE`
