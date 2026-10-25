"""Timer-only adapter for the existing Tetele ADF player and native VA timers."""
import esphome.codegen as cg
import esphome.config_validation as cv
from esphome import automation
from esphome.components import light, voice_assistant
from esphome.components.adf_pipeline.media_player import ADFMediaPlayer
from esphome.const import CONF_ID

DEPENDENCIES = ["voice_assistant", "adf_pipeline", "light"]
ns = cg.esphome_ns.namespace("onju_timer")
TimerManager = ns.class_("TimerManager", cg.Component)
CONFIG_SCHEMA = cv.Schema({
    cv.GenerateID(): cv.declare_id(TimerManager),
    cv.Required("voice_assistant"): cv.use_id(voice_assistant.VoiceAssistant),
    cv.Required("media_player"): cv.use_id(ADFMediaPlayer),
    cv.Required("light"): cv.use_id(light.LightState),
    cv.Required("playback_allowed"): cv.returning_lambda,
    cv.Optional("on_refresh"): automation.validate_automation(single=True),
    cv.Optional("on_recover"): automation.validate_automation(single=True),
}).extend(cv.COMPONENT_SCHEMA)

async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    for key in ("voice_assistant", "media_player", "light"):
        cg.add(getattr(var, "set_" + key)(await cg.get_variable(config[key])))
    cg.add(var.set_playback_allowed(await cg.process_lambda(config["playback_allowed"], [], return_type=cg.bool_)))
    for key in ("on_refresh", "on_recover"):
        if key in config:
            trigger = getattr(var, "get_" + key[3:] + "_trigger")()
            await automation.build_automation(trigger, [], config[key])
