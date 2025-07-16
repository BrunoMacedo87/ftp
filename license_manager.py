import os
import json
import uuid
import hashlib
import datetime
from pathlib import Path
import winreg

class LicenseManager:
    def __init__(self):
        self.license_file = Path.home() / ".ftpmanager" / "license.json"
        self.trial_days = 15
        self.machine_id = self._get_machine_id()
        self.secret_key = "FTPManager2024#SecretKey"  # Chave para geração de licenças
        
    def _get_machine_id(self):
        """Gera ID único para o computador baseado no hardware"""
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                              "SOFTWARE\\Microsoft\\Cryptography", 0,
                              winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
                return winreg.QueryValueEx(key, "MachineGuid")[0]
        except:
            return str(uuid.getnode())
    
    def _generate_license_key(self, machine_id):
        """Gera uma chave de licença para um machine_id específico"""
        key_base = f"{machine_id}{self.secret_key}"
        return hashlib.sha256(key_base.encode()).hexdigest()[:32]
    
    def check_license(self):
        """Verifica o status da licença - SISTEMA LIBERADO"""
        return True, "Sistema liberado - sem restrições"
    
    def start_trial(self):
        """Inicia o período de trial"""
        try:
            self.license_file.parent.mkdir(exist_ok=True)
            license_data = {
                "type": "trial",
                "start_date": datetime.datetime.now().isoformat(),
                "machine_id": self.machine_id
            }
            with open(self.license_file, "w") as f:
                json.dump(license_data, f)
            return True, f"Trial iniciado: {self.trial_days} dias restantes"
        except Exception as e:
            return False, f"Erro ao iniciar trial: {str(e)}"
    
    def activate_license(self, license_key):
        """Ativa uma licença com a chave fornecida - SISTEMA LIBERADO"""
        return True  # Sempre retorna True - sistema liberado
    
    def get_machine_info(self):
        """Retorna informações da máquina para geração de licença"""
        return {
            "machine_id": self.machine_id,
            "license_key": self._generate_license_key(self.machine_id)
        }
