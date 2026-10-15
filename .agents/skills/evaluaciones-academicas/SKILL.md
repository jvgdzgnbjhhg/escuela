---
name: evaluaciones-academicas
description: "Diseñar, implementar o revisar reglas de evaluaciones de esta plataforma: intentos independientes, instrumentos versionados, integridad institucional, correcciones, historial y auditoría. Usar al cambiar estos contratos o sus pruebas; no para estilos, despliegue o CRUD ajeno al dominio académico."
---

# Evaluaciones académicas

## Fuente y alcance

Lee el [documento maestro](../../../PLATAFORMA-EVALUACION-ACADEMICA-MASTER.md) completo antes de crear o modificar código (§16). Para revisiones focalizadas consulta §4.3–4.7 (actividades, instrumentos, evaluación e historial), §5 (permisos), §6.2–6.4 (relaciones e independencia), §7 (API), §9.4 (auditoría) y §12 (aceptación). El maestro es la fuente de reglas; esta skill guía su aplicación, no lo sustituye. Si cambia su numeración, busca los títulos. Si falta, detén decisiones de dominio y señala la referencia ausente.

Respeta el alcance del encargo actual; la primera tarea sugerida en el maestro no autoriza iniciar una fase. No cambies arquitectura ni inventes políticas académicas. Las decisiones no definidas se presentan como pendientes, sin convertirlas en requisitos implementados.

## Procedimiento

1. Identifica la operación: crear un intento, corregir uno existente, cambiar un instrumento, archivar o consultar/exportar. Traza cada regla afectada a una sección del maestro y a las capas existentes de API, dominio y persistencia.
2. Deriva institución y actor del contexto autenticado. Valida membresía, grupo, objeto y relaciones completas en backend; los UUID recibidos no demuestran autorización. Incluye relaciones indirectas como instrumento/versiones y actividad/instrumento. Aplica el mismo aislamiento a consultas, historial y exportaciones (§5, §6.2, §9.2).
3. Distingue identidad, número de intento y versión de edición. Crear produce otro ID; corregir conserva el ID e incrementa la versión. Conserva intentos anteriores y la versión del instrumento aplicada (§4.4–4.5, §6.4). No reemplaces el historial por un único resultado ni deduzcas promedios, mejor intento o nota final: esas políticas no están definidas.
4. Traduce §6.3 en restricciones reales y migraciones Alembic. En particular, la unicidad es por estudiante, actividad y número de intento, no por instrumento. Evita depender solo de comprobaciones previas: dos solicitudes pueden competir. Una colisión debe producir un conflicto comprensible; no renumeres ni sobrescribas silenciosamente (§8.4).
5. Para correcciones, verifica la versión leída y persiste el cambio junto con su auditoría en una transacción. No modifiques otras evaluaciones. Conserva autoría y fechas con su semántica: evaluador original, actor de la corrección y hora del servidor no son intercambiables (§4.5, §9.4).
6. Al archivar, revisa restricciones referenciales para conservar historia. Usa niveles y etiquetas de §4.5; comprueba fechas, matrículas y asociación del instrumento. Si una política temporal o de edición de registros archivados no está definida, haz explícita esa incertidumbre.
7. Si el cambio involucra cola local, reenvíos o reconciliación, aplica también [sincronizacion-offline](../sincronizacion-offline/SKILL.md). Esta skill conserva la responsabilidad sobre validez académica, incluso al procesar operaciones offline.

## Validación y entrega

Adapta las pruebas al cambio autorizado, usando datos ficticios. Para reglas persistidas usa Pytest e integración con PostgreSQL real (§12); una simulación del ORM no prueba restricciones ni carreras.

- Tres intentos: corregir el segundo conserva ID, incrementa versión, registra revisión y deja intactos primero y tercero.
- Instrumento usado: una nueva configuración no cambia el contenido aplicado a evaluaciones históricas.
- Dos instituciones: rechazar lectura/escritura y relaciones indirectas cruzadas, también en exportaciones; probar docente sin asignación y permisos revocados.
- Dos creaciones con el mismo número y dos correcciones con la misma versión: conflicto sin duplicados ni pérdida silenciosa.
- Datos inválidos: sin evaluación ni revisión parcial; archivar conserva el historial.

Entrega trazabilidad regla → cambio → prueba, resultados realmente ejecutados y decisiones pendientes. Una revisión documental no demuestra que el dominio esté implementado ni listo para producción (§17).
