import time
from datetime import datetime, timezone
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from backend.database.session import engine
from backend.api.v1 import api_v1_router

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

# Enable CORS for local Vite/React frontend and cross-origin access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    """Verify API and PostgreSQL connectivity."""
    db_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_ok = True
    except Exception:
        db_ok = False

    return {
        "status": "HEALTHY" if db_ok else "UNHEALTHY",
        "database": "CONNECTED" if db_ok else "DISCONNECTED",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# Mount API v1 router
app.include_router(api_v1_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
