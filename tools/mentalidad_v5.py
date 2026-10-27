"""Carrusel de mentalidad @amoryprofit, estilo v5 (27 oct 2026): papel #ECE0CC, grabado entintado en sepia, ganchos en naranja.
Uso: python3 mentalidad_v5.py post.json salida/
post.json = {"id": "2026-10-31_mentalidad", "grabado": "<id de tools/fondos/grabados.json o ruta a una imagen>", "foco": [x, y] (opcional),
             "gancho": "Frase fuerte de portada", "sub": "Segunda línea, frase completa",
             "slides": [{"titulo": "...", "texto": "..."}, ...]}   (3 interiores = 4 diapositivas; 4 como máximo)
La última diapositiva lleva «Paso corto, vista larga.» debajo."""
import asyncio, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import estilo_v5 as E

post = json.load(open(sys.argv[1])); out = sys.argv[2]
cat = json.load(open(os.path.join(E.IMG, "grabados.json")))["grabados"]
g = next((c for c in cat if c["id"] == post["grabado"]), None)
if g:
    nombre, foco = g["imagen"].rsplit(".", 1)[0], tuple(post.get("foco") or g.get("foco") or (.5, .5))
else:  # ruta a una imagen propia: se copia junto a los fondos con su nombre
    ruta = post["grabado"]; nombre = os.path.splitext(os.path.basename(ruta))[0]
    from PIL import Image
    Image.open(ruta).convert("L").save(os.path.join(E.IMG, nombre + ".jpg"), quality=92)
    foco = tuple(post.get("foco") or (.5, .5))
slides = post["slides"][:4]; t = 1 + len(slides)
pages = [(f"{post['id']}_01", E.mentalidad_portada(nombre, post["gancho"], post.get("sub", ""), 1, t, foco=foco))]
for i, s in enumerate(slides, 2):
    pages.append((f"{post['id']}_{i:02d}", E.mentalidad_interior(s["titulo"], s["texto"], i, t, lema=(i == t))))
asyncio.run(E.render(pages, out))
for n, _ in pages: print(os.path.join(out, n + ".png"))
