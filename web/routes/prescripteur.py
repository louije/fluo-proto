from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

router = APIRouter()


def _templates(request: Request):
    return request.app.state.templates


@router.get("/", response_class=HTMLResponse)
async def prescripteur_index():
    return RedirectResponse("/prescripteur/beneficiaires", status_code=302)


@router.get("/beneficiaires", response_class=HTMLResponse)
async def beneficiaires_list(request: Request):
    return _templates(request).TemplateResponse(
        "prescripteur/beneficiaires.html",
        {"request": request, "prefix": "/prescripteur"},
    )


@router.get("/orientations", response_class=HTMLResponse)
async def orientations_envoyees(request: Request):
    return _templates(request).TemplateResponse(
        "prescripteur/orientations_envoyees.html",
        {"request": request, "prefix": "/prescripteur"},
    )
