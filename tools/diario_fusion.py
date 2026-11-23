"""Diario con más trades que huecos (máx. 10 imágenes de Instagram). Uso: python3 diario_fusion.py dia.json salida/
Mismo dia.json que carrusel_diario.py y dos campos opcionales:
  "replicas": [[id_op_cuenta1, id_op_cuenta2], ...]  trade copiado en las dos cuentas (mismo gráfico): UNA diapositiva con la R de cada cuenta;
  "pares": [[id_a, id_b, "texto"], ...]  dos trades seguidos y parecidos de la misma cuenta: UNA diapositiva con los dos gráficos.
Con más de 7 trades la reflexión y el cierre comparten diapositiva. Probado el 23 nov 2026 (día del 20 nov, 11 trades)."""
import sys, os, json, asyncio, base64
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import carrusel_diario as C

dia_path, out = sys.argv[1], sys.argv[2]
dia = json.load(open(dia_path)); imgdir = os.path.dirname(os.path.abspath(dia_path))
REPL = dia.pop("replicas", [])   # [[id_cuenta1, id_cuenta2], ...]
PARES = dia.pop("pares", [])     # [[id_a, id_b, "texto común"], ...]
ops = {o["id"]: (c["nombre"], o) for c in dia["cuentas"] for o in c["ops"]}

def b64(i): return base64.b64encode(open(os.path.join(imgdir, i + ".png"), 'rb').read()).decode()
def durtxt(o):
    d = o.get("duracion_min") or 0
    if d < 1: return "menos de 1 minuto"
    d = round(d); return f"{d} minuto" if d == 1 else f"{d} minutos"
def rs(o): return f"<span class='{'pos' if o['r_real']>=0 else 'neg'}'>{C.r(o['r_real'])}</span>"

orig = C.build_cuenta
def build_cuenta(nombre, cops, imgdir_, fecha_corta, n_cuentas, merge_ids=()):
    skip = {b for a, b in REPL} | {p[1] for p in PARES}
    bodies = []
    for o in sorted(cops, key=lambda o: o["hora_entrada"]):
        if o["id"] in skip: continue
        rep = next((b for a, b in REPL if a == o["id"]), None)
        par = next((p for p in PARES if p[0] == o["id"]), None)
        if rep:
            n2, o2 = ops[rep]
            body = orig(nombre, [o], imgdir_, fecha_corta, n_cuentas, {o["id"]})[0]
            body = body.replace(f"<div class='kicker'>{C.esc(nombre)} · ", f"<div class='kicker'>{C.esc(nombre)} y {C.esc(n2)} · ", 1)
            old = f"<h2>{rs(o)} · {durtxt(o)}</h2>"
            new = (f"<h2 style='font-size:50px'>{C.esc(nombre)} {rs(o)} · {C.esc(n2)} {rs(o2)}</h2>"
                   f"<p style='font-size:32px;color:#9a968f;margin-top:6px'>Mismo trade en las dos cuentas · {durtxt(o)}</p>")
            assert old in body, "no encuentro la línea de R"
            body = body.replace(old, new, 1)
            bodies.append(body)
        elif par:
            ob = ops[par[1]][1]; t = C.tipo(o.get("tipo", "")) or ""
            charts = ""
            for x in (o, ob):
                charts += (f"<div style='display:flex;gap:30px;align-items:center;margin-top:18px'>"
                           f"<div style='padding:10px;background:#181b20;border:2px solid #2c3036;border-radius:18px'>"
                           f"<img src='data:image/png;base64,{b64(x['id'])}' style='display:block;width:500px;border-radius:10px'></div>"
                           f"<div><h2 style='font-size:58px'>{rs(x)}</h2><p style='font-size:32px;color:#9a968f'>{durtxt(x)}</p></div></div>")
            fila = f"<div class='row' style='padding:14px 0;margin-top:18px'><b style=\"min-width:200px;font-size:24px\">Setup</b><span style=\"font-size:36px\">{t}</span></div>" if t else ""
            bodies.append(f"<div class='kicker'>{C.esc(nombre)} · Dos reentradas · {C.sesion(o['hora_entrada'])}</div>{charts}{fila}"
                          f"<p style='font-size:36px;line-height:1.3;margin-top:10px;color:#d9d5ce'>{C.esc(par[2])}</p>")
        else:
            bodies += orig(nombre, [o], imgdir_, fecha_corta, n_cuentas, {o["id"]})
    return bodies
C.build_cuenta = build_cuenta

# el reparto de build() cuenta trades reales: con >7 junta reflexión y cierre, que es lo que queremos aquí
pages = C.build(dia, imgdir)
print(len(pages), "diapositivas")
asyncio.run(C.render(pages, out, dia["fecha"]))
