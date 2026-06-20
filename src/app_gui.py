# -*- coding: utf-8 -*-
# app_gui.py
import customtkinter as ctk
import threading
from telechargeur_core import telecharger_video_pro

# Configuration globale pour un look moderne
ctk.set_appearance_mode("System")  # Modes: "System", "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue", "green", "dark-blue"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("YouTube Downloader Pro")
        self.geometry("550x450")
        self.cancellation_requested = False

        # Titre principal
        self.label_title = ctk.CTkLabel(self, text="YouTube Downloader", font=("Roboto", 24, "bold"))
        self.label_title.pack(pady=20)

        # Entree URL
        self.url_entry = ctk.CTkEntry(self, width=450, placeholder_text="Collez le lien YouTube ici...")
        self.url_entry.pack(pady=10)

        # Selecteur de qualite
        self.quality_menu = ctk.CTkOptionMenu(
            self,
            values=["Haute (1080p)", "Moyenne (720p)", "Basse (480p)", "Tres Basse (240p)"],
            width=200,
        )
        self.quality_menu.pack(pady=10)

        # Taille du fichier correspondant au format choisi
        self.size_label = ctk.CTkLabel(self, text="Taille : en attente", text_color="gray")
        self.size_label.pack(pady=5)

        # Bouton Telecharger
        self.btn = ctk.CTkButton(self, text="Telecharger", command=self.lancer_thread, font=("Roboto", 14, "bold"))
        self.btn.pack(pady=20)

        # Bouton Annuler, cache par defaut
        self.cancel_btn = ctk.CTkButton(
            self,
            text="Annuler",
            command=self.cancel_download,
            fg_color="red",
            hover_color="darkred",
            font=("Roboto", 14, "bold"),
        )

        # Barre de progression
        self.progress = ctk.CTkProgressBar(self, width=450)
        self.progress.pack(pady=10)
        self.progress.set(0)

        # Etat
        self.status_label = ctk.CTkLabel(self, text="Pret", text_color="gray")
        self.status_label.pack(pady=10)

    def lancer_thread(self):
        url = self.url_entry.get()
        quality = self.quality_menu.get()

        if not url:
            self.status_label.configure(text="Erreur : Veuillez coller un lien.", text_color="red")
            return

        # Desactiver l'UI et afficher le bouton Annuler
        self.btn.configure(state="disabled")
        self.cancel_btn.pack(pady=5)
        self.status_label.configure(text_color="white")
        self.size_label.configure(text="Taille : analyse en cours", text_color="gray")
        self.cancellation_requested = False

        threading.Thread(target=self.tache_telechargement, args=(url, quality), daemon=True).start()

    def cancel_download(self):
        self.cancellation_requested = True
        self.update_status("Annulation en cours...")

    def check_cancel(self):
        return self.cancellation_requested

    def tache_telechargement(self, url, quality):
        try:
            success, message = telecharger_video_pro(
                url,
                quality,
                self.update_status,
                self.update_progress,
                self.check_cancel,
                self.update_size,
            )

            if success:
                self.update_status("Video telechargee avec succes !")
            else:
                self.update_status(f"Erreur : {message}")

        except Exception as e:
            self.update_status(f"Erreur systeme : {str(e)}")

        self.after(3000, self.reset_interface)

    def reset_interface(self):
        self.progress.set(0)
        self.status_label.configure(text="Pret", text_color="gray")
        self.size_label.configure(text="Taille : en attente", text_color="gray")
        self.btn.configure(state="normal")
        self.cancel_btn.pack_forget()

    def update_status(self, text):
        self.after(0, lambda: self.status_label.configure(text=text))

    def update_progress(self, val):
        self.after(0, lambda: self.progress.set(val / 100))

    def update_size(self, text):
        self.after(0, lambda: self.size_label.configure(text=text, text_color="white"))


if __name__ == "__main__":
    app = App()
    app.mainloop()
