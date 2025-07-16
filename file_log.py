import json
import os
import logging
from datetime import datetime

class FileLog:
    def __init__(self):
        # Configurar diretório de dados do aplicativo
        self.app_data_dir = os.path.join(os.getenv('APPDATA'), 'FTP Manager')
        if not os.path.exists(self.app_data_dir):
            os.makedirs(self.app_data_dir)
        
        self.log_file = os.path.join(self.app_data_dir, "file_log.json")
        self.logger = logging.getLogger(__name__)
        self.load_log()

    def load_log(self):
        """Carrega o log de arquivos do disco"""
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    self.log_data = json.load(f)
            else:
                self.log_data = {}
        except Exception as e:
            self.logger.error(f"Erro ao carregar log de arquivos: {str(e)}")
            self.log_data = {}

    def save_log(self):
        """Salva o log de arquivos no disco"""
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.log_data, f, indent=4)
        except Exception as e:
            self.logger.error(f"Erro ao salvar log de arquivos: {str(e)}")

    def update_file_status(self, filename, status, date=None):
        """Atualiza o status de um arquivo no log"""
        try:
            if filename not in self.log_data:
                self.log_data[filename] = {}
            
            # Se a data não for fornecida, usa a data atual
            if date is None:
                date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            
            self.log_data[filename]["status"] = status
            self.log_data[filename]["status_date"] = date
            
            # Se o status for "Enviado", atualiza a data de envio
            if status == "Enviado":
                self.log_data[filename]["upload_date"] = date
            
            self.save_log()
        except Exception as e:
            self.logger.error(f"Erro ao atualizar status do arquivo {filename}: {str(e)}")

    def update_file_mtime(self, filename, mtime):
        """Atualiza o timestamp de modificação de um arquivo no log"""
        try:
            if filename not in self.log_data:
                self.log_data[filename] = {}
            
            self.log_data[filename]["mtime"] = mtime
            # Converte o timestamp para string formatada
            self.log_data[filename]["date"] = datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M:%S")
            self.save_log()
        except Exception as e:
            self.logger.error(f"Erro ao atualizar mtime do arquivo {filename}: {str(e)}")

    def get_file_status(self, filename):
        """Retorna o status de um arquivo"""
        try:
            return self.log_data.get(filename, {}).get("status", None)
        except Exception as e:
            self.logger.error(f"Erro ao obter status do arquivo {filename}: {str(e)}")
            return None

    def get_file_date(self, filename):
        """Retorna a data de modificação do arquivo"""
        try:
            return self.log_data.get(filename, {}).get("date", None)
        except Exception as e:
            self.logger.error(f"Erro ao obter data do arquivo {filename}: {str(e)}")
            return None

    def get_file_mtime(self, filename):
        """Retorna o timestamp de modificação de um arquivo"""
        try:
            return self.log_data.get(filename, {}).get("mtime", None)
        except Exception as e:
            self.logger.error(f"Erro ao obter mtime do arquivo {filename}: {str(e)}")
            return None

    def get_upload_date(self, filename):
        """Retorna a data de envio do arquivo"""
        try:
            return self.log_data.get(filename, {}).get("upload_date", "")
        except Exception as e:
            self.logger.error(f"Erro ao obter data de envio do arquivo {filename}: {str(e)}")
            return ""

    def update_upload_date(self, filename, date):
        """Atualiza a data de envio do arquivo"""
        try:
            if filename not in self.log_data:
                self.log_data[filename] = {}
            self.log_data[filename]["upload_date"] = date
            self.save_log()
        except Exception as e:
            self.logger.error(f"Erro ao atualizar data de envio do arquivo {filename}: {str(e)}")

    def clear_log(self):
        """Limpa todo o log de arquivos"""
        self.log_data = {}
        self.save_log()
