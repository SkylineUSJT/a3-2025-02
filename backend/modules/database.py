"""
Módulo de gerenciamento de banco de dados SQLite v2.0
Estrutura atualizada com 6 tabelas e relacionamentos
"""
import sqlite3
import json
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path='backend/database/iot_system.db'):
        self.db_path = db_path
        
    def get_connection(self):
        """Cria conexão com banco de dados"""
        conn = sqlite3.connect(self.db_path, timeout=10, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA busy_timeout=5000')
            conn.execute('PRAGMA synchronous=NORMAL')
            conn.execute('PRAGMA foreign_keys=ON')
        except Exception:
            pass
        return conn
    
    def initialize(self):
        """Inicializa tabelas do banco de dados v2.0"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabela de funcionários
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS funcionario (
                idFunc INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                cargo TEXT NOT NULL,
                rfid TEXT NOT NULL UNIQUE,
                unidade TEXT NOT NULL,
                alterado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de computadores
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS computador (
                idComputador INTEGER PRIMARY KEY AUTOINCREMENT,
                hostname TEXT NOT NULL,
                ip TEXT NOT NULL,
                mac TEXT NOT NULL,
                osSystem TEXT NOT NULL,
                idFuncionario INTEGER,
                FOREIGN KEY (idFuncionario) REFERENCES funcionario(idFunc) ON DELETE SET NULL
            )
        ''')
        
        # Tabela de catracas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS catraca (
                idCatraca INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                localizacao TEXT NOT NULL,
                status TEXT DEFAULT 'ativo',
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de eventos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS evento (
                idEvento INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,
                data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                idCatraca INTEGER,
                idComputador INTEGER,
                idFuncionario INTEGER,
                FOREIGN KEY (idCatraca) REFERENCES catraca(idCatraca) ON DELETE SET NULL,
                FOREIGN KEY (idComputador) REFERENCES computador(idComputador) ON DELETE SET NULL,
                FOREIGN KEY (idFuncionario) REFERENCES funcionario(idFunc) ON DELETE SET NULL
            )
        ''')
        
        # Tabela de exceções
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS excecoes (
                idExcec INTEGER PRIMARY KEY AUTOINCREMENT,
                motivo TEXT NOT NULL,
                idFuncionario INTEGER NOT NULL,
                duracao INTEGER,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (idFuncionario) REFERENCES funcionario(idFunc) ON DELETE CASCADE
            )
        ''')
        
        # Tabela de configurações
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de usuários do sistema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                user_type TEXT NOT NULL DEFAULT 'usuario',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Banco de dados v2.0 inicializado com sucesso")
    
    # ==================== FUNCIONÁRIOS ====================
    
    def add_funcionario(self, nome, cargo, rfid, unidade):
        """Adiciona novo funcionário"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO funcionario (nome, cargo, rfid, unidade)
                VALUES (?, ?, ?, ?)
            ''', (nome, cargo, rfid, unidade))
            conn.commit()
            return cursor.lastrowid
        except Exception:
            conn.rollback()
            raise
        finally:
            try:
                conn.close()
            except Exception:
                pass
    
    def get_funcionario_by_id(self, idFunc):
        """Busca funcionário por ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM funcionario WHERE idFunc = ?', (idFunc,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_funcionario_by_rfid(self, rfid):
        """Busca funcionário por RFID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM funcionario WHERE rfid = ?', (rfid,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_all_funcionarios(self):
        """Lista todos os funcionários"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM funcionario')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def update_funcionario(self, idFunc, nome=None, cargo=None, rfid=None, unidade=None):
        """Atualiza dados do funcionário"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            updates = []
            params = []
            if nome:
                updates.append('nome = ?')
                params.append(nome)
            if cargo:
                updates.append('cargo = ?')
                params.append(cargo)
            if rfid:
                updates.append('rfid = ?')
                params.append(rfid)
            if unidade:
                updates.append('unidade = ?')
                params.append(unidade)
            
            if updates:
                updates.append('alterado_em = CURRENT_TIMESTAMP')
                params.append(idFunc)
                cursor.execute(f'''
                    UPDATE funcionario SET {', '.join(updates)}
                    WHERE idFunc = ?
                ''', params)
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            try:
                conn.close()
            except Exception:
                pass
    
    def delete_funcionario(self, idFunc):
        """Exclui um funcionário"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM funcionario WHERE idFunc = ?', (idFunc,))
            conn.commit()
        finally:
            try:
                conn.close()
            except Exception:
                pass
    
    # ==================== COMPUTADORES ====================
    
    def add_computador(self, hostname, ip, mac, osSystem, idFuncionario):
        """Adiciona novo computador"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO computador (hostname, ip, mac, osSystem, idFuncionario)
                VALUES (?, ?, ?, ?, ?)
            ''', (hostname, ip, mac, osSystem, idFuncionario))
            conn.commit()
            return cursor.lastrowid
        except Exception:
            conn.rollback()
            raise
        finally:
            try:
                conn.close()
            except Exception:
                pass
    
    def get_computador_by_id(self, idComputador):
        """Busca computador por ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM computador WHERE idComputador = ?', (idComputador,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_computador_by_funcionario(self, idFuncionario):
        """Busca computador vinculado ao funcionário"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM computador WHERE idFuncionario = ?', (idFuncionario,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_all_computadores(self):
        """Lista todos os computadores com JOIN de funcionário"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.*, f.nome as funcionario_nome
            FROM computador c
            LEFT JOIN funcionario f ON c.idFuncionario = f.idFunc
        ''')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def update_computador(self, idComputador, hostname=None, ip=None, mac=None, osSystem=None, idFuncionario=None):
        """Atualiza dados do computador"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            updates = []
            params = []
            if hostname:
                updates.append('hostname = ?')
                params.append(hostname)
            if ip:
                updates.append('ip = ?')
                params.append(ip)
            if mac:
                updates.append('mac = ?')
                params.append(mac)
            if osSystem:
                updates.append('osSystem = ?')
                params.append(osSystem)
            if idFuncionario is not None:
                updates.append('idFuncionario = ?')
                params.append(idFuncionario)
            
            if updates:
                params.append(idComputador)
                cursor.execute(f'''
                    UPDATE computador SET {', '.join(updates)}
                    WHERE idComputador = ?
                ''', params)
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            try:
                conn.close()
            except Exception:
                pass
    
    def delete_computador(self, idComputador):
        """Exclui um computador"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM computador WHERE idComputador = ?', (idComputador,))
            conn.commit()
        finally:
            try:
                conn.close()
            except Exception:
                pass
    
    # ==================== CATRACAS ====================
    
    def add_catraca(self, nome, localizacao, status='ativo'):
        """Adiciona nova catraca"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO catraca (nome, localizacao, status)
                VALUES (?, ?, ?)
            ''', (nome, localizacao, status))
            conn.commit()
            return cursor.lastrowid
        except Exception:
            conn.rollback()
            raise
        finally:
            try:
                conn.close()
            except Exception:
                pass
    
    def get_catraca_by_id(self, idCatraca):
        """Busca catraca por ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM catraca WHERE idCatraca = ?', (idCatraca,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_all_catracas(self):
        """Lista todas as catracas"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM catraca')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def update_catraca(self, idCatraca, nome=None, localizacao=None, status=None):
        """Atualiza dados da catraca"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            updates = []
            params = []
            if nome:
                updates.append('nome = ?')
                params.append(nome)
            if localizacao:
                updates.append('localizacao = ?')
                params.append(localizacao)
            if status:
                updates.append('status = ?')
                params.append(status)
            
            if updates:
                params.append(idCatraca)
                cursor.execute(f'''
                    UPDATE catraca SET {', '.join(updates)}
                    WHERE idCatraca = ?
                ''', params)
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            try:
                conn.close()
            except Exception:
                pass
    
    def delete_catraca(self, idCatraca):
        """Exclui uma catraca"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM catraca WHERE idCatraca = ?', (idCatraca,))
            conn.commit()
        finally:
            try:
                conn.close()
            except Exception:
                pass
    
    # ==================== EVENTOS ====================
    
    def add_evento(self, tipo, idCatraca=None, idComputador=None, idFuncionario=None):
        """Registra novo evento"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO evento (tipo, idCatraca, idComputador, idFuncionario)
                VALUES (?, ?, ?, ?)
            ''', (tipo, idCatraca, idComputador, idFuncionario))
            conn.commit()
            return cursor.lastrowid
        except Exception:
            conn.rollback()
            raise
        finally:
            try:
                conn.close()
            except Exception:
                pass
    
    def get_eventos(self, limit=50, idFuncionario=None, tipo=None):
        """Busca eventos com JOIN de funcionário, catraca e computador"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT e.*, 
                   f.nome as funcionario_nome,
                   c.nome as catraca_nome,
                   comp.hostname as computador_hostname
            FROM evento e
            LEFT JOIN funcionario f ON e.idFuncionario = f.idFunc
            LEFT JOIN catraca c ON e.idCatraca = c.idCatraca
            LEFT JOIN computador comp ON e.idComputador = comp.idComputador
        '''
        
        conditions = []
        params = []
        
        if idFuncionario:
            conditions.append('e.idFuncionario = ?')
            params.append(idFuncionario)
        
        if tipo:
            conditions.append('e.tipo = ?')
            params.append(tipo)
        
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        
        query += ' ORDER BY e.data DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def has_recent_evento(self, idFuncionario, tipo, window_seconds=3):
        """Verifica se há evento recente (anti-duplicação)"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 1 FROM evento
                WHERE idFuncionario = ? AND tipo = ?
                  AND data >= datetime('now', ?)
                LIMIT 1
            ''', (idFuncionario, tipo, f'-{int(window_seconds)} seconds'))
            row = cursor.fetchone()
            return row is not None
        finally:
            try:
                conn.close()
            except Exception:
                pass
    
    # ==================== EXCEÇÕES ====================
    
    def add_excecao(self, motivo, idFuncionario, duracao=None):
        """Adiciona nova exceção"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO excecoes (motivo, idFuncionario, duracao)
                VALUES (?, ?, ?)
            ''', (motivo, idFuncionario, duracao))
            conn.commit()
            return cursor.lastrowid
        except Exception:
            conn.rollback()
            raise
        finally:
            try:
                conn.close()
            except Exception:
                pass
    
    def get_excecoes(self, idFuncionario=None, limit=50):
        """Busca exceções com JOIN de funcionário"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if idFuncionario:
            cursor.execute('''
                SELECT e.*, f.nome as funcionario_nome
                FROM excecoes e
                LEFT JOIN funcionario f ON e.idFuncionario = f.idFunc
                WHERE e.idFuncionario = ?
                ORDER BY e.criado_em DESC
                LIMIT ?
            ''', (idFuncionario, limit))
        else:
            cursor.execute('''
                SELECT e.*, f.nome as funcionario_nome
                FROM excecoes e
                LEFT JOIN funcionario f ON e.idFuncionario = f.idFunc
                ORDER BY e.criado_em DESC
                LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def delete_excecao(self, idExcec):
        """Exclui uma exceção"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM excecoes WHERE idExcec = ?', (idExcec,))
            conn.commit()
        finally:
            try:
                conn.close()
            except Exception:
                pass
    
    # ==================== COMPATIBILIDADE (métodos antigos) ====================
    
    def add_device(self, user_id, hostname, mac_address, ip_address, os_type='windows', credentials=None):
        """COMPAT: add_device → cria funcionário + computador"""
        # Cria funcionário fictício se não existir
        func = self.get_funcionario_by_rfid(user_id)
        if not func:
            func_id = self.add_funcionario(f"Usuário {user_id}", "N/A", user_id, "N/A")
        else:
            func_id = func['idFunc']
        
        # Cria computador
        comp_id = self.add_computador(hostname, ip_address, mac_address, os_type, func_id)
        return comp_id
    
    def get_device_by_user(self, user_id):
        """COMPAT: get_device_by_user → busca por RFID"""
        func = self.get_funcionario_by_rfid(user_id)
        if not func:
            return None
        
        comp = self.get_computador_by_funcionario(func['idFunc'])
        if not comp:
            return None
        
        return {
            'id': comp['idComputador'],
            'user_id': user_id,
            'hostname': comp['hostname'],
            'mac_address': comp['mac'],
            'ip_address': comp['ip'],
            'os_type': comp['osSystem'],
            'status': 'offline'
        }
    
    def get_all_devices(self):
        """COMPAT: get_all_devices → retorna computadores"""
        computadores = self.get_all_computadores()
        devices = []
        for comp in computadores:
            func = self.get_funcionario_by_id(comp['idFuncionario']) if comp['idFuncionario'] else None
            devices.append({
                'id': comp['idComputador'],
                'user_id': func['rfid'] if func else 'N/A',
                'hostname': comp['hostname'],
                'mac_address': comp['mac'],
                'ip_address': comp['ip'],
                'os_type': comp['osSystem'],
                'status': 'offline'
            })
        return devices
    
    def get_device_by_id(self, device_id):
        """COMPAT: get_device_by_id → retorna computador"""
        comp = self.get_computador_by_id(device_id)
        if not comp:
            return None
        
        func = self.get_funcionario_by_id(comp['idFuncionario']) if comp['idFuncionario'] else None
        return {
            'id': comp['idComputador'],
            'user_id': func['rfid'] if func else 'N/A',
            'hostname': comp['hostname'],
            'mac_address': comp['mac'],
            'ip_address': comp['ip'],
            'os_type': comp['osSystem'],
            'status': 'offline'
        }
    
    def delete_device(self, device_id):
        """COMPAT: delete_device → remove computador"""
        self.delete_computador(device_id)
    
    def log_access(self, user_id, access_type, device_action=None, success=True):
        """COMPAT: log_access → cria evento"""
        func = self.get_funcionario_by_rfid(user_id)
        if not func:
            return
        
        comp = self.get_computador_by_funcionario(func['idFunc'])
        tipo = 'entrada' if access_type == 'entry' else 'saida'
        
        self.add_evento(tipo, idComputador=comp['idComputador'] if comp else None, 
                       idFuncionario=func['idFunc'])
    
    def get_access_logs(self, limit=50):
        """COMPAT: get_access_logs → retorna eventos"""
        eventos = self.get_eventos(limit=limit)
        logs = []
        for ev in eventos:
            logs.append({
                'id': ev['idEvento'],
                'user_id': ev.get('funcionario_nome', 'N/A'),
                'access_type': ev['tipo'],
                'action': ev['tipo'],
                'timestamp': ev['data'],
                'success': 1,
                'status': 'success',
                'turnstile_id': ev.get('catraca_nome')
            })
        return logs
    
    def has_recent_access(self, user_id, access_type, window_seconds=3):
        """COMPAT: has_recent_access → verifica evento recente"""
        func = self.get_funcionario_by_rfid(user_id)
        if not func:
            return False
        
        tipo = 'entrada' if access_type == 'entry' else 'saida'
        return self.has_recent_evento(func['idFunc'], tipo, window_seconds)
    
    def get_all_turnstiles(self):
        """COMPAT: get_all_turnstiles → retorna catracas"""
        catracas = self.get_all_catracas()
        return [{'id': c['idCatraca'], 'location': c['localizacao'], 'status': c['status']} for c in catracas]
    
    def add_turnstile(self, turnstile_id, location=None):
        """COMPAT: add_turnstile → adiciona catraca"""
        return self.add_catraca(f"Catraca {turnstile_id}", location or "N/A")
    
    def delete_turnstile(self, turnstile_id):
        """COMPAT: delete_turnstile → remove catraca"""
        self.delete_catraca(turnstile_id)
    
    # ==================== CONFIG & USERS ====================
    
    def set_config(self, key, value):
        """Define valor de configuração"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO config (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (key, value))
        conn.commit()
        conn.close()
    
    def get_config(self, key, default=None):
        """Busca valor de configuração"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM config WHERE key = ?', (key,))
        row = cursor.fetchone()
        conn.close()
        return row['value'] if row else default
    
    def get_user_by_username(self, username):
        """Busca usuário por nome de usuário"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def create_user(self, username, password, user_type='usuario'):
        """Cria novo usuário"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, password, user_type)
                VALUES (?, ?, ?)
            ''', (username, password, user_type))
            conn.commit()
            return cursor.lastrowid
        except Exception:
            conn.rollback()
            raise
        finally:
            try:
                conn.close()
            except Exception:
                pass
    
    def get_all_users(self):
        """Lista todos os usuários (sem senha)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, user_type, created_at FROM users')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
