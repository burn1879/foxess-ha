from __future__ import annotations

from homeassistant.components.rest import RestData
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.util.ssl import SSLCipherList

from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem

import logging
import json

from .const import (
    _ENDPOINT_AUTH,
    METHOD_POST,
    DEFAULT_ENCODING,
    DEFAULT_VERIFY_SSL
)

software_names = [SoftwareName.CHROME.value]
operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]
user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems, limit=100)
_LOGGER = logging.getLogger(__name__)


async def auth_and_get_token(hass, username, hashed_password):
    # https://github.com/macxq/foxess-ha/issues/93#issuecomment-1319326849
    #    payloadAuth = {"user": username, "password": hashedPassword}
    payload_auth = f'user={username}&password={hashed_password}'
    user_agent = user_agent_rotator.get_random_user_agent()
    headers_auth = {"User-Agent": user_agent,
                    "Accept": "application/json, text/plain, */*",
                    "lang": "en",
                    "sec-ch-ua-platform": "macOS",
                    "Sec-Fetch-Site": "same-origin",
                    "Sec-Fetch-Mode": "cors",
                    "Sec-Fetch-Dest": "empty",
                    "Referer": "https://www.foxesscloud.com/bus/device/inverterDetail?id=xyz&flowType=1&status=1&hasPV=true&hasBattery=false",
                    "Accept-Language": "en-US;q=0.9,en;q=0.8,de;q=0.7,nl;q=0.6",
                    "Connection": "keep-alive",
                    "X-Requested-With": "XMLHttpRequest"}

    rest_auth = RestData(hass, METHOD_POST, _ENDPOINT_AUTH, DEFAULT_ENCODING, None,
                         headers_auth, None, payload_auth, DEFAULT_VERIFY_SSL, SSLCipherList.PYTHON_DEFAULT)

    await rest_auth.async_update()

    if rest_auth.data is None:
        _LOGGER.error("Unable to login to FoxESS Cloud - No data recived")
        return False

    response = json.loads(rest_auth.data)

    if response["result"] is None:
        if response["errno"] is not None and response["errno"] == 41807:
            raise UpdateFailed(
                f"Unable to login to FoxESS Cloud - bad username or password! {rest_auth.data}")
        else:
            raise UpdateFailed(
                f"Error communicating with API: {rest_auth.data}")
    else:
        _LOGGER.debug("Login succesfull" + rest_auth.data)

    token = response["result"]["token"]
    return token
