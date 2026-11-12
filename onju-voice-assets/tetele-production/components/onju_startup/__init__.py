"""Bounded local wake-word startup, independent of a VA API subscription."""
import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import micro_wake_word, microphone, voice_assistant, switch, binary_sensor
from esphome.const import CONF_ID
from esphome.components.adf_pipeline.microphone import ADFMicrophone
DEPENDENCIES = ["micro_wake_word", "microphone", "voice_assistant", "switch", "binary_sensor", "adf_pipeline"]
ns = cg.esphome_ns.namespace("onju_startup")
WakeWordStartup = ns.class_("WakeWordStartup", cg.Component)
CONFIG_SCHEMA = cv.Schema({
    cv.GenerateID(): cv.declare_id(WakeWordStartup),
    cv.Required("mww"): cv.use_id(micro_wake_word.MicroWakeWord),
    cv.Required("microphone"): cv.use_id(ADFMicrophone),
    cv.Required("voice_assistant"): cv.use_id(voice_assistant.VoiceAssistant),
    cv.Required("use_wake_word"): cv.use_id(switch.Switch),
    cv.Required("hardware_mute"): cv.use_id(binary_sensor.BinarySensor),
    cv.Required("handover_idle"): cv.returning_lambda,
}).extend(cv.COMPONENT_SCHEMA)

async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    for key in ("mww", "microphone", "voice_assistant", "use_wake_word", "hardware_mute"):
        cg.add(getattr(var, "set_" + key)(await cg.get_variable(config[key])))
    cg.add(var.set_handover_idle(await cg.process_lambda(config["handover_idle"], [], return_type=cg.bool_)))
