"""Estilo v5 @amoryprofit (aprobado por Ivan el 27 oct 2026). Guía: claude/guia-editorial.md, sección 12.
Fondos en tools/fondos/ (dominio público).
- Tipografía única (Inter Display), texto blanco hueso, secundario hueso apagado. Sin franjas de color por pilar.
- Mismo filtro para todas las imágenes (el de vida real: saturación/contraste, color 0,65, cálido, grano).
- Session recap: David de Miguel Ángel entero (dominio público) ligeramente difuminado en portada, más en el cierre.
- Mentalidad: grabado en un recuadro centrado sobre el mismo grabado muy difuminado; gancho debajo.
- Vida real: foto propia con el filtro; gancho arriba a la izquierda.
- Portadas: gancho fuerte y, debajo, la segunda parte más pequeña."""
import asyncio, base64, io, json, os, sys, datetime, html
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
from playwright.async_api import async_playwright

HUESO, SEC, OSC = "#EEE7D9", "#BDB4A5", "#121314"
POS, NEG = "#3FE584", "#FF5040"   # R más vivo (v5)
PAPEL, NARANJA, TINTA, TINTA2 = "#ECE0CC", "#E4580B", "#2A211B", "#7A6A58"   # papel cálido (v5)
DIAS = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
MESES = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "fondos")
e = lambda t: html.escape(str(t))

def color(im):
    """Parte de color del filtro común (sin grano)."""
    im = ImageEnhance.Contrast(ImageEnhance.Color(im).enhance(1.5)).enhance(1.08)
    im = ImageEnhance.Color(im).enhance(0.65)
    a = np.array(im).astype(float); a[..., 0] *= 1.05; a[..., 2] *= 0.92
    return Image.fromarray(a.clip(0, 255).astype("uint8"))

def grano(im, k=0.045, seed=7):
    a = np.array(im).astype(float)
    a += np.random.default_rng(seed).normal(0, 255 * k, a.shape[:2])[..., None]
    return Image.fromarray(a.clip(0, 255).astype("uint8"))

def b64(im, q=88):
    buf = io.BytesIO(); im.convert("RGB").save(buf, "JPEG", quality=q); return base64.b64encode(buf.getvalue()).decode()

def david(blur, oscuro=1.0, x=300):
    """David entero: estatua a toda altura (1350) desplazada a la derecha; laterales rellenos con la propia foto muy difuminada."""
    src = Image.open(os.path.join(IMG, "david.jpg")).convert("RGB")
    h = 1350; w = int(src.width * h / src.height)
    base = src.resize((int(src.width * 1500 / src.height) * 2, 1500), Image.LANCZOS)
    base = base.crop(((base.width - 1080) // 2, 75, (base.width - 1080) // 2 + 1080, 1425)).filter(ImageFilter.GaussianBlur(45))
    base.paste(src.resize((w, h), Image.LANCZOS), (x, 0))
    im = color(base)
    if blur: im = im.filter(ImageFilter.GaussianBlur(blur))
    if oscuro != 1: im = ImageEnhance.Brightness(im).enhance(oscuro)
    return grano(im)

def foto(ruta, recorte, tapar=()):
    im = Image.open(ruta).convert("RGB")
    for (x0, y0, x1, y1) in tapar:
        im.paste(im.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(14)), (x0, y0))
    im = im.crop(recorte).resize((1080, 1350), Image.LANCZOS)
    return grano(color(im))

CSS = f"""*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1350px;position:relative;overflow:hidden;background:{OSC};color:{HUESO};font-family:'Inter Display','Inter',sans-serif}}
.bg{{position:absolute;inset:0;background-size:cover;background-position:center}}
.v{{position:absolute;inset:0}}
.foot{{position:absolute;left:84px;right:84px;bottom:52px;display:flex;justify-content:space-between;font-size:26px;color:{SEC};font-weight:500;z-index:5}}
.sh{{text-shadow:0 2px 18px rgba(0,0,0,.45)}}
.g1{{text-wrap:balance;font-weight:800;letter-spacing:-.022em;line-height:1.02;color:{HUESO}}}
.g2{{font-weight:500;letter-spacing:-.005em;line-height:1.22;color:{SEC};margin-top:22px}}
.pos{{color:{POS}}}.neg{{color:{NEG}}}"""

def page(body, n, t, claro=False, papel=None):
    extra = f"body{{background:{papel or PAPEL}}}.foot{{color:{TINTA2}}}" if claro else ""
    return f"<html><head><meta charset='utf-8'><style>{CSS}{extra}</style></head><body>{body}<div class='foot'><span>@amoryprofit</span><span>{n}/{t}</span></div></body></html>"

def rfmt(x): return f"{x:+.2f}".replace('.', ',').replace('-', '−') + "R"

def recap_portada(fecha, cuentas, n=1, t=7):
    f = datetime.date.fromisoformat(fecha)
    fl = f"{DIAS[f.weekday()]} {f.day} de {MESES[f.month-1]}"
    filas = ""
    for c in cuentas:
        ses = " y ".join(c["ses"]); tr = f"{c['n']} {'trade' if c['n']==1 else 'trades'}" + (f" · {ses}" if ses else "")
        filas += (f"<div style='display:flex;justify-content:space-between;align-items:flex-end;border-top:2px solid rgba(238,231,217,.30);padding-top:20px'>"
                  f"<div><div style='font-size:54px;font-weight:700'>{e(c['nombre'])}</div><div style='font-size:34px;color:{HUESO};opacity:.82;margin-top:8px'>{tr}</div></div>"
                  f"<div class='{'pos' if c['r']>=0 else 'neg'}' style='font-size:132px;font-weight:800;letter-spacing:-.03em;line-height:1'>{rfmt(c['r'])}</div></div>")
    body = (f"<div class='bg' style=\"background-image:url(data:image/jpeg;base64,{b64(david(5))})\"></div>"
            f"<div class='v' style='background:linear-gradient(180deg,rgba(12,12,13,.72) 0%,rgba(12,12,13,.35) 18%,rgba(12,12,13,0) 34%,rgba(12,12,13,0) 52%,rgba(12,12,13,.86) 100%)'></div>"
            f"<div class='sh' style='position:absolute;left:84px;top:84px;z-index:3'><div class='g1' style='font-size:156px;line-height:.9'>Session<br>recap</div>"
            f"<div class='g2' style='font-size:52px;font-weight:600;color:{HUESO};margin-top:28px'>{fl}</div></div>"
            f"<div class='sh' style='position:absolute;left:84px;right:84px;bottom:132px;z-index:3;display:flex;flex-direction:column;gap:26px'>{filas}</div>")
    return page(body, n, t)

def recap_cierre(n=7, t=7):
    body = (f"<div class='bg' style=\"background-image:url(data:image/jpeg;base64,{b64(david(16, .62))})\"></div>"
            f"<div class='sh' style='position:absolute;left:84px;right:84px;top:0;bottom:130px;display:flex;flex-direction:column;justify-content:center;z-index:3'>"
            f"<div class='g1' style='font-size:98px'>Somos lo que hacemos repetidamente.</div>"
            f"<div class='g2' style='font-size:38px'>Will Durant</div>"
            f"<div style='font-size:68px;font-weight:700;margin-top:72px;color:{HUESO}'>Paso corto, vista larga.</div></div>")
    return page(body, n, t)

def grabado_claro(nombre, recorte=None):
    """Grabado de línea (Flaxman) entintado: blanco -> papel, negro -> tinta sepia. Sin recuadro."""
    g = Image.open(os.path.join(IMG, nombre + ".jpg")).convert("L")
    if recorte: g = g.crop(recorte)
    a = np.array(ImageEnhance.Contrast(g).enhance(1.25)).astype(float) / 255
    p = np.array([0xF5, 0xF0, 0xE8], float); t = np.array([0x2B, 0x26, 0x22], float)
    return grano(Image.fromarray((t + (p - t) * a[..., None]).clip(0, 255).astype("uint8")), .018)

def hx(c): return np.array([int(c[k:k+2], 16) for k in (1, 3, 5)], float)

def grabado_tono(nombre, caja, foco=(.5, .5), papel=None):
    """Grabado tonal (Doré y similares) recortado a la caja y entintado en sepia cálido sobre el papel."""
    g = Image.open(os.path.join(IMG, nombre + ".jpg")).convert("L")
    m = int(min(g.size) * .035); g = g.crop((m, m, g.width - m, g.height - m))   # fuera márgenes del escaneo
    bw, bh = caja; r = bw / bh
    w, h = g.size
    if w / h > r: nw = int(h * r); x = int((w - nw) * foco[0]); g = g.crop((x, 0, x + nw, h))
    else: nh = int(w / r); y = int((h - nh) * foco[1]); g = g.crop((0, y, w, y + nh))
    g = ImageEnhance.Contrast(g.resize((bw * 2, bh * 2), Image.LANCZOS)).enhance(1.12)
    a = (np.array(g).astype(float) / 255) ** 1.25   # un punto más oscuro
    p = hx(papel or PAPEL) * 1.02; t = hx("#1E1712")
    return grano(Image.fromarray((t + (p - t) * a[..., None]).clip(0, 255).astype("uint8")), .02)

def mentalidad_portada(grabado, g1, g2, n=1, t=4, foco=(.5, .5), papel=None, caja=(912, 720)):
    bw, bh = caja
    im = grabado_tono(grabado, caja, foco, papel)
    body = (f"<img src='data:image/jpeg;base64,{b64(im, 86)}' style='position:absolute;left:{(1080-bw)//2}px;top:84px;width:{bw}px;height:{bh}px;box-shadow:0 1px 0 rgba(42,33,27,.25)'>"
            f"<div style='position:absolute;left:84px;right:84px;top:{84+bh+60}px'>"
            f"<div class='g1' style='font-size:80px;color:{NARANJA}'>{e(g1)}</div>"
            f"<div class='g2' style='font-size:40px;color:{TINTA};margin-top:26px'>{e(g2)}</div></div>")
    return page(body, n, t, claro=True, papel=papel)

def mentalidad_interior(titulo, texto, n, t, papel=None):
    body = (f"<div style='position:absolute;left:96px;right:96px;top:0;bottom:120px;display:flex;flex-direction:column;justify-content:center'>"
            f"<div style='font-size:30px;font-weight:700;letter-spacing:.14em;color:{NARANJA}'>{n:02d}</div>"
            f"<div class='g1' style='font-size:66px;color:{NARANJA};margin-top:26px'>{e(titulo)}</div>"
            f"<div style='font-size:42px;line-height:1.38;color:{TINTA};margin-top:34px;font-weight:450'>{e(texto)}</div></div>")
    return page(body, n, t, claro=True, papel=papel)

VIDA = {  # variantes de color para vida real
    "A": ("#FF7A2F", "#F3EEE4"),   # gancho naranja vivo, texto blanco roto
    "B": ("#F3EEE4", "#FFB15C"),   # gancho blanco roto, texto ámbar
}

def vida_portada(img, g1, g2, n=1, t=3, var="A"):
    if var == "C":   # banda de papel abajo, como mentalidad: gancho naranja y texto negro
        body = (f"<div class='bg' style=\"background-image:url(data:image/jpeg;base64,{b64(img)});background-position:center top;bottom:420px;inset:0 0 420px 0\"></div>"
                f"<div style='position:absolute;left:0;right:0;bottom:0;height:420px;background:{PAPEL}'></div>"
                f"<div style='position:absolute;left:84px;right:84px;bottom:128px'>"
                f"<div class='g1' style='font-size:72px;color:{NARANJA}'>{e(g1)}</div>"
                f"<div class='g2' style='font-size:38px;color:{TINTA}'>{e(g2)}</div></div>")
        return page(body, n, t, claro=True)
    c1, c2 = VIDA[var]
    body = (f"<div class='bg' style=\"background-image:url(data:image/jpeg;base64,{b64(img)})\"></div>"
            f"<div class='v' style='background:linear-gradient(180deg,rgba(12,12,13,0) 0%,rgba(12,12,13,0) 42%,rgba(12,12,13,.6) 66%,rgba(12,12,13,.92) 100%)'></div>"
            f"<div class='sh' style='position:absolute;left:84px;right:110px;bottom:132px;z-index:3'>"
            f"<div class='g1' style='font-size:86px;color:{c1}'>{e(g1)}</div><div class='g2' style='font-size:42px;font-weight:600;color:{c2}'>{e(g2)}</div></div>")
    return page(body, n, t)

async def render(pages, out):
    os.makedirs(out, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={"width": 1080, "height": 1350})
        for name, h in pages:
            await pg.set_content(h); await pg.wait_for_timeout(250)
            await pg.screenshot(path=os.path.join(out, name + ".png"))
        await b.close()
