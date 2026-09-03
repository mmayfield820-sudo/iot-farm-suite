# Python backend

This service uses FastAPI, SQLAlchemy, PyMySQL, bcrypt, JWT, and Paho MQTT. It reads MySQL data, authenticates users, and consumes device messages from EMQX.

## Local startup

From the project root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8080
```

Set a non-default `JWT_SECRET` in `.env` before startup. The local demo employee numbers `E000001`, `E000002`, and `E000003` use the development password `DemoPass123!`.

## HTTP endpoints

- `GET /health` checks the service and MySQL.
- `POST /api/auth/login` returns a JWT.
- `GET /api/farms` lists farms in the current user scope.
- `GET /api/farms/F001/overview` returns authorized plot summaries.
- `GET /api/devices?plotId=P001` lists authorized devices.

Other than health and login, requests need `Authorization: Bearer <token>`.

## MQTT ingestion

The service subscribes to `farm/telemetry/+`, `farm/status/+`, and `farm/command_result/+` when it starts. Telemetry is deduplicated by device and `msgId`; a `plot_report` is saved only after both humidity and temperature readings arrive within `TELEMETRY_PAIR_TIMEOUT_SECONDS`. An unpaired reading after that timeout creates a `device_fault` alert.

Run one local telemetry cycle after starting the backend:

```powershell
.venv\Scripts\python.exe device-simulator/simulator.py --once
```
