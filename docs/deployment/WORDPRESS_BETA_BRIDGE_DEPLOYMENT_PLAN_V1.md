# WordPress Beta Bridge Deployment Plan V1

**Version:** 1.0 · **Target:** `www.setuphelfer.de` (WordPress)  
**Architecture:** `WORDPRESS_BETA_PORTAL_BRIDGE_V1.md`

---

## 1. Objective

Deploy the WordPress plugin and landing page templates that link to the beta registration portal without storing secrets or enabling server-side telemetry.

---

## 2. Components to deploy

| Artifact | Source | Destination |
|----------|--------|-------------|
| Beta CTA plugin ZIP | Private CI build | `wp-content/plugins/setuphelfer-beta-bridge/` |
| Landing page template | Theme child or block pattern | Page slug `/beta` |
| Config constants | Plesk wp-config.php snippet | `SETUPHELFER_BETA_URL` |

---

## 3. Plugin configuration (no secrets in repo)

```php
// wp-config.php (example — values set on server only)
define('SETUPHELFER_BETA_BASE_URL', 'https://beta.setuphelfer.de');
define('SETUPHELFER_BETA_STATUS_URL', 'https://beta.setuphelfer.de/public/v1/beta/status');
define('SETUPHELFER_BETA_STATUS_CACHE_TTL', 300);
```

Plugin reads constants; provides:

- Shortcode `[setuphelfer_beta_cta]`  
- Optional status banner shortcode  
- Admin settings page (URL override for staging)

---

## 4. Plesk WordPress toolkit steps

1. Backup existing site (files + DB).  
2. Upload plugin ZIP via WP admin → Plugins → Add New.  
3. Activate **Setuphelfer Beta Bridge**.  
4. Create page **Beta** using block pattern from `BETA_LANDING_PAGE_REQUIREMENTS_V1.md`.  
5. Insert CTA shortcode in hero block.  
6. Flush permalinks.  
7. Verify DE/EN Polylang/WPML pages if multilingual plugin active.

---

## 5. Content publish checklist

- [ ] Hero + requirements sections complete  
- [ ] Privacy policy links resolve  
- [ ] Impressum linked  
- [ ] No ISO download links on WP  
- [ ] UTM parameters on CTA  
- [ ] Status banner tested (open/closed)

---

## 6. Staging workflow

| Environment | BR target |
|-------------|-----------|
| staging.setuphelfer.de | beta-staging.setuphelfer.de |
| production www | beta.setuphelfer.de |

Use separate `SETUPHELFER_BETA_BASE_URL` per vhost in Plesk.

---

## 7. Security

- Plugin from signed ZIP only; verify checksum in deploy runbook.  
- Disable file editor in wp-config: `DISALLOW_FILE_EDIT`.  
- Keep WP core and plugins updated via Plesk advisor.

---

## 8. Monitoring

- Uptime on `/beta` page.  
- Weekly link check: CTA → BR register returns 200.  
- No server-side cron calling internal BR APIs except cached status GET.

---

## 9. Rollback

Deactivate plugin; restore page revision from before deploy. No database migration required for bridge-only deploy.

---

## 10. Related documents

- `BETA_LANDING_PAGE_REQUIREMENTS_V1.md`  
- `BETA_PORTAL_IONOS_PLESK_DEPLOYMENT_PLAN_V1.md`  
- `PUBLIC_PRIVATE_BOUNDARY_V1.md`
