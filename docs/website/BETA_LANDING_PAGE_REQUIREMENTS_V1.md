# Beta Landing Page Requirements V1

**Version:** 1.0 · **Host:** WordPress (`www.setuphelfer.de/beta` or equivalent)  
**Bridge:** `WORDPRESS_BETA_PORTAL_BRIDGE_V1.md`

---

## 1. Goals

The beta landing page recruits **informed** Rescue Stick testers. It must explain scope, privacy, and hardware requirements before users reach the registration portal.

---

## 2. Required sections (DE primary, EN mirror)

| Section | Content |
|---------|---------|
| Hero | Product name, one-line value proposition, primary CTA “Beta anmelden” |
| What you test | Rescue Stick live boot, read-only diagnostics, optional telemetry |
| What you do not get | No remote disk repair, no cloud backup in beta |
| Requirements | 64-bit PC, USB 16 GB+, UEFI recommended, internet for activation |
| Privacy | Link to privacy policy; telemetry opt-in explained; no ID documents |
| Timeline | Beta phase label, no guaranteed SLA |
| FAQ | 5–8 questions (activation, MFA, machine approval wait) |
| Legal | Impressum link, beta agreement link (on BR) |
| Footer CTA | Secondary button to documentation / rescue overview |

---

## 3. CTA behavior

Primary button:

```
https://beta.setuphelfer.de/register?utm_source=landing&utm_medium=cta
```

- Opens in same tab (HTTPS only).  
- No embedded iframe of BR login.  
- Track UTM in analytics (WP-side only, no stick data).

---

## 4. Visual assets

| Asset | Spec |
|-------|------|
| Hero image | Rescue stick + laptop, no real serial numbers visible |
| Screenshot | Kiosk UI with demo data only |
| Icons | Consistent with Setuphelfer brand guidelines |

Do not use customer machines or identifiable office backgrounds.

---

## 5. Copy constraints

- State that **machine approval** may delay telemetry upload.  
- State that **MFA is mandatory**.  
- Do not promise features marked “future” in architecture docs.  
- Avoid “we collect everything” — list categories at high level only.

---

## 6. Optional status banner

If `GET /public/v1/beta/status` returns:

```json
{ "registration_open": false, "mfa_required": true }
```

Show banner: “Registrierung derzeit geschlossen” and hide primary CTA.

Cache response 5 minutes (transient).

---

## 7. Accessibility

- WCAG 2.1 AA contrast for CTA buttons.  
- Alt text on all images.  
- DE/EN language switcher links equivalent anchors.

---

## 8. SEO / metadata

| Meta | Value |
|------|-------|
| `title` | Setuphelfer Beta — Rescue Stick Testprogramm |
| `description` | Teste den Setuphelfer Rescue Stick… (≤ 160 chars) |
| `robots` | `index, follow` (unless closed beta flag) |

---

## 9. Out of scope for landing page

- ISO direct download (BR only after auth).  
- Telemetry or diagnostics URLs.  
- Operator dashboard links.

---

## 10. Acceptance checklist

- [ ] DE + EN published  
- [ ] CTA reaches BR register route  
- [ ] Privacy + agreement links verified  
- [ ] No secrets in page source  
- [ ] Mobile layout tested  
- [ ] Status banner tested with mock 8100

---

## 11. Related documents

- `WORDPRESS_BETA_PORTAL_BRIDGE_V1.md`  
- `beta_stick_activation_flow.md`  
- `SETUPHELFER_BETA_SYSTEM_ARCHITECTURE_V1.md`
