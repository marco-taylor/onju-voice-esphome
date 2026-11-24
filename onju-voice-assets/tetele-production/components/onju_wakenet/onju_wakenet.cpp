#include "onju_wakenet.h"
#include "esphome/core/log.h"
#include "esphome/core/hal.h"
#include "esp_heap_caps.h"
#include "esp_timer.h"
extern "C" {
#include "esp_wn_models.h"
#include "model_path.h"
}
namespace esphome::onju_wakenet {
static const char *const TAG="onju.wakenet";
void WakeNet::setup() {
  auto info=source_->get_audio_stream_info();
  if (!blob_ || (uintptr_t(blob_)&15) || blob_size_<160 || info.get_sample_rate()!=16000 || info.get_bits_per_sample()!=16 || info.get_channels()!=1) { mark_failed(); return; }
  preference_=global_preferences->make_preference<bool>(0x574E4131,true); preference_.load(&enabled_);
  ring_=ring_buffer::RingBuffer::create(4096);
  if (!ring_) { mark_failed(); return; }
  ota::get_global_ota_callback()->add_global_state_listener(this);
  source_->add_data_callback([this](const std::vector<uint8_t> &data) {
    if (!accepting_.load() || source_->is_muted()) return;
    if ((data.size()&1) || ring_->free()<data.size()) { drops_++; return; }
    audio_bytes_+=ring_->write(const_cast<uint8_t *>(data.data()),data.size());
  });
}
void WakeNet::on_ota_global_state(ota::OTAState state, float progress, uint8_t error, ota::OTAComponent *comp) {
  if (state==ota::OTA_STARTED) {ota_blocked_=true;stop();}
  else if (state==ota::OTA_ERROR) {ota_blocked_=false;if(enabled_ && on_enabled_)on_enabled_();}
}
void WakeNet::set_enabled(bool enabled) {
  if (enabled_==enabled) return;
  enabled_=enabled;preference_.save(&enabled_);
  if (!enabled) stop(); else if (on_enabled_) on_enabled_();
}
void WakeNet::start() {
  if (ota_blocked_.load() || !is_ready() || is_failed() || state_!=STOPPED || !enabled_ || source_->is_muted() || !can_listen_()) return;
  stop_requested_=false;cancelled_=false;ready_=false;done_=false;detected_=false;failed_=false;ring_->reset();state_=STARTING;
  if (!task_.create(worker,"wakenet",8192,this,3,false)) {state_=STOPPED;status_momentary_error("task_alloc",1000);}
}
void WakeNet::stop() {
  // Cancels both a pending start and a delayed detection. No forced task deletion.
  cancelled_=true;accepting_=false;stop_requested_=true;
  if (state_!=STOPPED) state_=STOPPING;
}
void WakeNet::loop() {
  if (state_==STOPPED) return;
  if (!enabled_ || source_->is_muted() || !can_listen_()) stop();
  if (ready_.load() && state_==STARTING && !stop_requested_.load()) {source_->start();accepting_=true;state_=LISTENING;}
  if (done_.load() && task_.deallocate()) {
    accepting_=false;source_->stop();state_=STOPPED;
    if (failed_.load()) status_momentary_error("model_start",1000);
    const bool emit=detected_.exchange(false) && !cancelled_.load() && enabled_ && !source_->is_muted() && can_listen_();
    if (emit) detected_trigger_.trigger("Alexa");
  }
}
void WakeNet::worker(void *arg) {
  auto *self=static_cast<WakeNet *>(arg);
  srmodel_list_t *models=nullptr;const esp_wn_iface_t *iface=nullptr;model_iface_data_t *model=nullptr;int16_t *frame=nullptr;
  const size_t before=heap_caps_get_free_size(MALLOC_CAP_INTERNAL|MALLOC_CAP_8BIT);
  ESP_LOGI(TAG,"Init begin internal_free=%u largest=%u psram_free=%u",unsigned(before),unsigned(heap_caps_get_largest_free_block(MALLOC_CAP_INTERNAL|MALLOC_CAP_8BIT)),unsigned(heap_caps_get_free_size(MALLOC_CAP_SPIRAM)));
  // Conservative failure gates, not a claim of measured VA/TTS reserve.
  if (before<98304 || heap_caps_get_largest_free_block(MALLOC_CAP_INTERNAL|MALLOC_CAP_8BIT)<65536 || heap_caps_get_free_size(MALLOC_CAP_SPIRAM)<1048576) goto cleanup;
  if (self->stop_requested_.load()) goto cleanup;
  models=srmodel_load(self->blob_);
  if (!models || models->num!=1 || std::string(models->model_name[0])!="wn9_alexa") goto cleanup;
  iface=esp_wn_handle_from_name(models->model_name[0]);if (!iface) goto cleanup;
  model=iface->create(models->model_name[0],DET_MODE_90);if (!model) goto cleanup;
  {
    const int samples=iface->get_samp_chunksize(model),rate=iface->get_samp_rate(model),channels=iface->get_channel_num(model);
    ESP_LOGI(TAG,"Model loaded rate=%d channels=%d samples=%d internal_free=%u psram_free=%u",rate,channels,samples,unsigned(heap_caps_get_free_size(MALLOC_CAP_INTERNAL|MALLOC_CAP_8BIT)),unsigned(heap_caps_get_free_size(MALLOC_CAP_SPIRAM)));
    if (rate!=16000 || channels!=1 || samples<=0 || samples>2048 || heap_caps_get_free_size(MALLOC_CAP_INTERNAL|MALLOC_CAP_8BIT)<65536 || heap_caps_get_largest_free_block(MALLOC_CAP_INTERNAL|MALLOC_CAP_8BIT)<32768) goto cleanup;
    frame=static_cast<int16_t *>(heap_caps_malloc(samples*sizeof(int16_t),MALLOC_CAP_SPIRAM|MALLOC_CAP_8BIT));if (!frame) goto cleanup;
    self->ready_=true;
    while (!self->stop_requested_.load()) {
      const size_t bytes=samples*sizeof(int16_t);
      if (self->ring_->available()<bytes) {vTaskDelay(pdMS_TO_TICKS(2));continue;}
      if (self->ring_->read(reinterpret_cast<void *>(frame),bytes,0)!=bytes) {self->drops_++;continue;}
      const int64_t begin=esp_timer_get_time();const int result=iface->detect(model,frame);const uint32_t elapsed=esp_timer_get_time()-begin;
      self->inference_total_us_+=elapsed;uint32_t max=self->inference_max_us_.load();if(elapsed>max)self->inference_max_us_=elapsed;self->inferences_++;
      if (result>0) {self->detected_=true;self->stop_requested_=true;break;}
      if (result<0 && result!=WAKENET_CHANNEL_VERIFIED) {self->failed_=true;break;}
    }
  }
cleanup:
  self->accepting_=false;
  if (!self->ready_.load() && !self->cancelled_.load()) {self->failed_=true;ESP_LOGW(TAG,"WakeNet start failed; no inference/audio ownership claimed");}
  if (frame) heap_caps_free(frame);
  if (model && iface) iface->destroy(model);
  if (models) esp_srmodel_deinit(models);
  self->done_=true;vTaskSuspend(nullptr);
}
void WakeNet::dump_config() {
  ESP_LOGCONFIG(TAG,"WakeNet9-family Alexa; embedded=%u bytes; active=%s enabled=%s audio_bytes=%u inference=%u drops=%u total_us(mod32)=%u max_us=%u",unsigned(blob_size_),YESNO(is_detecting_wake_word()),YESNO(enabled_),unsigned(audio_bytes_.load()),unsigned(inferences_.load()),unsigned(drops_.load()),unsigned(inference_total_us_.load()),unsigned(inference_max_us_.load()));
}
}
