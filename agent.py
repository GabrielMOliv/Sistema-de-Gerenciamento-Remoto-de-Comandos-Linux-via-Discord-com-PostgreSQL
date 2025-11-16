import os
import time
import uuid
import requests
import asyncio
import aiohttp
from dotenv import load_dotenv

#Variáveis do ambiente 
load_dotenv()
SERVER_URL = os.getenv("SERVER_URL")  #https://seu-servico-web.up.railway.app
MACHINE_NAME = os.getenv("MACHINE_NAME", "maquina1")
MACHINE_ID = os.getenv("MACHINE_ID", str(uuid.uuid4()))  #se não existir, gera UUID único
PING_INTERVAL = 300  # 5 minutos


async def ping_server(session: aiohttp.ClientSession):
    """
    Envia ping ao servidor, registrando máquina ativa.
    """
    payload = {"id": MACHINE_ID, "name": MACHINE_NAME}
    try:
        r = requests.post(f"{SERVER_URL}/register_machine", json=payload)
        if r.status_code in (200, 201):
            print(f"[PING] Registrado com sucesso: {MACHINE_NAME}")
        else:
            print(f"[PING] Erro no registro: {r.status_code}")
    except Exception as e:
        print(f"[PING] Erro na requisição: {e}")

async def get_commands(session: aiohttp.ClientSession):
    """
    Busca comandos pendentes para esta máquina.
    """
    try:
        r = requests.get(f"{SERVER_URL}/commands/{MACHINE_ID}")
        if r.status_code == 200:
            return r.json()  # lista de comandos
        else:
            print(f"[COMMANDS] Erro ao buscar comandos: {r.status_code}")
    except Exception as e:
        print(f"[COMMANDS] Erro na requisição: {e}")
    return []

async def execute_command(session: aiohttp.ClientSession, command):
    """
    Executa um comando no shell e envia o resultado ao servidor.
    """
    command_id = command["id"]
    content = command["content"]

    print(f"[EXEC] Executando comando {command_id}: {content}")

    # Executa comando de forma assíncrona
    try:
        proc = await asyncio.create_subprocess_shell(
            content,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await proc.communicate()
        output = (stdout.decode() if stdout else "") + "\n" + (stderr.decode() if stderr else "")

    except Exception as e:
        output = f"Erro ao executar comando: {e}"

    # Envia resultado ao servidor
    try:
        async with session.post(
            f"{SERVER_URL}/commands/{command_id}/result",
            json={"output": output}
        ) as resp:
            if resp.status in (200, 201):
                print(f"[RESULT] Resultado enviado para comando {command_id}")
            else:
                print(f"[RESULT] Erro ao enviar resultado: {resp.status}")
    except Exception as e:
        print(f"[RESULT] Erro na requisição: {e}")


async def main():
    """
    Loop principal do agente.
    """
    async with aiohttp.ClientSession() as session:
        while True:
            # 1. Ping no servidor
            await ping_server(session)

            # 2. Buscar comandos pendentes
            commands = await get_commands(session)

            # 3. Executar comandos recebidos
            for cmd in commands:
                await execute_command(session, cmd)

            # 4. Esperar 5 min
            print(f"[SLEEP] Aguardando {PING_INTERVAL} segundos...\n")
            await asyncio.sleep(PING_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
