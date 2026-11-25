# Native NSNet2 model test

This isolated ESP32-S3 ESP-IDF test uses the pinned real ESP-SR Xtensa libraries and the same application blob as the NS candidate. It has no network or installer and must not be flashed on the production devices.

Run the official toolchain export, bootstrap models with `python tools/bootstrap_wakenet.py`, then from this directory run `idf.py -D IDF_TARGET=esp32s3 build`. The project expects ESP-IDF 5.5.6 and octal PSRAM, matching the candidate. Model weights are not mocked.

Checks: exact three blob records (two unchanged WakeNet10 models and NSNet2), native AFE config validation with only NS enabled, native NS interface lookup, native NS create, 512-sample/16-kHz geometry, eight process calls and destroy. Success requires NATIVE_NS_TEST_PASS; a linker success is insufficient. The raw native process results are recorded without interpreting them as audio-quality scores. Zero input checks execution, not noise-suppression quality.

Memory deltas are measured around the NS create call. Emulator timings are not hardware CPU measurements. An emulator peripheral limitation is a blocked native test, never PASS.

The existing ../native_wakenet_test continues to test both individual native WakeNet model creates and both AFE slots; it accepts the optional third NS blob record but still tests the baseline WakeNet path with NS off. Its prior AES/GDMA emulator limitation is not bypassed. Both unchanged WakeNet payloads have already passed native creation on the baseline ESP32-S3 hardware; that provenance must be distinguished from a fresh emulator PASS.
