from flask import Flask, render_template_string, jsonify, send_file
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

buffer = bytearray()
csv_file = None
csv_writer = None

status = "Desconectado"
client = None
ble_loop = None

def notification_handler(sender, data):
    global buffer, csv_writer, csv_file
    buffer.extend(data)

    while len(buffer) >= struct_size:
        chunk = buffer[:struct_size]
        buffer[:] = buffer[struct_size:]

        unpacked = struct.unpack(struct_format, chunk)
        sLed, rSensor1, rSensor2, rSensor3, rSensor4, timeStamp = unpacked

        if csv_writer:
            csv_writer.writerow([sLed, rSensor1, rSensor2, rSensor3, rSensor4, timeStamp])
            csv_file.flush()

async def ble_task():
    global status, client, csv_file, csv_writer
    status = "Procurando ESP32..."
    devices = await BleakScanner.discover()

    esp32_device = next((d for d in devices if d.name and DEVICE_NAME in d.name), None)
    if not esp32_device:
        status = "Dispositivo ESP32 não encontrado."
        return

    status = f"Conectando ao {esp32_device.name}..."
    async with BleakClient(esp32_device) as client:
        status = "Conectado!"
        # Abre CSV para escrita
        csv_file = open(csv_filename, mode="w", newline="")
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["sLed", "rSensor1", "rSensor2", "rSensor3", "rSensor4", "timeStamp"])

        try:
            await client.start_notify(CHARACTERISTIC_UUID, notification_handler)
            while True:
                await asyncio.sleep(1)
        except Exception as e:
            status = f"Erro: {e}"
        finally:
            if csv_file:
                csv_file.close()
                csv_file = None
            status = "Desconectado"

def start_ble_loop():
    global ble_loop
    ble_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(ble_loop)
    ble_loop.run_until_complete(ble_task())

@app.route("/")
def index():
    return render_template_string("""
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>BLE ESP32</title>
</head>
<body>
    <h1>Status: <span id="status">{{status}}</span></h1>
    <button onclick="startConnection()">Iniciar Conexão</button>
    <button onclick="downloadCSV()">Baixar CSV</button>

<script>
function startConnection(){
    fetch('/start')
    .then(resp => resp.json())
    .then(data => {
        alert(data.message);
        updateStatus();
    });
}

function updateStatus(){
    fetch('/status')
    .then(resp => resp.json())
    .then(data => {
        document.getElementById("status").textContent = data.status;
        setTimeout(updateStatus, 2000);
    });
}

function downloadCSV(){
    window.location.href = '/download';
}

updateStatus();
</script>
</body>
</html>
""", status=status)

@app.route("/start")
def start():
    global ble_loop
    if ble_loop and ble_loop.is_running():
        return jsonify({"message":"BLE já está rodando"})
    else:
        t = threading.Thread(target=start_ble_loop, daemon=True)
        t.start()
        return jsonify({"message":"Iniciando conexão BLE..."})

@app.route("/status")
def get_status():
    return jsonify({"status": status})

@app.route("/download")
def download():
    try:
        return send_file(csv_filename, as_attachment=True)
    except Exception:
        return "Arquivo CSV não encontrado", 404

if __name__ == "__main__":
    app.run(debug=True)
