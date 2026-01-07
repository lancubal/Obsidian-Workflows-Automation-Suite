# 🧠 Obsidian Workflows & Automation Suite

Este repositorio contiene una colección de scripts en Python diseñados para centralizar toda la información laboral y personal (Tickets, Reuniones y Comunicaciones) en **Obsidian**, creando una "Fuente Única de Verdad".

El sistema automatiza la ingesta de datos desde diversas fuentes, procesándolos con IA (Local y Cloud) para generar notas estructuradas y accionables.

## 🚀 Módulos del Sistema

### 1. 🎫 GitLab Sync
Sincroniza issues/tickets asignados desde GitLab hacia Obsidian.
- **Funcionalidades:**
    - Descarga descripciones completas de los tickets.
    - **Gestión Inteligente de Imágenes:** Descarga adjuntos usando el hash único de GitLab para evitar duplicados.
    - Organiza automáticamente en carpetas: `Categoría > Proyecto > Tarjetas`.
    - Actualiza tickets existentes sin sobrescribir notas manuales.

### 2. 🎙️ Meeting Assistant
Convierte grabaciones de reuniones en notas de Obsidian procesadas.
- **Flujo de Trabajo:**
    1. **Transcribe:** Usa **OpenAI Whisper** (local) para convertir audio a texto con alta precisión.
    2. **Resume:** Usa **Google Gemini 1.5 Flash** (API) para generar Objetivos, Action Items y Decisiones Técnicas.
    3. **Archiva:** Comprime el video original (FFmpeg) para ahorrar espacio y lo mueve a un disco de backup.
    4. **Conserva:** Guarda tanto el resumen IA como la transcripción literal ("bruta") para búsquedas futuras.

### 3. ⚡ Quick Capture
Herramienta de captura universal (agnóstica a la aplicación) para Mails, Chats (Teams/Slack) y Logs.
- **Uso:** Funciona en segundo plano. Al seleccionar texto y presionar `Ctrl + Alt + M`:
    - Simula `Ctrl+C`.
    - Detecta el proyecto de destino mediante menú interactivo.
    - Genera una nota Markdown con el contenido y un prompt para IA.
    - Funciona sobre Firefox, Terminal, PDFs, etc.

---

## 🛠️ Requisitos Previos

### Sistema
- **Python 3.10+**
- **FFmpeg** instalado y agregado al PATH del sistema (necesario para Whisper y compresión de video).
- **Obsidian** (para visualizar las notas generadas).

### Librerías de Python
Instala las dependencias con:
```bash
pip install openai-whisper python-gitlab google-generativeai keyboard pyperclip
