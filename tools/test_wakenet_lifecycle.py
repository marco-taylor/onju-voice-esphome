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
#include <thread>
#include <mutex>
#include <chrono>
#include <map>
inline size_t heap_free=210000,heap_largest=140000,psram_free=8000000;
inline int creates=0,destroys=0,loads=0,frees=0,detects=0,allocs=0;
inline int input_rate=16000,input_channels=1,input_samples=128;
inline int detect_result=1;inline bool fail_create=false,can_deallocate=true;
inline std::atomic<int> target_id{1},feed_count{0},fetch_count{0},adds{0};inline int add_result=3;inline bool bad_format=false;
inline std::function<void()> delay_hook;
#define MALLOC_CAP_INTERNAL 1
#define MALLOC_CAP_SPIRAM 2
#define MALLOC_CAP_8BIT 4
inline size_t heap_caps_get_free_size(int c){return (c&MALLOC_CAP_INTERNAL)?heap_free:psram_free;}
inline size_t heap_caps_get_largest_free_block(int){return heap_largest;}
inline void* heap_caps_malloc(size_t n,int caps){assert(caps&MALLOC_CAP_SPIRAM);allocs++;return std::malloc(n);}
inline void heap_caps_free(void*p){std::free(p);}
inline int64_t esp_timer_get_time(){return std::chrono::duration_cast<std::chrono::microseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();}
inline int esp_reset_reason(){return 1;}
inline size_t heap_caps_get_minimum_free_size(int c){return heap_caps_get_free_size(c);}
inline int pdMS_TO_TICKS(int x){return x;}
inline void vTaskDelay(int){std::this_thread::sleep_for(std::chrono::milliseconds(1));}
inline void vTaskSuspend(void*){}
#define ESP_LOGI(...)
#define ESP_LOGW(...)
#define ESP_LOGCONFIG(...)
#define YESNO(x) ((x)?"YES":"NO")
namespace esphome {
namespace ota {enum OTAState {OTA_STARTED,OTA_ERROR};class OTAComponent{};struct OTAGlobalStateListener{virtual void on_ota_global_state(OTAState,float,uint8_t,OTAComponent*)=0;};struct Callback{void add_global_state_listener(OTAGlobalStateListener*){}};inline Callback cb;inline Callback*get_global_ota_callback(){return &cb;}}
namespace setup_priority{constexpr float AFTER_WIFI=200;}
class Component{public:bool ready=true,failed=false;virtual void setup(){}virtual void loop(){}virtual void dump_config(){}virtual float get_setup_priority()const{return 0;}bool is_ready()const{return ready;}bool is_failed()const{return failed;}void mark_failed(){failed=true;}void status_momentary_error(const char*,int){}};
class StaticTask{std::thread t;public:bool create(void(*f)(void*),const char*,int,void*p,int,bool){assert(!t.joinable());t=std::thread(f,p);return true;}bool deallocate(){if(!can_deallocate)return false;if(t.joinable())t.join();return true;}};
inline std::map<uint32_t,uint8_t> stored;inline int saves=0;struct ESPPreferenceObject{uint32_t key=0;template<typename T>bool load(T*p){if(!stored.count(key))return false;*p=stored[key];return true;}template<typename T>bool save(T*p){stored[key]=*p;saves++;return true;}};
struct Pref{template<typename T>ESPPreferenceObject make_preference(uint32_t key,bool){return {key};}};inline Pref prefs;inline Pref*global_preferences=&prefs;
template<typename...Ts>struct Trigger{int calls=0;void trigger(Ts...){calls++;}};
template<typename...Ts>struct Action{virtual void play(const Ts &...)=0;};
namespace microphone{struct Info{int get_sample_rate(){return 16000;}int get_bits_per_sample(){return 16;}int get_channels(){return 1;}};class MicrophoneSource{public:bool muted=false;int starts=0,stops=0;std::function<void(const std::vector<uint8_t>&)> cb;Info get_audio_stream_info(){return {};}bool is_muted(){return muted;}void start(){starts++;}void stop(){stops++;}template<typename F>void add_data_callback(F f){cb=f;}};}
namespace ring_buffer{class RingBuffer{std::mutex m;std::vector<uint8_t>d;size_t cap;public:explicit RingBuffer(size_t n):cap(n){}static std::shared_ptr<RingBuffer>create(size_t n){return std::make_shared<RingBuffer>(n);}size_t available(){std::lock_guard<std::mutex>l(m);return d.size();}size_t free(){std::lock_guard<std::mutex>l(m);return cap-d.size();}void reset(){std::lock_guard<std::mutex>l(m);d.clear();}size_t write(void*p,size_t n){std::lock_guard<std::mutex>l(m);auto*b=(uint8_t*)p;d.insert(d.end(),b,b+n);return n;}size_t read(void*p,size_t n,int){std::lock_guard<std::mutex>l(m);n=std::min(n,d.size());memcpy(p,d.data(),n);d.erase(d.begin(),d.begin()+n);return n;}};}
}
struct srmodel_list_t{int num;char**model_name;};struct esp_afe_sr_data_t{};
struct afe_config_t{bool aec_init,se_init,ns_init,vad_init,agc_init,wakenet_init;char*wakenet_model_name;char*wakenet_model_name_2;int wakenet_mode,memory_alloc_mode;float afe_linear_gain;bool fixed_first_channel,fixed_output_channel,output_playback_channel;int afe_ringbuf_size;bool debug_init;struct{int mic_num,ref_num,total_ch_num,sample_rate;}pcm_config;};
enum{AFE_TYPE_SR,AFE_MODE_LOW_COST,DET_MODE_90,AFE_MEMORY_ALLOC_MORE_PSRAM,WAKENET_DETECTED};
struct afe_fetch_result_t{int ret_value,wakeup_state,wakenet_model_index,wake_word_index;};
struct esp_afe_sr_iface_t{esp_afe_sr_data_t*(*create_from_config)(afe_config_t*);int(*add_wakenet_model)(esp_afe_sr_data_t*,const char*);int(*get_feed_chunksize)(esp_afe_sr_data_t*);int(*get_feed_channel_num)(esp_afe_sr_data_t*);int(*get_fetch_channel_num)(esp_afe_sr_data_t*);int(*get_samp_rate)(esp_afe_sr_data_t*);int(*get_fetch_chunksize)(esp_afe_sr_data_t*);int(*feed)(esp_afe_sr_data_t*,int16_t*);afe_fetch_result_t*(*fetch_with_delay)(esp_afe_sr_data_t*,int);void(*destroy)(esp_afe_sr_data_t*);};
inline esp_afe_sr_data_t md;
inline esp_afe_sr_data_t*create_fake(afe_config_t*c){creates++;assert(c->wakenet_init&&!c->aec_init&&!c->vad_init&&!c->ns_init&&!c->agc_init&&!c->se_init);assert(!strcmp(c->wakenet_model_name,"wn10_alexa")&&!strcmp(c->wakenet_model_name_2,"wn10_de_halloesp"));return fail_create?nullptr:&md;}
inline int add_fake(esp_afe_sr_data_t*,const char*n){assert(!strcmp(n,"wn9_jarvis_tts"));adds++;return add_result;}
inline int samples_fake(esp_afe_sr_data_t*){return input_samples;}inline int channels_fake(esp_afe_sr_data_t*){return bad_format?2:1;}inline int rate_fake(esp_afe_sr_data_t*){return input_rate;}
inline int feed_fake(esp_afe_sr_data_t*,int16_t*){feed_count++;return 1;}
inline afe_fetch_result_t*fetch_fake(esp_afe_sr_data_t*,int){static afe_fetch_result_t r;std::this_thread::sleep_for(std::chrono::milliseconds(1));if(fetch_count>=feed_count)return nullptr;fetch_count++;r={0,target_id>0?WAKENET_DETECTED:0,target_id.load(),1};return &r;}
inline void destroy_fake(esp_afe_sr_data_t*){destroys++;}
inline esp_afe_sr_iface_t iface={create_fake,add_fake,samples_fake,channels_fake,channels_fake,rate_fake,samples_fake,feed_fake,fetch_fake,destroy_fake};
extern "C" inline srmodel_list_t*srmodel_load(const void*){loads++;static char a[]="wn10_alexa",b[]="wn10_de_halloesp",c[]="wn9_jarvis_tts";static char*n[]={a,b,c};static srmodel_list_t l{3,n};return &l;}
extern "C" inline void esp_srmodel_deinit(srmodel_list_t*){frees++;}
extern "C" inline afe_config_t*afe_config_init(const char*f,srmodel_list_t*m,int,int){assert(!strcmp(f,"M")&&m->num==3);return new afe_config_t{};}
extern "C" inline afe_config_t*afe_config_check(afe_config_t*c){c->pcm_config={1,0,1,16000};return c;}
extern "C" inline void afe_config_free(afe_config_t*c){delete c;}
extern "C" inline const esp_afe_sr_iface_t*esp_afe_handle_from_config(afe_config_t*){return &iface;}
'''
(inc/'common.h').write_text(common)
for p in ["esphome/components/ota/ota_backend.h","esphome/core/component.h","esphome/core/automation.h","esphome/core/preferences.h","esphome/core/static_task.h","esphome/core/log.h","esphome/core/hal.h","esphome/components/microphone/microphone_source.h","esphome/components/ring_buffer/ring_buffer.h","esp_heap_caps.h","esp_timer.h","esp_system.h","esp_afe_sr_models.h","model_path.h"]:
 q=inc/p;q.parent.mkdir(parents=True,exist_ok=True);q.write_text('#pragma once\n#include "common.h"\n')
code=r'''

#include "common.h"
#define protected public
#include "onju_wakenet.h"
#undef protected
#include "onju_wakenet.cpp"
#include <iostream>
using namespace esphome;using namespace esphome::onju_wakenet;
alignas(16) uint8_t blob[1024]{};
struct Rig{microphone::MicrophoneSource mic;bool allowed=true;WakeNet w;Rig(){feed_count=0;fetch_count=0;w.set_model_blob(blob,sizeof(blob));w.set_microphone_source(&mic);w.set_can_listen([&]{return allowed;});w.setup();}void pump(bool audio=true){w.loop();if(audio&&w.is_detecting_wake_word()){std::vector<uint8_t>d(256,1);mic.cb(d);}std::this_thread::sleep_for(std::chrono::milliseconds(2));}void finish(){for(int i=0;i<1000&&w.is_running();i++)pump();assert(!w.is_running());}~Rig(){if(w.is_running()){w.stop();finish();}}};
int main(){
 stored.clear();
 {Rig r;r.allowed=false;r.w.start();assert(!r.w.is_running());r.allowed=true;r.mic.muted=true;r.w.start();assert(!r.w.is_running());r.mic.muted=false;r.w.set_active_words({});r.w.start();assert(!r.w.is_running());}
 stored.clear();
 for(int id=1;id<=3;id++){Rig r;r.w.set_active_words({WakeNet::WORD_IDS[id-1]});int before=adds;target_id=id;r.w.start();r.finish();assert(adds==before+1);assert(r.w.detected_trigger_.calls==1&&r.w.get_successful_inferences()>0&&r.w.get_received_audio_bytes()>0);assert(r.mic.stops==1);}
 {Rig r;r.w.set_active_words({"alexa","jarvis"});int count=saves;r.w.set_active_words({"jarvis","alexa"});assert(saves==count);r.w.set_active_words({"alexa","jarvis","hallo_esp"});assert(r.w.active_mask_==5);r.w.set_active_words({"unknown"});assert(r.w.active_mask_==5);}
 {Rig r;assert(r.w.word_enabled(0)&&r.w.word_enabled(2)&&!r.w.word_enabled(1));}
 {Rig r;target_id=1;r.w.set_active_words({"jarvis"});r.w.start();for(int i=0;i<30;i++)r.pump();assert(r.w.detected_trigger_.calls==0&&r.w.get_successful_inferences()>0);r.w.stop();r.finish();}
 {Rig r;r.w.set_active_words({"alexa"});target_id=4;r.w.start();r.finish();assert(r.w.failed_&&r.w.detected_trigger_.calls==0);}
 for(int kind=0;kind<4;kind++){Rig r;target_id=1;if(kind==0)fail_create=true;if(kind==1)add_result=-1;if(kind==2)bad_format=true;if(kind==3)heap_free=50000;r.w.start();r.finish();assert(r.w.failed_&&r.w.detected_trigger_.calls==0);fail_create=false;add_result=3;bad_format=false;heap_free=210000;}
 {Rig r;target_id=1;r.w.set_active_words({"alexa"});r.w.start();for(int i=0;i<1000&&!r.w.done_.load();i++)r.pump();assert(r.w.done_);r.w.stop();r.w.loop();assert(!r.w.is_running()&&r.w.detected_trigger_.calls==0);}
 {Rig r;target_id=0;r.w.start();for(int i=0;i<20;i++)r.pump();assert(r.w.is_detecting_wake_word());r.mic.muted=true;r.w.loop();r.finish();assert(!r.w.accepting_&&r.w.detected_trigger_.calls==0);}
 {Rig r;int enabled=0;r.w.set_on_enabled([&]{enabled++;});r.w.start();r.w.on_ota_global_state(ota::OTA_STARTED,0,0,nullptr);r.finish();r.w.start();assert(!r.w.is_running());r.w.on_ota_global_state(ota::OTA_ERROR,0,0,nullptr);assert(enabled==1);}
 {Rig r;target_id=0;r.w.start();for(int i=0;i<15;i++)r.pump();r.w.set_active_words({});r.finish();assert(r.w.detected_trigger_.calls==0);}
 stored.clear();stored[0x574E4131]=0;{Rig r;assert(!r.w.is_enabled());}
 stored.clear();stored[0x574E4131]=1;{Rig r;assert(r.w.word_enabled(0));}
 assert(loads==frees&&creates-destroys==1); // Exactly one deliberately failed create.
 std::cout<<"PASS: actual AFE consumer lifecycle; three registrations, IDs 1/2/3, rejection of fourth/unknown ID and >2 HA assignments, PCM/feed/fetch, persistent mask migration, Mute/OFF, cancellation, low-memory failure, cleanup and OTA guard. Vendor AFE/DSP and FreeRTOS mocked; no target-runtime claim.\n";
}
'''
(out/'test.cpp').write_text(code)
src=str(ROOT/'onju-voice-assets/tetele-production/components/onju_wakenet')
subprocess.run(['g++','-std=c++17','-pthread','-fsanitize=address,undefined','-g','-Wno-unused-parameter','-I'+str(inc),'-I'+src,str(out/'test.cpp'),'-o',str(out/'test')],check=True)
r=subprocess.run([str(out/'test')],capture_output=True,text=True,timeout=30);print(r.stdout);assert r.returncode==0,r.stderr
(out/'result.json').write_text(json.dumps({'PASS':True,'vendor_DSP_mocked':True,'actual_component':True,'asan_ubsan':True},indent=2))
