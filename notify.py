import logging

import voluptuous as vol

from homeassistant.const import ATTR_LOCATION

from homeassistant.components.notify import (
    ATTR_DATA,
    ATTR_MESSAGE,
    ATTR_TARGET,
    ATTR_TITLE,
    PLATFORM_SCHEMA,
    BaseNotificationService,
)

from .const import (
    DOMAIN,
    ATTR_PHOTO,
)

_LOGGER = logging.getLogger(__name__)

def get_service(hass, config, discovery_info=None):
    """Get the KakaoTalk notification service."""
    return KakaoTalkNotificationService(hass)

class KakaoTalkNotificationService(BaseNotificationService):
    def __init__(self, hass):
        """Initialize the service."""
        self.hass = hass

    def send_message(self, message="", **kwargs):
        service_data = {}
        if ATTR_TITLE in kwargs:
            service_data.update({ATTR_TITLE: kwargs.get(ATTR_TITLE)})
        if message:
            service_data.update({ATTR_MESSAGE: message})

        data = kwargs.get(ATTR_DATA)
        if data is not None and ATTR_PHOTO in data:
            photos = data.get(ATTR_PHOTO, None)
            photos = photos if isinstance(photos, list) else [photos]
            for photo_data in photos:
                service_data.update(photo_data)
                self.hass.services.call(DOMAIN, "send_message", service_data=service_data)
            return

        # Send message
        _LOGGER.debug(
            "KAKAOTALK NOTIFIER calling %s.send_message with %s", DOMAIN, service_data
        )

        return self.hass.services.call(
            DOMAIN, "send_message", service_data=service_data
        )