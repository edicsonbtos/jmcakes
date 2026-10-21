#!/usr/bin/env bash
# Entorno local de la API (docs/plan/05 §1): venv con Python 3.11, dependencias, Postgres y la base del agente.
#
# Uso (desde la raíz del repo):
#   TEST_DATABASE_URL=postgresql+psycopg://dev:dev@127.0.0.1:5432/panaderia_test_<id> scripts/dev-setup.sh
# Sin TEST_DATABASE_URL usa panaderia_test_fnd.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="${VENV:-$ROOT/.venv}"
PYTHON="${PYTHON:-python3.11}"
TEST_DATABASE_URL="${TEST_DATABASE_URL:-postgresql+psycopg://dev:dev@127.0.0.1:5432/panaderia_test_fnd}"

echo "==> Python: $($PYTHON --version)"
if [[ ! -x "$VENV/bin/python" ]]; then
  "$PYTHON" -m venv "$VENV"
fi
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q -r "$ROOT/api/requirements.txt" -r "$ROOT/spec/requirements.txt"
echo "==> Dependencias instaladas en $VENV"

echo "==> Postgres"
if ! pg_isready -h 127.0.0.1 -p 5432 >/dev/null 2>&1; then
  service postgresql start >/dev/null
  for _ in $(seq 1 30); do pg_isready -h 127.0.0.1 -p 5432 >/dev/null 2>&1 && break; sleep 1; done
fi
if ! PGPASSWORD=dev psql -h 127.0.0.1 -U dev -d postgres -tAc "SELECT 1" >/dev/null 2>&1; then
  su postgres -c "psql -c \"CREATE ROLE dev LOGIN SUPERUSER PASSWORD 'dev'\""
fi

DB_NAME="${TEST_DATABASE_URL##*/}"
DB_NAME="${DB_NAME%%\?*}"
if [[ -z "$(PGPASSWORD=dev psql -h 127.0.0.1 -U dev -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'")" ]]; then
  PGPASSWORD=dev psql -h 127.0.0.1 -U dev -d postgres -qc "CREATE DATABASE \"$DB_NAME\""
  echo "==> Base $DB_NAME creada"
else
  echo "==> Base $DB_NAME ya existe"
fi

cat <<EOF

Listo. Comandos (desde api/):
  export TEST_DATABASE_URL=$TEST_DATABASE_URL
  $VENV/bin/python -m pytest -q                        # pruebas de la API
  $VENV/bin/python -m scripts.export_openapi --check   # contrato al día
  cd .. && $VENV/bin/python -m pytest spec -q          # modelo de dinero
EOF
