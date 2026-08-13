from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter()


def redirect_to_portal():
    return RedirectResponse(
        url="/",
        status_code=302
    )


# Android
@router.get("/generate_204")
async def android_generate_204():
    return redirect_to_portal()


@router.get("/gen_204")
async def android_gen_204():
    return redirect_to_portal()


# Apple
@router.get("/hotspot-detect.html")
async def apple_hotspot_detect():
    return redirect_to_portal()


# Windows
@router.get("/connecttest.txt")
async def windows_connect_test():
    return redirect_to_portal()


@router.get("/ncsi.txt")
async def windows_ncsi():
    return redirect_to_portal()


@router.get("/redirect")
async def windows_redirect():
    return redirect_to_portal()

@router.get("/{path:path}")
async def captive_fallback(path: str):
    return RedirectResponse(
        url="/",
        status_code=302
    )