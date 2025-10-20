"""
Script de exemplo para testar o sistema
"""
import requests
import json

BASE_URL = 'http://127.0.0.1:5000/api'

def test_health():
    """Testa se o servidor está online"""
    response = requests.get(f'{BASE_URL}/health')
    print(f"Health Check: {response.json()}")

def cadastrar_dispositivo():
    """Cadastra um dispositivo de teste"""
    device = {
        "user_id": "FUNC001",
        "hostname": "PC-JOAO-SILVA",
        "mac_address": "00:11:22:33:44:55",
        "ip_address": "192.168.1.100",
        "os_type": "windows",
        "credentials": {
            "username": "admin",
            "password": "senha123"
        }
    }
    
    response = requests.post(f'{BASE_URL}/devices', json=device)
    print(f"Cadastro: {response.json()}")

def simular_entrada():
    """Simula entrada de funcionário"""
    data = {"user_id": "FUNC001"}
    response = requests.post(f'{BASE_URL}/access/entry', json=data)
    print(f"Entrada: {response.json()}")

def simular_saida():
    """Simula saída de funcionário"""
    data = {"user_id": "FUNC001"}
    response = requests.post(f'{BASE_URL}/access/exit', json=data)
    print(f"Saída: {response.json()}")

def listar_dispositivos():
    """Lista todos os dispositivos"""
    response = requests.get(f'{BASE_URL}/devices')
    print(f"Dispositivos: {json.dumps(response.json(), indent=2)}")

def ver_logs():
    """Lista últimos logs"""
    response = requests.get(f'{BASE_URL}/logs?limit=10')
    print(f"Logs: {json.dumps(response.json(), indent=2)}")

if __name__ == '__main__':
    print("=== TESTE DO SISTEMA IoT ===\n")
    
    print("1. Verificando servidor...")
    test_health()
    print()
    
    print("2. Cadastrando dispositivo...")
    cadastrar_dispositivo()
    print()
    
    print("3. Listando dispositivos...")
    listar_dispositivos()
    print()
    
    print("4. Simulando entrada (liga PC)...")
    simular_entrada()
    print()
    
    print("5. Simulando saída (desliga PC)...")
    simular_saida()
    print()
    
    print("6. Visualizando logs...")
    ver_logs()
    print()
    
    print("=== TESTES CONCLUÍDOS ===")
