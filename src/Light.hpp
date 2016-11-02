//
//  Light.hpp
//  forestControl
//
//  Created by Jesse Garrison on 7/26/16.
//
//

#ifndef Light_hpp
#define Light_hpp

#define MAX_DISTANCE 300
#define STEPS_PER_TRACK 300

#include <stdio.h>
#include "ofMain.h"
#include "OscHandler.hpp"
#include "Target.hpp"

class Light{
    
    
public:
    Light(){};
    Light(int _id, ofPoint _start, ofPoint _end):id(_id), start(_start), end(_end){
        track.addVertex(start);
        track.addVertex(end);
        

        moveTarget = track.getPointAtPercent(0.5);
        current = moveTarget;
        
        nearestPoint = &blankPoint;
    };
    void draw();
    void update();
    
    void react(Target *_target);
    
    int id;
    
    ofPoint start, end, current, moveTarget;
    ofPolyline track = ofPolyline();
    
    float intensity, targetIntensity;
    float maxDistance = MAX_DISTANCE;
    
    void setOscPtr(OscHandler *_osc){
        osc = _osc;
    }
    
    void setPoints(ofPoint _start, ofPoint _end){
        start = _start;
        end = _end;
        updateTrack();

    }
    
    void updateTrack(){
        track.clear();
        track.addVertex(start);
        track.addVertex(end);
    }
    
    void hitMin();
    void hitMax();
    
private:
    
    void jumpToStart();
    void jumpToEnd();
    
    ofPoint *nearestPoint;
    ofPoint blankPoint = ofPoint();
    float locationPercent = 0;
    
    OscHandler *osc;
    
    void report();
    void getPercent();
    
    bool bAtMin, bAtMax;
    bool bChanged;
    bool bIsIdle;
    
    vector<Target*> trackedPoints;
    
};
#endif /* Light_hpp */
