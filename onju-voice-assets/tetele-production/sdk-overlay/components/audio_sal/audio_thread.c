/*
 * ESPRESSIF MIT License
 *
 * Copyright (c) 2020 <ESPRESSIF SYSTEMS (SHANGHAI) CO., LTD>
 *
 * Permission is hereby granted for use on all ESPRESSIF SYSTEMS products, in which case,
 * it is free of charge, to any person obtaining a copy of this software and associated
 * documentation files (the "Software"), to deal in the Software without restriction, including
 * without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
 * and/or sell copies of the Software, and to permit persons to whom the Software is furnished
 * to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all copies or
 * substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
 * FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
 * COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
 * IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
 * CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 *
 */

#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "freertos/task.h"

#include "esp_log.h"
#include "audio_mem.h"
#include "audio_error.h"
#include "audio_thread.h"
#include "freertos/idf_additions.h"
#include "esp_heap_caps.h"

static const char *TAG = "AUDIO_THREAD";

/* ESP-IDF 5.x supplies the capability-aware task API. Keep external stacks
 * external without applying the old ADF patch to the shared FreeRTOS kernel. */
esp_err_t audio_thread_create(audio_thread_t *p_handle, const char *name, void(*main_func)(void *arg), void *arg,
                              uint32_t stack, int prio, bool stack_in_ext, int core_id)
{
    BaseType_t result;
    if (stack_in_ext && audio_mem_spiram_stack_is_enabled()) {
        result = xTaskCreatePinnedToCoreWithCaps(main_func, name, stack, arg, prio,
                                               (TaskHandle_t *)p_handle, core_id,
                                               MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
    } else {
        result = xTaskCreatePinnedToCore(main_func, name, stack, arg, prio,
                                        (TaskHandle_t *)p_handle, core_id);
    }
    return result == pdPASS ? ESP_OK : ESP_FAIL;
}

esp_err_t audio_thread_cleanup(audio_thread_t *p_handle)
{
    // TODO nothing
    return ESP_OK;
}

esp_err_t audio_thread_delete_task(audio_thread_t *p_handle)
{
    /* WithCaps stacks/TCBs are static allocations owned by the IDF helper.
     * Match their creation with its deletion API; preserve ordinary deletion
     * for ADF tasks created with the normal internal-memory API. */
    StackType_t *stack;
    StaticTask_t *tcb;
    if (xTaskGetStaticBuffers(xTaskGetCurrentTaskHandle(), &stack, &tcb) == pdTRUE) {
        vTaskDeleteWithCaps(NULL);
    } else {
        vTaskDelete(NULL);
    }
    return ESP_OK; /* Control never reach here if this is self delete */
}
