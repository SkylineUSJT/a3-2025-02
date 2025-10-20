"""
Simulador de catraca MQTT
Simula eventos de entrada e saída de funcionários
"""
import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime

# Configurações
BROKER = 'localhost'
PORT = 1883
TOPIC = 'catraca/acesso'

def simular_entrada(user_id):
    """Simula passagem na catraca - ENTRADA"""
    client = mqtt.Client()
    client.connect(BROKER, PORT, 60)
    
    message = {
        "user_id": user_id,
        "type": "entry",
        "timestamp": datetime.now().isoformat()
    }
    
    client.publish(TOPIC, json.dumps(message))
    print(f"✅ Entrada registrada: Usuário {user_id}")
    client.disconnect()

def simular_saida(user_id):
    """Simula passagem na catraca - SAÍDA"""
    client = mqtt.Client()
    client.connect(BROKER, PORT, 60)
    
    message = {
        "user_id": user_id,
        "type": "exit",
        "timestamp": datetime.now().isoformat()
    }
    
    client.publish(TOPIC, json.dumps(message))
    print(f"❌ Saída registrada: Usuário {user_id}")
    client.disconnect()

def simular_dia_trabalho():
    """Simula um dia de trabalho completo"""
    print("=== SIMULAÇÃO DE CATRACA MQTT ===\n")
    
    usuarios = ["FUNC001", "FUNC002", "FUNC003"]
    
    # Chegada dos funcionários
    print("🌅 Manhã - Funcionários chegando...")
    for user in usuarios:
        simular_entrada(user)
        time.sleep(1)
    
    print("\n⏰ Aguardando 5 segundos (simulando expediente)...\n")
    time.sleep(5)
    
    # Saída dos funcionários
    print("🌆 Tarde - Funcionários saindo...")
    for user in usuarios:
        simular_saida(user)
        time.sleep(1)
    
    print("\n=== SIMULAÇÃO CONCLUÍDA ===")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        comando = sys.argv[1]
        
        if comando == 'entrada' and len(sys.argv) > 2:
            simular_entrada(sys.argv[2])
        elif comando == 'saida' and len(sys.argv) > 2:
            simular_saida(sys.argv[2])
        elif comando == 'dia':
            simular_dia_trabalho()
        else:
            print("Uso:")
            print("  python simulador_catraca.py entrada FUNC001")
            print("  python simulador_catraca.py saida FUNC001")
            print("  python simulador_catraca.py dia")
    else:
        # Modo interativo
        simular_dia_trabalho()
