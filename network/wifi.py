import asyncio
import subprocess

from .settings import (
    WIFI_INTERFACE,
    AP_CONNECTION_NAME,
)
from .state import state, NetworkMode

from error.parser import parse_wifi_error


TEMP_CONNECTION_NAME = "GoodLife-WiFi-Test"


def decode_ssid(ssid: str):
    if "\\x" not in ssid:
        return ssid

    try:
        return (
            bytes(ssid, "ascii")
            .decode("unicode_escape")
            .encode("latin1")
            .decode("utf-8")
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
            [
                "sudo",
                "-n",
                "iw",
                "dev",
                WIFI_INTERFACE,
                "scan",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )

    except subprocess.TimeoutExpired:
        print("WiFi 扫描超时")
        return []

    if result.returncode != 0:
        if result.stderr:
            print("WiFi 扫描失败:", result.stderr)

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

            if not ssid:
                continue

            old_signal = wifi_map.get(ssid, -101.0)

            if current_signal > old_signal:
                wifi_map[ssid] = current_signal

    wifi_list = [
        {
            "ssid": ssid,
            "signal": signal,
        }
        for ssid, signal in wifi_map.items()
    ]

    wifi_list.sort(
        key=lambda item: item["signal"],
        reverse=True,
    )

    return wifi_list


def create_temp_connection(ssid: str, password: str):
    # 清理上一次遗留的测试连接
    delete_temp_connection()

    # 创建临时 WiFi profile
    result = subprocess.run(
        [
            "sudo",
            "-n",
            "nmcli",
            "connection",
            "add",
            "type",
            "wifi",
            "ifname",
            WIFI_INTERFACE,
            "con-name",
            TEMP_CONNECTION_NAME,
            "ssid",
            ssid,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return False, result.stderr

    # 设置 WiFi 密码
    result = subprocess.run(
        [
            "sudo",
            "-n",
            "nmcli",
            "connection",
            "modify",
            TEMP_CONNECTION_NAME,
            "wifi-sec.key-mgmt",
            "wpa-psk",
            "wifi-sec.psk",
            password,
            "connection.autoconnect",
            "no",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        delete_temp_connection()
        return False, result.stderr

    return True, None


def connect_temp_connection():
    return subprocess.run(
        [
            "sudo",
            "-n",
            "nmcli",
            "connection",
            "up",
            TEMP_CONNECTION_NAME,
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )


def delete_temp_connection():
    subprocess.run(
        [
            "sudo",
            "-n",
            "nmcli",
            "connection",
            "delete",
            TEMP_CONNECTION_NAME,
        ],
        capture_output=True,
        text=True,
    )


def restore_ap():
    result = subprocess.run(
        [
            "sudo",
            "-n",
            "nmcli",
            "connection",
            "up",
            AP_CONNECTION_NAME,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(
            "恢复 GoodLife AP 失败:",
            result.stderr
        )

    return result.returncode == 0


async def switch_wifi(ssid: str, password: str):
    state.wifi_switching = True

    # 开始新的连接流程，旧 status_info 自动清空
    state.set_state(
        NetworkMode.CONNECTING,
        ssid
    )

    try:
        # --------------------------------------------------
        # 1. 创建临时 WiFi profile
        # --------------------------------------------------

        ok, error = create_temp_connection(
            ssid,
            password
        )

        if not ok:
            err_info = {
                "code": "CREATE_PROFILE_FAILED",
                "message": error,
            }

            # AP 此时还没有关闭
            state.set_state(
                NetworkMode.ONAP,
                ssid,
                err_info
            )
            return

        # --------------------------------------------------
        # 2. 关闭 GoodLife AP
        # --------------------------------------------------

        _, connection = get_wifi_status()

        if connection == AP_CONNECTION_NAME:
            subprocess.run(
                [
                    "sudo",
                    "-n",
                    "nmcli",
                    "connection",
                    "down",
                    AP_CONNECTION_NAME,
                ],
                capture_output=True,
                text=True,
            )

            await asyncio.sleep(1)

        # --------------------------------------------------
        # 3. 尝试连接用户 WiFi
        # --------------------------------------------------

        result = connect_temp_connection()

        # --------------------------------------------------
        # 4. 连接成功
        # --------------------------------------------------

        if result.returncode == 0:
            print(f"{ssid} 连接成功")

            # 测试成功，以后允许自动连接
            subprocess.run(
                [
                    "sudo",
                    "-n",
                    "nmcli",
                    "connection",
                    "modify",
                    TEMP_CONNECTION_NAME,
                    "connection.autoconnect",
                    "yes",
                ],
                capture_output=True,
                text=True,
            )

            state.set_state(
                NetworkMode.ONLINE,
                ssid
            )

            return

        # --------------------------------------------------
        # 5. 连接失败
        # --------------------------------------------------

        print(
            f"{ssid} 连接失败:",
            result.stderr
        )

        err_info = parse_wifi_error(
            result.stderr
        )

        delete_temp_connection()

        # 恢复配网 AP
        restore_ap()

        # 当前已经回到 AP，同时保存刚才失败原因
        state.set_state(
            NetworkMode.ONAP,
            ssid,
            err_info
        )

    # ------------------------------------------------------
    # 6. 连接超时
    # ------------------------------------------------------

    except subprocess.TimeoutExpired:
        print(f"连接 {ssid} 超时")

        err_info = {
            "code": "TIMEOUT",
            "message": "连接超时",
        }

        delete_temp_connection()
        restore_ap()

        state.set_state(
            NetworkMode.ONAP,
            ssid,
            err_info
        )

    # ------------------------------------------------------
    # 7. 未知异常
    # ------------------------------------------------------

    except Exception as error:
        print(
            "WiFi切换异常:",
            error
        )

        err_info = {
            "code": "INTERNAL_ERROR",
            "message": str(error),
        }

        delete_temp_connection()
        restore_ap()

        state.set_state(
            NetworkMode.ONAP,
            ssid,
            err_info
        )

    finally:
        # finally只负责解除“正在主动切网”标记
        # 绝对不要在这里修改 NetworkMode
        state.wifi_switching = False