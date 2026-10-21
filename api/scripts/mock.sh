#!/usr/bin/env bash
# Mock del contrato con Prism (docs/plan/05 §5). Responde con los `example` de contracts/openapi.json.
# Uso: MOCK_PORT=4011 api/scripts/mock.sh        (puerto por agente: 05 §1)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PORT="${MOCK_PORT:-4010}"
SPEC="$ROOT/contracts/openapi.json"

if [[ ! -f "$SPEC" ]]; then
  echo "Falta $SPEC: corre 'cd api && python -m scripts.export_openapi'." >&2
  exit 1
fi

exec npx --yes @stoplight/prism-cli@5.16.0 mock "$SPEC" --host 127.0.0.1 --port "$PORT" --dynamic=false
