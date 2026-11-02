"""Recreate the embedded MP3 from the unmodified official Voice PE FLAC."""
import argparse,hashlib,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--ffmpeg',required=True,type=Path);a=p.parse_args()
r=Path(__file__).resolve().parent;m=json.loads((r/'manifest.json').read_text());t=m['integrated']['timer']
assert hashlib.sha256(a.ffmpeg.read_bytes()).hexdigest()==t['encoder_binary_sha256'],'Use the recorded ffmpeg binary'
subprocess.run([str(a.ffmpeg.resolve()),*t['arguments']],cwd=r,check=True)
assert hashlib.sha256((r/t['mp3']).read_bytes()).hexdigest()==t['sha256'],'Output checksum mismatch'
print('Reproducible timer MP3: PASS')
