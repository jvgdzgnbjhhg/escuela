# Plataforma de Evaluación Académica

Plataforma en desarrollo con Next.js/TypeScript, FastAPI, PostgreSQL y Alembic. La Fase 1 incorpora acceso con sesiones, instituciones, roles, años escolares, cursos, secciones, estudiantes, matrículas, traslados y asignaciones docentes. Evaluaciones y sincronización offline corresponden a las siguientes fases.

El alcance está en [el documento maestro](PLATAFORMA-EVALUACION-ACADEMICA-MASTER.md); las decisiones y separación de capas en [arquitectura](docs/architecture/overview.md). Consulta [las comprobaciones y pendientes de Fase 1](docs/testing/FASE-1.md) antes de considerar terminada una fase.

## Arranque con Docker

Requisitos: Docker Engine con Compose 2.24.4 o posterior (el override E2E utiliza `!override`) y acceso al daemon. La primera construcción descarga imágenes oficiales fijadas y dependencias de los registros npm/PyPI. Revisión de procedencia y efectos: [dependencias](docs/operations/DEPENDENCIAS.md).

1. Copia `.env.example` a `.env` si aún no existe.
2. Sustituye `POSTGRES_PASSWORD` y `RUNTIME_DB_PASSWORD` por dos contraseñas locales diferentes. `.env` está excluido de Git; no compartas su contenido. En esta entrega ya se generaron valores locales aleatorios en `.env` con permisos 0600.
3. Ejecuta desde la raíz:

```bash
docker compose config --quiet
docker compose up --build -d --wait --wait-timeout 180
```

- Interfaz por defecto: http://localhost:3000. En este equipo: **http://localhost:3100**, porque 3000 estaba ocupado.
- API activa: http://localhost:8000/api/v1/health/live
- PostgreSQL y esquema listos: http://localhost:8000/api/v1/health/ready
- OpenAPI de desarrollo: http://localhost:8000/api/v1/docs

`live` devuelve 200 si el proceso responde. `ready` devuelve 200 solo cuando conecta a PostgreSQL y la revisión Alembic coincide con el código; en caso contrario devuelve 503 sin detalles internos. El navegador utiliza el proxy de Next.js; la dirección interna de FastAPI no se envía al cliente.

Los puertos solo escuchan en 127.0.0.1 y PostgreSQL no publica puertos. Cambia `FRONTEND_PORT`/`BACKEND_PORT` en `.env` si están ocupados. En ese caso ajusta también URLs de comprobación y `E2E_BASE_URL`. La contraseña PostgreSQL inicializa un volumen nuevo; cambiar `.env` después no cambia automáticamente la contraseña de una base existente.

```bash
docker compose ps
docker compose logs --tail=100 backend frontend migrate
docker compose stop
docker compose start
# Retira contenedores y red, conservando el volumen de PostgreSQL:
docker compose --profile test down
```

No uses `down -v` para un apagado habitual: elimina el volumen y sus datos. No se publicó esta aplicación en Internet.

## Primera cuenta

Con los servicios levantados, ejecuta una sola vez:

```bash
docker compose run --rm migrate python -m app.manage bootstrap
```

Introduce institución, nombre, correo y una contraseña de al menos 12 caracteres. La contraseña no se muestra ni se acepta como argumento. El comando rechaza una segunda inicialización si ya existen cuentas. No se crea un administrador predeterminado ni se insertan cuentas de prueba en la base local. Inicia sesión en la interfaz y prepara años escolares → cursos → secciones → estudiantes → matrículas; añade docentes en «Equipo y permisos» y asígnales sus secciones.

Un administrador puede crear otra institución desde «Gestionar institución». El selector cambia el contexto de trabajo. Las ediciones con versiones antiguas se rechazan; recarga antes de repetirlas. Los registros se archivan y conservan historial. [Permisos y límites de seguridad](docs/architecture/adr/ADR-003-identidad-y-permisos.md).

## Pruebas y lint

La base de pruebas `db-test` es efímera, no publica puertos y no comparte el volumen de desarrollo. Los tests de integración requieren PostgreSQL y un nombre de base terminado en `_test`; no apuntarlos a una base compartida o con datos que se deban conservar.

```bash
docker compose --profile test run --build --rm backend-test
docker compose run --rm --no-deps backend-test ruff check --no-cache .
docker compose run --rm --no-deps backend-test ruff format --check --no-cache .
docker compose build frontend
```

La construcción frontend incluye ESLint, TypeScript y build. Con la aplicación levantada, `sh scripts/check-persistence.sh` verifica la revisión persistida tras reiniciar PostgreSQL sin volver a migrar. Para smoke tests del navegador, con la aplicación levantada y Node compatible:

```bash
cd frontend
npm ci --ignore-scripts --no-audit --no-fund
node node_modules/playwright/cli.js install chromium --only-shell
npm run test:e2e
```

La instalación de Playwright descarga Chromium/FFmpeg oficiales. Si el host carece de bibliotecas del navegador, revisa los requisitos antes de instalar paquetes del sistema. Para probar la instancia de esta sesión: `E2E_BASE_URL=http://127.0.0.1:3100 PLAYWRIGHT_BROWSERS_PATH=/tmp/escuela-playwright npm run test:e2e`. Se prueban escritorio y viewport móvil con Chromium; esto no acredita Safari/iOS real.

Para probar los flujos autenticados sin tocar la base local, con dependencias y navegador ya instalados:

```bash
PLAYWRIGHT_BROWSERS_PATH=/tmp/escuela-playwright sh scripts/check-identity.sh
```

El script usa el proyecto `escuelagestion-e2e`, puertos locales 3101/8001 y PostgreSQL tmpfs. Crea únicamente cuentas ficticias, prueba escritorio/móvil y elimina sus contenedores al terminar. No usar `docker-compose.e2e.yml` sobre el proyecto de desarrollo; su finalidad es descartar datos de prueba. Si el navegador está en su ubicación estándar, omite `PLAYWRIGHT_BROWSERS_PATH`.

El workflow [CI](.github/workflows/ci.yml) ejecuta esas comprobaciones en GitHub, arranca Compose, comprueba el reinicio de PostgreSQL y apaga el entorno. No despliega ni publica. La ejecución remota requiere subir el repositorio a GitHub y no se ha realizado desde esta sesión.

## Desarrollo sin reconstruir todo

Frontend local (API Docker ya levantada):

```bash
cd frontend
npm ci --ignore-scripts --no-audit --no-fund
API_INTERNAL_URL=http://127.0.0.1:8000 NEXT_TELEMETRY_DISABLED=1 npm run dev -- --port 3100
```

El puerto elegido debe figurar en `ALLOWED_ORIGINS` del backend para permitir login y escrituras.

Backend local con Python 3.13 y uv revisado:

```bash
cd backend
uv sync --frozen --no-build
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync pytest -m 'not integration'
```

Para servir backend fuera de Docker, exporta `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER` y `POSTGRES_PASSWORD` de una base local autorizada y ejecuta `uv run --no-sync uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8001`. Compose no expone PostgreSQL al host por defecto. No se toma `.env` de la raíz desde `backend/` automáticamente; exportar variables o crear su `.env` local ignorado. Nunca incluyas secretos en argumentos de comandos.

## Migraciones

```bash
docker compose run --rm migrate alembic current
docker compose run --rm migrate alembic heads
docker compose run --rm migrate python -m app.manage migrate
```

`0001_foundation` establece la versión inicial; `0002_identity` añade identidad y estructura académica. El comando `app.manage migrate` aplica Alembic y los permisos de la cuenta de ejecución `evaluacion_app`, que no es propietaria del esquema. No hay `create_all` automático. Las nuevas revisiones se generan en `backend/alembic/versions` en el checkout de desarrollo, se revisan y se prueban en una base dedicada antes de aplicarlas. El contenedor `migrate` no monta código del host: generar una revisión dentro de él no la conservaría en el repositorio.

Para actualizar dependencias Python, revisar cambios, editar pines y regenerar `uv.lock` y los dos exports con hashes usando uv 0.11.24:

```bash
cd backend
uv lock --no-build
uv export --frozen --no-dev --no-emit-project --output-file requirements.lock
uv export --frozen --no-emit-project --output-file requirements-dev.lock
```

Para npm mantener versiones directas exactas y `package-lock.json`; conservar `--ignore-scripts`. Las actualizaciones de imágenes requieren resolver y revisar un digest nuevo, modificar Dockerfiles/Compose y repetir pruebas.

## Estructura

```text
.agents/skills/           Reglas de dominio y sincronización
.github/workflows/ci.yml  Comprobaciones automáticas
backend/
  app/api/               Identidad, instituciones, estructura y health checks
  app/core/              Configuración y conexión PostgreSQL
  app/models/            Metadata SQLAlchemy
  alembic/versions/      Historial de migraciones
  tests/                 Pruebas unitarias e integración
  pyproject.toml         Dependencias directas
  uv.lock                Resolución reproducible
  requirements*.lock     Exports con hashes para Docker
frontend/
  src/app/               Acceso, proxy API y health check
  src/components/        Gestión institucional y formularios
  tests/                 Smoke tests Playwright
  package-lock.json      Resolución npm fijada
docs/architecture/       Decisiones y alcance
docs/operations/         Procedencia y operación
docs/testing/            Resultados y siguiente fase
docker-compose.yml       Entorno local y perfil test
```

## Próxima fase

Fase 2: motor de evaluaciones, instrumentos versionados e intentos independientes conforme al maestro. La Fase 1 deja controles funcionales de identidad, pero quedan MFA, recuperación de cuentas y otros controles de producción enumerados en el ADR 003. No iniciar el motor de evaluaciones ni offline antes de sus fases. Las skills del proyecto están descritas en [el inventario](docs/skills/INVENTARIO-Y-VALIDACION.md).
