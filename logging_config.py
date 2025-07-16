import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging():
    # Certifica que o diretório de logs existe
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Configura o logger principal
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Configura o formato do log
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Handler para arquivo com rotação
    # Mantém até 5 arquivos de backup, cada um com máximo de 5MB
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'ftp_manager.log'),
        maxBytes=5*1024*1024,  # 5MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
