# ADR-008 — Entorno local y CI

Estado: aceptado para desarrollo; despliegue productivo pendiente.

Contexto: §11 y Fase 0 necesitan un arranque reproducible y comprobaciones automatizadas.

Decisión: Docker Compose con PostgreSQL saludable → migración completada → API saludable → frontend. API y frontend ejecutan como usuarios no root, con `no-new-privileges`; los puertos del host se enlazan a 127.0.0.1. Dependencias directas y transitivas fijadas; imágenes por digest. npm desactiva scripts de instalación, Python usa wheels con hashes. GitHub Actions ejecuta integración, lint, compilación y smoke tests de navegador sin despliegue automático.

Alternativas: Sites/Workers, Kubernetes o despliegue público inmediato. No se eligen: no corresponden a esta fase ni al backend/PostgreSQL acordados.

Consecuencias: la primera construcción necesita red y espacio Docker. Los digests deben actualizarse conscientemente tras revisión y pruebas. No se considera producción: faltan autenticación/autorización, HTTPS, roles PostgreSQL separados, backups/restauración, límites de tráfico y monitorización. Los logs y pruebas solo deben contener datos ficticios.
