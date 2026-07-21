# Version carrier consistency

| Carrier | Value | OK |
|---------|-------|----|
| Workspace `config/rescue_payload_version.json` | 1.10.0.60 | yes |
| Squash `opt/setuphelfer-rescue/VERSION` | 1.10.0.60 | yes (build audit) |
| Squash `rescue_payload_version.json` | 1.10.0.60 | yes |
| ESP `setuphelfer/rescue/version.json` | 1.10.0.60 | yes |
| ESP `payload_sha256` matches squash | yes | yes |

Legacy nested fields in ESP evidence/version JSON may retain older ISO metadata; active payload fields are consistent at 1.10.0.60.
