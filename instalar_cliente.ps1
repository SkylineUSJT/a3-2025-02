# ================================================================
# INSTALADOR SKYLINE A3 - CLIENTE
# ================================================================
# 
# Este script configura uma máquina cliente para ser gerenciada
# pelo sistema Skyline (shutdown remoto e Wake-on-LAN).
#
# INSTRUÇÕES:
# 1. Edite a linha 100 com o IP correto do servidor
# 2. Execute como ADMINISTRADOR em cada máquina cliente
# 3. Quando solicitado, informe o RFID do funcionário
#
# IMPORTANTE - Wake-on-LAN:
# Após executar este script, configure na BIOS/UEFI:
# - Wake on LAN / Power On by PCI-E: ENABLED
# - ErP Support: DISABLED
# (Consulte CONFIGURACAO_WAKE_ON_LAN.txt para detalhes)
#
# ================================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "          INSTALADOR SKYLINE A3 - CLIENTE" -ForegroundColor Cyan
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

Write-Host "[Cliente] Iniciando configuração..." -ForegroundColor Green
Write-Host ""

# ================================================================
# 1. CONFIGURAR SERVIÇOS DE REDE
# ================================================================

# 1.1. Ativar o serviço LanmanServer
Write-Host "[1/7] Ativando serviço LanmanServer..." -ForegroundColor Green
$service = Get-Service -Name 'LanmanServer' -ErrorAction SilentlyContinue
if ($service -eq $null) {
    Write-Host "      [ERRO] Serviço LanmanServer não encontrado!" -ForegroundColor Red
    exit 1
}
if ($service.Status -ne 'Running') {
    Start-Service -Name 'LanmanServer'
    Set-Service -Name 'LanmanServer' -StartupType Automatic
    Write-Host "      LanmanServer ativado" -ForegroundColor White
} else {
    Write-Host "      LanmanServer já está ativo" -ForegroundColor White
}

# 1.2. Criar regra de firewall para shutdown remoto
Write-Host ""
Write-Host "[2/7] Configurando firewall..." -ForegroundColor Green
$rule = Get-NetFirewallRule -DisplayName 'Skyline - Shutdown Remoto' -ErrorAction SilentlyContinue
if ($rule -eq $null) {
    New-NetFirewallRule -DisplayName 'Skyline - Shutdown Remoto' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 445 | Out-Null
    Write-Host "      Regra de firewall criada" -ForegroundColor White
} else {
    Write-Host "      Regra de firewall já existe" -ForegroundColor White
}

# ================================================================
# 2. CONFIGURAR REDE E COMPARTILHAMENTO
# ================================================================

Write-Host ""
Write-Host "[3/7] Configurando rede e compartilhamento..." -ForegroundColor Green
try {
    # Configurar rede como Privada
    Set-NetConnectionProfile -NetworkCategory Private -ErrorAction SilentlyContinue
    
    # Habilitar descoberta de rede
    Set-NetFirewallRule -DisplayGroup "Descoberta de Rede" -Enabled True -Profile Private -ErrorAction SilentlyContinue
    
    # Habilitar compartilhamento de arquivos
    Set-NetFirewallRule -DisplayGroup "Compartilhamento de Arquivo e Impressora" -Enabled True -Profile Private -ErrorAction SilentlyContinue
    
    Write-Host "      Descoberta de rede habilitada" -ForegroundColor White
} catch {
    Write-Host "      [AVISO] Configure manualmente no Painel de Controle" -ForegroundColor Yellow
}

# Habilitar compartilhamentos administrativos
try {
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters" -Name "AutoShareWks" -Value 1 -ErrorAction Stop
    Write-Host "      Compartilhamentos administrativos habilitados" -ForegroundColor White
} catch {
    Write-Host "      [AVISO] Erro ao habilitar compartilhamentos" -ForegroundColor Yellow
}

# ================================================================
# 3. CONFIGURAR POWERSHELL REMOTING
# ================================================================

Write-Host ""
Write-Host "[4/7] Configurando PowerShell Remoting..." -ForegroundColor Green
try {
    # Habilitar PSRemoting
    Enable-PSRemoting -Force -SkipNetworkProfileCheck -ErrorAction Stop
    
    # Configurar WinRM para aceitar conexões
    Set-Item WSMan:\localhost\Client\TrustedHosts -Value "*" -Force -ErrorAction Stop
    
    # Reiniciar serviço WinRM
    Restart-Service WinRM -Force -ErrorAction Stop
    
    Write-Host "      PowerShell Remoting configurado" -ForegroundColor White
} catch {
    Write-Host "      [AVISO] Execute manualmente: Enable-PSRemoting -Force" -ForegroundColor Yellow
}

# ================================================================
# 4. CONFIGURAR WAKE-ON-LAN
# ================================================================

Write-Host ""
Write-Host "[5/7] Configurando Wake-on-LAN..." -ForegroundColor Green
try {
    # Encontrar adaptador de rede ethernet ativo
    $adapters = Get-NetAdapter | Where-Object { $_.Status -eq 'Up' -and $_.PhysicalMediaType -match 'Ethernet|802.3' }
    
    if ($adapters) {
        foreach ($adapter in $adapters) {
            # Habilitar Wake on Magic Packet via registro
            $regPath = "HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4D36E972-E325-11CE-BFC1-08002bE10318}"
            $subKeys = Get-ChildItem $regPath -ErrorAction SilentlyContinue
            
            foreach ($subKey in $subKeys) {
                $driverDesc = (Get-ItemProperty -Path $subKey.PSPath -Name "DriverDesc" -ErrorAction SilentlyContinue).DriverDesc
                if ($driverDesc -eq $adapter.InterfaceDescription) {
                    Set-ItemProperty -Path $subKey.PSPath -Name "*WakeOnMagicPacket" -Value "1" -ErrorAction SilentlyContinue
                    Set-ItemProperty -Path $subKey.PSPath -Name "WakeOnMagicPacket" -Value "1" -ErrorAction SilentlyContinue
                    Set-ItemProperty -Path $subKey.PSPath -Name "*WakeOnPattern" -Value "1" -ErrorAction SilentlyContinue
                    break
                }
            }
        }
        Write-Host "      Wake-on-LAN configurado no Windows" -ForegroundColor White
        Write-Host "      [!] Configure TAMBEM na BIOS: Wake on LAN = Enabled" -ForegroundColor Yellow
    } else {
        Write-Host "      [AVISO] Nenhum adaptador ethernet encontrado" -ForegroundColor Yellow
    }
} catch {
    Write-Host "      [AVISO] Erro ao configurar: $_" -ForegroundColor Yellow
}

# ================================================================
# 5. CRIAR USUARIO ADMINISTRATIVO
# ================================================================

Write-Host ""
Write-Host "[6/7] Criando usuário administrativo..." -ForegroundColor Green
$adminUser = "skyline_admin"
$adminPass = "Skyline@2025"
try {
    # Verificar se usuário já existe
    $userExists = Get-LocalUser -Name $adminUser -ErrorAction SilentlyContinue
    if (-not $userExists) {
        $securePass = ConvertTo-SecureString $adminPass -AsPlainText -Force
        New-LocalUser -Name $adminUser -Password $securePass -Description "Usuario para shutdown remoto Skyline" -PasswordNeverExpires -ErrorAction Stop
        Add-LocalGroupMember -Group "Administradores" -Member $adminUser -ErrorAction Stop
        Write-Host "[Skyline] Usuário administrativo criado: $adminUser" -ForegroundColor Green
        Write-Host "  (Senha: $adminPass)" -ForegroundColor Yellow
    } else {
        Write-Host "[Skyline] Usuário $adminUser já existe."
    }
    
    # Conceder permissão de shutdown remoto via política de segurança
    Write-Host "[Skyline] Configurando permissões de shutdown remoto..."
    
    # Usar secedit para exportar política atual
    $tempSecPol = "$env:TEMP\secpol.cfg"
    $tempNewSecPol = "$env:TEMP\newsecpol.cfg"
    
    secedit /export /cfg $tempSecPol /quiet
    
    # Ler arquivo e adicionar permissão se não existir
    $content = Get-Content $tempSecPol
    $newContent = @()
    $found = $false
    
    foreach ($line in $content) {
        if ($line -match '^SeRemoteShutdownPrivilege = ') {
            if ($line -notmatch $adminUser) {
                # Adicionar usuário à linha existente
                $line = $line.TrimEnd() + ",*S-1-5-21-$adminUser"
                $found = $true
            }
        }
        $newContent += $line
    }
    
    # Se não achou a linha, adicionar na seção [Privilege Rights]
    if (-not $found) {
        for ($i = 0; $i -lt $newContent.Count; $i++) {
            if ($newContent[$i] -match '\[Privilege Rights\]') {
                $newContent = $newContent[0..$i] + "SeRemoteShutdownPrivilege = *S-1-5-32-544,*S-1-5-32-551,$adminUser" + $newContent[($i+1)..($newContent.Count-1)]
                break
            }
        }
    }
    
    # Salvar e aplicar
    $newContent | Set-Content $tempNewSecPol
    secedit /configure /db secedit.sdb /cfg $tempNewSecPol /quiet
    
    # Limpar arquivos temporários
    Remove-Item $tempSecPol, $tempNewSecPol -Force -ErrorAction SilentlyContinue
    
    Write-Host "[Skyline] Permissões configuradas com sucesso." -ForegroundColor Green
    
} catch {
    Write-Host "[Skyline] Aviso: Erro ao criar usuário administrativo: $_" -ForegroundColor Yellow
    Write-Host "  O shutdown remoto pode não funcionar sem credenciais adequadas." -ForegroundColor Yellow
}


# 3. Coletar informações do PC (hostname, IP, MAC)
$hostname = $env:COMPUTERNAME
$ipObj = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike '*Loopback*' -and $_.IPAddress -notlike '169.*' } | Select-Object -First 1
$ip = $ipObj.IPAddress

# ================================================================
# 6. COLETAR INFORMAÇÕES E REGISTRAR NO SERVIDOR
# ================================================================

Write-Host ""
Write-Host "[7/7] Registrando computador no servidor..." -ForegroundColor Green

# Coletar informações do sistema
$hostname = $env:COMPUTERNAME
$ipObj = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notmatch '^169\.|^127\.' } | Select-Object -First 1
$ip = if ($ipObj) { $ipObj.IPAddress } else { "0.0.0.0" }

# Obter MAC address
$mac = $null
if ($ipObj -and $ipObj.InterfaceIndex) {
    $adapter = Get-NetAdapter | Where-Object { $_.InterfaceIndex -eq $ipObj.InterfaceIndex }
    if ($adapter) { $mac = $adapter.MacAddress }
}
if (-not $mac) {
    $mac = (Get-NetAdapter | Where-Object { $_.Status -eq 'Up' } | Select-Object -First 1 -ExpandProperty MacAddress)
}

# Converter MAC para formato padrão (AA:BB:CC:DD:EE:FF)
if ($mac) {
    $mac = $mac.Replace('-', ':')
}

Write-Host ""
Write-Host "      Hostname: $hostname" -ForegroundColor White
Write-Host "      IP: $ip" -ForegroundColor White
Write-Host "      MAC: $mac" -ForegroundColor White
Write-Host ""

# Solicitar RFID do funcionário
Write-Host "      Digite o RFID do funcionário que usará este PC:" -ForegroundColor Yellow
$rfid = Read-Host "      RFID"
if (-not $rfid -or $rfid.Trim() -eq '') {
    Write-Host ""
    Write-Host "[ERRO] RFID é obrigatório!" -ForegroundColor Red
    pause
    exit 1
}

# Configurar endereço do servidor
Write-Host ""
Write-Host "      Digite o IP do servidor Skyline:" -ForegroundColor Yellow
Write-Host "      (Exemplo: 192.168.18.2)" -ForegroundColor Gray
$serverIp = Read-Host "      IP do Servidor"
if (-not $serverIp) {
    Write-Host ""
    Write-Host "[ERRO] IP do servidor é obrigatório!" -ForegroundColor Red
    pause
    exit 1
}

$backendUrl = "http://${serverIp}:5000/api/devices"

# Enviar dados para o backend
Write-Host ""
Write-Host "      Enviando dados para: $backendUrl" -ForegroundColor Cyan

$body = @{ 
    hostname = $hostname
    ip_address = $ip
    user_id = $rfid
    mac_address = $mac
    os_type = "windows"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri $backendUrl -Method Post -Body $body -ContentType 'application/json' -TimeoutSec 10
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "          INSTALAÇÃO CONCLUÍDA COM SUCESSO!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Computador registrado:" -ForegroundColor White
    Write-Host "  - Device ID: $($response.device_id)" -ForegroundColor Cyan
    Write-Host "  - Hostname: $hostname" -ForegroundColor Cyan
    Write-Host "  - Usuário (RFID): $rfid" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "LEMBRE-SE:" -ForegroundColor Yellow
    Write-Host "  Configure Wake-on-LAN na BIOS/UEFI" -ForegroundColor White
    Write-Host "  (Consulte CONFIGURACAO_WAKE_ON_LAN.txt)" -ForegroundColor White
    Write-Host ""
} catch {
    Write-Host ""
    Write-Host "[ERRO] Falha ao registrar no servidor!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Verifique:" -ForegroundColor Yellow
    Write-Host "  1. Servidor rodando em: $backendUrl" -ForegroundColor White
    Write-Host "  2. RFID '$rfid' existe no banco de dados" -ForegroundColor White
    Write-Host "  3. Rede permite conexão na porta 5000" -ForegroundColor White
    Write-Host ""
    Write-Host "Erro: $_" -ForegroundColor Red
    Write-Host ""
    pause
    exit 1
}
