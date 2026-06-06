"""
OpenAPI documentation configuration for SMS-Engine
"""

from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi import FastAPI


def configure_docs(app: FastAPI):
    """Configure OpenAPI documentation for SMS-Engine"""

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title="SMS-Engine API - Aviation Safety Intelligence System",
            version="2.1.0",
            description="""
## ICAO-Aligned Aviation Risk Assessment API

The **SMS-Engine** provides automated safety risk assessment for flight operations based on:

- **IMSAFE** (Pilot readiness: Illness, Medication, Stress, Alcohol, Fatigue, Emotion)
- **PAVE** (Operational risk: Pilot, Aircraft, Environment, External pressures)
- **Risk Matrix** (1-25 score with ICAO categorization)
- **AI Explanations** (via Claude Haiku on OpenRouter)

### Authentication

**Production (IAP):**
```bash
export TOKEN=$(gcloud auth print-identity-token \\
  --audiences="660696925387-rk1ffklc4bcje0toq2psnqf3kv24ujdn.apps.googleusercontent.com")
curl -H "Authorization: Bearer $TOKEN" https://sms-engine-660696925387.us-central1.run.app/health
```

**Local Dev:**
```bash
curl http://localhost:8080/health
```

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Health check |
| GET | `/health` | Health check alias |
| GET | `/ping` | Health check alias |
| GET | `/healthz` | Health check alias (local only) |
| POST | `/assess-flight` | Evaluate a flight scenario |
| GET | `/safety-report` | Get aggregated safety metrics |
| POST | `/simulate` | Batch evaluate multiple scenarios |
| GET | `/history` | Get recent assessments |
| GET | `/assessments` | Get recent assessments (alias) |
| GET | `/dashboard` | Interactive web dashboard |
| GET | `/status/status.html` | Status monitoring page |
| GET | `/docs` | This documentation |
            """,
            routes=app.routes,
        )

        openapi_schema["info"]["x-logo"] = {
            "url": "https://storage.googleapis.com/sms-engine-audit-logs/sms-logo.png"
        }

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi
