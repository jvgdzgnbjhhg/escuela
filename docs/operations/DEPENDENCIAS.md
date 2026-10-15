# Procedencia de dependencias — Fase 0

Revisión realizada el 2026-10-14 antes de ejecutar las herramientas instaladas. Se consultaron registros oficiales npm/PyPI, metadatos de licencia/repositorio y scripts de las dependencias directas, fuentes de imágenes oficiales y efectos de sus comandos. No es una auditoría exhaustiva del código de todas las dependencias transitivas.

## Paquetes

| Grupo | Versiones directas | Procedencia y licencia |
|---|---|---|
| Web | Next 16.4.1, React/React DOM 19.3.1 | npm; repositorios vercel/next.js y react/react; MIT |
| Tipado | TypeScript 5.9.3, @types/node 22.19.15, @types/react y react-dom 19.3.0 | npm; Microsoft/TypeScript (Apache-2.0), DefinitelyTyped (MIT) |
| Estilos | Tailwind y @tailwindcss/postcss 4.3.3 | npm; tailwindlabs/tailwindcss; MIT |
| Calidad web | ESLint 10.12.0, eslint-config-next 16.4.1, @playwright/test 1.64.1 | npm; ESLint/Vercel (MIT), Microsoft Playwright (Apache-2.0) |
| API | FastAPI 0.143.1, uvicorn 0.54.0, pydantic-settings 2.16.0 | PyPI; fastapi/fastapi, Kludex/uvicorn, pydantic/pydantic-settings; MIT/BSD-3-Clause |
| Persistencia | SQLAlchemy 2.1.4, Alembic 1.20.0, psycopg[binary] 3.3.6 | PyPI; sqlalchemy/sqlalchemy, sqlalchemy/alembic, psycopg/psycopg; MIT y LGPL-3.0-only para psycopg |
| Calidad Python | Pytest 9.1.1, HTTPX 0.28.1, Ruff 0.17.0 | PyPI; pytest-dev/pytest, encode/httpx, astral-sh/ruff; MIT/BSD-3-Clause |

Las versiones se verifican en `package.json`, `package-lock.json`, `pyproject.toml`, `uv.lock` y exports con hashes. Se eligió TypeScript 5.9.3 como versión compatible con la herramienta Next; no se adoptó automáticamente el salto mayor del registro. ESLint 9.39.1 mostró aviso de fin de soporte y se sustituyó por 10.12.0; comprobar los resultados reales de lint/build en el registro de pruebas.

- `npm install --package-lock-only --ignore-scripts` resolvió el árbol sin ejecutarlo. Se verificó que las URLs resueltas pertenecen a registry.npmjs.org. `npm ci --ignore-scripts` conserva desactivados los hooks también en Docker/CI.
- Se detectó `unrs-resolver` con postinstall basado en `napi-postinstall`. Se leyó su entrada; ese postinstall no se ejecutó. Binarios opcionales publicados resuelven las necesidades de las herramientas para la plataforma instalada.
- `uv lock --no-build` fijó el árbol desde PyPI. La instalación usa wheels (`--no-build` con uv, `--only-binary=:all:` y `--require-hashes` con pip en Docker); no ejecuta builds de paquetes fuente. Imports y herramientas sí ejecutan código de las dependencias revisadas.
- No se ejecutó create-next-app, instaladores de skills ni código copiado de skills externas. El código de aplicación fue escrito en este proyecto.
- Next puede generar telemetría: se desactiva con `NEXT_TELEMETRY_DISABLED=1` en Docker y CI. El frontend no descarga fuentes ni imágenes remotas.
- Playwright descarga Chromium headless y FFmpeg de cdn.playwright.dev; se revisó la revisión del navegador en `playwright-core/browsers.json` y el descargador antes de ejecutar. En esta máquina se guardó en `/tmp/escuela-playwright`. La CI usa `--with-deps` dentro del runner efímero; eso instala bibliotecas del sistema en ese runner, no en el equipo local.
- npm audit transmite nombres/versiones de paquetes al registro, sin código de aplicación ni datos académicos. El resultado no cubre dependencias Python ni vulnerabilidades de las imágenes.

## Imágenes y automatización

Fuentes primarias revisadas: [Node oficial](https://github.com/nodejs/docker-node), [Python oficial](https://github.com/docker-library/python), [PostgreSQL oficial](https://github.com/docker-library/postgres). Se consultaron sus manifiestos y Dockerfiles; el entrypoint PostgreSQL inicializa directorios y una base nueva, ajusta permisos y ejecuta el servidor. Solo se usa sobre volúmenes nuevos de este proyecto.

| Imagen | Digest del índice fijado |
|---|---|
| node:24-bookworm-slim | `sha256:a5f4366e834695d5f363b920c104953a535d3a9864d1bdf74566a0ebe01daee5` |
| python:3.13-slim-bookworm | `sha256:a1165e272e578941b84abc79e4ab38a0305cd12803a5c4247979ac7655f4d641` |
| postgres:18-bookworm | `sha256:afc7e2d441324c0388fa80c3d24f733b4194a4eb7f47dd8ee2b08eb1a24a647c` |

Los Dockerfiles descargan dependencias durante build, crean archivos de imagen y usuarios locales del contenedor. Los servicios crean una red y un volumen de proyecto; la aplicación no monta el socket Docker ni carpetas personales. La base de test vive en tmpfs. El usuario bootstrap PostgreSQL es solo para desarrollo; no es el rol final de aplicación productiva.

GitHub Actions utiliza `actions/checkout` y `actions/setup-node` fijadas a commits en `.github/workflows/ci.yml`, con Node 24.22.0 fijado y permisos `contents: read` y sin persistir credenciales Git. Checkout lee el repositorio; setup-node descarga Node y administra caché npm del runner. No hay secretos de producción, despliegues, pushes ni acciones de terceros adicionales. No se ejecutó CI remota en esta entrega.

Actualizar cualquiera de estos componentes implica revisar origen, licencia, scripts, compatibilidad y cambios de comportamiento antes de ejecutar la nueva versión. Fijar un hash aporta reproducibilidad, no garantiza ausencia de vulnerabilidades.

## Incorporaciones de identidad — 2026-10-14

Se revisaron metadatos de distribución, repositorios, licencias y scripts antes de instalar estas versiones exactas:

| Paquete | Procedencia | Licencia | Efectos revisados |
|---|---|---|---|
| argon2-cffi 25.1.0 | [PyPI](https://pypi.org/project/argon2-cffi/25.1.0/), hynek/argon2-cffi | MIT | Hashes Argon2id; bindings nativos. Instalación exclusivamente desde wheels con hashes, sin compilar fuentes. Consume memoria/CPU al verificar contraseñas. |
| email-validator 2.3.0 | [PyPI](https://pypi.org/project/email-validator/2.3.0/), JoshData/python-email-validator | Unlicense | Validación de correo usada por Pydantic; no se habilita comprobación DNS de entrega. |
| react-hook-form 7.90.0 | [npm](https://www.npmjs.com/package/react-hook-form/v/7.90.0), react-hook-form/react-hook-form | MIT | Gestión de formularios; scripts de desarrollo/publicación, incluido Husky, omitidos mediante `--ignore-scripts`. |
| zod 4.6.7 | [npm](https://www.npmjs.com/package/zod/v/4.6.7), colinhacks/zod | MIT | Validación local; scripts de build/limpieza del paquete no ejecutados. |

Transitivas Python incorporadas y fijadas: argon2-cffi-bindings 26.1.0, cffi 2.1.1, pycparser 3.11 y dnspython 2.9.0. `uv.lock` y ambos exports contienen la resolución y hashes. npm usa el lockfile y `--ignore-scripts`. Se revisó `@hookform/resolvers` como opción, pero no se instaló: la validación utiliza directamente Zod. No se instaló ningún plugin ni skill externa durante esta fase.
