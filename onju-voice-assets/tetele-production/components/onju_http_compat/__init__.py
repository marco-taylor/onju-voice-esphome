"""Keep existing ADF TLS fallback while native managed OTA verifies its own CA chain.

Codegen only. Never changes microphone, DSP, MWW or running device settings.
The IDF certificate-bundle branch takes precedence over its no-CA fallback.
"""
import esphome.config_validation as cv
from esphome.components import esp32
from esphome.core import coroutine_with_priority, CoroPriority
import esphome.final_validate as fv

DEPENDENCIES = ["esp32", "adf_pipeline", "http_request"]
CONFIG_SCHEMA = cv.Schema({})


def validate(config):
    if not fv.full_config.get()["http_request"]["verify_ssl"]:
        raise cv.Invalid("Managed updates require verify_ssl: true and the native CA bundle")
    return config


FINAL_VALIDATE_SCHEMA = validate


@coroutine_with_priority(CoroPriority.FINAL)
async def to_code(config):
    # Existing ADF player supplies no CA; preserve its established behavior.
    # The managed HTTP client always supplies crt_bundle_attach and therefore
    # uses MBEDTLS_SSL_VERIFY_REQUIRED, not this no-CA fallback (IDF 5.5.6).
    esp32.add_idf_sdkconfig_option("CONFIG_ESP_TLS_INSECURE", True)
    esp32.add_idf_sdkconfig_option("CONFIG_ESP_TLS_SKIP_SERVER_CERT_VERIFY", True)
