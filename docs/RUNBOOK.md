# RUNBOOK — Operación y Monitoreo del Sistema IACS GCP

## 1. Verificación del Estado Operativo (Health Checks)

* **Backend Health Check:**
  `GET /api/health` o `GET /api/v1/health`
  Respuesta esperada: `{"status": "ok", "app": "IACS Enterprise (GCP)", "env": "local"}`

* **Base de Datos PostgreSQL 17:**
  Verificar conectividad mediante `pg_isready -h localhost -p 5432 -U iacs_user -d iacs_db`.

* **Frontend Nuxt 4:**
  `GET /` devuelve código HTTP 200/302.

---

## 2. Monitoreo y Observabilidad en GCP

1. **Google Cloud Logging:**
   Todos los logs se emiten en formato JSON estructurado con campo `severity`, `timestamp` y `correlation_id` cuando aplica.
   * Filtro recomendado para errores en Logs Explorer:
     ```text
     resource.type="cloud_run_revision"
     severity>=ERROR
     ```

2. **Google Cloud Monitoring:**
   Alertas configuradas sobre:
   * Latencia de Cloud Run P95 > 2.5s.
   * Códigos HTTP 5xx > 1% en ventana de 5 minutos.
   * Conexiones activas en Cloud SQL > 80% de la capacidad de pool.

3. **Dynatrace:**
   Inyección del OneAgent en contenedores de Cloud Run mediante la variable de entorno `DYNATRACE_API_TOKEN` y `DYNATRACE_ENVIRONMENT_ID` para rastreo distribuido de transacciones de extremo a extremo.
