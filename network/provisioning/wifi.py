import asyncio
import subprocess

from .config import (
    WIFI_INTERFACE,
    AP_CONNECTION_NAME,
)
from .state import state


def decode_ssid(ssid: str):
    if "\\x" not in ssid:
        return ssid

    try:
        return bytes(
            ssid,
            "ascii"
        ).decode(
            "unicode_escape"
        ).encode(
            "latin1"
        ).decode(
            "utf-8"
        )

    except Exception:
        return ssid
        
def get_wifi_status():
    state_result = subprocess.run(
        [
            "nmcli",
            "-g",
            "GENERAL.STATE",
            "device",
            "show",
            WIFI_INTERFACE,
        ],
        capture_output=True,
        text=True,
    )

    connection_result = subprocess.run(
        [
            "nmcli",
            "-g",
            "GENERAL.CONNECTION",
            "device",
            "show",
            WIFI_INTERFACE,
        ],
        capture_output=True,
        text=True,
    )

    state_text = state_result.stdout.strip()
    connection = connection_result.stdout.strip()

    try:
        wifi_state = int(state_text.split()[0])
    except (ValueError, IndexError):
        wifi_state = 0

    return wifi_state, connection


def scan_wifi_networks():
    try:
        result = subprocess.run(
            ["sudo", "-n", "iw", "dev", WIFI_INTERFACE, "scan"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except subprocess.TimeoutExpired:
        print("WiFi 扫描超时")
        return []

    if result.returncode != 0:
        if result.stderr:
            print(result.stderr)
        return []

    wifi_map = {}
    current_signal = -100.0

    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()

        if line.startswith("BSS "):
            current_signal = -100.0

        elif line.startswith("signal:"):
            try:
                current_signal = float(line.split()[1])
            except (ValueError, IndexError):
                current_signal = -100.0

        elif line.startswith("SSID:"):
            ssid = line[5:].strip()

            ssid = decode_ssid(ssid)

            if ssid and current_signal > wifi_map.get(ssid, -101.0):
                wifi_map[ssid] = current_signal

    return [
        {
            "ssid": ssid,
            "signal": signal
        }
        for ssid, signal in sorted(
            wifi_map.items(),
            key=lambda item: item[1],
            reverse=True
        )
    ]


async def switch_wifi(ssid: str, password: str):
    state.wifi_switching = True
    await asyncio.sleep(2)

    try:
        _, connection = get_wifi_status()
        if connection == AP_CONNECTION_NAME:
            subprocess.run(
                ["sudo", "-n", "nmcli", "connection", "down", AP_CONNECTION_NAME],
                capture_output=True,
                text=True,
            )
            await asyncio.sleep(2)

        result = subprocess.run(
            [
                "sudo", "-n", "nmcli", "device", "wifi", "connect", ssid,
                "password", password, "ifname", WIFI_INTERFACE,
            ],
            capture_output=True,
            text=True,
            timeout=25,
        )
        if result.returncode == 0:
            print(f"{ssid} 连接成功")
        else:
            print(f"{ssid} 连接失败: {result.stderr}")
    except subprocess.TimeoutExpired:
        print(f"连接 {ssid} 超时")
    finally:
        state.wifi_switching = False
