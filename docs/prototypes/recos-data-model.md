# recos — data model notes

Working document for the recos prototype data model. Not a formal spec — captures decisions as they're made.

## Conventions

- **URLs, file names, model names in English** (les-emplois convention). UI labels stay in French.
- URL: `/beneficiaries`, `/beneficiary/{id}`, not `/personnes`, `/personne/{id}`.
- Files: `beneficiaries.py`, `beneficiary_detail.html`.
- Models: `Beneficiary`, `Structure`, not `Personne`, `StructureReferente`.

## Routes

| URL | Route | French label | Status (step 1-2) |
|---|---|---|---|
| `/` | redirect → `/dashboard` | | |
| `/dashboard` | `dashboard` | Accueil | Functional (hardcoded stats) |
| `/beneficiaries` | `list_beneficiaries` | Personnes accompagnées | Functional |
| `/beneficiary/{id}` | `detail_beneficiary` | Fiche personne | Functional (3 tabs) |
| `/beneficiary/{id}/recommendations` | `recommendations` | Recommandations | Placeholder |
| `/prescriptions-sent` | `prescriptions_sent` | Demandes envoyées | Placeholder |
| `/prescriptions-received` | `prescriptions_received` | Demandes reçues | Placeholder |

Route files: `web/routes/beneficiaries.py` (functional pages), `web/routes/placeholders.py` (shells).

## Models

### Structure

Normalized reference table for structures d'accompagnement.

```
Structure(SQLModel, table=True)
    id: int (PK)
    name: str               # "Jardins de Cocagne", "Lille Avenir", "Ville de Montluçon"
    type_acronym: str        # "ACI", "PLIE", "CCAS", "E2C", "EPIDE"
```

Display: `f"{structure.name} ({structure.type_acronym})"` → "Jardins de Cocagne (ACI)".

Seeded with a handful of realistic structures. Menu entry "Demandes reçues" could eventually filter by structure.

### Beneficiary

One record per personne accompagnée in the portefeuille. English model/file/URL names, French UI labels (les-emplois convention).

```
Beneficiary(SQLModel, table=True)
    id: int (PK)
    person_first_name: str
    person_last_name: str
    person_phone: str | None
    person_email: str | None
    person_birthdate: str | None
    person_address: str | None
    modalite: str | None              # FT internal: "Suivi", "Guidé", "Renforcé", "Global"
    structure_referente_id: int | None  # FK → Structure.id
    eligibilites: str | None          # JSON array: ["PASS IAE valide", "Éligible PLIE"]
    nb_prescriptions: int = 0         # denormalized count (no Prescription model in step 1-2)
    diagnostic_data: str | None       # full diag JSON stored as TEXT, parsed in routes
    date_inscription: str
```

A Beneficiary has either a `modalite` (FT-managed) OR a `structure_referente` (external structure), or neither ("Inconnue"). Not both simultaneously — the display logic picks one.

### Not modeled in step 1-2

- **Prescription / Orientation / Candidature**: `nb_prescriptions` is a static int on Personne. The Prescriptions tab is a placeholder.
- **Recommendation / Solution de parcours**: the rec engine isn't integrated yet. The Recommandations screen is a placeholder.
- **Dashboard stats**: hardcoded in the template (1 dossier sans solution, 5 réponses, 1 fin de parcours).

## Seed data

4 `Beneficiary` records, one per diagnostic JSON file:

| File | Identity (from extra.identite) | Modalité / structure | Eligibility |
|---|---|---|---|
| brsa.json | extracted at seed time | TBD from data | bRSA-related badges |
| detld-glo.json | extracted at seed time | modalite from extra.modaliteSuivi | PASS IAE related |
| fle-qpv-brsa.json | extracted at seed time | TBD | FLE + QPV + bRSA badges |
| qpv.json | extracted at seed time | TBD | QPV badges |

A few `Structure` records seeded for the FK relationships (those that appear as structure_referente for the 4 people, plus a couple extras for the rec screen later).

## Diagnostic rendering

Ported from the TypeScript renderers in `explorations-nova/diags/build.ts`, adapted to Jinja2 + les-emplois design system:

- Sections: Projet professionnel, Points forts et besoins, Contraintes personnelles, Confiance et capacité à agir, Maîtrise du numérique, Données hors schéma
- **Skip empty sections entirely** — glanceability over completeness
- Each section is a `c-box` card
- Items within sections use `list-data` pattern (label + value)
- Values rendered as les-emplois badges with semantic colors:
  - BESOIN → `bg-info` (blue)
  - POINT_FORT → `bg-success` (green)
  - NON_EXPLORE → `bg-secondary` (grey)
  - EN_COURS → `bg-warning` (yellow)
  - OUI / impact FORT → `bg-danger` (red)
- Agent attribution as muted text below items
- Layout: single column within the tab (no masonry — les-emplois doesn't use CSS columns)
