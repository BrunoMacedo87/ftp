import os
import ftplib
import logging
from datetime import datetime
import shutil
# Ajuste: Dependências opcionais
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    Observer = None
    FileSystemEventHandler = type("FileSystemEventHandler", (), {})
# tqdm é opcional, usado apenas se necessário
try:
    from tqdm import tqdm
except ImportError:
    tqdm = None
import time
import socket
from file_handler import FileHandler

class FTPImageUploader:
    def __init__(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.ftp = None
        self.logger = logging.getLogger(__name__)
        self.is_connected = False

    def connect(self):
        """Conecta ao servidor FTP"""
        try:
            # Se já estiver conectado, desconecta primeiro
            self.disconnect()
            
            # Cria nova conexão
            self.ftp = ftplib.FTP()
            self.ftp.connect(self.host, int(self.port), timeout=30)
            self.ftp.login(self.username, self.password)
            self.ftp.encoding = 'utf-8'
            
            # Testa a conexão
            self.ftp.voidcmd("NOOP")
            
            self.is_connected = True
            self.logger.info(f"Conectado ao servidor FTP: {self.host}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao conectar ao servidor FTP: {str(e)}")
            self.disconnect()
            return False

    def disconnect(self):
        """Desconecta do servidor FTP"""
        try:
            if self.ftp:
                try:
                    self.ftp.quit()
                except:
                    self.ftp.close()
        except:
            pass
        finally:
            self.ftp = None
            self.is_connected = False

    def reconnect(self):
        """Tenta reconectar ao servidor FTP"""
        try:
            self.disconnect()  # Garante que a conexão anterior está fechada
            
            # Tenta reconectar
            self.ftp = ftplib.FTP()
            self.ftp.connect(self.host, int(self.port), timeout=30)
            self.ftp.login(self.username, self.password)
            self.is_connected = True
            self.logger.info("Reconectado ao servidor FTP com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao reconectar: {str(e)}")
            self.is_connected = False
            return False

    def upload_file(self, filepath, progress_callback=None, force=False):
        """Faz upload de um arquivo para o servidor FTP"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                if not self.ftp or not self.is_connected:
                    if not self.reconnect():
                        self.logger.error("Não foi possível reconectar ao servidor FTP")
                        return False

                filename = os.path.basename(filepath)
                filesize = os.path.getsize(filepath)

                # Abre o arquivo em modo binário
                with open(filepath, 'rb') as file:
                    # Cria um wrapper para monitorar o progresso
                    if progress_callback:
                        bytes_sent = 0
                        last_callback = 0
                        def callback_wrapper(data):
                            nonlocal bytes_sent, last_callback
                            bytes_sent += len(data)
                            # Atualiza a cada 256 KB enviados ou ao finalizar
                            if bytes_sent - last_callback >= 262144 or bytes_sent == filesize:
                                progress_callback(bytes_sent, filesize)
                                last_callback = bytes_sent
                            return data
                        
                        # Inicia o upload com callback
                        if self.ftp is not None:
                            self.ftp.storbinary(f'STOR {filename}', file, blocksize=65536, callback=callback_wrapper)
                        else:
                            self.logger.error("FTP não está conectado.")
                            return False
                    else:
                        # Upload sem callback
                        if self.ftp is not None:
                            self.ftp.storbinary(f'STOR {filename}', file, blocksize=65536)
                        else:
                            self.logger.error("FTP não está conectado.")
                            return False

                # Se for upload forçado, não verifica o status anterior
                if force:
                    return True
                    
                # Verifica se o arquivo existe no servidor e tem o mesmo tamanho
                if self.verify_upload(filename, filesize):
                    self.logger.info(f"Upload do arquivo {filename} verificado com sucesso")
                    return True
                else:
                    self.logger.error(f"Falha na verificação do upload do arquivo {filename}")
                    return False

            except (ConnectionError, TimeoutError, socket.error) as e:
                retry_count += 1
                self.logger.warning(f"Tentativa {retry_count} de {max_retries} falhou: {str(e)}")
                
                if retry_count < max_retries:
                    time.sleep(2)  # Espera 2 segundos antes de tentar novamente
                    self.reconnect()  # Tenta reconectar antes da próxima tentativa
                else:
                    self.logger.error(f"Erro de conexão após {max_retries} tentativas: {str(e)}")
                    return False
                    
            except Exception as e:
                self.logger.error(f"Erro no upload do arquivo {filepath}: {str(e)}")
                return False

        return False

    def verify_upload(self, filename, local_size):
        """Verifica se o arquivo foi enviado corretamente"""
        try:
            # Tenta reconectar se necessário
            if not self.is_connected:
                if not self.reconnect():
                    return False
                    
            # Verifica se o arquivo existe
            try:
                if self.ftp is not None:
                    server_size = self.ftp.size(filename)
                    return server_size == local_size
                else:
                    self.logger.error("FTP não está conectado.")
                    return False
            except ftplib.error_perm:
                self.logger.error(f"Arquivo {filename} não encontrado no servidor")
                return False
                
        except (ConnectionError, TimeoutError, socket.error) as e:
            self.logger.error(f"Erro de conexão ao verificar upload: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Erro ao verificar upload: {str(e)}")
            return False

def start_monitoring(host, port=21, user=None, password=None, watch_folder=None, completed_folder=None, remote_dir='/', callback=None):
    """Inicia o monitoramento da pasta"""
    uploader = FTPImageUploader(host, port, user, password)
    uploader.connect()
    
    if not uploader.is_connected:
        print("Não foi possível conectar ao servidor FTP")
        return False, False
    
    if Observer is None:
        print("Dependência watchdog não instalada. Monitoramento automático desabilitado.")
        return False, False
    event_handler = FileHandler(uploader, app=None)
    observer = Observer()
    observer.schedule(event_handler, watch_folder, recursive=False)
    observer.start()
    return uploader, observer

# Exemplo de uso
if __name__ == "__main__":
    try:
        # Substitua com suas credenciais do servidor FTP
        FTP_HOST = "seu_servidor_ftp.com"
        FTP_USER = "seu_usuario"
        FTP_PASS = "sua_senha"
        
        # Pastas para monitorar e armazenar arquivos completados
        WATCH_FOLDER = os.path.join(os.path.dirname(__file__), "para_upload")
        COMPLETED_FOLDER = os.path.join(os.path.dirname(__file__), "realizados")
        
        print(f"Iniciando monitoramento da pasta: {WATCH_FOLDER}")
        print(f"Arquivos completados serão movidos para: {COMPLETED_FOLDER}")
        
        uploader, observer = start_monitoring(
            FTP_HOST, 
            21, 
            FTP_USER, 
            FTP_PASS, 
            WATCH_FOLDER, 
            COMPLETED_FOLDER
        )
        
        if not uploader or not observer:
            print("Não foi possível conectar ao servidor FTP ou iniciar o monitoramento.")
            exit()
        
        if uploader:
            # Mantém o programa rodando
            try:
                while True:
                    import time
                    time.sleep(1)
            except KeyboardInterrupt:
                observer.stop()
                uploader.disconnect()
                observer.join()
                print("\nMonitoramento finalizado.")
        else:
            print("Erro ao iniciar o monitoramento. Verifique as credenciais FTP.")
    except Exception as e:
        print(f"Erro: {str(e)}")
