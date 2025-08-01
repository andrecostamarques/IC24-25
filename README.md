# 📡 Monitor ESP32 - Sistema de Sensores BLE

Um sistema completo de monitoramento de sensores em tempo real usando ESP32 com comunicação Bluetooth Low Energy (BLE) e interface web Flask.

## 🎯 Visão Geral

Este projeto consiste em duas partes principais:
- **Hardware (ESP32)**: Coleta dados de 4 sensores analógicos com controle dinâmico de velocidade via potenciômetro
- **Software (Python/Flask)**: Interface web para visualização em tempo real, armazenamento de dados e análise

## ⚡ Características Principais

### Hardware (ESP32)
- 📊 **4 Sensores Analógicos**: Leitura simultânea de sensores conectados aos GPIOs 34, 35, 36, 39
- 🔄 **Controle Dinâmico**: Potenciômetro (GPIO 4) controla intervalo de troca entre sensores (250ms - 4s)
- 💡 **LEDs Indicadores**: 2 LEDs (GPIOs 26, 27) mostram sensor ativo atual
- 📡 **Comunicação BLE**: Transmissão de dados via Bluetooth Low Energy
- 🔘 **Controles Físicos**: Botões para gravar dados e enviar via BLE

### Software (Flask)
- 🌐 **Interface Web Responsiva**: Dashboard em tempo real para monitoramento
- 📈 **Gráficos Interativos**: Visualização usando Plotly.js com código de cores por sensor
- 🔍 **Detecção Inteligente**: Algoritmo para detectar mudanças de intervalo automaticamente
- 💾 **Exportação CSV**: Salvamento automático de dados com timestamps
- 🔗 **Conexão Flexível**: Escaneamento e conexão a múltiplos dispositivos BLE

## 🏗️ Arquitetura do Sistema

```
┌─────────────────────┐         BLE          ┌─────────────────────┐
│      ESP32          │ ◄──────────────────► │   Flask Server      │
│  - 4 Sensores       │                      │  - Interface Web    │
│  - Potenciômetro    │                      │  - Processamento    │
│  - LEDs Controle    │                      │  - Armazenamento    │
│  - Controles        │                      │  - Visualização     │
└─────────────────────┘                      └─────────────────────┘
```

## 📁 Estrutura do Projeto

```
projeto_esp32/
├── 📱 Hardware (Arduino/ESP32)
│   └── esp32_sensor_server.ino
├── 🐍 Software (Python/Flask)
│   ├── app.py                    # Aplicação principal
│   ├── routes/
│   │   ├── main_routes.py        # Rotas da interface
│   │   └── api_routes.py         # API endpoints
│   ├── services/
│   │   ├── ble_manager.py        # Gerenciador BLE
│   │   ├── data_manager.py       # Processamento de dados
│   │   └── app_state.py          # Estado da aplicação
│   ├── templates/
│   │   └── index.html            # Interface web
│   ├── static/
│   │   ├── css/style.css         # Estilos
│   │   └── js/app.js            # JavaScript
│   └── data/                     # Arquivos CSV gerados
└── README.md
```

## 🔧 Hardware - Configuração ESP32

### Componentes Necessários
- 1x ESP32 (qualquer modelo)
- 4x Sensores analógicos (LDR, potenciômetros, etc.)
- 1x Potenciômetro (controle de velocidade)
- 2x LEDs + resistores
- 2x Botões (normalmente abertos)
- 1x LED de status + resistor
- Breadboard e jumpers

### Conexões

| Componente | GPIO ESP32 | Descrição |
|------------|------------|-----------|
| Sensor 1 | 34 | Entrada analógica |
| Sensor 2 | 35 | Entrada analógica |
| Sensor 3 | 36 | Entrada analógica |
| Sensor 4 | 39 | Entrada analógica |
| LED Controle 1 | 26 | Indicador sensor ativo |
| LED Controle 2 | 27 | Indicador sensor ativo |
| Botão Record | 23 | Gravar dados |
| Botão Send | 18 | Enviar dados |
| LED Status | 13 | Status conexão |
| Potenciômetro | 4 | Controle velocidade |

### Código Arduino

```cpp
// Intervalo dinâmico controlado por potenciômetro
unsigned long intervaloTroca = 1000;  // 250ms - 4000ms
const unsigned long minIntervalo = 250;
const unsigned long maxIntervalo = 4000;

// Estrutura do payload transmitido
struct PL {
  uint8_t sLed;      // Sensor ativo (0-3)
  int rSensor[4];    // Valores dos 4 sensores
  uint32_t timeStamp; // Timestamp
};
```

## 💻 Software - Configuração Python

### Pré-requisitos
- Python 3.7+
- Sistema operacional com suporte BLE (Windows 10+, Linux, macOS)

### Instalação

1. **Clone/baixe o projeto**:
```bash
git clone <repository-url>
cd projeto_esp32
```

2. **Instale as dependências**:
```bash
pip install flask bleak asyncio
```

3. **Execute a aplicação**:
```bash
python app.py
```

4. **Acesse a interface**:
```
http://localhost:5000
```

### Dependências Python
```
flask>=2.0.0
bleak>=0.19.0
asyncio (built-in)
```

## 🚀 Como Usar

### 1. Preparação do Hardware
1. Monte o circuito conforme o diagrama de conexões
2. Carregue o código Arduino para o ESP32
3. Verifique se o ESP32 está anunciando como "ESP32-SENSOR-SERVER"

### 2. Iniciando o Software
1. Execute o servidor Flask
2. Abra o navegador em `http://localhost:5000`
3. Use "Buscar Dispositivos" para encontrar o ESP32
4. Conecte ao dispositivo

### 3. Operação
1. **Controle de Velocidade**: Gire o potenciômetro para ajustar intervalo (0.25s - 4s)
2. **Gravação**: Pressione botão "Record" no ESP32 para gravar dados
3. **Envio**: Pressione botão "Send" no ESP32 para transmitir via BLE
4. **Monitoramento**: Visualize dados em tempo real na interface web
5. **Exportação**: Use "Download CSV" para salvar dados

## 📊 Funcionalidades da Interface Web

### Dashboard Principal
- ✅ **Status da Conexão**: Indicador visual do estado BLE
- ✅ **Controles**: Scan, conectar, desconectar dispositivos
- ✅ **Informações de Intervalo**: Detecção automática de mudanças de velocidade
- ✅ **Notificações**: Alertas quando novos dados são recebidos

### Gráfico em Tempo Real
- 📈 **4 Séries de Dados**: Uma linha para cada sensor
- 🎨 **Código de Cores**: Fundo colorido indica sensor ativo
- 🔄 **Atualização Automática**: Refresh a cada 1 segundo
- 📱 **Responsivo**: Adaptável a diferentes tamanhos de tela

### Detecção Inteligente
- 🧠 **Algoritmo Automático**: Detecta mudanças de intervalo baseado em padrões sLed
- ⏱️ **Cálculo Preciso**: Converte diferenças de timestamp para milissegundos
- 📋 **Histórico**: Mantém registro das últimas 20 mudanças de zona

## 🎨 Código de Cores

| Sensor Ativo | Cor de Fundo | Valor sLed |
|--------------|--------------|------------|
| Sensor 1 | 🔴 Vermelho | 0 |
| Sensor 2 | 🟢 Verde | 1 |
| Sensor 3 | 🔵 Azul | 2 |
| Sensor 4 | 🟡 Verde-Água | 3 |

## 💾 Formato dos Dados

### Estrutura CSV
```csv
sLed,rSensor1,rSensor2,rSensor3,rSensor4,timeStamp,interval_ms
0,1234,2345,3456,4567,1000,1500
1,1235,2346,3457,4568,1001,1500
...
```

### Protocolo BLE
- **Service UUID**: `12345678-1234-1234-1234-1234567890ab`
- **Characteristic UUID**: `abcd1234-5678-90ab-cdef-1234567890ab`
- **MTU**: 180 bytes para transmissão otimizada
- **Estrutura**: Pacotes binários com struct C/C++

## 🔧 Configurações Avançadas

### Parâmetros do ESP32
```cpp
const unsigned long minIntervalo = 250;   // Intervalo mínimo (ms)
const unsigned long maxIntervalo = 4000;  // Intervalo máximo (ms)
const unsigned long intervaloBlink = 500; // Piscar LED status
```

### Configurações Flask
```python
# Número máximo de pontos no gráfico
max_chart_points = 100

# Pasta para arquivos CSV
csv_folder = "data"

# Nome padrão do dispositivo
device_name = "ESP32-SENSOR-SERVER"
```

## 🐛 Solução de Problemas

### Problemas Comuns

**ESP32 não aparece no scan:**
- Verifique se o BLE está habilitado no sistema
- Certifique-se que o ESP32 está em modo advertising
- Reinicie o ESP32 e tente novamente

**Conexão BLE falha:**
- Verifique distância entre dispositivos (< 10m)
- Feche outras aplicações BLE
- Reinicie o serviço Bluetooth do sistema

**Dados não chegam:**
- Verifique se o botão "Record" está sendo pressionado no ESP32
- Confirme se o botão "Send" foi pressionado
- Monitore o Serial do ESP32 para debug

**Gráfico não atualiza:**
- Verifique conexão de rede
- Confira console do navegador para erros JavaScript
- Recarregue a página

## 🔮 Funcionalidades Futuras

- [ ] **Calibração de Sensores**: Interface para calibrar offsets/ganhos
- [ ] **Filtros Digitais**: Implementar filtros passa-baixa nos dados
- [ ] **Alertas**: Sistema de notificações para valores fora da faixa
- [ ] **Histórico**: Banco de dados para armazenamento de longo prazo
- [ ] **API REST**: Endpoints para integração com outros sistemas
- [ ] **Dashboard Móvel**: App nativo para Android/iOS

## 👨‍💻 Desenvolvimento

### Estrutura Modular
O projeto foi desenvolvido seguindo princípios de arquitetura limpa:

- **Separação de Responsabilidades**: Cada módulo tem função específica
- **Baixo Acoplamento**: Componentes independentes e reutilizáveis
- **Alta Coesão**: Funcionalidades relacionadas agrupadas
- **Padrões Flask**: Uso de Blueprints e factory pattern

### Testes
```bash
# Para testar componentes individuais
python -m pytest tests/

# Para teste manual da API
curl http://localhost:5000/api/status
```

## 📝 Licença

Este projeto é open source e está disponível sob a licença MIT.
