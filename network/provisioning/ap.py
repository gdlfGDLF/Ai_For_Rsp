import subprocess

from .config import AP_CONNECTION_NAME, AP_PASSWORD, AP_SSID, WIFI_INTERFACE
from .wifi import get_wifi_status


def goodlife_ap_exists():
    result = subprocess.run(
        ["nmcli", "-t", "-f", "NAME", "connection", "show"],
        capture_output=True,
        text=True,
    )
    return AP_CONNECTION_NAME in result.stdout.splitlines()


def start_goodlife_ap():
    wifi_state, connection = get_wifi_status()
    if wifi_state == 100 and connection == AP_CONNECTION_NAME:
        return

    ap_exists = goodlife_ap_exists()
    if ap_exists:
        command = ["sudo", "-n", "nmcli", "connection", "up", AP_CONNECTION_NAME]
    else:
        command = [
            "sudo", "-n", "nmcli", "device", "wifi", "hotspot",
            "ifname", WIFI_INTERFACE, "con-name", AP_CONNECTION_NAME,
            "ssid", AP_SSID, "password", AP_PASSWORD,
        ]

    result = subprocess.run(command, capture_output=True, text=True)
    if not ap_exists and result.returncode == 0:
        subprocess.run(
            [
                "sudo", "-n", "nmcli", "connection", "modify",
                AP_CONNECTION_NAME, "connection.autoconnect", "no",
            ],
            capture_output=True,
            text=True,
        )
    if result.returncode != 0:
        print(f"GoodLife AP 启动失败: {result.stderr}")
