import asyncio

from .ap import start_goodlife_ap
from .state import state,NetworkMode
from .wifi import get_wifi_status
from .firewall import(
    add_http_redirect,
    remove_http_redirect,
)
from .settings import (
    AP_CONNECTION_NAME,
)
async def network_watch():
    disconnected_count = 0

    print("GoodLife 网络监控已启动")

    while True:
        if state.wifi_switching:
            disconnected_count = 0

        else:
            wifi_state, connection = get_wifi_status()

            if wifi_state == 100:
                disconnected_count = 0

                # 当前连接的是 GoodLife AP
                if connection == AP_CONNECTION_NAME:
                    add_http_redirect()

                    # 如果已经是 ONAP，不要重新 set_state
                    # 避免把上一次连接失败的 status_info 清掉
                    if state.mode != NetworkMode.ONAP:
                        state.set_state(NetworkMode.ONAP)

                # 当前连接的是正常 WiFi
                else:
                    state.set_state(
                        NetworkMode.ONLINE,
                        connection
                    )

                    remove_http_redirect()

            else:
                disconnected_count += 1

                if disconnected_count >= 3:
                    start_goodlife_ap()
                    add_http_redirect()

                    state.set_state(NetworkMode.ONAP)

                    disconnected_count = 0

        await asyncio.sleep(5)
