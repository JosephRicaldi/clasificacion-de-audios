import os
import math
import time
import datetime
import threading
import tempfile
import collections
import shutil
import subprocess
import unicodedata
import whisper
import re

# ---------- Normalización ----------
def normalizar(s: str) -> str:
    s = s.strip().lower()
    # quitar tildes
    return ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )

# Leer palabras clave normalizadas
with open("palabras_clave.txt", "r", encoding="utf-8-sig") as f:
    KEYWORDS = [normalizar(line) for line in f if line.strip()]

# -------- CONFIG --------
STREAM_URL = "https://us-b4-p-e-zs14-audio.cdn.mdstrm.com/live-audio-aw/5fab3416b5f9ef165cfab6e9"
CHUNK_SECONDS = 20
PRE_ROLL = 20
POST_ROLL = 20
EXTRA_POST_CHUNKS = 0   # puedes poner 1 si quieres 1 chunk extra
OUTPUT_DIR = "noticias_guardadas"
WHISPER_MODEL = "small"
COOLDOWN_SECONDS = 30   # no guardar otra noticia en este lapso

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Cargar modelo
print("Cargando modelo Whisper...")
model = whisper.load_model(WHISPER_MODEL)
print("Whisper cargado ✅\n")

# stop flag
stop_event = threading.Event()

def wait_enter_to_stop():
    input("Presiona ENTER para detener la transcripción...\n")
    stop_event.set()

threading.Thread(target=wait_enter_to_stop, daemon=True).start()

# buffer ajustado por chunks (usar ceil)
pre_chunks = math.ceil(PRE_ROLL / CHUNK_SECONDS)
post_chunks = math.ceil(POST_ROLL / CHUNK_SECONDS)

BufferItem = collections.namedtuple("BufferItem", ["wav_path", "text"])
buffer = collections.deque(maxlen=pre_chunks + 2)  # un poco de margen

last_saved_ts = 0.0

def safe_remove(path):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass

def grabar_chunk_wav(url, seconds, out_path):
    cmd = [
        "ffmpeg",
        "-y",
        "-i", url,
        "-t", str(seconds),
        "-ac", "1", "-ar", "16000",
        out_path
    ]
    # capturar errores para debug
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        err = proc.stderr.decode(errors="ignore")
        raise RuntimeError(f"ffmpeg error: {err}")

# función auxiliar para coincidencias exactas con regex
def contiene_keyword(texto, keywords):
    for kw in keywords:
        if re.search(rf"\b{re.escape(kw)}\b", texto):
            return True
    return False

def transcribe_loop():
    global last_saved_ts
    while not stop_event.is_set():
        try:
            # si buffer está lleno, eliminar el item más viejo del disco antes de añadir
            if len(buffer) >= buffer.maxlen:
                old = buffer.popleft()
                safe_remove(old.wav_path)

            # crear wav temporal y grabar chunk
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpfile:
                wav_path = tmpfile.name
            grabar_chunk_wav(STREAM_URL, CHUNK_SECONDS, wav_path)

            # transcribir y normalizar texto
            result = model.transcribe(
                wav_path,
                fp16=False,
                language="es",
                condition_on_previous_text=True,
                no_speech_threshold=0.6
            )
            raw_text = result.get("text", "").strip()
            text = normalizar(raw_text)

            timestamp = datetime.datetime.now().strftime("[%H:%M:%S]")
            if text:
                print(f"{timestamp} {raw_text}")
                buffer.append(BufferItem(wav_path, text))

                # debug: coincidencias exactas
                matched = [k for k in KEYWORDS if re.search(rf"\b{re.escape(k)}\b", text)]
                if matched:
                    print("👉 Coincidencias exactas:", matched)

                # chequeo de keywords exactos
                if contiene_keyword(text, KEYWORDS):
                    now = time.time()
                    if now - last_saved_ts < COOLDOWN_SECONDS:
                        print("Cooldown activo — no se guarda (evitando duplicados).")
                        continue

                    print(f"⚡ DETECTADA NOTICIA: {raw_text}")

                    # nombre con formato: año-mes-día-hora-minuto_lima
                    timestamp_name = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M") + "_lima"

                    folder = os.path.join(OUTPUT_DIR, timestamp_name)
                    os.makedirs(folder, exist_ok=True)

                    # ruta del archivo .txt con el mismo nombre
                    txt_path = os.path.join(folder, f"{timestamp_name}.txt")

                    # guardar PRE-ROLL
                    with open(txt_path, "a", encoding="utf-8") as ftxt:
                        for item in list(buffer):
                            dst = os.path.join(folder, os.path.basename(item.wav_path))
                            shutil.copy(item.wav_path, dst)
                            ftxt.write(item.text + "\n")
                            safe_remove(item.wav_path)


                    # POST-ROLL + extra
                    for _ in range(post_chunks + EXTRA_POST_CHUNKS):
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp2:
                            post_wav = tmp2.name
                        try:
                            grabar_chunk_wav(STREAM_URL, CHUNK_SECONDS, post_wav)
                            post_result = model.transcribe(post_wav, fp16=False, language="es")
                            post_text_raw = post_result.get("text", "").strip()
                            post_text = normalizar(post_text_raw)
                            shutil.copy(post_wav, os.path.join(folder, os.path.basename(post_wav)))
                            with open(txt_path, "a", encoding="utf-8") as ftxt:
                                ftxt.write(post_text + "\n")

                        finally:
                            safe_remove(post_wav)

                    buffer.clear()
                    last_saved_ts = time.time()

            else:
                print(f"{timestamp} (silencio)")
                safe_remove(wav_path)

        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(1)

# main
if __name__ == "__main__":
    try:
        print("🎙️ Escuchando la radio y detectando noticias...")
        transcribe_loop()
    except KeyboardInterrupt:
        stop_event.set()
        print("⏹️ Finalizado por el usuario")
 