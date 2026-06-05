import logging
import time

import aiohttp

_LOGGER = logging.getLogger(__name__)


class PulseEightAPIError(Exception):
    pass


class PulseEightConnectionError(Exception):
    pass


class PulseEightAPI:

    def __init__(self, host, port=80, session=None):
        self.host = host
        self.port = port
        self.session = session
        self.base_url = f"http://{host}:{port}"

    async def _request(self, endpoint):
        if self.session is None:
            raise PulseEightAPIError("No HTTP session")

        ts = int(time.time() * 1000)
        url = f"{self.base_url}{endpoint}"
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}_={ts}"

        _LOGGER.debug("GET %s", url)

        try:
            async with self.session.get(url) as resp:
                if resp.status != 200:
                    raise PulseEightAPIError(f"HTTP {resp.status}")
                data = await resp.json()
                if isinstance(data, dict) and not data.get("Result", True):
                    raise PulseEightAPIError(data.get("Message", "unknown error"))
                return data
        except aiohttp.ClientError as e:
            raise PulseEightConnectionError(str(e)) from e
        except (PulseEightAPIError, PulseEightConnectionError):
            raise
        except Exception as e:
            raise PulseEightAPIError(str(e)) from e

    async def get_system_details(self):
        return await self._request("/System/Details")

    async def get_ports(self):
        data = await self._request("/Port/List")
        return data.get("Ports", [])

    async def set_port_routing(self, input_bay, output_bay):
        return await self._request(f"/Port/Set/{input_bay}/{output_bay}")

    async def get_system_health(self):
        return await self._request("/System/Health")

    async def get_port_details(self, mode, bay):
        return await self._request(f"/Port/Details/{mode.capitalize()}/{bay}")

    async def reboot(self):
        return await self._request("/System/Reboot")
