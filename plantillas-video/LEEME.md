# Plantilla de vídeo vertical 9:16 con zona segura

```
pip install rapidocr-onnxruntime   # lo instala solo el control si falta
python3 montar_vertical.py --video corte.mp4 --salida video/AAAA-MM-DD/nombre-9x16.mp4 \
  --cinta "J9 EUROLIGA · FC BARCELONA - VALENCIA BASKET" --nombre "ALEKSANDER SEKULIĆ" \
  --frase "«Nunca nos rendimos»" --fuente "Fuente: QuimCam - PickandRollTV" \
  --competicion euroleague --srt subtitulos.srt [--x 0.5] [--t-portada 2]
```

- Cajas (1080x1920): cinta y 200-258 · nombre y 268-368 · subtítulos y 1080-1250, x 240-840 · logos y 1290-1370,
  hasta x 830 · fuente y 1385-1430. Todo dentro de la zona segura (x 61-1019, y 151-1451, sin tocar x>855 desde y=698).
- Portada: frase literal grande dentro del recorte 3:4 de la cuadrícula (y 240-1680), 0,2 s al principio del vídeo.
  En Buffer, `assets[].video.metadata.thumbnailOffset = 0`.
- El montaje pasa solo `control_zona_segura.py` (con `--ref` del vídeo sin montaje, para no confundir los letreros de
  la sala de prensa con texto nuestro) y el control de la portada. Si falla, no deja el vídeo final.
- Vídeos montados con otra herramienta: `python3 control_zona_segura.py video.mp4` antes de subirlos.
