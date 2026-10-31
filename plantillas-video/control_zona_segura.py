#!/usr/bin/env python3
"""CONTROL DE ZONA SEGURA DE VÍDEOS VERTICALES (orden 25 de Jaume, 31-10-2026:
«Instruccion, baja el texto superior. Usa esta plantilla para la zona segura» y «Guarda esta instruccion para SIEMPRE»).

Plantilla: zona-segura-vertical-1080x1920.png (en esta carpeta). En 1080x1920:
  - zona segura: x 61-1019, y 151-1451;
  - botones de la app: x > 855 desde y = 698 (zona poco segura).
Los textos y logos FIJOS del montaje (cinta superior, nombre, subtítulos, logos, fuente) tienen que quedar dentro.

Cómo mide: saca 12 fotogramas repartidos por el vídeo, busca bordes nítidos que NO se mueven entre fotogramas (lo que
el montaje pone encima) y mira si alguno cae fuera de la zona segura. La imagen del vídeo, que se mueve, no cuenta.
Además (31-10, 21:15): lee el texto de cada fotograma (OCR, rapidocr) y falla si alguna palabra del montaje cae fuera
de la zona segura, también cuando el vídeo tiene zoom o movimiento (el detector de bordes fijos no lo ve).
Letreros del fondo (patrocinadores de la sala de prensa): --fondo "BARCA,ASSISTENCIA" los ignora; el subagente
revisor tiene que confirmar en zona-segura-revision.png que de verdad son del fondo.
--ref fondo.mp4 (lo pasa montar_vertical.py): el mismo vídeo SIN el montaje; el texto que ya está ahí es del fondo.
Uso:  python3 control_zona_segura.py <video.mp4> [--fondo "PALABRA1,PALABRA2"] [--ref fondo.mp4]   → «ZONA SEGURA OK» o «ZONA SEGURA FALLO» (sale con código 1)
      Deja zona-segura-revision.png (fotograma con la plantilla encima) para que lo mire un subagente distinto.
Ningún vídeo vertical se sube sin «ZONA SEGURA OK» y sin mirar ese PNG."""
import os, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageFilter

W, H = 1080, 1920
SEG = (61, 151, 1019, 1451)          # x0, y0, x1, y1
BOT = (855, 698)                      # botones: x > 855 y y > 698


def fotogramas(video, n=12):
    dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of',
                                         'default=nw=1:nk=1', video]).decode().strip() or 0)
    d = tempfile.mkdtemp()
    out = []
    for i in range(n):
        t = dur * (i + 0.5) / n
        f = os.path.join(d, f'f{i:02d}.png')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t:.2f}', '-i', video, '-frames:v', '1',
                        '-vf', f'scale={W}:{H}', f], check=True)
        out.append(Image.open(f).convert('L'))
    return out


def fuera_mascara():
    m = np.ones((H, W), bool)
    x0, y0, x1, y1 = SEG
    m[y0:y1, x0:x1] = False
    m[BOT[1]:, BOT[0]:] = True
    return m


def ocr_cajas(ocr, f):
    out = []
    res, _ = ocr(f)
    for caja, texto, conf in res or []:
        xs = [q[0] for q in caja]; ys = [q[1] for q in caja]
        out.append((texto, float(conf), min(xs), min(ys), max(xs), max(ys)))
    return out


def solapa(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0])); iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    return ix * iy > 0.3 * (a[2] - a[0]) * (a[3] - a[1])


def ocr_fuera(video, fondo, ref=None, n=10):
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'rapidocr-onnxruntime'], check=True)
        from rapidocr_onnxruntime import RapidOCR
    ocr = RapidOCR()
    dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of',
                                         'default=nw=1:nk=1', video]).decode().strip() or 0)
    d = tempfile.mkdtemp(); malas = {}
    for i in range(n):
        t = 0.3 + (dur - 0.6) * i / max(1, n - 1)
        f = os.path.join(d, f'o{i:02d}.png')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t:.2f}', '-i', video, '-frames:v', '1',
                        '-vf', f'scale={W}:{H}', f], check=True)
        cajas_ref = []
        if ref:
            fr = os.path.join(d, f'r{i:02d}.png')
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t:.2f}', '-i', ref, '-frames:v', '1',
                            '-vf', f'scale={W}:{H}', fr], check=True)
            cajas_ref = [c[2:] for c in ocr_cajas(ocr, fr)]
        for texto, conf, x0, y0, x1, y1 in ocr_cajas(ocr, f):
            if conf < 0.8 or len(texto.strip()) < 2:
                continue
            if any(p and p in texto.upper() for p in fondo):
                continue
            if any(solapa((x0, y0, x1, y1), r) for r in cajas_ref):
                continue   # ya estaba en la imagen de fondo (letreros de la sala), no es del montaje
            if y1 - y0 < 18:
                continue
            fuera = x0 < SEG[0] - 2 or x1 > SEG[2] + 2 or y0 < SEG[1] - 2 or y1 > SEG[3] + 2 or \
                    (x1 > BOT[0] + 2 and y1 > BOT[1])
            if fuera:
                malas.setdefault(texto, (int(x0), int(y0), int(x1), int(y1), round(t, 1)))
    return malas


def main(video, fondo=(), ref=None):
    fs = fotogramas(video)
    bordes = np.stack([np.asarray(f.filter(ImageFilter.FIND_EDGES), np.float32) for f in fs])
    pix = np.stack([np.asarray(f, np.float32) for f in fs])
    fijo = (bordes.min(axis=0) > 60) & (pix.std(axis=0) < 12)   # borde nítido en TODOS los fotogramas y sin moverse
    fijo[:3, :] = fijo[-3:, :] = False; fijo[:, :3] = fijo[:, -3:] = False   # el filtro marca el borde de la imagen
    fuera = fijo & fuera_mascara()
    fallos = []
    for nombre, (ya, yb, xa, xb) in {'arriba (barra del móvil)': (0, SEG[1], 0, W), 'abajo': (SEG[3], H, 0, W),
                                      'izquierda': (0, H, 0, SEG[0]), 'derecha': (0, H, SEG[2], W),
                                      'botones de la derecha': (BOT[1], SEG[3], BOT[0], SEG[2])}.items():
        n = int(fuera[ya:yb, xa:xb].sum())
        if n > 400:
            fallos.append(f'{nombre}: {n} píxeles de texto/logo fijo fuera de la zona segura')
    for texto, (x0, y0, x1, y1, t) in ocr_fuera(video, fondo, ref).items():
        fallos.append(f'texto «{texto}» en x {x0}-{x1}, y {y0}-{y1} (segundo {t}) fuera de la zona segura')
    # revisión visual: fotograma central + plantilla semitransparente
    base = Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'zona-segura-vertical-1080x1920.png')).convert('RGBA').resize((W, H))
    fr = fs[len(fs) // 2].convert('RGBA')
    a = np.asarray(base).copy(); a[..., 3] = np.where(fuera_mascara(), 110, 0)
    Image.alpha_composite(fr, Image.fromarray(a)).convert('RGB').save('zona-segura-revision.png')
    if fallos:
        print('ZONA SEGURA FALLO: no se sube. Baja/mete los textos en la zona segura (orden 25 de Jaume).\n- ' + '\n- '.join(fallos))
        sys.exit(1)
    print('ZONA SEGURA OK. Falta que un subagente distinto mire zona-segura-revision.png.')


if __name__ == '__main__':
    if len(sys.argv) < 2: sys.exit(__doc__)
    fondo = ()
    if '--fondo' in sys.argv:
        fondo = tuple(p.strip().upper() for p in sys.argv[sys.argv.index('--fondo') + 1].split(',') if p.strip())
    ref = sys.argv[sys.argv.index('--ref') + 1] if '--ref' in sys.argv else None
    main(sys.argv[1], fondo, ref)
