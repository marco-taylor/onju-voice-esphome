# Known-good software-mute release validation — 2026-11-02

ESPHome **2026.10.0**, ESP-IDF **5.5.6**. Public-source checks:
**Config PASS, Codegen PASS, fresh Clean Build PASS**. The factory image comes
from that same build; each segment is compared byte-for-byte with its build input.

The user additionally confirmed physical software mute/unmute, microphone silence,
no wakeword response while muted, red LED, repeated switching, reliable MWW
recovery, Okay Nabu/Alexa after unmute and media player/timer while muted.
Native API and HA registry confirm Mute is a configuration entity.
Mute logic and category match the hardware-tested source exactly.

The user confirmed real-device Okay Nabu/slot 1 + Alexa/slot 2, STT, intent,
immediate TTS, VA-IDLE race fix, player handover, VA/MWW recovery, dynamic touch,
timer, Center dismissal, MWW after timer and Voice-PE wake/timer sounds.
Other model combinations, USB factory installation and dedicated safety
fault-injection/real-time limit tests are not claimed individually validated.

Release/production functional YAML matches after allowing only generic device
identity and DHCP in place of private static networking. All 72 local components
and 843 SDK inputs match the frozen hardware-tested source. All active MP3 bytes
match, including wake, timer and existing generic error sound. Documentation and
asset-manifest inventory are adapted for public distribution only.

The unchanged END barrier waits for actual VA IDLE. All five models plus VAD,
two native slots, model limit/duplicate handling, ADF/DC, timer safety, dynamic
touch, local assets, Improv Serial and OTA are verified in source/generated/linked
artifacts. No AEC/FIR/48-kHz microphone architecture is imported.

Public dummy Wi-Fi/identity/DHCP/build metadata differ from the installed private
image, so byte identity between public and private firmware is not claimed.
Factory application bytes must match the validated public application exactly.
No production changes, OTA, HA settings changes or other-device changes occur.

Sensitivity definitions and the boot default are unchanged. The existing
nonpersistent runtime sensitivity is not made a new firmware default.
