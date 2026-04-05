# Proto-factory design

**Date:** 2026-04-05
**Status:** Approved, ready for implementation planning
**Scope:** Restructure `fluo-proto-factory` from a single-prototype app into a factory that produces independent, throwaway prototypes from a shared scaffold. (fluo = the overall endeavour; each prototype lives under `prototypes/<name>/`. The current app becomes `prototypes/demandes/`.)

## Goals

- Multiple prototypes live side-by-side in one repo, each fully self-contained.
- An agent can create a new prototype from a template with minimal friction.
- Each prototype has its own Scaleway Serverless Container and its own PostgreSQL database on the shared Scaleway RDB instance.
- Each prototype deploys independently on push to main.
- The template can improve over time; improvements **never** propagate to existing prototypes.
- Protos are throwaway by default; a rare "keeper" can be ejected to its own standalone repo.

## Non-goals

- No shared runtime code between prototypes. No `core/` Python package that protos import from.
- No auth in the core spec. Protos that need auth follow a recipe in `PROTOTYPE.md` to add oauth2-proxy on their own.
- No automatic regression testing across protos. Template changes do not re-validate existing protos.
- No migration framework. `SQLModel.metadata.create_all()` on startup; schema changes during iteration = drop and reseed.
- No per-proto GitHub secrets. One factory-level set of Scaleway credentials covers all protos.
- No root `README.md` proto list. The `prototypes/` directory is the list.

## Repo layout

```
fluo-proto-factory/
├── README.md                       # one-paragraph factory description
├── PROTOTYPE.md                    # guide for agents (build, deploy, destroy, eject, auth recipe)
├── CLAUDE.md                       # factory-level agent instructions
├── Makefile                        # operator commands (new, provision, deploy, help)
├── copier.yml                      # copier template config
├── ruff.toml                       # shared lint config; ruff walks up the tree
├── .gitignore
├── .githooks/
│   └── pre-commit                  # URL grep (blocks Scaleway URLs from being committed)
├── _template/                      # copier source (Jinja placeholders)
│   ├── web/
│   │   ├── app.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models.py               # minimal example
│   │   ├── seed.py                 # minimal example
│   │   ├── routes/
│   │   │   └── hello.py
│   │   ├── templates/
│   │   │   ├── base.html
│   │   │   └── includes/
│   │   └── static/                 # frozen copy of theme-inclusion + bootstrap + itou.css
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── docker-compose.yml
│   ├── .dockerignore
│   └── README.md
├── prototypes/
│   └── demandes/                   # current app, migrated here, fully self-contained
│       ├── web/
│       ├── Dockerfile
│       ├── pyproject.toml
│       ├── uv.lock
│       ├── docker-compose.yml
│       ├── .dockerignore
│       └── README.md
├── scripts/
│   └── fetch-assets.sh             # refreshes _template/web/static from a local les-emplois clone
└── .github/workflows/
    ├── ci.yml                      # single ruff command at factory root
    └── deploy.yml                  # bash loop over changed protos
```

## Isolation model

**Copied into each proto at creation, frozen forever:**
- Entire `web/` subtree
- Static assets (~4 MB) — duplicated per proto; disk is cheap, ejection is trivial
- `Dockerfile`, `pyproject.toml`, `uv.lock`, `docker-compose.yml`, `README.md`

**Stays at factory root, shared tooling only:**
- `Makefile`, `copier.yml`, `ruff.toml`, `PROTOTYPE.md`, `CLAUDE.md`, `.github/workflows/*`, `.githooks/*`
- Dev-time / CI-time artifacts. Prototypes never import or read them at runtime.

**Not shared at all:**
- No `core/` Python package. No runtime imports across the proto boundary.
- Each proto has its own `.venv`, its own `pyproject.toml`, its own `uv.lock`. Per-proto lockfile, strict freezing.
- Each proto has its own PostgreSQL database on the shared Scaleway RDB instance.

**Consequence:** editing `_template/` or `ruff.toml` has zero effect on any existing proto.

## Per-proto configuration

**Nothing committed per-proto** beyond the proto's own code. Everything derives from the directory name `prototypes/<name>/`:

- Container name = `<name>`
- DB name = `<name>`
- DB user = `<name>`
- Image tag = `<SCW_REGISTRY>/<name>:latest`
- Container ID = looked up at deploy time via `scw container container list name=<name>`, never stored in git.
- Public URL = queried on demand via `scw container container list`, never stored in a file.

**Set on the Scaleway container at provision time, never in git:**
- `DATABASE_URL=postgresql+psycopg://<name>:<pass>@<host>:<port>/<name>`

**Source of truth for container resources** (memory, CPU, min-scale, privacy): the Scaleway container itself. Change via `scw container container update`. Defaults: 256 MB / 140 mVCPU / min-scale=1 / privacy=public.

**Factory-level GitHub secrets** (one set, shared):
- `SCW_ACCESS_KEY`, `SCW_SECRET_KEY`, `SCW_REGISTRY`, `SCW_PROJECT_ID`, `SCW_ORG_ID`
- `PROTO_DB_INSTANCE_ID`, `PROTO_DB_HOST`, `PROTO_DB_PORT`, `PROTO_DB_ADMIN_USER`, `PROTO_DB_ADMIN_PASSWORD` (used by `make provision` only)

## Makefile (operator interface)

Self-documenting via `make help`. Ten targets. **All arguments are positional** — `make dev demandes`, not `make dev PROTO=demandes` — via the standard `MAKECMDGOALS` + catch-all `%: @:` idiom:

```make
ARGS := $(filter-out $@,$(MAKECMDGOALS))
%:
	@:
```

Each target that takes an argument uses `$(firstword $(ARGS))` to read it and fails with a usage message if empty.

| Target | What it does |
|---|---|
| `make help` | Print targets with one-line descriptions. |
| `make new <name>` | `uvx copier copy _template prototypes/<name>` with prompts. |
| `make provision <name>` | Create SCW RDB database + user, create SCW container (name=`<name>`, privacy=public), set `DATABASE_URL` env var on the container. Print the generated URL. |
| `make deploy <name>` | Build image, push to registry, look up container ID by name, `scw container container deploy <id>`. |
| `make dev <name>` | Start the proto's local docker-compose PG and run uvicorn with `--reload` against it. The daily iteration command. |
| `make reseed <name>` | Drop + recreate the proto's DB tables in the **local** docker-compose PG and re-run its seed script. Never touches prod. |
| `make urls` | `scw container container list -o json \| jq -r '.[] \| "\(.name)\t\(.domain_name)"'`. Local output only, never captured to a file. |
| `make lint` | `uvx ruff check prototypes/ _template/` — same command CI runs. |
| `make fmt` | `uvx ruff format prototypes/ _template/`. |
| `make update-assets <path-to-les-emplois>` | Run `scripts/fetch-assets.sh` against a local les-emplois clone. Refreshes `_template/web/static/` only; existing protos keep their frozen copies. |

Not in the Makefile: `logs` (`scw container container logs <name>` is short enough, learned once), destroy, eject — the last two stay as documented snippets in `PROTOTYPE.md` because they are destructive or rare and deserve the friction of being read before being run.

## Copier template

`copier.yml` at factory root, ~15 lines:

```yaml
_subdirectory: _template
proto_name:
  type: str
  help: "Proto name (lowercase, DNS-safe)"
  validator: >-
    {% if not (proto_name | regex_search('^[a-z][a-z0-9-]{1,30}$')) %}
    Must match ^[a-z][a-z0-9-]{1,30}$
    {% endif %}
description:
  type: str
  help: "One-line description"
```

Jinja placeholders `{{ proto_name }}` and `{{ description }}` are substituted into `pyproject.toml`, `docker-compose.yml`, `README.md`. No conditional files. No `has_auth` question (auth is a separate recipe).

## Dockerfile (single, minimal, no auth)

Same shape as the current `demandes` Dockerfile — no changes from today's pattern:

```dockerfile
FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache --no-install-project
COPY . .
RUN uv sync --frozen --no-cache
EXPOSE 8080
CMD [".venv/bin/uvicorn", "web.app:app", "--host", "0.0.0.0", "--port", "8080"]
```

uvicorn runs as PID 1 and handles `SIGTERM` on its own. No tini, no entrypoint script, no oauth2-proxy binary.

## Auth recipe (documented in PROTOTYPE.md, not in core)

`PROTOTYPE.md` carries a section titled "If your proto needs auth" with:

1. Replace `Dockerfile` with a variant that installs `tini` + downloads `oauth2-proxy` + copies an `entrypoint.sh` that launches uvicorn on loopback and execs oauth2-proxy in front.
2. Add `OAUTH2_PROXY_CLIENT_ID`, `OAUTH2_PROXY_CLIENT_SECRET`, `OAUTH2_PROXY_COOKIE_SECRET`, `OAUTH2_PROXY_EMAIL_DOMAINS`, `OAUTH2_PROXY_OIDC_ISSUER_URL` as env vars on that proto's Scaleway container.
3. Paste the proto's `<url>/oauth2/callback` into the Google OAuth client's authorized redirect URIs (manual — Google does not expose a public API for this).
4. Redeploy.

This lives in `PROTOTYPE.md` as copy-pasteable snippets. The core spec, `_template/`, `copier.yml`, and `Makefile` carry zero auth code. Factory complexity stays put.

## GitHub Actions

### `.github/workflows/ci.yml`

```yaml
name: ci
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uvx ruff check prototypes/ _template/
      - run: uvx ruff format --check prototypes/ _template/
```

One command at repo root; `ruff.toml` at root is picked up automatically.

### `.github/workflows/deploy.yml`

```yaml
name: deploy
on:
  push:
    branches: [main]
    paths: ['prototypes/**']
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 2
      - name: Install scw CLI
        run: # (one-liner)
      - name: Deploy changed protos
        env:
          SCW_ACCESS_KEY: ${{ secrets.SCW_ACCESS_KEY }}
          SCW_SECRET_KEY: ${{ secrets.SCW_SECRET_KEY }}
          SCW_REGISTRY: ${{ secrets.SCW_REGISTRY }}
          SCW_PROJECT_ID: ${{ secrets.SCW_PROJECT_ID }}
        run: |
          set -euo pipefail
          for proto in $(git diff --name-only HEAD^ HEAD \
            | grep -oP '^prototypes/\K[^/]+' | sort -u); do
            echo "Deploying $proto"
            make deploy "$proto"
          done
```

Sequential, bash, standard. No third-party action.

## Pre-commit hook

`.githooks/pre-commit`, ~10 lines:

```sh
#!/bin/sh
if git diff --cached --name-only | xargs -I{} grep -l -E '[a-z0-9-]+\.functions\.fnc\.fr-par\.scw\.cloud' {} 2>/dev/null; then
  echo "error: Scaleway container URL found in staged files"
  exit 1
fi
```

Activated by `git config core.hooksPath .githooks` (already the repo's convention per PROTOTYPE.md). No `pre-commit` framework, no `.pre-commit-config.yaml`.

## Migration of existing `web/` → `prototypes/demandes/`

Single commit; Dockerfile is unchanged, so risk is low.

1. `mkdir -p prototypes/demandes`
2. `git mv web prototypes/demandes/web`
3. `git mv Dockerfile pyproject.toml uv.lock docker-compose.yml .dockerignore prototypes/demandes/`
4. Verify `prototypes/demandes/Dockerfile` paths still work with build context `prototypes/demandes/` (current `COPY . .` is context-relative, so yes).
5. Write `prototypes/demandes/README.md` describing the app (orientation requests for PLIE Lille Avenir, `/plie` and `/prescripteur` scenarios, seed data, local dev command).
6. Move `[tool.ruff]` config from `prototypes/demandes/pyproject.toml` into a new `ruff.toml` at factory root; strip it from the proto's pyproject.
7. Add factory-root `Makefile` with `new`, `provision`, `deploy`, `help` targets.
8. Add factory-root `copier.yml`.
9. Create `_template/` by copying `prototypes/demandes/` and stripping demandes-specific code (models, routes, seed, templates) down to a minimal hello-world. Static assets and `base.html` stay. Convert names to Jinja placeholders.
10. Rewrite `.github/workflows/deploy.yml` to the bash-loop shape.
11. Add `.github/workflows/ci.yml`.
12. Add `.githooks/pre-commit`.
13. Rewrite `PROTOTYPE.md` around the new workflow; add the auth recipe section.
14. Push; verify Scaleway container redeploys successfully with no change in public URL or behavior.

## Destroy and eject (documented in PROTOTYPE.md)

**Destroy:**
```sh
scw container container delete $(scw container container list name=<name> -o json | jq -r '.[0].id')
scw rdb database delete instance-id=$PROTO_DB_INSTANCE_ID name=<name>
scw rdb user delete instance-id=$PROTO_DB_INSTANCE_ID name=<name>
git rm -r prototypes/<name> && git commit -m "destroy <name>"
```

**Eject:**
```sh
git clone . ../<name>-ejected
cd ../<name>-ejected
git filter-repo --subdirectory-filter prototypes/<name> --to-subdirectory-filter .
gh repo create <name> --private --source . --push
```

## Open items

- **No migration framework.** A proto that needs durable data beyond a user-testing session is graduating out of throwaway status — eject it.
- **Per-proto lockfile is deliberate** over a uv workspace, to preserve strict freezing. Revisit if N grows past ~15 protos and `uv sync` latency at creation becomes annoying.
- **Auth is manual per-proto.** If auth-enabled protos become common, promote the recipe into `_template/` as a variant, or look at Cloudflare Access as a centralized alternative.

## Acceptance criteria

- `make new recs` runs copier, produces `prototypes/recs/` that builds with `docker build prototypes/recs`.
- `make provision recs` creates a Scaleway container named `recs` and a database named `recs`, sets `DATABASE_URL` on the container, prints the public URL.
- `make deploy recs` builds, pushes, looks up container ID by name, deploys — from a clean checkout, no committed per-proto config.
- `make dev demandes` starts local PG and uvicorn with reload.
- Pushing under `prototypes/X/**` deploys only X; pushing under `Makefile`, `_template/`, `scripts/`, `docs/` deploys nothing.
- `prototypes/demandes/` keeps its current public URL and behavior post-migration.
- `_template/` can be modified without affecting any existing proto.
- `git grep` in the committed tree returns no hits for any `*.functions.fnc.fr-par.scw.cloud` URL, and the pre-commit hook blocks any attempt to add one.
