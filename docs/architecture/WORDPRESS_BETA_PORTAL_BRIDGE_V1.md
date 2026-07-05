# WordPress Beta Portal Bridge V1

**Version:** 1.0 · **Scope:** Public marketing site ↔ private beta registration  
**Deploy plan:** `docs/deployment/WORDPRESS_BETA_BRIDGE_DEPLOYMENT_PLAN_V1.md`

---

## 1. Purpose

WordPress hosts the **public marketing** presence (`www.setuphelfer.de`). The beta bridge is a thin integration layer that routes interested users to `beta.setuphelfer.de` without exposing internal APIs, secrets, or telemetry endpoints on the CMS host.

---

## 2. Architecture

```
┌─────────────────┐         HTTPS redirect          ┌──────────────────┐
│  WordPress      │  ─────────────────────────────► │ beta.setuphelfer │
│  (www)          │   CTA buttons + deep links      │ .de (BR)         │
└─────────────────┘                                 └──────────────────┘
        │                                                    │
        │ REST (read-only, cached)                           │
        └──────── optional: /public/v1/beta/status ──────────┘
```

WordPress **never** calls telemetry or diagnostics hosts.

---

## 3. Bridge components

| Component | Location | Responsibility |
|-----------|----------|----------------|
| Landing blocks | WP theme / page builder | Copy, screenshots, legal links |
| Beta CTA plugin | Private build artifact | Signed redirect URLs |
| Status widget (optional) | Transient cache 5 min | `registration_open` flag |
| UTM tags | Query params | Campaign analytics |

---

## 4. Allowed WordPress → BR interactions

| Action | Method | Notes |
|--------|--------|-------|
| Open registration | 302 redirect | `https://beta.setuphelfer.de/register?utm_source=wp` |
| Open download page | 302 redirect | After login on BR, not direct from WP |
| Fetch public status | GET `/public/v1/beta/status` | No auth, rate-limited |

Forbidden: stick activation, ingest, internal APIs, operator routes.

---

## 5. Security requirements

- Store BR API base URL in WP config — **not** in public git.  
- No telemetry tokens in WP database.  
- Plugin updates signed; distribute via private package URL.  
- CSP on WP pages: no inline scripts from untrusted sources.

---

## 6. Content requirements

Landing content spec: `docs/website/BETA_LANDING_PAGE_REQUIREMENTS_V1.md`.

Must link:

- Beta participation agreement (hosted on BR)  
- Privacy policy (DE/EN)  
- Rescue Stick safety disclaimer  
- Contact for beta support (email only, no PII form on WP)

---

## 7. Failure modes

| Failure | User experience |
|---------|-----------------|
| BR down | CTA shows “registration temporarily unavailable” |
| Status fetch fails | Assume `registration_open: false` in widget |
| SSL mismatch | Hard fail — fix cert before campaign |

---

## 8. Staging

- WP staging subdomain: `staging.setuphelfer.de`  
- BR staging: `beta-staging.setuphelfer.de` (optional)  
- Never point staging WP at production BR without data isolation.

---

## 9. Related documents

- `BETA_LANDING_PAGE_REQUIREMENTS_V1.md`  
- `SERVICE_INTERACTION_MATRIX_V1.md`  
- `PUBLIC_PRIVATE_BOUNDARY_V1.md`
