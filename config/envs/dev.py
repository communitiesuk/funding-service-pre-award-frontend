"""Flask Dev Pipeline Environment Configuration."""

import logging
from os import getenv

from fsd_utils import configclass

from config.envs.default import DefaultConfig


@configclass
class DevConfig(DefaultConfig):
    FSD_LOGGING_LEVEL = logging.INFO
    SESSION_COOKIE_DOMAIN = getenv("SESSION_COOKIE_DOMAIN")

    # assess dev config 
    REDIS_INSTANCE_NAME = "funding-service-magic-links-dev"
    FSD_LOG_LEVEL = "DEBUG"
