# GoodLife

GoodLife 是一个运行在 Linux 设备上的 WiFi 配网页面。设备无法连接到可用 WiFi 时，会通过 NetworkManager 启动 `GoodLife` 热点；用户连接热点并访问网页后，可以扫描附近网络并提交 WiFi 密码。

## 系统要求

- Linux（需要 NetworkManager）
- Python 3.10 或更高版本
- 无线网卡接口默认名为 `wlan0`
- 系统命令：`nmcli`、`iw`、`sudo`
- 运行账户需要能够通过 `sudo -n` 非交互执行相关网络命令

## 安装依赖

建议使用虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install fastapi uvicorn python-multipart
```

## 配置

网络配置位于 `network/provisioning/config.py`：

```python
WIFI_INTERFACE = "wlan0"
AP_CONNECTION_NAME = "GoodLife-AP"
AP_SSID = "GoodLife"
AP_PASSWORD = "12345678"
```

部署前请修改默认热点密码。热点密码至少需要 8 个字符。

## 启动

在项目根目录运行：

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

开发时如需自动重载：

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

然后访问：

```text
http://设备IP:8000/
```

## 工作流程

1. 应用启动时创建网络监控任务。
2. 监控任务每 5 秒检查一次 `wlan0`。
3. 连续三次未连接时，应用创建或启动 `GoodLife-AP`。
4. 用户打开配网页面并扫描附近 WiFi。
5. 用户提交 SSID 和密码后，设备关闭热点并连接目标 WiFi。
6. 切换期间暂停热点自动恢复；切换结束后恢复网络监控。

## 接口

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| `GET` | `/` | 返回配网页面 |
| `GET` | `/api/wifi` | 扫描并返回附近 WiFi |
| `POST` | `/api/connect` | 提交 `ssid` 和 `password`，后台切换网络 |
| `GET` | `/static/*` | 前端静态资源 |

## 常见问题

- 扫描结果为空：确认 `iw dev wlan0 scan` 可以正常执行，并检查无线接口名称。
- 无法启动热点：检查 `nmcli`、NetworkManager 和 `sudo -n` 权限。
- POST 接口启动时报错：确认已安装 `python-multipart`。
- 页面能打开但脚本加载失败：必须从项目根目录启动；当前代码也会使用项目绝对路径定位静态文件。

## 安全提示

- 不要在日志中输出用户提交的 WiFi 密码。
- 部署时修改默认热点密码。
- `sudoers` 仅授权应用实际需要的 `nmcli` 和 `iw` 命令，不要授予无范围限制的 sudo 权限。

cd ~/GoodLife 
source .venv/bin/activate

nohup python -u -m uvicorn main:app
--host 0.0.0.0
--port 8000
> goodlife.log 2>&1 &

disown

一些计划
目前已经初步完成 ：
WiFi Provisioning WiFi 配网模块
