#include <Arduino.h>
#include <vector>
#include <cstdint>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

// -------------------- Estrutura do Payload --------------------
struct __attribute__((packed)) PL {
  uint8_t sLed;      // ATUAL: Controle GH 2 bits (0-3) | FUTURO: 3 bits (0-7)
  int rSensor[4];    // ATUAL: 4 sensores | FUTURO: expandir para rSensor[6]
  uint32_t timeStamp;
};

// TODO: Estrutura expandida para futuras melhorias:
/*
struct __attribute__((packed)) PL_EXPANDIDO {
  uint8_t sLed;      // GH 3 bits (0-7)
  int rSensor[6];    // 6 sensores (pinos 34,35,36,39,33,32)
  uint32_t timeStamp;
};
*/

// -------------------- Definições --------------------
const int sensores[] = {34, 35, 36, 39};
// TODO: Para expansão de sensores, adicionar pinos 33 e 32:
// const int sensores[] = {34, 35, 36, 39, 33, 32};  // 6 sensores total
// CIRCUITO ELÉTRICO: Já preparado para receber os sensores nos pinos 33 e 32

// MODIFICADO: Pinos para controle GH (Gain/Hardware) - CONFIGURAÇÃO ATUAL: 2 BITS (0-3)
const int gh_pin_27 = 27;  // Sempre LOW (bit mais significativo fixo)
const int gh_pin_26 = 26;  // Bit 1 do controle GH
const int gh_pin_25 = 25;  // Bit 0 do controle GH

// TODO: Para expansão GH de 2 bits (0-3) para 3 bits (0-7):
// - Usar pino 27 como bit 2 ativo (não mais fixo em LOW)
// - Manter pinos 26 (bit 1) e 25 (bit 0) 
// - Modificar função atualizarGH() para 3 bits
// - Alterar random(0, 4) para random(0, 8) no loop
// CONFIGURAÇÃO FUTURA 3 BITS:
// const int gh_pin_27 = 27;  // Bit 2 do controle GH (0-7)
// const int gh_pin_26 = 26;  // Bit 1 do controle GH  
// const int gh_pin_25 = 25;  // Bit 0 do controle GH

const int botaoRecord = 23;
const int sendButton = 18;
const int led_status = 2;
const int potenciometro = 4;

bool deviceConnected = false;
bool oldDeviceConnected = false;
bool ledState = false;
unsigned long ultimoBlink = 0;
const unsigned long intervaloBlink = 500;

std::vector<PL> vetorRecord;
int val_sensor[4];  // ATUAL: 4 sensores | FUTURO: int val_sensor[6] para 6 sensores
uint32_t timestamp = 0;
uint8_t intLed = 0;  // ATUAL: GH 2 bits (0-3) | FUTURO: 3 bits (0-7)
unsigned long ultimaTroca = 0;

// Intervalo controlado pelo potenciômetro
unsigned long intervaloTroca = 1000;
const unsigned long minIntervalo = 250;   // 0.25s em ms
const unsigned long maxIntervalo = 4000;  // 4.0s em ms

BLEServer *pServer = nullptr;
BLECharacteristic *pCharacteristic = nullptr;

// -------------------- BLE UUIDs --------------------
#define SERVICE_UUID        "12345678-1234-1234-1234-1234567890ab"
#define CHARACTERISTIC_UUID "abcd1234-5678-90ab-cdef-1234567890ab"

// -------------------- Funções --------------------

// ATUAL: Controla pinos GH baseado no valor 0-3 (2 bits)
void atualizarGH(uint8_t valorGH) {
  // CONFIGURAÇÃO ATUAL - 2 BITS (0-3):
  // Pino 27 sempre LOW
  digitalWrite(gh_pin_27, LOW);
  
  // Pinos 26 e 25 controlam os 2 bits (0-3)
  digitalWrite(gh_pin_26, (valorGH >> 1) & 0x01);  // Bit 1
  digitalWrite(gh_pin_25, valorGH & 0x01);         // Bit 0
  
  // Debug: mostra estado dos pinos
  Serial.printf("GH=%d | Pin27:%d Pin26:%d Pin25:%d\n", 
                valorGH, 
                digitalRead(gh_pin_27),
                digitalRead(gh_pin_26), 
                digitalRead(gh_pin_25));

  // TODO: EXPANSÃO PARA 3 BITS (0-7) - IMPLEMENTAÇÃO FUTURA:
  /*
  // CONFIGURAÇÃO FUTURA - 3 BITS (0-7):
  digitalWrite(gh_pin_27, (valorGH >> 2) & 0x01);  // Bit 2
  digitalWrite(gh_pin_26, (valorGH >> 1) & 0x01);  // Bit 1  
  digitalWrite(gh_pin_25, valorGH & 0x01);         // Bit 0
  
  // Tabela de estados para 3 bits:
  // GH=0: 000 | GH=1: 001 | GH=2: 010 | GH=3: 011
  // GH=4: 100 | GH=5: 101 | GH=6: 110 | GH=7: 111
  */
}

// ATUAL: Lê 4 sensores
void lerSensores() {
  for (int i = 0; i < 4; i++) {
    val_sensor[i] = analogRead(sensores[i]);
  }
  
  // TODO: EXPANSÃO PARA 6 SENSORES - IMPLEMENTAÇÃO FUTURA:
  /*
  // Leitura expandida para 6 sensores (incluindo pinos 33 e 32):
  for (int i = 0; i < 6; i++) {
    val_sensor[i] = analogRead(sensores[i]);
  }
  // CIRCUITO: Pinos 33 e 32 já estão preparados eletricamente
  */
}

// Leitura e mapeamento do potenciômetro
void atualizarIntervaloTroca() {
  int valorPot = analogRead(potenciometro);  // Lê valor 0-4095 (12-bit ADC)
  
  // Mapeia o valor do potenciômetro (0-4095) para o intervalo (250-4000ms)
  intervaloTroca = map(valorPot, 0, 4095, minIntervalo, maxIntervalo);
  
  // Debug: imprime valores ocasionalmente para monitoramento
  static unsigned long ultimoDebug = 0;
  if (millis() - ultimoDebug >= 2000) {  // A cada 2 segundos
    Serial.printf("Potenciômetro: %d | Intervalo: %lu ms (%.2f s)\n", 
                  valorPot, intervaloTroca, intervaloTroca / 1000.0);
    ultimoDebug = millis();
  }
}

void gravarPayload() {
  PL novoPayload;
  novoPayload.sLed = intLed;  // ATUAL: GH 2 bits (0-3) | FUTURO: 3 bits (0-7)
  novoPayload.timeStamp = timestamp;
  
  // ATUAL: Copia 4 sensores
  for (int i = 0; i < 4; i++) {
    novoPayload.rSensor[i] = val_sensor[i];
  }
  // TODO: Para 6 sensores, alterar loop para i < 6
  
  vetorRecord.push_back(novoPayload);

  Serial.printf("%lu: S1: %d | S2: %d | S3: %d | S4: %d | GH: %d\n",
                timestamp, val_sensor[0], val_sensor[1], val_sensor[2], val_sensor[3], intLed);
  // TODO: Para 6 sensores, adicionar S5 e S6 no printf
  
  Serial.printf("Tamanho Bytes: %d | Tamanho Vetor: %d\n",
                sizeof(PL) * vetorRecord.size(), vetorRecord.size());
}

void enviarPayloadsBLE() {
  if (!deviceConnected) return;

  size_t totalSize = vetorRecord.size() * sizeof(PL);
  if (totalSize == 0) return;

  const uint8_t *dataPtr = reinterpret_cast<const uint8_t *>(vetorRecord.data());
  const size_t mtu = 180;  // MTU prático para BLE
  for (size_t offset = 0; offset < totalSize; offset += mtu) {
    size_t chunkSize = min(mtu, totalSize - offset);
    pCharacteristic->setValue((uint8_t *)(dataPtr + offset), chunkSize);
    pCharacteristic->notify();
    delay(20); // Delay para garantir envio
  }

  Serial.println("Vetor enviado via BLE!");
  
  // OPCIONAL: Limpa vetor após envio para economizar memória
  // vetorRecord.clear();
}

// -------------------- Callbacks BLE --------------------
class MyServerCallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer* pServer) {
    deviceConnected = true;
    Serial.println("Dispositivo conectado!");
  }

  void onDisconnect(BLEServer* pServer) {
    deviceConnected = false;
    Serial.println("Dispositivo desconectado!");
  }
};

// -------------------- Setup --------------------
void setup() {
  Serial.begin(115200);

  // Configuração dos pinos de sensores
  for (int i = 0; i < 4; i++) {
    pinMode(sensores[i], INPUT);
  }
  // TODO: Para expansão de sensores, descomentar:
  // pinMode(33, INPUT);  // Sensor 5 - circuito já preparado
  // pinMode(32, INPUT);  // Sensor 6 - circuito já preparado
  
  // MODIFICADO: Configuração dos pinos GH - ATUAL: 2 BITS (0-3)
  pinMode(gh_pin_27, OUTPUT);  // ATUAL: Sempre LOW | FUTURO: Bit 2 ativo
  pinMode(gh_pin_26, OUTPUT);  // Bit 1 do GH
  pinMode(gh_pin_25, OUTPUT);  // Bit 0 do GH
  
  // Configuração outros pinos
  pinMode(botaoRecord, INPUT);
  pinMode(sendButton, INPUT);
  pinMode(led_status, OUTPUT);
  pinMode(potenciometro, INPUT);

  // MODIFICADO: Inicializa GH com valor 1 (01 em binário)
  intLed = 1;
  atualizarGH(intLed);

  // Leitura inicial do potenciômetro
  atualizarIntervaloTroca();
  Serial.printf("Intervalo inicial de troca: %lu ms\n", intervaloTroca);
  Serial.println("=== CONFIGURAÇÃO ATUAL DO SISTEMA ===");
  Serial.println("SENSORES: 4 sensores ativos (pinos 34, 35, 36, 39)");
  Serial.println("  > EXPANSÃO DISPONÍVEL: Pinos 33 e 32 preparados no circuito");
  Serial.println("GH CONTROL: 2 bits ativos (valores 0-3)");
  Serial.println("  Pin 27: Sempre LOW (bit fixo)");
  Serial.println("  Pin 26: Bit 1 do controle GH");
  Serial.println("  Pin 25: Bit 0 do controle GH");
  Serial.println("  > EXPANSÃO DISPONÍVEL: Pin 27 pode ser ativado para 3 bits (0-7)");
  Serial.println("==========================================");

  // Configuração BLE
  BLEDevice::init("ESP32-SENSOR-SERVER");
  pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  BLEService *pService = pServer->createService(SERVICE_UUID);
  pCharacteristic = pService->createCharacteristic(
    CHARACTERISTIC_UUID,
    BLECharacteristic::PROPERTY_NOTIFY
  );
  pCharacteristic->addDescriptor(new BLE2902());

  pService->start();
  pServer->getAdvertising()->start();
  Serial.println("Aguardando conexão BLE...");
}

// -------------------- Loop --------------------
void loop() {
  unsigned long agora = millis();

  // Atualiza intervalo baseado no potenciômetro
  atualizarIntervaloTroca();

  // Reinicia advertising quando desconecta
  if (!deviceConnected && oldDeviceConnected) {
    delay(500); // Pequeno delay antes de reiniciar
    pServer->startAdvertising();
    Serial.println("Reiniciando advertising BLE...");
    oldDeviceConnected = deviceConnected;
  }
  
  // Atualiza estado da conexão
  if (deviceConnected && !oldDeviceConnected) {
    oldDeviceConnected = deviceConnected;
    Serial.println("Cliente conectado!");
  }

  // Piscar LED de status se desconectado, caso contrário LED fixo aceso
  if (deviceConnected) {
    digitalWrite(led_status, HIGH);
  } else {
    if (agora - ultimoBlink >= intervaloBlink) {
      ledState = !ledState;
      digitalWrite(led_status, ledState);
      ultimoBlink = agora;
    }
  }

  // MODIFICADO: Alternar valor GH (0-3) com intervalo dinâmico
  if (agora - ultimaTroca >= intervaloTroca) {
    intLed = random(0, 4);  // ATUAL: Gera valores 0-3 (2 bits)
    // TODO: Para GH 3 bits, alterar para: intLed = random(0, 8);
    
    atualizarGH(intLed);    // Atualiza pinos GH
    ultimaTroca = agora;
    
    Serial.printf("Mudança GH para: %d\n", intLed);
  }

  // Lê sensores continuamente - ATUAL: 4 sensores
  lerSensores();
  // TODO: Com 6 sensores, lerSensores() já lerá automaticamente pelos arrays expandidos

  // Gravar payload somente se botão de gravar estiver pressionado
  if (digitalRead(botaoRecord) == HIGH) {
    gravarPayload();
  }

  // Enviar vetor somente se botão enviar estiver pressionado
  if (digitalRead(sendButton) == LOW) {
    enviarPayloadsBLE();
  }

  timestamp++;
  delay(50);
}