from config.envs.default import DefaultConfig
from fsd_utils import configclass


@configclass
class TestConfig(DefaultConfig):
    # Redis Feature Toggle Configuration
    REDIS_INSTANCE_NAME = "funding-service-magic-links-test"

    if not hasattr(DefaultConfig, "VCAP_SERVICES"):
        REDIS_INSTANCE_URI = DefaultConfig.REDIS_INSTANCE_URI
    else:
        REDIS_INSTANCE_URI = DefaultConfig.VCAP_SERVICES.get_service_credentials_value(
            "redis", REDIS_INSTANCE_NAME, "uri"
        )

    TOGGLES_URL = REDIS_INSTANCE_URI + "/0"

    # LRU cache settings
    LRU_CACHE_TIME = 300  # in seconds
