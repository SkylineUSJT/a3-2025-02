// Validações e utilitários para o frontend

/**
 * Valida endereço IP
 */
function isValidIP(ip) {
    const pattern = /^(\d{1,3}\.){3}\d{1,3}$/;
    if (!pattern.test(ip)) return false;
    
    return ip.split('.').every(octet => {
        const num = parseInt(octet, 10);
        return num >= 0 && num <= 255;
    });
}

/**
 * Valida endereço MAC
 */
function isValidMAC(mac) {
    const pattern = /^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$/;
    return pattern.test(mac);
}

/**
 * Formata MAC address para formato padrão
 */
function formatMAC(mac) {
    mac = mac.replace(/[^0-9A-Fa-f]/g, '');
    if (mac.length !== 12) return mac;
    
    return mac.match(/.{1,2}/g).join(':').toUpperCase();
}

/**
 * Valida hostname
 */
function isValidHostname(hostname) {
    const pattern = /^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$/;
    return pattern.test(hostname);
}

/**
 * Sanitiza input do usuário
 */
function sanitizeInput(input) {
    if (typeof input !== 'string') return input;
    
    return input
        .trim()
        .replace(/[<>]/g, '')
        .substring(0, 255);
}

/**
 * Formata bytes para formato legível
 */
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

/**
 * Debounce para otimizar buscas
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Gera ID único
 */
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

/**
 * Valida email
 */
function isValidEmail(email) {
    const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return pattern.test(email);
}

/**
 * Formata data relativa (ex: "há 5 minutos")
 */
function formatRelativeTime(timestamp) {
    const now = new Date();
    const date = new Date(timestamp);
    const diffMs = now - date;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);
    
    if (diffSec < 60) return 'agora mesmo';
    if (diffMin < 60) return `há ${diffMin} minuto${diffMin > 1 ? 's' : ''}`;
    if (diffHour < 24) return `há ${diffHour} hora${diffHour > 1 ? 's' : ''}`;
    if (diffDay < 7) return `há ${diffDay} dia${diffDay > 1 ? 's' : ''}`;
    
    return formatDateTime(timestamp);
}

/**
 * Copia texto para clipboard
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showNotification('Copiado para a área de transferência!', 'success');
        return true;
    } catch (err) {
        showNotification('Erro ao copiar', 'error');
        return false;
    }
}

/**
 * Download de arquivo
 */
function downloadFile(content, filename, type = 'text/plain') {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

/**
 * Exportar logs para CSV
 */
function exportLogsToCSV(logs) {
    const headers = ['Data/Hora', 'Usuário', 'Catraca', 'Ação', 'Status'];
    const rows = logs.map(log => [
        formatDateTime(log.timestamp),
        log.user_id || 'N/A',
        log.turnstile_id || 'N/A',
        log.action,
        log.status
    ]);
    
    const csv = [
        headers.join(','),
        ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');
    
    downloadFile(csv, `logs_${new Date().toISOString().split('T')[0]}.csv`, 'text/csv');
    showNotification('Logs exportados com sucesso!', 'success');
}

/**
 * Detecta modo escuro do sistema
 */
function isDarkMode() {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
}

/**
 * Adiciona listener para mudança de tema
 */
function watchThemeChange(callback) {
    if (!window.matchMedia) return;
    
    const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
    darkModeQuery.addEventListener('change', (e) => {
        callback(e.matches ? 'dark' : 'light');
    });
}

/**
 * Verifica se o navegador suporta recursos necessários
 */
function checkBrowserCompatibility() {
    const features = {
        fetch: typeof fetch !== 'undefined',
        localStorage: typeof localStorage !== 'undefined',
        Promise: typeof Promise !== 'undefined',
        ES6: typeof Symbol !== 'undefined'
    };
    
    const unsupported = Object.entries(features)
        .filter(([, supported]) => !supported)
        .map(([feature]) => feature);
    
    if (unsupported.length > 0) {
        console.warn('Recursos não suportados:', unsupported);
        return false;
    }
    
    return true;
}

/**
 * Throttle para otimizar eventos de scroll/resize
 */
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Retry automático para requisições
 */
async function retryRequest(fn, maxRetries = 3, delay = 1000) {
    for (let i = 0; i < maxRetries; i++) {
        try {
            return await fn();
        } catch (error) {
            if (i === maxRetries - 1) throw error;
            await new Promise(resolve => setTimeout(resolve, delay * (i + 1)));
        }
    }
}

/**
 * Logger customizado
 */
const Logger = {
    debug: (...args) => {
        if (localStorage.getItem('debugMode') === 'true') {
            console.log('[DEBUG]', new Date().toISOString(), ...args);
        }
    },
    
    info: (...args) => {
        console.info('[INFO]', new Date().toISOString(), ...args);
    },
    
    warn: (...args) => {
        console.warn('[WARN]', new Date().toISOString(), ...args);
    },
    
    error: (...args) => {
        console.error('[ERROR]', new Date().toISOString(), ...args);
    }
};

/**
 * Performance monitor
 */
class PerformanceMonitor {
    constructor() {
        this.marks = {};
    }
    
    start(label) {
        this.marks[label] = performance.now();
    }
    
    end(label) {
        if (!this.marks[label]) {
            Logger.warn(`Mark ${label} não encontrado`);
            return;
        }
        
        const duration = performance.now() - this.marks[label];
        Logger.debug(`${label}: ${duration.toFixed(2)}ms`);
        delete this.marks[label];
        return duration;
    }
}

// Exportar para uso global
if (typeof window !== 'undefined') {
    window.Validators = {
        isValidIP,
        isValidMAC,
        isValidHostname,
        isValidEmail,
        formatMAC,
        sanitizeInput
    };
    
    window.Utils = {
        formatBytes,
        debounce,
        throttle,
        generateUUID,
        formatRelativeTime,
        copyToClipboard,
        downloadFile,
        exportLogsToCSV,
        isDarkMode,
        watchThemeChange,
        checkBrowserCompatibility,
        retryRequest
    };
    
    window.Logger = Logger;
    window.PerformanceMonitor = PerformanceMonitor;
}
