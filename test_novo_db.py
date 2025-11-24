"""
Script de teste para validar o novo modelo do banco de dados
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from backend.modules.database import Database

def test_database():
    print("=" * 60)
    print("TESTE DO NOVO MODELO DE BANCO DE DADOS")
    print("=" * 60)
    
    # Inicializa banco
    db = Database('backend/database/test_iot_system.db')
    db.initialize()
    print("✅ Banco de dados inicializado\n")
    
    # Testa Funcionários
    print("📋 TESTANDO FUNCIONÁRIOS")
    print("-" * 60)
    func1_id = db.add_funcionario(
        nome="João Silva",
        cargo="Desenvolvedor",
        rfid="FUNC001",
        unidade="TI"
    )
    print(f"✅ Funcionário adicionado - ID: {func1_id}")
    
    func2_id = db.add_funcionario(
        nome="Maria Santos",
        cargo="Analista",
        rfid="FUNC002",
        unidade="RH"
    )
    print(f"✅ Funcionário adicionado - ID: {func2_id}")
    
    funcionarios = db.get_all_funcionarios()
    print(f"📊 Total de funcionários: {len(funcionarios)}")
    for f in funcionarios:
        print(f"   - {f['nome']} ({f['cargo']}) - RFID: {f['rfid']}")
    print()
    
    # Testa Computadores
    print("💻 TESTANDO COMPUTADORES")
    print("-" * 60)
    comp1_id = db.add_computador(
        hostname="PC-JOAO",
        ip="192.168.1.10",
        mac="00:11:22:33:44:55",
        osSystem="windows",
        idFuncionario=func1_id
    )
    print(f"✅ Computador adicionado - ID: {comp1_id}")
    
    comp2_id = db.add_computador(
        hostname="PC-MARIA",
        ip="192.168.1.11",
        mac="AA:BB:CC:DD:EE:FF",
        osSystem="linux",
        idFuncionario=func2_id
    )
    print(f"✅ Computador adicionado - ID: {comp2_id}")
    
    computadores = db.get_all_computadores()
    print(f"📊 Total de computadores: {len(computadores)}")
    for c in computadores:
        print(f"   - {c['hostname']} ({c['ip']}) - Func: {c.get('funcionario_nome', 'N/A')}")
    print()
    
    # Testa Catracas
    print("🚪 TESTANDO CATRACAS")
    print("-" * 60)
    catraca1_id = db.add_catraca(
        nome="Catraca Principal",
        localizacao="Entrada Bloco A",
        status="ativo"
    )
    print(f"✅ Catraca adicionada - ID: {catraca1_id}")
    
    catraca2_id = db.add_catraca(
        nome="Catraca Secundária",
        localizacao="Entrada Bloco B",
        status="ativo"
    )
    print(f"✅ Catraca adicionada - ID: {catraca2_id}")
    
    catracas = db.get_all_catracas()
    print(f"📊 Total de catracas: {len(catracas)}")
    for c in catracas:
        print(f"   - {c['nome']} ({c['localizacao']}) - Status: {c['status']}")
    print()
    
    # Testa Eventos
    print("📝 TESTANDO EVENTOS")
    print("-" * 60)
    evento1_id = db.add_evento(
        tipo="entrada",
        idCatraca=catraca1_id,
        idComputador=comp1_id,
        idFuncionario=func1_id
    )
    print(f"✅ Evento de entrada registrado - ID: {evento1_id}")
    
    evento2_id = db.add_evento(
        tipo="saida",
        idCatraca=catraca1_id,
        idComputador=comp1_id,
        idFuncionario=func1_id
    )
    print(f"✅ Evento de saída registrado - ID: {evento2_id}")
    
    eventos = db.get_eventos(limit=10)
    print(f"📊 Total de eventos: {len(eventos)}")
    for e in eventos:
        print(f"   - {e['tipo']} | Func: {e.get('funcionario_nome')} | Catraca: {e.get('catraca_nome')}")
    print()
    
    # Testa Exceções
    print("⚠️ TESTANDO EXCEÇÕES")
    print("-" * 60)
    excecao1_id = db.add_excecao(
        motivo="Férias",
        idFuncionario=func1_id,
        duracao=15
    )
    print(f"✅ Exceção adicionada - ID: {excecao1_id}")
    
    excecao2_id = db.add_excecao(
        motivo="Home Office",
        idFuncionario=func2_id,
        duracao=3
    )
    print(f"✅ Exceção adicionada - ID: {excecao2_id}")
    
    excecoes = db.get_excecoes()
    print(f"📊 Total de exceções: {len(excecoes)}")
    for e in excecoes:
        print(f"   - {e['motivo']} | Func: {e['funcionario_nome']} | Duração: {e.get('duracao', 'N/A')} dias")
    print()
    
    # Testa métodos de compatibilidade
    print("🔄 TESTANDO COMPATIBILIDADE COM CÓDIGO ANTIGO")
    print("-" * 60)
    device = db.get_device_by_user("FUNC001")
    if device:
        print(f"✅ get_device_by_user: {device['hostname']}")
    
    all_devices = db.get_all_devices()
    print(f"✅ get_all_devices: {len(all_devices)} dispositivos")
    
    logs = db.get_access_logs(limit=5)
    print(f"✅ get_access_logs: {len(logs)} logs")
    print()
    
    print("=" * 60)
    print("✅ TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
    print("=" * 60)

if __name__ == '__main__':
    try:
        test_database()
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
