# Production validation — 1.2.0

Release tag **v1.2.0**, source commit
`133cd1024a7a53551fb4367be7ed44216d9c7b2e`, was validated with
**ESPHome 2026.10.2 / ESP-IDF 5.5.6**: Config, Codegen, fresh Clean Build and
all relevant host/native/packager regression tests PASS.

The hardware-approved RC2 source is
`78bf58dbcc1f1ece2daa4957776cb3608fc0d7fb`. Final 1.2.0 differs only in
project-version/release metadata and documentation. Generated runtime code,
component sources, dependencies, SDK, models and sounds were compared.
The user accepted both devices: wakeword/Assist/TTS, mute, timer/touch,
real cold boot and sensitivity retention. This does not claim every possible
wakeword pair or every fault-injection case was physically tested.

The source of truth is [../onju-voice.yaml](../onju-voice.yaml), including its
local components and pinned build inputs. The same generic YAML supplies both
release artifacts and self-builds; see [Using with ESPHome](../README.md#using-with-esphome).
No compiled Wi-Fi station or personal identity is present in the shared image.
Improv/native saved Wi-Fi and the tested MAC-bound identity/Preferences
migration are retained. Optional private `!secret` Wi-Fi changes are local
customizations, not the distributed generic release configuration.

Regression coverage includes bounded MWW startup/restore, sensitivity
persistence, OFF/mute guards, pending-start cancellation, microphone/VA guards,
VA-IDLE/TTS recovery, timer safety, identity/NVS/native Wi-Fi, HTTP OTA error
paths, update actions, TLS compatibility, native manifest parsing and release
packaging. Five models plus VAD, two slots, ADF/DC, dynamic touch, local
Voice-PE sounds, Improv Serial and native ESPHome OTA remain present.

HTTP OTA and the HA Update Entity use verified TLS, five redirects and
4096-byte RX/TX buffers. The production source is GitHub
`releases/latest/download/onju-voice.manifest.json`; installation requires an
explicit user action. Factory/OTA application bytes match the same final build.
All published assets were downloaded and byte/hash verified; historical
releases, tags and assets remain unchanged.

Documentation-only follow-ups do not rebuild or replace the immutable v1.2.0
release. They validate the repository instructions separately and do not
install firmware, reboot devices or change device settings.
