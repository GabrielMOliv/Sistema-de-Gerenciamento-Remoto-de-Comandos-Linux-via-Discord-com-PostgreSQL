echo "===================================================="
echo "   Instalador do Agente Linux - Remote Manager"
echo "===================================================="

# Verifica se está rodando como root
if [ "$EUID" -ne 0 ]; then
    echo "Execute como root: sudo ./install.sh"
    exit
fi

# Diretórios
INSTALL_DIR="/usr/local/remote_agent"
SERVICE_FILE="/etc/systemd/system/remote_agent.service"
ENV_FILE="$INSTALL_DIR/.env"

echo "Criando diretórios..."
mkdir -p "$INSTALL_DIR"

echo "Copiando agent.py..."
cp agent.py "$INSTALL_DIR/"


#Criar arquivo .env
echo "Configurando arquivo .env do agente..."
if [ ! -f "$ENV_FILE" ]; then
    echo "SERVER_URL=" > "$ENV_FILE"
    echo "MACHINE_NAME=$(hostname)" >> "$ENV_FILE"
    echo "MACHINE_ID=" >> "$ENV_FILE"
    echo "PING_INTERVAL=300" >> "$ENV_FILE"
fi

chmod 600 "$ENV_FILE"

echo "Arquivo .env criado em: $ENV_FILE"
echo "→ Você deve editar este arquivo e preencher:"
echo "   - SERVER_URL"
echo "   - MACHINE_ID (deixe vazio para gerar automático)"
echo "   - MACHINE_NAME (opcional)"
echo ""


#Instalar Python e dependências
echo "🐍 Instalando dependências Python..."

apt update -y
apt install -y python3 python3-pip

pip3 install aiohttp python-dotenv requests --break-system-packages


#Criar serviço systemd
echo "Criando serviço systemd..."

cat <<EOF > $SERVICE_FILE
[Unit]
Description=Remote Agent - Máquina de Gerenciamento
After=network.target

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/agent.py
Restart=always
RestartSec=5
EnvironmentFile=$ENV_FILE

[Install]
WantedBy=multi-user.target
EOF

chmod 644 $SERVICE_FILE


#Ativar serviço
echo "🔄 Recarregando systemd..."
systemctl daemon-reload

echo "🚀 Iniciando agente..."
systemctl start remote_agent

echo "📌 Ativando para iniciar automaticamente..."
systemctl enable remote_agent


echo "Preencha SERVER_URL no .env antes de confiar no agente."
