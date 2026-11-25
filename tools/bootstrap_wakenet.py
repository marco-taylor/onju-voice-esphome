#!/usr/bin/env python3
"""Prepare one pinned ESP-SR checkout and one aligned, in-Application two-model blob.
Does not build, contact a device or change the baseline ADF SDK.
"""
from pathlib import Path
import argparse,hashlib,json,shutil,struct,subprocess,tempfile,runpy,sys
ROOT=Path(__file__).resolve().parents[1]
REV='bb552f1a559396a17681299cb3e199a0f1a4520a'
WAKE_MODELS=['wn10_alexa','wn10_de_halloesp']
NS_MODEL='nsnet2'
MODELS=WAKE_MODELS+[NS_MODEL]
TARGET=ROOT/'onju-voice-assets/tetele-production/sdk/esp-sr-wakenet/esp-sr'
def git(*args,cwd=None):return subprocess.check_output(['git',*args],cwd=cwd,text=True).strip()
def prepare_esp32s3(directories, destination):
 # Run the exact pinned vendor target preparation, not a local format conversion.
 model_tools=TARGET/'model'
 sys.path.insert(0,str(model_tools))
 try:
  vendor=runpy.run_path(str(model_tools/'movemodel.py'))
 finally:
  sys.path.pop(0)
 prepared={}
 for name in WAKE_MODELS:
  target=destination/name
  vendor['copy_wn10_model'](str(directories[name]),str(target),'esp32s3')
  prepared[name]=target
 # NS uses the pinned official copy routine, without target-variant renaming.
 cfg=destination/'ns-sdkconfig';cfg.write_text('CONFIG_SR_NSN_NSNET2=y\n')
 vendor['copy_nsnet_from_sdkconfig'](str(model_tools),str(cfg),str(destination))
 prepared[NS_MODEL]=destination/NS_MODEL
 return prepared

def pack(directories):
 # Fail closed if raw multi-target assets bypass official preparation again.
 for name in MODELS:
  actual={p.name for p in directories[name].iterdir() if p.is_file()}
  expected_files={'wn10_data','_MODEL_INFO_'} if name in WAKE_MODELS else {'nsnet2_data','nsnet2_index','_MODEL_INFO_'}
  if actual!=expected_files:
   raise ValueError(f'{name}: expected prepared ESP32-S3 files, got {sorted(actual)}')
 files={n:sorted(p for p in directories[n].iterdir() if p.is_file()) for n in MODELS}
 header=4+36*len(MODELS)+40*sum(map(len,files.values()));payload=bytearray((header+15)&~15);struct.pack_into('<I',payload,0,len(MODELS));offset=4;entries=[]
 for model in MODELS:
  struct.pack_into('<32sI',payload,offset,model.encode(),len(files[model]));offset+=36
  for p in files[model]:
   data=p.read_bytes();cursor=(len(payload)+15)&~15;payload.extend(b'\0'*(cursor-len(payload)));struct.pack_into('<32sII',payload,offset,p.name.encode(),cursor,len(data));offset+=40;payload.extend(data);entries.append({'model':model,'name':p.name,'offset':cursor,'size':len(data),'sha256':hashlib.sha256(data).hexdigest()})
 assert offset==header
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
 # Exact pinned model files; bootstrap never fetches floating model revisions.
 directories={n:TARGET/'model/wakenet_model'/n for n in MODELS}
 for n,d in directories.items():
  if n==NS_MODEL:directories[n]=TARGET/'model/nsnet_model'/n
  assert directories[n].is_dir(),n
 expected={"wn10_alexa/_MODEL_INFO_p1":"21e6a3544c58b770981d4fd8153c06ace8a99795f701e12647ce32f9d86fe66a","wn10_alexa/_MODEL_INFO_p2":"bad88074818c5fbef750a7f3e223ff226e6da544cadbeefcc50d23b95906620d","wn10_alexa/wn10_data_p1":"ddd8bb15b8fe95adcaecfcef66eb67dc35d9d2f1133b0bcd9d8b9a890128227c","wn10_alexa/wn10_data_p2":"534d0f56c4f3ee61e65495762b9c6333357d2433167568b20746879b1829c3a9","wn10_de_halloesp/_MODEL_INFO_p1":"58d2617ae1e1625fcb5307bc704d453c81efe0ae216752a36aa1a1c571c3d904","wn10_de_halloesp/_MODEL_INFO_p2":"8de149c71d0e0a49f0324ad72416084a9131ffb50a3be75fd73b9817c9fba998","wn10_de_halloesp/wn10_data_p1":"1d723b8267ad1b7fb4111c2a864220c07df33dc211b1768feb4aa46539f1dcfa","wn10_de_halloesp/wn10_data_p2":"223bf433548dc062dc296a96465668982d5987943fd528f7b37b0dc3e16edb86"}
 for key,digest in expected.items():
  assert hashlib.sha256((TARGET/'model/wakenet_model'/key).read_bytes()).hexdigest()==digest,key+' differs from pinned official model'
 ns_expected={"_MODEL_INFO_":"d6faa56078a6c954f27088385f4a6cd7ca3e8da37a68d30e35e45f59e9a823f1","nsnet2_data":"88c12b3f98d4983bd8078b5bf9c0ddc24d5301c0008a0038f05a6b300413147a","nsnet2_index":"1a73ed9796d6117aacbdbf596895425cdcd826bd97453b7187310ea740e2b2bd"}
 for file,digest in ns_expected.items():
  assert hashlib.sha256((TARGET/'model/nsnet_model'/NS_MODEL/file).read_bytes()).hexdigest()==digest,file+' differs from pinned NS model'
 with tempfile.TemporaryDirectory(prefix='onju-esp32s3-models-') as temp:
  prepared=prepare_esp32s3(directories,Path(temp))
  data,entries=pack(prepared)
 out=TARGET.parent/'wakenet-two.bin';out.write_bytes(data)
 info={'target':'esp32s3','preparation':'official model/movemodel.py:copy_wn10_model','variant':'p1','esp_sr_commit':REV,'models':MODELS,'wakeword_models':WAKE_MODELS,'noise_suppression_model':NS_MODEL,'blob_size':len(data),'blob_sha256':hashlib.sha256(data).hexdigest(),'files':entries,'alignment':16,'license':'ESPRESSIF MIT; Espressif products only; retain notices; trademark rights separate'}
 (TARGET.parent/'wakenet-model.json').write_text(json.dumps(info,indent=2)+'\n');print(json.dumps(info,indent=2))
