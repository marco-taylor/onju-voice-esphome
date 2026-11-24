#!/usr/bin/env python3
"""Read-only, host-side integration gates. Passing means blockers reproduced,
not that a WakeNet firmware/recognizer has been implemented or validated.
Usage: python3 tools/test_wakenet_feasibility.py --old-sdk PATH --esp-sr PATH --output PATH
"""
import argparse,csv,hashlib,json,re,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--old-sdk',type=Path,required=True);p.add_argument('--esp-sr',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[1];old=a.old_sdk/'components/esp-sr';new=a.esp_sr;checks={}
def check(k,condition):
 checks[k]=bool(condition)
 if not condition:raise AssertionError(k)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def iface(p):
 s=p.read_text();m=re.search(r'typedef struct\s*{([^{}]*)}\s*esp_wn_iface_t;',s,re.S);assert m
 return re.findall(r'esp_wn_iface_op_\w+\s+(\w+)\s*;',m[1])
def targets(p):return set(re.findall(r'add_prebuilt_library\(\s*(\w+)',p.read_text()))
check('baseline_exact_1_2_0',subprocess.check_output(['git','-C',str(root),'merge-base','HEAD','v1.2.0'],text=True).strip()=='133cd1024a7a53551fb4367be7ed44216d9c7b2e')
check('runtime_source_unchanged',subprocess.run(['git','-C',str(root),'diff','--quiet','v1.2.0','--','onju-voice.yaml','onju-voice-assets'],check=False).returncode==0)
collisions=sorted(targets(old/'CMakeLists.txt')&targets(new/'CMakeLists.txt'))
check('parallel_native_sdk_targets_collide','wakenet' in collisions and 'esp_audio_front_end' in collisions)
o=iface(old/'include/esp32s3/esp_wn_iface.h');n=iface(new/'include/esp32s3/esp_wn_iface.h')
check('wakenet_interface_abi_differs',o!=n and 'reset_det_threshold' not in o and 'reset_det_threshold' in n)
check('old_loader_has_no_native_embedded_blob_api','srmodel_load(' not in (old/'src/include/model_path.h').read_text())
check('new_loader_has_embedded_blob_api','srmodel_load(' in (new/'src/include/model_path.h').read_text())
# Exact public 1.2.0 partition layout. Default app alignment 64 KiB, data alignment 4 KiB.
partition_file=root/'.esphome/wakenet-feasibility/onju-voice/partitions.csv'
rows=[list(map(str.strip,row[:5])) for row in csv.reader(partition_file.read_text().splitlines()) if row and not row[0].startswith('#')]
cursor=0x9000;layout=[]
for name,typ,sub,offset,size in rows:
 align=0x10000 if typ=='app' else 0x1000;start=((cursor+align-1)//align)*align;end=start+int(size,0);layout.append({'name':name,'offset':start,'size':int(size,0),'end':end});cursor=end
check('no_space_to_append_model_partition',cursor==0x1000000)
check('no_existing_model_partition',not any(x['name']=='model' for x in layout))
models={}
for name in ['wn9_alexa','wn9s_alexa','wn10_alexa','wn9_jarvis_tts','wn9_mycroft_tts']:
 directory=new/'model/wakenet_model'/name;assert directory.is_dir()
 files={x.name:{'bytes':x.stat().st_size,'sha256':sha(x)} for x in sorted(directory.iterdir()) if x.is_file()};models[name]={'bytes':sum(x['bytes'] for x in files.values()),'files':files,'metadata':{x.name:x.read_text().strip() for x in directory.glob('_MODEL_INFO*')}}
check('official_alexa_all_three_model_folders_exist',all(x in models for x in ['wn9_alexa','wn9s_alexa','wn10_alexa']))
check('official_jarvis_mycroft_exist',all(x in models for x in ['wn9_jarvis_tts','wn9_mycroft_tts']))
allnames=[x.name.lower() for x in (new/'model/wakenet_model').iterdir()]
check('no_official_nabu_or_hey_home_assistant_model',not any('nabu' in x or 'home_assistant' in x for x in allnames))
source=(root/'onju-voice.yaml').read_text()
check('no_active_afe_aec_dsp_stage_in_yaml','esp_sr_afe:' not in source and 'aec:' not in source and 'noise_suppression:' not in source)
check('va_catalog_directly_bound_to_mww','this->micro_wake_word_->get_wake_words()' in (root/'onju-voice-assets/tetele-production/components/voice_assistant/voice_assistant.cpp').read_text())
check('espressif_only_license', 'for use on all ESPRESSIF SYSTEMS products' in (new/'LICENSE').read_text())
result={'all_feasibility_tests_passed':all(checks.values()),'firmware_implemented':False,'checks':checks,'duplicate_targets':collisions,'old_iface_fields':o,'new_iface_fields':n,'models':models,'partition_layout':layout,'partition_end':cursor,'latest_sr_commit':subprocess.check_output(['git','-C',str(new),'rev-parse','HEAD'],text=True).strip(),'latest_sr_manifest':(new/'idf_component.yml').read_text(),'old_sr_commit':'0c1eecaac259af95f76723b61d4e16cef5904fc7'}
a.output.write_text(json.dumps(result,indent=2));print(json.dumps({'tests':len(checks),'PASS':all(checks.values()),'blockers_reproduced':True,'firmware_implemented':False}))
