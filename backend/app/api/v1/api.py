from fastapi import APIRouter
from app.api.v1.endpoints import (
    admin,
    ai,
    ai_training,
    auth,
    fields,
    health,
    initiatives,
    stage_forms,
    workflow,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(initiatives.router, prefix="/initiatives", tags=["Iniciativas"])
api_router.include_router(workflow.router, prefix="/workflow", tags=["Workflows"])
api_router.include_router(stage_forms.router, tags=["Formularios y Consentimientos"])
api_router.include_router(ai.router, tags=["Inteligencia Artificial (Teo)"])
api_router.include_router(ai_training.router, tags=["Entrenamiento de IA"])
api_router.include_router(ai_training.router, prefix="/admin", tags=["Entrenamiento de IA"])
api_router.include_router(fields.router, prefix="/fields", tags=["Campos Dinámicos"])
api_router.include_router(admin.router, prefix="/admin", tags=["Administración"])
api_router.include_router(admin.router, tags=["Administración Global"])

