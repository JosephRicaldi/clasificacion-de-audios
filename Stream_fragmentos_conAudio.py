import subprocess
import tempfile
import os
import time
import whisper
import datetime
import threading
import shutil

# Reproductor (python-vlc)
try:
    import vlc
except Exception as e:
    vlc = None
    print("Aviso: python-vlc no está disponible. El audio no se reproducirá localmente. Instala 'python-vlc' si quieres reproducción.")

# --------------------------
# CONFIG
# --------------------------
STREAM_URL = "https://us-b4-p-e-zs14-audio.cdn.mdstrm.com/live-audio-aw/5fab3416b5f9ef165cfab6e9"
OUTPUT_FILE = "transcripcion.txt"
CHUNK_SECONDS = 5               # leer y transcribir cada 5 segundos
WHISPER_MODEL = "base"          # "small"/"medium" si quieres más precisión (y más RAM/CPU/GPU)
VLC_VOLUME = 80                 # 0..100 volumen local (si se reproduce)

# --------------------------
# Chequear ffmpeg
# --------------------------
if shutil.which("ffmpeg") is None:
    raise SystemExit("ffmpeg no encontrado. Instálalo y asegúrate de que 'ffmpeg' esté en tu PATH.")

# --------------------------
# Cargar Whisper
# --------------------------
print("Cargando modelo Whisper...")
model = whisper.load_model(WHISPER_MODEL)
print("Whisper cargado ✅\n")

# --------------------------
# Flags de parada
# --------------------------
stop_event = threading.Event()

def wait_enter_to_stop():
    input("Presiona ENTER para detener la transcripción y la reproducción...\n")
    stop_event.set()

threading.Thread(target=wait_enter_to_stop, daemon=True).start()

# --------------------------
# Iniciar reproducción local con VLC (opcional)
# --------------------------
player = None
if vlc is not None:
    try:
        # Intentamos crear instancia con mínimos logs
        instance = vlc.Instance("--no-xlib", "--quiet")
        player = instance.media_player_new()
        media = instance.media_new(STREAM_URL)
        player.set_media(media)
        player.audio_set_volume(VLC_VOLUME)
        player.play()
        print("🔊 Reproduciendo en vivo localmente con VLC (si está disponible).")
    except Exception as e:
        print("⚠️ No se pudo iniciar la reproducción con VLC:", e)
        player = None
else:
    print("🔈 Reproducción local deshabilitada (python-vlc no instalado).")

# --------------------------
# Función: grabar N segundos del stream con ffmpeg -> archivo WAV 16k mono
# --------------------------
def grabar_chunk_wav(stream_url, segundos=5):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp.close()
    out_path = tmp.name

    # ffmpeg: -y (sobrescribir), -i (input), -t (duración), -ac 1 (mono), -ar 16000 (sample rate), -vn (no video)
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner", "-loglevel", "error",  # reduce logs
        "-i", stream_url,
        "-t", str(segundos),
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-f", "wav",
        out_path
    ]

    try:
        proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=segundos + 10)
        if proc.returncode != 0:
            # devolver error con stderr para diagnóstico
            err = proc.stderr.decode(errors="ignore")
            if os.path.exists(out_path):
                os.remove(out_path)
            raise RuntimeError(f"ffmpeg returned {proc.returncode}. stderr:\n{err}")
        return out_path
    except subprocess.TimeoutExpired:
        if os.path.exists(out_path):
            os.remove(out_path)
        raise RuntimeError("ffmpeg timeout obteniendo chunk del stream")

# --------------------------
# Función: transcribir y escribir con timestamp
# --------------------------
def transcribe_loop():
    last_text = ""  # para evitar repetición directa
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        while not stop_event.is_set():
            try:
                wav_path = grabar_chunk_wav(STREAM_URL, CHUNK_SECONDS)
            except Exception as e:
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ⚠️ Error al capturar chunk: {e}")
                # si hay fallo severo, esperar un poco y reintentar
                time.sleep(1)
                continue

            # Transcribir con ajustes para evitar repeticiones
            try:
                result = model.transcribe(
                    wav_path,
                    fp16=False,
                    language="es",
                    condition_on_previous_text=False,   # evita que Whisper reutilice texto anterior
                    no_speech_threshold=0.6              # mayor umbral para ignorar silencios
                )
                text = result.get("text", "").strip()

                timestamp = datetime.datetime.now().strftime("[%H:%M:%S]")
                if text:
                    # filtro simple anti-repetición: si es exactamente igual a la anterior no la reescribimos
                    if text != last_text:
                        line = f"{timestamp} {text}"
                        print(line)
                        f.write(line + "\n")
                        f.flush()
                        last_text = text
                    else:
                        # misma frase que se sigue mencionando — la ignoramos para evitar spam
                        print(f"{timestamp} (igual al anterior - salto)")
                else:
                    # no speech detectado en este chunk
                    print(f"{timestamp} (silencio / nada para transcribir)")
            except Exception as e:
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ⚠️ Error transcribiendo: {e}")
            finally:
                # limpiar archivo temporal WAV
                try:
                    if os.path.exists(wav_path):
                        os.remove(wav_path)
                except Exception:
                    pass

# --------------------------
# Ejecutar
# --------------------------
if __name__ == "__main__":
    print("▶️ Empezando captura y transcripción cada", CHUNK_SECONDS, "segundos.")
    print("(Presiona ENTER para detener la transcripción y la reproducción.)\n")
    try:
        transcribe_loop()
    except KeyboardInterrupt:
        stop_event.set()
        print("\n⏹️ Interrumpido por teclado. Terminando...")
    finally:
        # Asegurar que el reproductor se detenga si existe
        if player is not None:
            try:
                player.stop()
                print("🔈 Reproducción detenida.")
            except Exception:
                pass
        print("Proceso finalizado.")