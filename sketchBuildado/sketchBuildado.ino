#include <Arduino.h>
#include <vector>
#include <cstdint>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

// -------------------- Estrutura do Payload --------------------
struct __attribute__((packed)) PL {
  uint8_t sLed;
  int rSensor[4];
  uint32_t timeStamp;
};

// -------------------- Definições --------------------
const int sensores[] = {34, 35, 36, 39};
const int sLed[] = {26, 27};
const int botaoRecord = 23;
const int sendButton = 18;
const int led_status = 13;
const int potenciometro = 4;  // NOVO: GPIO do potenciômetro

bool deviceConnected = false;
bool oldDeviceConnected = false;
bool ledState = false;
unsigned long ultimoBlink = 0;
const unsigned long intervaloBlink = 500;

std::vector<PL> vetorRecord;
int val_sensor[4];
uint32_t timestamp = 0;
uint8_t intLed = 0;
unsigned long ultimaTroca = 0;

// MODIFICADO: intervalo agora é variável controlado pelo potenciômetro
unsigned long intervaloTroca = 1000;  // Valor inicial padrão
const unsigned long minIntervalo = 250;   // 0.25s em ms
const unsigned long maxIntervalo = 4000;  // 4.0s em ms

BLEServer *pServer = nullptr;
BLECharacteristic *pCharacteristic = nullptr;

// -------------------- BLE UUIDs --------------------
#define SERVICE_UUID        "12345678-1234-1234-1234-1234567890ab"
#define CHARACTERISTIC_UUID "abcd1234-5678-90ab-cdef-1234567890ab"

// -------------------- Funções --------------------
void atualizarLEDs(uint8_t estado) {
  digitalWrite(sLed[0], estado & 0x01);
  digitalWrite(sLed[1], (estado >> 1) & 0x01);
}

void lerSensores() {
  for (int i = 0; i < 4; i++) {
    val_sensor[i] = analogRead(sensores[i]);
  }
}

// NOVA FUNÇÃO: Leitura e mapeamento do potenciômetro
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
  novoPayload.sLed = intLed;
  novoPayload.timeStamp = timestamp;
  for (int i = 0; i < 4; i++) {
    novoPayload.rSensor[i] = val_sensor[i];
  }
  vetorRecord.push_back(novoPayload);

  Serial.printf("%lu: S1: %d | S2: %d | S3: %d | S4: %d | Led: %d\n",
                timestamp, val_sensor[0], val_sensor[1], val_sensor[2], val_sensor[3], intLed);
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

  for (int i = 0; i < 4; i++) pinMode(sensores[i], INPUT);
  pinMode(sLed[0], OUTPUT);
  pinMode(sLed[1], OUTPUT);
  pinMode(botaoRecord, INPUT);
  pinMode(sendButton, INPUT);
  pinMode(led_status, OUTPUT);
  pinMode(potenciometro, INPUT);  // NOVO: Configura pino do potenciômetro

  atualizarLEDs(1);

  // NOVO: Leitura inicial do potenciômetro
  atualizarIntervaloTroca();
  Serial.printf("Intervalo inicial de troca: %lu ms\n", intervaloTroca);

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

  // NOVO: Atualiza intervalo baseado no potenciômetro
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

  // MODIFICADO: Alternar LEDs com intervalo dinâmico baseado no potenciômetro
  if (agora - ultimaTroca >= intervaloTroca) {
    intLed = random(0, 4);
    atualizarLEDs(intLed);
    ultimaTroca = agora;
  }

  lerSensores();

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