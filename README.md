# Panadería — pedidos mayoristas, producción, delivery y cobranza

Plataforma para una panadería en Caracas (nombre comercial configurable). Reutiliza el stack y el manejo de dinero de **OpenGravity**.

| Rol | Superficie |
|---|---|
| Administrador | Web `/admin`: clientes, catálogo y precios, crédito, **aprobación de pagos**, billeteras, cuentas por cobrar, dashboard, cierres |
| Producción | Web `/cocina` en tablet o TV: pedidos de hoy y programados (con la fecha en grande), Preparando y Listo |
| Motorizado | App Android (APK): En camino y Entregado |
| Cliente mayorista | App Android (Play Store): pedido para hoy o programado, billetera, pago con referencia y comprobante, crédito |

**Stack:**
- **API:** FastAPI + SQLAlchemy + Alembic.
- **Datos y hosting:** Neon Postgres y Railway.
- **Web:** Next.js 16 + Tailwind 4.
- **Android:** Kotlin + Jetpack Compose.
- **Diseño:** Impeccable.

## Documentación
- [PRODUCT.md](PRODUCT.md): el producto, para diseño (Impeccable).
- **Plan** (`docs/plan/`):
  - [00 Visión y decisiones](docs/plan/00-vision-y-alcance.md)
  - [01 Arquitectura](docs/plan/01-arquitectura.md)
  - [02 Modelo de datos](docs/plan/02-modelo-de-datos.md)
  - [03 Flujos de negocio](docs/plan/03-flujos-de-negocio.md)
  - [04 Fases y 10 agentes](docs/plan/04-fases-y-bloques.md)
  - [05 Protocolo](docs/plan/05-protocolo-agentes.md)
  - [06 Reutilización de OpenGravity](docs/plan/06-reutilizacion-opengravity.md)
  - [07 Pruebas](docs/plan/07-pruebas.md)
  - [08 Endpoints](docs/plan/08-api-endpoints.md)
- [Fichas de los agentes](docs/plan/bloques/) y el [tablero de estado](docs/plan/STATUS.md).
- [Cuestionario](docs/CUESTIONARIO.md).
- [`spec/`](spec/): modelo ejecutable y probado de las reglas de dinero (`python -m pytest spec -q`).
