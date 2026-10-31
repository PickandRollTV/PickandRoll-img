#!/usr/bin/env python3
"""MONTAJE DE VÍDEOS VERTICALES 9:16 (Reels, Shorts, TikTok) DENTRO DE LA ZONA SEGURA.
Orden 25 de Jaume (31-10-2026, «baja el texto superior», «usa esta plantilla para la zona segura», «guarda esta
instruccion para SIEMPRE») y orden 26 («No quiero que mi grid se vea asi»: portadas de la cuadrícula de Instagram).

Plantilla: zona-segura-vertical-1080x1920.png (esta carpeta). Zona segura x 61-1019, y 151-1451; botones x>855 desde y=698.
Cuadrícula del perfil de Instagram: recorta el centro 3:4 (1080x1440 → y 240-1680). La portada se diseña dentro de
la intersección: x 80-830 (abajo) / 80-1000 (arriba), y 260-1430.

Qué hace:
  1. Fondo 1080x1920 a partir del vídeo (recorte centrado o --x 0-1 para mover el encuadre).
  2. Capa fija (cinta de competición, nombre, logos, fuente) SIEMPRE dentro de la zona segura:
       cinta  y 200-258   ·  nombre y 268-368   ·  subtítulos y 1080-1250, x 240-840
       logos  y 1290-1370 (competición a la izquierda, PickandRollTV a la derecha, hasta x 830)
       fuente y 1385-1430
  3. Subtítulos .srt (opcional) con libass dentro de la caja de subtítulos.
  4. Portada: 0,2 s al principio con frase grande y legible en la cuadrícula; Buffer con thumbnailOffset 0.
  5. Pasa control_zona_segura.py (vídeo) y control_portada_grid (portada). Si falla, NO deja el vídeo final.

Uso:
  python3 montar_vertical.py --video entrada.mp4 --salida salida-9x16.mp4 \
      --cinta "J9 EUROLIGA · FC BARCELONA - VALENCIA BASKET" --nombre "ALEKSANDER SEKULIĆ" \
      --frase "«NUNCA NOS RENDIMOS»" --fuente "Fuente: QuimCam - PickandRollTV" \
      [--competicion euroleague|ligaendesa|ninguna] [--srt subs.srt] [--x 0.5] [--t-portada 3.0]
Deja también <salida>-portada.jpg y zona-segura-revision.png para que los mire un subagente distinto."""
import argparse, os, subprocess, sys, tempfile, textwrap
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

AQUI = os.path.dirname(os.path.abspath(__file__))
PF = '/mnt/project-files'
W, H = 1080, 1920
SEG = (61, 151, 1019, 1451)
BOT = (855, 698)
GRID = (0, 240, 1080, 1680)          # lo que enseña la cuadrícula del perfil (3:4 centrado)
REC = os.path.join(AQUI, 'recursos')     # copia de fuentes y logos junto al script (repo pickandroll-img)


def recurso(nombre, ruta_pf):
    r = os.path.join(REC, nombre)
    return r if os.path.exists(r) else ruta_pf


F_TIT = recurso('Anton.ttf', f'{PF}/estilo/fuentes/Anton.ttf')
F_TXT = recurso('Poppins-Bold.ttf', f'{PF}/estilo/fuentes/Poppins-Bold.ttf')
LOGO_PRT = recurso('logo-pickandrolltv.png', f'{PF}/estilo/logo/02_logo_transparente.png')
LOGOS = {'euroleague': recurso('euroleague-horizontal-blanco.png',
                               f'{PF}/estilo/logos-oficiales/euroleague/euroleague-horizontal-blanco.png'),
         'ligaendesa': recurso('liga-endesa-blanco.png', f'{PF}/estilo/logos-oficiales/liga-endesa-blanco.png')}
AZUL = (0, 77, 152, 255)
GRANATE = (165, 0, 68, 255)
AMARILLO = (255, 204, 0, 255)

# cajas de la plantilla (x0, y0, x1, y1): todas dentro de SEG y fuera de los botones
CAJA_CINTA = (120, 200, 960, 258)
CAJA_NOMBRE = (90, 268, 990, 368)
CAJA_SUBS = (240, 1080, 840, 1250)
CAJA_LOGOS = (80, 1290, 830, 1370)
CAJA_FUENTE = (80, 1385, 830, 1430)
CAJA_FRASE = (80, 1000, 830, 1400)     # portada: frase grande, dentro de cuadrícula y zona segura


def fuente_que_cabe(texto, ruta, ancho, alto, maximo):
    t = maximo
    while t > 12:
        f = ImageFont.truetype(ruta, t)
        b = f.getbbox(texto)
        if b[2] - b[0] <= ancho and b[3] - b[1] <= alto:
            return f
        t -= 2
    return ImageFont.truetype(ruta, 12)


def texto_centrado(d, caja, texto, ruta, color, maximo, sombra=True):
    x0, y0, x1, y1 = caja
    f = fuente_que_cabe(texto, ruta, x1 - x0, y1 - y0, maximo)
    b = d.textbbox((0, 0), texto, font=f)
    x = x0 + (x1 - x0 - (b[2] - b[0])) // 2 - b[0]
    y = y0 + (y1 - y0 - (b[3] - b[1])) // 2 - b[1]
    if sombra:
        d.text((x + 4, y + 4), texto, font=f, fill=GRANATE)
    d.text((x, y), texto, font=f, fill=(255, 255, 255, 255))


def pegar_logo(capa, ruta, caja, alinear):
    if not ruta or not os.path.exists(ruta):
        return
    lg = Image.open(ruta).convert('RGBA')
    lg = lg.crop(lg.getbbox())
    x0, y0, x1, y1 = caja
    esc = min((y1 - y0) / lg.height, (x1 - x0) / lg.width)
    lg = lg.resize((max(1, int(lg.width * esc)), max(1, int(lg.height * esc))), Image.LANCZOS)
    x = x0 if alinear == 'izq' else x1 - lg.width
    capa.alpha_composite(lg, (x, y0 + (y1 - y0 - lg.height) // 2))


def capa_fija(a):
    capa = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    if a.cinta:
        f = fuente_que_cabe(a.cinta, F_TIT, CAJA_CINTA[2] - CAJA_CINTA[0] - 40, 40, 40)
        b = d.textbbox((0, 0), a.cinta, font=f)
        ancho = b[2] - b[0] + 40
        x0 = (W - ancho) // 2
        d.rounded_rectangle((x0, CAJA_CINTA[1], x0 + ancho, CAJA_CINTA[3]), 8, fill=AZUL)
        texto_centrado(d, (x0, CAJA_CINTA[1], x0 + ancho, CAJA_CINTA[3]), a.cinta, F_TIT, (255, 255, 255, 255), 40, sombra=False)
    if a.nombre:
        texto_centrado(d, CAJA_NOMBRE, a.nombre, F_TIT, None, 92)
    mitad = (CAJA_LOGOS[0] + CAJA_LOGOS[2]) // 2
    pegar_logo(capa, LOGOS.get(a.competicion), (CAJA_LOGOS[0], CAJA_LOGOS[1] + 18, mitad - 20, CAJA_LOGOS[3] - 18), 'izq')
    pegar_logo(capa, LOGO_PRT, (mitad + 20, CAJA_LOGOS[1], CAJA_LOGOS[2], CAJA_LOGOS[3]), 'der')
    if a.fuente:
        x0, y0, x1, y1 = CAJA_FUENTE
        f = fuente_que_cabe(a.fuente, F_TXT, x1 - x0, y1 - y0, 30)
        b = d.textbbox((0, 0), a.fuente, font=f)
        x = x0 + (x1 - x0 - (b[2] - b[0])) // 2 - b[0]
        d.text((x + 2, y0 + 2), a.fuente, font=f, fill=(0, 0, 0, 200))
        d.text((x, y0), a.fuente, font=f, fill=(255, 255, 255, 255))
    return capa


def comprobar_capa(capa, nombre):
    """Ningún píxel de la capa fija fuera de la zona segura ni sobre los botones."""
    al = np.asarray(capa)[..., 3] > 20
    fuera = al.copy()
    x0, y0, x1, y1 = SEG
    fuera[y0:y1, x0:x1] = False
    fuera[BOT[1]:, BOT[0]:] |= al[BOT[1]:, BOT[0]:]
    n = int(fuera.sum())
    if n:
        sys.exit(f'ZONA SEGURA FALLO ({nombre}): {n} píxeles de la capa fija fuera de la zona segura. No se monta.')


def control_portada_grid(capa_portada):
    """La frase de la portada entera dentro de lo que enseña la cuadrícula (3:4) y de la zona segura."""
    al = np.asarray(capa_portada)[..., 3] > 20
    ys, xs = np.nonzero(al)
    if not len(ys):
        sys.exit('PORTADA FALLO: la portada no lleva frase.')
    gx0, gy0, gx1, gy1 = GRID
    m = 20
    if ys.min() < gy0 + m or ys.max() > gy1 - m or xs.min() < gx0 + 61 or xs.max() > gx1 - 61:
        sys.exit(f'PORTADA FALLO: la frase se sale de la cuadrícula (y {ys.min()}-{ys.max()}, x {xs.min()}-{xs.max()}).')
    comprobar_capa(capa_portada, 'portada')
    print('PORTADA OK: la frase se lee entera en la cuadrícula del perfil.')



def capa_portada(a):
    capa = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    x0, y0, x1, y1 = CAJA_FRASE
    frase = a.frase.upper()
    for ancho_lin in (12, 14, 16, 18, 22):
        lineas = textwrap.wrap(frase, ancho_lin)
        if len(lineas) <= 3:
            break
    t = 150
    while t > 40:
        f = ImageFont.truetype(F_TIT, t)
        alto = sum(d.textbbox((0, 0), l, font=f)[3] - d.textbbox((0, 0), l, font=f)[1] + 18 for l in lineas)
        anch = max(d.textbbox((0, 0), l, font=f)[2] - d.textbbox((0, 0), l, font=f)[0] for l in lineas)
        if alto <= (y1 - y0) and anch <= (x1 - x0):
            break
        t -= 4
    y = y1 - alto
    for i, l in enumerate(lineas):
        b = d.textbbox((0, 0), l, font=f)
        color = AMARILLO if i == len(lineas) - 1 else (255, 255, 255, 255)
        d.text((x0 - b[0] + 5, y - b[1] + 5), l, font=f, fill=GRANATE)
        d.text((x0 - b[0], y - b[1]), l, font=f, fill=color)
        y += b[3] - b[1] + 18
    # cinta y nombre arriba, también dentro de la cuadrícula (y >= 260)
    if a.nombre:
        f2 = fuente_que_cabe(a.nombre, F_TIT, x1 - x0, 70, 70)
        b = d.textbbox((0, 0), a.nombre, font=f2)
        yy = y0 - 30 - (b[3] - b[1])
        d.rectangle((x0, yy - 14, x0 + b[2] - b[0] + 28, yy + b[3] - b[1] + 14), fill=AZUL)
        d.text((x0 + 14 - b[0], yy - b[1]), a.nombre, font=f2, fill=(255, 255, 255, 255))
    pegar_logo(capa, LOGO_PRT, (x1 - 300, 280, x1 + 160, 380), 'der')
    return capa


def srt_a_ass(srt, ass):
    """Subtítulos en ASS a 1080x1920 reales, dentro de CAJA_SUBS (abajo, centrados, fuera de los botones)."""
    import re
    bloques = re.split(r'\n\s*\n', open(srt, encoding='utf-8-sig').read().strip())
    mv = H - CAJA_SUBS[3]
    cab = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 0\n\n[V4+ Styles]\n"
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
           "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, "
           "MarginR, MarginV, Encoding\n"
           f"Style: S,Anton,70,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,4,0,2,"
           f"{CAJA_SUBS[0]},{W - CAJA_SUBS[2]},{mv},1\n\n[Events]\n"
           "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    def t(x):
        h, m, r = x.strip().replace(',', '.').split(':')
        return f"{int(h)}:{m}:{float(r):05.2f}"
    lin = []
    for b in bloques:
        partes = b.strip().splitlines()
        i = next(k for k, l in enumerate(partes) if '-->' in l)
        ini, fin = partes[i].split('-->')
        txt = '\\N'.join(partes[i + 1:]).upper()
        lin.append(f"Dialogue: 0,{t(ini)},{t(fin)},S,,0,0,0,,{txt}")
    open(ass, 'w', encoding='utf-8').write(cab + '\n'.join(lin) + '\n')


def ffmpeg(*args):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *args], check=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--video', required=True); p.add_argument('--salida', required=True)
    p.add_argument('--cinta', default=''); p.add_argument('--nombre', default='')
    p.add_argument('--frase', required=True, help='frase literal de la portada (entre comillas «»)')
    p.add_argument('--fuente', default='Fuente: PickandRollTV')
    p.add_argument('--competicion', default='euroleague', choices=['euroleague', 'ligaendesa', 'ninguna'])
    p.add_argument('--srt', default=''); p.add_argument('--x', type=float, default=0.5)
    p.add_argument('--t-portada', type=float, default=2.0)
    a = p.parse_args()
    tmp = tempfile.mkdtemp()

    fija = capa_fija(a); comprobar_capa(fija, 'capa fija')
    fija.save(f'{tmp}/fija.png')
    port = capa_portada(a); control_portada_grid(port)

    fondo = (f"scale={W}:{H}:force_original_aspect_ratio=increase,"
             f"crop={W}:{H}:(iw-{W})*{a.x}:(ih-{H})/2,setsar=1")
    # portada: fotograma del vídeo + degradado + frase
    ffmpeg('-ss', str(a.t_portada), '-i', a.video, '-frames:v', '1', '-vf', fondo, f'{tmp}/fot.png')
    base = Image.open(f'{tmp}/fot.png').convert('RGBA')
    grad = Image.new('L', (1, H)); grad.putdata([int(max(0, (y - 700) / 1220) ** 1.2 * 235) for y in range(H)])
    base.alpha_composite(Image.merge('RGBA', [Image.new('L', (W, H), 0)] * 3 + [grad.resize((W, H))]))
    base.alpha_composite(port)
    portada_jpg = os.path.splitext(a.salida)[0] + '-portada.jpg'
    base.convert('RGB').save(portada_jpg, quality=93)

    subs = ''
    if a.srt:
        fd = f'{tmp}/fuentes'; os.makedirs(fd)
        subprocess.run(['cp', F_TIT, fd], check=True)
        srt_a_ass(a.srt, f'{tmp}/subs.ass')
        subs = f",ass='{tmp}/subs.ass':fontsdir='{fd}'"
    ffmpeg('-i', a.video, '-i', f'{tmp}/fija.png', '-filter_complex',
           f'[0:v]{fondo},fps=30[b];[b][1:v]overlay=0:0{subs}[v]', '-map', '[v]', '-map', '0:a?',
           '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
           '-ar', '48000', '-ac', '2', f'{tmp}/cuerpo.mp4')
    # 0,2 s de portada al principio (Buffer: video.metadata.thumbnailOffset = 0)
    ffmpeg('-loop', '1', '-t', '0.2', '-i', portada_jpg, '-f', 'lavfi', '-t', '0.2', '-i',
           'anullsrc=channel_layout=stereo:sample_rate=48000', '-vf', 'fps=30,format=yuv420p', '-c:v', 'libx264',
           '-preset', 'medium', '-crf', '19', '-c:a', 'aac', '-b:a', '192k', '-shortest', f'{tmp}/portada.mp4')
    # mismo vídeo sin montaje: referencia para que el control no confunda los letreros del fondo con el montaje
    ffmpeg('-i', a.video, '-vf', f'{fondo},fps=30', '-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20',
           '-pix_fmt', 'yuv420p', f'{tmp}/fondo.mp4')
    for nom, cuerpo in (('final', 'cuerpo'), ('ref', 'fondo')):
        with open(f'{tmp}/lista-{nom}.txt', 'w') as fh:
            fh.write(f"file '{tmp}/portada.mp4'\nfile '{tmp}/{cuerpo}.mp4'\n")
        ffmpeg('-f', 'concat', '-safe', '0', '-i', f'{tmp}/lista-{nom}.txt', *(['-c', 'copy'] if nom == 'final' else
               ['-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20']), '-movflags', '+faststart', f'{tmp}/{nom}.mp4')

    r = subprocess.run([sys.executable, os.path.join(AQUI, 'control_zona_segura.py'), f'{tmp}/final.mp4',
                        '--ref', f'{tmp}/ref.mp4'])
    if r.returncode:
        sys.exit('No se deja el vídeo final: ZONA SEGURA FALLO.')
    os.replace(f'{tmp}/final.mp4', a.salida)
    print(f'VERTICAL OK: {a.salida}\nPortada: {portada_jpg} (Buffer: thumbnailOffset 0)\n'
          'Falta que un subagente distinto mire zona-segura-revision.png y la portada.')


if __name__ == '__main__':
    main()
