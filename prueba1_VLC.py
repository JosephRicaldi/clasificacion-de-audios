import vlc
import os
import threading
import time
import wave
import pyaudio
import speech_recognition as sr
from datetime import datetime
import queue
import numpy as np

class OptimizedStreamTranscriber:
    def __init__(self):
        # Configuración de audio OPTIMIZADA para captura continua
        self.CHUNK = 2048  # Chunks más grandes = menos gaps
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 22050  # Mejor calidad para streams de radio
        
        # Cola para audio capturado con buffer más grande
        self.audio_queue = queue.Queue(maxsize=100)
        self.is_running = True
        
        # Inicializar reconocedor de voz OPTIMIZADO
        self.recognizer = sr.Recognizer()
        # Configuraciones para captura más agresiva y continua
        self.recognizer.energy_threshold = 800   # Más sensible al audio
        self.recognizer.dynamic_energy_threshold = True  # Se adapta automáticamente
        self.recognizer.pause_threshold = 0.4    # Pausas más cortas entre palabras
        self.recognizer.phrase_threshold = 0.2   # Frases más cortas
        self.recognizer.non_speaking_duration = 0.3  # Detección rápida de no-habla
        
        # PyAudio instance
        self.p = pyaudio.PyAudio()
        
        # Configurar VLC
        self.setup_vlc()
        
        print("🎧 Sistema OPTIMIZADO de transcripción en tiempo real")
        print("📻 Stream: Radio en vivo")
        print("🎤 Captura continua mejorada")
        print("⚡ Configuración: Micrófono cerca del parlante")
        print("-" * 50)
    
    def setup_vlc(self):
        """Configurar VLC player optimizado"""
        vlc_path = r"C:\Program Files\VideoLAN\VLC"
        os.add_dll_directory(vlc_path)
        
        # Crear instancia VLC con opciones optimizadas
        vlc_args = [
            '--intf', 'dummy',  # Sin interfaz gráfica
            '--quiet',  # Menos mensajes de debug
            '--no-video',  # Solo audio
            '--aout', 'directsound',  # Salida directa de audio
            '--network-caching', '1000'  # Buffer de red reducido
        ]
        
        self.instance = vlc.Instance(vlc_args)
        self.player = self.instance.media_player_new()
        
        # Configurar volumen al máximo para mejor captura
        self.player.audio_set_volume(100)
        
        # URL del stream
        media = self.instance.media_new("https://us-b4-p-e-zs14-audio.cdn.mdstrm.com/live-audio-aw/5fab3416b5f9ef165cfab6e9")
        self.player.set_media(media)
    
    def find_best_input_device(self):
        """Encontrar el mejor dispositivo de entrada disponible"""
        print("🔍 Analizando dispositivos de audio...")
        available_devices = []
        
        for i in range(self.p.get_device_count()):
            try:
                dev_info = self.p.get_device_info_by_index(i)
                if dev_info['maxInputChannels'] > 0:
                    name = dev_info['name']
                    channels = dev_info['maxInputChannels']
                    rate = int(dev_info['defaultSampleRate'])
                    
                    print(f"  [{i}] {name}")
                    print(f"      📥 Canales: {channels} | 🎵 Rate: {rate}Hz")
                    
                    available_devices.append((i, name, channels, rate))
                    
                    # Priorizar dispositivos específicos
                    name_lower = name.lower()
                    if any(keyword in name_lower for keyword in [
                        'stereo mix', 'mezcla estéreo', 'what u hear', 'wave out mix'
                    ]):
                        print(f"      ✅ DISPOSITIVO DE SISTEMA ENCONTRADO")
                        return i
                    elif 'microsoft sound mapper' in name_lower:
                        print(f"      🎯 MAPPER DEL SISTEMA")
                        # Continúa buscando, pero es buena opción
                    elif 'micrófono' in name_lower or 'microphone' in name_lower:
                        print(f"      🎤 MICRÓFONO")
                    elif 'primario' in name_lower or 'primary' in name_lower:
                        print(f"      🔊 CAPTURA PRIMARIA")
            except:
                continue
        
        if available_devices:
            # Usar el primer dispositivo disponible
            device_id, device_name, channels, rate = available_devices[0]
            print(f"\n✅ Seleccionado: [{device_id}] {device_name}")
            return device_id
        
        print("❌ No se encontraron dispositivos de entrada")
        return None
    
    def audio_callback(self, in_data, frame_count, time_info, status):
        """Callback optimizado para capturar audio"""
        if self.is_running and not self.audio_queue.full():
            try:
                self.audio_queue.put_nowait(in_data)
            except queue.Full:
                # Si la cola está llena, descartar el más antiguo
                try:
                    self.audio_queue.get_nowait()
                    self.audio_queue.put_nowait(in_data)
                except queue.Empty:
                    pass
        return (in_data, pyaudio.paContinue)
    
    def capture_audio(self):
        """Capturar audio del sistema de forma optimizada"""
        device_index = self.find_best_input_device()
        
        if device_index is None:
            print("❌ No hay dispositivos de entrada disponibles")
            return
        
        try:
            # Configuración optimizada para captura continua
            stream = self.p.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.CHUNK,
                stream_callback=self.audio_callback
            )
            
            stream.start_stream()
            print(f"🎤 Captura OPTIMIZADA activa - Dispositivo: {device_index}")
            print(f"📊 Configuración: {self.RATE}Hz, Chunk:{self.CHUNK}")
            
            # Mantener el stream activo
            while stream.is_active() and self.is_running:
                time.sleep(0.05)  # Menor latencia
            
            stream.stop_stream()
            stream.close()
            
        except Exception as e:
            print(f"❌ Error capturando audio: {e}")
            print("💡 Verifica que el micrófono esté cerca del parlante")
    
    def transcribe_audio_continuous(self):
        """Transcripción OPTIMIZADA para captura continua"""
        audio_buffer = []
        last_transcription = ""
        consecutive_empty = 0
        
        print("🧠 Iniciando transcripción CONTINUA optimizada...")
        
        while self.is_running:
            try:
                # Procesar audio de la cola más rápidamente
                batch_data = []
                
                # Recoger varios chunks a la vez para procesamiento más eficiente
                for _ in range(5):  # Procesar 5 chunks juntos
                    try:
                        data = self.audio_queue.get_nowait()
                        batch_data.append(data)
                        consecutive_empty = 0
                    except queue.Empty:
                        consecutive_empty += 1
                        break
                
                if batch_data:
                    audio_buffer.extend(batch_data)
                
                # Procesar cada 1.5 segundos (más frecuente)
                buffer_duration = len(audio_buffer) * self.CHUNK / self.RATE
                
                if buffer_duration >= 1.2 and audio_buffer:  # Procesamiento más rápido
                    # Combinar buffer de audio
                    audio_data = b''.join(audio_buffer)
                    
                    # Verificar que hay volumen suficiente (filtro de ruido)
                    audio_array = np.frombuffer(audio_data, dtype=np.int16)
                    volume_level = np.sqrt(np.mean(audio_array**2))
                    
                    if volume_level > 50:  # Umbral bajo para capturar más audio
                        try:
                            # Crear objeto AudioData para speech_recognition
                            audio_obj = sr.AudioData(audio_data, self.RATE, 2)
                            
                            # Transcribir usando Google Speech Recognition
                            text = self.recognizer.recognize_google(
                                audio_obj, 
                                language='es-ES',  # Cambiar a 'en-US' si necesario
                                show_all=False
                            )
                            
                            # Mostrar transcripción si es nueva y significativa
                            if text and len(text.strip()) > 2:
                                # Evitar repeticiones exactas consecutivas
                                if text.strip().lower() != last_transcription.strip().lower():
                                    timestamp = datetime.now().strftime("%H:%M:%S")
                                    print(f"[{timestamp}] 📝 {text}")
                                    last_transcription = text
                        
                        except sr.UnknownValueError:
                            # No se pudo reconocer - normal, continuar
                            pass
                        except sr.RequestError as e:
                            print(f"❌ Error API Google: {e}")
                            time.sleep(1)
                        except Exception as e:
                            print(f"⚠️  Error transcribiendo: {e}")
                    
                    # Buffer management optimizado - mantener más overlap
                    overlap_size = int(len(audio_buffer) * 0.3)  # 30% overlap
                    audio_buffer = audio_buffer[-max(overlap_size, 15):]
                
                # Dormir menos tiempo para mayor responsividad
                time.sleep(0.02)
                
            except Exception as e:
                print(f"❌ Error en loop de transcripción: {e}")
                time.sleep(0.1)
    
    def monitor_audio_levels(self):
        """Monitor de niveles de audio para debugging"""
        print("📊 Monitor de niveles de audio activo...")
        
        while self.is_running:
            try:
                if not self.audio_queue.empty():
                    # Obtener muestra sin consumir de la cola principal
                    temp_data = []
                    for _ in range(min(3, self.audio_queue.qsize())):
                        try:
                            temp_data.append(self.audio_queue.get_nowait())
                        except queue.Empty:
                            break
                    
                    if temp_data:
                        # Volver a poner los datos en la cola
                        for data in reversed(temp_data):
                            try:
                                self.audio_queue.put_nowait(data)
                            except queue.Full:
                                break
                        
                        # Analizar volumen
                        combined_data = b''.join(temp_data)
                        audio_array = np.frombuffer(combined_data, dtype=np.int16)
                        volume = np.sqrt(np.mean(audio_array**2))
                        
                        # Mostrar nivel cada 10 segundos
                        if int(time.time()) % 10 == 0:
                            volume_bars = "█" * min(int(volume / 100), 20)
                            print(f"🎚️  Nivel: {volume_bars} ({int(volume)})")
            except:
                pass
            
            time.sleep(0.5)
    
    def start(self):
        """Iniciar el sistema OPTIMIZADO completo"""
        try:
            print("▶️  Iniciando stream VLC...")
            # Iniciar reproducción VLC
            self.player.play()
            
            # Esperar a que VLC inicie completamente
            time.sleep(3)
            
            print("🚀 Iniciando hilos optimizados...")
            # Iniciar hilos con prioridades optimizadas
            audio_thread = threading.Thread(
                target=self.capture_audio, 
                daemon=True, 
                name="AudioCapture"
            )
            transcription_thread = threading.Thread(
                target=self.transcribe_audio_continuous, 
                daemon=True, 
                name="Transcription"
            )
            monitor_thread = threading.Thread(
                target=self.monitor_audio_levels,
                daemon=True,
                name="AudioMonitor"
            )
            
            audio_thread.start()
            transcription_thread.start()
            monitor_thread.start()
            
            print("✅ Sistema OPTIMIZADO activo")
            print("💡 El micrófono debe estar cerca del parlante")
            print("🔊 Ajusta el volumen del PC si es necesario")
            print("=" * 50)
            print("🎤 Transcripción en tiempo real:")
            print()
            
            # Esperar input del usuario
            input("[Presiona Enter para detener]")
            
        except KeyboardInterrupt:
            print("\n🛑 Deteniendo sistema...")
        finally:
            self.stop()
    
    def stop(self):
        """Detener el sistema de forma limpia"""
        print("\n⏹️  Deteniendo sistema...")
        self.is_running = False
        
        # Detener VLC
        if hasattr(self, 'player'):
            self.player.stop()
        
        # Limpiar cola de audio
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break
        
        # Cerrar PyAudio
        if hasattr(self, 'p'):
            self.p.terminate()
        
        print("✅ Sistema detenido correctamente")

def main():
    """Función principal optimizada"""
    print("🎵 VLC STREAM + TRANSCRIPCIÓN OPTIMIZADA")
    print("⚡ Versión: Captura continua mejorada")
    print("🎤 Método: Micrófono físico cerca del parlante")
    print("=" * 60)
    
    try:
        transcriber = OptimizedStreamTranscriber()
        transcriber.start()
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        print("💡 Verifica:")
        print("   - VLC instalado correctamente")
        print("   - Micrófono conectado y funcionando")  
        print("   - Permisos de audio habilitados")
        print("   - Conexión a internet para Google Speech API")

if __name__ == "__main__":
    main()
    