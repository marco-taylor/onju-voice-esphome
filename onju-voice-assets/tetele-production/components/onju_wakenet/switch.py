"""Acknowledged NS control; persistence belongs to the AFE consumer, not an optimistic switch."""
from esphome import codegen as cg, config_validation as cv
from esphome.components import switch
from esphome.const import CONF_ID, ENTITY_CATEGORY_CONFIG
from . import ns, WakeNet

DEPENDENCIES = ["onju_wakenet"]
NoiseSuppressionSwitch = ns.class_("NoiseSuppressionSwitch", switch.Switch)
CONFIG_SCHEMA = switch.switch_schema(
    NoiseSuppressionSwitch, entity_category=ENTITY_CATEGORY_CONFIG, icon="mdi:waveform",
    default_restore_mode="DISABLED",  # Parent owns the sole NVS key and native acknowledgement.
).extend({cv.Required("onju_wakenet_id"): cv.use_id(WakeNet)})

async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await switch.register_switch(var, config)
    cg.add(var.set_parent(await cg.get_variable(config["onju_wakenet_id"])))
