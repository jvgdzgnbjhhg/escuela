# Fundación técnica

Se conserva el monolito modular descrito en el [maestro](../../PLATAFORMA-EVALUACION-ACADEMICA-MASTER.md), §3. El navegador accede a Next.js; su servidor consulta FastAPI dentro de la red de Compose. FastAPI usa SQLAlchemy y psycopg para PostgreSQL. La base no publica puerto al host.

La Fase 0 incorporó configuración, health checks y herramientas. La Fase 1 añade identidad, contexto institucional y estructura académica conforme al [ADR 003](adr/ADR-003-identidad-y-permisos.md). Las evaluaciones y la sincronización offline siguen fuera de esta fase.

```text
Navegador → Next.js :3000 → FastAPI :8000 → PostgreSQL :5432
                               ↑
                    Alembic prepara el esquema
```

`backend/app/api` contiene adaptadores HTTP; `core` configuración y conexión; `models` la metadata compartida. `schemas` valida entradas y salidas; `services` concentra reglas, auditoría y seguridad. Los componentes frontend presentan formularios y contexto institucional. No se añaden capas vacías. Las pruebas backend viven solo en `backend/tests`, en lugar de dividirlas también en `app/tests`. Estas son las únicas simplificaciones de estructura.

El proxy de datos limita rutas, cuerpos y tiempo de espera; no hay credenciales en código cliente ni necesidad de CORS para este flujo. Los health checks públicos solo informan estado, sin versión del motor, errores SQL ni datos internos.

Alembic se ejecuta como un servicio finito antes de iniciar la API. La migración inicial registra el punto de partida en `alembic_version`; no crea una tabla ficticia para simular persistencia. Readiness consulta PostgreSQL y compara la revisión real con las cabeceras de migración del código.

Consulta los ADR [001](adr/ADR-001-monolito-modular.md), [002](adr/ADR-002-postgresql.md) y [008](adr/ADR-008-despliegue.md). El [ADR 003](adr/ADR-003-identidad-y-permisos.md) documenta identidad. Los ADR de intentos y offline corresponden a fases posteriores.
