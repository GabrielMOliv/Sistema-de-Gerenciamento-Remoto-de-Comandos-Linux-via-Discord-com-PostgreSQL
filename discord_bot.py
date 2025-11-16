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
    payload = {"machine_id": machine_id, "script_name": script_name}
    
    # Adicionando tratamento de erros de conexão/timeout
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{SERVER_URL}/execute", json=payload) as resp:
                
                # Tenta decodificar o JSON (pode falhar se o corpo estiver vazio ou não for JSON)
                try:
                    data = await resp.json()
                except aiohttp.ContentTypeError:
                    data = None # Nenhuma data JSON para processar

                if resp.status == 200:
                     # Sucesso
                    # Usa a mensagem do servidor, ou uma mensagem padrão se não houver JSON
                    message = data.get('message', 'Comando executado com sucesso.') if data else 'Comando executado com sucesso (sem resposta JSON detalhada).'
                    await ctx.send(f"✅ {message}")
                else:
                    # Erro HTTP retornado pelo servidor
                    if data:
                        error_detail = data.get('detail', f'Erro desconhecido (Status: {resp.status}).')
                    else:
                        error_detail = f"O servidor retornou um erro HTTP {resp.status} e o corpo da resposta estava vazio ou não era JSON."
                        
                    await ctx.send(f"Falha na execução: {error_detail}")
                    
    except aiohttp.ClientConnectorError:
        await ctx.send("Erro de conexão com o servidor. Verifique se o `SERVER_URL` está correto e o servidor online.")
    except Exception as e:
        await ctx.send(f"Ocorreu um erro inesperado: {e}")

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")

bot.run(BOT_TOKEN)