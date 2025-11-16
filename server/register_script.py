import requests

# MUDE ESTA URL PARA A URL DO SEU SERVIÇO RAILWAY
# EX: 'https://seu-projeto-fastapi-xxx.up.railway.app'
BASE_URL = "https://web-production-30b2.up.railway.app" 

if BASE_URL == "[SUA_URL_RAILWAY]":
    print("ERRO: Por favor, substitua [SUA_URL_RAILWAY] pela URL real do seu serviço Railway.")
    exit()

# Dados do script que será registrado no banco de dados
script_data = {
    "name": "hello_test",
    "content": "echo 'Script de teste registrado com sucesso!' && whoami"
}

# Endpoint para registro de scripts
url = f"{BASE_URL}/scripts"

print(f"Tentando registrar o script '{script_data['name']}' em {url}...")

try:
    # Faz a requisição POST para o servidor FastAPI
    response = requests.post(url, json=script_data)
    
    # Verifica o status da resposta
    if response.status_code == 200:
        print("\n✅ SUCESSO! Script registrado com êxito.")
        print(f"Resposta do servidor: {response.json()}")
        print("\nAgora você pode executar o script 'hello_test' no Discord.")
    
    elif response.status_code == 400:
        print(f"\n❌ ERRO (400 - Já Existe): O script '{script_data['name']}' já está registrado.")
        print("Você pode ignorar esta mensagem, o script já está pronto para uso.")
        
    else:
        print(f"\n❌ ERRO INESPERADO ({response.status_code}):")
        print(f"Detalhes do erro: {response.text}")

except requests.exceptions.RequestException as e:
    print(f"\n❌ ERRO DE CONEXÃO: Não foi possível conectar ao servidor. Verifique a URL e a conexão à internet.")
    print(f"Detalhes: {e}")