import os
import pywhatkit

# Ruta principal
ruta_base = "noticias_guardadas"

# Tu número de WhatsApp (con código de país, sin +)
mi_numero = "(inserte numero)"  # Ejemplo: 51 para Perú

# Construir un solo mensaje con todas las noticias
mensaje_final = "📰 Noticias guardadas:\n\n"

for carpeta in os.listdir(ruta_base):
    ruta_carpeta = os.path.join(ruta_base, carpeta)
    
    if os.path.isdir(ruta_carpeta):
        nombre_txt = carpeta + ".txt"
        ruta_txt = os.path.join(ruta_carpeta, nombre_txt)
        
        if os.path.exists(ruta_txt):
            with open(ruta_txt, "r", encoding="utf-8") as f:
                contenido = f.read().strip()
            
            if contenido:
                mensaje_final += f"📂 {carpeta}\n{contenido}\n\n"

# Enviar todo en un solo mensaje
try:
    pywhatkit.sendwhatmsg_instantly(
        phone_no="+" + mi_numero,
        message=mensaje_final.strip(),
        tab_close=True
    )
    print("✅ Todas las noticias fueron enviadas en un solo mensaje")
except Exception as e:
    print(f"❌ Error enviando el mensaje: {e}")
