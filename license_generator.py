import customtkinter as ctk
import json
import pyperclip
from datetime import datetime
from license_manager import LicenseManager
import os
import csv
from tkinter import ttk

class LicenseGenerator:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Gerador de Licenças - FTP Manager")
        self.root.geometry("800x600")  # Aumentado para acomodar a nova funcionalidade
        
        # Criar notebook para abas
        self.notebook = ctk.CTkTabview(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Adicionar abas
        self.tab_generate = self.notebook.add("Gerar Licença")
        self.tab_manage = self.notebook.add("Gerenciar Licenças")
        
        # Configurar aba de geração
        self.setup_generate_tab()
        
        # Configurar aba de gerenciamento
        self.setup_manage_tab()
        
        self.license_manager = LicenseManager()
        
        # Arquivo para armazenar histórico de licenças
        self.licenses_file = "licenses_history.json"
        self.load_licenses_history()
        
    def setup_generate_tab(self):
        """Configura a aba de geração de licença"""
        # Frame principal
        main_frame = ctk.CTkFrame(self.tab_generate)
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
        
        # Label do Machine ID
        id_label = ctk.CTkLabel(id_frame, text="Machine ID do Cliente:")
        id_label.pack(anchor="w", pady=(5,0))
        
        # Frame para entrada e botão de colar
        input_frame = ctk.CTkFrame(id_frame)
        input_frame.pack(fill="x", pady=5)
        
        # Entrada do Machine ID
        self.machine_id_entry = ctk.CTkEntry(input_frame, width=400)
        self.machine_id_entry.pack(side="left", padx=(0,10))
        
        # Botão de colar
        paste_button = ctk.CTkButton(
            input_frame, 
            text="Colar", 
            width=80,
            command=self.paste_id
        )
        paste_button.pack(side="left")
        
        # Campo para nome/identificação do cliente
        client_frame = ctk.CTkFrame(main_frame)
        client_frame.pack(fill="x", padx=20, pady=10)
        
        client_label = ctk.CTkLabel(client_frame, text="Nome/Identificação do Cliente:")
        client_label.pack(anchor="w", pady=(5,0))
        
        self.client_entry = ctk.CTkEntry(client_frame, width=400)
        self.client_entry.pack(fill="x", pady=5)
        
        # Botão para gerar licença
        generate_button = ctk.CTkButton(
            main_frame,
            text="Gerar Licença",
            command=self.generate_license,
            width=200
        )
        generate_button.pack(pady=20)
        
        # Frame para o resultado
        result_frame = ctk.CTkFrame(main_frame)
        result_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Label do resultado
        result_label = ctk.CTkLabel(result_frame, text="Licença Gerada:")
        result_label.pack(anchor="w", pady=5)
        
        # Área de resultado
        self.result_text = ctk.CTkTextbox(result_frame, height=200)
        self.result_text.pack(fill="both", expand=True, pady=5)
        
        # Frame para botões de ação
        button_frame = ctk.CTkFrame(result_frame)
        button_frame.pack(fill="x", pady=10)
        
        # Botão de copiar
        self.copy_button = ctk.CTkButton(
            button_frame,
            text="Copiar Licença",
            command=self.copy_license,
            width=150,
            state="disabled"
        )
        self.copy_button.pack(side="left", padx=5)
        
        # Botão de salvar
        self.save_button = ctk.CTkButton(
            button_frame,
            text="Salvar em Arquivo",
            command=self.save_license,
            width=150,
            state="disabled"
        )
        self.save_button.pack(side="left", padx=5)
        
        # Botão de limpar
        clear_button = ctk.CTkButton(
            button_frame,
            text="Limpar",
            command=self.clear_form,
            width=150
        )
        clear_button.pack(side="left", padx=5)
    
    def setup_manage_tab(self):
        """Configura a aba de gerenciamento de licenças"""
        # Frame principal
        main_frame = ctk.CTkFrame(self.tab_manage)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        title_label = ctk.CTkLabel(
            main_frame, 
            text="Gerenciar Licenças",
            font=("Helvetica", 20)
        )
        title_label.pack(pady=20)
        
        # Frame de pesquisa
        search_frame = ctk.CTkFrame(main_frame)
        search_frame.pack(fill="x", padx=20, pady=10)
        
        search_label = ctk.CTkLabel(search_frame, text="Pesquisar:")
        search_label.pack(side="left", padx=5)
        
        self.search_entry = ctk.CTkEntry(search_frame, width=300)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<KeyRelease>", self.filter_licenses)
        
        # Frame para a lista de licenças
        list_frame = ctk.CTkFrame(main_frame)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Criar Treeview
        self.tree = ttk.Treeview(list_frame, columns=("Data", "Cliente", "Machine ID", "Licença"), show="headings")
        self.tree.heading("Data", text="Data")
        self.tree.heading("Cliente", text="Cliente")
        self.tree.heading("Machine ID", text="Machine ID")
        self.tree.heading("Licença", text="Licença")
        
        # Configurar larguras das colunas
        self.tree.column("Data", width=150)
        self.tree.column("Cliente", width=200)
        self.tree.column("Machine ID", width=200)
        self.tree.column("Licença", width=200)
        
        # Adicionar scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Posicionar elementos
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Frame de botões
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", padx=20, pady=10)
        
        # Botões de ação
        refresh_button = ctk.CTkButton(
            button_frame,
            text="Atualizar Lista",
            command=self.refresh_licenses_list,
            width=150
        )
        refresh_button.pack(side="left", padx=5)
        
        export_button = ctk.CTkButton(
            button_frame,
            text="Exportar Lista",
            command=self.export_licenses,
            width=150
        )
        export_button.pack(side="left", padx=5)
        
    def load_licenses_history(self):
        """Carrega o histórico de licenças do arquivo"""
        try:
            if os.path.exists(self.licenses_file):
                with open(self.licenses_file, 'r') as f:
                    self.licenses_history = json.load(f)
            else:
                self.licenses_history = []
        except Exception as e:
            self.show_error(f"Erro ao carregar histórico de licenças: {str(e)}")
            self.licenses_history = []
    
    def save_licenses_history(self):
        """Salva o histórico de licenças no arquivo"""
        try:
            with open(self.licenses_file, 'w') as f:
                json.dump(self.licenses_history, f, indent=4)
        except Exception as e:
            self.show_error(f"Erro ao salvar histórico de licenças: {str(e)}")
    
    def refresh_licenses_list(self):
        """Atualiza a lista de licenças na interface"""
        # Limpar lista atual
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Adicionar licenças
        for license in self.licenses_history:
            self.tree.insert("", "end", values=(
                license["generation_date"],
                license["client_name"],
                license["machine_id"],
                license["license_key"]
            ))
    
    def filter_licenses(self, event=None):
        """Filtra a lista de licenças com base no texto de pesquisa"""
        search_text = self.search_entry.get().lower()
        
        # Limpar lista atual
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Adicionar licenças filtradas
        for license in self.licenses_history:
            if (search_text in license["client_name"].lower() or
                search_text in license["machine_id"].lower() or
                search_text in license["license_key"].lower()):
                self.tree.insert("", "end", values=(
                    license["generation_date"],
                    license["client_name"],
                    license["machine_id"],
                    license["license_key"]
                ))
    
    def export_licenses(self):
        """Exporta a lista de licenças para um arquivo CSV"""
        try:
            filename = f"licenses_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Data", "Cliente", "Machine ID", "Licença"])
                for license in self.licenses_history:
                    writer.writerow([
                        license["generation_date"],
                        license["client_name"],
                        license["machine_id"],
                        license["license_key"]
                    ])
            self.show_success(f"Lista exportada para {filename}")
        except Exception as e:
            self.show_error(f"Erro ao exportar licenças: {str(e)}")
    
    def generate_license(self):
        """Gera uma nova licença"""
        machine_id = self.machine_id_entry.get().strip()
        client_name = self.client_entry.get().strip()
        
        if not machine_id:
            self.show_error("Por favor, insira o Machine ID do cliente")
            return
            
        if not client_name:
            self.show_error("Por favor, insira o nome/identificação do cliente")
            return
        
        try:
            # Gera a licença
            license_key = self.license_manager._generate_license_key(machine_id)
            
            # Formata o resultado
            result = {
                "machine_id": machine_id,
                "client_name": client_name,
                "license_key": license_key,
                "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Adiciona ao histórico
            self.licenses_history.append(result)
            self.save_licenses_history()
            
            # Atualiza a lista
            self.refresh_licenses_list()
            
            # Mostra o resultado
            self.result_text.delete("0.0", "end")
            self.result_text.insert("0.0", 
                f"=== Licença FTP Manager ===\n\n"
                f"Data de Geração: {result['generation_date']}\n"
                f"Cliente: {result['client_name']}\n"
                f"Machine ID: {result['machine_id']}\n"
                f"Chave de Licença: {result['license_key']}\n\n"
                f"Instruções:\n"
                f"1. Forneça esta chave de licença ao cliente\n"
                f"2. O cliente deve usar a opção 'Ativar Licença' no menu do FTP Manager\n"
                f"3. A licença é válida apenas para o computador com o Machine ID fornecido"
            )
            
            # Habilita botões
            self.copy_button.configure(state="normal")
            self.save_button.configure(state="normal")
            
        except Exception as e:
            self.show_error(f"Erro ao gerar licença: {str(e)}")
    
    def show_success(self, message):
        """Mostra uma mensagem de sucesso"""
        ctk.CTkMessagebox(
            title="Sucesso",
            message=message,
            icon="check"
        )
    
    def paste_id(self):
        """Cola o conteúdo da área de transferência no campo de Machine ID"""
        try:
            self.machine_id_entry.delete(0, "end")
            self.machine_id_entry.insert(0, pyperclip.paste())
        except:
            pass
    
    def copy_license(self):
        """Copia a licença para a área de transferência"""
        try:
            license_text = self.result_text.get("0.0", "end")
            pyperclip.copy(license_text)
            self.copy_button.configure(text="Copiado!")
            self.root.after(1500, lambda: self.copy_button.configure(text="Copiar Licença"))
        except Exception as e:
            self.show_error(f"Erro ao copiar licença: {str(e)}")
    
    def save_license(self):
        """Salva a licença em um arquivo"""
        try:
            machine_id = self.machine_id_entry.get().strip()
            date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"license_{machine_id}_{date_str}.txt"
            
            with open(filename, "w") as f:
                f.write(self.result_text.get("0.0", "end"))
            
            self.save_button.configure(text="Salvo!")
            self.root.after(1500, lambda: self.save_button.configure(text="Salvar em Arquivo"))
        except Exception as e:
            self.show_error(f"Erro ao salvar licença: {str(e)}")
    
    def clear_form(self):
        """Limpa o formulário"""
        self.machine_id_entry.delete(0, "end")
        self.client_entry.delete(0, "end")
        self.result_text.delete("0.0", "end")
        self.copy_button.configure(state="disabled")
        self.save_button.configure(state="disabled")
    
    def show_error(self, message):
        """Mostra uma mensagem de erro"""
        ctk.CTkMessagebox(
            title="Erro",
            message=message,
            icon="cancel"
        )
    
    def run(self):
        """Inicia o aplicativo"""
        self.root.mainloop()

if __name__ == "__main__":
    app = LicenseGenerator()
    app.run()
