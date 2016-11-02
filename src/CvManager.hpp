//
//  CvManager.hpp
//  forestControl
//
//  Created by Jesse Garrison on 11/1/16.
//
//

#ifndef CvManager_hpp
#define CvManager_hpp

#define CAM_WIDTH 640
#define CAM_HEIGHT 480

#include <stdio.h>
#include "ofMain.h"
#include "ofxCv.h"
#include "ofxGui.h"

#include "Util.h"


using namespace ofxCv;
using namespace cv;

class CvManager{
public:
    CvManager(){};
    void setup();
    void update();
    void draw();
    
    bool bDebug;
    
    vector<ofPoint> getCenters();
    vector<labeledBlob> getLabelBlobs();
    vector<unsigned int> getDeadLabels();
    
    ofxPanel gui;

    
private:
    
    ofVideoGrabber grabber;
    ofImage cvImg, thresholded;
    
    RunningBackground background;
    ContourFinder contours;
    
    ofParameter<bool> resetBackground;
    ofParameter<float> learningTime, thresholdValue;
    //
    ofParameter<bool> showLabels;
    ofParameter<float> minBlobSize, maxBlobSize;
    
    ofFbo camFbo;
};


#endif /* CvManager_hpp */
