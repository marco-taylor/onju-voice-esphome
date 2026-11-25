"""Experimental single-engine WakeNet consumer for the existing Onju PCM source."""
from pathlib import Path
import hashlib,json
from esphome import automation
import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import microphone,esp32,ota
from esphome.const import CONF_ID,CONF_MICROPHONE
CONF_ON_WAKE_WORD_DETECTED="on_wake_word_detected"
DEPENDENCIES=['esp32','microphone']
AUTO_LOAD=['audio','ring_buffer']
ns=cg.esphome_ns.namespace('onju_wakenet');WakeNet=ns.class_('WakeNet',cg.Component)
StartAction=ns.class_('StartAction',automation.Action);StopAction=ns.class_('StopAction',automation.Action)
CONFIG_SCHEMA=cv.All(cv.Schema({cv.GenerateID():cv.declare_id(WakeNet),cv.Required(CONF_MICROPHONE):microphone.microphone_source_schema(min_bits_per_sample=16,max_bits_per_sample=16,min_channels=1,max_channels=1),cv.Required('can_listen'):cv.returning_lambda,cv.Required('on_enabled'):cv.lambda_,cv.Optional(CONF_ON_WAKE_WORD_DETECTED):automation.validate_automation(single=True)}).extend(cv.COMPONENT_SCHEMA),cv.only_on_esp32,cv.only_with_framework('esp-idf'))
FINAL_VALIDATE_SCHEMA=cv.Schema({cv.Required(CONF_MICROPHONE):microphone.final_validate_microphone_source_schema('onju_wakenet',sample_rate=16000)},extra=cv.ALLOW_EXTRA)
async def to_code(config):
 root=Path(__file__).resolve().parents[2];sdk=root/'sdk'/'esp-sr-wakenet';sr=sdk/'esp-sr';blob=sdk/'wakenet-three.bin'
 if not blob.is_file() or not (sr/'CMakeLists.txt').is_file():raise cv.Invalid('Run tools/bootstrap_wakenet.py first')
 meta=json.loads((sdk/'wakenet-model.json').read_text());data=blob.read_bytes()
 if meta['esp_sr_commit']!='bb552f1a559396a17681299cb3e199a0f1a4520a' or hashlib.sha256(data).hexdigest()!=meta['blob_sha256']:raise cv.Invalid('Pinned WakeNet blob integrity failure')
 esp32.add_idf_component(name='esp-sr',path=str(sr))
 # Exact resolved versions from the first native dependency graph.
 for name,version in [('espressif/esp-dl','3.3.13'),('espressif/dl_fft','0.8.0'),('espressif/cjson','1.7.19~2'),('espressif/esp_new_jpeg','1.0.2')]:
  esp32.add_idf_component(name=name,ref=version)
 ota.request_ota_state_listeners()
 cg.add_define('USE_ONJU_WAKENET')
 cg.add_global(cg.RawStatement('alignas(16) static const uint8_t onju_wakenet_three_blob[] = {'+','.join(f'0x{x:02x}' for x in data)+'};'))
 var=cg.new_Pvariable(config[CONF_ID]);await cg.register_component(var,config)
 cg.add(var.set_model_blob(cg.RawExpression('onju_wakenet_three_blob'),len(data)))
 cg.add(var.set_microphone_source(await microphone.microphone_source_to_code(config[CONF_MICROPHONE])))
 cg.add(var.set_can_listen(await cg.process_lambda(config['can_listen'],[],return_type=cg.bool_)))
 cg.add(var.set_on_enabled(await cg.process_lambda(config['on_enabled'],[],return_type=cg.void)))
 if CONF_ON_WAKE_WORD_DETECTED in config:await automation.build_automation(var.get_wake_word_detected_trigger(),[(cg.std_string,'wake_word')],config[CONF_ON_WAKE_WORD_DETECTED])
@automation.register_action('onju_wakenet.start',StartAction,automation.maybe_simple_id({cv.GenerateID():cv.use_id(WakeNet)}),synchronous=True)
async def start_to_code(config,action_id,template_arg,args):return cg.new_Pvariable(action_id,template_arg,await cg.get_variable(config[CONF_ID]))
@automation.register_action('onju_wakenet.stop',StopAction,automation.maybe_simple_id({cv.GenerateID():cv.use_id(WakeNet)}),synchronous=True)
async def stop_to_code(config,action_id,template_arg,args):return cg.new_Pvariable(action_id,template_arg,await cg.get_variable(config[CONF_ID]))
