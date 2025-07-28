// includes
  #include <Arduino.h>
  #include <vector>
  #include <cstdint>

// pinagem
  int out_ledStatus =13; //led que fala status do bluetooth
  int in_potVelocidadeGH = 4; //entrada do potenciometro de velocidade do GH
  int in_sensorReading[] = {34,35,36,39}; //leitura dos sensores
  int in_isRec = 23; //leitura para ver se está gravando
  int in_buttonSend = 18; //botão que verifica se vamos enviar o pacote
  int out_GH[] = {26,27}; //o led GH que vai ser sinalizado

// declaração de objetos
  struct __attribute__((packed)) PL{ 
    uint8_t sinalized_GH;
    float sensorReading[4];
    uint32_t timeStamp;
  }; // Struct com o snapshot do momento de leitura

  int timestamp = 0; //inicializa o primeiro tick como 0
  int waitTimes = 0; //inicializa o wait times como 0 também

// máquina de estados
  enum Estado { 
    waitingConnectionBLE,
    connectingBLE,
    idle,
    recording,
    sendingPacket
  }

// funcoes

void stateWaitingConnectionBLE(){
  //abre o ble para conectarem, espera alguém fazer o pedido
  Serial.printf("Estado: Waiting Connection BLE");
}

void stateConnectingBLE(){
  //faz todo o processo de conexão com ble
  Serial.printf("Estado: ConnectingBLE");
  
}

void stateIdle(){
  //após conectado, esse é o estado onde estará funcionando tudo
  Serial.printf("stateIdle");
}

void stateRecording(){
  //esse é o estado quando tiver gravando, ou seja, in_isRec == HIGH.
  Serial.printf("stateRecording");
}

void stateSendingPacket(){
  //estado que vai enviar o pacote via bluetooth
  Serial.printf("Enviando Pacote");
}

void setup() {
  std::vector<PL> vetorRecord;

  // PinModes:
  pinMode(in_potVelocidadeGH,INPUT);
  pinMode(in_isRec,INPUT);
  pinMode(in_buttonSend,INPUT);
  pinMode(out_ledStatus,OUTPUT);
  pinMode(out_GH[0],OUTPUT);
  pinMode(out_GH[1],OUTPUT);
  pinMode(out_ledStatus,OUTPUT);

  for(int i = 0; i < 4; i++){
    pinMode(in_sensorReading[i,INPUT];)
  }

  Estado estadoAtual = waitingConnectionBLE;
}

void loop() {
  switch(estadoAtual):
  
    case waitingConnectionBLE:
    stateWaitingConnectionBLE();
    Delay(1000);
    estadoAtual = connectingBLE;
    break;
    
    case connectingBLE:
    stateConnectingBLE();
    Delay(1000);
    estadoAtual = idle;
    break;
    
    case idle:
    stateIdle();
    break;
    
    case recording:
    stateRecording();
    break;

    case sendingPacket:
    stateSendingPacket();
    break;
}
