import subprocess
import shlex
import os
import whisper

# ==============================
# CONFIGURACIÓN
# ==============================

# URL del stream
url = "https://us-b4-p-e-zs14-audio.cdn.mdstrm.com/live-audio-aw/5fab3416b5f9ef165cfab6e9"

# Carpeta donde guardar
save_dir = r"c:/Users/Joseph/Desktop/Proyectos_Python/Proyecto_Marina"

# Archivos
outfile_wav = os.path.join(save_dir, "prueba.wav")
outfile_txt = os.path.join(save_dir, "transcripcion.txt")

# Duración de la grabación (segundos)
duration = 30  

# ==============================
# 1. Grabar con FFmpeg
# ==============================

cmd = [
    "ffmpeg",
    "-y",               # Sobrescribe si ya existe
    "-i", url,          # URL de entrada
    "-t", str(duration), # Duración
    "-ar", "16000",     # Sample rate (16k recomendado para STT)
    "-ac", "1",         # Mono
    outfile_wav         # Archivo de salida
]

print("🎙️ Grabando audio...")
print("Ejecutando:", " ".join(shlex.quote(c) for c in cmd))
subprocess.run(cmd)
print(f"✅ Archivo guardado en: {outfile_wav}")

# ==============================
# 2. Transcribir con Whisper
# ==============================

print("📝 Transcribiendo audio con Whisper...")
model = whisper.load_model("base")  # Puedes cambiar a "small", "medium", "large" si quieres más precisión
result = model.transcribe(outfile_wav, language="es")  # Forzamos español

texto = result["text"]

# ==============================
# 3. Guardar en TXT
# ==============================

with open(outfile_txt, "w", encoding="utf-8") as f:
    f.write(texto)

print(f"✅ Transcripción guardada en: {outfile_txt}")
print("Texto transcrito:")
print(texto)