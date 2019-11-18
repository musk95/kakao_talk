import asyncio
import logging

from typing import Dict, Any
import voluptuous as vol
from homeassistant.helpers import config_validation as cv

from homeassistant.core import HomeAssistant, ServiceCall

from .const import (
    DOMAIN,
    CONF_API_KEY,
    CONF_REDIRECT_URI,
    CONF_SEND_TO_FRIENDS,
)

from .http import async_register_http

_LOGGER = logging.getLogger(__name__)

DEFALUT_SEND_TO_FRIENDS = False

KAKAO_TALK_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(CONF_API_KEY): cv.string,
            vol.Required(CONF_REDIRECT_URI): cv.string,
            vol.Optional(CONF_SEND_TO_FRIENDS, default=DEFALUT_SEND_TO_FRIENDS): cv.boolean,
        },
        extra=vol.PREVENT_EXTRA,
    ),
)

CONFIG_SCHEMA = vol.Schema({DOMAIN: KAKAO_TALK_SCHEMA}, extra=vol.ALLOW_EXTRA)

async def async_setup(hass: HomeAssistant, yaml_config: Dict[str, Any]):
    _LOGGER.debug("async_setup")
    config = yaml_config.get(DOMAIN, {})
    api_key = config.get(CONF_API_KEY)
    async_register_http(hass, config)

    return True