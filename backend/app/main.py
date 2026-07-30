from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging_config import setup_logging, get_logger, log_event
from app.api.deps import RequestContextMiddleware
from app.api import routes_auth, routes_analysis, routes_kpi, routes_trace, routes_export

setup_logging()
logger = get_logger(__name__)

app = FastAPI(title=settings.APP_NAME, version="1.0.0")

app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_auth.router)
app.include_router(routes_analysis.router)
app.include_router(routes_kpi.router)
app.include_router(routes_trace.router)
app.include_router(routes_export.router)


@app.on_event("startup")
async def on_startup():
    log_event(logger, "clientiq_backend_startup", env=settings.ENV, app=settings.APP_NAME)


@app.on_event("shutdown")
async def on_shutdown():
    log_event(logger, "clientiq_backend_shutdown")


@app.get("/api/health")
async def health():
    log_event(logger, "health_check_requested")
    return {"status": "ok", "service": settings.APP_NAME}
