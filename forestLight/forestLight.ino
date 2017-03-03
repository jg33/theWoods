/*\\                                        //*\

 CONTROL FOR MOTORS AND LIGHTS FOR "THE WOODS"
              BY JESSE GARRISON

*/                                          //*\

#include <AccelStepper.h>
#include <MultiStepper.h>

#define MOTOR_PIN_1 2
#define MOTOR_PIN_2 3
#define MOTOR_PIN_3 4
#define MOTOR_PIN_4 5
#define LIGHT_PIN 6
#define MINBUTTON_PIN 7
#define MAXBUTTON_PIN 8

int intensity = 0;

bool atMin = false;
bool atMax = false;
int maxSteps = 1000;

String serialInput = "";
bool inputStringComplete = false;

bool isCalibrating = false;
int calibrationPhase = 0;

int debugCount = 0;
AccelStepper motor(8,MOTOR_PIN_1, MOTOR_PIN_3,MOTOR_PIN_2,MOTOR_PIN_4) ;


void setup() {
  //setup serial
  Serial.begin(115200);
  Serial.println("Hello.");

  serialInput.reserve(200);
  
  //setup pins
  pinMode(LIGHT_PIN, OUTPUT);
  pinMode(MINBUTTON_PIN, INPUT);
  pinMode(MAXBUTTON_PIN, INPUT);
  
  //motor setup
  motor.setMaxSpeed(1000.0);
  motor.setAcceleration(1000.0);
  
  
  //calibrate();
  
}

void loop() {
  //calibration routine
  if(isCalibrating){
    switch(calibrationPhase){
     case 0:
       //set to 50% brighness, move to min
       intensity=127;
       if(!atMin) motor.move(-1);
       if(atMin) calibrationPhase++;
     break;
     case 1:
       //move to max
       if(!atMax) motor.move(1);
       if(atMax) calibrationPhase++;
     break; 
     case 2:
       //move to center
       motor.moveTo(maxSteps/2);
       calibrationPhase++;
     break;
     case 3:
       // if at center, get bright
       if(motor.currentPosition()==maxSteps/2) intensity = 254;
       if(motor.currentPosition()==maxSteps/2) calibrationPhase++;
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
  //getMinMaxStatus();
  
  //run motor a
  if(!atMin && !atMax){
     motor.run();
  } else if (atMin){
     motor.stop();
     motor.setCurrentPosition(0);
  } else if (atMax){
     motor.stop();
     maxSteps = motor.currentPosition();
     sendMaxPos('a',maxSteps);
  }
  
  //set brightness of light a
  analogWrite(LIGHT_PIN, intensity);

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
  Serial.println("/debug got serial!");
  while (Serial.available()){
    char inChar = (char)Serial.read();
    // add it to the inputString:
    serialInput += inChar;
    // if the incoming character is a newline, set a flag
    // so the main loop can do something about it:
    if (inChar == '\n'|| inChar == '\r') {
      inputStringComplete = true;
    }
    
  }
  
  
}


///////

void sendMaxPos(char motorID, int pos){
    String posMsg = "/maxPos ";
    posMsg+= debugCount;
    Serial.println(posMsg);
}

void getMinMaxStatus(){
  if(digitalRead(MINBUTTON_PIN)==HIGH){
    atMin = true;
  } else {
    atMin = false;
  }
  
  if(digitalRead(MAXBUTTON_PIN)==HIGH){
    atMax = true;
  } else {
    atMax = false;
  }
  
}


void calibrate(){
  isCalibrating = true;
  calibrationPhase =0;
}

/////
void parseCommand(String msg){
  Serial.println("/debug parsing");
 
  char cmd = msg.charAt(0);
  Serial.println("/debug/command "+cmd);
  
  if(cmd=='i'){ 
    //intensity
    signed int val = msg.substring(1,msg.length()-1).toInt();
    intensity = val;
    //Serial.println("/debug/intensity "+ String(val));
    
  } else if(cmd=='p'){ 
    //position
     String stringVal = msg.substring(2, msg.length()-1);
     //Serial.println("/debug "+stringVal);
     
     long val = stringVal.toInt();
     //Serial.println("/debug "+ val);

     motor.moveTo(val);
     Serial.println("/debug/position "+String(val));
     
  } else if(cmd=='x'){
    //identify
    identify();
    
  } else if (cmd=='-'){
    motor.move(-100);
  } else if (cmd=='='){
    motor.move(100);

  } else if (cmd=='c'){
    calibrate(); 
  }

}

void identify(){
    analogWrite(LIGHT_PIN, 255);
    delay(500);
    analogWrite(LIGHT_PIN, 0);
    delay(500);
    analogWrite(LIGHT_PIN, 255);
    delay(500);
    analogWrite(LIGHT_PIN, 0);
    delay(500);
    analogWrite(LIGHT_PIN, 255);
    delay(500);
    analogWrite(LIGHT_PIN, 0);
    delay(500);
    analogWrite(LIGHT_PIN, intensity);

}


