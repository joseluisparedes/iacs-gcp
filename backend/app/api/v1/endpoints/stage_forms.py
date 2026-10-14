from datetime import datetime, timezone
from typing import Any, Dict
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_current_user_claims
from app.domain.models import DocumentTemplate, InitiativeStageRecord, StageConsent, StageForm
from app.infrastructure.database import get_db

router = APIRouter()


# ── Stage Forms (Formularios de Etapa) ─────────────────────────────────────────

@router.get("/stage-forms")
async def list_stage_forms(
    include_inactive: bool = Query(True),
    db: AsyncSession = Depends(get_db)
):
    query = select(StageForm)
    if not include_inactive:
        query = query.where(StageForm.is_active == True)
    query = query.order_by(StageForm.name.asc())
    result = await db.execute(query)
    forms = result.scalars().all()
    form_list = [
        {
            "id": str(f.id),
            "code": f.code,
            "name": f.name,
            "description": f.description,
            "fields": f.fields or [],
            "is_active": f.is_active,
            "created_at": f.created_at.isoformat() if f.created_at else None,
            "updated_at": f.updated_at.isoformat() if f.updated_at else None,
        }
        for f in forms
    ]
    return {"data": form_list, "forms": form_list}


@router.get("/stage-forms/{id}")
async def get_stage_form(id: str, db: AsyncSession = Depends(get_db)):
    try:
        f_uuid = UUID(id)
        result = await db.execute(select(StageForm).where(StageForm.id == f_uuid))
    except ValueError:
        result = await db.execute(select(StageForm).where(StageForm.code == id))

    form = result.scalar_one_or_none()
    if not form:
        raise HTTPException(status_code=404, detail="Formulario no encontrado")

    return {
        "data": {
            "id": str(form.id),
            "code": form.code,
            "name": form.name,
            "description": form.description,
            "fields": form.fields or [],
            "is_active": form.is_active,
            "created_at": form.created_at.isoformat() if form.created_at else None,
            "updated_at": form.updated_at.isoformat() if form.updated_at else None,
        }
    }


@router.post("/stage-forms")
async def create_stage_form(payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    code = payload.get("code") or f"form_{int(datetime.now().timestamp())}"
    # Verify uniqueness of code
    existing = await db.execute(select(StageForm).where(StageForm.code == code))
    if existing.scalar_one_or_none():
        code = f"{code}_{int(datetime.now().timestamp())}"

    form = StageForm(
        code=code,
        name=payload.get("name", "Nuevo Formulario"),
        description=payload.get("description", ""),
        fields=payload.get("fields", []),
        is_active=payload.get("is_active", True),
    )
    db.add(form)
    await db.commit()
    await db.refresh(form)
    return {
        "data": {
            "id": str(form.id),
            "code": form.code,
            "name": form.name,
            "description": form.description,
            "fields": form.fields or [],
            "is_active": form.is_active,
        }
    }


@router.put("/stage-forms/{id}")
@router.patch("/stage-forms/{id}")
async def update_stage_form(id: str, payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    try:
        f_uuid = UUID(id)
        result = await db.execute(select(StageForm).where(StageForm.id == f_uuid))
    except ValueError:
        result = await db.execute(select(StageForm).where(StageForm.code == id))

    form = result.scalar_one_or_none()
    if not form:
        raise HTTPException(status_code=404, detail="Formulario no encontrado")

    if "name" in payload:
        form.name = payload["name"]
    if "description" in payload:
        form.description = payload["description"]
    if "code" in payload:
        form.code = payload["code"]
    if "fields" in payload:
        form.fields = payload["fields"]
        if form.code == "form_registro_iniciativa":
            from app.domain.models import InitiativeField
            for idx, fld in enumerate(payload["fields"]):
                f_key = fld.get("key")
                if not f_key:
                    continue
                res_if = await db.execute(select(InitiativeField).where(InitiativeField.key == f_key))
                existing_if = res_if.scalar_one_or_none()
                if existing_if:
                    existing_if.label = fld.get("label", existing_if.label)
                    existing_if.field_type = fld.get("type", existing_if.field_type)
                    existing_if.options = fld.get("options", existing_if.options)
                    existing_if.is_required = fld.get("required", existing_if.is_required)
                    existing_if.ask_in_initial_form = fld.get("ask_in_initial_form", existing_if.ask_in_initial_form)
                    existing_if.help_text = fld.get("helpText") or fld.get("help_text", existing_if.help_text)
                    existing_if.sort_order = idx + 1
                else:
                    new_if = InitiativeField(
                        label=fld.get("label", f_key),
                        key=f_key,
                        field_type=fld.get("type", "text"),
                        options=fld.get("options", []),
                        is_required=fld.get("required", False),
                        ask_in_initial_form=fld.get("ask_in_initial_form", False),
                        help_text=fld.get("helpText") or fld.get("help_text", ""),
                        is_visible=True,
                        sort_order=idx + 1,
                        section="form"
                    )
                    db.add(new_if)
    if "is_active" in payload:
        form.is_active = payload["is_active"]
    form.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(form)
    return {
        "data": {
            "id": str(form.id),
            "code": form.code,
            "name": form.name,
            "description": form.description,
            "fields": form.fields or [],
            "is_active": form.is_active,
        }
    }


@router.delete("/stage-forms/{id}")
async def delete_stage_form(id: str, db: AsyncSession = Depends(get_db)):
    try:
        f_uuid = UUID(id)
        result = await db.execute(select(StageForm).where(StageForm.id == f_uuid))
    except ValueError:
        result = await db.execute(select(StageForm).where(StageForm.code == id))

    form = result.scalar_one_or_none()
    if not form:
        raise HTTPException(status_code=404, detail="Formulario no encontrado")

    await db.delete(form)
    await db.commit()
    return {"data": {"status": "deleted", "id": str(form.id)}}


@router.post("/stage-forms/{id}/duplicate")
async def duplicate_stage_form(id: str, db: AsyncSession = Depends(get_db)):
    try:
        f_uuid = UUID(id)
        result = await db.execute(select(StageForm).where(StageForm.id == f_uuid))
    except ValueError:
        result = await db.execute(select(StageForm).where(StageForm.code == id))

    form = result.scalar_one_or_none()
    if not form:
        raise HTTPException(status_code=404, detail="Formulario no encontrado")

    new_code = f"{form.code}_copia_{int(datetime.now().timestamp())}"
    new_form = StageForm(
        code=new_code,
        name=f"{form.name} (Copia)",
        description=form.description,
        fields=form.fields,
        is_active=True,
    )
    db.add(new_form)
    await db.commit()
    await db.refresh(new_form)
    return {
        "data": {
            "id": str(new_form.id),
            "code": new_form.code,
            "name": new_form.name,
            "description": new_form.description,
            "fields": new_form.fields or [],
            "is_active": new_form.is_active,
        }
    }


# ── Stage Consents (Consentimientos & Declaraciones) ──────────────────────────

@router.get("/stage-consents")
async def list_stage_consents(
    include_inactive: bool = Query(True),
    db: AsyncSession = Depends(get_db)
):
    query = select(StageConsent)
    if not include_inactive:
        query = query.where(StageConsent.is_active == True)
    query = query.order_by(StageConsent.title.asc())
    result = await db.execute(query)
    consents = result.scalars().all()
    consent_list = [
        {
            "id": str(c.id),
            "code": c.code,
            "title": c.title,
            "statement": c.statement,
            "version": c.version,
            "is_active": c.is_active,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        }
        for c in consents
    ]
    return {"data": consent_list, "consents": consent_list}


@router.get("/stage-consents/{id}")
async def get_stage_consent(id: str, db: AsyncSession = Depends(get_db)):
    try:
        c_uuid = UUID(id)
        result = await db.execute(select(StageConsent).where(StageConsent.id == c_uuid))
    except ValueError:
        result = await db.execute(select(StageConsent).where(StageConsent.code == id))

    consent = result.scalar_one_or_none()
    if not consent:
        raise HTTPException(status_code=404, detail="Consentimiento no encontrado")

    return {
        "data": {
            "id": str(consent.id),
            "code": consent.code,
            "title": consent.title,
            "statement": consent.statement,
            "version": consent.version,
            "is_active": consent.is_active,
            "created_at": consent.created_at.isoformat() if consent.created_at else None,
            "updated_at": consent.updated_at.isoformat() if consent.updated_at else None,
        }
    }


@router.post("/stage-consents")
async def create_stage_consent(payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    code = payload.get("code") or f"consent_{int(datetime.now().timestamp())}"
    existing = await db.execute(select(StageConsent).where(StageConsent.code == code))
    if existing.scalar_one_or_none():
        code = f"{code}_{int(datetime.now().timestamp())}"

    consent = StageConsent(
        code=code,
        title=payload.get("title", "Nuevo Consentimiento"),
        statement=payload.get("statement", ""),
        version=payload.get("version", 1),
        is_active=payload.get("is_active", True),
    )
    db.add(consent)
    await db.commit()
    await db.refresh(consent)
    return {
        "data": {
            "id": str(consent.id),
            "code": consent.code,
            "title": consent.title,
            "statement": consent.statement,
            "version": consent.version,
            "is_active": consent.is_active,
        }
    }


@router.put("/stage-consents/{id}")
@router.patch("/stage-consents/{id}")
async def update_stage_consent(id: str, payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    try:
        c_uuid = UUID(id)
        result = await db.execute(select(StageConsent).where(StageConsent.id == c_uuid))
    except ValueError:
        result = await db.execute(select(StageConsent).where(StageConsent.code == id))

    consent = result.scalar_one_or_none()
    if not consent:
        raise HTTPException(status_code=404, detail="Consentimiento no encontrado")

    if "title" in payload:
        consent.title = payload["title"]
    if "statement" in payload:
        consent.statement = payload["statement"]
    if "version" in payload:
        consent.version = payload["version"]
    if "code" in payload:
        consent.code = payload["code"]
    if "is_active" in payload:
        consent.is_active = payload["is_active"]
    consent.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(consent)
    return {
        "data": {
            "id": str(consent.id),
            "code": consent.code,
            "title": consent.title,
            "statement": consent.statement,
            "version": consent.version,
            "is_active": consent.is_active,
        }
    }


@router.delete("/stage-consents/{id}")
async def delete_stage_consent(id: str, db: AsyncSession = Depends(get_db)):
    try:
        c_uuid = UUID(id)
        result = await db.execute(select(StageConsent).where(StageConsent.id == c_uuid))
    except ValueError:
        result = await db.execute(select(StageConsent).where(StageConsent.code == id))

    consent = result.scalar_one_or_none()
    if not consent:
        raise HTTPException(status_code=404, detail="Consentimiento no encontrado")

    await db.delete(consent)
    await db.commit()
    return {"data": {"status": "deleted", "id": str(consent.id)}}


# ── Document Templates (Generador de Documentos) ───────────────────────────────

@router.get("/document-templates")
async def list_document_templates(
    include_inactive: bool = Query(True),
    db: AsyncSession = Depends(get_db)
):
    query = select(DocumentTemplate)
    if not include_inactive:
        query = query.where(DocumentTemplate.is_active == True)
    query = query.order_by(DocumentTemplate.is_default.desc(), DocumentTemplate.name.asc())
    result = await db.execute(query)
    templates = result.scalars().all()
    template_list = [
        {
            "id": str(t.id),
            "code": t.code,
            "name": t.name,
            "description": t.description,
            "template_html": t.template_html,
            "margins": t.margins or {"top": 15, "right": 15, "bottom": 15, "left": 15},
            "is_active": t.is_active,
            "is_default": t.is_default,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "updated_at": t.updated_at.isoformat() if t.updated_at else None,
        }
        for t in templates
    ]
    return {"data": template_list, "templates": template_list}


@router.get("/document-templates/{id}")
async def get_document_template(id: str, db: AsyncSession = Depends(get_db)):
    try:
        t_uuid = UUID(id)
        result = await db.execute(select(DocumentTemplate).where(DocumentTemplate.id == t_uuid))
    except ValueError:
        result = await db.execute(select(DocumentTemplate).where(DocumentTemplate.code == id))

    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")

    return {
        "data": {
            "id": str(t.id),
            "code": t.code,
            "name": t.name,
            "description": t.description,
            "template_html": t.template_html,
            "margins": t.margins or {"top": 15, "right": 15, "bottom": 15, "left": 15},
            "is_active": t.is_active,
            "is_default": t.is_default,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "updated_at": t.updated_at.isoformat() if t.updated_at else None,
        }
    }


@router.post("/document-templates")
async def create_document_template(payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    code = payload.get("code") or f"doc_{int(datetime.now().timestamp())}"
    existing = await db.execute(select(DocumentTemplate).where(DocumentTemplate.code == code))
    if existing.scalar_one_or_none():
        code = f"{code}_{int(datetime.now().timestamp())}"

    t = DocumentTemplate(
        code=code,
        name=payload.get("name", "Nueva Plantilla de Documento"),
        description=payload.get("description", ""),
        template_html=payload.get("template_html", "<div>Plantilla IACS</div>"),
        margins=payload.get("margins", {"top": 15, "right": 15, "bottom": 15, "left": 15}),
        is_active=payload.get("is_active", True),
        is_default=payload.get("is_default", False),
    )
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return {
        "data": {
            "id": str(t.id),
            "code": t.code,
            "name": t.name,
            "description": t.description,
            "is_active": t.is_active,
            "is_default": t.is_default,
        }
    }


@router.patch("/document-templates/{id}")
async def update_document_template(id: str, payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    try:
        t_uuid = UUID(id)
        result = await db.execute(select(DocumentTemplate).where(DocumentTemplate.id == t_uuid))
    except ValueError:
        result = await db.execute(select(DocumentTemplate).where(DocumentTemplate.code == id))

    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")

    if "name" in payload:
        t.name = payload["name"]
    if "description" in payload:
        t.description = payload["description"]
    if "template_html" in payload:
        t.template_html = payload["template_html"]
    if "margins" in payload:
        t.margins = payload["margins"]
    if "is_active" in payload:
        t.is_active = payload["is_active"]
    if "is_default" in payload:
        t.is_default = payload["is_default"]
    t.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(t)
    return {
        "data": {
            "id": str(t.id),
            "code": t.code,
            "name": t.name,
            "is_active": t.is_active,
            "is_default": t.is_default,
        }
    }


@router.delete("/document-templates/{id}")
async def delete_document_template(id: str, db: AsyncSession = Depends(get_db)):
    try:
        t_uuid = UUID(id)
        result = await db.execute(select(DocumentTemplate).where(DocumentTemplate.id == t_uuid))
    except ValueError:
        result = await db.execute(select(DocumentTemplate).where(DocumentTemplate.code == id))

    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")

    await db.delete(t)
    await db.commit()
    return {"data": {"status": "deleted", "id": str(t.id)}}


# ── Initiative Stage Records (Cadena de Custodia & Dictámenes) ───────────────

@router.get("/initiatives/{id}/stage-records")
async def get_initiative_stage_records(id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(InitiativeStageRecord)
        .where(InitiativeStageRecord.initiative_id == id)
        .order_by(InitiativeStageRecord.submitted_at)
    )
    return result.scalars().all()


@router.post("/initiatives/{id}/stage-record")
async def create_initiative_stage_record(
    id: str,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    claims: Dict[str, Any] = Depends(get_current_user_claims),
):
    record = InitiativeStageRecord(
        initiative_id=id,
        node_id=payload["node_id"],
        stage_name=payload.get("stage_name"),
        form_id=payload.get("form_id"),
        consent_id=payload.get("consent_id"),
        user_name=claims.get("name"),
        user_role=payload.get("user_role") or (claims.get("roles", ["registrador"])[0]),
        form_data=payload.get("form_data", {}),
        consent_accepted=payload.get("consent_accepted", True),
        consent_text_snapshot=payload.get("consent_text_snapshot"),
        action_taken=payload.get("action_taken", "approved"),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record
