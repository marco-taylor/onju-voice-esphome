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
  void setup() override;
  void loop() override;
  void dump_config() override;
  void on_ota_global_state(ota::OTAState state, float progress, uint8_t error, ota::OTAComponent *comp) override;
  float get_setup_priority() const override { return setup_priority::AFTER_WIFI; }
  void set_model_blob(const uint8_t *data, size_t size) { blob_=data; blob_size_=size; }
  void set_microphone_source(microphone::MicrophoneSource *p) { source_=p; }
  void set_can_listen(std::function<bool()> fn) { can_listen_=std::move(fn); }
  void set_on_enabled(std::function<void()> fn) { on_enabled_=std::move(fn); }
  void set_enabled(bool enabled);
  bool is_enabled() const { return enabled_; }
  void start();
  void stop();
  bool is_running() const { return state_!=STOPPED; }
  bool is_detecting_wake_word() const { return state_==LISTENING && accepting_.load(); }
  uint32_t get_received_audio_bytes() const { return audio_bytes_.load(); }
  uint32_t get_successful_inferences() const { return inferences_.load(); }
  Trigger<std::string> *get_wake_word_detected_trigger() { return &detected_trigger_; }
 protected:
  static void worker(void *arg);
  enum State {STOPPED,STARTING,LISTENING,STOPPING} state_{STOPPED};
  const uint8_t *blob_{nullptr}; size_t blob_size_{0};
  microphone::MicrophoneSource *source_{nullptr};
  std::function<bool()> can_listen_;
  std::function<void()> on_enabled_;
  std::shared_ptr<ring_buffer::RingBuffer> ring_;
  StaticTask task_;
  ESPPreferenceObject preference_;
  bool enabled_{true};
  std::atomic<bool> ota_blocked_{false};
  std::atomic<bool> stop_requested_{false},cancelled_{false},ready_{false},done_{false},detected_{false},accepting_{false},failed_{false};
  std::atomic<uint32_t> audio_bytes_{0},inferences_{0},drops_{0},inference_total_us_{0},inference_max_us_{0};
  Trigger<std::string> detected_trigger_;
};
template<typename... Ts> class StartAction : public Action<Ts...> { public: explicit StartAction(WakeNet *p):parent_(p){} void play(const Ts &...x) override {parent_->start();} protected: WakeNet *parent_; };
template<typename... Ts> class StopAction : public Action<Ts...> { public: explicit StopAction(WakeNet *p):parent_(p){} void play(const Ts &...x) override {parent_->stop();} protected: WakeNet *parent_; };
}
