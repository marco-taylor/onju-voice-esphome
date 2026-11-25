# Onju Voice — experimental AFE / three-model WakeNet candidate

Isolated from production v1.2.0 (`133cd1024a7a53551fb4367be7ed44216d9c7b2e`).
This branch is **not production firmware** and has no update-feed entity.
No device was flashed for this candidate. The direct WakeNet9 fallback remains
on the separate `experiment/wakenet` branch at
`a972d6f8cba5f96d61024ce04134e24408f74b09`.

Source of truth: [./onju-voice.yaml](./onju-voice.yaml).
ESPHome **2026.10.2**, project **1.3.0-wakenet10-afe.1**.

## Architecture

One official ESP-SR 2.6.2 stack pinned to
`bb552f1a559396a17681299cb3e199a0f1a4520a`.
The existing Onju 16-kHz / 32-bit LEFT I2S → ADF → DC correction → runtime gain
path supplies signed 16-bit mono PCM to one AFE (`M`, speech recognition,
low-cost mode). There is no second microphone reader or direct detector.

Exactly three models are packaged in one 16-byte-aligned Application blob:

1. `wn10_alexa` — Alexa; native AFE model ID 1.
2. `wn10_de_halloesp` — Hallo ESP; ID 2.
3. `wn9_jarvis_tts` — Jarvis, **not Hey Jarvis**; ID 3.

Two models are configured during AFE creation; the native third-model API is
called once and must return 3. No SDK patch or fourth registration is used.
VAD, NS, AEC, AGC and SE are deliberately disabled for this first candidate.
No playback reference exists. Duplex I2S does not constitute AEC.

All three models are loaded/inferred by the AFE when listening. The existing
**two native HA pipeline slots** remain the routing authority: all three
wakewords are available in the catalog, but at most two can be selected for
Assist. A detection from an unselected model is logged and ignored. Each word
can be assigned to either slot in HA; there is no implicit third-word fallback
and no third pipeline. The selection mask is persistent and migrates the old
Alexa enable preference. An explicit later design decision is needed if all
three must trigger Assist simultaneously through only two native HA slots.

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

The bootstrap verifies the eleven exact official model-file hashes. The
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
ASan/UBSan and checks three model directories, bounds and alignment. Neither
executes Espressif's Xtensa DSP. The older feasibility script and single-engine
report are historical evidence, not acceptance tests for this AFE architecture.

Clean build/link and host tests pass. Runtime initialization of all three
models, heap/PSRAM peaks, real detection, VA/TTS and repeated physical cold boots
remain hardware tests requiring separate authorization. See
[./docs/experiments/wakenet/AFE_THREE_MODELS.md](./docs/experiments/wakenet/AFE_THREE_MODELS.md).

## Licensing

Espressif SDK/model notices are retained in
[./docs/ESP_SR_LICENSE.txt](./docs/ESP_SR_LICENSE.txt) and
[./DEPENDENCIES.md](./DEPENDENCIES.md). The Espressif MIT variant permits use
on Espressif products subject to retaining notices; it grants no separate
wakeword trademark rights. The bootstrap downloads official model files from
the exact pinned source; no alternative model source is used.
