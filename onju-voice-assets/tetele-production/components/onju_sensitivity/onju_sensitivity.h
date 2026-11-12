#pragma once
#include "esphome/components/select/select.h"
#include "esphome/core/preferences.h"
#include "esphome/core/log.h"

namespace esphome::onju_sensitivity {
class SensitivitySelect : public select::Select, public Component {
 public:
  float get_setup_priority() const override { return setup_priority::HARDWARE; }
  void set_initial_index(uint8_t index) { this->initial_index_ = index; }
  void setup() override {
    // A different key AND storage size prevent legacy four-option size_t indices being reinterpreted.
    this->pref_ = this->make_entity_preference<uint8_t>(0x53454E31);
    uint8_t index = this->initial_index_;
    bool restored = this->pref_.load(&index) && this->has_index(index);
    if (!restored) index = this->initial_index_;
    this->publish_state(size_t(index));
    ESP_LOGI("onju.sensitivity", "%s: %s (schema 1)", restored ? "Restored" : "Initial", this->option_at(index));
    if (!restored) this->save_(index);
  }
  void dump_config() override {
    ESP_LOGCONFIG("onju.sensitivity", "Wake word sensitivity: %s; Restore Value: YES; preference schema: 1", this->current_option().c_str());
  }
 protected:
  void control(size_t index) override {
    if (!this->has_index(index) || (this->has_state() && this->active_index().value() == index)) return;
    this->publish_state(index);
    this->save_(uint8_t(index));
  }
  void save_(uint8_t index) {
    if (!this->pref_.save(&index)) {
      ESP_LOGW("onju.sensitivity", "Could not queue sensitivity preference");
      return;
    }
    // Only actual changes (and first migration) flush. The global 60 s policy is unchanged.
    if (global_preferences->sync()) {
      ESP_LOGI("onju.sensitivity", "Sensitivity persisted: %s", this->option_at(index));
    } else {
      ESP_LOGW("onju.sensitivity", "Sensitivity flush failed; normal preference sync will retry");
    }
  }
  ESPPreferenceObject pref_;
  uint8_t initial_index_{1};
};
}  // namespace esphome::onju_sensitivity
