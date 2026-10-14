# Onju Voice Deutsch – ESPHome

Full-Duplex-Konfiguration für die originale Onju-Voice-Platine mit ESP32-S3,
16 MB Flash und octal PSRAM. Geprüfte Build-Version: ESPHome 2026.9.1.
Die öffentliche Konfiguration enthält keine persönlichen WLAN-Daten.

## Lokale Installation

1. Die beiliegende Onju-Konfiguration und das gesamte Asset-Verzeichnis
   in das persistente ESPHome-Konfigurationsverzeichnis
   übernehmen, sodass YAML und Asset-Verzeichnis nebeneinander liegen.
2. In der dortigen privaten Secret-Datei die Schlüssel `wifi_ssid` und
   `wifi_password` mit den eigenen WLAN-Daten hinterlegen. Eine bestehende
   Secret-Datei ergänzen, nicht überschreiben. Die Platzhalter-Vorlage liegt im
   Asset-Verzeichnis und muss nicht direkt im Dashboard-Verzeichnis liegen.
3. Die Konfiguration mit ESPHome validieren und kompilieren. Im Docker-Container
   sind die Befehle:

```sh
esphome config /config/onju-voice.yaml
esphome compile /config/onju-voice.yaml
```

Es werden keine API-, OTA- oder Fallback-AP-Secrets benötigt. Die API ist wie
upstream unverschlüsselt; OTA und Fallback-AP sind in dieser Variante deaktiviert.
Die Secret-Datei und sämtliche generierten Build-Dateien/Firmware-Binaries
gehören nicht ins öffentliche Repository. Die entsprechenden Ignore-Regeln
stehen in der mitgelieferten Git-Ignore-Konfiguration. Ein lokal mit WLAN-Secrets erzeugtes Factory-Image
enthält diese Daten und darf nicht als öffentliche Firmware veröffentlicht werden.

## Improv Serial

Improv Serial über USB_SERIAL_JTAG bleibt aktiviert. Die Firmware versucht
zunächst das lokal konfigurierte WLAN. Über Improv können anschließend andere
WLAN-Daten übertragen und gespeichert werden, auch wenn das eingebettete WLAN
nicht erreichbar ist. Das wurde am Implementierungscode von ESPHome 2026.9.1
geprüft; ein Test auf echter Hardware steht noch aus.

Mit einer vorkonfigurierten SSID meldet Improv bereits `PROVISIONED`, auch wenn
dieses WLAN nicht erreichbar ist. Neue WLAN-Einstellungen werden trotzdem
angenommen. Dafür einen Improv-Client mit Funktion zum Ändern des WLANs verwenden;
ein reiner Ersteinrichtungsdialog muss das Formular nicht automatisch anzeigen.

Für einen Build ohne passende persönliche WLAN-Daten können die zwei benötigten
Schlüssel lokal zunächst mit den Platzhaltern aus der Vorlage belegt werden.
Die Schlüssel müssen für die `!secret`-Auflösung existieren. Nach dem Flash wird
das echte WLAN über Improv eingerichtet. Bei Firmware mit vorkonfiguriertem WLAN
sind gespeicherte Improv-Daten an den Konfigurationshash gebunden; ein späterer
Build mit geänderter Konfiguration kann erneute Provisionierung erfordern.

Referenzen: [Improv Serial](https://esphome.io/components/improv_serial/) und
[gespeicherte WLAN-Daten](https://esphome.io/components/wifi/#user-entered-credentials).

## Herkunft und Audio

- Onju-Quellstand: `09b3b65c237e8dc42c40677492965865429fe12e`.
- Audio-Stack: `0482d741a938378ef948e3b8f3dd31536f9f2cc9` aus
  https://github.com/n-IA-hane/esphome-audio-stack.
- Intercom-Migrationsdokumentation: `6581cfea712d0e13bf88c5aff3fa97b9e27123ab`;
  keine aktive Intercom-Komponente. Die zuvor gelistete `audio_processor`-
  Schnittstelle ist heute intern im Audio-Stack enthalten.
- ESP32-S3, GPIOs, I2S, 48-kHz-Bus, 16-kHz-Mikrofon/AEC, Software-AEC
  `sr_low_cost`, Filterlänge 4, Mixer, Resampler, microWakeWord `okay_nabu`, VAD,
  Voice Assistant und Bedienelemente bleiben erhalten.
- Lokale Signaltöne unter CC0; Lizenz bei den Sound-Dateien. Keine privaten Sound-URLs.

Deutsch in der später zugewiesenen Home-Assistant-Assist-Pipeline einstellen.
Home Assistant wird durch diese Konfiguration nicht geändert.

## Factory-Image

Nach erfolgreichem Build das von ESPHome erzeugte Factory-Image verwenden.
Bei der nativen ESP-IDF-Toolchain und Datenverzeichnis `/data` lautet der
Containerpfad /data/build/onju-voice/build/firmware.factory.bin.
Die tatsächliche Datei wird im Compile-Protokoll genannt.
Bootloader, Partitionstabelle, OTA-Initialisierung und Anwendung anhand der
Flashargumente prüfen. Das vollständige ESP32-S3-Factory-Image gehört beim
späteren USB-Flash an Offset `0x0`; der Anwendungs-Offset `0x10000` ist kein
Ziel für das Gesamtimage. Diese Vorbereitung führt keinen Flash aus.
