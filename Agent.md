# GoodLife 项目指南

## 结构与职责

- `main.py`：应用组装入口，不放置具体网络操作。
- `network/ap.py`：仅负责 GoodLife 热点生命周期。
- `network/wifi.py`：负责 Wi-Fi 扫描、切换与失败恢复。
- `network/monitor.py`：负责周期性网络检查，不定义 HTTP 接口。
- `network/state.py`：保存配网运行状态；修改状态字段时同步检查 API 和前端。
- `network/config.py`：集中保存网络常量。
- `network/provisioning/router.py`：FastAPI 配网路由；通过 `network.*` 使用底层能力。
- `network/provisioning/captive_portal.py`：可选 captive portal 支持。
- `storage/`：持久化配置读写。
- `error/`：外部命令错误解析。
- `templates/`、`static/`：配网页面资源。

## 修改约定

- 底层网络模块使用 `network.*` 包内导入；应用入口使用绝对导入。
- 不要让 `network/ap.py`、`network/wifi.py` 等底层模块依赖 FastAPI。
- 所有 `subprocess.run` 调用应明确设置超时（适用时）、捕获输出并检查返回码。
- 修改 API 返回结构时，同步检查 `static/js/provisioning.js`。
- 修改模板或静态资源路径时，同步检查 `main.py` 和 `network/provisioning/router.py`。
- 不提交日志、`__pycache__` 或设备上的敏感 Wi-Fi 凭据。

## 验证

至少执行：

```bash
python -m compileall main.py network storage error
python -c "import main"
```

涉及真实联网流程的改动还应在配有 NetworkManager、`nmcli` 和 `iw` 的 Linux 设备上验证扫描、热点恢复、连接成功及连接失败回滚。
