#define MOTOR_1_PIN_1 2
#define MOTOR_1_PIN_2 3
#define MOTOR_1_PIN_3 4
#define MOTOR_1_PIN_4 5
#define LIGHT_1_PIN 6
#define MOTOR_2_PIN_1 7
#define MOTOR_2_PIN_2 8
#define MOTOR_2_PIN_3 9
#define MOTOR_2_PIN_4 10
#define LIGHT_2_PIN 11
#define MOTOR_3_PIN_1 12
#define MOTOR_3_PIN_2 13
#define MOTOR_3_PIN_3 A0
#define MOTOR_3_PIN_4 A1
#define LIGHT_3_PIN A2

int id = 0;
int stepsPerTrack = 0;

void setup() {
  // put your setup code here, to run once:
  
  /* set ID based on which pin has input
  if(digitalRead(0)){
    id=0;
  } else if(digitalRead(1)){
    id=1;
  } else if (digitalRead(2)){
    id=2;
  } else {
    Serial.println("NO ID SET!"); 
  }*/
  
}

void loop() {
  

}

void calibrate(){
  
}

void stepUp(){
  
}

void stepDown(){
  
}
