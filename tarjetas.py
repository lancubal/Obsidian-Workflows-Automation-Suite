import gitlab
import os
import re
import requests
import uuid
from datetime import datetime

# CONFIGURACIÓN EXTERNA
import config_ia as cfg

# ---------------------

def limpiar_nombre(nombre):
    nombre = nombre.replace(" ", "_")
    return re.sub(r'[\\/*?:"<>|]', "", nombre)

def formatear_fecha(fecha_str):
    if not fecha_str: return ""
    try:
        dt = datetime.fromisoformat(fecha_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M')
    except:
        return fecha_str


def descargar_imagen(url_encontrada, carpeta_destino, token, project_id):
    """
    Descarga imagen usando el hash de GitLab para evitar duplicados.
    """

    # 1. Extraer el 'secret' y el 'filename'
    match = re.search(r'/uploads/([a-f0-9A-F\-]+)/(.*)', url_encontrada)

    if not match:
        return None

    secret = match.group(1)  # Este hash es único y constante en GitLab
    filename_raw = match.group(2)

    # Limpiamos filename
    filename = filename_raw.split('?')[0].split('#')[0]
    nombre_limpio = limpiar_nombre(filename)

    # 2. Generar Nombre DETERMINISTA (Sin UUID aleatorio)
    # Usamos el 'secret' original. Así, si corres el script 100 veces,
    # el nombre generado siempre será idéntico.
    nombre_unico = f"{project_id}_{secret}_{nombre_limpio}"
    ruta_local = os.path.join(carpeta_destino, nombre_unico)

    # 3. VERIFICACIÓN DE EXISTENCIA (La clave del arreglo)
    if os.path.exists(ruta_local):
        # Si ya existe, no descargamos nada y devolvemos el nombre
        # para que el Markdown se genere bien.
        # print(f"      [SKIP] Ya existe: {nombre_unico}") # Descomentar si quieres ver el log
        return nombre_unico

    # 4. Si no existe, procedemos a descargar via API
    url_api = f"{cfg.GITLAB_URL}/api/v4/projects/{project_id}/uploads/{secret}/{filename}"

    try:
        headers = {"PRIVATE-TOKEN": token}
        r = requests.get(url_api, headers=headers, stream=True)

        if r.status_code == 200:
            content_type = r.headers.get('content-type', '')
            if 'text/html' in content_type:
                print(f"      [ERR] HTML recibido (Auth fallida): {url_api}")
                return None

            with open(ruta_local, 'wb') as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)

            print(f"      [IMG] Descargada: {nombre_unico}")
            return nombre_unico
        else:
            print(f"      [ERR] Status {r.status_code}: {url_api}")

    except Exception as e:
        print(f"      [ERR] Excepcion: {e}")

    return None

def procesar_texto_con_imagenes(texto, carpeta_imagenes, token, project_id):
    if not texto: return ""

    # Regex para capturar ![alt](url)
    patron = r'!\[(.*?)\]\((.*?)\)'

    def reemplazar_match(match):
        alt_text = match.group(1)
        url = match.group(2)

        # Solo procesamos si parece un upload interno
        if 'uploads' in url:
            # Notese que ahora pasamos project_id en vez de url base
            archivo_guardado = descargar_imagen(url, carpeta_imagenes, token, project_id)
            if archivo_guardado:
                return f'![{alt_text}](adjuntos/{archivo_guardado})'

        return match.group(0)

    return re.sub(patron, reemplazar_match, texto)


def main():
    # Usamos las variables de cfg
    gl = gitlab.Gitlab(cfg.GITLAB_URL, private_token=cfg.PRIVATE_TOKEN)

    try:
        gl.auth()
        print(f"[OK] Conectado a: {cfg.GITLAB_URL} como {gl.user.username}\n")
    except:
        print("[WARN] Token valido, pero no se pudo obtener usuario completo.\n")

    # Bucle adaptado a la nueva estructura
    for categoria_nombre, proyectos_dict in cfg.PROYECTOS.items():
        cat_limpia = limpiar_nombre(categoria_nombre)
        print(f"[CAT] Procesando: {categoria_nombre}")

        # Ahora 'datos' contiene el diccionario con "nombre" y "tickets"
        for project_id, datos in proyectos_dict.items():
            ticket_ids = datos['tickets']  # Leemos la lista de tickets

            try:
                project = gl.projects.get(project_id)
                proj_limpio = limpiar_nombre(project.name)

                # Usamos cfg.CARPETA_OBSIDIAN
                ruta_final = os.path.join(cfg.CARPETA_OBSIDIAN, cat_limpia, proj_limpio, "Tarjetas")
                ruta_adjuntos = os.path.join(ruta_final, "adjuntos")

                if not os.path.exists(ruta_adjuntos):
                    os.makedirs(ruta_adjuntos)

                print(f"   Repo: {project.name} | Tickets: {len(ticket_ids)}")

                issues = project.issues.list(iids=ticket_ids, get_all=True)

                for issue in issues:
                    # PROCESAR DESCRIPCION
                    desc_procesada = procesar_texto_con_imagenes(
                        issue.description, ruta_adjuntos, cfg.PRIVATE_TOKEN, project_id
                    )

                    nombre_archivo = f"{issue.iid}_{limpiar_nombre(issue.title)}.md"
                    ruta_completa = os.path.join(ruta_final, nombre_archivo)
                    assignee = issue.assignee['name'] if issue.assignee else "Sin asignar"
                    labels = ", ".join(issue.labels)

                    contenido = f"""---
id: {issue.iid}
categoria: "{categoria_nombre}"
proyecto: "{project.name}"
titulo: "{issue.title}"
estado: {issue.state}
link: {issue.web_url}
updated: {issue.updated_at}
---

# [{project.name}] #{issue.iid}: {issue.title}

> **Categoria:** {categoria_nombre}
> **Asignado a:** {assignee}

## Descripcion
{desc_procesada}

---
## Historial
"""
                    notes = issue.notes.list(sort='asc', get_all=True)
                    for note in notes:
                        if not note.system or (note.system and "moved to" in note.body):
                            autor = note.author['name']
                            fecha = formatear_fecha(note.created_at)

                            # PROCESAR COMENTARIOS
                            body_procesado = procesar_texto_con_imagenes(
                                note.body, ruta_adjuntos, cfg.PRIVATE_TOKEN, project_id
                            )

                            contenido += f"\n> **{autor}** ({fecha}):\n\n{body_procesado}\n\n---\n"

                    with open(ruta_completa, "w", encoding="utf-8") as f:
                        f.write(contenido)

                print(f"     -> Completado: /{proj_limpio}")

            except Exception as e:
                print(f"   [ERROR] Project {project_id}: {e}")

            print("------------------------------------------------")

if __name__ == "__main__":
    main()
