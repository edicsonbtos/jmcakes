# JM Cakes — Plataforma de gestión para panadería

Sistema para una panadería en Caracas, Venezuela, con cuatro roles:

| Rol | Superficie | Qué hace |
|---|---|---|
| **Administrador** | Web (backoffice) | Control total: clientes, productos y precios, línea de crédito, cuentas por cobrar, billeteras, pagos, dashboards, supervisión de producción y delivery. |
| **Producción (cocina)** | Web (tablet, ruta `/cocina`) | Recibe los pedidos nuevos en tiempo real, los prepara y marca **Listo**. |
| **Delivery (motorizado)** | App Android (APK por fuera de Play Store) | Recibe automáticamente los pedidos listos y marca **En camino** y **Entregado**. |
| **Cliente mayorista** | App Android (Play Store) | Se registra, ve el catálogo, hace pedidos, paga de contado o a crédito y reporta pagos a su billetera. |

> **Estado:** fase de planificación. El plan de trabajo para los agentes autónomos está en [`docs/plan/`](docs/plan/).

## Índice del plan

1. [Visión y alcance](docs/plan/00-vision-y-alcance.md)
2. [Arquitectura y stack](docs/plan/01-arquitectura.md)
3. [Modelo de datos](docs/plan/02-modelo-de-datos.md)
4. [Flujos de negocio (pedidos, billetera, CxC)](docs/plan/03-flujos-de-negocio.md)
5. [Fases y bloques para agentes](docs/plan/04-fases-y-bloques.md)
6. [Protocolo de trabajo entre agentes](docs/plan/05-protocolo-agentes.md)
7. [Tablero de estado](docs/plan/STATUS.md)
8. [**Cuestionario de aclaraciones**](docs/CUESTIONARIO.md) ← responder antes de lanzar la Fase 1

Fichas de cada bloque: [`docs/plan/bloques/`](docs/plan/bloques/).
