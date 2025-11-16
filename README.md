Discord Remote Script Manager

Este projeto permite executar scripts remotamente através de um bot do Discord, conectado a um servidor FastAPI e a um agente instalado em máquinas clientes.
A comunicação ocorre via HTTP, com autenticação por MACHINE_ID.
O servidor controla máquinas, scripts e comandos enviados pelo Discord.

Funcionalidades
Servidor (FastAPI)

Cadastro de máquinas e heartbeat automático.

Cadastro, listagem e execução de scripts remotos.

Distribuição de comandos para máquinas conectadas.

Banco de dados PostgreSQL com SQLAlchemy.

Bot do Discord

Lista máquinas disponíveis.

Lista scripts registrados.

Executa scripts em máquinas específicas.

Mostra logs e estados de execução.

Apenas usuários autorizados podem usar os comandos.

Agente

Roda em segundo plano usando systemd.

Faz heartbeat periódico no servidor.

Recebe comandos e executa scripts locais.

Envia a saída ao servidor.

Requisitos
Sistema

Python 3.10+

PostgreSQL 13+

pip

Python

Instale dependências com:

pip install -r requirements.txt

Estrutura de Pastas
projeto/
│
├── README.md
├── requirements.txt
├── Procfile
├── install.sh
├── .env.example
│
├── server/
│   ├── server.py
│   ├── migrate.py
│   └── register_script.py
│
├── bot/
│   └── discord_bot.py
│
└── agent/
    └── agent.py

Configuração
1. Crie o arquivo .env

Use o modelo:

cp .env.example .env


Preencha:

DATABASE_URL=postgresql://USER:SENHA@localhost:5432/discord_manager
BOT_TOKEN=seu_token_do_discord
AUTHORIZED_USERS=ID1,ID2
SERVER_URL=https://seu-servidor.com

Executando Cada Módulo
1. Servidor (FastAPI + Uvicorn)
cd server
python server.py


O servidor inicia em:

http://localhost:8000

2. Banco de dados (criação das tabelas)
cd server
python migrate.py

3. Cadastro de scripts

Exemplo:

cd server
python register_script.py /home/gabriel/scripts/backup.sh

4. Agente
Teste manual
cd agent
python agent.py

Rodar em segundo plano com systemd

Arquivo gerado durante a instalação:

/etc/systemd/system/agent.service


Comandos principais:

sudo systemctl start agent
sudo systemctl stop agent
sudo systemctl status agent
sudo journalctl -u agent -f

5. Bot do Discord
cd bot
python discord_bot.py


Comandos disponíveis no Discord:

!ping_server
!list_machines
!list_scripts
!run_script <machine_id> <script_id>
!machine_status <machine_id>

Documentação da API
1. Registrar heartbeat
POST /machines/ping


Body:

{
  "machine_id": "",
  "machine_name": ""
}

2. Buscar comandos pendentes para uma máquina
GET /commands/{machine_id}

3. Registrar execução de script
POST /scripts/execute


Body:

{
  "machine_id": "",
  "script_id": ""
}

4. Listar scripts
GET /scripts

5. Listar máquinas registradas
GET /machines

Instalação Automática

O arquivo install.sh:

Cria .env interativo.

Instala dependências.

Verifica Python.

Cria serviço systemd para o agente.

Ativa e inicia o agente.

Execute:

chmod +x install.sh
./install.sh

Deploy em Outra Máquina

Clone o repositório:

git clone https://github.com/seuusuario/projeto.git


Vá para a pasta:

cd projeto


Execute o instalador:

./install.sh


Preencha o .env.

Inicie os módulos desejados (servidor, bot, agente).

Contribuição

Faça um fork.

Crie uma branch:
git checkout -b nova-feature

Faça commit:
git commit -m "descrição"

Envie:
git push origin nova-feature

Abra um Pull Request.