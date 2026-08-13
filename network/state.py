class ProvisioningState:
    def __init__(self):
        self.wifi_switching = False
        # 当前配网状态
        self.wifi_status = {
            "status": "idle",
            "ssid": None,
            "error": None
        }
           
state = ProvisioningState()

