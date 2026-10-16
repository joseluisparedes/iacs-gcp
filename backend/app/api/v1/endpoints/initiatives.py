from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_current_user_claims
from app.domain.models import Initiative, Profile
from app.infrastructure.database import get_db
from app.schemas.initiatives import InitiativeCreate, InitiativeResponse, InitiativeUpdate

router = APIRouter()


def is_initiative_draft(initiative: Initiative) -> bool:
    """
    Verifica si una iniciativa se encuentra en estado borrador / inicial.
    Retorna True si el estado o el nodo corresponden a borrador o chat no formalizado.
    """
    status_lower = (initiative.status or "").strip().lower()
    node_lower = (initiative.current_node_id or "").strip().lower()

    if status_lower in ("borrador", "1. borrador", "draft", "chat", "chat pendiente"):
        return True
    if status_lower.startswith("borrador") or status_lower.startswith("1. borrador"):
        return True
    if node_lower in ("borrador", "node_borrador"):
        return True
    return False


async def get_current_user_profile(db: AsyncSession, claims: Dict[str, Any]) -> Optional[Profile]:
    """Obtiene el perfil del usuario autenticado a partir de los claims del token."""
    email = (claims.get("email") or "").strip().lower()
    if email:
        res = await db.execute(select(Profile).where(func.lower(Profile.email) == email))
        p = res.scalar_one_or_none()
        if p:
            return p
    sub = claims.get("sub")
    if sub:
        try:
            u_uuid = UUID(str(sub))
            res = await db.execute(select(Profile).where(Profile.id == u_uuid))
            p = res.scalar_one_or_none()
            if p:
                return p
        except Exception:
            pass
    return None


def is_user_initiative_registrador(
    initiative: Initiative,
    claims: Dict[str, Any],
    profile: Optional[Profile] = None,
) -> bool:
    """
    Determina si el usuario autenticado es el registrador de la iniciativa.
    REGLA: Las iniciativas en estado borrador solo las puede visualizar el registrador de la misma,
    nadie más. Esta recién se hace visible para el resto siempre y cuando pasen a los siguientes estados.
    """
    # 1. Comparación directa por user_id (UUID del perfil)
    if initiative.user_id:
        if profile and initiative.user_id == profile.id:
            return True
        sub = claims.get("sub")
        if sub and str(initiative.user_id) == str(sub):
            return True

    # 2. Comparación por correo del registrador
    claim_email = (claims.get("email") or "").strip().lower()
    profile_email = (profile.email if profile else "").strip().lower()
    user_emails = {e for e in (claim_email, profile_email) if e}

    form_data = initiative.form_data or {}
    init_email = str(
        form_data.get("registrador_email")
        or form_data.get("solicitante_email")
        or form_data.get("email")
        or ""
    ).strip().lower()

    if init_email and init_email in user_emails:
        return True

    # 3. Comparación por registrador_id en form_data
    init_reg_id = str(form_data.get("registrador_id") or "").strip()
    if init_reg_id:
        if profile and init_reg_id == str(profile.id):
            return True
        if claims.get("sub") and init_reg_id == str(claims.get("sub")):
            return True

    # 4. Comparación por nombre del registrador / solicitante
    claim_name = (claims.get("name") or "").strip().lower()
    profile_name = (profile.name if profile else "").strip().lower()
    user_names = {n for n in (claim_name, profile_name) if n}

    init_name = str(form_data.get("registrador") or form_data.get("solicitante") or "").strip().lower()
    if init_name and init_name in user_names:
        return True

    return False


@router.get("", response_model=List[InitiativeResponse])
async def list_initiatives(
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    claims: Dict[str, Any] = Depends(get_current_user_claims),
):
    """
    Lista las iniciativas registradas con filtros opcionales de estado.
    REGLA: Las iniciativas en estado borrador solo las puede visualizar el registrador de la misma,
    nadie más. Esta recién se hace visible para el resto siempre y cuando pasen a los siguientes estados.
    """
    profile = await get_current_user_profile(db, claims)

    query = select(Initiative).order_by(desc(Initiative.updated_at))
    if status_filter:
        query = query.where(Initiative.status == status_filter)
    result = await db.execute(query)
    all_initiatives = result.scalars().all()

    visible = []
    for init in all_initiatives:
        if is_initiative_draft(init):
            # Solo la puede visualizar el registrador de la misma
            if is_user_initiative_registrador(init, claims, profile):
                visible.append(init)
        else:
            # Ya avanzó a los siguientes estados -> visible para los demás
            visible.append(init)

    return visible


@router.get("/{id}", response_model=InitiativeResponse)
async def get_initiative(
    id: str,
    db: AsyncSession = Depends(get_db),
    claims: Dict[str, Any] = Depends(get_current_user_claims),
):
    """
    Obtiene el detalle completo de una iniciativa por ID.
    REGLA: Las iniciativas en estado borrador solo las puede visualizar el registrador de la misma.
    """
    result = await db.execute(select(Initiative).where(Initiative.id == id))
    initiative = result.scalar_one_or_none()
    if not initiative:
        raise HTTPException(status_code=404, detail="Iniciativa no encontrada")

    if is_initiative_draft(initiative):
        profile = await get_current_user_profile(db, claims)
        if not is_user_initiative_registrador(initiative, claims, profile):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado: Las iniciativas en estado borrador solo las puede visualizar el registrador de la misma."
            )

    return initiative


@router.post("", response_model=InitiativeResponse)
async def create_initiative(
    payload: InitiativeCreate,
    db: AsyncSession = Depends(get_db),
    claims: Dict[str, Any] = Depends(get_current_user_claims),
):
    """Crea una nueva iniciativa o borrador asegurando la vinculación con el usuario registrador."""
    init_id = payload.id or f"init_{int(datetime.now().timestamp())}_{str(uuid4())[:8]}"

    # Resolver perfil del usuario autor
    profile = await get_current_user_profile(db, claims)
    user_id = profile.id if profile else None

    form_data = dict(payload.form_data or {})
    if profile:
        if not form_data.get("registrador"):
            form_data["registrador"] = profile.name
        if not form_data.get("registrador_email"):
            form_data["registrador_email"] = profile.email
        if not form_data.get("registrador_id"):
            form_data["registrador_id"] = str(profile.id)
    else:
        if claims.get("name") and not form_data.get("registrador"):
            form_data["registrador"] = claims.get("name")
        if claims.get("email") and not form_data.get("registrador_email"):
            form_data["registrador_email"] = claims.get("email")
        if claims.get("sub") and not form_data.get("registrador_id"):
            form_data["registrador_id"] = str(claims.get("sub"))

    initiative = Initiative(
        id=init_id,
        status=payload.status,
        form_data=form_data,
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
    """Guarda o actualiza un borrador de iniciativa validando la propiedad del registrador."""
    profile = await get_current_user_profile(db, claims)
    if payload.id:
        result = await db.execute(select(Initiative).where(Initiative.id == payload.id))
        existing = result.scalar_one_or_none()
        if existing:
            if is_initiative_draft(existing) and not is_user_initiative_registrador(existing, claims, profile):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Acceso denegado: Las iniciativas en estado borrador solo las puede visualizar o modificar el registrador de la misma."
                )

            # Asociar autoría si no estaba vinculada
            if not existing.user_id and profile:
                existing.user_id = profile.id

            form_data = dict(payload.form_data or {})
            if profile:
                if not form_data.get("registrador"):
                    form_data["registrador"] = existing.form_data.get("registrador") or profile.name
                if not form_data.get("registrador_email"):
                    form_data["registrador_email"] = existing.form_data.get("registrador_email") or profile.email
                if not form_data.get("registrador_id"):
                    form_data["registrador_id"] = existing.form_data.get("registrador_id") or str(profile.id)

            existing.form_data = form_data
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
    """Actualiza campos, estado o expediente de una iniciativa validando permisos de borrador."""
    result = await db.execute(select(Initiative).where(Initiative.id == id))
    initiative = result.scalar_one_or_none()
    if not initiative:
        raise HTTPException(status_code=404, detail="Iniciativa no encontrada")

    if is_initiative_draft(initiative):
        profile = await get_current_user_profile(db, claims)
        if not is_user_initiative_registrador(initiative, claims, profile):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado: Las iniciativas en estado borrador solo las puede visualizar o modificar el registrador de la misma."
            )

    update_data = payload.model_dump(exclude_unset=True)
    if "chat_history" in update_data and update_data["chat_history"]:
        update_data["chat_history"] = [m.model_dump() if hasattr(m, "model_dump") else m for m in update_data["chat_history"]]

    for key, value in update_data.items():
        setattr(initiative, key, value)

    initiative.updated_at = datetime.now()
    await db.commit()
    await db.refresh(initiative)
    return initiative
