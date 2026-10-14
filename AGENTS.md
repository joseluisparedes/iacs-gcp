# AGENTS.md — Reglas y Directivas para Agentes de IA en IACS GCP

## 1. Propósito y Principio Rector

Este repositorio gobierna la solución modernizada de **IACS (Iniciativas y Asistencia Cognitiva de Software)** adaptada al stack corporativo de Google Cloud Platform (GCP).

> **La IA acelera el desarrollo; el Golden Path corporativo controla cómo se desarrolla, prueba, asegura y despliega.**

Cualquier agente que opere sobre este código debe respetar los estándares de arquitectura limpia, seguridad por diseño, datos desacoplados y pruebas automatizadas.

---

## 2. Stack Tecnológico Objetivo Aprobado

| Capa | Tecnología / Estándar |
| :--- | :--- |
| **Frontend** | Nuxt 4.x + Vue 3.x + TypeScript 5.x |
| **Runtime Frontend** | Node.js 24 LTS |
| **Backend** | Python 3.13 + FastAPI 0.116.x |
| **Base de Datos** | Cloud SQL for PostgreSQL 17.x (local: PostgreSQL 17 Docker) |
| **Contenedores** | Docker / OCI multi-stage sin privilegios de root |
| **Plataforma de Ejecución** | Google Cloud Run (Serverless) |
| **Almacenamiento de Archivos** | Google Cloud Storage (GCS) con interfaz abstracta |
| **Inteligencia Artificial** | Vertex AI (Gemini 2.5 Flash / Pro) con interfaz abstracta |
| **Identidad & Acceso** | SecureAuth / IdP Corporativo (OIDC / JWT) |
| **Servicio de Correo** | Microsoft 365 / Exchange Online con interfaz abstracta |
| **Secretos** | Google Secret Manager |
| **Infraestructura como Código** | Terraform 1.9+ |
| **Integración Continua** | GitHub Actions |
| **Observabilidad** | Cloud Logging + Cloud Monitoring + Dynatrace |

---

## 3. Reglas Innegociables de Arquitectura

1. **Frontend Desacoplado de la Base de Datos:**
   El frontend Nuxt **NUNCA** debe conectarse directamente a PostgreSQL. Toda interacción debe canalizarse a través de las APIs REST expuestas por el backend FastAPI.
2. **Abstracción de Servicios Externos:**
   Toda integración con servicios en la nube (Vertex AI, GCS, Microsoft 365) debe residir detrás de interfaces abstractas en `app/integrations/`. Esto garantiza que la lógica de negocio permanezca pura e independiente del proveedor.
3. **Contenedores Stateless y Compatibles con Cloud Run:**
   Ningún contenedor debe guardar estado en el sistema de archivos local de forma persistente. No debe contener credenciales ni secretos quemados en el código o imagen.
4. **Respeto a la Fuente de Verdad Funcional:**
   No modificar, simplificar ni eliminar reglas de negocio previamente identificadas en el proyecto original sin documentar y justificar el cambio.
5. **Calidad y Verificación Continua:**
   Cada cambio debe incluir pruebas automatizadas correspondientes (`pytest` en backend, `vitest` en frontend) y un comando ejecutable que valide que no se introducen regresiones.

---

## 4. Estructura del Proyecto

```text
├── .github/workflows/          # Pipelines de CI/CD (Quality & Security Gates)
├── backend/                    # API y lógica de negocio (Python 3.13 / FastAPI)
│   ├── app/
│   │   ├── api/v1/             # Controladores y rutas REST
│   │   ├── application/        # Casos de uso y orquestadores (Workflow Engine)
│   │   ├── domain/             # Entidades y reglas de dominio puras
│   │   ├── infrastructure/     # Conexión DB, SQLAlchemy y repositorios
│   │   └── integrations/       # Adaptadores de Vertex AI, GCS y M365
│   ├── tests/                  # Pruebas unitarias e integración (pytest)
│   └── Dockerfile              # Contenedor Cloud Run
├── frontend/                   # Interfaz de usuario (Nuxt 4 / Vue 3)
│   ├── pages/                  # Vistas del sistema
│   ├── components/             # Componentes modulares y nodos de Vue Flow
│   ├── stores/                 # Estado global Pinia
│   └── Dockerfile              # Contenedor Cloud Run
├── database/                   # DDL y scripts iniciales para PostgreSQL 17
├── infra/terraform/            # Configuración IaC
└── docker-compose.yml          # Entorno de desarrollo local
```
