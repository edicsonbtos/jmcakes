"""Exporta el contrato a `contracts/openapi.json` (se **genera**, no se edita a mano).

Uso (desde `api/`):
    python -m scripts.export_openapi           # escribe el archivo
    python -m scripts.export_openapi --check   # falla si el archivo no está al día
    python -m scripts.export_openapi --count   # imprime el número de operaciones

Importa la app sin conectarse a la base (engine perezoso).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "contracts" / "openapi.json"
METHODS = ("get", "post", "put", "patch", "delete")


def render() -> str:
    from src.main import app

    return json.dumps(app.openapi(), ensure_ascii=False, indent=2, sort_keys=False) + "\n"


def operations(spec: dict) -> list[tuple[str, str]]:
    return sorted((m.upper(), p) for p, item in spec.get("paths", {}).items() for m in item if m in METHODS)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="falla si contracts/openapi.json no está al día")
    parser.add_argument("--count", action="store_true", help="imprime el número de operaciones")
    args = parser.parse_args(argv)

    text = render()
    if args.count:
        print(len(operations(json.loads(text))))
        return 0
    if args.check:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != text:
            print("contracts/openapi.json no está al día: corre `cd api && python -m scripts.export_openapi`.", file=sys.stderr)
            return 1
        print("contracts/openapi.json al día.")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(f"Escrito {OUT.relative_to(ROOT)} ({len(operations(json.loads(text)))} operaciones).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
