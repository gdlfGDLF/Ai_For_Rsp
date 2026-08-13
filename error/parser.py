def parse_wifi_error(stderr: str):
    text = stderr.lower()

    if "secrets were required" in text:
        return {
            "code": "PASSWORD_ERROR",
            "message": "WiFi 密码错误"
        }

    if "no network with ssid" in text:
        return {
            "code": "SSID_NOT_FOUND",
            "message": "未找到该 WiFi"
        }

    if "timeout" in text or "timed out" in text:
        return {
            "code": "TIMEOUT",
            "message": "WiFi 连接超时"
        }

    return {
        "code": "UNKNOWN_ERROR",
        "message": "WiFi 连接失败"
    }