# WakeNet single-engine feasibility — Phase 1, 2026-11-24

## Decision and scope

**Clean build/link PASS. Controlled first hardware-test candidate: YES; hardware acceptance: NOT TESTED. No device was contacted, flashed or rebooted.** Runtime heap, initialization peak, inference performance and acoustic recognition remain unmeasured. This is not production-ready firmware and is not offered through any update feed.

The user superseded the earlier dual-engine design. This experiment replaces microWakeWord with WakeNet; there is no engine selector, runtime arbitration or concurrent inferencing. The earlier report in ./docs/experiments/wakenet/BERICHT.md is historical evidence, not the current architecture.

Base: production v1.2.0, commit 133cd1024a7a53551fb4367be7ed44216d9c7b2e. Branch experiment/wakenet; isolated worktree development/wakenet/. Experimental project version 1.3.0-wakenet.1. ESPHome 2026.10.2 / ESP-IDF 5.5.6 / GCC 14.2.0_20260121. Build time: 2026-11-24 17:24:18 +0000. No main, remote, release or production manifest mutation.

## One consistent ESP-SR stack

ESP-SR reports version **2.6.2**, pinned to official commit **bb552f1a559396a17681299cb3e199a0f1a4520a**. This is a pinned upstream development snapshot, not a claim of a stable registry release. Previous ADF SDK ESP-SR was 0c1eecaac259af95f76723b61d4e16cef5904fc7.

The previous old/new collision concerned five CMake targets: wakenet, multinet, hufzip, esp_audio_front_end and esp_audio_processor. The experiment removes the old esp-sr registration and registers exactly one current local esp-sr component. Its upstream CMake dependency graph supplies its libraries; unused sections are removed by the linker. No second ESP-SR generation, target aliases, symbol stubs or ABI mixing are used. The final compile graph contains one current model_path.c and no legacy ESP-SR paths. The final ELF defines esp_wn_handle_from_name, srmodel_load and esp_srmodel_deinit exactly once; the WakeNet9 interface table is 68 bytes (17 32-bit function pointers), matching the current headers. No new unresolved symbols are introduced; three baseline IDF NOTYPE undefined markers remain inherited.

Two generated CMake-only overlays exclude inactive legacy AFE wrappers: ./onju-voice-assets/tetele-production/wakenet-overlay/audio_stream/CMakeLists.txt omits algorithm_stream.c; ./onju-voice-assets/tetele-production/wakenet-overlay/audio_recorder/CMakeLists.txt omits recorder_sr.c. Those wrappers require obsolete AFE interfaces. All copied C/H files remain byte-identical to the pinned ADF SDK. Active ADF microphone, I2S, player and VA processing code are unchanged. tts_stream.c remains compiled. No rewrite of the audio architecture is needed for the build proof.

Pinned new dependencies: esp-dl 3.3.13, dl_fft 0.8.0, cjson 1.7.19~2, esp_new_jpeg 1.0.2. Existing resolved shared dependencies remain ArduinoJson 7.4.3, esp-audio-libs 4.0.1, mdns 1.14.0 and nghttp 1.68.1. The resolved lock is ./docs/experiments/wakenet/dependencies.lock (local paths made checkout-relative). Reproduction commands are in ./README.md.

## Official Alexa model and storage

- WakeNet generation: **9-family / 9l**, model directory **wn9_alexa**.
- Model metadata: **wakenet9l_v4h8_Alexa_3_0.640_0.650**; English Alexa; vendor DET_MODE_90 default retained.
- [Official pinned model](https://github.com/espressif/esp-sr/tree/bb552f1a559396a17681299cb3e199a0f1a4520a/model/wakenet_model/wn9_alexa).
- Raw model files: **290,873 bytes**. Packed application blob: **291,056 bytes**.
- Blob SHA256: **c1dea57bc3c10089be1c1137ab781bf0d9bde9d07eb5a25ddc9fa2095f2583c3**.
- 16-byte aligned blob and file offsets; final symbol at **0x3c131710**, in flash-mapped .flash.rodata. ELF and application image bytes match the generated blob.
- Native srmodel_load() parses that buffer. Host execution of the actual upstream loader, using ASan/UBSan, confirms file pointers into the original blob and repeated deinitialization. No bulk weight copy by this loader. Vendor create()/DSP runtime allocation is not proven by host tests.
- Cleanup uses the public esp_srmodel_deinit(); the blob is static for the application lifetime. No extra model partition, no partition table change.
- [ESP-SR license](https://github.com/espressif/esp-sr/blob/bb552f1a559396a17681299cb3e199a0f1a4520a/LICENSE): Espressif MIT grant limited to Espressif products; retain notices. No separate model license was found in the model directory. Redistribution follows that repository grant and conditions; Alexa trademark/product authorization is separate and not implied. SDK/model binaries are fetched from the official pinned source, not committed here.

WakeNet9-family was selected because it builds with the current consistent SDK and a substantially smaller Alexa model than the inspected WakeNet10 Alexa files (1,564,918 raw bytes). No legacy SDK is required for this choice. No quality or speed superiority is claimed. No extra models are included.

## Audio, ownership and lifecycle

Existing path: 16-kHz / 32-bit LEFT I2S -> ADF microphone -> existing integer DC correction/runtime gain/clipping -> 16-bit mono MicrophoneSource -> WakeNet. No second hardware I2S reader, no resampling, no new AFE/AEC/VAD/NS. Duplex I2S is not AEC. Playback ALC is not microphone AGC.

The existing microphone callback copies PCM into a bounded 4,096-byte ring (framework PSRAM-first allocation). Inference runs in a separate priority-3 task with an 8,192-byte internal stack. Vendor frame size/rate/channel are queried and validated at runtime (16 kHz, mono, 1..2048 samples); the frame buffer uses PSRAM. The exact vendor frame size and timing have not been measured on an S3. The ESPHome ring read handles wrap internally. Callback overflow drops are counted instead of blocking the audio path; real throughput/drop behavior is a hardware gate.

WakeNet start is reconciled locally after setup through the existing bounded startup controller. Use Wake Word OFF, actual microphone mute, VA active and OTA-in-progress block starts. The worker initializes the model before requesting the microphone source. Microphone startup remains owned by the consumer, preserving the existing cold-boot architecture. Startup success requires actual audio bytes and completed inferences, not merely loaded metadata. Existing bounded retry/cleanup remains.

On detection the worker exits, model/task resources are released, then the main loop emits Alexa. The existing handover waits for physical microphone STOPPED, plays the unchanged local confirmation tone and uses the existing Assist start delay/VA path. The VA-IDLE END barrier, TTS/media-player ownership, error recovery and timer cleanup remain protected. No new VA or artificial preroll/gapless guarantee is introduced. Mute/OFF cancel pending start/detection and prevent a late callback. OTA start stops WakeNet; OTA failure requests bounded recovery.

The native HA catalog advertises only Alexa and retains max_active_wake_words=2. Thus the two existing HA slots remain representable, but this first single-model prototype cannot provide two different wakewords. Actual HA slot routing and duplicate Alexa priority remain hardware/API tests; no personal pipeline IDs are compiled.

Intentional differences from production: no MWW inference or models (including its VAD), no MWW sensitivity entity, no engine selector. The production managed-update feed entity is absent, so this experiment cannot offer itself via releases/latest. Native ESPHome OTA and HTTP OTA backends remain compiled. Timer, touch, LEDs, sounds, microphone mute and identity logic are retained.

## Build and resource proof

| Check | Result |
|---|---|
| ESPHome Config / Codegen / Clean Build / Link | PASS / PASS / PASS / PASS |
| One current ESP-SR; no old ABI or duplicate targets | PASS |
| Existing 16-MB CSV and compiled partition table unchanged | PASS |
| Application fits 0x7c0000-byte OTA app partition | PASS |
| Embedded model alignment, bytes, flash placement | PASS |
| No MWW, TFLite Micro interpreter, frontend symbols or compile units | PASS |
| Native factory application equals OTA application | PASS |

| Resource | 1.2.0 | WakeNet | Delta |
|---|---:|---:|---:|
| ESPHome reported flash | 1,823,307 | 1,893,083 | +69,776 bytes |
| Static RAM | 130,095 | 142,915 | +12,820 bytes |

Application binary: **1,893,200 bytes**, SHA256 **a01fa2fbffaeb32028e033a1d57d8e9b92b32eb046c4dd2eff1dbf8f1acc12c0**. The native compiler also generates a local merged factory image (1,958,736 bytes), with identical application at 0x10000; no factory image is published or offered for installation. Local analysis artifact: diagnostics/wakenet-single-20261124/artifacts/onju-voice-wakenet-phase1.application.bin.

The six production TFLite blobs (five wakewords plus VAD) total **322,080 bytes** and are absent from the WakeNet ELF. The Alexa blob uses 31,024 fewer model-data bytes; the whole application nevertheless grows by 69,776 bytes because the engine/libraries differ. An isolated RAM saving attributable solely to removing MWW is not measured. Unused MWW source files may remain in the repository for historical/reference purposes; none enter the compile/link graph.

**Internal free heap, largest free block, PSRAM runtime usage, boot/model initialization peak, inference time/CPU, audio drops and VA/TTS peaks: NOT MEASURED.** They cannot honestly be inferred from a link map. The prototype logs pre/post-model free memory and rejects startup before create if internal free <98,304 bytes, largest block <65,536 or PSRAM free <1,048,576; after create it rejects free <65,536 or largest block <32,768. These are conservative failure gates, not measured sufficient reserve. Actual model creation may consume memory before the post-create gate. Hardware allocation/VA coexistence must be checked before any production use.

## Tests and limits

PASS: adapted existing actual startup-controller tests (restore/deferred setup/readiness/OFF/mute/VA/retries/audio+inference), microphone mute/VA guards, known-good TTS START/STOP race and VA-IDLE barrier, timer central cleanup/safety tests.

PASS: actual new C++ lifecycle with mocked RTOS/DSP/heap: OFF/mute gates, bounded callback, pending cancellation, task teardown before event, invalid model format, allocation failure, OTA stop/error recovery. PASS: actual upstream model-blob loader with ASan/UBSan and eight load/deinit cycles. Reusable new tests are ./tools/test_wakenet_lifecycle.py and ./tools/test_wakenet_blob.py.

PASS: source/diff protection, final ELF/dependency/partition/blob audit. Existing dual-engine feasibility checker remains historical and its runtime-unchanged assertion is intentionally NOT APPLICABLE; it has not been disabled to claim a pass. MWW-specific sensitivity tests are not claimed as a WakeNet sensitivity feature. No acoustic detection or Xtensa DSP execution occurs in host tests.

## Decision / next step

**Safe to hardware-test: YES, as a controlled Phase-1 candidate only after separate user authorization.** Build/link/partition/static resources are acceptable for that next experiment; runtime allocation and audio/VA interaction remain unverified. Stop immediately if allocation guards fail, audio drops persist, boot/ADF errors occur or VA/TTS ownership breaks. No broad audio rewrite is authorized.

First authorized hardware test should capture model initialization memory, actual frame geometry, audio/inference counters and drops; verify Alexa detection -> existing VA -> STT/Intent/TTS -> recovery, then Use Wake Word OFF/ON, mute/unmute and cold boot. Keep a proven recovery firmware available. No test has been performed on either current device.

Later A/B: separate production MWW-Alexa firmware versus WakeNet-Alexa firmware on the same authorized Onju, one variable at a time. Distances 1/3/5 m; frontal/side; quiet/normal/loud voice; quiet/TV background/self playback; several speakers where practical. Record trials/hits/misses/false positives and detection latency plus CPU/inference/internal heap/largest block/PSRAM/drops. No winner or AEC capability is assumed.

## Protected state

Wohnzimmer changed: NO. Küche changed: NO. Device OTA performed: NO. USB flash performed: NO. Device reboot performed: NO. Main changed: NO. Release 1.2.0 changed: NO. Tags changed: NO. releases/latest changed: NO. Production manifest changed: NO. No experimental release, update asset or remote push.
