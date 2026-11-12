#pragma once
#include "esphome/core/component.h"
#include "esphome/core/log.h"
#include "esphome/components/micro_wake_word/micro_wake_word.h"
#include "esphome/components/adf_pipeline/microphone/esp_adf_microphone.h"
#include "esphome/components/voice_assistant/voice_assistant.h"
#include "esphome/components/switch/switch.h"
#include "esphome/components/binary_sensor/binary_sensor.h"

namespace esphome::onju_startup {
class WakeWordStartup : public Component {
 public:
  void set_mww(micro_wake_word::MicroWakeWord *p) { this->mww_ = p; }
  void set_microphone(esp_adf::ADFMicrophone *p) { this->mic_ = p; }
  void set_voice_assistant(voice_assistant::VoiceAssistant *p) { this->va_ = p; }
  void set_use_wake_word(switch_::Switch *p) { this->use_ = p; }
  void set_hardware_mute(binary_sensor::BinarySensor *p) { this->mute_ = p; }
  void set_handover_idle(std::function<bool()> fn) { this->handover_idle_ = std::move(fn); }
  float get_setup_priority() const override { return setup_priority::LATE - 10; }
  void setup() override { this->armed_ = false; this->request_start("boot"); }
  void request_start(const char *reason) {
    // Called before TemplateSwitch optimistic publish as well: evaluate only later, in loop().
    if (this->armed_) return;
    this->armed_ = true;
    this->attempts_ = 0;
    this->phase_ = WAITING;
    this->since_ = this->began_ = millis();
    this->enable_loop();
    ESP_LOGI("onju.startup", "Local listening request: %s", reason);
  }
  void cancel_start() {
    // OFF/mute can arrive between start() and the first MWW loop iteration.
    if (this->armed_ && this->phase_ == OBSERVING && !this->mww_->is_running()) this->mww_->stop();
    this->armed_ = false;
    this->disable_loop();
  }
  void loop() override {
    if (!this->armed_) return;
    if (!this->use_->state || this->mute_->state || this->mic_->get_mute_state()) {
      ESP_LOGI("onju.startup", "Listening suppressed: use=%s hardware_mute=%s microphone_muted=%s",
               YESNO(this->use_->state), YESNO(this->mute_->state), YESNO(this->mic_->get_mute_state()));
      this->cancel_start();
      return;
    }
    const uint32_t now = millis();
    if (now - this->began_ > 45000) { this->fail_("Startup deadline reached"); return; }
    // Never interfere with the known-good VA handover/recovery path.
    if (this->va_->is_running() || !this->handover_idle_()) {
      this->phase_ = WAITING;
      return;
    }
    if (this->phase_ == RELEASING) {
      if (!this->mww_->is_running() && this->mic_->is_stopped()) this->phase_ = WAITING;
      else if (now - this->since_ > 10000) this->fail_("Microphone release timed out");
      return;
    }
    if (this->phase_ == WAITING) {
      if (!this->mww_->is_ready() || !this->mic_->is_ready() || !this->va_->is_ready()) return;
      if (!this->mww_->is_running() && !this->mic_->is_stopped()) return;
      if (this->attempts_ >= 2) { this->fail_("Listening did not become healthy after two attempts"); return; }
      ++this->attempts_;
      this->audio_ = this->mww_->get_received_audio_bytes();
      this->inferences_ = this->mww_->get_successful_inferences();
      this->since_ = now;
      this->phase_ = OBSERVING;
      if (!this->mww_->is_running()) this->mww_->start();  // MWW owns microphone startup.
      ESP_LOGI("onju.startup", "Listening check attempt %u/2", this->attempts_);
      return;
    }
    if (this->mww_->is_detecting_wake_word() && this->mic_->is_running() &&
        this->mww_->get_received_audio_bytes() != this->audio_ &&
        this->mww_->get_successful_inferences() != this->inferences_) {
      ESP_LOGI("onju.startup", "Listening healthy: MWW=DETECTING_WAKE_WORD microphone=RUNNING audio_bytes=%u wakeword_inferences=%u",
               unsigned(this->mww_->get_received_audio_bytes()), unsigned(this->mww_->get_successful_inferences()));
      this->cancel_start();
    } else if (now - this->since_ > 15000) {
      ESP_LOGW("onju.startup", "Listening check timed out; bounded MWW stop/retry");
      this->mww_->stop();
      this->phase_ = RELEASING;
      this->since_ = now;
    }
  }
  void dump_config() override {
    ESP_LOGCONFIG("onju.startup", "Use Wake Word=%s; hardware mute=%s; microphone muted=%s; MWW detecting=%s; microphone running=%s; audio_bytes=%u; wakeword_inferences=%u",
      YESNO(this->use_->state), YESNO(this->mute_->state), YESNO(this->mic_->get_mute_state()),
      YESNO(this->mww_->is_detecting_wake_word()), YESNO(this->mic_->is_running()),
      unsigned(this->mww_->get_received_audio_bytes()), unsigned(this->mww_->get_successful_inferences()));
  }
 protected:
  void fail_(const char *message) { ESP_LOGW("onju.startup", "%s; no further automatic attempts", message); this->cancel_start(); }
  enum Phase { WAITING, OBSERVING, RELEASING } phase_{WAITING};
  micro_wake_word::MicroWakeWord *mww_;
  esp_adf::ADFMicrophone *mic_;
  voice_assistant::VoiceAssistant *va_;
  switch_::Switch *use_;
  binary_sensor::BinarySensor *mute_;
  std::function<bool()> handover_idle_;
  bool armed_{false};
  uint8_t attempts_{0};
  uint32_t since_{0}, began_{0}, audio_{0}, inferences_{0};
};
}  // namespace esphome::onju_startup
