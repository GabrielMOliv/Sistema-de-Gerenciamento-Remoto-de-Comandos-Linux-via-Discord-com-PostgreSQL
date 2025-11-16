import discord
from discord.ext import commands
from discord.ext.commands import CheckFailure
import aiohttp
import os
from dotenv import load_dotenv
import datetime 

# Carrega variáveis de ambiente
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
SERVER_URL = os.getenv("SERVER_URL")
# Converte a string de IDs em uma lista de inteiros, ignorando entradas vazias
AUTHORIZED_USERS = [int(x) for x in os.getenv("AUTHORIZED_USERS", "").split(",") if x.strip().isdigit()]

#Config do Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

#Checa para ver se o usuário está presente na lista de usuários autorizados
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
    """Lista todas as máquinas ativas (último ping nos últimos 5 minutos)."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{SERVER_URL}/machines") as resp:
            if resp.status != 200:
                return await ctx.send(f"Erro ao consultar o servidor ({resp.status}).")

            machines = await resp.json()

            if not machines:
                return await ctx.send("Nenhuma máquina ativa no momento.")

            msg = "📡 **Máquinas Ativas:**\n"
            for m in machines:
                last_seen_dt = datetime.datetime.fromtimestamp(m["last_seen"], tz=datetime.timezone.utc)
                formatted = last_seen_dt.strftime("%d/%m/%Y %H:%M:%S UTC")
                msg += f"- **{m['name']}** (`{m['id']}`) — Último ping: `{formatted}`\n"

            await ctx.send(msg)


@bot.command()
@is_authorized()
async def register_script(ctx, name: str, *, content: str):
    payload = {"name": name, "content": content}

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{SERVER_URL}/scripts", json=payload) as resp:

            data = await resp.json()

            if resp.status in (200, 201):
                return await ctx.send(f"Script `{name}` registrado com sucesso!")

            await ctx.send(f"Erro ({resp.status}): {data.get('detail', 'Erro desconhecido')}")

@bot.command()
@is_authorized()
async def execute_script(ctx, machine_id:str, script_name:str):
    """Agenda a execução de um script em uma máquina específica (ex: !execute_script maquina1 hello_test)."""
    payload = {"machine_id": machine_id, "script_name": script_name}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{SERVER_URL}/execute", json=payload) as resp:
                try:
                    data = await resp.json()
                except:
                    data = None

                if resp.status == 200:
                    cmd_id = data.get("command_id", "?")
                    return await ctx.send(
                        f"Execução agendada!\n"
                        f"ID do comando: `{cmd_id}`\n"
                        f"Use `!check_result {cmd_id}` para consultar o resultado."
                    )

                await ctx.send(f"Erro ({resp.status}): {data.get('detail', 'Erro desconhecido')}")
                    
    except aiohttp.ClientConnectorError:
        await ctx.send("Erro de conexão com o servidor. Verifique se o `SERVER_URL` está correto e o servidor online.")
    except Exception as e:
        await ctx.send(f"Ocorreu um erro inesperado: {e}")


@bot.command()
@is_authorized()
async def check_result(ctx, command_id: int):
    """Verifica o status e a saída de um comando agendado (ex: !check_result 1)."""
    async with aiohttp.ClientSession() as session:
        # Este endpoint é o GET /commands/{command_id} implementado na resposta anterior no server.py
        async with session.get(f"{SERVER_URL}/commands/{command_id}") as resp:
            
            if resp.status == 200:
                data = await resp.json()
                status = data['status']
                
                if status == 'pending':
                    await ctx.send(f"Comando `{command_id}` ainda **Pendente** na máquina `{data['machine_id']}`. Aguarde o próximo ciclo do Agente.")
                
                elif status == 'completed':
                    output = data['output']
                    # Limita a saída para o limite do Discord (2000 chars) para evitar erros
                    if len(output) > 1800:
                         output = output[:1800] + "\n... [SAÍDA TRUNCADA]"
                         
                    await ctx.send(
                        f"Comando `{command_id}` **CONCLUÍDO** na máquina `{data['machine_id']}`:\n"
                        f"**Script:** `{data['script_name']}`\n"
                        f"```bash\n{output}\n```"
                    )
                
                else:
                    await ctx.send(f"Status do comando `{command_id}` desconhecido: `{status}`")
                    
            elif resp.status == 404:
                await ctx.send(f"Comando ID `{command_id}` não encontrado no servidor.")
            
            else:
                await ctx.send(f"Erro ao consultar o servidor: Status {resp.status}")


@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")

bot.run(BOT_TOKEN)
