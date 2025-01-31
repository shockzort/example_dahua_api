import ssl
import asyncio
import logging
import dateutil
import os
import urllib
from aiohttp import ClientSession, TCPConnector
import dateutil.parser
from client import DahuaClient

logging.basicConfig(level=logging.INFO)
_LOGGER: logging.Logger = logging.getLogger("Dahua info fetcher")

# Конфигурация устройства Dahua
IP_ADDRESS = "10.50.50.166"  # IP-адрес вашего NVR
PORT = 80
RTSP_PORT = 554
USERNAME = "admin"  # Имя пользователя
PASSWORD = "cnord-010950"  # Пароль

# Формирование URL для запросов
BASE_URL = f"http://{IP_ADDRESS}/cgi-bin/"

SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.set_ciphers("DEFAULT")
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE


async def get_device_info(client: DahuaClient):
    coros = []
    coros.append(asyncio.ensure_future(client.get_device_type()))
    coros.append(asyncio.ensure_future(client.get_software_version()))
    coros.append(asyncio.ensure_future(client.get_hardware_version()))
    coros.append(asyncio.ensure_future(client.get_onvif_version()))
    coros.append(asyncio.ensure_future(client.get_http_api_version()))

    coros.append(asyncio.ensure_future(client.async_current_time()))
    coros.append(asyncio.ensure_future(client.async_get_system_info()))
    coros.append(asyncio.ensure_future(client.async_get_machine_name()))
    coros.append(asyncio.ensure_future(client.async_get_general_config()))
    coros.append(asyncio.ensure_future(client.get_channels()))

    return await asyncio.gather(*coros)


async def main():
    connector = TCPConnector(enable_cleanup_closed=True, ssl=SSL_CONTEXT)

    async with ClientSession(connector=connector) as session:
        client = DahuaClient(USERNAME, PASSWORD, IP_ADDRESS, PORT, RTSP_PORT, session)

        results = await asyncio.gather(get_device_info(client))
        for res in results:
            for line in res:
                _LOGGER.info(line)

        # Пример генерации RTSP ссылки
        channel = 1
        subtype = 0
        _LOGGER.info(
            "Example rtsp url for channel {}, subtype {}: {}".format(
                channel, subtype, client.get_rtsp_stream_url(channel, subtype)
            )
        )

        # Пример скачивания файла
        start_time = "2025-01-31 16:21:00"
        end_time = "2025-01-31 16:21:10"
        res_path = "/home/shockzor/"
        file_type = "dav"
        name = "{}_{}.{}".format(
            dateutil.parser.parse(start_time).strftime("%Y-%m-%d_%H-%M-%S"),
            dateutil.parser.parse(end_time).strftime("%Y-%m-%d_%H-%M-%S"),
            file_type,
        )
        await asyncio.gather(
            client.fetch_file(
                channel=channel,
                subtype=subtype,
                start_time=urllib.parse.quote(start_time),
                end_time=urllib.parse.quote(end_time),
                type=file_type,
                res_path=os.path.join(res_path, name),
            )
        )


if __name__ == "__main__":

    _LOGGER.info("Start fetching")
    asyncio.run(main())
