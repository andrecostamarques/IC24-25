from flask import Flask, render_template_string, jsonify, send_file, request
import asyncio
import struct
import csv
from bleak import BleakClient, BleakScanner
import threading

app = Flask(__name__)

DEVICE_NAME = "ESP32-SENSOR-SERVER"
CHARACTERISTIC_UUID = "abcd1234-5678-90ab-cdef-1234567890ab"

struct_format = "<B4iI"
struct_size = struct.calcsize(struct_format)

csv_filename = "dados_ble.csv"

# Armazenamento de dados para gráfico
chart_data = []

# NOVO: Variáveis para detecção de intervalo
last_sLed = None
last_timestamp_change = None
current_interval_ms = 0
interval_zones = []  # Lista de zonas de intervalo detectadas

buffer = bytearray()
csv_file = None
csv_writer = None

status = "Desconectado"
client = None
ble_loop = None
available_devices = []
should_disconnect = False
last_packet_count = 0
new_data_received = False

def detect_interval_change(sLed, timeStamp):
    """Detecta mudanças no intervalo baseado nas trocas de sLed"""
    global last_sLed, last_timestamp_change, current_interval_ms, interval_zones
    
    # Se é a primeira leitura
    if last_sLed is None:
        last_sLed = sLed
        last_timestamp_change = timeStamp
        return
    
    # Se houve mudança no sLed
    if sLed != last_sLed:
        # Calcula quantos timestamps passaram
        timestamp_diff = timeStamp - last_timestamp_change
        # Converte para milissegundos (cada timestamp = 50ms)
        interval_ms = timestamp_diff * 50
        
        # Se o intervalo mudou significativamente (diferença > 100ms)
        if abs(interval_ms - current_interval_ms) > 100:
            # Registra mudança de zona
            zone_info = {
                'timestamp': timeStamp,
                'old_interval': current_interval_ms,
                'new_interval': interval_ms,
                'change_time': timestamp_diff
            }
            interval_zones.append(zone_info)
            
            # Mantém apenas últimas 20 mudanças de zona
            if len(interval_zones) > 20:
                interval_zones.pop(0)
            
            print(f"🔄 MUDANÇA DE ZONA detectada em timestamp {timeStamp}:")
            print(f"   Intervalo anterior: {current_interval_ms}ms")
            print(f"   Novo intervalo: {interval_ms}ms") 
            print(f"   Diferença de timestamps: {timestamp_diff}")
            
            current_interval_ms = interval_ms
        
        # Atualiza referências
        last_sLed = sLed
        last_timestamp_change = timeStamp

def notification_handler(sender, data):
    global buffer, csv_writer, csv_file, new_data_received, chart_data
    buffer.extend(data)

    while len(buffer) >= struct_size:
        chunk = buffer[:struct_size]
        buffer[:] = buffer[struct_size:]

        unpacked = struct.unpack(struct_format, chunk)
        sLed, rSensor1, rSensor2, rSensor3, rSensor4, timeStamp = unpacked

        # NOVO: Detecta mudanças de intervalo
        detect_interval_change(sLed, timeStamp)

        # Adiciona aos dados do gráfico (incluindo intervalo atual)
        chart_data.append({
            'timestamp': timeStamp,
            'led': sLed,
            'sensors': [rSensor1, rSensor2, rSensor3, rSensor4],
            'interval_ms': current_interval_ms  # NOVO: intervalo atual
        })
        
        # Mantém apenas os últimos 100 pontos para performance
        if len(chart_data) > 100:
            chart_data.pop(0)

        if csv_writer:
            # NOVO: Inclui intervalo detectado no CSV
            csv_writer.writerow([sLed, rSensor1, rSensor2, rSensor3, rSensor4, timeStamp, current_interval_ms])
            csv_file.flush()
            new_data_received = True

async def scan_devices():
    global available_devices, status
    status = "Procurando dispositivos..."
    devices = await BleakScanner.discover()
    available_devices = []
    
    for device in devices:
        if device.name:
            available_devices.append({
                'name': device.name,
                'address': device.address
            })
    
    status = f"Encontrados {len(available_devices)} dispositivos"

async def connect_to_device(device_address):
    global status, client, csv_file, csv_writer, should_disconnect
    global last_sLed, last_timestamp_change, current_interval_ms, interval_zones  # NOVO: Reset variáveis
    
    try:
        status = f"Conectando ao dispositivo {device_address}..."
        
        async with BleakClient(device_address) as client:
            status = "Conectado!"
            
            # NOVO: Reset das variáveis de detecção
            last_sLed = None
            last_timestamp_change = None
            current_interval_ms = 0
            interval_zones.clear()
            
            # Abre CSV para escrita
            csv_file = open(csv_filename, mode="w", newline="")
            csv_writer = csv.writer(csv_file)
            # NOVO: Cabeçalho inclui intervalo detectado
            csv_writer.writerow(["sLed", "rSensor1", "rSensor2", "rSensor3", "rSensor4", "timeStamp", "interval_ms"])

            await client.start_notify(CHARACTERISTIC_UUID, notification_handler)
            
            # Mantém conexão ativa até sinalizar desconexão
            while not should_disconnect:
                await asyncio.sleep(1)
                
    except Exception as e:
        status = f"Erro na conexão: {e}"
    finally:
        if csv_file:
            csv_file.close()
            csv_file = None
        should_disconnect = False
        status = "Desconectado"

async def ble_task():
    global status, client, csv_file, csv_writer, should_disconnect
    status = "Procurando ESP32..."
    devices = await BleakScanner.discover()

    esp32_device = next((d for d in devices if d.name and DEVICE_NAME in d.name), None)
    if not esp32_device:
        status = "Dispositivo ESP32 não encontrado."
        return

    await connect_to_device(esp32_device.address)

def start_ble_loop():
    global ble_loop
    ble_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(ble_loop)
    ble_loop.run_until_complete(ble_task())

def start_connect_loop(device_address):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(connect_to_device(device_address))

def start_scan_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(scan_devices())

@app.route("/")
def index():
    return render_template_string("""
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monitor ESP32</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/plotly.js/2.26.0/plotly.min.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1, h3 {
            color: #333;
            text-align: center;
        }
        h1 { margin-bottom: 30px; }
        .status {
            background: #e7f3ff; padding: 15px; border-radius: 5px;
            margin-bottom: 20px; text-align: center; font-weight: bold;
        }
        .status.connected { background: #d4edda; color: #155724; }
        .status.connecting { background: #fff3cd; color: #856404; }
        .data-notification {
            background: #28a745; color: white; padding: 15px; border-radius: 5px;
            margin-bottom: 20px; text-align: center; font-weight: bold;
            font-size: 16px; animation: fadeIn 0.5s ease-in;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .controls {
            display: flex; gap: 15px; justify-content: center;
            margin-bottom: 30px; flex-wrap: wrap;
        }
        button {
            background: #007bff; color: white; border: none; padding: 12px 24px;
            border-radius: 5px; cursor: pointer; font-size: 16px; transition: background-color 0.3s;
        }
        button:hover { background: #0056b3; }
        button:disabled { background: #ccc; cursor: not-allowed; }
        .device-list {
            background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px;
            max-height: 200px; overflow-y: auto; margin-top: 20px;
        }
        .device-item {
            padding: 10px; border-bottom: 1px solid #dee2e6; cursor: pointer;
            transition: background-color 0.2s;
        }
        .device-item:hover { background: #e9ecef; }
        .device-item:last-child { border-bottom: none; }
        .device-name { font-weight: bold; }
        .device-address { font-size: 0.9em; color: #666; }
        .hidden { display: none; }

        /* NOVO: Estilos para info do intervalo */
        .interval-info {
            background: #e8f4f8;
            border: 1px solid #bee5eb;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            text-align: center;
        }
        .interval-current {
            font-size: 18px;
            font-weight: bold;
            color: #0c5460;
            margin-bottom: 10px;
        }
        .interval-zones {
            max-height: 150px;
            overflow-y: auto;
            background: white;
            border-radius: 5px;
            padding: 10px;
            margin-top: 10px;
        }
        .zone-item {
            font-size: 12px;
            padding: 5px;
            border-bottom: 1px solid #eee;
            color: #666;
        }

        /* Estilos para a legenda de cores */
        .legend-container {
            margin-top: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border: 1px solid #e9ecef;
        }
        .legend-container h4 {
            margin-top: 0;
            margin-bottom: 10px;
            text-align: center;
            color: #555;
        }
        .legend-item {
            display: flex;
            align-items: center;
            margin-bottom: 5px;
            font-size: 14px;
        }
        .color-box {
            display: inline-block;
            width: 18px;
            height: 18px;
            margin-right: 10px;
            border: 1px solid #ccc;
            border-radius: 3px;
            vertical-align: middle;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Monitor ESP32 - Sensores BLE</h1>
        
        <div id="status" class="status">Desconectado</div>
        <div id="data-notification" class="data-notification hidden">📊 Dados de leitura recebidos!</div>
        
        <!-- NOVO: Informações do intervalo -->
        <div class="interval-info">
            <div class="interval-current" id="current-interval">Intervalo atual: Aguardando dados...</div>
            <div style="font-size: 14px; color: #666;">
                <span id="interval-range">Faixa detectada: 250ms - 4000ms</span>
            </div>
            <div class="interval-zones">
                <strong>Últimas mudanças de zona:</strong>
                <div id="zones-list">Aguardando detecção...</div>
            </div>
        </div>
        
        <div class="controls">
            <button onclick="scanDevices()">Buscar Dispositivos</button>
            <button onclick="connectESP32()">Conectar ESP32</button>
            <button onclick="disconnectESP32()">Desconectar</button>
            <button onclick="downloadCSV()">Download CSV</button>
        </div>
        
        <div id="devices-section" class="hidden">
            <h3>Dispositivos Encontrados:</h3>
            <div id="device-list" class="device-list"></div>
        </div>
        
        <div class="container" style="margin-top: 30px; padding: 10px;">
            <h3>📊 Gráfico em Tempo Real - Sensores + Controle de Velocidade</h3>
            <div id="sensor-chart" style="width: 100%; height: 500px;"></div>
            
            <div class="legend-container">
                <h4>Legenda de Cores (Sensor Alvo)</h4>
                <div class="legend-item"><span class="color-box" style="background-color: rgba(255, 107, 107, 0.4);"></span> Fundo Vermelho: Sensor 1 (sLed=0)</div>
                <div class="legend-item"><span class="color-box" style="background-color: rgba(78, 205, 196, 0.4);"></span> Fundo Verde: Sensor 2 (sLed=1)</div>
                <div class="legend-item"><span class="color-box" style="background-color: rgba(69, 183, 209, 0.4);"></span> Fundo Azul: Sensor 3 (sLed=2)</div>
                <div class="legend-item"><span class="color-box" style="background-color: rgba(150, 206, 180, 0.4);"></span> Fundo Verde-Água: Sensor 4 (sLed=3)</div>
            </div>
        </div>
    </div>

    <script>
        function updateStatus() {
            fetch('/status')
                .then(resp => resp.json())
                .then(data => {
                    const statusDiv = document.getElementById('status');
                    statusDiv.textContent = data.status;
                    statusDiv.className = 'status';
                    if (data.status.includes('Conectado')) {
                        statusDiv.classList.add('connected');
                    } else if (data.status.includes('Conectando') || data.status.includes('Procurando')) {
                        statusDiv.classList.add('connecting');
                    }
                    if (data.new_data) {
                        showDataNotification();
                    }
                });
        }
        
        // NOVA FUNÇÃO: Atualiza informações do intervalo
        function updateIntervalInfo() {
            fetch('/interval_info')
                .then(resp => resp.json())
                .then(data => {
                    document.getElementById('current-interval').textContent = 
                        `Intervalo atual: ${data.current_interval}ms (${(data.current_interval/1000).toFixed(2)}s)`;
                    
                    const zonesList = document.getElementById('zones-list');
                    if (data.zones.length > 0) {
                        zonesList.innerHTML = data.zones.map(zone => 
                            `<div class="zone-item">Timestamp ${zone.timestamp}: ${zone.old_interval}ms → ${zone.new_interval}ms</div>`
                        ).join('');
                    } else {
                        zonesList.innerHTML = 'Aguardando detecção...';
                    }
                })
                .catch(() => {
                    // Silencioso se não conseguir buscar dados
                });
        }
        
        function showDataNotification() {
            const notification = document.getElementById('data-notification');
            notification.classList.remove('hidden');
            setTimeout(() => { notification.classList.add('hidden'); }, 4000);
        }
        
        function initChart() {
            const trace1 = { x: [], y: [], mode: 'lines+markers', name: 'Sensor 1', line: {color: '#FF6B6B', width: 3}, marker: {size: 6} };
            const trace2 = { x: [], y: [], mode: 'lines+markers', name: 'Sensor 2', line: {color: '#4ECDC4', width: 3}, marker: {size: 6} };
            const trace3 = { x: [], y: [], mode: 'lines+markers', name: 'Sensor 3', line: {color: '#45B7D1', width: 3}, marker: {size: 6} };
            const trace4 = { x: [], y: [], mode: 'lines+markers', name: 'Sensor 4', line: {color: '#96CEB4', width: 3}, marker: {size: 6} };
            
            const layout = {
                title: { text: 'Monitoramento com Controle Dinâmico de Velocidade', font: {size: 18, color: '#333'} },
                xaxis: { title: 'Timestamp', gridcolor: '#E8E8E8', showgrid: true },
                yaxis: { title: 'Valor do Sensor', gridcolor: '#E8E8E8', showgrid: true },
                plot_bgcolor: 'rgba(0,0,0,0)',
                paper_bgcolor: 'rgba(0,0,0,0)',
                legend: { x: 0.5, y: 1.1, xanchor: 'center', orientation: 'h', bgcolor: 'rgba(255,255,255,0.8)', bordercolor: '#DDD', borderwidth: 1 },
                margin: {l: 60, r: 40, t: 80, b: 60}
            };
            
            const config = { responsive: true, displayModeBar: true, modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'] };
            
            Plotly.newPlot('sensor-chart', [trace1, trace2, trace3, trace4], layout, config);
        }
        
        function updateChart() {
            fetch('/chart_data')
                .then(resp => resp.json())
                .then(data => {
                    if (data.data && data.data.length > 0) {
                        const chartData = data.data;
                        
                        const timestamps = chartData.map(d => d.timestamp);
                        const sensor1Data = chartData.map(d => d.sensors[0]);
                        const sensor2Data = chartData.map(d => d.sensors[1]);
                        const sensor3Data = chartData.map(d => d.sensors[2]);
                        const sensor4Data = chartData.map(d => d.sensors[3]);
                        
                        const shapes = [];
                        const ledColors = {
                            0: 'rgba(255, 107, 107, 0.4)',
                            1: 'rgba(78, 205, 196, 0.4)',
                            2: 'rgba(69, 183, 209, 0.4)',
                            3: 'rgba(150, 206, 180, 0.4)'
                        };
                        
                        for (let i = 0; i < chartData.length - 1; i++) {
                            shapes.push({
                                type: 'rect', xref: 'x', yref: 'paper',
                                x0: chartData[i].timestamp, y0: 0,
                                x1: chartData[i+1].timestamp, y1: 1,
                                fillcolor: ledColors[chartData[i].led] || 'rgba(200, 200, 200, 0.1)',
                                layer: 'below', line: {width: 0}
                            });
                        }
                        
                        const update = {
                            x: [timestamps, timestamps, timestamps, timestamps],
                            y: [sensor1Data, sensor2Data, sensor3Data, sensor4Data]
                        };
                        
                        const layoutUpdate = { shapes: shapes };
                        
                        Plotly.update('sensor-chart', update, layoutUpdate);
                    }
                })
                .catch(error => console.log('Erro ao atualizar gráfico:', error));
        }
        
        function scanDevices() {
            document.getElementById('status').textContent = 'Escaneando...';
            fetch('/scan').then(resp => resp.json()).then(data => {
                const deviceList = document.getElementById('device-list');
                const devicesSection = document.getElementById('devices-section');
                deviceList.innerHTML = '';
                if (data.devices.length > 0) {
                    devicesSection.classList.remove('hidden');
                    data.devices.forEach(device => {
                        const deviceDiv = document.createElement('div');
                        deviceDiv.className = 'device-item';
                        deviceDiv.onclick = () => connectToDevice(device.address, device.name);
                        deviceDiv.innerHTML = `<div class="device-name">${device.name}</div><div class="device-address">${device.address}</div>`;
                        deviceList.appendChild(deviceDiv);
                    });
                }
                alert(data.message);
            });
        }
        
        function connectESP32() {
            fetch('/start').then(resp => resp.json()).then(data => alert(data.message));
        }
        
        function connectToDevice(address, name) {
            if (confirm(`Conectar ao dispositivo: ${name}?`)) {
                fetch('/connect', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({address: address})
                }).then(resp => resp.json()).then(data => alert(data.message));
            }
        }
        
        function disconnectESP32() {
            fetch('/disconnect').then(resp => resp.json()).then(data => alert(data.message));
        }
        
        function downloadCSV() {
            window.location.href = '/download';
        }
        
        setInterval(updateStatus, 2000);
        setInterval(updateIntervalInfo, 1000);  // NOVO: Atualiza info do intervalo
        updateStatus();
        
        initChart();
        setInterval(updateChart, 1000);
    </script>
</body>
</html>
""")

@app.route("/scan")
def scan():
    t = threading.Thread(target=start_scan_loop, daemon=True)
    t.start()
    t.join(timeout=8)
    return jsonify({
        "message": f"Escaneamento concluído. {len(available_devices)} dispositivos encontrados.",
        "devices": available_devices
    })

@app.route("/start")
def start():
    global ble_loop, should_disconnect
    if ble_loop and ble_loop.is_running():
        return jsonify({"message":"BLE já está rodando"})
    else:
        should_disconnect = False
        t = threading.Thread(target=start_ble_loop, daemon=True)
        t.start()
        return jsonify({"message":"Iniciando conexão BLE..."})

@app.route("/connect", methods=["POST"])
def connect():
    global should_disconnect
    data = request.get_json()
    device_address = data.get('address')
    if not device_address:
        return jsonify({"message": "Endereço do dispositivo não fornecido."})
    should_disconnect = False
    t = threading.Thread(target=start_connect_loop, args=(device_address,), daemon=True)
    t.start()
    return jsonify({"message": f"Conectando ao dispositivo {device_address}..."})

@app.route("/disconnect")
def disconnect():
    global should_disconnect
    should_disconnect = True
    return jsonify({"message":"Desconectando..."})

@app.route("/status")
def get_status():
    global new_data_received
    data_flag = new_data_received
    new_data_received = False
    return jsonify({
        "status": status,
        "new_data": data_flag
    })

@app.route("/chart_data")
def get_chart_data():
    return jsonify({"data": chart_data})

# NOVA ROTA: Informações do intervalo
@app.route("/interval_info")
def get_interval_info():
    return jsonify({
        "current_interval": current_interval_ms,
        "zones": interval_zones[-10:]  # Últimas 10 mudanças
    })

@app.route("/download")
def download():
    try:
        return send_file(csv_filename, as_attachment=True)
    except Exception:
        return "Arquivo CSV não encontrado", 404

if __name__ == "__main__":
    app.run(debug=True)