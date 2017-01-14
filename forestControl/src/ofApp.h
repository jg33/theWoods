#pragma once

#include "ofMain.h"
#include "ofxXmlSettings.h"

#include "Light.hpp"
#include "Target.hpp"
#include "OscHandler.hpp"
#include "CvManager.hpp"
#include "Util.h"

class ofApp : public ofBaseApp{

	public:
		void setup();
		void update();
		void draw();

		void keyPressed(int key);
		void keyReleased(int key);
		void mouseMoved(int x, int y );
		void mouseDragged(int x, int y, int button);
		void mousePressed(int x, int y, int button);
		void mouseReleased(int x, int y, int button);
		void mouseEntered(int x, int y);
		void mouseExited(int x, int y);
		void windowResized(int w, int h);
		void dragEvent(ofDragInfo dragInfo);
		void gotMessage(ofMessage msg);
		
    
private:
    int selectedTarget=0;
    vector<Target> targets;
    
    //Light light0;
    
    vector<Light> lights;
    
    OscHandler osc;
    CvManager cvMan;
    
    void saveXML();
    void loadXML();
    
    // UI
    lightTrackPoint getNearestPoint(int _x, int _y);
    void moveLight(int lightIndex, StartEnd startEnd, ofPoint location);
    bool bIsDragging = false;
    lightTrackPoint nearestPoint;
    
};
