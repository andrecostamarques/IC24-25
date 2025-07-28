from flask import Blueprint, jsonify, request
from services.app_state import app_state
import threading

api_bp = Blueprint('api', __name__)

@api_bp.route("/scan")
def scan():
    """Escaneia dispositivos BLE disponíveis"""
    thread = app_state.ble_manager.start_scan_async()
    thread.join(timeout=8)  # Timeout de 8 segundos
    
    devices = app_state.ble_manager.get_available_devices()
    device_list = [{'name': d.name, 'address': d.address} for d in devices]
    
    return jsonify({
        "message": f"Escaneamento concluído. {len(devices)} dispositivos encontrados.",
        "devices": device_list
    })

@api_bp.route("/start")
def start():
    """Inicia conexão automática com ESP32"""
    if app_state.ble_manager.get_status() != "Desconectado":
        return jsonify({"message": "BLE já está ativo"})
    
    # Inicia gravação CSV
    app_state.data_manager.start_csv_recording()
    
    # Inicia conexão
    app_state.ble_manager.start_esp32_connection_async()
    
    return jsonify({"message": "Iniciando conexão BLE..."})

@api_bp.route("/connect", methods=["POST"])
def connect():
    """Conecta a um dispositivo específico"""
    data = request.get_json()
    device_address = data.get('address')
    
    if not device_address:
        return jsonify({"message": "Endereço do dispositivo não fornecido."}), 400
    
    # Inicia gravação CSV
    app_state.data_manager.start_csv_recording()
    
    # Inicia conexão
    app_state.ble_manager.start_connection_async(device_address)
    
    return jsonify({"message": f"Conectando ao dispositivo {device_address}..."})

@api_bp.route("/disconnect")
def disconnect():
    """Desconecta do dispositivo atual"""
    app_state.ble_manager.disconnect()
    app_state.data_manager.stop_csv_recording()
    
    return jsonify({"message": "Desconectando..."})

@api_bp.route("/status")
def get_status():
    """Retorna status atual da conexão"""
    status = app_state.ble_manager.get_status()
    new_data = app_state.data_manager.has_new_data()
    
    return jsonify({
        "status": status,
        "new_data": new_data
    })

@api_bp.route("/chart_data")
def get_chart_data():
    """Retorna dados para o gráfico"""
    chart_data = app_state.data_manager.get_chart_data()
    return jsonify({"data": chart_data})

@api_bp.route("/interval_info")
def get_interval_info():
    """Retorna informações sobre intervalos detectados"""
    interval_info = app_state.ble_manager.get_interval_info()
    return jsonify({
        "current_interval": interval_info['current_interval'],
        "zones": interval_info['zones'][-10:]  # Últimas 10 mudanças
    })

@api_bp.route("/data_summary")
def get_data_summary():
    """Retorna resumo dos dados coletados"""
    summary = app_state.data_manager.get_data_summary()
    return jsonify(summary)

@api_bp.route("/clear_data", methods=["POST"])
def clear_data():
    """Limpa dados do gráfico (não afeta CSV)"""
    app_state.data_manager.clear_chart_data()
    return jsonify({"message": "Dados do gráfico limpos com sucesso"})

@api_bp.route("/export_data")
def export_data():
    """Exporta todos os dados em formato JSON"""
    exported_data = app_state.data_manager.export_data_to_dict()
    return jsonify(exported_data)