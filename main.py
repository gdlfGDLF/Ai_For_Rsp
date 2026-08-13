import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from network.monitor import network_watch
from network.provisioning.router import router as provisioning_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    monitor_task = asyncio.create_task(network_watch())
    try:
        yield
    finally:
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass


BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.include_router(provisioning_router)
