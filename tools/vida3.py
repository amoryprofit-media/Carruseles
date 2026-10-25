"""Vida real @amoryprofit: carrusel de 3 imágenes.
1 foto + gancho · 2 reflexión larga sobre la foto desenfocada · 3 foto muy desenfocada + frase final + lema.
Uso: python3 vida3.py foto_filtrada.jpg salida_prefijo "Gancho" "Titular diapo 2" "Párrafo diapo 2" "Frase diapo 3"
Sin nombre de pilar; pie solo @amoryprofit y número."""
import asyncio, base64, sys
from io import BytesIO
from PIL import Image, ImageFilter, ImageEnhance
from playwright.async_api import async_playwright

foto, out, gancho, titular, parrafo, final = sys.argv[1:7]
BAND = "#8a9bb0"

def b64(im):
    buf = BytesIO(); im.save(buf, "JPEG", quality=90); return base64.b64encode(buf.getvalue()).decode()

im = Image.open(foto).convert("RGB")
f1 = b64(im)
f2 = b64(ImageEnhance.Brightness(im.filter(ImageFilter.GaussianBlur(26))).enhance(0.40))
f3 = b64(ImageEnhance.Brightness(im.filter(ImageFilter.GaussianBlur(60))).enhance(0.42))

BASE = """*{margin:0;box-sizing:border-box}
body{width:1080px;height:1350px;position:relative;overflow:hidden;font-family:'Inter Display','Inter',sans-serif;color:#f5f0e8}
.band{position:absolute;left:0;top:0;bottom:0;width:18px;background:%s;z-index:3}
.f{position:absolute;left:96px;right:84px;bottom:56px;display:flex;justify-content:space-between;font-size:26px;color:#cfc8bd;z-index:3}
.w{position:absolute;left:96px;right:96px;top:0;bottom:130px;display:flex;flex-direction:column;justify-content:center;gap:34px}
.h{font-weight:800;line-height:1.08;letter-spacing:-.02em;text-wrap:balance;text-shadow:0 2px 16px rgba(0,0,0,.5)}
.l{font-size:44px;color:#b9c6d6;font-weight:600;margin-top:20px}""" % BAND

S1 = f"""<html><head><meta charset='utf-8'><style>{BASE}
body{{background:url(data:image/jpeg;base64,{f1}) center/cover}}
.g{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(10,11,13,0) 35%,rgba(10,11,13,.55) 62%,rgba(10,11,13,.92) 100%)}}
.h1{{position:absolute;left:96px;right:96px;bottom:150px;font-size:92px;z-index:2}}
</style></head><body><div class='band'></div><div class='g'></div><div class='h h1'>{gancho}</div>
<div class='f'><span>@amoryprofit</span><span>1/3</span></div></body></html>"""

S2 = f"""<html><head><meta charset='utf-8'><style>{BASE}
body{{background:url(data:image/jpeg;base64,{f2}) center/cover}}
.t{{font-size:70px}}
.p{{font-size:41px;line-height:1.38;color:#e6e0d6;white-space:pre-line;text-shadow:0 1px 10px rgba(0,0,0,.45)}}
</style></head><body><div class='band'></div><div class='w'>
<div class='h t'>{titular}</div><div class='p'>{parrafo}</div></div>
<div class='f'><span>@amoryprofit</span><span>2/3</span></div></body></html>"""

S3 = f"""<html><head><meta charset='utf-8'><style>{BASE}
body{{background:url(data:image/jpeg;base64,{f3}) center/cover}}
.t{{font-size:84px}}
</style></head><body><div class='band'></div><div class='w'>
<div class='h t'>{final}</div><div class='l'>Paso corto, vista larga.</div></div>
<div class='f'><span>@amoryprofit</span><span>3/3</span></div></body></html>"""

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={"width": 1080, "height": 1350})
        for i, h in enumerate((S1, S2, S3), 1):
            await pg.set_content(h); await pg.wait_for_timeout(200)
            await pg.screenshot(path=f"{out}_{i:02d}.png"); print(f"{out}_{i:02d}.png")
        await b.close()

asyncio.run(main())
