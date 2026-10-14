from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.infrastructure.seeder import seed_database_if_needed


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    await seed_database_if_needed()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Backend corporativo para gestión de iniciativas y flujos de trabajo (IACS GCP)",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["Health"])
async def root_health_check():
    """Health check raíz compatible con pings existentes de warm-up."""
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.ENVIRONMENT}


# Montaje de Enrutadores API v1
app.include_router(api_router, prefix="/api/v1")
