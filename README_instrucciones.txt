Seguir los siguientes pasos para instalarlo

(1. Clonar o descargar del repositorio Abre una terminal de VsCode (o PowerShell en Windows) y ejecuta:)
```bash
git clone https://github.com/JosephRicaldi/clasificador-marina-radio.git

(2. Crear y activar un entorno virtual para que no se mezclen las versiones con otros programas) 
python -m venv venv
.\venv\Scripts\activate

(3. Instalar librerias necesarias)
pip install -r requirements.txt

(4. Instalar FFmpeg https://ffmpeg.org/download.html
	1. Descarga el archivo **ZIP build**             Ejemplo: ffmpeg-2025-08-10-full_build.zip
	2. Descomprime y copia la carpeta `bin/` (donde está `ffmpeg.exe` y `ffmpeg.dll`).
		Dentro tendrás algo así: (EN DISCO LOCAL C)  (UNA VEZ EXTRAIDO DEL COMPRIMIDO CAMBIAR EL NOMBRE PARA QUE QUEDE ASI)
			C:\ffmpeg\bin\ffmpeg.exe
			C:\ffmpeg\bin\ffplay.exe
			C:\ffmpeg\bin\ffprobe.exe
	3. Añade la ruta de esa carpeta `bin` a las **Variables de Entorno** del sistema (PATH).)
		En Windows, presiona Windows + R, escribe: sysdm.cpl sysdm.cpl
		Ve a la pestaña Opciones avanzadas → Variables de entorno.
		En Variables del sistema, busca la variable Path y dale Editar.
		Presiona Nuevo y pega la ruta:
			C:\ffmpeg\bin
		Guarda y cierra todas las ventanas.
		ffmpeg -version
		Si ves la información de versión, está listo.	

(5. Instalar VLC Media Player ya que utiliza **VLC** para el stream. https://www.videolan.org/vlc/download-windows.html) 
	GUARDARLO EN LA SIGUIENTE DIRECCION C:\Program Files\VideoLAN\VLC\   (ESTA POR DEFECTO PERO VERIFICAR POR SI ACASO EN LA INSTALACION)
	Dentro de esa carpeta encontrarás libvlc.dll y libvlccore.dll.
	Ahora en los scripts, encontrara en esas rutas cuando se encuentre el vlc.

# Ruta al directorio de VLC (ajústala si instalaste en otra ubicación)
vlc_path = r"C:\Program Files\VideoLAN\VLC"
os.add_dll_directory(vlc_path)


Notas
- Asegurarse de activar siempre el entorno virtual antes de correr el proyecto.  
- Si hay problemas con FFmpeg, verifica que ffmpeg -version`funciona en la terminal.  
- Si VLC no abre el stream, revisa que esté correctamente instalado.
