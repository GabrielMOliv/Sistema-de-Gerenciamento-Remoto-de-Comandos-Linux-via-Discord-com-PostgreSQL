# migrate.py

import os
from sqlalchemy import create_engine
# Importa APENAS a base e os modelos do seu server.py
from server import Base, Machine, Script, Command, SessionLocal 

# A RAILWAY INJETA DATABASE_URL VIA VARIÁVEL DE AMBIENTE
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("ERRO: Variável DATABASE_URL não encontrada.")
    exit(1)

try:
    print("Tentando criar tabelas do banco de dados...")
    
    # Cria a engine de conexão, incluindo a configuração SSL necessária para o Railway
    engine = create_engine(
        DATABASE_URL,
        connect_args={"sslmode": "require"} 
    )
    
    # Cria as tabelas (o comando que precisamos)
    # ATENÇÃO: create_all() só cria tabelas que AINDA não existem.
    # Para a tabela 'commands', ele adicionará a nova coluna se ela já não estiver lá 
    # ou tentará criar a tabela inteira se for a primeira vez.
    Base.metadata.create_all(bind=engine)
    
    print("Tabelas criadas com sucesso! Saindo...")
    
except Exception as e:
    print(f"ERRO DE MIGRACAO FATAL: Falha ao criar tabelas: {e}")
    # Força a saída com código de erro, se algo falhar
    exit(1)