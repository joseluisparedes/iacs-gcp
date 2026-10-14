# AGENTS.md

## 1. Propósito

Este archivo define las reglas para agentes de IA que participen en el
desarrollo, mantenimiento, pruebas y evolución de la aplicación.

La solución debe seguir el principio:

> **La IA acelera el desarrollo; el Golden Path corporativo controla
> cómo se desarrolla, prueba, asegura y despliega.**

El objetivo es mantener una alta velocidad de evolución mediante IA +
GitHub + CI/CD, sin perder los estándares corporativos de arquitectura,
seguridad, datos, observabilidad y operación.

------------------------------------------------------------------------

## 2. Stack tecnológico objetivo

El stack tecnológico aprobado inicialmente es:

| Capa | Tecnología / versión objetivo |
| ---- | ------------------------------ |
| Frontend | Nuxt 4.x + Vue 3.x + TypeScript 5.x |
| Runtime frontend | Node.js 24 LTS |
| Backend | Python 3.13 + FastAPI 0.116.x |
| Base de datos | PostgreSQL 17.x |
| Runtime backend | Python 3.13 |
| Contenedores | Docker / OCI |
| Plataforma de ejecución | Google Cloud Run |
| API Management | Google Cloud API Gateway |
| Base de datos administrada | Cloud SQL for PostgreSQL |
| Archivos | Google Cloud Storage |
| Secretos | Google Secret Manager |
| IA | Vertex AI |
| Identidad | SecureAuth / IdP corporativo |
| Correo | Microsoft 365 / Exchange Online |
| Registry | Artifact Registry |
| IaC | Terraform 1.9+ |
| Repositorio | GitHub |
| CI/CD | GitHub Actions |
| Observabilidad | Cloud Logging + Cloud Monitoring + Dynatrace |
| Edge / WAF | Cloudflare + WAF + Cloud Load Balancing |

### Política de versiones

Las versiones indicadas son la línea tecnológica objetivo inicial.

Antes de fijar versiones exactas en producción, verificar:

-   compatibilidad entre dependencias;
-   soporte oficial;
-   vulnerabilidades conocidas;
-   políticas corporativas;
-   compatibilidad con GCP;
-   compatibilidad entre Node.js, Nuxt y Vue;
-   compatibilidad entre Python y FastAPI.

Las versiones deben quedar fijadas mediante los archivos de dependencias
del proyecto y no deben actualizarse arbitrariamente.

No cambiar de framework o major version sin justificar el cambio.

------------------------------------------------------------------------

## 3. Roles del agente

Según la tarea, actuar como:

### Arquitecto de Solución

Analizar arquitectura, decisiones, riesgos, deuda técnica y
alternativas.

### Arquitecto Cloud GCP

Diseñar sobre servicios administrados, PaaS y serverless. Priorizar
Cloud Run y evitar IaaS innecesario.

### Software Architect / Full Stack Developer

Mantener código limpio, modular, testeable y alineado al stack definido.

### DevOps / Platform Engineer

Gestionar Docker, GitHub Actions, Artifact Registry, Cloud Run y
Terraform.

### Security Architect

Revisar identidad, autorización, IAM, secretos, OWASP, dependencias,
contenedores, SAST, SCA y seguridad de IA.

### AI Architect / AI Engineer

Diseñar la integración con Vertex AI de forma desacoplada, segura y
controlable.

### QA / Test Engineer

Implementar y mantener pruebas unitarias, integración, API, frontend,
regresión y smoke tests.

### Technical Writer

Mantener README, arquitectura, APIs, configuración, operación y
decisiones técnicas.

------------------------------------------------------------------------

## 4. Regla de arquitectura

No sustituir una tecnología por otra únicamente porque exista una
alternativa.

Cuando exista una decisión relevante:

1.  explicar el problema;
2.  presentar alternativas;
3.  indicar ventajas y desventajas;
4.  recomendar una opción;
5.  explicar impacto.

No introducir nuevas tecnologías sin necesidad.

------------------------------------------------------------------------

## 5. Desarrollo local

El desarrollo debe ser reproducible mediante Docker.

Modelo esperado:

``` text
Docker Compose
   |
   +-- Frontend
   +-- Backend
   +-- PostgreSQL
```

El entorno local no necesita replicar todos los servicios administrados
de GCP.

Para servicios externos o administrados se podrán utilizar:

-   mocks;
-   interfaces;
-   emuladores;
-   servicios de desarrollo autorizados;
-   configuración específica de desarrollo.

La lógica de negocio debe permanecer independiente de estas diferencias.

------------------------------------------------------------------------

## 6. Contenedores

Todo componente desplegable debe tener un Dockerfile.

Los contenedores deben:

-   ser reproducibles;
-   ser compatibles con Cloud Run;
-   ser stateless;
-   no almacenar información persistente localmente;
-   no contener secretos;
-   ejecutar con usuario no privilegiado cuando sea posible;
-   minimizar superficie de ataque;
-   exponer únicamente los puertos necesarios.

------------------------------------------------------------------------

## 7. Frontend

Stack:

-   Nuxt 4.x;
-   Vue 3.x;
-   TypeScript 5.x;
-   Node.js 24 LTS.

El frontend no debe acceder directamente a PostgreSQL.

Debe consumir APIs mediante los mecanismos definidos en la arquitectura.

------------------------------------------------------------------------

## 8. Backend

Stack:

-   Python 3.13;
-   FastAPI 0.116.x.

El backend debe concentrar:

-   lógica de negocio;
-   APIs;
-   validaciones;
-   integración con datos;
-   integración con servicios externos;
-   integración con Vertex AI;
-   envío de correo;
-   autorización.

Mantener separación entre:

``` text
API
Application / Business Logic
Domain
Infrastructure
Integrations
```

cuando la complejidad del proyecto lo justifique.

------------------------------------------------------------------------

## 9. Base de datos

La base de datos objetivo es:

**Cloud SQL for PostgreSQL 17.x**

Localmente se utilizará PostgreSQL mediante Docker.

No asumir que una funcionalidad específica de Supabase existe en Cloud
SQL.

Si se migra una funcionalidad de Supabase:

1.  identificar su comportamiento;
2.  determinar qué servicio lo reemplaza;
3.  implementar una alternativa compatible;
4.  probar regresión.

------------------------------------------------------------------------

## 10. Archivos

El almacenamiento objetivo es:

**Google Cloud Storage**

La aplicación debe encapsular el acceso al almacenamiento mediante un
servicio o interfaz.

Esto permitirá reemplazar posteriormente el proveedor si fuese
necesario.

No acoplar la lógica de negocio directamente a una implementación
concreta de Storage.

------------------------------------------------------------------------

## 11. Identidad

La autenticación utilizará el proveedor de identidad corporativo
definido, inicialmente:

**SecureAuth / IdP corporativo**

La solución debe separar:

-   autenticación;
-   autorización;
-   roles;
-   permisos;
-   claims;
-   scopes.

No crear mecanismos de autenticación propios si el requerimiento puede
resolverse con el IdP corporativo.

------------------------------------------------------------------------

## 12. Inteligencia Artificial

El proveedor objetivo es:

**Vertex AI**

La aplicación debe utilizar una abstracción:

``` text
Application
    |
    v
AI Service
    |
    v
Vertex AI
```

Evitar llamadas directas a Vertex AI distribuidas por todo el código.

La abstracción debe facilitar una futura sustitución o incorporación de
otro proveedor sin reescribir la lógica de negocio.

Considerar:

-   prompt injection;
-   fuga de información;
-   límites de consumo;
-   costos;
-   logging;
-   evaluación de respuestas;
-   datos sensibles.

------------------------------------------------------------------------

## 13. Servicio de correo

El servicio inicial de entrega de correo será:

**Microsoft 365 / Exchange Online**

No debe acoplarse la lógica de negocio directamente a Microsoft Graph o
Exchange.

Implementar una abstracción similar a:

``` text
Application
    |
    v
Email Service
    |
    v
Microsoft 365 / Exchange Online
```

El objetivo es que posteriormente pueda sustituirse por un servicio
transaccional especializado sin modificar la lógica de negocio.

Ejemplo conceptual:

``` text
EmailService
     |
     +-- Microsoft365EmailProvider
     |
     +-- FutureTransactionalEmailProvider
```

La implementación inicial utilizará Microsoft 365 porque el volumen de
correos esperado no justifica inicialmente un servicio transaccional
especializado.

Si el volumen, requisitos de entrega, trazabilidad o necesidades
operativas cambian, evaluar nuevamente el proveedor.

------------------------------------------------------------------------

## 14. Secretos

Nunca almacenar en Git:

-   passwords;
-   API keys;
-   tokens;
-   certificados privados;
-   credenciales.

Localmente utilizar:

``` text
.env
.env.example
```

Los valores reales deben permanecer fuera del repositorio.

En GCP utilizar:

**Secret Manager**

------------------------------------------------------------------------

## 15. GitHub

GitHub es el repositorio central.

Ramas sugeridas:

``` text
feature/*
fix/*
refactor/*
chore/*
```

Los cambios relevantes deben utilizar Pull Requests.

La IA puede ayudar a preparar:

-   código;
-   tests;
-   documentación;
-   commit;
-   descripción del Pull Request.

No debe saltarse los controles del repositorio.

------------------------------------------------------------------------

## 16. CI/CD

Pipeline objetivo:

``` text
GitHub
   |
   v
GitHub Actions
   |
   +-- Lint
   +-- Unit Tests
   +-- SAST
   +-- SCA
   +-- Secret Scan
   +-- Build
   +-- Docker Build
   +-- Container Scan
   |
   v
Artifact Registry
   |
   v
Cloud Run
```

Los despliegues deben ser reproducibles.

Los controles de promoción a QA/PROD deben respetar las políticas
corporativas.

------------------------------------------------------------------------

## 17. Terraform

Terraform administrará infraestructura.

Separar:

``` text
Aplicación
frontend/
backend/

Infraestructura
infra/terraform/

Automatización
.github/workflows/
```

Terraform podrá gestionar:

-   Cloud Run;
-   Cloud SQL;
-   Cloud Storage;
-   API Gateway;
-   Secret Manager;
-   IAM;
-   networking;
-   otros recursos GCP.

No utilizar Terraform para cambios funcionales normales.

------------------------------------------------------------------------

## 18. Observabilidad

Implementar:

-   logs estructurados;
-   health checks;
-   métricas;
-   trazabilidad;
-   correlation ID cuando corresponda;
-   manejo controlado de errores.

Integrar:

``` text
Cloud Logging
Cloud Monitoring
Dynatrace
```

Nunca registrar secretos o información sensible innecesaria.

------------------------------------------------------------------------

## 19. Reglas de seguridad

Antes de considerar una funcionalidad completa, revisar cuando
corresponda:

-   autenticación;
-   autorización;
-   validación de entradas;
-   OWASP;
-   dependencias;
-   secretos;
-   IAM;
-   seguridad de contenedores;
-   API security;
-   datos sensibles;
-   seguridad de IA.

No ocultar vulnerabilidades para conseguir que el pipeline pase.

------------------------------------------------------------------------

## 20. Documentación

Mantener actualizados:

``` text
README.md
AGENTS.md
ARCHITECTURE.md
docs/
```

Toda modificación arquitectónica relevante debe actualizar
`ARCHITECTURE.md`.

Toda nueva regla de trabajo para agentes debe actualizar `AGENTS.md`.

------------------------------------------------------------------------

## 21. Trabajo incremental

No intentar completar toda la migración en una sola iteración.

Orden recomendado:

``` text
FASE 0  Descubrimiento
   |
FASE 1  Docker + desarrollo local
   |
FASE 2  Configuración
   |
FASE 3  GitHub + estándares IA
   |
FASE 4  Migración de servicios
   |
FASE 5  Terraform
   |
FASE 6  CI/CD
   |
FASE 7  Observabilidad
   |
FASE 8  Seguridad + Hardening
   |
FASE 9  Validación final
```

Cada fase debe dejar el proyecto en un estado verificable.

------------------------------------------------------------------------

## 22. Formato de trabajo

Para tareas relevantes:

### Objetivo

### Análisis

### Decisión

### Cambios

### Implementación

### Validación

### Riesgos

### Pendientes

### Siguiente paso

No afirmar que una tarea está terminada si no fue validada.

------------------------------------------------------------------------

## 23. Regla final

El resultado esperado es:

``` text
Developer + IA
       |
       v
    GitHub
       |
       v
 Pull Request
       |
       v
Quality + Security Gates
       |
       v
Artifact Registry
       |
       v
    Cloud Run
       |
       +-- Cloud SQL
       +-- Cloud Storage
       +-- Vertex AI
       +-- Microsoft 365
       +-- Secret Manager
       +-- API Gateway
```

La solución debe mantener la capacidad de evolucionar rápidamente
mediante IA sin perder los controles corporativos.
