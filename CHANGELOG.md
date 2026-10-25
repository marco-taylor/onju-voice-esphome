# Changelog

## Pre-hardware-test timer milestone — 2026-10-25

- Publish the current production timer adapter, native timer callbacks and
  proportional countdown based on the earliest active timer.
- Add Timer LED (default ON), repeated local flash MP3 alarm, immediate
  Center-touch dismissal and normal media STOP handling, including silent gaps.
- Retain the Tetele 16-kHz ADF audio path, DC correction, runtime gain, three
  wakewords, two native slots, existing MWW→VA handover/END/ERROR recovery,
  local confirmation tone, Assist delay, listening light, dynamic touch and
  native volume. No functional changes for this publication.
- Preserve exact SDK inputs through the updated hash manifest and source overlays.
- **BUILD VALIDATED:** Config PASS, Codegen PASS, Clean Build PASS with
  ESPHome 2026.10.0; see [./docs/VALIDATION.md](./docs/VALIDATION.md).
- **HARDWARE VALIDATION PENDING:** dynamic touch, both native pipeline/wakeword
  slots, timer integration, timer LEDs, alarm sound/repetition and Center touch.
- No OTA, firmware binary publication or final/stable release.
