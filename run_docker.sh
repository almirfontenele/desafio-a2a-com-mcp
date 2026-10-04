#!/usr/bin/env bash
set -e

echo "==================================================="
echo "  A Ponte: Agente A2A com MCP por dentro (Docker)  "
echo "==================================================="

# Valida ou gera a chave REQUEST_STATE_SECRET caso não exista no ambiente
if [ -z "$REQUEST_STATE_SECRET" ]; then
    echo "[INFO] REQUEST_STATE_SECRET não definida. Gerando nova chave..."
    export REQUEST_STATE_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || openssl rand -hex 32)
fi

echo "[INFO] Utilizando REQUEST_STATE_SECRET=${REQUEST_STATE_SECRET:0:16}..."

echo "[INFO] Construindo imagem Docker..."
docker build -t desafio-a2a-mcp .

echo "[INFO] Subindo contêiner Docker nas portas 7300 (A2A) e 7301 (MCP)..."
docker run --rm -it \
    -p 7300:7300 \
    -p 7301:7301 \
    -e REQUEST_STATE_SECRET="$REQUEST_STATE_SECRET" \
    -v "$(pwd):/app" \
    --name desafio-a2a-mcp-container \
    desafio-a2a-mcp
