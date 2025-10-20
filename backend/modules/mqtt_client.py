"""
Cliente MQTT para comunicação com catraca de acesso
"""
import paho.mqtt.client as mqtt
import json
import logging
from threading import Thread

logger = logging.getLogger(__name__)


class MQTTClient:
    def __init__(self, broker='localhost', port=1883, topic='catraca/acesso'):
        self.broker = broker
        self.port = port
        self.topic = topic
        self.client = None
        self.connected = False
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback quando conecta ao broker"""
        if rc == 0:
            self.connected = True
            logger.info(f"Conectado ao broker MQTT: {self.broker}:{self.port}")
            # Subscreve ao tópico da catraca
            client.subscribe(self.topic)
            logger.info(f"Inscrito no tópico: {self.topic}")
        else:
            logger.error(f"Falha na conexão MQTT. Código: {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback quando desconecta do broker"""
        self.connected = False
        logger.warning("Desconectado do broker MQTT")
    
    def on_message(self, client, userdata, msg):
        """Callback quando recebe mensagem da catraca"""
        try:
            payload = json.loads(msg.payload.decode())
            logger.info(f"Mensagem recebida: {payload}")
            
            # Processa evento da catraca
            self.process_access_event(payload)
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem MQTT: {e}")
    
    def process_access_event(self, event):
        """
        Processa evento de acesso da catraca
        Formato esperado: {"user_id": "123", "type": "entry/exit", "timestamp": "..."}
        """
        from modules.database import Database
        from modules.wol import WakeOnLAN
        from modules.shutdown import RemoteShutdown
        
        user_id = event.get('user_id')
        access_type = event.get('type')
        
        if not user_id or not access_type:
            logger.warning("Evento inválido recebido da catraca")
            return
        
        db = Database()
        device = db.get_device_by_user(user_id)
        
        if not device:
            logger.warning(f"Dispositivo não encontrado para usuário {user_id}")
            return
        
        # Registra log de acesso
        db.log_access(user_id, access_type)
        
        if access_type == 'entry':
            # Liga o computador
            wol = WakeOnLAN()
            success = wol.wake(device['mac_address'])
            logger.info(f"Wake-on-LAN enviado para {device['hostname']}: {'sucesso' if success else 'falha'}")
            
        elif access_type == 'exit':
            # Desliga o computador
            shutdown = RemoteShutdown()
            success = shutdown.shutdown_device(
                ip_address=device['ip_address'],
                os_type=device['os_type'],
                credentials=device.get('credentials', {})
            )
            logger.info(f"Shutdown enviado para {device['hostname']}: {'sucesso' if success else 'falha'}")
    
    def start(self):
        """Inicia cliente MQTT em thread separada"""
        def run():
            try:
                self.client = mqtt.Client()
                self.client.on_connect = self.on_connect
                self.client.on_disconnect = self.on_disconnect
                self.client.on_message = self.on_message
                
                logger.info(f"Conectando ao broker MQTT {self.broker}:{self.port}")
                self.client.connect(self.broker, self.port, 60)
                self.client.loop_forever()
                
            except Exception as e:
                logger.error(f"Erro ao iniciar cliente MQTT: {e}")
        
        thread = Thread(target=run, daemon=True)
        thread.start()
        logger.info("Cliente MQTT iniciado em background")
    
    def publish(self, message, topic=None):
        """Publica mensagem no broker"""
        if not self.connected:
            logger.warning("Cliente MQTT não conectado")
            return False
        
        try:
            topic = topic or self.topic
            payload = json.dumps(message)
            self.client.publish(topic, payload)
            logger.info(f"Mensagem publicada no tópico {topic}")
            return True
        except Exception as e:
            logger.error(f"Erro ao publicar mensagem: {e}")
            return False
    
    def stop(self):
        """Para o cliente MQTT"""
        if self.client:
            self.client.disconnect()
            logger.info("Cliente MQTT desconectado")
