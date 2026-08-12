import asyncio

from .ap import start_goodlife_ap
from .state import state
from .wifi import get_wifi_status


async def network_watch():
    disconnected_count = 0
    print("GoodLife 网络监控已启动")

    while True:
        if state.wifi_switching:
            disconnected_count = 0
        else:
            wifi_state, _ = get_wifi_status()
            if wifi_state == 100:
                disconnected_count = 0
            else:
                disconnected_count += 1
                if disconnected_count >= 3:
                    start_goodlife_ap()
                    disconnected_count = 0

        await asyncio.sleep(5)
