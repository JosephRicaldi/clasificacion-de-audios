import vlc
import os
import threading
import time
import pyaudio
import speech_recognition as sr
from datetime import datetime
import queue
import numpy as np
import webrtcvad
import audioop

class OptimizedStreamTranscriber:
    def __init__(self):
        # Configuración optimizada para tiempo real
        self.CHUNK = 1024  # Tamaño reducido para menor latencia
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000  # Tasa de muestreo óptima para reconocimiento de voz
        
        # Cola para audio con tamaño ajustado
        self.audio_queue = queue.Queue(maxsize=50)
        self.is_running = True
        
        # Inicializar reconocedor de voz
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.recognizer.phrase_threshold = 0.3
        self.recognizer.non_speaking_duration = 0.5
        
        # Detector de actividad de voz (VAD)
        self.vad = webrtcvad.Vad(2)  # Nivel de sensibilidad moderado (0-3)
        
        # PyAudio instance
        self.p = pyaudio.PyAudio()
        
        # Buffer para acumular audio
        self.audio_buffer = bytearray()
        self.buffer_duration = 0
        self.target_duration = 2.0  # 2 segundos de audio por transcripción
        
        print("🎧 Sistema de transcripción en tiempo real OPTIMIZADO")
        print("📻 Stream: Radio en vivo")
        print("🎤 Captura con filtro de actividad vocal")
        print("⚡ Latencia reducida")
        print("-" * 50)
    
    def find_best_input_device(self):
        """Encontrar el mejor dispositivo de entrada disponible"""
        print("🔍 Buscando dispositivos de audio...")
        
        # Lista de dispositivos preferidos (en orden de prioridad)
        preferred_devices = [
            'stereo mix', 'mezcla estéreo', 'what u hear', 
            'wave out mix', 'salida de audio', 'audio output'
        ]
        
        for i in range(self.p.get_device_count()):
            dev_info = self.p.get_device_info_by_index(i)
            if dev_info['maxInputChannels'] > 0:
                name = dev_info['name'].lower()
                print(f"  [{i}] {dev_info['name']}")
                
                # Verificar si es un dispositivo preferido
                for preferred in preferred_devices:
                    if preferred in name:
                        print(f"      ✅ DISPOSITIVO PREFERIDO ENCONTRADO")
                        return i
        
        # Si no encontramos un dispositivo preferido, usar el primero disponible
        for i in range(self.p.get_device_count()):
            dev_info = self.p.get_device_info_by_index(i)
            if dev_info['maxInputChannels'] > 0:
                print(f"✅ Usando dispositivo: [{i}] {dev_info['name']}")
                return i
        
        print("❌ No se encontraron dispositivos de entrada")
        return None

    def audio_callback(self, in_data, frame_count, time_info, status):
        """Callback para capturar audio con preprocesamiento"""
        if self.is_running:
            # Aplicar ganancia para mejorar la señal (ajustar según necesidad)
            in_data, _ = audioop.ratecv(in_data, 2, 1, 44100, self.RATE, None)
            
            # Detección de actividad de voz
            is_speech = False
            try:
                is_speech = self.vad.is_speech(in_data, self.RATE)
            except:
                pass
            
            if is_speech and not self.audio_queue.full():
                try:
                    self.audio_queue.put_nowait(in_data)
                except queue.Full:
                    pass
        
        return (in_data, pyaudio.paContinue)
    
    def capture_audio(self):
        """Capturar audio del sistema optimizado para tiempo real"""
        device_index = self.find_best_input_device()
        
        if device_index is None:
            print("❌ No hay dispositivos de entrada disponibles")
            return
        
        try:
            # Configuración optimizada para baja latencia
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
            print(f"🎤 Captura activa - Dispositivo: {device_index}")
            print(f"📊 Configuración: {self.RATE}Hz, Chunk:{self.CHUNK}")
            
            # Mantener el stream activo
            while stream.is_active() and self.is_running:
                time.sleep(0.1)
            
            stream.stop_stream()
            stream.close()
            
        except Exception as e:
            print(f"❌ Error capturando audio: {e}")
    
    def transcribe_audio_continuous(self):
        """Transcripción optimizada para tiempo real"""
        print("🧠 Iniciando transcripción en tiempo real...")
        
        while self.is_running:
            try:
                # Procesar chunks de audio disponibles
                if not self.audio_queue.empty():
                    data = self.audio_queue.get_nowait()
                    
                    # Agregar al buffer
                    self.audio_buffer.extend(data)
                    self.buffer_duration += len(data) / (self.RATE * 2)  # 2 bytes por muestra
                    
                    # Transcribir cuando tengamos suficiente audio
                    if self.buffer_duration >= self.target_duration:
                        audio_data = bytes(self.audio_buffer)
                        
                        # Verificar que hay volumen suficiente
                        audio_array = np.frombuffer(audio_data, dtype=np.int16)
                        volume_level = np.sqrt(np.mean(audio_array**2))
                        
                        if volume_level > 100:  # Umbral ajustado
                            try:
                                # Crear objeto AudioData
                                audio_obj = sr.AudioData(audio_data, self.RATE, 2)
                                
                                # Transcribir usando Google Speech Recognition
                                text = self.recognizer.recognize_google(
                                    audio_obj, 
                                    language='es-ES',
                                    show_all=False
                                )
                                
                                # Mostrar transcripción
                                if text and len(text.strip()) > 2:
                                    timestamp = datetime.now().strftime("%H:%M:%S")
                                    print(f"[{timestamp}] 📝 {text}")
                                    
                            except sr.UnknownValueError:
                                # No se pudo reconocer - normal en pausas
                                pass
                            except sr.RequestError as e:
                                print(f"❌ Error API: {e}")
                                time.sleep(1)
                            except Exception as e:
                                print(f"⚠️  Error transcribiendo: {e}")
                        
                        # Resetear buffer
                        self.audio_buffer = bytearray()
                        self.buffer_duration = 0
                
                # Pequeña pausa para no saturar la CPU
                time.sleep(0.01)
                
            except Exception as e:
                print(f"❌ Error en loop de transcripción: {e}")
                time.sleep(0.1)
    
    def monitor_audio_levels(self):
        """Monitor de niveles de audio para debugging"""
        print("📊 Monitor de niveles de audio activo...")
        
        while self.is_running:
            try:
                if not self.audio_queue.empty():
                    # Obtener muestra para análisis
                    temp_data = []
                    for _ in range(min(5, self.audio_queue.qsize())):
                        try:
                            temp_data.append(self.audio_queue.get_nowait())
                        except queue.Empty:
                            break
                    
                    # Volver a poner los datos en la cola
                    for data in temp_data:
                        try:
                            self.audio_queue.put_nowait(data)
                        except queue.Full:
                            break
                    
                    # Analizar volumen
                    if temp_data:
                        combined_data = b''.join(temp_data)
                        audio_array = np.frombuffer(combined_data, dtype=np.int16)
                        volume = np.sqrt(np.mean(audio_array**2))
                        
                        # Barra de nivel visual
                        bars = int(volume / 100)
                        volume_bars = "█" * min(bars, 20)
                        print(f"🎚️  Nivel: {volume_bars} ({int(volume)})")
            except Exception as e:
                print(f"Error en monitor: {e}")
            
            time.sleep(2)  # Reducir frecuencia de monitoreo
    
    def start(self):
        """Iniciar el sistema optimizado"""
        try:
            print("🚀 Iniciando hilos optimizados...")
            
            # Iniciar hilos
            audio_thread = threading.Thread(
                target=self.capture_audio, 
                daemon=True
            )
            transcription_thread = threading.Thread(
                target=self.transcribe_audio_continuous, 
                daemon=True
            )
            monitor_thread = threading.Thread(
                target=self.monitor_audio_levels,
                daemon=True
            )
            
            audio_thread.start()
            time.sleep(1)  # Esperar a que la captura de audio inicie
            transcription_thread.start()
            monitor_thread.start()
            
            print("✅ Sistema activo - Transcripción en tiempo real")
            print("🔊 Asegúrate de que el volumen esté ajustado correctamente")
            print("=" * 50)
            print("🎤 Transcripción:")
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
    print("🎵 TRANSCRIPCIÓN EN TIEMPO REAL OPTIMIZADA")
    print("⚡ Versión: Baja latencia con filtro VAD")
    print("=" * 60)
    
    try:
        transcriber = OptimizedStreamTranscriber()
        transcriber.start()
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        print("💡 Verifica:")
        print("   - Dependencias instaladas (webrtcvad, pyaudio, etc.)")
        print("   - Dispositivo de audio configurado correctamente")

if __name__ == "__main__":
    main()