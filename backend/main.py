import logging
import os
import re
import time
from datetime import datetime, timezone
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from backend.database.session import engine, DATABASE_URL_CONFIGURED
from backend.api.v1 import api_v1_router

health_logger = logging.getLogger("backend.health")

def sanitize_error_message(msg: str) -> str:
    """Safely strip any credentials, passwords, or query tokens from error messages."""
    if not msg:
        return ""
    # Strip passwords embedded in URLs like :password@
    sanitized = re.sub(r':([^:@\s]+)@', ':***@', msg)
    # Strip parameter patterns like password=xyz
    sanitized = re.sub(r'(password=)[^\s;&]+', r'\1***', sanitized, flags=re.IGNORECASE)
    # Strip tokens and secret keys
    sanitized = re.sub(r'((?:secret|token|api_key|jwt)=)[^\s;&]+', r'\1***', sanitized, flags=re.IGNORECASE)
    return sanitized

app = FastAPI(
    title="Enterprise Accounts Payable Control Platform API",
    version="1.0.0",
    description=(
        "Production-grade REST API backend for automated 3-way matching, "
        "deterministic control execution, exception routing, and payable ledger governance.\n\n"
        "**Core Invariant:** `RECEIVED INVOICE != PAYABLE OBLIGATION`"
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Enable CORS for local Vite/React frontend, Vercel deployments, and production origins
allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins_raw.strip():
    allowed_origins = [o.strip() for o in allowed_origins_raw.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Development & preview deployments: allow localhost and all vercel.app preview URLs
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|.*\.vercel\.app)(:\d+)?",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.middleware("http")
async def add_process_time_and_correlation_headers(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = f"{process_time * 1000:.2f}ms"
    return response

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc), "error_type": "VALIDATION_ERROR"}
    )

@app.exception_handler(PermissionError)
async def permission_error_handler(request: Request, exc: PermissionError):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": str(exc), "error_type": "PERMISSION_DENIED"}
    )

@app.get("/", tags=["Health & Status"])
def root():
    return {
        "service": "Enterprise Accounts Payable Control Platform",
        "version": "1.0.0",
        "status": "OPERATIONAL",
        "documentation": "/docs",
        "core_invariant": "RECEIVED INVOICE != PAYABLE OBLIGATION",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/health", tags=["Health & Status"])
@app.get("/api/v1/health", tags=["Health & Status"])
def health_check():
    """Verify API and PostgreSQL connectivity with safe diagnostic logging."""
    db_ok = False
    exc_class = None
    safe_error = None

    safe_host = None
    safe_port = None
    safe_driver = None
    try:
        safe_host = engine.url.host
        safe_port = engine.url.port
        safe_driver = engine.url.drivername
    except Exception:
        pass

    database_url_env = os.getenv("DATABASE_URL")
    database_url_is_set = bool(database_url_env and database_url_env.strip())

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_ok = True
            health_logger.info(
                "PostgreSQL connection healthy | host=%s | port=%s | driver=%s",
                safe_host,
                safe_port,
                safe_driver,
            )
    except Exception as exc:
        db_ok = False
        exc_class = exc.__class__.__name__
        safe_error = sanitize_error_message(str(exc))
        health_logger.error(
            "PostgreSQL connection failed | exception_class=%s | error=%s | "
            "db_host=%s | db_port=%s | driver=%s | database_url_configured=%s | "
            "can_create_connection=False",
            exc_class,
            safe_error,
            safe_host,
            safe_port,
            safe_driver,
            database_url_is_set,
        )

    response = {
        "status": "HEALTHY" if db_ok else "UNHEALTHY",
        "database": "CONNECTED" if db_ok else "DISCONNECTED",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if not db_ok:
        response["diagnostics"] = {
            "exception_class": exc_class,
            "error_message": safe_error,
            "database_host": safe_host,
            "database_port": safe_port,
            "database_driver": safe_driver,
            "database_url_configured": database_url_is_set,
            "can_create_connection": False,
        }

    return response

# Mount API v1 router
app.include_router(api_v1_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
