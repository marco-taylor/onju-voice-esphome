#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_wn_models.h"
#include "esp_afe_sr_models.h"
#include "model_path.h"
extern const unsigned char onju_native_blob[];
void app_main(void) {
  srmodel_list_t *models=srmodel_load(onju_native_blob);
  assert(models && models->num==2);
  const char *names[]={"wn10_alexa","wn10_de_halloesp"};
  for(int i=0;i<2;i++) {
    assert(strcmp(models->model_name[i],names[i])==0);
    const esp_wn_iface_t *wn=esp_wn_handle_from_name(names[i]); assert(wn);
    model_iface_data_t *model=wn->create(names[i],DET_MODE_90);
    printf("NATIVE_INDIVIDUAL model=%s handle=%p\n",names[i],model);
    if(!model){printf("NATIVE_MODEL_CREATE_FAIL model=%s\n",names[i]);fflush(stdout);}
    assert(model);wn->destroy(model);
  }
  afe_config_t *cfg=afe_config_init("M",models,AFE_TYPE_SR,AFE_MODE_LOW_COST);assert(cfg);
  cfg->aec_init=false;cfg->se_init=false;cfg->ns_init=false;cfg->vad_init=false;cfg->agc_init=false;
  cfg->wakenet_init=true;cfg->wakenet_model_name=models->model_name[0];cfg->wakenet_model_name_2=models->model_name[1];
  cfg->wakenet_mode=DET_MODE_90;cfg->memory_alloc_mode=AFE_MEMORY_ALLOC_MORE_PSRAM;
  cfg->afe_linear_gain=1.0f;cfg->fixed_first_channel=true;cfg->fixed_output_channel=true;cfg->output_playback_channel=false;
  cfg->afe_ringbuf_size=16;cfg->debug_init=false;cfg=afe_config_check(cfg);assert(cfg);
  const esp_afe_sr_iface_t *afe=esp_afe_handle_from_config(cfg);assert(afe);
  esp_afe_sr_data_t *data=afe->create_from_config(cfg);assert(data);
  int a=afe->reset_wakenet_threshold(data,1),b=afe->reset_wakenet_threshold(data,2);
  printf("NATIVE_BOTH_SLOTS slot1=%d slot2=%d feed=%d fetch=%d\n",a,b,afe->get_feed_chunksize(data),afe->get_fetch_chunksize(data));
  assert(a==1&&b==1);afe->destroy(data);afe_config_free(cfg);esp_srmodel_deinit(models);
  puts("NATIVE_MODEL_TEST_PASS");fflush(stdout);
  for(;;)vTaskDelay(pdMS_TO_TICKS(1000));
}
