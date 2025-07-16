import customtkinter as ctk
import json
from datetime import datetime
from license_manager import LicenseManager
import os
from tkinter import ttk, messagebox

class LicenseGenerator:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Gerador de Licenças - FTP Manager")
        self.root.geometry("600x400")
        
        # Frame principal
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        title_label = ctk.CTkLabel(
            main_frame, 
            text="Gerador de Licenças FTP Manager",
            font=("Helvetica", 20)
        )
        title_label.pack(pady=20)
        
        # Frame para entrada do Machine ID
        id_frame = ctk.CTkFrame(main_frame)
        id_frame.pack(fill="x", padx=20, pady=10)
        
        # Label e entrada para Machine ID
        id_label = ctk.CTkLabel(id_frame, text="Machine ID:")
        id_label.pack(side="left", padx=5)
        
        self.id_entry = ctk.CTkEntry(id_frame, width=300)
        self.id_entry.pack(side="left", padx=5)
        
        # Frame para a chave de licença
        key_frame = ctk.CTkFrame(main_frame)
        key_frame.pack(fill="x", padx=20, pady=10)
        
        # Label e entrada para a chave de licença
        key_label = ctk.CTkLabel(key_frame, text="Chave de Licença:")
        key_label.pack(side="left", padx=5)
        
        self.key_entry = ctk.CTkEntry(key_frame, width=300)
        self.key_entry.pack(side="left", padx=5)
        
        # Botão para gerar licença
        generate_button = ctk.CTkButton(
            main_frame,
            text="Gerar Licença",
            command=self.generate_license
        )
        generate_button.pack(pady=20)
        
        self.license_manager = LicenseManager()
        
    def generate_license(self):
        machine_id = self.id_entry.get().strip()
        if not machine_id:
            messagebox.showerror("Erro", "Por favor, insira o Machine ID")
            return
            
        try:
            license_key = self.license_manager._generate_license_key(machine_id)
            self.key_entry.delete(0, 'end')
            self.key_entry.insert(0, license_key)
            messagebox.showinfo("Sucesso", "Licença gerada com sucesso!\nA chave foi inserida no campo 'Chave de Licença'.\nVocê pode selecionar e copiar a chave.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar licença: {str(e)}")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = LicenseGenerator()
    app.run()
