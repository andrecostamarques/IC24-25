typedef struct payLoad { 
  int sLed;
  float rSensor[4];
  uint32_t timeStamp;
} PL;

#include <Arduino.h>

int sensores[]={32,33,34,35};
int leds[]={2,4,18,19};
int ledsinal[] = {12,14,27,26};
int waitTimes = 0;
int brilhos[4];
float val_sensor[4];

PL writeStruct(int sLed, float val_sensor[4], uint32_t timeStamp){

}

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  //seta os pinmodes
  for(int i = 0; i < 4; i++){
    pinMode(leds[i],OUTPUT);
    pinMode(ledsinal[i],OUTPUT);
  }

}

void loop() {
  //adiciona o waitTime 
  waitTimes++;

  //le os sensores
  for(int i = 0; i < 4; i++){
    val_sensor[i] = analogRead(sensores[i]);
  }

  //transforma o valor da voltagem em kg
  for(int i = 0; i < 4; i++){
    val_sensor[i] = (4095.0 - val_sensor[i]) * (2.0/ (4095.0 - 370.0));
    if(val_sensor[i] < 0) val_sensor[i] = 0;
    brilhos[i] = constrain(val_sensor[i] * 127.5, 0, 255);
  }
  
  //printa os leds
  for(int i  = 0; i < 4; i++){
    analogWrite(leds[i], brilhos[i]);
  }
  //se já deu o tempo de execução
  if(waitTimes > 20){
    int rand  = random(0,3);

    //executar leds
    for(int i = 0; i < 4; i++){
      analogWrite(ledsinal[i], 0);
    }

    analogWrite(ledsinal[rand],255.0);

    //reseta waitTimes
    waitTimes = 0;
  }


  delay(50);
}
