from pathlib import Path
import re,struct,subprocess,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
sr=ROOT/'onju-voice-assets/tetele-production/sdk/esp-sr-wakenet/esp-sr'
out=ROOT/'.cache/wakenet-tests/blob-host';out.mkdir(parents=True,exist_ok=True)
names=['wn10_alexa','wn10_de_halloesp']
blob=sr.parent/'wakenet-two.bin';buf=blob.read_bytes();meta=json.loads((sr.parent/'wakenet-model.json').read_text())
assert meta['models']==names and len(buf)==meta['blob_size'] and hashlib.sha256(buf).hexdigest()==meta['blob_sha256']
assert struct.unpack_from('<I',buf)[0]==2
offset=4;seen=[]
for name in names:
 raw,n=struct.unpack_from('<32sI',buf,offset);assert raw.split(b'\0')[0].decode()==name;offset+=36
 for j in range(n):
  raw,pos,size=struct.unpack_from('<32sII',buf,offset);offset+=40;file=raw.split(b'\0')[0].decode();data=buf[pos:pos+size]
  assert pos%16==0 and len(data)==size and data==(sr/'model/wakenet_model'/name/file).read_bytes()
  seen.append((name,file,hashlib.sha256(data).hexdigest()))
assert len(seen)==8 and all(name.startswith('wn10_') for name,_,_ in seen)
src=(sr/'src/model_path.c').read_text()
def function(name):
 m=re.search(r'(?:static\s+)?(?:srmodel_list_t\s*\*|uint32_t|char\s*\*|void)\s*'+name+r'\([^;]*?\)\s*\{',src);assert m,name
 pos=m.end();depth=1
 while depth:
  c=src[pos];depth+=(c=='{')-(c=='}');pos+=1
 return src[m.start():pos]
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
const char*names[]={"wn10_alexa","wn10_de_halloesp"};
for(int cycle=0;cycle<8;cycle++){srmodel_list_t*m=srmodel_load(root);assert(m&&m->num==2);
for(int j=0;j<2;j++){assert(!strcmp(m->model_name[j],names[j]));assert(m->model_data[j]->num==4);
// WN10 uses split _MODEL_INFO_p1/p2, so this loader's generic model_info is NULL.
assert(m->model_info[j]==NULL);
for(int i=0;i<m->model_data[j]->num;i++){char*data=m->model_data[j]->data[i];assert(data>=(char*)root&&data+m->model_data[j]->sizes[i]<=(char*)root+n);assert(((uintptr_t)data-(uintptr_t)root)%16==0);}}
srmodel_host_deinit(m);assert(!static_srmodels);}free(root);puts("PASS: official blob loader holds both WakeNet10 models; native DSP creation is not executed on this host");}
'''
(out/'two-loader.c').write_text(code);subprocess.run(['gcc','-std=c11','-fsanitize=address,undefined','-g','-I'+str(sr/'src/include'),str(out/'two-loader.c'),'-o',str(out/'two-loader')],check=True);r=subprocess.run([str(out/'two-loader'),str(blob)],capture_output=True,text=True);print(r.stdout);assert r.returncode==0,r.stderr
(out/'loader-test.json').write_text(json.dumps({'pass':True,'official_loader':True,'asan_ubsan':True,'cycles':8,'models':names,'blob_size':len(buf),'blob_sha256':hashlib.sha256(buf).hexdigest(),'no_device_test':True,'afe_or_dsp_not_executed':True,'wn10_split_metadata_generic_model_info_is_null':True},indent=2))
