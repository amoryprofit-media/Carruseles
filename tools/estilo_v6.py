"""Estilo v6 del diario @amoryprofit (aprobado por Ivan el 24 nov 2026; sustituye al session recap del David).
- Fondo liso grafito #322E29 en todas las diapositivas (ni negro puro ni imagen).
- Portada: día enorme + mes y día de la semana arriba a la izquierda; en medio el gráfico REAL del primer trade
  de Nueva York del día (si no hay, el primero), recoloreado al grafito, sin cabecera, sin ejes y algo estirado
  en vertical; abajo una fila por cuenta con trades · sesiones y su R.
- Trade: hora · sesión · setup · dirección · duración; gráfico recoloreado SIN eje de precios; R de cada cuenta; idea.
- Resumen del día: R por cuenta en grande + reflexión de Ivan.
- Cierre: logo de Amor y Profit (tools/fondos/logo_amoryprofit.png, sin montañas) + Will Durant + lema.
Los gráficos son los de la Bitácora (render.py v33, 1080x780, fondo gris 198): se recolorean píxel a píxel,
así que las velas son exactamente las del gráfico original."""
import os, io, base64, datetime
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
BG = (50, 46, 41); PANEL = (40, 37, 33)
HUESO, SEC, POS, NEG = (237, 230, 216), (154, 146, 133), (63, 229, 132), (255, 80, 64)
HX = lambda c: "#%02x%02x%02x" % tuple(c)
FONT = "/usr/share/fonts/opentype/inter/InterDisplay-%s.otf"
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
SRC_BG = np.array([198, 198, 198], float)

def font(w, s):
    try: return ImageFont.truetype(FONT % w, s)
    except OSError: return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", s)

def inks(bg):
    return [((112, 106, 106), tuple(min(255, c + 62) for c in bg)),   # vela bajista
            ((171, 181, 219), (176, 188, 232)),                        # vela alcista
            ((79, 79, 79), tuple(min(255, c + 105) for c in bg)),      # mechas, bordes, textos del eje
            ((31, 46, 92), (110, 132, 200)),                           # EMA
            ((17, 17, 17), (237, 230, 216)),                           # línea punteada, borde de flechas
            ((255, 255, 255), None),                                   # halo blanco
            ((196, 102, 26), (226, 128, 54)),                          # naranja punteado
            ((214, 166, 44), (222, 178, 70)),                          # amarilla
            ((18, 161, 80), (40, 196, 110)),                           # flecha de compra
            ((156, 61, 61), (232, 92, 76))]                            # flecha de venta

def recolor(img, bg):
    """Cambia el fondo gris del gráfico por bg y cada tinta por su color nuevo, conservando el antialias."""
    a = np.asarray(img.convert("RGB"), float); bgn = np.array(bg, float)
    best = np.full(a.shape[:2], 1e9); out = np.zeros_like(a); d = a - SRC_BG
    for src, dst in inks(bg):
        v = np.array(src, float) - SRC_BG
        al = np.clip((d @ v) / (v @ v), 0, 1)
        res = np.linalg.norm(d - al[..., None] * v, axis=2)
        new = bgn if dst is None else np.array(dst, float)
        col = al[..., None] * new + (1 - al[..., None]) * bgn
        m = res < best; best[m] = res[m]; out[m] = col[m]
    return Image.fromarray(out.clip(0, 255).astype("uint8"))

def _limpio(path):
    """Gráfico original con el logo de TradingView tapado."""
    im = Image.open(path).convert("RGB")
    ImageDraw.Draw(im).rectangle((0, 695, 60, 732), fill=(198, 198, 198))
    return im

def _derecha(im, x_max=950, y0=100, y1=730):
    """Última columna con velas (para no dejar hueco vacío a la derecha)."""
    a = np.asarray(im.crop((0, y0, x_max, y1)), float)
    cols = np.where((np.abs(a - SRC_BG).sum(2) > 30).any(0))[0]
    return min(x_max, int(cols.max()) + 24) if len(cols) else x_max

def grafico_portada(path, bg=BG, size=(1000, 770)):
    im = _limpio(path)
    return recolor(im.crop((0, 102, _derecha(im), 700)), bg).resize(size, Image.LANCZOS)

def grafico_trade(path, bg=PANEL):
    """Sin cabecera, sin eje de precios (decisión de Ivan, 24 nov 2026); conserva el eje de horas."""
    im = _limpio(path)
    return recolor(im.crop((0, 96, 955, 780)), bg)

def b64png(im):
    buf = io.BytesIO(); im.save(buf, "PNG"); return base64.b64encode(buf.getvalue()).decode()

def b64jpg(im, q=90):
    buf = io.BytesIO(); im.convert("RGB").save(buf, "JPEG", quality=q); return base64.b64encode(buf.getvalue()).decode()

def r(x): return f"{x:+.2f}".replace(".", ",").replace("-", "−") + "R"

def grano(im, k=0.03, seed=7):
    a = np.array(im).astype(float)
    a += np.random.default_rng(seed).normal(0, 255 * k, a.shape[:2])[..., None]
    return Image.fromarray(a.clip(0, 255).astype("uint8"))

# ---------- diapositivas ----------
def portada_png(fecha, cuentas, chart_path, n, t):
    """cuentas: [{"nombre", "sub" (trades · sesiones), "r"}]. Devuelve PIL.Image 1080x1350."""
    W, H = 1080, 1350; line = tuple(c + 22 for c in BG)
    im = Image.new("RGB", (W, H), BG); dr = ImageDraw.Draw(im)
    if chart_path and os.path.exists(chart_path):
        im.paste(grafico_portada(chart_path), (40, 270))
    f = datetime.date.fromisoformat(fecha)
    fd = font("ExtraBold", 210); dia = str(f.day)
    dr.text((68, 40), dia, font=fd, fill=HUESO)
    x = 68 + dr.textlength(dia, font=fd) + 26
    dr.text((x, 96), MESES[f.month - 1], font=font("SemiBold", 46), fill=HUESO)
    dr.text((x, 152), DIAS[f.weekday()], font=font("Medium", 42), fill=SEC)
    y = 1058 if len(cuentas) > 1 else 1162
    for c in cuentas[:2]:
        dr.line((72, y, W - 72, y), fill=line, width=2)
        dr.text((72, y + 22), c["nombre"], font=font("SemiBold", 34), fill=HUESO)
        dr.text((72, y + 66), c["sub"], font=font("Medium", 26), fill=SEC)
        fr = font("ExtraBold", 72); tx = r(c["r"])
        dr.text((W - 72 - dr.textlength(tx, font=fr), y + 14), tx, font=fr, fill=POS if c["r"] >= 0 else NEG)
        y += 104
    fp = font("Medium", 26); pag = f"{n}/{t}"
    dr.text((72, 1290), "@amoryprofit", font=fp, fill=SEC)
    dr.text((W - 72 - dr.textlength(pag, font=fp), 1290), pag, font=fp, fill=SEC)
    return im

CSS = f"""*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1350px;background:{HX(BG)};color:{HX(HUESO)};font-family:'Inter Display','Inter',sans-serif;position:relative;overflow:hidden}}
.foot{{position:absolute;left:72px;right:72px;bottom:46px;display:flex;justify-content:space-between;font-size:26px;color:{HX(SEC)};font-weight:500}}
.k{{font-size:34px;font-weight:600;color:{HX(SEC)}}}
.row{{display:flex;justify-content:space-between;align-items:baseline;border-top:2px solid {HX(tuple(c + 22 for c in BG))};padding:18px 0}}
.row b{{font-size:34px;font-weight:600}} .row small{{display:block;font-size:26px;color:{HX(SEC)};font-weight:500;margin-top:6px}}
.row span{{font-weight:800;letter-spacing:-.02em;line-height:1}}
.pos{{color:{HX(POS)}}}.neg{{color:{HX(NEG)}}}"""

def page(body, n, t):
    return f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}<div class='foot'><span>@amoryprofit</span><span>{n}/{t}</span></div></body></html>"

def html_img(im):
    return f"<img src='data:image/png;base64,{b64png(im)}' style='position:absolute;inset:0;width:1080px;height:1350px'>"

def trade(kicker, chart_path, filas, idea, esc, n, t):
    """filas: [(nombre, r)]; un trade (o el mismo trade replicado en varias cuentas) por diapositiva."""
    graf = ""
    if chart_path and os.path.exists(chart_path):
        graf = (f"<div style='margin-top:30px;border-radius:22px;overflow:hidden;background:{HX(PANEL)};padding:18px 10px 8px'>"
                f"<img src='data:image/png;base64,{b64png(grafico_trade(chart_path))}' style='width:100%;display:block'></div>")
    rows = "".join(f"<div class='row'><b>{esc(nm)}</b><span class='{'pos' if v >= 0 else 'neg'}' style='font-size:64px'>{r(v)}</span></div>" for nm, v in filas)
    fs = 38 if len(idea) <= 260 else 34 if len(idea) <= 380 else 30
    p = f"<p style='margin-top:26px;font-size:{fs}px;line-height:1.3;font-weight:500'>{esc(idea)}</p>" if idea else ""
    body = (f"<div style='position:absolute;left:72px;right:72px;top:72px'><div class='k'>{esc(kicker)}</div>{graf}"
            f"<div style='margin-top:34px'>{rows}</div>{p}</div>")
    return page(body, n, t)

def pareja(items, esc, n, t):
    """Dos trades seguidos en una diapositiva. items: [(kicker, chart_path, filas)], texto común aparte."""
    bloques = ""
    for kicker, path, filas in items:
        img = (f"<img src='data:image/png;base64,{b64png(grafico_trade(path))}' style='width:100%;display:block'>"
               if path and os.path.exists(path) else "")
        rows = "".join(f"<div class='row' style='padding:10px 0'><b style='font-size:28px'>{esc(nm)}</b><span class='{'pos' if v >= 0 else 'neg'}' style='font-size:48px'>{r(v)}</span></div>" for nm, v in filas)
        bloques += (f"<div class='k' style='font-size:28px;margin-top:22px'>{esc(kicker)}</div>"
                    f"<div style='margin-top:12px;border-radius:18px;overflow:hidden;background:{HX(PANEL)};padding:10px 8px 4px;width:820px'>{img}</div>{rows}")
    return page(f"<div style='position:absolute;left:72px;right:72px;top:50px'>{bloques}</div>", n, t)

def resumen(cuentas, reflexion, esc, n, t):
    rows = "".join(f"<div class='row'><b>{esc(c['nombre'])}<small>{esc(c['sub'])}</small></b>"
                   f"<span class='{'pos' if c['r'] >= 0 else 'neg'}' style='font-size:110px'>{r(c['r'])}</span></div>" for c in cuentas)
    L = len(reflexion or "")
    fs = 48 if L < 220 else 44 if L < 400 else 40 if L < 520 else 36
    p = f"<p style='font-size:{fs}px;line-height:1.32;font-weight:500'>{esc(reflexion)}</p>" if reflexion else ""
    body = (f"<div style='position:absolute;left:72px;right:72px;top:72px;bottom:130px;display:flex;flex-direction:column'>"
            f"<div class='k'>Resumen del día</div><div style='margin-top:40px'>{rows}</div>"
            f"<div style='flex:1;display:flex;align-items:center'>{p}</div></div>")
    return page(body, n, t)

def fondo_logo(w=600, cy=400, op=.92, blur=1.0):
    """Logo sin montañas (son más oscuras que el grafito): solo velas, nombre y subtítulo."""
    lg = Image.open(os.path.join(HERE, "fondos", "logo_amoryprofit.png")).convert("RGB").resize((w, w), Image.LANCZOS)
    a = np.asarray(lg, float); al = np.clip((a.max(2) - 120) / 40, 0, 1) * op
    b = np.asarray(Image.new("RGB", (1080, 1350), BG), float).copy()
    x0 = (1080 - w) // 2; y0 = cy - w // 2
    b[y0:y0 + w, x0:x0 + w] = b[y0:y0 + w, x0:x0 + w] * (1 - al[..., None]) + a * al[..., None]
    return grano(Image.fromarray(b.clip(0, 255).astype("uint8")).filter(ImageFilter.GaussianBlur(blur)))

def cierre(n, t):
    body = (f"<div style='position:absolute;inset:0;background:url(data:image/jpeg;base64,{b64jpg(fondo_logo())}) center/cover'></div>"
            f"<div style='position:absolute;left:84px;right:84px;top:0;bottom:140px;display:flex;flex-direction:column;justify-content:flex-end;text-shadow:0 2px 18px rgba(0,0,0,.5)'>"
            f"<div style='font-size:98px;font-weight:800;letter-spacing:-.022em;line-height:1.02'>Somos lo que hacemos repetidamente.</div>"
            f"<div style='font-size:38px;font-weight:500;color:#BDB4A5;margin-top:22px'>Will Durant</div>"
            f"<div style='font-size:68px;font-weight:700;margin-top:64px'>Paso corto, vista larga.</div></div>")
    return page(body, n, t)
