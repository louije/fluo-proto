from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from db import add_message, get_history, get_messages, get_orientation, init_db, update_orientation_status

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

init_db()

STATUS_LABELS = {
    "nouvelle": ("Nouvelle demande", "bg-info"),
    "acceptee": ("Acceptée", "bg-success"),
    "refusee": ("Refusée", "bg-danger"),
}

EVENT_LABELS = {
    "created": "Nouvelle demande",
    "accepted": "Demande acceptée",
    "refused": "Demande refusée",
}

MODALITE_LABELS = {
    "accompagnement_emploi": "Accompagnement vers l'emploi",
}

SERVICE_NAME = "PLIE Lille Avenir"


@app.get("/orientation/{orientation_id}", response_class=HTMLResponse)
async def orientation_detail(request: Request, orientation_id: int):
    orientation = get_orientation(orientation_id)
    if not orientation:
        return HTMLResponse("Not found", status_code=404)
    messages = get_messages(orientation_id)
    history = get_history(orientation_id)
    status_label, status_class = STATUS_LABELS.get(
        orientation["status"], ("Inconnu", "bg-secondary")
    )
    return templates.TemplateResponse(
        "orientation_detail.html",
        {
            "request": request,
            "o": orientation,
            "messages": messages,
            "history": history,
            "status_label": status_label,
            "status_class": status_class,
            "event_labels": EVENT_LABELS,
            "modalite_label": MODALITE_LABELS.get(orientation["modalite"], orientation["modalite"]),
            "service_name": SERVICE_NAME,
        },
    )


@app.post("/orientation/{orientation_id}/accept")
async def accept_orientation(orientation_id: int):
    update_orientation_status(orientation_id, "acceptee")
    return RedirectResponse(f"/orientation/{orientation_id}", status_code=303)


@app.post("/orientation/{orientation_id}/refuse")
async def refuse_orientation(orientation_id: int):
    update_orientation_status(orientation_id, "refusee")
    return RedirectResponse(f"/orientation/{orientation_id}", status_code=303)


@app.post("/orientation/{orientation_id}/message")
async def post_message(request: Request, orientation_id: int):
    form = await request.form()
    content = form.get("content", "").strip()
    author = form.get("author_name", SERVICE_NAME)
    redirect_to = form.get("redirect_to", f"/orientation/{orientation_id}")
    if content:
        add_message(orientation_id, author, content)
    return RedirectResponse(redirect_to, status_code=303)


@app.get("/orientation/{orientation_id}/orienteur", response_class=HTMLResponse)
async def orienteur_reply(request: Request, orientation_id: int):
    orientation = get_orientation(orientation_id)
    if not orientation:
        return HTMLResponse("Not found", status_code=404)
    messages = get_messages(orientation_id)
    status_label, status_class = STATUS_LABELS.get(
        orientation["status"], ("Inconnu", "bg-secondary")
    )
    return templates.TemplateResponse(
        "orienteur_reply.html",
        {
            "request": request,
            "o": orientation,
            "messages": messages,
            "status_label": status_label,
            "status_class": status_class,
        },
    )
