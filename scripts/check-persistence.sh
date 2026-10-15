#!/bin/sh
# Solo reinicia el PostgreSQL de este proyecto; no ejecuta migraciones ni borra datos.
set -eu
cd "$(dirname "$0")/.."
before=$(docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "SELECT version_num FROM alembic_version ORDER BY version_num"')
test -n "$before"
backend_address=$(docker compose port backend 8000)
docker compose restart db
# Esperar recuperación de la API sin recrearla ni volver a migrar.
curl --fail --silent --show-error --retry 20 --retry-delay 1 --retry-all-errors \
  "http://${backend_address}/api/v1/health/ready"
after=$(docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "SELECT version_num FROM alembic_version ORDER BY version_num"')
test "$before" = "$after"
printf '\nPersistencia verificada: la revisión almacenada se conserva después del reinicio.\n'
