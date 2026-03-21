# Fluo Proto

FastAPI + Jinja2 + PostgreSQL prototype for orientation requests (demandes d'orientation).

## Architecture

Clickable prototype — no auth, no real API, just enough to demonstrate the UX.

```
app.py              — FastAPI setup, template globals, mount routers
config.py           — settings, constants, labels
database.py         — SQLAlchemy engine, session, init_db
models.py           — SQLModel models (Orientation, Message, HistoryEvent)
routes/
  orientations.py   — all orientation routes (list, detail, accept, refuse, message, orienteur)
seed.py             — 5 mock orientations with diagnostic data
templates/          — Jinja2: base.html + pages + includes/
static/             — vendored CSS/JS/fonts from les-emplois (committed to git, ~4MB)
```

Two user views without auth:
- `/` and `/orientation/{id}` — the receiving service (PLIE Lille Avenir) processes incoming orientations
- `/orientation/{id}/orienteur` — the sender can view status and exchange messages

Status flow: `nouvelle` → `acceptee` / `refusee`

Adding a new feature: create `routes/feature.py` with an `APIRouter`, include it in `app.py`.

## Relation to les-emplois

Reproduces the look of [les-emplois](https://github.com/gip-inclusion/les-emplois) via `theme-inclusion`. Static assets are committed to git (trimmed from 16MB to ~4MB). To refresh from les-emplois:

```bash
./scripts/fetch-assets.sh /path/to/les-emplois
```

## Design system gotchas

- **CSS class prefixes**: `s-` sections, `c-` components. Always use `__container` / `__row` / `__col` BEM nesting.
- **c-box variants**: `c-box--action` (dark), `c-box--note` (light). Plain `c-box` = white card.
- **list-data / list-note / list-step**: expect exact markup structure from les-emplois.
- **Remix Icons**: `ri-*` classes, loaded via app.css. Use `fw-medium` after icon class.
- **Badges**: `badge-sm` (tables), `badge-base` (titles). Both need `rounded-pill text-nowrap`.
- **Body class**: `l-authenticated` triggers permanent sidebar on xl+ screens.

## Template globals

Available in all templates without passing per-route:
- `service_name` — "PLIE Lille Avenir"
- `status_labels` — dict mapping status → (label, css_class)
- `event_labels` — dict mapping event_type → label
- `modalite_labels` — dict mapping modalite → label

Custom filter: `{{ value|format_datetime }}` — formats ISO datetime to "HH:MM à YYYY-MM-DD"

## Local dev

```bash
docker compose up -d
DATABASE_URL=postgresql+psycopg://fluo:fluo@localhost:5432/fluo uv run python seed.py
DATABASE_URL=postgresql+psycopg://fluo:fluo@localhost:5432/fluo uv run uvicorn app:app --reload --host 0.0.0.0 --port 8002
```

## Deploy

**Push to main → auto-deploys** via GitHub Actions. Builds Docker image → pushes to registry → redeploys container.

### Infrastructure

- **Database**: Scaleway Managed PostgreSQL DB-DEV-S `proto-db` (shared across prototypes)
  - Instance ID: `REDACTED_DB_INSTANCE_ID`
  - Endpoint: `REDACTED_DB_ENDPOINT`
  - Database: `fluo`, user: `fluo` (separate DB per prototype)
  - Admin creds: `~/.config/scw/proto-db.env`
- **Container**: Scaleway Serverless Container (140 mVCPU / 256 MB)
  - Container ID: `REDACTED_CONTAINER_ID`
  - URL: https://REDACTED_CONTAINER_URL
  - Namespace: `nova` (`REDACTED_NAMESPACE_ID`)
- **Registry**: `REDACTED_REGISTRY`
- **GitHub Secrets**: `SCW_ACCESS_KEY`, `SCW_SECRET_KEY`, `SCW_CONTAINER_ID`, `DATABASE_URL`
- **DATABASE_URL format**: `postgresql+psycopg://user:pass@host:port/db` (SQLAlchemy dialect)

### Manual deploy

```bash
docker buildx build --platform linux/amd64 -t REDACTED_REGISTRY:latest . --push
scw container container deploy REDACTED_CONTAINER_ID region=fr-par
```

### Adding a new prototype to the shared DB

```bash
scw rdb database create instance-id=REDACTED_DB_INSTANCE_ID name=<proto_name>
scw rdb user create instance-id=REDACTED_DB_INSTANCE_ID name=<proto_name> password=<password>
scw rdb privilege set instance-id=REDACTED_DB_INSTANCE_ID database-name=<proto_name> user-name=<proto_name> permission=all
```
