# Rescue Agent E2EE Transport (Contract + Stub)

Status: **Contract/Stubs vorhanden**, nicht als produktive Kryptografie freigegeben.

## Warum E2EE zusätzlich zu TLS

- TLS schützt Transportkanal, E2EE schützt Payload-Endpunkte zusätzlich
- Verringert Risiko durch Proxy/Terminierungspunkte
- Ermöglicht klare Agent↔Server-Vertrauensgrenze pro Session

## Envelope

- `envelope_version=1.0`
- `alg=X25519-Ed25519-AEAD` (vertraglich reserviert)
- `sender_public_key`, `recipient_key_id`, `nonce`, `ciphertext`, `aad`

## Sicherheitsvorgaben

- Kein Klartext-Report im Envelope speichern
- Unverschlüsselter Fallback blockiert
- Replay-Schutz als nächster Pflichtschritt dokumentiert

## Nächste Pflichtaktion

- Verbindliche Library-Auswahl und echte Nonce-/Replay-Persistenz
