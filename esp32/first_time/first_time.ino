#include <Arduino.h>

// Definindo os pinos dos sensores
const int sensor1 = 32;
const int sensor2 = 33;
const int sensor3 = 34;
const int sensor4 = 35;

const int led1 = 2;
const int led2 = 4;
const int led3 = 18;
const int led4 = 19;

const int ledsinal[] = { 12, 14, 27, 26 };
const int numLedsSinal = 4;

unsigned long ultimoTempo = 0;
const unsigned long intervalo = 1000;

void setup() {
  Serial.begin(115200);

  // Configurar os pinos dos LEDs como saída
  pinMode(led1, OUTPUT);
  pinMode(led2, OUTPUT);
  pinMode(led3, OUTPUT);
  pinMode(led4, OUTPUT);
  for (int i = 0; i < numLedsSinal; i++) {
    pinMode(ledsinal[i], OUTPUT);
    digitalWrite(ledsinal[i], LOW);
  }

  randomSeed(analogRead(0));
}

void loop() {
  // Leitura dos sensores
  float val1 = analogRead(sensor1);
  float val2 = analogRead(sensor2);
  float val3 = analogRead(sensor3);
  float val4 = analogRead(sensor4);

  // Conversão para peso em kg (supondo que 4095 = 0kg e 400 ≈ 2kg)
  float peso1 = (4095.0 - val1) * (2.0 / (4095.0 - 370.0));
  float peso2 = (4095.0 - val2) * (2.0 / (4095.0 - 370.0));
  float peso3 = (4095.0 - val3) * (2.0 / (4095.0 - 370.0));
  float peso4 = (4095.0 - val4) * (2.0 / (4095.0 - 370.0));

  // Evita valores negativos
  if (peso1 < 0) peso1 = 0;
  if (peso2 < 0) peso2 = 0;
  if (peso3 < 0) peso3 = 0;
  if (peso4 < 0) peso4 = 0;

  // Mapear o peso (0–2kg) para brilho (0–255)
  int brilho1 = constrain(peso1 * 127.5, 0, 255);
  int brilho2 = constrain(peso2 * 127.5, 0, 255);
  int brilho3 = constrain(peso3 * 127.5, 0, 255);
  int brilho4 = constrain(peso4 * 127.5, 0, 255);

  Serial.print("Sensor 1: ");
  Serial.print(peso1, 2);
  Serial.println(" kg");
  Serial.print("Sensor 2: ");
  Serial.print(peso2, 2);
  Serial.println(" kg");
  Serial.print("Sensor 3: ");
  Serial.print(peso3, 2);
  Serial.println(" kg");
  Serial.print("Sensor 4: ");
  Serial.print(peso4, 2);
  Serial.println(" kg");
  Serial.println("----------------------");

  // Aplicar PWM nos LEDs com analogWrite
  analogWrite(led1, brilho1);
  analogWrite(led2, brilho2);
  analogWrite(led3, brilho3);
  analogWrite(led4, brilho4);

  // Atualiza LED de sinal a cada 1 segundo
  if (millis() - ultimoTempo >= intervalo) {
    ultimoTempo = millis();

    // Desliga todos
    for (int i = 0; i < numLedsSinal; i++) {
      digitalWrite(ledsinal[i], LOW);
    }

    // Liga um aleatório
    int escolhido = random(numLedsSinal);
    digitalWrite(ledsinal[escolhido], HIGH);
  }
}
