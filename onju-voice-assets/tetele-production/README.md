# Production source snapshot

These components are the unmodified production Tetele ADF port for ESPHome
2026.10.0, including the latest dynamic S3 touch implementation. Prepare the
exact SDK using `tools/bootstrap_sdk.py` from the repository root. The SDK
manifest selects all 16 required ADF components; overlays preserve the existing
IDF compatibility patches and flash-resident confirmation sound.

No functional component changes are made for this publication. Only the public
YAML device name and network configuration are generalized. Touch is
implemented / build validated, physical hardware validation pending.
