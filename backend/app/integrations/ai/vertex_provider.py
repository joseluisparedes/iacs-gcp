import io
import json
import logging
import re
import time
from typing import Any, Dict, List, Optional
import httpx

from app.core.config import settings
from app.integrations.ai.base import BaseAIService

logger = logging.getLogger(__name__)


def clean_extracted_field(val: Optional[str]) -> Optional[str]:
    if not val:
        return None
    clean = val.strip()
    clean = re.sub(r"^[\s*:'\"“”#\-]+", "", clean)
    clean = re.sub(r"[\s*'\"“”]+$", "", clean).strip()
    return clean or None


def extract_proposal_from_history(history: List[Dict[str, Any]]) -> Dict[str, str]:
    if not history or not isinstance(history, list):
        return {}
    for msg in reversed(history):
        if msg.get("role") in ("model", "assistant") and msg.get("text"):
            text = msg["text"]
            t_match = re.search(
                r"Título\s*[-:]\s*['\"“]?([^'\"”\n]+?)(?:['\"”]?\s*(?:,\s*Objetivo|\s+Objetivo)|\n|$)",
                text,
                re.IGNORECASE,
            ) or re.search(r"Título\s*[-:]\s*['\"“]?([^'\"”\n]+)", text, re.IGNORECASE)
            o_match = re.search(
                r"Objetivo\s*[-:]\s*['\"“]?([^'\"”\n]+?)(?:['\"”]?\s*\.|\?|\n|$)",
                text,
                re.IGNORECASE,
            )
            res = {}
            if t_match:
                t = clean_extracted_field(t_match.group(1))
                if t:
                    res["titulo"] = t
            if o_match:
                o = clean_extracted_field(o_match.group(1))
                if o:
                    res["objetivo"] = o
            if res:
                return res
    return {}


def parse_ai_json(raw: str) -> Optional[Dict[str, Any]]:
    if not raw:
        return None
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text).strip()
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
    return None


class VertexAIService(BaseAIService):
    """
    Motor Empresarial Multi-Proveedor de Inteligencia Artificial para IACS.

    Casacada de ejecución de alta disponibilidad:
    1. Azure OpenAI (GPT-5.1) - Motor Principal Corporativo
    2. Groq (Llama / OSS 120B) - Contingencia de Ultra Baja Latencia
    3. Google Cloud Vertex AI / Gemini 3.8 Flash - Capacidades Multimodales y Fallback
    4. Fallback Dinámico Inteligente - Contingencia Local sin Caídas
    """

    def __init__(self):
        self.use_mock = settings.USE_AI_MOCK
        self.azure_endpoint = settings.AZURE_OPENAI_ENDPOINT.rstrip("/")
        self.azure_key = settings.AZURE_OPENAI_API_KEY
        self.azure_deployment = settings.AZURE_OPENAI_DEPLOYMENT
        self.azure_api_version = settings.AZURE_OPENAI_API_VERSION
        self.gemini_key = settings.GEMINI_API_KEY
        self.groq_key = settings.GROQ_API_KEY
        self._cooldowns: Dict[str, float] = {}

    def _is_cooling_down(self, provider: str) -> bool:
        return time.time() < self._cooldowns.get(provider, 0)

    def _set_cooldown(self, provider: str, seconds: int = 60):
        self._cooldowns[provider] = time.time() + seconds

    async def call_ai_for_json(self, prompt: str, temperature: float = 0.2) -> str:
        """Invoca la cascada de proveedores LLM retornando la cadena JSON cruda."""
        if self.use_mock:
            return ""

        # ── 1. Primary Enterprise Engine: Azure OpenAI (GPT-5.1) ─────────────
        if self.azure_key and self.azure_endpoint and not self._is_cooling_down("azure"):
            try:
                url = f"{self.azure_endpoint}/openai/deployments/{self.azure_deployment}/chat/completions?api-version={self.azure_api_version}"
                headers = {
                    "api-key": self.azure_key,
                    "Content-Type": "application/json",
                }
                payload = {
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "Eres Teo, analista senior de negocio y arquitectura de TI en Laureate Perú (UPC, UPN, Cibertec). "
                                "Responde ÚNICAMENTE en formato JSON válido y estructurado."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": temperature,
                    "max_completion_tokens": 1500,
                    "response_format": {"type": "json_object"},
                }
                async with httpx.AsyncClient(timeout=45.0) as client:
                    resp = await client.post(url, headers=headers, json=payload)
                    if resp.status_code == 200:
                        content = resp.json()["choices"][0]["message"]["content"]
                        if content and content.strip():
                            logger.info("[AI Cascade] Azure OpenAI GPT-5.1 exitoso.")
                            return content.strip()
                    elif resp.status_code in (429, 503):
                        logger.warning(f"[AI Cascade] Azure rate limited ({resp.status_code}). Cooldown 60s.")
                        self._set_cooldown("azure", 60)
            except Exception as e:
                logger.warning(f"[AI Cascade] Azure OpenAI error: {e}")

        # ── 2. Secondary Fast Engine: Groq ────────────────────────────────────
        if self.groq_key and not self._is_cooling_down("groq"):
            models_to_try = ["openai/gpt-oss-120b", "qwen/qwen3.8-27b", "openai/gpt-oss-20b"]
            for model in models_to_try:
                try:
                    headers = {
                        "Authorization": f"Bearer {self.groq_key}",
                        "Content-Type": "application/json",
                    }
                    payload = {
                        "model": model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "Eres Teo, analista de negocio y TI. Responde estrictamente en formato JSON válido.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": temperature,
                        "response_format": {"type": "json_object"},
                    }
                    async with httpx.AsyncClient(timeout=20.0) as client:
                        resp = await client.post(
                            "https://api.groq.com/openai/v1/chat/completions",
                            headers=headers,
                            json=payload,
                        )
                        if resp.status_code == 200:
                            content = resp.json()["choices"][0]["message"]["content"]
                            if content and content.strip():
                                logger.info(f"[AI Cascade] Groq ({model}) exitoso.")
                                return content.strip()
                        elif resp.status_code in (429, 503):
                            logger.warning(f"[AI Cascade] Groq {model} rate limited.")
                except Exception as e:
                    logger.warning(f"[AI Cascade] Groq error on {model}: {e}")
            self._set_cooldown("groq", 60)

        # ── 3. Tertiary Engine: Google Gemini ─────────────────────────────────
        if self.gemini_key and not self._is_cooling_down("gemini"):
            try:
                from google import genai
                client = genai.Client(api_key=self.gemini_key)
                res = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=prompt,
                    config={"response_mime_type": "application/json", "temperature": temperature},
                )
                if res and res.text:
                    logger.info("[AI Cascade] Google Gemini (3.8-flash) exitoso.")
                    return res.text.strip()
            except Exception as e:
                logger.warning(f"[AI Cascade] Gemini error: {e}")
                self._set_cooldown("gemini", 60)

        logger.warning("[AI Cascade] Todos los proveedores remotos fallaron o están en cooldown. Retornando vacío.")
        return ""

    async def chat(
        self,
        system_prompt: str,
        history: List[Dict[str, Any]],
        message: str,
        temperature: float = 0.2,
        initial_data: Optional[Dict[str, Any]] = None,
        ai_fields: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Ejecuta el ciclo conversacional de indagación activa con Teo."""
        initial_data = initial_data or {}
        is_initial_greeting = message == "[INICIALIZAR_CHAT]"
        if is_initial_greeting:
            return {
                "text": (
                    "¡Hola! Soy Teo, tu asesor de arquitectura y proyectos de TI. "
                    "Cuéntame qué necesidad, dolor operativo o mejora deseas abordar. "
                    "También puedes adjuntar documentos o evidencias de sustento con el botón del clip 📎 "
                    "para analizarlos y estructurar tu iniciativa en conjunto."
                ),
                "options": [],
                "allow_multiple": False,
                "extractedFields": {},
            }

        user_messages = [h for h in history if h.get("role") == "user"]
        is_first_user_turn = len(user_messages) == 0
        is_document_submission = bool(re.search(r"\[El usuario adjuntó (?:el archivo|el documento):", message or ""))

        is_user_acceptance = bool(
            re.search(
                r"^\s*(sí|si|de acuerdo|estoy de acuerdo|acepto|conforme|ok|perfecto|adelante|excelente|proceder)",
                message or "",
                re.IGNORECASE,
            )
        )
        extracted_proposal = {}
        if is_user_acceptance or is_first_user_turn or is_document_submission:
            extracted_proposal = extract_proposal_from_history(history)
            if extracted_proposal.get("titulo") and not initial_data.get("titulo"):
                initial_data["titulo"] = extracted_proposal["titulo"]
            if extracted_proposal.get("objetivo") and not initial_data.get("objetivo"):
                initial_data["objetivo"] = extracted_proposal["objetivo"]

        if ai_fields:
            fields_lines = []
            for f in ai_fields:
                key = f.get("key", "")
                if key in ["registrador", "solicitante", "institucion", "vicepresidencia", "direccion", "adjuntos_sustento"]:
                    continue
                label = f.get("label", key)
                ftype = f.get("field_type", "text")
                opts = f.get("options") or []
                opts_str = f" [Opciones permitidas: {', '.join(opts)}]" if ftype == "select" and opts else ""
                instr = f" [Instrucciones: {f.get('ai_instructions')}]" if f.get("ai_instructions") else ""
                req_str = " [Obligatorio]" if f.get("is_required") else ""
                fields_lines.append(f"- Clave: \"{key}\", Campo: \"{label}\" ({ftype}){opts_str}{instr}{req_str}")
            fields_list_str = "\n".join(fields_lines)
        else:
            fields_list_str = (
                "- Clave: \"titulo\", Campo: \"Título de la iniciativa\" (text) [Obligatorio]\n"
                "- Clave: \"objetivo\", Campo: \"Objetivo principal\" (textarea) [Obligatorio]\n"
                "- Clave: \"pilar_estrategico\", Campo: \"Pilar Estratégico\" (select) [Obligatorio]\n"
                "- Clave: \"descripcion_necesidad\", Campo: \"Descripción de la Necesidad\" (textarea) [Obligatorio]\n"
                "- Clave: \"justificacion\", Campo: \"Justificación del Negocio\" (textarea) [Obligatorio]\n"
                "- Clave: \"impacto_esperado\", Campo: \"Impacto Esperado\" (textarea) [Obligatorio]\n"
                "- Clave: \"tipo_solucion\", Campo: \"Tipo de Solución Propuesta\" (select) [Obligatorio]\n"
                "- Clave: \"sistemas_afectados\", Campo: \"Sistemas Core Afectados\" (text)\n"
                "- Clave: \"usuarios_beneficiados\", Campo: \"Usuarios Estimados Beneficiados\" (text)\n"
                "- Clave: \"fecha_tentativa\", Campo: \"Fecha Tentativa de Salida (DD/MM/AAAA)\" (date) [Obligatorio]\n"
                "- Clave: \"requiere_presupuesto\", Campo: \"¿Requiere Presupuesto Externo?\" (select) [Obligatorio]\n"
                "- Clave: \"monto_estimado_usd\", Campo: \"Monto Estimado USD\" (number)\n"
                "- Clave: \"observaciones_adicionales\", Campo: \"Observaciones Adicionales\" (textarea)"
            )

        if is_document_submission:
            session_directive = """
⚠️ DIRECTIVA OBLIGATORIA: ANÁLISIS DE DOCUMENTO ADJUNTO POR EL USUARIO:
El usuario ha adjuntado un documento de sustento técnico o funcional con su contenido transcrito.
DEBES CUMPLIR ESTRICTAMENTE:
1. Confirma con precisión y empatía ejecutiva haber leído minuciosamente el documento adjunto (menciona su nombre exacto y la síntesis del problema o caso de uso extraído).
2. Queda TERMINANTEMENTE PROHIBIDO decir que 'no tienes el detalle funcional' si se incluye el texto del documento. Analiza a fondo las tablas y especificaciones proporcionadas.
3. Sintetiza y formula directamente en negritas markdown:
   **Título de la iniciativa (propuesto):** "[Verbo en infinitivo + alcance concreto extraído del documento]"
   **Objetivo principal (propuesto):** "[Propósito institucional y valor cuantificable extraído del documento]"
4. Pregunta cordialmente: "¿Estás de acuerdo con este planteamiento estructurado a partir de tu documento o deseas afinar algún punto?"
5. En 'options', coloca EXACTAMENTE: ["Sí, estoy de acuerdo", "Quiero ajustarlo"].
6. NO agregues cuestionarios ni múltiples preguntas adicionales en este turno.
"""
        elif is_first_user_turn:
            session_directive = """
⚠️ DIRECTIVA OBLIGATORIA DEL TURNO 1 (PRESENTACIÓN EXCLUSIVA DE TÍTULO Y OBJETIVO):
El usuario acaba de expresar su necesidad o requerimiento por primera vez.
DEBES CUMPLIR ESTRICTAMENTE LO SIGUIENTE:
1. Responde con MÁXIMA BREVEDAD (1 sola frase empática y profesional reconociendo la necesidad).
2. Presenta la propuesta formal en negritas markdown:
   **Título de la iniciativa (propuesto):** "[Verbo en infinitivo como Automatizar/Implementar/Habilitar + alcance concreto]"
   **Objetivo principal (propuesto):** "[Propósito cuantificable o de valor de negocio institucional]"
3. Pregunta amablemente: "¿Estás de acuerdo con esta formulación o deseas realizar algún ajuste?"
4. REGLA ESTRICTA ANTI-SATURACIÓN: ESTÁ TOTALMENTE PROHIBIDO formular ninguna otra pregunta sobre sistemas, alcances, fechas, presupuesto ni aspectos operativos en este mensaje. NO agregues listas numeradas ni preguntas adicionales.
5. En 'options', coloca EXACTAMENTE y ÚNICAMENTE: ["Sí, estoy de acuerdo", "Quiero ajustarlo"].
6. 'allow_multiple': false.
"""
        elif is_user_acceptance:
            current_t = initial_data.get("titulo") or extracted_proposal.get("titulo", "")
            current_o = initial_data.get("objetivo") or extracted_proposal.get("objetivo", "")
            session_directive = f"""
⚠️ DIRECTIVA DEL TURNO 2 — CUESTIONAMIENTO GRILL-ME SOBRE ECOSISTEMA TECNOLÓGICO:
El usuario ha aceptado el Título ("{current_t}") y Objetivo ("{current_o}").
COMO LEAD ENTERPRISE ARCHITECT / BP TI, DEBES:
1. Confirmar brevemente la alineación inicial en 1 sola frase.
2. Queda ESTRICTAMENTE PROHIBIDO volver a proponer el título y objetivo.
3. CUESTIONAR CON RIGOR EL ECOSISTEMA Y LA FUENTE DE VERDAD:
   No te limites a preguntar '¿qué sistemas usas?'. Cuestiona la interacción técnica real entre las plataformas del área sin asumir marcas que el usuario no haya nombrado (como Salesforce o SAP). Pregunta por el rol de la plataforma (CRM, ERP, portal analítico, etc.).
   Formula el dilema técnico central: ¿dónde residirá la regla de negocio, cómo se sincronizarán los estados y cuál será la fuente de verdad?
4. Plantea el dilema en 1-2 párrafos concisos y ofrece una alternativa técnica bien justificada.
5. En 'options', sugiere entre 2 y 4 alternativas técnicas directas y estratégicas. Queda ESTRICTAMENTE PROHIBIDO generar opciones como 'Prefiero que tú propongas el rango', 'Decídelo tú' o que deleguen decisiones y criterios de negocio a la IA.
"""
        else:
            session_directive = """
⚠️ DIRECTIVA DE CUESTIONAMIENTO GRILL-ME Y ESTRUCTURACIÓN INTEGRAL:
Actúa con el ojo crítico de un Lead Enterprise Architect y Business Partner Senior de TI. NO seas complaciente ni actúes como una secretaria que solo toma nota.
1. EVALÚA LA MADUREZ DE LA INICIATIVA:
   Revisa qué aspectos de negocio, arquitectura y operación siguen siendo supuestos o vacíos críticos:
   - Impacto cruzado en otras áreas (ej: finanzas/caja, operaciones, registros académicos, auditoría).
   - Necesidad real y justificación cuantificable: ¿qué dolor resuelve y cómo se medirá el éxito (horas, tasa de conversión, CSAT)?
   - Alternativas vs desarrollo a medida: ¿por qué no parametrizar una herramienta existente?
   - Viabilidad de plazos (DD/MM/AAAA) y riesgo si no se implementa a tiempo.
   - Presupuesto externo (Capex/Opex) y dependencias con terceros.
2. REPREGUNTA CONCISA Y QUIRÚRGICA:
   Formula ÚNICAMENTE UNA sola repregunta retadora por turno.
   Estructura:
   - Diagnóstico o riesgo detectado en 1 o 2 líneas.
   - El dilema o pregunta incisiva que obliga al solicitante a pensar en el proceso global.
   - Tu recomendación técnica sugerida.
3. CONCISIÓN: Máximo 2 a 3 párrafos breves. Cero sábanas de texto.
4. CIERRE DEFINITIVO Y OBLIGATORIO ([INFORMACION_COMPLETA]):
   Únicamente cuando los aspectos clave (sistemas, justificación/impacto, fecha y presupuesto) hayan sido desafiados y acordados, o si el solicitante confirma que no hay más observaciones:
   - Confirma formalmente en 1 frase que la iniciativa ha quedado blindada y estructurada para comité.
   - Incluye OBLIGATORIAMENTE la etiqueta técnica `[INFORMACION_COMPLETA]` al final de tu respuesta.
   - En 'options', coloca: [].
"""

        chat_prompt = f"""{system_prompt}

Datos iniciales proporcionados por el usuario:
{json.dumps(initial_data, ensure_ascii=False, indent=2)}

Campos de la ficha técnica que debemos estructurar:
{fields_list_str}

Historial de conversación:
{chr(10).join([f"{(h.get('role') == 'user' and 'Usuario' or 'Teo')}: {h.get('text', '')}" for h in history])}

Usuario: {message}

{session_directive}

RESPONDE SIEMPRE EN FORMATO JSON ESTRICTO CON LA SIGUIENTE ESTRUCTURA:
{{
  "text": "tu respuesta empática, concisa y ejecutiva respetando las directivas",
  "options": ["Opción sugerida 1", "Opción sugerida 2"],
  "allow_multiple": false,
  "extractedFields": {{}}
}}
"""

        raw_json = await self.call_ai_for_json(chat_prompt, temperature=temperature)
        parsed = parse_ai_json(raw_json)

        if not parsed or not parsed.get("text"):
            logger.info("[AI Chat] Fallback a respuesta local estructurada.")
            return self._mock_chat(history, message, initial_data)

        response_text = parsed.get("text", "")
        # Salvaguarda de Cierre Automático: Si se detecta intención de cierre o texto de finalización
        is_closing_intent = bool(
            re.search(
                r"(ficha técnica ya queda completa|la ficha.*queda completa|procedo a generar el resumen|resumen consolidado|hemos completado todos los puntos|no hay más observaciones)",
                response_text,
                re.IGNORECASE,
            )
            or re.search(
                r"^\s*(no|dejémoslo así|dejemoslo asi|sin observaciones|ninguna|todo conforme|listo|conforme|generar resumen|ver ficha)",
                message.strip(),
                re.IGNORECASE,
            )
        )

        if is_closing_intent and "[INFORMACION_COMPLETA]" not in response_text:
            # Si el modelo empezó a ofrecer slides o continuar conversando cuando ya todo estaba listo:
            if re.search(r"(versión.*slide|presentación ejecutiva|quieres que te entregue.*ficha técnica)", response_text, re.IGNORECASE):
                response_text = (
                    "Excelente. Hemos recopilado toda la información técnica y funcional requerida para la iniciativa. "
                    "A continuación se generará la ficha resumen ejecutiva para tu revisión y validación final. [INFORMACION_COMPLETA]"
                )
            else:
                response_text = f"{response_text.strip()} [INFORMACION_COMPLETA]"

        parsed_options = parsed.get("options") or []
        if "[INFORMACION_COMPLETA]" in response_text:
            parsed_options = []

        parsed_fields = parsed.get("extractedFields") or {}
        if extracted_proposal:
            parsed_fields.update(extracted_proposal)

        return {
            "text": response_text,
            "options": parsed_options,
            "allow_multiple": bool(parsed.get("allow_multiple", False)),
            "extractedFields": parsed_fields,
        }

    async def summarize(
        self,
        system_prompt: str,
        history: List[Dict[str, Any]],
        initial_data: Dict[str, Any],
        fields_schema: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Sintetiza la conversación y extrae la ficha técnica completa."""
        if fields_schema:
            schema_lines = []
            for f in fields_schema:
                k = f.get("key", "")
                if k in ["registrador", "solicitante"]:
                    continue
                opts = f.get("options") or []
                t = f.get("field_type", "string")
                hint = f" (opciones permitidas: {', '.join(opts)})" if opts else ""
                schema_lines.append(f'  "{k}": "{t} - {f.get("label", k)}{hint}"')
            schema_desc = ",\n".join(schema_lines)
        else:
            schema_desc = '  "titulo": "string",\n  "objetivo": "string"'

        summarize_prompt = f"""Eres un Business Analyst Senior de TI en Laureate Perú. A partir de la siguiente conversación y datos, genera un resumen estructurado estrictamente en formato JSON.

REGLA DE ORO — PRIORIDAD DE FUENTES:
1. La conversación con el solicitante es la FUENTE PRIMARIA y VERDADERA.
2. Los datos iniciales son únicamente contexto de partida.

Datos iniciales:
{json.dumps(initial_data, ensure_ascii=False, indent=2)}

Conversación completa:
{chr(10).join([f"{(h.get('role') == 'user' and 'Solicitante' or 'Teo')}: {h.get('text', '')}" for h in history])}

Devuelve SOLO un JSON con la siguiente estructura de campos (llena TODOS los campos posibles con lo acordado en la conversación):
{{
{schema_desc}
}}

REGLAS PARA EL TÍTULO:
- Debe comenzar con un verbo en infinitivo (ej: "Automatización de...", "Implementación de...", "Integración de...").
- Prohibido usar frases genéricas como "Nueva iniciativa" o "Mejora para...".

REGLAS PARA SELECTS Y FECHAS:
- Para campos select (como pilar_estrategico, tipo_solucion, requiere_presupuesto), usa exactamente uno de los valores de las opciones permitidas si aplica.
- Para fechas (fecha_tentativa o fecha_requerida), usa formato DD/MM/AAAA.
"""

        raw_json = await self.call_ai_for_json(summarize_prompt, temperature=0.1)
        parsed = parse_ai_json(raw_json)
        if parsed and (parsed.get("titulo") or parsed.get("objetivo")):
            return parsed

        return self._mock_summarize(history, initial_data)

    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        mime_type: str = "audio/webm",
        domain_prompt: Optional[str] = None,
    ) -> str:
        """Transcribe audio en español utilizando Groq Whisper Large v3 Turbo."""
        if self.groq_key:
            try:
                headers = {"Authorization": f"Bearer {self.groq_key}"}
                files = {
                    "file": ("audio.webm", audio_bytes, mime_type),
                }
                data = {
                    "model": "whisper-large-v3-turbo",
                    "language": "es",
                    "prompt": domain_prompt or "Banner, Blackboard, Salesforce, SAP, ERP, CRM, Laureate Perú, UPC, UPN, Cibertec.",
                    "response_format": "json",
                }
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(
                        "https://api.groq.com/openai/v1/audio/transcriptions",
                        headers=headers,
                        files=files,
                        data=data,
                    )
                    if resp.status_code == 200:
                        text = resp.json().get("text", "").strip()
                        if text:
                            logger.info("[SpeechToText] Whisper transcribe exitoso.")
                            return text
            except Exception as e:
                logger.warning(f"[SpeechToText] Groq Whisper error: {e}")

        return ""

    async def extract_document_text(
        self,
        file_bytes: bytes,
        filename: str,
        mime_type: str,
    ) -> str:
        """Extrae texto de documentos PDF, Word, Excel o planos."""
        lower_name = filename.lower()
        try:
            if lower_name.endswith(".pdf"):
                import pypdf
                reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                return "\n".join([page.extract_text() or "" for page in reader.pages])
            elif lower_name.endswith(".docx"):
                import docx
                doc = docx.Document(io.BytesIO(file_bytes))
                lines = []
                # 1. Párrafos
                for p in doc.paragraphs:
                    t = p.text.strip()
                    if t:
                        lines.append(t)
                # 2. Tablas (crucial para plantillas de caso de uso corporativas)
                for table in doc.tables:
                    for row in table.rows:
                        row_cells = []
                        for cell in row.cells:
                            c_text = cell.text.strip()
                            if c_text and (not row_cells or row_cells[-1] != c_text):
                                row_cells.append(c_text)
                        if row_cells:
                            lines.append(" | ".join(row_cells))
                return "\n".join(lines)
            elif lower_name.endswith((".xlsx", ".xls")):
                import openpyxl
                wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
                lines = []
                for sheet in wb.worksheets:
                    for row in sheet.iter_rows(values_only=True):
                        vals = [str(v).strip() for v in row if v is not None and str(v).strip()]
                        if vals:
                            lines.append(" | ".join(vals))
                return "\n".join(lines)
            elif lower_name.endswith(".txt"):
                return file_bytes.decode("utf-8", errors="ignore")
        except Exception as err:
            logger.error(f"Error al extraer texto de {filename}: {err}")
        return ""

    def _mock_chat(
        self,
        history: List[Dict[str, Any]],
        message: str,
        initial_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Respuesta local estructurada de contingencia si no hay internet o claves."""
        inst = initial_data.get("institucion", "UPC")
        dir_name = initial_data.get("direccion", "tu área")
        user_name = initial_data.get("registrador", "Colega")

        if len(history) == 0:
            return {
                "text": (
                    f"¡Hola {user_name}! He revisado la información inicial para **{inst}** en la {dir_name}.\n\n"
                    f"Para avanzar con la estructuración de la iniciativa, ¿cuál es el problema u oportunidad de negocio concreto que buscas resolver?"
                ),
                "options": [
                    "Optimizar tiempos operativos",
                    "Automatizar reportería manual",
                    "Integrar sistemas existentes",
                    "Cumplimiento normativo institucional",
                ],
                "allow_multiple": False,
                "extractedFields": {},
            }

        return {
            "text": (
                f"Entendido. He incorporado tu aporte. Para dimensionar el impacto técnico en {inst}: "
                f"¿Qué sistemas actuales o plataformas intervendrían en la solución?"
            ),
            "options": [
                "Banner SIS",
                "Salesforce CRM",
                "Blackboard LMS",
                "Portal de Autoservicio / Pagos",
            ],
            "allow_multiple": True,
            "extractedFields": {},
        }

    def _mock_summarize(
        self,
        history: List[Dict[str, Any]],
        initial_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "titulo": f"Modernización y Automatización de Procesos para {initial_data.get('direccion', 'el área')}",
            "objetivo": f"Optimizar la eficiencia y reducir tiempos manuales en {initial_data.get('institucion', 'la institución')}.",
            "descripcion_de_la_necesidad": "Necesidad operativa estructurada mediante sesión asistida por Teo.",
            "institucion": initial_data.get("institucion", "UPC"),
            "vicepresidencia": initial_data.get("vicepresidencia", ""),
            "direccion": initial_data.get("direccion", ""),
            "fecha_tentativa": "31/12/2026",
            "impacto_esperado": "Alto",
            "tipo_solucion": "Mejora Evolutiva",
        }
