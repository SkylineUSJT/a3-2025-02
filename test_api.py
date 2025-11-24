"""
Script de teste para validar a nova API REST
Executa testes em todos os endpoints principais
"""
import requests
import json
from datetime import datetime

BASE_URL = 'http://localhost:5000/api'

def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_health():
    """Testa endpoint de health check"""
    print_section("TESTE: Health Check")
    response = requests.get(f'{BASE_URL}/health')
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_funcionarios():
    """Testa CRUD de funcionários"""
    print_section("TESTE: Funcionários")
    
    # CREATE
    print("\n1. Criando funcionário...")
    data = {
        "nome": "Carlos Teste",
        "cargo": "Testador",
        "rfid": "TEST001",
        "unidade": "QA"
    }
    response = requests.post(f'{BASE_URL}/funcionarios', json=data)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    func_id = result.get('idFunc')
    
    # READ
    print("\n2. Listando funcionários...")
    response = requests.get(f'{BASE_URL}/funcionarios')
    print(f"Status: {response.status_code}")
    print(f"Total: {len(response.json()['funcionarios'])} funcionários")
    
    # READ ONE
    print(f"\n3. Buscando funcionário {func_id}...")
    response = requests.get(f'{BASE_URL}/funcionarios/{func_id}')
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # UPDATE
    print(f"\n4. Atualizando funcionário {func_id}...")
    data = {"cargo": "Testador Sênior"}
    response = requests.put(f'{BASE_URL}/funcionarios/{func_id}', json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return func_id

def test_computadores(func_id):
    """Testa CRUD de computadores"""
    print_section("TESTE: Computadores")
    
    # CREATE
    print("\n1. Criando computador...")
    data = {
        "hostname": "PC-TESTE",
        "ip": "192.168.1.99",
        "mac": "FF:EE:DD:CC:BB:AA",
        "osSystem": "windows",
        "idFuncionario": func_id
    }
    response = requests.post(f'{BASE_URL}/computadores', json=data)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    comp_id = result.get('idComputador')
    
    # READ
    print("\n2. Listando computadores...")
    response = requests.get(f'{BASE_URL}/computadores')
    print(f"Status: {response.status_code}")
    computadores = response.json()['computadores']
    print(f"Total: {len(computadores)} computadores")
    if computadores:
        print(f"Exemplo: {computadores[0]['hostname']} - Func: {computadores[0].get('funcionario_nome')}")
    
    # UPDATE
    print(f"\n3. Atualizando computador {comp_id}...")
    data = {"ip": "192.168.1.100"}
    response = requests.put(f'{BASE_URL}/computadores/{comp_id}', json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return comp_id

def test_catracas():
    """Testa CRUD de catracas"""
    print_section("TESTE: Catracas")
    
    # CREATE
    print("\n1. Criando catraca...")
    data = {
        "nome": "Catraca Teste",
        "localizacao": "Entrada Teste",
        "status": "ativo"
    }
    response = requests.post(f'{BASE_URL}/catracas', json=data)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    catraca_id = result.get('idCatraca')
    
    # READ
    print("\n2. Listando catracas...")
    response = requests.get(f'{BASE_URL}/catracas')
    print(f"Status: {response.status_code}")
    print(f"Total: {len(response.json()['catracas'])} catracas")
    
    return catraca_id

def test_eventos(func_id, comp_id, catraca_id):
    """Testa eventos"""
    print_section("TESTE: Eventos")
    
    # CREATE
    print("\n1. Registrando evento de entrada...")
    data = {
        "tipo": "entrada",
        "idCatraca": catraca_id,
        "idComputador": comp_id,
        "idFuncionario": func_id
    }
    response = requests.post(f'{BASE_URL}/eventos', json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # CREATE
    print("\n2. Registrando evento de saída...")
    data = {
        "tipo": "saida",
        "idCatraca": catraca_id,
        "idComputador": comp_id,
        "idFuncionario": func_id
    }
    response = requests.post(f'{BASE_URL}/eventos', json=data)
    print(f"Status: {response.status_code}")
    
    # READ
    print("\n3. Listando eventos...")
    response = requests.get(f'{BASE_URL}/eventos?limit=5')
    print(f"Status: {response.status_code}")
    eventos = response.json()['eventos']
    print(f"Total: {len(eventos)} eventos")
    for ev in eventos[:3]:
        print(f"  - {ev['tipo']} | {ev.get('funcionario_nome')} | {ev.get('catraca_nome')}")

def test_excecoes(func_id):
    """Testa exceções"""
    print_section("TESTE: Exceções")
    
    # CREATE
    print("\n1. Criando exceção...")
    data = {
        "motivo": "Teste de Férias",
        "idFuncionario": func_id,
        "duracao": 5
    }
    response = requests.post(f'{BASE_URL}/excecoes', json=data)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    excecao_id = result.get('idExcec')
    
    # READ
    print("\n2. Listando exceções...")
    response = requests.get(f'{BASE_URL}/excecoes')
    print(f"Status: {response.status_code}")
    excecoes = response.json()['excecoes']
    print(f"Total: {len(excecoes)} exceções")
    for ex in excecoes:
        print(f"  - {ex['motivo']} | {ex.get('funcionario_nome')} | {ex.get('duracao')} dias")
    
    return excecao_id

def test_access_flow():
    """Testa fluxo de entrada/saída"""
    print_section("TESTE: Fluxo de Acesso (Entrada/Saída)")
    
    print("\n1. Simulando entrada via RFID...")
    data = {
        "rfid": "TEST001",
        "idCatraca": 1
    }
    response = requests.post(f'{BASE_URL}/access/entry', json=data)
    print(f"Status: {response.status_code}")
    if response.status_code in [200, 202]:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"Erro: {response.json()}")
    
    print("\n2. Aguardando 3 segundos...")
    import time
    time.sleep(3)
    
    print("\n3. Simulando saída via RFID...")
    data = {
        "rfid": "TEST001",
        "idCatraca": 1
    }
    response = requests.post(f'{BASE_URL}/access/exit', json=data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"Erro: {response.json()}")

def cleanup(func_id, comp_id, catraca_id, excecao_id):
    """Remove dados de teste"""
    print_section("LIMPEZA: Removendo dados de teste")
    
    print(f"\n1. Removendo exceção {excecao_id}...")
    response = requests.delete(f'{BASE_URL}/excecoes/{excecao_id}')
    print(f"Status: {response.status_code}")
    
    print(f"\n2. Removendo computador {comp_id}...")
    response = requests.delete(f'{BASE_URL}/computadores/{comp_id}')
    print(f"Status: {response.status_code}")
    
    print(f"\n3. Removendo catraca {catraca_id}...")
    response = requests.delete(f'{BASE_URL}/catracas/{catraca_id}')
    print(f"Status: {response.status_code}")
    
    print(f"\n4. Removendo funcionário {func_id}...")
    response = requests.delete(f'{BASE_URL}/funcionarios/{func_id}')
    print(f"Status: {response.status_code}")

def main():
    print("=" * 70)
    print("  TESTE COMPLETO DA API REST v2.0")
    print("  Certifique-se de que o servidor está rodando!")
    print("=" * 70)
    
    try:
        # Health Check
        if not test_health():
            print("\n❌ Servidor não está respondendo!")
            return
        
        # Testes CRUD
        func_id = test_funcionarios()
        comp_id = test_computadores(func_id)
        catraca_id = test_catracas()
        test_eventos(func_id, comp_id, catraca_id)
        excecao_id = test_excecoes(func_id)
        
        # Teste fluxo de acesso
        test_access_flow()
        
        # Limpeza
        cleanup(func_id, comp_id, catraca_id, excecao_id)
        
        print("\n" + "=" * 70)
        print("  ✅ TODOS OS TESTES CONCLUÍDOS!")
        print("=" * 70)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERRO: Não foi possível conectar ao servidor!")
        print("   Certifique-se de que o servidor está rodando em http://localhost:5000")
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
