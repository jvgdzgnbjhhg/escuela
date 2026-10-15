# Validación de Fase 1 — Identidad y Estructura Académica

Fecha: 2026-10-14. Alcance entregado: sesiones autenticadas, multi-tenancy institucional, roles y permisos, estructura académica (años escolares, cursos, secciones, estudiantes, matrículas, asignaciones docentes) y auditoría transaccional. No incluye motor de evaluación ni sincronización offline (Fases 2 y 4).

## Resultados ejecutados

| Comprobación | Comando | Resultado |
|---|---|---|
| Compose sintaxis y variables | `docker compose config --quiet` | Correcto |
| Ruff check | `docker compose run --rm --no-deps backend-test ruff check --no-cache .` | Correcto: 0 errores |
| Ruff format | `docker compose run --rm --no-deps backend-test ruff format --check --no-cache .` | Correcto: 27 archivos formateados |
| Tests de integración backend | `docker compose --profile test run --rm backend-test` | **21 passed** (incluye PostgreSQL real, aislamiento de dos centros, roles, sesiones, cookies, concurrencia y auditoría) |
| Construcción frontend | `docker compose build frontend` | Correcto: ESLint sin advertencias, TypeScript estricto y Next.js build |
| Persistencia y revisión Alembic | `sh scripts/check-persistence.sh` | Correcto: La revisión `0002_identity` persiste tras reinicio de PostgreSQL |
| Suite E2E completa | `sh scripts/check-identity.sh` | **10 passed** (Chromium desktop y mobile: health checks, proxy, autenticación, creación/edición/archivado, cambio de centro institucional y permisos docentes) |
| Health endpoints en vivo | `curl http://127.0.0.1:8000/api/v1/health/live` y `/ready` | 200 OK (`{"status":"ok"}` y `{"status":"ready"}`) |

## Cobertura de criterios de salida de Fase 1

1. **Aislamiento institucional:** Validado en `test_identity.py` y `identity.spec.ts`. Las entidades de una institución nunca se filtran a otra; el selector de cliente no autoriza por sí mismo y las claves foráneas compuestas obligan la concordancia de `institution_id`.
2. **Permisos en backend:** Los roles `ADMIN`, `COORDINATOR`, `TEACHER`, `VIEWER` y `TECHNICAL` son verificados a nivel de servicio y dependencia HTTP; los docentes solo leen sus secciones y estudiantes asignados.
3. **Control de concurrencia y optimismo:** Control de versiones con columna `version` y bloqueo transaccional a nivel de institución para mutaciones concurrentes.
4. **Auditoría inmutable:** Todas las mutaciones académicas registran `AuditEvent` en la misma transacción con actor, entidad y acción.

## Preparación para Fase 2

Con los criterios de salida de Fase 1 verificados y aprobados, se autoriza el paso a la **Fase 2 — Motor de Evaluación**:
- Definición de períodos, semanas y actividades académicas.
- Instrumentos de evaluación (rúbricas, escalas, listas de cotejo) y sus versiones inmutables.
- Evaluaciones con múltiples intentos independientes por estudiante.
- Historial y trazabilidad de notas.
