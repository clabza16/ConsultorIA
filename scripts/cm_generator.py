#!/usr/bin/env python3
"""
ConsultorIA - Community Manager Automatizado
Genera contenido para X (Twitter) usando Gemini API

Uso:
    python scripts/cm_generator.py

Requiere:
    pip install google-generativeai
    Variable de entorno: GEMINI_API_KEY
"""

import google.generativeai as genai
import base64
import json
import os
import re
import sys
import webbrowser
from datetime import datetime
from pathlib import Path


def _load_dotenv():
    """Lee .env desde la raíz del proyecto (sin dependencias extra)."""
    candidates = [
        Path(__file__).parent.parent / ".env",   # scripts/../.env
        Path(".env"),                             # directorio actual
    ]
    for p in candidates:
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    os.environ.setdefault(key.strip(), val.strip())
            break

_load_dotenv()


# ─── LOGO ─────────────────────────────────────────────────────────────────────

LOGO_CANDIDATES = [
    "static/logo.png", "static/logo.jpg", "static/logo.svg",
    "static/logo.webp", "static/consultoria_logo.png",
    "static/consultoria_logo.jpg",
]

def get_logo_html(size: int = 40) -> str:
    """Return an <img> tag with the logo embedded as base64, or the fallback SVG."""
    for path in LOGO_CANDIDATES:
        p = Path(path)
        if p.exists():
            ext = p.suffix.lower().lstrip(".")
            mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png",
                    "svg": "svg+xml", "webp": "webp"}.get(ext, "png")
            data = base64.b64encode(p.read_bytes()).decode()
            return (f'<img src="data:image/{mime};base64,{data}" '
                    f'width="{size}" height="{size}" '
                    f'style="border-radius:50%;object-fit:cover;flex-shrink:0;">')
    # Fallback SVG — replica el logo real: fondo blanco, "Consultor" negro, "IA" azul-índigo
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 40 40" '
            f'style="flex-shrink:0;border-radius:50%;overflow:hidden;">'
            f'<rect width="40" height="40" fill="#ffffff" rx="20"/>'
            f'<text x="4" y="26" font-family="-apple-system,sans-serif" '
            f'font-weight="900" font-size="10" fill="#111111">Cons</text>'
            f'<text x="4" y="37" font-family="-apple-system,sans-serif" '
            f'font-weight="900" font-size="10" fill="#111111">ultor</text>'
            f'<text x="28" y="37" font-family="-apple-system,sans-serif" '
            f'font-weight="900" font-size="10" fill="#6366f1">IA</text>'
            f'</svg>')


# ─── ESTRATEGIA DE CONTENIDO ──────────────────────────────────────────────────

CONTENT_TYPES = [
    {
        "id": 1,
        "name": "Tweet Educativo (Insight IA)",
        "emoji": "🧠",
        "desc": "Reflexión/perspectiva sobre IA en el trabajo. Contraintuitiva o reveladora.",
        "hook": "verdad que la gente no se espera o perspectiva que nadie dice",
        "cta": "Guarda esto / Sigue para más",
        "img_style": "comparación: situación sin IA vs con IA",
    },
    {
        "id": 2,
        "name": "Tip del Día",
        "emoji": "💡",
        "desc": "Un consejo accionable y específico para usar IA HOY en el trabajo.",
        "hook": "acción concreta con resultado inmediato y medible",
        "cta": "Prueba esto hoy",
        "img_style": "prompt de ejemplo o captura de resultado real",
    },
    {
        "id": 3,
        "name": "Antes vs Después con IA",
        "emoji": "⚡",
        "desc": "Transformación concreta de una tarea con y sin IA. Tiempo, calidad, esfuerzo.",
        "hook": "contraste impactante con números reales (horas → minutos)",
        "cta": "DM si quieres aprender a hacer esto",
        "img_style": "dos cards: ANTES (fondo oscuro/gris) | CON IA (fondo azul marca)",
    },
    {
        "id": 4,
        "name": "¿Sabías que...? (Dato Viral)",
        "emoji": "🤯",
        "desc": "Dato sorprendente sobre IA que desafía creencias. Genera shares orgánicos.",
        "hook": "estadística o hecho inesperado que cambia la perspectiva del lector",
        "cta": "Comparte si te sorprendió",
        "img_style": "número grande o dato visual impactante",
    },
    {
        "id": 5,
        "name": "El Error Más Común",
        "emoji": "❌",
        "desc": "Pain point que la audiencia reconoce → solución natural → clase 1-a-1.",
        "hook": "error relatable que el profesional promedio comete hoy",
        "cta": "Link en bio → agenda tu clase 1-a-1",
        "img_style": "error (tachado/rojo) vs la forma correcta (verde/azul)",
    },
    {
        "id": 6,
        "name": "Thread Educativo",
        "emoji": "🧵",
        "desc": "Serie de 5-7 tweets sobre un tema de IA. Genera follows masivos y saves.",
        "hook": "primer tweet con promesa de valor muy específica ('Voy a mostrarte X en 5 pasos')",
        "cta": "Sigue @consultoria_info para no perderte el próximo thread",
        "img_style": "diagrama o mapa visual del tema del thread",
    },
    {
        "id": 7,
        "name": "Caso de Uso Real",
        "emoji": "📊",
        "desc": "Historia de cómo un profesional (anónimo) usó IA para resolver un problema real.",
        "hook": "historia concreta con resultado medible y personaje relatable",
        "cta": "Agenda tu clase 1-a-1 y consigue resultados como estos",
        "img_style": "métrica o resultado visual (antes/después con números)",
    },
    {
        "id": 8,
        "name": "Invitación a Clase 1-a-1",
        "emoji": "🎓",
        "desc": "CTA directo para agendar clase personalizada. Máximo 1-2 veces por semana.",
        "hook": "problema específico y concreto que el lector siente HOY → solución en 1 sesión",
        "cta": "Agenda en el link de la bio · WhatsApp +56 9 9682 9223",
        "img_style": "foto del instructor o imagen de resultado de una clase",
    },
]

SYSTEM_PROMPT = """Eres el Community Manager de ConsultorIA, una consultora educativa que enseña a usar IA
(Claude, ChatGPT, Gemini, etc.) a profesionales chilenos no técnicos.

ConsultorIA ofrece:
- Clases 1-a-1 personalizadas de IA para profesionales
- Metodologías para integrar IA en el flujo de trabajo diario
- Contacto: WhatsApp +56 9 9682 9223 | Email: clabza16@gmail.com

Audiencia objetivo:
- Profesionales chilenos de 28-50 años
- Contadores, abogados, ingenieros, ejecutivos, enfermeras, docentes, vendedores
- Quieren ser más productivos pero no saben cómo usar IA bien
- Tienen miedo de quedarse atrás en su carrera o que la IA los reemplace

VOZ DE MARCA: directa, experta pero accesible, auténtica, con tono chileno natural.
Sin tecnicismos. En español de Chile. Ocasionalmente irreverente.

REGLAS PARA X/TWITTER:
- Primer tweet DEBE enganchar en las primeras 5 palabras
- Saltos de línea frecuentes (1-3 palabras por línea para tweets de impacto)
- Específico y concreto (números reales, ejemplos concretos)
- Los mejores tweets generan "eso me pasa a mí" o "no lo sabía"
- Máximo 2-3 hashtags al final: #IA #ProductividadIA o #ChileTech

SIEMPRE responde con un JSON válido y nada más. Estructura:
{
  "tweet_text": "texto completo del tweet (saltos de línea con \\n, máx 280 chars para tweet simple, más para threads)",
  "image1_description": "qué mostrar en imagen 1 (null si no aplica)",
  "image2_description": "qué mostrar en imagen 2 (null si no aplica)",
  "image1_label": "etiqueta corta para el placeholder (ej: 'SIN IA')",
  "image2_label": "etiqueta corta para el placeholder (ej: 'CON IA')",
  "why_this_works": "1-2 oraciones explicando por qué este contenido va a funcionar",
  "best_time": "ej: Martes 9:00 AM",
  "estimated_reach": "estimación optimista de vistas para una cuenta nueva en Chile"
}"""


# ─── FUNCIONES CORE ───────────────────────────────────────────────────────────

def generate_content(model, ct: dict) -> dict:
    prompt = f"""Crea contenido para X (Twitter) de tipo: {ct['emoji']} {ct['name']}

Descripción: {ct['desc']}
Hook recomendado: {ct['hook']}
CTA sugerido: {ct['cta']}
Estilo visual imágenes: {ct['img_style']}

El contenido debe ser en español de Chile, auténtico y diseñado para ganar seguidores
Y convertir a clases 1-a-1 con ConsultorIA."""

    print(f"\n  ⏳ Generando con Gemini...")
    response = model.generate_content(prompt)
    raw = response.text
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return {"tweet_text": raw, "image1_description": None, "image2_description": None}


def generate_weekly_calendar(model) -> list:
    print("\n  ⏳ Generando calendario de 7 días con Gemini...")
    prompt = """Crea un calendario de contenido para X/Twitter de ConsultorIA para los próximos 7 días.

Distribuye los tipos de contenido de forma estratégica:
- Máximo 1 CTA directo (tipo Invitación a Clase) por semana
- Alterna: educativo → viral → storytelling → tip
- Considera horarios pico en Chile: 8-9 AM, 12-13 PM, 7-8 PM

Responde SOLO con un JSON array de 7 objetos:
[
  {
    "dia": "Lunes 4 marzo",
    "hora": "9:00 AM",
    "tipo": "nombre del tipo",
    "emoji": "emoji",
    "tweet_preview": "primeras 2 líneas del tweet...",
    "razon": "por qué este tipo hoy a esta hora"
  }
]"""
    response = model.generate_content(prompt)
    raw = response.text
    m = re.search(r"\[.*\]", raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return []


# ─── HTML GENERATOR ───────────────────────────────────────────────────────────

def fmt_number(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def create_tweet_html(tweet_data: dict, type_name: str = "") -> str:
    out_dir = Path("static/tweets")
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = out_dir / f"tweet_{ts}.html"

    text = tweet_data.get("tweet_text", "")
    img1_desc = tweet_data.get("image1_description") or ""
    img2_desc = tweet_data.get("image2_description") or ""
    img1_label = tweet_data.get("image1_label") or img1_desc[:30]
    img2_label = tweet_data.get("image2_label") or img2_desc[:30]

    # Format text for HTML
    formatted = text.replace("\n", "<br>")
    formatted = re.sub(r"(#\w+)", r'<span style="color:#1D9BF0">\1</span>', formatted)

    # Images HTML
    images_html = ""
    if img1_desc and img2_desc:
        images_html = f"""
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:2px;border-radius:16px;overflow:hidden;border:1px solid #2F3336;margin-bottom:12px;">
            <div style="background:#111827;height:210px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;color:#71767B;font-size:12px;text-align:center;padding:16px;line-height:1.5;">
                <svg width="28" height="28" fill="#71767B" viewBox="0 0 24 24"><path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/></svg>
                <b style="color:#9ca3af;font-size:11px;text-transform:uppercase;letter-spacing:0.05em;">{img1_label}</b>
                <span>{img1_desc}</span>
            </div>
            <div style="background:#0a1628;height:210px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;color:#3b82f6;font-size:12px;text-align:center;padding:16px;line-height:1.5;">
                <svg width="28" height="28" fill="#3b82f6" viewBox="0 0 24 24"><path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/></svg>
                <b style="color:#60a5fa;font-size:11px;text-transform:uppercase;letter-spacing:0.05em;">{img2_label}</b>
                <span>{img2_desc}</span>
            </div>
        </div>"""
    elif img1_desc:
        images_html = f"""
        <div style="border-radius:16px;overflow:hidden;border:1px solid #2F3336;margin-bottom:12px;">
            <div style="background:#111827;height:280px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;color:#71767B;font-size:13px;text-align:center;padding:20px;line-height:1.5;">
                <svg width="32" height="32" fill="#71767B" viewBox="0 0 24 24"><path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/></svg>
                <b style="color:#9ca3af;font-size:11px;text-transform:uppercase;letter-spacing:0.05em;">{img1_label}</b>
                <span>{img1_desc}</span>
            </div>
        </div>"""

    # Timestamp
    now = datetime.now()
    months = ["ene.","feb.","mar.","abr.","may.","jun.","jul.","ago.","sep.","oct.","nov.","dic."]
    h = now.hour % 12 or 12
    ampm = "PM" if now.hour >= 12 else "AM"
    time_str = f"{h}:{now.strftime('%M')} {ampm} · {now.day} {months[now.month-1]} {now.year}"

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ConsultorIA — {type_name}</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
    background:#15202B; min-height:100vh;
    display:flex; justify-content:center; align-items:flex-start;
    padding:30px 20px;
    font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
}}
.card {{
    background:#000; border:1px solid #2F3336; border-radius:12px;
    padding:16px; width:100%; max-width:598px; color:#E7E9EA;
}}
@media print {{
    body {{ background:#000; padding:0; }}
    .card {{ border:none; border-radius:0; max-width:100%; }}
}}
</style>
</head>
<body>
<div class="card">
    <!-- Header -->
    <div style="display:flex;gap:12px;margin-bottom:12px;align-items:flex-start;">
        {get_logo_html(40)}
        <div style="flex:1;">
            <div style="font-weight:700;font-size:15px;color:#E7E9EA;display:flex;align-items:center;gap:4px;">
                Consultor<span style="color:#3b82f6">IA</span>
                <svg viewBox="0 0 22 22" width="16" height="16" style="fill:#1D9BF0;flex-shrink:0;">
                    <path d="M20.396 11c-.018-.646-.215-1.275-.57-1.816-.354-.54-.852-.972-1.438-1.246.223-.607.27-1.264.14-1.897-.131-.634-.437-1.218-.882-1.687-.47-.445-1.053-.75-1.687-.882-.633-.13-1.29-.083-1.897.14-.273-.587-.704-1.086-1.245-1.44S11.647 1.62 11 1.604c-.646.017-1.273.213-1.813.568s-.969.854-1.24 1.44c-.608-.223-1.267-.272-1.902-.14-.635.13-1.22.436-1.69.882-.445.47-.749 1.055-.878 1.688-.13.633-.08 1.29.144 1.896-.587.274-1.087.705-1.443 1.246-.356.54-.555 1.17-.574 1.817.02.647.218 1.276.574 1.817.356.54.856.972 1.443 1.245-.224.606-.274 1.263-.144 1.896.13.634.433 1.218.877 1.688.47.443 1.054.747 1.687.878.633.132 1.29.084 1.897-.136.274.586.705 1.084 1.246 1.439.54.354 1.17.551 1.816.569.647-.016 1.276-.213 1.817-.567s.972-.854 1.245-1.44c.604.239 1.266.296 1.903.164.636-.132 1.22-.447 1.68-.907.46-.46.776-1.044.908-1.681s.075-1.299-.165-1.903c.586-.274 1.084-.705 1.439-1.246.354-.54.551-1.17.569-1.816zM9.662 14.85l-3.429-3.428 1.293-1.302 2.072 2.072 4.4-4.794 1.347 1.246z"/>
                </svg>
            </div>
            <div style="color:#71767B;font-size:14px;">@consultoria_info</div>
        </div>
        <button style="border:1px solid #E7E9EA;color:#E7E9EA;background:transparent;border-radius:999px;padding:6px 16px;font-size:14px;font-weight:700;">Seguir</button>
    </div>

    <!-- Text -->
    <div style="font-size:17px;line-height:1.5625;color:#E7E9EA;margin-bottom:12px;white-space:pre-wrap;">{formatted}</div>

    <!-- Images -->
    {images_html}

    <!-- Timestamp -->
    <div style="color:#71767B;font-size:14px;padding:12px 0;border-top:1px solid #2F3336;">
        {time_str} · <span style="color:#1D9BF0">Consultor<b>IA</b></span>
    </div>

    <!-- Stats -->
    <div style="display:flex;flex-wrap:wrap;gap:16px;padding:12px 0;border-top:1px solid #2F3336;border-bottom:1px solid #2F3336;font-size:14px;">
        <div style="color:#71767B"><b style="color:#E7E9EA">1.2K</b> Reposts</div>
        <div style="color:#71767B"><b style="color:#E7E9EA">89</b> Citas</div>
        <div style="color:#71767B"><b style="color:#E7E9EA">8.4K</b> Me gusta</div>
        <div style="color:#71767B"><b style="color:#E7E9EA">48.2K</b> Vistas</div>
    </div>

    <!-- Actions -->
    <div style="display:flex;justify-content:space-around;padding:12px 0 4px;color:#71767B;">
        <div style="display:flex;align-items:center;gap:6px;font-size:13px;">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M1.751 10c0-4.42 3.584-8 8.005-8h4.366c4.49 0 7.501 3.58 7.501 8 0 4.09-3.001 7.38-7.11 7.892l.02.108v3l-1.72-1.72-.14-.14H9.756c-4.421 0-8.005-3.58-8.005-8z"/></svg> 312
        </div>
        <div style="display:flex;align-items:center;gap:6px;font-size:13px;color:#00BA7C;">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M4.5 3.88l4.432 4.14-1.364 1.46L5.5 7.55V16c0 1.1.896 2 2 2H13v2H7.5c-2.209 0-4-1.79-4-4V7.55L1.432 9.48.068 8.02 4.5 3.88zM16.5 6H11V4h5.5c2.209 0 4 1.79 4 4v8.45l2.068-1.93 1.364 1.46-4.432 4.14-4.432-4.14 1.364-1.46 2.068 1.93V8c0-1.1-.896-2-2-2z"/></svg> 1.2K
        </div>
        <div style="display:flex;align-items:center;gap:6px;font-size:13px;color:#F91880;">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M16.697 5.5c-1.222-.06-2.679.51-3.89 2.16l-.805 1.09-.806-1.09C9.984 6.01 8.526 5.44 7.304 5.5c-1.243.07-2.349.78-2.91 1.91-.552 1.12-.633 2.78.479 4.82 1.074 1.97 3.257 4.27 7.129 6.61 3.87-2.34 6.052-4.64 7.126-6.61 1.111-2.04 1.03-3.7.477-4.82-.561-1.13-1.666-1.84-2.908-1.91zm4.187 7.69c-1.351 2.48-4.001 5.12-8.379 7.67l-.503.3-.504-.3c-4.379-2.55-7.029-5.19-8.382-7.67-1.36-2.5-1.41-4.86-.514-6.67.887-1.79 2.647-2.91 4.601-3.01 1.651-.09 3.368.56 4.798 2.01 1.429-1.45 3.146-2.1 4.796-2.01 1.954.1 3.714 1.22 4.601 3.01.896 1.81.846 4.17-.514 6.67z"/></svg> 8.4K
        </div>
        <div style="display:flex;align-items:center;gap:6px;font-size:13px;">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M8.75 21V3h2v18h-2zM18 21V8.5h2V21h-2zM4 21l.004-10h2L6 21H4zm9.248 0v-7h2v7h-2z"/></svg> 48.2K
        </div>
        <div style="display:flex;align-items:center;gap:6px;">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M4 4.5C4 3.12 5.119 2 6.5 2h11C18.881 2 20 3.12 20 4.5v18.44l-8-5.71-8 5.71V4.5zM6.5 4c-.276 0-.5.22-.5.5v14.56l6-4.29 6 4.29V4.5c0-.28-.224-.5-.5-.5h-11z"/></svg>
        </div>
        <div style="display:flex;align-items:center;gap:6px;">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.59l5.7 5.7-1.41 1.42L13 6.41V16h-2V6.41l-3.3 3.3-1.41-1.42L12 2.59zM21 15l-.02 3.51c0 1.38-1.12 2.49-2.5 2.49H5.5C4.11 21 3 19.88 3 18.5V15h2v3.5c0 .28.22.5.5.5h12.98c.28 0 .5-.22.5-.5L19 15h2z"/></svg>
        </div>
    </div>
</div>
</body>
</html>"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    return str(filepath)


# ─── UI ───────────────────────────────────────────────────────────────────────

def print_result(data: dict, ct: dict):
    w = 62
    print("\n" + "═" * w)
    print(f"  {ct['emoji']}  {ct['name'].upper()}")
    print("═" * w)

    text = data.get("tweet_text", "")
    print("\n📝 TWEET:\n" + "─" * 40)
    print(text)
    print("─" * 40)
    print(f"   ({len(text)} caracteres)")

    for i, key in enumerate(["image1_description", "image2_description"], 1):
        val = data.get(key)
        if val:
            label = data.get(f"image{i}_label", "")
            print(f"\n🖼️  Imagen {i}{' — ' + label if label else ''}: {val}")

    if data.get("why_this_works"):
        print(f"\n🎯 Por qué funciona: {data['why_this_works']}")
    if data.get("best_time"):
        print(f"⏰ Mejor hora para publicar: {data['best_time']}")
    if data.get("estimated_reach"):
        print(f"📈 Alcance estimado: {data['estimated_reach']}")


def print_menu():
    w = 62
    print("\n" + "═" * w)
    print("  🤖  ConsultorIA — Community Manager Automatizado")
    print("═" * w)
    print("\n  TIPOS DE CONTENIDO:\n")
    for ct in CONTENT_TYPES:
        print(f"  {ct['id']}.  {ct['emoji']}  {ct['name']}")
    print()
    print("  9.  📅  Calendario Semanal (7 días de contenido)")
    print("  0.  🚪  Salir")
    print()


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    # Check google-generativeai package
    try:
        import google.generativeai  # noqa: F401
    except ImportError:
        print("\n❌ El paquete 'google-generativeai' no está instalado.")
        print("   Ejecuta: pip install google-generativeai\n")
        sys.exit(1)

    # Check API key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or api_key == "pega-tu-key-aqui":
        print("\n❌ API Key de Gemini no configurada.")
        print("   Abre el archivo .env y agrega:")
        print('   GEMINI_API_KEY=tu-key-aqui')
        print("   Obtén tu key en: https://aistudio.google.com/app/apikey\n")
        sys.exit(1)

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-flash-latest",
        system_instruction=SYSTEM_PROMPT,
    )
    print("\n  ✅ Conectado a Gemini API")

    while True:
        print_menu()
        choice = input("  Elige una opción (0-9): ").strip()

        if choice == "0":
            print("\n  👋 ¡Hasta luego! Sigue creando contenido increíble.\n")
            break

        elif choice == "9":
            calendar = generate_weekly_calendar(model)
            if calendar:
                print("\n" + "═" * 62)
                print("  📅  CALENDARIO SEMANAL — ConsultorIA")
                print("═" * 62 + "\n")
                for day in calendar:
                    print(f"  📆  {day.get('dia','')} — {day.get('hora','')}")
                    print(f"      {day.get('emoji','')} {day.get('tipo','')}")
                    print(f"      \"{day.get('tweet_preview','')}\"")
                    print(f"      💡 {day.get('razon','')}\n")

                out = Path("static/tweets")
                out.mkdir(parents=True, exist_ok=True)
                cal_file = out / f"calendar_{datetime.now().strftime('%Y%m%d')}.json"
                with open(cal_file, "w", encoding="utf-8") as f:
                    json.dump(calendar, f, ensure_ascii=False, indent=2)
                print(f"  ✅ Calendario guardado en: {cal_file}\n")
            else:
                print("\n  ❌ Error generando el calendario. Intenta de nuevo.\n")

        elif choice in [str(ct["id"]) for ct in CONTENT_TYPES]:
            ct = next(c for c in CONTENT_TYPES if str(c["id"]) == choice)
            data = generate_content(model, ct)
            print_result(data, ct)

            html_file = create_tweet_html(data, str(ct["name"]))
            print(f"\n  ✅ HTML guardado en: {html_file}")

            ans = input("\n  ¿Abrir en el navegador? (s/n): ").strip().lower()
            if ans == "s":
                webbrowser.open(f"file:///{Path(html_file).resolve()}")

            print("\n  📸 Para capturar el tweet:")
            print("     1. Abre el HTML en el navegador")
            print("     2. Usa Win + Shift + S (Snipping Tool)")
            print("     3. Guarda y adjunta en X al publicar\n")

        else:
            print("\n  ❌ Opción no válida. Elige entre 0 y 9.\n")


if __name__ == "__main__":
    main()
