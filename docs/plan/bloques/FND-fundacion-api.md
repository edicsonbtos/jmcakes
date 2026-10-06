# FND — Fundación de la API, base de datos y contrato

**Fase 0** (en paralelo con DSN) · **Rama** `block/FND` · **Reutiliza** OpenGravity ([06](../06-reutilizacion-opengravity.md))

## Objetivo
Dejar `api/` lista para que B1, B2 y B3 trabajen en paralelo sin tocar archivos compartidos, y `contracts/openapi.json` **completo**, para que W1, W2 y M construyan contra el mock.

## Alcance
1. **Estructura y base técnica (copiada de OpenGravity)**
   - `api/`: `requirements.txt` con versiones fijas de OpenGravity, sin Telegram (+ `apscheduler`, `hypothesis`, `boto3` o `httpx` para S3, `firebase-admin` opcional).
   - `pytest.ini` dentro de `api/` (`asyncio_mode = strict`, `pythonpath = .`), `.env.example`, `alembic.ini`, `alembic/`, `railway.toml` (start uvicorn con `$PORT`, `preDeployCommand = "alembic upgrade head"`, healthcheck `/api/health`), `nixpacks.toml`.
   - `src/config.py`, `src/db/*`, `src/core/*`, `src/utils/date_utils.py` y `src/api/limiter.py`, adaptados.
   - `src/main.py`: CORS (`CORS_ORIGINS`), handlers de error (formato `{detail, code, meta}`), lifespan con APScheduler y `_safe_job`, y **todos los routers de [08](../08-api-endpoints.md) registrados**.
2. **Modelos y migración**
   - Todos los `db_models.py` de [02](../02-modelo-de-datos.md): nombres camelCase, enums con `name=`, índices, CHECKs, secuencia `order_number_seq` desde 1001 e índice único parcial de `payments`.
   - Registro único en `models_registry.py`.
   - **Una** revisión Alembic inicial. Debe aplicar sobre Postgres vacío, revertir con `downgrade base` y volver a aplicar.
3. **Auth completa** (FND la implementa, no stub)
   - `users`, `refresh_tokens` y `device_tokens`.
   - Endpoints: register (crea customer CASH), login con rate limit, refresh rotativo, logout, me, device-tokens y `DELETE /auth/account`.
   - Dependencias `get_current_user` y `require_role(*roles)`, y `get_current_customer` para el rol C.
4. **Contrato completo**
   - Esquemas Pydantic de request/response de **todos** los endpoints de 08, en el `schemas.py` de cada dominio, con ejemplos realistas: productos venezolanos, montos en string decimal, fechas Caracas en ISO.
   - Routers con roles y respuestas de error declaradas. Los cuerpos no implementados lanzan `AppError("Aún no disponible", code="NOT_IMPLEMENTED", status=501)`.
   - `scripts/export_openapi.py` (con `--check`) escribe `contracts/openapi.json`.
   - `scripts/mock.sh` levanta Prism (`npx @stoplight/prism-cli mock contracts/openapi.json -p 4010`).
5. **Interfaces y stubs** de [08](../08-api-endpoints.md) §Interfaces, con el comportamiento mínimo descrito. Más el `EventBus` en memoria con `publish_after_commit` (hook `after_commit` de la sesión).
6. **Dominios que FND deja funcionando** (copiados de OpenGravity con sus pruebas): `exchange_rates` (service, fetcher y repository; sin endpoints), `audit` (service y repository) y `settings` (service con caché y defaults de 02; sin endpoints).
7. **Pruebas**
   - `tests/conftest.py`: Postgres local por `TEST_DATABASE_URL` y sesión con savepoint, como OpenGravity.
   - Fixtures: `client` (httpx con la app), `make_user(role)` con su token, `customer_cash`, `customer_credit`, `money_setup`.
   - `tests/helpers.py` con `assert_money_invariants(session)`: I-1…I-7 en SQL.
   - Arnés `tests/test_authz_matrix.py`: recorre las rutas del OpenAPI y verifica que cada rol no permitido recibe 401/403. B1–B3 lo amplían.
   - Pruebas de auth, del arnés, de la migración (upgrade/downgrade) y de `export_openapi --check`.
8. **Seed** `scripts/seed.py`, idempotente, según [07](../07-pruebas.md) §5.
9. **CI**
   - `.github/workflows/api.yml`: Python 3.11, servicio `postgres:16`, `pip install`, `alembic upgrade head`, `pytest -q` y `export_openapi --check`.
   - `.github/workflows/contract.yml`: lint del OpenAPI con Spectral.
   - `spec.yml`, o un job dentro de `api.yml`: `pytest spec`.
10. **Skills y agente adaptados.**
    - Copiar a `.claude/skills/` las skills `contabilidad-opengravity`, `migraciones-esquema-opengravity`, `tests-bot-opengravity`, `cambios-quirurgicos-opengravity`, `jobs-programados-opengravity` y `panel-web-opengravity`, como `<nombre>-panaderia`, con rutas, tablas y reglas de esta panadería y sin préstamos.
    - Adaptar el subagente `auditor-contable` a `.claude/agents/`.
11. Completar la sección **Comandos** de `CLAUDE.md`.

## No tocar
`web/`, `android/`, `DESIGN.md` y `docs/design/` (son de DSN).

## Limitantes
- Sin salida a Neon:5432. Se prueba con Postgres 16 local (`service postgresql start`; crear el rol y la base `panaderia_test` como usuario `postgres`).
- No tiene que haber lógica de negocio de B1, B2 ni B3 más allá de los stubs; si no, se duplica trabajo.
- Python disponible: 3.11.

## Oportunidades
- Copiar las pruebas de OpenGravity de `exchange_rates` y `audit` da cobertura inmediata.
- Los ejemplos ricos en los esquemas hacen el mock útil para W1, W2 y M.

## Compuerta G1 (parte FND)
- [ ] `alembic upgrade head` → `downgrade base` → `upgrade head` sin errores en Postgres local.
- [ ] `pytest -q` verde (resultado en el handoff).
- [ ] `contracts/openapi.json` con todos los endpoints de 08 (contarlos en el handoff).
- [ ] `python -m pytest spec -q` verde.
- [ ] `scripts/seed.py` corre dos veces sin duplicar nada.
