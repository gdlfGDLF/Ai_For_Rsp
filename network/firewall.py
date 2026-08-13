import subprocess

from .settings import WIFI_INTERFACE


HTTP_PORT = "80"
FASTAPI_PORT = "8000"


def redirect_exists():
    result = subprocess.run(
        [
            "sudo", "-n",
            "iptables",
            "-t", "nat",
            "-C", "PREROUTING",
            "-i", WIFI_INTERFACE,
            "-p", "tcp",
            "--dport", HTTP_PORT,
            "-j", "REDIRECT",
            "--to-ports", FASTAPI_PORT,
        ],
        capture_output=True,
        text=True,
    )

    return result.returncode == 0


def add_http_redirect():
    if redirect_exists():
        return True

    result = subprocess.run(
        [
            "sudo", "-n",
            "iptables",
            "-t", "nat",
            "-A", "PREROUTING",
            "-i", WIFI_INTERFACE,
            "-p", "tcp",
            "--dport", HTTP_PORT,
            "-j", "REDIRECT",
            "--to-ports", FASTAPI_PORT,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(
            "HTTP 重定向规则添加失败:",
            result.stderr
        )
        return False

    return True


def remove_http_redirect():
    if not redirect_exists():
        return True

    result = subprocess.run(
        [
            "sudo", "-n",
            "iptables",
            "-t", "nat",
            "-D", "PREROUTING",
            "-i", WIFI_INTERFACE,
            "-p", "tcp",
            "--dport", HTTP_PORT,
            "-j", "REDIRECT",
            "--to-ports", FASTAPI_PORT,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(
            "HTTP 重定向规则删除失败:",
            result.stderr
        )
        return False

    return True