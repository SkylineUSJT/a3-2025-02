"""
Script para inicializar o sistema completo com dados de teste
"""
import sys
import os
import time
sys.path.append(os.path.dirname(__file__))

from backend.modules.database import Database

def setup_test_data():
    """Popula o banco com dados de teste"""
    print("=" * 70)
    print("  INICIALIZANDO SISTEMA SKYLINE A3")
    print("=" * 70)
    
    # Inicializa banco
    db = Database()
    db.initialize()
    print("\n✅ Banco de dados inicializado")
    
    # Verifica se já tem dados
    funcionarios = db.get_all_funcionarios()
    if len(funcionarios) > 0:
        print(f"\n⚠️  Banco já possui {len(funcionarios)} funcionários cadastrados - pulando inserção de dados de teste")
        return db
    
    # Cria funcionários
    print("\n📋 Criando funcionários...")
    func1_id = db.add_funcionario("João Silva", "Desenvolvedor", "FUNC001", "TI")
    func2_id = db.add_funcionario("Maria Santos", "Analista", "FUNC002", "RH")
    func3_id = db.add_funcionario("Pedro Costa", "Designer", "FUNC003", "Marketing")
    print(f"   ✅ {func1_id} - João Silva (FUNC001)")
    print(f"   ✅ {func2_id} - Maria Santos (FUNC002)")
    print(f"   ✅ {func3_id} - Pedro Costa (FUNC003)")
    
    # Cria computadores
    print("\n💻 Criando computadores...")
    comp1_id = db.add_computador("PC-JOAO", "192.168.1.10", "00:11:22:33:44:55", "windows", func1_id)
    comp2_id = db.add_computador("PC-MARIA", "192.168.1.11", "AA:BB:CC:DD:EE:FF", "windows", func2_id)
    comp3_id = db.add_computador("PC-PEDRO", "192.168.1.12", "11:22:33:44:55:66", "linux", func3_id)
    print(f"   ✅ {comp1_id} - PC-JOAO (João Silva)")
    print(f"   ✅ {comp2_id} - PC-MARIA (Maria Santos)")
    print(f"   ✅ {comp3_id} - PC-PEDRO (Pedro Costa)")
    
    # Cria catracas
    print("\n🚪 Criando catracas...")
    catraca1_id = db.add_catraca("Catraca Principal", "Entrada Bloco A", "ativo")
    catraca2_id = db.add_catraca("Catraca Secundária", "Entrada Bloco B", "ativo")
    print(f"   ✅ {catraca1_id} - Catraca Principal (Bloco A)")
    print(f"   ✅ {catraca2_id} - Catraca Secundária (Bloco B)")
    
    # Cria eventos de exemplo
    print("\n📝 Criando eventos de exemplo...")
    db.add_evento("entrada", catraca1_id, comp1_id, func1_id)
    db.add_evento("wake", None, comp1_id, func1_id)
    db.add_evento("entrada", catraca2_id, comp2_id, func2_id)
    db.add_evento("wake", None, comp2_id, func2_id)
    db.add_evento("saida", catraca1_id, comp1_id, func1_id)
    db.add_evento("shutdown", None, comp1_id, func1_id)
    print("   ✅ 6 eventos criados")
    
    # Cria exceções
    print("\n⚠️ Criando exceções...")
    db.add_excecao("Férias", func1_id, 15)
    db.add_excecao("Home Office", func2_id, 3)
    print("   ✅ 2 exceções criadas")
    
    print("\n" + "=" * 70)
    print("  ✅ SISTEMA INICIALIZADO COM SUCESSO!")
    print("=" * 70)
    print("\n📊 Resumo:")
    print(f"   • {len(db.get_all_funcionarios())} funcionários")
    print(f"   • {len(db.get_all_computadores())} computadores")
    print(f"   • {len(db.get_all_catracas())} catracas")
    print(f"   • {len(db.get_eventos(limit=100))} eventos")
    print(f"   • {len(db.get_excecoes(limit=100))} exceções")
    
    print("\n🚀 Iniciando servidor Flask...")
    print("   Acesse: http://localhost:5000")
    print("   Usuário: admin | Senha: 123")
    print("\n" + "=" * 70)

if __name__ == '__main__':
    try:
        setup_test_data()
        
        # Importa e inicia o servidor Flask
        from backend.app import app, db as app_db, mqtt_client, logger
        
        # Inicializa MQTT
        mqtt_client.start()
        
        # Inicia servidor
        logger.info("Sistema IoT de Automação iniciado")
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Sistema encerrado pelo usuário")
    except Exception as e:
        print(f"\n\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
