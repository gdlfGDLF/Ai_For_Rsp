from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Form
from fastapi.responses import FileResponse

from network.state import state
from network.wifi import scan_wifi_networks, switch_wifi

router = APIRouter()
TEMPLATE_PATH = Path(__file__).resolve().parents[2] / "templates" / "provisioning.html"


@router.get("/", response_class=FileResponse)
async def index():
    return FileResponse(TEMPLATE_PATH)


@router.get("/api/wifi")
async def scan_wifi():
    return scan_wifi_networks()


@router.post("/api/connect")
async def connect_wifi(
    background_tasks: BackgroundTasks,
    ssid: str = Form(...),
    password: str = Form(...),
):
    background_tasks.add_task(switch_wifi, ssid, password)
    return {"message": f"正在连接 {ssid}，设备网络即将切换..."}

@router.get("/api/status")
async def get_status():
    return state.wifi_status
