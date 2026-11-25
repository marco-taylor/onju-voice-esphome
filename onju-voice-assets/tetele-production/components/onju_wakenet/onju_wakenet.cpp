#include "onju_wakenet.h"
#include "esphome/core/log.h"
#include "esphome/core/hal.h"
#include "esp_heap_caps.h"
#include "esp_timer.h"
#include "esp_system.h"
#include "esp_err.h"
#include <cmath>
#include <algorithm>
extern "C" {
#include "esp_afe_sr_models.h"
#include "model_path.h"
}
namespace esphome::onju_wakenet {
static const char *const TAG="onju.wakenet";
static const char *const MODELS[2]={"wn10_alexa","wn10_de_halloesp"};
static void memory(const char *stage){
  ESP_LOGI(TAG,"%s internal=%u min_internal=%u largest=%u psram=%u",stage,
    unsigned(heap_caps_get_free_size(MALLOC_CAP_INTERNAL|MALLOC_CAP_8BIT)),
    unsigned(heap_caps_get_minimum_free_size(MALLOC_CAP_INTERNAL|MALLOC_CAP_8BIT)),
    unsigned(heap_caps_get_largest_free_block(MALLOC_CAP_INTERNAL|MALLOC_CAP_8BIT)),
    unsigned(heap_caps_get_free_size(MALLOC_CAP_SPIRAM)));
}
void WakeNet::diag(const char *event,intptr_t native,bool heap){
  const uint32_t n=diag_count_.fetch_add(1);
  if(n>=64)return;
  auto &e=diag_events_[n];e.event=event;e.ms=millis();e.native=native;e.ready=ready_.load();
  if(heap){e.free=heap_caps_get_free_size(MALLOC_CAP_INTERNAL|MALLOC_CAP_8BIT);e.min=heap_caps_get_minimum_free_size(MALLOC_CAP_INTERNAL|MALLOC_CAP_8BIT);e.largest=heap_caps_get_largest_free_block(MALLOC_CAP_INTERNAL|MALLOC_CAP_8BIT);e.psram=heap_caps_get_free_size(MALLOC_CAP_SPIRAM);}
  e.published.store(true,std::memory_order_release);
  ESP_LOGI(TAG,"DIAG %s t=%u native=%ld ready=%d heap=%u min=%u largest=%u psram=%u",event,unsigned(e.ms),long(native),e.ready,unsigned(e.free),unsigned(e.min),unsigned(e.largest),unsigned(e.psram));
}
void WakeNet::dump_diag(){
  for(uint32_t i=0;i<std::min<uint32_t>(diag_count_.load(),64);i++){const auto&e=diag_events_[i];if(e.published.load(std::memory_order_acquire))ESP_LOGCONFIG(TAG,"HISTORY %s t=%u native=%ld ready=%d heap=%u min=%u largest=%u psram=%u",e.event,unsigned(e.ms),long(e.native),e.ready,unsigned(e.free),unsigned(e.min),unsigned(e.largest),unsigned(e.psram));}
}
void WakeNet::setup(){
  diag("READY_INITIAL_FALSE");
  auto info=source_->get_audio_stream_info();
  if(!blob_ || (uintptr_t(blob_)&15) || blob_size_<512 || info.get_sample_rate()!=16000 || info.get_bits_per_sample()!=16 || info.get_channels()!=1){diag("AFE_ERR_SETUP_FORMAT",0,true);mark_failed();return;}
  feed_signal_=xSemaphoreCreateBinaryStatic(&feed_signal_storage_);
  if(!feed_signal_){diag("AFE_ERR_FEED_SIGNAL",0,true);mark_failed();return;}
  preference_=global_preferences->make_preference<uint8_t>(0x574E4132,true);
  uint8_t mask=3;
  if(!preference_.load(&mask)){
    uint8_t prior=0;
    if(global_preferences->make_preference<uint8_t>(0x574E4133,true).load(&prior))mask=prior&3;
    else {bool old=true;if(global_preferences->make_preference<bool>(0x574E4131,true).load(&old))mask=old?1:0;}
  }
  active_mask_=mask<=3?mask:3;
  ring_=ring_buffer::RingBuffer::create(16384);
  if(!ring_){mark_failed();return;}
  ota::get_global_ota_callback()->add_global_state_listener(this);
  ESP_LOGI(TAG,"Boot reset=%d blob=%p size=%u aligned16=yes; two WakeNet10 models, two HA assignments",int(esp_reset_reason()),blob_,unsigned(blob_size_));
  source_->add_data_callback([this](const std::vector<uint8_t>&data){
    if(!accepting_.load() || source_->is_muted())return;
    if(audio_bytes_.load()==0)diag("AFE_START_20_FIRST_PCM",data.size());
    if((data.size()&1) || ring_->free()<data.size()){drops_++;return;}
    audio_bytes_+=ring_->write(const_cast<uint8_t*>(data.data()),data.size());
  });
}
void WakeNet::set_active_words(const std::vector<std::string>&words){
  uint8_t mask=0;
  for(const auto&w:words){
    bool found=false;for(size_t i=0;i<2;i++)if(w==WORD_IDS[i]){mask|=1U<<i;found=true;break;}
    if(!found){ESP_LOGW(TAG,"Unknown wakeword selection rejected");return;}
  }
  if(__builtin_popcount(mask)>2){ESP_LOGW(TAG,"More than two HA assignments rejected");return;}
  if(active_mask_.exchange(mask)==mask)return;
  preference_.save(&mask); // ESPHome Preferences batching unchanged; no cyclic writes.
  stop();if(mask && on_enabled_)on_enabled_();
}
void WakeNet::on_ota_global_state(ota::OTAState state,float progress,uint8_t error,ota::OTAComponent*comp){
  if(state==ota::OTA_STARTED){ota_blocked_=true;stop();}
  else if(state==ota::OTA_ERROR){ota_blocked_=false;if(is_enabled()&&on_enabled_)on_enabled_();}
}
void WakeNet::start(){
  if(ota_blocked_.load()||!is_ready()||is_failed()||state_!=STOPPED||!is_enabled()||source_->is_muted()||!can_listen_()){diag("AFE_ERR_START_GUARD",(ota_blocked_.load()?1:0)|(!is_ready()?2:0)|(is_failed()?4:0)|(state_!=STOPPED?8:0)|(!is_enabled()?16:0)|(source_->is_muted()?32:0),true);return;}
  xSemaphoreTake(feed_signal_,0);first_feed_done_=false;
  stop_requested_=false;cancelled_=false;ready_=false;diag("READY_FALSE_NEW_START");done_=false;detected_id_=0;failed_=false;feed_done_=false;ring_->reset();state_=STARTING;
  if(!task_.create(worker,"wn_afe_fetch",8192,this,3,false)){diag("AFE_ERR_WORKER_TASK",0,true);state_=STOPPED;status_momentary_error("task_alloc",1000);}else diag("AFE_WORKER_TASK_CREATED",reinterpret_cast<intptr_t>(task_.get_handle()));
}
void WakeNet::stop(){cancelled_=true;accepting_=false;stop_requested_=true;if(feed_signal_)xSemaphoreGive(feed_signal_);if(state_!=STOPPED)state_=STOPPING;}
void WakeNet::loop(){
  if(state_==STOPPED)return;
  if(source_->is_running()&&!diag_mic_running_.exchange(true))diag("AFE_START_19_MIC_RUNNING");
  if(source_->is_running()&&feeds_.load()&&inferences_.load()&&!diag_operational_.exchange(true))diag("AFE_START_23_LISTENING_OPERATIONAL");
  if(!is_enabled()||source_->is_muted()||!can_listen_())stop();
  if(ready_.load()&&state_==STARTING&&!stop_requested_.load()){diag("AFE_START_17_MIC_START_REQUESTED");source_->start();diag("AFE_START_18_MIC_START_RETURNED_VOID",source_->is_running());accepting_=true;state_=LISTENING;}
  if(done_.load()&&task_.deallocate()){
    accepting_=false;source_->stop();state_=STOPPED;
    if(failed_.load())status_momentary_error("afe_start",1000);
    const int id=detected_id_.exchange(0);
    if(id>=1&&id<=2&&!cancelled_.load()&&word_enabled(id-1)&&!source_->is_muted()&&can_listen_())detected_trigger_.trigger(PHRASES[id-1]);
  }
}
void WakeNet::feeder(void*arg){
  auto*self=static_cast<WakeNet*>(arg);
  self->diag("AFE_FEED_TASK_ENTRY");
  const auto*iface=static_cast<const esp_afe_sr_iface_t*>(self->afe_iface_);
  auto*data=static_cast<esp_afe_sr_data_t*>(self->afe_data_);
  const size_t bytes=self->feed_samples_*sizeof(int16_t);
  auto*frame=static_cast<int16_t*>(heap_caps_malloc(bytes,MALLOC_CAP_SPIRAM|MALLOC_CAP_8BIT));
  self->diag("AFE_FEED_BUFFER_RESULT",reinterpret_cast<intptr_t>(frame),true);
  if(!frame){self->diag("AFE_ERR_FEED_BUFFER_ALLOC",0,true);self->failed_=true;self->stop_requested_=true;}
  uint64_t squares=0;int64_t sum=0;uint32_t count=0,clipped=0;int peak=0;bool first_window=true;
  while(frame&&!self->stop_requested_.load()){
    if(self->ring_->available()<bytes){vTaskDelay(pdMS_TO_TICKS(2));continue;}
    if(self->ring_->read(frame,bytes,0)!=bytes){self->drops_++;continue;}
    for(int i=0;i<self->feed_samples_;i++){const int x=frame[i];sum+=x;squares+=int64_t(x)*x;peak=std::max(peak,std::abs(x));clipped+=(x>=32767||x<=-32768);count++;}
    const int result=iface->feed(data,frame);
    if(result<0){self->diag("AFE_ERR_FEED_NATIVE",result,true);self->failed_=true;self->stop_requested_=true;break;}
    if(result==0){self->drops_++;continue;}
    if(self->feeds_.fetch_add(1)==0)self->diag("AFE_START_21_FIRST_AFE_FEED",result);
    self->first_feed_done_=true;xSemaphoreGive(self->feed_signal_);
    // First second, then ten-second aggregates; no per-sample logging or capture.
    if(count>=(first_window?16000U:160000U)){
      const double dc=double(sum)/count,rms2=double(squares)/count;
      ESP_LOGI(TAG,"PCM n=%u dc=%.1f rms=%.1f ac_rms=%.1f peak=%d clip=%u feed=%u fetch=%u drops=%u",unsigned(count),dc,std::sqrt(rms2),std::sqrt(std::max(0.0,rms2-dc*dc)),peak,unsigned(clipped),unsigned(self->feeds_.load()),unsigned(self->inferences_.load()),unsigned(self->drops_.load()));
      if(first_window)memory("AFE first PCM");
      first_window=false;sum=0;squares=0;count=0;clipped=0;peak=0;
    }
  }
  if(frame)heap_caps_free(frame);
  self->diag("AFE_FEED_TASK_EXIT",self->stop_requested_.load());self->feed_done_=true;xSemaphoreGive(self->feed_signal_);vTaskSuspend(nullptr);
}
void WakeNet::worker(void*arg){
  auto*self=static_cast<WakeNet*>(arg);srmodel_list_t*models=nullptr;afe_config_t*cfg=nullptr;
  const esp_afe_sr_iface_t*iface=nullptr;esp_afe_sr_data_t*data=nullptr;bool feeder_created=false;
  bool wait_for_feed=true,fetch_enabled=false,no_data_reported=false;
  self->diag("AFE_START_00_ENTRY",0,true);
  self->diag("AFE_START_01_MODEL_BLOB_FOUND",reinterpret_cast<intptr_t>(self->blob_));
  memory("AFE init begin");
  if(heap_caps_get_free_size(MALLOC_CAP_INTERNAL|MALLOC_CAP_8BIT)<131072 || heap_caps_get_largest_free_block(MALLOC_CAP_INTERNAL|MALLOC_CAP_8BIT)<65536 || heap_caps_get_free_size(MALLOC_CAP_SPIRAM)<4194304){self->diag("AFE_ERR_MEMORY_PRE",0,true);goto cleanup;}
  self->diag("AFE_START_08_MEMORY_PRECHECK_PASS",0,true);
  if(self->stop_requested_.load()){self->diag("AFE_ERR_CANCELLED_BEFORE_INIT");goto cleanup;}
  models=srmodel_load(self->blob_);
  self->diag("AFE_START_02_MODEL_LOADER_RETURN",reinterpret_cast<intptr_t>(models));
  if(!models||models->num!=2){self->diag("AFE_ERR_MODEL_LOADER",models?models->num:-1,true);goto cleanup;}
  for(int i=0;i<2;i++){if(std::string(models->model_name[i])!=MODELS[i]){self->diag(i==0?"AFE_ERR_ALEXA_MODEL":"AFE_ERR_HALLOESP_MODEL",i,true);goto cleanup;}self->diag(i==0?"AFE_START_03_ALEXA_MODEL_FOUND":"AFE_START_04_HALLOESP_MODEL_FOUND",reinterpret_cast<intptr_t>(models->model_name[i]));}
  self->diag("AFE_START_05_MODEL_METADATA_SLOTS_VALID",models->num);
  cfg=afe_config_init("M",models,AFE_TYPE_SR,AFE_MODE_LOW_COST);self->diag("AFE_START_06_AFE_CONFIG_RETURN",reinterpret_cast<intptr_t>(cfg));if(!cfg){self->diag("AFE_ERR_AFE_CONFIG",0,true);goto cleanup;}
  // Existing ADF/DC/gain delivers one 16-kHz s16 microphone; no playback reference exists.
  cfg->aec_init=false;cfg->se_init=false;cfg->ns_init=false;cfg->vad_init=false;cfg->agc_init=false;
  cfg->wakenet_init=true;cfg->wakenet_model_name=models->model_name[0];cfg->wakenet_model_name_2=models->model_name[1];
  cfg->wakenet_mode=DET_MODE_90;cfg->memory_alloc_mode=AFE_MEMORY_ALLOC_MORE_PSRAM;
  cfg->afe_linear_gain=1.0f;cfg->fixed_first_channel=true;cfg->fixed_output_channel=true;cfg->output_playback_channel=false;
  cfg->afe_ringbuf_size=16;cfg->debug_init=false;
  cfg=afe_config_check(cfg);
  if(cfg){self->diag("AFE_CONFIG_FLAGS",(cfg->aec_init?1:0)|(cfg->se_init?2:0)|(cfg->ns_init?4:0)|(cfg->vad_init?8:0)|(cfg->agc_init?16:0)|(cfg->wakenet_init?32:0));self->diag("AFE_INPUT_RATE",cfg->pcm_config.sample_rate);self->diag("AFE_INPUT_COUNTS",(cfg->pcm_config.mic_num<<16)|(cfg->pcm_config.ref_num<<8)|cfg->pcm_config.total_ch_num);}
  if(!cfg || cfg->aec_init||cfg->se_init||cfg->ns_init||cfg->vad_init||cfg->agc_init||cfg->pcm_config.mic_num!=1||cfg->pcm_config.ref_num!=0||cfg->pcm_config.total_ch_num!=1||cfg->pcm_config.sample_rate!=16000){self->diag("AFE_ERR_INPUT_FORMAT",0,true);goto cleanup;}
  self->diag("AFE_START_07_INPUT_FORMAT_VALID",cfg->pcm_config.total_ch_num);
  iface=esp_afe_handle_from_config(cfg);self->diag("AFE_INTERFACE_RETURN",reinterpret_cast<intptr_t>(iface));if(!iface){self->diag("AFE_ERR_AFE_INTERFACE",0,true);goto cleanup;}
  self->diag("AFE_START_09_AFE_CREATE_BEGIN",0,true);
  data=iface->create_from_config(cfg);self->diag("AFE_CREATE_NATIVE_RETURN",reinterpret_cast<intptr_t>(data),true);if(!data){self->diag("AFE_ERR_AFE_CREATE",0,true);goto cleanup;}
  self->diag("AFE_START_10_AFE_CREATE_SUCCESS");self->diag("AFE_START_11_AFE_HANDLE_VALID",reinterpret_cast<intptr_t>(data));
  // Verify both native slots exist; a partially initialized AFE must not claim readiness.
  // Fresh-model defaults are retained, not replaced with application cutoffs.
  if(self->diag_result("AFE_NATIVE_SLOT_1",iface->reset_wakenet_threshold(data,1))!=1 || self->diag_result("AFE_NATIVE_SLOT_2",iface->reset_wakenet_threshold(data,2))!=1){self->diag("AFE_ERR_MODEL_SLOTS",0,true);goto cleanup;}
  // Both native configuration slots are used; no dynamic model registration.
  memory("AFE two WakeNet10 models loaded");
  self->feed_samples_=iface->get_feed_chunksize(data);
  if(self->feed_samples_<=0||self->feed_samples_>2048||iface->get_feed_channel_num(data)!=1||iface->get_fetch_channel_num(data)!=1||iface->get_samp_rate(data)!=16000||iface->get_fetch_chunksize(data)<=0||iface->get_fetch_chunksize(data)>2048){self->diag("AFE_ERR_FRAME_SIZE",self->feed_samples_,true);goto cleanup;}
  self->diag("AFE_START_12_FRAME_SIZES_VALID",self->feed_samples_);self->diag("AFE_FETCH_CHUNK",iface->get_fetch_chunksize(data));
  ESP_LOGI(TAG,"AFE ready M/16000/s16 feed=%d fetch=%d; IDs 1=Alexa 2=Hallo ESP; WN only",self->feed_samples_,iface->get_fetch_chunksize(data));
  // Fail closed rather than consuming the VA/audio reserve. Runtime peaks remain to be measured.
  if(heap_caps_get_free_size(MALLOC_CAP_INTERNAL|MALLOC_CAP_8BIT)<98304||heap_caps_get_largest_free_block(MALLOC_CAP_INTERNAL|MALLOC_CAP_8BIT)<49152||heap_caps_get_free_size(MALLOC_CAP_SPIRAM)<2097152){self->diag("AFE_ERR_MEMORY_POST",0,true);goto cleanup;}
  self->diag("AFE_START_13_AFE_BUFFERS_CREATED",0,true);
  self->afe_iface_=iface;self->afe_data_=data;
  self->diag("AFE_START_14_FEED_TASK_CREATE_BEGIN");
  if(!self->feed_task_.create(feeder,"wn_afe_feed",4096,self,3,false)){self->diag("AFE_ERR_FEED_TASK",0,true);goto cleanup;}
  self->diag("AFE_START_15_FEED_TASK_CREATED",reinterpret_cast<intptr_t>(self->feed_task_.get_handle()),true);
  feeder_created=true;self->ready_=true;self->diag("AFE_START_16_READY_SET_TRUE",0,true);
  while(!self->stop_requested_.load()){
    // The pinned one-mic AFE reports ESP_FAIL for an incomplete ring-buffer read.
    // Wait for actual successful feed, not elapsed startup time. Stop/feeder exit
    // also wake this semaphore, so cancellation never depends on more audio.
    if(wait_for_feed){
      xSemaphoreTake(self->feed_signal_,portMAX_DELAY);
      if(self->stop_requested_.load())break;
      if(!self->first_feed_done_.load())continue;
      wait_for_feed=false;
      if(!fetch_enabled){self->diag("AFE_FETCH_ENABLED");fetch_enabled=true;}
    }
    xSemaphoreTake(self->feed_signal_,0); // Discard stale feed notification before this read.
    const int64_t begin=esp_timer_get_time();auto*result=iface->fetch_with_delay(data,pdMS_TO_TICKS(100));
    if(!result){self->diag("AFE_ERR_FETCH_HANDLE",0,true);self->failed_=true;break;}
    if(result->ret_value==ESP_FAIL){
      if(!no_data_reported){self->diag("AFE_FETCH_NO_DATA",result->ret_value);no_data_reported=true;}
      wait_for_feed=true;continue; // Re-arm on a new successful feed; never poll empty input.
    }
    if(result->ret_value<0){self->diag("AFE_ERR_FETCH_NATIVE",result->ret_value,true);self->failed_=true;break;}
    const uint32_t elapsed=esp_timer_get_time()-begin;self->inference_total_us_+=elapsed;
    if(elapsed>self->inference_max_us_.load())self->inference_max_us_=elapsed;
    if(self->inferences_.fetch_add(1)==0)self->diag("AFE_START_22_FIRST_AFE_FETCH",result->ret_value); // Successful AFE fetch: vendor WakeNet path ran. Includes wait, not pure inference timing.
    if(result->wakeup_state==WAKENET_DETECTED){
      const int id=result->wakenet_model_index;
      ESP_LOGI(TAG,"AFE detection model_id=%d word_index=%d",id,result->wake_word_index);
      if(id<1||id>2||result->wake_word_index!=1){self->failed_=true;break;}
      self->detections_++;
      if(self->word_enabled(id-1)){self->detected_id_=id;self->stop_requested_=true;break;}
    }
  }
cleanup:
  self->diag("AFE_CLEANUP_ENTRY",self->cancelled_.load(),true);
  self->accepting_=false;self->stop_requested_=true;
  // Keep fetch draining until feed exits; feed can block on a full vendor output ring.
  // No task is deleted while it can access AFE/model memory.
  if(feeder_created){while(!self->feed_done_.load()){if(iface&&data&&self->first_feed_done_.load())iface->fetch_with_delay(data,pdMS_TO_TICKS(100));vTaskDelay(1);}while(!self->feed_task_.deallocate())vTaskDelay(1);}
  self->afe_data_=nullptr;self->afe_iface_=nullptr;
  if(!self->ready_.load()&&!self->cancelled_.load()){self->failed_=true;ESP_LOGW(TAG,"AFE start failed; no listening claim");}
  if(data&&iface)iface->destroy(data);
  if(cfg)afe_config_free(cfg);
  if(models)esp_srmodel_deinit(models);
  memory("AFE stopped");self->done_=true;vTaskSuspend(nullptr);
}
void WakeNet::dump_config(){
  dump_diag();
  ESP_LOGCONFIG(TAG,"AFE WakeNet10 Alexa + Hallo ESP; blob=%u mask=%u listening=%s PCM=%u feed=%u fetch=%u detect=%u drops=%u fetch_wait_max_us=%u",unsigned(blob_size_),unsigned(active_mask_.load()),YESNO(is_detecting_wake_word()),unsigned(audio_bytes_.load()),unsigned(feeds_.load()),unsigned(inferences_.load()),unsigned(detections_.load()),unsigned(drops_.load()),unsigned(inference_max_us_.load()));
}
}
