// ===== Configuração =====
const API_BASE_URL = 'http://localhost:5000/api';
let authToken = null;
let currentUser = null;
let autoRefreshInterval = null;

// ===== Inicialização =====
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

function initializeApp() {
    // Verificar se já está logado
    authToken = localStorage.getItem('authToken');
    currentUser = JSON.parse(localStorage.getItem('currentUser') || 'null');

    // Se estamos na página de dashboard, verificar autenticação
    if (window.location.pathname.includes('dashboard')) {
        if (!authToken || !currentUser) {
            window.location.href = '/';
            return;
        }
        // Atualizar informações do usuário
        updateUserInfo();
        // Configurar permissões baseadas no tipo de usuário
        setupPermissions();
    }

    // Event Listeners
    setupEventListeners();
    
    // Atualizar data/hora
    updateDateTime();
    setInterval(updateDateTime, 1000);
    
    // Carregar dados iniciais
    if (window.location.pathname.includes('dashboard')) {
        navigateToPage('overview');
        startAutoRefresh();
    }
}

function updateUserInfo() {
    const userSpan = document.getElementById('currentUser');
    const userTypeSpan = document.getElementById('userType');
    
    if (userSpan && currentUser) {
        userSpan.textContent = currentUser.username;
    }
    
    if (userTypeSpan && currentUser) {
        const userTypeLabel = currentUser.user_type === 'admin' ? 'Administrador' : 'Usuário';
        userTypeSpan.textContent = userTypeLabel;
    }
}

function setupPermissions() {
    // Esconder/mostrar elementos baseado no tipo de usuário
    const isAdmin = currentUser && currentUser.user_type === 'admin';
    
    // Botões de adicionar (apenas admin)
    const addDeviceBtn = document.getElementById('addDeviceBtn');
    const addTurnstileBtn = document.getElementById('addTurnstileBtn');
    const mqttSaveBtn = document.getElementById('mqttSaveBtn');
    const actionsHeader = document.getElementById('actionsHeader');
    const turnstilesActionsHeader = document.getElementById('turnstilesActionsHeader');
    
    if (addDeviceBtn) {
        addDeviceBtn.style.display = isAdmin ? 'inline-flex' : 'none';
    }
    if (addTurnstileBtn) {
        addTurnstileBtn.style.display = isAdmin ? 'inline-flex' : 'none';
    }
    if (mqttSaveBtn) {
        mqttSaveBtn.style.display = isAdmin ? 'inline-flex' : 'none';
    }
    if (actionsHeader) {
        actionsHeader.style.display = isAdmin ? 'table-cell' : 'none';
    }
    if (turnstilesActionsHeader) {
        turnstilesActionsHeader.style.display = isAdmin ? 'table-cell' : 'none';
    }
}

function setupEventListeners() {
    // Login
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    // Logout
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }

    // Navegação
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const page = e.currentTarget.dataset.page;
            navigateToPage(page);
        });
    });

    // Modais
    setupModalListeners();

    // Forms
    setupFormListeners();
}

// ===== Autenticação =====
// Esta função não é mais necessária aqui, pois o login está em login.html
// Mantida para compatibilidade caso seja chamada de outro lugar
async function handleLogin(e) {
    if (e) e.preventDefault();
    
    const usernameEl = document.getElementById('username');
    const passwordEl = document.getElementById('password');
    const errorDiv = document.getElementById('loginError');

    if (!usernameEl || !passwordEl) {
        return;
    }

    const username = usernameEl.value;
    const password = passwordEl.value;

    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            authToken = data.access_token;
            currentUser = data.user;
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            
            // Redirecionar para dashboard
            window.location.href = '/dashboard';
        } else {
            if (errorDiv) {
                errorDiv.textContent = data.error || 'Erro ao fazer login';
                errorDiv.classList.add('show');
            }
        }
    } catch (error) {
        console.error('Erro no login:', error);
        if (errorDiv) {
            errorDiv.textContent = 'Erro de conexão com o servidor';
            errorDiv.classList.add('show');
        }
    }
}

function handleLogout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    
    // Redirecionar para login
    window.location.href = '/';
}

function navigateToPage(pageName) {
    // Atualizar navegação ativa
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-page="${pageName}"]`)?.classList.add('active');

    // Atualizar seção ativa
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });

    // Atualizar título
    const titles = {
        'overview': 'Visão Geral',
        'devices': 'Dispositivos',
        'turnstiles': 'Catracas',
        'logs': 'Logs de Acesso',
        'settings': 'Configurações'
    };
    
    document.getElementById('pageTitle').textContent = titles[pageName] || pageName;

    // Mostrar seção correspondente
    const sectionMap = {
        'overview': 'overviewSection',
        'devices': 'devicesSection',
        'turnstiles': 'turnstilesSection',
        'logs': 'logsSection',
        'settings': 'settingsSection'
    };
    
    const sectionId = sectionMap[pageName];
    if (sectionId) {
        document.getElementById(sectionId).classList.add('active');
    }

    // Carregar dados da página
    loadPageData(pageName);
}

async function loadPageData(pageName) {
    switch(pageName) {
        case 'overview':
            await loadOverview();
            break;
        case 'devices':
            await loadDevices();
            break;
        case 'turnstiles':
            await loadTurnstiles();
            break;
        case 'logs':
            await loadLogs();
            break;
        case 'settings':
            loadSettings();
            break;
    }
}

// ===== Visão Geral =====
async function loadOverview() {
    try {
        // Verificar status do sistema
        const healthResponse = await apiRequest('/health');
        if (healthResponse.status === 'online') {
            document.getElementById('systemStatus').textContent = 'Sistema Online';
        }

        // Carregar dispositivos
        const devicesResponse = await apiRequest('/devices');
        const devices = devicesResponse.devices || [];
        
        document.getElementById('totalDevices').textContent = devices.length;
        document.getElementById('activeDevices').textContent = 
            devices.filter(d => d.status === 'online').length;

        // Atualizar lista de status dos dispositivos
        const deviceStatusList = document.getElementById('deviceStatusList');
        if (devices.length === 0) {
            deviceStatusList.innerHTML = '<p class="text-muted">Nenhum dispositivo cadastrado</p>';
        } else {
            deviceStatusList.innerHTML = devices.slice(0, 5).map(device => `
                <div class="list-item">
                    <div>
                        <strong>${device.hostname}</strong>
                        <br>
                        <small class="text-muted">${device.ip_address}</small>
                    </div>
                    <span class="badge ${device.status === 'online' ? 'badge-success' : 'badge-danger'}">
                        ${device.status === 'online' ? 'Online' : 'Offline'}
                    </span>
                </div>
            `).join('');
        }

        // Carregar logs recentes
        const logsResponse = await apiRequest('/logs?limit=5');
        const logs = logsResponse.logs || [];
        
        // Contar acessos de hoje
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const todayLogs = logs.filter(log => {
            const logDate = new Date(log.timestamp);
            logDate.setHours(0, 0, 0, 0);
            return logDate.getTime() === today.getTime();
        });
        
        const recentAccessList = document.getElementById('recentAccessList');
        if (logs.length === 0) {
            recentAccessList.innerHTML = '<p class="text-muted">Nenhum acesso registrado</p>';
        } else {
            recentAccessList.innerHTML = logs.slice(0, 5).map(log => {
                const actionLabel = log.action === 'entry' ? 'Entrada' : 'Saída';
                const actionClass = log.action === 'entry' ? 'badge-success' : 'badge-info';
                return `
                    <div class="list-item">
                        <div>
                            <strong>${log.user_id || 'Desconhecido'}</strong>
                            <br>
                            <small class="text-muted">${formatDateTime(log.timestamp)}</small>
                        </div>
                        <span class="badge ${actionClass}">
                            ${actionLabel}
                        </span>
                    </div>
                `;
            }).join('');
            
            document.getElementById('todayAccess').textContent = todayLogs.length || logs.length;
        }

    } catch (error) {
        console.error('Erro ao carregar visão geral:', error);
    }
}

// ===== Dispositivos =====
async function loadDevices() {
    try {
        const response = await apiRequest('/devices');
        const devices = response.devices || [];
        
        const tbody = document.getElementById('devicesTableBody');
        
        if (devices.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">Nenhum dispositivo cadastrado</td></tr>';
        } else {
            const isAdmin = currentUser && currentUser.user_type === 'admin';
            tbody.innerHTML = devices.map(device => {
                const actionsHtml = isAdmin ? `
                    <td>
                        <button class="btn btn-sm btn-success" onclick="wakeDevice(${device.id})">
                            <i class="fas fa-power-off"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="shutdownDevice(${device.id})">
                            <i class="fas fa-stop"></i>
                        </button>
                        <button class="btn btn-sm btn-secondary" onclick="deleteDevice(${device.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                ` : '<td></td>';
                
                return `
                    <tr>
                        <td>${device.hostname}</td>
                        <td>${device.ip_address}</td>
                        <td>${device.mac_address || 'N/A'}</td>
                        <td>${device.user_id}</td>
                        <td>
                            <span class="badge ${device.status === 'online' ? 'badge-success' : 'badge-danger'}">
                                ${device.status === 'online' ? 'Online' : 'Offline'}
                            </span>
                        </td>
                        ${actionsHtml}
                    </tr>
                `;
            }).join('');
        }
    } catch (error) {
        console.error('Erro ao carregar dispositivos:', error);
    }
}

async function wakeDevice(deviceId) {
    try {
        await apiRequest(`/devices/${deviceId}/wake`, { method: 'POST' });
        showNotification('Comando Wake-on-LAN enviado!', 'success');
        await loadDevices();
    } catch (error) {
        showNotification('Erro ao ligar dispositivo', 'error');
    }
}

async function shutdownDevice(deviceId) {
    if (!confirm('Deseja realmente desligar este dispositivo?')) return;
    
    try {
        await apiRequest(`/devices/${deviceId}/shutdown`, { method: 'POST' });
        showNotification('Comando de desligamento enviado!', 'success');
        await loadDevices();
    } catch (error) {
        showNotification('Erro ao desligar dispositivo', 'error');
    }
}

async function deleteDevice(deviceId) {
    if (!confirm('Deseja realmente excluir este dispositivo?')) return;
    
    try {
        await apiRequest(`/devices/${deviceId}`, { method: 'DELETE' });
        showNotification('Dispositivo excluído!', 'success');
        await loadDevices();
    } catch (error) {
        showNotification('Erro ao excluir dispositivo', 'error');
    }
}

// ===== Catracas =====
async function loadTurnstiles() {
    try {
        const response = await apiRequest('/turnstiles');
        const turnstiles = response.turnstiles || [];
        
        const tbody = document.getElementById('turnstilesTableBody');
        
        if (turnstiles.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">Nenhuma catraca cadastrada</td></tr>';
        } else {
            const isAdmin = currentUser && currentUser.user_type === 'admin';
            tbody.innerHTML = turnstiles.map(turnstile => {
                const actionsHtml = isAdmin ? `
                    <td>
                        <button class="btn btn-sm btn-secondary" onclick="deleteTurnstile('${turnstile.id}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                ` : '<td></td>';
                
                return `
                    <tr>
                        <td>${turnstile.id}</td>
                        <td>${turnstile.location || 'N/A'}</td>
                        <td>
                            <span class="badge badge-success">Ativa</span>
                        </td>
                        <td>${turnstile.last_access ? formatDateTime(turnstile.last_access) : 'Nunca'}</td>
                        ${actionsHtml}
                    </tr>
                `;
            }).join('');
        }
        
        document.getElementById('totalTurnstiles').textContent = turnstiles.length;
    } catch (error) {
        console.error('Erro ao carregar catracas:', error);
    }
}

async function deleteTurnstile(turnstileId) {
    if (!confirm('Deseja realmente excluir esta catraca?')) return;
    
    try {
        await apiRequest(`/turnstiles/${turnstileId}`, { method: 'DELETE' });
        showNotification('Catraca excluída!', 'success');
        await loadTurnstiles();
    } catch (error) {
        showNotification('Erro ao excluir catraca', 'error');
    }
}

// ===== Logs =====
async function loadLogs() {
    try {
        const response = await apiRequest('/logs');
        const logs = response.logs || [];
        
        const tbody = document.getElementById('logsTableBody');
        
        if (logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">Nenhum log registrado</td></tr>';
        } else {
            tbody.innerHTML = logs.map(log => `
                <tr>
                    <td>${formatDateTime(log.timestamp)}</td>
                    <td>${log.user_id || 'Desconhecido'}</td>
                    <td>${log.turnstile_id || 'N/A'}</td>
                    <td>${log.action}</td>
                    <td>
                        <span class="badge ${log.status === 'success' ? 'badge-success' : 'badge-danger'}">
                            ${log.status === 'success' ? 'Sucesso' : 'Falha'}
                        </span>
                    </td>
                </tr>
            `).join('');
        }
    } catch (error) {
        console.error('Erro ao carregar logs:', error);
    }
}

// ===== Configurações =====
function loadSettings() {
    // Carregar configurações do localStorage
    const debugMode = localStorage.getItem('debugMode') === 'true';
    const autoRefresh = localStorage.getItem('autoRefresh') !== 'false'; // padrão true
    const refreshInterval = localStorage.getItem('refreshInterval') || '30';
    
    document.getElementById('debugMode').checked = debugMode;
    document.getElementById('autoRefresh').checked = autoRefresh;
    document.getElementById('refreshInterval').value = refreshInterval;
}

// ===== Modais =====
function setupModalListeners() {
    // Botão adicionar dispositivo
    document.getElementById('addDeviceBtn')?.addEventListener('click', () => {
        openModal('addDeviceModal');
    });

    // Botão adicionar catraca
    document.getElementById('addTurnstileBtn')?.addEventListener('click', () => {
        openModal('addTurnstileModal');
    });

    // Botões de fechar modal
    document.querySelectorAll('.close-modal').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const modal = e.target.closest('.modal');
            closeModal(modal.id);
        });
    });

    // Fechar modal ao clicar fora
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal(modal.id);
            }
        });
    });
}

function openModal(modalId) {
    document.getElementById(modalId)?.classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId)?.classList.remove('active');
}

// ===== Forms =====
function setupFormListeners() {
    // Form adicionar dispositivo
    document.getElementById('addDeviceForm')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData);
        
        try {
            await apiRequest('/devices', {
                method: 'POST',
                body: JSON.stringify(data)
            });
            showNotification('Dispositivo adicionado com sucesso!', 'success');
            closeModal('addDeviceModal');
            e.target.reset();
            await loadDevices();
        } catch (error) {
            showNotification('Erro ao adicionar dispositivo', 'error');
        }
    });

    // Form adicionar catraca
    document.getElementById('addTurnstileForm')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData);
        
        try {
            await apiRequest('/turnstiles', {
                method: 'POST',
                body: JSON.stringify(data)
            });
            showNotification('Catraca adicionada com sucesso!', 'success');
            closeModal('addTurnstileModal');
            e.target.reset();
            await loadTurnstiles();
        } catch (error) {
            showNotification('Erro ao adicionar catraca', 'error');
        }
    });

    // Form configurações MQTT
    document.getElementById('mqttForm')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        showNotification('Configurações salvas!', 'success');
    });

    // Auto refresh toggle
    document.getElementById('autoRefresh')?.addEventListener('change', (e) => {
        localStorage.setItem('autoRefresh', e.target.checked);
        if (e.target.checked) {
            startAutoRefresh();
        } else {
            stopAutoRefresh();
        }
    });

    // Intervalo de refresh
    document.getElementById('refreshInterval')?.addEventListener('change', (e) => {
        localStorage.setItem('refreshInterval', e.target.value);
        if (document.getElementById('autoRefresh').checked) {
            stopAutoRefresh();
            startAutoRefresh();
        }
    });

    // Debug mode
    document.getElementById('debugMode')?.addEventListener('change', (e) => {
        localStorage.setItem('debugMode', e.target.checked);
    });

    // Filtros de logs
    document.getElementById('applyFilters')?.addEventListener('click', async () => {
        const date = document.getElementById('filterDate').value;
        const user = document.getElementById('filterUser').value;
        
        let url = '/logs?';
        if (date) url += `date=${date}&`;
        if (user) url += `user=${user}&`;
        
        try {
            const response = await apiRequest(url);
            const logs = response.logs || [];
            // Atualizar tabela com logs filtrados
            const tbody = document.getElementById('logsTableBody');
            if (logs.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="text-center">Nenhum log encontrado</td></tr>';
            } else {
                tbody.innerHTML = logs.map(log => `
                    <tr>
                        <td>${formatDateTime(log.timestamp)}</td>
                        <td>${log.user_id || 'Desconhecido'}</td>
                        <td>${log.turnstile_id || 'N/A'}</td>
                        <td>${log.action}</td>
                        <td>
                            <span class="badge ${log.status === 'success' ? 'badge-success' : 'badge-danger'}">
                                ${log.status === 'success' ? 'Sucesso' : 'Falha'}
                            </span>
                        </td>
                    </tr>
                `).join('');
            }
        } catch (error) {
            console.error('Erro ao filtrar logs:', error);
        }
    });
}

// ===== API Helper =====
async function apiRequest(endpoint, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...(authToken && { 'Authorization': `Bearer ${authToken}` })
    };

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: { ...headers, ...options.headers }
    });

    if (response.status === 401) {
        // Token expirado
        handleLogout();
        throw new Error('Sessão expirada');
    }

    if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
    }

    return await response.json();
}

// ===== Auto Refresh =====
function startAutoRefresh() {
    const interval = parseInt(localStorage.getItem('refreshInterval') || '30') * 1000;
    
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    
    autoRefreshInterval = setInterval(() => {
        const activePage = document.querySelector('.nav-item.active')?.dataset.page;
        if (activePage) {
            loadPageData(activePage);
        }
    }, interval);
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
}

// ===== Utilitários =====
function updateDateTime() {
    const now = new Date();
    const dateTimeStr = now.toLocaleString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    
    const element = document.getElementById('currentDateTime');
    if (element) {
        element.textContent = dateTimeStr;
    }
}

function formatDateTime(timestamp) {
    if (!timestamp) return 'N/A';
    const date = new Date(timestamp);
    return date.toLocaleString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function showNotification(message, type = 'info') {
    // Criar notificação simples
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        z-index: 9999;
        animation: slideInRight 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    `;
    
    const colors = {
        'success': '#43e97b',
        'error': '#f5576c',
        'warning': '#feca57',
        'info': '#4facfe'
    };
    
    notification.style.background = colors[type] || colors.info;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Adicionar estilos de animação
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
