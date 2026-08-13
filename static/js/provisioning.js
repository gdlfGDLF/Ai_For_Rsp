async function loadStatus() {
    try {
        const response = await fetch("/api/status");
        const status = await response.json();

        updateStatus(status);
    }
    catch (error) {
        console.log("获取状态失败:", error);
    }
}


function updateStatus(status) {
    const text = document.getElementById("status");

    switch (status.status) {

        case "INIT":
            text.innerText = "正在初始化网络...";
            break;


        case "CONNECTING":
            if (status.ssid) {
                text.innerText =
                    "正在连接 " + status.ssid + "...";
            }
            else {
                text.innerText = "正在连接 WiFi...";
            }
            break;


        case "ONLINE":
            if (status.ssid) {
                text.innerText =
                    "已连接 " + status.ssid;
            }
            else {
                text.innerText = "连接成功";
            }
            break;


        case "ONAP":

            // ONAP + status_info
            // 表示连接失败后已经恢复到 GoodLife AP
            if (status.status_info) {

                const message =
                    status.status_info.message ||
                    status.status_info.code ||
                    "未知错误";

                text.innerText =
                    "连接失败: " + message;
            }
            else {
                // 正常处于配网模式
                text.innerText = "请选择 WiFi";
            }

            break;


        default:
            text.innerText = "请选择 WiFi";
            break;
    }
}


// 页面打开时读取状态
window.addEventListener(
    "load",
    () => {
        loadStatus();

        // 周期查询设备状态
        setInterval(
            loadStatus,
            1500
        );
    }
);


async function scanWifi() {
    const text =
        document.getElementById("status");

    const select =
        document.getElementById("wifi");

    text.innerText = "正在扫描...";

    try {
        const response =
            await fetch("/api/wifi");

        const wifiList =
            await response.json();

        select.innerHTML = "";

        if (wifiList.length === 0) {
            const option =
                document.createElement("option");

            option.value = "";
            option.text = "没有扫描到 WiFi";

            select.appendChild(option);

            text.innerText = "没有扫描到 WiFi";

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

        text.innerText = "扫描完成";
    }
    catch (error) {
        console.log(
            "扫描失败:",
            error
        );

        text.innerText = "扫描失败";
    }
}


async function connectWifi() {
    const ssid =
        document.getElementById("wifi").value;

    const password =
        document.getElementById("password").value;


    if (!ssid) {
        updateStatus({
            status: "ONAP",
            ssid: null,
            status_info: {
                code: "NO_SSID",
                message: "请选择 WiFi"
            }
        });

        return;
    }


    const form = new FormData();

    form.append(
        "ssid",
        ssid
    );

    form.append(
        "password",
        password
    );


    // 用户点击后立即更新页面
    updateStatus({
        status: "CONNECTING",
        ssid: ssid,
        status_info: null
    });


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

        // 如果接口直接返回状态
        if (result.status) {
            updateStatus(result);
        }
        else {
            // 否则重新读取后端真实状态
            await loadStatus();
        }
    }
    catch (error) {

        /*
         * 单网卡切换 WiFi 时：
         *
         * GoodLife AP 会消失，
         * 浏览器和树莓派的连接也会断开。
         *
         * 所以 fetch 报错并不一定表示连接失败。
         */
        console.log(
            "连接请求中断:",
            error
        );

        updateStatus({
            status: "CONNECTING",
            ssid: ssid,
            status_info: null
        });
    }
}   