# ASUS Lab Authorization Profile

Profile `ASUS_ROG_GABRIEL_LAB` is machine-bound (`config/lab-targets/asus-rog-gabriel.yaml`).

- Grants activate only on `exact_match` (manufacturer, G513QM, machine_id, system_uuid_hash).
- MSI / developer ASUS / unknown → no grants.
- Hostname/IP/USB alone never activate grants.
- Disk roles use `nvme_identity_hash`, never `/dev/nvmeXnY` alone.
- `bitlocker_mutation` is always `false`.
