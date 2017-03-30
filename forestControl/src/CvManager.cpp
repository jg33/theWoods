//
//  CvManager.cpp
//  forestControl
//
//  Created by Jesse Garrison on 11/1/16.
//
//

#include "CvManager.hpp"

void CvManager::setup(){
    grabber.setGrabber(std::make_shared<ofxPS3EyeGrabber>());
    grabber.setup(CAM_WIDTH,CAM_HEIGHT);
    //grabber.setDesiredFrameRate(60);
    grabber.getGrabber<ofxPS3EyeGrabber>()->setAutogain(false);
    grabber.getGrabber<ofxPS3EyeGrabber>()->setGain(2550);

    camFbo.allocate(CAM_WIDTH, CAM_HEIGHT);
    
    // Contour Tracker
    contours.setMinAreaRadius(1);
    contours.setMaxAreaRadius(100);
    contours.setThreshold(15);
    // wait for half a frame before forgetting something
    contours.getTracker().setPersistence(1000);
    // an object can move up to 32 pixels per frame
    contours.getTracker().setMaximumDistance(100);
    
    // GUI
    gui.setup();
    gui.add(resetBackground.set("Reset Background", false));
    gui.add(learningTime.set("Learning Time", 30, -1, 600));
    gui.add(thresholdValue.set("BG Threshold Value", 10, 0, 255));
    gui.add(showLabels.set("Show Blob Labels", true));
    gui.add(minBlobSize.set("Min Blob Size", 10, 0, 5000));
    gui.add(maxBlobSize.set("Max Blob Size", 100, 0, 50000));

    
}

void CvManager::update(){
    
    grabber.update();
    
    if(resetBackground) {
        background.reset();
        resetBackground = false;
    }
    if(grabber.isFrameNew()) {
        //background.setLearningTime(learningTime);
        
        //ignore flickers?
        
        background.setThresholdValue(thresholdValue);
        background.update(grabber, thresholded);
        thresholded.update();
        dilate(thresholded,5);
        blur(thresholded,10);
        contours.findContours(thresholded);
    }
    contours.setMinArea(minBlobSize);
    contours.setMaxArea(maxBlobSize);
    
    
    // idle logic
    if(contours.getContours().size()>0){
        idleTimer=0;
        if(bIsIdle) {
            osc->sendIntMsg("/idle",0);
            ofLogNotice()<<"no longer idle!"<<endl;
        }
        
        bIsIdle = false;
        
    } else if(idleTimer>IDLE_TIMEOUT && !bIsIdle){
        bIsIdle = true;
        ofLogNotice()<<"Going Idle"<<endl;
        osc->sendIntMsg("/idle",1);
    } else if (!bIsIdle){
        idleTimer++;
        
    } else{
    }

    
}

void CvManager::draw(){
    
    camFbo.begin();
    if(bDebug){
        grabber.draw(0,0,ofGetWidth(),ofGetHeight());
        
    }
    if(thresholded.isAllocated()) {
        ofSetColor(255);
        thresholded.draw(0, 0);//,ofGetWidth(),ofGetHeight());
    }
    
   // ofPushMatrix();
 //   ofScale(ofGetWidth()/CAM_WIDTH, ofGetHeight()/CAM_HEIGHT);
    ofSetColor(255,0,0);
    contours.draw();
   // ofPopMatrix();
    
    //ofSetBackgroundAuto(showLabels);
    RectTracker& tracker = contours.getTracker();
    
    //movie.draw(0, 0);
    //contours.draw();
    for(int i = 0; i < contours.size(); i++) {
        ofPoint center = toOf(contours.getCenter(i));
        ofPushMatrix();
        ofTranslate(center.x, center.y);
        int label = contours.getLabel(i);
        string msg = ofToString(label) + ":" + ofToString(tracker.getAge(label));
        ofDrawBitmapString(msg, 0, 0);
        //ofVec2f velocity = toOf(contours.getVelocity(i));
        ofScale(5, 5);
        //ofDrawLine(0, 0, velocity.x, velocity.y);
        ofPopMatrix();

    }
    camFbo.end();
    camFbo.draw(0, 0, ofGetWidth(), ofGetHeight());
    
    gui.draw();
    
}


vector<ofPoint> CvManager::getCenters(){
    vector<ofPoint> _centers;
    for(int i=0;i<contours.size();i++){
        ofPoint thisCenter = toOf(contours.getCenter(i));
        thisCenter.x = ofMap(thisCenter.x, 0, CAM_WIDTH, 0, ofGetWidth());
        thisCenter.y = ofMap(thisCenter.y, 0, CAM_HEIGHT, 0, ofGetHeight());
        //if(contours.getTracker().getAge(contours.getLabel(i))>60);
        _centers.push_back( thisCenter);
    }
    return _centers;
    
    
}

vector<labeledBlob> CvManager::getLabelBlobs(){
    vector<labeledBlob> _blobs;
    for(int i=0;i<contours.size();i++){
        labeledBlob thisBlob;
        thisBlob.center = toOf(contours.getCenter(i));
        thisBlob.center.x = ofMap(thisBlob.center.x, 0, CAM_WIDTH, 0, ofGetWidth());
        thisBlob.center.y = ofMap(thisBlob.center.y, 0, CAM_HEIGHT, 0, ofGetHeight());
        thisBlob.label = contours.getTracker().getLabelFromIndex(i);
        thisBlob.age = contours.getTracker().getAge(thisBlob.label);
        //if(contours.getTracker().getAge(contours.getLabel(i))>60);
        _blobs.push_back( thisBlob);
    }
    return _blobs;
    
    
}

vector<unsigned int> CvManager::getDeadLabels(){
    return contours.getTracker().getDeadLabels();
    
}
