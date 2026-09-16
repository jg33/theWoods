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


char ssid[] = "The Woods";          // your network SSID (name)
char pass[] = "d33pd4rk";                    // your network password

// A UDP instance to let us send and receive packets over UDP
WiFiUDP Udp;
// TD network COMP: sendcook unicasts commands to each node on Nodeport (9999),
// so we listen here; we report status back to TD's oscIn Listenport (8899).
const IPAddress outIp(255,255,255,255);        // broadcast: TD oscIn receives on any host
const unsigned int outPort = 8899;          // TD oscIn Listenport (our reports go here)
const unsigned int localPort = 9999;        // TD Nodeport (TD->node commands arrive here)

// Update these with values suitable for your network.
IPAddress ip(192,168,0,103);  //Node static IP
IPAddress gateway(192,168,0,1);
IPAddress subnet(255,255,255,0);

// This node's light index in the TD map (/light/<n>/...). Set per-node.
#define NODE_ID 3

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

int intensity = 0;
int targetIntensity = 0;

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
  OSCMessage msg;
  int size = Udp.parsePacket();

  if (size > 0) {
    while (size--) {
      msg.fill(Udp.read());
    }
    if (!msg.hasError()) {
      routeOSC(msg);
    } else {
      Serial.print("OSC error");
    }
    msg.empty();
  }

  //deal with serial, if not calibrating
//  if(inputStringComplete && !isCalibrating){
//    parseCommand(serialInput);
//    serialInput="";
//    inputStringComplete=false;
//  }
  
  //check min / max status
  getMinMaxStatus();

  //run motor a
  long toGo = motor.distanceToGo();
  bool movingTowardMin = (toGo < 0);
  bool movingTowardMax = (toGo > 0);

  if (atMin && movingTowardMin) {
     motor.stop();
     motor.setCurrentPosition(0);
     sendTrigger("minTrigger");
  } else if (atMax && movingTowardMax) {
     motor.stop();
     maxSteps = motor.currentPosition();
     sendMaxPos(maxSteps);
  } else {
     motor.run();
  }
  
  //interpolate intensity
  if (intensity < targetIntensity) intensity++;
  else if (intensity > targetIntensity) intensity--;
  //Serial.println((String)intensity + " "+ (String)targetIntensity);

  //set brightness of light a
  analogWrite(LIGHT_PIN, intensity);

  //debugging;
  //String debugMsg = "/debug/this ";
  //debugMsg += debugCount;
 // //Serial.println(debugMsg);
 // debugCount++;
 
  //yield();

}



/////
void routeOSC(OSCMessage &msg){
  char addrBuff[128];
  msg.getAddress(addrBuff);
  String addr = String(addrBuff);
  String prefix = "/light/";
  prefix += String(NODE_ID);
  prefix += "/";
  String cmd = addr.substring(prefix.length());

  // TD sends /light/<n>/position <float 0-1> ; stepper move to arg * maxPos
  if (cmd.equals("position")) {
     float val = msg.getFloat(0);
     motor.moveTo((long)(val * maxSteps));
  } else if (cmd.equals("intensity")) {
     // float 0-1 -> LED PWM 0-255
     float val = msg.getFloat(0);
     targetIntensity = (int)constrain(val * 255.0, 0, 255);
  } else if (cmd.equals("identify")) {
     identify();
  } else if (cmd.equals("move")) {
     long val = msg.getInt(0);
     motor.move(val);
  } else if (cmd.equals("calibrate")) {
     calibrate();
  } else if (cmd.equals("zero")) {
     motor.setCurrentPosition(0);
  } else if (cmd.equals("stop")) {
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

void sendMaxPos(int pos){
    OSCMessage msg;
    char addr[64];
    snprintf(addr, sizeof(addr), "/light/%d/maxPos", NODE_ID);
    msg.setAddress(addr);
    msg.add(pos);
    Udp.beginPacket(outIp, outPort);
    msg.send(Udp);
    Udp.endPacket();
}

// Report a limit-switch hit ("minTrigger"/"maxTrigger") back to TD.
void sendTrigger(const char* which){
    OSCMessage msg;
    char addr[64];
    snprintf(addr, sizeof(addr), "/light/%d/%s", NODE_ID, which);
    msg.setAddress(addr);
    msg.add(1);
    Udp.beginPacket(outIp, outPort);
    msg.send(Udp);
    Udp.endPacket();
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


