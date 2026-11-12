import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import select
from esphome.const import CONF_ID

ns = cg.esphome_ns.namespace("onju_sensitivity")
SensitivitySelect = ns.class_("SensitivitySelect", select.Select, cg.Component)
OPTIONS = ["Slightly sensitive", "Moderately sensitive", "Very sensitive"]
def validate_options(value):
    if value != OPTIONS:
        raise cv.Invalid("Keep the versioned three-option order unchanged")
    return value

CONFIG_SCHEMA = select.select_schema(SensitivitySelect).extend({
    cv.Required("options"): cv.All(cv.ensure_list(cv.string_strict), validate_options),
    cv.Optional("restore_value", default=True): cv.All(cv.boolean, cv.one_of(True)),
    cv.Optional("initial_option", default="Moderately sensitive"): cv.one_of(*OPTIONS),
}).extend(cv.COMPONENT_SCHEMA)

async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    await select.register_select(var, config, options=OPTIONS)
    cg.add(var.set_initial_index(OPTIONS.index(config["initial_option"])))
