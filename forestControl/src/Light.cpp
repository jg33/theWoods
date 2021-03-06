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
    



    
}

void Light::update(){
    
    switch(currentMode){
            
        case NORMAL: // if not idle!
                
                if(trackedPoints.size()>0){
                    Target* nearestTarget = trackedPoints[0];
                    Target* nearestLivingTarget = trackedPoints[0];
                    ofPoint nearestPt = nearestTarget->current;
                    float distanceSum =0;
                    
                    for(int i=0;i<trackedPoints.size();i++){
                        
                        // Calc Dist
                        float dist = current.distance(trackedPoints[i]->current);
                        float distInfluence = (maxDistance-dist)/maxDistance;
                        distInfluence = ofClamp(distInfluence, 0., 1.);
                        if (distInfluence < 0.1) distInfluence = 0;
                        
                        distInfluence*=trackedPoints[i]->influence;
                        //ofLogNotice()<<trackedPoints[i]->influence<<endl;
                        
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
                    
                    
                } else if (intensity>0){
                    intensity -= 0.01;
                }
                
                
                // Move
                current.interpolate(moveTarget,0.001);
                getPercent();
                newStepperPosition = floor(ofMap(locationPercent, 0, 1, 0, STEPS_PER_TRACK));
                
                trackedPoints.clear();
                ofLogNotice()<<"normal"<<endl;
            break;
        case IDLE: //if idle!
            ofLogNotice()<<"idle"<<endl;

                if(bIsIdleHighlight){
                    
                    if(ofGetElapsedTimef()>endHighlightTime) bIsIdleHighlight= false;
                    targetIntensity = ofNoise(ofGetElapsedTimef()+(id*6.66))*ofNoise(ofGetElapsedTimef()+(id*6.66));
                    targetIntensity*=0.5;
                    //if(ofRandomf()>.5){ bIsIdleHighlight = false; }
                    
                } else {
                    targetIntensity = 0.005;
                    //if(ofRandomf()>.999){ bIsIdleHighlight = true; }
                }
                //lerp intensity
                intensity += (targetIntensity-intensity)*0.01;
            break;
            
        case QUIET:
            //targetIntensity = 0.005;
            if(ofGetElapsedTimef()>endHighlightTime) bIsIdleHighlight= false;
            targetIntensity = ofNoise(ofGetElapsedTimef()+(id*6.66))*ofNoise(ofGetElapsedTimef()+(id*6.66));
            targetIntensity*=0.5;
            
            
            //lerp intensity
            intensity += (targetIntensity-intensity)*0.01;
            ofLogNotice()<<"quiet."<<endl;
            break;
            
        default:
            break;

            
    }
    
    
    
    // report if changed
    if(current.distance(moveTarget) > 0.1 || intensity > 0.001){
        bChanged = true;
    } else{
    }
    
    if(bChanged){
        report();
        bChanged = false;
    } else {
        //ofLogNotice()<<current.distance(moveTarget)<<endl;
    }
    
    //ofLogNotice()<<"updated "<<ofToString(id)<<endl;
}

void Light::draw(){
    
    ofPushStyle();
    
    //range
    ofSetColor(130, 130, 0,100);
    ofDrawCircle(current, maxDistance);
    
    
    //track
    ofSetColor(255, 0, 0);
    ofDrawEllipse(start, 5, 5);
    ofDrawEllipse(end, 5,5);
    track.draw();
    ofDrawBitmapString(ofToString(id), start.x+10, start.y);
    ofDrawBitmapString(ofToString(moveTarget), start.x+10, start.y+10);

    
    //light
    ofSetColor(255,255,0);
    ofDrawEllipse(current,11,11);
    ofSetColor(intensity*255);
    ofDrawEllipse(current,10,10);

    ofPopStyle();
    
    
}

void Light::report(){
    
    osc->sendFloatMsg("/light/"+ofToString(id)+"/intensity", intensity);
    osc->sendFloatMsg("/light/"+ofToString(id)+"/position", locationPercent);
    
//    if(newStepperPosition>previousStepperPosition){
//        osc->sendIntMsg("/light/"+ofToString(id)+"/stepUp", locationPercent);
//        previousStepperPosition = newStepperPosition;
//
//    } else if(newStepperPosition<previousStepperPosition){
//        osc->sendIntMsg("/light/"+ofToString(id)+"/stepDown", locationPercent);
//        previousStepperPosition = newStepperPosition;
//
//    }

}

void Light::getPercent(){
    float totalDist = start.distance(end);
    float distFromStart = current.distance(start);
    locationPercent = distFromStart/totalDist;
}

void Light::jumpToStart(){
    current = start;
    newStepperPosition = 0;
    previousStepperPosition = newStepperPosition;
}

void Light::jumpToEnd(){
    current = end;
    newStepperPosition = STEPS_PER_TRACK;
    previousStepperPosition = newStepperPosition;
}

void Light::hitMin(){
    jumpToStart();
}

void Light::hitMax(){
    jumpToEnd();
}



