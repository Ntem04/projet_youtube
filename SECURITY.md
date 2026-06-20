# Securite de YouTube Downloader Pro

Ce document decrit les mesures de securite appliquees au projet et les bonnes pratiques pour distribuer l'application.

## Principes appliques

- Principe du moindre privilege : l'installateur utilise `PrivilegesRequired=lowest` et installe l'application dans le profil utilisateur.
- Validation stricte des entrees : seules les URL `http` et `https` des domaines YouTube autorises sont acceptees.
- Reduction de surface d'attaque : les playlists sont bloquees avec `noplaylist`, et les telechargements concurrents sont limites.
- Controle du systeme de fichiers : les fichiers sont enregistres uniquement dans le dossier `Downloads` de l'utilisateur.
- Protection contre l'ecrasement : l'application n'ecrase plus automatiquement les fichiers deja presents.
- Noms de fichiers durcis : `restrictfilenames` et `windowsfilenames` limitent les caracteres dangereux dans les noms.
- Limitation de taille : un telechargement connu comme superieur a 2 Go est bloque.
- Comportement reseau prudent : delais et tentatives limites pour eviter les blocages longs.

## Distribution a un ami

Partager uniquement l'installateur :

```text
dist\YouTubeDownloaderSetup.exe
```

Ne pas partager seulement `dist\YouTubeDownloader\YouTubeDownloader.exe`, car il depend du dossier `_internal`.

## Verification avant partage

Depuis la racine du projet :

```powershell
Get-FileHash dist\YouTubeDownloaderSetup.exe -Algorithm SHA256
```

Envoie le hash SHA256 a ton ami avec le fichier. Il peut verifier que le fichier n'a pas ete modifie avec la meme commande.

## Avertissement Windows

Windows peut afficher SmartScreen ou un avertissement parce que l'executable n'est pas signe par un certificat officiel. Pour une distribution professionnelle, il faut signer l'installateur avec un certificat de signature de code.

## Recommandations avancees

- Signer `YouTubeDownloaderSetup.exe` avec un certificat Authenticode.
- Scanner l'installateur avec Windows Defender avant partage.
- Garder `yt-dlp` a jour, car YouTube change regulierement ses protections.
- Ne jamais executer une version de l'installateur provenant d'une source inconnue.
- Eviter d'ajouter des options qui permettent de choisir un dossier systeme comme destination.
