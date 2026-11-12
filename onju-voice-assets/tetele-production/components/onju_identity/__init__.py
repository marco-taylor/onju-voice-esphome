"""ESPHome 2026.10.2-only, pre-entity identity and native Wi-Fi migration."""
import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.core import CORE, coroutine_with_priority

DEPENDENCIES = ["esp32", "wifi"]
ns = cg.esphome_ns.namespace("onju_identity")
BOOTSTRAP = cv.Schema({
    cv.Required("expected_mac"): cv.mac_address,
    cv.Required("node_name"): cv.valid_name,
    cv.Required("friendly_name"): cv.string_strict,
    cv.Required("ssid"): cv.string_strict,
    cv.Required("password"): cv.string_strict,
    cv.Required("static_ip"): cv.ipv4address,
    cv.Required("gateway"): cv.ipv4address,
    cv.Required("subnet"): cv.ipv4address,
    cv.Optional("dns1", default="0.0.0.0"): cv.ipv4address,
    cv.Optional("dns2", default="0.0.0.0"): cv.ipv4address,
})
CONFIG_SCHEMA = cv.Schema({cv.Optional("bootstrap"): BOOTSTRAP})

@coroutine_with_priority(99)
async def to_code(config):
    # Core priority=100, entity construction=0: replace exactly one supported
    # native pre_setup call, not an on_boot callback after preference registration.
    if CORE.config["esphome"]["name_add_mac_suffix"]:
        raise cv.Invalid("onju_identity supplies the MAC suffix locally; name_add_mac_suffix must be false")
    cg.add_define("USE_ONJU_IDENTITY")
    cg.add_define("USE_WIFI_MANUAL_IP")
    seed = "nullptr"
    if "bootstrap" in config:
        c = config["bootstrap"]
        values = [str(c["expected_mac"]), c["node_name"], c["friendly_name"], c["ssid"], c["password"]]
        values += [str(c[k]) for k in ["static_ip", "gateway", "subnet", "dns1", "dns2"]]
        cg.add_global(cg.RawStatement("static const onju_identity::Seed onju_identity_seed = {" + ", ".join(str(cg.safe_exp(v)) for v in values) + "};"))
        seed = "&onju_identity_seed"
    hits = []
    for i, expression in enumerate(CORE.main_statements):
        text = str(expression).strip()
        if text.startswith("App.pre_setup("):
            hits.append(i)
            args = text[len("App.pre_setup("):].removesuffix(";").removesuffix(")")
            CORE.main_statements[i] = cg.RawStatement("onju_identity::pre_setup(" + args + ", " + seed + ");")
    if len(hits) != 1:
        raise cv.Invalid("Unsupported core codegen: expected exactly one pre_setup; stop migration build")
