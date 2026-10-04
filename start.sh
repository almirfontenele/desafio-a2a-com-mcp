#!/usr/bin/env bash
set -e

echo "--------------------------------------------------------"
echo "  Inicializando ambiente A Ponte (Agente A2A + MCP)    "
echo "--------------------------------------------------------"

# Valida ou gera a chave de segredo REQUEST_STATE_SECRET
if [ -z "$REQUEST_STATE_SECRET" ]; then
    echo "[INFO] REQUEST_STATE_SECRET não definida. Gerando chave aleatória de 32 bytes hex..."
    export REQUEST_STATE_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
fi

echo "[INFO] REQUEST_STATE_SECRET configurada."

# Função para iniciar o Servidor MCP (Porta 7301)
start_mcp() {
    echo "[INFO] Procurando ponto de entrada do Servidor MCP (Porta 7301)..."
    if [ -f "servidor-mcp/main.py" ]; then
        echo "[INFO] Iniciando Servidor MCP via Python (servidor-mcp/main.py)..."
        python3 servidor-mcp/main.py &
    elif [ -f "servidor-mcp/server.py" ]; then
        echo "[INFO] Iniciando Servidor MCP via Python (servidor-mcp/server.py)..."
        python3 servidor-mcp/server.py &
    elif [ -f "servidor-mcp/index.js" ]; then
        echo "[INFO] Iniciando Servidor MCP via Node.js (servidor-mcp/index.js)..."
        node servidor-mcp/index.js &
    elif [ -f "servidor-mcp/package.json" ]; then
        echo "[INFO] Iniciando Servidor MCP via npm (servidor-mcp)..."
        (cd servidor-mcp && npm start) &
    else
        echo "[WARN] Nenhum código de aplicação encontrado em servidor-mcp/. Aguardando implementação..."
    fi
}

# Função para iniciar o Agente A2A (Porta 7300)
start_agent() {
    echo "[INFO] Procurando ponto de entrada do Agente A2A (Porta 7300)..."
    if [ -f "agente/main.py" ]; then
        echo "[INFO] Iniciando Agente A2A via Python (agente/main.py)..."
        python3 agente/main.py &
    elif [ -f "agente/agent.py" ]; then
        echo "[INFO] Iniciando Agente A2A via Python (agente/agent.py)..."
        python3 agente/agent.py &
    elif [ -f "agente/index.js" ]; then
        echo "[INFO] Iniciando Agente A2A via Node.js (agente/index.js)..."
        node agente/index.js &
    elif [ -f "agente/package.json" ]; then
        echo "[INFO] Iniciando Agente A2A via npm (agente)..."
        (cd agente && npm start) &
    else
        echo "[WARN] Nenhum código de aplicação encontrado em agente/. Aguardando implementação..."
    fi
}

start_mcp
start_agent

echo "[INFO] Contêiner operacional nas portas 7300 (A2A) e 7301 (MCP)."
# Mantém o contêiner ativo
tail -f /dev/null
