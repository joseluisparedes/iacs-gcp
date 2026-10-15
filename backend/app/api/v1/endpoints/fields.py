from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.models import InitiativeField, StageForm
from app.infrastructure.database import get_db

router = APIRouter()


@router.get("")
async def list_initiative_fields(db: AsyncSession = Depends(get_db)):
    """Obtiene el catálogo de campos dinámicos para formularios de iniciativas, reflejando form_registro_iniciativa."""
    # 1. Priorizar stage_forms form_registro_iniciativa (Golden Path IACS)
    res_sf = await db.execute(select(StageForm).where(StageForm.code == "form_registro_iniciativa"))
    stage_form = res_sf.scalar_one_or_none()
    if stage_form and isinstance(stage_form.fields, list) and len(stage_form.fields) > 0:
        mapped = [
            {
                "id": f.get("id") or f"f_{f.get('key')}",
                "label": f.get("label"),
                "key": f.get("key"),
                "field_type": f.get("type", "text"),
                "type": f.get("type", "text"),
                "options": f.get("fileOptions") or f.get("options") or [],
                "fileOptions": f.get("fileOptions") or None,
                "is_visible": True,
                "is_required": bool(f.get("required")),
                "sort_order": idx,
                "section": "form",
                "help_text": f.get("helpText") or f.get("placeholder") or f.get("help_text"),
                "placeholder": f.get("placeholder"),
                "allow_multiple": bool(f.get("allow_multiple") or f.get("type") == "multiselect"),
                "ai_instructions": f.get("ai_instructions"),
                "ask_in_initial_form": bool(f.get("ask_in_initial_form")),
            }
            for idx, f in enumerate(stage_form.fields)
        ]
        return mapped

    # 2. Fallback a tabla legacy initiative_fields
    result = await db.execute(
        select(InitiativeField)
        .where(InitiativeField.is_visible == True)
        .order_by(InitiativeField.sort_order)
    )
    fields = result.scalars().all()
    return [
        {
            "id": str(f.id),
            "label": f.label,
            "key": f.key,
            "field_type": f.field_type,
            "type": f.field_type,
            "options": f.options,
            "is_visible": f.is_visible,
            "is_required": f.is_required,
            "sort_order": f.sort_order,
            "section": f.section,
            "depends_on": f.depends_on,
            "options_map": f.options_map,
            "ai_instructions": f.ai_instructions,
            "allow_multiple": f.allow_multiple,
            "help_text": f.help_text,
            "requires_confirmation": f.requires_confirmation,
            "ask_in_initial_form": f.ask_in_initial_form,
            "file_options": f.file_options,
        }
        for f in fields
    ]

