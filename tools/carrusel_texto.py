"""Carrusel de texto (mentalidad) @amoryprofit. Fondo beige, acento naranja (#e4580b desde el 25 oct 2026; titular 76 px, texto 62 px, portada 100 px).
Uso: python3 carrusel_texto.py post.json salida/
post.json = {"id":"m-2026-10-14","slides":[{"arriba":"texto pequeño opcional","grande":"texto grande","naranja":"texto grande en naranja opcional","abajo":"texto pequeño opcional"}, ...]}
- La primera diapositiva es la portada (gancho). Si la portada no trae "naranja", su "grande" sale en naranja.
- Al final se añade sola la diapositiva «Paso corto, vista larga.» salvo que el post traiga "sin_lema": true
  (en ese caso, el lema sale pequeño bajo la última diapositiva).
- Sin nombre de pilar en ningún sitio: pie solo «@amoryprofit» y número.
"""
import asyncio, json, sys, os, html
from playwright.async_api import async_playwright
BG, FG, SUB, NAR = "#ECE0CC", "#2A211B", "#3b3229", "#e4580b"   # papel cálido v5 (27 oct 2026)
CSS=f"""*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1350px;background:{BG};color:{FG};font-family:'Inter Display','Inter',sans-serif;position:relative;overflow:hidden}}
.band{{position:absolute;left:0;top:0;bottom:0;width:18px;background:{NAR}}}
.wrap{{position:absolute;left:96px;right:96px;top:84px;bottom:130px;display:flex;flex-direction:column;justify-content:center;gap:36px}}
.foot{{position:absolute;left:96px;right:84px;bottom:56px;display:flex;justify-content:space-between;font-size:26px;color:#7A6A58;font-weight:500}}
.g{{font-size:76px;line-height:1.06;font-weight:800;letter-spacing:-.02em}}
.p{{font-size:62px;line-height:1.28;font-weight:650;color:{FG}}}
.n{{color:{NAR}}} .lema{{font-size:44px;color:{NAR};font-weight:600;margin-top:16px}}"""
e=lambda t: html.escape(str(t)).replace("\n","<br>")
def body(s, portada=False, lema_peq=False):
    out=[]
    if s.get("arriba"): out.append(f"<div class='p'>{e(s['arriba'])}</div>")
    if s.get("grande"):
        c=" n" if portada and not s.get("naranja") else ""
        fs=" style='font-size:100px'" if portada else ""
        out.append(f"<div class='g{c}'{fs}>{e(s['grande'])}</div>")
    if s.get("naranja"): out.append(f"<div class='g n'>{e(s['naranja'])}</div>")
    if s.get("abajo"): out.append(f"<div class='p'>{e(s['abajo'])}</div>")
    if lema_peq: out.append("<div class='lema'>Paso corto, vista larga.</div>")
    return "".join(out)
def page(b,n,t): return f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body><div class='band'></div><div class='wrap'>{b}</div><div class='foot'><span>@amoryprofit</span><span>{n}/{t}</span></div></body></html>"
async def main(spec,out):
    post=json.load(open(spec)); sl=post["slides"]; sin=post.get("sin_lema",False)
    bodies=[body(s, i==0, sin and i==len(sl)-1) for i,s in enumerate(sl)]
    if not sin: bodies.append("<div class='g' style='font-size:110px'>Paso corto,<br>vista larga.</div>")
    os.makedirs(out,exist_ok=True)
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(viewport={'width':1080,'height':1350})
        for i,h in enumerate(bodies,1):
            await pg.set_content(page(h,i,len(bodies))); await pg.wait_for_timeout(120)
            path=f"{out}/{post['id']}_{i:02d}.png"; await pg.screenshot(path=path); print(path)
        await b.close()
asyncio.run(main(sys.argv[1],sys.argv[2]))
