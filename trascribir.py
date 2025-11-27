import whisper
import os
import datetime
import shutil
import warnings
import subprocess
import sys

import re

# IMPORTAMOS LA CONFIGURACIÓN EXTERNA
import config_ia as cfg

warnings.filterwarnings("ignore")


def verificar_ffmpeg():
    if not shutil.which("ffmpeg"):
        print("❌ Error: FFmpeg no encontrado.")
        return False
    return True

def limpiar_nombre(nombre):
    """Reemplaza espacios por guiones bajos y quita caracteres raros"""
    nombre = nombre.replace(" ", "_")
    return re.sub(r'[\\/*?:"<>|]', "", nombre)


def seleccionar_destino():
    opciones = []
    print("\n📂 ¿A qué proyecto pertenece esta reunión?")

    idx = 1
    for cat, proyectos in cfg.PROYECTOS.items():
        print(f"\n--- {cat} ---")

        # Limpiamos el nombre de la categoría (ej: "Trabajo Principal" -> "Trabajo_Principal")
        cat_limpia = limpiar_nombre(cat)

        for pid, datos in proyectos.items():
            nombre_proyecto = datos['nombre']

            # Limpiamos el nombre del proyecto (ej: "ARBA RECAUDA" -> "ARBA_RECAUDA")
            proj_limpio = limpiar_nombre(nombre_proyecto)

            print(f" {idx}. {nombre_proyecto}")

            opciones.append({
                "categoria": cat,
                "proyecto": nombre_proyecto,
                # Agregamos "Reuniones" al path
                "ruta_md": os.path.join(cfg.CARPETA_OBSIDIAN, cat_limpia, proj_limpio, "Reuniones"),
                "ruta_video": os.path.join(cfg.CARPETA_VIDEOS_ARCHIVADOS, cat_limpia, proj_limpio)
            })
            idx += 1

    try:
        entrada = input("\n👉 Elige el número: ")
        if not entrada.isdigit(): return None
        seleccion = int(entrada) - 1
        if 0 <= seleccion < len(opciones):
            return opciones[seleccion]
    except:
        pass
    print("❌ Selección inválida.")
    return None


def comprimir_y_archivar(ruta_original, info_destino):
    nombre_original = os.path.basename(ruta_original)
    nombre_sin_ext = os.path.splitext(nombre_original)[0]

    if not os.path.exists(info_destino["ruta_video"]):
        os.makedirs(info_destino["ruta_video"])

    ruta_destino_final = os.path.join(info_destino["ruta_video"], f"{nombre_sin_ext}_comprimido.mp4")

    print(f"\n[3/3] 🗜️ Comprimiendo video...")

    comando = [
        "ffmpeg", "-y",
        "-i", ruta_original,
        "-vcodec", "libx264", "-crf", "28", "-preset", "veryfast", "-acodec", "aac",
        ruta_destino_final
    ]

    try:
        subprocess.run(comando, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(ruta_destino_final):
            print(f"✅ Video archivado en: {ruta_destino_final}")
            os.remove(ruta_original) # Descomentar para borrar original
    except Exception as e:
        print(f"❌ Error comprimiendo: {e}")


def transcribir_reunion(ruta_archivo):
    if not verificar_ffmpeg(): return
    ruta_archivo = ruta_archivo.strip('"')

    if not os.path.exists(ruta_archivo):
        print(f"❌ Archivo no encontrado.")
        return

    info_destino = seleccionar_destino()
    if not info_destino: return

    print(f"\n[1/3] 🧠 Cargando Whisper ({cfg.MODELO_WHISPER})...")
    model = whisper.load_model(cfg.MODELO_WHISPER)

    print(f"[2/3] 👂 Transcribiendo...")
    result = model.transcribe(ruta_archivo, fp16=False)

    # --- GUARDADO ---
    nombre_archivo = os.path.basename(ruta_archivo)
    fecha_hoy = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    fecha_corta = datetime.datetime.now().strftime("%Y-%m-%d")

    if not os.path.exists(info_destino["ruta_md"]):
        os.makedirs(info_destino["ruta_md"])

    ruta_md = os.path.join(info_destino["ruta_md"], f"Reunion_{fecha_corta}_{os.path.splitext(nombre_archivo)[0]}.md")

    # PROMPT MAESTRO INCRUSTADO
    contenido = f"""--- 
`🤖 INSTRUCCIONES PARA ASISTENTE IA (Copilot / Cursor):
Analiza la transcripción de abajo y genera un resumen ejecutivo AQUÍ MISMO (arriba de la transcripción).
Tu respuesta debe incluir:
1. 🎯 Objetivo: ¿Para qué fue esta reunión? (Máx 2 líneas)
2. ✅ Action Items: Lista de tareas detectadas, asignados y fechas (Checkboxes [ ]).
3. 💡 Decisiones Técnicas: Acuerdos sobre código, arquitectura o flujos.
4. ⚠️ Riesgos/Bloqueos: Qué está impidiendo avanzar.
Ignora la charla informal y céntrate en el valor técnico.`
tipo: reunion
fecha: {fecha_hoy}
archivo_original: "{nombre_archivo}"
proyecto: "{info_destino['proyecto']}"
tags: [reunion, pendiente_resumen]
---

# 🎙️ Reunión: {info_destino['proyecto']}
**Fecha:** {fecha_hoy}

## 📝 Transcripción Automática

{result["text"].strip()}
"""
    with open(ruta_md, "w", encoding="utf-8") as f:
        f.write(contenido)

    print(f"✅ Nota creada con Prompt IA: {ruta_md}")

    # Comprimir y archivar (según tu script previo)
    comprimir_y_archivar(ruta_archivo, info_destino)


if __name__ == "__main__":
    # RUTA DE PRUEBA
    ARCHIVO = r"C:\Users\agustin.lancuba\PycharmProjects\SCRIPTSARBA\videoplayback.mp4"
    transcribir_reunion(ARCHIVO)