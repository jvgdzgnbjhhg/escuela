---
name: sincronizacion-offline
description: "Diseñar, implementar, depurar o revisar sincronización offline de esta plataforma con IndexedDB: cola persistente, idempotencia, reintentos, conflictos, cursor y recuperación tras cierres o respuestas perdidas. Usar en PWA y contratos sync/push o sync/pull; no para caché visual o redes sin datos pendientes."
---

# Sincronización offline

## Fuente y alcance

Lee el [documento maestro](../../../PLATAFORMA-EVALUACION-ACADEMICA-MASTER.md) completo antes de crear o modificar código (§16). Consulta especialmente §8.1–8.5 (flujo y conflictos), §5 y §9.2–9.3 (autorización y protección local), §6.3–6.4 (identidad e intentos), §7 (API), §10 (límites de recuperación) y §12 (aceptación). PostgreSQL sigue siendo la fuente oficial; IndexedDB conserva trabajo local pendiente.

La skill indica comprobaciones de fiabilidad, no fija un nuevo esquema, biblioteca o protocolo. Revisa contratos y ADR existentes antes de proponer detalles no especificados (formato de cursor, plazos de reintento o retención de idempotencia). Documenta propuestas como pendientes de decisión. No inicies una fase por leer el maestro. Si falta la fuente, señala el bloqueo antes de decidir reglas.

## Guardado local y cola

- Identifica el contexto usuario/institución y los datos autorizados descargados. Aísla caché, cola y cursor por contexto; un cambio de cuenta no puede enviar la cola anterior con otra identidad.
- Distingue UUID de evaluación, identificador de operación y versión base. Un reenvío conserva operación y contenido; una edición posterior es otra operación. Nunca generes una nueva clave solo porque se perdió la respuesta.
- Guarda evaluación local y operación pendiente en una transacción IndexedDB y espera su confirmación antes de anunciar guardado local. Ante cuota agotada o aborto, muestra el fallo sin prometer persistencia.
- Conserva orden/dependencias por evaluación (crear antes de editar). Si se edita mientras hay un envío, la confirmación de una operación anterior no puede marcar los cambios posteriores como sincronizados.
- Usa los estados de §8.2: LOCAL_PENDING al guardar, SYNCING durante envío, SYNCED solo tras confirmación inequívoca, CONFLICT para resolución explícita y FAILED para fallos que requieren atención. Conserva el contenido pendiente al fallar.

## Envío e idempotencia

1. Inspecciona cómo la API autentica y autoriza cada operación, incluso repetida; no devuelvas resultados de otro usuario/institución desde una caché de idempotencia.
2. Define en el contrato el alcance de la clave, la detección de reutilización con contenido diferente y el resultado estable de una repetición. La reserva/deduplicación, el cambio académico, la revisión y el resultado durable deben coordinarse transaccionalmente en PostgreSQL para resistir solicitudes simultáneas y caídas.
3. Para una repetición ya confirmada, devuelve su resultado autorizado sin repetir efectos ni auditoría de la mutación; no ejecutes primero una nueva edición contra su antigua versión. Para una operación nueva, verifica la versión base y las reglas de [evaluaciones-academicas](../evaluaciones-academicas/SKILL.md).
4. Procesa respuestas por operación. Un HTTP exitoso de lote no confirma elementos ausentes o fallidos. Ante resultado desconocido o respuesta perdida, conserva la operación y consulta/reenvía con la misma clave.
5. Revisa retención de claves frente al tiempo offline permitido. Si una clave ha expirado, no asumas que el cambio nunca ocurrió: reconcilia identidad y estado antes de repetir efectos. No prometas entrega «exactamente una vez» por usar UUID.

## Reintentos y conflictos

- Red interrumpida, timeout y fallos transitorios: espera progresiva con variación aleatoria y límite; respeta Retry-After cuando exista. Persiste el próximo intento y evita ciclos intensivos. Al agotar el presupuesto acordado, deja un error visible y reintento manual sin borrar datos.
- Sesión vencida: pausa hasta reautenticar el mismo contexto. Permiso revocado o validación permanente: detén el reintento automático y explica el rechazo. No reenvíes indiscriminadamente todos los errores 4xx.
- Versión obsoleta o número de intento ocupado: conserva versión base, cambio local y estado remoto autorizado para una resolución explícita. No uses última escritura gana, ni renumeración automática (§8.4).
- Una resolución que cambie el contenido genera una nueva operación con versión actual, vinculada a la anterior para diagnóstico; un simple reenvío mantiene su identidad. No descartes la operación conflictiva antes de conservar la resolución.

## Descarga y recuperación

- Aplica cada página de cambios y su cursor en una misma transacción local; avanza solo después de persistirla. Repetir una página no debe duplicar ni revertir datos más nuevos. Un pull no puede sobrescribir cambios locales pendientes: conserva la base remota por separado o detecta conflicto según el contrato.
- Documenta tratamiento de archivados, permisos revocados, cursor inválido/expirado y resincronización completa sin destruir la cola. No inventes borrados físicos ni un formato de cursor nuevo si ya existe contrato.
- Recupera operaciones que quedaron SYNCING tras cierre/caída; coordina pestañas y Service Worker para evitar emisores concurrentes innecesarios, manteniendo idempotencia en servidor como garantía final. No consideres navigator.onLine prueba de disponibilidad de la API.
- Sincroniza al abrir y al recuperar conexión, sin depender exclusivamente de Background Sync. Migra IndexedDB sin borrar pendientes; trata bloqueo por otra pestaña y fallo de migración de forma visible.
- Antes de limpiar al cerrar sesión, informa pendientes y solicita confirmación (§8.5). No guardes credenciales en IndexedDB/localStorage; minimiza datos y diagnósticos. El borrado del navegador o pérdida del dispositivo puede hacer irrecuperable lo no sincronizado: los respaldos centrales no lo cubren (§10).

## Validación y entrega

Usa datos ficticios, Pytest/PostgreSQL real para atomicidad y carreras, y Playwright en navegador real para persistencia IndexedDB y recuperación. Prueba los casos afectados y vincúlalos a §12:

| Escenario | Resultado observable |
|---|---|
| Guardar offline, cerrar y reabrir | Evaluación y cola sobreviven, sin falsa confirmación central |
| Commit remoto con respuesta perdida; doble envío concurrente | Un efecto académico, misma respuesta confirmada y sin revisión duplicada |
| Misma clave con otro contenido o contexto | Rechazo seguro, sin fuga de datos |
| Lote parcialmente confirmado o edición durante envío | Solo se confirman operaciones exactas; siguen visibles cambios posteriores |
| Ediciones concurrentes y colisión de número de intento | Conflicto visible, historial intacto y resolución explícita |
| 401, revocación, validación, 429 y error transitorio | Pausa/rechazo/reintento según causa, sin bucle ni pérdida |
| Caída durante pull, cursor vencido, varias pestañas | Recuperación sin saltar cambios ni borrar pendientes |
| Cuota, migración fallida y logout con pendientes | Fallo visible; no se promete guardado ni se limpia sin confirmación |

Entrega estados/transiciones afectados, decisiones de contrato pendientes y resultados ejecutados. Distingue revisión de diseño de pruebas de funcionamiento; no declares sincronización fiable sin evidencia.
