#!/bin/sh
# Sólo el proyecto escuelagestion-e2e; PostgreSQL es tmpfs y contiene datos ficticios.
set -eu
cd "$(dirname "$0")/.."
project_root=$(pwd)
compose_e2e() {
  cd "$project_root"
  docker compose -p escuelagestion-e2e -f docker-compose.yml -f docker-compose.e2e.yml "$@"
}
cleanup() { compose_e2e --profile e2e down; }
trap cleanup EXIT
trap 'exit 130' INT TERM
compose_e2e up --build -d --wait --wait-timeout 180
compose_e2e --profile e2e run --build --rm seed-e2e
cd frontend
E2E_BASE_URL=http://127.0.0.1:3101 E2E_IDENTITY=1 npm run test:e2e
# Volver a la raíz para que el trap resuelva correctamente los archivos Compose.
cd ..
