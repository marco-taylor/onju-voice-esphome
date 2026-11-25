#include "onju_wakenet.h"
#include "esphome/core/log.h"
#include "esphome/core/hal.h"
#include "esp_heap_caps.h"
#include "esp_timer.h"
#include "esp_system.h"
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
void WakeNet::setup(){
  auto info=source_->get_audio_stream_info();
  if(!blob_ || (uintptr_t(blob_)&15) || blob_size_<512 || info.get_sample_rate()!=16000 || info.get_bits_per_sample()!=16 || info.get_channels()!=1){mark_failed();return;}
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
  if(ota_blocked_.load()||!is_ready()||is_failed()||state_!=STOPPED||!is_enabled()||source_->is_muted()||!can_listen_())return;
  stop_requested_=false;cancelled_=false;ready_=false;done_=false;detected_id_=0;failed_=false;feed_done_=false;ring_->reset();state_=STARTING;
  if(!task_.create(worker,"wn_afe_fetch",8192,this,3,false)){state_=STOPPED;status_momentary_error("task_alloc",1000);}
}
void WakeNet::stop(){cancelled_=true;accepting_=false;stop_requested_=true;if(state_!=STOPPED)state_=STOPPING;}
void WakeNet::loop(){
  if(state_==STOPPED)return;
  if(!is_enabled()||source_->is_muted()||!can_listen_())stop();
  if(ready_.load()&&state_==STARTING&&!stop_requested_.load()){source_->start();accepting_=true;state_=LISTENING;}
  if(done_.load()&&task_.deallocate()){
    accepting_=false;source_->stop();state_=STOPPED;
    if(failed_.load())status_momentary_error("afe_start",1000);
    const int id=detected_id_.exchange(0);
    if(id>=1&&id<=2&&!cancelled_.load()&&word_enabled(id-1)&&!source_->is_muted()&&can_listen_())detected_trigger_.trigger(PHRASES[id-1]);
  }
}
void WakeNet::feeder(void*arg){
  auto*self=static_cast<WakeNet*>(arg);
  const auto*iface=static_cast<const esp_afe_sr_iface_t*>(self->afe_iface_);
  auto*data=static_cast<esp_afe_sr_data_t*>(self->afe_data_);
  const size_t bytes=self->feed_samples_*sizeof(int16_t);
  auto*frame=static_cast<int16_t*>(heap_caps_malloc(bytes,MALLOC_CAP_SPIRAM|MALLOC_CAP_8BIT));
  if(!frame){self->failed_=true;self->stop_requested_=true;}
  uint64_t squares=0;int64_t sum=0;uint32_t count=0,clipped=0;int peak=0;bool first_window=true;
  while(frame&&!self->stop_requested_.load()){
    if(self->ring_->available()<bytes){vTaskDelay(pdMS_TO_TICKS(2));continue;}
    if(self->ring_->read(frame,bytes,0)!=bytes){self->drops_++;continue;}
    for(int i=0;i<self->feed_samples_;i++){const int x=frame[i];sum+=x;squares+=int64_t(x)*x;peak=std::max(peak,std::abs(x));clipped+=(x>=32767||x<=-32768);count++;}
    const int result=iface->feed(data,frame);
    if(result<0){self->failed_=true;self->stop_requested_=true;break;}
    if(result==0){self->drops_++;continue;}
    self->feeds_++;
    // First second, then ten-second aggregates; no per-sample logging or capture.
    if(count>=(first_window?16000U:160000U)){
      const double dc=double(sum)/count,rms2=double(squares)/count;
      ESP_LOGI(TAG,"PCM n=%u dc=%.1f rms=%.1f ac_rms=%.1f peak=%d clip=%u feed=%u fetch=%u drops=%u",unsigned(count),dc,std::sqrt(rms2),std::sqrt(std::max(0.0,rms2-dc*dc)),peak,unsigned(clipped),unsigned(self->feeds_.load()),unsigned(self->inferences_.load()),unsigned(self->drops_.load()));
      if(first_window)memory("AFE first PCM");
      first_window=false;sum=0;squares=0;count=0;clipped=0;peak=0;
    }
  }
  if(frame)heap_caps_free(frame);
  self->feed_done_=true;vTaskSuspend(nullptr);
}
void WakeNet::worker(void*arg){
  auto*self=static_cast<WakeNet*>(arg);srmodel_list_t*models=nullptr;afe_config_t*cfg=nullptr;
  const esp_afe_sr_iface_t*iface=nullptr;esp_afe_sr_data_t*data=nullptr;bool feeder_created=false;
  memory("AFE init begin");
  if(heap_caps_get_free_size(MALLOC_CAP_INTERNAL|MALLOC_CAP_8BIT)<131072 || heap_caps_get_largest_free_block(MALLOC_CAP_INTERNAL|MALLOC_CAP_8BIT)<65536 || heap_caps_get_free_size(MALLOC_CAP_SPIRAM)<4194304)goto cleanup;
  if(self->stop_requested_.load())goto cleanup;
  models=srmodel_load(self->blob_);
  if(!models||models->num!=2)goto cleanup;
  for(int i=0;i<2;i++)if(std::string(models->model_name[i])!=MODELS[i])goto cleanup;
  cfg=afe_config_init("M",models,AFE_TYPE_SR,AFE_MODE_LOW_COST);if(!cfg)goto cleanup;
  // Existing ADF/DC/gain delivers one 16-kHz s16 microphone; no playback reference exists.
  cfg->aec_init=false;cfg->se_init=false;cfg->ns_init=false;cfg->vad_init=false;cfg->agc_init=false;
  cfg->wakenet_init=true;cfg->wakenet_model_name=models->model_name[0];cfg->wakenet_model_name_2=models->model_name[1];
  cfg->wakenet_mode=DET_MODE_90;cfg->memory_alloc_mode=AFE_MEMORY_ALLOC_MORE_PSRAM;
  cfg->afe_linear_gain=1.0f;cfg->fixed_first_channel=true;cfg->fixed_output_channel=true;cfg->output_playback_channel=false;
  cfg->afe_ringbuf_size=16;cfg->debug_init=false;
  cfg=afe_config_check(cfg);
  if(!cfg || cfg->aec_init||cfg->se_init||cfg->ns_init||cfg->vad_init||cfg->agc_init||cfg->pcm_config.mic_num!=1||cfg->pcm_config.ref_num!=0||cfg->pcm_config.total_ch_num!=1||cfg->pcm_config.sample_rate!=16000)goto cleanup;
  iface=esp_afe_handle_from_config(cfg);if(!iface)goto cleanup;
  data=iface->create_from_config(cfg);if(!data)goto cleanup;
  // Verify both native slots exist; a partially initialized AFE must not claim readiness.
  // Fresh-model defaults are retained, not replaced with application cutoffs.
  if(iface->reset_wakenet_threshold(data,1)!=1 || iface->reset_wakenet_threshold(data,2)!=1)goto cleanup;
  // Both native configuration slots are used; no dynamic model registration.
  memory("AFE two WakeNet10 models loaded");
  self->feed_samples_=iface->get_feed_chunksize(data);
  if(self->feed_samples_<=0||self->feed_samples_>2048||iface->get_feed_channel_num(data)!=1||iface->get_fetch_channel_num(data)!=1||iface->get_samp_rate(data)!=16000||iface->get_fetch_chunksize(data)<=0||iface->get_fetch_chunksize(data)>2048)goto cleanup;
  ESP_LOGI(TAG,"AFE ready M/16000/s16 feed=%d fetch=%d; IDs 1=Alexa 2=Hallo ESP; WN only",self->feed_samples_,iface->get_fetch_chunksize(data));
  // Fail closed rather than consuming the VA/audio reserve. Runtime peaks remain to be measured.
  if(heap_caps_get_free_size(MALLOC_CAP_INTERNAL|MALLOC_CAP_8BIT)<98304||heap_caps_get_largest_free_block(MALLOC_CAP_INTERNAL|MALLOC_CAP_8BIT)<49152||heap_caps_get_free_size(MALLOC_CAP_SPIRAM)<2097152)goto cleanup;
  self->afe_iface_=iface;self->afe_data_=data;
  if(!self->feed_task_.create(feeder,"wn_afe_feed",4096,self,3,false))goto cleanup;
  feeder_created=true;self->ready_=true;
  while(!self->stop_requested_.load()){
    const int64_t begin=esp_timer_get_time();auto*result=iface->fetch_with_delay(data,pdMS_TO_TICKS(100));
    if(!result)continue;
    if(result->ret_value<0){self->failed_=true;break;}
    const uint32_t elapsed=esp_timer_get_time()-begin;self->inference_total_us_+=elapsed;
    if(elapsed>self->inference_max_us_.load())self->inference_max_us_=elapsed;
    self->inferences_++; // Successful AFE fetch: vendor WakeNet path ran. Includes wait, not pure inference timing.
    if(result->wakeup_state==WAKENET_DETECTED){
      const int id=result->wakenet_model_index;
      ESP_LOGI(TAG,"AFE detection model_id=%d word_index=%d",id,result->wake_word_index);
      if(id<1||id>2||result->wake_word_index!=1){self->failed_=true;break;}
      self->detections_++;
      if(self->word_enabled(id-1)){self->detected_id_=id;self->stop_requested_=true;break;}
    }
  }
cleanup:
  self->accepting_=false;self->stop_requested_=true;
  // Keep fetch draining until feed exits; feed can block on a full vendor output ring.
  // No task is deleted while it can access AFE/model memory.
  if(feeder_created){while(!self->feed_done_.load()){if(iface&&data)iface->fetch_with_delay(data,pdMS_TO_TICKS(100));vTaskDelay(1);}while(!self->feed_task_.deallocate())vTaskDelay(1);}
  self->afe_data_=nullptr;self->afe_iface_=nullptr;
  if(!self->ready_.load()&&!self->cancelled_.load()){self->failed_=true;ESP_LOGW(TAG,"AFE start failed; no listening claim");}
  if(data&&iface)iface->destroy(data);
  if(cfg)afe_config_free(cfg);
  if(models)esp_srmodel_deinit(models);
  memory("AFE stopped");self->done_=true;vTaskSuspend(nullptr);
}
void WakeNet::dump_config(){
  ESP_LOGCONFIG(TAG,"AFE WakeNet10 Alexa + Hallo ESP; blob=%u mask=%u listening=%s PCM=%u feed=%u fetch=%u detect=%u drops=%u fetch_wait_max_us=%u",unsigned(blob_size_),unsigned(active_mask_.load()),YESNO(is_detecting_wake_word()),unsigned(audio_bytes_.load()),unsigned(feeds_.load()),unsigned(inferences_.load()),unsigned(detections_.load()),unsigned(drops_.load()),unsigned(inference_max_us_.load()));
}
}
