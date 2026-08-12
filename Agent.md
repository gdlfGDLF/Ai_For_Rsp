# GoodLife 开发说明

本文档供维护本项目的开发者和代码 Agent 使用。修改代码前先阅读本文件，并保持既有模块边界。

## 代码结构

```text
GoodLife/
├── main.py                         # FastAPI 应用组装和生命周期
├── README.md                       # 安装、配置、启动和使用说明
├── AGENTS.md                       # 代码结构与维护约束
├── network/
│   └── provisioning/
│       ├── __init__.py             # 配网包声明
│       ├── config.py               # 网卡、热点名称、SSID、密码配置
│       ├── state.py                # 进程内共享运行状态
│       ├── wifi.py                 # WiFi 状态、扫描和网络切换
│       ├── ap.py                   # GoodLife 热点检测与启动
│       ├── monitor.py              # 周期性网络监控
│       └── router.py               # 页面路由和配网 API
├── templates/
│   └── provisioning.html           # 配网页面结构
└── static/
    └── js/
        └── provisioning.js         # 页面扫描与连接交互
```

运行生成的 `__pycache__/`、日志和本地虚拟环境不属于业务代码，不应作为模块依赖。

## 模块职责

- `main.py` 只组装应用：创建 FastAPI、注册生命周期、挂载静态目录、引入路由。不要将业务逻辑放回 `main.py`。
- `config.py` 只保存配网相关常量。新增可配置项优先集中于此。
- `state.py` 保存多个模块需要共享的进程内状态。目前 `wifi_switching` 用于防止主动切换 WiFi 时监控任务重新拉起热点。
- `wifi.py` 负责普通 WiFi：读取连接状态、调用 `iw` 扫描、调用 `nmcli` 连接目标网络。
- `ap.py` 只负责 GoodLife 热点，不处理 HTTP 请求。
- `monitor.py` 负责轮询和恢复策略，不包含路由代码。
- `router.py` 负责参数接收和响应，具体网络操作应调用业务模块。
- `templates/` 保存 HTML，`static/` 保存 JavaScript、CSS、图片等前端资源。不要把大段 HTML 或 JavaScript 写回 Python 字符串。

## 依赖方向

```text
main
├── monitor
└── router

monitor ──> ap ──> wifi
monitor ─────────> wifi
router ──────────> wifi
wifi ──> config, state
ap ────> config
```

避免引入反向依赖。例如 `wifi.py` 不应导入 `router.py` 或 `monitor.py`，否则容易形成循环导入。

## 修改约束

- 保持路由兼容：`/`、`/api/wifi` 和 `/api/connect` 未经明确需求不要变更。
- 所有外部命令使用参数列表调用 `subprocess.run`，不要拼接 shell 字符串。
- 用户输入的 SSID 和密码不得写入日志；SSID 如需记录，应考虑日志暴露风险。
- 网络命令必须设置合理的超时，并处理 `subprocess.TimeoutExpired`。
- 修改共享切换状态时使用 `try/finally`，确保异常后状态能够恢复。
- 网络监控必须在 FastAPI 关闭时取消，不得留下后台任务。
- 新增文本文件统一使用 UTF-8，避免中文乱码。
- 前端接口发生变化时，同步修改 `templates/provisioning.html`、`static/js/provisioning.js` 和 `README.md`。

## 验证方式

至少执行 Python 语法检查：

```bash
python -m compileall -q main.py network
```

安装依赖后检查应用可导入：

```bash
python -c "from main import app; print(app.title)"
```

在目标 Linux 设备上继续验证：

1. `GET /` 能加载 HTML 和 JavaScript。
2. `GET /api/wifi` 返回按信号强度降序排列的网络。
3. `POST /api/connect` 能接收表单并启动后台切换。
4. WiFi 断开约 15 秒后热点能够自动恢复。
5. 应用退出后网络监控任务正常取消。

开发机若没有 `nmcli`、`iw` 或无线网卡，只做导入和语法检查，不要把平台缺失误判为 Python 代码错误。

## 启动命令

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

依赖安装及系统权限配置参见 `README.md`。
