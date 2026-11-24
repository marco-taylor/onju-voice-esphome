from pathlib import Path
import struct,json,hashlib,subprocess
ROOT=Path(__file__).resolve().parents[1]
root=ROOT/'onju-voice-assets/tetele-production/sdk/esp-sr-wakenet';blob=(root/'wakenet-alexa.bin').read_bytes();meta=json.loads((root/'wakenet-model.json').read_text());assert len(blob)==meta['blob_size'] and hashlib.sha256(blob).hexdigest()==meta['blob_sha256'];assert struct.unpack_from('<I',blob)[0]==1 and blob[4:36].split(b'\0')[0]==b'wn9_alexa';num=struct.unpack_from('<I',blob,36)[0];assert num==3
for i,f in enumerate(meta['files']):
 name,offset,length=struct.unpack_from('<32sII',blob,40+40*i);assert name.split(b'\0')[0].decode()==f['name'];assert offset%16==0 and offset>=160 and offset+length<=len(blob);assert (offset,length)==(f['offset'],f['size']);data=blob[offset:offset+length];assert hashlib.sha256(data).hexdigest()==f['sha256'];assert data==(root/'esp-sr/model/wakenet_model/wn9_alexa'/f['name']).read_bytes()
src=(root/'esp-sr/src/model_path.c').read_text()
def function(name):
 import re
 m=re.search(r'(?:static\s+)?(?:srmodel_list_t\s*\*|uint32_t|char\s*\*|void)\s*'+name+r'\([^;]*?\)\s*\{',src);assert m,name
 pos=m.end();depth=1
 while depth:
  c=src[pos];depth+=(c=='{')-(c=='}');pos+=1
 return src[m.start():pos]
out=ROOT/'.cache/wakenet-tests/blob-host';out.mkdir(exist_ok=True)
code='''#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "model_path.h"
#define ESP_LOGI(...)
static srmodel_list_t*static_srmodels=NULL;
static char*base=(char*)"unused";
void set_model_base_path(const char*p){base=(char*)p;}
'''+ '\n'.join(function(n) for n in ['get_model_info','srmodel_list_alloc','read_int32','srmodel_load','srmodel_host_deinit'])+r'''
int main(int argc,char**argv){assert(argc==2);FILE*f=fopen(argv[1],"rb");assert(f);fseek(f,0,SEEK_END);size_t n=ftell(f);rewind(f);unsigned char*root=malloc(n);assert(fread(root,1,n,f)==n);fclose(f);
for(int j=0;j<8;j++){srmodel_list_t*m=srmodel_load(root);assert(m&&m->num==1);assert(!strcmp(m->model_name[0],"wn9_alexa"));assert(m->model_data[0]->num==3);assert(strstr(m->model_info[0],"wakenet9l_v4h8_Alexa"));assert(!base);for(int i=0;i<3;i++){char*data=m->model_data[0]->data[i];assert(data>=(char*)root&&data+m->model_data[0]->sizes[i]<=(char*)root+n);assert(((uintptr_t)data-(uintptr_t)root)%16==0);}srmodel_host_deinit(m);assert(!static_srmodels);}free(root);puts("PASS: actual official srmodel_load accepts the aligned Application blob; file pointers reference the original blob, no bulk model copy by loader; metadata correct; repeated load/deinit works");}
'''
(out/'loader.c').write_text(code);subprocess.run(['gcc','-std=c11','-fsanitize=address,undefined','-g','-I'+str(root/'esp-sr/src/include'),str(out/'loader.c'),'-o',str(out/'loader')],check=True);r=subprocess.run([str(out/'loader'),str(root/'wakenet-alexa.bin')],capture_output=True,text=True);print(r.stdout);assert r.returncode==0,r.stderr
(out/'result.json').write_text(json.dumps({'pass':True,'model':'wn9_alexa','blob_size':len(blob),'sha256':meta['blob_sha256'],'official_loader_tested':True,'asan_ubsan':True,'no_bulk_copy_by_loader':True,'vendor_inference_not_executed':True},indent=2))
