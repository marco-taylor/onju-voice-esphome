#pragma once
#include "esphome/core/component.h"
#include "esphome/core/log.h"
#include "esphome/components/ota/ota_backend.h"
#include <esp_heap_caps.h>
#include "esphome/components/onju_identity/onju_identity.h"
namespace esphome::onju_update_metrics {
class MemoryMetrics : public Component, public ota::OTAGlobalStateListener {
 public:
  float get_setup_priority() const override { return setup_priority::BUS + 1; }
  void dump_config() override {
    onju_identity::Profile check{};
    wifi::SavedWifiSettings credentials{};
    auto identity = global_preferences->make_preference<onju_identity::Profile>(onju_identity::PROFILE_KEY, true);
    auto station = global_preferences->make_preference<wifi::SavedWifiSettings>(onju_identity::WIFI_KEY, true);
    bool confirmed = onju_identity::loaded && onju_identity::persisted && identity.load(&check) &&
      onju_identity::valid(check, get_mac_address_pretty().c_str()) &&
      memcmp(&check, &onju_identity::profile, sizeof(check)) == 0 && station.load(&credentials) && credentials.ssid[0];
    ESP_LOGCONFIG("onju.identity", "Migration profile/native Wi-Fi readback confirmed=%s; loaded=%s; persisted=%s", YESNO(confirmed), YESNO(onju_identity::loaded), YESNO(onju_identity::persisted));
  }
  void setup() override {
    ota::get_global_ota_callback()->add_global_state_listener(this);
    this->begin("boot-and-initial-manifest");
    this->set_timeout(170000,[this]{this->end();});
  }
  void begin(const char *phase) {
    if(active_)this->end();
    phase_=phase;
    before_=heap_caps_get_free_size(MALLOC_CAP_INTERNAL|MALLOC_CAP_8BIT);
    active_=heap_caps_monitor_local_minimum_free_size_start()==ESP_OK;
    ESP_LOGI("onju.memory","BEGIN %s internal_free=%u largest_internal=%u psram_free=%u monitor=%s",phase_,unsigned(before_),unsigned(heap_caps_get_largest_free_block(MALLOC_CAP_INTERNAL|MALLOC_CAP_8BIT)),unsigned(heap_caps_get_free_size(MALLOC_CAP_SPIRAM)),YESNO(active_));
  }
  void end() {
    if(!active_)return;
    ESP_LOGI("onju.memory","END %s internal_before=%u internal_min=%u internal_now=%u largest_internal_now=%u psram_min=%u psram_now=%u",phase_,unsigned(before_),unsigned(heap_caps_get_minimum_free_size(MALLOC_CAP_INTERNAL|MALLOC_CAP_8BIT)),unsigned(heap_caps_get_free_size(MALLOC_CAP_INTERNAL|MALLOC_CAP_8BIT)),unsigned(heap_caps_get_largest_free_block(MALLOC_CAP_INTERNAL|MALLOC_CAP_8BIT)),unsigned(heap_caps_get_minimum_free_size(MALLOC_CAP_SPIRAM)),unsigned(heap_caps_get_free_size(MALLOC_CAP_SPIRAM)));
    heap_caps_monitor_local_minimum_free_size_stop();active_=false;
  }
  void on_ota_global_state(ota::OTAState state,float progress,uint8_t error,ota::OTAComponent *) override {
    if(state==ota::OTA_STARTED)this->begin("OTA-TLS-download-flash");
    if(state==ota::OTA_COMPLETED||state==ota::OTA_ERROR)this->end();
  }
 protected:
  bool active_{false}; uint32_t before_{0}; const char *phase_{"inactive"};
};
}
