# recos prototype — design spec

**Date:** 2026-04-06
**Status:** Approved, ready for implementation planning
**Scope:** Step 1-2 of the recos prototype: menu structure, functional pages (dashboard, beneficiary list, beneficiary detail with 3 tabs), placeholder pages, 4 seeded people from real diagnostic JSON data. No recommendation engine, no working search, no prescription flow.

## Goal

Test a new orientation flow from the perspective of a conseiller France Travail. For each personne accompagnée, recommend a modalité (FT-internal: Suivi, Guidé, Renforcé, Global) or a structure d'accompagnement (SIAE, PLIE, E2C, etc.).

Step 1-2 builds the shell and populates it with real diagnostic data. The recommendation engine and prescription flows come later (steps 3-4).

## Conventions

- **English URLs, file names, model names** (les-emplois convention). UI labels stay in French.
- URLs: `/beneficiaries`, `/beneficiary/{id}`, not `/personnes`, `/personne/{id}`.
- Files: `beneficiaries.py`, `beneficiary_detail.html`.
- Models: `Beneficiary`, `Structure`.

## Data model

### Structure

Normalized reference table for structures d'accompagnement.

```python
class Structure(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str               # "Jardins de Cocagne", "Lille Avenir"
    type_acronym: str        # "ACI", "PLIE", "CCAS", "E2C", "EPIDE"
```

Display: `f"{structure.name} ({structure.type_acronym})"` → "Jardins de Cocagne (ACI)".

### Beneficiary

```python
class Beneficiary(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    person_first_name: str
    person_last_name: str
    person_phone: str | None = None
    person_email: str | None = None
    person_birthdate: str | None = None
    person_address: str | None = None
    modalite: str | None = None
    structure_referente_id: int | None = Field(default=None, foreign_key="structure.id")
    eligibilites: str | None = None   # JSON array: ["PASS IAE valide", "Éligible PLIE"]
    nb_prescriptions: int = 0
    diagnostic_data: str | None = None  # full diag JSON, parsed in routes
    date_inscription: str
```

A Beneficiary has either a `modalite` (FT-managed) OR a `structure_referente` (external structure), or neither ("Inconnue"). Display logic picks one.

`eligibilites` is a JSON array of badge strings, parsed in routes with `json.loads()`.

`diagnostic_data` stores the full diagnostic JSON from the explorations-nova diag files.

### Not modeled in step 1-2

- **Prescription / Orientation / Candidature**: `nb_prescriptions` is a static int. Prescriptions tab is a placeholder.
- **Recommendation / Solution de parcours**: rec engine not integrated. Recommandations screen is a placeholder.
- **Dashboard stats**: hardcoded in template.

## Routes

| URL | Route function | French label | Status |
|---|---|---|---|
| `/` | redirect → `/dashboard` | | |
| `/dashboard` | `dashboard` | Accueil | Functional (hardcoded stats) |
| `/beneficiaries` | `list_beneficiaries` | Personnes accompagnées | Functional |
| `/beneficiary/{id}` | `detail_beneficiary` | Fiche personne | Functional (3 tabs) |
| `/beneficiary/{id}/recommendations` | `recommendations` | Recommandations | Placeholder |
| `/prescriptions-sent` | `prescriptions_sent` | Demandes envoyées | Placeholder |
| `/prescriptions-received` | `prescriptions_received` | Demandes reçues | Placeholder |

Two route files:
- `web/routes/beneficiaries.py` — dashboard, list, detail, recommendations
- `web/routes/placeholders.py` — prescriptions-sent, prescriptions-received

Both mounted in `web/app.py` with no URL prefix (flat structure, no scenario middleware).

## Template structure

```
web/templates/
  base.html                      # sidebar (4 entries), prototype banner, scripts
  dashboard.html                 # search bar + 3 cards
  beneficiary_list.html          # filter bar + table
  beneficiary_detail.html        # prevstep + title + CTA + modalité bar + tabs
  recommendations.html           # placeholder (status bar + empty tabs)
  placeholder.html               # generic shell for prescriptions-sent/received
  includes/
    general_info.html            # Informations générales tab
    diagnostic.html              # Diagnostic tab (dense, skip-empty)
    prescriptions.html           # Prescriptions tab placeholder
```

## Pages

### Sidebar menu (base.html)

4 entries:
- `ri-home-line` Accueil → `/dashboard`
- `ri-group-line` Personnes accompagnées → `/beneficiaries`
- `ri-compass-line` Demandes envoyées → `/prescriptions-sent`
- `ri-mail-send-line` Demandes reçues → `/prescriptions-received`

### Dashboard (`/dashboard`)

`s-title-02` with a disabled search `<input>`, placeholder "Rechercher une personne, une structure, un emploi...".

Below, `s-section` with 3 cards in auto-grid (`row` + `col-12 col-md-6 col-xl-4`):

**Card 1 — Personnes accompagnées.** `c-box`:
- Header: "Personnes accompagnées" + "70 dossiers" badge
- 3 stat lines: "1 dossier sans solution", "5 réponses à des demandes d'orientation", "1 personne en fin de parcours" (subtitle: "Anticiper la sortie de cette personne")
- Footer link: "Voir tous les dossiers" → `/beneficiaries`

**Card 2 — En ce moment sur mon territoire.** `c-box`:
- Hardcoded lines: "Prochain comité local : personnes isolées et santé mentale" (date + lieu), "Nouveaux services référencés : Mobilité (3), Hébergement (1)", "3 nouvelles fiches de poste en SIAE"

**Card 3 — Organisation.** `c-box` with placeholder content similar to les-emplois prescripteur dashboard.

All stats hardcoded. No DB queries. One template, zero includes.

### Beneficiary list (`/beneficiaries`)

Standard `s-title-02` (title "Personnes accompagnées") → `s-section` (table).

Table columns:
- **Nom Prénom** — `btn-link` to `/beneficiary/{id}`, formal format ("Mme Martin")
- **Éligibilité** — `badge rounded-pill badge-sm` per eligibility string. Colors: "PASS IAE valide" → `bg-success`, "à valider" → `bg-warning`, "Éligible X" → `bg-info`
- **Nbr prescriptions** — integer
- **Modalité / structure référente** — modalité name, or "Structure (TYPE)", or "Inconnue" in muted text

No filter bar in step 1-2 (only 4 rows). Arrow column at the end per les-emplois pattern.

### Beneficiary detail (`/beneficiary/{id}`)

**Title bar:**
- `c-prevstep` → "Retour à la liste" → `/beneficiaries`
- `c-title` → formal name + badge (modalité or structure)
- CTA: "Prescrire une solution" (`btn btn-primary btn-ico`) → `/beneficiary/{id}/recommendations`

**Modalité bar** (below title, above tabs): `c-box` showing the current modalité or structure référente assignment. `btn-outline-primary` "Modifier" button → `/beneficiary/{id}/recommendations`.

**Tabs:**

**Tab 1 — Informations générales** (default, `show active`):
- `c-box` with `list-data`: nom, prénom, email, téléphone, date de naissance, adresse
- Single column layout (`col-12 col-xxl-8`), no sidebar

**Tab 2 — Diagnostic:**
- Ported from `explorations-nova/diags/build.ts`, adapted to Jinja2 + les-emplois design system
- Sections rendered as `c-box` cards: Projet professionnel, Points forts et besoins, Contraintes personnelles, Confiance et capacité à agir, Maîtrise du numérique, Données hors schéma
- **Skip empty sections entirely** — glanceability is the goal
- Items within sections use `list-data` pattern
- Values rendered as les-emplois badges:
  - BESOIN → `bg-info` (blue)
  - POINT_FORT → `bg-success` (green)
  - NON_EXPLORE → `bg-secondary` (grey)
  - EN_COURS → `bg-warning` (yellow)
  - OUI / impact FORT → `bg-danger` (red)
- Agent attribution as muted text below items
- Single column layout within the tab

**Tab 3 — Prescriptions:**
- Placeholder: `c-box` with "Aucune prescription pour le moment"

### Recommendations (`/beneficiary/{id}/recommendations`)

Placeholder page:
- `alert alert-primary` status bar: "Vous recherchez actuellement pour [Mme Martin]"
- Tab nav with 4 tabs: "Employeurs (SIAE et GEIQ)", "Postes ouverts", "Services d'insertion", "Solutions de parcours" (default selected)
- Empty content area: "Aucune recommandation disponible pour le moment"
- `c-prevstep` back to the beneficiary detail

### Placeholder pages (`/prescriptions-sent`, `/prescriptions-received`)

Generic shell extending `base.html`: `s-title-02` with the French label as title, `s-section` with a `c-box` containing "Page en construction".

## Seed data

4 `Beneficiary` records, one per diagnostic JSON file from `/Users/louije/Development/gip/explorations-nova/diags/`:

| File | Source | Notes |
|---|---|---|
| `brsa.json` | Identity from `extra.identite` | bRSA profile |
| `detld-glo.json` | Identity from `extra.identite` | DETLD with modalité from `extra.modaliteSuivi` |
| `fle-qpv-brsa.json` | Identity from `extra.identite` | FLE + QPV + bRSA |
| `qpv.json` | Identity from `extra.identite` | QPV |

The 4 JSON files are copied into `prototypes/recos/data/` at development time so the proto is self-contained. The seed script reads from `data/*.json` relative to the proto root, extracts identity fields from `extra.identite`, and stores the full JSON as `diagnostic_data`.

A handful of `Structure` records seeded for FK relationships: at least 2-3 realistic structures (e.g., "Jardins de Cocagne" ACI, "Lille Avenir" PLIE, "Ville de Montluçon" CCAS).

Eligibility badges and modalité/structure assignments are set per person at seed time based on the profile type (brsa → bRSA-relevant badges, etc.).

`nb_prescriptions` set to small integers (0-3) for display variety.

## Config (web/config.py)

Template globals:
- `SERVICE_NAME` — "France Travail"
- `MODALITE_LABELS` — dict mapping modalité keys to display labels
- `ELIGIBILITY_COLORS` — dict mapping eligibility badge strings to CSS classes

## What is explicitly deferred

- Recommendation engine (step 4)
- Search functionality
- Prescription / orientation / candidature models and flows
- Filter bar on the list page (only 4 rows — no filtering needed)
- Additional seed people beyond the 4 diagnostic profiles
- Rec screen actual results and content
