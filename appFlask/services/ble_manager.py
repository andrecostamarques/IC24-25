import asyncio
import struct
import threading
from bleak import BleakClient, BleakScanner
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass

@dataclass
class SensorData:
    """Estrutura para dados do sensor"""
    sLed: int
    rSensor1: int
    rSensor2: int
    rSensor3: int
    rSensor4: int
    timeStamp: int
    interval_ms: int = 0

@dataclass
class DeviceInfo:
    """Informações do dispositivo BLE"""
    name: str
    address: str

class IntervalDetector:
    """Classe para detectar mudanças de intervalo baseado em sLed"""
    
    def __init__(self):
        self.last_sLed: Optional[int] = None
        self.last_timestamp_change: Optional[int] = None
        self.current_interval_ms: int = 0
        self.interval_zones: List[Dict] = []
    
    def detect_interval_change(self, sLed: int, timeStamp: int) -> None:
        """Detecta mudanças no intervalo baseado nas trocas de sLed"""
        # Se é a primeira leitura
        if self.last_sLed is None:
            self.last_sLed = sLed
            self.last_timestamp_change = timeStamp
            return
        
        # Se houve mudança no sLed
        if sLed != self.last_sLed:
            # Calcula quantos timestamps passaram
            timestamp_diff = timeStamp - self.last_timestamp_change
            # Converte para milissegundos (cada timestamp = 50ms)
            interval_ms = timestamp_diff * 50
            
            # Se o intervalo mudou significativamente (diferença > 100ms)
            if abs(interval_ms - self.current_interval_ms) > 100:
                # Registra mudança de zona
                zone_info = {
                    'timestamp': timeStamp,
                    'old_interval': self.current_interval_ms,
                    'new_interval': interval_ms,
                    'change_time': timestamp_diff
                }
                self.interval_zones.append(zone_info)
                
                # Mantém apenas últimas 20 mudanças de zona
                if len(self.interval_zones) > 20:
                    self.interval_zones.pop(0)
                
                print(f"🔄 MUDANÇA DE ZONA detectada em timestamp {timeStamp}:")
                print(f"   Intervalo anterior: {self.current_interval_ms}ms")
                print(f"   Novo intervalo: {interval_ms}ms") 
                print(f"   Diferença de timestamps: {timestamp_diff}")
                
                self.current_interval_ms = interval_ms
            
            # Atualiza referências
            self.last_sLed = sLed
            self.last_timestamp_change = timeStamp
    
    def reset(self) -> None:
        """Reset das variáveis de detecção"""
        self.last_sLed = None
        self.last_timestamp_change = None
        self.current_interval_ms = 0
        self.interval_zones.clear()
    
    def get_current_interval(self) -> int:
        """Retorna o intervalo atual em ms"""
        return self.current_interval_ms
    
    def get_zones(self) -> List[Dict]:
        """Retorna as zonas de intervalo detectadas"""
        return self.interval_zones.copy()

class BLEManager:
    """Gerenciador para conexões BLE e processamento de dados"""
    
    def __init__(self, device_name: str = "ESP32-SENSOR-SERVER"):
        self.DEVICE_NAME = device_name
        self.CHARACTERISTIC_UUID = "abcd1234-5678-90ab-cdef-1234567890ab"
        self.struct_format = "<B4iI"
        self.struct_size = struct.calcsize(self.struct_format)
        
        # Estado da conexão
        self.status = "Desconectado"
        self.client: Optional[BleakClient] = None
        self.available_devices: List[DeviceInfo] = []
        self.should_disconnect = False
        
        # Buffer para dados recebidos
        self.buffer = bytearray()
        
        # Callbacks para dados recebidos
        self.data_callbacks: List[Callable[[SensorData], None]] = []
        
        # Detector de intervalo
        self.interval_detector = IntervalDetector()
    
    def add_data_callback(self, callback: Callable[[SensorData], None]) -> None:
        """Adiciona callback para quando dados são recebidos"""
        self.data_callbacks.append(callback)
    
    def remove_data_callback(self, callback: Callable[[SensorData], None]) -> None:
        """Remove callback"""
        if callback in self.data_callbacks:
            self.data_callbacks.remove(callback)
    
    def _notification_handler(self, sender, data: bytearray) -> None:
        """Handler para notificações BLE recebidas"""
        self.buffer.extend(data)

        while len(self.buffer) >= self.struct_size:
            chunk = self.buffer[:self.struct_size]
            self.buffer[:] = self.buffer[self.struct_size:]

            unpacked = struct.unpack(self.struct_format, chunk)
            sLed, rSensor1, rSensor2, rSensor3, rSensor4, timeStamp = unpacked

            # Detecta mudanças de intervalo
            self.interval_detector.detect_interval_change(sLed, timeStamp)

            # Cria objeto SensorData
            sensor_data = SensorData(
                sLed=sLed,
                rSensor1=rSensor1,
                rSensor2=rSensor2,
                rSensor3=rSensor3,
                rSensor4=rSensor4,
                timeStamp=timeStamp,
                interval_ms=self.interval_detector.get_current_interval()
            )

            # Chama todos os callbacks registrados
            for callback in self.data_callbacks:
                try:
                    callback(sensor_data)
                except Exception as e:
                    print(f"Erro no callback: {e}")
    
    async def scan_devices(self) -> List[DeviceInfo]:
        """Escaneia dispositivos BLE disponíveis"""
        self.status = "Procurando dispositivos..."
        devices = await BleakScanner.discover()
        self.available_devices = []
        
        for device in devices:
            if device.name:
                self.available_devices.append(DeviceInfo(
                    name=device.name,
                    address=device.address
                ))
        
        self.status = f"Encontrados {len(self.available_devices)} dispositivos"
        return self.available_devices
    
    async def connect_to_device(self, device_address: str) -> None:
        """Conecta a um dispositivo específico"""
        try:
            self.status = f"Conectando ao dispositivo {device_address}..."
            
            async with BleakClient(device_address) as client:
                self.client = client
                self.status = "Conectado!"
                
                # Reset do detector de intervalo
                self.interval_detector.reset()
                
                await client.start_notify(
                    self.CHARACTERISTIC_UUID, 
                    self._notification_handler
                )
                
                # Mantém conexão ativa até sinalizar desconexão
                while not self.should_disconnect:
                    await asyncio.sleep(1)
                    
        except Exception as e:
            self.status = f"Erro na conexão: {e}"
            print(f"Erro BLE: {e}")
        finally:
            self.client = None
            self.should_disconnect = False
            self.status = "Desconectado"
    
    async def connect_to_esp32(self) -> None:
        """Conecta automaticamente ao ESP32 se encontrado"""
        self.status = "Procurando ESP32..."
        devices = await BleakScanner.discover()

        esp32_device = next(
            (d for d in devices if d.name and self.DEVICE_NAME in d.name), 
            None
        )
        
        if not esp32_device:
            self.status = "Dispositivo ESP32 não encontrado."
            return

        await self.connect_to_device(esp32_device.address)
    
    def start_scan_async(self) -> None:
        """Inicia escaneamento em thread separada"""
        def run_scan():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.scan_devices())
        
        thread = threading.Thread(target=run_scan, daemon=True)
        thread.start()
        return thread
    
    def start_connection_async(self, device_address: str) -> None:
        """Inicia conexão em thread separada"""
        def run_connection():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.connect_to_device(device_address))
        
        thread = threading.Thread(target=run_connection, daemon=True)
        thread.start()
        return thread
    
    def start_esp32_connection_async(self) -> None:
        """Inicia conexão ESP32 em thread separada"""
        def run_esp32_connection():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.connect_to_esp32())
        
        thread = threading.Thread(target=run_esp32_connection, daemon=True)
        thread.start()
        return thread
    
    def disconnect(self) -> None:
        """Sinaliza desconexão"""
        self.should_disconnect = True
    
    def get_status(self) -> str:
        """Retorna status atual"""
        return self.status
    
    def get_available_devices(self) -> List[DeviceInfo]:
        """Retorna dispositivos disponíveis"""
        return self.available_devices
    
    def get_interval_info(self) -> Dict:
        """Retorna informações do detector de intervalo"""
        return {
            'current_interval': self.interval_detector.get_current_interval(),
            'zones': self.interval_detector.get_zones()
        }