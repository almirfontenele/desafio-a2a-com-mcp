# Dockerfile para ambiente de execução local: Servidor MCP e Agente A2A
FROM python:3.11-slim

# Diretório de trabalho
WORKDIR /app

# Instalação de dependências do sistema e Node.js 20 (suporte híbrido Python/Node.js)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list \
    && apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copia os arquivos do repositório para a imagem
COPY . /app

# Instala dependências declaradas com versões pinadas no pyproject.toml
RUN pip install --no-cache-dir .

# Exposição das portas 7300 (Agente A2A) e 7301 (Servidor MCP)
EXPOSE 7300 7301

# Variáveis de ambiente padrão
ENV PORT_AGENT=7300
ENV PORT_MCP=7301
ENV REQUEST_STATE_SECRET=""

# Torna o script de inicialização executável
RUN chmod +x /app/start.sh

# Comando de inicialização do contêiner
CMD ["/app/start.sh"]
