# Timer safety validation — 2026-10-25

## BUILD VALIDATED

- ESPHome **2026.10.0**, ESP-IDF **5.5.6**.
- Public configuration with dummy Wi-Fi credentials: **Config PASS**.
- Source generation: **Codegen PASS**.
- Full compilation in a fresh isolated directory: **Clean Build PASS**.
- Public build timestamp: 2026-10-25 14:59:27 +0100.
- All 72 local component files match the installed production source snapshot;
  all 48 compiled local C++/header inputs match those sources.
- SDK: 842 files verified against the public production hash manifest.
- YAML remains generic: device identity and DHCP differ from private deployment;
  functional configuration and secret references are preserved.
- Existing ADF/DC/gain, MWW/models, native slots, handover/recovery, touch,
  confirmation tone, Assist delay, local MP3 and all five timer events retained.
- No extra decoder, stop wakeword, persistent player repeat mode or old PCM/raw
  probes. No firmware changes for publication beyond copying the installed safety code.
- Known-secret and private-IP scans cover all tracked public files. No personal
  configuration, secrets, firmware binaries, builds, backups or raw logs published.

| Linker use | Installed production safety build | Public dummy build |
| --- | ---: | ---: |
| Flash | 1,548,667 bytes | 1,548,407 bytes |
| Static RAM | 126,151 bytes | 126,007 bytes |

These are linker figures, not runtime heap measurements. Public dummy
credentials/device identity/DHCP account for differing build inputs.

Public configuration SHA256: `a7d9ba4dd6332b7db1ae5e58206bee9ea84a7359537196e316c23360fdaccbbd`.
SDK manifest SHA256: `0fee7aa5362d21d5f76c3ad0a404e9b7bb4e10b07e0074d7600ee85702a10e0c`.

## Timer safety

A ringing session is limited to 15 minutes, including player wait time. Further
expired timers do not extend it. The deadline calls the existing central
`dismiss()` cleanup. Manual dismissal disarms it; a new session starts afresh.
Cleanup waits at most 10 seconds for player IDLE, emits one WARN on timeout and
continues the existing guarded recovery if no active VA owns the handover.
The existing recovery has its own bounded waits. No second cleanup is added.

Production timer C++ host tests passed for Center dismissal, HA STOP, the
15-minute deadline, player becoming IDLE and player remaining stuck. Also
checked repeat cessation, LED release, one-shot recovery/WARN, VA ownership,
new-session reset, concurrent alarms and clock rollover. These tests use mocked
dependencies and do not establish real ADF/task/hardware fault recovery.

## BOOT / HARDWARE INITIALIZATION VALIDATED

The production safety build was installed successfully before this publication:
boot without bootloop, Wi-Fi and Home Assistant API connected, 8 MB PSRAM,
ADF/microphone RUNNING, unchanged DC path and MWW DETECTING_WAKE_WORD.
Voice Assistant, player and timer initialized. Both native pipeline/wakeword
slot pairs were present, all three model definitions were available, and touch
GPIO4/3/2 initialized. Passive stability: **125 seconds PASS**, no critical or
repeated audio/ADF/ringbuffer errors. DC was verified through the installed
source and running microphone path, without a new quantitative audio capture.

## FUNCTIONAL HARDWARE TESTS PENDING

- Timer countdown and alarm/repetition.
- Center-touch dismissal and dynamic touch operation.
- The 15-minute timeout in real time and 10-second timeout under a real fault.
- Full two-pipeline routing and acoustic recognition of all three wakewords.

These functions are implemented/build validated; initialization alone does not
prove physical operation. No timer, touch or speech tests were triggered during
the OTA observation. No OTA, HA changes or other device changes during this
publication. No stable release; private logs and diagnostics remain local.
