//
//  OscHandler.cpp
//  forestControl
//
//  Created by Jesse Garrison on 9/22/16.
//
//

#include "OscHandler.hpp"


void OscHandler::setup(){
    oscOut.setup("127.0.0.1", OUTGOING_PORT);
    oscIn.setup(INCOMING_PORT);
    
}

void OscHandler::update(){
    
    //receive
    while(oscIn.hasWaitingMessages()){
        ofxOscMessage m;
        oscIn.getNextMessage(m);
        vector<string> splitAddr = ofSplitString(m.getAddress(), "/");
        if(splitAddr[1]=="light" ){
            int lightNum = ofToInt(splitAddr[2]);
            if(splitAddr[3]=="minTrigger"){
                lights->at(lightNum).hitMin();
            } else if (splitAddr[3]=="maxTrigger"){
                lights->at(lightNum).hitMax();

            }
        }
        
    }
    
    //Ping
    if(timeSincePing >= PING_TIME){
        ofxOscMessage msg;
        msg.setAddress("/ping");
        msg.addIntArg(1);
        oscOut.sendMessage(msg);
        timeSincePing =0;
        ofLogNotice()<<"ping."<<endl;
    } else {
        timeSincePing++;
    }
    
    
    
    
}

void OscHandler::sendFloatMsg(string _addr, float val){
    
    ofxOscMessage msg;
    msg.setAddress(_addr);
    msg.addFloatArg(val);
    oscOut.sendMessage(msg);
    
}