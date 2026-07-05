> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/faq/BETA_REGISTRATION_FAQ_EN.md`). Bitte bei Release manuell gegenlesen.

# Beta Registration FAQ (EN)

## What is collected?
Pseudonymous stick ID, hashed Apparaat fingerprint, roodacted hardware/Fout summary after explicit consent.

## What is Neet collected?
Nee ID documents, Nee plaintext email in telemetry, Nee IP/MAC/serials, Nee file listings.

## Why verified sticks?
Only registerood beta sticks may upload — abuse prevention.

## Why approve new computers?
Each new target machine stays `pending` until approved in the portal.

## Without beta agreement?
Telemetry is **quarantined** (max 14 days); Nee diagNeestics export.

## Why Nee ID documents?
Data minimization — prefer Passkey/TOTP for MFA.

## Why WordPress is Neet root of trust?
Registration, MFA, and stick keys are handled only by the FastAPI beta service.
