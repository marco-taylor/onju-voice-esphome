#!/usr/bin/env python3
"""Prepare one pinned ESP-SR checkout and one aligned, in-Application Alexa blob.
Does not build, contact a device or change the baseline ADF SDK.
"""
from pathlib import Path
import argparse,hashlib,json,shutil,struct,subprocess
ROOT=Path(__file__).resolve().parents[1]
REV='bb552f1a559396a17681299cb3e199a0f1a4520a'
MODEL='wn9_alexa'
TARGET=ROOT/'onju-voice-assets/tetele-production/sdk/esp-sr-wakenet/esp-sr'
def git(*args,cwd=None):return subprocess.check_output(['git',*args],cwd=cwd,text=True).strip()
def pack(directory):
 files=sorted(p for p in directory.iterdir() if p.is_file());header=4+36+40*len(files);cursor=(header+15)&~15;entries=[];payload=bytearray(cursor)
 struct.pack_into('<I',payload,0,1);payload[4:36]=MODEL.encode().ljust(32,b'\0');struct.pack_into('<I',payload,36,len(files))
 for i,p in enumerate(files):
  assert len(p.name.encode())<32;data=p.read_bytes();cursor=(len(payload)+15)&~15;payload.extend(b'\0'*(cursor-len(payload)));struct.pack_into('<32sII',payload,40+40*i,p.name.encode(),cursor,len(data));payload.extend(data);entries.append({'name':p.name,'offset':cursor,'size':len(data),'sha256':hashlib.sha256(data).hexdigest()})
 return bytes(payload),entries
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path);args=ap.parse_args()
 if not TARGET.exists():
  if args.source:
   assert git('rev-parse','HEAD',cwd=args.source)==REV and not git('status','--porcelain',cwd=args.source)
   shutil.copytree(args.source,TARGET,ignore=shutil.ignore_patterns('.git'))
  else:
   TARGET.parent.mkdir(parents=True,exist_ok=True);subprocess.run(['git','clone','--no-checkout','--filter=blob:none','https://github.com/espressif/esp-sr.git',str(TARGET)],check=True);subprocess.run(['git','fetch','--depth','1','origin',REV],cwd=TARGET,check=True);subprocess.run(['git','checkout','--detach',REV],cwd=TARGET,check=True)
  (TARGET/'.onju-source-revision').write_text(REV+'\n')
 assert (TARGET/'.onju-source-revision').read_text().strip()==REV
 assets=ROOT/'onju-voice-assets/tetele-production'
 for name in ['audio_stream','audio_recorder']:
  src=assets/'sdk/esp-adf/components'/name;dest=assets/'sdk/wakenet-adf'/name
  assert src.is_dir(),'Run tools/bootstrap_sdk.py first'
  shutil.copytree(src,dest,dirs_exist_ok=True)
  shutil.copy2(assets/'wakenet-overlay'/name/'CMakeLists.txt',dest/'CMakeLists.txt')
 # Hashes of all official files: copied source mode does not require a nested .git.
 md=TARGET/'model/wakenet_model'/MODEL
 expected={"_MODEL_INFO_":"a93580fe133549f8bb3806317a289d8802721ccfbde87431eff13120e3108a24","wn9_data":"232af46bf553dd832733bb12d0cd4b4027c5b134693870ca6d32a61718c3c7ac","wn9_index":"c5557ca5d1ec6943540a6abbb3ea235a693f4637369f92e873ff566b73a61cfd"}
 for name,expected_hash in expected.items():
  assert hashlib.sha256((md/name).read_bytes()).hexdigest()==expected_hash,name+" hash differs from pinned official model"
 data,entries=pack(md);out=TARGET.parent/'wakenet-alexa.bin';out.write_bytes(data)
 info={'esp_sr_commit':REV,'model':MODEL,'model_info':(md/'_MODEL_INFO_').read_text().strip(),'blob_size':len(data),'blob_sha256':hashlib.sha256(data).hexdigest(),'files':entries,'alignment':16,'license':'ESPRESSIF MIT; Espressif products only; retain notices; trademark rights separate'}
 (TARGET.parent/'wakenet-model.json').write_text(json.dumps(info,indent=2)+'\n');print(json.dumps(info,indent=2))
