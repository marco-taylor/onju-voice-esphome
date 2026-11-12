# Controlled managed-update candidate

Base: `06065b6c80fa5e88944add8415897251e0653885`
(`known-good-2026-11-coldboot-20261112`). This is test development, not an
assertion of completed physical validation. Do not overwrite historical releases.

The native ESPHome 2026.10.2 HTTP update/OTA components use GitHub
`releases/latest/download/onju-voice.manifest.json`, CA-verified TLS, five
redirects and 4096-byte RX/TX buffers. Native ESPHome OTA and Improv remain.
A user must request installation; there is no auto-install automation.

## Identity/network migration

The public image contains no compiled station, room identity or personal IP.
A **private one-time bootstrap package** supplies the existing device's exact
MAC, node/friendly names, Wi-Fi credentials and static network configuration.
Never upload this private bootstrap binary as a release asset.

Before native `App.pre_setup` and all entity registration, `onju_identity`
loads a versioned, MAC-bound `Profile` from the existing ESPHome NVS namespace.
A valid private bootstrap writes and synchronizes the profile and native
`SavedWifiSettings` under stable key 88491487, then reads both back. It does not
erase NVS or copy settings from another device. A failed persistence result
must stop the test before any shared-image installation.

Later shared images load this profile before entity names/hashes/preferences
are formed, preserving the original identity and dynamic media-player name.
Without a profile, the same image constructs a generic MAC-suffixed identity
locally; the native name_add_mac_suffix codegen flag is intentionally false.
This avoids calling arch_init twice or altering ESPHome Application internals.

The shared Wi-Fi configuration has zero compiled stations. Native Wi-Fi chooses
its stable Improv preference key before loading a station. The only vendored
Wi-Fi change adds the persisted static network parameters to that loaded AP in
`set_sta`; credentials/provisioning and native connection code remain native.
The same hook retains static networking after later Improv credential changes.
A fresh device has no profile and uses DHCP/Improv normally. Profiles cannot be
copied between MAC addresses. No credentials are logged by the migration code.

All existing entity names/IDs, model IDs, sensitivity schema and preference keys
remain unchanged for migrated devices. Home Assistant retains pipeline settings
and its MAC-based device mapping. Software Mute deliberately remains ALWAYS_OFF
at boot. Do not claim arbitrary power-loss-during-flash or corrupted-NVS recovery.

## Measurement and test channel

`onju_update_metrics` uses IDF's local heap-minimum monitor, with no capture
buffer or dedicated sampling task. Native API actions begin/end a bounded
measurement; OTA callbacks record the TLS/download/flash interval. Largest free
blocks are reported at boundaries, not falsely claimed as an exact transient
largest-block minimum. Boot measurement ends automatically after 170 seconds.

GitHub prereleases cannot be latest. Controlled RC tags therefore require a
**normal GitHub test release explicitly marked latest**, with release notes
clearly identifying pending hardware validation. This is not a quality/stable
claim. Old known-good tags/assets stay unchanged. Initial RC and next RC must
have strictly increasing SemVer versions; factory and OTA come from one build.
Only the designated first device may be migrated/tested. Physical wakeword,
Assist/TTS, timer/touch and real cold-boot acceptance remain required.
