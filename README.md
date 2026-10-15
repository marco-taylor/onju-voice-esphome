# Onju Voice German ESPHome

Deutsche ESPHome-/Home-Assistant-Ausrichtung für die originale Onju-Voice-Platine.
Dies ist ein echter Fork von
[rmeissn/onju-voice-esphome](https://github.com/rmeissn/onju-voice-esphome).
Danke an Dr. Roy Meissner und die unten genannten Projekte.

Die Konfiguration erhält Full-Duplex-I2S, Software-AEC, microWakeWord
`okay_nabu`, Home Assistant Voice Assistant, Bedienung/LEDs, Timer und lokale
Sounds. Der Audio-Stack wurde auf die aktuelle Repository-Struktur migriert
und auf einen getesteten Commit fixiert. WLAN verwendet ausschließlich private
ESPHome-Secrets; Improv Serial bleibt aktiv.

**Prüfstand:** ESPHome **2026.9.1**: Konfiguration validiert, Firmware kompiliert,
Factory-Image erzeugt und strukturell geprüft. Die öffentliche Projektkopie
wurde zusätzlich sauber und ausschließlich mit Dummy-Secrets gebaut.
**Hardware-Teststand (15. Oktober 2026):** Auf einer originalen Onju-Voice-Platine
wurden folgende Prüfungen erfolgreich durchgeführt (vom Betreiber bestätigt):

| Prüfung | Ergebnis |
| --- | --- |
| Factory-Flash per USB | PASS |
| Boot | PASS |
| WLAN-Verbindung | PASS |
| ESPHome API | PASS |
| Erkennung im ESPHome Device Builder | PASS |
| Erkennung/Integration in Home Assistant | PASS |
| ESPHome OTA ohne Passwort | PASS |
| Neustart nach OTA | PASS |
| Erneute WLAN-/API-Verbindung nach OTA | PASS |

Die Hardwaretests erfolgten mit lokal angepasstem Gerätenamen und lokaler
WLAN-Konfiguration. Der öffentliche Standard bleibt allgemein benannt und
verwendet DHCP.

**Noch nicht praktisch verifiziert:** Mikrofonqualität, Lautsprecherqualität,
Wake Word `okay_nabu`, vollständiger Assist-Dialog, Full-Duplex im Betrieb und
AEC-Qualität/Barge-in. Full-Duplex bleibt experimentell.
USB-/OTA-Erfolg belegt keine Audio- oder Assist-Qualität.

## Voraussetzungen

- Originale Onju-Voice-Platine: ESP32-S3, 16 MB Flash, octal PSRAM 80 MHz.
- ESPHome 2026.9.1 und Internetzugriff zum Laden der Build-Abhängigkeiten.
- Home Assistant mit ESPHome-Integration und einer deutschen Assist-Pipeline.
- Für die spätere Erstinstallation: USB-Datenkabel, Downloadmodus der Platine,
  esptool oder ein geeigneter ESPHome-WebSerial-Installer.

## Installation

```sh
git clone https://github.com/marco-taylor/onju-voice-esphome.git
cd onju-voice-esphome
```

./onju-voice.yaml und das ganze Verzeichnis onju-voice-assets/ nebeneinander in
die eigene ESPHome-Konfiguration übernehmen. ./main.yaml und
./onju_duplex_i2s.yaml sind alternative Einstiegspunkte auf dieselbe Variante.
Die erhaltenen Upstream-Quellen in components/ werden hier nicht geladen.

## secrets.yaml

Die Platzhalter aus ./secrets.example.yaml in der eigenen privaten
./secrets.yaml ergänzen; eine bestehende Datei nicht überschreiben:

```yaml
wifi_ssid: "YOUR_WIFI_SSID"
wifi_password: "YOUR_WIFI_PASSWORD"
```

Die öffentliche Konfiguration verwendet nur:

```yaml
wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password
```

Weitere Secrets werden nicht benötigt. ESPHome OTA ist ohne Passwort aktiviert:

```yaml
ota:
  - platform: esphome
```

Es gibt kein OTA-Passwort und kein OTA-Secret. OTA-Updates sind aus dem
erreichbaren Netzwerk ohne Authentifizierung möglich; diese Variante setzt ein
vertrauenswürdiges lokales Netzwerk voraus. API-Verschlüsselung und Fallback-AP
sind nicht aktiviert. Private Secret-Dateien,
generierter C++-Code, Caches und Firmware gehören nicht auf GitHub. Eine mit
echten WLAN-Daten kompilierte BIN enthält diese Daten und darf nicht als
öffentliches Firmware-Asset verwendet werden.

## ESPHome-Konfiguration

Im eigenen ESPHome-Container:

```sh
esphome version
esphome config /config/onju-voice.yaml
```

Oder direkt aus dem Projektordner mit einem separaten Container:

```sh
docker run --rm -v "$PWD:/config" ghcr.io/esphome/esphome:2026.9.1 config onju-voice.yaml
```

Die Standardkonfiguration verwendet DHCP, keine persönliche statische IP und
keine privaten Sound-URLs. Externe Komponenten sind commit-gepinnt.
Gerätename und Friendly Name lassen sich lokal in den Substitutionen `name`
und `friendly_name` anpassen. Technische Namen mit Kleinbuchstaben, Ziffern und
Bindestrichen verwenden und für jedes Gerät eindeutig wählen.

## Kompilieren

```sh
docker run --rm -v "$PWD:/config" ghcr.io/esphome/esphome:2026.9.1 compile onju-voice.yaml
```

Alternativ im bestehenden eigenen ESPHome-Container:

```sh
esphome compile /config/onju-voice.yaml
```

ESPHome verwaltet ESP-IDF und Toolchain. Der erste Build lädt viele Bibliotheken
und kann länger dauern. Andere Geräte müssen dafür nicht aktualisiert werden.

## Factory-Image

Maßgeblich ist der im Compile-Protokoll genannte Factory-Pfad. Beim nativen
ESP-IDF-Build liegt er ohne abweichendes Datenverzeichnis üblicherweise unter
.esphome/build/onju-voice/build/firmware.factory.bin; mit Datenverzeichnis `/data`
unter /data/build/onju-voice/build/firmware.factory.bin.

| Bestandteil | Flash-Offset |
| --- | --- |
| ESP32-S3-Bootloader | `0x0` |
| Partitionstabelle | `0x8000` |
| OTA-Initialisierung | `0x9000` |
| Anwendung | `0x10000` |

Diese Segmente wurden bytegenau gegen das Gesamtimage geprüft, einschließlich
Image-Checksummen/Digests, Partitions-MD5, Grenzen und Anwendungsgröße.
Die standardmäßigen OTA-Partitionen und der ESPHome-OTA-Dienst sind aktiviert.
Kein Dummy-Testimage und keine persönliche BIN werden verteilt.
Jeder Benutzer erzeugt sein eigenes Factory-Image.

## Erstinstallation per USB

Die USB-Erstinstallation wurde auf echter Hardware erfolgreich getestet.
Für die eigene Platine ein eigenes `firmware.factory.bin` erzeugen. USB-Datenkabel
verbinden, bei Bedarf den ROM-Downloadmodus gemäß Platinenanleitung herstellen
und den tatsächlichen seriellen Port bestimmen. Nach eigener Image-Prüfung
mit esptool 5:

```sh
esptool --chip esp32s3 --port /dev/ttyACM0 --baud 460800 write-flash --flash-mode dio --flash-freq 80m --flash-size 16MB 0x0 .esphome/build/onju-voice/build/firmware.factory.bin
```

Port und Dateipfad sind Beispiele. Das **Gesamtimage an `0x0`** schreiben;
`0x10000` ist nur der Offset der separaten Anwendung. Ein vollständiger Erase
löscht auch vorhandene WLAN-/Geräteeinstellungen und ist kein normaler
Anwendungsupdate. Danach normal starten. Ein leeres Gerät benötigt das
Factory-Image einschließlich Bootloader und Partitionstabelle.

## WLAN

Lokale Secrets ermöglichen die direkte WLAN-Verbindung; IP-Adressen kommen
per DHCP. Improv Serial über USB_SERIAL_JTAG bleibt aktiv. Über einen
Improv-Client mit WLAN-Wechsel-Funktion können andere Daten gespeichert werden.
Mit vorkonfigurierter SSID meldet ESPHome bereits `PROVISIONED`, auch wenn
dieses WLAN nicht erreichbar ist. Ein reiner Erstinstallationsdialog zeigt sein
Formular deshalb nicht zwingend automatisch.

Für eine spätere Improv-Einrichtung kann lokal mit ausschließlich fiktiven
Platzhalter-Secrets gebaut werden. Die zwei Schlüssel müssen für die YAML-
Auflösung dennoch existieren. Gespeicherte Daten sind bei statischem WLAN an
den Konfigurationshash gebunden; geänderte Builds können erneute Provisionierung
erfordern. Diese Kombination wurde nicht auf Hardware getestet.
Referenzen: [Improv Serial](https://esphome.io/components/improv_serial/),
[WiFi](https://esphome.io/components/wifi/#user-entered-credentials).

## Home Assistant

Nach dem späteren Flash den Satelliten über die ESPHome-Integration hinzufügen.
Eine deutsche Assist-Pipeline mit deutschfähigem STT, Conversation-Agent und
TTS auswählen und dem Satelliten zuweisen. Kein bestimmter Cloud-Anbieter wird
erzwungen. Die Native API ist im getesteten Stand unverschlüsselt; lokal
eingeführte API-Verschlüsselung benötigt zusätzliche private Schlüssel und
eine erneute Prüfung. Diese Vorbereitung verändert Home Assistant nicht.

## Wakeword

microWakeWord verwendet `okay_nabu` aus dem Release `okay_nabu_20241226.3`;
VAD bleibt aktiv. Die Wakeword-Sprache ist von der deutschen Assist-Pipeline
unabhängig. Sensitivitätsauswahl und Mikrofon-Gain stammen aus der Onju-
Konfiguration. Erkennungsqualität ist nicht auf echter Hardware nachgewiesen.

## Full-Duplex / AEC

ESP32-S3, ESP-IDF, CPU 240 MHz, 16 MB Flash, octal PSRAM 80 MHz. LRCLK GPIO13,
BCLK GPIO18, Mikrofon-DIN GPIO17, Lautsprecher-DOUT GPIO12. 48-kHz-Bus,
32-bit Slots, rechter Mikrofonkanal; Verarbeitung für Mikrofon/AEC/Wakeword/
Assist bei 16 kHz. AEC `sr_low_cost`, `filter_length: 4`, Puffer in PSRAM.
Der Audio-Stack konvertiert intern die Raten. Mixer, Resampler, Timer, Alarm,
Hardware-/Software-Mute, LEDs und Bedienung bleiben erhalten.

Software-AEC und Wakeword während Wiedergabe müssen an der Platine geprüft
werden. Eine erfolgreiche Kompilierung belegt keine Audioqualität.

## Updates

```sh
git remote add upstream https://github.com/rmeissn/onju-voice-esphome.git
git remote -v
git fetch upstream
```

`origin` gehört zum eigenen Fork, `upstream` zum Original. Vor Übernahme neuer
Stände Diff, Pins, Lizenzen und ESPHome-Version prüfen und erneut validieren/
kompilieren. Kein automatisches Firmware-Update, Release oder Actions-Artefakt.
Die **Erstinstallation** erfolgt per USB mit dem vollständigen
`firmware.factory.bin`. **Spätere Updates** erfolgen über ESPHome OTA per WLAN,
beispielsweise über „Installieren“ → drahtlose Installation im Device Builder
oder mit `esphome upload ./onju-voice.yaml`. Dabei verwendet ESPHome das
OTA-Anwendungsimage `firmware.ota.bin`; das Factory-Gesamtimage ist für USB.
Das Gerät muss bereits die OTA-fähige Firmware ausführen und im WLAN erreichbar
sein. OTA benötigt in dieser Konfiguration kein Passwort. Nach einem Update
Neustart, WLAN- und API-Verbindung prüfen.
Ein Upstream-PR ist erst nach gesonderter Entscheidung und Hardwaretest vorgesehen.

## Fehlerbehebung

- Fehlendes Secret: `wifi_ssid` und `wifi_password` lokal ergänzen.
- Fehlende Sounds: vollständiges Asset-Verzeichnis neben die YAML kopieren.
- Komponentenfehler: dokumentierten Commit und ESPHome 2026.9.1 verwenden;
  AEC oder Assist nicht zur Fehlerumgehung entfernen.
- Offline im Dashboard: ohne verbundene/geflashte Platine normal.
- USB/Improv: Datenkabel, Port, Downloadmodus und WLAN-Wechsel-fähigen Client
  prüfen; USB_CDC ist hier nicht der konfigurierte Improv-Transport.
- `rgb_order` ist für eine spätere ESPHome-Version deprecated, für 2026.9.1
  unverändert erhalten. Die PlatformIO-Optionen werden beim nativen ESP-IDF-
  Build ignoriert; tatsächliche SDK-/Flashartefakte bestätigen DIO und 16 MB.

## Abhängigkeiten

[./DEPENDENCIES.md](DEPENDENCIES.md) dokumentiert Herkunft und Lizenzen.
Aktive Komponenten: `esp_audio_stack` und `esp_aec`, Commit
`0482d741a938378ef948e3b8f3dd31536f9f2cc9`.
`AudioProcessor` ist intern; die alte `intercom_api` war bereits auskommentiert.
Geprüfte Intercom-Migrationsdokumentation:
`6581cfea712d0e13bf88c5aff3fa97b9e27123ab`.

## Lizenz

Die MIT-Lizenz des Upstream bleibt in [./LICENSE](LICENSE) erhalten.
Mathematisch erzeugte lokale Signaltöne sind CC0; Hinweise stehen in
onju-voice-assets/sounds/LICENSE.txt. Keine privaten Fremdaufnahmen übernommen.
Lizenzen fremder Runtimes/Modelle gelten unabhängig von der Konfigurationslizenz;
siehe ./DEPENDENCIES.md und docs/AUDIO_STACK_THIRD_PARTY_NOTICES.md.

## Danksagungen

Danke an Dr. Roy Meissner für
[Onju Voice ESPHome](https://github.com/rmeissn/onju-voice-esphome),
[tetele/onju-voice-satellite](https://github.com/tetele/onju-voice-satellite),
[s00500/onjuconfig](https://github.com/s00500/onjuconfig),
[Home Assistant Voice PE](https://github.com/esphome/home-assistant-voice-pe),
die originale Onju-Voice-Hardware, ESPHome/Home Assistant, n-IA-hane für
[Audio Stack](https://github.com/n-IA-hane/esphome-audio-stack) und
[Intercom](https://github.com/n-IA-hane/esphome-intercom), sowie Kevin Ahrendt
und alle microWakeWord-Mitwirkenden. Diese Arbeiten sind nicht unsere Erfindung.
Die Original-README und ihre Attributionen bleiben unverändert unter
docs/UPSTREAM_README.md erhalten. Ihre Erfahrungsberichte sind nicht der
Hardware-Prüfstand dieses Forks.
