# pickandroll-img: reglas para cualquier sesión que suba piezas aquí

## Vídeos verticales 9:16 (Reels, Shorts, TikTok): ZONA SEGURA, PARA SIEMPRE

Orden de Jaume Salvà (31-10-2026): «Instruccion, baja el texto superior. Usa esta plantilla para la zona segura» y
«Guarda esta instruccion para SIEMPRE». Y, sobre la cuadrícula de Instagram: «No quiero que mi grid se vea asi».

- Plantilla: `plantillas-video/zona-segura-vertical-1080x1920.png`. En 1080x1920, todo texto o logo del montaje
  (cinta de competición, nombre, subtítulos, logos, «Fuente: …») va dentro de **x 61-1019, y 151-1451** y **nunca en
  x > 855 desde y = 698** (botones de la app). Nada por encima de y = 151: lo tapa la barra del móvil.
- Monta los verticales con `plantillas-video/montar_vertical.py` (ya lo coloca todo dentro y pone la portada).
- **Portada de la cuadrícula**: el perfil de Instagram enseña solo el centro 3:4 (y 240-1680). La portada lleva la
  frase literal entera dentro de ese recorte (montar_vertical.py la hace y la pone 0,2 s al principio; en Buffer,
  `video.metadata.thumbnailOffset = 0`). Nunca una portada con el titular cortado ni diez portadas iguales seguidas:
  si hay varios cortes del mismo protagonista, cada portada con su frase y un encuadre distinto.
- **Control bloqueante antes de subir o programar en Buffer**:
  `python3 plantillas-video/control_zona_segura.py <video.mp4>` → solo «ZONA SEGURA OK» se sube. Lee el texto de los
  fotogramas (OCR) y detecta textos fijos; un subagente distinto mira `zona-segura-revision.png` y la portada.
  Con «ZONA SEGURA FALLO» no se sube ni se programa: se vuelve a montar.
- Las historias promo ya aprobadas por Jaume (funko web y café) no se tocan sin su orden.
