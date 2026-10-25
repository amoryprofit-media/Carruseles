"""Filtro común de las fotos de vida real @amoryprofit (25 oct 2026).
Uso: python3 filtro_foto.py entrada.jpg salida.jpg [x0,y0,ancho]   (recorte 4:5 opcional; alto = ancho*1.25)
Pasos: recorte 4:5 → 1080x1350 → saturación x1,5 + contraste 1,08 → filtro: Color 0,65, rojo x1,05, azul x0,92, grano 4,5 %.
Antes: revisar la foto con Read; difuminar con PIL lo que identifique (rótulos, matrículas, nombres, cara, corcho con fotos)."""
import sys
from PIL import Image, ImageEnhance
import numpy as np
im = Image.open(sys.argv[1]).convert("RGB")
if len(sys.argv) > 3:
    x0, y0, w = map(int, sys.argv[3].split(",")); im = im.crop((x0, y0, x0 + w, y0 + int(w * 1.25)))
im = im.resize((1080, 1350), Image.LANCZOS)
im = ImageEnhance.Contrast(ImageEnhance.Color(im).enhance(1.5)).enhance(1.08)
im = ImageEnhance.Color(im).enhance(0.65)
a = np.array(im).astype(float); a[..., 0] *= 1.05; a[..., 2] *= 0.92
a += np.random.normal(0, 255 * 0.045, a.shape[:2])[..., None]
Image.fromarray(a.clip(0, 255).astype("uint8")).save(sys.argv[2], quality=92)
