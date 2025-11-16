import os
import time
import uuid
import subprocess
from datetime import datetime, timezone
from typing import List, Dict, Any

from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError

# --- Configuração do Banco de Dados ---

# Obter a URL do DB do ambiente (essencial para Railway)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Se estiver rodando localmente sem .env, use um valor padrão para testes
    # Altere esta linha se você não estiver usando PostgreSQL localmente
    # raise RuntimeError("DATABASE_URL environment variable is not set.")
    print("AVISO: DATABASE_URL não definida, assumindo SQLite para DEV. NÃO use em produção!")
    DATABASE_URL = "sqlite:///./sql_app.db"
    
# Configuração da Engine
# connect_args={"sslmode": "require"} é necessário para muitos hosts como Railway
if "postgres" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"sslmode": "require"}
    )
else: # Para SQLite local
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

# Criação da Sessão e Base
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Modelos SQLAlchemy ---

class Machine(Base):
    __tablename__ = "machines"
    # O ID é definido pelo agente, não gerado pelo DB
    id = Column(String, primary_key=True, index=True) 
    name = Column(String, index=True)
    # last_seen armazena um timestamp Unix
    last_seen = Column(Float, default=time.time) 

class Script(Base):
    __tablename__ = "scripts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    content = Column(String)

class Command(Base):
    __tablename__ = "commands"
    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(String, index=True)
    script_name = Column(String)
    status = Column(String, default="pending") # pending, executing, completed, failed
    output = Column(String, nullable=True)
    # Adicionado campo de criação com fuso horário UTC
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

# --- Criação de Tabelas (Garantir que as tabelas existam para testes) ---
# Em produção, use o migrate.py, mas isto ajuda em testes locais.
Base.metadata.create_all(bind=engine)

# --- Pydantic Schemas ---

class RegisterMachine(BaseModel):
    id: str
    name: str

class ScriptRequest(BaseModel):
    name: str
    content: str

class ExecuteRequest(BaseModel):
    machine_id: str
    script_name: str

class CommandResult(BaseModel):
    output: str

class CommandResponse(BaseModel):
    id: int
    machine_id: str
    script_name: str
    status: str
    output: str | None
    created_at: datetime

# --- Inicialização do FastAPI ---

app = FastAPI(
    title="Remote Linux Command Manager",
    description="Backend para gerenciamento de comandos remotos via Discord."
)

# Dependência para obter a sessão do DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Funções de Segurança ---

DANGEROUS_COMMANDS = ["rm -rf", "shutdown", "reboot", "poweroff", "mkfs", "dd", "chmod 777"]

def check_for_dangerous_commands(content: str):
    content_lower = content.lower()
    for cmd in DANGEROUS_COMMANDS:
        if cmd in content_lower:
            return True
    return False

# --- Endpoints ---

@app.post("/register_machine")
def register_machine(data: RegisterMachine, db: Session = Depends(get_db)):
    # 1. Atualiza o timestamp se a máquina já existe
    machine = db.query(Machine).filter_by(id=data.id).first()
    if machine:
        # Atualiza apenas last_seen
        machine.last_seen = time.time()
        # Se o nome mudou, atualiza também
        if machine.name != data.name:
            machine.name = data.name
        db.commit()
        return {"status": "updated", "message": f"Machine {data.name} updated."}
    
    # 2. Cria uma nova máquina se não existir
    new_machine = Machine(id=data.id, name=data.name, last_seen=time.time())
    db.add(new_machine)
    db.commit()
    return {"status": "created", "message": f"Machine {data.name} registered."}

@app.get("/machines")
def list_machines(db: Session = Depends(get_db)):
    # Filtra máquinas que fizeram ping nos últimos 5 minutos (300 segundos)
    timeout = time.time() - 300
    machines = db.query(Machine).filter(Machine.last_seen >= timeout).all()
    # Retorna uma lista de dicionários
    return [{"id": m.id, "name": m.name, "last_seen": m.last_seen} for m in machines]

@app.post("/scripts")
def register_script(data: ScriptRequest, db: Session = Depends(get_db)):
    # Checa comandos perigosos
    if check_for_dangerous_commands(data.content):
        raise HTTPException(status_code=403, detail="Script content contains dangerous commands.")
        
    # Checa se o script já existe (case-insensitive)
    existing_script = db.query(Script).filter(func.lower(Script.name) == func.lower(data.name)).first()
    if existing_script:
        raise HTTPException(status_code=400, detail=f"Script name '{data.name}' already exists.")
        
    # Cria novo script
    new_script = Script(name=data.name, content=data.content)
    db.add(new_script)
    db.commit()
    return {"status": "created", "message": f"Script '{data.name}' registered successfully."}

@app.post("/execute")
def execute_script(data: ExecuteRequest, db: Session = Depends(get_db)):
# 1. Busca pela Máquina e Script
    machine = db.query(Machine).filter_by(id=data.machine_id).first()
    script = db.query(Script).filter(func.lower(Script.name) == func.lower(data.script_name)).first()
    
    # Se máquina ou script não forem encontrados, retorna 404 (com JSON)
    if not machine or not script:
        raise HTTPException(status_code=404, detail="Machine or script not found")
        
    # 2. Criação do Comando e Inserção no DB (Bloco crítico com tratamento de erro)
    try:
        # 2a. Instancia o objeto (created_at é preenchido automaticamente)
        cmd = Command(machine_id=machine.id, script_name=script.name)
        
        # 2b. Adiciona e tenta commit
        db.add(cmd)
        db.commit()
        
        # 2c. ATUALIZA O OBJETO COM O ID GERADO PELO BANCO DE DADOS
        db.refresh(cmd) # <--- OBRIGATÓRIO: Obtém o ID autogerado pelo DB!
        
        # 3. Sucesso: Retorna o ID do comando para o Discord Bot
        return {
            "status": "ok", 
            "message": f"Command created for {machine.name}",
            "command_id": cmd.id # <--- ID real retornado aqui!
        }

    except SQLAlchemyError as e:
        # Captura erros de DB (ex: constraint violation)
        db.rollback() 
        print(f"DATABASE ERROR during execute_script: {e}")
        
        # Retorna 500 COM corpo JSON (tratável pelo Discord bot)
        raise HTTPException(
            status_code=500, 
            detail=f"Database integrity error during command creation. Check server logs for details. Original Error: {e.orig}"
        )
    except Exception as e:
        # Captura outros erros inesperados
        db.rollback()
        print(f"UNEXPECTED ERROR during execute_script: {e}")
        
        raise HTTPException(
            status_code=500, 
            detail=f"An unexpected server error occurred: {e}"
        )

# Endpoint para o Agente buscar comandos
@app.get("/commands/{machine_id}")
def get_pending_commands(machine_id: str, db: Session = Depends(get_db)):
    # 1. Busca comandos pendentes para a máquina específica
    pending_commands = db.query(Command).filter_by(
        machine_id=machine_id, 
        status="pending"
    ).order_by(Command.created_at).all()
    
    # 2. Converte para uma lista de dicionários com o conteúdo do script
    commands_to_execute = []
    for cmd in pending_commands:
        # Busca o conteúdo do script
        script = db.query(Script).filter_by(name=cmd.script_name).first()
        
        if script:
            commands_to_execute.append({
                "id": cmd.id,
                "script_name": cmd.script_name,
                "content": script.content 
            })
            # Opcional: Mudar status para 'executing' para evitar que outro agente pegue
            # cmd.status = "executing"
            
    db.commit() # Salva a mudança de status (se implementada)
    return commands_to_execute

# Endpoint para o Agente enviar o resultado
@app.post("/commands/{command_id}/result")
def post_command_result(command_id: int, result: CommandResult, db: Session = Depends(get_db)):
    # 1. Busca o comando
    cmd = db.query(Command).filter_by(id=command_id).first()
    
    if not cmd:
        raise HTTPException(status_code=404, detail="Command not found.")
        
    # 2. Atualiza o status e a saída
    cmd.status = "completed"
    cmd.output = result.output
    
    db.commit()
    
    return {"status": "ok", "message": f"Command {command_id} result saved."}

# Endpoint para o Bot Discord verificar o resultado (NOVO)
@app.get("/commands/{command_id}", response_model=CommandResponse)
def get_command_status(command_id: int, db: Session = Depends(get_db)):
    # 1. Busca o comando
    cmd = db.query(Command).filter_by(id=command_id).first()
    
    if not cmd:
        raise HTTPException(status_code=404, detail="Command ID not found.")
        
    # 2. Retorna o objeto Command, que será serializado pelo Pydantic Response Model
    return cmd