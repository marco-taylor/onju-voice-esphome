# Known-good validation — 2026-11-12

ESPHome **2026.10.2**, ESP-IDF **5.5.6**. Config, Codegen and fresh Clean Build
are required for publication. Host tests exercise the real local startup and
sensitivity headers, microphone mute/VA guards, preserved pending-TTS race fix
and timer safety.

The user confirmed wakeword PASS/current installed firmware works. Existing
known-good dual-pipeline, mute, timer/touch and Voice-PE sound acceptance is
retained. This is not a claim that each physical power-cycle/offline/model-pair
test was separately performed.

Production and release component/SDK/audio inputs must match. YAML comparison
permits only generic name, friendly name, MAC suffix and DHCP instead of private
identity/static network values. Project version remains 1.1.0, matching the
installed reference; this release has no version-driven managed update feature.
Factory Application bytes are compared with the exact validated public App.
Public/private firmware bytes differ due to identity/network/build metadata.

Five models plus VAD, two slots, ADF/DC, VA-IDLE END barrier, bounded local startup,
versioned sensitivity, software mute, timer safety, dynamic touch, local sounds,
Improv Serial and native ESPHome OTA must be present. No HTTP Update Entity,
HTTP OTA, managed-update manifest or additional HTTP buffer is included.

Historical releases and assets remain available. No OTA/reboot or user-setting
change is performed during this publication. Sound-specific CC BY 4.0 attribution
and original notices remain unchanged.
