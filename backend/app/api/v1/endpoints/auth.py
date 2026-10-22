from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token, get_current_user_claims, verify_password, get_password_hash
from app.domain.models import Profile, ProfileRole, AllowedUser, UserRoleWhitelist, VP, Direccion
from app.infrastructure.database import get_db

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


class SignUpRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None


class CheckEmailRequest(BaseModel):
    email: str


class DevTokenRequest(BaseModel):
    email: str
    name: str
    role: str = "registrador"


async def build_user_profile_payload(
    profile: Profile,
    db: AsyncSession,
    allowed_user: Optional[AllowedUser] = None
) -> Dict[str, Any]:
    """Construye un payload estructurado y actualizado con los roles, VP y Direcciones del usuario."""
    # 1. Obtener roles asignados
    roles_res = await db.execute(select(ProfileRole).where(ProfileRole.profile_id == profile.id))
    profile_roles = roles_res.scalars().all()
    roles = [r.role for r in profile_roles]

    whitelist_roles = []
    if not roles and allowed_user:
        w_res = await db.execute(select(UserRoleWhitelist).where(UserRoleWhitelist.allowed_user_id == allowed_user.id))
        whitelist_roles = w_res.scalars().all()
        roles = [w.role for w in whitelist_roles]
    if not roles:
        roles = ["registrador"]

    # 2. Determinar VP efectiva
    effective_vp_id = profile.vp_id
    # Si profile_roles tiene asignación no transversal, tiene prioridad
    for r in profile_roles:
        if not r.is_transversal and r.vp_id:
            effective_vp_id = r.vp_id
            break
    if not effective_vp_id and whitelist_roles:
        for w in whitelist_roles:
            if not w.is_transversal and w.vp_id:
                effective_vp_id = w.vp_id
                break

    # Si se detectó VP y profile no la tenía actualizada, sincronizarla
    if effective_vp_id and profile.vp_id != effective_vp_id:
        profile.vp_id = effective_vp_id
        await db.commit()
        await db.refresh(profile)

    vp_name = None
    if effective_vp_id:
        v_res = await db.execute(select(VP).where(VP.id == effective_vp_id))
        v_obj = v_res.scalar_one_or_none()
        if v_obj:
            vp_name = v_obj.name

    # 3. Recopilar IDs y nombres de Direcciones asignadas
    dir_ids_set = set()
    for r in profile_roles:
        if r.direcciones_ids:
            for d in r.direcciones_ids:
                if d:
                    dir_ids_set.add(d)
    if not dir_ids_set and whitelist_roles:
        for w in whitelist_roles:
            if w.direcciones_ids:
                for d in w.direcciones_ids:
                    if d:
                        dir_ids_set.add(d)

    direcciones_names = []
    if dir_ids_set:
        d_res = await db.execute(select(Direccion).where(Direccion.id.in_(list(dir_ids_set))))
        dirs_list = d_res.scalars().all()
        direcciones_names = [d.name for d in dirs_list]

    return {
        "id": str(profile.id),
        "email": profile.email,
        "name": profile.name,
        "roles": roles,
        "role": roles[0] if roles else "registrador",
        "vp_id": str(effective_vp_id) if effective_vp_id else None,
        "vp_name": vp_name,
        "vpName": vp_name,
        "direccion_id": str(profile.direccion_id) if profile.direccion_id else None,
        "direcciones": direcciones_names,
        "direcciones_ids": [str(d) for d in dir_ids_set],
        "profile_roles": [
            {
                "role": r.role,
                "vp_id": str(r.vp_id) if r.vp_id else None,
                "direcciones_ids": [str(d) for d in (r.direcciones_ids or [])],
                "is_transversal": r.is_transversal,
            }
            for r in profile_roles
        ],
    }


@router.post("/login")
@router.post("/auth/login")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    clean_email = payload.email.strip().lower()

    # 1. Verificar estrictamente la lista blanca institucional (allowed_users)
    allowed_res = await db.execute(select(AllowedUser).where(func.lower(AllowedUser.email) == clean_email))
    allowed_user = allowed_res.scalar_one_or_none()
    if not allowed_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu correo no está en la lista de accesos permitidos. Contacta al administrador."
        )

    # 2. Verificar perfil del usuario
    prof_res = await db.execute(select(Profile).where(func.lower(Profile.email) == clean_email))
    profile = prof_res.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Credenciales incorrectas. Si eres nuevo y ya te dieron acceso, ve a \"Activar mi acceso\"."
        )

    # 3. Validar contraseña
    if profile.password_hash and not verify_password(payload.password, profile.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas. Si eres nuevo y ya te dieron acceso, ve a \"Activar mi acceso\"."
        )

    # 4. Construir información completa y actualizada del perfil
    user_data = await build_user_profile_payload(profile, db, allowed_user)

    token = create_access_token({
        "sub": str(profile.id),
        "email": profile.email,
        "name": profile.name,
        "roles": user_data["roles"],
        "vp_id": user_data["vp_id"],
        "direccion_id": user_data["direccion_id"],
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_data
    }


@router.post("/signup")
@router.post("/auth/signup")
@router.post("/auth/activate")
async def signup(payload: SignUpRequest, db: AsyncSession = Depends(get_db)):
    clean_email = payload.email.strip().lower()

    # 1. Verificar estrictamente la lista blanca institucional (allowed_users)
    allowed_res = await db.execute(select(AllowedUser).where(func.lower(AllowedUser.email) == clean_email))
    allowed_user = allowed_res.scalar_one_or_none()
    if not allowed_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu correo no está en la lista de accesos permitidos. Contacta al administrador."
        )

    # 2. Verificar si ya tiene contraseña establecida
    prof_res = await db.execute(select(Profile).where(func.lower(Profile.email) == clean_email))
    profile = prof_res.scalar_one_or_none()
    if profile and profile.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya tienes una cuenta creada. Por favor, inicia sesión."
        )

    # 3. Establecer contraseña y crear/activar Profile
    hashed_pwd = get_password_hash(payload.password)
    user_name = (payload.name or (allowed_user.name if allowed_user else "Usuario IACS")).strip()

    if not profile:
        profile = Profile(
            email=clean_email,
            name=user_name,
            password_hash=hashed_pwd,
            is_active=True
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    else:
        profile.password_hash = hashed_pwd
        profile.name = user_name
        profile.is_active = True

    # Sincronizar roles desde lista blanca si existen
    if allowed_user:
        allowed_user.password_hash = hashed_pwd
        w_res = await db.execute(select(UserRoleWhitelist).where(UserRoleWhitelist.allowed_user_id == allowed_user.id))
        w_roles = w_res.scalars().all()
        await db.execute(delete(ProfileRole).where(ProfileRole.profile_id == profile.id))
        for w in w_roles:
            db.add(ProfileRole(
                profile_id=profile.id,
                role=w.role,
                vp_id=w.vp_id,
                direcciones_ids=w.direcciones_ids,
                is_transversal=w.is_transversal
            ))
            if w.vp_id and not profile.vp_id:
                profile.vp_id = w.vp_id

    await db.commit()
    await db.refresh(profile)

    user_data = await build_user_profile_payload(profile, db, allowed_user)

    token = create_access_token({
        "sub": str(profile.id),
        "email": profile.email,
        "name": profile.name,
        "roles": user_data["roles"],
        "vp_id": user_data["vp_id"],
        "direccion_id": user_data["direccion_id"],
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "message": "Cuenta creada y activada exitosamente.",
        "user": user_data
    }


@router.post("/check-allowed")
@router.post("/auth/check-allowed")
async def check_allowed(payload: CheckEmailRequest, db: AsyncSession = Depends(get_db)):
    clean_email = payload.email.strip().lower()
    res = await db.execute(select(AllowedUser).where(func.lower(AllowedUser.email) == clean_email))
    user = res.scalar_one_or_none()
    return {"allowed": bool(user), "name": user.name if user else None}


@router.get("/me")
async def get_me(
    email: Optional[str] = None,
    claims: Dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_db)
):
    """Devuelve el perfil del usuario autenticado y sus roles asignados."""
    target_email = (email.strip() if email else None) or claims.get("email")
    if not target_email:
        return claims

    clean_email = target_email.strip().lower()
    result = await db.execute(select(Profile).where(func.lower(Profile.email) == clean_email))
    profile = result.scalar_one_or_none()

    if profile:
        allowed_res = await db.execute(select(AllowedUser).where(func.lower(AllowedUser.email) == clean_email))
        allowed_user = allowed_res.scalar_one_or_none()
        return await build_user_profile_payload(profile, db, allowed_user)

    return claims


@router.post("/dev-token")
async def generate_dev_token(payload: DevTokenRequest):
    """Generador de tokens JWT para agilizar el desarrollo local y pruebas."""
    token = create_access_token({
        "sub": payload.email,
        "email": payload.email,
        "name": payload.name,
        "roles": [payload.role]
    })
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "email": payload.email,
            "name": payload.name,
            "roles": [payload.role]
        }
    }
