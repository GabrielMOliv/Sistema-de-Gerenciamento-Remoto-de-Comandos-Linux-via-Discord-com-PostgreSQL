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
    
    # Cria a engine de conexão
    engine = create_engine(DATABASE_URL)
    
    # Cria as tabelas (o comando que precisamos)
    Base.metadata.create_all(bind=engine)
    
    print("Tabelas criadas com sucesso! Saindo...")
    
except Exception as e:
    print(f"ERRO DE MIGRACAO FATAL: Falha ao criar tabelas: {e}")
    # Força a saída com código de erro, se algo falhar
    exit(1)

# O script termina aqui com sucesso (código de saída 0)