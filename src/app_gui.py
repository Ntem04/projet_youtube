# -*- coding: utf-8 -*-
# app_gui.py
import os
import threading
import customtkinter as ctk
from tkinter import filedialog

from telechargeur_core import (
    chemin_telechargements, telecharger_video_pro, valider_url_youtube,
    ffmpeg_disponible, AUDIO_QUALITY_MAP,
)


ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


VIDEO_QUALITY_OPTIONS = ["Haute (1080p)", "Moyenne (720p)", "Basse (480p)", "Tres Basse (240p)"]
AUDIO_QUALITY_OPTIONS = list(AUDIO_QUALITY_MAP.keys())


class DesignSystem:
    """Echelle d'espacement et typographie unique, sobre, peu de niveaux."""

    SPACING_XS = 4
    SPACING_SM = 8
    SPACING_MD = 14
    SPACING_LG = 20
    SPACING_XL = 32
    SPACING_2XL = 40

    CORNER_RADIUS_SM = 6
    CORNER_RADIUS_MD = 8

    BUTTON_HEIGHT = 40
    INPUT_HEIGHT = 40

    FONT_TITLE = ("Segoe UI", 20, "bold")
    FONT_SUBTITLE = ("Segoe UI", 12)
    FONT_LABEL = ("Segoe UI", 12, "bold")
    FONT_BODY = ("Segoe UI", 13)
    FONT_SMALL = ("Segoe UI", 11)
    FONT_BUTTON = ("Segoe UI", 13, "bold")

    # Palette neutre, peu de couleurs : un fond, une surface, un accent.
    COLORS = {
        "bg_primary": ("#fafafa", "#121212"),
        "bg_secondary": ("#fafafa", "#121212"),
        "text_primary": ("#1a1a1a", "#f0f0f0"),
        "text_secondary": ("#6b6b6b", "#9a9a9a"),
        "border": ("#e3e3e3", "#2a2a2a"),
        "input_bg": ("#ffffff", "#1c1c1c"),
    }

    STATUS_COLORS = {
        "muted": ("#6b6b6b", "#9a9a9a"),
        "info": ("#2563eb", "#60a5fa"),
        "success": ("#15803d", "#4ade80"),
        "warning": ("#b45309", "#fbbf24"),
        "error": ("#b91c1c", "#f87171"),
    }

    ACCENT = ("#2563eb", "#60a5fa")
    ACCENT_HOVER = ("#1e40af", "#3b82f6")


class AnimatedProgressBar(ctk.CTkProgressBar):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._target_value = 0
        self._animation_running = False

    def set_animated(self, value):
        self._target_value = max(0, min(1, value))
        if not self._animation_running:
            self._animate()

    def _animate(self):
        current = self.get()
        if abs(current - self._target_value) > 0.01:
            self._animation_running = True
            new_value = current + (self._target_value - current) * 0.15
            self.set(new_value)
            self.after(25, self._animate)
        else:
            self.set(self._target_value)
            self._animation_running = False


class ModernButton(ctk.CTkButton):
    """Un seul accent neutre pour le bouton principal, le reste reste discret (outline/texte)."""

    def __init__(self, *args, variant="primary", **kwargs):
        self.variant = variant

        if variant == "secondary":
            kwargs.setdefault("fg_color", "transparent")
            kwargs.setdefault("hover_color", DesignSystem.COLORS["border"])
            kwargs.setdefault("text_color", DesignSystem.COLORS["text_primary"])
            kwargs.setdefault("border_width", 1)
            kwargs.setdefault("border_color", DesignSystem.COLORS["border"])
        elif variant == "danger":
            kwargs.setdefault("fg_color", "transparent")
            kwargs.setdefault("hover_color", DesignSystem.COLORS["border"])
            kwargs.setdefault("text_color", DesignSystem.STATUS_COLORS["error"])
            kwargs.setdefault("border_width", 1)
            kwargs.setdefault("border_color", DesignSystem.STATUS_COLORS["error"])
        else:
            kwargs.setdefault("fg_color", DesignSystem.ACCENT)
            kwargs.setdefault("hover_color", DesignSystem.ACCENT_HOVER)
            kwargs.setdefault("text_color", ("#ffffff", "#121212"))

        kwargs.setdefault("corner_radius", DesignSystem.CORNER_RADIUS_SM)
        super().__init__(*args, **kwargs)


class StatusCard(ctk.CTkFrame):
    """Bloc d'etat minimal : pas de fond ni de bordure propres, juste un separateur au-dessus."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.grid_columnconfigure(0, weight=1)

        separator = ctk.CTkFrame(self, height=1, fg_color=DesignSystem.COLORS["border"])
        separator.grid(row=0, column=0, sticky="ew", pady=(0, DesignSystem.SPACING_MD))

        self.status_label = ctk.CTkLabel(
            self,
            text="Pret",
            text_color=DesignSystem.COLORS["text_secondary"],
            font=DesignSystem.FONT_BODY,
            anchor="w",
            justify="left",
            wraplength=640
        )
        self.status_label.grid(row=1, column=0, sticky="ew")

        progress_row = ctk.CTkFrame(self, fg_color="transparent")
        progress_row.grid(row=2, column=0, sticky="ew", pady=(DesignSystem.SPACING_SM, 0))
        progress_row.grid_columnconfigure(0, weight=1)

        self.progress = AnimatedProgressBar(
            progress_row,
            height=6,
            corner_radius=3,
            progress_color=DesignSystem.ACCENT,
            fg_color=DesignSystem.COLORS["border"],
        )
        self.progress.grid(row=0, column=0, sticky="ew")
        self.progress.set(0)

        self.progress_label = ctk.CTkLabel(
            progress_row,
            text="0%",
            width=44,
            text_color=DesignSystem.COLORS["text_secondary"],
            font=DesignSystem.FONT_SMALL
        )
        self.progress_label.grid(row=0, column=1, padx=(DesignSystem.SPACING_MD, 0))

        # Ligne d'informations : taille + vitesse/ETA
        info_row = ctk.CTkFrame(self, fg_color="transparent")
        info_row.grid(row=3, column=0, sticky="ew", pady=(DesignSystem.SPACING_XS, 0))
        info_row.grid_columnconfigure(0, weight=1)

        self.size_label = ctk.CTkLabel(
            info_row,
            text="Taille : en attente",
            text_color=DesignSystem.COLORS["text_secondary"],
            font=DesignSystem.FONT_SMALL,
            anchor="w",
            justify="left",
        )
        self.size_label.grid(row=0, column=0, sticky="w")

        self.speed_label = ctk.CTkLabel(
            info_row,
            text="",
            text_color=DesignSystem.COLORS["text_secondary"],
            font=DesignSystem.FONT_SMALL,
            anchor="e",
            justify="right",
        )
        self.speed_label.grid(row=0, column=1, sticky="e")

    def update_status(self, text, kind="info"):
        color = DesignSystem.STATUS_COLORS.get(kind, DesignSystem.STATUS_COLORS["info"])
        self.status_label.configure(text=text, text_color=color)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("YouTube Downloader Pro")
        self.geometry("700x620")
        self.minsize(450, 520)

        self.cancellation_requested = False
        self.is_downloading = False
        self.current_layout_mode = None
        self.output_path = chemin_telechargements()

        self.configure(fg_color=DesignSystem.COLORS["bg_primary"])
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_ui()
        self.bind("<Configure>", self._on_resize)

    def _build_ui(self):
        # Une seule colonne de contenu, marges generes, pas de cartes imbriquees.
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=0, column=0, sticky="nsew",
                     padx=DesignSystem.SPACING_XL, pady=DesignSystem.SPACING_MD)
        content.grid_columnconfigure(0, weight=1)
        # Row 9 = status card, flexible pour absorber l'espace vertical restant.
        content.grid_rowconfigure(9, weight=1, minsize=80)

        self._build_header(content)
        self._build_form(content)
        self._build_actions(content)
        self._build_status(content)
        self._build_footer(content)

    def _build_header(self, parent):
        title = ctk.CTkLabel(
            parent,
            text="YouTube Downloader Pro",
            font=DesignSystem.FONT_TITLE,
            anchor="w",
            text_color=DesignSystem.COLORS["text_primary"]
        )
        title.grid(row=0, column=0, sticky="ew")

        subtitle = ctk.CTkLabel(
            parent,
            text="Telechargement Video MP4 et Audio MP3",
            text_color=DesignSystem.COLORS["text_secondary"],
            font=DesignSystem.FONT_SUBTITLE,
            anchor="w"
        )
        subtitle.grid(row=1, column=0, sticky="ew", pady=(DesignSystem.SPACING_XS, 0))

    def _build_form(self, parent):
        # --- Lien YouTube ---
        url_label = ctk.CTkLabel(
            parent,
            text="Lien YouTube",
            font=DesignSystem.FONT_LABEL,
            anchor="w",
            text_color=DesignSystem.COLORS["text_primary"]
        )
        url_label.grid(row=2, column=0, sticky="ew", pady=(DesignSystem.SPACING_MD, DesignSystem.SPACING_XS))

        url_row = ctk.CTkFrame(parent, fg_color="transparent")
        url_row.grid(row=3, column=0, sticky="ew")
        url_row.grid_columnconfigure(0, weight=1)

        self.url_entry = ctk.CTkEntry(
            url_row,
            height=DesignSystem.INPUT_HEIGHT,
            placeholder_text="https://www.youtube.com/watch?v=...",
            border_width=1,
            corner_radius=DesignSystem.CORNER_RADIUS_SM,
            fg_color=DesignSystem.COLORS["input_bg"],
            border_color=DesignSystem.COLORS["border"],
            font=DesignSystem.FONT_BODY
        )
        self.url_entry.grid(row=0, column=0, sticky="ew")
        self.url_entry.bind("<Return>", lambda _: self.lancer_thread())

        self.paste_btn = ModernButton(
            url_row,
            text="Coller",
            width=88,
            height=DesignSystem.INPUT_HEIGHT,
            variant="secondary",
            font=DesignSystem.FONT_BUTTON,
            command=self.paste_clipboard
        )
        self.paste_btn.grid(row=0, column=1, padx=(DesignSystem.SPACING_SM, 0))

        # --- Dossier de destination ---
        dest_label = ctk.CTkLabel(
            parent,
            text="Dossier de destination",
            font=DesignSystem.FONT_LABEL,
            anchor="w",
            text_color=DesignSystem.COLORS["text_primary"]
        )
        dest_label.grid(row=4, column=0, sticky="ew", pady=(DesignSystem.SPACING_MD, DesignSystem.SPACING_XS))

        dest_row = ctk.CTkFrame(parent, fg_color="transparent")
        dest_row.grid(row=5, column=0, sticky="ew")
        dest_row.grid_columnconfigure(0, weight=1)

        self.dest_entry = ctk.CTkEntry(
            dest_row,
            height=DesignSystem.INPUT_HEIGHT,
            border_width=1,
            corner_radius=DesignSystem.CORNER_RADIUS_SM,
            fg_color=DesignSystem.COLORS["input_bg"],
            border_color=DesignSystem.COLORS["border"],
            font=DesignSystem.FONT_SMALL,
            state="disabled",
        )
        self.dest_entry.grid(row=0, column=0, sticky="ew")
        # Afficher le chemin par defaut
        self.dest_entry.configure(state="normal")
        self.dest_entry.insert(0, self.output_path)
        self.dest_entry.configure(state="disabled")

        self.browse_btn = ModernButton(
            dest_row,
            text="Parcourir",
            width=100,
            height=DesignSystem.INPUT_HEIGHT,
            variant="secondary",
            font=DesignSystem.FONT_BUTTON,
            command=self.choisir_dossier
        )
        self.browse_btn.grid(row=0, column=1, padx=(DesignSystem.SPACING_SM, 0))

        # --- Type de media ---
        media_label = ctk.CTkLabel(
            parent,
            text="Format",
            font=DesignSystem.FONT_LABEL,
            anchor="w",
            text_color=DesignSystem.COLORS["text_primary"]
        )
        media_label.grid(row=6, column=0, sticky="ew", pady=(DesignSystem.SPACING_MD, DesignSystem.SPACING_XS))

        self.media_type_control = ctk.CTkSegmentedButton(
            parent,
            values=["Video (MP4)", "Audio (MP3)"],
            height=36,
            corner_radius=DesignSystem.CORNER_RADIUS_SM,
            font=DesignSystem.FONT_SMALL,
            selected_color=DesignSystem.ACCENT,
            selected_hover_color=DesignSystem.ACCENT_HOVER,
            command=self._on_media_type_change,
        )
        self.media_type_control.set("Video (MP4)")
        self.media_type_control.grid(row=7, column=0, sticky="ew")

        # --- Qualite ---
        self.quality_label = ctk.CTkLabel(
            parent,
            text="Qualite",
            font=DesignSystem.FONT_LABEL,
            anchor="w",
            text_color=DesignSystem.COLORS["text_primary"]
        )
        self.quality_label.grid(row=8, column=0, sticky="ew", pady=(DesignSystem.SPACING_MD, DesignSystem.SPACING_XS))

        self.quality_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.quality_frame.grid(row=9, column=0, sticky="new")

        self.quality_control = ctk.CTkSegmentedButton(
            self.quality_frame,
            values=VIDEO_QUALITY_OPTIONS,
            height=36,
            corner_radius=DesignSystem.CORNER_RADIUS_SM,
            font=DesignSystem.FONT_SMALL,
            selected_color=DesignSystem.ACCENT,
            selected_hover_color=DesignSystem.ACCENT_HOVER,
            command=lambda _: self.update_size("Taille : en attente")
        )
        self.quality_control.set("Moyenne (720p)")
        self.quality_control.grid(row=0, column=0, sticky="ew")
        self.quality_frame.grid_columnconfigure(0, weight=1)

    def _on_media_type_change(self, value):
        """Mettre a jour les options de qualite selon le type de media selectionne."""
        if value == "Audio (MP3)":
            if not ffmpeg_disponible():
                self.set_status("FFmpeg requis pour l'extraction audio. Installez FFmpeg.", "error")
                self.media_type_control.set("Video (MP4)")
                return
            new_options = AUDIO_QUALITY_OPTIONS
            default_option = "Moyenne (192 kbps)"
        else:
            new_options = VIDEO_QUALITY_OPTIONS
            default_option = "Moyenne (720p)"

        # Reconstruire le segmented button avec les nouvelles options
        self.quality_control.destroy()
        self.quality_control = ctk.CTkSegmentedButton(
            self.quality_frame,
            values=new_options,
            height=36,
            corner_radius=DesignSystem.CORNER_RADIUS_SM,
            font=DesignSystem.FONT_SMALL,
            selected_color=DesignSystem.ACCENT,
            selected_hover_color=DesignSystem.ACCENT_HOVER,
            command=lambda _: self.update_size("Taille : en attente")
        )
        self.quality_control.set(default_option)
        self.quality_control.grid(row=0, column=0, sticky="ew")

        self.update_size("Taille : en attente")

    def _build_actions(self, parent):
        self.action_row = ctk.CTkFrame(parent, fg_color="transparent")
        self.action_row.grid(row=10, column=0, sticky="ew", pady=(DesignSystem.SPACING_MD, 0))

        self.open_folder_btn = ModernButton(
            self.action_row,
            text="Ouvrir le dossier",
            height=DesignSystem.BUTTON_HEIGHT,
            variant="secondary",
            font=DesignSystem.FONT_BUTTON,
            command=self.open_downloads
        )

        self.cancel_btn = ModernButton(
            self.action_row,
            text="Annuler",
            width=110,
            height=DesignSystem.BUTTON_HEIGHT,
            variant="danger",
            font=DesignSystem.FONT_BUTTON,
            command=self.cancel_download,
            state="disabled"
        )

        self.download_btn = ModernButton(
            self.action_row,
            text="Telecharger",
            width=140,
            height=DesignSystem.BUTTON_HEIGHT,
            font=DesignSystem.FONT_BUTTON,
            command=self.lancer_thread
        )

        # Initialiser avec le mode par defaut
        self.appliquer_layout_boutons("wide")

    def _on_resize(self, event):
        if event.widget == self:
            # On passe en mode compact en dessous de 550 pixels de large
            mode = "compact" if event.width < 550 else "wide"
            if mode != self.current_layout_mode:
                self.current_layout_mode = mode
                self.appliquer_layout_boutons(mode)

    def appliquer_layout_boutons(self, mode):
        # Retirer les boutons de la grille pour les replacer proprement
        self.open_folder_btn.grid_forget()
        self.cancel_btn.grid_forget()
        self.download_btn.grid_forget()

        if mode == "compact":
            # Mode compact : "Ouvrir le dossier" prend toute la largeur,
            # "Annuler" et "Telecharger" sont cote a cote en dessous (50% / 50%)
            self.action_row.grid_columnconfigure(0, weight=1)
            self.action_row.grid_columnconfigure(1, weight=1)
            self.action_row.grid_columnconfigure(2, weight=0, minsize=0)

            self.open_folder_btn.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, DesignSystem.SPACING_SM))
            self.cancel_btn.grid(row=1, column=0, columnspan=1, sticky="ew", padx=(0, DesignSystem.SPACING_SM))
            self.download_btn.grid(row=1, column=1, columnspan=1, sticky="ew")
        else:
            # Mode large : tout sur une seule ligne
            self.action_row.grid_columnconfigure(0, weight=1)
            self.action_row.grid_columnconfigure(1, weight=0, minsize=110)
            self.action_row.grid_columnconfigure(2, weight=0, minsize=140)

            self.open_folder_btn.grid(row=0, column=0, columnspan=1, sticky="w", pady=0)
            self.cancel_btn.grid(row=0, column=1, columnspan=1, sticky="e", padx=(0, DesignSystem.SPACING_SM), pady=0)
            self.download_btn.grid(row=0, column=2, columnspan=1, sticky="e", pady=0)

    def _build_status(self, parent):
        self.status_card = StatusCard(parent)
        self.status_card.grid(row=11, column=0, sticky="ew", pady=(DesignSystem.SPACING_MD, 0))

        self.status_label = self.status_card.status_label
        self.size_label = self.status_card.size_label
        self.speed_label = self.status_card.speed_label
        self.progress = self.status_card.progress
        self.progress_label = self.status_card.progress_label

    def _build_footer(self, parent):
        self.footer_label = ctk.CTkLabel(
            parent,
            text="Liens YouTube uniquement - pas de playlist - limite 2 Go",
            text_color=DesignSystem.COLORS["text_secondary"],
            font=DesignSystem.FONT_SMALL,
            anchor="w"
        )
        self.footer_label.grid(row=12, column=0, sticky="sew", pady=(DesignSystem.SPACING_SM, 0))

    # --- Actions utilisateur ---

    def choisir_dossier(self):
        """Ouvrir un dialogue pour choisir le dossier de destination."""
        dossier = filedialog.askdirectory(
            initialdir=self.output_path,
            title="Choisir le dossier de destination"
        )
        if dossier:
            self.output_path = os.path.abspath(dossier)
            self.dest_entry.configure(state="normal")
            self.dest_entry.delete(0, "end")
            self.dest_entry.insert(0, self.output_path)
            self.dest_entry.configure(state="disabled")
            self.set_status(f"Dossier : {self.output_path}", "success")

    def paste_clipboard(self):
        try:
            value = self.clipboard_get().strip()
        except Exception:
            self.set_status("Impossible de lire le presse-papiers.", "error")
            return

        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, value)
        self.set_status("Lien colle. Pret a analyser.", "success")

    def clear_input(self):
        self.url_entry.delete(0, "end")
        self.progress.set(0)
        self.progress_label.configure(text="0%")
        self.speed_label.configure(text="")
        self.update_size("Taille : en attente")
        self.set_status("Pret", "muted")

    def open_downloads(self):
        try:
            os.startfile(self.output_path)
        except Exception as exc:
            self.set_status(f"Impossible d'ouvrir le dossier : {exc}", "error")

    def lancer_thread(self):
        if self.is_downloading:
            return

        url = self.url_entry.get().strip()
        quality = self.quality_control.get()
        media_type_label = self.media_type_control.get()
        media_type = "audio" if media_type_label == "Audio (MP3)" else "video"

        if not url:
            self.set_status("Veuillez coller un lien YouTube.", "warning")
            return

        if not valider_url_youtube(url):
            self.set_status("Lien refuse. Utilisez une URL YouTube valide.", "error")
            return

        self.cancellation_requested = False
        self.set_busy(True)
        self.progress.set(0)
        self.progress_label.configure(text="0%")
        self.speed_label.configure(text="")
        self.update_size("Taille : analyse en cours...")
        self.set_status("Analyse du lien et du format...", "info")

        threading.Thread(
            target=self.tache_telechargement,
            args=(url, quality, media_type),
            daemon=True
        ).start()

    def cancel_download(self):
        self.cancellation_requested = True
        self.set_status("Annulation en cours...", "warning")
        self.cancel_btn.configure(state="disabled")

    def check_cancel(self):
        return self.cancellation_requested

    def tache_telechargement(self, url, quality, media_type):
        success = False
        try:
            success, message = telecharger_video_pro(
                url,
                quality,
                self.update_status_from_worker,
                self.update_progress,
                self.check_cancel,
                self.update_size,
                media_type=media_type,
                dossier_sortie=self.output_path,
            )

            if success:
                type_label = "Audio" if media_type == "audio" else "Video"
                self.set_status(f"{type_label} telecharge(e) avec succes !", "success")
                self.update_progress(100, "", "")

            else:
                self.set_status(f"Erreur : {message}", "error")

        except Exception as exc:
            self.set_status(f"Erreur systeme : {exc}", "error")

        finally:
            self.after(0, lambda: self.finish_download(success))

    def finish_download(self, success):
        self.set_busy(False)
        self.speed_label.configure(text="")
        if not success and self.cancellation_requested:
            self.progress.set(0)
            self.progress_label.configure(text="0%")

    def set_busy(self, busy):
        self.is_downloading = busy

        normal_state = "disabled" if busy else "normal"
        self.url_entry.configure(state=normal_state)
        self.paste_btn.configure(state=normal_state)
        self.quality_control.configure(state=normal_state)
        self.media_type_control.configure(state=normal_state)
        self.browse_btn.configure(state=normal_state)
        self.open_folder_btn.configure(state=normal_state)
        self.download_btn.configure(state=normal_state if not busy else "disabled")
        self.cancel_btn.configure(state="normal" if busy else "disabled")

    def set_status(self, text, kind="info"):
        self.after(0, lambda: self.status_card.update_status(text, kind))

    def update_status_from_worker(self, text):
        if "termine" in text.lower() or "success" in text.lower():
            self.set_status(text, "success")
        elif "erreur" in text.lower() or "error" in text.lower():
            self.set_status(f"{text}", "error")
        elif "annule" in text.lower() or "cancelled" in text.lower():
            self.set_status(f"{text}", "warning")
        else:
            self.set_status(f"{text}", "info")

    def update_progress(self, val, speed="", eta=""):
        value = max(0, min(100, float(val)))

        def apply_progress():
            self.progress.set_animated(value / 100)
            self.progress_label.configure(text=f"{value:.0f}%")
            # Construire le texte de vitesse + ETA
            parts = []
            if speed:
                parts.append(speed)
            if eta:
                parts.append(f"{eta} restant")
            self.speed_label.configure(text=" | ".join(parts))

        self.after(0, apply_progress)

    def update_size(self, text):
        self.after(0, lambda: self.size_label.configure(text=text))


if __name__ == "__main__":
    app = App()
    app.mainloop()