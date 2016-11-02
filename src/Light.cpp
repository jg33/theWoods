//
//  Light.cpp
//  forestControl
//
//  Created by Jesse Garrison on 7/26/16.
//
//

#include "Light.hpp"

void Light::react(Target *_target){
    
    float dist = current.distance(_target->current);
    
    if(dist<maxDistance){
        
        trackedPoints.push_back(_target);
  
    }
    
    float nearestDist = current.distance(*nearestPoint);
    
    if(dist<nearestDist){
        nearestPoint = &_target->current;
        nearestDist = current.distance(_target->current);
    }
    

    
    if(current.distance(moveTarget) > 0.1 ){
        bChanged = true;
    } else{
    }

    
}

void Light::update(){
    
    if(trackedPoints.size()>0){
        Target* nearestTarget = trackedPoints[0];
        Target* nearestLivingTarget = trackedPoints[0];
        ofPoint nearestPt = nearestTarget->current;
        float distanceSum =0;
        
        for(int i=0;i<trackedPoints.size();i++){
            
            // Calc Dist
            float dist = current.distance(trackedPoints[i]->current);
            float distInfluence = (maxDistance-dist)/maxDistance;
            
            distInfluence*=trackedPoints[i]->influence;
            
            // Find nearest
            if(dist< current.distance(nearestPt)){
                nearestTarget = trackedPoints[i];
                nearestPt = nearestTarget->current;
                if(!nearestTarget->bDying){
                    nearestLivingTarget = nearestTarget;
                }
            }
            
            
            ofPoint tempTarget = track.getClosestPoint(trackedPoints[i]->current);
            moveTarget.interpolate(tempTarget,distInfluence);
            
            distanceSum += dist;
        }
        
        // Set Intensity based on nearest living target only
    //    float nearDist = current.distance(nearestPt);
   //     targetIntensity = (maxDistance-nearDist)/maxDistance;
        
        float nearDist = current.distance(nearestLivingTarget->current);
        targetIntensity = (maxDistance-nearDist)/maxDistance;
        targetIntensity *= nearestLivingTarget->influence;

        //lerp intensity
        intensity += (targetIntensity-intensity)*0.01;
    
        
        
    } else{
        intensity -= 0.01;
    }
    

    getPercent();
    
    // Move
    current.interpolate(moveTarget,0.01);

    
    if(bChanged){
        report();
        bChanged = false;
    } else {
        //ofLogNotice()<<current.distance(moveTarget)<<endl;
    }
    
    trackedPoints.clear();
}

void Light::draw(){
    
    ofPushStyle();
    
    ofSetColor(255, 0, 0);
    ofDrawEllipse(start, 5, 5);
    ofDrawEllipse(end, 5,5);
    track.draw();
    
    ofSetColor(intensity*255);
    ofDrawEllipse(current,10,10);

    
    ofPopStyle();
    
    
}

void Light::report(){
    
    osc->sendFloatMsg("/"+ofToString(id)+"/intensity", intensity);
    osc->sendFloatMsg("/"+ofToString(id)+"/location", locationPercent);

}

void Light::getPercent(){
    float totalDist = start.distance(end);
    float distFromStart = current.distance(start);
    locationPercent = distFromStart/totalDist;
}

void Light::jumpToStart(){
    current = start;
}

void Light::jumpToEnd(){
    current = end;
}

void Light::hitMin(){
    jumpToStart();
}

void Light::hitMax(){
    jumpToEnd();
}



