"""
Módulo de shutdown remoto para Windows e Linux
"""
import subprocess
import logging
import paramiko
from pathlib import Path
import json
import os
import base64

logger = logging.getLogger(__name__)


class RemoteShutdown:
    def __init__(self):
        # Tenta carregar configuração opcional
        self.config = {}
        try:
            config_path = Path('config/config.json')
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
        except Exception:
            self.config = {}
    
    def shutdown_windows_wmi(self, ip_address, username, password):
        """
        Desliga computador Windows usando WMI via PowerShell (mais confiável)
        
        Args:
            ip_address: IP do computador
            username: Usuário administrador
            password: Senha
        
        Returns:
            bool: True se sucesso
        """
        try:
            # Primeiro, adicionar IP aos TrustedHosts usando winrm (não requer elevação)
            logger.info(f"Configurando TrustedHosts para {ip_address}...")
            try:
                # Usar winrm.cmd que é mais permissivo
                config_result = subprocess.run(
                    ["winrm", "set", "winrm/config/client", f"@{{TrustedHosts=\"{ip_address}\"}}"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if config_result.returncode == 0:
                    logger.info(f"TrustedHosts configurado para {ip_address}")
                else:
                    logger.warning(f"Não foi possível configurar TrustedHosts automaticamente")
            except Exception as e:
                logger.warning(f"TrustedHosts: {e}")
            
            # Criar script PowerShell inline para shutdown via WMI
            ps_script = f"""
$password = ConvertTo-SecureString '{password}' -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential('{username}', $password)
$result = Invoke-Command -ComputerName {ip_address} -Credential $cred -ScriptBlock {{
    Stop-Computer -Force
}} -ErrorAction Stop
exit 0
"""
            
            # Executar PowerShell
            cmd = ['powershell', '-Command', ps_script]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info(f"Shutdown WMI enviado para {ip_address}")
                return True
            else:
                logger.error(f"Erro WMI em {ip_address}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout ao desligar {ip_address} via WMI")
            return False
        except Exception as e:
            logger.error(f"Erro ao usar WMI em {ip_address}: {e}")
            return False
    
    def shutdown_windows(self, ip_address, username=None, password=None):
        """
        Desliga computador Windows remotamente usando shutdown
        
        Para uso completo, instale PsExec: https://docs.microsoft.com/sysinternals/downloads/psexec
        
        Args:
            ip_address: IP do computador
            username: Usuário (opcional)
            password: Senha (opcional)
        
        Returns:
            bool: True se sucesso, False caso contrário
        """
        try:
            # Método 1: Usando shutdown do Windows (requer permissões)
            # shutdown /s /m \\IP /t 0 /f
            
            # Se houver credenciais, tenta mapear sessão IPC primeiro
            mapped = False
            mapped_format = None
            if username and password:
                # Tenta diferentes formatos de usuário para autenticar sessão IPC
                user_variants = [
                    username,
                    f'.\\{username}',  # conta local
                ]
                for u in user_variants:
                    try:
                        # Primeiro limpar conexões antigas
                        cleanup_cmd = ['net', 'use', f'\\\\{ip_address}\\IPC$', '/delete', '/yes']
                        subprocess.run(cleanup_cmd, capture_output=True, text=True, timeout=5)
                        
                        # Mapear com credenciais
                        map_cmd = [
                            'net', 'use', f'\\\\{ip_address}\\IPC$', password, f'/user:{u}'
                        ]
                        map_res = subprocess.run(map_cmd, capture_output=True, text=True, timeout=15)
                        if map_res.returncode == 0:
                            mapped = True
                            mapped_format = u
                            logger.info(f"Sessão IPC autenticada com sucesso: {u}")
                            break
                        else:
                            logger.warning(f"Falha ao autenticar sessão IPC com '{u}': {map_res.stderr.strip()}")
                    except Exception as e:
                        logger.warning(f"Erro ao executar net use com '{u}': {e}")

            cmd = [
                'shutdown',
                '/s',  # Shutdown
                '/m', f'\\\\{ip_address}',  # Máquina remota
                '/t', '10',  # Tempo em segundos
                '/f',  # Força fechar aplicações
                '/c', 'Desligamento automático - Sistema IoT'
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=int(self.config.get('shutdown', {}).get('timeout', 30))
            )
            
            if result.returncode == 0:
                logger.info(f"Shutdown Windows enviado para {ip_address}")
                
                # Limpar sessão IPC após shutdown
                if mapped:
                    try:
                        cleanup_cmd = ['net', 'use', f'\\\\{ip_address}\\IPC$', '/delete', '/yes']
                        subprocess.run(cleanup_cmd, capture_output=True, text=True, timeout=5)
                    except Exception:
                        pass
                
                return True
            else:
                logger.error(f"Erro ao desligar {ip_address}: {result.stderr}")
                
                # Se shutdown tradicional falhou mas temos credenciais, tentar WMI
                if username and password:
                    logger.info("Tentando método alternativo via WMI/PowerShell...")
                    wmi_success = self.shutdown_windows_wmi(ip_address, username, password)
                    if wmi_success:
                        return True
                
                # Limpar sessão em caso de erro
                if mapped:
                    try:
                        cleanup_cmd = ['net', 'use', f'\\\\{ip_address}\\IPC$', '/delete', '/yes']
                        subprocess.run(cleanup_cmd, capture_output=True, text=True, timeout=5)
                    except Exception:
                        pass
                
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout ao desligar {ip_address}")
            return False
        except Exception as e:
            logger.error(f"Erro ao desligar Windows {ip_address}: {e}")
            return False
        finally:
            # Limpa a sessão IPC mapeada
            if 'mapped' in locals() and mapped:
                try:
                    del_cmd = ['net', 'use', f'\\\\{ip_address}', '/delete', '/y']
                    subprocess.run(del_cmd, capture_output=True, text=True, timeout=10)
                except Exception:
                    pass
    
    def shutdown_windows_psexec(self, ip_address, username, password, psexec_path='PsExec.exe'):
        """
        Desliga computador Windows usando PsExec (mais robusto)
        
        Download PsExec: https://docs.microsoft.com/sysinternals/downloads/psexec
        
        Args:
            ip_address: IP do computador
            username: Usuário administrativo
            password: Senha
            psexec_path: Caminho para PsExec.exe
        
        Returns:
            bool: True se sucesso, False caso contrário
        """
        try:
            cmd = [
                psexec_path,
                f'\\\\{ip_address}',
                '-u', username,
                '-p', password,
                '-accepteula',
                'shutdown',
                '/s',
                '/t', '10',
                '/f'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=int(self.config.get('shutdown', {}).get('timeout', 30))
            )
            
            if result.returncode == 0 or 'successfully' in result.stdout.lower():
                logger.info(f"Shutdown PsExec enviado para {ip_address}")
                return True
            else:
                logger.error(f"Erro PsExec em {ip_address}: {result.stderr}")
                return False
                
        except FileNotFoundError:
            logger.error(f"PsExec não encontrado em {psexec_path}")
            return False
        except Exception as e:
            logger.error(f"Erro ao usar PsExec em {ip_address}: {e}")
            return False
    
    def shutdown_linux(self, ip_address, username, password=None, ssh_key_path=None, port=22):
        """
        Desliga computador Linux usando SSH
        
        Args:
            ip_address: IP do computador
            username: Usuário SSH
            password: Senha (ou None se usar chave SSH)
            ssh_key_path: Caminho para chave privada SSH
            port: Porta SSH (padrão 22)
        
        Returns:
            bool: True se sucesso, False caso contrário
        """
        try:
            # Cria cliente SSH
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Conecta
            if ssh_key_path:
                # Autenticação por chave
                ssh.connect(
                    hostname=ip_address,
                    port=port,
                    username=username,
                    key_filename=ssh_key_path,
                    timeout=10
                )
            else:
                # Autenticação por senha
                ssh.connect(
                    hostname=ip_address,
                    port=port,
                    username=username,
                    password=password,
                    timeout=10
                )
            
            # Executa comando de shutdown
            # sudo shutdown -h now (pode requerer configuração NOPASSWD no sudoers)
            stdin, stdout, stderr = ssh.exec_command('sudo shutdown -h +1')
            
            exit_status = stdout.channel.recv_exit_status()
            ssh.close()
            
            if exit_status == 0:
                logger.info(f"Shutdown Linux enviado para {ip_address}")
                return True
            else:
                error_msg = stderr.read().decode()
                logger.error(f"Erro ao desligar Linux {ip_address}: {error_msg}")
                return False
                
        except paramiko.AuthenticationException:
            logger.error(f"Falha de autenticação SSH em {ip_address}")
            return False
        except paramiko.SSHException as e:
            logger.error(f"Erro SSH em {ip_address}: {e}")
            return False
        except Exception as e:
            logger.error(f"Erro ao desligar Linux {ip_address}: {e}")
            return False
    
    def shutdown_device(self, ip_address, os_type='windows', credentials=None):
        """
        Desliga dispositivo baseado no tipo de SO
        
        Args:
            ip_address: IP do computador
            os_type: Tipo de SO ('windows' ou 'linux')
            credentials: Dicionário com credenciais
                Para Windows: {'username': 'admin', 'password': 'senha'}
                Para Linux: {'username': 'user', 'password': 'senha', 'ssh_key': '/path/key'}
        
        Returns:
            bool: True se sucesso, False caso contrário
        """
        credentials = credentials or {}
        
        if os_type.lower() == 'windows':
            username = credentials.get('username')
            password = credentials.get('password')
            
            # Tenta com PsExec se credenciais fornecidas
            if username and password:
                success = self.shutdown_windows_psexec(ip_address, username, password)
                if success:
                    return True
            
            # Fallback para shutdown nativo
            return self.shutdown_windows(ip_address, username, password)
            
        elif os_type.lower() == 'linux':
            username = credentials.get('username', 'root')
            password = credentials.get('password')
            ssh_key = credentials.get('ssh_key')
            
            return self.shutdown_linux(ip_address, username, password, ssh_key)
        
        else:
            logger.error(f"Tipo de SO não suportado: {os_type}")
            return False
