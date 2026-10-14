import calendar
from datetime import datetime

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.models import AITrainingConfig
from app.infrastructure.database import get_db
from app.integrations.ai.vertex_provider import VertexAIService
from app.schemas.ai import SpeechToTextResponse, SummarizeRequest, TeoChatRequest, TeoChatResponse

router = APIRouter()
ai_service = VertexAIService()


def get_date_context_section() -> str:
    now = datetime.now()
    d = str(now.day).zfill(2)
    m = str(now.month).zfill(2)
    y = now.year
    today_str = f"{d}/{m}/{y}"

    month_names = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
    ]
    today_readable = f"{now.day} de {month_names[now.month - 1]} de {y}"

    def format_offset(months_ahead: int) -> str:
        new_m = ((now.month - 1 + months_ahead) % 12) + 1
        new_y = now.year + ((now.month - 1 + months_ahead) // 12)
        max_d = calendar.monthrange(new_y, new_m)[1]
        target_d = min(now.day, max_d)
        return f"{str(target_d).zfill(2)}/{str(new_m).zfill(2)}/{new_y}"

    def end_of_month(months_ahead: int = 0) -> str:
        new_m = ((now.month - 1 + months_ahead) % 12) + 1
        new_y = now.year + ((now.month - 1 + months_ahead) // 12)
        max_d = calendar.monthrange(new_y, new_m)[1]
        return f"{str(max_d).zfill(2)}/{str(new_m).zfill(2)}/{new_y}"

    return f"""
## Contexto Temporal del Sistema (CRÍTICO PARA CÁLCULO DE FECHAS)
- **Fecha actual del sistema (HOY)**: {today_str} ({today_readable})
- **Año actual**: {y}
- **Referencias precalculadas de plazos exactos desde hoy ({today_str})**:
  * En 1 mes: {format_offset(1)} (o fin de mes: {end_of_month(1)})
  * En 2 meses: {format_offset(2)}
  * En 3 meses: {format_offset(3)}
  * En 4 meses: {format_offset(4)}
  * En 6 meses: {format_offset(6)}
  * Fin de este mes: {end_of_month(0)}
  * Fin de año actual: 31/12/{y}
- **REGLAS ESTRICTAS PARA EL CÁLCULO Y SUGERENCIA DE FECHAS**:
  1. Si el usuario o el objetivo menciona un plazo relativo (ej. 'en los próximos 3 meses', 'en 2 meses', 'el próximo mes', 'a fin de año'), DEBES calcular la fecha tentativa sumando exactamente dicho plazo a la **Fecha actual de hoy ({today_str})**.
  2. NUNCA calcules una fecha en el pasado o en un mes menor al plazo mencionado.
  3. Propón siempre la fecha estimada en formato **DD/MM/AAAA** para que el usuario la valide o confirme.
""".strip()


async def get_system_prompt_from_db(db: AsyncSession) -> str:
    """Construye el system prompt de Teo concatenando identidad, contexto temporal, Grill-Me y carpetas de conocimiento."""
    from app.domain.models import AIKnowledgeFolder

    # 1. Obtener carpetas para mapeo de rutas jerárquicas
    folders_res = await db.execute(select(AIKnowledgeFolder))
    folders = folders_res.scalars().all()
    folder_map = {f.id: f for f in folders}

    def build_path(fid):
        if not fid or fid not in folder_map:
            return ""
        f = folder_map[fid]
        parent = build_path(f.parent_id)
        return f"{parent} > {f.name}" if parent else f.name

    # 2. Obtener configuraciones activas
    result = await db.execute(
        select(AITrainingConfig)
        .where(AITrainingConfig.is_active == True)
        .order_by(AITrainingConfig.sort_order)
    )
    configs = result.scalars().all()

    identity = (
        "Eres Teo, Asesor Senior de Arquitectura e Iniciativas de TI en IACS. "
        "Tu propósito es guiar de forma empática, ejecutiva y analítica a los solicitantes para estructurar iniciativas "
        "claras, cuantificables y técnicamente viables. Tu comunicación es natural, elegante, concisa y profesional: "
        "dialogas como un consultor humano de primer nivel, vas al grano, evitas explicaciones teóricas innecesarias "
        "y nunca saturas al usuario con muros de texto ni cuestionarios abrumadores. Avanzas paso a paso, abordando "
        "un solo aspecto crítico por turno."
    )

    for c in configs:
        if c.layer == "identity":
            identity = c.content
            break

    date_section = f"\n\n{get_date_context_section()}"

    dialogue_guidelines = """
## Directivas de Diálogo Progresivo y Concisión Ejecutiva (OBLIGATORIO)
1. **Extrema Concisión**: Escribe mensajes breves, cálidos y directos (máximo 2 a 3 párrafos cortos de 2 a 3 líneas cada uno). NUNCA redactes textos kilométricos ni discursos teóricos.
2. **Una Sola Pregunta por Turno**: Está TERMINANTEMENTE PROHIBIDO enviar listas o cuestionarios de múltiples preguntas (como '1)... 2)... 3)... 4)...') en un solo mensaje. En cada turno formula ÚNICAMENTE UNA sola pregunta enfocada. Espera la respuesta del usuario antes de pasar al siguiente aspecto.
3. **Cero Meta-Lenguaje**: NUNCA uses ni menciones términos internos frente al usuario como 'grillarte', 'grill-me', 'guardarrieles', 'árbol de dependencias', 'orquestador' o 'metodología de indagación'. Exprésate de forma 100% natural, cercana y humana.
4. **Validación Inicial Exclusiva**: Cuando el usuario plantee su necesidad por primera vez, tu ÚNICA tarea es reconocer brevemente su requerimiento en una frase empática, proponer el **Título de la iniciativa (propuesto)** y el **Objetivo principal (propuesto)** en negritas markdown, y consultar amablemente si está de acuerdo. NO formules preguntas sobre sistemas, fechas, alcance ni presupuesto en este primer mensaje. Las opciones deben ser estrictamente: ["Sí, estoy de acuerdo", "Quiero ajustarlo"].
5. **Opciones Breves y Accionables**: Cada alternativa en 'options' debe ser una opción concisa de máximo 6 a 8 palabras.
6. **Cierre sin Vacíos**: No añadas la etiqueta técnica '[INFORMACION_COMPLETA]' si quedan supuestos sin responder o campos obligatorios vacíos.
"""

    context_items = [c for c in configs if c.layer == "context"]
    context_section = ""
    if context_items:
        lines = ["\n## Contexto Institucional"]
        for c in context_items:
            path = build_path(c.folder_id)
            hdr = f"### [{path}] {c.title}" if path else f"### {c.title}"
            lines.append(f"{hdr}\n{c.content}")
        context_section = "\n\n".join(lines)

    example_items = [c for c in configs if c.layer == "examples"]
    examples_section = ""
    if example_items:
        lines = ["\n## Ejemplos de Conversación Ideal"]
        for e in example_items:
            lines.append(f"Usuario: \"{e.title}\"\nAgente: \"{e.content}\"")
        examples_section = "\n\n".join(lines)

    guardrail_items = [c for c in configs if c.layer == "guardrails"]
    guardrails_section = ""
    if guardrail_items:
        lines = ["\n## Guardarrieles y Restricciones Absolutas (DEBES cumplir siempre sin excepción)"]
        for g in guardrail_items:
            lines.append(f"- **{g.title}**: {g.content}")
        guardrails_section = "\n".join(lines)

    return f"{identity}{date_section}\n{dialogue_guidelines}{context_section}\n{examples_section}\n{guardrails_section}".strip()


@router.post("/chat", response_model=TeoChatResponse)
async def chat_with_teo(
    payload: TeoChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """Endpoint conversacional principal con Teo aplicando Grill-Me."""
    system_prompt = await get_system_prompt_from_db(db)
    response_data = await ai_service.chat(
        system_prompt=system_prompt,
        history=payload.history,
        message=payload.message,
        initial_data=payload.initialData or {},
        ai_fields=payload.aiFields or [],
    )
    return TeoChatResponse(**response_data)


@router.post("/summarize")
async def summarize_initiative(
    payload: SummarizeRequest,
    db: AsyncSession = Depends(get_db),
):
    """Sintetiza la conversación de chat y extrae la ficha técnica estructurada."""
    system_prompt = await get_system_prompt_from_db(db)
    return await ai_service.summarize(
        system_prompt=system_prompt,
        history=payload.history,
        initial_data=payload.initialData or {},
        fields_schema=payload.aiFields or [],
    )


@router.post("/chat/speech-to-text", response_model=SpeechToTextResponse)
async def speech_to_text(audio: UploadFile = File(...)):
    """Transcribe un archivo de audio grabado por el usuario a texto en español."""
    audio_bytes = await audio.read()
    mime = audio.content_type or "audio/webm"
    text = await ai_service.transcribe_audio(audio_bytes=audio_bytes, mime_type=mime)
    return SpeechToTextResponse(text=text)


@router.post("/chat/attach-file")
async def attach_file_to_chat(file: UploadFile = File(...)):
    """Extrae texto de un documento adjunto para ser inyectado en el contexto de Teo."""
    file_bytes = await file.read()
    filename = file.filename or "uploaded_file"
    mime = file.content_type or "application/octet-stream"
    extracted_text = await ai_service.extract_document_text(file_bytes, filename, mime)
    return {
        "filename": filename,
        "name": filename,
        "size": len(file_bytes),
        "content": extracted_text[:35000],
        "text": extracted_text[:35000],
    }
