# Beta Registration FAQ (EN)

## What is collected?
Pseudonymous stick ID, hashed device fingerprint, redacted hardware/error summary after explicit consent.

## What is not collected?
No ID documents, no plaintext email in telemetry, no IP/MAC/serials, no file listings.

## Why verified sticks?
Only registered beta sticks may upload — abuse prevention.

## Why approve new computers?
Each new target machine stays `pending` until approved in the portal.

## Without beta agreement?
Telemetry is **quarantined** (max 14 days); no diagnostics export.

## Why no ID documents?
Data minimization — prefer Passkey/TOTP for MFA.

## Why WordPress is not root of trust?
Registration, MFA, and stick keys are handled only by the FastAPI beta service.
