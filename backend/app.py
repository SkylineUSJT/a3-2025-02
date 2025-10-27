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
def serve_frontend():
    """Serve a página inicial do frontend"""
    return send_from_directory(FRONTEND_DIR, 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    """Serve arquivos estáticos do frontend"""
    if os.path.exists(os.path.join(FRONTEND_DIR, path)):
        return send_from_directory(FRONTEND_DIR, path)
    else:
        return send_from_directory(FRONTEND_DIR, 'index.html')


@app.route('/api/health', methods=['GET'])
def health_check():
    """Verifica status do sistema"""
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat()
    })


# --- Auth ---
@app.route('/api/auth/login', methods=['POST'])
def login():
    """
    Autenticação básica - APENAS PARA DESENVOLVIMENTO
    TODO: Implementar autenticação real com banco de dados/LDAP em produção
    """
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')
    # Placeholder: validacao simples; troque por consulta ao DB/LDAP
    if username and password and len(password) >= 3:
        token = create_access_token(identity=username)
        return jsonify({ 'access_token': token, 'user': { 'username': username } })
    return jsonify({ 'error': 'Credenciais inválidas' }), 401


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


if __name__ == '__main__':
    # Inicializa banco de dados
    db.initialize()
    
    # Inicia cliente MQTT
    mqtt_client.start()
    
    logger.info("Sistema IoT de Automação iniciado")
    # Executar sem reloader para evitar reinicializações durante testes
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
