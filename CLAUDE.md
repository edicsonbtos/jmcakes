# CLAUDE.md — reglas para agentes en este repositorio

Proyecto **JM Cakes**: plataforma para una panadería en Caracas (admin web, cocina web, app Android cliente, app Android delivery). Lee `README.md` y `docs/plan/` antes de cualquier cambio.

## Reglas de oro
1. **Trabaja solo en tu bloque.** Tu ficha está en `docs/plan/bloques/<ID>-*.md`; respeta sus carpetas propias. Protocolo completo: `docs/plan/05-protocolo-agentes.md`.
2. **Contrato primero.** `contracts/openapi.yaml` es la fuente de verdad. Cambios solo aditivos; los que rompen compatibilidad se piden en el handoff.
3. **Dinero = centavos enteros + ledger.** Nunca `float`; nunca editar saldos fuera del módulo de finanzas.
4. **Hora de Caracas** (`America/Caracas`) para todo “día”, reporte o texto visible. Usa los helpers de `api/src/lib/time.ts`.
5. **Español de Venezuela** en toda interfaz y mensaje de error visible.
6. **Sin sobreingeniería:** un motorizado, sin mapas ni rutas, un backend, una base de datos.
7. **Sin secretos en el repo.** Variables nuevas → `.env.example`.
8. Al terminar: tests y CI verdes, `docs/handoffs/<ID>.md`, fila actualizada en `docs/plan/STATUS.md`, PR hacia `main`.
9. Preguntas del negocio sin responder → usa el valor por defecto de `docs/CUESTIONARIO.md` y anótalo.
10. Acciones destructivas en Neon/Railway/producción → confirmar con el humano.

## Comandos
> F0 completa esta sección con los comandos reales (instalar, test, lint, mock, migraciones, build Android).

## Entorno de la nube
- Node 22 y pnpm disponibles. Java 21 y Gradle disponibles. **Sin Android SDK ni KVM**: compila Android en GitHub Actions o instala `cmdline-tools` si la red lo permite.
