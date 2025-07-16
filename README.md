# Sistema de Upload FTP

Sistema de upload automático de arquivos via FTP com interface gráfica, desenvolvido em Python. **Agora totalmente livre para uso, sem necessidade de licença ou período de teste!**

## Funcionalidades

- Interface gráfica amigável usando CustomTkinter
- Configuração de servidor FTP (host, porta, usuário, senha)
- Upload manual e automático de arquivos
- Monitoramento de pasta para upload automático
- Verificação de integridade dos arquivos enviados
- Log detalhado de operações
- Reconexão automática em caso de falha
- Status de envio para cada arquivo

## Requisitos

- Python 3.8 ou superior
- Windows (recomendado)
- Dependências listadas em `requirements.txt`

## Instalação

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/BrunoMacedo87/ftp.git
   cd ftp
   ```

2. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```
   > Se necessário, instale o Python pelo site oficial: https://www.python.org/downloads/
   >
   > Certifique-se de marcar a opção "Add Python to PATH" durante a instalação.

## Como usar

1. **Execute o programa:**
   ```bash
   python ftp_gui_tk.py
   ```

2. **Configure o servidor FTP:**
   - Host
   - Porta (padrão: 21)
   - Usuário
   - Senha

3. **Selecione a pasta para monitoramento**

4. **Envie arquivos:**
   - Use o botão "Enviar Arquivos" para upload manual
   - Ou deixe o sistema monitorar a pasta automaticamente para uploads automáticos

5. **Acompanhe o status:**
   - O sistema mostra logs detalhados e status de cada envio

## Como gerar o executável (.exe) com PyInstaller

Para gerar o executável Windows com ícone, nome personalizado e todas as dependências necessárias, use o comando abaixo na raiz do projeto:

```sh
pyinstaller --noconfirm --onefile --windowed --name "TARGETWEB_FTP" ftp_gui_tk.py --icon=ftp.ico --hidden-import=win32con --hidden-import=win32com --hidden-import=win32api --hidden-import=pywintypes
```

- O executável será gerado na pasta `dist/` com o nome `TARGETWEB_FTP.exe`.
- O ícone do executável será o `ftp.ico`.
- Os parâmetros `--hidden-import` garantem que todas as dependências do Windows sejam incluídas no build.

Se for usar o Inno Setup para criar o instalador, utilize esse executável gerado.

## Principais arquivos do projeto

- `