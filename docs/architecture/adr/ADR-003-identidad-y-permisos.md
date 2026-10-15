# ADR 003 — Identidad, contexto institucional y permisos

Estado: implementado para desarrollo en Fase 1. Fuente de alcance: [maestro](../../../PLATAFORMA-EVALUACION-ACADEMICA-MASTER.md), §§5, 6, 9 y 13. No cambia el monolito ni introduce un proveedor externo.

Se utilizan cuentas propias con Argon2id y sesiones opacas persistidas en PostgreSQL. El servidor conserva SHA-256 del token aleatorio, con caducidad absoluta de 8 horas e inactividad máxima de 30 minutos. La cookie `ea_session` es HttpOnly, SameSite=Lax y Secure en producción. Cambiar contraseña revoca todas las sesiones; cerrar sesión elimina la actual. La primera cuenta se crea mediante consola interactiva, sin contraseña en argumentos ni credenciales predeterminadas. No existe registro público.

Next.js reenvía únicamente rutas y cabeceras permitidas hacia FastAPI. Las escrituras requieren un origen de la lista explícita del backend y, salvo login, token CSRF derivado de la sesión, recibido con `/auth/me` y mantenido en memoria. Ningún token se guarda en localStorage/IndexedDB. Respuestas privadas usan `Cache-Control: no-store`. Hay límite de cuerpo de 64 KiB y presupuesto de login persistente de 8 intentos por correo y 120 por dirección del cliente durante ventanas de 15 minutos. Tras el proxy todos los navegadores comparten su dirección de origen: antes de un despliegue real se debe resolver la identificación confiable del cliente y calibrar límites sin confiar en X-Forwarded-For del navegador.

Referencias consultadas: [OWASP Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html), [OWASP CSRF](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html), [API de Argon2](https://argon2-cffi.readthedocs.io/en/stable/api.html).

## Contexto y alcance de los roles

Cada petición académica exige `X-Institution-ID` y verifica una membresía vigente del usuario en esa institución. El selector del navegador no constituye autorización. Los roles de lectura institucional representan una concesión de lectura al conjunto del centro; deben asignarse deliberadamente por un administrador. Las autorizaciones más granulares de evaluaciones se definirán al implementar ese dominio.

| Rol | Lectura académica | Escrituras de estructura y matrícula | Equipo y permisos | Auditoría |
|---|---|---|---|---|
| ADMIN | Su institución | Sí | Sí | Sí |
| COORDINATOR | Su institución | No | No | Sí |
| VIEWER | Su institución | No | No | Sí |
| TEACHER | Secciones asignadas; estudiantes con matrícula vigente; matrículas de esas secciones | No | No | No |
| TECHNICAL | No | No | No | No |

Las membresías se comprueban de nuevo en cada petición. Revocar una membresía docente o cambiar su rol archiva sus asignaciones activas. No se puede quitar el último administrador activo. Cambios de membresía y entidades usan versión optimista; un conflicto devuelve 409, sin sobrescribir silenciosamente.

## Persistencia e integridad

Las claves foráneas compuestas incluyen institución para impedir referencias entre centros incluso cuando se escribe SQL directamente. Fechas y estados tienen restricciones CHECK y las relaciones tienen índices y unicidad. Los solapamientos de matrícula se validan transaccionalmente en el servicio; no hay una restricción de exclusión de intervalos en PostgreSQL. Las escrituras académicas toman primero un bloqueo de institución y después los objetos: evita carreras entre crear, archivar, revocar y trasladar. Esto serializa escrituras de un mismo centro; medir y refinar antes de cargas elevadas.

Una matrícula sin fecha final termina efectivamente al finalizar su año escolar. El traslado cierra la matrícula anterior el día previo y crea otra en una única transacción. Si el traslado es futuro, la matrícula anterior conserva estado activo y acceso docente hasta su fecha final. El estado activo no sustituye la comprobación de vigencia por fechas. No se cambian las relaciones de una sección/matrícula/asignación existente ni las fechas de un año que ya tiene secciones. Archivar padres exige archivar primero sus hijos activos; no hay borrado HTTP de historia.

Las mutaciones académicas escriben auditoría en la misma transacción, con actor, objeto y valores anterior/posterior, sin hashes de contraseña ni tokens. La API usa `evaluacion_app`, distinta del propietario de migraciones: no puede borrar entidades, modificar/eliminar auditoría ni ejecutar DDL. RLS se evaluó como segunda barrera, pero no está implementada: el aislamiento de lectura depende de los filtros y permisos del backend, probados con dos centros. [Documentación PostgreSQL sobre RLS](https://www.postgresql.org/docs/17/ddl-rowsecurity.html).

## Límites de esta entrega

Pendientes para el endurecimiento de producción: MFA, recuperación segura de cuentas, HTTPS y orígenes reales, limpieza programada de sesiones/presupuestos caducados, auditoría de eventos de identidad, calibración de rate limits, revisión de RLS y pruebas de carga. No se afirma que la autenticación esté certificada ni lista para exponer datos reales de menores. Los controles futuros no cambian los criterios funcionales de salida de Fase 1.
