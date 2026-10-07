# CLAUDE.md — reglas para agentes en este repositorio

Proyecto: plataforma de una **panadería en Caracas**. Superficies:
- **API:** FastAPI.
- **Web:** Next.js 16, con el panel `/admin` y la cocina `/cocina`.
- **Android:** app del cliente y app del motorizado.

Reutiliza **OpenGravity** (`/home/user/opengraviti` en el entorno de agentes). Antes de cualquier cambio, leer `README.md`, `PRODUCT.md` y `docs/plan/`.

## Reglas de oro
1. **Trabaja solo en tu bloque.**
   - Tu ficha está en `docs/plan/bloques/`; respeta sus carpetas propias.
   - Protocolo: `docs/plan/05-protocolo-agentes.md`.
   - Archivos congelados: ver el protocolo, §3.
2. **Copiar antes que inventar.**
   - Si OpenGravity ya lo resolvió (pagos, tasa BCV, billeteras, auditoría, cierres, panel), copia y adapta según `docs/plan/06-reutilizacion-opengravity.md`.
   - Al copiar, deja la línea `# Adaptado de OpenGravity: <ruta>`.
3. **Dinero:**
   - `Decimal` y `Numeric(14,2)` en USD; en JSON, string decimal. Nunca `float` ni `Double`.
   - Toda escritura de saldo pasa por `api/src/services/ledger.py`, con `SELECT … FOR UPDATE` y `balanceAfter`.
   - Las reglas exactas están en `docs/plan/03-flujos-de-negocio.md`. La referencia ejecutable es `spec/money_model.py`: si hay duda, manda el modelo.
4. **Tiempo:**
   - Columnas `DateTime` naive en UTC (`to_utc_naive`).
   - El “día” se calcula en `America/Caracas` (`get_today_caracas`, `as_caracas_date`).
   - Nunca `.date()` sobre un UTC crudo.
5. **Contrato:** `contracts/openapi.json` se **genera** desde la API, no se edita a mano. Web y Android no inventan campos.
6. **BD:**
   - Tablas en snake_case y columnas en camelCase; IDs String (cuid2); `SQLEnum(..., name="X")`.
   - Solo Alembic migra; nunca `create_all` en Postgres ni `DROP` sin autorización.
7. **Español de Venezuela** en toda la interfaz y en los mensajes de error. El cliente muestra el `detail` de la API tal cual.
8. **UI:** carga la skill **impeccable** y sigue `DESIGN.md`. Nombre del negocio desde la configuración (`business.name`), nunca fijo en el código.
9. **Sin sobreingeniería:** un motorizado, sin mapas ni rutas, una API, una base de datos.
10. **Sin secretos en el repo.** Las variables nuevas van a `.env.example`. Este repositorio es **público**.
11. **Pruebas:**
    - Todo cambio de comportamiento lleva su prueba.
    - Toda prueba de dinero verifica saldos **y** asientos (`assert_money_invariants`).
12. **Cambios quirúrgicos:** en archivos existentes usa `Edit` puntual, no reescrituras completas.
13. **Acciones destructivas** en Neon, Railway o producción: confirmar con el humano.
    - Neon: solo el proyecto `jmcakes` (`square-poetry-91370020`). Nunca otro proyecto u organización.
14. **Agentes del enjambre:** no hacen push ni PR, no editan `docs/plan/STATUS.md` y usan su propia base de pruebas y sus puertos (`docs/plan/05-protocolo-agentes.md` §1). Integra el orquestador.
15. **Código copiado de OpenGravity**, que es privado (este repo es público): leer antes `/home/user/panaderia-privado/NO-COPIAR-OPENGRAVITY.md` y sanear. Ni el código ni los documentos describen defectos de OpenGravity (`docs/plan/06` §Reglas).

## Comandos
> FND completa esta sección con los comandos reales.

```bash
pip install -r spec/requirements.txt && python -m pytest spec -q   # modelo ejecutable de las reglas de dinero
# FND agregará: scripts/dev-setup.sh (venv + Postgres local + base del agente), pytest de api, export_openapi, mock
```

## Entorno de la nube (verificado el 2026-10-06)
- **Lenguajes y Android:**
  - Python 3.11, Node 22, Java 21 y Gradle disponibles.
  - **Sin Android SDK ni KVM** (`dl.google.com` bloqueado y `maven.google.com` redirige allí): AGP y androidx no se resuelven aquí. En local solo los módulos JVM puros; lo demás compila en GitHub Actions.
- **Base de datos:**
  - PostgreSQL 16 local: `service postgresql start`; rol `dev`/`dev`; una base por agente (`panaderia_test_<id>`).
  - **Sin salida a Neon:5432**: usa el MCP de Neon; las migraciones en Neon las aplica Railway (`preDeployCommand`).
- **Red:** npm, PyPI, Maven Central y el portal de plugins de Gradle están accesibles. **Playwright no puede descargar navegadores**: sus pruebas se escriben en local y corren en GitHub Actions.
