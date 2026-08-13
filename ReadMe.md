# GoodLife

GoodLife 是一个基于 FastAPI 的 Linux 设备 Wi-Fi 配网服务。设备断网后会启动临时热点，用户通过配网页面扫描并连接目标 Wi-Fi。

## 项目结构

```text
GoodLife/
├── main.py                       # FastAPI 入口、静态资源挂载、网络监控生命周期
├── network/
│   ├── __init__.py              # 网络包标识
│   ├── ap.py                    # GoodLife 临时热点的检测、创建和启动
│   ├── config.py                # 网卡、热点名称、SSID 和密码等网络常量
│   ├── monitor.py               # 后台检测联网状态，连续断网时恢复热点
│   ├── state.py                 # 配网过程的共享运行状态
│   ├── wifi.py                  # Wi-Fi 扫描、连接、失败回滚和配置保存
│   └── provisioning/
│       ├── __init__.py          # 配网 Web 子包
│       ├── router.py            # 配网页面与 Wi-Fi API 路由
│       └── captive_portal.py    # dnsmasq 启停支持（当前尚未接入主流程）
├── storage/
│   ├── config_manager.py        # JSON 设备配置的读写封装
│   └── device_config.json       # 设备运行配置
├── error/
│   └── parser.py                # 将 nmcli 错误转换为前端可用错误信息
├── templates/
│   └── provisioning.html        # 配网页面
├── static/
│   ├── css/provisioning.css     # 页面样式
│   └── js/provisioning.js       # 扫描、连接及状态轮询逻辑
└── Config/provisioning.json     # 预留的配网配置文件
```

## 模块边界

- `network/` 是底层网络能力，不依赖 FastAPI。
- `network/provisioning/` 是 Web 接入层，将底层能力暴露为页面和 API。
- `main.py` 只负责组装应用以及启动、停止后台监控任务。

## 运行环境

项目面向使用 NetworkManager 的 Linux 设备。依赖分为两类：

- `requirements-apt.txt`：Debian/Ubuntu 系统软件，包括 `network-manager`（提供 `nmcli`）、`iw`、`iptables`、`sudo` 和 `dnsmasq`。
- `requirements.txt`：Python 软件包，包括 FastAPI、Uvicorn 和表单解析支持。

先安装系统依赖：

```bash
sudo apt-get update
sudo xargs -a requirements-apt.txt apt-get install -y
sudo systemctl enable --now NetworkManager
```

其中 `dnsmasq` 和 `iptables` 用于后续 captive portal/流量转发；当前主流程尚未启用 captive portal 时，它们不是启动 FastAPI 服务的硬性依赖。

建议先创建虚拟环境并安装依赖：

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

示例启动命令：

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 后续建议

1. 将热点密码等环境相关配置移至环境变量或独立配置文件，避免写死在源码中。
2. 用 `logging` 替代 `print`，并统一处理子进程失败和超时。
3. 为外部命令增加一层适配器，以便在非 Linux 环境中编写单元测试。
4. 明确 `captive_portal.py` 是否启用；若长期不用，可删除以免产生错误预期。
5. 补充锁或状态管理机制，避免监控任务与用户发起的 Wi-Fi 切换同时操作 NetworkManager。
