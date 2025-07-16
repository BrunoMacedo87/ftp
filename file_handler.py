import logging
import os
from watchdog.events import FileSystemEventHandler

class FileHandler(FileSystemEventHandler):
    def __init__(self, ftp_uploader, app):
        super().__init__()
        self.ftp_uploader = ftp_uploader
        self.app = app
        self.logger = logging.getLogger(__name__)
        self._ignore_patterns = ['.tmp', '.crdownload', '.part']  # Arquivos temporários para ignorar

    def _should_handle_file(self, filepath):
        """Verifica se o arquivo deve ser processado"""
        if not os.path.exists(filepath):
            return False
            
        # Ignora arquivos temporários
        return not any(pattern in filepath.lower() for pattern in self._ignore_patterns)

    def on_created(self, event):
        if event.is_directory:
            return
            
        if self._should_handle_file(event.src_path):
            try:
                self.logger.info(f"Arquivo detectado: {event.src_path}")
                self.app.update_file_list()
            except Exception as e:
                self.logger.error(f"Erro ao processar novo arquivo {event.src_path}: {str(e)}")

    def on_deleted(self, event):
        if not event.is_directory:
            try:
                self.logger.info(f"Arquivo removido: {event.src_path}")
                self.app.update_file_list()
            except Exception as e:
                self.logger.error(f"Erro ao processar remoção do arquivo {event.src_path}: {str(e)}")

    def on_modified(self, event):
        if event.is_directory:
            return
            
        if self._should_handle_file(event.src_path):
            try:
                filename = os.path.basename(event.src_path)
                self.logger.info(f"Arquivo modificado: {event.src_path}")
                
                # Verifica se o arquivo já existe no log
                file_info = self.app.file_log.get_file_info(filename)
                if file_info:
                    # Verifica se o arquivo realmente foi modificado comparando as datas
                    current_mtime = os.path.getmtime(event.src_path)
                    last_modified = float(file_info.get('last_modified', 0))
                    
                    if current_mtime > last_modified:
                        self.logger.info(f"Arquivo {filename} foi modificado. Iniciando reenvio...")
                        # Inicia o reenvio em uma nova thread
                        self.app.queue_upload(event.src_path, is_update=True)
                
                self.app.update_file_list()
                
            except Exception as e:
                self.logger.error(f"Erro ao processar modificação do arquivo {event.src_path}: {str(e)}")

    def on_moved(self, event):
        if event.is_directory:
            return
            
        if self._should_handle_file(event.dest_path):
            try:
                self.logger.info(f"Arquivo movido/renomeado de {event.src_path} para {event.dest_path}")
                self.app.update_file_list()
            except Exception as e:
                self.logger.error(f"Erro ao processar movimentação do arquivo {event.src_path}: {str(e)}")
