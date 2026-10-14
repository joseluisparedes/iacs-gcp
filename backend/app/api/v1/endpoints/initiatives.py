from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_current_user_claims
from app.domain.models import Initiative, Profile
from app.infrastructure.database import get_db
from app.schemas.initiatives import InitiativeCreate, InitiativeResponse, InitiativeUpdate

router = APIRouter()


@router.get("", response_model=List[InitiativeResponse])
async def list_initiatives(
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    claims: Dict[str, Any] = Depends(get_current_user_claims),
):
    """Lista las iniciativas registradas con filtros opcionales de estado."""
    query = select(Initiative).order_by(desc(Initiative.updated_at))
    if status_filter:
        query = query.where(Initiative.status == status_filter)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{id}", response_model=InitiativeResponse)
async def get_initiative(
    id: str,
    db: AsyncSession = Depends(get_db),
    claims: Dict[str, Any] = Depends(get_current_user_claims),
):
    """Obtiene el detalle completo de una iniciativa por ID."""
    result = await db.execute(select(Initiative).where(Initiative.id == id))
    initiative = result.scalar_one_or_none()
    if not initiative:
        raise HTTPException(status_code=404, detail="Iniciativa no encontrada")
    return initiative


@router.post("", response_model=InitiativeResponse)
async def create_initiative(
    payload: InitiativeCreate,
    db: AsyncSession = Depends(get_db),
    claims: Dict[str, Any] = Depends(get_current_user_claims),
):
    """Crea una nueva iniciativa o borrador."""
    init_id = payload.id or f"init_{int(datetime.now().timestamp())}_{str(uuid4())[:8]}"

    # Resolver usuario autor si existe
    user_id = None
    email = claims.get("email")
    if email:
        p_res = await db.execute(select(Profile).where(Profile.email == email))
        p = p_res.scalar_one_or_none()
        if p:
            user_id = p.id

    initiative = Initiative(
        id=init_id,
        status=payload.status,
        form_data=payload.form_data,
        chat_history=[m.model_dump() for m in payload.chat_history],
        summary=payload.summary,
        rejection_reason=payload.rejection_reason,
        user_id=user_id,
        confirmed_fields=payload.confirmed_fields,
        unstructured_text=payload.unstructured_text,
        workflow_version=payload.workflow_version,
        current_node_id=payload.current_node_id,
    )
    db.add(initiative)
    await db.commit()
    await db.refresh(initiative)
    return initiative


@router.post("/draft", response_model=InitiativeResponse)
async def save_draft(
    payload: InitiativeCreate,
    db: AsyncSession = Depends(get_db),
    claims: Dict[str, Any] = Depends(get_current_user_claims),
):
    """Guarda o actualiza un borrador de iniciativa."""
    if payload.id:
        result = await db.execute(select(Initiative).where(Initiative.id == payload.id))
        existing = result.scalar_one_or_none()
        if existing:
            existing.form_data = payload.form_data
            existing.chat_history = [m.model_dump() for m in payload.chat_history]
            existing.summary = payload.summary
            existing.status = payload.status or existing.status
            existing.updated_at = datetime.now()
            await db.commit()
            await db.refresh(existing)
            return existing

    return await create_initiative(payload, db, claims)


@router.patch("/{id}", response_model=InitiativeResponse)
async def update_initiative(
    id: str,
    payload: InitiativeUpdate,
    db: AsyncSession = Depends(get_db),
    claims: Dict[str, Any] = Depends(get_current_user_claims),
):
    """Actualiza campos, estado o expediente de una iniciativa."""
    result = await db.execute(select(Initiative).where(Initiative.id == id))
    initiative = result.scalar_one_or_none()
    if not initiative:
        raise HTTPException(status_code=404, detail="Iniciativa no encontrada")

    update_data = payload.model_dump(exclude_unset=True)
    if "chat_history" in update_data and update_data["chat_history"]:
        update_data["chat_history"] = [m.model_dump() if hasattr(m, "model_dump") else m for m in update_data["chat_history"]]

    for key, value in update_data.items():
        setattr(initiative, key, value)

    initiative.updated_at = datetime.now()
    await db.commit()
    await db.refresh(initiative)
    return initiative
