# Local production sounds

Wake and timer sounds are from the official Home Assistant Voice PE repository,
commit d4e6fa43d6a1a7d342b7d4d403567e06516719de:
https://github.com/esphome/home-assistant-voice-pe/tree/d4e6fa43d6a1a7d342b7d4d403567e06516719de/sounds

© 2024 Clayton Charles Tapp (https://www.cctaudio.com/), CC BY 4.0:
https://creativecommons.org/licenses/by/4.0/ . The original notice is retained
in ./VOICE_PE_SOUNDS_LICENSE.md. This sound-specific license applies rather than
the general repository MIT notice. Changes: offline FLAC-to-MP3 encoding only,
48-kHz mono / 320-kbit/s, no normalization, gain, trim, fade, filter or resampling.
The original FLACs and the exact hardware-tested MP3s are included.

./manifest.json records pinned sources, original/MP3 SHA256, encoder and arguments.
./rebuild_timer.py reproduces the timer MP3 using the recorded ffmpeg binary.
The wake MP3 is byte-for-byte the existing hardware-tested asset. These playback
assets do not change the 16-kHz microphone path. No FLAC decoder is added.

./tetele-error-original.mp3 is the unchanged existing Tetele error sound, now
embedded locally. Attribution: Error #8 by UNIVERSFIELD,
https://freesound.org/people/UNIVERSFIELD/sounds/734442/ . Historical attribution
records identify CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/):
https://github.com/alessandrobelli/Ticker-Farm#assets . The original Freesound
page now reports the sound deleted; that limitation is recorded, not concealed.
Pinned Tetele source and checksum are in ./manifest.json. No audio edits.
This unrelated sound is not attributed to the Voice PE author.

All three sounds are flash-resident; GitHub is never contacted for playback.
No unused Center, mute, reset, jack or Easter-egg sound files are shipped.
