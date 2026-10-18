# Team 21 CRA Vulnerability Ticketing Service — Phase 3

This repository now contains **two FastAPI applications** required for Phase 3:

1. **System service** — `app.main:app`
2. **Tester service** — `tester.main:app`

The shared Pod K specification is the Phase 2 `spec.md` maintained by Teams 17 and 21. The shared `openapi.yaml` is authoritative for exact project-interface details and should be checked before final cross-team grading.

## System service

Implemented Phase 3 project behavior:

- REQ-01 ticket intake
- REQ-02 actively-exploited triage
- REQ-03 non-reportable/invalid triage
- REQ-04 24h / 72h / final-report deadline calculation
- REQ-12 common error handling (Phase 3 subset)
- REQ-13 RFC 3339 input + UTC output
- REQ-14 bearer-token authentication + actor header for mutations
- REQ-16 reset + controllable test clock

Course-wide cross-team endpoints added:

- `POST /test/setup`
- `GET /test/report?session_id=...`

The existing Pod K controls remain:

- `POST /test/reset`
- `GET /test/clock`
- `PUT /test/clock`
- `DELETE /test/clock`

### Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
export API_TOKEN=dev-token
export DATABASE_URL=sqlite:///./cra.db
uvicorn app.main:app --reload
```

System docs: `http://127.0.0.1:8000/docs`

## Tester service

The Team 21 tester implements the course interface:

- `POST /test/setup`
- `POST /test/run`
- `GET /test/report?session_id=...`

Its Phase 3 suite checks AC-01 through AC-05, AC-14, AC-15, and AC-17 against the selected Pod K target.

### Run tester locally

The tester must know the target system's bearer token. Keep tokens in environment variables; never place them in the class registry URL.

For one target:

```bash
export TARGET_API_TOKEN='target-private-token'
export TARGET_ACTOR='team21-tester'
uvicorn tester.main:app --reload --port 8001
```

For multiple known targets, use a JSON mapping by hostname or full base URL:

```bash
export TARGET_TOKENS_JSON='{"team17.example.run.app":"TEAM17_TOKEN","cra-phase3.onrender.com":"TEAM21_TOKEN"}'
uvicorn tester.main:app --reload --port 8001
```

Tester docs: `http://127.0.0.1:8001/docs`

### Tester workflow

1. `POST /test/setup` with the selected system base URL:

```json
{"target_url":"https://target-system.example"}
```

2. Copy the returned `session_id` and call:

```json
POST /test/run
{"session_id":"run-..."}
```

3. The run response is the complete suite report. It can later be retrieved with:

```text
GET /test/report?session_id=run-...
```

## Run local automated tests

```bash
python3 -m pytest -q
ruff check app tester tests
```

## Render deployment

### Existing Team 21 system

Keep the current system service start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Environment variables:

```text
API_TOKEN=<private Team 21 token>
DATABASE_URL=sqlite:///./cra.db   # Phase 3 only; PostgreSQL is preferred for later persistence work
```

### Create the second Team 21 tester service

Create another Render Web Service from the **same GitHub repository**.

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
uvicorn tester.main:app --host 0.0.0.0 --port $PORT
```

Set either:

```text
TARGET_API_TOKEN=<private token for the system being tested>
TARGET_ACTOR=team21-tester
```

or, preferably for Team 17 + Team 21 targets:

```text
TARGET_TOKENS_JSON={"TEAM17_HOST":"TEAM17_PRIVATE_TOKEN","cra-phase3.onrender.com":"TEAM21_PRIVATE_TOKEN"}
TARGET_ACTOR=team21-tester
```

Do not put these tokens in GitHub or the class registry.

## Registry fields

Team 21 should register:

- **System base URL:** `https://cra-phase3.onrender.com`
- **Tester base URL:** the second Render service URL created for `tester.main:app`
- **Intra-pod specification URL:** the shared Pod K `spec.md` GitHub URL
- **Access/run notes:** state that protected system calls use Bearer auth and credentials are provided privately; include agreed setup/run limits.
