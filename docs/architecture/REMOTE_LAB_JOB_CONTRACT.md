# Remote Lab Job Contract

Extends existing `rescue_remote` with ASUS-bound jobs (`backend/core/rescue_lab_job_contract.py`).

Required fields: `target_profile=ASUS_ROG_GABRIEL_LAB`, fingerprint, action_type, risk_class, expiry, nonce, signature.

- Wrong profile / expired / replay / bad signature → blocked.
- Shell allowed only after exact identity match; BitLocker mutation patterns denied.
- States include `waiting_for_reboot` / `reconnected` for continuity.
- UI notice: Freigabe gilt nur für ASUS_ROG_GABRIEL_LAB.
