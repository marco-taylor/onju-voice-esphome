# Onju Voice — experimental AFE / two-model WakeNet candidate

Isolated from production v1.2.0 (`133cd1024a7a53551fb4367be7ed44216d9c7b2e`).
This branch is **not production firmware** and has no update-feed entity.
No device was flashed for this candidate. The direct WakeNet9 fallback remains
on the separate `experiment/wakenet` branch at
`a972d6f8cba5f96d61024ce04134e24408f74b09`.

Source of truth: [./onju-voice.yaml](./onju-voice.yaml).
ESPHome **2026.10.2**, project **1.3.0-wakenet10-afe.2**.

## Architecture

One official ESP-SR 2.6.2 stack pinned to
`bb552f1a559396a17681299cb3e199a0f1a4520a`.
The existing Onju 16-kHz / 32-bit LEFT I2S → ADF → DC correction → runtime gain
path supplies signed 16-bit mono PCM to one AFE (`M`, speech recognition,
low-cost mode). There is no second microphone reader or direct detector.

Exactly two models are packaged in one 16-byte-aligned Application blob:

1. `wn10_alexa` — Alexa; native AFE model ID 1.
2. `wn10_de_halloesp` — Hallo ESP; ID 2.

Both native AFE configuration slots are used. No dynamic model registration,
third-model adapter, Jarvis weights or WakeNet9 model is included. No SDK patch.
VAD, NS, AEC, AGC and SE are deliberately disabled for this first candidate.
No playback reference exists. Duplex I2S does not constitute AEC.

Both WakeNet10 models are loaded by the AFE when listening. The existing two
native HA pipeline slots remain the routing authority. Intended configuration:
**Alexa → slot 1; Hallo ESP → slot 2**. The catalog and detected phrases preserve
that order; HA owns the actual pipeline IDs. There is no third routing layer.
Each selected model can trigger the existing Assist path. The persistent
two-bit selection migrates the earlier experimental mask/Alexa boolean without
changing Mute or Use Wake Word preferences.

The unmodified vendor generic selector can keep WN9-family kernel/interface
code linked even though no WN9 model is embedded or initialized. This is audited
in the link map; it is not represented as a WN9-free executable. Removing vendor
selector branches would require an SDK modification, which is not done.

Mute/OFF/VA ownership, bounded startup recovery, physical microphone release
before VA, local sounds and VA-IDLE-based TTS recovery are retained.
Feed and fetch use separate tasks sharing the one AFE instance. Cleanup waits
for feeder termination before destroying the AFE. Model initialization uses
PSRAM-preferred allocation and conservative internal-RAM reserve gates.

PCM DC, raw/AC RMS, peak, clipping, feed/fetch/detection counters and model IDs
are logged after the first audio second and then at ten-second intervals.
Successful fetch counts are not a measurement of pure inference time; timed
fetch calls include waiting. No raw audio is recorded.

## Build without flashing

Run from the repository root. No credentials are required for this generic
Improv/saved-profile image. Do not use these commands on the production checkout.

```sh
docker run --rm --entrypoint python3 -v "$PWD":/config \
  ghcr.io/esphome/esphome:2026.10.2 /config/tools/bootstrap_sdk.py
docker run --rm --entrypoint python3 -v "$PWD":/config \
  ghcr.io/esphome/esphome:2026.10.2 /config/tools/bootstrap_wakenet.py
docker run --rm -v "$PWD":/config \
  ghcr.io/esphome/esphome:2026.10.2 config /config/onju-voice.yaml
docker run --rm -v "$PWD":/config \
  ghcr.io/esphome/esphome:2026.10.2 compile --only-generate /config/onju-voice.yaml
docker run --rm -v "$PWD":/config \
  ghcr.io/esphome/esphome:2026.10.2 clean /config/onju-voice.yaml
docker run --rm -v "$PWD":/config \
  ghcr.io/esphome/esphome:2026.10.2 compile /config/onju-voice.yaml
```

The bootstrap verifies the eight exact official model-file hashes. The
Application blob needs no model partition; the existing flash layout is retained.
Existing ADF CMake overlays still exclude unused legacy SR wrappers, with the
active ADF/I2S/microphone/player implementations unchanged.

## Host validation and limits

```sh
docker run --rm --entrypoint python3 -v "$PWD":/config \
  ghcr.io/esphome/esphome:2026.10.2 /config/tools/test_wakenet_lifecycle.py
docker run --rm --entrypoint python3 -v "$PWD":/config \
  ghcr.io/esphome/esphome:2026.10.2 /config/tools/test_wakenet_blob.py
```

The lifecycle test compiles the actual consumer with threaded RTOS/AFE/heap
mocks and ASan/UBSan. The blob test executes the actual official loader with
ASan/UBSan and checks two model directories, bounds and alignment. Neither
executes Espressif's Xtensa DSP. The older feasibility script and single-engine
report are historical evidence, not acceptance tests for this AFE architecture.

Clean build/link and host tests pass. Runtime initialization of both
models, heap/PSRAM peaks, real detection, VA/TTS and repeated physical cold boots
remain hardware tests requiring separate authorization. See
[./docs/experiments/wakenet/AFE_TWO_MODELS.md](./docs/experiments/wakenet/AFE_TWO_MODELS.md).

## Licensing

Espressif SDK/model notices are retained in
[./docs/ESP_SR_LICENSE.txt](./docs/ESP_SR_LICENSE.txt) and
[./DEPENDENCIES.md](./DEPENDENCIES.md). The Espressif MIT variant permits use
on Espressif products subject to retaining notices; it grants no separate
wakeword trademark rights. The bootstrap downloads official model files from
the exact pinned source; no alternative model source is used.
