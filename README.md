# Revival365 FastAPI — README

## 🚀 Project Overview

This repository contains a FastAPI compatibility layer for several existing AWS Lambda functions (AGP and Appointments). The FastAPI app exposes HTTP endpoints that behave identically to the original Lambda routes by dynamically loading and invoking the existing Lambda handlers. This lets you run and test the Lambdas locally (or inside a container) using a standard FastAPI server and OpenAPI docs.

---

## ✅ Key Features

- FastAPI app available at `app/main.py` with automatic docs at `/docs` and `/redoc`.
- Router modules in `app/routers/` mirror Lambda routes (AGP and Appointments).
- Service layer in `app/services/` loads original Lambda `lambda_function.py` modules and calls `lambda_handler` with an API Gateway–like event.
- Utility `app/utils/lambda_loader.py` isolates and imports Lambda handlers dynamically to avoid cross-module pollution.

---

## 🔧 Prerequisites

- Python 3.10+ (recommended)
- pip
- (Optional) A Google Cloud service account JSON for appointment/calendar access (place under the appointment module or set `GOOGLE_APPLICATION_CREDENTIALS`) if you plan to hit Google Calendar APIs.

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 🧩 Environment variables

The app reads configuration from environment variables (or a `.env` file via `python-dotenv`):

- DATABASE_URL — optional; if missing, set DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
- DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME — used to construct MySQL DB URL
- (Optional) `GOOGLE_APPLICATION_CREDENTIALS` — path to your Google service account JSON if using appointment endpoints

Note: The appointment Lambda code may expect a `serviceaccount.json` in `Revival365ai-Appointment-module-1/src/` by default.

---

## ▶️ Running locally (FastAPI)

Start the FastAPI app (development; auto-reload):

```bash
uvicorn app.main:app --reload --port 8000
```

- Health check: GET http://localhost:8000/health
- OpenAPI docs: http://localhost:8000/docs (Swagger UI)

The application will try a lightweight DB `SELECT 1` on startup (see `app/main.py`), so ensure DB env vars or DATABASE_URL is set if you need DB connectivity.

---

## 📡 Exposed Endpoints (summary)

AGP (Glucose Profile)

- POST /agp_profile
  - Body (JSON): { "mobile_number": "<mobile>" }
  - Example: curl -X POST http://localhost:8000/agp_profile -H 'Content-Type: application/json' -d '{"mobile_number":"9876543210"}'

Appointments (mirrors the appointment Lambda routes)

- GET /appointment?calendar_id=<id>&date=YYYY-MM-DD
- GET /slots/available?calendar_id=<id>&date=YYYY-MM-DD&duration=60
- POST /calendar (body: { "id": "<calendar_id>" })
- POST /create_appointment?calendar_id=<id> (body: appointment details)
  - Example body keys (expected by Lambda): `start`, `end`, `title`, `description`, `date`, `patient_id`
- POST /delete_appointment (body: { "calendar_id": "...", "event_id": "..." })
- GET /patient_appointment?patient_id=<id>&date=YYYY-MM-DD&calendar_id=<id>
- GET /upcoming_events?hours=0&minutes=30&max_threads=30
- POST /set_availability (body: calendar availability structure expected by Lambda)

All endpoints return the same response structure (status code + body) that the original Lambda returned. FastAPI will translate Lambda error codes into HTTP exceptions.

---

## 🔬 How FastAPI reuses the Lambda functionality (technical details)

1. Each router in `app/routers/` exposes an endpoint which roughly corresponds to a Lambda route.
2. The router calls a service function in `app/services/` (e.g., `app/services/appointments.py`).
3. The service layer uses `app/utils/lambda_loader.py` to dynamically import the Lambda's `lambda_handler` from the original Lambda source (e.g., `Revival365-AGP/src/lambda_function.py`).
4. The service constructs a minimal API Gateway–style `event` object with keys like `rawPath`, `queryStringParameters`, and `body` (JSON string when needed), then calls `lambda_handler(event, context=None)`.
5. The service normalises the Lambda's `statusCode` and `body` into `{'status': <int>, 'body': <dict|list|str>}` and the FastAPI route translates this into an HTTP response (raising `HTTPException` when status >= 400).

This approach preserves exact Lambda behaviour without modifying the original business code and makes it straightforward to test Lambda logic via HTTP.

---

## 🧪 Running and testing Lambdas directly (quick)

If you want to run a Lambda module on its own (handy for unit or integration debugging):

```bash
# Example – appointment module
python Revival365ai-Appointment-module-1/src/run_local.py
```

This runs the real `lambda_handler` against `event.json` and prints the result.

---

## 🛠️ Debugging & Tips

- Check `/docs` for a clear view of routes, required parameters and example payloads.
- If Database checks fail on startup, verify `DATABASE_URL` or the individual DB variables.
- Appointment routes require valid Google Calendar credentials (service account) to make real API calls. For local testing, you can mock/stub those calls in the Lambda code or run with test `event.json`.
- Logging is configured at INFO level by default in `app/main.py`. Increase/decrease as needed by adjusting `logging.basicConfig(level=...)`.

---

## ✅ Notes and Next Steps

- The approach lets you migrate traffic to FastAPI incrementally while continuing to reuse battle-tested Lambda code.
- For serverless deployment of the FastAPI app itself, consider using an adapter like `mangum` to run FastAPI inside AWS Lambda behind API Gateway (if you want to deploy the FastAPI app as a Lambda rather than keeping/rewiring the original handlers).

---

If you want, I can also:

- Add example cURL or Postman collections for each route ✅
- Add a short development script (`make run` or a `run.sh`/`run.ps1`) to simplify bootstrapping ✅

Feel free to tell me which extra items you want included or any specific examples you want added.
