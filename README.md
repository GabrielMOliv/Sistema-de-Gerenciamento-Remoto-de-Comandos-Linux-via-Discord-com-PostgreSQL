Discord Remote Script Manager

Este projeto permite executar scripts em máquinas remotas através de um bot do Discord.
O sistema é composto por três partes principais:

1. Servidor (FastAPI)
2. Bot do Discord
3. Agente instalado nas máquinas clientes

O servidor gerencia máquinas, scripts e comandos.
O bot envia comandos ao servidor.
O agente recebe comandos e executa os scripts localmente.

-Configuração do Ambiente
1. Criar arquivo .env

Copie o modelo:
cp .env.example .env

Preencha as variáveis necessárias no .env, como:
DATABASE_URL=...
BOT_TOKEN=...
AUTHORIZED_USERS=...
SERVER_URL=...
MACHINE_ID=...
MACHINE_NAME=...

-Instalação
no terminal:
pip install -r requirements.txt

-Banco de Dados
Crie as tabelas:
no terminal:
cd server
python migrate.py


-Executando o Servidor
no pgsql:
cd server
python server.py
O servidor iniciará em http://localhost:8000.


-Registrando Scripts no Servidor
no terminal:
cd server
python register_script.py /caminho/do/script.sh


-Executando o Bot do Discord
no terminal:
cd bot
python discord_bot.py

.possuí os comandos:
!ping_server
!list_machines
!list_scripts
!run_script <machine_id> <script_id>
!machine_status <machine_id>
pip install -r requirements.txt

-Executando o Agente
.Execução manual
no terminal:
cd agent
python agent.py

.Execução como serviço systemd (instalado pelo install.sh)
Arquivos criados:
/etc/systemd/system/agent.service
Comandos:

sudo systemctl start agent  #Starta o Agente
sudo systemctl stop agent   #Pausa o Agente
sudo systemctl status agent #Status do Agente
sudo journalctl -u agent -f #

-API 
✔ GET /machines
Lista máquinas ativas.

✔ POST /register_machine
Registra/atualiza status da máquina.

✔ POST /scripts
Registra scripts.

✔ GET /scripts
Lista scripts.

✔ POST /execute
Cria um comando para a máquina executar.

✔ GET /commands/{id}
Mostra status/output de um comando.

✔ GET /commands/pending/{machine_id}
Agente pega comandos pendentes.

✔ POST /commands/{id}/result
Agente envia resultado.