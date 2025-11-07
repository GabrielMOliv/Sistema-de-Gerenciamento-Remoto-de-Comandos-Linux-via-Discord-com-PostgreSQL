# agent.py
import os
import time
import uuid
import requests
import subprocess
from dotenv import load_dotenv

#Variáveis do ambiente 
load_dotenv()
SERVER_URL = os.getenv("SERVER_URL")  #https://seu-servico-web.up.railway.app
MACHINE_NAME = os.getenv("MACHINE_NAME", "maquina1")
MACHINE_ID = os.getenv("MACHINE_ID", str(uuid.uuid4()))  #se não existir, gera UUID único
PING_INTERVAL = 300  # 5 minutos

#Função para registrar máquina e enviar ping
def ping_server():
    payload = {"id": MACHINE_ID, "name": MACHINE_NAME}
    try:
        r = requests.post(f"{SERVER_URL}/register_machine", json=payload)
        if r.status_code in (200, 201):
            print(f"[PING] Registrado com sucesso: {MACHINE_NAME}")
        else:
            print(f"[PING] Erro no registro: {r.status_code}")
    except Exception as e:
        print(f"[PING] Erro na requisição: {e}")

#Função para buscar comandos pendentes
def get_commands():
    try:
        r = requests.get(f"{SERVER_URL}/commands/{MACHINE_ID}")
        if r.status_code == 200:
            return r.json()  # lista de comandos
        else:
            print(f"[COMMANDS] Erro ao buscar comandos: {r.status_code}")
    except Exception as e:
        print(f"[COMMANDS] Erro na requisição: {e}")
    return []

#Executa comando e envia resultado
def execute_command(command):
    command_id = command['id']
    script_name = command['script_name']
    content = command['content']

    try:
        # Executa comando no shell
        result = subprocess.run(content, shell=True, capture_output=True, text=True, timeout=300)
        output = result.stdout + "\n" + result.stderr
    except Exception as e:
        output = f"Erro ao executar comando: {e}"

    # Envia saída ao servidor
    try:
        r = requests.post(f"{SERVER_URL}/commands/{command_id}/result", json={"output": output})
        if r.status_code in (200, 201):
            print(f"[RESULT] Resultado enviado para comando {command_id}")
        else:
            print(f"[RESULT] Erro ao enviar resultado: {r.status_code}")
    except Exception as e:
        print(f"[RESULT] Erro na requisição: {e}")

#Loop principal
if __name__ == "__main__":
    while True:
        ping_server()
        commands = get_commands()
        for cmd in commands:
            execute_command(cmd)
        time.sleep(PING_INTERVAL)
