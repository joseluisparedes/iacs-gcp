# ARCHITECTURE.md — Arquitectura del Sistema IACS GCP

## 1. Visión General del Sistema (C4 Model - Nivel 1 Contexto)

IACS permite a los colaboradores (Key Users, Solicitantes, Líderes de Dominio y Business Partners TI) registrar, estructurar mediante diálogo natural asistido por IA (Teo), evaluar técnicamente y gobernar mediante flujos de aprobación formal las iniciativas tecnológicas de la organización.

```
+------------------------------------------------------------------------+
|                          USUARIOS DEL SISTEMA                          |
|  - Key Users / Solicitantes (Directores, Jefes, VPs)                   |
|  - Business Partners TI (Evaluación Técnica y Funcional)               |
|  - Administradores del Sistema (Gobernanza de Flujos y RBAC)           |
|  - Entrenadores de IA (Base de Conocimiento y Guardarraíles de Teo)   |
+------------------------------------------------------------------------+
                                    │
                                    │ HTTPS (OIDC / JWT)
                                    ▼
+────────────────────────────────────────────────────────────────────────+
|                          EDGE & SEGURIDAD                              |
|           Cloudflare WAF / Cloud Load Balancing / API Gateway          |
+────────────────────────────────────────────────────────────────────────+
                                    │
                  ┌─────────────────┴─────────────────┐
                  ▼                                   ▼
+───────────────────────────────────+   +────────────────────────────────+
|        FRONTEND CONTAINER         |   |       BACKEND CONTAINER        |
|  Nuxt 4.x + Vue 3.x + TypeScript  |──▶|  Python 3.13 + FastAPI 0.116   |
|         (Google Cloud Run)        |   |       (Google Cloud Run)       |
+───────────────────────────────────+   +────────────────────────────────+
                                                        │
                      ┌─────────────────────────────────┼───────────────────────────────┐
                      ▼                                 ▼                               ▼
      +───────────────────────────────+ +───────────────────────────────+ +───────────────────────────+
      |      ALMACENAMIENTO SQL       | |      ALMACENAMIENTO OBJETO    | |   INTELIGENCIA ARTIFICIAL |
      |   Cloud SQL for PostgreSQL 17 | |     Google Cloud Storage      | |      Google Vertex AI     |
      |   (26 tablas relacionales)    | |  (Documentos, evidencias,     | |  (Gemini 2.5 Flash / Pro, |
      |                               | |   avatares)                   | |   Multimodal Audio STT)   |
      +───────────────────────────────+ +───────────────────────────────+ +───────────────────────────+
```

## 2. Contenedores y Capas (C4 Model - Nivel 2 Contenedores)

### Frontend (Nuxt 4 / Vue 3)
- Renderizado híbrido SSR/SPA optimizado para Cloud Run.
- Gestión de estado con Pinia.
- Diseñador visual de flujos de trabajo sobre `@vue-flow/core`.
- Consumo estricto de APIs mediante `$fetch` y composables tipados (`useInitiatives`, `useWorkflow`, `useTeoChat`).
- Cero acoplamiento a la base de datos o lógica interna de persistencia.

### Backend (Python 3.13 / FastAPI)
- Arquitectura Limpia dividida en:
  - `api/`: Enrutadores FastAPI con validación automática vía Pydantic v2.
  - `application/`: Casos de uso de negocio y motor evaluador de transiciones de workflow (`WorkflowEngine`).
  - `domain/`: Modelos y contratos de negocio puros.
  - `infrastructure/`: Capa de persistencia SQLAlchemy 2.0 (asíncrona con `asyncpg`).
  - `integrations/`: Adaptadores intercambiables para Vertex AI, GCS y Microsoft 365.

---

## 3. Matriz de Entidades y Base de Datos (PostgreSQL 17)

El modelo de datos comprende 26 tablas organizadas en los siguientes dominios:

1. **Organización & RBAC:** `vps`, `direcciones`, `allowed_users`, `user_roles_whitelist`, `profiles`, `profile_roles`, `app_roles`.
2. **Iniciativas & Formularios:** `initiatives`, `initiative_fields`, `user_table_preferences`, `site_settings`.
3. **Motor de Flujos (Workflows):** `workflow_definitions`, `workflow_node_roles`, `workflow_transitions`, `workflow_role_assignments`, `workflow_audit_log`.
4. **Cadena de Custodia & Dictámenes:** `stage_forms`, `stage_consents`, `initiative_stage_records`, `document_templates`.
5. **Inteligencia Artificial (Teo):** `ai_knowledge_folders`, `ai_training_config`, `ai_feedback`, `agent_logs`.
6. **Comunicaciones & Auditoría:** `email_logs`, `notifications`.
