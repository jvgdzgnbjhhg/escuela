# Plataforma de Evaluación Académica
## Documento maestro de arquitectura, alcance y plan de implementación

**Estado:** Propuesta inicial para desarrollo  
**Idioma de la plataforma:** Español  
**Tipo de sistema:** Aplicación web multiinstitucional, multiusuario, con soporte offline  
**Documento:** `PLATAFORMA-EVALUACION-ACADEMICA-MASTER.md`

---

## 1. Propósito del proyecto

Construir una plataforma web para que centros educativos administren estudiantes, cursos, secciones, docentes, períodos académicos, semanas, actividades, instrumentos de evaluación y evaluaciones individuales.

El sistema debe permitir consultar el historial completo de cada estudiante y los resultados de todos los estudiantes de una actividad. Cada estudiante puede tener varios intentos de evaluación en una misma actividad. Los intentos deben conservarse de forma independiente.

La plataforma debe funcionar en línea y ofrecer un modo sin conexión para registrar evaluaciones de datos previamente sincronizados. Al recuperar la conexión, debe sincronizar las operaciones pendientes de forma segura, evitando duplicados y pérdida silenciosa de cambios.

No se debe construir solamente una interfaz visual ni utilizar almacenamiento temporal como fuente oficial de datos. La información central debe persistir en una base de datos real.

## 2. Objetivos y principios no negociables

1. La información académica persiste en PostgreSQL.
2. Cada evaluación pertenece a un estudiante, una actividad, un instrumento y un autor autorizado.
3. Se permiten múltiples intentos independientes por estudiante y actividad.
4. Editar un intento no modifica los demás intentos.
5. Los datos de una institución no son accesibles desde otra institución sin autorización explícita.
6. Las autorizaciones se validan en el backend, no solo en la interfaz.
7. La aplicación diferencia claramente los registros locales pendientes de sincronización de los registros confirmados por el servidor.
8. Los reintentos de sincronización no crean duplicados.
9. Los conflictos de edición se detectan y no se resuelven sobrescribiendo datos silenciosamente.
10. Los cambios relevantes quedan auditados.
11. Se implementan respaldos y pruebas de restauración.
12. El sistema debe ser sencillo y rápido para utilizarse durante las clases.
13. Las decisiones importantes de arquitectura se documentan como ADR.
14. No se debe afirmar que una funcionalidad está terminada hasta que esté implementada y probada.

---

## 3. Arquitectura recomendada

Utilizar un **monolito modular** inicialmente. No introducir microservicios durante el MVP sin una necesidad demostrada.

### 3.1 Stack tecnológico

| Componente | Tecnología | Responsabilidad |
|---|---|---|
| Frontend | Next.js, React, TypeScript | Interfaz web, navegación y formularios |
| Estilos | Tailwind CSS y componentes accesibles | Interfaz consistente y adaptable |
| Formularios | React Hook Form y Zod | Validación en cliente |
| PWA | Web App Manifest y Service Worker | Instalación y recursos disponibles offline |
| Almacenamiento local | IndexedDB | Datos descargados y cola de operaciones offline |
| Backend | Python y FastAPI | API, permisos y lógica de negocio |
| Validación backend | Pydantic | Validación de solicitudes y respuestas |
| Acceso a datos | SQLAlchemy | ORM y transacciones |
| Migraciones | Alembic | Versionado del esquema de base de datos |
| Base central | PostgreSQL | Fuente oficial de datos |
| Autenticación | Sesiones seguras o proveedor OIDC | Identidad y sesiones |
| Exportación Excel | openpyxl | Exportación de evaluaciones e informes |
| Pruebas backend | Pytest | Pruebas unitarias e integración |
| Pruebas E2E | Playwright | Pruebas del navegador y flujos completos |
| Contenedores | Docker y Docker Compose | Entorno reproducible |
| CI/CD | GitHub Actions | Lint, pruebas y despliegue controlado |

Elegir versiones estables y compatibles al iniciar el repositorio, fijar las dependencias y documentar la versión exacta en los archivos de dependencias. No utilizar versiones flotantes en producción.

### 3.2 Componentes

1. **Frontend PWA**
   - Interfaz responsiva para computadora, tableta y móvil.
   - Panel principal.
   - Gestión de estudiantes y cursos.
   - Registro de evaluaciones.
   - Historial y reportes.
   - Estado de conexión y sincronización.
   - Funciones offline explícitas.

2. **API FastAPI**
   - Autenticación y autorización.
   - Gestión institucional.
   - Gestión académica.
   - Motor de evaluación.
   - Historial y consultas.
   - Sincronización.
   - Exportaciones.
   - Auditoría.

3. **PostgreSQL**
   - Persistencia central.
   - Relaciones, claves foráneas, restricciones e índices.
   - Transacciones.
   - Aislamiento institucional.
   - Auditoría de cambios y versiones relevantes.

4. **Servicios operativos**
   - Copias de seguridad.
   - Monitorización y alertas.
   - Gestión segura de secretos.
   - Almacenamiento privado, si posteriormente se agregan archivos.
   - CI/CD.

### 3.3 Estructura sugerida del repositorio

```text
plataforma-evaluacion-academica/
├── AGENTS.md
├── README.md
├── PLATAFORMA-EVALUACION-ACADEMICA-MASTER.md
├── docker-compose.yml
├── .env.example
├── .gitignore
├── frontend/
│   ├── package.json
│   ├── next.config.ts
│   ├── public/
│   └── src/
│       ├── app/
│       ├── components/
│       ├── features/
│       │   ├── auth/
│       │   ├── institutions/
│       │   ├── students/
│       │   ├── academics/
│       │   ├── assessments/
│       │   ├── reports/
│       │   └── sync/
│       ├── lib/
│       └── offline/
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── repositories/
│   │   ├── services/
│   │   └── tests/
│   └── tests/
├── docs/
│   ├── architecture/
│   │   ├── overview.md
│   │   └── adr/
│   ├── api/
│   ├── security/
│   ├── operations/
│   └── testing/
└── scripts/
```

La estructura puede ajustarse durante la implementación, pero cualquier cambio debe mantener una separación clara entre frontend, backend, dominio, persistencia y documentación.

---

## 4. Alcance funcional del MVP

### 4.1 Administración institucional

- Crear y administrar instituciones.
- Gestionar usuarios y membresías.
- Asignar roles y permisos.
- Configurar años escolares y períodos académicos.
- Crear cursos y secciones.
- Asignar docentes a secciones y materias.
- Aislar los datos por institución.

### 4.2 Gestión de estudiantes

- Registrar nombre completo y código institucional.
- Editar datos permitidos.
- Consultar ficha individual.
- Buscar por nombre o código.
- Filtrar por curso, sección, período y estado.
- Gestionar matrícula y traslados entre secciones.
- Archivar estudiantes sin borrar su historial académico.

### 4.3 Semanas y actividades

- Crear períodos académicos y semanas.
- Asignar número, fechas y descripción a cada semana.
- Crear actividades con número, título, descripción y estado.
- Asociar uno o varios instrumentos a una actividad.
- Permitir editar y archivar actividades con controles de integridad.

### 4.4 Instrumentos de evaluación

- Registrar nombre y tipo del instrumento.
- Permitir rúbrica, lista de cotejo u otros tipos configurables.
- Asociar instrumentos a actividades.
- Versionar la configuración de instrumentos cuando cambie después de usarse.
- Cada evaluación debe conservar la versión del instrumento realmente aplicada.

### 4.5 Registro de evaluaciones

Cada intento debe incluir, como mínimo:

- Identificador único.
- Institución.
- Estudiante.
- Actividad.
- Instrumento y versión del instrumento.
- Número de intento.
- Nivel de desempeño.
- Observaciones individuales.
- Docente que evalúa.
- Fecha y hora de evaluación.
- Fecha de creación y última modificación.
- Versión de edición.
- Estado de sincronización en el cliente local, no como sustituto del estado central.

Niveles de desempeño iniciales:

- `ACHIEVED` — Logrado.
- `IN_PROGRESS` — En proceso.
- `BEGINNING` — En inicio.

Las etiquetas visibles en la interfaz deben estar en español.

Permitir crear varios intentos en la misma actividad. Cada intento nuevo crea un registro nuevo. Editar un intento existente conserva su ID y no modifica otros intentos.

### 4.6 Historial y consultas

- Historial cronológico por estudiante.
- Todos los intentos de una actividad.
- Filtros por institución, período, curso, sección, docente, semana, actividad y nivel.
- Paginación en consultas grandes.
- Exportación de resultados a Excel.
- Mostrar claramente quién realizó la evaluación y cuándo.
- Diferenciar fecha de evaluación y fecha de sincronización.

### 4.7 Experiencia de evaluación rápida

Flujo recomendado:

1. El docente selecciona institución/contexto, curso o sección.
2. Selecciona semana y actividad.
3. Busca o selecciona al estudiante.
4. Selecciona instrumento y número de intento, o solicita crear el siguiente intento.
5. Selecciona nivel de desempeño.
6. Escribe observaciones.
7. Guarda y recibe confirmación clara.
8. Pasa al siguiente estudiante sin perder el registro anterior.

La interfaz debe evitar el envío doble accidental, mostrar errores de validación comprensibles y distinguir “guardado localmente” de “sincronizado con el servidor”.

---

## 5. Roles y autorización

Roles iniciales:

| Rol | Permisos previstos |
|---|---|
| Administrador institucional | Configuración, usuarios, cursos, matrícula y reportes de su institución |
| Coordinador académico | Supervisión de grupos y evaluaciones autorizadas |
| Docente | Acceso a sus grupos asignados, actividades y evaluaciones autorizadas |
| Consulta/auditoría | Lectura de información expresamente autorizada |
| Administrador técnico | Operación técnica; sin acceso rutinario al contenido académico |

Reglas:

- Todos los permisos se verifican en el backend en cada operación.
- No confiar en IDs enviados por el cliente.
- No considerar que ocultar un botón equivale a autorizar o denegar una operación.
- Un usuario que pertenece a más de una institución debe seleccionar un contexto institucional válido.
- Cada consulta y modificación se limita al tenant/institución autorizada.
- Evaluar PostgreSQL Row-Level Security (RLS) como defensa adicional.
- Los permisos offline solo pueden basarse en datos y autorizaciones previamente sincronizados; la revocación se aplicará cuando el dispositivo vuelva a conectarse.

---

## 6. Modelo de datos relacional

El siguiente es el modelo lógico inicial. Ajustar tipos, índices y restricciones durante las migraciones, sin eliminar las reglas de integridad.

### 6.1 Tablas

| Tabla | Campos principales |
|---|---|
| `institutions` | `id`, `name`, `status`, `created_at` |
| `users` | `id`, `email`, `password_hash` o referencia de identidad externa, `status`, timestamps |
| `institution_memberships` | `id`, `institution_id`, `user_id`, `role`, `status` |
| `academic_years` | `id`, `institution_id`, `name`, `start_date`, `end_date`, `status` |
| `courses` | `id`, `institution_id`, `name`, `grade_level`, `status` |
| `sections` | `id`, `institution_id`, `course_id`, `academic_year_id`, `name`, `status` |
| `students` | `id`, `institution_id`, `student_code`, `full_name`, `status`, timestamps |
| `enrollments` | `id`, `institution_id`, `student_id`, `section_id`, `start_date`, `end_date`, `status` |
| `teaching_assignments` | `id`, `institution_id`, `teacher_id`, `section_id`, `subject`, `academic_year_id`, `status` |
| `academic_periods` | `id`, `institution_id`, `academic_year_id`, `name`, `start_date`, `end_date` |
| `weeks` | `id`, `institution_id`, `academic_period_id`, `week_number`, `start_date`, `end_date` |
| `activities` | `id`, `institution_id`, `week_id`, `activity_number`, `title`, `description`, `status` |
| `assessment_instruments` | `id`, `institution_id`, `name`, `type`, `configuration`, `status` |
| `instrument_versions` | `id`, `instrument_id`, `version_number`, `configuration_snapshot`, `created_by`, `created_at` |
| `activity_instruments` | `id`, `activity_id`, `instrument_version_id`, `is_default` |
| `evaluations` | `id`, `institution_id`, `student_id`, `activity_id`, `instrument_version_id`, `attempt_number`, `performance_level`, `observations`, `evaluated_by`, `evaluated_at`, `version`, timestamps |
| `evaluation_revisions` | `id`, `evaluation_id`, `revision_number`, `previous_snapshot`, `new_snapshot`, `changed_by`, `changed_at`, `reason` |
| `audit_events` | `id`, `institution_id`, `actor_id`, `entity_type`, `entity_id`, `action`, `metadata`, `occurred_at` |

Las tablas pueden incorporar `created_at`, `updated_at`, `archived_at` y otras columnas cuando sean pertinentes. No almacenar secretos en `audit_events`.

### 6.2 Relaciones esenciales

- Una institución tiene usuarios asociados mediante membresías.
- Una institución contiene cursos, años académicos, estudiantes y períodos.
- Una sección pertenece a un curso y un año escolar.
- La matrícula vincula estudiantes y secciones a lo largo del tiempo.
- Las asignaciones vinculan docentes con secciones y materias.
- Un período contiene semanas; una semana contiene actividades.
- Una actividad puede permitir uno o varios instrumentos.
- Una evaluación pertenece a un estudiante, una actividad, una versión de instrumento y un usuario evaluador.
- Una evaluación puede tener múltiples revisiones de auditoría.
- Cada entidad académica debe quedar limitada a la institución correcta.

### 6.3 UUID, integridad y restricciones

Utilizar UUID como identificadores primarios, especialmente para evaluaciones creadas offline.

Restricciones iniciales:

- `UNIQUE (institution_id, student_code)` para códigos de estudiantes, si la institución usa códigos.
- `UNIQUE (course_id, academic_year_id, name)` o una regla equivalente para secciones.
- `UNIQUE (academic_period_id, week_number)` para semanas.
- `UNIQUE (week_id, activity_number)` para numeración de actividades dentro de una semana.
- `UNIQUE (student_id, activity_id, attempt_number)` para evitar repetir el número de intento.
- `CHECK (attempt_number > 0)`.
- `CHECK` para niveles de desempeño válidos, o un tipo enum controlado por migraciones.
- Claves foráneas y restricciones para impedir relaciones entre instituciones diferentes.
- Índices para historiales por estudiante, consultas por actividad, institución, curso y fechas.
- Restricciones para evitar fechas y matrículas incoherentes.

Si la política permite varias evaluaciones paralelas para una misma actividad, deberán tener números de intento distintos o un concepto explícito de sesión/instancia. No introducir duplicados sin semántica.

### 6.4 Regla de independencia de intentos

Ejemplo: un estudiante tiene tres intentos en una actividad.

| Intento | Nivel | Observación |
|---|---|---|
| 1 | En inicio | Necesita apoyo para completar la tarea |
| 2 | En proceso | Reconoce los conceptos con orientación |
| 3 | Logrado | Resuelve la actividad de forma autónoma |

Cada intento tiene su propio `id`. Corregir el segundo no modifica el primero ni el tercero. El historial debe mostrar los tres en orden cronológico o por número de intento.

La edición mantiene el mismo ID y aumenta la versión del registro. Las modificaciones importantes se guardan en `evaluation_revisions` y/o `audit_events`.

No borrar evaluaciones en cascada al archivar estudiantes, actividades, instrumentos o secciones. Utilizar archivado y restricciones referenciales.

---

## 7. API propuesta

Versionar todas las rutas bajo `/api/v1`. Los siguientes endpoints son una guía inicial; especificar contratos Pydantic, errores, permisos y paginación durante la implementación.

| Dominio | Rutas propuestas |
|---|---|
| Autenticación | `/api/v1/auth/login`, `/auth/logout`, `/auth/me` |
| Instituciones | `/api/v1/institutions`, `/api/v1/institutions/{id}/members` |
| Estudiantes | `/api/v1/students`, `/api/v1/students/{id}` |
| Cursos/secciones | `/api/v1/courses`, `/api/v1/sections` |
| Matrícula | `/api/v1/enrollments` |
| Asignaciones docentes | `/api/v1/teaching-assignments` |
| Períodos/semanas | `/api/v1/academic-periods`, `/api/v1/weeks` |
| Actividades | `/api/v1/activities`, `/api/v1/activities/{id}` |
| Instrumentos | `/api/v1/instruments`, `/api/v1/activities/{id}/instruments` |
| Evaluaciones | `/api/v1/evaluations`, `/api/v1/evaluations/{id}` |
| Intentos | `/api/v1/students/{student_id}/activities/{activity_id}/attempts` |
| Historial | `/api/v1/students/{id}/assessment-history` |
| Consulta por actividad | `/api/v1/activities/{id}/evaluations` |
| Sincronización | `/api/v1/sync/push`, `/api/v1/sync/pull` |
| Exportaciones | `/api/v1/exports/evaluations` |
| Auditoría | `/api/v1/audit-events` |

La API debe incluir:

- Esquemas de entrada y salida explícitos.
- Paginación y filtros para consultas.
- Errores HTTP coherentes y mensajes seguros.
- Autorización a nivel de institución y objeto.
- Transacciones para operaciones relacionadas.
- Límites de tamaño para solicitudes y lotes de sincronización.
- Idempotencia en las operaciones que se pueden reintentar.
- Documentación OpenAPI generada por FastAPI, protegida si expone información interna.

---

## 8. Modo offline y sincronización

### 8.1 Objetivo

La aplicación debe permitir registrar evaluaciones sin conexión para los grupos y actividades sincronizados previamente. Al regresar Internet, los datos deben enviarse al servidor sin duplicados y con detección de conflictos.

### 8.2 Componentes offline

- PWA con Web App Manifest.
- Service Worker para almacenar recursos de la interfaz.
- IndexedDB para los datos descargados y las operaciones pendientes.
- Cola persistente de operaciones.
- UUID generado en cliente para nuevas evaluaciones.
- Identificador de operación/idempotencia.
- Cursor de sincronización para descargar cambios.
- Estados visibles: `LOCAL_PENDING`, `SYNCING`, `SYNCED`, `CONFLICT`, `FAILED`.
- Reintentos con espera progresiva.
- Mensajes claros de error y opción de reintentar.
- Herramienta de diagnóstico de operaciones pendientes.

Estos estados son del cliente; no deben confundirse con el estado de la evaluación central.

### 8.3 Flujo

1. Usuario autenticado y autorizado sincroniza grupos, estudiantes y actividades necesarios.
2. Sin Internet, la aplicación usa solo los datos descargados.
3. El docente crea una evaluación y el cliente genera un UUID.
4. La evaluación se guarda en IndexedDB antes de confirmar el guardado local.
5. Se agrega una operación a la cola con identificador idempotente y datos mínimos necesarios.
6. Al detectar conexión, el cliente envía operaciones por lotes.
7. El backend valida autorización, tenant, relaciones, instrumento, número de intento y datos.
8. El backend procesa cada operación de forma idempotente y transaccional.
9. La API responde con el resultado de cada operación, no solo con un resultado global ambiguo.
10. El cliente marca como sincronizadas únicamente las operaciones confirmadas.
11. Los errores recuperables se reintentan; los conflictos requieren intervención.
12. El cliente descarga los cambios nuevos usando un cursor o versión de sincronización.

### 8.4 Concurrencia y conflictos

No aplicar una política de “última escritura gana” silenciosa.

Para editar una evaluación, enviar la versión que el cliente leyó. El backend compara esa versión con la versión actual. Si difieren, responder con conflicto (por ejemplo, HTTP 409), incluyendo información segura para resolverlo.

Las evaluaciones nuevas son registros separados; los cambios posteriores a una evaluación existente requieren control de versión.

Si dos dispositivos crean un intento simultáneamente, la restricción única del servidor impedirá números duplicados. La API debe devolver un conflicto comprensible y permitir que el usuario asigne el siguiente número disponible.

### 8.5 Limitaciones y protección local

- Solo los datos previamente descargados estarán disponibles offline.
- No afirmar que una evaluación está sincronizada hasta recibir confirmación del servidor.
- Limpiar los datos locales al cerrar sesión debe considerar cambios pendientes y pedir confirmación.
- No almacenar contraseñas ni tokens de sesión de larga duración en `localStorage` o IndexedDB.
- Minimizar los datos académicos guardados en el dispositivo.
- Recomendar cifrado del disco, bloqueo de pantalla y cuentas separadas en los dispositivos.
- Documentar que borrar los datos del navegador o perder el dispositivo puede destruir cambios locales no sincronizados.
- Mostrar advertencias sobre la cantidad y antigüedad de los registros pendientes.
- La sincronización en segundo plano no está garantizada por todos los navegadores; también debe existir sincronización al abrir la aplicación o cuando vuelva la conexión.

---

## 9. Seguridad y privacidad

### 9.1 Autenticación

- Utilizar Argon2id para hashes de contraseña si se administra autenticación propia, o un proveedor OIDC confiable.
- Implementar sesiones seguras con cookies `HttpOnly`, `Secure`, `SameSite` cuando se use autenticación por cookie.
- Protección contra fuerza bruta y abuso de endpoints.
- Recuperación de contraseña con tokens de un solo uso y vencimiento.
- MFA para administradores y, cuando sea posible, otros usuarios.
- Cierre y revocación de sesiones.
- No registrar contraseñas, tokens ni secretos en logs.

### 9.2 Autorización y aislamiento

- Verificar permisos en el backend para cada lectura y escritura.
- Limitar cada operación por institución, rol, grupo y objeto.
- Considerar Row-Level Security de PostgreSQL como defensa adicional.
- No confiar en `institution_id`, `user_id`, `student_id` u otros identificadores proporcionados por el cliente sin verificarlos.
- Usar consultas parametrizadas/ORM y validación estricta.
- Proteger contra CSRF si se utilizan cookies de sesión.
- Configurar CORS con orígenes permitidos explícitos.
- Aplicar límites de tasa y tamaños máximos de solicitud.

### 9.3 Datos locales

- Guardar únicamente los datos requeridos para la tarea offline.
- No persistir credenciales en almacenamiento del navegador.
- Aplicar política de retención local y eliminación cuando corresponda.
- Informar al usuario si tiene operaciones pendientes antes de cerrar sesión.
- No considerar IndexedDB como almacenamiento cifrado por defecto.
- Definir procedimiento de pérdida o retirada de un dispositivo.
- La revocación de acceso no puede comunicarse a un dispositivo completamente desconectado; minimizar el alcance y la duración de datos offline.

### 9.4 Auditoría

Registrar, como mínimo:

- Usuario que realizó la operación.
- Institución.
- Tipo e ID de entidad.
- Acción realizada.
- Fecha/hora del servidor y, cuando sea relevante, fecha declarada del evento offline.
- Resultado de la operación.
- Cambios anteriores y nuevos para correcciones relevantes, minimizando la exposición de datos.

Restringir acceso a los eventos de auditoría. No permitir que un usuario normal los modifique desde la interfaz.

### 9.5 Protección de datos

- HTTPS en todas las comunicaciones.
- Secretos mediante variables protegidas o gestor de secretos.
- Cifrado de almacenamiento y respaldos.
- Política de retención y eliminación documentada.
- Acceso de mínimo privilegio.
- Revisión de dependencias y vulnerabilidades.
- Cumplimiento de las normas de protección de datos aplicables al centro educativo y a la jurisdicción correspondiente.

---

## 10. Respaldos y recuperación

Objetivos iniciales propuestos, sujetos a validación con el centro:

| Control | Objetivo inicial |
|---|---|
| Respaldo | Automático, al menos diario |
| Retención | 30 días, ajustable |
| RPO | Hasta 24 horas para datos centrales, mejorable con recuperación continua |
| RTO | Objetivo inicial de 8 horas |
| Prueba de restauración | Periódica y documentada |
| Cifrado | En tránsito y en reposo, incluidos respaldos |

RPO significa la pérdida máxima de datos que se tolera en una recuperación. RTO es el tiempo objetivo para restablecer el servicio.

Estos objetivos no son garantías hasta implementarse y probarse. Los cambios locales que no han llegado al servidor no están protegidos por el respaldo central. La interfaz debe alertar de pendientes offline.

Procedimiento mínimo:

1. Crear respaldo.
2. Verificar su integridad.
3. Restaurarlo en un entorno aislado.
4. Ejecutar comprobaciones de esquema y consistencia.
5. Comparar cantidades y muestras de registros.
6. Documentar el resultado y corregir fallos.

---

## 11. Despliegue y entornos

### 11.1 Entornos

- **Desarrollo:** Docker Compose y datos ficticios.
- **Pruebas/staging:** configuración separada para validar migraciones, permisos y sincronización.
- **Producción:** datos reales, secretos protegidos, HTTPS, respaldos, monitorización y acceso restringido.

No usar datos reales de estudiantes en pruebas automatizadas ni en capturas de pantalla de documentación.

### 11.2 Producción

- Frontend en un servicio HTTPS compatible con PWA.
- Backend FastAPI en contenedor Docker detrás de un proxy HTTPS.
- PostgreSQL administrado o una instalación gestionada con seguridad equivalente.
- Base de datos no expuesta públicamente.
- Acceso de red limitado a servicios autorizados.
- Variables de entorno documentadas en `.env.example`, sin secretos reales.
- Migraciones ejecutadas mediante un procedimiento controlado.
- Monitorización de disponibilidad, errores, espacio, conexiones y respaldos.
- Política de actualización y reversión de despliegues.

Vercel u otro hosting puede servir el frontend; el backend y PostgreSQL deben alojarse en servicios compatibles con sus necesidades operativas. Confirmar que el Service Worker y las rutas de la PWA se configuren correctamente.

No agregar alta disponibilidad, réplicas o Kubernetes al MVP sin una necesidad concreta.

---

## 12. Pruebas y criterios de aceptación

Todas las pruebas siguientes son obligatorias antes de declarar el MVP listo para producción.

1. Crear dos instituciones y verificar que sus datos no se mezclan.
2. Crear estudiantes, cursos, secciones, matrículas y asignaciones docentes.
3. Crear tres intentos para un mismo estudiante y actividad.
4. Editar el segundo intento y verificar que los demás permanecen intactos.
5. Consultar el historial individual y los resultados de una actividad.
6. Desconectar Internet, registrar evaluaciones y cerrar/reabrir la aplicación.
7. Reconectar y verificar sincronización sin duplicados.
8. Reenviar una operación ya procesada y comprobar idempotencia.
9. Simular edición concurrente desde dos dispositivos y verificar detección de conflicto.
10. Revocar el acceso de un docente y comprobar que las operaciones online posteriores son rechazadas.
11. Verificar que una institución no puede consultar IDs de otra institución.
12. Exportar Excel y verificar estudiantes, actividades, intentos y observaciones.
13. Restaurar un respaldo y comparar los registros recuperados.
14. Verificar que los errores de validación no creen registros parciales.
15. Verificar que las evaluaciones pendientes nunca se etiqueten como sincronizadas.
16. Comprobar que no se guardan contraseñas ni tokens en almacenamiento local.
17. Ejecutar pruebas de accesibilidad básica y diseño responsivo.
18. Ejecutar pruebas de migraciones sobre una base de datos de prueba.

Usar Pytest para lógica y API, pruebas de integración con PostgreSQL real y Playwright para los flujos principales del navegador. Las pruebas de sincronización deben incluir desconexiones, reintentos, respuestas perdidas y conflictos.

---

## 13. Plan de desarrollo por fases

### Fase 0 — Fundación técnica

**Entregables**
- Repositorio y documentación inicial.
- Docker Compose.
- Frontend y backend mínimos.
- PostgreSQL y migraciones.
- Configuración por entornos.
- CI básico.
- Health checks.
- Primeros ADR.

**Criterios de salida**
- El proyecto se levanta siguiendo el README.
- PostgreSQL persiste datos al reiniciar.
- Lint y pruebas básicas se ejecutan.
- No hay secretos en el repositorio.

### Fase 1 — Identidad e institución

**Entregables**
- Autenticación.
- Instituciones y membresías.
- Roles y permisos.
- Cursos, secciones y años escolares.
- Estudiantes, matrículas y asignaciones docentes.

**Criterios de salida**
- El aislamiento institucional funciona.
- Los permisos se validan en backend.
- Las operaciones inválidas se rechazan correctamente.

### Fase 2 — Motor de evaluación

**Entregables**
- Períodos, semanas y actividades.
- Instrumentos y versiones.
- Evaluaciones e intentos.
- Historial.
- Edición controlada.
- Auditoría.

**Criterios de salida**
- Varios intentos permanecen independientes.
- Las restricciones evitan duplicados inválidos.
- Las correcciones quedan registradas.

### Fase 3 — Interfaz docente e informes

**Entregables**
- Panel principal.
- Búsqueda y filtros.
- Flujo rápido de evaluación.
- Consulta por estudiante y actividad.
- Exportación a Excel.

**Criterios de salida**
- Los docentes pueden completar y consultar evaluaciones de forma sencilla.
- Los filtros respetan permisos.
- Las exportaciones son coherentes con la base de datos.

### Fase 4 — PWA y modo offline

**Entregables**
- Manifest y Service Worker.
- IndexedDB.
- Descarga selectiva de datos.
- Cola de operaciones.
- API idempotente de sincronización.
- Detección de conflictos.
- Indicadores y recuperación de errores.

**Criterios de salida**
- Los registros sobreviven al cierre y reapertura de la aplicación.
- Los reintentos no duplican evaluaciones.
- Los conflictos no se resuelven sobrescribiendo silenciosamente.
- La interfaz diferencia guardado local y sincronización confirmada.

### Fase 5 — Seguridad, recuperación y pruebas

**Entregables**
- Pruebas de autorización y aislamiento.
- Revisión de dependencias.
- Configuración de respaldos.
- Prueba de restauración.
- Monitorización.
- Documentación operativa.

**Criterios de salida**
- Todas las pruebas críticas de aceptación pasan.
- La restauración se ha probado y documentado.
- No hay vulnerabilidades críticas abiertas sin mitigación.

### Fase 6 — Piloto y producción

**Entregables**
- Despliegue controlado.
- Datos iniciales, si corresponde.
- Formación de usuarios.
- Guía de uso y soporte.
- Procedimiento de incidentes y recuperación.

**Criterios de salida**
- Un grupo piloto completa el ciclo de evaluación.
- Se verifica la integridad de los datos.
- Los usuarios conocen el flujo offline y la gestión de pendientes.
- Existe un procedimiento de soporte.

**Estimación orientativa:** 8–14 semanas para un equipo pequeño con experiencia, dependiendo de la complejidad real, la calidad exigida y las pruebas offline. No es un compromiso de entrega.

---

## 14. Decisiones de arquitectura (ADR)

Crear documentos en `docs/architecture/adr/`:

- `ADR-001-monolito-modular.md`: Next.js y FastAPI con separación por dominios.
- `ADR-002-postgresql.md`: PostgreSQL como fuente oficial.
- `ADR-003-multiinstitucion.md`: aislamiento institucional y estrategia de autorización.
- `ADR-004-intentos-evaluacion.md`: varios intentos independientes por estudiante/actividad.
- `ADR-005-pwa-offline.md`: PWA, IndexedDB y datos offline.
- `ADR-006-sincronizacion-conflictos.md`: idempotencia, versiones y resolución explícita.
- `ADR-007-seguridad-auditoria-respaldos.md`: seguridad, auditoría y recuperación.
- `ADR-008-despliegue.md`: entornos, CI/CD y operación.

Cada ADR debe documentar contexto, alternativas, decisión, consecuencias y estado. No inventar que una decisión está implementada si solo está propuesta.

---

## 15. Fuera del MVP

No desarrollar inicialmente, salvo petición explícita:

- Aplicación móvil nativa.
- Portal de padres o estudiantes.
- Integraciones con plataformas educativas externas.
- Boletines oficiales y cálculos complejos de calificaciones.
- Analítica predictiva o inteligencia artificial.
- Mensajería.
- Asistencia, pagos o administración integral del centro.
- Microservicios, Kubernetes o infraestructura distribuida compleja.

La arquitectura debe permitir evolución sin agregar complejidad prematura.

---

## 16. Instrucciones para Codex

Actúa como ingeniero de software responsable de implementar este proyecto de manera incremental, verificable y segura.

### Reglas de trabajo

1. Lee este documento completo antes de modificar o crear código.
2. Inspecciona el repositorio actual antes de asumir que está vacío.
3. Si ya existe código, conserva lo que funcione y propone migraciones cuidadosas; no reemplaces el proyecto entero sin justificación.
4. No intentes implementar todo en una sola operación.
5. Empieza por la Fase 0 y entrega un resumen de archivos creados, decisiones, comandos ejecutados, pruebas y resultados reales.
6. Mantén `README.md` actualizado con los pasos reales de instalación y ejecución.
7. Mantén un archivo `AGENTS.md` con las instrucciones prácticas del repositorio y enlaza este documento maestro.
8. Usa migraciones Alembic para todos los cambios de esquema. No depender de creación automática de tablas en producción.
9. Crea pruebas desde el inicio. No omitas las pruebas de integridad, aislamiento institucional e independencia de intentos.
10. No simules persistencia con arrays, JSON estático, `localStorage` o datos ficticios en la versión de producción.
11. `IndexedDB` se utiliza solamente como almacenamiento offline local; PostgreSQL es la fuente central oficial.
12. No introduzcas credenciales reales en código, archivos versionados, logs o documentación.
13. No marques tareas como completadas si no se ejecutaron las pruebas correspondientes.
14. Si una herramienta, servicio o permiso no está disponible, explica el bloqueo y deja instrucciones concretas sin fingir éxito.
15. Usa datos de prueba ficticios y no incluyas información personal real de estudiantes.
16. Mantén dependencias fijadas y documenta las decisiones relevantes.
17. Prioriza accesibilidad, diseño responsivo, mensajes de error claros y experiencia rápida para docentes.
18. Antes de cualquier operación destructiva, explica el riesgo y solicita autorización cuando sea necesario.
19. Después de cada fase, ejecuta las pruebas pertinentes y reporta resultados reales.
20. No avances a una fase que dependa de criterios de aceptación incumplidos sin documentar el bloqueo y pedir decisión.

### Primera tarea solicitada

Implementa únicamente la **Fase 0 — Fundación técnica**.

1. Inspecciona el repositorio y el entorno.
2. Propón la estructura definitiva y explica cualquier desviación de este documento.
3. Crea la estructura mínima frontend Next.js/TypeScript, backend FastAPI, PostgreSQL y Docker Compose.
4. Configura variables de entorno mediante `.env.example` sin secretos.
5. Añade health checks y una conexión real del backend a PostgreSQL.
6. Configura migraciones Alembic.
7. Añade pruebas mínimas para health check y conectividad con la base de datos.
8. Configura lint y CI básico donde sea viable.
9. Documenta comandos de instalación, arranque, pruebas y apagado.
10. Ejecuta las pruebas y reporta exactamente cuáles pasaron y cuáles no.

No implementes aún todas las funciones académicas. Primero deja una base funcional, reproducible y verificada. Al finalizar, presenta:
- Resumen de lo implementado.
- Árbol de archivos relevante.
- Comandos para ejecutarlo.
- Pruebas ejecutadas y resultados.
- Problemas pendientes.
- Plan concreto para iniciar la Fase 1.

---

## 17. Referencia de definición de terminado

Una fase solo se considera terminada si:

- Sus funcionalidades están implementadas y conectadas a la persistencia real cuando corresponda.
- Las migraciones se ejecutan correctamente desde una base de datos limpia.
- Las pruebas automáticas relevantes pasan.
- Se verificaron los permisos aplicables.
- La documentación corresponde al comportamiento real.
- Los errores y limitaciones conocidos están documentados.
- No hay secretos en el repositorio.
- El resultado puede ejecutarse siguiendo instrucciones reproducibles.

**Fin del documento maestro.**
