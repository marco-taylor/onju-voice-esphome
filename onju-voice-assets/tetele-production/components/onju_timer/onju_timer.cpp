#include "onju_timer.h"
#include "esphome/core/hal.h"
#include "esphome/core/log.h"

namespace esphome::onju_timer {
static const char *const TAG = "onju.timer";
static constexpr const char *ALARM_URI = "flash://onju-timer.mp3";
static constexpr uint32_t ALARM_TIMEOUT_MS = 15 * 60 * 1000;
static constexpr uint32_t PLAYER_IDLE_TIMEOUT_MS = 10 * 1000;

void TimerManager::setup() {
  this->player_->add_on_control_callback([this](const media_player::MediaPlayerCall &call) { this->on_control_(call); });
}
void TimerManager::dump_config() {
  ESP_LOGCONFIG(TAG, "Native VA timers; local MP3 alarm; physical validation pending");
}
void TimerManager::finished(const voice_assistant::Timer &timer) {
  const bool was_active = this->alarm_active();
  if (std::find(this->ringing_ids_.begin(), this->ringing_ids_.end(), timer.id) == this->ringing_ids_.end())
    this->ringing_ids_.push_back(timer.id);
  if (!was_active) {
    // One deadline for this ringing session; another expired timer cannot extend it.
    this->alarm_since_ = millis();
    this->playback_ = Playback::WAIT_IDLE;
    this->idle_since_ = 0;
    ESP_LOGI(TAG, "Timer alarm pending; waiting for idle VA/player");
  }
  this->timers_dirty_ = true;
}
void TimerManager::cancelled(const voice_assistant::Timer &timer) {
  auto found = std::find(this->ringing_ids_.begin(), this->ringing_ids_.end(), timer.id);
  if (found != this->ringing_ids_.end()) {
    if (this->ringing_ids_.size() == 1)
      this->dismiss();
    else
      this->ringing_ids_.erase(found);
  }
  this->timers_dirty_ = true;
}
void TimerManager::stop_owned_() {
  if (!this->owns_audio_)
    return;
  this->own_call_ = true;
  this->player_->make_call().set_command(media_player::MEDIA_PLAYER_COMMAND_STOP).perform();
  this->own_call_ = false;
  this->owns_audio_ = false;
}
void TimerManager::dismiss(bool recover, bool stop_owned) {
  if (!this->alarm_active())
    return;
  this->ringing_ids_.clear();  // Stops future repeats before touching playback/callbacks.
  this->alarm_since_ = 0;
  if (stop_owned)
    this->stop_owned_();
  else
    this->owns_audio_ = false;  // The caller's external STOP/PAUSE follows this callback.
  this->playback_ = Playback::WAIT_IDLE;
  this->idle_since_ = 0;
  this->recover_pending_ = recover;
  this->recovery_since_ = millis();
  ESP_LOGI(TAG, "Timer alarm dismissed");
  this->refresh_trigger_.trigger();
}
void TimerManager::voice_started() {
  // Existing MWW handover / manual VA start owns microphone recovery from here.
  this->dismiss(false);
  this->assist_phase_ = 0;
}
void TimerManager::on_control_(const media_player::MediaPlayerCall &call) {
  if (this->own_call_ || !this->alarm_active())
    return;
  if (call.get_media_url().has_value()) {
    // A new VA confirmation/TTS/media URL supersedes the alarm. Never stop it later.
    this->dismiss(false);
    return;
  }
  if (call.get_command().has_value()) {
    const auto command = *call.get_command();
    if (command == media_player::MEDIA_PLAYER_COMMAND_STOP)
      this->dismiss(true, false);  // Includes STOP during the silent repeat gap.
    else if (command == media_player::MEDIA_PLAYER_COMMAND_PAUSE)
      this->dismiss(true);  // Release alarm playback rather than leave it paused.
  }
}
void TimerManager::show_effect_(const char *effect, float red, float green, float blue, float brightness) {
  if (this->light_->remote_values.is_on() && this->light_->get_effect_name() == effect)
    return;
  auto call = this->light_->turn_on();
  call.set_transition_length(0);
  call.set_rgb(red, green, blue);
  call.set_brightness(brightness);
  call.set_effect(effect);
  call.perform();
}
bool TimerManager::apply_led_priority(bool notification) {
  if (this->volume_feedback_)
    return true;
  if (this->va_->is_running()) {
    switch (this->assist_phase_) {
      case 1: this->show_effect_("listening", 1, 1, 1, 1); break;
      case 2: this->show_effect_("processing", 0, 0.2f, 1, 0.7f); break;
      case 3: this->show_effect_("speaking", 0.2f, 1, 0, 1); break;
      default: break;
    }
    return true;
  }
  if (this->alarm_active()) {
    this->show_effect_("timer_alarm", 1, 0, 0, 1);
    return true;
  }
  // Preserve existing media/notification visuals; countdown is an idle overlay.
  if (this->player_->state != media_player::MEDIA_PLAYER_STATE_IDLE || notification)
    return false;
  if (this->display_enabled_ && this->countdown_.available) {
    this->show_effect_("timer_countdown", 1, 0.55f, 0, 0.7f);
    return true;
  }
  return false;
}
void TimerManager::loop() {
  const uint32_t now = millis();
  if (now - this->last_poll_ < 50)
    return;
  this->last_poll_ = now;
  if (this->alarm_active() && now - this->alarm_since_ >= ALARM_TIMEOUT_MS) {
    ESP_LOGW(TAG, "Timer alarm reached 15-minute safety timeout; dismissing");
    this->dismiss();
  }
  // Native event triggers run BEFORE CANCELLED/FINISHED erasure. Read only here,
  // after on_timer_event returned, not in the event's automation itself.
  if (this->timers_dirty_) {
    this->countdown_ = countdown_for(this->va_->get_timers());
    this->timers_dirty_ = false;
  }
  const bool voice = this->va_->is_running();
  const bool idle = this->player_->state == media_player::MEDIA_PLAYER_STATE_IDLE;
  if (!voice)
    this->assist_phase_ = 0;
  // Dismiss callbacks may advance the clock after this loop's initial sample.
  if (this->recover_pending_ && (idle || millis() - this->recovery_since_ >= PLAYER_IDLE_TIMEOUT_MS)) {
    this->recover_pending_ = false;
    if (!idle) {
      ESP_LOGW(TAG, "Timer cleanup: player not IDLE after 10 seconds; continuing existing recovery");
      this->refresh_trigger_.trigger();
    }
    if (!voice)
      this->recover_trigger_.trigger();
  }
  const uint16_t signature = (this->volume_feedback_ ? 1 : 0) | (voice ? 2 : 0) |
      (this->alarm_active() ? 4 : 0) | (!idle ? 8 : 0) |
      (this->countdown_.available && this->display_enabled_ ? 16 : 0) | (this->assist_phase_ << 5);
  const bool engage_led = this->alarm_active() || this->countdown_.available ||
      this->volume_feedback_ || this->assist_phase_ != 0;
  if (signature != this->led_signature_) {
    this->led_signature_ = signature;
    if (engage_led || this->led_engaged_)
      this->refresh_trigger_.trigger();
  }
  this->led_engaged_ = engage_led;
  if (!this->alarm_active())
    return;
  switch (this->playback_) {
    case Playback::WAIT_IDLE:
      if (voice || !idle || !this->playback_allowed_()) {
        this->idle_since_ = 0;
        break;
      }
      if (this->idle_since_ == 0)
        this->idle_since_ = now;
      if (now - this->idle_since_ < 1000)
        break;
      this->playback_ = Playback::REQUESTED;
      this->stage_since_ = now;
      this->owns_audio_ = true;
      this->own_call_ = true;
      this->player_->make_call().set_media_url(ALARM_URI).perform();
      this->own_call_ = false;
      break;
    case Playback::REQUESTED:
      if (!idle) {
        this->playback_ = Playback::PLAYING;
        this->stage_since_ = now;
      } else if (now - this->stage_since_ > 5000) {
        this->stop_owned_();
        this->playback_ = Playback::GAP;
        this->stage_since_ = now;
      }
      break;
    case Playback::PLAYING:
      if (idle || now - this->stage_since_ > 15000) {
        if (!idle)
          this->stop_owned_();
        this->playback_ = Playback::GAP;
        this->stage_since_ = now;
        // Keep ownership of a completed alarm URI until dismissed/replaced;
        // STOP must also clear the player's saved URI after natural EOF.
      }
      break;
    case Playback::GAP:
      if (now - this->stage_since_ >= 1500) {
        this->playback_ = Playback::WAIT_IDLE;
        this->idle_since_ = 0;
      }
      break;
  }
}
}  // namespace esphome::onju_timer
