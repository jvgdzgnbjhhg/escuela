# Skills para la plataforma

Revisión: 2026-10-14. Alcance: preparar instrucciones especializadas, sin implementar funcionalidades, iniciar Fase 0 ni alterar arquitectura. Fuente de negocio: [documento maestro](../../PLATAFORMA-EVALUACION-ACADEMICA-MASTER.md). No se instalaron skills externas ni dependencias.

## Inventario local

«Disponible en sesión» significa que Codex la anunció como utilizable. Un archivo en caché no demuestra activación. Las rutas siguientes corresponden al entorno inspeccionado.

| Estado | Skills | Ubicación |
|---|---|---|
| Instaladas y disponibles | `imagegen`, `openai-docs`, `plugin-creator`, `skill-creator`, `skill-installer` | `/home/richard/.codex/skills/.system/<nombre>/SKILL.md` |
| Instaladas y disponibles | `frontend-design` | `/home/richard/.codex/skills/frontend-design/SKILL.md` |
| Instalada y disponible | `animations` | `/home/richard/.codex/skills/ui-animations/SKILL.md` |
| Plugin disponible | `plugin-management:plugin-management` | `/home/richard/.codex/plugins/cache/openai-curated-remote/plugin-management/0.1.0/skills/plugin-management/SKILL.md` |
| Plugin disponible | `sites:sites` | `/home/richard/.codex/plugins/cache/openai-curated-remote/sites/1.0.0/skills/sites/SKILL.md` |
| Plugin disponible | `work-pets:create-pet`, `work-pets:pets`, `work-pets:update-pet` | `/home/richard/.codex/plugins/cache/openai-curated-remote/work-pets/0.1.6/skills/<nombre-sin-prefijo>/SKILL.md` |
| Archivo presente, no anunciado como skill disponible | `review-agent` | `/home/richard/.codex/skills/.system/review-agent/SKILL.md` |
| Caché presente, no anunciada como disponible | 20 plantillas `artifact-template-*` | `/home/richard/.codex/plugins/cache/openai-curated-remote/openai-templates/0.1.1/skills/` |

Las plantillas encontradas son: project-kickoff, project-tracker, strategy-memorandum, team-alignment, business-review, operating-review, experiment-analysis, sales-pipeline, simple-light-mode, simple-dark-mode, legal-memorandum, three-statement-forecast, analytics-dashboard, design-report, minimal-letterhead, system-design, financial-budget, investment-committee-memo, market-trends-report y operating-calendar (todas con prefijo `artifact-template-`).

No había skills propias del proyecto ni AGENTS.md. No se encontraron especialistas instalados en PostgreSQL, FastAPI, testing, seguridad o Docker en las ubicaciones inspeccionadas. `frontend-design` y `animations` cubren diseño y movimiento, no ingeniería completa de Next.js/TypeScript. Los plugins sugeridos por la interfaz, incluido Codex Security, no están instalados y no deben contarse como skills disponibles.

## Cobertura y candidatas instalables

Se consultó el [catálogo OpenAI](https://github.com/openai/skills/tree/main/skills/.curated) mediante el script local revisado `skill-installer/scripts/list-skills.py --format json`. Su indicador `installed` solo revisa directorios directos de `$CODEX_HOME/skills`: marcó `openai-docs` como ausente aunque existe en `.system`. Se contrastó el resultado con el inventario local.

Los enlaces son fuentes primarias y apuntan a ramas mutables consultadas ese día, no a versiones aprobadas. «Instalable» significa que existe una skill publicada; aún requiere revisión integral de una revisión fija antes de instalarla. Se leyó el SKILL.md de las candidatas principales, no todo su árbol de dependencias.

| Especialidad | Instalada | Candidata y procedencia | Cobertura restante / decisión |
|---|---|---|---|
| PostgreSQL | Ninguna específica | [supabase-postgres-best-practices](https://github.com/supabase/agent-skills/blob/main/skills/supabase-postgres-best-practices/SKILL.md), Supabase | SQL, índices, conexiones, RLS y concurrencia. Aplicable a PostgreSQL sin adoptar Supabase. Revisar referencias; posible skill propia de migraciones Alembic y restauración si el flujo se repite. |
| FastAPI | Ninguna específica | [fastapi](https://github.com/fastapi/fastapi/blob/master/fastapi/.agents/skills/fastapi/SKILL.md), repositorio FastAPI | API/Pydantic/dependencias. Recomienda SQLModel sobre SQLAlchemy y funciones recientes: no adoptar esas preferencias contra §3.1. Adaptación pendiente; podría convenir una skill local FastAPI/SQLAlchemy/Alembic. |
| Next.js/TypeScript | `frontend-design`, `animations` como apoyo visual | [vercel-react-best-practices](https://github.com/vercel-labs/agent-skills/blob/main/skills/react-best-practices/SKILL.md), Vercel Labs | Rendimiento React/Next.js. No cubre por sí sola contratos TypeScript/API, permisos o offline. No autoriza migrar backend a Next.js ni hosting a Vercel. |
| Testing | Ninguna específica activa | [playwright](https://github.com/openai/skills/blob/main/skills/.curated/playwright/SKILL.md), OpenAI; también `playwright-interactive` y `gh-fix-ci` enumeradas en catálogo | `playwright` prioriza automatización CLI, no una suite `@playwright/test`. Hace falta una skill propia de estrategia Pytest/PostgreSQL/Playwright/CI si se quiere cobertura reproducible integral. Las otras dos solo fueron inventariadas, no auditadas. |
| Seguridad | Ninguna específica activa | [security-best-practices](https://github.com/openai/skills/blob/main/skills/.curated/security-best-practices/SKILL.md) y [security-threat-model](https://github.com/openai/skills/blob/main/skills/.curated/security-threat-model/SKILL.md), OpenAI | Revisiones Python/TS y amenazas. `security-ownership-map` también está en catálogo, pero no se revisó y requiere historial para aportar valor. Las skills propias enlazan permisos y privacidad del maestro, sin duplicar un manual de seguridad. |
| Docker/Compose | Ninguna específica | [docker-expert](https://github.com/sickn33/agentic-awesome-skills/blob/main/skills/docker-expert/SKILL.md), comunidad | No seleccionada para adoptar: propone build/run, herramientas adicionales y derivaciones a otros agentes; metadatos extra incompatibles con el validador local. Preferir crear una skill acotada de Compose, persistencia, health checks y operación según §10–11. |

No se afirma que estas sean todas las skills existentes en Internet. En el catálogo curado consultado no se encontró una skill especializada general para PostgreSQL, FastAPI o Docker; por eso se contrastaron fuentes externas. El paquete recomendado inicialmente es: las dos skills propias, candidatas de PostgreSQL/React/seguridad después de revisión, FastAPI con compatibilidad resuelta, y futuros flujos propios de pruebas y operación Docker. Las skills técnicas propuestas no fueron creadas en esta tarea.

## Revisión de procedencia y efectos secundarios

- **Herramientas locales usadas:** se leyeron `list-skills.py`, su dependencia `github_utils.py` y `quick_validate.py` antes de intentar ejecutarlas. El listado hace GET a GitHub y puede usar GH_TOKEN/GITHUB_TOKEN si están configurados; no instala archivos. El validador lee Markdown, usa PyYAML y no necesita red.
- **Supabase:** entrada instructiva con referencias SQL; revisar el árbol completo y notas específicas del proveedor antes de permitir cambios de esquema o RLS. No se ejecutó SQL.
- **FastAPI:** instrucciones con comandos de arranque, instalación y configuración de telemetría. Las preferencias de ORM y la compatibilidad de versiones requieren revisión explícita. No se arrancó servidor ni habilitó telemetría.
- **Vercel Labs:** instrucciones y reglas de rendimiento; evaluar aislamiento de cachés entre instituciones antes de reutilizar ejemplos. No se ejecutaron ejemplos ni se adoptaron dependencias sugeridas.
- **Playwright:** el wrapper usa `npx`, puede descargar/ejecutar paquetes; navegador, capturas y trazas pueden leer o escribir datos y generar tráfico. No se ejecutó ni descargó.
- **Seguridad OpenAI:** las entradas leídas generan informes y pueden orientar correcciones; threat-model pide validar supuestos con el usuario. Las referencias adicionales quedan pendientes de revisión antes de adopción.
- **Docker comunitaria:** inspección, construcción y ejecución de contenedores, con consumo de red/disco y posibles efectos de Dockerfiles. No se ejecutó. La revisión de su entrada no equivale a auditar scripts y referencias.

Para una futura instalación: resolver commit/tag inmutable, verificar autor y licencia, revisar todo el directorio y referencias transitivas, enumerar escrituras/red/secretos/comandos y compatibilidad con el maestro, registrar revisión y hashes, y solo entonces instalar dentro del alcance autorizado. No usar instaladores remotos, `npx ...@latest` ni `curl | sh` como sustituto de esta revisión. Volver a revisar al actualizar.

## Skills propias y descubrimiento

| Skill | Ubicación | Propósito |
|---|---|---|
| `evaluaciones-academicas` | [SKILL.md](../../.agents/skills/evaluaciones-academicas/SKILL.md) y [agents/openai.yaml](../../.agents/skills/evaluaciones-academicas/agents/openai.yaml) | Aplicar reglas de intentos, instrumentos, integridad institucional, auditoría e historial; orientar pruebas del dominio. |
| `sincronizacion-offline` | [SKILL.md](../../.agents/skills/sincronizacion-offline/SKILL.md) y [agents/openai.yaml](../../.agents/skills/sincronizacion-offline/agents/openai.yaml) | Guiar persistencia local, operaciones idempotentes, reintentos, conflictos y recuperación sin pérdida silenciosa. |

Cada skill enlaza el maestro mediante ruta relativa y números/títulos de sección; no copia tablas ni arquitectura. Son instrucciones propias sin scripts, dependencias, servidores MCP ni acceso externo implícito. AGENTS.md añade un enrutamiento breve.

La [documentación oficial de Codex](https://learn.chatgpt.com/docs/build-skills) establece `.agents/skills` como ubicación por proyecto. Las dos skills usan esa ruta y `allow_implicit_invocation: true`; nombre y descripción limitan su activación a su especialidad. No se modifica configuración global ni se duplican en `~/.codex/skills`.

Invocación explícita en una conversación de Codex abierta en este directorio (no en la terminal):

```text
Usa $evaluaciones-academicas para revisar cómo se corrige el segundo de tres intentos, sin implementar código.
Usa $sincronizacion-offline para revisar qué ocurre si se pierde la respuesta después del commit del servidor, sin implementar código.
```

También pueden seleccionarse automáticamente por su descripción. Verificar que aparecen en el selector de skills de una nueva sesión; si no se refrescan, reiniciar Codex. La presencia y estructura de archivos se verifica aquí, pero no se puede afirmar que se haya probado el selector de una futura sesión desde esta conversación.

## Procedimiento de validación

1. Revisar frontmatter, nombre igual al directorio, descripción precisa, metadatos y prompt con `$nombre`; invocación implícita habilitada y ausencia de dependencias/scripts inesperados.
2. Resolver enlaces relativos al maestro, a la otra skill y al inventario; comprobar que las secciones siguen existiendo. Si el maestro cambia, revisar trazabilidad en vez de copiarlo.
3. Ejecutar el validador incluido con skill-creator, después de revisar su código:

   ```bash
   python3 /home/richard/.codex/skills/.system/skill-creator/scripts/quick_validate.py .agents/skills/evaluaciones-academicas
   python3 /home/richard/.codex/skills/.system/skill-creator/scripts/quick_validate.py .agents/skills/sincronizacion-offline
   ```

   Requiere PyYAML. No instalar automáticamente una dependencia faltante.
4. Ensayar los prompts siguientes en una sesión nueva, en modo revisión sin cambios de aplicación. Comparar la respuesta con los criterios; registrar desviaciones y corregir únicamente la skill afectada.

| Solicitud de ensayo | Selección y comportamiento esperado |
|---|---|
| Corregir el segundo de tres intentos | Académica: conservar ID, aumentar versión, auditar y preservar los otros dos. |
| Usar otra versión de instrumento con el mismo número de intento | Académica: no eludir unicidad añadiendo instrumento a la clave; conflicto explícito. |
| Respuesta perdida tras commit y reenvío | Offline: misma clave/contenido, resultado durable, sin nueva evaluación ni revisión. |
| Editar localmente mientras se confirma un envío | Offline: no marcar la nueva edición como sincronizada por el ACK anterior. |
| Crear el mismo número desde dos dispositivos | Ambas: restricción central y resolución explícita sin renumeración silenciosa. |
| Pull con cambios locales o cursor vencido | Offline: conservar pendientes y no avanzar cursor antes del commit local. |
| Cambiar color de un botón o una imagen Docker | Ninguna de las dos por defecto. |
| Pedir revisar una skill sin implementar plataforma | No ejecutar Fase 0 ni activar instalaciones por leer el maestro. |

Estas pruebas de comportamiento del agente son distintas de las pruebas Pytest/PostgreSQL/Playwright descritas dentro de las skills para futuras funcionalidades.

## Registro de comprobaciones de esta entrega

- Documento maestro leído completo y alcance contrastado; SHA-256 inicial: `3d8f9c0bad26c15e213e30067854eb8a88099a967d24794cfaab6edaf1a29299`.
- Inventario de filesystem y catálogo de sesión contrastados con listado remoto; no se instalaron skills externas.
- `rg` y `python` no disponibles: se usaron find/sed y Python 3. `git status` informa que este directorio no es un repositorio Git utilizable; no se inventa un diff Git.
- PyYAML no está instalado: el validador oficial no puede completar. La validación alternativa comprueba el subconjunto de YAML usado, estructura, enlaces y límites sin instalar paquetes; no es un validador YAML general.
- Revisión documental de los escenarios anteriores: las instrucciones cubren los resultados esperados. No equivale a ejecutar ensayos independientes del agente ni pruebas de aplicación.
- Sin cambios al documento maestro, sin aplicación implementada, sin Docker/SQL/Node ejecutados y sin servicios externos activados.
- Validación alternativa ejecutada sobre ambas skills antes y después de copiarlas: nombres, frontmatter simple, metadatos UI, longitud de descripción, prompt, política implícita y secciones del maestro correctos. Comprobador temporal propio: `/tmp/validate-academic-skills.py` (no forma parte del proyecto; puede desaparecer al limpiar temporales).
- Todos los enlaces locales de AGENTS.md, inventario y skills resuelven a archivos existentes. Las cuatro copias finales coinciden byte a byte con los archivos validados; SHA-256 final del maestro coincide con el inicial.
- La copia a `.agents/skills` se completó mediante escalación autorizada del entorno, por estar protegida esa ubicación. No se cambiaron permisos ni configuración global. La comprobación del selector en una nueva sesión sigue pendiente.

## Archivos creados

1. `.agents/skills/evaluaciones-academicas/SKILL.md`
2. `.agents/skills/evaluaciones-academicas/agents/openai.yaml`
3. `.agents/skills/sincronizacion-offline/SKILL.md`
4. `.agents/skills/sincronizacion-offline/agents/openai.yaml`
5. `AGENTS.md`
6. `docs/skills/INVENTARIO-Y-VALIDACION.md`

No se modificó ningún archivo preexistente del proyecto. No se añadieron archivos de aplicación ni dependencias.
