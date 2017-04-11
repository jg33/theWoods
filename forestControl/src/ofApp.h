#pragma once

#include "ofMain.h"
#include "ofxXmlSettings.h"

#include "ofxGui.h"

#include "Light.hpp"
#include "Target.hpp"
#include "OscHandler.hpp"
#include "CvManager.hpp"
#include "Util.h"
#include "EtcLight.hpp"

enum WoodsState{
    WOODS_NORMAL,
    WOODS_IDLE,
    WOODS_QUIET,
    WOODS_NIGHT,
    WOODS_DARK
};

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
    
    WoodsState mode = WOODS_NORMAL;
    
    OscHandler osc;
    CvManager cvMan;
    
    void saveXML();
    void loadXML();
    
    // MORE LIGHTS
    EtcLight quietLight= EtcLight(&osc,0);
    
    // UI
    lightTrackPoint getNearestPoint(int _x, int _y);
    void moveLight(int lightIndex, StartEnd startEnd, ofPoint location);
    bool bIsDragging = false;
    lightTrackPoint nearestPoint;
    ofxPanel lightCtrlPanel;
    ofParameter<float> light0Dist;
    ofParameter<float> light1Dist;
    ofParameter<float> light2Dist;
    ofParameter<float> light3Dist;
    ofParameter<float> light4Dist;
    ofParameter<float> light5Dist;
    ofParameter<float> light6Dist;
    ofParameter<float> light7Dist;

    

};
