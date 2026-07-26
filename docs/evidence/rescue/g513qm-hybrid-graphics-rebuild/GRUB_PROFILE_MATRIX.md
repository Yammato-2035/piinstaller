# GRUB profile matrix (G513QM hybrid rebuild)

| Order | Title | Profile ID | nomodeset | AMD | NVIDIA | Auto installer |
|------:|-------|------------|-----------|-----|--------|----------------|
| 0 (default) | Rescue Hybrid Auto (AMD display) | g513qm_hybrid_auto | no | KMS on | may load | no |
| 1 | AMD Safe Display | g513qm_amd_safe | no | KMS on | blacklisted | no |
| 2 | NVIDIA Proprietary Diagnostic | g513qm_nvidia_prop_diag | no | available | prop attempt | no |
| 3 | Nouveau Fallback Diagnostic | g513qm_nouveau_fallback | no | available | nouveau | no |
| 4 | Basic Graphics Emergency | g513qm_basic_emergency | **yes** | off | off | no |
| 5 | Capture Only / Text | g513qm_capture_only | yes | off | off | no |

Config: `config/rescue/g513qm_graphics_profiles.json`  
Generator: `backend/core/rescue_install_assistant_grub.py`

MSI Lab-Auto remains demoted warning entry (unchanged intent).
