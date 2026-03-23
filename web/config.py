import os

DATABASE_URL = os.environ["DATABASE_URL"]

SERVICE_NAME = "PLIE Lille Avenir"

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

ALL_STATUSES = ["nouvelle", "acceptee", "refusee"]

SCENARIOS = {
    "plie": {
        "slug": "plie",
        "label": "PLIE Lille Avenir",
        "description": "Orientations reçues",
        "nav": [
            {"label": "Tableau de bord", "icon": "ri-home-line", "href": "/plie/"},
            {"label": "Orientations", "icon": "ri-compass-line", "href": "/plie/orientations", "active_prefix": "/plie/orientation"},
            {"label": "Bénéficiaires", "icon": "ri-group-line", "href": "#"},
        ],
    },
    "prescripteur": {
        "slug": "prescripteur",
        "label": "France Travail Lille",
        "description": "Orientations envoyées",
        "nav": [
            {"label": "Tableau de bord", "icon": "ri-home-line", "href": "/prescripteur/"},
            {"label": "Bénéficiaires", "icon": "ri-group-line", "href": "/prescripteur/beneficiaires"},
            {"label": "Orientations envoyées", "icon": "ri-compass-line", "href": "/prescripteur/orientations", "active_prefix": "/prescripteur/orientation"},
        ],
    },
}
