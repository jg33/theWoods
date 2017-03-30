/*---------------------------------------------------------------------------------------------

  Open Sound Control (OSC) library for the ESP8266

  Example for receiving open sound control (OSC) bundles on the ESP8266
  Send integers '0' or '1' to the address "/led" to turn on/off the built-in LED of the esp8266.

  This example code is in the public domain.

--------------------------------------------------------------------------------------------- */
#include <ESP8266WiFi.h>
#include <WiFiUdp.h>
#include <OSCMessage.h>
#include <OSCBundle.h>
#include <OSCData.h>

#include <AccelStepper.h>
#include <MultiStepper.h>


char ssid[] = "THELIGHTHOUSE2";          // your network SSID (name)
char pass[] = "olieclipse";                    // your network password

// A UDP instance to let us send and receive packets over UDP
WiFiUDP Udp;
const IPAddress outIp(10,40,10,105);        // remote IP (not needed for receive)
const unsigned int outPort = 9999;          // remote port (not needed for receive)
const unsigned int localPort = 8888;        // local port to listen for UDP packets (here's where we send the packets)

// Update these with values suitable for your network.
IPAddress ip(192,168,0,28);  //Node static IP
IPAddress gateway(192,168,0,1);
IPAddress subnet(255,255,255,0);

OSCErrorCode error;
//unsigned int ledState = LOW;              // LOW means led is *on*
char packetBuffer[128]; //buffer to hold incoming packet,

// PINS ETC //
#define MOTOR_PIN_1 5
#define MOTOR_PIN_2 4
#define MOTOR_PIN_3 0
#define MOTOR_PIN_4 2
#define LIGHT_PIN 14
#define MINBUTTON_PIN D7
#define MAXBUTTON_PIN D8

float intensity = 0;
float targetIntensity = 0;

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
  pinMode(BUILTIN_LED, OUTPUT);
  //pinMode(LIGHT_PIN, PWM);
//  digitalWrite(BUILTIN_LED, ledState);    // turn *on* led

  Serial.begin(115200);

  // Connect to WiFi network
  Serial.println();
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, pass);
  WiFi.config(ip, gateway, subnet);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");

  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());

  Serial.println("Starting UDP");
  Udp.begin(localPort);
  Serial.print("Local port: ");
  Serial.println(Udp.localPort());

  //setup pins
  pinMode(LIGHT_PIN, OUTPUT);
  pinMode(MINBUTTON_PIN, INPUT);
  pinMode(MAXBUTTON_PIN, INPUT);
  
  //motor setup
  motor.setMaxSpeed(1500.0);
  motor.setAcceleration(1000.0);

}


void loop() {

  // handle OSC //
  OSCBundle bundle;
  int size = Udp.parsePacket();

  if (size > 0) {
    Udp.read(packetBuffer, UDP_TX_PACKET_MAX_SIZE);
    Serial.println("Contents:");
    String _msg = String(packetBuffer);
    Serial.println(_msg);
    parseCommand(_msg);
    
//    while (size--) {
//      bundle.fill(Udp.read());
//    }
//    if (!bundle.hasError()) {
//       //bundle.decode();
//       Serial.println("got msg");
//       Serial.println(bundle.size());
//
//      //bundle.dispatch("/led", led);
//      if(bundle.size()>0){
//        OSCMessage thisMsg;
//        thisMsg = bundle.getOSCMessage(0);
//        char addressBuff[200];
//   //   thisMsg.getAddress(addressBuff,0);
//      String msgString = "blank";//addressBuff;
////      msgString += " ";
////      msgString += String(thisMsg.getInt(0));
//      //parseCommand(msgString);
//        Serial.println(msgString);
//
//      }
//    } else {
//      //error = bundle.getError();
//      Serial.print("error: ");
//      //Serial.println(error);
//    }
  }

  //deal with serial, if not calibrating
//  if(inputStringComplete && !isCalibrating){
//    parseCommand(serialInput);
//    serialInput="";
//    inputStringComplete=false;
//  }
  
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
  
  //interpolate intensity
  if(targetIntensity == intensity || abs(targetIntensity-intensity) < 0.01){
    //don't move if equal
  } else if(targetIntensity > intensity){
    intensity+= 0.01;
  } else if(targetIntensity< intensity){
    intensity-= 0.01;
  } else{
     //do nothing 
  }
  //Serial.println((String)intensity + " "+ (String)targetIntensity);
  
  //set brightness of light a
  if(intensity<1){
    analogWrite(LIGHT_PIN, 0);
  } else {
    analogWrite(LIGHT_PIN, floor(intensity));
  }

  //debugging;
  //String debugMsg = "/debug/this ";
  //debugMsg += debugCount;
 // //Serial.println(debugMsg);
 // debugCount++;
 
  //yield();

}



/////
void parseCommand(String msg){
  Serial.println("/debug parsing");
  char msgArray[128];
  msg.toCharArray(msgArray,128);
  char cmd = msgArray[0];
  Serial.print("/debug/command ");
  Serial.println(cmd);
  
  if(cmd=='i'){ 
    //intensity
    signed int val = msg.substring(1,msg.length()).toInt();
    targetIntensity = val;
    ////Serial.println("/debug/intensity "+ String(val));
    
  } else if(cmd=='p'){ 
    //position
     String stringVal = msg.substring(1, msg.length());
     ////Serial.println("/debug "+stringVal);
     
     long val = stringVal.toInt();
     ////Serial.println("/debug "+ val);

     motor.moveTo(val);
     //Serial.println("/debug/position "+String(val));
     
  } else if(cmd=='x'){
    //identify
    Serial.println("identify");

    identify();
    
  } else if (cmd=='-'){
    String stringVal = msg.substring(1, msg.length());
    long val = stringVal.toInt();
    motor.move(-val);
    
  } else if (cmd=='='){
    String stringVal = msg.substring(1, msg.length());
    long val = stringVal.toInt();
    motor.move(val);

  } else if (cmd=='c'){
    calibrate(); 
  } else if (cmd=='r'){
    motor.setCurrentPosition(0);
  } else if (cmd =='z'){
     motor.stop(); 
  }

  yield();
}

void identify(){
    Serial.println("identifying");
    analogWrite(LIGHT_PIN, 0);
    Serial.println("set pin");

    delay(250);
    Serial.println("delayed");

    analogWrite(LIGHT_PIN, 0);

    delay(250);
    analogWrite(LIGHT_PIN, 254);

    delay(250);
    analogWrite(LIGHT_PIN, 0);

    delay(250);
    analogWrite(LIGHT_PIN, 254);

    delay(250);
    analogWrite(LIGHT_PIN, 0);

    delay(250);
    analogWrite(LIGHT_PIN, intensity);

}



void calibrate(){
  isCalibrating = true;
  calibrationPhase =0;
}


///////

void sendMaxPos(char motorID, int pos){
    String posMsg = "/maxPos ";
    posMsg+= debugCount;
    //Serial.println(posMsg);
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
  
/// serial stuff ///
void serialEventRun(void) {
  if (Serial.available()) serialEvent();
}

void serialEvent(){
  //get serial
  //Serial.println("/debug received!");
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


