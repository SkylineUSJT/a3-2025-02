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
    
    # Banco limpo - sem dados de teste
    print("\n📊 Banco de dados vazio e pronto para uso!")
    print("   • Use a interface web para cadastrar dados")
    print("   • Acesse: http://localhost:5000")
    print("   • Login: admin / admin123")
    
    
    print("\n🚀 Iniciando servidor Flask...")
    print("\n" + "=" * 70)
    
    return db

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
