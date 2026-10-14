"""Coherencia ejecutable del plan (docs/plan/): si un documento contradice a otro, falla aquí.

Correr:  python -m pytest spec -q
Revisa que 09 (E1) sea un subconjunto de 03 y 08, que los agentes de E1 no se crucen
y que los números que citan STATUS, 07 y 09 sean los reales.
"""
import ast
import fnmatch
import itertools
import pathlib
import re

import money_model
from money_model import ERROR_CODES, Shop

ROOT = pathlib.Path(__file__).parents[1]
PLAN = ROOT / "docs" / "plan"


def read(name: str) -> str:
    return (PLAN / name).read_text(encoding="utf-8")


DOC03, DOC08, DOC09 = read("03-flujos-de-negocio.md"), read("08-api-endpoints.md"), read("09-etapas-admin-primero.md")


# ---------------- inventarios ----------------
def parse_inventory(text: str, marker: str) -> set[tuple[str, str]]:
    """Expande `GET|POST /a/b|c` a operaciones (método, ruta)."""
    block = text[text.index(marker):].split("```")[1]
    ops = set()
    for part in re.split(r"\s·\s|\n", block):
        part = part.strip()
        if not part:
            continue
        methods, _, route = part.partition(" ")
        base, _, last = route.rpartition("/")
        for m in methods.split("|"):
            for leaf in last.split("|"):
                ops.add((m, f"{base}/{leaf}"))
    return ops


INV_FULL = parse_inventory(DOC08, "## Inventario")
INV_E1 = parse_inventory(DOC09, "**Inventario E1**")


def stated(text: str, pattern: str) -> int:
    return int(re.search(pattern, text).group(1))


def test_inventarios_cuadran_con_lo_que_dicen_los_documentos():
    assert len(INV_FULL) == stated(DOC08, r"Total: \*\*(\d+) operaciones")
    assert len(INV_E1) == stated(DOC09, r"## E1 — API \((\d+) operaciones")
    assert f"({len(INV_E1)} operaciones)" in DOC08          # 08 cita el inventario de E1
    assert f"**{len(INV_E1)} en E1**" in read("07-pruebas.md")


def test_e1_es_subconjunto_del_contrato_completo():
    assert INV_E1 <= INV_FULL, INV_E1 - INV_FULL


def test_las_operaciones_nuevas_de_e1_estan_documentadas_en_08():
    news = re.findall(r"`(POST|GET|PATCH) (/[^`]+)`", DOC08[DOC08.index("## Agregados v2.4"):])
    for method, route in news:
        assert (method, "/api/v1" + route) in INV_FULL, (method, route)
        assert (method, "/api/v1" + route) in INV_E1, (method, route)


# ---------------- códigos de error ----------------
CATALOG = set(re.findall(r"^\| `([A-Z_]+)` \| \d{3} \|", DOC03[DOC03.index("## 7. Catálogo de errores"):], re.M))


def test_todo_codigo_citado_en_03_08_09_esta_en_el_catalogo():
    cited = set()
    for doc in (DOC03, DOC08, DOC09):
        cited |= set(re.findall(r"\b(?:401|403|404|409|422|429|501|503) `?([A-Z][A-Z_]{3,})\b", doc))
        cited |= set(re.findall(r"warning = `?([A-Z][A-Z_]{3,})", doc))
    cited -= {"OK"}
    assert cited and cited <= CATALOG, cited - CATALOG
    assert ERROR_CODES <= CATALOG, ERROR_CODES - CATALOG


# ---------------- reglas de 09 contra el modelo ----------------
def test_las_funciones_del_modelo_citadas_en_09_existen():
    table = DOC09[DOC09.index("## E1 — Reglas"):DOC09.index("**Escenarios de `spec` del cuaderno**")]
    names = {n for n in re.findall(r"`([a-z_]+)(?:\(|`)", table) if hasattr(Shop, n) or n in ("balance",)}
    for fn in ("fiado", "manual_charge", "report_payment", "approve", "void_receivable", "reverse", "adjust"):
        assert fn in names and callable(getattr(Shop, fn)), fn


def spec_tests() -> set[str]:
    names = set()
    for f in pathlib.Path(__file__).parent.glob("test_*.py"):
        tree = ast.parse(f.read_text(encoding="utf-8"))
        names |= {n.name for n in tree.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")}
    return names


def test_los_escenarios_de_spec_citados_en_09_existen():
    section = DOC09[DOC09.index("**Escenarios de `spec` del cuaderno**"):DOC09.index("## E1 — Datos")]
    cited = set(re.findall(r"`(test_[a-z0-9_]+)`", section))
    assert cited <= spec_tests(), cited - spec_tests()
    assert any(t.startswith("test_cuaderno_") for t in spec_tests())


def test_aceptacion_cu_contigua():
    ids = sorted({int(n) for n in re.findall(r"^\| CU-(\d+) \|", DOC09, re.M)})
    assert ids == list(range(1, len(ids) + 1)) and len(ids) >= 10


def test_status_07_y_09_citan_el_numero_real_de_pruebas_de_spec():
    n = len(spec_tests())
    assert f"spec {n}/{n}" in read("STATUS.md")
    assert f"**{n} de {n} en verde**" in DOC09
    assert f"`{n} passed`" in read("07-pruebas.md")


# ---------------- agentes de E1: carpetas disjuntas y routers con dueño ----------------
def expand(path: str) -> list[str]:
    m = re.search(r"\{([^}]+)\}", path)
    if not m:
        return [path]
    return [x for alt in m.group(1).split(",") for x in expand(path[:m.start()] + alt + path[m.end():])]


def agent_paths() -> dict[str, list[str]]:
    table = DOC09[DOC09.index("## E1 — Agentes"):DOC09.index("**Por qué no se cruzan:**")]
    out = {}
    for row in re.findall(r"^\| ((?:FND|DSN|B|W|Q)[-\w]*) \|(.+)$", table, re.M):
        agent, rest = row
        cells = rest.split("|")
        writes = cells[-2]
        out[agent] = [p for raw in re.findall(r"`([^`]+)`", writes) if "/" in raw or "." in raw
                      for p in expand(raw) if not p.startswith("docs/handoffs/<")]
    return out


AGENTS = agent_paths()


def _glob(p: str) -> str:
    return p + "**" if p.endswith("/") else p


def _sample(p: str) -> str:
    return _glob(p).replace("**", "x/y").replace("*", "X")


def overlap(a: str, b: str) -> bool:
    return fnmatch.fnmatch(_sample(a), _glob(b)) or fnmatch.fnmatch(_sample(b), _glob(a))


def test_estan_los_seis_agentes_de_e1():
    assert set(AGENTS) == {"FND-E1", "DSN", "B-E1a", "B-E1b", "W-E1", "Q-E1"}


def test_agentes_en_paralelo_no_comparten_carpetas():
    for group in (("FND-E1", "DSN"), ("B-E1a", "B-E1b", "W-E1")):
        for x, y in itertools.combinations(group, 2):
            clashes = [(a, b) for a in AGENTS[x] for b in AGENTS[y] if overlap(a, b)]
            assert not clashes, (x, y, clashes)


def router_files_08() -> dict[tuple[str, str], str]:
    """(método, ruta) → archivo de router, leído de las tablas de 08."""
    owner = {}
    for line in DOC08.splitlines():
        if not line.startswith("| `"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        file_ = next((c.strip("`") for c in cells[1:2] if c.endswith(".py`")), None)
        prev = None
        for op in re.findall(r"`((?:GET|POST|PATCH|DELETE) [^`]+|\.\.\.\/[^`]+)`", cells[0]):
            if op.startswith(".../"):
                method, base = prev[0], prev[1].rsplit("/", 1)[0]
                op_t = (method, base + "/" + op[4:])
            else:
                method, route = op.split(" ", 1)
                op_t = (method, route)
            prev = op_t
            route = op_t[1]
            f = file_ or ("health.py" if route == "/api/health" else "auth.py" if route.startswith("/auth") else None)
            full = route if route.startswith("/api/") else "/api/v1" + route
            if f:
                owner[(op_t[0], full)] = f
    return owner


def test_cada_operacion_de_e1_tiene_router_con_un_solo_dueno():
    files = router_files_08()
    routers = {"FND-E1": {"auth.py", "health.py"}}
    for agent in ("B-E1a", "B-E1b"):
        routers[agent] = {p.rsplit("/", 1)[1] for p in AGENTS[agent] if p.startswith("api/src/api/v1/")}
    assert not routers["B-E1a"] & routers["B-E1b"]
    for op in INV_E1:
        assert op in files, f"{op} no tiene archivo de router en 08"
        owners = [a for a, fs in routers.items() if files[op] in fs]
        assert len(owners) == 1, (op, files[op], owners)


def test_modelo_sin_dependencias_fuera_de_la_libreria_estandar():
    tree = ast.parse(pathlib.Path(money_model.__file__).read_text(encoding="utf-8"))
    mods = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    mods |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    assert mods <= {"__future__", "dataclasses", "decimal", "enum", "itertools"}, mods
