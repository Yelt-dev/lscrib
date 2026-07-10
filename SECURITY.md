# Política de seguridad

## Versiones con soporte

Se da soporte a la **última versión publicada**. Al ser una app local-first, cada
instancia corre en la máquina del usuario; actualizar a la última imagen es la forma
recomendada de recibir parches.

## Reportar una vulnerabilidad

**No abras un issue público** para vulnerabilidades. Usa el reporte privado de GitHub:

> pestaña **Security** del repo → **Report a vulnerability**.

Incluye, si puedes: descripción, impacto, pasos para reproducir y versión afectada.
Se responde lo antes posible y se coordina la divulgación una vez haya un arreglo.

## Alcance

lscrib procesa audio **enteramente en local** y no expone un servicio multiusuario:
no hay cuentas, ni datos de terceros, ni telemetría. La única salida de red es la
descarga del modelo de Whisper la primera vez. El modelo de amenazas es el de una app
de escritorio: quien controla la máquina controla los datos.
