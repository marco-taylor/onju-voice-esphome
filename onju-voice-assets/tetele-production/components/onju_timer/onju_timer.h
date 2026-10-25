#pragma once
#include <functional>
#include <string>
#include <vector>
#include "esphome/core/automation.h"
#include "esphome/core/component.h"
#include "esphome/components/voice_assistant/voice_assistant.h"
#include "esphome/components/adf_pipeline/media_player/adf_media_player.h"
#include "esphome/components/light/light_state.h"
#include "timer_logic.h"

namespace esphome::onju_timer {
class TimerManager : public Component {
 public:
  void set_voice_assistant(voice_assistant::VoiceAssistant *value) { this->va_ = value; }
  void set_media_player(esp_adf::ADFMediaPlayer *value) { this->player_ = value; }
  void set_light(light::LightState *value) { this->light_ = value; }
  void set_playback_allowed(std::function<bool()> value) { this->playback_allowed_ = std::move(value); }
  Trigger<> *get_refresh_trigger() { return &this->refresh_trigger_; }
  Trigger<> *get_recover_trigger() { return &this->recover_trigger_; }
  void setup() override;
  void loop() override;
  void dump_config() override;
  void timers_changed() { this->timers_dirty_ = true; }
  void finished(const voice_assistant::Timer &timer);
  void cancelled(const voice_assistant::Timer &timer);
  void dismiss(bool recover = true, bool stop_owned = true);
  void voice_started();
  void set_assist_phase(uint8_t value) { this->assist_phase_ = value; }
  void set_display_enabled(bool value) { this->display_enabled_ = value; }
  void set_volume_feedback(bool value) { this->volume_feedback_ = value; }
  bool alarm_active() const { return !this->ringing_ids_.empty(); }
  float countdown_fraction() const { return this->countdown_.fraction; }
  bool apply_led_priority(bool notification);

 protected:
  enum class Playback : uint8_t { WAIT_IDLE, REQUESTED, PLAYING, GAP };
  void on_control_(const media_player::MediaPlayerCall &call);
  void stop_owned_();
  void show_effect_(const char *effect, float red, float green, float blue, float brightness);
  voice_assistant::VoiceAssistant *va_{nullptr};
  esp_adf::ADFMediaPlayer *player_{nullptr};
  light::LightState *light_{nullptr};
  std::function<bool()> playback_allowed_;
  Trigger<> refresh_trigger_;
  Trigger<> recover_trigger_;
  std::vector<std::string> ringing_ids_;
  Countdown countdown_;
  Playback playback_{Playback::WAIT_IDLE};
  uint32_t last_poll_{0}, stage_since_{0}, idle_since_{0};
  uint32_t alarm_since_{0}, recovery_since_{0};
  uint16_t led_signature_{0xFFFF};
  uint8_t assist_phase_{0};
  bool display_enabled_{true}, volume_feedback_{false}, timers_dirty_{true};
  bool led_engaged_{false};
  bool own_call_{false}, owns_audio_{false}, recover_pending_{false};
};
}  // namespace esphome::onju_timer
