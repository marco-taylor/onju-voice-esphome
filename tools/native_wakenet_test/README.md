# Native ESP32-S3 model-creation regression test

This isolated test application uses ESP-IDF 5.5.6 and the same pinned ESP-SR
libraries as the experimental Onju firmware. It has no Wi-Fi, API, microphone or
OTA installer. It must never be uploaded to an Onju as an application update.

After running the project model bootstrap, use an exported ESP-IDF environment:

```sh
cd tools/native_wakenet_test
idf.py -D IDF_TARGET=esp32s3 -B build build
```

The default input is the generated application blob. `ONJU_TEST_BLOB` can select
an absolute path to a known-bad blob for a negative test. The assembly input is
16-byte-aligned in read-only application data.

The actual native model API creates and destroys Alexa and Hallo ESP separately,
then the native AFE creates both models together and checks slots 1 and 2. Only
`NATIVE_MODEL_TEST_PASS` confirms a complete positive run. Assertions or timeouts
are failures; successful compilation or the model-loader message is insufficient.

The same Xtensa test binary can be executed under Espressif QEMU with ESP32-S3,
8 MB octal PSRAM and a merged 16 MB flash image. An emulator peripheral failure
(such as AES/GDMA) is inconclusive for real-hardware model creation and must not
be reported as PASS. This test does not measure production RAM reserve or audio.

After an independently authorized Onju hardware test, the separate evidence
validator at `tools/test_wakenet_native.py` checks real native AFE slot returns
and that the recorded running build matches the verified OTA application.
Neither host mocks nor structural blob tests replace a native positive result.
