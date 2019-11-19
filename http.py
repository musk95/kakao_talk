import logging
import json
import requests
import os

from aiohttp import web
from urllib.parse import urlparse
from homeassistant.components.http import HomeAssistantView
from homeassistant.components.http.const import KEY_REAL_IP
from homeassistant.core import callback, ServiceCall
import homeassistant.util as hass_util
from homeassistant.util.network import is_local

from .const import (
    DOMAIN,
    CONF_API_KEY,
    CONF_REDIRECT_URI,
    CONF_SEND_TO_FRIENDS,
    KAKAO_TALK_API_ENDPOINT,
    SESSION_FILE,
    SERVICE_SEND_MESSAGE,
    ATTR_URL,
)

from homeassistant.components.notify import (
    ATTR_TITLE,
)

_LOGGER = logging.getLogger(__name__)

class KakaoConfig:
    def __init__(self, hass, config):
        self.hass = hass
        self._config = config
        self._api_key = config.get(CONF_API_KEY)
        self._host = '{uri.netloc}'.format(uri=urlparse(config.get(CONF_REDIRECT_URI)))
        self._send_to_friends = config.get(CONF_SEND_TO_FRIENDS)
        self._friends = []
        self._access_token = None
        self._refresh_token = None
        self._frends_auth = False

        _LOGGER.debug("KakaoConfig {}".format(self._host))

        _filepath = "{}/{}".format(hass.config.config_dir, SESSION_FILE)
        if os.path.exists(_filepath):
            with open(_filepath, "r") as file:
                if os.stat(_filepath).st_size == 0:
                    _LOGGER.warning("Please login on Kakaotalk!!")
                else:
                    self._refresh_token = file.read()
                    _LOGGER.debug("KAKAO SESSION {}".format(self._refresh_token))
                file.close()

    def save_refresh_token(self):
        _filepath = "{}/{}".format(self.hass.config.config_dir, SESSION_FILE)
        with open(_filepath, "w") as file:
            file.write(self._refresh_token)
            file.close()

    async def _async_get_token(self, code):
        _res = await self.getAccessToken(self._api_key,code)
        _LOGGER.debug("KakaoTalkView [get key] %s", _res)

        if hasattr(_res , 'error'):
            return _res

        self._access_token = _res["access_token"]
        self._refresh_token = _res["refresh_token"]
        self.save_refresh_token()

        return _res

    async def async_send_text(self, message):
        _LOGGER.debug("KakaoTalkView [send message to kakao server] {}, {}".format(self._api_key, self._refresh_token))
        _res = await self.getAccessRefreshToken(self._api_key, self._refresh_token)
        self._access_token = _res["access_token"]
        if hasattr(_res , 'refresh_token'):
            self._refresh_token = _res["refresh_token"]
            save_refresh_token()

        _url = "http://{}".format(self._host)
        _LOGGER.debug("KakaoTalkView [Host URL] {}".format(_url))
        _res = await sendText(self._access_token, message, _url)
        _LOGGER.debug("KakaoTalkView [message] Result {}".format(_res))

        if self._send_to_friends is True:
            if not self._friends:
                await self.getFriends(self._access_token)
            if self._friends:
                _res = await sendTextToFriends(self._access_token, message, _url, self._friends)
                _LOGGER.debug("KakaoTalkView [message] Result {}".format(_res))

    async def async_send_default_template(self, title, message, image_url):
        _LOGGER.debug("KakaoTalkView [send template message to kakao server] {}, {}".format(self._api_key, self._refresh_token))
        _res = await self.getAccessRefreshToken(self._api_key, self._refresh_token)
        self._access_token = _res["access_token"]
        if hasattr(_res , 'refresh_token'):
            self._refresh_token = _res["refresh_token"]
            save_refresh_token()

        _url = "http://{}".format(self._host)
        _res = await sendDefaultTemplate(self._access_token, title, message, image_url, _url)
        _LOGGER.debug("KakaoTalkView [message] Result {}".format(_res))

        if self._send_to_friends is True:
            if not self._friends:
                await self.getFriends(self._access_token)
            if self._friends:
                _res = await sendDefaultTemplateToFriends(self._access_token, title, message, image_url, _url, self._friends)
                _LOGGER.debug("KakaoTalkView [message] Result {}".format(_res))

    async def get_setup_page(self):
        _path = "{}/custom_components/kakao_talk/setup.html".format(self.hass.config.config_dir)

        _filecontent = ""
        try:
            with open(_path, mode="r", encoding="utf-8", errors="ignore") as localfile:
                _filecontent = localfile.read()
                localfile.close()
        except Exception as exception:
            pass

        return _filecontent

    async def getAccessToken(self, clientId, code):
        url = "https://kauth.kakao.com/oauth/token"
        payload = "grant_type=authorization_code"
        payload += "&client_id=" + clientId
        payload += "&redirect_url=http%3A%2F%2Flocalhost%3A5000%2Foauth&code=" + code
        headers = {
            'Content-Type' : "application/x-www-form-urlencoded",
            'Cache-Control' : "no-cache",
        }
        reponse = requests.request("POST",url,data=payload, headers=headers)
        access_token = json.loads(((reponse.text).encode('utf-8')))
        return access_token

    async def getAccessRefreshToken(self, clientId, refreshToken):
        url = "https://kauth.kakao.com/oauth/token"
        payload = "grant_type=refresh_token"
        payload += "&client_id=" + clientId
        payload += "&refresh_token=" + refreshToken
        headers = {
            'Content-Type' : "application/x-www-form-urlencoded",
            'Cache-Control' : "no-cache",
        }
        reponse = requests.request("POST",url,data=payload, headers=headers)
        access_token = json.loads(((reponse.text).encode('utf-8')))
        return access_token

    async def getFriends(self, accessToken):
        url = "https://kapi.kakao.com/v1/api/talk/friends"
        headers = {
            'Authorization' : "Bearer " + accessToken,
        }
        reponse = requests.get(url, headers=headers)
        _LOGGER.debug("KakaoTalkView [Friends] %s", reponse.text)
        _ret = json.loads(((reponse.text).encode('utf-8')))
        if 'error' in _ret:
            _LOGGER.warning("KakaoTalk [Friends] Error : %s", _ret['error'])
            return
        for friend in _ret['elements']:
            self._friends.append(friend['uuid'])

        _LOGGER.debug("KakaoTalk [Friends] %s", json.dumps(self._friends))

@callback
def async_register_http(hass, cfg):
    _LOGGER.debug("async_register_http")
    api_key = cfg.get(CONF_API_KEY)
    config = KakaoConfig(hass, cfg)
    hass.http.register_view(KakaoTalkView(config))

    async def request_sync_service_handler(call: ServiceCall):
        """Handle request sync service calls."""
        _LOGGER.debug("request_sync_service_handler {}".format(call))
        if ATTR_URL in call.data:
            if ATTR_TITLE in call.data:
                _title = call.data.get(ATTR_TITLE)
            else:
                _title = ""
            _message = call.data.get("message")
            _image_url = call.data.get(ATTR_URL)
            await config.async_send_default_template(_title, _message, _image_url)
            return

        if ATTR_TITLE in call.data:
            _title = call.data.get(ATTR_TITLE)
            _message = call.data.get("message")
            _message = f"{_title}\n\n{_message}" if _title else _message
        else:
            _message = call.data.get("message")

        await config.async_send_text(_message)

    hass.services.async_register(
        DOMAIN, SERVICE_SEND_MESSAGE, request_sync_service_handler
    )

class KakaoTalkView(HomeAssistantView):
    _LOGGER.debug("KakaoTalkView")

    url = KAKAO_TALK_API_ENDPOINT
    name = "api:kakao_talk"
    requires_auth = False

    def __init__(self, config):
        _LOGGER.debug("KakaoTalkView [init]")
        self.config = config

    async def get(self, request): 
        _LOGGER.debug("KakaoTalkView [get] %s", request.rel_url)
        _code = None
        _message = None
        _query = request.rel_url.query
        if 'image' in _query:
            _path = "{}/custom_components/kakao_talk/images/{}".format(self.config.hass.config.config_dir, _query['image'])
            response = web.FileResponse(_path)
            response.content_type = 'image/png'
            return response

        if 'code' in _query:
            _code = _query['code']
            _LOGGER.debug("KakaoTalkView [get code] %s", _code)

            self._friends = []

            if self.config._frends_auth is not True:
                self.config._frends_auth = True
                return web.HTTPFound('https://kauth.kakao.com/oauth/authorize?client_id={}&redirect_uri=http%3A%2F%2F{}%2Fapi%2Fkakao_talk&response_type=code&scope=friends,talk_message'.format(self.config._api_key, request.host))

            _res = await self.config._async_get_token(str(_code))

            if hasattr(_res , 'error'):
                _error = _res["error_description"]
                _LOGGER.warning(_error)
                return web.Response(text=_error, status=200)

#            resp = web.Response(text='OK', status=200)
#            resp.set_cookie('key', self.config._access_token)
            _filecontent = await self.config.get_setup_page()
            _filecontent = _filecontent.replace("{_api_key}", self.config._api_key)
            _filecontent = _filecontent.replace("{_host}", request.host)
            resp = web.Response(body=_filecontent, content_type="text/html", charset="utf-8")
            return resp

        if 'message' in _query:
            _message = _query['message']
            _LOGGER.debug("KakaoTalkView [get messgae] %s", _message)
            await self.config.async_send_text(_message)
            return web.Response(text='OK', status=200)

        # Display Login Page
        #if not is_local(request[KEY_REAL_IP]):
        #    return web.Response(text="401: Unauthorized", status=401)

        if request.cookies is not None:
            cookie = request.cookies #('name_of_cookie')
            #if 'key' in cookie:
            _LOGGER.debug("KakaoTalkView [cookie] %s", cookie)
        self.config._frends_auth = False
        _filecontent = await self.config.get_setup_page()
        _filecontent = _filecontent.replace("{_api_key}", self.config._api_key)
        _filecontent = _filecontent.replace("{_host}", request.host)
        resp = web.Response(body=_filecontent, content_type="text/html", charset="utf-8")
        return resp

async def sendText(accessToken, message, url) :
    url = 'https://kapi.kakao.com/v2/api/talk/memo/default/send'
    payloadDict = {
            'object_type': 'text',
            'text': message,
            'link': {
                'web_url': url,
                'mobile_web_url': url
             },
            'button_title': '바로 확인'
            }
    payload = 'template_object=' + json.dumps(payloadDict)

    headers = {
        'Content-Type' : "application/x-www-form-urlencoded",
        'Cache-Control' : "no-cache",
        'Authorization' : "Bearer " + accessToken,
    }
    reponse = requests.request("POST",url,data=payload, headers=headers)
    return json.loads(((reponse.text).encode('utf-8')))

async def sendDefaultTemplate(accessToken, title, message, image_url, url):
    url = 'https://kapi.kakao.com/v2/api/talk/memo/default/send'
    payloadDict = {
        "object_type":"feed",
        "content":{
          "title":title,
          "description":message,
          "image_url":image_url,
          "link":{
            "mobile_web_url":url,
            "web_url":url
          }
        },
        "social":{},
        'button_title': '바로 확인'
      }
    payload = 'template_object=' + json.dumps(payloadDict)

    headers = {
        'Content-Type' : "application/x-www-form-urlencoded",
        'Cache-Control' : "no-cache",
        'Authorization' : "Bearer " + accessToken,
    }
    reponse = requests.request("POST",url,data=payload, headers=headers)
    return json.loads(((reponse.text).encode('utf-8')))

async def sendTextToFriends(accessToken, message, url, friends) :
    url = 'https://kapi.kakao.com/v1/api/talk/friends/message/default/send'
    payloadDict = {
            'object_type': 'text',
            'text': message,
            'link': {
                'web_url': url,
                'mobile_web_url': url
             },
            'button_title': '바로 확인'
            }
    payload = {
            'receiver_uuids': json.dumps(friends), 
            'template_object': json.dumps(payloadDict)
            }

    _LOGGER.debug("sendTextToFriends %s", payload)

    headers = {
        'Content-Type' : "application/x-www-form-urlencoded",
        'Cache-Control' : "no-cache",
        'Authorization' : "Bearer " + accessToken,
    }
    reponse = requests.request("POST",url,data=payload, headers=headers)
    return json.loads(((reponse.text).encode('utf-8')))

async def sendDefaultTemplateToFriends(accessToken, title, message, image_url, url, friends):
    url = 'https://kapi.kakao.com/v1/api/talk/friends/message/default/send'
    payloadDict = {
        "object_type":"feed",
        "content":{
          "title":title,
          "description":message,
          "image_url":image_url,
          "link":{
            "mobile_web_url":url,
            "web_url":url
          }
        },
        "social":{},
        'button_title': '바로 확인'
      }
    payload = {
            'receiver_uuids': json.dumps(friends), 
            'template_object': json.dumps(payloadDict)
            }

    _LOGGER.debug("sendTextToFriends %s", payload)

    headers = {
        'Content-Type' : "application/x-www-form-urlencoded",
        'Cache-Control' : "no-cache",
        'Authorization' : "Bearer " + accessToken,
    }
    reponse = requests.request("POST",url,data=payload, headers=headers)
    return json.loads(((reponse.text).encode('utf-8')))
