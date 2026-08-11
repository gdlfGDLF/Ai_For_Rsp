import subprocess
import asyncio

from fastapi import FastAPI, Form, BackgroundTasks
from fastapi.responses import HTMLResponse


app = FastAPI()


HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>GoodLife 配网</title>
</head>

<body>

<h2>GoodLife WiFi 配置</h2>

<button onclick="scanWifi()">扫描 WiFi</button>

<br><br>

<select id="wifi">
    <option>请先扫描</option>
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

    document.getElementById("status").innerText =
        "正在扫描...";

    try {

        const response = await fetch("/api/wifi");

        const wifiList = await response.json();

        const select =
            document.getElementById("wifi");

        select.innerHTML = "";

        if (wifiList.length === 0) {

            const option =
                document.createElement("option");

            option.text = "没有扫描到 WiFi";

            select.appendChild(option);

            document.getElementById("status").innerText =
                "没有扫描到 WiFi";

            return;
        }

        wifiList.forEach(wifi => {

            const option =
                document.createElement("option");

            option.value = wifi.ssid;

            option.text =
                wifi.ssid +
                " (" +
                wifi.signal +
                " dBm)";

            select.appendChild(option);
        });

        document.getElementById("status").innerText =
            "扫描完成";

    } catch (error) {

        document.getElementById("status").innerText =
            "扫描失败";
    }
}


async function connectWifi() {

    const ssid =
        document.getElementById("wifi").value;

    const password =
        document.getElementById("password").value;

    if (!ssid) {
        document.getElementById("status").innerText =
            "请选择 WiFi";
        return;
    }

    const form = new FormData();

    form.append("ssid", ssid);
    form.append("password", password);

    document.getElementById("status").innerText =
        "正在提交连接请求...";

    try {

        const response =
            await fetch(
                "/api/connect",
                {
                    method: "POST",
                    body: form
                }
            );

        const result =
            await response.json();

        document.getElementById("status").innerText =
            result.message;

    } catch (error) {

        document.getElementById("status").innerText =
            "连接请求发送失败";
    }
}

</script>

</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML


# ============================================================
# 扫描 WiFi
# ============================================================

@app.get("/api/wifi")
async def scan_wifi():

    print("开始扫描 WiFi...")

    try:

        result = subprocess.run(
        [
        "sudo",
        "-n",
        "iw",
        "dev",
        "wlan0",
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


    wifi_list = []

    seen = set()

    current = None


    for line in result.stdout.splitlines():

        line = line.strip()


        # 出现一个新的 AP
        if line.startswith("BSS "):

            current = {
                "ssid": "",
                "signal": "",
                "security": "UNKNOWN"
            }

            continue


        if current is None:
            continue


        # signal: -45.00 dBm
        if line.startswith("signal:"):

            parts = line.split()

            if len(parts) >= 2:
                current["signal"] = parts[1]

            continue


        # 简单判断加密
        if line.startswith("RSN:"):
            current["security"] = "WPA2/WPA3"

        elif line.startswith("WPA:"):
            current["security"] = "WPA"


        # SSID: xxxxx
        if line.startswith("SSID:"):

            ssid = line[5:].strip()


            # 隐藏 WiFi / 空 SSID
            if not ssid:
                current = None
                continue


            # 去重
            if ssid in seen:
                current = None
                continue


            seen.add(ssid)

            current["ssid"] = ssid


            if not current["signal"]:
                current["signal"] = "0"


            wifi_list.append(current)

            current = None


    # 信号从强到弱排序
    try:
        wifi_list.sort(
            key=lambda wifi: float(wifi["signal"]),
            reverse=True
        )
    except ValueError:
        pass


    print("扫描结果:")

    for wifi in wifi_list:
        print(
            wifi["ssid"],
            wifi["signal"],
            wifi["security"]
        )


    return wifi_list


# ============================================================
# 30 秒后恢复 iPhone
# ============================================================

async def rollback_wifi():

    print("已启动 WiFi 回滚保护")

    await asyncio.sleep(30)

    print("30 秒到，尝试恢复 iPhone WiFi...")


    result = subprocess.run(
        [
            "sudo",
            "-n",
            "nmcli",
            "connection",
            "up",
            "netplan-wlan0-iPhone"
        ],
        capture_output=True,
        text=True
    )


    print("回滚 stdout:")
    print(result.stdout)

    print("回滚 stderr:")
    print(result.stderr)

    print("回滚 returncode:")
    print(result.returncode)


# ============================================================
# 切换 WiFi
# ============================================================

async def switch_wifi(
    ssid: str,
    password: str
):

    # 给 HTTP 响应一点时间先发出去
    await asyncio.sleep(2)


    print()
    print("==============================")

    print(f"准备连接 WiFi: {ssid}")


    # 启动保护任务
    # 无论切换成功还是失败，
    # 30 秒后都会重新连接 iPhone
    asyncio.create_task(
        rollback_wifi()
    )


    try:

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
                "wlan0"
            ],
            capture_output=True,
            text=True,
            timeout=20
        )


        print("连接 stdout:")
        print(result.stdout)

        print("连接 stderr:")
        print(result.stderr)

        print("连接 returncode:")
        print(result.returncode)


        if result.returncode == 0:

            print(f"WiFi {ssid} 连接成功")

        else:

            print(f"WiFi {ssid} 连接失败")


    except subprocess.TimeoutExpired:

        print("连接 WiFi 超时")


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
        f"正在连接 {ssid}。测试模式：30 秒后会自动恢复 iPhone WiFi。"
    }