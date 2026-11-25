#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_heap_caps.h"
#include "esp_timer.h"
#include "esp_afe_sr_models.h"
#include "esp_nsn_iface.h"
#include "esp_nsn_models.h"
#include "model_path.h"
extern const unsigned char onju_native_blob[];
void app_main(void){
 srmodel_list_t *models=srmodel_load(onju_native_blob);assert(models&&models->num==3);
 assert(!strcmp(models->model_name[0],"wn10_alexa")&&!strcmp(models->model_name[1],"wn10_de_halloesp")&&!strcmp(models->model_name[2],"nsnet2"));
 afe_config_t *cfg=afe_config_init("M",models,AFE_TYPE_SR,AFE_MODE_LOW_COST);assert(cfg);
 cfg->aec_init=false;cfg->se_init=false;cfg->ns_init=true;cfg->afe_ns_mode=AFE_NS_MODE_NET;cfg->ns_model_name=models->model_name[2];cfg->vad_init=false;cfg->agc_init=false;cfg->wakenet_init=true;cfg->wakenet_model_name=models->model_name[0];cfg->wakenet_model_name_2=models->model_name[1];
 cfg=afe_config_check(cfg);assert(cfg&&cfg->ns_init&&cfg->afe_ns_mode==AFE_NS_MODE_NET&&!cfg->aec_init&&!cfg->vad_init&&!cfg->agc_init&&cfg->wakenet_init);puts("NATIVE_NS_AFE_CONFIG_PASS");afe_config_free(cfg);
 const esp_nsn_iface_t *ns=esp_nsnet_handle_from_name(models->model_name[2]);assert(ns);
 printf("NATIVE_NS_LOOKUP_PASS model=%s interface=%p\n",models->model_name[2],ns);fflush(stdout);
 unsigned before=heap_caps_get_free_size(MALLOC_CAP_INTERNAL|MALLOC_CAP_8BIT),psram=heap_caps_get_free_size(MALLOC_CAP_SPIRAM);
 esp_nsn_data_t *data=ns->create(models->model_name[2]);printf("NATIVE_NS_CREATE_RETURN handle=%p\n",data);fflush(stdout);assert(data);
 int chunk=ns->get_samp_chunksize(data),rate=ns->get_samp_rate(data);assert(chunk==512&&rate==16000);
 printf("NATIVE_NS_MODEL_CREATE_PASS chunk=%d rate=%d internal_cost=%u psram_cost=%u min_internal=%u\n",chunk,rate,before-heap_caps_get_free_size(MALLOC_CAP_INTERNAL|MALLOC_CAP_8BIT),psram-heap_caps_get_free_size(MALLOC_CAP_SPIRAM),heap_caps_get_minimum_free_size(MALLOC_CAP_INTERNAL|MALLOC_CAP_8BIT));fflush(stdout);
 int16_t *in=calloc(chunk,sizeof(int16_t)),*out=calloc(chunk,sizeof(int16_t));assert(in&&out);
 int64_t t=esp_timer_get_time();for(int i=0;i<8;i++){int res=ns->process(data,in,out);printf("NATIVE_NS_PROCESS frame=%d native=%d\n",i,res);assert(res>=0);}printf("NATIVE_NS_PROCESS_US=%lld\n",(long long)(esp_timer_get_time()-t));
 free(in);free(out);ns->destroy(data);esp_srmodel_deinit(models);puts("NATIVE_NS_TEST_PASS");fflush(stdout);
 for(;;)vTaskDelay(pdMS_TO_TICKS(1000));
}
