import csv
import os
from typing import List, Dict, Optional
from collections import deque
from services.ble_manager import SensorData

class DataManager:
    """Gerenciador para armazenamento e processamento de dados dos sensores"""
    
    def __init__(self, csv_folder: str = "data", max_chart_points: int = 100):
        self.csv_folder = csv_folder
        self.max_chart_points = max_chart_points
        
        # Dados para o gráfico em tempo real
        self.chart_data: deque = deque(maxlen=max_chart_points)
        
        # Estado do CSV
        self.csv_file = None
        self.csv_writer = None
        self.csv_filename = None
        
        # Flag para notificar novos dados
        self.new_data_received = False
        
        # Criar diretório se não existir
        os.makedirs(csv_folder, exist_ok=True)
    
    def start_csv_recording(self, filename: str = "dados_ble.csv") -> None:
        """Inicia gravação em arquivo CSV"""
        self.csv_filename = os.path.join(self.csv_folder, filename)
        
        try:
            self.csv_file = open(self.csv_filename, mode="w", newline="", encoding='utf-8')
            self.csv_writer = csv.writer(self.csv_file)
            
            # Escreve cabeçalho
            self.csv_writer.writerow([
                "sLed", "rSensor1", "rSensor2", "rSensor3", "rSensor4", 
                "timeStamp", "interval_ms"
            ])
            
            print(f"Iniciada gravação CSV: {self.csv_filename}")
            
        except Exception as e:
            print(f"Erro ao abrir arquivo CSV: {e}")
            self.csv_file = None
            self.csv_writer = None
    
    def stop_csv_recording(self) -> None:
        """Para gravação em arquivo CSV"""
        if self.csv_file:
            try:
                self.csv_file.close()
                print(f"Gravação CSV finalizada: {self.csv_filename}")
            except Exception as e:
                print(f"Erro ao fechar arquivo CSV: {e}")
            finally:
                self.csv_file = None
                self.csv_writer = None
    
    def add_sensor_data(self, sensor_data: SensorData) -> None:
        """Adiciona dados do sensor (callback para BLEManager)"""
        # Adiciona aos dados do gráfico
        chart_point = {
            'timestamp': sensor_data.timeStamp,
            'led': sensor_data.sLed,
            'sensors': [
                sensor_data.rSensor1, 
                sensor_data.rSensor2, 
                sensor_data.rSensor3, 
                sensor_data.rSensor4
            ],
            'interval_ms': sensor_data.interval_ms
        }
        
        self.chart_data.append(chart_point)
        
        # Grava no CSV se ativo
        if self.csv_writer:
            try:
                self.csv_writer.writerow([
                    sensor_data.sLed,
                    sensor_data.rSensor1,
                    sensor_data.rSensor2,
                    sensor_data.rSensor3,
                    sensor_data.rSensor4,
                    sensor_data.timeStamp,
                    sensor_data.interval_ms
                ])
                self.csv_file.flush()
            except Exception as e:
                print(f"Erro ao escrever no CSV: {e}")
        
        # Marca que novos dados foram recebidos
        self.new_data_received = True
    
    def get_chart_data(self) -> List[Dict]:
        """Retorna dados para o gráfico"""
        return list(self.chart_data)
    
    def has_new_data(self) -> bool:
        """Verifica e reseta flag de novos dados"""
        has_new = self.new_data_received
        self.new_data_received = False
        return has_new
    
    def get_csv_filename(self) -> Optional[str]:
        """Retorna nome do arquivo CSV atual"""
        return self.csv_filename
    
    def clear_chart_data(self) -> None:
        """Limpa dados do gráfico"""
        self.chart_data.clear()
    
    def get_data_summary(self) -> Dict:
        """Retorna resumo dos dados"""
        if not self.chart_data:
            return {
                'total_points': 0,
                'time_range': {'start': None, 'end': None},
                'sensor_ranges': {}
            }
        
        data_list = list(self.chart_data)
        timestamps = [d['timestamp'] for d in data_list]
        
        # Calcula ranges dos sensores
        sensor_ranges = {}
        for i in range(4):
            sensor_values = [d['sensors'][i] for d in data_list]
            sensor_ranges[f'sensor_{i+1}'] = {
                'min': min(sensor_values),
                'max': max(sensor_values),
                'avg': sum(sensor_values) / len(sensor_values)
            }
        
        return {
            'total_points': len(data_list),
            'time_range': {
                'start': min(timestamps),
                'end': max(timestamps)
            },
            'sensor_ranges': sensor_ranges
        }
    
    def export_data_to_dict(self) -> Dict:
        """Exporta todos os dados para um dicionário"""
        return {
            'chart_data': list(self.chart_data),
            'csv_filename': self.csv_filename,
            'data_summary': self.get_data_summary()
        }