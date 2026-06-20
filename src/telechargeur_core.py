# -*- coding: utf-8 -*-
# telechargeur_core.py
import os
import yt_dlp
from urllib.parse import urlparse

def valider_url_youtube(url):
    parsed_url = urlparse(url)
    domaine = parsed_url.netloc.lower()
    domaines_autorises = ['youtube.com', 'www.youtube.com', 'm.youtube.com', 'youtu.be', 'www.youtu.be']
    domaine_propre = domaine.split(':')[0]
    return domaine_propre in domaines_autorises

def telecharger_video_pro(url, quality, status_callback, progress_callback, check_cancel_callback):
    if not valider_url_youtube(url):
        return False, "URL invalide."

    dossier_sortie = os.path.join(os.path.expanduser("~"), "Downloads")
    
    # Mappage strict des options de qualité utilisant des fichiers pré-fusionnés (MP4)
    # Cela évite totalement le besoin de FFmpeg.
    format_map = {
        "Haute (1080p)": "best[height<=1080][ext=mp4]",
        "Moyenne (720p)": "best[height<=720][ext=mp4]",
        "Basse (480p)": "best[height<=480][ext=mp4]",
        "Très Basse (240p)": "best[height<=240][ext=mp4]"
    }
    
    # Si la qualité n'est pas dans le mappage, on prend le meilleur MP4 disponible
    ydl_format = format_map.get(quality, "best[ext=mp4]")

    # Callback pour la progression
    def my_hook(d):
        # Vérification d'annulation en cours de téléchargement
        if check_cancel_callback():
            raise Exception("Téléchargement annulé par l'utilisateur")

        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            if total:
                progress_callback((d.get('downloaded_bytes', 0) / total) * 100)
        elif d['status'] == 'finished':
            status_callback("Téléchargement terminé !")

    ydl_opts = {
        'format': ydl_format,
        # Inclure la résolution dans le nom de fichier pour éviter les écrasements accidentels
        'outtmpl': os.path.join(dossier_sortie, '%(title)s [%(resolution)s].%(ext)s'), 
        'restrictfilenames': True, 
        'noplaylist': True, 
        'quiet': True, 
        'overwrites': True, # Autorise l'écrasement si le fichier existe
        'progress_hooks': [my_hook], 
    }

    try:
        status_callback("Connexion...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True, "Succès"
    except Exception as e:
        return False, str(e)
