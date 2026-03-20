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

    # Orientation 2: accepted
    date2 = datetime(2025, 3, 5, 14, 15).isoformat()
    conn.execute(
        """INSERT INTO orientation (
            status, created_at,
            person_first_name, person_last_name, person_phone, person_email,
            person_birthdate, person_address,
            sender_name, sender_type, sender_organization, sender_email, sender_message,
            modalite, diagnostic_data
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            "acceptee",
            date2,
            "Karim",
            "BENALI",
            "06 98 76 54 32",
            "karim.benali@email.fr",
            "1985-11-22",
            "Lille, 59000",
            "Nathalie DUPONT",
            "prescripteur",
            "Mission Locale Lille",
            "n.dupont@ml-lille.fr",
            "Karim est en recherche active d'emploi dans le secteur de la logistique. "
            "Il a besoin d'un accompagnement renforcé.",
            "accompagnement_emploi",
            None,
        ),
    )
    conn.execute(
        "INSERT INTO history_event (orientation_id, event_type, created_at) VALUES (?, ?, ?)",
        (2, "created", date2),
    )
    conn.execute(
        "INSERT INTO history_event (orientation_id, event_type, created_at) VALUES (?, ?, ?)",
        (2, "accepted", datetime(2025, 3, 7, 9, 0).isoformat()),
    )

    # Orientation 3: refused
    date3 = datetime(2025, 3, 8, 11, 0).isoformat()
    conn.execute(
        """INSERT INTO orientation (
            status, created_at,
            person_first_name, person_last_name, person_phone, person_email,
            person_birthdate, person_address,
            sender_name, sender_type, sender_organization, sender_email, sender_message,
            modalite, diagnostic_data
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            "refusee",
            date3,
            "Amina",
            "DIALLO",
            "06 55 44 33 22",
            "amina.diallo@email.fr",
            "1992-04-10",
            "Roubaix, 59100",
            "Pierre MOREAU",
            "orienteur",
            "CCAS Roubaix",
            "p.moreau@ccas-roubaix.fr",
            "Amina souhaite une formation en comptabilité. "
            "Orientation vers un accompagnement adapté.",
            "accompagnement_emploi",
            None,
        ),
    )
    conn.execute(
        "INSERT INTO history_event (orientation_id, event_type, created_at) VALUES (?, ?, ?)",
        (3, "created", date3),
    )
    conn.execute(
        "INSERT INTO history_event (orientation_id, event_type, created_at) VALUES (?, ?, ?)",
        (3, "refused", datetime(2025, 3, 10, 16, 30).isoformat()),
    )

    # Orientation 4: nouvelle
    date4 = datetime(2025, 3, 14, 9, 45).isoformat()
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
            date4,
            "Lucas",
            "PETIT",
            "07 11 22 33 44",
            "lucas.petit@email.fr",
            "1998-08-03",
            "Villeneuve-d'Ascq, 59491",
            "Nathalie DUPONT",
            "prescripteur",
            "Mission Locale Lille",
            "n.dupont@ml-lille.fr",
            "Lucas sort d'un contrat en intérim et souhaite se stabiliser. "
            "Besoin d'un accompagnement vers un emploi durable.",
            "accompagnement_emploi",
            None,
        ),
    )
    conn.execute(
        "INSERT INTO history_event (orientation_id, event_type, created_at) VALUES (?, ?, ?)",
        (4, "created", date4),
    )

    # Orientation 5: nouvelle
    date5 = datetime(2025, 3, 18, 8, 30).isoformat()
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
            date5,
            "Fatou",
            "NDIAYE",
            "06 77 88 99 00",
            "fatou.ndiaye@email.fr",
            "1988-01-25",
            "Tourcoing, 59200",
            "Jean-Marc LEFÈVRE",
            "prescripteur",
            "FT Agence Cahors",
            "jean-marc.lefevre@francetravail.fr",
            "Fatou est en reconversion professionnelle après un congé parental. "
            "Elle cherche un accompagnement dans le secteur de l'aide à la personne.",
            "accompagnement_emploi",
            None,
        ),
    )
    conn.execute(
        "INSERT INTO history_event (orientation_id, event_type, created_at) VALUES (?, ?, ?)",
        (5, "created", date5),
    )

    # Add a message on orientation 2 for realism
    conn.execute(
        "INSERT INTO message (orientation_id, author_name, content, created_at) VALUES (?, ?, ?, ?)",
        (2, "PLIE Lille Avenir", "Merci pour cette orientation, nous prenons en charge le dossier.",
         datetime(2025, 3, 6, 10, 0).isoformat()),
    )

    conn.commit()
    conn.close()
    print("Seeded 5 orientations.")


if __name__ == "__main__":
    seed()
