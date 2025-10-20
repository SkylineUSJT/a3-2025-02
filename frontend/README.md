# Frontend - Sistema Skyline A3

## 📋 Descrição

Interface web moderna e responsiva para gerenciamento do Sistema IoT de Automação de Energia Skyline A3.

## 🎨 Características

- **Design Moderno**: Interface limpa e profissional com gradientes e animações suaves
- **Responsivo**: Funciona perfeitamente em desktop, tablet e mobile
- **Dashboard Interativo**: Visualização em tempo real de dispositivos e acessos
- **Gerenciamento Completo**: CRUD de dispositivos e catracas
- **Logs Detalhados**: Histórico de acessos com filtros
- **Auto-refresh**: Atualização automática dos dados
- **Notificações**: Feedback visual de ações

## 🚀 Funcionalidades

### 📊 Visão Geral
- Cards com estatísticas em tempo real
- Lista de últimos acessos
- Status dos dispositivos
- Indicador de sistema online

### 💻 Dispositivos
- Listar todos os dispositivos cadastrados
- Adicionar novos dispositivos
- Ligar dispositivos (Wake-on-LAN)
- Desligar dispositivos remotamente
- Excluir dispositivos

### 🚪 Catracas
- Gerenciar catracas do sistema
- Adicionar novas catracas
- Visualizar último acesso
- Excluir catracas

### 📝 Logs
- Visualizar histórico de acessos
- Filtrar por data
- Filtrar por usuário
- Status de cada ação

### ⚙️ Configurações
- Configurar broker MQTT
- Modo debug
- Auto-refresh configurável
- Intervalo de atualização

## 🛠️ Tecnologias

- **HTML5**: Estrutura semântica
- **CSS3**: Estilos modernos com variáveis CSS, gradientes e animações
- **JavaScript ES6+**: Lógica de aplicação
- **Font Awesome 6**: Ícones
- **Fetch API**: Comunicação com backend

## 📁 Estrutura

```
frontend/
├── index.html          # Página principal (SPA)
├── css/
│   └── style.css      # Estilos completos
├── js/
│   └── app.js         # Lógica da aplicação
└── assets/            # Recursos adicionais
```

## 🎨 Paleta de Cores

- **Primary**: #667eea (Roxo azulado)
- **Secondary**: #764ba2 (Roxo escuro)
- **Success**: #43e97b (Verde)
- **Warning**: #feca57 (Amarelo)
- **Danger**: #f5576c (Vermelho)
- **Info**: #4facfe (Azul)

## 🔒 Autenticação

O sistema utiliza JWT (JSON Web Tokens) para autenticação:
- Login inicial armazena token no localStorage
- Token é enviado em todas as requisições à API
- Logout automático em caso de token expirado

## 📱 Responsividade

### Desktop (> 768px)
- Sidebar completa com ícones e textos
- Layouts em grid otimizados
- Visualização completa de dados

### Tablet/Mobile (≤ 768px)
- Sidebar colapsada (apenas ícones)
- Layouts em coluna única
- Formulários em tela cheia

## ⚡ Performance

- **Auto-refresh**: Padrão 30 segundos (configurável)
- **Lazy Loading**: Dados carregados sob demanda
- **Cache**: Uso de localStorage para configurações
- **Otimização**: Código minimalista e eficiente

## 🔗 API Endpoints Utilizados

### Autenticação
- `POST /api/auth/login` - Login

### Dispositivos
- `GET /api/devices` - Listar dispositivos
- `POST /api/devices` - Adicionar dispositivo
- `POST /api/devices/{id}/wake` - Ligar dispositivo
- `POST /api/devices/{id}/shutdown` - Desligar dispositivo
- `DELETE /api/devices/{id}` - Excluir dispositivo

### Catracas
- `GET /api/turnstiles` - Listar catracas
- `POST /api/turnstiles` - Adicionar catraca
- `DELETE /api/turnstiles/{id}` - Excluir catraca

### Logs
- `GET /api/logs` - Listar logs
- `GET /api/logs?date={date}&user={user}` - Filtrar logs

### Sistema
- `GET /api/health` - Status do sistema

## 🚀 Como Usar

1. **Iniciar o Backend**:
```bash
cd backend
python app.py
```

2. **Acessar o Frontend**:
```
http://localhost:5000
```

3. **Login**:
- Usuário: qualquer usuário
- Senha: mínimo 3 caracteres

## 💡 Dicas de Uso

- Use o **auto-refresh** para manter dados atualizados
- Configure o **intervalo** conforme necessidade
- Utilize os **filtros** nos logs para análises específicas
- Monitore o **indicador de status** para verificar conexão

## 🎯 Próximas Melhorias

- [ ] Gráficos de uso
- [ ] Exportação de relatórios
- [ ] Notificações em tempo real via WebSocket
- [ ] Modo escuro
- [ ] Múltiplos idiomas
- [ ] Validação avançada de formulários
- [ ] Paginação de tabelas

## 📄 Licença

Este projeto faz parte do Sistema Skyline A3.
