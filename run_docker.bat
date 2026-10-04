@echo off
SETLOCAL EnableDelayedExpansion

echo ===================================================
echo   A Ponte: Agente A2A com MCP por dentro (Docker)
echo ===================================================

rem Verifica se a variavel REQUEST_STATE_SECRET foi definida
IF "%REQUEST_STATE_SECRET%"=="" (
    echo [INFO] REQUEST_STATE_SECRET nao encontrada. Gerando segredo temporario de 32 bytes...
    for /f "delims=" %%i in ('python -c "import secrets; print(secrets.token_hex(32))" 2^>nul') do set "REQUEST_STATE_SECRET=%%i"
)

IF "%REQUEST_STATE_SECRET%"=="" (
    set "REQUEST_STATE_SECRET=4b9f2d1e8c7a6b5a4f3e2d1c0b9a8f7e6d5c4b3a2f1e0d9c8b7a6f5e4d3c2b1a"
)

echo [INFO] Utilizando REQUEST_STATE_SECRET=%REQUEST_STATE_SECRET:~0,16%...

echo [INFO] Construindo a imagem Docker...
docker build -t desafio-a2a-mcp .

IF %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Falha ao construir a imagem Docker. Verifique se o Docker Daemon esta em execucao.
    pause
    exit /b %ERRORLEVEL%
)

echo [INFO] Executando o conteiner Docker (Mapeando portas 7300 e 7301)...
docker run --rm -it ^
    -p 7300:7300 ^
    -p 7301:7301 ^
    -e REQUEST_STATE_SECRET=%REQUEST_STATE_SECRET% ^
    -v "%CD%:/app" ^
    --name desafio-a2a-mcp-container ^
    desafio-a2a-mcp

ENDLOCAL
