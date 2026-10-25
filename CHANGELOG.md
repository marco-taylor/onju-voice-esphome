# Changelog

## Timer safety — 2026-10-25

- Limit a ringing session to 15 minutes using the existing central `dismiss()`
  cleanup; manual dismissal disarms it and a new session gets a fresh deadline.
- Bound the cleanup wait for player IDLE to 10 seconds; emit one WARN and
  continue existing guarded recovery when the player remains stuck.
- No changes to ADF/DC/gain, MWW/models, native slots, handover, touch, Assist
  delay or confirmation sound. No Voice-PE repeat mode or stop wakeword.
- **BOOT / HARDWARE INITIALIZATION VALIDATED:** production OTA, boot,
  Wi-Fi/API, PSRAM, ADF/microphone, MWW and component initialization passed;
  125 seconds passive stability without critical or repeated audio errors.
- **FUNCTIONAL HARDWARE TESTS PENDING:** timer countdown/alarm, Center dismiss,
  real-time safety/fault timeouts, touch operation, both pipeline routes and
  acoustic recognition of all three wakewords.
- Config, Codegen and Clean Build are rechecked with ESPHome 2026.10.0 for
  publication. No OTA during publication and no stable release.

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
