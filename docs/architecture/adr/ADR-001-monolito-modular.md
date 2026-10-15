# ADR-001 — Monolito modular

Estado: aceptado para la Fase 0.

Contexto: el maestro §3 exige una base sencilla y separación entre frontend, backend y dominio.

Decisión: Next.js/React/TypeScript para presentación y FastAPI/Pydantic para API. SQLAlchemy permanece como acceso a datos. Un solo backend organizado por módulos; contenedores separados no implican microservicios de negocio. Se crean carpetas por necesidad y se unifican pruebas en `backend/tests`.

Alternativas: backend en Next.js, SQLModel o microservicios. No se eligen porque cambiarían el stack acordado sin necesidad demostrada.

Consecuencias: contratos HTTP explícitos y migraciones compartidas. La pantalla inicial solo comunica disponibilidad y preparación; identidad y funciones académicas quedan para fases posteriores. No se incorporan formularios, openpyxl ni Service Worker antes de necesitarlos.
