// Funções para atualização de status e dados
function updateStatus() {
    fetch('/api/status')
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
        })
        .catch(error => console.log('Erro ao atualizar status:', error));
}

// Atualiza informações do intervalo
function updateIntervalInfo() {
    fetch('/api/interval_info')
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
        .catch(error => {
            // Silencioso se não conseguir buscar dados
            console.log('Erro ao buscar dados do intervalo:', error);
        });
}

function showDataNotification() {
    const notification = document.getElementById('data-notification');
    notification.classList.remove('hidden');
    setTimeout(() => { 
        notification.classList.add('hidden'); 
    }, 4000);
}

// Funções do gráfico
function initChart() {
    const trace1 = { 
        x: [], y: [], 
        mode: 'lines+markers', 
        name: 'Sensor 1', 
        line: {color: '#FF6B6B', width: 3}, 
        marker: {size: 6} 
    };
    const trace2 = { 
        x: [], y: [], 
        mode: 'lines+markers', 
        name: 'Sensor 2', 
        line: {color: '#4ECDC4', width: 3}, 
        marker: {size: 6} 
    };
    const trace3 = { 
        x: [], y: [], 
        mode: 'lines+markers', 
        name: 'Sensor 3', 
        line: {color: '#45B7D1', width: 3}, 
        marker: {size: 6} 
    };
    const trace4 = { 
        x: [], y: [], 
        mode: 'lines+markers', 
        name: 'Sensor 4', 
        line: {color: '#96CEB4', width: 3}, 
        marker: {size: 6} 
    };
    
    const layout = {
        title: { 
            text: 'Monitoramento com Controle Dinâmico de Velocidade', 
            font: {size: 18, color: '#333'} 
        },
        xaxis: { 
            title: 'Timestamp', 
            gridcolor: '#E8E8E8', 
            showgrid: true 
        },
        yaxis: { 
            title: 'Valor do Sensor', 
            gridcolor: '#E8E8E8', 
            showgrid: true 
        },
        plot_bgcolor: 'rgba(0,0,0,0)',
        paper_bgcolor: 'rgba(0,0,0,0)',
        legend: { 
            x: 0.5, y: 1.1, 
            xanchor: 'center', 
            orientation: 'h', 
            bgcolor: 'rgba(255,255,255,0.8)', 
            bordercolor: '#DDD', 
            borderwidth: 1 
        },
        margin: {l: 60, r: 40, t: 80, b: 60}
    };
    
    const config = { 
        responsive: true, 
        displayModeBar: true, 
        modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'] 
    };
    
    Plotly.newPlot('sensor-chart', [trace1, trace2, trace3, trace4], layout, config);
}

function updateChart() {
    fetch('/api/chart_data')
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
                        type: 'rect', 
                        xref: 'x', 
                        yref: 'paper',
                        x0: chartData[i].timestamp, 
                        y0: 0,
                        x1: chartData[i+1].timestamp, 
                        y1: 1,
                        fillcolor: ledColors[chartData[i].led] || 'rgba(200, 200, 200, 0.1)',
                        layer: 'below', 
                        line: {width: 0}
                    });
                }
                
                const update = {
                    x: [timestamps, timestamps, timestamps, timestamps],
                    y: [sensor1Data, sensor2Data, sensor3Data, sensor4Data]
                };
                
                const layoutUpdate = {
                    shapes: shapes
                };
                
                Plotly.update('sensor-chart', update, layoutUpdate);
            }
        })
        .catch(error => console.log('Erro ao atualizar gráfico:', error));
}

// Funções de controle
function scanDevices() {
    document.getElementById('status').textContent = 'Escaneando...';
    
    fetch('/api/scan')
        .then(resp => resp.json())
        .then(data => {
            const deviceList = document.getElementById('device-list');
            const devicesSection = document.getElementById('devices-section');
            
            deviceList.innerHTML = '';
            
            if (data.devices.length > 0) {
                devicesSection.classList.remove('hidden');
                data.devices.forEach(device => {
                    const deviceDiv = document.createElement('div');
                    deviceDiv.className = 'device-item';
                    deviceDiv.onclick = () => connectToDevice(device.address, device.name);
                    deviceDiv.innerHTML = `
                        <div class="device-name">${device.name}</div>
                        <div class="device-address">${device.address}</div>
                    `;
                    deviceList.appendChild(deviceDiv);
                });
            }
            
            alert(data.message);
        })
        .catch(error => {
            console.error('Erro ao escanear dispositivos:', error);
            alert('Erro ao escanear dispositivos');
        });
}

function connectESP32() {
    fetch('/api/start')
        .then(resp => resp.json())
        .then(data => alert(data.message))
        .catch(error => {
            console.error('Erro ao conectar ESP32:', error);
            alert('Erro ao conectar ao ESP32');
        });
}

function connectToDevice(address, name) {
    if (confirm(`Conectar ao dispositivo: ${name}?`)) {
        fetch('/api/connect', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({address: address})
        })
        .then(resp => resp.json())
        .then(data => alert(data.message))
        .catch(error => {
            console.error('Erro ao conectar dispositivo:', error);
            alert('Erro ao conectar ao dispositivo');
        });
    }
}

function disconnectESP32() {
    fetch('/api/disconnect')
        .then(resp => resp.json())
        .then(data => alert(data.message))
        .catch(error => {
            console.error('Erro ao desconectar:', error);
            alert('Erro ao desconectar');
        });
}

function downloadCSV() {
    window.location.href = '/download';
}

function clearData() {
    if (confirm('Limpar dados do gráfico? (O arquivo CSV não será afetado)')) {
        fetch('/api/clear_data', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        })
        .then(resp => resp.json())
        .then(data => {
            alert(data.message);
            // Limpa o gráfico visualmente
            initChart();
        })
        .catch(error => {
            console.error('Erro ao limpar dados:', error);
            alert('Erro ao limpar dados');
        });
    }
}

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    // Atualiza status periodicamente
    setInterval(updateStatus, 2000);
    setInterval(updateIntervalInfo, 1000);
    
    // Inicializa e atualiza gráfico
    initChart();
    setInterval(updateChart, 1000);
    
    // Primeira atualização
    updateStatus();
    updateIntervalInfo();
});