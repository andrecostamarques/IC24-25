#include <Arduino.h>
#include <vector>
#include <cstdint>

struct PL { 
  uint8_t sLed;
  float rSensor[4];
  uint32_t timeStamp;
};

int sensores[]={32,33,34,35};
int leds[]={2,4,18,19};
int ledsinal[] = {12,14,27,26};
int waitTimes = 0;
int brilhos[4];
float val_sensor[4];
int sLed = 0;

int botao_record = 16;   // GPIO onde está conectado o botão
int led_record = 17;  // GPIO onde está conectado o LED

bool isRecording = false;
bool lastButton = LOW;

int timestamp = 0;

void checkRecording(int botao_record, int led_record){

  if(digitalRead(botao_record) == HIGH && lastButton == LOW){
    isRecording = !isRecording;
    digitalWrite(led_record, isRecording);
  }

  lastButton = digitalRead(botao_record);

} //teste

//funcao que envia o struct pro vetor
void writeStruct(std::vector<PL>& vetor, uint8_t sLed, float val_sensor[4], uint32_t timeStamp){

  PL novoPayload;
  novoPayload.sLed = sLed;
  novoPayload.timeStamp = timeStamp;
  for(int i = 0; i < 4; i++){
    novoPayload.rSensor[i] = val_sensor[i];
  }

  vetor.push_back(novoPayload);
}

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  //seta os pinmodes
  for(int i = 0; i < 4; i++){
    pinMode(leds[i],OUTPUT);
    pinMode(ledsinal[i],OUTPUT);
  }

  pinMode(botao_record, INPUT);    // Sem pull-up interno
  pinMode(led_record, OUTPUT);

  analogWrite(ledsinal[sLed],255.0);
  std::vector<PL> vetorGravação; 

}

void loop() {

  //toggle do botão de gravar
  checkRecording(botao_record, led_record);

  //adiciona o waitTime 
  waitTimes++;

  //le os sensores
  for(int i = 0; i < 4; i++){
    val_sensor[i] = analogRead(sensores[i]);
  }

  //transforma o valor da voltagem em kg
  for(int i = 0; i < 4; i++){
    val_sensor[i] = (4095.0 - val_sensor[i]) * (2.0/ (4095.0 - 270));
    if(val_sensor[i] < 0) val_sensor[i] = 0;
    brilhos[i] = constrain(val_sensor[i] * 127.5, 0, 255);
  }
  
  //printa os leds
  for(int i  = 0; i < 4; i++){
    analogWrite(leds[i], brilhos[i]);
  }
  //se já deu o tempo de execução
  if(waitTimes > 20){
  
    //executar leds
    analogWrite(ledsinal[sLed], 0);
    sLed  = random(0,4);

    analogWrite(ledsinal[sLed],255.0);

    //reseta waitTimes
    waitTimes = 0;
  }

  if(isRecording){
    Serial.printf("%d: S1: %.2f | S2: %.2f | S3: %.2f | S4: %.4f | Led: %d\n", timestamp, val_sensor[0], val_sensor[1], val_sensor[2], val_sensor[3], sLed);
  }
             

  timestamp++;
  delay(50);
}
