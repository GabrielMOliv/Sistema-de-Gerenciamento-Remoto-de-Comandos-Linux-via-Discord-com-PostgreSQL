import os
from sqlalchemy import create_engine
from server.server import Base

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("ERRO: Variável DATABASE_URL não encontrada.")
    exit(1)

try:
    print("Iniciando MIGRACAO DE SCHEMA... Conectando ao DB...")
    
    engine = create_engine(
        DATABASE_URL,
        connect_args={"sslmode": "require"} 
    )
    
    # Força a atualização do schema, adicionando a coluna 'created_at'
    Base.metadata.create_all(bind=engine)
    
    print("MIGRACAO CONCLUIDA! O schema do banco de dados foi atualizado.")
    
except Exception as e:
    print(f"ERRO DE MIGRACAO FATAL: Falha ao criar tabelas: {e}")
    exit(1)