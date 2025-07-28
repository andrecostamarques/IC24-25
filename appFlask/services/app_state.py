from services.ble_manager import BLEManager
from services.data_manager import DataManager

class AppState:
    """Classe para gerenciar o estado global da aplicação"""
    
    def __init__(self):
        # Inicializa gerenciadores
        self.ble_manager = BLEManager()
        self.data_manager = DataManager()
        
        # Conecta callback do BLE ao DataManager
        self.ble_manager.add_data_callback(self.data_manager.add_sensor_data)
    
    def reset(self):
        """Reseta o estado da aplicação"""
        self.ble_manager.disconnect()
        self.data_manager.stop_csv_recording()
        self.data_manager.clear_chart_data()

# Instância global do estado da aplicação
app_state = AppState()