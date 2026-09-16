/*---------------------------------------------------------------------------------------------

  The Woods — light node firmware (ESP8266, OSC command interface)

  Based on the CNMAT OSC example for ESP8266. Receives OSC commands from the
  TouchDesigner `network` COMP over UDP and drives the stepper + LED.

  Address map (must match td/theWoods spec — docs/superpowers/specs/2026-09-15-td-port-design.md):
    TD→node   /light/<n>/position   <float 0-1>   move to arg * maxSteps
              /light/<n>/intensity  <float 0-1>   targetIntensity = arg * 255
              /light/<n>/identify                 flash light
              /light/<n>/calibrate                begin calibration (flag only, as before)
              /light/<n>/zero                     setCurrentPosition(0)
              /light/<n>/stop                     motor.stop()
              /light/<n>/move       <int steps>   relative move
              /ping                 <int>         heartbeat (ignored; one-way liveness)
    node→TD   /light/<n>/minTrigger               min limit hit
              /light/<n>/maxTrigger               max limit hit
              /light/<n>/maxPos     <int>         reported max position

  Status reports go to the last command sender (TD's oscIn listen port);
  before any command arrives, they broadcast to TD's default listen port.

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
// TD `network` COMP unicasts commands to each node on Nodeport (9999) — listen there.
// Status reports go to the last sender's IP:port (TD oscIn Listenport, default 8899).
const unsigned int localPort = 9999;
// Fallback destination for reports before any TD command has been received:
const IPAddress defaultReportIp(255, 255, 255, 255);   // broadcast
const unsigned int defaultReportPort = 8899;           // TD oscIn Listenport

// Update these with values suitable for your network.
IPAddress ip(192,168,0,103);  //Node static IP
IPAddress gateway(192,168,0,1);
IPAddress subnet(255,255,255,0);

// This node's light index in the TD map (/light/<n>/...). Set per-node
// (ip 192.168.0.10x → NODE_ID x-100, matching tracks.tsv default IPs).
#define NODE_ID 3

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

bool isCalibrating = false;
int calibrationPhase = 0;

int debugCount = 0;
AccelStepper motor(8,MOTOR_PIN_1, MOTOR_PIN_3,MOTOR_PIN_2,MOTOR_PIN_4) ;

// Last command sender (for status replies). Defaults to broadcast until
// the first command packet arrives.
IPAddress replyIp = defaultReportIp;
unsigned int replyPort = defaultReportPort;

// Dispatch address buffers, built once in setup() from NODE_ID.
char addrPosition[32];
char addrIntensity[32];
char addrIdentify[32];
char addrCalibrate[32];
char addrZero[32];
char addrStop[32];
char addrMove[32];


void setup() {
  pinMode(BUILTIN_LED, OUTPUT);

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

  // OSC dispatch addresses for this node
  snprintf(addrPosition,  sizeof(addrPosition),  "/light/%d/position",  NODE_ID);
  snprintf(addrIntensity, sizeof(addrIntensity), "/light/%d/intensity", NODE_ID);
  snprintf(addrIdentify,  sizeof(addrIdentify),  "/light/%d/identify",  NODE_ID);
  snprintf(addrCalibrate, sizeof(addrCalibrate), "/light/%d/calibrate", NODE_ID);
  snprintf(addrZero,      sizeof(addrZero),      "/light/%d/zero",      NODE_ID);
  snprintf(addrStop,      sizeof(addrStop),      "/light/%d/stop",      NODE_ID);
  snprintf(addrMove,      sizeof(addrMove),      "/light/%d/move",      NODE_ID);
}


void loop() {

  // handle OSC //
  int size = Udp.parsePacket();
  if (size > 0) {
    // Status replies: keep the sender's IP but always target TD's oscIn listen
    // port — the OSC Out DAT's source port is ephemeral, not the listen port.
    replyIp = Udp.remoteIP();
    replyPort = defaultReportPort;

    OSCBundle bundle;
    while (size--) {
      bundle.fill(Udp.read());
    }
    if (!bundle.hasError()) {
      bundle.dispatch(addrPosition,  onPosition);
      bundle.dispatch(addrIntensity, onIntensity);
      bundle.dispatch(addrIdentify,  onIdentify);
      bundle.dispatch(addrCalibrate, onCalibrate);
      bundle.dispatch(addrZero,      onZero);
      bundle.dispatch(addrStop,      onStop);
      bundle.dispatch(addrMove,      onMove);
      // /ping is a one-way liveness heartbeat from TD — nothing to do.
    } else {
      OSCErrorCode error = bundle.getError();
      Serial.print("osc error: ");
      Serial.println(error);
    }
    bundle.empty();
  }

  //check min / max status
  getMinMaxStatus();

  //run motor a
  long toGo = motor.distanceToGo();
  bool movingTowardMin = (toGo < 0);
  bool movingTowardMax = (toGo > 0);

  if (atMin && movingTowardMin) {
     motor.stop();
     motor.setCurrentPosition(0);
     sendStatus("minTrigger", 1);
  } else if (atMax && movingTowardMax) {
     motor.stop();
     maxSteps = motor.currentPosition();
     sendStatus("maxTrigger", 1);
     sendStatus("maxPos", maxSteps);
  } else {
     motor.run();
  }

  //interpolate intensity
  if (intensity < targetIntensity) intensity++;
  else if (intensity > targetIntensity) intensity--;

  //set brightness of light a
  analogWrite(LIGHT_PIN, intensity);

  //yield();

}


/////
// OSC command handlers (dispatched by address; the <n> in the address must
// match this node's NODE_ID or the dispatch never fires).

void onPosition(OSCMessage &msg){
  // /light/<n>/position <float 0-1> — same semantics as text 'p<n>': absolute
  // move in steps, but scaled by the calibrated maxSteps.
  float f = msg.getFloat(0);
  long val = (long)(f * (float)maxSteps);
  motor.moveTo(val);
}

void onIntensity(OSCMessage &msg){
  // /light/<n>/intensity <float 0-1> — text 'i<n>' took raw PWM 0-255;
  // OSC carries the normalized float TD speaks.
  float f = msg.getFloat(0);
  targetIntensity = (int)constrain(f * 255.0f, 0.0f, 255.0f);
}

void onIdentify(OSCMessage &msg){
  identify();
}

void onCalibrate(OSCMessage &msg){
  calibrate();
}

void onZero(OSCMessage &msg){
  // text 'r'
  motor.setCurrentPosition(0);
}

void onStop(OSCMessage &msg){
  // text 'z'
  motor.stop();
}

void onMove(OSCMessage &msg){
  // text '-n' / '=n' — signed relative move
  long val = msg.getInt(0);
  motor.move(val);
}

void identify(){
    Serial.println("identifying");
    analogWrite(LIGHT_PIN, 0);

    delay(250);
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

void sendStatus(const char* status, int value){
  // /light/<n>/<status> <int> to the last command sender (or broadcast).
  OSCMessage msg;
  char addr[40];
  snprintf(addr, sizeof(addr), "/light/%d/%s", NODE_ID, status);
  msg.setAddress(addr);
  msg.add(value);
  Udp.beginPacket(replyIp, replyPort);
  msg.send(Udp);
  Udp.endPacket();
  msg.empty();
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