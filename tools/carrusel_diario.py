"""Carrusel de diario @amoryprofit.
Uso: python3 carrusel_diario.py dia.json salida/   (las imágenes de cada op: <op_id>.png junto al json)
dia.json = {"fecha":"2026-10-09","reflexion":"<valoración del día>","ops":[{id,hora_entrada,direccion,duracion_min,r_real,tipo,reflexion(=frase del trade)}]}
--preview muestra huecos amarillos para lo que falte; sin él, lo que falte simplemente no sale.
Estructura: portada (gráfico del 1.er trade + R del día) · idea del trade 1 · por cada trade siguiente: gráfico + idea · reflexión del día · cierre.
Tipos del journal -> Instagram: Tipo 1 = Rotura ZA, Tipo 2 = ORB, Tipo 3 = Momentum.
"""
import asyncio, base64, json, sys, os, datetime
from playwright.async_api import async_playwright

TIPOS = {"1":"Rotura ZA","tipo 1":"Rotura ZA","2":"ORB","tipo 2":"ORB","3":"Momentum","tipo 3":"Momentum"}
DIAS = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
MESES = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
CIERRES = {
 1: ("Un día más.<br>Un paso más.", None),
 2: ("Sigo.", None),
 3: ("Todavía no.<br>Pero sigo.", None),
}
def r(x): s=f"{x:+.1f}".replace('.',',').replace('+','+').replace('-','−'); return s+"R"
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
.chart{width:100%;height:760px;border-radius:18px;overflow:hidden;margin-top:36px;background:#c5c5c5}
.chart img{width:100%;height:100%;object-fit:cover;object-position:50% 46%}
.pos{color:#6fbf95}.neg{color:#d9776b}
.big{font-size:230px;font-weight:800;letter-spacing:-.04em;line-height:1}
"""
def page(body, n, total, label="Diario"):
    return f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body><div class='band'></div><div class='wrap'>{body}</div><div class='foot'><span>@amoryprofit</span><span>{n}/{total}</span></div></body></html>"

def build(dia, imgdir):
    ops = sorted(dia["ops"], key=lambda o: o["hora_entrada"])
    f = datetime.date.fromisoformat(dia["fecha"])
    fecha_larga = f"{DIAS[f.weekday()]} {f.day} de {MESES[f.month-1]}"
    fecha_corta = f"{DIAS[f.weekday()]} {f.day} {MESES[f.month-1][:3]}"
    rtot = sum(o["r_real"] for o in ops); cls = "pos" if rtot >= 0 else "neg"
    sesiones = []
    for o in ops:
        s = sesion(o["hora_entrada"]); 
        if s not in sesiones: sesiones.append(s)
    n = len(ops)
    bodies = []
    # 1 · Portada del día: gráfico del primer trade + resultado del día
    o1 = ops[0]
    b64_1 = base64.b64encode(open(os.path.join(imgdir, o1["id"] + ".png"),'rb').read()).decode()
    bodies.append(f"""<div class='kicker'>{fecha_corta}</div>
      <div class='chart'><img src='data:image/png;base64,{b64_1}'></div>
      <div style='margin-top:40px;display:flex;align-items:baseline;gap:34px;flex-wrap:wrap'>
        <span class='{cls}' style='font-size:128px;font-weight:800;letter-spacing:-.03em;line-height:1'>{r(rtot)}</span>
        <span style='font-size:46px;font-weight:700'>{n} {'trade' if n==1 else 'trades'} · {' y '.join(sesiones)}</span></div>""")
    # por trade
    for i, o in enumerate(ops, 1):
        img = os.path.join(imgdir, o["id"] + ".png")
        b64 = base64.b64encode(open(img,'rb').read()).decode()
        c = "pos" if o["r_real"] >= 0 else "neg"
        dur = round(o.get("duracion_min") or 0)
        dur_txt = f"{dur} minutos" if dur < 90 else f"{dur//60} h {dur%60:02d} min"
        if i > 1: bodies.append(f"""<div class='kicker'>Trade {i} de {n} · {sesion(o['hora_entrada'])}</div>
          <div class='chart'><img src='data:image/png;base64,{b64}'></div>
          <div style='margin-top:44px'><h1><span class='{c}'>{r(o['r_real'])}.</span> {dur_txt[0].upper()+dur_txt[1:]}.</h1></div>""")
        t = tipo(o.get("tipo","")) or (ph("[Rotura ZA · ORB · Momentum]") if PREVIEW else "")
        idea = (o.get("reflexion") or "").strip() or (ph("[Por qué entré: una o dos frases]") if PREVIEW else "")
        fila_setup = f"<div class='row'><b>Setup</b><span>{t}</span></div>" if t else ""
        cab = f"Idea de trade" + (f" <span style='color:#7d7a74;font-size:34px;font-weight:600'>· {i} de {n} · {sesion(o['hora_entrada'])}</span>" if n > 1 else "")
        bodies.append(f"""<div class='head'>{cab}</div><div class='mid'>
          {f"<p style='font-size:50px'>{esc(idea) if not idea.startswith('<span') else idea}</p>" if idea else ""}
          <div>{fila_setup}
          <div class='row'><b>Dirección</b><span>{'Corto' if o['direccion'].upper().startswith('C') else 'Largo'}</span></div>
          <div class='row'><b>Resultado</b><span class='{c}'>{r(o['r_real'])}</span></div>
          <div class='row'><b>Duración</b><span>{dur_txt}</span></div></div></div>""")
    # Reflexión del día
    refl = (dia.get("reflexion") or "").strip()
    if refl or PREVIEW:
        txt = esc(refl) if refl else ph("[Lección del día]")
        fs = 54 if len(refl) < 220 else 44
        bodies.append(f"""<div class='head'>Reflexión del día</div><div class='mid'><p style='font-size:{fs}px;line-height:1.3'>{txt}</p></div>""")
    # Cierre: cita + lema
    bodies.append("""<div class='mid'><h1 style='font-size:96px;line-height:1.05'>Somos lo que hacemos repetidamente.</h1>
      <p style='font-size:34px;color:#7d7a74'>Will Durant</p>
      <p style='font-size:46px;color:#4f8a6f;font-weight:600;margin-top:30px'>Paso corto, vista larga.</p></div>""")
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
