import json
import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database import AsyncSessionLocal, Base, engine
from app.domain.models import (
    VP, Direccion, Profile, ProfileRole, AppRole, AllowedUser, UserRoleWhitelist, Initiative,
    InitiativeField, WorkflowDefinition, WorkflowNodeRole, WorkflowTransition, WorkflowRoleAssignment,
    StageForm, StageConsent, DocumentTemplate,
    AIKnowledgeFolder, AITrainingConfig, AgentLog, EmailLog, SiteSetting
)

logger = logging.getLogger("iacs.seeder")

SAMPLE_INITIATIVES = [
    {
        "id": "INIT-SAMPLE-01",
        "status": "Borrador",
        "current_node_id": "borrador",
        "form_data": {
            "institucion": "UPC",
            "vicepresidencia": "Comercial",
            "direccion": "Dirección de Admisiones y Ventas",
            "registrador": "Administrador General",
            "bp_ti_asignado": "Carlos Mendoza",
            "lider_de_dominio_responsable": "Roberto Gómez",
            "titulo": "Automatización del proceso de captura de prospectos digitales",
            "_reached_summary": True,
        },
        "summary": {
            "id_corta": "COM-001",
            "titulo": "Automatización del proceso de captura de prospectos digitales",
            "objetivo": "Optimizar el embudo de admisión e integrar leads de Meta/Google al CRM Salesforce.",
            "descripcionProblema": "Demoras de hasta 48 horas en la distribución manual de prospectos a los asesores.",
            "complejidad": "Media",
            "riesgo": "Bajo",
        },
        "days_ago": 5,
    },
    {
        "id": "INIT-SAMPLE-02",
        "status": "Borrador",
        "current_node_id": "borrador",
        "form_data": {
            "institucion": "UPN",
            "vicepresidencia": "Comercial",
            "direccion": "Dirección de Marketing Corporativo",
            "registrador": "Administrador General",
            "bp_ti_asignado": "Carlos Mendoza",
            "lider_de_dominio_responsable": "Roberto Gómez",
            "titulo": "Portal de eventos y charlas vocacionales online",
            "_reached_summary": True,
        },
        "summary": {
            "id_corta": "COM-002",
            "titulo": "Portal de eventos y charlas vocacionales online",
            "objetivo": "Centralizar el registro a webinars y talleres vivenciales para postulantes.",
            "complejidad": "Baja",
            "riesgo": "Bajo",
        },
        "days_ago": 4,
    },
    {
        "id": "INIT-SAMPLE-03",
        "status": "Borrador",
        "current_node_id": "borrador",
        "form_data": {
            "institucion": "Cibertec",
            "vicepresidencia": "Comercial",
            "direccion": "Dirección de Retención y Fidelización",
            "registrador": "Administrador General",
            "bp_ti_asignado": "Ana Lucía Ramos",
            "lider_de_dominio_responsable": "Jorge Velásquez",
            "titulo": "Sistema de alertas tempranas de deserción de postulantes",
            "_reached_summary": True,
        },
        "summary": {
            "id_corta": "COM-003",
            "titulo": "Sistema de alertas tempranas de deserción de postulantes",
            "objetivo": "Modelo predictivo para identificar candidatos con riesgo de no completar su matrícula.",
            "complejidad": "Alta",
            "riesgo": "Medio",
        },
        "days_ago": 3,
    },
    {
        "id": "INIT-SAMPLE-04",
        "status": "Iniciativa planificada",
        "current_node_id": "planificacion",
        "form_data": {
            "institucion": "UPC",
            "vicepresidencia": "Comercial",
            "direccion": "Dirección de Admisiones y Ventas",
            "registrador": "Administrador General",
            "bp_ti_asignado": "Carlos Mendoza",
            "lider_de_dominio_responsable": "Roberto Gómez",
            "titulo": "Integración de pasarela de pagos QR para matrículas y reservas",
            "_reached_summary": True,
        },
        "summary": {
            "id_corta": "COM-004",
            "titulo": "Integración de pasarela de pagos QR para matrículas y reservas",
            "objetivo": "Permitir pagos instantáneos con Yape y Plin en el portal de admisión.",
            "complejidad": "Media",
            "riesgo": "Bajo",
        },
        "days_ago": 10,
    },
    {
        "id": "INIT-SAMPLE-05",
        "status": "Iniciativa planificada",
        "current_node_id": "planificacion",
        "form_data": {
            "institucion": "UPN",
            "vicepresidencia": "Comercial",
            "direccion": "Dirección de Marketing Corporativo",
            "registrador": "Administrador General",
            "bp_ti_asignado": "Ana Lucía Ramos",
            "lider_de_dominio_responsable": "Roberto Gómez",
            "titulo": "Módulo de autogestión de convalidaciones en línea",
            "_reached_summary": True,
        },
        "summary": {
            "id_corta": "COM-005",
            "titulo": "Módulo de autogestión de convalidaciones en línea",
            "objetivo": "Revisión automática de mallas curriculares y sílabos para traslados externos.",
            "complejidad": "Alta",
            "riesgo": "Medio",
        },
        "days_ago": 9,
    },
    {
        "id": "INIT-SAMPLE-06",
        "status": "Iniciativa planificada",
        "current_node_id": "planificacion",
        "form_data": {
            "institucion": "Laureate Perú",
            "vicepresidencia": "Comercial",
            "direccion": "Dirección de Retención y Fidelización",
            "registrador": "Administrador General",
            "bp_ti_asignado": "Carlos Mendoza",
            "lider_de_dominio_responsable": "Jorge Velásquez",
            "titulo": "Tablero analítico corporativo de conversión de admisiones",
            "_reached_summary": True,
        },
        "summary": {
            "id_corta": "COM-006",
            "titulo": "Tablero analítico corporativo de conversión de admisiones",
            "objetivo": "Visualización en tiempo real de metas comerciales por sede y programa académico.",
            "complejidad": "Media",
            "riesgo": "Bajo",
        },
        "days_ago": 8,
    },
    {
        "id": "INIT-SAMPLE-07",
        "status": "En evaluación del BP TI",
        "current_node_id": "eval_bp",
        "form_data": {
            "institucion": "UPC",
            "vicepresidencia": "Comercial",
            "direccion": "Dirección de Admisiones y Ventas",
            "registrador": "Administrador General",
            "bp_ti_asignado": "Carlos Mendoza",
            "lider_de_dominio_responsable": "Roberto Gómez",
            "titulo": "Chatbot omnicanal de WhatsApp para atención 24/7 de postulantes",
            "_reached_summary": True,
        },
        "summary": {
            "id_corta": "COM-007",
            "titulo": "Chatbot omnicanal de WhatsApp para atención 24/7 de postulantes",
            "objetivo": "Desplegar asistente conversacional integrado con IA generativa de Vertex AI.",
            "complejidad": "Alta",
            "riesgo": "Medio",
        },
        "days_ago": 2,
    },
    {
        "id": "INIT-SAMPLE-08",
        "status": "En evaluación del BP TI",
        "current_node_id": "eval_bp",
        "form_data": {
            "institucion": "Cibertec",
            "vicepresidencia": "Comercial",
            "direccion": "Dirección de Marketing Corporativo",
            "registrador": "Administrador General",
            "bp_ti_asignado": "Ana Lucía Ramos",
            "lider_de_dominio_responsable": "Jorge Velásquez",
            "titulo": "Plataforma B2B para convenios educativos corporativos",
            "_reached_summary": True,
        },
        "summary": {
            "id_corta": "COM-008",
            "titulo": "Plataforma B2B para convenios educativos corporativos",
            "objetivo": "Portal para que empresas asociadas gestionen becas y capacitaciones para colaboradores.",
            "complejidad": "Media",
            "riesgo": "Bajo",
        },
        "days_ago": 2,
    },
    {
        "id": "INIT-SAMPLE-09",
        "status": "En evaluación del BP TI",
        "current_node_id": "eval_bp",
        "form_data": {
            "institucion": "UPN",
            "vicepresidencia": "Comercial",
            "direccion": "Dirección de Retención y Fidelización",
            "registrador": "Administrador General",
            "bp_ti_asignado": "Carlos Mendoza",
            "lider_de_dominio_responsable": "Roberto Gómez",
            "titulo": "App móvil para seguimiento de postulaciones y citas de admisión",
            "_reached_summary": True,
        },
        "summary": {
            "id_corta": "COM-009",
            "titulo": "App móvil para seguimiento de postulaciones y citas de admisión",
            "objetivo": "Notificaciones push y tracking en tiempo real del estado de admisión del estudiante.",
            "complejidad": "Alta",
            "riesgo": "Alto",
        },
        "days_ago": 1,
    },
    {
        "id": "INIT-SAMPLE-10",
        "status": "Pendiente de aprobación BO",
        "current_node_id": "aprob_bo",
        "form_data": {
            "institucion": "UPC",
            "vicepresidencia": "Comercial",
            "direccion": "Dirección de Admisiones y Ventas",
            "registrador": "Administrador General",
            "bp_ti_asignado": "Carlos Mendoza",
            "lider_de_dominio_responsable": "Roberto Gómez",
            "titulo": "Digitalización biométrica de validación de identidad en evaluaciones",
            "_reached_summary": True,
        },
        "summary": {
            "id_corta": "COM-010",
            "titulo": "Digitalización biométrica de validación de identidad en evaluaciones",
            "objetivo": "Validación facial y cotejo automático con RENIEC para exámenes de admisión virtuales.",
            "complejidad": "Alta",
            "riesgo": "Alto",
        },
        "hours_ago": 6,
    },
    {
        "id": "INIT-SAMPLE-11",
        "status": "Pendiente de estimación sin Presupuesto",
        "current_node_id": "est_sin_presupuesto",
        "form_data": {
            "institucion": "UPC",
            "vicepresidencia": "Académica",
            "direccion": "Dirección de Servicios Académicos",
            "registrador": "Administrador General",
            "bp_ti_asignado": "Ana Lucía Ramos",
            "lider_de_dominio_responsable": "Jorge Velásquez",
            "titulo": "Sistema de asignación automática de horarios y carga docente",
            "_reached_summary": True,
        },
        "summary": {
            "id_corta": "ACA-001",
            "titulo": "Sistema de asignación automática de horarios y carga docente",
            "objetivo": "Algoritmo de optimización de aulas y cruce de disponibilidad de profesores a tiempo parcial.",
            "complejidad": "Alta",
            "riesgo": "Medio",
        },
        "hours_ago": 12,
    },
]

ORGANIZATION_STRUCTURE = [
    {
        "name": "Comercial",
        "bp_name": "Carlos Mendoza",
        "direcciones": [
            "Dirección de Admisiones y Ventas",
            "Dirección de Marketing Corporativo",
            "Dirección de Retención y Fidelización"
        ]
    },
    {
        "name": "Académica",
        "bp_name": "Ana Lucía Ramos",
        "direcciones": [
            "Dirección de Servicios Académicos",
            "Dirección de Gestión Curricular y Docente",
            "Dirección de Calidad y Acreditación"
        ]
    },
    {
        "name": "Operaciones",
        "bp_name": "Jorge Valdivia",
        "direcciones": [
            "Dirección de Infraestructura y Mantenimiento",
            "Dirección de Logística y Adquisiciones",
            "Dirección de Seguridad y Servicios Generales"
        ]
    },
    {
        "name": "Finanzas",
        "bp_name": "Roberto Chang",
        "direcciones": [
            "Dirección de Contabilidad y Tesorería",
            "Dirección de Planeamiento Financiero y Control de Gestión",
            "Dirección de Cobranzas y Facturación"
        ]
    },
    {
        "name": "Personas & Talento",
        "bp_name": "María Elena Gómez",
        "direcciones": [
            "Dirección de Selección y Desarrollo Organizacional",
            "Dirección de Compensaciones y Bienestar",
            "Dirección de Relaciones Laborales"
        ]
    },
    {
        "name": "Transformación Digital",
        "bp_name": "Fernando Ruiz",
        "direcciones": [
            "Dirección de Arquitectura y Soluciones TI",
            "Dirección de Ciberseguridad y Riesgos Tecnológicos",
            "Dirección de Analítica Avanzada e IA Corporativa",
            "Dirección de Gobierno de Datos"
        ]
    }
]

AGENT_TEMPLATES = [
    {"role": "PO Men", "title": "Levantamiento de especificación funcional", "status": "completed", "progress": 100},
    {"role": "Seguridad TI", "title": "Evaluación de políticas de privacidad y RLS", "status": "completed", "progress": 100},
    {"role": "Arqui", "title": "Diseño de interfaces Nuxt 4 y componentes modulares", "status": "completed", "progress": 100},
    {"role": "Programador", "title": "Construcción de API REST en FastAPI y esquemas Pydantic", "status": "completed", "progress": 100},
    {"role": "QA", "title": "Generación de pruebas automatizadas con pytest y vitest", "status": "completed", "progress": 100},
    {"role": "Documentador", "title": "Elaboración de manuales técnicos y arquitectura C4", "status": "completed", "progress": 100},
    {"role": "Líder técnico", "title": "Orquestación del Golden Path y pipelines CI/CD", "status": "completed", "progress": 100},
    {"role": "Auditor IA", "title": "Auditoría de cuota de tokens Vertex AI (Gemini 2.5 Flash)", "status": "completed", "progress": 100}
]

AI_FOLDERS_SEED = [
    {"name": "Políticas Corporativas", "level": 1, "sort_order": 1, "children": [
        {"name": "Seguridad de la Información", "level": 2, "sort_order": 1, "children": [
            {"name": "Protección de Datos Personales (LPDP)", "level": 3, "sort_order": 1}
        ]},
        {"name": "Gobierno de TI", "level": 2, "sort_order": 2, "children": [
            {"name": "Gestión de Demanda y Proyectos", "level": 3, "sort_order": 1}
        ]}
    ]},
    {"name": "Arquitectura y Estándares", "level": 1, "sort_order": 2, "children": [
        {"name": "Integraciones y APIs", "level": 2, "sort_order": 1, "children": [
            {"name": "Patrones REST y Mensajería", "level": 3, "sort_order": 1}
        ]},
        {"name": "Sistemas Core Institucionales", "level": 2, "sort_order": 2, "children": [
            {"name": "Banner, Blackboard y Salesforce", "level": 3, "sort_order": 1}
        ]}
    ]},
    {"name": "Casos de Negocio y Plantillas", "level": 1, "sort_order": 3, "children": [
        {"name": "Modelos de Justificación Financiera", "level": 2, "sort_order": 1, "children": [
            {"name": "Cálculo de ROI y Ahorro HH", "level": 3, "sort_order": 1}
        ]}
    ]}
]

AI_TRAINING_CONFIG_SEED = [
    {
        "layer": "identity",
        "title": "Identidad Principal de Teo",
        "content": (
            "Eres Teo, Analista Senior de Negocios y Arquitectura de TI en IACS. "
            "Tu propósito es guiar, estructurar y blindar las iniciativas tecnológicas de los colaboradores. "
            "Actúas con la metodología de indagación activa ('Grill-Me'): eres un asesor constructivo pero "
            "incisivo que pone a prueba la solidez del requerimiento. No aceptas respuestas vagas ni supuestos ciegos, "
            "sino que ayudas al usuario a destapar dependencias técnicas, evaluar si necesita presupuesto (Capex/Opex), "
            "verificar impacto en sistemas existentes y anticipar riesgos antes de enviar la iniciativa a aprobación. "
            "Tu tono es ejecutivo, profesional, empático y orientado a la excelencia arquitectónica."
        ),
        "sort_order": 1,
    },
    {
        "layer": "settings",
        "title": "ai_name",
        "content": "Teo",
        "sort_order": 1,
    },
    {
        "layer": "settings",
        "title": "ai_avatar",
        "content": "https://api.dicebear.com/7.x/bottts/svg?seed=TeoIACS",
        "sort_order": 2,
    },
    {
        "layer": "context",
        "title": "Lineamientos de Arquitectura Corporativa Laureate Perú",
        "content": (
            "- Todos los nuevos desarrollos deben integrarse vía REST API con autenticación OAuth2/OIDC.\n"
            "- Sistemas Core disponibles: Banner (Alumnos y Docentes), Salesforce (Admisiones y Marketing), "
            "Blackboard Ultra (LMS), SAP S/4HANA (Finanzas y Compras).\n"
            "- Toda solución en la nube debe desplegarse preferentemente en Google Cloud Platform (Cloud Run, Cloud SQL, Vertex AI)."
        ),
        "sort_order": 1,
    },
    {
        "layer": "guardrails",
        "title": "Restricción de Seguridad y Confidencialidad",
        "content": "Nunca solicitar ni almacenar contraseñas, tokens de producción ni números completos de tarjetas de crédito en el formulario o chat.",
        "sort_order": 1,
    },
    {
        "layer": "guardrails",
        "title": "Cálculo Estricto de Fechas",
        "content": "Exigir siempre plazos con fechas tentativas en formato DD/MM/AAAA sin permitir fechas pasadas ni plazos inferiores a 30 días para proyectos con desarrollos a medida.",
        "sort_order": 2,
    },
    {
        "layer": "guardrails",
        "title": "Obligatoriedad de Justificación",
        "content": "No marcar '[INFORMACION_COMPLETA]' si el usuario no ha especificado un beneficio cuantificable (horas de ahorro o impacto en tasa de retención/conversión).",
        "sort_order": 3,
    },
    {
        "layer": "examples",
        "title": "Necesidad de automatizar admisiones",
        "content": (
            "Entiendo perfectamente el contexto y la necesidad de optimizar este proceso. Para formalizarlo ante el comité: "
            "¿Se integrará directamente con el CRM Salesforce o requerirá una base de datos intermedia?"
        ),
        "sort_order": 1,
    }
]


async def seed_database_if_needed():
    """Siembra inicial y sincronización completa de datos para garantizar paridad 1:1."""
    async with engine.begin() as conn:
        # Asegurar creación de todas las tablas definidas en modelos
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        try:
            # 1. Site Settings
            setting_res = await db.execute(select(SiteSetting).where(SiteSetting.id == 1))
            if not setting_res.scalar_one_or_none():
                db.add(SiteSetting(id=1, maintenance_mode=False, system_notice="IACS Enterprise operando normalmente en GCP."))
                await db.commit()

            # 2. Roles (10 roles exactos: 5 de sistema, 5 personalizados)
            ROLES_SEED = [
                ("admin", "Administrador General", "Control total de la plataforma, configuración de formularios, estructura organizacional y métricas globales.", "red", True),
                ("bp_ti", "Business Partner TI", "Aprobador (Business Partner). Edita iniciativas y sugerencias, decide aprobar u observar, gestión de Track Changes.", "indigo", True),
                ("entrenador_ia", "Entrenador IA", "Acceso y gestión exclusiva de la Base de Conocimiento y Entrenamiento del asistente Teo (crear/editar fichas, carpetas y carga de documentos).", "violet", True),
                ("invitado", "Invitado", "Acceso de solo lectura. Métricas de visualización y consulta de iniciativas finalizadas de su VP.", "slate", True),
                ("registrador", "Key user", "Crea y formula iniciativas guiado por la IA Teo. Responde observaciones y acepta/rechaza propuestas de cambio.", "emerald", True),
                ("business_owner", "Business Owner", "Líder de negocio responsable de la priorización, viabilidad y retorno de inversión de la iniciativa.", "violet", False),
                ("especialista_ti", "Especialista TI", "Especialista técnico encargado de la factibilidad arquitectónica y estimación técnica.", "violet", False),
                ("gestor_de_la_demanda", "Gestor de la demanda", "Responsable del registro, priorización y seguimiento de iniciativas dentro del portafolio tecnológico.", "violet", False),
                ("lider_de_dominio", "Líder de dominio", "Líder de dominio técnico que valida la coherencia con los lineamientos de arquitectura y estándares.", "violet", False),
                ("vicepresidente_del_negocio", "Vicepresidente del Negocio", "Aprobador final del negocio con facultades de patrocinio y asignación de presupuesto.", "violet", False),
            ]
            for code, name, desc, col, is_sys in ROLES_SEED:
                r_res = await db.execute(select(AppRole).where(AppRole.code == code))
                existing_role = r_res.scalar_one_or_none()
                if not existing_role:
                    db.add(AppRole(code=code, name=name, description=desc, color=col, is_system=is_sys, is_active=True))
                else:
                    existing_role.name = name
                    existing_role.description = desc
                    existing_role.color = col
                    existing_role.is_system = is_sys
                    existing_role.is_active = True
            await db.commit()

            # 3. Organizaciones (VPs y Direcciones)
            for org in ORGANIZATION_STRUCTURE:
                vp_res = await db.execute(select(VP).where(VP.name == org["name"]))
                vp = vp_res.scalar_one_or_none()
                if not vp:
                    vp = VP(name=org["name"], bp_name=org["bp_name"])
                    db.add(vp)
                    await db.commit()
                    await db.refresh(vp)
                else:
                    if not vp.bp_name and org["bp_name"]:
                        vp.bp_name = org["bp_name"]
                        await db.commit()

                for dir_name in org["direcciones"]:
                    dir_res = await db.execute(
                        select(Direccion).where(Direccion.name == dir_name, Direccion.vp_id == vp.id)
                    )
                    if not dir_res.scalar_one_or_none():
                        db.add(Direccion(name=dir_name, vp_id=vp.id))
            await db.commit()

            # 4. Usuarios de la Lista Blanca (10 usuarios idénticos a Imagen 1)
            USERS_SEED = [
                {
                    "email": "esther@captcha.com",
                    "name": "IA - Esther registradora",
                    "role": "registrador",
                    "vp_name": "Operaciones",
                    "dir_names": ["Dirección de Logística y Adquisiciones"],
                    "is_transversal": False,
                    "is_active_profile": True,
                },
                {
                    "email": "liz@linares.com",
                    "name": "Liz Linares",
                    "role": "registrador",
                    "vp_name": "Comercial",
                    "dir_names": ["Dirección de Admisiones y Ventas"],
                    "is_transversal": False,
                    "is_active_profile": False,
                },
                {
                    "email": "coba@david.com",
                    "name": "David Coba",
                    "role": "bp_ti",
                    "vp_name": "Académica",
                    "dir_names": "ALL",
                    "is_transversal": False,
                    "is_active_profile": True,
                },
                {
                    "email": "lider@iacs.pe",
                    "name": "Líder de Dominio Técnico",
                    "role": "lider_de_dominio",
                    "vp_name": "Transformación Digital",
                    "dir_names": ["Dirección de Arquitectura y Soluciones TI"],
                    "is_transversal": False,
                    "is_active_profile": True,
                },
                {
                    "email": "admin@iacs.empresa.com",
                    "name": "Administrador General",
                    "role": "admin",
                    "vp_name": None,
                    "dir_names": [],
                    "is_transversal": True,
                    "is_active_profile": True,
                },
                {
                    "email": "cmendoza@iacs.empresa.com",
                    "name": "Carlos Mendoza",
                    "role": "bp_ti",
                    "vp_name": "Comercial",
                    "dir_names": "ALL",
                    "is_transversal": False,
                    "is_active_profile": True,
                },
                {
                    "email": "aramos@iacs.empresa.com",
                    "name": "Ana Lucía Ramos",
                    "role": "bp_ti",
                    "vp_name": "Finanzas",
                    "dir_names": "ALL",
                    "is_transversal": False,
                    "is_active_profile": True,
                },
                {
                    "email": "rgomez@iacs.empresa.com",
                    "name": "Roberto Gómez",
                    "role": "lider_de_dominio",
                    "vp_name": "Transformación Digital",
                    "dir_names": ["Dirección de Arquitectura y Soluciones TI"],
                    "is_transversal": False,
                    "is_active_profile": True,
                },
                {
                    "email": "mgomez@iacs.empresa.com",
                    "name": "María Elena Gómez",
                    "role": "vicepresidente_del_negocio",
                    "vp_name": "Personas & Talento",
                    "dir_names": "ALL",
                    "is_transversal": False,
                    "is_active_profile": True,
                },
                {
                    "email": "entrenador@iacs.empresa.com",
                    "name": "Entrenador IA Bot",
                    "role": "entrenador_ia",
                    "vp_name": None,
                    "dir_names": [],
                    "is_transversal": True,
                    "is_active_profile": True,
                },
            ]

            for u_seed in USERS_SEED:
                u_email = u_seed["email"].lower().strip()
                allowed_res = await db.execute(select(AllowedUser).where(AllowedUser.email == u_email))
                allowed_u = allowed_res.scalar_one_or_none()
                if not allowed_u:
                    allowed_u = AllowedUser(email=u_email, name=u_seed["name"])
                    db.add(allowed_u)
                    await db.commit()
                    await db.refresh(allowed_u)
                else:
                    allowed_u.name = u_seed["name"]
                    await db.commit()

                # Obtener VP y direcciones
                vp_id = None
                dir_ids = []
                if u_seed["vp_name"]:
                    v_res = await db.execute(select(VP).where(VP.name == u_seed["vp_name"]))
                    v_obj = v_res.scalar_one_or_none()
                    if v_obj:
                        vp_id = v_obj.id
                        if u_seed["dir_names"] == "ALL":
                            d_res = await db.execute(select(Direccion).where(Direccion.vp_id == v_obj.id))
                            dir_ids = [d.id for d in d_res.scalars().all()]
                        elif isinstance(u_seed["dir_names"], list):
                            d_res = await db.execute(
                                select(Direccion).where(Direccion.vp_id == v_obj.id, Direccion.name.in_(u_seed["dir_names"]))
                            )
                            dir_ids = [d.id for d in d_res.scalars().all()]

                # Roles en UserRoleWhitelist
                w_res = await db.execute(
                    select(UserRoleWhitelist).where(UserRoleWhitelist.allowed_user_id == allowed_u.id)
                )
                if not w_res.scalars().all():
                    db.add(UserRoleWhitelist(
                        allowed_user_id=allowed_u.id,
                        role=u_seed["role"],
                        vp_id=vp_id,
                        direcciones_ids=dir_ids,
                        is_transversal=u_seed["is_transversal"]
                    ))
                    await db.commit()

                # Sincronización con Profile (para activos vs pendientes)
                prof_res = await db.execute(select(Profile).where(Profile.email == u_email))
                prof_obj = prof_res.scalar_one_or_none()
                if u_seed["is_active_profile"]:
                    if not prof_obj:
                        prof_obj = Profile(
                            email=u_email,
                            name=u_seed["name"],
                            vp_id=vp_id,
                            direccion_id=dir_ids[0] if dir_ids else None,
                            is_active=True
                        )
                        db.add(prof_obj)
                        await db.commit()
                        await db.refresh(prof_obj)
                    
                    # ProfileRole
                    pr_res = await db.execute(select(ProfileRole).where(ProfileRole.profile_id == prof_obj.id))
                    if not pr_res.scalars().all():
                        db.add(ProfileRole(
                            profile_id=prof_obj.id,
                            role=u_seed["role"],
                            vp_id=vp_id,
                            direcciones_ids=dir_ids,
                            is_transversal=u_seed["is_transversal"]
                        ))
                        await db.commit()
                else:
                    if prof_obj:
                        await db.delete(prof_obj)
                        await db.commit()


            # 5. Iniciativas de Muestra (11 iniciativas idénticas a Image 1)
            init_count_res = await db.execute(select(func.count(Initiative.id)))
            current_count = init_count_res.scalar_one() or 0

            # Si hay menos de 11 iniciativas, sembramos las 11
            for sample in SAMPLE_INITIATIVES:
                s_res = await db.execute(select(Initiative).where(Initiative.id == sample["id"]))
                existing = s_res.scalar_one_or_none()
                now = datetime.now(timezone.utc)
                if "days_ago" in sample:
                    created_at = now - timedelta(days=sample["days_ago"])
                elif "hours_ago" in sample:
                    created_at = now - timedelta(hours=sample["hours_ago"])
                else:
                    created_at = now

                if not existing:
                    db.add(Initiative(
                        id=sample["id"],
                        status=sample["status"],
                        current_node_id=sample["current_node_id"],
                        form_data=sample["form_data"],
                        summary=sample["summary"],
                        chat_history=[],
                        created_at=created_at,
                        updated_at=created_at,
                    ))
                else:
                    # Actualizar status y datos si cambió
                    existing.status = sample["status"]
                    existing.form_data = sample["form_data"]
                    existing.summary = sample["summary"]
            await db.commit()

            # 6. Carpetas de IA y Configuración de Entrenamiento
            folder_count = await db.execute(select(func.count(AIKnowledgeFolder.id)))
            if (folder_count.scalar_one() or 0) < 10:
                for f1_data in AI_FOLDERS_SEED:
                    f1_res = await db.execute(select(AIKnowledgeFolder).where(AIKnowledgeFolder.name == f1_data["name"]))
                    f1 = f1_res.scalar_one_or_none()
                    if not f1:
                        f1 = AIKnowledgeFolder(name=f1_data["name"], level=1, sort_order=f1_data["sort_order"])
                        db.add(f1)
                        await db.commit()
                        await db.refresh(f1)

                    for f2_data in f1_data.get("children", []):
                        f2_res = await db.execute(select(AIKnowledgeFolder).where(AIKnowledgeFolder.name == f2_data["name"], AIKnowledgeFolder.parent_id == f1.id))
                        f2 = f2_res.scalar_one_or_none()
                        if not f2:
                            f2 = AIKnowledgeFolder(name=f2_data["name"], level=2, parent_id=f1.id, sort_order=f2_data["sort_order"])
                            db.add(f2)
                            await db.commit()
                            await db.refresh(f2)

                        for f3_data in f2_data.get("children", []):
                            f3_res = await db.execute(select(AIKnowledgeFolder).where(AIKnowledgeFolder.name == f3_data["name"], AIKnowledgeFolder.parent_id == f2.id))
                            f3 = f3_res.scalar_one_or_none()
                            if not f3:
                                f3 = AIKnowledgeFolder(name=f3_data["name"], level=3, parent_id=f2.id, sort_order=f3_data["sort_order"])
                                db.add(f3)
                                await db.commit()

            for cfg in AI_TRAINING_CONFIG_SEED:
                c_res = await db.execute(select(AITrainingConfig).where(AITrainingConfig.title == cfg["title"]))
                if not c_res.scalar_one_or_none():
                    db.add(AITrainingConfig(
                        layer=cfg["layer"],
                        title=cfg["title"],
                        content=cfg["content"],
                        sort_order=cfg.get("sort_order", 0),
                        is_active=True,
                        source="manual"
                    ))
            await db.commit()

            # 7. Agent Logs
            agent_count = await db.execute(select(func.count(AgentLog.id)))
            if (agent_count.scalar_one() or 0) == 0:
                for a in AGENT_TEMPLATES:
                    db.add(AgentLog(
                        agent_name=a["role"],
                        action=a["title"],
                        agent_role=a["role"],
                        task_title=a["title"],
                        status=a["status"],
                        progress=a["progress"],
                    ))
                await db.commit()

            # 8. Email Logs
            email_count = await db.execute(select(func.count(EmailLog.id)))
            if (email_count.scalar_one() or 0) == 0:
                db.add(EmailLog(
                    initiative_id="INIT-SAMPLE-07",
                    recipient="carlos.mendoza@iacs.empresa.com",
                    subject="[IACS] Iniciativa lista para Dictamen de BP TI: COM-007",
                    body="Se ha completado el levantamiento de la iniciativa COM-007. Por favor ingresar para emitir dictamen técnico.",
                    status="sent"
                ))
                await db.commit()

            # 9. Formularios de Etapa (9 formularios canónicos según Image 2)
            STAGE_FORMS_SEED = [
                {
                    "code": "form_registro_iniciativa",
                    "name": "Formulario para captar iniciativa",
                    "description": "Formulario oficial de captura de necesidad, contexto organizacional [Institución, VP, Dirección], justificación detallada y beneficios esperados.",
                    "fields": [
                        {"id": "f_inst", "key": "institucion", "label": "¿Qué institución tiene la necesidad?", "type": "select", "required": True, "options": ["UPC", "UPN", "Cibertec", "Laureate Perú"], "ask_in_initial_form": True},
                        {"id": "f_vp", "key": "vicepresidencia", "label": "Vicepresidencia", "type": "select", "required": True, "ask_in_initial_form": True},
                        {"id": "f_dir", "key": "direccion", "label": "Dirección", "type": "select", "required": True, "ask_in_initial_form": True},
                        {"id": "f_tit", "key": "titulo", "label": "Título de la iniciativa", "type": "text", "required": True, "placeholder": "Verbo infinitivo + objeto + impacto", "ask_in_initial_form": False},
                        {"id": "f_pil", "key": "pilar_estrategico", "label": "Pilar Estratégico", "type": "select", "required": True, "options": ["Crecimiento y Admisiones", "Excelencia Académica", "Eficiencia Operativa", "Transformación Digital"], "ask_in_initial_form": False},
                        {"id": "f_obj", "key": "objetivo_estrategico", "label": "Objetivo Estratégico", "type": "textarea", "required": True, "ask_in_initial_form": False},
                        {"id": "f_nec", "key": "descripcion_necesidad", "label": "Descripción de la Necesidad", "type": "textarea", "required": True, "ask_in_initial_form": False},
                        {"id": "f_jus", "key": "justificacion", "label": "Justificación del Negocio", "type": "textarea", "required": True, "ask_in_initial_form": False},
                        {"id": "f_imp", "key": "impacto_esperado", "label": "Impacto Esperado", "type": "select", "required": True, "options": ["Alto", "Medio", "Bajo"], "ask_in_initial_form": False},
                        {"id": "f_sol", "key": "tipo_solucion", "label": "Tipo de Solución Propuesta", "type": "select", "required": True, "options": ["Nuevo Sistema", "Mejora Evolutiva", "Integración / API", "Automatización RPA", "Reporte / BI"], "ask_in_initial_form": False},
                        {"id": "f_sis", "key": "sistemas_afectados", "label": "Sistemas Core Afectados", "type": "multiselect", "required": False, "options": ["Banner", "Blackboard", "Salesforce", "SAP S/4HANA", "Portal Alumno"], "ask_in_initial_form": False},
                        {"id": "f_usr", "key": "usuarios_beneficiados", "label": "Usuarios Estimados Beneficiados", "type": "number", "required": False, "ask_in_initial_form": False},
                        {"id": "f_fec", "key": "fecha_tentativa", "label": "Fecha Tentativa de Salida", "type": "date", "required": True, "ask_in_initial_form": False},
                        {"id": "f_pre", "key": "requiere_presupuesto", "label": "¿Requiere Presupuesto Externo?", "type": "select", "required": True, "options": ["Sí", "No"], "ask_in_initial_form": False},
                        {"id": "f_mon", "key": "monto_estimado_usd", "label": "Monto Estimado USD", "type": "number", "required": False, "ask_in_initial_form": False},
                        {"id": "f_adj", "key": "adjuntos_sustento", "label": "Archivos y Documentos de Sustento", "type": "file", "required": False, "ask_in_initial_form": True},
                        {"id": "f_obs", "key": "observaciones_adicionales", "label": "Observaciones Adicionales", "type": "textarea", "required": False, "ask_in_initial_form": False},
                        {"id": "f_bp", "key": "bp_ti_sugerido", "label": "Business Partner de TI Asignado", "type": "role_user", "required": True, "target_role": "bp_ti", "ask_in_initial_form": False}
                    ]
                },
                {
                    "code": "form_bp_viabilidad",
                    "name": "Validar iniciativa",
                    "description": "Formulario para que el Business Partner de TI complete la viabilidad técnica y designe al Business Owner.",
                    "fields": [
                        {"id": "f_bp_sel", "key": "bp_ti_responsable", "label": "Selecciona tu BP TI", "type": "role_user", "required": True, "target_role": "bp_ti"},
                        {"id": "f_bp_sol", "key": "tipo_solucion_propuesta", "label": "Tipo de Solución Propuesta", "type": "select", "required": True, "options": ["Desarrollo Interno", "Compra SaaS", "Consultoría Externa", "Ajuste de Configuración"]},
                        {"id": "f_bp_obs", "key": "observaciones_bp", "label": "Observaciones y Criterios del BP", "type": "textarea", "required": True}
                    ]
                },
                {
                    "code": "form_bo_patrocinio",
                    "name": "Aprobar iniciativa",
                    "description": "Formulario para que el Business Owner sustente los impactos y justificación del área.",
                    "fields": [
                        {"id": "f_bo_kpi", "key": "kpi_negocio", "label": "KPI o Meta de Negocio Impactada", "type": "text", "required": True},
                        {"id": "f_bo_urg", "key": "nivel_urgencia", "label": "Nivel de Urgencia del Área", "type": "select", "required": True, "options": ["Crítica (Mandato Regulatorio)", "Alta (Impacto Directo en Ingresos)", "Media (Eficiencia Interna)", "Baja (Mejora Cosmética)"]},
                        {"id": "f_bo_sus", "key": "sustento_patrocinio", "label": "Sustento del Patrocinio", "type": "textarea", "required": True}
                    ]
                },
                {
                    "code": "prioridadiniciativa",
                    "name": "Aprobación Estratégica VP",
                    "description": "Dictamen de visto bueno del Vicepresidente para canalizar la iniciativa a demanda.",
                    "fields": [
                        {"id": "f_vp_prio", "key": "prioridad_estrategica", "label": "Prioridad Estratégica Corporativa", "type": "select", "required": True, "options": ["P1 - Estratégica Inmediata", "P2 - Plan Anual", "P3 - Oportunidad"]},
                        {"id": "f_vp_com", "key": "comentarios_vp", "label": "Comentarios y Directrices del VP", "type": "textarea", "required": False}
                    ]
                },
                {
                    "code": "form_dominio_dictamen",
                    "name": "Asignación de Líder de Dominio",
                    "description": "El Gestor de la Demanda designa formalmente al líder técnico responsable de la estimación.",
                    "fields": [
                        {"id": "f_ld_asig", "key": "lider_dominio_asignado", "label": "Líder de Dominio TI Asignado", "type": "role_user", "required": True, "target_role": "lider_de_dominio"},
                        {"id": "f_ld_dom", "key": "dominio_tecnologico", "label": "Dominio Tecnológico Principal", "type": "select", "required": True, "options": ["Sistemas Académicos", "Sistemas Comerciales", "Finanzas y ERP", "Infraestructura & Cloud", "Data & Analytics"]}
                    ]
                },
                {
                    "code": "form_dominio_compromiso_ventana",
                    "name": "Compromiso de Ventana de Estimación",
                    "description": "Líder de Dominio registra la ventana de tiempo en la que realizará el análisis técnico.",
                    "fields": [
                        {"id": "f_v_ini", "key": "fecha_inicio_ventana", "label": "Fecha de Inicio de Estimación", "type": "date", "required": True},
                        {"id": "f_v_fin", "key": "fecha_fin_ventana", "label": "Fecha Límite de Estimación", "type": "date", "required": True}
                    ]
                },
                {
                    "code": "form_dominio_est_con_presupuesto",
                    "name": "Estimación Técnica con Presupuesto",
                    "description": "Líder de Dominio detalla el presupuesto en USD y el esfuerzo técnico en horas.",
                    "fields": [
                        {"id": "f_ec_pre", "key": "presupuesto_usd", "label": "Presupuesto Requerido USD", "type": "number", "required": True},
                        {"id": "f_ec_hrs", "key": "horas_estimadas", "label": "Horas Técnicas Estimadas (HH)", "type": "number", "required": True},
                        {"id": "f_ec_prv", "key": "proveedor_sugerido", "label": "Proveedor o Fábrica Sugerida", "type": "text", "required": False},
                        {"id": "f_ec_des", "key": "desglose_tecnico", "label": "Desglose Técnico y Arquitectura", "type": "textarea", "required": True}
                    ]
                },
                {
                    "code": "form_dominio_est_sin_presupuesto",
                    "name": "Estimación Técnica Interna",
                    "description": "Líder de Dominio detalla el esfuerzo con equipo interno sin requerir Capex.",
                    "fields": [
                        {"id": "f_es_hrs", "key": "horas_estimadas", "label": "Horas Técnicas Internas (HH)", "type": "number", "required": True},
                        {"id": "f_es_cpx", "key": "complejidad_tecnica", "label": "Complejidad Técnica Estimada", "type": "select", "required": True, "options": ["Baja", "Media", "Alta", "Muy Alta"]},
                        {"id": "f_es_des", "key": "desglose_tecnico", "label": "Desglose Técnico y Entregables", "type": "textarea", "required": True}
                    ]
                },
                {
                    "code": "form_dominio_planificacion_fechas",
                    "name": "Cronograma Firme de Atención",
                    "description": "Fechas acordadas de inicio de desarrollo y pase a producción.",
                    "fields": [
                        {"id": "f_pl_ini", "key": "fecha_inicio_atencion", "label": "Fecha Firme de Inicio", "type": "date", "required": True},
                        {"id": "f_pl_fin", "key": "fecha_fin_atencion", "label": "Fecha Firme de Entrega", "type": "date", "required": True},
                        {"id": "f_pl_spr", "key": "sprint_o_release", "label": "Release / Sprint Tentativo", "type": "text", "required": False}
                    ]
                }
            ]

            for sf_data in STAGE_FORMS_SEED:
                sf_res = await db.execute(select(StageForm).where(StageForm.code == sf_data["code"]))
                sf_obj = sf_res.scalar_one_or_none()
                if not sf_obj:
                    db.add(StageForm(
                        code=sf_data["code"],
                        name=sf_data["name"],
                        description=sf_data["description"],
                        fields=sf_data["fields"],
                        is_active=True
                    ))
                else:
                    sf_obj.name = sf_data["name"]
                    sf_obj.description = sf_data["description"]
                    sf_obj.fields = sf_data["fields"]
            await db.commit()

            # 10. Consentimientos & Declaraciones (9 consentimientos canónicos)
            STAGE_CONSENTS_SEED = [
                ("consent_key_user", "Declaración de Veracidad del Key User", "Doy fe de que el levantamiento asistido por Teo representa fielmente la necesidad operativa de mi área y acepto los términos de alcance y fecha propuesta.", 1),
                ("consent_bp_ti", "Dictamen de Viabilidad Técnica del BP TI", "Declaro que he revisado exhaustivamente los requerimientos técnicos, dependencias con sistemas core y certifico la viabilidad de la iniciativa.", 1),
                ("consent_business_owner", "Conformidad y Patrocinio del Business Owner", "Declaro haber evaluado y aprobado el patrocinio de los recursos, la justificación de negocio y el impacto en metas para esta iniciativa.", 1),
                ("consent_vicepresidencia", "Visto Bueno Estratégico de Vicepresidencia", "Otorgo el visto bueno ejecutivo para la priorización y canalización formal de la presente iniciativa hacia la demanda corporativa de TI.", 1),
                ("consent_lider_dominio", "Compromiso Técnico del Líder de Dominio", "Confirmo la capacidad técnica de mi dominio para ejecutar el análisis, estimación y planificación de las actividades acordadas.", 1),
                ("consent_financiero", "Validación Presupuestal y Financiera", "Certifico la disponibilidad presupuestal (Capex/Opex) asignada a la iniciativa según los centros de costos correspondientes.", 1),
                ("consent_seguridad", "Aprobación de Ciberseguridad y Riesgos", "Certifico que la arquitectura planteada cumple con las políticas de ciberseguridad, gestión de identidades y privacidad de datos.", 1),
                ("consent_gobierno_ti", "Dictamen de Arquitectura y Gobierno TI", "Certifico que la solución técnica respeta los patrones de integración, estándares cloud y catálogo de sistemas institucionales.", 1),
                ("consent_cierre", "Acta Final de Conformidad y Pase a Cartera", "Declaro la conformidad formal para la incorporación de esta iniciativa en la cartera oficial de proyectos TI de Laureate Perú.", 1),
            ]

            for code, title, statement, ver in STAGE_CONSENTS_SEED:
                sc_res = await db.execute(select(StageConsent).where(StageConsent.code == code))
                sc_obj = sc_res.scalar_one_or_none()
                if not sc_obj:
                    db.add(StageConsent(code=code, title=title, statement=statement, version=ver, is_active=True))
                else:
                    sc_obj.title = title
                    sc_obj.statement = statement
            await db.commit()

            # 11. Document Templates (2 plantillas de exportación)
            DOC_TEMPLATES_SEED = [
                ("doc_expediente_completo", "Expediente Ejecutivo de Iniciativa (PDF)", "Plantilla oficial para la generación del expediente ejecutivo y técnico completo de la iniciativa.", "<div>Expediente Ejecutivo Laureate Perú</div>", True),
                ("doc_acta_aprobacion", "Acta Oficial de Aprobación de Cartera TI", "Plantilla corporativa para la emisión del acta firmada con cadena de custodia digital.", "<div>Acta de Aprobación de Demanda TI</div>", False),
            ]
            for code, name, desc, html, is_def in DOC_TEMPLATES_SEED:
                dt_res = await db.execute(select(DocumentTemplate).where(DocumentTemplate.code == code))
                dt_obj = dt_res.scalar_one_or_none()
                if not dt_obj:
                    db.add(DocumentTemplate(
                        code=code,
                        name=name,
                        description=desc,
                        template_html=html,
                        margins={"top": 15, "right": 15, "bottom": 15, "left": 15},
                        is_active=True,
                        is_default=is_def
                    ))
            await db.commit()

            # 12. Flujo Oficial de Gestión de la Demanda v2 (18 nodos, 30 transiciones)
            wf_official_res = await db.execute(
                select(WorkflowDefinition).where(WorkflowDefinition.name == "Flujo Oficial de Gestión de la Demanda v2")
            )
            wf_official = wf_official_res.scalar_one_or_none()
            if not wf_official:
                # Archivar cualquier flujo anterior publicado
                await db.execute(
                    update(WorkflowDefinition).where(WorkflowDefinition.status == "published").values(status="archived")
                )

                master_coords = {
                    "start": {"x": 60, "y": 180},
                    "borrador": {"x": 240, "y": 140},
                    "ai_chat": {"x": 240, "y": 340},
                    "eval_bp": {"x": 520, "y": 140},
                    "aprob_bo": {"x": 800, "y": 140},
                    "aprob_vp": {"x": 1080, "y": 140},
                    "asig_demanda": {"x": 1360, "y": 140},
                    "ventana_est": {"x": 1640, "y": 140},
                    "gw_presupuesto": {"x": 1920, "y": 140},
                    "est_con_presupuesto": {"x": 2180, "y": 40},
                    "est_sin_presupuesto": {"x": 2180, "y": 240},
                    "val_est_bp": {"x": 2480, "y": 140},
                    "vobo_est_bo": {"x": 2760, "y": 140},
                    "plan_fechas": {"x": 3040, "y": 140},
                    "val_plan_bp": {"x": 3320, "y": 140},
                    "aprob_plan_bo": {"x": 3600, "y": 140},
                    "planificacion": {"x": 3880, "y": 140},
                    "end": {"x": 4140, "y": 180},
                    "observada": {"x": 1640, "y": 440},
                    "desestimada": {"x": 1920, "y": 440},
                }

                nodes_seed = [
                    {"id": "start", "type": "start", "position": {"x": 60, "y": 180}, "data": {"label": "Inicio", "nodeType": "start"}},
                    {"id": "borrador", "type": "state", "position": {"x": 240, "y": 140}, "data": {"label": "1. Borrador", "nodeType": "state", "stateSubtype": "standard", "form_id": "form_registro_iniciativa", "consent_id": "consent_key_user", "action_label": "Guardar Borrador", "description": "Registro inicial de la necesidad TI por el Key User con asistencia de TEO IA."}},
                    {"id": "ai_chat", "type": "ai_agent", "position": {"x": 240, "y": 340}, "data": {"label": "Asistente IA (Chat)", "nodeType": "ai_agent", "description": "TEO guía interactivamente al registrador para clarificar y estructurar su necesidad."}},
                    {"id": "eval_bp", "type": "state", "position": {"x": 520, "y": 140}, "data": {"label": "2. Evaluación BP TI", "nodeType": "state", "stateSubtype": "standard", "form_id": "form_bp_viabilidad", "consent_id": "consent_bp_ti", "action_label": "Enviar a aprobación de Business Partner", "description": "BP TI evalúa viabilidad técnica preliminar y selecciona obligatoriamente al Business Owner (BO)."}},
                    {"id": "aprob_bo", "type": "state", "position": {"x": 800, "y": 140}, "data": {"label": "3. Aprobación BO", "nodeType": "state", "stateSubtype": "standard", "form_id": "form_bo_patrocinio", "consent_id": "consent_business_owner", "action_label": "Enviar a Aprobación BO", "description": "Business Owner valida beneficio y patrocinio del área usuaria y selecciona obligatoriamente al Vicepresidente."}},
                    {"id": "aprob_vp", "type": "state", "position": {"x": 1080, "y": 140}, "data": {"label": "4. Aprobación VP", "nodeType": "state", "stateSubtype": "standard", "consent_id": "consent_vicepresidencia", "action_label": "Escalar a Aprobación VP", "description": "Vicepresidente otorga visto bueno estratégico y canaliza directo a la bandeja general de Gestión de la Demanda."}},
                    {"id": "asig_demanda", "type": "state", "position": {"x": 1360, "y": 140}, "data": {"label": "5. Asignación de Dominio", "nodeType": "state", "stateSubtype": "standard", "form_id": "form_dominio_dictamen", "consent_id": "consent_lider_dominio", "action_label": "Canalizar a Gestión de Demanda", "description": "Gestor de la Demanda revisa capacidad técnica y asigna obligatoriamente al Líder de Dominio responsable."}},
                    {"id": "ventana_est", "type": "state", "position": {"x": 1640, "y": 140}, "data": {"label": "6. Compromiso Estimación", "nodeType": "state", "stateSubtype": "standard", "form_id": "form_dominio_compromiso_ventana", "action_label": "Asignar Ventana de Estimación", "description": "Líder de Dominio registra la ventana de tiempo (fecha inicio y fin) en la que realizará su análisis técnico."}},
                    {"id": "gw_presupuesto", "type": "gateway", "position": {"x": 1920, "y": 140}, "data": {"label": "¿Requiere Presupuesto?", "nodeType": "gateway", "description": "Al concluir la ventana, se bifurca según necesidad de presupuesto externo.", "gatewayConfig": {"variable": "requiere_presupuesto", "rules": [{"edgeId": "e-gw-si", "operator": "equals", "value": "Sí", "targetNodeId": "est_con_presupuesto"}, {"edgeId": "e-gw-no", "operator": "equals", "value": "No", "targetNodeId": "est_sin_presupuesto"}]}}},
                    {"id": "est_con_presupuesto", "type": "state", "position": {"x": 2180, "y": 40}, "data": {"label": "7A. Estimación con Presupuesto", "nodeType": "state", "stateSubtype": "standard", "form_id": "form_dominio_est_con_presupuesto", "consent_id": "consent_lider_dominio", "action_label": "Estimación con Presupuesto", "description": "Líder de Dominio detalla presupuesto USD requerido y tiempo estimado de atención (esfuerzo)."}},
                    {"id": "est_sin_presupuesto", "type": "state", "position": {"x": 2180, "y": 240}, "data": {"label": "7B. Estimación sin Presupuesto", "nodeType": "state", "stateSubtype": "standard", "form_id": "form_dominio_est_sin_presupuesto", "consent_id": "consent_lider_dominio", "action_label": "Estimación sin Presupuesto", "description": "Líder de Dominio detalla tiempo de atención con equipo interno (esfuerzo sin fechas fijas aún)."}},
                    {"id": "val_est_bp", "type": "state", "position": {"x": 2480, "y": 140}, "data": {"label": "8A. Validación Estimación BP", "nodeType": "state", "stateSubtype": "standard", "action_label": "Enviar a Validación BP", "description": "BP TI revisa la estimación técnica y la presenta al Business Owner para su conformidad."}},
                    {"id": "vobo_est_bo", "type": "state", "position": {"x": 2760, "y": 140}, "data": {"label": "8B. VoBo Estimación BO", "nodeType": "state", "stateSubtype": "standard", "consent_id": "consent_business_owner", "action_label": "Enviar a VoBo Estimación BO", "description": "Business Owner aprueba el esfuerzo o presupuesto propuesto antes de programar fechas en TI."}},
                    {"id": "plan_fechas", "type": "state", "position": {"x": 3040, "y": 140}, "data": {"label": "9. Planificación de Fechas", "nodeType": "state", "stateSubtype": "standard", "form_id": "form_dominio_planificacion_fechas", "action_label": "Planificar Fechas", "description": "Con la estimación aprobada por el BO, Líder de Dominio fija las fechas firmes de inicio y fin de atención."}},
                    {"id": "val_plan_bp", "type": "state", "position": {"x": 3320, "y": 140}, "data": {"label": "10. Validación Planificación", "nodeType": "state", "stateSubtype": "standard", "action_label": "Enviar a Validación de Plan BP", "description": "BP TI valida la viabilidad del calendario y coordina visto bueno final con el Business Owner."}},
                    {"id": "aprob_plan_bo", "type": "state", "position": {"x": 3600, "y": 140}, "data": {"label": "11. Aprobación Final Fechas", "nodeType": "state", "stateSubtype": "standard", "consent_id": "consent_business_owner", "action_label": "Enviar a Aprobación Final BO", "description": "Business Owner aprueba formalmente las fechas de entrega acordadas."}},
                    {"id": "planificacion", "type": "state", "position": {"x": 3880, "y": 140}, "data": {"label": "12. Planificación", "nodeType": "state", "stateSubtype": "demanda", "action_label": "Aprobar y Registrar en Cartera", "description": "ESTADO FINAL OFICIAL. Iniciativa aprobada, registrada en cartera oficial con presupuesto y fechas firmes."}},
                    {"id": "end", "type": "end", "position": {"x": 4140, "y": 180}, "data": {"label": "Fin", "nodeType": "end"}},
                    {"id": "observada", "type": "state", "position": {"x": 1640, "y": 440}, "data": {"label": "⚠️ Observada (Hub BP TI)", "nodeType": "state", "stateSubtype": "observada", "action_label": "Observar / Solicitar Ajustes", "description": "Recibe cualquier observación con detalle obligatorio. BP TI edita y recoloca con justificación."}},
                    {"id": "desestimada", "type": "state", "position": {"x": 1920, "y": 440}, "data": {"label": "🗄️ Desestimada", "nodeType": "state", "stateSubtype": "desestimada", "action_label": "Desestimar Iniciativa", "description": "Iniciativa archivada o declarada no viable."}},
                ]

                edges_seed = [
                    {"id": "e-start-borrador", "source": "start", "target": "borrador", "label": "Crear iniciativa", "type": "workflow", "data": {"allowed_roles": ["registrador", "admin"]}},
                    {"id": "e-borrador-eval_bp", "source": "borrador", "target": "eval_bp", "label": "Enviar a TI", "type": "workflow", "data": {"allowed_roles": ["registrador", "key_user", "admin"]}},
                    {"id": "e-eval_bp-aprob_bo", "source": "eval_bp", "target": "aprob_bo", "label": "Derivar a Negocio (BO)", "type": "workflow", "data": {"allowed_roles": ["bp_ti", "admin"]}},
                    {"id": "e-aprob_bo-aprob_vp", "source": "aprob_bo", "target": "aprob_vp", "label": "Escalar a VP", "type": "workflow", "data": {"allowed_roles": ["business_owner", "admin"]}},
                    {"id": "e-aprob_vp-asig_demanda", "source": "aprob_vp", "target": "asig_demanda", "label": "Aprobar y Canalizar", "type": "workflow", "data": {"allowed_roles": ["vicepresidente_del_negocio", "admin"]}},
                    {"id": "e-asig_demanda-ventana_est", "source": "asig_demanda", "target": "ventana_est", "label": "Asignar Líder", "type": "workflow", "data": {"allowed_roles": ["gestor_de_la_demanda", "admin"]}},
                    {"id": "e-ventana_est-gw", "source": "ventana_est", "target": "gw_presupuesto", "label": "Concluye Ventana", "type": "workflow", "data": {"allowed_roles": ["lider_de_dominio", "admin"]}},
                    {"id": "e-gw-si", "source": "gw_presupuesto", "target": "est_con_presupuesto", "label": "SÍ requiere presupuesto", "type": "workflow", "data": {"allowed_roles": []}},
                    {"id": "e-gw-no", "source": "gw_presupuesto", "target": "est_sin_presupuesto", "label": "NO requiere presupuesto", "type": "workflow", "data": {"allowed_roles": []}},
                    {"id": "e-est_si-val_bp", "source": "est_con_presupuesto", "target": "val_est_bp", "label": "Enviar Estimación", "type": "workflow", "data": {"allowed_roles": ["lider_de_dominio", "admin"]}},
                    {"id": "e-est_no-val_bp", "source": "est_sin_presupuesto", "target": "val_est_bp", "label": "Enviar Estimación", "type": "workflow", "data": {"allowed_roles": ["lider_de_dominio", "admin"]}},
                    {"id": "e-val_bp-vobo_bo", "source": "val_est_bp", "target": "vobo_est_bo", "label": "Solicitar VoBo al BO", "type": "workflow", "data": {"allowed_roles": ["bp_ti", "admin"]}},
                    {"id": "e-vobo_bo-plan_fechas", "source": "vobo_est_bo", "target": "plan_fechas", "label": "Estimación Aprobada por BO", "type": "workflow", "data": {"allowed_roles": ["business_owner", "admin"]}},
                    {"id": "e-plan_fechas-val_plan_bp", "source": "plan_fechas", "target": "val_plan_bp", "label": "Presentar Calendario", "type": "workflow", "data": {"allowed_roles": ["lider_de_dominio", "admin"]}},
                    {"id": "e-val_plan_bp-aprob_plan_bo", "source": "val_plan_bp", "target": "aprob_plan_bo", "label": "Canalizar a Negocio", "type": "workflow", "data": {"allowed_roles": ["bp_ti", "admin"]}},
                    {"id": "e-aprob_plan_bo-planificacion", "source": "aprob_plan_bo", "target": "planificacion", "label": "Aprobación Oficial", "type": "workflow", "data": {"allowed_roles": ["business_owner", "admin"]}},
                    {"id": "e-planificacion-end", "source": "planificacion", "target": "end", "label": "Cartera TI", "type": "workflow", "data": {"allowed_roles": ["bp_ti", "gestor_de_la_demanda", "admin"]}},
                    {"id": "e-aprob_bo-obs", "source": "aprob_bo", "target": "observada", "label": "Observar requerimiento", "type": "workflow", "data": {"allowed_roles": ["business_owner", "admin"]}},
                    {"id": "e-aprob_vp-obs", "source": "aprob_vp", "target": "observada", "label": "Observar iniciativa", "type": "workflow", "data": {"allowed_roles": ["vicepresidente_del_negocio", "admin"]}},
                    {"id": "e-vobo_bo-obs", "source": "vobo_est_bo", "target": "observada", "label": "Observar estimación", "type": "workflow", "data": {"allowed_roles": ["business_owner", "admin"]}},
                    {"id": "e-aprob_plan-obs", "source": "aprob_plan_bo", "target": "observada", "label": "Observar fechas", "type": "workflow", "data": {"allowed_roles": ["business_owner", "admin"]}},
                    {"id": "e-obs-borrador", "source": "observada", "target": "borrador", "label": "Recolocar -> Borrador (Key User)", "type": "workflow", "data": {"allowed_roles": ["bp_ti", "admin"]}},
                    {"id": "e-obs-ventana", "source": "observada", "target": "ventana_est", "label": "Recolocar -> Reestimar (Dominio)", "type": "workflow", "data": {"allowed_roles": ["bp_ti", "admin"]}},
                    {"id": "e-obs-plan", "source": "observada", "target": "plan_fechas", "label": "Recolocar -> Replanificar (Dominio)", "type": "workflow", "data": {"allowed_roles": ["bp_ti", "admin"]}},
                    {"id": "e-obs-desestimar", "source": "observada", "target": "desestimada", "label": "Desestimar / Cancelar", "type": "workflow", "data": {"allowed_roles": ["bp_ti", "admin"]}},
                ]

                wf_official = WorkflowDefinition(
                    name="Flujo Oficial de Gestión de la Demanda v2",
                    version=2,
                    status="published",
                    description="Flujo corporativo completo: Registro -> BP TI -> BO -> VP -> Gestor Demanda -> Estimación Dominio -> VoBo Negocio -> Planificación de Fechas -> Cartera TI",
                    graph_json={
                        "nodes": nodes_seed,
                        "edges": edges_seed,
                        "master_coordinates": master_coords
                    },
                    published_at=datetime.now(timezone.utc)
                )
                db.add(wf_official)
                await db.commit()
                await db.refresh(wf_official)

                # Roles del flujo oficial
                NODE_ROLES_DATA = [
                    ("borrador", "registrador", True, True, False),
                    ("borrador", "admin", True, True, False),
                    ("eval_bp", "bp_ti", True, True, True),
                    ("eval_bp", "admin", True, True, True),
                    ("aprob_bo", "business_owner", False, True, True),
                    ("aprob_bo", "admin", False, True, True),
                    ("aprob_vp", "vicepresidente_del_negocio", False, True, True),
                    ("aprob_vp", "admin", False, True, True),
                    ("asig_demanda", "gestor_de_la_demanda", False, True, True),
                    ("asig_demanda", "admin", False, True, True),
                    ("ventana_est", "lider_de_dominio", True, True, False),
                    ("ventana_est", "admin", True, True, False),
                    ("est_con_presupuesto", "lider_de_dominio", True, True, False),
                    ("est_con_presupuesto", "admin", True, True, False),
                    ("est_sin_presupuesto", "lider_de_dominio", True, True, False),
                    ("est_sin_presupuesto", "admin", True, True, False),
                    ("val_est_bp", "bp_ti", False, True, True),
                    ("val_est_bp", "admin", True, True, True),
                    ("vobo_est_bo", "business_owner", False, True, True),
                    ("vobo_est_bo", "admin", True, True, True),
                    ("plan_fechas", "lider_de_dominio", True, True, False),
                    ("plan_fechas", "admin", True, True, False),
                    ("val_plan_bp", "bp_ti", False, True, True),
                    ("val_plan_bp", "admin", True, True, True),
                    ("aprob_plan_bo", "business_owner", False, True, True),
                    ("aprob_plan_bo", "admin", True, True, True),
                    ("planificacion", "invitado", False, False, False),
                    ("planificacion", "admin", True, True, False),
                    ("observada", "bp_ti", True, True, True),
                    ("observada", "admin", True, True, True),
                    ("desestimada", "bp_ti", False, True, False),
                    ("desestimada", "admin", False, True, False),
                ]
                for nid, rname, cedit, capp, crej in NODE_ROLES_DATA:
                    db.add(WorkflowNodeRole(
                        workflow_id=wf_official.id,
                        node_id=nid,
                        role_name=rname,
                        can_edit=cedit,
                        can_approve=capp,
                        can_reject=crej,
                    ))

                # Transiciones del flujo oficial
                for e in edges_seed:
                    db.add(WorkflowTransition(
                        workflow_id=wf_official.id,
                        edge_id=e["id"],
                        label=e["label"],
                        source_node_id=e["source"],
                        target_node_id=e["target"],
                        condition_type="always",
                        condition_config={},
                    ))
                await db.commit()

            logger.info("Base de datos IACS sembrada y validada con éxito.")
        except Exception as e:
            print(f"ERROR SEEDER: {e}")
            logger.error(f"Error durante el sembrado de base de datos: {e}")
            await db.rollback()
