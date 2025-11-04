"""
Sistema IoT de Automação de Energia
Servidor Flask principal para gerenciamento de catracas e computadores
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from datetime import datetime
import logging
import os
import sys
import hashlib
from functools import wraps

# Adiciona o diretório backend ao PYTHONPATH
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from modules.database import Database
from modules.mqtt_client import MQTTClient
from modules.wol import WakeOnLAN
from modules.shutdown import RemoteShutdown

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configurar caminho para o frontend
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
CORS(app)
db = Database()
mqtt_client = MQTTClient()
wol = WakeOnLAN()
shutdown = RemoteShutdown()

# JWT Config
# ATENÇÃO: Altere a chave secreta em produção! Use variável de ambiente:
# export JWT_SECRET_KEY="sua-chave-super-secreta-aqui"
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'change-me-in-production-INSECURE')
jwt = JWTManager(app)


@app.route('/')
def serve_login():
    """Serve a página de login"""
    return send_from_directory(FRONTEND_DIR, 'login.html')

@app.route('/dashboard')
def serve_dashboard():
    """Serve a página do dashboard"""
    return send_from_directory(FRONTEND_DIR, 'dashboard.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve arquivos estáticos do frontend"""
    if os.path.exists(os.path.join(FRONTEND_DIR, path)):
        return send_from_directory(FRONTEND_DIR, path)
    else:
        # Se não for arquivo estático, redireciona para login
        return send_from_directory(FRONTEND_DIR, 'login.html')


@app.route('/api/health', methods=['GET'])
def health_check():
    """Verifica status do sistema"""
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat()
    })


# --- Auth ---
def hash_password(password):
    """Hash simples de senha (para desenvolvimento)"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    """Verifica senha"""
    return hash_password(password) == hashed

def admin_required(f):
    """Decorator para rotas que requerem permissão de admin"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user = get_jwt_identity()
        user = db.get_user_by_username(current_user)
        if not user or user.get('user_type') != 'admin':
            return jsonify({'error': 'Acesso negado. Apenas administradores.'}), 403
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Autenticação com validação de usuário e tipo"""
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Usuário e senha são obrigatórios'}), 400
    
    # Buscar usuário no banco
    user = db.get_user_by_username(username)
    
    if not user:
        return jsonify({'error': 'Credenciais inválidas'}), 401
    
    # Verificar senha
    if not verify_password(password, user['password']):
        return jsonify({'error': 'Credenciais inválidas'}), 401
    
    # Criar token JWT com informações do usuário
    token = create_access_token(
        identity=username,
        additional_claims={'user_type': user['user_type']}
    )
    
    return jsonify({
        'access_token': token,
        'user': {
            'username': user['username'],
            'user_type': user['user_type']
        }
    }), 200


@app.route('/api/devices', methods=['GET'])
def get_devices():
    """Lista todos os dispositivos cadastrados"""
    try:
        devices = db.get_all_devices()
        return jsonify({'devices': devices}), 200
    except Exception as e:
        logger.error(f"Erro ao listar dispositivos: {e}")
        return jsonify({'error': str(e)}), 500



@app.route('/api/devices', methods=['POST'])
def register_device():
    """Cadastra novo dispositivo (computador) - aceita dados mínimos do instalador PowerShell"""
    try:
        data = request.json
        # Aceita tanto user_id quanto user (do PowerShell)
        user_id = data.get('user_id') or data.get('user') or data.get('hostname')
        hostname = data.get('hostname')
        ip_address = data.get('ip') or data.get('ip_address')
        mac_address = data.get('mac_address', '')  # pode ser vazio
        os_type = data.get('os_type', 'windows')
        credentials = data.get('credentials', {})
        if not hostname or not ip_address or not user_id:
            return jsonify({'error': 'Campos obrigatórios ausentes: hostname, ip/user'}), 400
        device_id = db.add_device(
            user_id=user_id,
            hostname=hostname,
            mac_address=mac_address,
            ip_address=ip_address,
            os_type=os_type,
            credentials=credentials
        )
        logger.info(f"Dispositivo cadastrado: {hostname} (user_id={user_id})")
        return jsonify({'device_id': device_id, 'message': 'Dispositivo cadastrado com sucesso'}), 201
    except Exception as e:
        logger.error(f"Erro ao cadastrar dispositivo: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/access/entry', methods=['POST'])
def register_entry():
    """Registra entrada do funcionário e liga o computador"""
    try:
        data = request.json
        user_id = data['user_id']
        
        # Busca dispositivo do usuário
        device = db.get_device_by_user(user_id)
        
        if not device:
            return jsonify({'error': 'Dispositivo não encontrado para este usuário'}), 404
        
        # Evita logs/ações duplicadas em janela curta
        if db.has_recent_access(user_id, 'entry'):
            logger.info(f"Entrada recente já registrada para usuário {user_id}, ignorando ação duplicada")
            return jsonify({'message': 'Entrada já registrada recentemente', 'device': device['hostname']}), 200

        # Registra log de acesso
        db.log_access(user_id, 'entry')
        
        # Envia Wake-on-LAN
        success = wol.wake(device['mac_address'])

        if not success:
            return jsonify({'error': 'Falha ao enviar Wake-on-LAN'}), 500

        # Verifica se o host ficou online (ping/TCP) dentro do timeout configurado
        ip = device['ip_address']
        if wol.is_online(ip):
            logger.info(f"Computador ligado para usuário {user_id}")
            return jsonify({
                'message': 'Entrada registrada e computador ligado',
                'device': device['hostname']
            }), 200
        else:
            # Ainda acordando: retorna 202 para indicar que a ação foi aceita mas o host ainda não respondeu
            logger.info(f"WOL enviado, aguardando host {ip} ficar online para usuário {user_id}")
            return jsonify({
                'message': 'Entrada registrada; host acordando',
                'device': device['hostname'],
                'status': 'pending'
            }), 202
            
    except Exception as e:
        logger.error(f"Erro ao registrar entrada: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/access/exit', methods=['POST'])
def register_exit():
    """Registra saída do funcionário e desliga o computador"""
    try:
        data = request.json
        user_id = data['user_id']

        # Busca dispositivo do usuário
        device = db.get_device_by_user(user_id)

        if not device:
            return jsonify({'error': 'Dispositivo não encontrado para este usuário'}), 404

        # Evita logs/ações duplicadas em janela curta
        if db.has_recent_access(user_id, 'exit'):
            logger.info(f"Saída recente já registrada para usuário {user_id}, ignorando ação duplicada")
            return jsonify({'message': 'Saída já registrada recentemente', 'device': device['hostname']}), 200

        # Registra log de acesso
        db.log_access(user_id, 'exit')

        # Desliga computador remotamente (método tradicional)
        success = shutdown.shutdown_device(
            ip_address=device['ip_address'],
            os_type=device['os_type'],
            credentials=device.get('credentials', {})
        )

        if success:
            logger.info(f"Computador desligado para usuário {user_id}")
            return jsonify({
                'message': 'Saída registrada e computador desligado',
                'device': device['hostname']
            }), 200
        else:
            return jsonify({'warning': 'Saída registrada mas falha ao desligar computador'}), 200

    except Exception as e:
        logger.error(f"Erro ao registrar saída: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Lista logs de acesso"""
    try:
        limit = request.args.get('limit', 50, type=int)
        logs = db.get_access_logs(limit)
        return jsonify({'logs': logs}), 200
    except Exception as e:
        logger.error(f"Erro ao buscar logs: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/turnstiles', methods=['GET'])
def get_turnstiles():
    """Lista todas as catracas"""
    try:
        turnstiles = db.get_all_turnstiles()
        return jsonify({'turnstiles': turnstiles}), 200
    except Exception as e:
        logger.error(f"Erro ao listar catracas: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/turnstiles', methods=['POST'])
def add_turnstile():
    """Adiciona nova catraca"""
    try:
        data = request.json
        turnstile_id = data.get('turnstile_id')
        location = data.get('location')
        
        if not turnstile_id:
            return jsonify({'error': 'ID da catraca é obrigatório'}), 400
        
        db.add_turnstile(turnstile_id, location)
        return jsonify({'message': 'Catraca adicionada com sucesso'}), 201
    except Exception as e:
        logger.error(f"Erro ao adicionar catraca: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/devices/<int:device_id>/wake', methods=['POST'])
def wake_device(device_id):
    """Liga um dispositivo via Wake-on-LAN"""
    try:
        device = db.get_device_by_id(device_id)
        if not device:
            return jsonify({'error': 'Dispositivo não encontrado'}), 404
        
        success = wol.wake(device['mac_address'])
        if success:
            return jsonify({'message': 'Comando Wake-on-LAN enviado'}), 200
        else:
            return jsonify({'error': 'Falha ao enviar Wake-on-LAN'}), 500
    except Exception as e:
        logger.error(f"Erro ao ligar dispositivo: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/devices/<int:device_id>/shutdown', methods=['POST'])
def shutdown_device_route(device_id):
    """Desliga um dispositivo"""
    try:
        device = db.get_device_by_id(device_id)
        if not device:
            return jsonify({'error': 'Dispositivo não encontrado'}), 404
        
        success = shutdown.shutdown_device(
            ip_address=device['ip_address'],
            os_type=device['os_type'],
            credentials=device.get('credentials', {})
        )
        
        if success:
            return jsonify({'message': 'Comando de desligamento enviado'}), 200
        else:
            return jsonify({'error': 'Falha ao desligar dispositivo'}), 500
    except Exception as e:
        logger.error(f"Erro ao desligar dispositivo: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/devices/<int:device_id>', methods=['DELETE'])
def delete_device_route(device_id):
    """Exclui um dispositivo"""
    try:
        db.delete_device(device_id)
        return jsonify({'message': 'Dispositivo excluído'}), 200
    except Exception as e:
        logger.error(f"Erro ao excluir dispositivo: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/turnstiles/<turnstile_id>', methods=['DELETE'])
def delete_turnstile(turnstile_id):
    """Exclui uma catraca"""
    try:
        db.delete_turnstile(turnstile_id)
        return jsonify({'message': 'Catraca excluída'}), 200
    except Exception as e:
        logger.error(f"Erro ao excluir catraca: {e}")
        return jsonify({'error': str(e)}), 500


def init_default_users():
    """Inicializa usuários padrão se não existirem"""
    admin_user = db.get_user_by_username('admin')
    if not admin_user:
        admin_password = hash_password('admin123')
        db.create_user('admin', admin_password, 'admin')
        logger.info("Usuário admin criado (senha: admin123)")
    
    usuario_user = db.get_user_by_username('usuario')
    if not usuario_user:
        usuario_password = hash_password('usuario123')
        db.create_user('usuario', usuario_password, 'usuario')
        logger.info("Usuário padrão criado (senha: usuario123)")

def init_fake_data():
    """Inicializa dados fake para demonstração"""
    import random
    from datetime import timedelta
    
    # Verificar se já existem dados
    devices = db.get_all_devices()
    if len(devices) > 0:
        logger.info("Dados fake já existem, pulando inicialização")
        return
    
    logger.info("Criando dados fake para demonstração...")
    
    # Criar dispositivos fake
    fake_devices = [
        {'user_id': 'funcionario001', 'hostname': 'PC-OFICINA-01', 'mac_address': '00:1B:44:11:3A:B7', 'ip_address': '192.168.1.101', 'os_type': 'windows'},
        {'user_id': 'funcionario002', 'hostname': 'PC-ADMIN-02', 'mac_address': '00:1B:44:11:3A:B8', 'ip_address': '192.168.1.102', 'os_type': 'windows'},
        {'user_id': 'funcionario003', 'hostname': 'PC-RECEPCAO', 'mac_address': '00:1B:44:11:3A:B9', 'ip_address': '192.168.1.103', 'os_type': 'windows'},
        {'user_id': 'funcionario004', 'hostname': 'PC-SERV-01', 'mac_address': '00:1B:44:11:3A:BA', 'ip_address': '192.168.1.104', 'os_type': 'linux'},
        {'user_id': 'funcionario005', 'hostname': 'PC-DEV-01', 'mac_address': '00:1B:44:11:3A:BB', 'ip_address': '192.168.1.105', 'os_type': 'windows'},
    ]
    
    for device in fake_devices:
        try:
            db.add_device(
                user_id=device['user_id'],
                hostname=device['hostname'],
                mac_address=device['mac_address'],
                ip_address=device['ip_address'],
                os_type=device['os_type']
            )
        except Exception as e:
            logger.warning(f"Erro ao criar dispositivo fake {device['hostname']}: {e}")
    
    # Criar catracas fake
    fake_turnstiles = [
        {'turnstile_id': 'CAT001', 'location': 'Entrada Principal'},
        {'turnstile_id': 'CAT002', 'location': 'Entrada Secundária'},
        {'turnstile_id': 'CAT003', 'location': 'Estacionamento'},
    ]
    
    for turnstile in fake_turnstiles:
        try:
            db.add_turnstile(turnstile['turnstile_id'], turnstile['location'])
        except Exception as e:
            logger.warning(f"Erro ao criar catraca fake {turnstile['turnstile_id']}: {e}")
    
    # Criar logs fake (últimos 7 dias)
    now = datetime.now()
    for day in range(7):
        date = now - timedelta(days=day)
        for hour in range(8, 19):  # Horário comercial
            for minute in [0, 30]:  # A cada meia hora
                timestamp = date.replace(hour=hour, minute=minute, second=random.randint(0, 59))
                user_id = random.choice(['funcionario001', 'funcionario002', 'funcionario003', 'funcionario004', 'funcionario005'])
                access_type = random.choice(['entry', 'exit'])
                turnstile_id = random.choice(['CAT001', 'CAT002', 'CAT003'])
                
                try:
                    conn = db.get_connection()
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO access_logs (user_id, access_type, timestamp, turnstile_id, success)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (user_id, access_type, timestamp.isoformat(), turnstile_id, 1))
                    conn.commit()
                    conn.close()
                except Exception as e:
                    logger.warning(f"Erro ao criar log fake: {e}")
    
    logger.info("Dados fake criados com sucesso")

if __name__ == '__main__':
    # Inicializa banco de dados
    db.initialize()
    
    # Inicializa usuários padrão
    init_default_users()
    
    # Inicializa dados fake
    init_fake_data()
    
    # Inicia cliente MQTT
    mqtt_client.start()
    
    logger.info("Sistema IoT de Automação iniciado")
    # Executar sem reloader para evitar reinicializações durante testes
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
