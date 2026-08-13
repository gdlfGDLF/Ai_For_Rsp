apt:
- network-manager
- iptables

配置:
- /etc/NetworkManager/dnsmasq-shared.d/goodlife.conf

运行:
uvicorn main:app --host 0.0.0.0 --port 8000