////////////////
////  OLD  /////
////////////////
String splitAddress(String data, char separator, int index){
    int found = 0;
    int strIndex[] = { 0, -1 };
    int maxIndex = data.length() - 1;

    for (int i = 0; i <= maxIndex && found <= index; i++) {
        if (data.charAt(i) == separator || i == maxIndex) {
            found++;
            strIndex[0] = strIndex[1] + 1;
            strIndex[1] = (i == maxIndex) ? i+1 : i;
        }
    }
    return found > index ? data.substring(strIndex[0], strIndex[1]) : "";
}

void processOSC(String msg){
  
  String prefix = splitAddress(msg,'/',0);
  char light = splitAddress(msg,'/',1).charAt(0);
  String cmd = splitAddress(msg,'/',2);
  int val = splitAddress(msg, ' ',1).toInt();
  String output = "/debug prefix: "+prefix;
  output += " light: ";
  output += light;

  Serial.println(output);
  if(prefix == "calibrate"){
    if (val==1){
      calibrate();
    } else if (val ==0){
      isCalibrating = false;
      calibrationPhase = 0;
    }
  } else if (prefix=="light"){
    
    if(light == 'a'){
      if(cmd=="intensity"){
        lightAintensity= val;
      } else if (cmd=="motorPosition"){
       // motorA.moveTo(val);
      }
    } else if (light=='b'){
      if(cmd=="intensity"){
        lightBintensity= val;
      } else if (cmd=="motorPosition"){
       // motorB.moveTo(val);
      }
    }
  }
  
}
