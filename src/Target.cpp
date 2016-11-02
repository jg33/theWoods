//
//  Target.cpp
//  forestControl
//
//  Created by Jesse Garrison on 11/1/16.
//
//

#include "Target.hpp"


void Target::update(){
    current.interpolate(target,0.01);
    
    if(bDying && influence <= 0.){
        label = -1; //unlabel
        bReadyToDie = true;
    } else if(bDying){
        influence -= 0.001;
    }
    
    if(!bDying && influence < 1){
        influence += 0.01;
    }
    
    //ofLogNotice()<<label<<": "<<current<<endl;
    
    
}

void Target::draw(){
    
    ofPushStyle();
    ofPushMatrix();
    ofTranslate(current);
    if(label > -1 && !bDying){
        ofSetColor(0,255,0);
    } else if(bDying && influence>0){
        ofSetColor(0, 0, 255);
    } else {
        ofSetColor(255, 0, 0);
    }
    ofDrawBitmapString(ofToString(label)+": "+ofToString(influence),12,0);
    ofDrawEllipse(0,0,10,10);
    ofPopMatrix();
    ofPopStyle();
        
        
}