from typing import Any, Dict, Optional
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.models import (
    AppRole, Direccion, Profile, ProfileRole, VP,
    AllowedUser, UserRoleWhitelist,
    AgentLog, EmailLog, SiteSetting, DocumentTemplate
)
from app.infrastructure.database import get_db
from app.infrastructure.seeder import seed_database_if_needed
from app.api.v1.endpoints.auth import build_user_profile_payload

router = APIRouter()


# ── Sembrador Manual ────────────────────────────────────────────────────────
@router.post("/seed")
async def trigger_seeder():
    await seed_database_if_needed()
    return {"status": "ok", "message": "Sembrado ejecutado con éxito"}


# ── Roles del Sistema y Catálogo de Roles ──────────────────────────────────
@router.get("/roles")
@router.get("/admin/roles")
async def list_roles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AppRole).order_by(AppRole.is_system.desc(), AppRole.name.asc()))
    roles = result.scalars().all()

    # Contar usuarios asociados a cada rol
    count_res = await db.execute(
        select(UserRoleWhitelist.role, func.count(UserRoleWhitelist.id)).group_by(UserRoleWhitelist.role)
    )
    role_counts = dict(count_res.all())

    # Fallback también contando profile_roles
    p_count_res = await db.execute(
        select(ProfileRole.role, func.count(ProfileRole.id)).group_by(ProfileRole.role)
    )
    p_role_counts = dict(p_count_res.all())

    output = []
    for r in roles:
        u_count = max(role_counts.get(r.code, 0), p_role_counts.get(r.code, 0))
        output.append({
            "id": str(r.id),
            "code": r.code,
            "name": r.name,
            "description": r.description,
            "color": r.color or "indigo",
            "is_system": r.is_system,
            "is_active": r.is_active,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            "user_count": u_count,
        })
    return output


@router.post("/roles")
@router.post("/admin/roles")
async def create_role(payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    code = payload["code"].strip().lower()
    name = payload["name"].strip()
    existing = await db.execute(select(AppRole).where(AppRole.code == code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Ya existe un rol con el código '{code}'")

    role = AppRole(
        code=code,
        name=name,
        description=payload.get("description", "").strip() or None,
        color=payload.get("color", "indigo"),
        is_system=payload.get("is_system", False),
        is_active=payload.get("is_active", True),
    )
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return {
        "id": str(role.id),
        "code": role.code,
        "name": role.name,
        "description": role.description,
        "color": role.color,
        "is_system": role.is_system,
        "is_active": role.is_active,
        "user_count": 0,
    }


@router.put("/roles/{id}")
@router.put("/admin/roles/{id}")
async def update_role(id: str, payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AppRole).where(AppRole.id == id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")

    if "name" in payload and payload["name"]:
        role.name = payload["name"].strip()
    if "description" in payload:
        role.description = payload["description"].strip() if payload["description"] else None
    if "color" in payload and payload["color"]:
        role.color = payload["color"]
    if "is_active" in payload:
        if role.code == "admin" and not payload["is_active"]:
            raise HTTPException(status_code=400, detail="El rol Administrador no puede desactivarse")
        role.is_active = payload["is_active"]

    await db.commit()
    await db.refresh(role)
    return {
        "id": str(role.id),
        "code": role.code,
        "name": role.name,
        "description": role.description,
        "color": role.color,
        "is_system": role.is_system,
        "is_active": role.is_active,
    }


@router.delete("/roles/{id}")
@router.delete("/admin/roles/{id}")
async def delete_role(id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AppRole).where(AppRole.id == id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    if role.is_system:
        raise HTTPException(status_code=400, detail="Los roles base del sistema están protegidos y no pueden ser eliminados.")

    await db.delete(role)
    await db.commit()
    return {"success": True}



# ── Estructura Organizacional: VPs y Direcciones ─────────────────────────────
@router.get("/vps")
@router.get("/estructura/vps")
async def list_vps(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(VP).order_by(VP.name))
    return result.scalars().all()


@router.post("/estructura/vps")
async def save_vp(payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    vp_id = payload.get("id")
    name = payload.get("name", "").strip()
    bp_name = payload.get("bp_name", "").strip() or None
    if not name:
        raise HTTPException(status_code=400, detail="El nombre de la VP es requerido")

    if vp_id:
        result = await db.execute(select(VP).where(VP.id == vp_id))
        vp = result.scalar_one_or_none()
        if not vp:
            raise HTTPException(status_code=404, detail="VP no encontrada")
        vp.name = name
        vp.bp_name = bp_name
    else:
        vp = VP(name=name, bp_name=bp_name)
        db.add(vp)

    await db.commit()
    await db.refresh(vp)
    return vp


@router.delete("/estructura/vps/{id}")
async def delete_vp(id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(VP).where(VP.id == id))
    vp = result.scalar_one_or_none()
    if not vp:
        raise HTTPException(status_code=404, detail="VP no encontrada")
    await db.delete(vp)
    await db.commit()
    return {"success": True}


@router.get("/direcciones")
@router.get("/estructura/direcciones")
async def list_direcciones(vp_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    query = select(Direccion).order_by(Direccion.name)
    if vp_id:
        query = query.where(Direccion.vp_id == vp_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/estructura/direcciones")
async def save_direccion(payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    dir_id = payload.get("id")
    name = payload.get("name", "").strip()
    vp_id = payload.get("vp_id")
    if not name or not vp_id:
        raise HTTPException(status_code=400, detail="Nombre y VP son requeridos")

    if dir_id:
        result = await db.execute(select(Direccion).where(Direccion.id == dir_id))
        dir_obj = result.scalar_one_or_none()
        if not dir_obj:
            raise HTTPException(status_code=404, detail="Dirección no encontrada")
        dir_obj.name = name
        dir_obj.vp_id = vp_id
    else:
        dir_obj = Direccion(name=name, vp_id=vp_id)
        db.add(dir_obj)

    await db.commit()
    await db.refresh(dir_obj)
    return dir_obj


@router.delete("/estructura/direcciones/{id}")
async def delete_direccion(id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Direccion).where(Direccion.id == id))
    dir_obj = result.scalar_one_or_none()
    if not dir_obj:
        raise HTTPException(status_code=404, detail="Dirección no encontrada")
    await db.delete(dir_obj)
    await db.commit()
    return {"success": True}


# ── Gestión de Usuarios y Accesos (Lista Blanca y Perfiles) ─────────────────
@router.get("/users")
@router.get("/admin/users")
async def list_users(db: AsyncSession = Depends(get_db)):
    # 1. Traer usuarios de la lista blanca ordenados por fecha
    result = await db.execute(select(AllowedUser).order_by(AllowedUser.created_at.desc()))
    allowed = result.scalars().all()

    # 2. Traer perfiles para saber si el usuario activó su cuenta
    prof_res = await db.execute(select(Profile.email))
    active_emails = {p.lower().strip() for p in prof_res.scalars().all() if p}

    # 3. Mapa de VPs para incrustar el nombre de VP en las asignaciones
    vps_res = await db.execute(select(VP))
    vp_map = {str(v.id): v.name for v in vps_res.scalars().all()}

    output = []
    for u in allowed:
        roles_res = await db.execute(
            select(UserRoleWhitelist).where(UserRoleWhitelist.allowed_user_id == u.id)
        )
        whitelist_roles = roles_res.scalars().all()

        assignments_list = []
        for r in whitelist_roles:
            vp_id_str = str(r.vp_id) if r.vp_id else None
            assignments_list.append({
                "id": str(r.id),
                "role": r.role,
                "vp_id": vp_id_str,
                "direcciones_ids": [str(d) for d in (r.direcciones_ids or [])],
                "is_transversal": bool(r.is_transversal),
                "vps": {"name": vp_map.get(vp_id_str, "Sin VP")} if vp_id_str else None,
            })

        output.append({
            "id": str(u.id),
            "email": u.email,
            "name": u.name,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "is_active": u.email.lower().strip() in active_emails,
            "user_roles_whitelist": assignments_list,
        })
    return output


@router.post("/users")
@router.post("/admin/users")
async def save_user(payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    user_id = payload.get("id")
    email = payload.get("email", "").strip().lower()
    name = payload.get("name", "").strip()
    assignments = payload.get("assignments", [])

    if not email or not name:
        raise HTTPException(status_code=400, detail="Nombre y correo son requeridos")

    if user_id:
        u_res = await db.execute(select(AllowedUser).where(AllowedUser.id == user_id))
        user = u_res.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        user.name = name
    else:
        existing_res = await db.execute(select(AllowedUser).where(AllowedUser.email == email))
        user = existing_res.scalar_one_or_none()
        if user:
            user.name = name
        else:
            user = AllowedUser(email=email, name=name)
            db.add(user)
            await db.commit()
            await db.refresh(user)

    # Re-asignar roles de lista blanca
    await db.execute(delete(UserRoleWhitelist).where(UserRoleWhitelist.allowed_user_id == user.id))
    for a in assignments:
        is_trans = bool(a.get("is_transversal", False) or a.get("role") in ["admin", "entrenador_ia", "ai_trainer"])
        vp_id = None if is_trans else (a.get("vp_id") or None)
        dirs = [] if is_trans else a.get("direcciones_ids", [])
        db.add(UserRoleWhitelist(
            allowed_user_id=user.id,
            role=a.get("role", "registrador"),
            vp_id=vp_id,
            direcciones_ids=dirs,
            is_transversal=is_trans,
        ))

    # Sincronizar también con Profile y ProfileRole
    prof_res = await db.execute(select(Profile).where(func.lower(Profile.email) == email))
    prof = prof_res.scalar_one_or_none()

    primary_vp_id = None
    primary_dir_id = None
    for a in assignments:
        is_trans = bool(a.get("is_transversal", False) or a.get("role") in ["admin", "entrenador_ia", "ai_trainer"])
        if not is_trans and a.get("vp_id"):
            primary_vp_id = a.get("vp_id")
            if a.get("direcciones_ids") and len(a.get("direcciones_ids")) > 0:
                primary_dir_id = a.get("direcciones_ids")[0]
            break

    if not prof:
        prof = Profile(
            email=email,
            name=name,
            vp_id=primary_vp_id,
            direccion_id=primary_dir_id,
            is_active=True
        )
        db.add(prof)
        await db.commit()
        await db.refresh(prof)
    else:
        prof.name = name
        prof.vp_id = primary_vp_id
        prof.direccion_id = primary_dir_id
        prof.is_active = True

    await db.execute(delete(ProfileRole).where(ProfileRole.profile_id == prof.id))
    for a in assignments:
        is_trans = bool(a.get("is_transversal", False) or a.get("role") in ["admin", "entrenador_ia", "ai_trainer"])
        vp_id = None if is_trans else (a.get("vp_id") or None)
        dirs = [] if is_trans else a.get("direcciones_ids", [])
        db.add(ProfileRole(
            profile_id=prof.id,
            role=a.get("role", "registrador"),
            vp_id=vp_id,
            direcciones_ids=dirs,
            is_transversal=is_trans,
        ))

    await db.commit()
    await db.refresh(prof)

    user_payload = await build_user_profile_payload(prof, db, user)
    return {"success": True, "id": str(user.id), "user": user_payload}


@router.delete("/users/{id}")
@router.delete("/admin/users/{id}")
async def delete_user(id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AllowedUser).where(AllowedUser.id == id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    await db.delete(user)
    await db.commit()
    return {"success": True}


@router.get("/profiles")
@router.get("/admin/profiles")
async def list_profiles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Profile).order_by(Profile.name.asc()))
    profiles = result.scalars().all()
    return [
        {
            "id": str(p.id),
            "name": p.name,
            "email": p.email,
            "is_active": p.is_active,
            "avatar_url": p.avatar_url,
        }
        for p in profiles
    ]




# ── Tablero de Agentes IA (Agent Logs) ─────────────────────────────────────────
@router.get("/agents/logs")
async def list_agent_logs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AgentLog).order_by(AgentLog.created_at.desc()))
    return result.scalars().all()


@router.post("/agents/logs")
async def create_agent_log(payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    log = AgentLog(
        agent_role=payload["agent_role"],
        task_title=payload["task_title"],
        status=payload.get("status", "completed"),
        progress=payload.get("progress", 100),
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


# ── Auditoría de Correos Electrónicos ───────────────────────────────────────
@router.get("/emails/logs")
async def list_email_logs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EmailLog).order_by(EmailLog.created_at.desc()))
    return result.scalars().all()


# ── Configuración del Sitio (Site Settings) ──────────────────────────────────
@router.get("/settings")
async def get_site_settings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SiteSetting).where(SiteSetting.id == 1))
    setting = result.scalar_one_or_none()
    if not setting:
        return {"maintenance_mode": False, "sandbox_enabled": True}
    return {
        "maintenance_mode": setting.maintenance_mode,
        "system_notice": setting.system_notice,
        "sandbox_enabled": True
    }


@router.put("/settings")
async def update_site_settings(payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SiteSetting).where(SiteSetting.id == 1))
    setting = result.scalar_one_or_none()
    if not setting:
        setting = SiteSetting(id=1, maintenance_mode=payload.get("maintenance_mode", False), system_notice=payload.get("system_notice"))
        db.add(setting)
    else:
        if "maintenance_mode" in payload:
            setting.maintenance_mode = payload["maintenance_mode"]
        if "system_notice" in payload:
            setting.system_notice = payload["system_notice"]
    await db.commit()
    return {"status": "ok", "maintenance_mode": setting.maintenance_mode}


# ── Plantillas PDF Oficiales ────────────────────────────────────────────────
@router.get("/pdf-templates")
async def list_pdf_templates(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DocumentTemplate))
    return result.scalars().all()


@router.post("/pdf-templates")
async def save_pdf_template(payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    template_id = payload.get("id")
    if template_id:
        result = await db.execute(select(DocumentTemplate).where(DocumentTemplate.id == template_id))
        tmpl = result.scalar_one_or_none()
        if not tmpl:
            raise HTTPException(status_code=404, detail="Plantilla no encontrada")
        tmpl.name = payload.get("name", tmpl.name)
        tmpl.template_html = payload.get("template_html", tmpl.template_html)
        tmpl.margins = payload.get("margins", tmpl.margins)
    else:
        tmpl = DocumentTemplate(
            code=payload.get("code", f"TMPL_{uuid4().hex[:6].upper()}"),
            name=payload.get("name", "Plantilla PDF"),
            description=payload.get("description", ""),
            template_html=payload.get("template_html", "<div>{{titulo}}</div>"),
            margins=payload.get("margins", {"top": 20, "right": 20, "bottom": 20, "left": 20})
        )
        db.add(tmpl)
    await db.commit()
    await db.refresh(tmpl)
    return tmpl
