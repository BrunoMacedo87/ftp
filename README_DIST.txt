FTP Manager - Instruções de Uso
=============================

Este é um programa para gerenciar uploads de arquivos via FTP com monitoramento automático de pasta.

Instalação
----------
1. Extraia todos os arquivos deste pacote em uma pasta de sua escolha
2. Execute o arquivo "FTP Manager.exe"

Configuração Inicial
------------------
1. Ao abrir o programa pela primeira vez, você precisará configurar:
   - Host: endereço do servidor FTP
   - Port: porta do servidor (geralmente 21)
   - Username: seu nome de usuário
   - Password: sua senha
   - Pasta: pasta local que será monitorada

2. Clique em "Salvar Configuração" para salvar suas configurações
3. Clique em "Conectar ao Servidor" para estabelecer a conexão FTP

Uso do Programa
--------------
1. Monitoramento Automático:
   - O programa monitora automaticamente a pasta selecionada
   - Novos arquivos são enviados automaticamente para o servidor FTP

2. Upload Manual:
   - Clique em "Enviar Arquivos" para selecionar arquivos manualmente
   - Os arquivos selecionados serão enviados imediatamente

3. Pesquisa de Arquivos:
   - Use o campo de pesquisa acima da tabela para filtrar arquivos por nome
   - A pesquisa é atualizada em tempo real conforme você digita
   - Clique no X para limpar a pesquisa

4. Sistema Tray:
   - O programa pode ser minimizado para a bandeja do sistema
   - Clique com o botão direito no ícone para ver as opções
   - Você pode mostrar/ocultar a janela ou fechar o programa

Arquivos de Configuração
----------------------
- ftp_config.json: armazena as configurações do servidor FTP
- file_log.json: mantém o registro dos arquivos enviados

Suporte
-------
Em caso de problemas:
1. Verifique se suas configurações FTP estão corretas
2. Certifique-se de que a pasta monitorada existe e está acessível
3. Verifique sua conexão com a internet
4. Consulte os logs em ftp_manager.log para mais detalhes
