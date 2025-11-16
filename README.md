Discord Remote Script Manager
<br />
Este projeto permite executar scripts em máquinas remotas através de um bot do Discord.
O sistema é composto por três partes principais:
<br />
1. Servidor (FastAPI)
2. Bot do Discord
3. Agente instalado nas máquinas clientes
<br />
O servidor gerencia máquinas, scripts e comandos.
O bot envia comandos ao servidor.
O agente recebe comandos e executa os scripts localmente.
<br />
-Configuração do Ambiente
1. Criar arquivo .env
<br />
Copie o modelo:
cp .env.example .env
<br />
Preencha as variáveis necessárias no .env, como:<br />
DATABASE_URL=...<br />
BOT_TOKEN=...<br />
AUTHORIZED_USERS=...<br />
SERVER_URL=...<br />
MACHINE_ID=...<br />
MACHINE_NAME=...<br />
<br />
-Instalação<br />
no terminal:<br />
pip install -r requirements.txt<br />
<br />
-Banco de Dados<br />
Crie as tabelas,
no terminal:<br />
cd server<br />
python migrate.py<br />
<br />

-Executando o Servidor<br />
no pgsql:<br />
cd server<br />
python server.py<br />
O servidor iniciará em http://localhost:8000.<br />
<br />

-Registrando Scripts no Servidor<br />
no terminal:<br />
cd server<br />
python register_script.py /caminho/do/script.sh<br />
<br />

-Executando o Bot do Discord<br />
no terminal:<br />
cd bot<br />
python discord_bot.py<br />
<br />
.possuí os comandos:<br />
!ping_server<br />
!list_machines<br />
!list_scripts<br />
!run_script <machine_id> <script_id> <br />
!machine_status <machine_id> <br />
pip install -r requirements.txt <br />
<br />
-Executando o Agente<br />
.Execução manual<br />
no terminal:<br />
cd agent<br />
python agent.py<br />
<br />
.Execução como serviço systemd (instalado pelo install.sh)<br />
Arquivos criados:<br />
/etc/systemd/system/agent.service<br />
Comandos:<br />
<br />
sudo systemctl start agent  #Starta o Agente<br />
sudo systemctl stop agent   #Pausa o Agente<br />
sudo systemctl status agent #Status do Agente<br />
sudo journalctl -u agent -f #<br />
<br />
-API <br />
GET /machines<br />
Lista máquinas ativas.<br />
<br />
POST /register_machine<br />
Registra/atualiza status da máquina.<br />
<br />
POST /scripts<br />
Registra scripts.<br />
<br />
GET /scripts<br />
Lista scripts.<br />
<br />
POST /execute<br />
Cria um comando para a máquina executar.<br />
<br />
GET /commands/{id}<br />
Mostra status/output de um comando.<br />
<br />
GET /commands/pending/{machine_id}<br />
Agente pega comandos pendentes.<br />
<br />
POST /commands/{id}/result<br />
Agente envia resultado.<br />