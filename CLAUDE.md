# Fluo Proto

FastAPI + Jinja2 + SQLite prototype for orientation requests.

## Dev server

```bash
uv run uvicorn app:app --reload --host 0.0.0.0 --port 8002
```

## Seed / reset database

```bash
rm -f data.db && uv run python seed.py
```

## Deploy to Scaleway (STARDUST1-S)

Instance: `163.172.180.4` (fluo-proto-stardust)
URL: http://163.172.180.4:8002/

```bash
# Sync files
rsync -avz --exclude='.venv' --exclude='__pycache__' --exclude='.git' --exclude='data.db' --exclude='.DS_Store' --exclude='docs/' --exclude='.superpowers/' ./ root@163.172.180.4:/opt/fluo-proto/

# Re-seed and restart
ssh root@163.172.180.4 "cd /opt/fluo-proto && rm -f data.db && /root/.local/bin/uv run python seed.py && systemctl restart fluo-proto"
```

Full setup on a fresh instance:
```bash
apt-get update -qq && apt-get install -yqq python3 python3-venv curl
curl -LsSf https://astral.sh/uv/install.sh | sh
mkdir -p /opt/fluo-proto
# rsync files (see above)
cd /opt/fluo-proto && /root/.local/bin/uv sync && /root/.local/bin/uv run python seed.py
# create /etc/systemd/system/fluo-proto.service then:
systemctl daemon-reload && systemctl enable --now fluo-proto
```
