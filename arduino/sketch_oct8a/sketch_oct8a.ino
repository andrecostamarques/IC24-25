#include <Servo.h>

#define SERVO 9 // Porta Digital 6 PWM
const int pinoLed = 3; //PINO DIGITAL UTILIZADO PELO LED
const int pinoLDR = A5; //PINO ANALÓGICO UTILIZADO PELO LDR

Servo s; // Variável Servo
bool ativo = true;

void setup () {
  s.attach(SERVO);
  pinMode(2, INPUT);
  pinMode(pinoLed, OUTPUT); //DEFINE O PINO COMO SAÍDA
  pinMode(pinoLDR, INPUT); //DEFINE O PINO COMO ENTRADA
  
}

void loop() {
  // Lê o valor do potenciômetro e mapeia para o ângulo do servo (0-180 graus
  // Posiciona o servo no ângulo calculado
  // if(digitalRead(2) == HIGH){
  //   ativo != ativo;
  //   delay(100);
  // }

    s.write(0);
    delay(100);
    s.write(60);
    delay(100);
 

  //   //O VALOR 600 PODE SER AJUSTADO
  // if(analogRead(pinoLDR) > 600){ //SE O VALOR LIDO FOR MAIOR QUE 600, FAZ
  //   digitalWrite(pinoLed, HIGH); //ACENDE O LED
  // }  
  // else{ //SENÃO, FAZ
  //   digitalWrite(pinoLed, LOW); //APAGA O LED
  // }  

}