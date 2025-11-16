from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import os

# --- CONEXÃO E CONFIGURAÇÃO DA RAILWAY ---
# 1. REMOÇÃO DA LÓGICA DE .ENV: O Railway já injeta DATABASE_URL.
#    Confiamos apenas no ambiente (os.getenv).

DATABASE_URL = os.getenv("DATABASE_URL")

# VERIFICAÇÃO DE SEGURANÇA: Garante que a URL foi carregada
if not DATABASE_URL:
    # Se o servidor não conseguir iniciar, ele falha com uma mensagem clara.
    raise RuntimeError("DATABASE_URL não configurada. O servidor não pode iniciar.")

# 2. Conexão PostgreSQL
engine = create_engine(
    DATABASE_URL,
    connect_args={"sslmode": "require"}
)
print(f"Usando Banco: {DATABASE_URL}")

# Configuração da Sessão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI(title="Linux Remote Manager")

# 3. FUNÇÃO DE INJEÇÃO DE DEPENDÊNCIA (Gerenciamento Seguro da Sessão)
def get_db():
    db = SessionLocal()
    try:
        # Fornece a sessão para o endpoint
        yield db
    finally:
        # Garante que a sessão é fechada, mesmo que ocorra um erro no endpoint.
        db.close()

# -----------------MODELOS-----------------
class Machine(Base):
    __tablename__ = "machines"
    id = Column(String, primary_key=True)
    name = Column(String)
    last_seen = Column(Integer)

class Script(Base):
    __tablename__ = "scripts"
    name = Column(String, primary_key=True)
    content = Column(Text)

class Command(Base):
    __tablename__ = "commands"
    id = Column(Integer, primary_key=True, autoincrement=True)
    machine_id = Column(String, ForeignKey("machines.id"))
    script_name = Column(String, ForeignKey("scripts.name"))
    status = Column(String, default="pending")
    output = Column(Text, default="")

    created_at = Column(DateTime, default=datetime.utcnow)

    machine = relationship("Machine")
    script = relationship("Script")


#modelos Pydantic
class MachineRegister(BaseModel):
    id: str
    name: str

class ScriptRegister(BaseModel):
    name: str
    content: str

class ExecuteRequest(BaseModel):
    machine_id: str
    script_name: str

class CommandResult(BaseModel):
    output: str



# ----------ENDPOINTS----------
@app.get("/machines")
def list_machines(db: Session = Depends(get_db)):
    five_minutes_ago = int(datetime.utcnow().timestamp()) - 300
    machines = db.query(Machine).filter(Machine.last_seen >= five_minutes_ago).all()
    return [
        {"id": m.id, "name": m.name, "last_seen": m.last_seen} 
        for m in machines
    ]


@app.post("/register_machine")
def register_machine(data: MachineRegister, db: Session = Depends(get_db)):
    machine = db.query(Machine).filter_by(id=data.id).first()
    now = int(datetime.utcnow().timestamp())
    if machine:
        machine.last_seen = now
        machine.name = data.name
    else:
        db.add(Machine(id=data.id, name=data.name, last_seen=now))
    db.commit()
    return {"status": "ok", "message": f"Machine {data.name} registered"}


@app.post("/scripts")
def register_script(data: ScriptRegister, db: Session = Depends(get_db)):
    script = db.query(Script).filter_by(name=data.name).first()
    if script:
        raise HTTPException(status_code=400, detail="Script name already exists")
    
    db.add(Script(name=data.name, content=data.content))
    db.commit()

    return {"status": "ok", "message": f"Script {data.name} registered"}


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
        db.refresh(cmd)
        
        # 3. Sucesso
        return {
            "status": "ok", 
            "message": f"Command created for {machine.name}",
            "command_id": cmd.id
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


#ENDPOINT QUE O DISCORD BOT PRECISA PARA check_result
@app.get("/commands/{command_id}")
def get_command_status(command_id: int, db: Session = Depends(get_db)):
    cmd = db.query(Command).filter_by(id=command_id).first()

    if not cmd:
        raise HTTPException(status_code=404, detail="Command not found")

    return {
        "id": cmd.id,
        "machine_id": cmd.machine_id,
        "script_name": cmd.script_name,
        "status": cmd.status,
        "output": cmd.output,
        "created_at": str(cmd.created_at)
    }

# ENDPOINT QUE O AGENTE USA PARA PEGAR COMANDOS PENDENTES
@app.get("/commands/pending/{machine_id}")
def get_pending_commands(machine_id: str, db: Session = Depends(get_db)):
    # Faz um JOIN entre Command e Script para obter o conteúdo (content)
    cmds = (
        db.query(Command.id, Command.script_name, Script.content)
        .join(Script, Command.script_name == Script.name)
        .filter(Command.machine_id == machine_id, Command.status == "pending")
        .all()
    )

    return [
        {"id": c.id, "script_name": c.script_name, "content": c.content}
        for c in cmds
    ]

# ENDPOINT PARA O AGENTE REPORTAR RESULTADO
@app.post("/commands/{command_id}/result")
def post_command_result(command_id: int, result: CommandResult, db: Session = Depends(get_db)):
    cmd = db.query(Command).filter_by(id=command_id).first()
    
    if not cmd:
        raise HTTPException(status_code=404, detail="Command not found")
    
    cmd.status = "completed"
    cmd.output = result.output
    db.commit()

    return {"status": "ok", "message": "Result saved"}