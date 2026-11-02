# Changelog

## Known good release — 2026-11-02

- Hardware-tested dual HA pipelines with Okay Nabu and Alexa active together:
  STT, intent, immediate TTS, media-player handover and VA/MWW recovery.
- Preserve the delayed-TTS race fix: END recovery waits for actual VA IDLE,
  preventing STOP from overwriting a pending player START.
- Hardware-tested dynamic touch, timer/Center dismissal, MWW after timer, and
  official Voice-PE wake/timer sounds. All active sounds are local.
- Five selectable models, two native slots, at most two distinct enabled models.
  Other model pairs are available, not all individually hardware tested.
- Retain ADF/DC/gain, 16-kHz/32-bit LEFT mic, VAD/cutoffs, timer safety (15-minute
  ringing limit, central dismiss, 10-second player-IDLE cleanup) and LED logic.
- Correct Voice-PE CC-BY-4.0 sound attribution and preserve exact sound bytes.
- Generic public Config/Codegen/Clean Build with ESPHome 2026.10.0; full USB
  factory image from the same build, Improv Serial and OTA support.
- Prerelease only; historical tags/releases preserved. No OTA during publication.

## Known good dual pipeline — 2026-11-01

- Hardware-tested Okay Nabu/slot 1 and Alexa/slot 2 concurrently: correct routing,
  STT, conversation, immediate TTS, player handover and VA/MWW recovery.
- Preserve the known-good fix: END recovery waits for actual VA IDLE. This
  prevents STOP from overwriting a pending media-player START.
- Five selectable models: Okay Nabu, Hey Jarvis, Hey Mycroft, experimental
  Hey Home Assistant and stable Alexa; at most two distinct active models.
  Duplicate selections enable one model and keep slot-1 routing priority.
- Retain 16-kHz/32-bit LEFT Tetele ADF, DC correction, runtime gain, timer
  safety (15-minute alarm limit, central dismiss, 10-second player-IDLE wait),
  dynamic touch, native volume, local sounds and configurable Assist delay.
- Pipeline-2 missing-STT failure was HA configuration, not a firmware defect.
- Public source uses a generic identity, DHCP and secret references. ESPHome
  2026.10.0 Config, Codegen and fresh Clean Build validate the publication.
- Publish a full USB factory image as a prerelease asset. No OTA during release.
- Not every wakeword combination is hardware tested. Timer/touch operation and
  real safety fault/time-limit cases are not newly claimed as physically tested.

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
