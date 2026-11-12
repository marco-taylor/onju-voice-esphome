#pragma once
#include "esphome/core/application.h"
#include "esphome/core/preferences.h"
#include "esphome/core/helpers.h"
#include "esphome/core/log.h"
#include "esphome/components/wifi/wifi_component.h"
#include <cstring>
#include <cstdio>

namespace esphome::onju_identity {
// Inputs exist only in the private, one-time migration package, never in shared images.
struct Seed { const char *mac, *name, *friendly, *ssid, *password, *ip, *gateway, *subnet, *dns1, *dns2; };
struct Profile {
  uint32_t magic;
  char mac[18], name[64], friendly[96];
  uint8_t network[5][4];
  bool static_ip;
};
inline Profile profile{};
inline bool loaded = false, persisted = false;
inline char default_name[64], default_friendly[96];
constexpr uint32_t PROFILE_KEY = 0x4F4E4A31;  // ONJ1; independent of name/config hash
constexpr uint32_t WIFI_KEY = 88491487UL;     // Native no-compiled-stations / Improv key

template<size_t N> bool copy_text(char (&out)[N], const char *in) {
  const size_t len = strlen(in);
  if (len >= N) return false;
  memcpy(out, in, len + 1);
  return true;
}
inline bool valid(const Profile &p, const char *mac) {
  return p.magic == PROFILE_KEY && memchr(p.mac, 0, sizeof(p.mac)) && strcmp(p.mac, mac) == 0 &&
    memchr(p.name, 0, sizeof(p.name)) && p.name[0] && memchr(p.friendly, 0, sizeof(p.friendly)) && p.friendly[0];
}
inline bool ipv4(uint8_t (&out)[4], const char *s) {
  unsigned a,b,c,d; char tail;
  if (sscanf(s, "%u.%u.%u.%u%c", &a,&b,&c,&d,&tail) != 4 || a>255 || b>255 || c>255 || d>255) return false;
  out[0]=a;out[1]=b;out[2]=c;out[3]=d;return true;
}
inline void pre_setup(const char *name, size_t name_len, const char *friendly, size_t friendly_len, const Seed *seed) {
  const auto mac = get_mac_address_pretty();
  auto pref = global_preferences->make_preference<Profile>(PROFILE_KEY, true);
  loaded = pref.load(&profile) && valid(profile, mac.c_str());
  persisted = loaded;
  if (!loaded && seed != nullptr) {
    Profile candidate{};candidate.magic=PROFILE_KEY;candidate.static_ip=true;
    wifi::SavedWifiSettings credentials{};
    bool okay = strcmp(seed->mac, mac.c_str())==0 && copy_text(candidate.mac, seed->mac) &&
      copy_text(candidate.name, seed->name) && copy_text(candidate.friendly, seed->friendly) &&
      copy_text(credentials.ssid, seed->ssid) && credentials.ssid[0] && copy_text(credentials.password, seed->password);
    const char *addresses[] = {seed->ip,seed->gateway,seed->subnet,seed->dns1,seed->dns2};
    for (size_t i=0;i<5;i++) okay = ipv4(candidate.network[i],addresses[i]) && okay;
    if (okay) {
      auto wifi_pref = global_preferences->make_preference<wifi::SavedWifiSettings>(WIFI_KEY,true);
      bool saved = wifi_pref.save(&credentials) && pref.save(&candidate) && global_preferences->sync();
      Profile check{}; wifi::SavedWifiSettings wifi_check{};
      persisted = saved && pref.load(&check) && valid(check,mac.c_str()) && memcmp(&check,&candidate,sizeof(candidate))==0 && wifi_pref.load(&wifi_check) &&
        memcmp(&wifi_check,&credentials,sizeof(credentials))==0;
      // Preserve connectivity even on a reported sync failure; the controller must
      // refuse the next managed install unless the persisted readback is confirmed.
      profile = candidate;loaded = true;
      if (persisted) ESP_LOGI("onju.identity", "Migration profile and native Wi-Fi committed/read back; MAC bound; no NVS erase");
      else ESP_LOGE("onju.identity", "Migration persistence failed; do NOT perform a shared-image update");
    } else ESP_LOGE("onju.identity", "Invalid/mismatched migration seed; profile not written");
  }
  if (loaded) {
    App.pre_setup(profile.name,strlen(profile.name),profile.friendly,strlen(profile.friendly));
    ESP_LOGI("onju.identity", "Restored node identity before entity registration: %s; persisted=%s",profile.name,YESNO(persisted));
  } else {
    char compact[MAC_ADDRESS_BUFFER_SIZE];get_mac_address_into_buffer(compact);
    snprintf(default_name,sizeof(default_name),"%.*s-%s",int(name_len),name,compact+6);
    snprintf(default_friendly,sizeof(default_friendly),"%.*s %s",int(friendly_len),friendly,compact+6);
    App.pre_setup(default_name,strlen(default_name),default_friendly,strlen(default_friendly));
  }
}
inline void apply_network(wifi::WiFiAP &ap) {
  if (!loaded || !profile.static_ip) return;
  network::IPAddress ip[5];
  for(size_t i=0;i<5;i++)ip[i]=network::IPAddress(profile.network[i][0],profile.network[i][1],profile.network[i][2],profile.network[i][3]);
  ap.set_manual_ip(wifi::ManualIP{ip[0],ip[1],ip[2],ip[3],ip[4]});
}
}  // namespace esphome::onju_identity
