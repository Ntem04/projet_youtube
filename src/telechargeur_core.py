# -*- coding: utf-8 -*-
# telechargeur_core.py
import os
from urllib.parse import urlparse

import yt_dlp

MAX_DOWNLOAD_BYTES = 2 * 1024 * 1024 * 1024
ALLOWED_SCHEMES = {"http", "https"}
ALLOWED_DOMAINS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be", "www.youtu.be"}

FORMAT_MAP = {
    "Haute (1080p)": "best[height<=1080][ext=mp4]/best[height<=1080]/best[ext=mp4]/best",
    "Moyenne (720p)": "best[height<=720][ext=mp4]/best[height<=720]/worst[height<=720][ext=mp4]/worst[height<=720]/worst",
    "Basse (480p)": "best[height<=480][ext=mp4]/best[height<=480]/worst[height<=480][ext=mp4]/worst[height<=480]/worst",
    "Tres Basse (240p)": "best[height<=240][ext=mp4]/best[height<=240]/worst[height<=240][ext=mp4]/worst[height<=240]/worst",
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


def _formats_selectionnes(info):
    formats = info.get("requested_formats")
    if formats:
        return formats
    return [info]


def decrire_format_selectionne(info, quality):
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

    resolution = info.get("resolution")
    if not resolution or resolution == "audio only":
        height = info.get("height")
        resolution = f"{height}p" if height else "resolution inconnue"

    extension = info.get("ext") or "format inconnu"
    taille_formatee = formater_taille(taille)
    return f"{quality} - {prefixe} : {taille_formatee} ({resolution}, {extension})"


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


def telecharger_video_pro(url, quality, status_callback, progress_callback, check_cancel_callback, size_callback=None):
    if not valider_url_youtube(url):
        return False, "URL invalide."

    dossier_sortie = chemin_telechargements()

    # Chaque option garde la qualite demandee en priorite, puis utilise un format disponible en secours.
    ydl_format = FORMAT_MAP.get(quality, "best[ext=mp4]")

    def my_hook(d):
        if check_cancel_callback():
            raise Exception("Telechargement annule par l'utilisateur")

        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            if total:
                progress_callback((d.get('downloaded_bytes', 0) / total) * 100)
        elif d['status'] == 'finished':
            status_callback("Telechargement termine !")

    ydl_opts = {
        'format': ydl_format,
        # Inclure la resolution dans le nom de fichier pour eviter les ecrasements accidentels.
        'outtmpl': os.path.join(dossier_sortie, '%(title)s [%(resolution)s].%(ext)s'),
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

    try:
        status_callback("Analyse du format choisi...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            description_taille = decrire_format_selectionne(info, quality)
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
