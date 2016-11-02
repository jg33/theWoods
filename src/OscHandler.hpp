//
//  OscHandler.hpp
//  forestControl
//
//  Created by Jesse Garrison on 9/22/16.
//
//

#ifndef OscHandler_hpp
#define OscHandler_hpp

#define INCOMING_PORT 8888
#define OUTGOING_PORT 9999
#define PING_TIME 1000

#include <stdio.h>
#include <ofMain.h>
#include "ofxOsc.h"
#include "Light.hpp"

class OscHandler{
    
public:
    OscHandler(){
        
    };
    void setup();
    void update();
    
    void sendFloatMsg(string _addr, float val);
    
    void setLightVector(vector<Light>* _lights){
        lights = _lights;
    };
    
private:
    
    ofxOscSender oscOut;
    ofxOscReceiver oscIn;
    
    int timeSincePing =0;
    vector<Light> * lights;
    
};

#endif /* OscHandler_hpp */
