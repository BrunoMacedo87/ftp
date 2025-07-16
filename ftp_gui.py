import sys
import os
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
                            QLabel, QMessageBox, QLineEdit, QFormLayout, QFileDialog,
                            QProgressBar, QGroupBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon
from ftp_uploader import FTPImageUploader, start_monitoring
import json

class MonitorThread(QThread):
    file_uploaded = pyqtSignal(str)
    upload_progress = pyqtSignal(str, int, int)
    error_occurred = pyqtSignal(str)

    def __init__(self, host, user, password, watch_folder, completed_folder):
        super().__init__()
        self.host = host
        self.user = user
        self.password = password
        self.watch_folder = watch_folder
        self.completed_folder = completed_folder
        self.running = True

    def run(self):
        try:
            uploader, observer = start_monitoring(
                self.host,
                self.user,
                self.password,
                self.watch_folder,
                self.completed_folder
            )
            
            if not uploader:
                self.error_occurred.emit("Falha ao conectar ao servidor FTP")
                return

            while self.running:
                self.sleep(1)

            observer.stop()
            uploader.disconnect()
            observer.join()

        except Exception as e:
            self.error_occurred.emit(f"Erro: {str(e)}")

    def stop(self):
        self.running = False

class FTPManagerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.monitor_thread = None
        self.config_file = "ftp_config.json"
        self.setWindowTitle("Gerenciador de Upload FTP")
        self.setGeometry(100, 100, 900, 600)

        # Criar pastas padrão
        self.watch_folder = os.path.join(os.path.dirname(__file__), "para_upload")
        self.completed_folder = os.path.join(os.path.dirname(__file__), "realizados")
        os.makedirs(self.watch_folder, exist_ok=True)
        os.makedirs(self.completed_folder, exist_ok=True)

        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Grupo de Configurações FTP
        config_group = QGroupBox("Configurações do Servidor FTP")
        config_layout = QFormLayout()

        self.host_input = QLineEdit()
        self.user_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        config_layout.addRow("Host:", self.host_input)
        config_layout.addRow("Usuário:", self.user_input)
        config_layout.addRow("Senha:", self.password_input)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Grupo de Pastas
        folders_group = QGroupBox("Configuração de Pastas")
        folders_layout = QFormLayout()

        self.watch_folder_label = QLabel(self.watch_folder)
        self.completed_folder_label = QLabel(self.completed_folder)

        folder_watch_layout = QHBoxLayout()
        folder_watch_layout.addWidget(self.watch_folder_label)
        watch_btn = QPushButton("Escolher")
        watch_btn.clicked.connect(lambda: self.choose_folder("watch"))
        folder_watch_layout.addWidget(watch_btn)

        folder_completed_layout = QHBoxLayout()
        folder_completed_layout.addWidget(self.completed_folder_label)
        completed_btn = QPushButton("Escolher")
        completed_btn.clicked.connect(lambda: self.choose_folder("completed"))
        folder_completed_layout.addWidget(completed_btn)

        folders_layout.addRow("Pasta Monitorada:", folder_watch_layout)
        folders_layout.addRow("Pasta Realizados:", folder_completed_layout)

        folders_group.setLayout(folders_layout)
        layout.addWidget(folders_group)

        # Status e Controles
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("Status: Desconectado")
        status_layout.addWidget(self.status_label)
        
        self.start_btn = QPushButton("Iniciar Monitoramento")
        self.start_btn.clicked.connect(self.toggle_monitoring)
        status_layout.addWidget(self.start_btn)

        layout.addLayout(status_layout)

        # Barra de Progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Tabela de arquivos
        self.files_table = QTableWidget()
        self.files_table.setColumnCount(4)
        self.files_table.setHorizontalHeaderLabels(["Nome do Arquivo", "Data", "Hora", "Status"])
        self.files_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.files_table)

        # Botão para abrir pasta
        open_folder_layout = QHBoxLayout()
        
        watch_folder_btn = QPushButton("Abrir Pasta de Upload")
        watch_folder_btn.clicked.connect(lambda: self.open_folder(self.watch_folder))
        open_folder_layout.addWidget(watch_folder_btn)
        
        completed_folder_btn = QPushButton("Abrir Pasta Realizados")
        completed_folder_btn.clicked.connect(lambda: self.open_folder(self.completed_folder))
        open_folder_layout.addWidget(completed_folder_btn)
        
        layout.addLayout(open_folder_layout)

    def choose_folder(self, folder_type):
        folder = QFileDialog.getExistingDirectory(self, "Escolher Pasta")
        if folder:
            if folder_type == "watch":
                self.watch_folder = folder
                self.watch_folder_label.setText(folder)
            else:
                self.completed_folder = folder
                self.completed_folder_label.setText(folder)

    def open_folder(self, path):
        os.startfile(path)

    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.host_input.setText(config.get('host', ''))
                    self.user_input.setText(config.get('user', ''))
                    self.password_input.setText(config.get('password', ''))
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Erro ao carregar configurações: {str(e)}")

    def save_config(self):
        try:
            config = {
                'host': self.host_input.text(),
                'user': self.user_input.text(),
                'password': self.password_input.text()
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Erro ao salvar configurações: {str(e)}")

    def toggle_monitoring(self):
        if self.monitor_thread is None or not self.monitor_thread.isRunning():
            # Validar campos
            if not all([self.host_input.text(), self.user_input.text(), self.password_input.text()]):
                QMessageBox.warning(self, "Erro", "Preencha todos os campos de configuração FTP!")
                return

            # Salvar configurações
            self.save_config()

            # Iniciar monitoramento
            self.monitor_thread = MonitorThread(
                self.host_input.text(),
                self.user_input.text(),
                self.password_input.text(),
                self.watch_folder,
                self.completed_folder
            )
            
            self.monitor_thread.file_uploaded.connect(self.on_file_uploaded)
            self.monitor_thread.upload_progress.connect(self.on_upload_progress)
            self.monitor_thread.error_occurred.connect(self.on_error)
            
            self.monitor_thread.start()
            
            self.status_label.setText("Status: Monitorando")
            self.status_label.setStyleSheet("color: green")
            self.start_btn.setText("Parar Monitoramento")
            
            # Desabilitar campos de configuração
            self.host_input.setEnabled(False)
            self.user_input.setEnabled(False)
            self.password_input.setEnabled(False)
        else:
            # Parar monitoramento
            self.monitor_thread.stop()
            self.monitor_thread = None
            
            self.status_label.setText("Status: Desconectado")
            self.status_label.setStyleSheet("color: black")
            self.start_btn.setText("Iniciar Monitoramento")
            
            # Habilitar campos de configuração
            self.host_input.setEnabled(True)
            self.user_input.setEnabled(True)
            self.password_input.setEnabled(True)

    def on_file_uploaded(self, filename):
        row = self.files_table.rowCount()
        self.files_table.insertRow(row)
        
        now = datetime.now()
        
        self.files_table.setItem(row, 0, QTableWidgetItem(filename))
        self.files_table.setItem(row, 1, QTableWidgetItem(now.strftime("%d/%m/%Y")))
        self.files_table.setItem(row, 2, QTableWidgetItem(now.strftime("%H:%M:%S")))
        self.files_table.setItem(row, 3, QTableWidgetItem("Concluído"))
        
        self.progress_bar.setVisible(False)

    def on_upload_progress(self, filename, current, total):
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

    def on_error(self, error_msg):
        self.status_label.setText("Status: Erro")
        self.status_label.setStyleSheet("color: red")
        QMessageBox.critical(self, "Erro", error_msg)
        self.toggle_monitoring()

    def closeEvent(self, event):
        if self.monitor_thread and self.monitor_thread.isRunning():
            self.monitor_thread.stop()
            self.monitor_thread.wait()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = FTPManagerWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
