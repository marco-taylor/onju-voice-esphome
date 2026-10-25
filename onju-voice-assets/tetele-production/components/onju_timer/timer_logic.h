#pragma once
#include <algorithm>
#include <cstdint>

namespace esphome::onju_timer {
// Earliest active timer; paused/invalid/expired entries do not drive the bar.
// Native ESPHome owns IDs, updates and expiry; no parallel timer counter.
struct Countdown {
  bool available{false};
  float fraction{0.0f};
};
template<typename Timers> Countdown countdown_for(const Timers &timers) {
  const typename Timers::value_type *selected = nullptr;
  for (const auto &timer : timers) {
    if (!timer.is_active || timer.total_seconds == 0 || timer.seconds_left == 0)
      continue;
    if (selected == nullptr || timer.seconds_left < selected->seconds_left ||
        (timer.seconds_left == selected->seconds_left && timer.id < selected->id))
      selected = &timer;
  }
  if (selected == nullptr)
    return {};
  return {true, std::min(1.0f, float(selected->seconds_left) / float(selected->total_seconds))};
}
}  // namespace esphome::onju_timer
