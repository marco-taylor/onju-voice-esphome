import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.const import CONF_ID
DEPENDENCIES = ["esp32", "ota"]
ns = cg.esphome_ns.namespace("onju_update_metrics")
MemoryMetrics = ns.class_("MemoryMetrics", cg.Component)
CONFIG_SCHEMA = cv.Schema({cv.GenerateID(): cv.declare_id(MemoryMetrics)}).extend(cv.COMPONENT_SCHEMA)
async def to_code(config):
    cg.add_define("USE_OTA_STATE_LISTENER")
    var=cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var,config)
