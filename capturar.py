import keyboard
import pyperclip
import time
import os
import datetime
import re
import sys
import ctypes
import traceback  # Para ver el error completo
from config_ia import PROYECTOS, CARPETA_OBSIDIAN

# --- CONFIGURACIÓN ---
HOTKEY = "ctrl+alt+m"
# ---------------------

activar_captura = False


def limpiar_nombre(nombre):
    nombre = nombre.replace(" ", "_")
    return re.sub(r'[\\/*?:"<>|]', "", nombre)


def forzar_primer_plano():
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd != 0:
            ctypes.windll.user32.ShowWindow(hwnd, 9)
            ctypes.windll.user32.keybd_event(0x12, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0x12, 0, 2, 0)
            ctypes.windll.user32.SetForegroundWindow(hwnd)
    except Exception as e:
        print(f"⚠️ No pude traer la ventana al frente: {e}")


def seleccionar_proyecto_consola():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"\n🚀 ¡Captura Activada!")
    print("📂 ¿A qué proyecto pertenece?")

    opciones = []
    idx = 1
    for cat, proyectos_dict in PROYECTOS.items():
        print(f"\n--- {cat} ---")
        cat_limpia = limpiar_nombre(cat)
        for pid, datos in proyectos_dict.items():
            print(f" {idx}. {datos['nombre']}")
            opciones.append({
                "proyecto": datos['nombre'],
                # Agregamos "Capturas" al path
                "ruta_md": os.path.join(CARPETA_OBSIDIAN, cat_limpia, limpiar_nombre(datos['nombre']), "Capturas")
            })
            idx += 1

    try:
        # Limpiar buffer de teclado
        while keyboard.is_pressed('enter'): pass

        entrada = input("\n👉 Elige número: ")
        if entrada.isdigit():
            seleccion = int(entrada) - 1
            if 0 <= seleccion < len(opciones):
                return opciones[seleccion]
    except:
        pass
    return None


def realizar_captura():
    try:
        # 1. PAUSA VITAL: Esperar a que sueltes las teclas Ctrl+Alt
        print("✋ Soltando teclas...", end="\r")
        time.sleep(0.5)

        # 2. Limpiar portapapeles
        pyperclip.copy("")

        # 3. Enviar Ctrl+C
        print("✂️ Copiando...", end="\r")
        keyboard.send('ctrl+c')

        # 4. Esperar texto (Timeout de 2 segundos)
        texto = ""
        intentos = 0
        while intentos < 20:  # 20 * 0.1 = 2 segundos
            time.sleep(0.1)
            texto = pyperclip.paste()
            if texto.strip():
                break
            intentos += 1

        if not texto.strip():
            print("\n❌ FALLÓ LA COPIA: No se detectó texto seleccionado.")
            print("   Asegúrate de haber seleccionado el texto antes de presionar las teclas.")
            time.sleep(2)
            return

        # 5. Traer ventana
        forzar_primer_plano()

        # 6. Lógica normal
        destino = seleccionar_proyecto_consola()
        if not destino:
            print("❌ Cancelado.")
            return

        asunto = input("📝 Asunto/Título breve: ")
        if not asunto: asunto = "Nota_Rapida"

        fecha_larga = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        fecha_corta = datetime.datetime.now().strftime("%Y-%m-%d")

        nombre_archivo = f"Captura_{fecha_corta}_{limpiar_nombre(asunto)[:40]}.md"
        ruta_completa = os.path.join(destino['ruta_md'], nombre_archivo)

        if not os.path.exists(destino['ruta_md']):
            os.makedirs(destino['ruta_md'])

        md_content = f"""---
tipo: captura
fecha: {fecha_larga}
asunto: "{asunto}"
proyecto: "{destino['proyecto']}"
tags: [captura_rapida]
---
# 📥 {asunto}
**Fecha:** {fecha_larga}

## Contenido
{texto}
"""
        with open(ruta_completa, "w", encoding="utf-8") as f:
            f.write(md_content)

        print(f"\n✅ Guardado en: {ruta_completa}")
        time.sleep(1.5)

    except Exception as e:
        # AQUI CAPTURAMOS EL ERROR ROJO
        print("\n\n" + "=" * 30)
        print("❌ ERROR FATAL EN CAPTURA")
        print("=" * 30)
        traceback.print_exc()  # Imprime el error completo
        print("=" * 30)
        input("\n⚠️ Presiona ENTER para continuar (no se cerrará)...")


def main():
    global activar_captura

    print(f"👀 Escuchando... Selecciona texto y presiona [{HOTKEY}]")
    print("   (Minimiza esta ventana, pero no la cierres)")

    def trigger():
        global activar_captura
        activar_captura = True

    keyboard.add_hotkey(HOTKEY, trigger)

    while True:
        if activar_captura:
            realizar_captura()
            activar_captura = False

            os.system('cls' if os.name == 'nt' else 'clear')
            print(f"👀 Escuchando... [{HOTKEY}]")

        time.sleep(0.1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("❌ El script se rompió en el nivel principal:")
        traceback.print_exc()
        input("Presiona ENTER para salir...")