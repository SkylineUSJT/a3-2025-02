# Instalador automático para configuração do shutdown remoto e registro do PC no backend
# Execute este script como administrador

# 1. Ativar o serviço LanmanServer
Write-Host "[Skyline] Ativando serviço LanmanServer (Server)..."
$service = Get-Service -Name 'LanmanServer' -ErrorAction SilentlyContinue
if ($service -eq $null) {
    Write-Host "[Skyline] Serviço LanmanServer não encontrado! Verifique a versão do Windows." -ForegroundColor Red
    exit 1
}
if ($service.Status -ne 'Running') {
    Start-Service -Name 'LanmanServer'
    Set-Service -Name 'LanmanServer' -StartupType Automatic
    Write-Host "[Skyline] LanmanServer ativado."
} else {
    Write-Host "[Skyline] LanmanServer já está ativo."
}

# 2. Criar regra de firewall para shutdown remoto
Write-Host "[Skyline] Configurando firewall para shutdown remoto..."
$rule = Get-NetFirewallRule -DisplayName 'Permitir shutdown remoto Skyline' -ErrorAction SilentlyContinue
if ($rule -eq $null) {
    New-NetFirewallRule -DisplayName 'Permitir shutdown remoto Skyline' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 445
    Write-Host "[Skyline] Regra de firewall criada."
} else {
    Write-Host "[Skyline] Regra de firewall já existe."
}


# 3. Coletar informações do PC (hostname, IP, usuário, MAC)
$hostname = $env:COMPUTERNAME
$ipObj = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike '*Loopback*' -and $_.IPAddress -notlike '169.*' } | Select-Object -First 1
$ip = $ipObj.IPAddress
$user = $env:USERNAME
# Tentar obter o MAC address da interface do IP principal
$mac = $null
if ($ipObj -and $ipObj.InterfaceIndex) {
    $adapter = Get-NetAdapter | Where-Object { $_.InterfaceIndex -eq $ipObj.InterfaceIndex }
    if ($adapter) { $mac = $adapter.MacAddress }
}
if (-not $mac) {
    # fallback: primeiro MAC válido
    $mac = (Get-NetAdapter | Where-Object { $_.Status -eq 'Up' } | Select-Object -First 1 -ExpandProperty MacAddress)
}

Write-Host "[Skyline] Informações coletadas:"
Write-Host "  Hostname: $hostname"
Write-Host "  IP: $ip"
Write-Host "  Usuário: $user"
Write-Host "  MAC: $mac"


# 4. Enviar informações para o backend
$backendUrl = "http://SEU_BACKEND:5000/api/devices"  # Substitua pelo endereço correto
$body = @{ hostname = $hostname; ip = $ip; user = $user; mac_address = $mac } | ConvertTo-Json
try {
    $response = Invoke-RestMethod -Uri $backendUrl -Method Post -Body $body -ContentType 'application/json'
    Write-Host "[Skyline] Registro enviado ao backend com sucesso!"
    Write-Host $response
} catch {
    Write-Host "[Skyline] Falha ao registrar no backend: $_" -ForegroundColor Red
}

Write-Host "[Skyline] Instalação concluída. O PC está pronto para shutdown remoto!" -ForegroundColor Green
