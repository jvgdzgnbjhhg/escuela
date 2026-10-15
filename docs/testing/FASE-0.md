# Validación de Fase 0

Fecha: 2026-10-14. Alcance entregado: fundación técnica local. No es una certificación de producción ni una implementación de las fases académicas.

## Resultados ejecutados

| Comprobación | Resultado |
|---|---|
| `docker compose config --quiet` | Correcto |
| Ruff check y format, local e imagen de CI | Correcto: 12 archivos Python |
| Pytest local sin conexión de integración configurada | 5 passed, 3 skipped; las tres omitidas se ejecutaron posteriormente en Docker |
| `docker compose --profile test run --build --rm backend-test` | **8 passed**, incluyendo PostgreSQL real, upgrade/downgrade/repetición, readiness y rollback |
| `docker compose build frontend` | ESLint sin advertencias, TypeScript y Next build correctos |
| Arranque de db → migrate → backend → frontend | Correcto; migración termina en 0 y servicios saludables |
| Playwright, Chromium desktop y viewport móvil | **4 passed**, pantalla, idioma, disponibilidad real, recarga, ancho y health check |
| Revisión visual | Capturas 1440×1000 y 390×844 revisadas; texto legible y sin desbordamiento horizontal |
| Reinicio de PostgreSQL | La revisión `0001_foundation` se conserva y la API recupera readiness sin ejecutar migraciones de nuevo |
| Caída controlada de API | Frontend muestra indisponibilidad; tras restaurarla vuelve a mostrar servicio disponible |
| `npm audit --omit=dev --audit-level=high` | 0 vulnerabilidades reportadas; solo dependencias de ejecución frontend |
| Coherencia de lockfiles | Versiones directas coinciden con package-lock.json y uv.lock |
| Secretos y alcance | `.env`, .venv y node_modules ignorados; maestro sin cambios |

Las pruebas usan exclusivamente datos ficticios y una base dedicada. La prueba de persistencia verifica una fila real de `alembic_version`; no prueba todavía persistencia de entidades académicas, que no existen en esta fase. Las capturas temporales están en `/tmp/escuela-desktop.png` y `/tmp/escuela-mobile.png`, y no forman parte del código.

## Incidencias encontradas y resolución

- No existía un repositorio Git utilizable; se inicializó el directorio existente sin remoto ni publicación. No se creó commit automático.
- El sandbox impidió acceso Docker y sockets usados por TestClient/Turbopack. Se usó la escalación autorizada para Docker/pruebas; la compilación completa pasó dentro de Docker. La ejecución TestClient bloqueada en sandbox fue interrumpida; la ejecución autorizada pasó.
- El lint inicial detectó importaciones Python, export anónimo de PostCSS y enlaces de recarga. Se corrigieron; el resultado final pasa.
- ESLint 9.39.1 informó fin de soporte. Se actualizó a 10.12.0 y la construcción final verificó la combinación con eslint-config-next 16.4.1. npm mostró advertencias de peer dependency durante la actualización; el lockfile se instaló después correctamente mediante `npm ci` en Docker.
- El puerto 3000 ya estaba ocupado. Se preservó el otro servicio y se configuró solo `.env` local con `FRONTEND_PORT=3100`. URL de esta entrega: http://localhost:3100. La configuración de ejemplo mantiene 3000.
- Starlette emite una advertencia de deprecación por HTTPX en TestClient. Las ocho pruebas pasan. Antes de actualizar el cliente de pruebas, revisar procedencia y compatibilidad de la alternativa; no silenciar el aviso para aparentar ausencia de deuda.
- No había un parser YAML independiente disponible para validar el workflow (intento con js-yaml: módulo ausente). Se revisó el workflow manualmente; Compose sí se validó con su herramienta nativa. La ejecución real de GitHub Actions queda pendiente de disponer de un remoto y activar CI.

## Reproducción

Los comandos completos de arranque, pruebas, migraciones, apagado y actualización están en [README](../../README.md). El script `sh scripts/check-persistence.sh` reinicia solo la base de este proyecto y compara su revisión antes/después. No elimina volúmenes ni datos. La comprobación de caída de API detuvo/restauró el servicio mediante un script temporal con bloque finally.

Las comprobaciones de seguridad realizadas no reemplazan análisis de dependencias Python, imágenes, autorización o privacidad de la Fase 5. No se ejecutaron tests de independencia de intentos, aislamiento institucional o sincronización porque sus funcionalidades no están implementadas. Deben añadirse en las fases correspondientes antes de declarar el MVP listo.

## Plan concreto para Fase 1

1. Decidir sesiones propias u OIDC y documentar ADR-003 con contexto institucional, roles, revocación y estrategia de aislamiento; definir roles PostgreSQL separados para aplicación y migración.
2. Migrar instituciones, usuarios y membresías con constraints y pruebas de dos instituciones. No confiar en institution_id del cliente.
3. Implementar autenticación y comprobación central de permisos; verificar lectura/escritura contra objetos de otra institución y accesos revocados.
4. Incorporar años, cursos, secciones, estudiantes, matrícula y asignaciones con migraciones y contratos Pydantic.
5. Añadir interfaz mínima autenticada con casos E2E de permisos; continuar solo con criterios de salida de Fase 1 probados.

Autenticación, acceso de docentes, evaluaciones, exportaciones y offline quedan pendientes. No se han activado publicación pública ni servicios externos de aplicación.

Estado final: frontend y API permanecen levantados para revisión local; la base efímera `db-test` está detenida. Runtime en imágenes verificadas: Node 24.22.0 y Python 3.13.16. Se comprobaron enlaces locales y ausencia de bloques de claves privadas en los archivos candidatos a Git. Esto no equivale a un escaneo completo de secretos.
