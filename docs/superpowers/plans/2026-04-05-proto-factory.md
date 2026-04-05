# Proto-factory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure `fluo-proto-factory` from a single-prototype repo into a factory that scaffolds independent, throwaway prototypes under `prototypes/<name>/`, with shared tooling (Makefile, copier, CI) at the factory root and the current app living as `prototypes/demandes/`.

**Architecture:** Two phases. Phase A migrates the existing `web/` app into `prototypes/demandes/`, builds the full Makefile, rewrites the GitHub Actions workflows, and updates the live Scaleway container to pull from the new image path. Phase B introduces `_template/`, `copier.yml`, `.githooks/pre-commit` URL guard, and rewrites `PROTOTYPE.md` / `CLAUDE.md` / `README.md`. Existing protos never read from `_template/` — full isolation, no runtime coupling.

**Tech Stack:** Python 3.13 / uv / FastAPI / SQLModel / PostgreSQL / Jinja2 / Docker / Scaleway Serverless Containers / Scaleway RDB / GitHub Actions / ruff / copier (via `uvx`) / GNU Make / bash

**Reference spec:** `docs/superpowers/specs/2026-04-05-proto-factory-design.md`

---

## Execution notes

**Local commits vs. push:** Phase A tasks produce intermediate states where the old `web/` path no longer exists but the deploy workflow hasn't caught up yet. Commit locally at each task; do NOT push until Phase A is entirely complete (Task A.6). Phase A ends with a single push that triggers the first deploy from the new path. Phase B also ends with a single push.

**No Python tests exist in this codebase.** Verification is by running `docker build`, `make help`, `uvx ruff check`, `copier copy`, `gh run watch`. Do not invent unit tests for file-restructuring work.

**Python version mismatch is pre-existing.** `pyproject.toml` declares `requires-python = ">=3.14"` but `Dockerfile` uses `python:3.13-slim`. This is the current working state — do not "fix" it as part of this plan.

**Scaleway operations mostly happen via operator action against live infra.** Phase A Task A.5 updates the existing Scaleway container; Phase B Task B.4 writes `scripts/provision.sh` (not executed during the plan — it runs later when an operator creates a new proto).

---

# Phase A — Migrate `web/` → `prototypes/demandes/`

Goal: by the end of Phase A, `git push` deploys the demandes app from its new location with zero change in public URL or behavior, and the full Makefile operator interface is in place.

## Task A.1: Move app files and extract ruff config

**Files:**
- Create: `prototypes/demandes/` (directory)
- Move: `web/` → `prototypes/demandes/web/`
- Move: `Dockerfile`, `pyproject.toml`, `uv.lock`, `docker-compose.yml`, `.dockerignore` → `prototypes/demandes/`
- Create: `ruff.toml` (at factory root)
- Modify: `prototypes/demandes/pyproject.toml` (strip `[tool.ruff*]` blocks)

- [ ] **Step 1: Create target directory and move app files**

```bash
mkdir -p prototypes/demandes
git mv web prototypes/demandes/web
git mv Dockerfile prototypes/demandes/Dockerfile
git mv pyproject.toml prototypes/demandes/pyproject.toml
git mv uv.lock prototypes/demandes/uv.lock
git mv docker-compose.yml prototypes/demandes/docker-compose.yml
git mv .dockerignore prototypes/demandes/.dockerignore
```

- [ ] **Step 2: Verify the layout**

```bash
ls prototypes/demandes/
```

Expected: `.dockerignore  Dockerfile  docker-compose.yml  pyproject.toml  uv.lock  web`

- [ ] **Step 3: Extract ruff config to `ruff.toml` at factory root**

Create `ruff.toml`:
```toml
target-version = "py313"
line-length = 120

[lint]
select = ["E", "F", "W", "I", "UP"]
ignore = ["E501"]

[lint.isort]
known-first-party = ["web"]
```

Standalone `ruff.toml` omits the `[tool.ruff]` prefix that was in `pyproject.toml`; `[lint]` and `[lint.isort]` are top-level.

- [ ] **Step 4: Remove the ruff config from `prototypes/demandes/pyproject.toml`**

Open `prototypes/demandes/pyproject.toml` and delete lines 19–28 (the three `[tool.ruff*]` blocks). The file ends after the `[dependency-groups]` section.

- [ ] **Step 5: Verify Docker build still works and ruff picks up the new config**

```bash
docker build --platform linux/amd64 -t demandes-test prototypes/demandes
uvx ruff check prototypes/demandes/
uvx ruff format --check prototypes/demandes/
```

Expected: docker build succeeds; ruff passes (same result as before — the config is identical, just relocated).

- [ ] **Step 6: Commit (local only)**

```bash
git add -A
git commit -m "move web/ into prototypes/demandes/ and extract ruff.toml"
```

---

## Task A.2: Write `prototypes/demandes/README.md`

**Files:**
- Create: `prototypes/demandes/README.md`

- [ ] **Step 1: Write the README**

File: `prototypes/demandes/README.md`
```markdown
# demandes

Prototype for processing orientation requests (demandes d'orientation) at PLIE Lille Avenir.

## What it demonstrates

Two user views without auth, sharing the same fictitious data:

- **PLIE side** (`/plie/...`) — the receiving service processes incoming orientations: list, detail, accept/refuse, exchange messages, view history.
- **Prescripteur side** (`/prescripteur/...`) — the sender views status and replies to messages.

Status flow: `nouvelle` → `acceptee` / `refusee`.

## Seed data

5 mock orientations with diagnostic data, seeded by `web/seed.py`. See `web/config.py` for the label dictionaries.

## Run locally

From the factory root:

```bash
make dev demandes
```

This starts the local PostgreSQL via docker-compose and runs uvicorn with `--reload` on port 8002.

First run only — seed the database:

```bash
cd prototypes/demandes
DATABASE_URL=postgresql+psycopg://demandes:demandes@localhost:5432/demandes uv run python -m web.seed
```

After any local schema change, reseed: `make reseed demandes` from the factory root.

## Deploy

From the factory root:

```bash
make deploy demandes
```

Deploys to the existing Scaleway Serverless Container. Push to `main` triggers the same flow via GitHub Actions.

## Auth

This proto has no auth — the fictitious-data banner + obscure Scaleway URL are the only protection. See `../../PROTOTYPE.md` for the auth recipe if needed.
```

- [ ] **Step 2: Commit**

```bash
git add prototypes/demandes/README.md
git commit -m "add demandes README"
```

---

## Task A.3: Create the full Makefile (10 targets)

**Files:**
- Create: `Makefile`

Build the entire operator interface in one task. Targets that require later-phase infrastructure (`new` needs `_template/`, `dev`/`reseed` need B.6's docker-compose rename) will error cleanly with their usage guards until their prerequisites are in place. `make help` and `make deploy demandes` work immediately.

**Design note on the `lint` target:** until `_template/` exists (Phase B), it lints `prototypes/` only. B.1 extends the lint paths in the same commit that creates `_template/`.

- [ ] **Step 1: Create the Makefile**

File: `Makefile`
```make
# Factory-level operator commands. Positional args: `make deploy demandes`.

# Extract positional args (everything on the command line that isn't the target name)
ARGS := $(filter-out $@,$(MAKECMDGOALS))

# Catch-all rule: turn each positional arg into a no-op target so Make doesn't
# complain "No rule to make target 'demandes'".
%:
	@:

.PHONY: help new provision deploy dev reseed urls lint fmt update-assets

help: ## Print targets
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

new: ## Scaffold a new proto from _template — usage: make new <name>
	@proto=$(firstword $(ARGS)); \
	test -n "$$proto" || { echo "usage: make new <proto>"; exit 1; }; \
	test ! -d "prototypes/$$proto" || { echo "error: prototypes/$$proto already exists"; exit 1; }; \
	test -d "_template" || { echo "error: _template/ does not exist"; exit 1; }; \
	uvx copier copy . "prototypes/$$proto" --data proto_name="$$proto"

provision: ## Create SCW container + DB for a proto — usage: make provision <name>
	@proto=$(firstword $(ARGS)); \
	test -n "$$proto" || { echo "usage: make provision <proto>"; exit 1; }; \
	test -d "prototypes/$$proto" || { echo "error: prototypes/$$proto does not exist (run make new first)"; exit 1; }; \
	scripts/provision.sh "$$proto"

deploy: ## Build, push, and deploy one proto — usage: make deploy <name>
	@proto=$(firstword $(ARGS)); \
	test -n "$$proto" || { echo "usage: make deploy <proto>"; exit 1; }; \
	test -d "prototypes/$$proto" || { echo "error: prototypes/$$proto does not exist"; exit 1; }; \
	test -n "$$SCW_REGISTRY" || { echo "error: SCW_REGISTRY not set (source ~/.config/scw/proto-db.env or configure GH secrets)"; exit 1; }; \
	echo "Building $$proto..."; \
	docker buildx build --platform linux/amd64 \
		-t "$$SCW_REGISTRY/$$proto:latest" \
		"prototypes/$$proto" --push; \
	echo "Looking up container ID for $$proto..."; \
	container_id=$$(scw container container list name="$$proto" -o json | jq -r '.[0].id'); \
	test -n "$$container_id" && test "$$container_id" != "null" || { echo "error: no Scaleway container named $$proto"; exit 1; }; \
	echo "Deploying container $$container_id..."; \
	scw container container deploy "$$container_id" region=fr-par

dev: ## Run a proto locally with hot reload — usage: make dev <name>
	@proto=$(firstword $(ARGS)); \
	test -n "$$proto" || { echo "usage: make dev <proto>"; exit 1; }; \
	test -d "prototypes/$$proto" || { echo "error: prototypes/$$proto does not exist"; exit 1; }; \
	cd "prototypes/$$proto" && \
	docker compose up -d && \
	DATABASE_URL="postgresql+psycopg://$$proto:$$proto@localhost:5432/$$proto" \
		uv run uvicorn web.app:app --reload --host 0.0.0.0 --port 8002

reseed: ## Drop + reseed a proto's local DB — usage: make reseed <name>
	@proto=$(firstword $(ARGS)); \
	test -n "$$proto" || { echo "usage: make reseed <proto>"; exit 1; }; \
	test -d "prototypes/$$proto" || { echo "error: prototypes/$$proto does not exist"; exit 1; }; \
	cd "prototypes/$$proto" && \
	docker compose up -d && \
	sleep 2 && \
	docker compose exec -T db psql -U "$$proto" -d "$$proto" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" && \
	DATABASE_URL="postgresql+psycopg://$$proto:$$proto@localhost:5432/$$proto" \
		uv run python -m web.seed

urls: ## Print all proto names and their Scaleway URLs
	@scw container container list -o json | jq -r '.[] | "\(.name)\t\(.domain_name)"'

lint: ## Run ruff lint + format check on all protos
	@uvx ruff check prototypes/
	@uvx ruff format --check prototypes/

fmt: ## Run ruff format on all protos
	@uvx ruff format prototypes/

update-assets: ## Refresh _template/web/static from a les-emplois clone — usage: make update-assets <path>
	@path=$(firstword $(ARGS)); \
	test -n "$$path" || { echo "usage: make update-assets <path-to-les-emplois>"; exit 1; }; \
	test -d "$$path" || { echo "error: $$path does not exist"; exit 1; }; \
	scripts/fetch-assets.sh "$$path"
```

- [ ] **Step 2: Verify `make help` lists all 10 targets**

```bash
make help
```

Expected: 10 lines, one per target, colorized.

- [ ] **Step 3: Verify usage guards fire for each PROTO-taking target**

```bash
make new
make provision
make deploy
make dev
make reseed
make update-assets
```

Expected: each prints `usage: make <target> <...>` and exits 1.

- [ ] **Step 4: Verify `make lint` runs (on prototypes/ only; `_template/` doesn't exist yet)**

```bash
make lint
```

Expected: passes with no errors.

- [ ] **Step 5: Verify `make deploy` argument-handling works without hitting infra**

```bash
make deploy nonexistent
```

Expected: `error: prototypes/nonexistent does not exist` (exit 1).

Do NOT run `make deploy demandes` yet — Scaleway container isn't prepared for the new image path until Task A.5.

- [ ] **Step 6: Commit**

```bash
git add Makefile
git commit -m "add Makefile with 10 operator targets"
```

---

## Task A.4: Rewrite both GitHub Actions workflows

**Files:**
- Modify: `.github/workflows/ci.yml`
- Modify: `.github/workflows/deploy.yml`

- [ ] **Step 1: Rewrite `.github/workflows/ci.yml`**

File: `.github/workflows/ci.yml`
```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v5

      - name: Lint
        run: uvx ruff check prototypes/

      - name: Check formatting
        run: uvx ruff format --check prototypes/
```

`_template/` is added to these lint paths in Phase B Task B.1 (same commit that creates `_template/`).

- [ ] **Step 2: Rewrite `.github/workflows/deploy.yml`**

File: `.github/workflows/deploy.yml`
```yaml
name: Deploy

on:
  push:
    branches: [main]
    paths: ['prototypes/**']
  workflow_dispatch:
    inputs:
      proto:
        description: 'Proto name to deploy (leave blank to auto-detect from diff)'
        required: false

permissions:
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 2

      - name: Install Scaleway CLI
        run: |
          SCW_URL=$(curl -fsSL https://api.github.com/repos/scaleway/scaleway-cli/releases/latest | grep -o 'https://[^"]*linux_amd64' | head -1)
          curl -fsSL "$SCW_URL" -o /usr/local/bin/scw
          chmod +x /usr/local/bin/scw

      - name: Configure Scaleway CLI
        env:
          SCW_ACCESS_KEY: ${{ secrets.SCW_ACCESS_KEY }}
          SCW_SECRET_KEY: ${{ secrets.SCW_SECRET_KEY }}
        run: |
          scw init secret-key="$SCW_SECRET_KEY" access-key="$SCW_ACCESS_KEY" \
            organization-id="${{ secrets.SCW_ORG_ID }}" \
            project-id="${{ secrets.SCW_PROJECT_ID }}" \
            send-telemetry=false with-ssh-key=false install-autocomplete=false

      - name: Login to Scaleway container registry
        env:
          SCW_SECRET_KEY: ${{ secrets.SCW_SECRET_KEY }}
          SCW_REGISTRY: ${{ secrets.SCW_REGISTRY }}
        run: |
          docker login "${SCW_REGISTRY%%/*}" -u nologin --password-stdin <<< "$SCW_SECRET_KEY"

      - name: Deploy changed protos
        env:
          SCW_REGISTRY: ${{ secrets.SCW_REGISTRY }}
        run: |
          set -euo pipefail
          if [ -n "${{ github.event.inputs.proto }}" ]; then
            protos="${{ github.event.inputs.proto }}"
          else
            protos=$(git diff --name-only HEAD^ HEAD \
              | grep -oE '^prototypes/[^/]+' \
              | sed 's|^prototypes/||' \
              | sort -u)
          fi
          if [ -z "$protos" ]; then
            echo "No protos changed, nothing to deploy."
            exit 0
          fi
          for proto in $protos; do
            if [ ! -d "prototypes/$proto" ]; then
              echo "Skipping $proto (directory does not exist)"
              continue
            fi
            echo "::group::Deploying $proto"
            make deploy "$proto"
            echo "::endgroup::"
          done
```

**Important note on `SCW_REGISTRY` secret shape:** the `SCW_REGISTRY` GitHub secret must be the **namespace path only** (e.g. `rg.fr-par.scw.cloud/ns`), not a full image reference with a trailing image name. Phase A Task A.5 includes a verification step for this.

- [ ] **Step 3: Verify YAML syntax**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml')); yaml.safe_load(open('.github/workflows/deploy.yml')); print('ok')"
```

Expected: `ok`

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/
git commit -m "rewrite CI and deploy workflows for factory layout"
```

---

## Task A.5: Prepare Scaleway container for new image path

**Files:** (none — operator actions against live infrastructure)

The existing Scaleway container currently pulls `$SCW_REGISTRY:latest` (single-app pattern, e.g. `rg.fr-par.scw.cloud/ns/fluo-proto:latest`). After Phase A, it must pull `$SCW_REGISTRY/demandes:latest` (factory pattern). Three operator actions in strict order to avoid a window where the container references a nonexistent image:

1. **Verify `SCW_REGISTRY` shape** (read-only).
2. **Push the new image tag** to the registry (so the tag exists before we point at it).
3. **Update the container's `registry-image`** to the new path (now safe).
4. **Redeploy** to pull + run the new tag as a sanity check.

This ordering matters: if the container's registry-image pointer is updated BEFORE the new image exists, an auto-scale event between the two steps would try to pull a nonexistent image and fail the container.

- [ ] **Step 1: Verify `SCW_REGISTRY` is namespace-only**

```bash
grep SCW_REGISTRY ~/.config/scw/proto-db.env
```

Two possibilities:
- **Namespace only** (e.g. `rg.fr-par.scw.cloud/fluo-proto`) — compatible, proceed.
- **Namespace + image name** (e.g. `rg.fr-par.scw.cloud/fluo-proto/fluo-proto`) — the trailing image name must be stripped.

If the secret bakes in an image name, stop and do these three things before continuing:
1. Edit `~/.config/scw/proto-db.env` locally: remove the trailing image name from `SCW_REGISTRY`.
2. Update the `SCW_REGISTRY` GitHub secret at the same URL: repo → Settings → Secrets and variables → Actions → `SCW_REGISTRY`. Replace the value with the namespace path only.
3. Confirm both match, then continue.

- [ ] **Step 2: Load SCW credentials and log in to the registry**

```bash
source ~/.config/scw/proto-db.env
docker login "${SCW_REGISTRY%%/*}" -u nologin -p "$SCW_SECRET_KEY"
```

Expected: `Login Succeeded`.

- [ ] **Step 3: Build and push the new image tag FIRST (before touching the container)**

```bash
docker buildx build --platform linux/amd64 \
  -t "$SCW_REGISTRY/demandes:latest" \
  prototypes/demandes --push
```

Expected: image pushed. Verify the tag exists:

```bash
scw registry image list -o json | jq -r '.[] | select(.name == "demandes") | .tags'
```

Expected: an array including `"latest"`.

- [ ] **Step 4: Now update the container's `registry-image` pointer**

```bash
scw container container update "$SCW_CONTAINER_ID" region=fr-par \
  registry-image="$SCW_REGISTRY/demandes:latest"
```

Expected: command succeeds. Verify:

```bash
scw container container get "$SCW_CONTAINER_ID" region=fr-par -o json | jq -r '.registry_image'
```

Expected: the new path.

- [ ] **Step 5: Redeploy to pull + run the new tag (sanity check)**

```bash
scw container container deploy "$SCW_CONTAINER_ID" region=fr-par
```

Expected: container redeploys. Wait ~20s, then check status:

```bash
scw container container get "$SCW_CONTAINER_ID" region=fr-par -o json | jq -r '.status'
```

Expected: `ready`.

- [ ] **Step 6: Visit the public URL and confirm the app still works**

Look up the URL:

```bash
scw container container get "$SCW_CONTAINER_ID" region=fr-par -o json | jq -r '.domain_name'
```

Open `https://<domain>/plie/orientations` in a browser. Expected: the orientation list renders normally. Verify a detail page works too.

No commit for this task — all steps run against live infrastructure, no repo changes.

---

## Task A.6: Push Phase A to main

**Files:** (none — push task)

- [ ] **Step 1: Final local verification**

```bash
make help
make lint
docker build --platform linux/amd64 -t demandes-verify prototypes/demandes
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/deploy.yml')); yaml.safe_load(open('.github/workflows/ci.yml'))"
```

All should succeed.

- [ ] **Step 2: Review the commits that will be pushed**

```bash
git log --oneline origin/main..HEAD
```

Expected commits (in order):
1. `move web/ into prototypes/demandes/ and extract ruff.toml`
2. `add demandes README`
3. `add Makefile with 10 operator targets`
4. `rewrite CI and deploy workflows for factory layout`

- [ ] **Step 3: Push**

```bash
git push origin main
```

- [ ] **Step 4: Watch the GitHub Actions runs**

```bash
gh run watch
```

Expected:
- `CI` workflow: `lint` job passes.
- `Deploy` workflow: `deploy` job runs (the push touched `prototypes/demandes/**`), detects `demandes` as changed, runs `make deploy demandes`, which builds + pushes `$SCW_REGISTRY/demandes:latest` and deploys the container.

Visit the public URL and confirm demandes still works as expected. If anything fails, do not proceed to Phase B — diagnose and fix in Phase A.

---

# Phase B — Factory tooling, `_template/`, docs

Goal: by the end of Phase B, an agent can run `make new recs` and scaffold a working new proto from the template.

## Task B.1: Create `_template/` and extend CI + Makefile to lint it

**Files:**
- Create: `_template/` (entire directory tree, from stripped copy of `prototypes/demandes/`)
- Modify: `.github/workflows/ci.yml` (add `_template/` to lint paths)
- Modify: `Makefile` (add `_template/` to the `lint` and `fmt` targets)

- [ ] **Step 1: Copy demandes to `_template/` as starting point and remove caches**

```bash
cp -r prototypes/demandes _template
rm -rf _template/web/routes/__pycache__ _template/web/__pycache__
```

- [ ] **Step 2: Remove demandes-specific files that won't be reused**

```bash
rm -f _template/web/solutions.py
rm -rf _template/web/templates/prescripteur
rm -f _template/web/templates/orientation_detail.html \
      _template/web/templates/orientation_list.html \
      _template/web/templates/beneficiaire_detail.html \
      _template/web/templates/beneficiaire_list.html \
      _template/web/templates/orienteur_reply.html
rm -rf _template/web/templates/includes
rm -rf _template/web/routes
mkdir -p _template/web/routes
```

- [ ] **Step 3: Replace `web/models.py` with a minimal model**

Overwrite `_template/web/models.py`:
```python
from sqlmodel import Field, SQLModel


class Item(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
```

- [ ] **Step 4: Replace `web/seed.py` with a minimal seed**

Overwrite `_template/web/seed.py`:
```python
from sqlmodel import Session

from .database import engine, init_db
from .models import Item


def seed() -> None:
    init_db()
    with Session(engine) as session:
        session.add(Item(name="hello"))
        session.commit()


if __name__ == "__main__":
    seed()
    print("Seeded.")
```

- [ ] **Step 5: Replace `web/config.py` with a Jinja template**

Remove the copy inherited from demandes and write the template version directly:

```bash
rm _template/web/config.py
```

Create `_template/web/config.py.jinja`:
```python
import os

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://{{ proto_name }}:{{ proto_name }}@localhost:5432/{{ proto_name }}",
)

SERVICE_NAME = "{{ proto_name }}"
```

- [ ] **Step 6: Create `web/routes/__init__.py` and `web/routes/hello.py`**

File: `_template/web/routes/__init__.py`
```python
from .hello import router as hello_router

__all__ = ["hello_router"]
```

File: `_template/web/routes/hello.py`
```python
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def hello(request: Request):
    return request.app.state.templates.TemplateResponse(
        "hello.html",
        {"request": request},
    )
```

- [ ] **Step 7: Replace `web/app.py` with a minimal version**

Overwrite `_template/web/app.py`:
```python
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .database import init_db
from .routes import hello_router

_dir = Path(__file__).parent

app = FastAPI()
app.mount("/static", StaticFiles(directory=_dir / "static"), name="static")

templates = Jinja2Templates(directory=_dir / "templates")
app.state.templates = templates

init_db()
app.include_router(hello_router)
```

- [ ] **Step 8: Replace `web/templates/` content with `base.html` (verbatim from demandes) and a minimal `hello.html`**

`base.html` comes through verbatim from the `cp -r` in Step 1 (design system, header, banner, sidebar — unchanged across all protos). Just create a new `hello.html`:

File: `_template/web/templates/hello.html`
```html
{% extends "base.html" %}
{% block content %}
<section class="s-title-02">
    <div class="s-title-02__container container">
        <div class="s-title-02__row row">
            <div class="s-title-02__col col-12">
                <div class="c-title">
                    <div class="c-title__main">
                        <h1>Hello</h1>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>
{% endblock %}
```

- [ ] **Step 9: Convert `pyproject.toml`, `docker-compose.yml`, `README.md` to Jinja templates**

```bash
mv _template/pyproject.toml _template/pyproject.toml.jinja
mv _template/docker-compose.yml _template/docker-compose.yml.jinja
rm -f _template/README.md  # the demandes README copied in is wrong for _template
```

Edit `_template/pyproject.toml.jinja`. Replace the first three lines:
```toml
[project]
name = "fluo-proto"
version = "0.1.0"
```
with:
```toml
[project]
name = "{{ proto_name }}"
version = "0.1.0"
```

Edit `_template/docker-compose.yml.jinja`. Replace:
```yaml
      POSTGRES_DB: fluo
      POSTGRES_USER: fluo
      POSTGRES_PASSWORD: fluo
```
with:
```yaml
      POSTGRES_DB: {{ proto_name }}
      POSTGRES_USER: {{ proto_name }}
      POSTGRES_PASSWORD: {{ proto_name }}
```

Create `_template/README.md.jinja`:
```markdown
# {{ proto_name }}

{{ description }}

## Run locally

```bash
make dev {{ proto_name }}
```

## Deploy

```bash
make deploy {{ proto_name }}
```

See `../../PROTOTYPE.md` for provisioning, auth recipe, destroy and eject snippets.
```

- [ ] **Step 10: Verify `_template/` structure**

```bash
find _template -type f | sort
```

Expected paths include:
- `_template/.dockerignore`
- `_template/Dockerfile`
- `_template/README.md.jinja`
- `_template/docker-compose.yml.jinja`
- `_template/pyproject.toml.jinja`
- `_template/uv.lock`
- `_template/web/__init__.py`
- `_template/web/app.py`
- `_template/web/config.py.jinja`
- `_template/web/database.py`
- `_template/web/models.py`
- `_template/web/routes/__init__.py`
- `_template/web/routes/hello.py`
- `_template/web/seed.py`
- `_template/web/templates/base.html`
- `_template/web/templates/hello.html`
- (plus ~4MB under `_template/web/static/`)

Verify no demandes-specific files leaked through:
```bash
find _template -name 'orientation*' -o -name 'beneficiaire*' -o -name 'prescripteur*' -o -name 'solutions.py'
```

Expected: empty output.

- [ ] **Step 11: Extend CI + Makefile to lint `_template/`**

Edit `.github/workflows/ci.yml`. Change:
```yaml
      - name: Lint
        run: uvx ruff check prototypes/

      - name: Check formatting
        run: uvx ruff format --check prototypes/
```
to:
```yaml
      - name: Lint
        run: uvx ruff check prototypes/ _template/

      - name: Check formatting
        run: uvx ruff format --check prototypes/ _template/
```

Edit `Makefile`. Update the `lint` and `fmt` targets:

Replace:
```make
lint: ## Run ruff lint + format check on all protos
	@uvx ruff check prototypes/
	@uvx ruff format --check prototypes/

fmt: ## Run ruff format on all protos
	@uvx ruff format prototypes/
```
with:
```make
lint: ## Run ruff lint + format check on all protos and the template
	@uvx ruff check prototypes/ _template/
	@uvx ruff format --check prototypes/ _template/

fmt: ## Run ruff format on all protos and the template
	@uvx ruff format prototypes/ _template/
```

- [ ] **Step 12: Verify lint passes across both paths**

```bash
make lint
```

Expected: passes with no errors. If `_template/web/` has any lint issues introduced during the strip-and-replace, fix them in place.

Note: `ruff` by default ignores `.jinja` files (they aren't Python syntax), so the `.jinja` extensions on `pyproject.toml.jinja`, `config.py.jinja`, etc. don't need special handling. Verify:

```bash
uvx ruff check _template/web/config.py.jinja 2>&1 | head -5
```

Expected: ruff either skips the file or treats it as an unknown format. Either way, `make lint` should pass.

- [ ] **Step 13: Commit**

```bash
git add _template .github/workflows/ci.yml Makefile
git commit -m "add _template scaffold and extend lint paths"
```

---

## Task B.2: Add `copier.yml`

**Files:**
- Create: `copier.yml`

- [ ] **Step 1: Create the copier config**

File: `copier.yml`
```yaml
_subdirectory: _template
_templates_suffix: .jinja

proto_name:
  type: str
  help: "Proto name (lowercase, DNS-safe, 2-31 chars)"
  validator: >-
    {% if not (proto_name | regex_search('^[a-z][a-z0-9-]{1,30}$')) %}
    Must match ^[a-z][a-z0-9-]{1,30}$
    {% endif %}

description:
  type: str
  help: "One-line description"
  default: ""
```

- [ ] **Step 2: Smoke-test copier end-to-end**

```bash
uvx copier copy . /tmp/copier-smoke-test --defaults --data proto_name=smoke --data description="smoke test"
```

Expected: copier runs, produces `/tmp/copier-smoke-test/` with rendered files.

```bash
cat /tmp/copier-smoke-test/pyproject.toml | head -5
```

Expected:
```
[project]
name = "smoke"
version = "0.1.0"
```

```bash
cat /tmp/copier-smoke-test/docker-compose.yml | grep POSTGRES_DB
```

Expected: `POSTGRES_DB: smoke`

```bash
cat /tmp/copier-smoke-test/web/config.py | grep -E '(DATABASE_URL|SERVICE_NAME)'
```

Expected: contains `postgresql+psycopg://smoke:smoke@...` and `SERVICE_NAME = "smoke"`.

Clean up:
```bash
rm -rf /tmp/copier-smoke-test
```

- [ ] **Step 3: Commit**

```bash
git add copier.yml
git commit -m "add copier.yml for proto scaffolding"
```

---

## Task B.3: Retarget `scripts/fetch-assets.sh`

**Files:**
- Modify: `scripts/fetch-assets.sh` (one-line change)

- [ ] **Step 1: Edit the `STATIC` path**

Open `scripts/fetch-assets.sh`. Change line 7 from:
```bash
STATIC="$(dirname "$0")/../web/static"
```
to:
```bash
STATIC="$(dirname "$0")/../_template/web/static"
```

- [ ] **Step 2: Verify the path resolves correctly**

```bash
realpath scripts/../_template/web/static
```

Expected: `/Users/louije/Development/gip/fluo-proto-factory/_template/web/static`

Do NOT run the full script — it needs a les-emplois checkout and would overwrite static assets.

- [ ] **Step 3: Commit**

```bash
git add scripts/fetch-assets.sh
git commit -m "retarget fetch-assets.sh at _template/web/static"
```

---

## Task B.4: Write `scripts/provision.sh`

**Files:**
- Create: `scripts/provision.sh`

- [ ] **Step 1: Create the provisioning script**

File: `scripts/provision.sh`
```bash
#!/bin/bash
# Create a Scaleway Serverless Container + PostgreSQL database for a new proto.
# Usage: scripts/provision.sh <proto_name>
#
# Reads credentials from ~/.config/scw/proto-db.env:
#   SCW_REGISTRY, SCW_SECRET_KEY, PROTO_DB_INSTANCE_ID, PROTO_DB_HOST,
#   PROTO_DB_PORT, SCW_NAMESPACE_ID (Serverless Container namespace)

set -euo pipefail

proto="${1:?usage: $0 <proto_name>}"

# shellcheck disable=SC1090
source ~/.config/scw/proto-db.env

: "${SCW_REGISTRY:?SCW_REGISTRY not set}"
: "${SCW_SECRET_KEY:?SCW_SECRET_KEY not set}"
: "${PROTO_DB_INSTANCE_ID:?PROTO_DB_INSTANCE_ID not set}"
: "${PROTO_DB_HOST:?PROTO_DB_HOST not set}"
: "${PROTO_DB_PORT:?PROTO_DB_PORT not set}"
: "${SCW_NAMESPACE_ID:?SCW_NAMESPACE_ID not set (Scaleway Serverless Container namespace)}"

echo "Provisioning proto: $proto"

# 1. Create DB user with random password
db_password=$(openssl rand -hex 24)
echo "Creating database user '$proto'..."
scw rdb user create instance-id="$PROTO_DB_INSTANCE_ID" name="$proto" password="$db_password"

# 2. Create database
echo "Creating database '$proto'..."
scw rdb database create instance-id="$PROTO_DB_INSTANCE_ID" name="$proto"

# 3. Grant privileges
echo "Granting privileges..."
scw rdb privilege set instance-id="$PROTO_DB_INSTANCE_ID" database-name="$proto" user-name="$proto" permission=all

# 4. Pre-seed the image tag (container create fails if image doesn't exist yet)
echo "Building and pushing initial image..."
docker login "${SCW_REGISTRY%%/*}" -u nologin -p "$SCW_SECRET_KEY"
docker buildx build --platform linux/amd64 \
  -t "$SCW_REGISTRY/$proto:latest" \
  "prototypes/$proto" --push

# 5. Create the Serverless Container
database_url="postgresql+psycopg://$proto:$db_password@$PROTO_DB_HOST:$PROTO_DB_PORT/$proto"
echo "Creating Scaleway Serverless Container '$proto'..."
scw container container create \
  namespace-id="$SCW_NAMESPACE_ID" \
  name="$proto" \
  registry-image="$SCW_REGISTRY/$proto:latest" \
  min-scale=1 \
  max-scale=3 \
  memory-limit=256 \
  cpu-limit=140 \
  privacy=public \
  port=8080 \
  protocol=http1 \
  environment-variables.DATABASE_URL="$database_url" \
  -o json > "/tmp/proto-container-$proto.json"

container_id=$(jq -r '.id' "/tmp/proto-container-$proto.json")
domain_name=$(jq -r '.domain_name' "/tmp/proto-container-$proto.json")
rm "/tmp/proto-container-$proto.json"

echo
echo "Provisioned:"
echo "  container_id: $container_id"
echo "  public URL:   https://$domain_name"
echo "  DB:           $proto"
echo
echo "Run 'make deploy $proto' to trigger the first real deploy."
```

- [ ] **Step 2: Make executable and verify syntax**

```bash
chmod +x scripts/provision.sh
bash -n scripts/provision.sh && echo "syntax ok"
```

Expected: `syntax ok`

- [ ] **Step 3: Commit**

```bash
git add scripts/provision.sh
git commit -m "add scripts/provision.sh"
```

---

## Task B.5: Extend `.githooks/pre-commit` with URL guard

**Files:**
- Modify: `.githooks/pre-commit` (full rewrite — existing content points at `web/` which no longer exists)

- [ ] **Step 1: Rewrite the hook**

Overwrite `.githooks/pre-commit`:
```sh
#!/bin/sh
set -e

# Lint and format-check all protos and the template (matches CI).
uvx ruff check prototypes/ _template/
uvx ruff format --check prototypes/ _template/

# Block Scaleway container URLs from being committed.
# docs/ is excluded so the spec can reference the pattern.
staged=$(git diff --cached --name-only --diff-filter=ACM | grep -v '^docs/' || true)
if [ -n "$staged" ]; then
  if echo "$staged" | xargs -I{} grep -l -E '[a-z0-9-]+\.functions\.fnc\.fr-par\.scw\.cloud' {} 2>/dev/null; then
    echo ""
    echo "error: Scaleway container URL found in staged files above."
    echo "       URLs must not be committed. Remove them and retry."
    exit 1
  fi
fi
```

- [ ] **Step 2: Verify executable and `core.hooksPath`**

```bash
ls -l .githooks/pre-commit
git config core.hooksPath
```

Expected: executable (`-rwxr-xr-x`), `core.hooksPath` = `.githooks`. If the config isn't set, run `git config core.hooksPath .githooks`.

- [ ] **Step 3: Smoke-test the URL guard with a temporary bad file**

```bash
echo "fake-proto-abc123.functions.fnc.fr-par.scw.cloud" > bad-url-test.txt
git add bad-url-test.txt
git commit -m "this should fail" || echo "HOOK BLOCKED COMMIT (expected)"
git reset HEAD bad-url-test.txt
rm bad-url-test.txt
```

Expected: the commit is blocked with the "Scaleway container URL found" error and `HOOK BLOCKED COMMIT (expected)` is printed.

- [ ] **Step 4: Commit the hook change**

```bash
git add .githooks/pre-commit
git commit -m "rewrite pre-commit hook: new lint paths + URL guard"
```

---

## Task B.6: Rename demandes local db from `fluo` to `demandes`

**Files:**
- Modify: `prototypes/demandes/docker-compose.yml`

The Makefile's `dev` target constructs `DATABASE_URL=postgresql+psycopg://<proto>:<proto>@localhost:5432/<proto>`. For `make dev demandes` to work, the local docker-compose PG must use `demandes`/`demandes`/`demandes` as db/user/password. This is local dev only — production uses `DATABASE_URL` from the Scaleway container env var, unaffected.

- [ ] **Step 1: Edit `prototypes/demandes/docker-compose.yml`**

Change:
```yaml
      POSTGRES_DB: fluo
      POSTGRES_USER: fluo
      POSTGRES_PASSWORD: fluo
```
to:
```yaml
      POSTGRES_DB: demandes
      POSTGRES_USER: demandes
      POSTGRES_PASSWORD: demandes
```

- [ ] **Step 2: Tear down the old local volume**

```bash
cd prototypes/demandes
docker compose down -v
cd ../..
```

The `-v` flag removes the `pgdata` volume so new credentials apply on next `up`.

- [ ] **Step 3: Verify `make dev demandes` starts cleanly, then seed**

```bash
make dev demandes &
MAKE_DEV_PID=$!
sleep 6
curl -fsS http://localhost:8002/plie/orientations > /dev/null && echo "uvicorn is up"
kill $MAKE_DEV_PID 2>/dev/null || true
```

Expected: `uvicorn is up`. (The list may be empty — no seed yet — but the endpoint responds 200.)

Then seed:
```bash
cd prototypes/demandes
DATABASE_URL=postgresql+psycopg://demandes:demandes@localhost:5432/demandes uv run python -m web.seed
cd ../..
```

Expected: seed script runs without error.

- [ ] **Step 4: Commit**

```bash
git add prototypes/demandes/docker-compose.yml
git commit -m "rename demandes local db from fluo to demandes"
```

---

## Task B.7: Rewrite top of `PROTOTYPE.md` and add auth recipe

**Files:**
- Modify: `PROTOTYPE.md` (prepend new factory-workflow section + auth recipe; keep the rest)

The existing `PROTOTYPE.md` (~1068 lines) describes the les-emplois design system and component patterns. All of that stays — it applies to every proto. What changes is the top section (was: "how to build a single prototype from scratch"; becomes: "how to build a proto in the factory") and a new inline auth recipe.

- [ ] **Step 1: Replace the top section**

Open `PROTOTYPE.md`. Replace lines 1–8 (the existing `# Building a les-emplois-like prototype` heading and the Overview paragraph) with the following block:

```markdown
# Building a proto in the fluo factory

This guide covers how to build a new prototype inside the `fluo-proto-factory` repo. Each proto is a self-contained FastAPI + Jinja2 + PostgreSQL app under `prototypes/<name>/`, visually identical to [les-emplois](https://github.com/gip-inclusion/les-emplois). The factory-root `_template/` directory holds the scaffold, and the `Makefile` exposes operator commands.

## Quickstart: create a new proto

From the factory root:

```bash
make new recs              # scaffolds prototypes/recs/ from _template/
make provision recs        # creates Scaleway container + PostgreSQL database
make dev recs              # starts local PG + uvicorn with hot reload
```

The first command prompts for a one-line description. The second uses credentials from `~/.config/scw/proto-db.env` to provision infrastructure.

## Deployment

Every push to `main` that touches `prototypes/<name>/` triggers a GitHub Actions deploy of that proto. Manual deploy from a laptop: `make deploy <name>` (requires `scw` CLI, docker login, `SCW_REGISTRY` sourced from `~/.config/scw/proto-db.env`).

## Local iteration

```bash
make dev recs              # hot reload on localhost:8002
make reseed recs           # drop + re-seed local DB
make lint                  # ruff check
make fmt                   # ruff format
```

## Seeing the URLs

```bash
make urls                  # prints name → Scaleway URL for all protos
```

URLs are not stored in the repo. The `.githooks/pre-commit` hook blocks any attempt to commit a Scaleway container URL.

## Destroying a proto

Destructive. Run by hand:

\`\`\`sh
source ~/.config/scw/proto-db.env
scw container container delete $(scw container container list name=<name> -o json | jq -r '.[0].id')
scw rdb database delete instance-id=$PROTO_DB_INSTANCE_ID name=<name>
scw rdb user delete instance-id=$PROTO_DB_INSTANCE_ID name=<name>
git rm -r prototypes/<name>
git commit -m "destroy <name>"
git push
\`\`\`

## Ejecting a proto to its own repo

When a throwaway graduates to a keeper:

\`\`\`sh
git clone . ../<name>-ejected
cd ../<name>-ejected
git filter-repo --subdirectory-filter prototypes/<name> --to-subdirectory-filter .
gh repo create <name> --private --source . --push
# Then copy factory-level Scaleway secrets into the new repo and add a standalone deploy workflow.
\`\`\`

## If your proto needs auth

Most throwaway protos run with `privacy=public` and the obscure Scaleway URL is the only protection. If you need real auth for user testing, wrap your proto's image in oauth2-proxy.

1. **Replace your proto's `Dockerfile`** with the version below. It installs tini (to reap zombies) and oauth2-proxy, and launches both processes via an entrypoint script:

\`\`\`dockerfile
FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

RUN apt-get update && apt-get install -y --no-install-recommends tini ca-certificates curl \\
 && rm -rf /var/lib/apt/lists/*

ADD https://github.com/oauth2-proxy/oauth2-proxy/releases/download/v7.15.1/oauth2-proxy-v7.15.1.linux-amd64.tar.gz /tmp/
RUN tar -xzf /tmp/oauth2-proxy-v7.15.1.linux-amd64.tar.gz -C /tmp \\
 && mv /tmp/oauth2-proxy-v7.15.1.linux-amd64/oauth2-proxy /usr/local/bin/ \\
 && rm -rf /tmp/oauth2-proxy-v7.15.1.linux-amd64*

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache --no-install-project
COPY . .
RUN uv sync --frozen --no-cache

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
EXPOSE 8080
ENTRYPOINT ["tini", "--"]
CMD ["/entrypoint.sh"]
\`\`\`

2. **Add `prototypes/<name>/entrypoint.sh`:**

\`\`\`sh
#!/bin/sh
set -e
.venv/bin/uvicorn web.app:app --host 127.0.0.1 --port 8000 &
exec oauth2-proxy \\
  --http-address=0.0.0.0:8080 \\
  --upstream=http://127.0.0.1:8000 \\
  --reverse-proxy=true \\
  --skip-provider-button=true \\
  --cookie-secure=true \\
  --cookie-httponly=true \\
  --cookie-samesite=lax
\`\`\`

3. **Set oauth2-proxy env vars on the Scaleway container** (not in the repo):

\`\`\`sh
source ~/.config/scw/proto-db.env
container_id=$(scw container container list name=<name> -o json | jq -r '.[0].id')
scw container container update "$container_id" region=fr-par \\
  environment-variables.OAUTH2_PROXY_CLIENT_ID=... \\
  environment-variables.OAUTH2_PROXY_CLIENT_SECRET=... \\
  environment-variables.OAUTH2_PROXY_COOKIE_SECRET="$(openssl rand -base64 32 | tr -- '+/' '-_' | tr -d '=')" \\
  environment-variables.OAUTH2_PROXY_OIDC_ISSUER_URL=https://accounts.google.com \\
  environment-variables.OAUTH2_PROXY_EMAIL_DOMAINS=your-org.fr
\`\`\`

4. **Add the callback URL to the Google OAuth client.** After provisioning, visit the Google Cloud Console → APIs & Services → Credentials → your OAuth 2.0 Client ID → Authorized redirect URIs, and add `https://<proto-url>/oauth2/callback`. Google does not expose a public API for this — it is manual.

5. **Redeploy:** `make deploy <name>`.

---

(The rest of this document describes the les-emplois design system — component patterns, template structure, common pitfalls. It applies to every proto regardless of auth.)
```

- [ ] **Step 2: Verify the rest of `PROTOTYPE.md` is untouched**

```bash
wc -l PROTOTYPE.md
grep -c "^## " PROTOTYPE.md
```

Expected: file is significantly longer than 1068 lines (the new section adds ~130 lines). Several `## ` headings appear from the existing content.

- [ ] **Step 3: Commit**

```bash
git add PROTOTYPE.md
git commit -m "rewrite PROTOTYPE.md top for factory workflow + auth recipe"
```

---

## Task B.8: Rewrite `CLAUDE.md` for factory context

**Files:**
- Modify: `CLAUDE.md` (full rewrite)

- [ ] **Step 1: Overwrite `CLAUDE.md`**

File: `CLAUDE.md`
```markdown
# Fluo Proto Factory

Monorepo that produces throwaway prototypes for product design, user testing, and fast iteration. Each prototype lives under `prototypes/<name>/` as a self-contained FastAPI + Jinja2 + PostgreSQL app visually identical to [les-emplois](https://github.com/gip-inclusion/les-emplois).

"Fluo" is the overall endeavour. Individual protos are named after what they explore (e.g., `demandes` for orientation requests, `recs` for recommendations, etc.).

## Layout

```
fluo-proto-factory/
├── _template/            — the scaffold (copied into each new proto by copier)
├── prototypes/           — one subdirectory per proto, fully self-contained
│   └── demandes/         — orientation requests for PLIE Lille Avenir
├── Makefile              — operator commands (make help lists them)
├── copier.yml            — copier config for `make new`
├── ruff.toml             — shared lint config
├── scripts/              — provision.sh, fetch-assets.sh
├── .githooks/pre-commit  — lint + URL guard
├── PROTOTYPE.md          — the guide for building a new proto (read this)
└── .github/workflows/    — CI (lint) and deploy (per-proto)
```

## Isolation

- Each proto has its own `Dockerfile`, `pyproject.toml`, `uv.lock`, `docker-compose.yml`, and DB. Nothing is shared at runtime.
- Static assets (~4 MB) are duplicated per proto — frozen at creation time.
- Editing `_template/` has zero effect on existing protos. No propagation.
- Each proto has its own PostgreSQL database on a shared Scaleway RDB instance.

## Creating a new proto

See `PROTOTYPE.md`. TL;DR:

```bash
make new recs              # scaffold from _template/
make provision recs        # create Scaleway container + DB
make dev recs              # run locally with hot reload
```

## Local dev

```bash
make dev <proto>           # hot reload on localhost:8002
make reseed <proto>        # drop + re-seed local DB
make lint                  # ruff check
make fmt                   # ruff format
```

## Deploy

Push to `main` → GitHub Actions detects which protos changed and runs `make deploy <proto>` for each. Manual: `make deploy <proto>` from a laptop (requires `scw` CLI, docker login, `SCW_REGISTRY` from `~/.config/scw/proto-db.env`).

## Infrastructure

- **Database:** Scaleway Managed PostgreSQL `proto-db` (shared instance, one database per proto).
- **Containers:** Scaleway Serverless Containers (one per proto, 256 MB / 140 mVCPU / min-scale=1 / privacy=public).
- **Registry:** Scaleway Container Registry (one image per proto, tagged by proto name).
- **Secrets:** factory-level GitHub secrets cover all protos. Operator credentials live in `~/.config/scw/proto-db.env` (never in the repo).
- **DATABASE_URL** is set on each Scaleway container at provision time, never in the repo.

## URL privacy

Public proto URLs are **not** stored in the repo. The pre-commit hook blocks any attempt to commit a `*.functions.fnc.fr-par.scw.cloud` URL. Use `make urls` to list all current URLs locally.

## Commit rules

- Atomic, one-line commits.
- No "co-authored by Claude" trailers.
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "rewrite CLAUDE.md for factory context"
```

---

## Task B.9: Add factory root `README.md`

**Files:**
- Create (or overwrite): `README.md`

- [ ] **Step 1: Write `README.md`**

File: `README.md`
```markdown
# fluo-proto-factory

Monorepo that produces throwaway prototypes for product design, user testing, and fast iteration at [Plateforme de l'inclusion](https://inclusion.gouv.fr). Each prototype looks identical to [les-emplois](https://github.com/gip-inclusion/les-emplois) but implements different domain logic.

See [`PROTOTYPE.md`](PROTOTYPE.md) to build a new proto, and [`CLAUDE.md`](CLAUDE.md) for the factory layout.

## Quick start

```bash
make new <name>            # scaffold from _template/
make provision <name>      # create Scaleway container + DB
make dev <name>            # hot reload on localhost:8002
make deploy <name>         # build + push + deploy
```

`make help` lists all targets.
```

No prototypes list — deliberate. The `prototypes/` directory is the list.

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "add factory README"
```

---

## Task B.10: End-to-end smoke test with a throwaway `smoke` proto

**Files:** (none committed — verification task, cleanup at the end)

- [ ] **Step 1: Scaffold a smoke-test proto**

```bash
uvx copier copy . prototypes/smoke --defaults --data proto_name=smoke --data description="end-to-end smoke test"
```

(Invokes copier directly rather than `make new smoke`, because `make new` runs copier in interactive mode — we want non-interactive for the smoke test.)

- [ ] **Step 2: Verify rendered output**

```bash
ls prototypes/smoke/
head -3 prototypes/smoke/pyproject.toml
grep POSTGRES_DB prototypes/smoke/docker-compose.yml
grep SERVICE_NAME prototypes/smoke/web/config.py
head -3 prototypes/smoke/README.md
```

Expected:
- `pyproject.toml` → `name = "smoke"`
- `docker-compose.yml` → `POSTGRES_DB: smoke`
- `web/config.py` → `SERVICE_NAME = "smoke"`
- `README.md` → starts with `# smoke`

- [ ] **Step 3: Lint the new proto**

```bash
make lint
```

Expected: passes.

- [ ] **Step 4: Verify Docker build**

```bash
docker build --platform linux/amd64 -t smoke-verify prototypes/smoke
```

Expected: successful build — confirms the template produces a valid, buildable proto.

- [ ] **Step 5: Clean up**

```bash
rm -rf prototypes/smoke
docker rmi smoke-verify 2>/dev/null || true
```

- [ ] **Step 6: Verify working tree is clean**

```bash
git status --short
```

Expected: no untracked files under `prototypes/smoke/`. (The smoke proto was never committed.)

No commit for this task.

---

## Task B.11: Push Phase B to main

**Files:** (none — push task)

- [ ] **Step 1: Review the commits that will be pushed**

```bash
git log --oneline origin/main..HEAD
```

Expected commits (in order):
1. `add _template scaffold and extend lint paths`
2. `add copier.yml for proto scaffolding`
3. `retarget fetch-assets.sh at _template/web/static`
4. `add scripts/provision.sh`
5. `rewrite pre-commit hook: new lint paths + URL guard`
6. `rename demandes local db from fluo to demandes`
7. `rewrite PROTOTYPE.md top for factory workflow + auth recipe`
8. `rewrite CLAUDE.md for factory context`
9. `add factory README`

- [ ] **Step 2: Final verification**

```bash
make help
make lint
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml')); yaml.safe_load(open('.github/workflows/deploy.yml')); print('ok')"
docker build --platform linux/amd64 -t demandes-final prototypes/demandes
```

All should succeed.

- [ ] **Step 3: Verify no Scaleway URLs leaked into tracked files**

```bash
git grep -nE '[a-z0-9-]+\.functions\.fnc\.fr-par\.scw\.cloud' -- ':!docs/' || echo "CLEAN"
```

Expected: `CLEAN`. Hits under `docs/` are fine — the spec references the pattern.

- [ ] **Step 4: Push**

```bash
git push origin main
```

- [ ] **Step 5: Watch the GitHub Actions run**

```bash
gh run watch
```

Expected:
- `CI` workflow passes (lint on both `prototypes/` and `_template/`).
- `Deploy` workflow: Phase B touches `prototypes/demandes/docker-compose.yml`, so the path filter matches and the deploy job runs. `make deploy demandes` rebuilds and redeploys. The rebuild is effectively a no-op for production (only the local docker-compose credentials changed, which affect local dev only). Verify the public URL still works.

---

## Self-review

- **Spec coverage:** every section of the spec maps to at least one task.
  - Repo layout → A.1, B.1, B.9
  - Isolation model → enforced by design
  - Per-proto configuration → A.3 (Makefile deploy target looks up container by name), B.4 (`provision.sh` sets DATABASE_URL on container)
  - Makefile → A.3 (full 10 targets) + B.1 (lint path extension)
  - Copier template → B.1 + B.2
  - Dockerfile (single, no auth) → preserved as-is from demandes
  - Auth recipe → B.7 (in PROTOTYPE.md)
  - GitHub Actions ci.yml → A.4 + B.1 (lint path extension)
  - GitHub Actions deploy.yml → A.4
  - Pre-commit hook → B.5
  - Migration → A.1, A.2, A.3, A.4, A.5, A.6
  - Destroy/eject snippets → B.7 (in PROTOTYPE.md)
  - Acceptance criteria → exercised by B.10 (smoke test) and B.11 (push + deploy)
- **Placeholder scan:** no "TBD", "TODO", "implement later", "similar to Task N".
- **Type consistency:** Make target names match across Makefile, PROTOTYPE.md, CLAUDE.md, README.md, and acceptance criteria: `help`, `new`, `provision`, `deploy`, `dev`, `reseed`, `urls`, `lint`, `fmt`, `update-assets`.
- **Known gotchas flagged explicitly:**
  - `SCW_REGISTRY` must be namespace-only (A.5 Step 1)
  - Scaleway container image-path transition ordering: push image BEFORE updating `registry-image` pointer (A.5 Steps 3–4)
  - demandes docker-compose credentials rename requires `docker compose down -v` (B.6)
  - `_template/` must exist before CI and Makefile reference it (B.1 Step 11 updates both in the same commit)
