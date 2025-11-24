"""
Módulo Wake-on-LAN para ligar computadores remotamente
"""
import socket
import struct
import logging
import subprocess
import sys
import time
from pathlib import Path
import json
import ipaddress

logger = logging.getLogger(__name__)


class WakeOnLAN:
    def __init__(self, broadcast_ip='255.255.255.255', port=9):
        # Carrega config opcional
        self.broadcast_ip = broadcast_ip
        self.port = port
        try:
            config_path = Path('config/config.json')
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                wol_cfg = cfg.get('wake_on_lan', {})
                self.broadcast_ip = wol_cfg.get('broadcast_ip', self.broadcast_ip)
                self.port = wol_cfg.get('port', self.port)
                verify_cfg = wol_cfg.get('verify', {})
                self.verify_timeout = int(verify_cfg.get('timeout', 10))
                self.verify_interval = float(verify_cfg.get('interval', 1))
                self.verify_ports = verify_cfg.get('ports', [445, 3389, 135])
            else:
                self.verify_timeout = 10
                self.verify_interval = 1.0
                self.verify_ports = [445, 3389, 135]
        except Exception:
            self.verify_timeout = 10
            self.verify_interval = 1.0
            self.verify_ports = [445, 3389, 135]
    
    def get_network_broadcast(self, ip_address):
        """
        Calcula o endereço de broadcast para um IP específico
        """
        try:
            # Tenta detectar a interface de rede do IP
            interface = ipaddress.ip_interface(f"{ip_address}/24")  # Assume /24
            return str(interface.network.broadcast_address)
        except:
            # Se falhar, retorna broadcast padrão da classe C
            parts = ip_address.split('.')
            if len(parts) == 4:
                return f"{parts[0]}.{parts[1]}.{parts[2]}.255"
            return "255.255.255.255"
    
    def create_magic_packet(self, mac_address):
        """
        Cria o Magic Packet para Wake-on-LAN
        Formato: 6 bytes FF + 16 repetições do MAC address
        """
        # Remove separadores do MAC address (: ou -)
        mac = mac_address.replace(':', '').replace('-', '').replace('.', '').upper()
        
        if len(mac) != 12:
            raise ValueError(f"Endereço MAC inválido: {mac_address}")
        
        # Valida se são apenas caracteres hexadecimais
        try:
            int(mac, 16)
        except ValueError:
            raise ValueError(f"Endereço MAC contém caracteres inválidos: {mac_address}")
        
        # Converte MAC para bytes
        mac_bytes = bytes.fromhex(mac)
        
        # Cria o Magic Packet: 6 bytes 0xFF + 16x MAC address
        magic_packet = b'\xFF' * 6 + mac_bytes * 16
        
        return magic_packet
    
    def wake(self, mac_address, broadcast_ip=None, port=None, target_ip=None):
        """
        Envia Magic Packet para acordar o computador
        
        Args:
            mac_address: Endereço MAC do computador (formato: XX:XX:XX:XX:XX:XX)
            broadcast_ip: IP de broadcast (padrão: auto-detectado)
            port: Porta UDP (padrão: 9)
            target_ip: IP do computador alvo (usado para calcular broadcast correto)
        
        Returns:
            bool: True se enviado com sucesso, False caso contrário
        """
        try:
            # Cria o Magic Packet
            magic_packet = self.create_magic_packet(mac_address)
            
            # Lista de broadcasts para tentar (aumenta chance de sucesso)
            broadcasts = []
            
            if broadcast_ip:
                broadcasts.append(broadcast_ip)
            else:
                # Se temos o IP do target, calcula o broadcast específico
                if target_ip:
                    network_broadcast = self.get_network_broadcast(target_ip)
                    broadcasts.append(network_broadcast)
                    logger.info(f"Broadcast calculado para {target_ip}: {network_broadcast}")
                
                # Adiciona broadcasts padrão
                broadcasts.extend([
                    '255.255.255.255',  # Broadcast geral
                    '192.168.18.255',   # Broadcast da rede local específica
                ])
            
            # Remove duplicatas mantendo ordem
            broadcasts = list(dict.fromkeys(broadcasts))
            
            # Portas para tentar (9 é padrão, 7 é alternativa comum)
            ports = [port or self.port, 7] if port != 7 else [7, 9]
            
            success_count = 0
            for bcast in broadcasts:
                for p in ports:
                    try:
                        # Cria socket UDP
                        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                        
                        # Envia o Magic Packet
                        sock.sendto(magic_packet, (bcast, p))
                        sock.close()
                        
                        logger.info(f"Magic Packet enviado para {mac_address} via {bcast}:{p}")
                        success_count += 1
                    except Exception as e:
                        logger.warning(f"Falha ao enviar para {bcast}:{p} - {e}")
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Erro ao enviar Wake-on-LAN para {mac_address}: {e}")
            return False

    # ---------- Verificação de dispositivo online ----------
    def _ping(self, ip: str, timeout_s: float = 1.0) -> bool:
        try:
            timeout_ms = max(100, int(timeout_s * 1000))
            if sys.platform.startswith('win'):
                # -n 1 pacotes, -w timeout em ms
                cmd = ['ping', '-n', '1', '-w', str(timeout_ms), ip]
            else:
                # -c 1 pacotes, -W timeout em s
                cmd = ['ping', '-c', '1', '-W', str(int(timeout_s)), ip]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s + 1)
            return res.returncode == 0
        except Exception:
            return False

    def _tcp_open(self, ip: str, port: int, timeout_s: float = 1.0) -> bool:
        try:
            with socket.create_connection((ip, port), timeout=timeout_s):
                return True
        except Exception:
            return False

    def is_online(self, ip: str, ports=None, timeout: float = None, interval: float = None) -> bool:
        """
        Verifica se o host está online usando ping e portas TCP comuns (Windows: 445, 3389, 135).
        Retorna True assim que qualquer verificação indicar disponibilidade.
        """
        ports = ports or self.verify_ports
        timeout = timeout if timeout is not None else self.verify_timeout
        interval = interval if interval is not None else self.verify_interval

        end_time = time.time() + timeout
        while time.time() < end_time:
            # 1) Ping
            if self._ping(ip, timeout_s=min(1.0, interval)):
                return True
            # 2) Portas TCP
            for p in ports:
                if self._tcp_open(ip, p, timeout_s=min(1.0, interval)):
                    return True
            time.sleep(interval)
        return False
    
    def wake_multiple(self, mac_addresses):
        """
        Envia Wake-on-LAN para múltiplos computadores
        
        Args:
            mac_addresses: Lista de endereços MAC
        
        Returns:
            dict: Resultado do envio para cada MAC
        """
        results = {}
        for mac in mac_addresses:
            results[mac] = self.wake(mac)
        return results
