# YouTube Downloader Pro

Application Python avec interface graphique pour telecharger une video YouTube au format MP4.

## Fonctionnalites

- Validation des liens YouTube avant le telechargement.
- Choix de qualite : 1080p, 720p, 480p ou 240p selon les formats disponibles.
- Format de secours automatique si YouTube ne fournit pas exactement le MP4 demande.
- Affichage de la taille du fichier correspondant a la qualite choisie avant le telechargement.
- Barre de progression pendant le telechargement.
- Bouton d'annulation.
- Enregistrement automatique dans le dossier `Downloads` de l'utilisateur.

## Installation developpeur

Installez les dependances :

```bash
pip install -r requirements.txt
```

## Lancement depuis le code

Depuis la racine du projet :

```bash
python src/app_gui.py
```

## Utilisation

1. Collez une URL YouTube.
2. Choisissez la qualite souhaitee.
3. Cliquez sur `Telecharger`.
4. Verifiez la taille affichee, puis suivez la progression.

Les fichiers sont nommes avec le titre et la resolution de la video pour limiter les ecrasements accidentels.

## Executable Windows

L'application compilée est disponible dans `dist\`:

- `YouTubeDownloader.exe` (Exécutable autonome)
- `YouTubeDownloaderSetup.exe` (Installateur)

Pour utiliser l'extraction audio, placez `ffmpeg.exe` dans un dossier nommé `bin\` à la racine de l'application.

Apres installation, l'application est copiee dans :

```powershell
%LOCALAPPDATA%\Programs\YouTubeDownloader\YouTubeDownloader.exe
```

Un raccourci `YouTube Downloader Pro` est aussi cree sur le Bureau si l'option est cochee.

## Securite

L'application applique une validation stricte des liens YouTube, installe sans privileges administrateur, enregistre uniquement dans `Downloads`, empeche l'ecrasement automatique des fichiers et bloque les telechargements connus comme superieurs a 2 Go. Elle sécurise l'utilisation de FFmpeg en ne le recherchant que dans le `PATH` système ou dans un dossier `bin\` local.

Avant de partager l'installateur, vous pouvez generer son hash :

```powershell
Get-FileHash dist\YouTubeDownloaderSetup.exe -Algorithm SHA256
```

Voir aussi `SECURITY.md`.

## Rebuild de l'executable

Depuis la racine du projet :

```powershell
python -m pip install -r requirements.txt -r requirements-build.txt
python -m PyInstaller --noconfirm --onefile --windowed --name YouTubeDownloader src/app_gui.py --collect-all customtkinter
tools\InnoSetup\ISCC.exe installer\YouTubeDownloader.iss
```

## Dependances

- `yt-dlp` pour l'extraction des informations et le telechargement.
- `customtkinter` pour l'interface graphique.
- `pyinstaller` pour generer l'executable Windows.
- Inno Setup pour generer l'installateur Windows.

## Notes

La taille affichee depend des informations fournies par YouTube via `yt-dlp`. Elle peut donc etre exacte ou estimee selon la video et le format selectionne.

La taille change selon la qualite choisie quand YouTube fournit plusieurs formats exploitables. Si une qualite precise n'existe pas pour une video, l'application essaie automatiquement un format plus proche ou plus petit disponible au lieu d'arreter le telechargement avec l'erreur `Requested format is not available`.

Le warning `No supported JavaScript runtime could be found` vient de `yt-dlp` et de YouTube. Le telechargement peut continuer, mais installer un runtime JavaScript comme Deno ou Node.js peut aider `yt-dlp` a detecter davantage de formats.
