# Building a les-emplois-like prototype

Guide for an agent building a visually identical prototype to [les-emplois](https://github.com/gip-inclusion/les-emplois), with variant features and modular tab-based layouts. This documents the approach used for fluo-proto and can be followed step-by-step.

## Overview

The goal is to produce a clickable prototype that looks indistinguishable from les-emplois but implements different domain logic. No auth, no real API — just FastAPI + Jinja2 + SQLite with vendored static assets from les-emplois.

## Step 1: Extract the design system from les-emplois

The visual identity lives in three layers. You need all three.

### Layer 1: theme-inclusion (the design system)

This is the shared CSS/JS/fonts/images package used by all Plateforme de l'inclusion products. Copy the entire directory:

```bash
mkdir -p static/vendor/theme-inclusion
cp -r /path/to/les-emplois/itou/static/vendor/theme-inclusion/ static/vendor/theme-inclusion/
```

This gives you:
- `stylesheets/app.css` — the compiled CSS (Bootstrap 5 + custom theme)
- `fonts/marianne/` — the Marianne typeface (French government)
- `fonts/remixicon/` — Remix Icons (icon font, loaded via app.css)
- `images/` — logos, pictos, illustrations
- `javascripts/app.js` — theme JS

### Layer 2: Bootstrap + jQuery (JS dependencies)

```bash
mkdir -p static/vendor/bootstrap static/vendor/jquery
cp /path/to/les-emplois/node_modules/bootstrap/dist/js/bootstrap.min.js static/vendor/bootstrap/
cp /path/to/les-emplois/node_modules/bootstrap/dist/js/bootstrap.min.js.map static/vendor/bootstrap/
cp /path/to/les-emplois/node_modules/@popperjs/core/dist/umd/popper.min.js static/vendor/bootstrap/
cp /path/to/les-emplois/node_modules/@popperjs/core/dist/umd/popper.min.js.map static/vendor/bootstrap/
cp /path/to/les-emplois/itou/static/vendor/jquery/jquery.min.js static/vendor/jquery/
```

### Layer 3: itou.css (les-emplois custom styles)

On top of theme-inclusion, les-emplois has its own CSS for components like `list-data`, `list-note`, `list-step`, `c-box`, `c-prevstep`, etc. Without this file, many layout patterns won't render correctly.

```bash
mkdir -p static/css
cp /path/to/les-emplois/itou/static/css/itou.css static/css/
```

### Gitignore these assets

They're large (~17MB total) and not yours to version. Add to `.gitignore`:

```
static/vendor/
static/css/itou.css
```

When deploying to a fresh server, rsync them manually from your dev machine.

## Step 2: Prototype banner

Every prototype **must** display a prominent red banner stating it uses fictitious data. This is a non-negotiable part of the methodology — it prevents any confusion with the real application.

les-emplois uses this pattern on its demo/staging environments (`DEMO - Données fictives`). We reproduce it with the text "PROTOTYPE" instead.

Add this between `</header>` and `<main>` in your base template:

```html
<div class="global-messages-container">
    <div class="alert alert-danger" role="status">
        <strong>PROTOTYPE – Données fictives</strong>
    </div>
</div>
```

This renders a full-width red bar at the top of every page. It uses Bootstrap's `alert alert-danger` classes (styled by theme-inclusion) and the `global-messages-container` wrapper from les-emplois.

Do not make it dismissible — it should always be visible.

## Step 3: Base template

The base template establishes the authenticated layout. Key elements:

```html
<!DOCTYPE html>
<html lang="fr">
<head>
    <link rel="stylesheet" href="/static/vendor/theme-inclusion/stylesheets/app.css">
    <link rel="stylesheet" href="/static/css/itou.css">
</head>
<body class="l-authenticated">
    <header><!-- see below --></header>
    <main id="main" role="main" class="s-main">
        {% block content %}{% endblock %}
    </main>
    <script src="/static/vendor/jquery/jquery.min.js"></script>
    <script src="/static/vendor/bootstrap/popper.min.js"></script>
    <script src="/static/vendor/bootstrap/bootstrap.min.js"></script>
</body>
</html>
```

**Critical**: the `l-authenticated` body class activates the sidebar layout on large screens.

### Header structure

The header has three parts:

1. **Logo column** — links to home, uses a Plateforme de l'inclusion logo
2. **Nav column** — "Mon espace" dropdown (right-aligned), only visible on `sm+`
3. **Burger column** — triggers the offcanvas sidebar

### Offcanvas sidebar

The left navigation uses Bootstrap's offcanvas component. On large screens (`xl+`), `l-authenticated` makes it permanently visible. On smaller screens, the burger button opens it.

```html
<div class="offcanvas" id="offcanvasNav">
    <div class="offcanvas-header offcanvas-header--organization">
        <!-- Organization name -->
    </div>
    <div class="offcanvas-body d-flex flex-column">
        <nav>
            <ul class="nav nav-tabs flex-column mb-3">
                <li class="nav-item">
                    <a href="/" class="nav-link active">
                        <i class="ri-compass-line fw-medium" aria-hidden="true"></i>
                        <span>Orientations</span>
                    </a>
                </li>
                <!-- more nav items -->
            </ul>
        </nav>
    </div>
</div>
```

## Step 4: The page section pattern

Every page in les-emplois follows this nesting:

```html
<section class="s-title-02">
    <div class="s-title-02__container container">
        <div class="s-title-02__row row">
            <div class="s-title-02__col col-12">
                <!-- title, breadcrumb, action bar, tabs -->
            </div>
        </div>
    </div>
</section>

<section class="s-section">
    <div class="s-section__container container">
        <div class="s-section__row row">
            <div class="s-section__col col-12 col-xxl-8">
                <!-- main content -->
            </div>
        </div>
    </div>
</section>
```

**Always** use the `__container` / `__row` / `__col` BEM suffixes. The theme applies margins, padding, and max-widths on these. If you skip them, spacing breaks.

## Step 5: Component patterns

### c-box (card)

The basic content card. All info sections live inside these.

```html
<div class="c-box mb-3 mb-md-4">
    <h3>Section title</h3>
    <!-- content -->
</div>
```

Variants:
- `c-box--action` — dark background, used for the accept/refuse action bar
- `c-box--note` — lighter background, used for message quick-compose sidebar

### list-data (key-value pairs)

The main pattern for displaying structured info (person details, sender info, etc.):

```html
<ul class="list-data mb-3">
    <li>
        <small>Label</small>
        <strong>Value</strong>
    </li>
    <li>
        <small>Another label</small>
        <strong>Another value</strong>
    </li>
</ul>
```

For empty values: `<i class="text-disabled">Non renseigné</i>`

### list-note (messages / notes)

Used for message lists and threaded conversations:

```html
<ul class="list-note">
    <li>
        <div>
            <time class="fs-xs text-muted">2025-03-12 à 10:30</time>
            <strong class="d-block">Author Name</strong>
            <blockquote class="blockquote mt-1 mb-0">
                <p>Message content here</p>
            </blockquote>
        </div>
    </li>
</ul>
```

Add `class="is-current-user"` on `<li>` for the current user's messages.

### list-step (timeline / history)

```html
<ul class="list-step">
    <li>
        <time datetime="2025-03-12T10:30:00">Le 2025-03-12 à 10:30</time>
        <span>Event description</span>
    </li>
</ul>
```

### Badges

```html
<!-- Small badge (in tables) -->
<span class="badge rounded-pill text-nowrap badge-sm bg-info">Label</span>

<!-- Normal badge (in titles) -->
<span class="badge rounded-pill text-nowrap badge-base bg-success">Label</span>
```

Status colors: `bg-info` (blue, new), `bg-success` (green, accepted), `bg-danger` (red, refused), `bg-secondary` (grey, unknown).

### Buttons with icons

```html
<button class="btn btn-lg btn-link-white btn-block btn-ico">
    <i class="ri-check-line fw-medium" aria-hidden="true"></i>
    <span>Accepter</span>
</button>
```

Always add `fw-medium` after the Remix Icon class for consistent weight. Always set `aria-hidden="true"` on decorative icons.

### Filter bar (dropdown checkboxes)

```html
<div class="btn-dropdown-filter-group mb-3 mb-md-4">
    <form method="get" action="/" id="filter-form">
        <div class="dropdown">
            <button type="button"
                    class="btn btn-dropdown-filter dropdown-toggle"
                    data-bs-toggle="dropdown"
                    data-bs-display="static"
                    data-bs-auto-close="outside">
                Filter Label
            </button>
            <ul class="dropdown-menu">
                <li class="dropdown-item">
                    <div class="form-check">
                        <input class="form-check-input"
                               name="status" type="checkbox"
                               value="nouvelle"
                               onchange="this.form.submit()"
                               checked>
                        <label class="form-check-label">Nouvelle demande</label>
                    </div>
                </li>
            </ul>
        </div>
    </form>
</div>
```

`data-bs-auto-close="outside"` keeps the dropdown open when clicking checkboxes. `onchange="this.form.submit()"` submits immediately on toggle.

## Step 6: Tab system for modular detail pages

The detail page uses Bootstrap 5 tabs to split content into sections. This is the core modularity pattern — each tab is an independent `includes/` partial.

### Tab navigation (inside `s-title-02`)

```html
<ul class="s-tabs-01__nav nav nav-tabs mb-0" role="tablist">
    <li class="nav-item" role="presentation">
        <a class="nav-link active" id="info-tab"
           data-bs-toggle="tab" href="#info"
           role="tab" aria-controls="info" aria-selected="true">
            Informations
        </a>
    </li>
    <li class="nav-item" role="presentation">
        <a class="nav-link" id="messages-tab"
           data-bs-toggle="tab" href="#messages"
           role="tab" aria-controls="messages" aria-selected="false">
            Messages{% if messages %} ({{ messages|length }}){% endif %}
        </a>
    </li>
</ul>
```

### Tab content (inside `s-section`)

```html
<div class="tab-content">
    <div class="tab-pane fade show active" id="info"
         role="tabpanel" aria-labelledby="info-tab">
        <div class="s-section__row row">
            <div class="s-section__col col-12 col-xxl-8 order-2 order-xxl-1">
                {% include "includes/personal_info.html" %}
                {% include "includes/sender_info.html" %}
            </div>
            <div class="s-section__col col-12 col-xxl-4 order-1 order-xxl-2">
                {% include "includes/messages_sidebar.html" %}
            </div>
        </div>
    </div>

    <div class="tab-pane fade" id="messages"
         role="tabpanel" aria-labelledby="messages-tab">
        {% include "includes/messages_tab.html" %}
    </div>
</div>
```

### How to add a new tab

1. Add a `<li>` to the tab nav
2. Add a `<div class="tab-pane fade">` to the tab content
3. Create a new `includes/your_section.html` partial
4. Use any of the component patterns above inside it

Tabs are fully modular — you can add, remove, or reorder them without touching other code.

## Step 7: The list page pattern

For index/list pages, les-emplois uses a table inside `s-section`:

```html
<div class="table-responsive">
    <table class="table table-hover">
        <thead>
            <tr>
                <th scope="col">Column</th>
            </tr>
        </thead>
        <tbody>
            {% for item in items %}
            <tr class="align-top">
                <td>
                    <a class="btn-link" href="/item/{{ item.id }}">
                        {{ item.name }}
                    </a>
                    <span class="badge rounded-pill text-nowrap badge-sm bg-info">Status</span>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
```

Empty state:
```html
<div class="c-box mb-3 mb-md-4">
    <p class="text-muted mb-0">Aucun résultat ne correspond aux filtres sélectionnés.</p>
</div>
```

## Step 8: Backend (FastAPI + SQLite)

### Minimal stack

```
uv init --bare
uv add fastapi uvicorn jinja2 python-multipart
```

`python-multipart` is **required** for form parsing — without it, any `POST` with form data returns 500.

### app.py pattern

```python
from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
```

Routes return `templates.TemplateResponse("page.html", {"request": request, ...})`.

POST actions (accept, refuse, send message) do their work then `return RedirectResponse(url, status_code=303)` (POST-redirect-GET).

### db.py pattern

Use `sqlite3.Row` for dict-like access. Store JSON blobs as TEXT and parse with `json.loads()` on read. The database file (`data.db`) is gitignored — re-created by `seed.py`.

### Query parameters for list filtering

FastAPI requires explicit `Query()` for list parameters:

```python
@app.get("/")
async def list_view(request: Request, status: list[str] = Query(default=["nouvelle"])):
```

Without `Query(default=...)`, multiple `?status=a&status=b` params won't parse correctly.

## Step 9: Finding reference markup in les-emplois

When you need to reproduce a specific pattern:

1. Find the page in les-emplois (e.g., candidature detail)
2. Find the Django template: `grep -r "candidature" itou/templates/` or look at the URL patterns
3. The templates use the same Jinja2-compatible syntax (Django templates)
4. Copy the HTML structure, replace Django-specific tags (`{% url %}`, `{% trans %}`) with plain Jinja2
5. Replace `{{ object.field }}` with your own context variables

Key les-emplois template locations:
- Candidature detail: `itou/templates/apply/`
- Candidature list: `itou/templates/apply/`
- Layout: `itou/templates/layout/`
- Components: check for `{% include %}` paths

## Step 10: GitHub repo + push-to-deploy on Scaleway

### Create a private repo

```bash
git init
git add -A
git commit -m "Initial commit"
gh repo create <username>/fluo-proto --private --source=. --push
```

If SSH push fails, switch to HTTPS:
```bash
git remote set-url origin https://github.com/<username>/fluo-proto.git
git push -u origin main
```

### Create a Scaleway instance

Use `scw` CLI. STARDUST1-S is the cheapest (€0.0001/h, ~free):

```bash
scw instance server create \
  name=fluo-proto \
  type=STARDUST1-S \
  image=ubuntu_noble \
  zone=fr-par-1 \
  ip=new
```

Note the public IP from the output. The instance auto-starts.

Wait for SSH then set up the server:

```bash
ssh root@<IP> "apt-get update -qq && apt-get install -yqq python3 python3-venv curl"
ssh root@<IP> "curl -LsSf https://astral.sh/uv/install.sh | sh"

# Copy all files including static assets
rsync -avz --exclude='.venv' --exclude='__pycache__' --exclude='.git' --exclude='data.db' ./ root@<IP>:/opt/fluo-proto/

# Install deps and seed
ssh root@<IP> "cd /opt/fluo-proto && /root/.local/bin/uv sync && /root/.local/bin/uv run python seed.py"
```

### Create a systemd service

```bash
ssh root@<IP> 'cat > /etc/systemd/system/fluo-proto.service << EOF
[Unit]
Description=Fluo Proto
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/fluo-proto
ExecStart=/opt/fluo-proto/.venv/bin/uvicorn app:app --host 0.0.0.0 --port 8002
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload && systemctl enable --now fluo-proto'
```

### Set up a deploy key (not your personal SSH key)

Generate a dedicated key on the server and register it with Scaleway:

```bash
# On the server
ssh root@<IP> 'ssh-keygen -t ed25519 -f /root/.ssh/deploy_key -N "" -C "fluo-proto-deploy"'

# Register in Scaleway IAM so the server accepts it
scw iam ssh-key create name=fluo-proto-deploy public-key="$(ssh root@<IP> 'cat /root/.ssh/deploy_key.pub')"

# Store private key as GitHub secret
ssh root@<IP> 'cat /root/.ssh/deploy_key' | gh secret set SSH_PRIVATE_KEY --repo <username>/fluo-proto
```

### GitHub Actions deploy workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to server
        env:
          SSH_KEY: ${{ secrets.SSH_PRIVATE_KEY }}
        run: |
          mkdir -p ~/.ssh
          echo "$SSH_KEY" > ~/.ssh/id_ed25519
          chmod 600 ~/.ssh/id_ed25519
          ssh-keyscan -H <IP> >> ~/.ssh/known_hosts

          rsync -avz \
            --exclude='.venv' \
            --exclude='__pycache__' \
            --exclude='.git' \
            --exclude='data.db' \
            --exclude='.DS_Store' \
            --exclude='docs/' \
            --exclude='.superpowers/' \
            ./ root@<IP>:/opt/fluo-proto/

          ssh root@<IP> "cd /opt/fluo-proto && /root/.local/bin/uv sync && systemctl restart fluo-proto"
```

**Important**: do NOT use `--delete` in rsync — it would wipe the gitignored `static/` assets on the server.

Now every push to main auto-deploys.

## Pitfalls and lessons learned

1. **Don't use `--delete` in rsync deploys** — static assets are gitignored, `--delete` wipes them
2. **`python-multipart` is not optional** — FastAPI silently fails on form POSTs without it (500, no clear error)
3. **Respect the BEM nesting** — `s-section` needs `s-section__container`, `s-section__row`, `s-section__col`. Skip a level and margins collapse or padding disappears
4. **`l-authenticated` on `<body>`** — without this class, the sidebar layout doesn't activate on large screens
5. **Remix Icons are in app.css** — don't look for a separate `remixicon.css`, it's compiled into the theme stylesheet
6. **itou.css is essential** — without it, `list-data`, `list-note`, `list-step`, `c-box` variants, and many other patterns render incorrectly. It's the glue between theme-inclusion and les-emplois-specific markup
7. **Use formal names in French UI** — always "Mme Martin", "M. Benali", never first names
8. **Logo choice** — use `logo-plateforme-inclusion.svg` for a generic Plateforme de l'inclusion prototype, not `logo-emploi-inclusion.svg` (which is les-emplois specific)
