from pathlib import Path
import subprocess,json
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'.cache/wakenet-tests/lifecycle';inc=out/'include';inc.mkdir(parents=True,exist_ok=True)
common=r'''
#pragma once
#include <cstdint>
#include <cstddef>
#include <functional>
#include <memory>
#include <vector>
#include <string>
#include <algorithm>
#include <cstring>
#include <cstdlib>
#include <atomic>
#include <cassert>
inline size_t heap_free=210000,heap_largest=140000,psram_free=8000000;
inline int creates=0,destroys=0,loads=0,frees=0,detects=0,allocs=0;
inline int input_rate=16000,input_channels=1,input_samples=128;
inline int detect_result=1;inline bool fail_create=false,can_deallocate=true;
inline std::function<void()> delay_hook;
#define MALLOC_CAP_INTERNAL 1
#define MALLOC_CAP_SPIRAM 2
#define MALLOC_CAP_8BIT 4
inline size_t heap_caps_get_free_size(int c){return (c&MALLOC_CAP_INTERNAL)?heap_free:psram_free;}
inline size_t heap_caps_get_largest_free_block(int){return heap_largest;}
inline void* heap_caps_malloc(size_t n,int caps){assert(caps&MALLOC_CAP_SPIRAM);allocs++;return std::malloc(n);}
inline void heap_caps_free(void*p){std::free(p);}
inline int64_t esp_timer_get_time(){static int64_t t=0;return t+=3000;}
inline int pdMS_TO_TICKS(int x){return x;}
inline void vTaskDelay(int){if(delay_hook)delay_hook();}
inline void vTaskSuspend(void*){}
#define ESP_LOGI(...)
#define ESP_LOGW(...)
#define ESP_LOGCONFIG(...)
#define YESNO(x) ((x)?"YES":"NO")
namespace esphome {
namespace ota {enum OTAState {OTA_STARTED,OTA_ERROR};class OTAComponent{};struct OTAGlobalStateListener{virtual void on_ota_global_state(OTAState,float,uint8_t,OTAComponent*)=0;};struct Callback{void add_global_state_listener(OTAGlobalStateListener*){}};inline Callback cb;inline Callback*get_global_ota_callback(){return &cb;}}
namespace setup_priority{constexpr float AFTER_WIFI=200;}
class Component{public:bool ready=true,failed=false;virtual void setup(){}virtual void loop(){}virtual void dump_config(){}virtual float get_setup_priority()const{return 0;}bool is_ready()const{return ready;}bool is_failed()const{return failed;}void mark_failed(){failed=true;}void status_momentary_error(const char*,int){}};
class StaticTask{public:bool created=false;bool create(void(*)(void*),const char*,int,void*,int,bool){created=true;return true;}bool deallocate(){if(!can_deallocate)return false;created=false;return true;}};
struct ESPPreferenceObject{template<typename T>bool load(T*){return false;}template<typename T>bool save(T*){return true;}};
struct Pref{template<typename T>ESPPreferenceObject make_preference(uint32_t,bool){return {};}};inline Pref prefs;inline Pref*global_preferences=&prefs;
template<typename...Ts>struct Trigger{int calls=0;void trigger(Ts...){calls++;}};
template<typename...Ts>struct Action{virtual void play(const Ts &...)=0;};
namespace microphone{struct Info{int get_sample_rate(){return 16000;}int get_bits_per_sample(){return 16;}int get_channels(){return 1;}};class MicrophoneSource{public:bool muted=false;int starts=0,stops=0;std::function<void(const std::vector<uint8_t>&)> cb;Info get_audio_stream_info(){return {};}bool is_muted(){return muted;}void start(){starts++;}void stop(){stops++;}template<typename F>void add_data_callback(F f){cb=f;}};}
namespace ring_buffer{class RingBuffer{public:std::vector<uint8_t>d;static std::shared_ptr<RingBuffer>create(size_t){return std::make_shared<RingBuffer>();}size_t available(){return d.size();}size_t free(){return 4096-d.size();}void reset(){d.clear();}size_t write(void*p,size_t n){auto*b=(uint8_t*)p;d.insert(d.end(),b,b+n);return n;}size_t read(void*p,size_t n,int){n=std::min(n,d.size());memcpy(p,d.data(),n);d.erase(d.begin(),d.begin()+n);return n;}};}
}
struct model_iface_data_t{};struct srmodel_list_t{int num;char**model_name;};
enum det_mode_t{DET_MODE_90};enum{WAKENET_CHANNEL_VERIFIED=-1};
struct esp_wn_iface_t{model_iface_data_t*(*create)(const void*,det_mode_t);int(*get_samp_chunksize)(model_iface_data_t*);int(*get_samp_rate)(model_iface_data_t*);int(*get_channel_num)(model_iface_data_t*);int(*detect)(model_iface_data_t*,int16_t*);void(*destroy)(model_iface_data_t*);};
inline model_iface_data_t md;
inline model_iface_data_t* create_fake(const void*,det_mode_t){creates++;return fail_create?nullptr:&md;}
inline int samples_fake(model_iface_data_t*){return input_samples;}
inline int rate_fake(model_iface_data_t*){return input_rate;}
inline int channels_fake(model_iface_data_t*){return input_channels;}
inline int detect_fake(model_iface_data_t*,int16_t*){detects++;return detect_result;}
inline void destroy_fake(model_iface_data_t*){destroys++;}
inline esp_wn_iface_t iface={create_fake,samples_fake,rate_fake,channels_fake,detect_fake,destroy_fake};
extern "C" inline srmodel_list_t*srmodel_load(const void*){loads++;static char name[]="wn9_alexa";static char*n[]={name};static srmodel_list_t l{1,n};return &l;}
extern "C" inline const esp_wn_iface_t*esp_wn_handle_from_name(const char*){return &iface;}
extern "C" inline void esp_srmodel_deinit(srmodel_list_t*){frees++;}
'''
(inc/'common.h').write_text(common)
for p in ['esphome/components/ota/ota_backend.h','esphome/core/component.h','esphome/core/automation.h','esphome/core/preferences.h','esphome/core/static_task.h','esphome/core/log.h','esphome/core/hal.h','esphome/components/microphone/microphone_source.h','esphome/components/ring_buffer/ring_buffer.h','esp_heap_caps.h','esp_timer.h','esp_wn_models.h','model_path.h']:
 q=inc/p;q.parent.mkdir(parents=True,exist_ok=True);q.write_text('#pragma once\n#include "common.h"\n')
code=r'''
#include "common.h"
#define protected public
#include "onju_wakenet.h"
#undef protected
#include "onju_wakenet.cpp"
#include <iostream>
using namespace esphome;using namespace esphome::onju_wakenet;
alignas(16) uint8_t blob[160]{};
struct Rig{microphone::MicrophoneSource mic;bool allowed=true;WakeNet w;Rig(){w.set_model_blob(blob,sizeof(blob));w.set_microphone_source(&mic);w.set_can_listen([&]{return allowed;});w.setup();}void frame(){std::vector<uint8_t>d(256,0);w.ring_->write(d.data(),d.size());}};
int main(){
 {Rig r;StartAction<std::string> start(&r.w);StopAction<std::string> stop(&r.w);r.allowed=false;start.play(std::string("test"));assert(!r.w.is_running());r.allowed=true;start.play(std::string("test"));assert(r.w.is_running());stop.play(std::string("test"));r.w.worker(&r.w);r.w.loop();assert(!r.w.is_running());}
 {Rig r;r.allowed=false;r.w.start();assert(!r.w.is_running());r.allowed=true;r.mic.muted=true;r.w.start();assert(!r.w.is_running());r.mic.muted=false;r.w.start();assert(r.w.is_running());r.w.stop();r.w.worker(&r.w);r.w.loop();assert(!r.w.is_running()&&r.w.detected_trigger_.calls==0);}
 {Rig r;r.w.start();r.w.ready_=true;r.w.loop();assert(r.mic.starts==1&&r.w.is_detecting_wake_word());std::vector<uint8_t>d(256,1);r.mic.cb(d);assert(r.w.get_received_audio_bytes()==256);r.mic.muted=true;r.mic.cb(d);assert(r.w.get_received_audio_bytes()==256);r.w.loop();assert(!r.w.accepting_);r.w.worker(&r.w);r.w.loop();assert(!r.w.is_running()&&r.w.detected_trigger_.calls==0);}
 {Rig r;r.w.start();r.frame();int before=detects;r.w.worker(&r.w);assert(detects==before+1&&r.w.get_successful_inferences()==1);can_deallocate=false;r.w.loop();assert(r.w.detected_trigger_.calls==0);can_deallocate=true;r.w.loop();assert(r.mic.stops==1&&r.w.detected_trigger_.calls==1);r.w.loop();assert(r.w.detected_trigger_.calls==1);}
 {Rig r;r.w.start();r.frame();r.w.worker(&r.w);r.w.stop();r.w.loop();assert(r.w.detected_trigger_.calls==0);}
 {Rig r;heap_free=50000;int before=creates;r.w.start();r.w.worker(&r.w);r.w.loop();assert(creates==before&&r.w.failed_&&r.w.detected_trigger_.calls==0);heap_free=210000;}
 for(int kind=0;kind<3;kind++){Rig r;if(kind==0)fail_create=true;if(kind==1)input_rate=48000;if(kind==2)input_channels=3;r.w.start();r.w.worker(&r.w);r.w.loop();assert(r.w.failed_&&r.w.get_successful_inferences()==0&&r.w.detected_trigger_.calls==0);fail_create=false;input_rate=16000;input_channels=1;}
 {Rig r;int requests=0;r.w.set_on_enabled([&]{requests++;});r.w.set_enabled(false);r.w.start();assert(!r.w.is_running());r.w.set_enabled(true);assert(requests==1&&!r.w.is_running());r.w.start();r.w.on_ota_global_state(ota::OTA_STARTED,0,0,nullptr);r.w.worker(&r.w);r.w.loop();assert(!r.w.is_running()&&r.w.detected_trigger_.calls==0);r.w.start();assert(!r.w.is_running());r.w.on_ota_global_state(ota::OTA_ERROR,0,0,nullptr);assert(requests==2);r.w.start();assert(r.w.is_running());r.w.stop();r.w.worker(&r.w);r.w.loop();}
 assert(loads==frees);assert(creates>=destroys);std::cout<<"PASS: actual WakeNet source lifecycle; gating/mute/OFF, bounded audio, stop-before-trigger, cancelled pending detection, task-deallocation barrier, low-memory and invalid-model-format failure cleanup. Vendor DSP mocked; no acoustic/inference quality claim.\n";
}
'''
(out/'test.cpp').write_text(code);src=str(ROOT/'onju-voice-assets/tetele-production/components/onju_wakenet')
subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Wno-unused-parameter','-I'+str(inc),'-I'+src,str(out/'test.cpp'),'-o',str(out/'test')],check=True)
f=subprocess.run([str(out/'test')],check=True,capture_output=True,text=True);print(f.stdout);(out/'result.json').write_text(json.dumps({'PASS':True,'scope':'Actual component lifecycle with mocked vendor DSP/RTOS/heap; no on-device inference'},indent=2))
