from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import require_role
from app.domain.models import AIKnowledgeFolder, AITrainingConfig, AIFeedback, SiteSetting
from app.infrastructure.database import get_db

router = APIRouter()


# ── Carpetas de Conocimiento (Hasta 3 niveles) ──────────────────────────────
@router.get("/ai-training/folders")
async def list_training_folders(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AIKnowledgeFolder)
        .order_by(AIKnowledgeFolder.level.asc(), AIKnowledgeFolder.sort_order.asc(), AIKnowledgeFolder.name.asc())
    )
    return result.scalars().all()


@router.post("/ai-training/folders", dependencies=[Depends(require_role(["admin", "entrenador_ia"]))])
async def create_training_folder(payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    parent_id = payload.get("parent_id")
    level = 1
    if parent_id:
        p_res = await db.execute(select(AIKnowledgeFolder).where(AIKnowledgeFolder.id == parent_id))
        parent = p_res.scalar_one_or_none()
        if parent:
            if parent.level >= 3:
                raise HTTPException(status_code=400, detail="La jerarquía solo admite un máximo de 3 niveles.")
            level = parent.level + 1

    folder = AIKnowledgeFolder(
        name=payload["name"].strip(),
        parent_id=parent_id or None,
        level=level,
        sort_order=payload.get("sort_order", 0),
    )
    db.add(folder)
    await db.commit()
    await db.refresh(folder)
    return folder


@router.patch("/ai-training/folders/{id}", dependencies=[Depends(require_role(["admin", "entrenador_ia"]))])
async def update_training_folder(id: str, payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AIKnowledgeFolder).where(AIKnowledgeFolder.id == id))
    folder = result.scalar_one_or_none()
    if not folder:
        raise HTTPException(status_code=404, detail="Carpeta no encontrada")

    if "name" in payload and payload["name"]:
        folder.name = payload["name"].strip()
    if "sort_order" in payload:
        folder.sort_order = payload["sort_order"]

    await db.commit()
    await db.refresh(folder)
    return folder


@router.delete("/ai-training/folders/{id}", dependencies=[Depends(require_role(["admin", "entrenador_ia"]))])
async def delete_training_folder(
    id: str,
    deleteItems: bool = Query(False),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(AIKnowledgeFolder).where(AIKnowledgeFolder.id == id))
    folder = result.scalar_one_or_none()
    if not folder:
        raise HTTPException(status_code=404, detail="Carpeta no encontrada")

    if deleteItems:
        await db.execute(delete(AITrainingConfig).where(AITrainingConfig.folder_id == folder.id))
    else:
        # Desvincular entradas a la raíz
        entries_res = await db.execute(select(AITrainingConfig).where(AITrainingConfig.folder_id == folder.id))
        for e in entries_res.scalars().all():
            e.folder_id = None

    await db.delete(folder)
    await db.commit()
    return {"success": True}


# ── Configuración de Entrenamiento y Guardarraíles ──────────────────────────
@router.get("/ai-training")
async def list_ai_training_entries(layer: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    query = select(AITrainingConfig).order_by(AITrainingConfig.sort_order.asc(), AITrainingConfig.created_at.asc())
    if layer:
        query = query.where(AITrainingConfig.layer == layer)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/ai-training", dependencies=[Depends(require_role(["admin", "entrenador_ia"]))])
async def create_ai_training_entry(payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    entry = AITrainingConfig(
        layer=payload["layer"],
        title=payload["title"].strip(),
        content=payload["content"].strip(),
        is_active=payload.get("is_active", True),
        sort_order=payload.get("sort_order", 0),
        source=payload.get("source", "manual"),
        folder_id=payload.get("folder_id"),
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


@router.patch("/ai-training/{id}", dependencies=[Depends(require_role(["admin", "entrenador_ia"]))])
@router.put("/ai-training/{id}", dependencies=[Depends(require_role(["admin", "entrenador_ia"]))])
async def update_ai_training_entry(id: str, payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AITrainingConfig).where(AITrainingConfig.id == id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entrada no encontrada")

    if "title" in payload and payload["title"] is not None:
        entry.title = payload["title"].strip()
    if "content" in payload and payload["content"] is not None:
        entry.content = payload["content"].strip()
    if "is_active" in payload and payload["is_active"] is not None:
        entry.is_active = bool(payload["is_active"])
    if "sort_order" in payload and payload["sort_order"] is not None:
        entry.sort_order = int(payload["sort_order"])
    if "folder_id" in payload:
        entry.folder_id = payload["folder_id"]

    await db.commit()
    await db.refresh(entry)
    return entry


@router.delete("/ai-training/{id}", dependencies=[Depends(require_role(["admin", "entrenador_ia"]))])
async def delete_ai_training_entry(id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AITrainingConfig).where(AITrainingConfig.id == id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entrada no encontrada")
    await db.delete(entry)
    await db.commit()
    return {"success": True}


# ── Sandbox Status & Toggle ────────────────────────────────────────────────
@router.get("/sandbox/status")
async def get_sandbox_status(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SiteSetting).where(SiteSetting.id == 1))
    setting = result.scalar_one_or_none()
    if not setting:
        return {"enabled": True}
    return {"enabled": bool(setting.sandbox_enabled)}


@router.post("/sandbox/toggle", dependencies=[Depends(require_role(["admin", "entrenador_ia"]))])
async def toggle_sandbox_status(payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    enabled = payload.get("enabled", True)
    result = await db.execute(select(SiteSetting).where(SiteSetting.id == 1))
    setting = result.scalar_one_or_none()
    if not setting:
        setting = SiteSetting(id=1, sandbox_enabled=enabled)
        db.add(setting)
    else:
        setting.sandbox_enabled = enabled
    await db.commit()
    return {"enabled": enabled}


@router.post("/sandbox/chat")
async def sandbox_chat(payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    # 1. Validar si el sandbox está activo
    result = await db.execute(select(SiteSetting).where(SiteSetting.id == 1))
    setting = result.scalar_one_or_none()
    if setting and setting.sandbox_enabled is False:
        raise HTTPException(
            status_code=403,
            detail="El Sandbox Ejecutivo de Teo se encuentra temporalmente desactivado por la Dirección de TI."
        )

    history = payload.get("history", [])
    message = payload.get("message", "")
    current_draft = payload.get("currentDraft", {}) or {}
    attachment = payload.get("attachment")

    if not message and not attachment:
        raise HTTPException(status_code=400, detail="Mensaje o archivo requerido.")

    # 2. Extraer contexto de base de conocimiento activa
    kb_res = await db.execute(
        select(AITrainingConfig).where(
            AITrainingConfig.layer == "context",
            AITrainingConfig.is_active == True
        )
    )
    kb_items = kb_res.scalars().all()
    kb_text = "\n\n".join([f"[{k.title}]: {k.content}" for k in kb_items])

    # 3. Intentar procesar con Vertex AI si está activo
    import json
    import logging
    logger = logging.getLogger(__name__)

    prompt = f"""
Eres TEO, el Business Partner de TI (BP TI) Senior más experimentado de Laureate Perú (red que incluye UPC, UPN y Cibertec).
Tu misión es entrevistar al solicitante (CIO, directores y jefaturas de negocio) para CAPTURAR, DESAFIAR Y ATERRIZAR una necesidad de TI con el máximo rigor técnico y funcional.

REGLAS DE INTERACCIÓN DE TEO:
1. Desafía constructivamente, no seas un tomador pasivo de pedidos.
2. Reconoce lo que el usuario aporta y formula 1 o 2 preguntas incisivas y específicas.
3. Conoce el ecosistema Laureate Perú: Banner, Blackboard Ultra, Salesforce, SAP, Niubiz.
4. Rúbrica de madurez en 5 dimensiones (0 a 100%): problema_raiz, impacto_usuarios, metricas_exito, ecosistema_ti, restricciones_plazos.
5. Actualiza continua y obligatoriamente 'draftPreview' en cada turno.
6. Párrafos respirables con doble salto de línea (\\n\\n) y negritas (**texto**).

BASE DE CONOCIMIENTO INSTITUCIONAL:
{kb_text}

ESTADO ACTUAL DE LA FICHA BORRADOR:
{json.dumps(current_draft, ensure_ascii=False, indent=2)}

HISTORIAL:
{json.dumps(history, ensure_ascii=False)}

MENSAJE DEL USUARIO:
{message}
{f'ARCHIVO ADJUNTO: {attachment.get("name")} - {attachment.get("textContent", "")[:3000]}' if attachment else ''}

Devuelve EXCLUSIVAMENTE un JSON válido con esta estructura:
{{
  "text": "Tu respuesta conversacional con párrafos respirables y negritas markdown",
  "options": ["Opción 1", "Opción 2", "Opción 3"],
  "draftPreview": {{
    "titulo_de_la_necesidad": "...",
    "objetivo": "...",
    "descripcion_de_la_necesidad": "...",
    "beneficio_cuantitativo_anual": "...",
    "proceso_y_areas_impactadas": "...",
    "qu_pasa_si_no_lo_tenemos_en_esta_fecha": "...",
    "sistemas_involucrados": ["Banner", "SAP"],
    "institucion_sugerida": "UPC" | "UPN" | "Cibertec" | "Laureate Perú (Corporativo)"
  }},
  "dimensions": {{
    "problema_raiz": {{ "score": 75, "comment": "..." }},
    "impacto_usuarios": {{ "score": 60, "comment": "..." }},
    "metricas_exito": {{ "score": 50, "comment": "..." }},
    "ecosistema_ti": {{ "score": 70, "comment": "..." }},
    "restricciones_plazos": {{ "score": 55, "comment": "..." }}
  }},
  "readinessScore": 62,
  "isReady": false
}}
"""

    ai_result = None
    try:
        from app.api.v1.endpoints.ai import ai_service
        if not ai_service.use_mock and ai_service._client:
            resp = await ai_service._client.generate_content_async(prompt)
            clean_text = resp.text.strip().replace("```json", "").replace("```", "").strip()
            ai_result = json.loads(clean_text)
    except Exception as e:
        logger.warning(f"Error calling Vertex AI in sandbox: {e}")

    if not ai_result or not ai_result.get("text"):
        # Fallback determinista inteligente (The Architect)
        lower_msg = (message or "").lower()
        inst = "Laureate Perú (Corporativo)"
        if "upn" in lower_msg:
            inst = "UPN"
        elif "upc" in lower_msg:
            inst = "UPC"
        elif "cibertec" in lower_msg:
            inst = "Cibertec"

        title_derived = message[:60] + "..." if len(message) > 60 else message
        turn_count = len(history) // 2 + 1
        base_score = min(85, 30 + (turn_count * 15))

        ai_result = {
            "text": f"Comprendo el planteamiento sobre **\"{title_derived}\"** para **{inst}**.\n\nPara que la necesidad quede debidamente estructurada ante el comité de TI, afinemos dos aspectos clave:\n\n(1) **Ecosistema y Arquitectura:** ¿Qué sistemas corporativos (**Banner**, **SAP**, **Blackboard** o portal web) deberán conectarse?\n\n(2) **Impacto Cuantitativo:** ¿Cuál es la meta medible esperada (reducción de tiempos, alumnos impactados o ahorro estimado)?",
            "options": [
                f"Integrar autoservicio en el Portal del Estudiante con SAP y pasarela de pagos en {inst}",
                "Alertas preventivas y seguimiento de retención estudiantil",
                "Piloto focalizado para el próximo ciclo académico con medición de impacto"
            ],
            "draftPreview": {
                "titulo_de_la_necesidad": current_draft.get("titulo_de_la_necesidad") or f"Iniciativa: {title_derived}",
                "objetivo": current_draft.get("objetivo") or f"Implementar y optimizar la solución de {title_derived} para incrementar la efectividad operativa y experiencia estudiantil en {inst}.",
                "descripcion_de_la_necesidad": (current_draft.get("descripcion_de_la_necesidad") + f"\n\nDetalle: {message}") if current_draft.get("descripcion_de_la_necesidad") else message,
                "beneficio_cuantitativo_anual": current_draft.get("beneficio_cuantitativo_anual") or "Estimación de ahorro o retención entre 15% y 25% anual",
                "proceso_y_areas_impactadas": current_draft.get("proceso_y_areas_impactadas") or f"Operaciones y Servicios Académicos - {inst}",
                "qu_pasa_si_no_lo_tenemos_en_esta_fecha": current_draft.get("qu_pasa_si_no_lo_tenemos_en_esta_fecha") or "Riesgo de cuello de botella operativo y fricción en la experiencia de los alumnos",
                "sistemas_involucrados": current_draft.get("sistemas_involucrados") or ["Banner", "SAP", "Portal Web"],
                "institucion_sugerida": inst
            },
            "dimensions": {
                "problema_raiz": { "score": min(100, base_score + 10), "comment": "Problema identificado y delimitado con proceso." },
                "impacto_usuarios": { "score": min(100, base_score), "comment": f"Población objetivo identificada en {inst}." },
                "metricas_exito": { "score": min(100, max(20, base_score - 10)), "comment": "En proceso de dimensionar métricas cuantificables." },
                "ecosistema_ti": { "score": min(100, base_score + 5), "comment": "Ecosistema de plataformas base identificado." },
                "restricciones_plazos": { "score": min(100, base_score - 5), "comment": "Ventana de despliegue en evaluación." }
            },
            "readinessScore": base_score,
            "isReady": base_score >= 80
        }

    # Mergear con currentDraft
    if ai_result.get("draftPreview") and current_draft:
        merged = {**current_draft, **ai_result["draftPreview"]}
        for k in ["titulo_de_la_necesidad", "objetivo", "descripcion_de_la_necesidad", "beneficio_cuantitativo_anual", "proceso_y_areas_impactadas", "qu_pasa_si_no_lo_tenemos_en_esta_fecha", "institucion_sugerida"]:
            if not ai_result["draftPreview"].get(k) and current_draft.get(k):
                merged[k] = current_draft[k]
        ai_result["draftPreview"] = merged

    return {"data": ai_result}


# ── AI Feedback (Retroalimentación de Usuarios) ───────────────────────────
@router.get("/ai-feedback")
async def list_ai_feedback(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AIFeedback).order_by(AIFeedback.created_at.desc()))
    return result.scalars().all()


@router.post("/ai-feedback")
async def create_ai_feedback(payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    rating = payload.get("rating", "positive")
    if rating not in ["positive", "negative"]:
        raise HTTPException(status_code=400, detail="Rating must be 'positive' or 'negative'")

    feedback = AIFeedback(
        initiative_id=payload.get("initiative_id"),
        message_index=payload.get("message_index", 0),
        user_message=payload.get("user_message", ""),
        agent_response=payload.get("agent_response", ""),
        rating=rating,
        admin_approved=payload.get("admin_approved", False),
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    return feedback


@router.post("/ai-feedback/{id}/approve", dependencies=[Depends(require_role(["admin", "entrenador_ia"]))])
async def approve_ai_feedback(id: str, payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AIFeedback).where(AIFeedback.id == id))
    fb = result.scalar_one_or_none()
    if not fb:
        raise HTTPException(status_code=404, detail="Feedback no encontrado")

    ideal_response = payload.get("ideal_response", fb.agent_response).strip()
    fb.admin_approved = True

    # Guardar como nuevo ejemplo en ai_training_config
    new_example = AITrainingConfig(
        layer="examples",
        title=fb.user_message.strip(),
        content=ideal_response,
        is_active=True,
        sort_order=0,
        source="feedback",
    )
    db.add(new_example)
    await db.commit()
    await db.refresh(fb)
    return {"success": True, "feedback": fb}


@router.delete("/ai-feedback/{id}", dependencies=[Depends(require_role(["admin", "entrenador_ia"]))])
async def delete_ai_feedback(id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AIFeedback).where(AIFeedback.id == id))
    fb = result.scalar_one_or_none()
    if not fb:
        raise HTTPException(status_code=404, detail="Feedback no encontrado")
    await db.delete(fb)
    await db.commit()
    return {"success": True}


# ── Reordenamiento de Guardarraíles / Reglas ───────────────────────────────
@router.post("/ai-training/reorder", dependencies=[Depends(require_role(["admin", "entrenador_ia"]))])
async def reorder_ai_training(payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    ordered_ids = payload.get("orderedIds", [])
    for idx, eid in enumerate(ordered_ids):
        res = await db.execute(select(AITrainingConfig).where(AITrainingConfig.id == eid))
        entry = res.scalar_one_or_none()
        if entry:
            entry.sort_order = idx
    await db.commit()
    return {"success": True}


import io
import re


def extract_text_from_file(filename: str, content_bytes: bytes) -> str:
    name = filename.lower()
    text = ""
    if name.endswith(".pdf"):
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(content_bytes))
            pages_text = [page.extract_text() or "" for page in reader.pages]
            text = "\n\n".join([p.strip() for p in pages_text if p.strip()])
        except Exception as e:
            text = f"[Lectura de PDF: {filename} - {e}]"
    elif name.endswith(".docx"):
        try:
            import docx
            doc = docx.Document(io.BytesIO(content_bytes))
            text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()]).strip()
        except Exception as e:
            text = f"[Lectura de DOCX: {filename} - {e}]"
    elif name.endswith((".xlsx", ".xls")):
        try:
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(content_bytes), data_only=True)
            sheets_text = []
            for sheetname in wb.sheetnames[:3]:
                sheet = wb[sheetname]
                rows_text = []
                for row in sheet.iter_rows(values_only=True):
                    row_vals = [str(v) for v in row if v is not None]
                    if row_vals:
                        rows_text.append(", ".join(row_vals))
                if rows_text:
                    sheets_text.append(f"[Hoja: {sheetname}]\n" + "\n".join(rows_text[:40]))
            text = "\n\n".join(sheets_text).strip()
        except Exception as e:
            text = f"[Lectura de Excel: {filename} - {e}]"
    else:
        try:
            text = content_bytes.decode("utf-8").strip()
        except UnicodeDecodeError:
            try:
                text = content_bytes.decode("latin-1").strip()
            except Exception:
                text = f"[Archivo binario: {filename} ({len(content_bytes)} bytes)]"

    # Sanitizar inyecciones de prompts
    sanitized = re.sub(r'\[/?(SYSTEM|INSTRUCTION|PROMPT|ASSISTANT|ADMIN).*?\]', '', text, flags=re.IGNORECASE)
    sanitized = re.sub(r'(?:ignore|olvida)\s+(?:all\s+)?(?:previous\s+)?instructions', '[instrucción no permitida]', sanitized, flags=re.IGNORECASE)
    return sanitized.strip()


# ── Carga de Documentos / Diagramas para la Base de Conocimiento ──────────
@router.post("/ai-training/upload-document", dependencies=[Depends(require_role(["admin", "entrenador_ia"]))])
async def upload_document_for_training(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if not file:
        raise HTTPException(status_code=400, detail="No se subió ningún archivo.")

    content_bytes = await file.read()
    filename = file.filename or "documento.txt"
    extracted_text = extract_text_from_file(filename, content_bytes)

    if not extracted_text:
        extracted_text = f"Documento {filename} procesado sin contenido de texto legible."

    # Segmentar documento en chunks semánticos (máx 1500 chars por chunk)
    chunks = []
    chunk_size = 1500
    if len(extracted_text) <= chunk_size:
        chunks.append({
            "title": f"Ficha: {filename}",
            "content": extracted_text,
        })
    else:
        parts = [extracted_text[i:i + chunk_size] for i in range(0, len(extracted_text), chunk_size)]
        for idx, part in enumerate(parts):
            chunks.append({
                "title": f"{filename} (Parte {idx + 1} de {len(parts)})",
                "content": part.strip(),
            })

    return {"chunks": chunks, "totalChunks": len(chunks)}


# ── Adjuntos de Chat ───────────────────────────────────────────────────────
@router.post("/chat/attach-file")
async def chat_attach_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if not file:
        raise HTTPException(status_code=400, detail="No se subió ningún archivo.")

    content_bytes = await file.read()
    filename = file.filename or "adjunto.txt"
    name_lower = filename.lower()
    
    # Determinar tipo
    if name_lower.endswith(".pdf"):
        type_key = "pdf"
    elif name_lower.endswith(".docx"):
        type_key = "docx"
    elif name_lower.endswith((".jpg", ".jpeg", ".png", ".webp")):
        type_key = "image"
    else:
        type_key = "txt"

    # Verificar configuración en DB
    res = await db.execute(
        select(AITrainingConfig).where(
            AITrainingConfig.layer == "settings",
            AITrainingConfig.title == f"enable_{type_key}"
        )
    )
    en_setting = res.scalar_one_or_none()
    if en_setting and en_setting.content == "false":
        raise HTTPException(status_code=400, detail=f"La subida de archivos {type_key.upper()} está deshabilitada.")

    # Verificar límite de tamaño
    res_lim = await db.execute(
        select(AITrainingConfig).where(
            AITrainingConfig.layer == "settings",
            AITrainingConfig.title == f"max_size_{type_key}"
        )
    )
    lim_setting = res_lim.scalar_one_or_none()
    max_mb = float(lim_setting.content) if lim_setting and lim_setting.content else 25.0
    if len(content_bytes) > (max_mb * 1024 * 1024):
        raise HTTPException(status_code=400, detail=f"El archivo supera el límite de {max_mb} MB.")

    if type_key == "image":
        formatted_content = f"[Imagen adjunta como evidencia: {filename}]"
    else:
        extracted = extract_text_from_file(filename, content_bytes)
        formatted_content = f'[Contenido del documento {filename} adjunto (DATOS DE LECTURA):\n"""\n{extracted[:3500]}\n"""]'

    return {
        "filename": filename,
        "content": formatted_content,
        "size": len(content_bytes),
        "type": type_key,
    }


# ── Preview Chat (Conexión directa con Teo para pruebas en vivo) ───────────
@router.post("/ai-training/preview-chat")
async def preview_chat_with_teo(payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    from app.api.v1.endpoints.ai import ai_service, get_system_prompt_from_db
    system_prompt = await get_system_prompt_from_db(db)
    history = payload.get("history", [])
    message = payload.get("message", "")
    attached_content = payload.get("attached_content")

    if attached_content:
        full_message = f"{message}\n\n{attached_content}" if message else attached_content
    else:
        full_message = message

    response_data = await ai_service.chat(
        system_prompt=system_prompt,
        history=history,
        message=full_message,
    )
    return response_data

