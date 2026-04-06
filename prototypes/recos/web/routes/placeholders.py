from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter()


def _templates(request: Request):
    return request.app.state.templates


@router.get("/prescriptions-sent", response_class=HTMLResponse)
async def prescriptions_sent(request: Request):
    return _templates(request).TemplateResponse(
        "placeholder.html",
        {"request": request, "page_title": "Demandes envoyées"},
    )


@router.get("/prescriptions-received", response_class=HTMLResponse)
async def prescriptions_received(request: Request):
    return _templates(request).TemplateResponse(
        "placeholder.html",
        {"request": request, "page_title": "Demandes reçues"},
    )
