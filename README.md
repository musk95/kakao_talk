# kakao_talk
The **kakao_talk** platform uses KakaoTalk to deliver notifications from [Home Assistant][hass] to your Android device, your Windows phone, or your iOS device.

<div>
  <img width="600" src="https://user-images.githubusercontent.com/11463289/69047831-69a72300-0a3f-11ea-9382-94141f96a88e.png"/>
</div>

## Installation

* All files of this repository should be placed on `custom_components\kakaotalk` inside of `~/.homeassistant` or `~/config` folder. 

       $ cd ~/.homeassistant
       $ mkdir custom_components
       $ cd custom_components
       $ git clone https://github.com/musk95/kakao_talk.git kakaotalk
       
* Restart the Home Assistant service

## Configuration

The requirements are:
* You need the REST API Key for KakaoTalk.

To enable KakaoTalk notifications in your installation, add the following to your `configuration.yaml` file:
```
kakao_talk:
  api_key: YOUR_API_KEY
  redirect_uri: YOUR_HASSIO_URL
  send_to_friends: True
  
notify:
  - name: kakaotalk_noti
    platform: kakao_talk

```

Restart the Home Assistant service.

and type YOUR_HASSIO_URL/api/kakao_talk on the web browser such as Chrome, Firefox...
