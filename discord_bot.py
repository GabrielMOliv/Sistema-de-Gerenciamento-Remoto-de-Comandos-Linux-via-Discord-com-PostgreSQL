# discord_bot.py
import discord
from discord.ext import commands
from discord.ext.commands import CheckFailure
import aiohttp
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
SERVER_URL = os.getenv("SERVER_URL")
AUTHORIZED_USERS = [int(x) for x in os.getenv("AUTHORIZED_USERS", "").split(",")]

# Inicializa bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def is_authorized():
    async def predicate(ctx):
        if ctx.author.id not in AUTHORIZED_USERS:
            await ctx.send("Você não tem permissão para usar este comando.")
            raise CheckFailure("Usuário não autorizado")
        return True
    return commands.check(predicate)

@bot.command()
@is_authorized()
async def list_machines(ctx):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{SERVER_URL}/machines") as resp:
            if resp.status == 200:
                machines = await resp.json()
                if not machines:
                    await ctx.send("Nenhuma máquina ativa no momento.")
                    return
                msg = "**Máquinas Ativas:**\n"
                for m in machines:
                    msg += f"- {m['name']} (ID: {m['id']})\n"
                await ctx.send(msg)
            else:
                await ctx.send("Erro ao consultar o servidor.")

@bot.command()
@is_authorized()
async def register_script(ctx, name: str, *, content: str):
    payload = {"name": name, "content": content}
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{SERVER_URL}/scripts", json=payload) as resp:
            if resp.status in (200, 201):
                data = await resp.json()
                await ctx.send(f"✅ {data['message']}")
            else:
                data = await resp.json()
                await ctx.send(f"Erro: {data.get('detail', 'Desconhecido')}")

@bot.command()
@is_authorized()
async def execute_script(ctx, machine_id:str, script_name:str):
    """
    Executa um script em uma máquina específica usando seu ID.
    O Bot não precisa mais buscar a lista de máquinas.
    """
    # 1. Prepara o payload diretamente com o ID e o nome do script
    payload = {"machine_id":machine_id, "script_name":script_name}

    # 2. Envia a requisição de execução para o servidor
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{SERVER_URL}/execute", json=payload) as resp:
            data = await resp.json()

            if resp.status == 200:
                # Sucesso
                await ctx.send(f"{data['message']}")
            else:
                # Erro (ex: Máquina ou script não encontrado)
                error_detail = data.get('detail', 'Erro desconhecido na execução.')
                await ctx.send(f" Falha na execução: {error_detail}")

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")

bot.run(BOT_TOKEN)