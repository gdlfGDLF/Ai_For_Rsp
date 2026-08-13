"""Manage the optional dnsmasq service used by the captive portal."""

import subprocess


def start_dnsmasq():
    subprocess.run(
        ["sudo", "-n", "systemctl", "start", "dnsmasq"],
        check=True,
    )


def stop_dnsmasq():
    subprocess.run(
        ["sudo", "-n", "systemctl", "stop", "dnsmasq"],
        check=False,
    )
