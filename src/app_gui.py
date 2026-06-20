# -*- coding: utf-8 -*-
# app_gui.py
import customtkinter as ctk
import threading
from telechargeur_core import telecharger_video_pro

# Configuration globale pour un look moderne
ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("YouTube Downloader Pro")
        self.geometry("550x450")
        self.cancellation_requested = False

        # Titre principal
        self.label_title = ctk.CTkLabel(self, text="YouTube Downloader", font=("Roboto", 24, "bold"))
        self.label_title.pack(pady=20)

        # Entrée URL
        self.url_entry = ctk.CTkEntry(self, width=450, placeholder_text="Collez le lien YouTube ici...")
        self.url_entry.pack(pady=10)

        # Sélecteur de qualité
        self.quality_menu = ctk.CTkOptionMenu(self, values=["Haute (1080p)", "Moyenne (720p)", "Basse (480p)", "Très Basse (240p)"], width=200)
        self.quality_menu.pack(pady=10)

        # Bouton Télécharger
        self.btn = ctk.CTkButton(self, text="Télécharger", command=self.lancer_thread, font=("Roboto", 14, "bold"))
        self.btn.pack(pady=20)

        # Bouton Annuler (caché par défaut)
        self.cancel_btn = ctk.CTkButton(self, text="Annuler", command=self.cancel_download, fg_color="red", hover_color="darkred", font=("Roboto", 14, "bold"))
        # On ne le pack pas ici, on le fera quand nécessaire

        # Barre de progression
        self.progress = ctk.CTkProgressBar(self, width=450)
        self.progress.pack(pady=10)
        self.progress.set(0)

        # État
        self.status_label = ctk.CTkLabel(self, text="Prêt", text_color="gray")
        self.status_label.pack(pady=10)

    def lancer_thread(self):
        url = self.url_entry.get()
        quality = self.quality_menu.get()
        
        if not url:
            self.status_label.configure(text="Erreur : Veuillez coller un lien.", text_color="red")
            return
            
        # Désactiver UI et afficher bouton Annuler
        self.btn.configure(state="disabled")
        self.cancel_btn.pack(pady=5)
        self.status_label.configure(text_color="white")
        self.cancellation_requested = False
        
        # Lancer le thread
        threading.Thread(target=self.tache_telechargement, args=(url, quality), daemon=True).start()

    def cancel_download(self):
        self.cancellation_requested = True
        self.update_status("Annulation en cours...")

    def check_cancel(self):
        return self.cancellation_requested

    def tache_telechargement(self, url, quality):
        try:
            # Appel de la fonction corrigée avec le callback d'annulation
            success, message = telecharger_video_pro(url, quality, self.update_status, self.update_progress, self.check_cancel)

            if success:
                self.update_status("Vidéo téléchargée avec succès !")
            else:
                self.update_status(f"Erreur : {message}")

        except Exception as e:
            # Capture de toute erreur inattendue pour l'afficher dans l'interface
            self.update_status(f"Erreur système : {str(e)}")

        # Réinitialisation de l'interface après 3 secondes
        self.after(3000, self.reset_interface)

    def reset_interface(self):
        self.progress.set(0)
        self.status_label.configure(text="Prêt", text_color="gray")
        self.btn.configure(state="normal")
        self.cancel_btn.pack_forget() # Masquer le bouton Annuler

    def update_status(self, text):
        self.status_label.configure(text=text)

    def update_progress(self, val):
        self.progress.set(val / 100)

if __name__ == "__main__":
    app = App()
    app.mainloop()
