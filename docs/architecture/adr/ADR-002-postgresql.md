# ADR-002 — PostgreSQL y migraciones

Estado: aceptado para la Fase 0.

Contexto: §2, §3 y §16 del maestro requieren PostgreSQL real y Alembic; no basta simular persistencia.

Decisión: PostgreSQL 18 en imagen oficial fijada por digest, SQLAlchemy 2.1 con psycopg 3 y sesiones/conexiones síncronas en handlers FastAPI síncronos. Alembic administra toda evolución de esquema; no se llama a `create_all` al iniciar la API. El pool comprueba conexiones y limita tiempos de conexión/consulta.

Alternativas: SQLite de pruebas, creación automática de tablas o un ORM alternativo. Se descartan porque ocultarían diferencias de integridad/transacciones o contradirían el maestro.

Consecuencias: volumen persistente montado en `/var/lib/postgresql` para PostgreSQL 18; base efímera aparte para pruebas. La migración 0001 establece el historial sin anticipar entidades. Readiness falla si falta conexión o migración. La Fase 1 debe definir roles de aplicación/migración de mínimo privilegio antes de tratar datos de usuarios; las credenciales bootstrap de Compose son solo de desarrollo.
