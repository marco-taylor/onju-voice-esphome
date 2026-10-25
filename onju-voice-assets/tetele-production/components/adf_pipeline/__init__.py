"""General ADF-Pipeline Setup."""

from pathlib import Path

import esphome.codegen as cg
from esphome.components.esp32 import add_idf_component
from esphome.components import esp32
import esphome.config_validation as cv
from esphome.const import CONF_ID
from esphome.core import coroutine_with_priority, ID


CODEOWNERS = ["@gnumpi"]
DEPENDENCIES = []

IS_PLATFORM_COMPONENT = True

CONF_ADF_COMPONENT_TYPE = "type"
CONF_ADF_PIPELINE = "pipeline"
CONF_ADF_KEEP_PIPELINE_ALIVE = "keep_pipeline_alive"

esp_adf_ns = cg.esphome_ns.namespace("esp_adf")
ADFPipelineController = esp_adf_ns.class_("ADFPipelineController")

ADFPipelineElement = esp_adf_ns.class_("ADFPipelineElement")
ADFPipelineSink = esp_adf_ns.class_("ADFPipelineSinkElement", ADFPipelineElement)
ADFPipelineSource = esp_adf_ns.class_("ADFPipelineSourceElement", ADFPipelineElement)
ADFPipelineProcess = esp_adf_ns.class_("ADFPipelineProcessElement", ADFPipelineElement)

BUILT_IN_AUDIO_ELEMENT_IDS = ["resampler"]

# Pipeline Controller

COMPONENT_TYPES = ["sink", "source", "filter"]
SELF_DESCRIPTORS = ["this", "source", "sink", "self"]

ADF_PIPELINE_CONTROLLER_SCHEMA = cv.Schema(
    {
        cv.Optional(CONF_ADF_COMPONENT_TYPE): cv.one_of(*COMPONENT_TYPES),
        cv.Optional(CONF_ADF_KEEP_PIPELINE_ALIVE, default=False): cv.boolean,
        cv.Optional(CONF_ADF_PIPELINE): cv.ensure_list(
            cv.Any(
                cv.one_of(*SELF_DESCRIPTORS),
                cv.one_of(*BUILT_IN_AUDIO_ELEMENT_IDS),
                cv.use_id(ADFPipelineElement),
            )
        ),
    }
)

ADFResampler = esp_adf_ns.class_("ADFResampler", ADFPipelineProcess, ADFPipelineElement)


async def setup_pipeline_controller(cntrl, config: dict) -> None:
    """Set controller parameter and register elements to pipeline."""

    cg.add(cntrl.set_keep_alive(config[CONF_ADF_KEEP_PIPELINE_ALIVE]))

    if CONF_ADF_PIPELINE in config:
        for comp_id in config[CONF_ADF_PIPELINE]:
            if comp_id in SELF_DESCRIPTORS:
                cg.add(cntrl.append_own_elements())
            elif comp_id in BUILT_IN_AUDIO_ELEMENT_IDS:
                element_id = ID(
                    cv.validate_id_name(config[CONF_ID].id + "_resampler"),
                    is_declaration=True,
                    type=ADFResampler,
                )
                comp = cg.new_Pvariable(element_id)
                cg.add(cntrl.add_element_to_pipeline(comp))
            else:
                comp = await cg.get_variable(comp_id)
                cg.add(cntrl.add_element_to_pipeline(comp))


# Pipeline Elements

ADF_PIPELINE_ELEMENT_SCHEMA = cv.Schema({})

element_classes = {
    "resampler": esp_adf_ns.class_(
        "ADFResampler", ADFPipelineProcess, ADFPipelineElement
    )
}


@coroutine_with_priority(55.0)
async def to_code(config):
    
    cg.add_platformio_option("build_unflags", "-Wl,--end-group")

    cg.add_platformio_option(
        "board_build.embed_txtfiles", "components/dueros_service/duer_profile"
    )

    esp32.add_idf_sdkconfig_option("CONFIG_ESP_TLS_INSECURE", True)
    esp32.add_idf_sdkconfig_option("CONFIG_ESP_TLS_SKIP_SERVER_CERT_VERIFY", True)

    # ESPHome 2026.9.1 emits one idf_component.yml dependency per call.
    # The installed IDF Component Manager initializes Git submodules recursively
    # (idf_component_tools.sources.git.GitSource -> prepare_ref(with_submodules=True)).
    # Do not patch the shared ESP-IDF installation via the old PlatformIO hook.
    adf_components = (
        "audio_pipeline", "audio_sal", "esp-adf-libs", "esp-sr",
        "dueros_service", "clouds", "audio_stream", "audio_board",
        "esp_peripherals", "audio_hal", "display_service", "esp_dispatcher",
        "esp_actions", "wifi_service", "audio_recorder", "tone_partition",
    )
    # Vendored SDK and submodules are pinned in sdk/esp-adf/SOURCE_LOCK.json.
    # Local directory dependencies are supported by ESPHome's current IDF manifest API.
    sdk_root = Path(__file__).resolve().parents[2] / "sdk" / "esp-adf"
    for component in adf_components:
        component_path = sdk_root / "components" / component
        if not (component_path / "CMakeLists.txt").is_file():
            raise cv.Invalid(f"Missing pinned ADF component: {component_path}")
        add_idf_component(name=component, path=str(component_path))

    # nghttp moved from ESP-IDF into the official component registry in IDF 5.x.
    add_idf_component(name="espressif/nghttp", ref="1.68.1")

    # IDF compatibility settings; no change to sample format or signal processing.
    esp32.add_idf_sdkconfig_option("CONFIG_FREERTOS_ENABLE_BACKWARD_COMPATIBILITY", True)
    esp32.add_idf_sdkconfig_option("CONFIG_FREERTOS_TASK_CREATE_ALLOW_EXT_MEM", True)
