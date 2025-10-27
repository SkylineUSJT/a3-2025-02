# 🌟 Sistema Skyline A3 - IoT de Automação de Energia

Sistema completo de automação IoT que integra catracas de acesso com computadores, permitindo ligar/desligar automaticamente via Wake-on-LAN e shutdown remoto.

## 📋 Índice

- [Características](#características)
- [Tecnologias](#tecnologias)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Uso](#uso)
- [Arquitetura](#arquitetura)
- [API](#api)
- [Segurança](#segurança)
- [Troubleshooting](#troubleshooting)

## ✨ Características

- 🖥️ **Gerenciamento de Dispositivos**: Cadastro e controle de computadores
- ⚡ **Wake-on-LAN**: Liga computadores remotamente via pacote mágico
- 🔌 **Shutdown Remoto**: Desliga computadores Windows/Linux remotamente
- 🚪 **Integração MQTT**: Comunicação em tempo real com catracas
- 📊 **Dashboard Web**: Interface moderna e responsiva
- 🔐 **Autenticação JWT**: Segurança nas APIs
- 📝 **Logs Detalhados**: Histórico completo de acessos
- 🗄️ **Banco SQLite**: Armazenamento local eficiente

## 🛠️ Tecnologias

### Backend
- Python 3.8+
- Flask (servidor web)
- SQLite (banco de dados)
- Paho-MQTT (comunicação)
- Paramiko (SSH para Linux)
- Flask-JWT-Extended (autenticação)

### Frontend
- HTML5/CSS3
- JavaScript ES6+
- Font Awesome (ícones)
- Fetch API (requisições)

## 📦 Pré-requisitos

- Python 3.8 ou superior
- Mosquitto MQTT Broker (para testes locais)
- PsExec (opcional, para shutdown Windows)
- Rede local configurada

## 🚀 Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/SrGoes/a3-2025-02.git
cd a3-2025-02
```

### 2. Crie um ambiente virtual

```bash
python -m venv .venv
```

### 3. Ative o ambiente virtual

**Windows:**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
source .venv/bin/activate
```

### 4. Instale as dependências

```bash
pip install -r requirements.txt
```

### 5. Configure o ambiente

```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

## ⚙️ Configuração

### Backend

Edite `config/config.json` ou use variáveis de ambiente:

```json
{
  "mqtt": {
    "broker": "localhost",
    "port": 1883,
    "topic": "catraca/acesso"
  },
  "wake_on_lan": {
    "broadcast_ip": "255.255.255.255",
    "port": 9
  }
}
```

### MQTT Broker

Instale e inicie o Mosquitto:

```bash
# Windows
choco install mosquitto
net start mosquitto

# Linux
sudo apt install mosquitto mosquitto-clients
sudo systemctl start mosquitto
```

## 🎮 Uso

### Iniciar o servidor

**Windows:**
```powershell
.\start_server.ps1
```

**Manual:**
```bash
python backend/app.py
```

### Acessar o sistema

Abra o navegador em: **http://localhost:5000**

**Credenciais padrão (desenvolvimento):**
- Usuário: qualquer
- Senha: mínimo 3 caracteres

### Simular catraca

```bash
# Simular entrada
python simulador_catraca.py entrada FUNC001

# Simular saída
python simulador_catraca.py saida FUNC001

# Simular dia completo
python simulador_catraca.py dia
```

### Testar API

```bash
python test_sistema.py
```

## 🏗️ Arquitetura

```
┌─────────────┐     MQTT      ┌──────────────┐
│   Catraca   │ ────────────> │   Backend    │
└─────────────┘               │   (Flask)    │
                              └──────┬───────┘
                                     │
                   ┌─────────────────┼─────────────────┐
                   │                 │                 │
              ┌────▼────┐      ┌────▼────┐      ┌────▼────┐
              │   WOL   │      │Shutdown │      │Database │
              │ Module  │      │ Module  │      │ SQLite  │
              └────┬────┘      └────┬────┘      └─────────┘
                   │                │
              ┌────▼────────────────▼────┐
              │   Computadores Alvo     │
              └─────────────────────────┘
```

## 🔌 API Endpoints

### Autenticação
- `POST /api/auth/login` - Login

### Dispositivos
- `GET /api/devices` - Listar dispositivos
- `POST /api/devices` - Cadastrar dispositivo
- `POST /api/devices/{id}/wake` - Ligar dispositivo
- `POST /api/devices/{id}/shutdown` - Desligar dispositivo
- `DELETE /api/devices/{id}` - Excluir dispositivo

### Acessos
- `POST /api/access/entry` - Registrar entrada
- `POST /api/access/exit` - Registrar saída

### Logs
- `GET /api/logs` - Buscar logs

### Catracas
- `GET /api/turnstiles` - Listar catracas
- `POST /api/turnstiles` - Adicionar catraca
- `DELETE /api/turnstiles/{id}` - Excluir catraca

## 🔐 Segurança

### ⚠️ IMPORTANTE - Antes de usar em produção:

1. **Altere a chave JWT**:
```bash
export JWT_SECRET_KEY="sua-chave-super-secreta-aqui"
```

2. **Implemente autenticação real**:
   - Substitua a autenticação placeholder
   - Use banco de dados ou LDAP
   - Adicione hash de senhas (bcrypt)

3. **Configure HTTPS**:
   - Use certificados SSL/TLS
   - Configure proxy reverso (nginx)

4. **Restrinja acesso**:
   - Configure firewall
   - Use VPN se necessário
   - Limite IPs permitidos

## 🐛 Troubleshooting

### Erro: "flask_cors not found"
```bash
pip install Flask-CORS
```

### Wake-on-LAN não funciona
- Verifique se WOL está habilitado na BIOS
- Confirme o endereço MAC correto
- Teste na mesma rede local

### Shutdown remoto falha
- Verifique credenciais
- Habilite compartilhamento (Windows)
- Configure sudoers (Linux)

### MQTT não conecta
```bash
# Teste o broker
mosquitto_sub -h localhost -t "#" -v
```

## 📄 Licença

Este projeto foi desenvolvido para fins acadêmicos - A3 2025.

## 👥 Contribuidores

- Desenvolvido pela equipe Skyline A3

## 📞 Suporte

Para dúvidas e problemas, abra uma issue no GitHub.
