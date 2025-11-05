# Script para instalar o Chocolatey
# Execute este script como Administrador

Write-Host "Instalando Chocolatey..." -ForegroundColor Green

# Remove instalação anterior se existir
if (Test-Path 'C:\ProgramData\chocolatey') {
    Write-Host "Removendo instalação anterior do Chocolatey..." -ForegroundColor Yellow
    Remove-Item -Path 'C:\ProgramData\chocolatey' -Recurse -Force -ErrorAction SilentlyContinue
}

# Configura a política de execução
Set-ExecutionPolicy Bypass -Scope Process -Force

# Configura o protocolo de segurança
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072

# Instala o Chocolatey
Write-Host "Baixando e instalando Chocolatey..." -ForegroundColor Green
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Atualiza o PATH do ambiente
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Verifica a instalação
if (Get-Command choco -ErrorAction SilentlyContinue) {
    Write-Host "Chocolatey instalado com sucesso!" -ForegroundColor Green
    choco --version
} else {
    Write-Host "A instalação pode ter sido concluída. Por favor, feche e reabra o terminal e tente novamente." -ForegroundColor Yellow
    Write-Host "Ou execute: refreshenv" -ForegroundColor Yellow
}

