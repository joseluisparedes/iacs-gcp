# IACS Enterprise — Google Cloud Platform

Sistema de **Gestión de Iniciativas y Asistencia Cognitiva de Software (IACS)** modernizado para Google Cloud Platform (GCP).

## Requisitos Previos

* Docker & Docker Compose (v2.20+)
* Node.js 24 LTS (opcional para desarrollo fuera de contenedor)
* Python 3.13 (opcional para desarrollo fuera de contenedor)

## Inicio Rápido (Entorno Local Reproducible)

1. Clonar el repositorio y copiar el archivo de variables de entorno:
   ```bash
   cp .env.example .env
   ```

2. Levantar el stack completo (PostgreSQL 17 + FastAPI Backend + Nuxt 4 Frontend):
   ```bash
   docker compose up --build
   ```

3. Acceder a las aplicaciones:
   * **Frontend (Nuxt 4 / Vue 3):** [http://localhost:3000](http://localhost:3000)
   * **Backend API Docs (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)
   * **Health Check API:** [http://localhost:8000/api/health](http://localhost:8000/api/health)
   * **Base de Datos PostgreSQL 17:** `localhost:5432` (Usuario: `iacs_user`, DB: `iacs_db`)

## Arquitectura de la Solución

Para detalles arquitectónicos, diagrama C4, flujos de datos y mapa de componentes, consultar [ARCHITECTURE.md](file:///D:/ProyectosJLPH/IACS%20GCP/ARCHITECTURE.md).

Para reglas de desarrollo y directivas operativas de IA, consultar [AGENTS.md](file:///D:/ProyectosJLPH/IACS%20GCP/AGENTS.md).
