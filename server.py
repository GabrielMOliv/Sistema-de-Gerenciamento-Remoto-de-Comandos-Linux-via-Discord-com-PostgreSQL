from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Integer, Text, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Carrega variáveis do .env e força o caminho
from pathlib import Path
dotenv_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

# Mostra se foi carregado e oq foi carregado
print("Arquivo .env carregado de:", dotenv_path)
print("DATABASE_URL =", os.getenv("DATABASE_URL"))

DATABASE_URL = os.getenv("DATABASE_URL")

#Conexão PostgreSQL
engine = create_engine(DATABASE_URL)
print(f"Usando Banco: {DATABASE_URL}")
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

app = FastAPI(title="Linux Remote Manager")

#----------MODELOS----------
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
    machine = relationship("Machine")
    script = relationship("Script")

# Cria as tabelas no banco
Base.metadata.create_all(bind=engine)


#---------MODELOS Pydantic--------
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



#----------ENDPOINTS----------
@app.get("/machines")
def list_machines():
    session = SessionLocal()
    five_minutes_ago = int(datetime.utcnow().timestamp()) - 300
    machines = session.query(Machine).filter(Machine.last_seen >= five_minutes_ago).all()
    session.close()
    return [{"id": m.id, "name": m.name, "last_seen": m.last_seen} for m in machines]

@app.post("/register_machine")
def register_machine(data: MachineRegister):
    session = SessionLocal()
    machine = session.query(Machine).filter_by(id=data.id).first()
    now = int(datetime.utcnow().timestamp())
    if machine:
        machine.last_seen = now
        machine.name = data.name
    else:
        session.add(Machine(id=data.id, name=data.name, last_seen=now))
    session.commit()
    session.close()
    return {"status": "ok", "message": f"Machine {data.name} registered"}

@app.post("/scripts")
def register_script(data: ScriptRegister):
    session = SessionLocal()
    script = session.query(Script).filter_by(name=data.name).first()
    if script:
        raise HTTPException(status_code=400, detail="Script name already exists")
    session.add(Script(name=data.name, content=data.content))
    session.commit()
    session.close()
    return {"status": "ok", "message": f"Script {data.name} registered"}

@app.post("/execute")
def execute_script(data: ExecuteRequest):
    session = SessionLocal()
    machine = session.query(Machine).filter_by(id=data.machine_id).first()
    script = session.query(Script).filter_by(name=data.script_name).first()
    if not machine or not script:
        raise HTTPException(status_code=404, detail="Machine or script not found")
    cmd = Command(machine_id=machine.id, script_name=script.name)
    session.add(cmd)
    session.commit()
    session.close()
    return {"status": "ok", "message": f"Command created for {machine.name}"}

@app.get("/commands/{machine_id}")
def get_pending_commands(machine_id: str):
    session = SessionLocal()
    
    #Faz um JOIN entre Command e Script para obter o conteúdo (content)
    #necessário para o agente executar o comando.
    cmds = session.query(
        Command.id, 
        Command.script_name, 
        Script.content
    ).join(
        Script, Command.script_name == Script.name
    ).filter(
        Command.machine_id == machine_id, 
        Command.status == "pending"
    ).all()
    
    session.close()
    
    # Retorna uma lista de dicionários com os campos necessários
    return [
        {"id": c.id, "script_name": c.script_name, "content": c.content} 
        for c in cmds
    ]

@app.post("/commands/{command_id}/result")
def post_command_result(command_id: int, result: CommandResult):
    session = SessionLocal()
    cmd = session.query(Command).filter_by(id=command_id).first()
    if not cmd:
        raise HTTPException(status_code=404, detail="Command not found")
    cmd.status = "completed"
    cmd.output = result.output
    session.commit()
    session.close()
    return {"status": "ok", "message": "Result saved"}

