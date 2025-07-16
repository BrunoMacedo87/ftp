import os
import json
import logging
import threading
import queue
import time
from datetime import datetime
from tkinter import filedialog, messagebox
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from dotenv import load_dotenv
from ftp_uploader import FTPImageUploader
from file_log import FileLog
from file_handler import FileHandler
# Dependências opcionais
try:
    import pystray
except ImportError:
    pystray = None
try:
    from PIL import Image
except ImportError:
    Image = None
from assets.icon import create_icon
# from license_manager import LicenseManager  # Removido - sistema liberado
# Watchdog Observer
try:
    from watchdog.observers import Observer
except ImportError:
    Observer = None
import winshell
import win32con
import win32com
import win32api
import pywintypes
import sys

class FTPManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        # Corrigir APPDATA None
        appdata = os.getenv('APPDATA') or os.path.expanduser('~')
        self.app_data_dir = os.path.join(appdata, 'FTP Manager')
        if not os.path.exists(self.app_data_dir):
            os.makedirs(self.app_data_dir)
        
        # Configurar logging antes de qualquer coisa
        log_file = os.path.join(self.app_data_dir, "ftp_manager.log")
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Licença removida - sistema liberado
        
        self.title("TARGETWEB FTP")
        self.geometry("1024x768")  # Aumentando o tamanho inicial da janela
        
        # Define o ícone da janela
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "public", "favicon.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
                # Define o mesmo ícone para todas as janelas filhas
                self.iconphoto(True, tk.PhotoImage(file=icon_path.replace(".ico", ".png")))
        except Exception as e:
            self.logger.error(f"Erro ao carregar ícone da janela: {str(e)}")
        
        # Criar menu
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)
        
        # Menu de Licença removido - sistema liberado
        
        self.is_connected = False
        self.ftp_uploader = None
        self.observer = None
        self.event_handler = None
        self.auto_upload_enabled = True
        self.upload_queue = queue.Queue()
        self.upload_threads = {}
        
        # Inicia thread de processamento de upload
        self.upload_processor = threading.Thread(target=self._process_upload_queue, daemon=True)
        self.upload_processor.start()
        
        self.config_file = os.path.join(self.app_data_dir, "ftp_config.json")
        
        # Inicializar gerenciador de arquivos
        self.file_log = FileLog()
        
        # Variáveis de configuração
        self.host_var = tk.StringVar(value="")
        self.port_var = tk.StringVar(value="21")
        self.user_var = tk.StringVar(value="")
        self.pass_var = tk.StringVar(value="")
        self.monitored_folder_var = tk.StringVar(value="")
        self.monitored_folder_var.trace_add("write", lambda *args: self.update_file_list())
        
        # Fila de eventos para comunicação entre threads
        self.event_queue = queue.Queue()
        
        # Configuração do ícone do system tray
        self.icon = None
        self.setup_system_tray()
        
        # Evento para controlar a visibilidade da janela
        self.is_visible = True
        self.is_running = True
        
        # Intercepta o evento de fechar a janela
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.startup_checkbox_var = tk.BooleanVar(value=False)
        self.autoconnect_checkbox_var = tk.BooleanVar(value=False)
        
        self.setup_ui()
        self.load_config()
        self.load_startup_checkbox()
        # Conexão automática se opção marcada
        if self.autoconnect_checkbox_var.get() and all([
            self.host_var.get(), self.port_var.get(), self.user_var.get(), self.pass_var.get()
        ]):
            self.logger.info("Tentando conexão automática ao FTP...")
            self.connect_ftp()
        
        # Iniciar timers
        self.update_timer = None
        self.start_auto_update()
        self.check_new_files()  # Inicia a verificação de novos arquivos
        
        # Inicia o processamento de eventos
        self.process_events()
        
    def setup_ui(self):
        """Configura a interface do usuário"""
        # Frame principal
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Frame de configuração
        config_frame = ctk.CTkFrame(main_frame)
        config_frame.pack(fill=tk.X, padx=5, pady=5)

        # Campos de configuração
        # Host
        host_frame = ctk.CTkFrame(config_frame)
        host_frame.pack(fill=tk.X, padx=5, pady=2)
        host_label = ctk.CTkLabel(host_frame, text="Host:")
        host_label.pack(side=tk.LEFT)
        self.host_var = tk.StringVar()
        host_entry = ctk.CTkEntry(host_frame, textvariable=self.host_var, width=200)
        host_entry.pack(side=tk.LEFT, padx=5)

        # Port
        port_frame = ctk.CTkFrame(config_frame)
        port_frame.pack(fill=tk.X, padx=5, pady=2)
        port_label = ctk.CTkLabel(port_frame, text="Port:")
        port_label.pack(side=tk.LEFT)
        self.port_var = tk.StringVar(value="21")
        port_entry = ctk.CTkEntry(port_frame, textvariable=self.port_var, width=200)
        port_entry.pack(side=tk.LEFT, padx=5)

        # Username
        user_frame = ctk.CTkFrame(config_frame)
        user_frame.pack(fill=tk.X, padx=5, pady=2)
        user_label = ctk.CTkLabel(user_frame, text="Username:")
        user_label.pack(side=tk.LEFT)
        self.user_var = tk.StringVar()
        user_entry = ctk.CTkEntry(user_frame, textvariable=self.user_var, width=200)
        user_entry.pack(side=tk.LEFT, padx=5)

        # Password
        pass_frame = ctk.CTkFrame(config_frame)
        pass_frame.pack(fill=tk.X, padx=5, pady=2)
        pass_label = ctk.CTkLabel(pass_frame, text="Password:")
        pass_label.pack(side=tk.LEFT)
        self.pass_var = tk.StringVar()
        pass_entry = ctk.CTkEntry(pass_frame, textvariable=self.pass_var, show="*", width=200)
        pass_entry.pack(side=tk.LEFT, padx=5)

        # Monitored Folder
        folder_frame = ctk.CTkFrame(config_frame)
        folder_frame.pack(fill=tk.X, padx=5, pady=2)
        folder_label = ctk.CTkLabel(folder_frame, text="Pasta:")
        folder_label.pack(side=tk.LEFT)
        self.monitored_folder_var = tk.StringVar()
        folder_entry = ctk.CTkEntry(folder_frame, textvariable=self.monitored_folder_var, width=400)
        folder_entry.pack(side=tk.LEFT, padx=5)
        folder_button = ctk.CTkButton(folder_frame, text="Escolher", command=self.browse_folder)
        folder_button.pack(side=tk.LEFT, padx=5)

        # Botões de ação
        button_frame = ctk.CTkFrame(config_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        save_button = ctk.CTkButton(button_frame, text="Salvar Configuração", command=self.save_config)
        save_button.pack(side=tk.LEFT, padx=5)
        
        self.connect_button = ctk.CTkButton(button_frame, text="Conectar ao Servidor", command=self.connect_ftp)
        self.connect_button.pack(side=tk.LEFT, padx=5)
        
        stop_button = ctk.CTkButton(button_frame, text="Parar", command=self.stop_monitoring)
        stop_button.pack(side=tk.LEFT, padx=5)
        
        # Status
        self.status_label = ctk.CTkLabel(main_frame, text="Status: Desconectado")
        self.status_label.pack(pady=5)

        # Frame da tabela
        self.table_frame = ctk.CTkFrame(main_frame)
        self.table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Frame de pesquisa
        search_frame = ctk.CTkFrame(self.table_frame)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Campo de pesquisa
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.update_file_list())
        search_entry = ctk.CTkEntry(search_frame, textvariable=self.search_var, placeholder_text="Pesquisar arquivos...")
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Botão limpar pesquisa
        clear_button = ctk.CTkButton(search_frame, text="✕", width=30, command=lambda: self.search_var.set(""))
        clear_button.pack(side=tk.RIGHT)

        # Tabela de arquivos
        columns = ("Nome", "Tipo", "Tamanho", "Status", "Data Modificação", "Data Envio")
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show="headings", selectmode="extended")
        
        # Configurar cabeçalhos
        self.tree.heading("Nome", text="Nome", command=lambda: self.sort_treeview("Nome", False))
        self.tree.heading("Tipo", text="Tipo", command=lambda: self.sort_treeview("Tipo", False))
        self.tree.heading("Tamanho", text="Tamanho", command=lambda: self.sort_treeview("Tamanho", False))
        self.tree.heading("Status", text="Status", command=lambda: self.sort_treeview("Status", False))
        self.tree.heading("Data Modificação", text="Data Modificação", command=lambda: self.sort_treeview("Data Modificação", False))
        self.tree.heading("Data Envio", text="Data Envio", command=lambda: self.sort_treeview("Data Envio", False))
        
        # Configurar colunas
        self.tree.column("Nome", width=200)
        self.tree.column("Tipo", width=50)
        self.tree.column("Tamanho", width=100)
        self.tree.column("Status", width=100)
        self.tree.column("Data Modificação", width=150)
        self.tree.column("Data Envio", width=150)

        # Scrollbar
        scrollbar = ttk.Scrollbar(self.table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Layout
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Botão de upload
        self.upload_button = ctk.CTkButton(main_frame, text="Enviar Arquivo Manualmente", command=self.upload_files)
        self.upload_button.pack(pady=5)

        # Frame de progresso
        self.progress_frame = ctk.CTkFrame(main_frame)
        self.progress_frame.pack(fill=tk.X, padx=5, pady=5)
        self.progress_frame.pack_forget()  # Inicialmente oculto
        
        # Label e barra de progresso
        self.progress_label = ctk.CTkLabel(self.progress_frame, text="Enviando arquivo: ")
        self.progress_label.pack(side=tk.LEFT, padx=5)
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.progress_bar.set(0)

        # Após os botões de ação, adicionar checkboxes
        self.startup_checkbox = ctk.CTkCheckBox(
            config_frame,
            text="Iniciar com o Windows",
            variable=self.startup_checkbox_var,
            command=self.toggle_startup
        )
        self.startup_checkbox.pack(anchor=tk.W, padx=5, pady=2)
        self.autoconnect_checkbox = ctk.CTkCheckBox(
            config_frame,
            text="Conectar automaticamente ao FTP ao abrir",
            variable=self.autoconnect_checkbox_var,
            command=self.save_config
        )
        self.autoconnect_checkbox.pack(anchor=tk.W, padx=5, pady=2)

    def save_config(self):
        """Salva as configurações do servidor e preferências"""
        config = {
            'host': self.host_var.get(),
            'port': self.port_var.get(),
            'user': self.user_var.get(),
            'password': self.pass_var.get(),
            'monitored_folder': self.monitored_folder_var.get(),
            'autoconnect': self.autoconnect_checkbox_var.get()
        }
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
            messagebox.showinfo("Sucesso", "Configurações salvas com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar configurações: {str(e)}")

    def load_config(self):
        """Carrega as configurações do servidor e preferências"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.host_var.set(config.get('host', ''))
                    self.port_var.set(config.get('port', '21'))
                    self.user_var.set(config.get('user', ''))
                    self.pass_var.set(config.get('password', ''))
                    self.monitored_folder_var.set(config.get('monitored_folder', ''))
                    self.autoconnect_checkbox_var.set(config.get('autoconnect', False))
                    return config
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar configurações: {str(e)}")

    def connect_ftp(self):
        """Conecta ao servidor FTP"""
        try:
            # Se já estiver conectado, desconecta
            if self.is_connected:
                if self.ftp_uploader:
                    self.ftp_uploader.disconnect()
                self.is_connected = False
                self.connect_button.configure(text="Conectar")
                self.update_status("Desconectado do servidor FTP")
                return

            # Verifica se todos os campos estão preenchidos
            if not all([self.host_var.get(), self.port_var.get(), self.user_var.get(), self.pass_var.get()]):
                messagebox.showerror("Erro", "Por favor, preencha todos os campos de configuração")
                return

            # Cria nova instância do uploader com os dados de conexão
            self.ftp_uploader = FTPImageUploader(
                host=self.host_var.get(),
                port=self.port_var.get(),
                username=self.user_var.get(),
                password=self.pass_var.get()
            )
            
            # Tenta conectar
            if self.ftp_uploader.connect():
                self.is_connected = True
                self.connect_button.configure(text="Desconectar")
                self.update_status("Conectado ao servidor FTP")
                messagebox.showinfo("Sucesso", "Conectado ao servidor FTP com sucesso!")
            else:
                self.is_connected = False
                messagebox.showerror("Erro", "Não foi possível conectar ao servidor FTP")
        except Exception as e:
            self.logger.error(f"Erro ao conectar ao servidor FTP: {str(e)}")
            messagebox.showerror("Erro", f"Erro ao conectar: {str(e)}")

    def start_monitoring(self):
        """Inicia o monitoramento da pasta"""
        try:
            # Para monitoramento existente
            self.stop_monitoring()
            
            monitored_folder = self.monitored_folder_var.get()
            if not monitored_folder or not os.path.exists(monitored_folder):
                messagebox.showerror("Erro", "Pasta monitorada não encontrada")
                return False

            # Cria novo observer
            if Observer is None:
                messagebox.showerror("Erro", "Dependência watchdog não instalada.")
                return False
            self.event_handler = FileHandler(self.ftp_uploader, self)
            self.observer = Observer()
            self.observer.schedule(self.event_handler, monitored_folder, recursive=False)
            
            try:
                self.observer.start()
                self.update_status(f"Monitorando pasta: {monitored_folder}")
                return True
            except Exception as e:
                self.logger.error(f"Erro ao iniciar observer: {str(e)}")
                self.observer = None
                return False

        except Exception as e:
            self.logger.error(f"Erro ao iniciar monitoramento: {str(e)}")
            self.update_status("Erro ao iniciar monitoramento")
            return False

    def stop_monitoring(self):
        """Para o monitoramento da pasta"""
        try:
            if self.observer:
                self.observer.stop()
                self.observer.join()
                self.observer = None
                self.logger.info("Monitoramento parado")
                self.update_status("Monitoramento parado")
        except Exception as e:
            self.logger.error(f"Erro ao parar monitoramento: {str(e)}")
            self.observer = None

    def update_file_list(self):
        """Atualiza a lista de arquivos"""
        try:
            # Guardar seleção atual
            selected_files = []
            for item in self.tree.selection():
                values = self.tree.item(item)["values"]
                if values:
                    selected_files.append(values[0])  # Nome do arquivo

            # Limpar tabela
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Obter pasta monitorada
            monitored_folder = self.monitored_folder_var.get()
            if not monitored_folder or not os.path.exists(monitored_folder):
                return

            # Obter termo de pesquisa
            search_term = self.search_var.get().lower()

            # Listar arquivos
            for filename in os.listdir(monitored_folder):
                # Filtrar por termo de pesquisa
                if search_term and search_term not in filename.lower():
                    continue
                    
                filepath = os.path.join(monitored_folder, filename)
                if not os.path.isfile(filepath):
                    continue

                # Obter informações do arquivo
                file_type = os.path.splitext(filename)[1]
                file_size = os.path.getsize(filepath)
                
                # Usar o horário de modificação do arquivo
                file_mtime = os.path.getmtime(filepath)
                file_date = datetime.fromtimestamp(file_mtime)
                
                # Formatar tamanho
                if file_size < 1024:
                    size_str = f"{file_size} B"
                elif file_size < 1024*1024:
                    size_str = f"{file_size/1024:.1f} KB"
                else:
                    size_str = f"{file_size/(1024*1024):.1f} MB"
                
                # Obter status e data de envio do arquivo
                status = self.file_log.get_file_status(filename)
                if not status:
                    status = "Pendente"
                    # Atualiza o timestamp inicial no log
                    self.file_log.update_file_mtime(filename, file_mtime)
                
                # Obter data de envio
                upload_date = self.file_log.get_upload_date(filename)
                
                # Inserir na tabela
                item = self.tree.insert("", tk.END, values=(
                    filename,
                    file_type,
                    size_str,
                    status,
                    file_date.strftime("%d/%m/%Y %H:%M:%S"),
                    upload_date
                ))
                
                # Restaurar seleção se arquivo estava selecionado
                if filename in selected_files:
                    self.tree.selection_add(item)

        except Exception as e:
            self.logger.error(f"Erro ao atualizar lista de arquivos: {str(e)}")

    def upload_files(self):
        """Faz upload dos arquivos selecionados"""
        try:
            if not self.is_connected:
                if not self.connect_ftp():
                    return

            selected_items = self.tree.selection()
            if not selected_items:
                messagebox.showwarning("Aviso", "Selecione pelo menos um arquivo para upload")
                return

            # Processa cada arquivo selecionado
            for item in selected_items:
                values = self.tree.item(item)["values"]
                if not values:
                    continue

                filename = values[0]
                filepath = os.path.join(self.monitored_folder_var.get(), filename)
                
                # Verifica se o arquivo existe
                if not os.path.exists(filepath):
                    self.logger.error(f"Arquivo não encontrado: {filename}")
                    messagebox.showerror("Erro", f"Arquivo não encontrado: {filename}")
                    continue
                    
                # Verifica status atual
                status = self.file_log.get_file_status(filename)
                if status == "Enviando...":
                    self.logger.warning(f"Arquivo já está sendo enviado: {filename}")
                    messagebox.showwarning("Aviso", f"Arquivo já está sendo enviado: {filename}")
                    continue

                # Adiciona à fila de upload
                self._update_status_quietly(filename, "Aguardando...")
                self.upload_queue.put((filepath, filename))
                self.logger.info(f"Arquivo adicionado à fila: {filename}")

            # Atualiza interface
            self.update_file_list()
            self.update_status("Arquivos adicionados à fila de upload")

        except Exception as e:
            self.logger.error(f"Erro ao iniciar upload: {str(e)}")
            messagebox.showerror("Erro", f"Erro ao iniciar upload: {str(e)}")

    def _process_upload_queue(self):
        """Thread dedicada para processar a fila de upload"""
        while True:
            try:
                # Espera por um novo item na fila
                filepath, filename = self.upload_queue.get()
                
                try:
                    # Atualiza status inicial e mostra barra de progresso
                    self.after(0, lambda: self._update_status_quietly(filename, "Enviando..."))
                    self.after(0, lambda: self.progress_frame.pack(fill=tk.X, padx=5, pady=5))
                    self.after(0, lambda: self.progress_label.configure(text=f"Enviando arquivo: {filename}"))
                    self.after(0, lambda: self.progress_bar.set(0))
                    
                    def progress_callback(current, total):
                        progress = current / total if total > 0 else 0
                        self.after(0, lambda: self.progress_bar.set(progress))
                        self.after(0, lambda: self.progress_label.configure(
                            text=f"Enviando arquivo: {filename} ({current/1024/1024:.1f}MB / {total/1024/1024:.1f}MB)"
                        ))
                    
                    # Faz o upload com callback de progresso
                    if self.ftp_uploader and hasattr(self.ftp_uploader, 'upload_file'):
                        if self.ftp_uploader.upload_file(filepath, progress_callback=progress_callback, force=True):
                            # Sucesso - atualiza status e timestamp
                            current_mtime = os.path.getmtime(filepath)
                            self.after(0, lambda: self._update_status_quietly(filename, "Enviado"))
                            self.after(0, lambda: self.file_log.update_file_mtime(filename, current_mtime))
                        else:
                            # Falha
                            self.after(0, lambda: self._update_status_quietly(filename, "Erro"))
                    else:
                        self.after(0, lambda: self._update_status_quietly(filename, "Erro: FTP Uploader não disponível"))
                    
                    # Oculta barra de progresso após concluir
                    self.after(1000, lambda: self.progress_frame.pack_forget())
                        
                except Exception as e:
                    self.logger.error(f"Erro no upload do arquivo {filename}: {str(e)}")
                    self.after(0, lambda: self._update_status_quietly(filename, f"Erro: {str(e)}"))
                    self.after(0, lambda: self.progress_frame.pack_forget())
                
                finally:
                    # Marca o item como processado e atualiza a lista
                    self.upload_queue.task_done()
                    self.after(0, self.update_file_list)
                    
            except Exception as e:
                self.logger.error(f"Erro no processador de upload: {str(e)}")
                time.sleep(1)  # Evita consumo excessivo de CPU em caso de erro
                
    def _update_status_quietly(self, filename, status):
        """Atualiza o status sem bloquear a interface"""
        try:
            # Atualiza o log
            self.file_log.update_file_status(filename, status)
            
            # Atualiza a interface sem travar
            self.status_label.configure(text=f"Status: Arquivo {filename}: {status}")
            
            # Agenda uma atualização da lista para o próximo ciclo de eventos
            self.after(100, self.update_file_list)
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar status: {str(e)}")

    def update_status(self, message):
        """Atualiza a mensagem de status na interface"""
        self.status_label.configure(text=f"Status: {message}")

    def start_auto_update(self):
        """Inicia a atualização automática da lista de arquivos"""
        if not self.update_timer:
            self.update_file_list()  # Atualização inicial
            # Agendar próxima atualização
            self.update_timer = self.after(2000, self.start_auto_update)  # Atualiza a cada 2 segundos
        
    def stop_auto_update(self):
        """Para a atualização automática"""
        if self.update_timer:
            self.after_cancel(self.update_timer)
            self.update_timer = None

    def on_closing(self):
        """Minimiza para a bandeja ao fechar a janela principal"""
        self.withdraw()
        self.is_visible = False

    def run(self):
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.mainloop()

    def browse_folder(self):
        """Abre diálogo para selecionar pasta"""
        folder = filedialog.askdirectory()
        if folder:
            self.monitored_folder_var.set(folder)

    def format_size(self, size):
        """Formata o tamanho do arquivo"""
        if size < 1024:
            return f"{size} B"
        elif size < 1024*1024:
            return f"{size/1024:.1f} KB"
        else:
            return f"{size/(1024*1024):.1f} MB"

    def sort_treeview(self, column, reverse):
        """Ordena a tabela por uma coluna específica"""
        l = [(self.tree.set(k, column), k) for k in self.tree.get_children('')]
        # Corrigir para garantir que o valor é string para comparação
        l.sort(key=lambda t: str(t[0]), reverse=reverse)

        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)

        self.tree.heading(column, command=lambda: self.sort_treeview(column, not reverse))

    def check_new_files(self):
        """Verifica novos arquivos e arquivos modificados para envio automático"""
        try:
            if self.is_connected and self.ftp_uploader and self.auto_upload_enabled:
                monitored_folder = self.monitored_folder_var.get()
                if monitored_folder and os.path.exists(monitored_folder):
                    # Lista todos os arquivos na pasta
                    for filename in os.listdir(monitored_folder):
                        filepath = os.path.join(monitored_folder, filename)
                        if not os.path.isfile(filepath):
                            continue

                        # Obtém o timestamp de modificação atual do arquivo
                        current_mtime = os.path.getmtime(filepath)
                        
                        # Verifica se o arquivo já foi enviado
                        status = self.file_log.get_file_status(filename)
                        last_mtime = self.file_log.get_file_mtime(filename)
                        
                        # Arquivo precisa ser enviado se:
                        # 1. Nunca foi enviado (status None ou "Pendente")
                        # 2. Teve erro no envio anterior
                        # 3. Foi modificado desde o último envio
                        # 4. Não está atualmente sendo enviado
                        needs_upload = (
                            not status or 
                            status == "Pendente" or 
                            status == "Erro" or
                            (status == "Enviado" and last_mtime and current_mtime > last_mtime)
                        )
                        
                        if needs_upload and status != "Enviando...":
                            try:
                                self.logger.info(f"Iniciando upload automático do arquivo: {filename} (mtime: {datetime.fromtimestamp(current_mtime)})")
                                self.file_log.update_file_status(filename, "Aguardando...")
                                self.file_log.update_file_mtime(filename, current_mtime)
                                
                                # Adiciona à fila de upload
                                self.upload_queue.put((filepath, filename))
                                self.update_file_list()
                                
                            except Exception as e:
                                self.logger.error(f"Erro ao preparar upload do arquivo {filename}: {str(e)}")
                                self.file_log.update_file_status(filename, "Erro")
                                self.update_status(f"Erro ao enviar arquivo: {filename}")

        except Exception as e:
            self.logger.error(f"Erro ao verificar novos arquivos: {str(e)}")
        finally:
            # Agenda próxima verificação
            self.after(5000, self.check_new_files)  # Verifica a cada 5 segundos

    def setup_system_tray(self):
        """Configura o ícone na área de notificação"""
        try:
            # Carrega o ícone do sistema
            icon_path = os.path.join(os.path.dirname(__file__), "public", "ftp.ico")
            self.logger.info(f"Tentando carregar ícone de: {icon_path}")
            
            image = None
            if os.path.exists(icon_path) and Image:
                try:
                    image = Image.open(icon_path)
                    # Redimensiona para um tamanho padrão de ícone do sistema
                    image = image.resize((32, 32))
                except Exception as e:
                    self.logger.error(f"Erro ao abrir o arquivo de ícone: {str(e)}")
                    image = create_icon()
            else:
                self.logger.warning(f"Arquivo de ícone não encontrado em {icon_path}")
                image = create_icon()
            
            # Define o menu do system tray com mais opções
            if pystray is None:
                self.logger.warning("pystray não está instalado. System tray desabilitado.")
                return
            menu = (
                pystray.MenuItem('Mostrar/Ocultar', self.toggle_window),
                pystray.MenuItem('Status', lambda: self.show_status_notification()),
                pystray.MenuItem('Sair', self.quit_app)
            )
            
            # Remove ícone anterior se existir
            if self.icon is not None:
                self.icon.stop()
            
            self.icon = pystray.Icon("TARGETWEB FTP", image, "TARGETWEB FTP", menu)
            
            # Configura o evento de clique duplo
            # self.icon.on_click = lambda icon, button: self.toggle_window() if button == 1 else None
            
            # Inicia o ícone em uma thread separada
            threading.Thread(target=self._run_system_tray, daemon=True).start()
            
            self.logger.info("System tray configurado com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro ao configurar system tray: {str(e)}")
            
    def _run_system_tray(self):
        """Executa o system tray em uma thread separada"""
        try:
            if self.icon:
                self.icon.run()
        except Exception as e:
            self.logger.error(f"Erro ao executar system tray: {str(e)}")
            
    def show_status_notification(self):
        """Mostra uma notificação com o status atual do aplicativo"""
        status = "Conectado" if self.is_connected else "Desconectado"
        if self.icon:
            self.icon.notify(f"Status: {status}", "TARGETWEB FTP")
    
    def toggle_window(self, icon=None):
        """Alterna a visibilidade da janela"""
        try:
            if self.is_visible:
                self.withdraw()
                self.is_visible = False
            else:
                self.deiconify()
                self.lift()
                self.focus_force()
                self.is_visible = True
        except Exception as e:
            self.logger.error(f"Erro ao alternar visibilidade: {str(e)}")
    
    def quit_app(self, icon=None):
        """Fecha o aplicativo completamente"""
        try:
            if self.icon:
                self.icon.stop()
            if hasattr(self, 'observer') and self.observer:
                self.observer.stop()
                self.observer.join()
            self.destroy()
        except Exception as e:
            self.logger.error(f"Erro ao fechar aplicativo: {str(e)}")
            self.destroy()
    
    def process_events(self):
        """Processa eventos da fila"""
        try:
            while True:
                try:
                    event = self.event_queue.get_nowait()
                    if event == "quit":
                        if self.icon:
                            self.icon.stop()
                        if self.observer:
                            self.observer.stop()
                            self.observer.join()
                        self.quit()
                        return
                except queue.Empty:
                    break
                
            if self.is_running:
                self.after(100, self.process_events)
        except Exception as e:
            self.logger.error(f"Erro ao processar eventos: {str(e)}")
    
    def __del__(self):
        """Destrutor da classe"""
        self.quit_app()

    def queue_upload(self, filepath, is_update=False):
        """Adiciona um arquivo à fila de upload"""
        try:
            filename = os.path.basename(filepath)
            
            # Verifica se já existe uma thread de upload para este arquivo
            if filename in self.upload_threads:
                self.logger.warning(f"Upload do arquivo {filename} já está em andamento")
                return
                
            # Inicia uma nova thread para o upload
            upload_thread = threading.Thread(
                target=self._upload_file_thread,
                args=(filepath, filename, is_update),
                daemon=True
            )
            self.upload_threads[filename] = upload_thread
            upload_thread.start()
            
        except Exception as e:
            self.logger.error(f"Erro ao adicionar arquivo à fila de upload: {str(e)}")
            messagebox.showerror("Erro", f"Erro ao iniciar upload: {str(e)}")

    def _upload_file_thread(self, filepath, filename, is_update=False):
        """Função executada em thread separada para fazer o upload"""
        try:
            # Mostra frame de progresso
            # self.after(0, lambda: self._show_progress(filename))
            def update_progress(progress):
                pass  # Removido _update_progress
            # Atualiza o status no log
            status_text = "Atualizando..." if is_update else "Enviando..."
            self.file_log.update_file_status(filename, status_text)
            # Faz o upload com callback de progresso
            if self.ftp_uploader:
                self.ftp_uploader.upload_file(filepath, progress_callback=update_progress)
            # Atualiza o status no log
            status_text = "Atualizado" if is_update else "Enviado"
            self.file_log.update_file_status(filename, status_text, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            # Atualiza a interface
            self.after(0, lambda: self._upload_complete(filename, is_update))
        except Exception as e:
            error_msg = f"Erro no upload do arquivo {filename}: {str(e)}"
            self.logger.error(error_msg)
            # self.after(0, lambda: self._upload_error(filename, str(e)))
        finally:
            self.upload_threads.pop(filename, None)

    def _upload_complete(self, filename, is_update=False):
        """Chamado quando o upload é concluído com sucesso"""
        self.progress_frame.pack_forget()
        self.update_file_list()
        action = "atualização" if is_update else "upload"
        message = f"{action.capitalize()} do arquivo {filename} concluído com sucesso"
        self.update_status(message)
        messagebox.showinfo("Sucesso", message)

    # Métodos de licença removidos - sistema liberado

    def toggle_startup(self):
        try:
            exe_path = os.path.abspath(sys.argv[0])
            appdata = os.getenv('APPDATA') or os.path.expanduser('~')
            startup = os.path.join(appdata, r'Microsoft\Windows\Start Menu\Programs\Startup')
            exe_name = os.path.splitext(os.path.basename(exe_path))[0]
            shortcut = os.path.join(startup, f"{exe_name}.lnk")
            if self.startup_checkbox_var.get():
                with winshell.shortcut(shortcut) as link:
                    link.path = exe_path
                    link.arguments = "--tray"
                    link.description = f"Iniciar {exe_name} com o Windows"
                self.logger.info(f"Atalho de inicialização criado: {shortcut}")
            else:
                if os.path.exists(shortcut):
                    os.remove(shortcut)
                    self.logger.info(f"Atalho de inicialização removido: {shortcut}")
        except Exception as e:
            self.logger.error(f"Erro ao manipular atalho de inicialização: {str(e)}")

    def load_startup_checkbox(self):
        try:
            exe_path = os.path.abspath(sys.argv[0])
            appdata = os.getenv('APPDATA') or os.path.expanduser('~')
            startup = os.path.join(appdata, r'Microsoft\Windows\Start Menu\Programs\Startup')
            exe_name = os.path.splitext(os.path.basename(exe_path))[0]
            shortcut = os.path.join(startup, f"{exe_name}.lnk")
            self.startup_checkbox_var.set(os.path.exists(shortcut))
        except Exception as e:
            self.logger.error(f"Erro ao verificar atalho de inicialização: {str(e)}")

if __name__ == "__main__":
    start_minimized = "--tray" in sys.argv
    app = FTPManagerApp()
    if start_minimized:
        app.withdraw()  # Oculta a janela principal
    app.mainloop()
