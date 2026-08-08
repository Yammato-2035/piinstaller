# Evidence Mirror Gate — 009

## Result

**`evidence_mirror_gate=passed`**

## Tests

`backend/tests/test_highinfo_xorg_evidence_mirror_v1.py` (+ related 007/orchestrator): **23 passed**

Covered:

1. startx success + log  
2. startx failed + log  
3. startx failed without log  
4. startx never invoked  
5. SETUP_LOGS available  
6. SETUP_LOGS unavailable  
7. previous boot present / not overwritten  
8. stale classification  
9. boot_id preserved  
10. no secret fields  
11. no GUI-success dependency  

## Code

| Path | Role |
|------|------|
| `backend/rescue/highinfo_xorg_evidence.py` | record + mirror helpers |
| `scripts/rescue-live/image/setuphelfer-rescue-highinfo-boot.sh` | invokes startx, writes `xorg_probe_evidence.json`, mirrors to SETUP_LOGS |

Failed Xorg starts still produce persistable evidence (`startx_invoked=true`, exit code, optional log path). Never-invoked path records `reason=startx_not_invoked`.
