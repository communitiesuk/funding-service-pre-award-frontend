"""Flask Test Environment Configuration."""
from os import environ

import redis
from config.environments.default import Config
from config.utils import VcapServices


class TestConfig(Config):

    # GOV.UK PaaS
    VCAP_SERVICES = VcapServices.from_env_json(environ.get("VCAP_SERVICES"))

    # Redis
    REDIS_INSTANCE_NAME = "funding-service-magic-links-test"
    REDIS_INSTANCE_URI = VCAP_SERVICES.get_service_credentials_value(
        "redis", REDIS_INSTANCE_NAME, "uri"
    )
    REDIS_MLINKS_URL = REDIS_INSTANCE_URI + "/0"
    REDIS_SESSIONS_URL = REDIS_INSTANCE_URI + "/1"
    SESSION_REDIS = redis.from_url(REDIS_SESSIONS_URL)
