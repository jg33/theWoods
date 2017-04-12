//
//  Target.cpp
//  forestControl
//
//  Created by Jesse Garrison on 11/1/16.
//
//

#include "Target.hpp"


void Target::update(){
    previous = current;
    current.interpolate(target,0.05);
    
    if(bDying && influence <= 0.){
        label = -1; //unlabel
        bReadyToDie = true;
    } else if(bDying){
        influence -= 0.001;
    }
    
    if(!bDying && influence < 1){
        influence += 0.01;
    }
    
    influence = ofClamp(influence, 0, 1.);
    
    
    
    if(quietTimer>quietTimeThreshold){
        bIsQuiet = true;
        
    } else if(previous.distance(current)>quietMoveThreshold  && !bDying){
        //if there's movement above the threshold, reset timer
        quietTimer=0;
        bIsQuiet = false;
    } else{
        quietTimer++;
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
    ofDrawBitmapString(ofToString(label)+": "+ofToString(influence,3),12,0);
    ofDrawEllipse(0,0,10,10);
    ofPopMatrix();
    ofPopStyle();
        
        
}
