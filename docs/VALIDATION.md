# Timer milestone validation — 2026-10-25

## BUILD VALIDATED

- ESPHome **2026.10.0**, ESP-IDF **5.5.6**.
- Public configuration with dummy Wi-Fi credentials: **Config PASS**.
- Source generation: **Codegen PASS**.
- Full compilation in a fresh isolated build directory: **Clean Build PASS**.
- Build timestamp: 2026-10-25 12:46:11 +0100.
- All 72 component files match the current production snapshot unchanged;
  all 48 compiled local C++/header inputs match those sources.
- Reconstructed SDK: **842 files**, all sizes/hashes match production.
- No functional source changes for publication. Device identity is generic and
  private static network settings are replaced by DHCP; secret references remain.
- Checked 16-kHz ADF, DC correction, runtime gain, all three wakewords, two
  native slots, MWW→VA handover, END/ERROR recovery, local confirmation tone,
  Assist delay, listening light, native volume, dynamic touch and touch snapshot.
- Checked all five native timer callbacks and the timer manager in the ELF.
  The exact local MP3 alarm bytes are embedded; no new decoder is enabled.
- Timer LED defaults to ON; Center touch, regular STOP and VA/media takeover
  retain the production timer lifecycle logic.
- Old PCM/raw probe symbols and unused ADF-VAD define remain absent.
- Known-secret and generic credential/private-IP scans cover the final staged
  source tree. No private device config, secret files, firmware BINs, backups,
  build directories or capture data are published.

| Linker use | Previous production snapshot | Timer production snapshot |
| --- | ---: | ---: |
| Flash | 1,524,923 bytes | 1,548,395 bytes |
| Static RAM | 125,439 bytes | 126,143 bytes |

The independently rebuilt **public dummy configuration** uses 1,548,131
bytes flash and 125,999 bytes static RAM. Generic device
identity/DHCP and dummy credentials differ from the production device config;
these are linker figures, not runtime heap or hardware measurements.

Public `onju-voice.yaml` SHA256:
`a7d9ba4dd6332b7db1ae5e58206bee9ea84a7359537196e316c23360fdaccbbd`

SDK manifest SHA256:
`0fee7aa5362d21d5f76c3ad0a404e9b7bb4e10b07e0074d7600ee85702a10e0c`

## HARDWARE VALIDATION PENDING

- New dynamic touch calibration.
- Both native pipeline/wakeword slots and their routing.
- Timer integration and proportional timer LEDs.
- Local alarm sound/repetition, Center-touch dismissal and cleanup/recovery.

These features are **implemented / build validated, physical hardware
validation pending**. No claim of successful physical validation is made.

Hardware validated: **NO**. OTA performed: **NO**.
No final/stable release. Production config, Home Assistant and other devices
are unchanged by this publication. Only this summary is published; private
internal development reports, captures, logs and backups remain local.
