/*\\                                        //*\

 CONTROL FOR MOTORS AND LIGHTS FOR "THE WOODS"
              BY JESSE GARRISON

*/                                          //*\

#include <AccelStepper.h>
#include <MultiStepper.h>

#define A_MOTOR_PIN_1 2
#define A_MOTOR_PIN_2 3
#define A_MOTOR_PIN_3 4
#define A_MOTOR_PIN_4 5
#define A_LIGHT_PIN 6
#define A_MINBUTTON_PIN 7
#define A_MAXBUTTON_PIN 8

//#define B_MOTOR_PIN_1 A0
//#define B_MOTOR_PIN_2 A1
//#define B_MOTOR_PIN_3 A2
//#define B_MOTOR_PIN_4 A3
//#define B_LIGHT_PIN A4
//#define B_MINBUTTON_PIN A5 
//#define B_MAXBUTTON_PIN A6
//int lightBintensity = 0;
//bool BatMin = false;
//bool BatMax = false;
//int Bmax = 1000;
//AccelStepper motorB(AccelStepper::FULL4WIRE,B_MOTOR_PIN_1, B_MOTOR_PIN_2,B_MOTOR_PIN_3,B_MOTOR_PIN_4) ;


int lightAintensity = 0;

bool AatMin = false;
bool AatMax = false;
int Amax = 1000;

String serialInput = "";
bool inputStringComplete = false;

bool isCalibrating = false;
int calibrationPhase = 0;

int debugCount = 0;
AccelStepper motorA(AccelStepper::FULL4WIRE,A_MOTOR_PIN_1, A_MOTOR_PIN_2,A_MOTOR_PIN_3,A_MOTOR_PIN_4) ;


void setup() {
  //setup serial
  Serial.begin(115200);
  Serial.println("Hello.");

  serialInput.reserve(200);
  
  //setup pins
  pinMode(A_LIGHT_PIN, OUTPUT);
  pinMode(A_MINBUTTON_PIN, INPUT);
  pinMode(A_MAXBUTTON_PIN, INPUT);
  pinMode(B_LIGHT_PIN, OUTPUT);
  pinMode(B_MINBUTTON_PIN, INPUT);
  pinMode(B_MAXBUTTON_PIN, INPUT);
  
  calibrate();
  
}

void loop() {
  //calibration routine
  if(isCalibrating){
    switch(calibrationPhase){
     case 0:
       //set to 50% brighness, move to min
       lightAintensity=127;
       lightBintensity=127;
     //  if(!AatMin) motorA.move(-1);
     //  if(!BatMin) motorB.move(-1); 
       if(AatMin&&BatMin) calibrationPhase++;
     break;
     case 1:
       //move to max
      // if(!AatMax) motorA.move(1);
      // if(!BatMax) motorB.move(1);
       if(AatMax&&BatMax) calibrationPhase++;
     break; 
     case 2:
       //move to center
      // motorA.moveTo(Amax/2);
      // motorB.moveTo(Bmax/2);
       calibrationPhase++;
     break;
     case 3:
       // if at center, get bright
      // if(motorA.currentPosition()==Amax/2) lightAintensity = 254;
      // if(motorB.currentPosition()==Bmax/2) lightBintensity = 254;
      // if(motorA.currentPosition()==Amax/2 && motorB.currentPosition()==Bmax/2) calibrationPhase++;
     break;
     case 4:
       isCalibrating = false;
       calibrationPhase = 0;
     break;
     
    }
    
    
  }
  
  //deal with serial, if not calibrating
  if(inputStringComplete && !isCalibrating){
    parseCommand(serialInput);
    serialInput="";
    inputStringComplete=false;
  }
  
  //check min / max status
  getMinMaxStatus();
  
  //run motor a
  if(!AatMin && !AatMax){
    // motorA.run();
  } else if (AatMin){
    // motorA.stop();
    // motorA.setCurrentPosition(0);
  } else if (AatMax){
    // motorA.stop();
    // Amax = motorA.currentPosition();
    sendMaxPos('a',Amax);
  }
  
  //set brightness of light a
  analogWrite(A_LIGHT_PIN, lightAintensity);
  
  //run motor b;
  //set brightness of light b
  
  //debugging;
  //String debugMsg = "/debug/this ";
  //debugMsg += debugCount;
 // Serial.println(debugMsg);
 // debugCount++;
}


/// serial stuff ///
void serialEventRun(void) {
  if (Serial.available()) serialEvent();
}

void serialEvent(){
  //get serial
  Serial.println("got serial!");
  while (Serial.available()){
    char inChar = (char)Serial.read();
    // add it to the inputString:
    serialInput += inChar;
    // if the incoming character is a newline, set a flag
    // so the main loop can do something about it:
    if (inChar == '\n') {
      inputStringComplete = true;
    }
    
  }
  
  
}


///////

void sendMaxPos(char motorID, int pos){
  if(motorID=='a'){
    String posMsg = "/light/a/maxPos ";
    posMsg+= debugCount;
    Serial.println(posMsg);
    
  } else if (motorID=='b'){
    String posMsg = "/light/b/maxPos ";
    posMsg+= pos;
    Serial.println(posMsg);
  }
  
}

void getMinMaxStatus(){
  if(digitalRead(A_MINBUTTON_PIN)==HIGH){
    AatMin = true;
  } else {
    AatMin = false;
  }
  
  if(digitalRead(A_MAXBUTTON_PIN)==HIGH){
    AatMax = true;
  } else {
    AatMax = false;
  }
  
  if(digitalRead(B_MINBUTTON_PIN)==HIGH){
    BatMin = true;
  } else {
    BatMin = false;
  }
  
  if(digitalRead(B_MAXBUTTON_PIN)==HIGH){
    BatMax = true;
  } else {
    BatMax = false;
  }
  
}


void calibrate(){
  isCalibrating = true;
  calibrationPhase =0;
}

/////
void parseCommand(String msg){
  Serial.println("parsing");
 
  char cmd = msg.charAt(0);
  Serial.println(cmd);
  if(cmd=='i'){ //intensity
    
    Serial.println("intensity!");
    int val = msg.substring(1).toInt();
    Serial.println(val);

  } else if(cmd=='p'){ //position
     Serial.println("position!");

    
  } else if(cmd=='x'){//identify
    identify();
    
  }

}

void identify(){
    analogWrite(A_LIGHT_PIN, 255);
    delay(500);
    analogWrite(A_LIGHT_PIN, 0);
    delay(500);
    analogWrite(A_LIGHT_PIN, 255);
    delay(500);
    analogWrite(A_LIGHT_PIN, 0);
    delay(500);
    analogWrite(A_LIGHT_PIN, 255);
    delay(500);
    analogWrite(A_LIGHT_PIN, 0);
    delay(500);
    analogWrite(A_LIGHT_PIN, lightAintensity);

}


