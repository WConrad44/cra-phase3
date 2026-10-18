# CRA Vulnerability Ticketing Service — Phase 3 starter

Implements the Phase 3 increment from the pod specification:

- REQ-01 ticket intake
- REQ-02 actively-exploited triage
- REQ-03 non-reportable/invalid triage
- REQ-04 24h / 72h / final-report deadline calculation
- REQ-12 common error handling (starter implementation)
- REQ-13 RFC 3339 input + UTC output
- REQ-14 bearer-token authentication + actor header for mutations
- REQ-16 reset + controllable test clock

It also includes `GET /tickets/{id}` because it is useful for automated verification.

## 1. Local setup

Python 3.12 recommended.

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate

pip install -r requirements-dev.txt
```

Set environment variables:

```bash
# PowerShell
$env:API_TOKEN="dev-token"
$env:DATABASE_URL="sqlite:///./cra.db"

# macOS/Linux
export API_TOKEN="dev-token"
export DATABASE_URL="sqlite:///./cra.db"
```

Run:

```bash
uvicorn app.main:app --reload
```

Then open:

- API docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

## 2. Run tests

```bash
pytest -q
ruff check app tests
```

## 3. Quick manual test

Set fixed time:

```bash
curl -X PUT http://127.0.0.1:8000/test/clock \
  -H "Authorization: Bearer dev-token" \
  -H "X-Actor: student" \
  -H "Content-Type: application/json" \
  -d '{"now":"2026-10-07T15:00:00Z"}'
```

Create ticket:

```bash
curl -X POST http://127.0.0.1:8000/tickets \
  -H "Authorization: Bearer dev-token" \
  -H "X-Actor: student" \
  -H "Content-Type: application/json" \
  -d '{
    "source":"external_researcher",
    "title":"Auth bypass",
    "description":"Researcher reports login bypass.",
    "product":{"manufacturer":"Acme","name":"Acme Router OS","affected_versions":["4.1.0"]}
  }'
```

Triage the returned ticket ID:

```bash
curl -X POST http://127.0.0.1:8000/tickets/TICKET_ID/triage \
  -H "Authorization: Bearer dev-token" \
  -H "X-Actor: security-engineer" \
  -H "Content-Type: application/json" \
  -d '{
    "decision":"actively_exploited",
    "aware_at":"2026-10-07T14:30:00Z",
    "reason":"Customer logs show exploitation."
  }'
```

Expected due times:

- early warning: 2026-10-08T14:30:00Z
- notification: 2026-10-10T14:30:00Z
- final report: awaiting fix unless `fix.available_at` is already present

## 4. PostgreSQL later / deployment

The app already uses SQLAlchemy. For local development the default can be SQLite. For deployment, set `DATABASE_URL` to a PostgreSQL connection string and install/use the same requirements.

The included `Dockerfile` and `render.yaml` are starter deployment files. You still need to create/provision a database and set `DATABASE_URL` in the host.

## Important before cross-team testing

Compare these endpoint schemas with the pod's **actual frozen OpenAPI file** if one exists separately from the Phase 2 report. Exact field names/status codes/error bodies must match the shared contract, even if FastAPI's defaults differ.
