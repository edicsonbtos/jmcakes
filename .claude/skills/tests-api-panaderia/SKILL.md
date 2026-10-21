---
name: tests-api-panaderia
description: Cómo escribir y correr las pruebas de la API de la panadería — Postgres real por agente, pytest-asyncio estricto con loop de sesión, fixtures db_session/committed_db/client/make_user/money_setup, dobles inyectables y assert_money_invariants. Úsala antes de crear o modificar archivos en api/tests/.
---
# Adaptado de OpenGravity: .agents/skills/tests-bot-opengravity/SKILL.md

# Pruebas de la API

## Correr
```bash
scripts/dev-setup.sh                                   # venv + Postgres + base del agente
cd api
export TEST_DATABASE_URL=postgresql+psycopg://dev:dev@127.0.0.1:5432/panaderia_test_<id>
python -m pytest -q                                    # toda la suite
python -m pytest -q tests/b3/test_fiado.py -k anular   # una parte
```
- `TEST_DATABASE_URL` es obligatorio y local (127.0.0.1, localhost o postgres). El conftest crea la
  base y corre `alembic upgrade head` una vez. Cada agente usa **su** base y sus puertos (05 §1).
- `asyncio_mode = strict`: marca cada prueba async con `@pytest.mark.asyncio` (o `pytestmark` en
  módulos que solo tengan pruebas async).

## Fixtures (`api/tests/conftest.py`)
| Fixture | Para qué |
|---|---|
| `db_session` | Sesión en una transacción externa que se deshace; los `commit` del código son savepoints. |
| `client` | httpx + ASGITransport; cada request usa `db_session`. |
| `committed_db` / `committed_client` | Commits reales para concurrencia (`asyncio.gather`), con TRUNCATE de tu base antes y después. Marca la prueba con `@pytest.mark.committed`. |
| `make_user(role, must_change_password=False)` | Usuario + `headers` con Bearer. `admin` es un atajo. |
| `customer_cash`, `customer_credit` | Clientes listos (detal CASH; mayorista CREDIT con límite $100). |
| `money_setup` | Pago móvil y transferencia (Bs, “Banco Bs”), Zelle (USD) y Efectivo USD (“Caja” → “Caja USD”). |
| `money_double` | Sustituye `MoneyService` y registra `open_balance`. |
| `settings_cache_clear` | Autouse: limpia la caché de configuración. |

Para sustituir otra fábrica: `with registry.override("finance", mi_doble): ...` (`src/services/registry.py`).

## Reglas
- Prueba de dinero = saldos **y** asientos + `await assert_money_invariants(db_session)` al final.
- Las pruebas de un bloque afirman sobre su implementación o sobre los dobles, **nunca** sobre el
  comportamiento del stub por defecto de FND.
- Nombres por comportamiento, en español (`test_abono_en_bs_usa_la_tasa_de_paid_on`).
- Fechas: congela "ahora" pasando valores explícitos; el día es de Caracas
  (`caracas_day_bounds_utc`). Prueba el borde de las 22:30 VET.
- Cada bloque escribe solo en `tests/<bloque>/`; si la carpeta existe debe recoger pruebas.
- `tests/test_authz_matrix.py` es de FND: verifica 401/403 por `x-roles`. Los casos de propiedad
  van en `tests/<bloque>/test_authz_<bloque>.py`.
