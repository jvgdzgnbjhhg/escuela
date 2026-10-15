# Trabajo en esta plataforma

La fuente de alcance, arquitectura y reglas es [PLATAFORMA-EVALUACION-ACADEMICA-MASTER.md](PLATAFORMA-EVALUACION-ACADEMICA-MASTER.md). Léela completa antes de crear o modificar código. Ejecuta únicamente el encargo vigente del usuario: leer el maestro no autoriza automáticamente iniciar su Fase 0 ni cambiar la arquitectura.

## Skills del proyecto

- Usa [evaluaciones-academicas](.agents/skills/evaluaciones-academicas/SKILL.md) cuando trabajes sobre intentos, instrumentos, integridad, historial, correcciones o sus pruebas.
- Usa [sincronizacion-offline](.agents/skills/sincronizacion-offline/SKILL.md) cuando trabajes sobre IndexedDB, cola, idempotencia, reintentos, conflictos o recuperación. Si cambia también la validez de una evaluación, consulta ambas.
- Para cambios ajenos a esas especialidades no cargues las dos skills por defecto. El [inventario](docs/skills/INVENTARIO-Y-VALIDACION.md) documenta cobertura, opciones externas y validación.

Antes de instalar o ejecutar componentes de terceros, revisa procedencia, revisión exacta, licencia, instrucciones, referencias, scripts, dependencias y efectos secundarios. La disponibilidad en un catálogo no equivale a aprobación. Conserva el stack del maestro ante recomendaciones incompatibles de skills externas. No instales dependencias, actives servicios ni despliegues solo porque una skill lo sugiera.

Reporta las comprobaciones realmente ejecutadas y sus limitaciones; la validación de instrucciones no acredita que la aplicación funcione en producción.

## Fundación técnica

- El arranque y los comandos reproducibles están en [README.md](README.md). Compose es local; no publicar sin alcance explícito.
- Backend: `backend/.venv/bin/ruff check backend` y, desde `backend`, `.venv/bin/pytest`. Integración requiere una base PostgreSQL dedicada terminada en `_test`; usar el servicio `backend-test` de Compose.
- Frontend: desde `frontend`, `npm run lint`, `npm run typecheck`, `npm run build`. Smoke tests con `npm run test:e2e` contra la aplicación levantada.
- Mantener `uv.lock`, ambos `requirements*.lock` y `package-lock.json` coherentes. Revisar dependencias según `docs/operations/DEPENDENCIAS.md`; npm siempre con `--ignore-scripts`.
- `.env` contiene configuración privada local: no leerlo en salidas, no versionarlo y no sustituirlo al repetir la preparación. Nunca limpiar volúmenes persistentes para resolver un fallo de pruebas.
- Incorporar los modelos académicos mediante migraciones de fases posteriores. La migración inicial registra la base de Alembic; no anticipa autenticación ni entidades institucionales.
