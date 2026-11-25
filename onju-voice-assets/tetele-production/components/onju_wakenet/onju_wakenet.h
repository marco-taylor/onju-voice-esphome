#pragma once
#include "esphome/core/component.h"
#include "esphome/core/automation.h"
#include "esphome/core/preferences.h"
#include "esphome/core/static_task.h"
#include "esphome/components/ota/ota_backend.h"
#include "esphome/components/microphone/microphone_source.h"
#include "esphome/components/ring_buffer/ring_buffer.h"
#include <atomic>
#include <functional>
namespace esphome::onju_wakenet {
class WakeNet final : public Component, public ota::OTAGlobalStateListener {
 public:
  inline static constexpr const char *WORD_IDS[2]={"alexa","hallo_esp"};
  inline static constexpr const char *PHRASES[2]={"Alexa","Hallo ESP"};
  // Diagnostic-only bounded boot history; no lifecycle decisions use these fields.
  void diag(const char *event, intptr_t native=0, bool heap=false);
  int diag_result(const char *event,int value){diag(event,value);return value;}
  void dump_diag();
  bool diag_ready()const{return ready_.load();}
  void setup() override;void loop() override;void dump_config() override;
  void on_ota_global_state(ota::OTAState,float,uint8_t,ota::OTAComponent *) override;
  float get_setup_priority() const override { return setup_priority::AFTER_WIFI; }
  void set_model_blob(const uint8_t *data,size_t size){blob_=data;blob_size_=size;}
  void set_microphone_source(microphone::MicrophoneSource *p){source_=p;}
  void set_can_listen(std::function<bool()> fn){can_listen_=std::move(fn);}
  void set_on_enabled(std::function<void()> fn){on_enabled_=std::move(fn);}
  void set_active_words(const std::vector<std::string> &words);
  void set_enabled(bool enabled){set_active_words(enabled?std::vector<std::string>{"alexa"}:std::vector<std::string>{});}
  bool word_enabled(size_t index)const{return index<2 && (active_mask_.load()&(1U<<index));}
  bool is_enabled()const{return active_mask_.load()!=0;}
  void start();void stop();
  bool is_running()const{return state_!=STOPPED;}
  bool is_detecting_wake_word()const{return state_==LISTENING && accepting_.load();}
  uint32_t get_received_audio_bytes()const{return audio_bytes_.load();}
  uint32_t get_successful_inferences()const{return inferences_.load();}
  Trigger<std::string> *get_wake_word_detected_trigger(){return &detected_trigger_;}
 protected:
  struct DiagEvent { const char *event; uint32_t ms; intptr_t native; uint32_t free,min,largest,psram; bool ready; std::atomic<bool> published{false}; };
  DiagEvent diag_events_[64]{};
  std::atomic<uint32_t> diag_count_{0};
  std::atomic<bool> diag_mic_running_{false},diag_operational_{false};
  static void worker(void *arg);static void feeder(void *arg);
  enum State{STOPPED,STARTING,LISTENING,STOPPING}state_{STOPPED};
  const uint8_t *blob_{nullptr};size_t blob_size_{0};
  microphone::MicrophoneSource *source_{nullptr};
  std::function<bool()> can_listen_;std::function<void()> on_enabled_;
  std::shared_ptr<ring_buffer::RingBuffer> ring_;StaticTask task_,feed_task_;
  ESPPreferenceObject preference_;std::atomic<uint8_t> active_mask_{1};
  std::atomic<bool> ota_blocked_{false},stop_requested_{false},cancelled_{false},ready_{false},done_{false},accepting_{false},failed_{false},feed_done_{false};
  std::atomic<uint32_t> audio_bytes_{0},inferences_{0},drops_{0},feeds_{0},detections_{0},inference_total_us_{0},inference_max_us_{0};
  std::atomic<int> detected_id_{0};
  // Only published before feeder creation, and cleared after its task is joined.
  const void *afe_iface_{nullptr};void *afe_data_{nullptr};int feed_samples_{0};
  Trigger<std::string> detected_trigger_;
};
template<typename... Ts>class StartAction:public Action<Ts...>{public:explicit StartAction(WakeNet*p):parent_(p){}void play(const Ts &...x)override{parent_->start();}protected:WakeNet*parent_;};
template<typename... Ts>class StopAction:public Action<Ts...>{public:explicit StopAction(WakeNet*p):parent_(p){}void play(const Ts &...x)override{parent_->stop();}protected:WakeNet*parent_;};
}
