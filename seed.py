import json
from datetime import datetime

from db import get_db, init_db

DIAGNOSTIC_DATA = {
    "projet_professionnel": {
        "nom_metier": "Assistante de vie aux familles",
        "code_rome": "K1302",
        "statut": "EN_COURS",
        "est_prioritaire": True,
    },
    "contraintes": [
        {
            "libelle": "Développer sa mobilité",
            "valeur": "OUI",
            "impact": "FORT",
            "est_prioritaire": True,
            "situations": [
                {"libelle": "Aucun moyen de transport à disposition", "valeur": "OUI"},
                {"libelle": "Dépendant des transports en commun", "valeur": "NON"},
            ],
            "objectifs": [
                {"libelle": "Obtenir le permis de conduire", "valeur": "EN_COURS"},
            ],
        },
        {
            "libelle": "Surmonter ses contraintes familiales",
            "valeur": "OUI",
            "impact": "MOYEN",
            "est_prioritaire": False,
            "situations": [
                {"libelle": "Enfant(s) de moins de 3 ans sans solution de garde", "valeur": "OUI"},
                {"libelle": "Contraintes horaires", "valeur": "OUI"},
            ],
            "objectifs": [
                {"libelle": "Trouver des solutions de garde d'enfant", "valeur": "EN_COURS"},
            ],
        },
    ],
    "pouvoir_agir": {
        "confiance": "NON",
        "accompagnement": "OUI",
        "resultat_analyse": "Besoin d'appui pour consolider sa confiance à mener ses démarches",
    },
    "autonomie_numerique": {
        "impact": "FAIBLE",
        "situations": [
            {"libelle": "Dispose d'un smartphone", "valeur": "OUI"},
            {"libelle": "Dispose d'un ordinateur", "valeur": "NON"},
            {"libelle": "Difficulté à réaliser des démarches administratives en ligne", "valeur": "OUI"},
        ],
        "objectifs": [
            {"libelle": "Maîtriser les fondamentaux du numérique", "valeur": "EN_COURS"},
        ],
    },
    "agent": {
        "nom": "Lefèvre",
        "prenom": "Jean-Marc",
        "structure": "FT Agence Cahors",
    },
    "date_mise_a_jour": "2025-03-12",
}


def seed():
    init_db()
    conn = get_db()

    # Check if already seeded
    count = conn.execute("SELECT COUNT(*) FROM orientation").fetchone()[0]
    if count > 0:
        print("Database already seeded.")
        conn.close()
        return

    now = datetime(2025, 3, 12, 10, 30).isoformat()

    conn.execute(
        """INSERT INTO orientation (
            status, created_at,
            person_first_name, person_last_name, person_phone, person_email,
            person_birthdate, person_address,
            sender_name, sender_type, sender_organization, sender_email, sender_message,
            modalite, diagnostic_data
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            "nouvelle",
            now,
            "Sophie",
            "MARTIN",
            "06 12 34 56 78",
            "sophie.martin@email.fr",
            "1990-06-15",
            "Cahors, 46000",
            "Jean-Marc LEFÈVRE",
            "prescripteur",
            "FT Agence Cahors",
            "jean-marc.lefevre@francetravail.fr",
            "Sophie souhaite se reconvertir comme assistante de vie. "
            "Elle a besoin d'un accompagnement pour lever ses freins "
            "de mobilité et de garde d'enfant.",
            "accompagnement_emploi",
            json.dumps(DIAGNOSTIC_DATA, ensure_ascii=False),
        ),
    )

    conn.execute(
        "INSERT INTO history_event (orientation_id, event_type, created_at) VALUES (?, ?, ?)",
        (1, "created", now),
    )

    conn.commit()
    conn.close()
    print("Seeded 1 orientation.")


if __name__ == "__main__":
    seed()
