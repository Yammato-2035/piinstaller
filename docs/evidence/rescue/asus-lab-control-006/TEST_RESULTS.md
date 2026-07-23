# TEST_RESULTS — PI-RS-ASUS-LAB-CONTROL-006

```text
python3 -m pytest \
  backend/tests/test_rescue_asus_lab_control_006_v1.py \
  backend/tests/test_rescue_asus_rog_boot_profile_v1.py -q
→ 27 passed
```

Abgedeckt u. a.: exact ASUS match, MSI/Dev block, Hostname unzureichend, BitLocker RO vs Mutation,
Run-ID-Gate, SETUP_LOGS Label, Heartbeat/Finalize, Job Signatur/Replay/Expiry/Cancel,
Disk-Fingerprint + unconfirmed roles, Payload-Flag `1.10.3.1`.

Payload Stick: `1.10.3.1` sha256 `56a37200d7c3c72ead3f9fd8584a57fa36b4e578013b64e6a8d38d3d76491026`
