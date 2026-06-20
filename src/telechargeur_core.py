# -*- coding: utf-8 -*-
# telechargeur_core.py
import os
import shutil
from urllib.parse import urlparse

import yt_dlp

MAX_DOWNLOAD_BYTES = 2 * 1024 * 1024 * 1024
ALLOWED_SCHEMES = {"http", "https"}
ALLOWED_DOMAINS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be", "www.youtu.be"}

_chemin_ffmpeg_cached = None
_ffmpeg_checked = False

def obtenir_chemin_ffmpeg():
    """Trouve ffmpeg dans le dossier 'bin' fixe du projet ou dans le PATH systeme."""
    global _chemin_ffmpeg_cached, _ffmpeg_checked
    if _ffmpeg_checked:
        return _chemin_ffmpeg_cached
        
    # 1. Dans le PATH systeme
    path_path = shutil.which("ffmpeg")
    if path_path:
        _chemin_ffmpeg_cached = path_path
        _ffmpeg_checked = True
        return path_path
    
    # 2. Recherche dans le dossier 'bin' specifique du projet
    dossier_projet = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    chemin_fixe = os.path.join(dossier_projet, "bin", "ffmpeg.exe")
    if os.path.exists(chemin_fixe):
        _chemin_ffmpeg_cached = chemin_fixe
            
    _ffmpeg_checked = True
    return _chemin_ffmpeg_cached

def ffmpeg_disponible():
    """Verifier si ffmpeg est disponible."""
    return obtenir_chemin_ffmpeg() is not None

# Strategie de selection de formats : 
# - Si ffmpeg est disponible, on peut forcer bestvideo[height<=X]+bestaudio 
#   pour avoir vraiment des tailles differentes par palier.
# - Sinon, on cherche d'abord un format avec hauteur EXACTE, puis fallback
#   sur height<=X. Cela donne quand meme des tailles differentes si les formats 
#   exacts existent (ex: 1080p, 720p, etc.), mais peut fallback sur le meme 
#   format pour plusieurs paliers si les resolutions exactes ne sont pas disponibles.
if ffmpeg_disponible():
    FORMAT_MAP = {
        "Haute (1080p)": "bestvideo[height<=1080]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "Moyenne (720p)": "bestvideo[height<=720]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best[height<=720]",
        "Basse (480p)": "bestvideo[height<=480]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio/best[height<=480]",
        "Tres Basse (240p)": "bestvideo[height<=240]+bestaudio[ext=m4a]/bestvideo[height<=240]+bestaudio/best[height<=240]",
    }
else:
    FORMAT_MAP = {
        "Haute (1080p)": "best[height=1080]/best[height<=1080]/best",
        "Moyenne (720p)": "best[height=720]/best[height<=720]/best",
        "Basse (480p)": "best[height=480]/best[height<=480]/best",
        "Tres Basse (240p)": "best[height=240]/best[height<=240]/best",
    }

# Map des qualites audio : cle affichee dans l'interface -> debit en kbps.
AUDIO_QUALITY_MAP = {
    "Haute (320 kbps)": "320",
    "Moyenne (192 kbps)": "192",
    "Basse (128 kbps)": "128",
    "Tres Basse (96 kbps)": "96",
}


def valider_url_youtube(url):
    if not isinstance(url, str) or len(url.strip()) > 2048:
        return False

    parsed_url = urlparse(url)
    if parsed_url.scheme.lower() not in ALLOWED_SCHEMES:
        return False

    domaine = parsed_url.netloc.lower()
    domaine_propre = domaine.split(':')[0]
    return domaine_propre in ALLOWED_DOMAINS


def formater_taille(nb_octets):
    if not nb_octets:
        return "taille indisponible"

    taille = float(nb_octets)
    for unite in ("o", "Ko", "Mo", "Go"):
        if taille < 1024 or unite == "Go":
            if unite == "o":
                return f"{int(taille)} {unite}"
            return f"{taille:.1f} {unite}"
        taille /= 1024


def formater_vitesse(octets_par_seconde):
    """Formater une vitesse de telechargement en unite lisible."""
    if not octets_par_seconde:
        return ""
    vitesse = float(octets_par_seconde)
    for unite in ("o/s", "Ko/s", "Mo/s", "Go/s"):
        if vitesse < 1024 or unite == "Go/s":
            return f"{vitesse:.1f} {unite}"
        vitesse /= 1024


def formater_eta(secondes):
    """Formater un temps restant en MM:SS ou HH:MM:SS."""
    if secondes is None or secondes < 0:
        return ""
    secondes = int(secondes)
    if secondes >= 3600:
        h = secondes // 3600
        m = (secondes % 3600) // 60
        s = secondes % 60
        return f"{h:02d}:{m:02d}:{s:02d}"
    m = secondes // 60
    s = secondes % 60
    return f"{m:02d}:{s:02d}"


def _formats_selectionnes(info):
    formats = info.get("requested_formats")
    if formats:
        return formats
    return [info]


def decrire_format_selectionne(info, quality, media_type="video"):
    """Decrire le format selectionne avec la taille, la resolution ou le debit audio."""
    formats = _formats_selectionnes(info)
    tailles = [fmt.get("filesize") for fmt in formats]
    tailles_estimees = [fmt.get("filesize_approx") for fmt in formats]

    if all(tailles):
        taille = sum(tailles)
        prefixe = "Taille"
    elif any(tailles) or any(tailles_estimees):
        taille = sum(taille or estimee or 0 for taille, estimee in zip(tailles, tailles_estimees))
        prefixe = "Taille estimee"
    else:
        taille = None
        prefixe = "Taille"

    if media_type == "audio":
        # Pour l'audio, afficher le debit (abr) au lieu de la resolution.
        abr = info.get("abr")
        detail = f"{abr:.0f} kbps" if abr else "debit inconnu"
        extension = "mp3"
    else:
        resolution = info.get("resolution")
        if not resolution or resolution == "audio only":
            height = info.get("height")
            resolution = f"{height}p" if height else "resolution inconnue"
        detail = resolution
        extension = info.get("ext") or "format inconnu"

    taille_formatee = formater_taille(taille)
    return f"{quality} - {prefixe} : {taille_formatee} ({detail}, {extension})"


def taille_selectionnee(info):
    formats = _formats_selectionnes(info)
    tailles = [fmt.get("filesize") or fmt.get("filesize_approx") for fmt in formats]
    if not any(tailles):
        return None
    return sum(taille or 0 for taille in tailles)


def chemin_telechargements():
    dossier_sortie = os.path.abspath(os.path.join(os.path.expanduser("~"), "Downloads"))
    os.makedirs(dossier_sortie, exist_ok=True)
    return dossier_sortie


def telecharger_video_pro(url, quality, status_callback, progress_callback,
                          check_cancel_callback, size_callback=None,
                          media_type="video", dossier_sortie=None):
    """Telecharger une video ou un audio depuis YouTube.

    Args:
        media_type: "video" pour MP4 ou "audio" pour MP3.
        dossier_sortie: Dossier de destination (defaut : Downloads).
    """
    if not valider_url_youtube(url):
        return False, "URL invalide."

    if not dossier_sortie:
        dossier_sortie = chemin_telechargements()
    else:
        os.makedirs(dossier_sortie, exist_ok=True)

    is_audio = media_type == "audio"

    if is_audio:
        if not ffmpeg_disponible():
            return False, "FFmpeg est requis pour l'extraction audio MP3. Installez FFmpeg."
        ydl_format = "bestaudio/best"
        audio_bitrate = AUDIO_QUALITY_MAP.get(quality, "192")
    else:
        # Chaque option garde la qualite demandee en priorite, puis utilise un format disponible en secours.
        ydl_format = FORMAT_MAP.get(quality, "best[ext=mp4]")

    def my_hook(d):
        if check_cancel_callback():
            raise Exception("Telechargement annule par l'utilisateur")

        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            if total:
                pct = (d.get('downloaded_bytes', 0) / total) * 100
            else:
                pct = 0
            vitesse = formater_vitesse(d.get('speed'))
            eta = formater_eta(d.get('eta'))
            progress_callback(pct, vitesse, eta)
        elif d['status'] == 'finished':
            if is_audio:
                status_callback("Conversion en MP3 en cours...")
            else:
                status_callback("Telechargement termine !")

    chemin_ffmpeg = obtenir_chemin_ffmpeg()
    ydl_opts = {
        'format': ydl_format,
        # La qualite demandee fait partie du nom de fichier : meme si la
        # resolution reelle se ressemble entre deux paliers, chaque
        # telechargement produit un fichier distinct au lieu d'etre ignore
        # par nooverwrites (qui sinon "garde" silencieusement l'ancien fichier).
        'outtmpl': os.path.join(dossier_sortie, f'%(title)s [{quality}].%(ext)s'),
        'restrictfilenames': True,
        'windowsfilenames': True,
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'overwrites': False,
        'nooverwrites': True,
        'ignoreerrors': False,
        'cachedir': False,
        'socket_timeout': 20,
        'retries': 3,
        'fragment_retries': 3,
        'extractor_retries': 3,
        'concurrent_fragment_downloads': 1,
        'progress_hooks': [my_hook],
    }

    if is_audio:
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': audio_bitrate,
        }]

    if chemin_ffmpeg:
        ydl_opts['ffmpeg_location'] = os.path.dirname(chemin_ffmpeg)

    try:
        status_callback("Analyse du format choisi...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            description_taille = decrire_format_selectionne(info, quality, media_type)
            status_callback(description_taille)
            if size_callback:
                size_callback(description_taille)

            taille = taille_selectionnee(info)
            if taille and taille > MAX_DOWNLOAD_BYTES:
                limite = formater_taille(MAX_DOWNLOAD_BYTES)
                return False, f"Fichier trop volumineux. Limite securite : {limite}."

            if check_cancel_callback():
                raise Exception("Telechargement annule par l'utilisateur")

            status_callback("Telechargement en cours...")
            ydl.download([url])
        return True, "Succes"
    except Exception as e:
        return False, str(e)