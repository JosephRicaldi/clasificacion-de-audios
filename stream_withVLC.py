import vlc
import os

vlc_path = r"C:\Program Files\VideoLAN\VLC"
os.add_dll_directory(vlc_path)

instance = vlc.Instance()
player = instance.media_player_new()
media = instance.media_new("https://us-b4-p-e-zs14-audio.cdn.mdstrm.com/live-audio-aw/5fab3416b5f9ef165cfab6e9")
player.set_media(media)
player.play()

input("Presiona Enter para salir...\n")
