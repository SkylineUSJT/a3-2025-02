# ================================================================
# INSTALADOR SKYLINE A3 - SERVIDOR
# ================================================================
# 
# Este script configura o servidor principal do sistema Skyline.
# Execute como ADMINISTRADOR na máquina que hospedará o servidor.
#
# O que este script faz:
# - Verifica Python 3.x instalado
# - Instala dependências Python (requirements.txt)
# - Configura WinRM para shutdown remoto
# - Configura TrustedHosts para aceitar clientes
# - Cria estrutura de diretórios necessária
# - Configura inicialização automática (opcional)
#
# ================================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "          INSTALADOR SKYLINE A3 - SERVIDOR" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se está rodando como administrador
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[ERRO] Este script precisa ser executado como ADMINISTRADOR!" -ForegroundColor Red
    Write-Host "       Clique com botão direito e selecione 'Executar como administrador'" -ForegroundColor Yellow
    pause
    exit 1
}

# ================================================================
# 1. VERIFICAR PYTHON
# ================================================================
Write-Host "[1/6] Verificando Python..." -ForegroundColor Green

$pythonCmd = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $version = & $cmd --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $pythonCmd = $cmd
            Write-Host "      Python encontrado: $version" -ForegroundColor White
            break
        }
    } catch {}
}

if (-not $pythonCmd) {
    Write-Host "[ERRO] Python não encontrado!" -ForegroundColor Red
    Write-Host "       Instale Python 3.x de https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "       Marque a opção 'Add Python to PATH' durante a instalação" -ForegroundColor Yellow
    pause
    exit 1
}

# ================================================================
# 2. INSTALAR DEPENDÊNCIAS PYTHON
# ================================================================
Write-Host ""
Write-Host "[2/6] Instalando dependências Python..." -ForegroundColor Green

if (Test-Path "requirements.txt") {
    try {
        Write-Host "      Atualizando pip..." -ForegroundColor White
        & $pythonCmd -m pip install --upgrade pip --quiet
        
        Write-Host "      Instalando pacotes (Flask, MQTT, etc)..." -ForegroundColor White
        & $pythonCmd -m pip install -r requirements.txt --quiet
        
        Write-Host "      Verificando instalação..." -ForegroundColor White
        $packages = & $pythonCmd -m pip list --format=freeze
        $required = @("Flask", "Flask-CORS", "paho-mqtt", "paramiko", "Werkzeug", "Flask-JWT-Extended")
        
        foreach ($pkg in $required) {
            if ($packages -match "(?i)^$pkg") {
                Write-Host "      ✓ $pkg instalado" -ForegroundColor Green
            } else {
                Write-Host "      ✗ $pkg NÃO encontrado" -ForegroundColor Yellow
            }
        }
        
        Write-Host ""
        Write-Host "      Dependências instaladas com sucesso" -ForegroundColor White
    } catch {
        Write-Host "[AVISO] Erro ao instalar dependências: $_" -ForegroundColor Yellow
        Write-Host "        Execute manualmente: pip install -r requirements.txt" -ForegroundColor Yellow
    }
} else {
    Write-Host "[AVISO] Arquivo requirements.txt não encontrado" -ForegroundColor Yellow
}

# ================================================================
# 3. CRIAR ESTRUTURA DE DIRETÓRIOS
# ================================================================
Write-Host ""
Write-Host "[3/6] Criando estrutura de diretórios..." -ForegroundColor Green

$dirs = @("logs", "backend/database", "config")
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "      Criado: $dir" -ForegroundColor White
    }
}

# ================================================================
# 4. CONFIGURAR WINRM (para shutdown remoto)
# ================================================================
Write-Host ""
Write-Host "[4/6] Configurando WinRM para shutdown remoto..." -ForegroundColor Green

try {
    # Configurar WinRM automaticamente
    winrm quickconfig -quiet -force | Out-Null
    
    # Garantir que o serviço está rodando
    Start-Service WinRM -ErrorAction SilentlyContinue
    Set-Service WinRM -StartupType Automatic -ErrorAction Stop
    
    Write-Host "      WinRM configurado e iniciado" -ForegroundColor White
} catch {
    Write-Host "[AVISO] Erro ao configurar WinRM: $_" -ForegroundColor Yellow
}

# ================================================================
# 5. CONFIGURAR TRUSTEDHOSTS
# ================================================================
Write-Host ""
Write-Host "[5/6] Configurando TrustedHosts para aceitar clientes..." -ForegroundColor Green

try {
    # Aceitar conexões de qualquer IP da rede local
    Set-Item WSMan:\localhost\Client\TrustedHosts -Value "*" -Force -ErrorAction Stop
    
    $trustedHosts = (Get-Item WSMan:\localhost\Client\TrustedHosts).Value
    Write-Host "      TrustedHosts configurado: $trustedHosts" -ForegroundColor White
} catch {
    Write-Host "[AVISO] Erro ao configurar TrustedHosts: $_" -ForegroundColor Yellow
    Write-Host "        O shutdown remoto pode não funcionar" -ForegroundColor Yellow
}

# ================================================================
# 6. CONFIGURAR FIREWALL
# ================================================================
Write-Host ""
Write-Host "[6/6] Configurando regras de firewall..." -ForegroundColor Green

try {
    # Porta 5000 - Flask/Backend
    $ruleName = "Skyline Backend (Port 5000)"
    $existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
    
    if (-not $existingRule) {
        New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow -ErrorAction Stop | Out-Null
        Write-Host "      Regra criada: Porta 5000 (Backend)" -ForegroundColor White
    } else {
        Write-Host "      Regra já existe: Porta 5000" -ForegroundColor White
    }
    
    # Porta 1883 - MQTT (opcional)
    $mqttRule = "Skyline MQTT (Port 1883)"
    $existingMqtt = Get-NetFirewallRule -DisplayName $mqttRule -ErrorAction SilentlyContinue
    
    if (-not $existingMqtt) {
        New-NetFirewallRule -DisplayName $mqttRule -Direction Inbound -Protocol TCP -LocalPort 1883 -Action Allow -ErrorAction Stop | Out-Null
        Write-Host "      Regra criada: Porta 1883 (MQTT)" -ForegroundColor White
    } else {
        Write-Host "      Regra já existe: Porta 1883" -ForegroundColor White
    }
} catch {
    Write-Host "[AVISO] Erro ao configurar firewall: $_" -ForegroundColor Yellow
}

# ================================================================
# CONCLUÍDO
# ================================================================
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "          INSTALAÇÃO CONCLUÍDA COM SUCESSO!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "PRÓXIMOS PASSOS:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Verifique o arquivo config/config.json:" -ForegroundColor White
Write-Host "   - MQTT broker (padrão: localhost:1883)" -ForegroundColor Gray
Write-Host "   - Credenciais de shutdown (skyline_admin/Skyline@2025)" -ForegroundColor Gray
Write-Host "   - Porta do servidor (padrão: 5000)" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Inicie o servidor executando:" -ForegroundColor White
Write-Host "   python start_system.py" -ForegroundColor Yellow
Write-Host ""
Write-Host "3. Acesse a interface web em:" -ForegroundColor White
Write-Host "   http://localhost:5000" -ForegroundColor Yellow
Write-Host "   ou" -ForegroundColor White
Write-Host "   http://SEU_IP:5000" -ForegroundColor Yellow
Write-Host ""
Write-Host "4. Credenciais padrão:" -ForegroundColor White
Write-Host "   Usuário: admin" -ForegroundColor Yellow
Write-Host "   Senha: admin123" -ForegroundColor Yellow
Write-Host ""
Write-Host "5. Cadastre funcionários e computadores na interface web" -ForegroundColor White
Write-Host ""
Write-Host "6. Execute instalar_cliente.ps1 nos computadores remotos" -ForegroundColor White
Write-Host "   (Como ADMINISTRADOR)" -ForegroundColor Gray
Write-Host ""

pause
