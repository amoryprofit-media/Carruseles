"""Carrusel de diario @amoryprofit.
Uso: python3 carrusel_diario.py dia.json salida/   (las imágenes de cada op: <op_id>.png junto al json)
dia.json = {"fecha":"2026-10-09","reflexion":"<valoración del día>","ops":[{id,hora_entrada,direccion,duracion_min,r_real,tipo,reflexion(=frase del trade)}]}
  o, con varias cuentas: {"fecha":…,"reflexion":…,"cuentas":[{"nombre":"Cuenta 50K","ops":[…]},{"nombre":"Cuenta 25K","ops":[…]}]}
  (cada cuenta tiene su portada con su R y sus trades; la primera es la principal). r_real de cada op = R contra el riesgo máximo de esa cuenta.
--preview muestra huecos amarillos para lo que falte; sin él, lo que falte simplemente no sale.
Estructura (desde 14 oct 2026): portada con imagen de fondo (cuadro clásico) + resumen del día por cuenta ·
  por cada cuenta y cada trade: gráfico con su R y duración + idea del trade · reflexión del día · cierre.
Portada: dia.json["portada"] = {"imagen": ruta (relativa al json o absoluta), "recorte": [x0,y0,x1,y1] en fracciones (opcional),
  "desenfoque": px (def. 6), "oscuro": 0-1 (def. .55), "gris": false,
  "completo": true para poner el cuadro entero (menos zoom) con "arriba": px desde arriba}. Sin "portada", fondo oscuro liso. "portada":"auto" elige de la colección tools/portadas/ (rota por fecha) o "portada":"<id>".
Tipos del journal -> Instagram: Tipo 1 = Rotura ZA, Tipo 2 = ORB, Tipo 3 = Momentum.
"""
import asyncio, base64, json, sys, os, datetime
from playwright.async_api import async_playwright

TIPOS = {"1":"Rotura ZA","tipo 1":"Rotura ZA","2":"ORB","tipo 2":"ORB","3":"Momentum","tipo 3":"Momentum","london 1":"EMA Trend","london 2":"FVG Reversal"}
DIAS = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
MESES = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
CIERRES = {
 1: ("Un día más.<br>Un paso más.", None),
 2: ("Sigo.", None),
 3: ("Todavía no.<br>Pero sigo.", None),
}
def r(x): s=f"{x:+.2f}".replace('.',',').replace('+','+').replace('-','−'); return s+"R"
def sesion(h): return "Londres" if int(h.split(':')[0]) < 14 else "Nueva York"
def tipo(t): return TIPOS.get(str(t).strip().lower(), None)
import html as _h
PREVIEW = False
def esc(t): return _h.escape(str(t))
def ph(t): return f"<span class='ph'>{t}</span>"

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1350px;background:#0f1114;color:#f1eee8;font-family:'Inter Display','Inter',sans-serif;position:relative;overflow:hidden}
.band{position:absolute;left:0;top:0;bottom:0;width:18px;background:#4f8a6f}
.wrap{position:absolute;left:96px;right:84px;top:84px;bottom:130px;display:flex;flex-direction:column}
.kicker{font-size:28px;letter-spacing:.14em;text-transform:uppercase;color:#4f8a6f;font-weight:600}
.head{font-size:52px;font-weight:750;color:#4f8a6f;letter-spacing:-.01em}
.foot{position:absolute;left:96px;right:84px;bottom:56px;display:flex;justify-content:space-between;font-size:26px;color:#7d7a74;font-weight:500}
h1{font-size:92px;line-height:1.02;font-weight:800;letter-spacing:-.02em}
h2{font-size:60px;line-height:1.1;font-weight:750;letter-spacing:-.015em}
p{font-size:46px;line-height:1.32;color:#d9d5ce}
.mid{flex:1;display:flex;flex-direction:column;justify-content:center;gap:40px}
.ph{color:#e0b44c;border:3px dashed #e0b44c;border-radius:14px;padding:10px 22px;display:inline-block}
.row{display:flex;gap:28px;align-items:center;border-top:2px solid #26292e;padding:24px 0}
.row b{font-size:30px;letter-spacing:.1em;text-transform:uppercase;color:#7d7a74;font-weight:600;min-width:250px}
.row span{font-size:46px;font-weight:500}
.chart{width:100%;height:900px;border-radius:18px;overflow:hidden;margin-top:36px;background:#c5c5c5}
.chart img{width:100%;height:100%;object-fit:cover;object-position:50% 55%}
.pos{color:#6fbf95}.neg{color:#d9776b}
.bg{position:absolute;inset:-40px;background-size:cover;background-position:center;z-index:0}
.veil{position:absolute;inset:0;z-index:1}
.cov{position:absolute;left:96px;right:84px;bottom:150px;z-index:2;display:flex;flex-direction:column;gap:26px}
.cov .fecha{font-size:40px;font-weight:600;color:#e9e4da;letter-spacing:.01em}
.cov .cta{display:flex;align-items:baseline;justify-content:space-between;gap:30px;border-top:2px solid rgba(241,238,232,.28);padding-top:22px}
.cov .cta b{font-size:40px;font-weight:600;color:#e9e4da}
.cov .cta span{font-size:118px;font-weight:800;letter-spacing:-.03em;line-height:1}
.cov .cta i{font-style:normal;font-size:30px;color:#cfc8bd;display:block;margin-top:6px}
.big{font-size:230px;font-weight:800;letter-spacing:-.04em;line-height:1}
"""
def page(body, n, total, label="Diario"):
    if isinstance(body, tuple):  # portada: (html de fondo, html encima)
        fondo, encima = body
        return f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{fondo}<div class='band' style='z-index:3'></div>{encima}<div class='foot' style='z-index:3;color:#cfc8bd'><span>@amoryprofit</span><span>{n}/{total}</span></div></body></html>"
    return f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body><div class='band'></div><div class='wrap'>{body}</div><div class='foot'><span>@amoryprofit</span><span>{n}/{total}</span></div></body></html>"

def portada_fondo(cfg, basedir, extra_blur=0, extra_oscuro=0):
    """Recorta a 4:5 y devuelve el html del fondo (imagen desenfocada y oscurecida).
    extra_blur: desenfoque adicional (los cierres usan el mismo fondo de la portada, más difuminado)."""
    if not cfg or not cfg.get("imagen"):
        return "<div class='veil' style='background:#0f1114'></div>"
    from PIL import Image, ImageFilter, ImageEnhance
    import io
    ruta = cfg["imagen"] if os.path.isabs(cfg["imagen"]) else os.path.join(basedir, cfg["imagen"])
    im = Image.open(ruta).convert("RGB"); W, H = im.size
    if cfg.get("recorte"):
        x0, y0, x1, y1 = cfg["recorte"]; im = im.crop((int(x0*W), int(y0*H), int(x1*W), int(y1*H))); W, H = im.size
    obj = 4/5
    if cfg.get("completo"):  # cuadro entero (menos zoom) sobre un fondo hecho con el propio cuadro muy desenfocado
        full = im.copy()
        fw = 1160; fh = int(H * fw / W)
        base = full.resize((int(W * 1450 / H), 1450), Image.LANCZOS)
        x = (base.width - 1160) // 2; base = base.crop((x, 0, x + 1160, 1450)).filter(ImageFilter.GaussianBlur(40))
        base = ImageEnhance.Brightness(base).enhance(0.55)
        base.paste(full.resize((fw, fh), Image.LANCZOS), (0, int(cfg.get("arriba", 120))))
        im = base; W, H = im.size
    elif W/H > obj:
        nw = int(H*obj); cx = cfg.get("centro_x", .5); x = min(max(int(cx*W - nw/2), 0), W-nw); im = im.crop((x, 0, x+nw, H))
    else:
        nh = int(W/obj); im = im.crop((0, (H-nh)//2, W, (H-nh)//2+nh))
    im = im.resize((1160, 1450), Image.LANCZOS)
    if cfg.get("gris"): im = ImageEnhance.Color(im).enhance(0)
    else: im = ImageEnhance.Color(im).enhance(cfg.get("color", 1.25))
    if not cfg.get("gris"): im = ImageEnhance.Brightness(im).enhance(cfg.get("brillo", 1.12))
    d = cfg.get("desenfoque", 6) + extra_blur
    if d: im = im.filter(ImageFilter.GaussianBlur(d))
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=88)
    b64 = base64.b64encode(buf.getvalue()).decode()
    k = cfg.get("oscuro", .35) + extra_oscuro
    # velo ligero arriba (el cuadro se ve luminoso y con color) y más oscuro solo abajo, donde va el texto
    return (f"<div class='bg' style=\"background-image:url(data:image/jpeg;base64,{b64})\"></div>"
            f"<div class='veil' style='background:linear-gradient(180deg,rgba(10,11,13,{k*.15:.2f}) 0%,rgba(10,11,13,{k*.25:.2f}) 45%,rgba(10,11,13,{min(k+.25,.9):.2f}) 100%)'></div>")

def resolver_portada(dia):
    """dia["portada"] == "auto" (o un id de la colección) -> config de tools/portadas/portadas.json. Rota por fecha."""
    cfg = dia.get("portada")
    if not isinstance(cfg, str): return cfg
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "portadas")
    cat = json.load(open(os.path.join(base, "portadas.json")))["portadas"]
    if cfg == "auto":
        n = datetime.date.fromisoformat(dia["fecha"]).toordinal()
        claras = [c for c in cat if c.get("auto", True)]  # los cuadros oscuros ("auto": false) no entran en la rotación
        elegido = claras[n % len(claras)]
    else:
        elegido = next(c for c in cat if c["id"] == cfg)
    out = dict(elegido); out["imagen"] = os.path.join(base, elegido["imagen"]); return out

def portada(dia, cuentas, basedir):
    f = datetime.date.fromisoformat(dia["fecha"])
    fecha = f"{DIAS[f.weekday()]} {f.day} de {MESES[f.month-1]}"
    filas = ""
    for c in cuentas:
        ops = c["ops"]; rt = sum(o["r_real"] for o in ops); n = len(ops)
        ses = []
        for o in sorted(ops, key=lambda o: o["hora_entrada"]):
            s_ = sesion(o["hora_entrada"])
            if s_ not in ses: ses.append(s_)
        nom = esc(c.get("nombre") or "Resultado")
        filas += (f"<div class='cta'><div><b>{nom}</b><i>{n} {'trade' if n==1 else 'trades'} · {' y '.join(ses)}</i></div>"
                  f"<span class='{'pos' if rt>=0 else 'neg'}'>{r(rt)}</span></div>")
    return (portada_fondo(resolver_portada(dia), basedir), f"<div class='cov'><div class='fecha'>{fecha}</div>{filas}</div>")

def build_cuenta(nombre, ops, imgdir, fecha_corta, n_cuentas, merge_ids=()):
    """merge_ids: ids de operaciones que, por límite de 10 imágenes de Instagram, van en UNA sola
    diapositiva (gráfico reducido + resumen compacto) en vez de gráfico + "Idea de trade" por separado."""
    ops = sorted(ops, key=lambda o: o["hora_entrada"])
    rtot = sum(o["r_real"] for o in ops); cls = "pos" if rtot >= 0 else "neg"
    sesiones = []
    for o in ops:
        s = sesion(o["hora_entrada"])
        if s not in sesiones: sesiones.append(s)
    n = len(ops)
    bodies = []
    for i, o in enumerate(ops, 1):
        img = os.path.join(imgdir, o["id"] + ".png")
        b64 = base64.b64encode(open(img,'rb').read()).decode() if os.path.exists(img) else None
        c = "pos" if o["r_real"] >= 0 else "neg"
        dur = round(o.get("duracion_min") or 0)
        dur_txt = (f"{dur} minuto" if dur == 1 else f"{dur} minutos") if dur < 90 else f"{dur//60} h {dur%60:02d} min"
        kicker = f"<div class='kicker'>{(esc(nombre)+' · ') if nombre and n_cuentas > 1 else ''}{('Trade '+str(i)+' de '+str(n)+' · ') if n > 1 else ''}{sesion(o['hora_entrada'])}</div>"
        t = tipo(o.get("tipo","")) or (ph("[Rotura ZA · ORB · Momentum]") if PREVIEW else "")
        idea = (o.get("reflexion") or "").strip() or (ph("[Por qué entré: una o dos frases]") if PREVIEW else "")
        if o["id"] in merge_ids:
            # diapositiva única: gráfico más pequeño + resumen compacto, para no pasar de 10 imágenes
            idea_corta = idea if len(idea) <= 200 or idea.startswith('<span') else idea[:197].rstrip() + "…"
            fila_setup = f"<div class='row' style='padding:16px 0'><b style=\"min-width:200px;font-size:24px\">Setup</b><span style=\"font-size:36px\">{t}</span></div>" if t else ""
            if b64: bodies.append(f"""{kicker}
              <div class='chart' style='height:560px'><img src='data:image/png;base64,{b64}'></div>
              <div style='margin-top:30px'><h2><span class='{c}'>{r(o['r_real'])}</span> · {dur_txt}</h2></div>
              {fila_setup}
              {f"<p style='font-size:32px;margin-top:14px;color:#d9d5ce'>{esc(idea_corta) if not idea.startswith('<span') else idea}</p>" if idea else ""}""")
            continue
        if b64: bodies.append(f"""{kicker}
          <div class='chart'><img src='data:image/png;base64,{b64}'></div>
          <div style='margin-top:44px'><h1><span class='{c}'>{r(o['r_real'])}.</span> {dur_txt[0].upper()+dur_txt[1:]}.</h1></div>""")
        fila_setup = f"<div class='row'><b>Setup</b><span>{t}</span></div>" if t else ""
        det = []
        if n > 1: det.append(f"{i} de {n}")
        det.append(sesion(o['hora_entrada']))
        if nombre and n_cuentas > 1: det.append(esc(nombre))
        cab = "Idea de trade" + f" <span style='color:#7d7a74;font-size:34px;font-weight:600'>· {' · '.join(det)}</span>"
        fs_idea = 50 if len(idea) < 170 else (44 if len(idea) < 240 else 40)
        bodies.append(f"""<div class='head'>{cab}</div><div class='mid'>
          {f"<p style='font-size:{fs_idea}px'>{esc(idea) if not idea.startswith('<span') else idea}</p>" if idea else ""}
          <div>{fila_setup}
          <div class='row'><b>Dirección</b><span>{'Corto' if o['direccion'].upper().startswith('C') else 'Largo'}</span></div>
          <div class='row'><b>Resultado</b><span class='{c}'>{r(o['r_real'])}</span></div>
          <div class='row'><b>Duración</b><span>{dur_txt}</span></div></div></div>""")
    return bodies

def build(dia, imgdir):
    f = datetime.date.fromisoformat(dia["fecha"])
    fecha_corta = f"{DIAS[f.weekday()]} {f.day} {MESES[f.month-1][:3]}"
    cuentas = dia.get("cuentas") or [{"nombre": "", "ops": dia["ops"]}]
    cuentas = [c for c in cuentas if c.get("ops")]

    # Instagram no admite carruseles de más de 10 imágenes (límite de la plataforma, 15 oct 2026).
    # Reparto de diapositivas (máximo 10):
    #  - con reflexión y hasta 7 trades: portada + trades + reflexión en su diapositiva + cierre en la suya (3 fijas);
    #  - si no cabe (8 trades): reflexión y cierre comparten diapositiva (2 fijas).
    # Cada trade ocupa 2 (gráfico + idea) salvo que haga falta "fundir" algunas en 1 sola para no pasar de 10.
    todas_ops = [o for c in cuentas for o in sorted(c["ops"], key=lambda o: o["hora_entrada"])]
    n_ops = len(todas_ops)
    refl = (dia.get("reflexion") or "").strip()
    hay_refl = bool(refl or PREVIEW)
    separar = hay_refl and n_ops <= 7
    fijas = 3 if separar else 2
    merges_necesarios = max(0, min(n_ops, 2 * n_ops - (10 - fijas)))
    # se funden primero las últimas operaciones del día (las primeras conservan el detalle completo)
    merge_ids = {o["id"] for o in todas_ops[n_ops - merges_necesarios:]} if merges_necesarios else set()

    bodies = [portada(dia, cuentas, imgdir)]
    for c in cuentas:
        bodies += build_cuenta(c.get("nombre",""), c["ops"], imgdir, fecha_corta, len(cuentas), merge_ids)

    cierre = """<h1 style='font-size:80px;line-height:1.05;text-shadow:0 2px 18px rgba(0,0,0,.55)'>Somos lo que hacemos repetidamente.</h1>
      <p style='font-size:32px;color:#e2ddd2'>Will Durant</p>
      <p style='font-size:44px;color:#9be0bd;font-weight:700;margin-top:26px;text-shadow:0 2px 14px rgba(0,0,0,.55)'>Paso corto, vista larga.</p>"""
    # El cierre lleva el fondo de la portada, más difuminado (extra_blur).
    fondo_cierre = portada_fondo(resolver_portada(dia), imgdir, extra_blur=5, extra_oscuro=.2)
    def con_fondo(html): return (fondo_cierre, f"<div class='wrap' style='z-index:3'>{html}</div>")
    if hay_refl:
        txt = esc(refl) if refl else ph("[Lección del día]")
        fs = 44 if len(refl) < 220 else 36
        if separar:
            bodies.append(f"""<div class='head'>Reflexión del día</div><div class='mid' style='gap:56px'>
              <p style='font-size:{fs}px;line-height:1.3'>{txt}</p></div>""")
            bodies.append(con_fondo(f"<div class='mid'>{cierre}</div>"))
        else:
            bodies.append(con_fondo(f"""<div class='head'>Reflexión del día</div><div class='mid' style='gap:56px'>
              <p style='font-size:{fs}px;line-height:1.3'>{txt}</p>
              <div style='border-top:2px solid rgba(241,238,232,.22);padding-top:40px'>{cierre}</div></div>"""))
    else:
        bodies.append(con_fondo(f"<div class='mid'>{cierre}</div>"))
    total = len(bodies)
    if total > 10:
        # salvaguarda extrema (más de 8 trades en un día): se mantiene el límite recortando el cierre,
        # nunca el dato de un trade.
        bodies = bodies[:10]
    total = len(bodies)
    return [page(b, k+1, total) for k, b in enumerate(bodies)]

async def render(pages, out, prefix):
    os.makedirs(out, exist_ok=True); paths=[]
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={'width':1080,'height':1350})
        for i, h in enumerate(pages, 1):
            await pg.set_content(h); await pg.wait_for_timeout(150)
            path = os.path.join(out, f"{prefix}_{i:02d}.png"); await pg.screenshot(path=path); paths.append(path)
        await b.close()
    return paths

if __name__ == "__main__":
    dia = json.load(open(sys.argv[1])); out = sys.argv[2]
    PREVIEW = "--preview" in sys.argv
    pages = build(dia, os.path.dirname(os.path.abspath(sys.argv[1])))
    for p in asyncio.run(render(pages, out, dia["fecha"])): print(p)
