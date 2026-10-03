# L1 — Lanzamiento a producción

**Fase:** 4 · **Esfuerzo:** M · **Rama:** `block/L1-lanzamiento`

## Objetivo
Poner el sistema en producción y dejar al dueño operando.

## Alcance
1. **Producción**: entorno `production` en Railway (api + web) con rama Neon `main`; dominio propio **[C-11]** con HTTPS; variables y secretos; seed mínimo (admin real, motorizado, producción, catálogo inicial).
2. **Respaldos**: snapshots/PITR de Neon configurados; procedimiento de restauración documentado y probado una vez.
3. **Monitoreo**: alertas de caída (Railway), logs de errores, métricas básicas.
4. **Android firmado**:
   - Keystores de firma (los genera y guarda el humano; el agente documenta el procedimiento y configura el CI para leerlos de GitHub Secrets).
   - **Delivery**: APK `release` firmada publicada en GitHub Releases (repo privado) o enlace privado; instrucciones de instalación (“permitir orígenes desconocidos”).
   - **Cliente**: AAB `release` + **Play App Signing**; ficha de Play Store (textos, capturas, ícono, gráfico destacado), **política de privacidad** publicada (página estática en la web), formulario de **Seguridad de los datos**, clasificación de contenido, eliminación de cuenta. Workflow `release-cliente.yml` que sube a la pista **interna** con fastlane/Gradle Play Publisher.
5. **Manuales** en `docs/manuales/` (cortos, con capturas): administrador, cocina, motorizado, cliente (este último también como texto para WhatsApp).
6. **Plan de arranque**: carga de clientes existentes y saldos iniciales de CxC (importación CSV con asientos `MANUAL` de apertura).

## Limitantes
- Crear la cuenta de **Google Play Console** (25 USD) y aceptar sus acuerdos lo hace el humano. **Cuentas personales nuevas** deben pasar una **prueba cerrada con al menos 12 testers durante 14 días** antes de publicar en producción; una cuenta de **organización** (requiere número D-U-N-S) está exenta **[C-12]**. Planificar esos 14 días.
- Dominio, DNS y cuentas de pago de Railway/Neon: el humano.
- El agente no debe tener acceso a los keystores en texto plano dentro del repo.

## Oportunidades
- Mientras corre la prueba cerrada de Play Store, el negocio puede operar con la app cliente distribuida como APK a los primeros mayoristas.
- Importar saldos iniciales evita llevar dos sistemas en paralelo.

## Definición de terminado
- Producción operando; un pedido real recorrido completo; respaldos verificados; manuales entregados; app cliente en prueba interna/cerrada; APK delivery instalada en el teléfono del motorizado.

## Prompt para lanzar este bloque
```
Eres el agente del bloque L1 del proyecto JM Cakes (repo edicsonbtos/jmcakes).
Lee CLAUDE.md, docs/plan/, docs/plan/bloques/L1-lanzamiento.md, docs/handoffs/Q1.md
y docs/CUESTIONARIO.md. Prepara producción (Railway + Neon), respaldos, monitoreo,
workflows de release de Android y manuales. Todo lo que requiera cuentas o
credenciales del dueño (Play Console, keystores, dominio) déjalo como checklist
paso a paso para el humano. Pide confirmación antes de acciones en producción.
```
