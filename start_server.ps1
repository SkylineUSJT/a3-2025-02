# Script para iniciar o servidor Skyline A3
# Usage: .\start_server.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Sistema Skyline A3 - IoT Automation  " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se esta no diretorio correto
if (-not (Test-Path "backend\app.py")) {
    Write-Host "Erro: Execute este script na raiz do projeto Skyline_A3" -ForegroundColor Red
    exit 1
}

# Verificar se o ambiente virtual existe
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "Ativando ambiente virtual..." -ForegroundColor Yellow
    & .\.venv\Scripts\Activate.ps1
} else {
    Write-Host "Ambiente virtual nao encontrado" -ForegroundColor Yellow
    Write-Host "   Continuando com Python global..." -ForegroundColor Yellow
}

# Verificar dependencias
Write-Host ""
Write-Host "Verificando dependencias..." -ForegroundColor Yellow
$modules = @("flask", "paho.mqtt", "flask_jwt_extended")
$missing = @()

foreach ($module in $modules) {
    try {
        python -c "import $($module.Replace('.', '_'))" 2>$null
        if ($LASTEXITCODE -ne 0) {
            $missing += $module
        }
    } catch {
        $missing += $module
    }
}

if ($missing.Count -gt 0) {
    Write-Host "Modulos faltando: $($missing -join ', ')" -ForegroundColor Red
    Write-Host ""
    $install = Read-Host "Deseja instalar as dependencias agora? (s/n)"
    if ($install -eq 's' -or $install -eq 'S') {
        Write-Host "Instalando dependencias..." -ForegroundColor Yellow
        python -m pip install -r requirements.txt
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Erro ao instalar dependencias" -ForegroundColor Red
            exit 1
        }
        Write-Host "Dependencias instaladas com sucesso!" -ForegroundColor Green
    } else {
        Write-Host "Nao e possivel continuar sem as dependencias" -ForegroundColor Red
        exit 1
    }
}

# Criar diretorios necessarios
Write-Host ""
Write-Host "Verificando estrutura de diretorios..." -ForegroundColor Yellow

$dirs = @("logs", "backend\database", "frontend")
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "   Criado: $dir" -ForegroundColor Green
    }
}

# Exibir informacoes
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Informacoes do Sistema" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "URL Frontend:  http://localhost:5000" -ForegroundColor Green
Write-Host "API Backend:   http://localhost:5000/api" -ForegroundColor Green
Write-Host "Health Check:  http://localhost:5000/api/health" -ForegroundColor Green
Write-Host ""
Write-Host "Logs serao salvos em: logs\app.log" -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Iniciar servidor
Write-Host "Iniciando servidor..." -ForegroundColor Green
Write-Host ""
Write-Host "Pressione Ctrl+C para parar o servidor" -ForegroundColor Yellow
Write-Host ""

try {
    python backend\app.py
} catch {
    Write-Host ""
    Write-Host "Erro ao iniciar o servidor" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Servidor finalizado" -ForegroundColor Yellow
