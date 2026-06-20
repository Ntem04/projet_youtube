# -*- coding: utf-8 -*-
# app_gui.py
import os
import threading
import customtkinter as ctk

from telechargeur_core import chemin_telechargements, telecharger_video_pro, valider_url_youtube


ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class DesignSystem:
    SPACING_XS = 4
    SPACING_SM = 8
    SPACING_MD = 12
    SPACING_LG = 16
    SPACING_XL = 24
    SPACING_2XL = 32
    
    CORNER_RADIUS_SM = 6
    CORNER_RADIUS_MD = 10
    CORNER_RADIUS_LG = 12
    
    BUTTON_HEIGHT = 44
    INPUT_HEIGHT = 42
    
    FONT_TITLE = ("Segoe UI", 26, "bold")
    FONT_SUBTITLE = ("Segoe UI", 13)
    FONT_LABEL = ("Segoe UI", 14, "bold")
    FONT_BODY = ("Segoe UI", 13)
    FONT_SMALL = ("Segoe UI", 12)
    FONT_BUTTON = ("Segoe UI", 14, "bold")
    
    COLORS = {
        "bg_primary": ("#f4f7fb", "#0f1419"),
        "bg_secondary": ("#ffffff", "#1a1f26"),
        "bg_tertiary": ("#f7f9fc", "#11161c"),
        "text_primary": ("#1a202c", "#e8edf5"),
        "text_secondary": ("#5b6675", "#aab4c0"),
        "text_tertiary": ("#6b7280", "#8f9baa"),
        "border": ("#e5e7eb", "#2a3038"),
        "input_bg": ("#ffffff", "#1f2530"),
    }
    
    STATUS_COLORS = {
        "muted": ("#5b6675", "#aab4c0"),
        "info": ("#1f5eff", "#74a7ff"),
        "success": ("#067647", "#3ccb7f"),
        "warning": ("#b54708", "#fdb022"),
        "error": ("#b42318", "#ff7b72"),
    }
    
    BUTTON_STATES = {
        "primary": {
            "fg": ("#2563eb", "#3b82f6"),
            "hover": ("#1d4ed8", "#1e40af"),
        },
        "secondary": {
            "fg": ("#e8edf5", "#2a3038"),
            "hover": ("#dbe3ef", "#343b45"),
            "text": ("#253142", "#e8edf5"),
        },
        "danger": {
            "fg": ("#d92d20", "#b42318"),
            "hover": ("#b42318", "#912018"),
        },
    }


QUALITY_OPTIONS = ["Haute (1080p)", "Moyenne (720p)", "Basse (480p)", "Tres Basse (240p)"]


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
    def __init__(self, *args, variant="primary", **kwargs):
        self.variant = variant
        
        if variant == "secondary":
            kwargs.setdefault("fg_color", DesignSystem.BUTTON_STATES["secondary"]["fg"])
            kwargs.setdefault("hover_color", DesignSystem.BUTTON_STATES["secondary"]["hover"])
            kwargs.setdefault("text_color", DesignSystem.BUTTON_STATES["secondary"]["text"])
        elif variant == "danger":
            kwargs.setdefault("fg_color", DesignSystem.BUTTON_STATES["danger"]["fg"])
            kwargs.setdefault("hover_color", DesignSystem.BUTTON_STATES["danger"]["hover"])
        else:
            kwargs.setdefault("fg_color", DesignSystem.BUTTON_STATES["primary"]["fg"])
            kwargs.setdefault("hover_color", DesignSystem.BUTTON_STATES["primary"]["hover"])
        
        super().__init__(*args, **kwargs)


class StatusCard(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, corner_radius=DesignSystem.CORNER_RADIUS_MD, 
                        fg_color=DesignSystem.COLORS["bg_tertiary"], **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        
        self.title_label = ctk.CTkLabel(
            self,
            text="Etat du telechargement",
            font=DesignSystem.FONT_LABEL,
            anchor="w",
            text_color=DesignSystem.COLORS["text_primary"]
        )
        self.title_label.grid(row=0, column=0, sticky="ew", padx=DesignSystem.SPACING_LG, 
                             pady=(DesignSystem.SPACING_LG, DesignSystem.SPACING_SM))
        
        self.status_label = ctk.CTkLabel(
            self,
            text="Pret",
            text_color=DesignSystem.COLORS["text_secondary"],
            font=DesignSystem.FONT_BODY,
            anchor="w",
            justify="left",
            wraplength=620
        )
        self.status_label.grid(row=1, column=0, sticky="ew", padx=DesignSystem.SPACING_LG, 
                              pady=(0, DesignSystem.SPACING_SM))
        
        self.size_label = ctk.CTkLabel(
            self,
            text="Taille : en attente",
            text_color=DesignSystem.COLORS["text_secondary"],
            font=DesignSystem.FONT_BODY,
            anchor="w",
            justify="left",
            wraplength=620
        )
        self.size_label.grid(row=2, column=0, sticky="ew", padx=DesignSystem.SPACING_LG, 
                            pady=(0, DesignSystem.SPACING_LG))
        
        progress_row = ctk.CTkFrame(self, fg_color="transparent")
        progress_row.grid(row=3, column=0, sticky="ew", padx=DesignSystem.SPACING_LG, 
                         pady=(0, DesignSystem.SPACING_LG))
        progress_row.grid_columnconfigure(0, weight=1)
        
        self.progress = AnimatedProgressBar(progress_row, height=10)
        self.progress.grid(row=0, column=0, sticky="ew")
        self.progress.set(0)
        
        self.progress_label = ctk.CTkLabel(
            progress_row,
            text="0%",
            width=50,
            text_color=DesignSystem.COLORS["text_secondary"],
            font=("Segoe UI", 11, "bold")
        )
        self.progress_label.grid(row=0, column=1, padx=(DesignSystem.SPACING_MD, 0))
    
    def update_status(self, text, kind="info"):
        color = DesignSystem.STATUS_COLORS.get(kind, DesignSystem.STATUS_COLORS["info"])
        self.status_label.configure(text=text, text_color=color)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("YouTube Downloader Pro")
        self.geometry("800x640")
        self.minsize(740, 600)
        
        self.cancellation_requested = False
        self.is_downloading = False
        
        self.configure(fg_color=DesignSystem.COLORS["bg_primary"])
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self._build_ui()
    
    def _build_ui(self):
        self._build_header()
        self._build_main()
        self._build_footer()
    
    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=DesignSystem.SPACING_2XL, 
                   pady=(DesignSystem.SPACING_2XL, DesignSystem.SPACING_MD))
        header.grid_columnconfigure(0, weight=1)
        
        title = ctk.CTkLabel(
            header,
            text="YouTube Downloader Pro",
            font=DesignSystem.FONT_TITLE,
            anchor="w",
            text_color=DesignSystem.COLORS["text_primary"]
        )
        title.grid(row=0, column=0, sticky="ew")
        
        subtitle = ctk.CTkLabel(
            header,
            text="Telechargement MP4 securise vers votre dossier Downloads",
            text_color=DesignSystem.COLORS["text_tertiary"],
            font=DesignSystem.FONT_SUBTITLE,
            anchor="w"
        )
        subtitle.grid(row=1, column=0, sticky="ew", pady=(DesignSystem.SPACING_SM, 0))
    
    def _build_main(self):
        main = ctk.CTkFrame(self, corner_radius=DesignSystem.CORNER_RADIUS_LG, 
                          fg_color=DesignSystem.COLORS["bg_secondary"])
        main.grid(row=1, column=0, sticky="nsew", padx=DesignSystem.SPACING_2XL, 
                 pady=DesignSystem.SPACING_MD)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(4, weight=1)
        
        url_label = ctk.CTkLabel(
            main,
            text="Lien YouTube",
            font=DesignSystem.FONT_LABEL,
            anchor="w",
            text_color=DesignSystem.COLORS["text_primary"]
        )
        url_label.grid(row=0, column=0, sticky="ew", padx=DesignSystem.SPACING_2XL, 
                      pady=(DesignSystem.SPACING_2XL, DesignSystem.SPACING_SM))
        
        url_row = ctk.CTkFrame(main, fg_color="transparent")
        url_row.grid(row=1, column=0, sticky="ew", padx=DesignSystem.SPACING_2XL)
        url_row.grid_columnconfigure(0, weight=1)
        
        self.url_entry = ctk.CTkEntry(
            url_row,
            height=DesignSystem.INPUT_HEIGHT,
            placeholder_text="https://www.youtube.com/watch?v=...",
            border_width=1,
            fg_color=DesignSystem.COLORS["input_bg"],
            border_color=DesignSystem.COLORS["border"],
            font=DesignSystem.FONT_BODY
        )
        self.url_entry.grid(row=0, column=0, sticky="ew")
        self.url_entry.bind("<Return>", lambda _: self.lancer_thread())
        
        self.paste_btn = ModernButton(
            url_row, 
            text="Coller", 
            width=100, 
            height=DesignSystem.INPUT_HEIGHT,
            font=DesignSystem.FONT_BUTTON,
            command=self.paste_clipboard
        )
        self.paste_btn.grid(row=0, column=1, padx=(DesignSystem.SPACING_MD, 0))
        
        self.clear_btn = ModernButton(
            url_row,
            text="Effacer",
            width=100,
            height=DesignSystem.INPUT_HEIGHT,
            variant="secondary",
            font=DesignSystem.FONT_BUTTON,
            command=self.clear_input
        )
        self.clear_btn.grid(row=0, column=2, padx=(DesignSystem.SPACING_MD, 0))
        
        quality_label = ctk.CTkLabel(
            main,
            text="Qualite video",
            font=DesignSystem.FONT_LABEL,
            anchor="w",
            text_color=DesignSystem.COLORS["text_primary"]
        )
        quality_label.grid(row=2, column=0, sticky="ew", padx=DesignSystem.SPACING_2XL, 
                          pady=(DesignSystem.SPACING_2XL, DesignSystem.SPACING_SM))
        
        self.quality_control = ctk.CTkSegmentedButton(
            main,
            values=QUALITY_OPTIONS,
            height=38,
            font=DesignSystem.FONT_SMALL,
            command=lambda _: self.update_size("Taille : en attente")
        )
        self.quality_control.set("Moyenne (720p)")
        self.quality_control.grid(row=3, column=0, sticky="ew", padx=DesignSystem.SPACING_2XL)
        
        self.status_card = StatusCard(main)
        self.status_card.grid(row=4, column=0, sticky="nsew", padx=DesignSystem.SPACING_2XL, 
                             pady=(DesignSystem.SPACING_2XL, DesignSystem.SPACING_LG))
        
        self.status_label = self.status_card.status_label
        self.size_label = self.status_card.size_label
        self.progress = self.status_card.progress
        self.progress_label = self.status_card.progress_label
        
        action_row = ctk.CTkFrame(main, fg_color="transparent")
        action_row.grid(row=5, column=0, sticky="ew", padx=DesignSystem.SPACING_2XL, 
                       pady=(0, DesignSystem.SPACING_2XL))
        action_row.grid_columnconfigure(1, weight=1)
        
        self.open_folder_btn = ModernButton(
            action_row,
            text="Ouvrir Downloads",
            height=DesignSystem.BUTTON_HEIGHT,
            variant="secondary",
            font=DesignSystem.FONT_BUTTON,
            command=self.open_downloads
        )
        self.open_folder_btn.grid(row=0, column=0, sticky="w")
        
        self.download_btn = ModernButton(
            action_row,
            text="Telecharger",
            height=DesignSystem.BUTTON_HEIGHT,
            font=DesignSystem.FONT_BUTTON,
            command=self.lancer_thread
        )
        self.download_btn.grid(row=0, column=2, padx=(DesignSystem.SPACING_MD, 0))
        
        self.cancel_btn = ModernButton(
            action_row,
            text="Annuler",
            height=DesignSystem.BUTTON_HEIGHT,
            variant="danger",
            font=DesignSystem.FONT_BUTTON,
            command=self.cancel_download,
            state="disabled"
        )
        self.cancel_btn.grid(row=0, column=3, padx=(DesignSystem.SPACING_MD, 0))
    
    def _build_footer(self):
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=DesignSystem.SPACING_2XL, 
                   pady=(0, DesignSystem.SPACING_LG))
        footer.grid_columnconfigure(0, weight=1)
        
        self.footer_label = ctk.CTkLabel(
            footer,
            text="Securite active : liens YouTube uniquement, pas de playlist, limite 2 Go.",
            text_color=DesignSystem.COLORS["text_tertiary"],
            font=DesignSystem.FONT_SMALL,
            anchor="w"
        )
        self.footer_label.grid(row=0, column=0, sticky="ew")
    
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
        self.update_size("Taille : en attente")
        self.set_status("Pret", "muted")
    
    def open_downloads(self):
        try:
            os.startfile(chemin_telechargements())
        except Exception as exc:
            self.set_status(f"Impossible d'ouvrir Downloads : {exc}", "error")
    
    def lancer_thread(self):
        if self.is_downloading:
            return
        
        url = self.url_entry.get().strip()
        quality = self.quality_control.get()
        
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
        self.update_size("Taille : analyse en cours...")
        self.set_status("Analyse du lien et du format...", "info")
        
        threading.Thread(
            target=self.tache_telechargement, 
            args=(url, quality), 
            daemon=True
        ).start()
    
    def cancel_download(self):
        self.cancellation_requested = True
        self.set_status("Annulation en cours...", "warning")
        self.cancel_btn.configure(state="disabled")
    
    def check_cancel(self):
        return self.cancellation_requested
    
    def tache_telechargement(self, url, quality):
        success = False
        try:
            success, message = telecharger_video_pro(
                url,
                quality,
                self.update_status_from_worker,
                self.update_progress,
                self.check_cancel,
                self.update_size,
            )
            
            if success:
                self.set_status("Video telechargee avec succes!", "success")
                self.update_progress(100)
            else:
                self.set_status(f"Erreur : {message}", "error")
        
        except Exception as exc:
            self.set_status(f"Erreur systeme : {exc}", "error")
        
        finally:
            self.after(0, lambda: self.finish_download(success))
    
    def finish_download(self, success):
        self.set_busy(False)
        if not success and self.cancellation_requested:
            self.progress.set(0)
            self.progress_label.configure(text="0%")
    
    def set_busy(self, busy):
        self.is_downloading = busy
        
        normal_state = "disabled" if busy else "normal"
        self.url_entry.configure(state=normal_state)
        self.paste_btn.configure(state=normal_state)
        self.clear_btn.configure(state=normal_state)
        self.quality_control.configure(state=normal_state)
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
    
    def update_progress(self, val):
        value = max(0, min(100, float(val)))
        
        def apply_progress():
            self.progress.set_animated(value / 100)
            self.progress_label.configure(text=f"{value:.0f}%")
        
        self.after(0, apply_progress)
    
    def update_size(self, text):
        self.after(0, lambda: self.size_label.configure(text=text))


if __name__ == "__main__":
    app = App()
    app.mainloop()