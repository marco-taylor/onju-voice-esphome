#!/usr/bin/env python3
"""Validate real ESP32-S3 native AFE/WakeNet-create evidence; never substitute mocks.

Run after a separately authorized target test:
  python tools/test_wakenet_native.py --runtime PATH --device PATH --build-info PATH --ota-result PATH --application PATH
Requires native slot checks from the same running build and its verified OTA image.
Without target evidence exits 2 (NOT RUN), not PASS. This is an evidence validator,
not an x86 implementation/emulation of the proprietary Xtensa DSP runtime.
"""
import argparse,hashlib,json,re,sys
from pathlib import Path

def native_checks(runtime):
 events=runtime.get('events',[])
 native={}
 for event in events:
  if event.get('after') is False:
   continue
  match=re.search(r'(?:DIAG|HISTORY) (AFE_[A-Z0-9_]+) t=(\d+) native=(-?\d+) ready=(\d+)',event.get('message',''))
  if match:
   name,when,value,ready=match.groups()
   native.setdefault(name,[]).append((int(when),int(value),bool(int(ready))))
 for name in ['AFE_START_03_ALEXA_MODEL_FOUND','AFE_START_04_HALLOESP_MODEL_FOUND','AFE_START_11_AFE_HANDLE_VALID']:
  assert native.get(name) and all(value!=0 for _,value,_ in native[name]),name+' missing/null'
 for name in ['AFE_NATIVE_SLOT_1','AFE_NATIVE_SLOT_2']:
  assert native.get(name) and all(value==1 for _,value,_ in native[name]),name+' native model creation/slot check failed or absent'
 assert native.get('AFE_START_16_READY_SET_TRUE') and any(ready for _,_,ready in native['AFE_START_16_READY_SET_TRUE'])
 assert not any(k.startswith('AFE_ERR_') for k in native),'native initialization error present'
 return {'native_alexa_model_creation':'PASS','native_halloesp_model_creation':'PASS','both_native_slots':'PASS','source':'real target ESP-SR AFE create plus reset_wakenet_threshold; no mock DSP'}

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 for name in ['runtime','device','build-info','ota-result','application']:
  parser.add_argument('--'+name,type=Path)
 args=parser.parse_args()
 if not all(vars(args).values()):
  print('NOT RUN: real ESP32-S3 target evidence and matching application are required',file=sys.stderr)
  return 2
 try:
  device=json.loads(args.device.read_text());build=json.loads(args.build_info.read_text());ota=json.loads(args.ota_result.read_text())
  assert device['compilation_time']==build['build_time_str'],'wrong target build'
  assert device['esphome_version']==build['esphome_version']
  assert ota['return_code']==0 and ota['sha256']==hashlib.sha256(args.application.read_bytes()).hexdigest(),'unverified installed application'
  result=native_checks(json.loads(args.runtime.read_text()))
  print(json.dumps(result,indent=2))
  return 0
 except (AssertionError,KeyError,ValueError,OSError) as err:
  print('FAIL: '+str(err),file=sys.stderr)
  return 1
if __name__=='__main__':
 raise SystemExit(main())
