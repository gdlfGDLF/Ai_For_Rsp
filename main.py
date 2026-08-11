import asyncio
import subprocess
from contextlib import asynccontextmanager

from fastapi import FastAPI, Form, BackgroundTasks
from fastapi.responses import HTMLResponse


# ============================================================
# 配置
# ============================================================

WIFI_INTERFACE = "wlan0"

AP_CONNECTION_NAME = "GoodLife-AP"
AP_SSID = "GoodLife"
AP_PASSWORD = "12345678"

wifi_switching = False

# ============================================================
# 获取 wlan0 当前连接
# ============================================================

def get_wifi_status():
    state_result = subprocess.run(
        [
            "nmcli",
            "-g",
            "GENERAL.STATE",
            "device",
            "show",
            WIFI_INTERFACE
        ],
        capture_output=True,
        text=True
    )

    connection_result = subprocess.run(
        [
            "nmcli",
            "-g",
            "GENERAL.CONNECTION",
            "device",
            "show",
            WIFI_INTERFACE
        ],
        capture_output=True,
        text=True
    )

    state_text = state_result.stdout.strip()
    connection = connection_result.stdout.strip()

    try:
        state = int(state_text.split()[0])
    except (ValueError, IndexError):
        state = 0

    return state, connection


# ============================================================
# 判断 GoodLife AP 配置是否存在
# ============================================================

def goodlife_ap_exists():
    result = subprocess.run(
        [
            "nmcli",
            "-t",
            "-f",
            "NAME",
            "connection",
            "show"
        ],
        capture_output=True,
        text=True
    )

    connections = result.stdout.splitlines()

    return AP_CONNECTION_NAME in connections


# ============================================================
# 启动 GoodLife AP
# ============================================================

def start_goodlife_ap():
    state, connection = get_wifi_status()

    if state == 100 and connection == AP_CONNECTION_NAME:
        print("GoodLife AP 已经启动")
        return

    print()
    print("==============================")
    print("准备启动 GoodLife AP")

    if goodlife_ap_exists():
        print("GoodLife-AP 配置已存在，直接启动")

        result = subprocess.run(
            [
                "sudo",
                "-n",
                "nmcli",
                "connection",
                "up",
                AP_CONNECTION_NAME
            ],
            capture_output=True,
            text=True
        )

    else:
        print("第一次创建 GoodLife AP")

        result = subprocess.run(
            [
                "sudo",
                "-n",
                "nmcli",
                "device",
                "wifi",
                "hotspot",
                "ifname",
                WIFI_INTERFACE,
                "con-name",
                AP_CONNECTION_NAME,
                "ssid",
                AP_SSID,
                "password",
                AP_PASSWORD
            ],
            capture_output=True,
            text=True
        )

        subprocess.run(
            [
                "sudo",
                "-n",
                "nmcli",
                "connection",
                "modify",
                AP_CONNECTION_NAME,
                "connection.autoconnect",
                "no"
            ],
            capture_output=True,
            text=True
        )

    print("AP stdout:")
    print(result.stdout)

    print("AP stderr:")
    print(result.stderr)

    print("AP returncode:", result.returncode)
    print("==============================")


# ============================================================
# 网络持续监控
# ============================================================

async def network_watch():
    global wifi_switching

    disconnected_count = 0

    print("GoodLife 网络监控启动")

    while True:

        # 正在进行配网切换时，不允许监控线程重新拉起 AP
        if wifi_switching:
            disconnected_count = 0
            print("正在切换 WiFi，暂停 AP 兜底")

            await asyncio.sleep(5)
            continue

        state, connection = get_wifi_status()

        print(
            f"wlan0 state={state}, connection={connection}"
        )

        # 已经正常连接
        if state == 100:

            disconnected_count = 0

        else:

            disconnected_count += 1

            print(
                "WiFi 尚未连接成功:",
                disconnected_count,
                "/ 3"
            )

            if disconnected_count >= 3:

                print("连续 15 秒没有可用 WiFi")

                start_goodlife_ap()

                disconnected_count = 0

        await asyncio.sleep(5)
        
# ============================================================
# FastAPI 生命周期
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(network_watch())

    try:
        yield
    finally:
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

app = FastAPI(lifespan=lifespan)


# ============================================================
# HTML
# ============================================================

HTML = """
<!DOCTYPE html>
<html>

<head>
    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>GoodLife 配网</title>
</head>

<body>

<h2>GoodLife WiFi 配置</h2>

<button onclick="scanWifi()">扫描 WiFi</button>

<br><br>

<select id="wifi">
    <option value="">请先扫描</option>
</select>

<br><br>

<input
    id="password"
    type="password"
    placeholder="WiFi 密码"
>

<br><br>

<button onclick="connectWifi()">连接</button>

<p id="status"></p>


<script>

async function scanWifi() {
    const status = document.getElementById("status");
    const select = document.getElementById("wifi");

    status.innerText = "正在扫描...";

    try {
        const response = await fetch("/api/wifi");
        const wifiList = await response.json();

        select.innerHTML = "";

        if (wifiList.length === 0) {
            const option = document.createElement("option");

            option.value = "";
            option.text = "没有扫描到 WiFi";

            select.appendChild(option);

            status.innerText = "没有扫描到 WiFi";

            return;
        }

        wifiList.forEach(wifi => {
            const option = document.createElement("option");

            option.value = wifi.ssid;

            option.text =
                wifi.ssid +
                " (" +
                wifi.signal +
                " dBm)";

            select.appendChild(option);
        });

        status.innerText = "扫描完成";
    }
    catch (error) {
        console.log(error);

        status.innerText = "扫描失败";
    }
}


async function connectWifi() {
    const status = document.getElementById("status");

    const ssid =
        document.getElementById("wifi").value;

    const password =
        document.getElementById("password").value;

    if (!ssid) {
        status.innerText = "请选择 WiFi";

        return;
    }

    const form = new FormData();

    form.append("ssid", ssid);
    form.append("password", password);

    status.innerText = "正在连接...";

    try {
        const response = await fetch(
            "/api/connect",
            {
                method: "POST",
                body: form
            }
        );

        const result = await response.json();

        status.innerText = result.message;
    }
    catch (error) {
        status.innerText = "设备正在切换 WiFi...";
    }
}

</script>

</body>

</html>
"""


# ============================================================
# 首页
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML


# ============================================================
# 扫描 WiFi
# ============================================================

@app.get("/api/wifi")
async def scan_wifi():
    print()
    print("开始扫描 WiFi...")

    try:
        result = subprocess.run(
            [
                "sudo",
                "-n",
                "iw",
                "dev",
                WIFI_INTERFACE,
                "scan"
            ],
            capture_output=True,
            text=True,
            timeout=15
        )

    except subprocess.TimeoutExpired:
        print("WiFi 扫描超时")
        return []

    print("iw returncode:", result.returncode)

    if result.stderr:
        print("iw stderr:")
        print(result.stderr)

    if result.returncode != 0:
        return []

    wifi_map = {}

    current_ssid = None
    current_signal = -100.0

    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()

        # 新的 AP
        if line.startswith("BSS "):
            current_ssid = None
            current_signal = -100.0
            continue

        # signal: -45.00 dBm
        if line.startswith("signal:"):
            parts = line.split()

            if len(parts) >= 2:
                try:
                    current_signal = float(parts[1])
                except ValueError:
                    current_signal = -100.0

            continue

        # SSID: xxx
        if line.startswith("SSID:"):
            current_ssid = line[5:].strip()

            if not current_ssid:
                continue

            # 同一个 SSID 可能有多个 AP
            # 只保留信号最强的
            if current_ssid not in wifi_map:
                wifi_map[current_ssid] = current_signal

            elif current_signal > wifi_map[current_ssid]:
                wifi_map[current_ssid] = current_signal

    wifi_list = []

    for ssid, signal in wifi_map.items():
        wifi_list.append(
            {
                "ssid": ssid,
                "signal": signal
            }
        )

    # 信号强的放前面
    wifi_list.sort(
        key=lambda wifi: wifi["signal"],
        reverse=True
    )

    print("扫描结果:")

    for wifi in wifi_list:
        print(
            wifi["ssid"],
            wifi["signal"],
            "dBm"
        )

    return wifi_list


# ============================================================
# 切换 WiFi
# ============================================================

async def switch_wifi(ssid: str, password: str):
    global wifi_switching

    # 标记：现在正在主动切换 WiFi
    wifi_switching = True

    # 先让 HTTP 响应发给浏览器
    await asyncio.sleep(2)

    print()
    print("==============================")
    print(f"准备连接 WiFi: {ssid}")

    try:

        # --------------------------------
        # 1. 如果当前是 GoodLife AP
        #    先关闭 AP
        # --------------------------------

        state, connection = get_wifi_status()

        if connection == AP_CONNECTION_NAME:

            print("关闭 GoodLife AP...")

            down_result = subprocess.run(
                [
                    "sudo",
                    "-n",
                    "nmcli",
                    "connection",
                    "down",
                    AP_CONNECTION_NAME
                ],
                capture_output=True,
                text=True
            )

            print("关闭 AP stdout:")
            print(down_result.stdout)

            print("关闭 AP stderr:")
            print(down_result.stderr)

            # 等 wlan0 从 AP 模式退出来
            await asyncio.sleep(2)

        # --------------------------------
        # 2. 连接用户选择的 WiFi
        # --------------------------------

        print(f"开始连接目标 WiFi: {ssid}")

        result = subprocess.run(
            [
                "sudo",
                "-n",
                "nmcli",
                "device",
                "wifi",
                "connect",
                ssid,
                "password",
                password,
                "ifname",
                WIFI_INTERFACE
            ],
            capture_output=True,
            text=True,
            timeout=25
        )

        print("连接 stdout:")
        print(result.stdout)

        print("连接 stderr:")
        print(result.stderr)

        print(
            "连接 returncode:",
            result.returncode
        )

        if result.returncode == 0:

            print(f"{ssid} 连接成功")

        else:

            print(f"{ssid} 连接失败")
            print("稍后自动恢复 GoodLife AP")

    except subprocess.TimeoutExpired:

        print("连接 WiFi 超时")
        print("稍后自动恢复 GoodLife AP")

    finally:

        # 无论成功失败，都恢复网络监控
        wifi_switching = False

        print("恢复网络监控")
        print("==============================")
        print()


# ============================================================
# 网页连接接口
# ============================================================

@app.post("/api/connect")
async def connect_wifi(
    background_tasks: BackgroundTasks,
    ssid: str = Form(...),
    password: str = Form(...)
):
    background_tasks.add_task(
        switch_wifi,
        ssid,
        password
    )

    return {
        "message":
            f"正在连接 {ssid}，设备网络即将切换..."
    }