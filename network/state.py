from enum import Enum


class NetworkMode(Enum):
    INIT = 0          # 程序刚启动，网络状态未知
    ONLINE = 1        # 已连接外部 WiFi
    ONAP = 2          # GoodLife AP 配网模式
    CONNECTING = 3    # 正在切换/连接目标 WiFi


class ProvisioningState:
    def __init__(self):
        self.wifi_switching = False

        self.mode = NetworkMode.INIT
        self.ssid = None
        self.status_info = None

    def set_state(
        self,
        mode,
        ssid=None,
        status_info=None
    ):
        # 每次状态转换整体刷新，避免残留旧状态
        self.mode = mode
        self.ssid = ssid
        self.status_info = status_info

    def to_dict(self):
        return {
            "status": self.mode.name,
            "ssid": self.ssid,
            "status_info": self.status_info
        }


state = ProvisioningState()