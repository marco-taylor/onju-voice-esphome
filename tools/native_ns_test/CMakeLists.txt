cmake_minimum_required(VERSION 3.16)
set(EXTRA_COMPONENT_DIRS "${CMAKE_CURRENT_LIST_DIR}/../../onju-voice-assets/tetele-production/sdk/esp-sr-wakenet/esp-sr")
include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(onju_native_model_test)
