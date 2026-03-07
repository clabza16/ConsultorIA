# Guía: Cómo medir las visitas a tu página (Analítica Web)

Para un proyecto profesional como **ConsultorIA**, es fundamental saber cuántas personas entran a tu sitio, desde dónde vienen y cuántas hacen clic en el botón de reserva.

La herramienta estándar para esto es **Google Analytics 4 (GA4)**. Es gratuita y potente.

---

## 🚀 Paso 1: Crear tu cuenta de Google Analytics
1. Entra a [analytics.google.com](https://analytics.google.com) con tu cuenta de Gmail.
2. Crea una "Propiedad" llamada **ConsultorIA**.
3. En la configuración de flujo de datos, selecciona **Web**.
4. Ingresa el link de tu página (ej: tu sitio en GitHub Pages o hosting).
5. Obtendrás un **ID de medición** que empieza con `G-` (ejemplo: `G-ABC123XYZ`).

---

## 🛠️ Paso 2: Instalar el código en tu página
Una vez que tengas tu ID, debes pegarlo en el archivo `index.html`. El código se ve así (reemplaza `TU_ID_AQUÍ` por tu ID real):

```html
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=TU_ID_AQUÍ"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'TU_ID_AQUÍ');
</script>
```

**¿Dónde se pega?**
Justo después de la etiqueta `<head>` en tu archivo `index.html`.

---

## 📊 ¿Qué datos mirar cada mañana?
1. **Usuarios:** Cuántas personas únicas entraron.
2. **Fuentes de tráfico:** ¿Vienen de LinkedIn, WhatsApp o acceso directo?
3. **Conversiones (Eventos):** Puedes ver cuántas veces se abrió el modal de reserva.

---

## 💡 Estrategia de Experto
Si estás haciendo el "Market Blitz" (contactando gente por WhatsApp), puedes usar un **acortador de enlaces con trackeo** (como Bitly) para saber exactamente quién de tus contactos hizo clic, antes de que lleguen a la analítica general.

> [!TIP]
> Si no quieres configurar Analytics hoy, puedes empezar mirando las estadísticas de tu **GitHub Pages** (si lo usas) o simplemente contar cuántas veces recibes el correo de reserva en tu Google Sheets. Pero para escalar, GA4 es el camino.
