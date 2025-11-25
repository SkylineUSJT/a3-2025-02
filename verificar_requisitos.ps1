# ================================================================
# VERIFICADOR DE REQUISITOS - SKYLINE A3
# ================================================================
# Script para verificar se todos os requisitos estão instalados
# Execute ANTES de iniciar o servidor
# ================================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "     VERIFICADOR DE REQUISITOS - SKYLINE A3" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$allOk = $true

# ================================================================
# 1. VERIFICAR PYTHON
# ================================================================
Write-Host "[1/5] Verificando Python..." -ForegroundColor Green

$pythonCmd = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $version = & $cmd --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $pythonCmd = $cmd
            Write-Host "      ✓ Python encontrado: $version" -ForegroundColor White
            break
        }
    } catch {}
}

if (-not $pythonCmd) {
    Write-Host "      ✗ Python NÃO encontrado!" -ForegroundColor Red
    Write-Host "        Instale de: https://www.python.org/downloads/" -ForegroundColor Yellow
    $allOk = $false
}

# ================================================================
# 2. VERIFICAR PACOTES PYTHON
# ================================================================
Write-Host ""
Write-Host "[2/5] Verificando pacotes Python..." -ForegroundColor Green

if ($pythonCmd) {
    $required = @(
        "Flask",
        "Flask-CORS", 
        "paho-mqtt",
        "paramiko",
        "Werkzeug",
        "Flask-JWT-Extended"
    )
    
    $packages = & $pythonCmd -m pip list --format=freeze 2>&1
    
    foreach ($pkg in $required) {
        if ($packages -match "(?i)^$pkg") {
            Write-Host "      ✓ $pkg instalado" -ForegroundColor White
        } else {
            Write-Host "      ✗ $pkg NÃO instalado" -ForegroundColor Red
            $allOk = $false
        }
    }
    
    if (-not $allOk) {
        Write-Host ""
        Write-Host "      Execute: pip install -r requirements.txt" -ForegroundColor Yellow
    }
}

# ================================================================
# 3. VERIFICAR ARQUIVOS DO PROJETO
# ================================================================
Write-Host ""
Write-Host "[3/5] Verificando arquivos do projeto..." -ForegroundColor Green

$files = @(
    "backend/app.py",
    "backend/modules/database.py",
    "backend/modules/mqtt_client.py",
    "backend/modules/shutdown.py",
    "backend/modules/wol.py",
    "config/config.json",
    "start_system.py",
    "requirements.txt"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "      ✓ $file" -ForegroundColor White
    } else {
        Write-Host "      ✗ $file FALTANDO" -ForegroundColor Red
        $allOk = $false
    }
}

# ================================================================
# 4. VERIFICAR DIRETÓRIOS
# ================================================================
Write-Host ""
Write-Host "[4/5] Verificando diretórios..." -ForegroundColor Green

$dirs = @("logs", "backend/database", "config")
foreach ($dir in $dirs) {
    if (Test-Path $dir) {
        Write-Host "      ✓ $dir" -ForegroundColor White
    } else {
        Write-Host "      ⚠ $dir não existe (será criado automaticamente)" -ForegroundColor Yellow
    }
}

# ================================================================
# 5. VERIFICAR CONFIGURAÇÃO
# ================================================================
Write-Host ""
Write-Host "[5/5] Verificando configuração..." -ForegroundColor Green

if (Test-Path "config/config.json") {
    try {
        $config = Get-Content "config/config.json" -Raw | ConvertFrom-Json
        
        # MQTT
        $mqttBroker = $config.mqtt.broker
        $mqttPort = $config.mqtt.port
        Write-Host "      ✓ MQTT: $mqttBroker:$mqttPort" -ForegroundColor White
        
        # Wake-on-LAN
        $wolBroadcast = $config.wake_on_lan.broadcast_ip
        $wolPort = $config.wake_on_lan.port
        Write-Host "      ✓ WOL: $wolBroadcast:$wolPort" -ForegroundColor White
        
        # Shutdown
        $shutdownUser = $config.shutdown.admin_username
        Write-Host "      ✓ Shutdown User: $shutdownUser" -ForegroundColor White
        
        # Server
        $serverHost = $config.server.host
        $serverPort = $config.server.port
        Write-Host "      ✓ Server: $serverHost:$serverPort" -ForegroundColor White
        
    } catch {
        Write-Host "      ✗ Erro ao ler config.json: $_" -ForegroundColor Red
        $allOk = $false
    }
} else {
    Write-Host "      ✗ config/config.json não encontrado" -ForegroundColor Red
    $allOk = $false
}

# ================================================================
# RESULTADO FINAL
# ================================================================
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan

if ($allOk) {
    Write-Host "          ✓ TODOS OS REQUISITOS ATENDIDOS!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Você pode iniciar o servidor:" -ForegroundColor White
    Write-Host "  python start_system.py" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host "          ✗ ALGUNS REQUISITOS FALTANDO" -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Corrija os problemas acima antes de iniciar o servidor" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Para instalar dependências Python:" -ForegroundColor White
    Write-Host "  pip install -r requirements.txt" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Para configurar o servidor:" -ForegroundColor White
    Write-Host "  Execute: instalar_servidor.ps1" -ForegroundColor Yellow
    Write-Host ""
}

pause
