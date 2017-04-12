//
//  DmxLight.cpp
//  forestControl
//
//  Created by Jesse Garrison on 4/1/17.
//
//

#include "EtcLight.hpp"

void EtcLight::update(){
    intensity += (targetIntensity-intensity)*0.007;
    
    if(intensity!=lastIntensity){
        report();
        ofLogNotice()<< "quietlight"<<endl;
    }
    lastIntensity = intensity;
}

void EtcLight::draw(){
    ofPushMatrix();
    ofPushStyle();
    ofTranslate(ofGetWidth()-20, 12+(20*id));
    ofSetColor(0,0,255);
    ofDrawCircle(0,0,11);
    ofSetColor(intensity*255);
    ofDrawCircle(0,0,10);
    ofPopStyle();
    ofPopMatrix();
}

void EtcLight::report(){
    
    osc->sendFloatMsg("/etcLight/"+ofToString(id), intensity);
}
