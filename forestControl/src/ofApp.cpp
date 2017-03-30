#include "ofApp.h"

//--------------------------------------------------------------
void ofApp::setup(){
    ofBackground(0);
    ofSetBackgroundAuto(true);
    
    ofSetFrameRate(30);
    
    // Load XML
    loadXML();
    
    // Osc setup
    osc.setup();
    
    // CV Setup
    cvMan.setup();
    cvMan.gui.loadFromFile("settings.xml");
    cvMan.setOscHandler(&osc);

    
    // GUI Setup
    lightCtrlPanel.setup();
    lightCtrlPanel.setPosition(10, 200);
    lightCtrlPanel.add(light0Dist.set("Light 0 Max Distance", 300,100, 1000));
    lightCtrlPanel.add(light1Dist.set("Light 1 Max Distance", 300,100, 1000));
    lightCtrlPanel.add(light2Dist.set("Light 2 Max Distance", 300,100, 1000));
    lightCtrlPanel.add(light3Dist.set("Light 3 Max Distance", 300,100, 1000));

    
    //setup lights//
    lights.push_back(Light(0,ofPoint(50,50),ofPoint(150,100)));
    
    for(int i=0;i<NUM_LIGHTS-1;i++){
        ofPoint randoPoint = ofPoint(ofRandom(200,ofGetWidth()-200), ofRandom(200,ofGetHeight()-200) );
        
        lights.push_back(Light(i+1,ofPoint(randoPoint.x-ofRandom(75),randoPoint.y-ofRandom(75)),ofPoint(randoPoint.x+ofRandom(75),randoPoint.y+ofRandom(75))));
        
    }
    for(int i=0;i<lights.size();i++){
        lights[i].setOscPtr(&osc);
    }
    
    for(int i=0;i<NUM_TARGETS;i++){
        targets.push_back(ofPoint(0,0));
        
    }
    
    
    //special
    
    
    

}

//--------------------------------------------------------------
void ofApp::update(){
    //osc
    osc.update();
    
    
    //cv
    cvMan.update();
    
    //gui
    if (light0Dist != lights[0].maxDistance){
        lights[0].maxDistance = light0Dist;
    }
    if (light1Dist != lights[1].maxDistance){
        lights[1].maxDistance = light1Dist;
    }
    if (light2Dist != lights[2].maxDistance){
        lights[2].maxDistance = light2Dist;
    }
    if (light3Dist != lights[3].maxDistance){
        lights[3].maxDistance = light3Dist;
    }

    // UPDATE TARGETS
    
    //kill old blobs
    vector<unsigned int> deadLabels = cvMan.getDeadLabels();
    for(int i=0;i<deadLabels.size();i++){
        for(int j=0;j<targets.size();j++){
            if(targets[j].label==deadLabels[i]){
                targets[j].bDying=true;
                
            }
        }

    }
    
    //get new blobs
    vector<labeledBlob> newPoints = cvMan.getLabelBlobs();
    
    for(int i=0;i<newPoints.size();i++){
        for(int j=0;j<targets.size();j++){
            if(targets[j].label == -1){  // if unassigned
                bool _bIsTracked = false;
                for(int k=0;k<targets.size();k++){ //does anything have this label?
                    if(targets[k].label == newPoints[i].label) _bIsTracked= true;
                    
                }
                
                if(!_bIsTracked){ //only set if it isn't already being tracked
                    targets[j]= Target(newPoints[i].center); //POTENTIAL MEM LEAK?
                    targets[j].label = newPoints[i].label;
                }
            }
            if(newPoints[i].label == targets[j].label){
                targets[j].target = newPoints[i].center;
                targets[j].bDying=false;
            }
        }
        
    }
    
    //check idle status
    if(cvMan.bIsIdle){
        bool bIsOneOn = false;;
        
        for(int i=0;i<lights.size();i++){
            lights[i].bIsIdle = true;
            if(lights[i].bIsIdleHighlight) bIsOneOn = true;
        }
        
        // make sure one is always on
        if (!bIsOneOn){
            int randoLightNum =floor(ofRandom(0,7));
            lights[randoLightNum].bIsIdleHighlight= true;
            lights[randoLightNum].endHighlightTime = ofGetElapsedTimef()+ ofRandom(10);
            
        }
        
    } else {
        for(int i=0;i<lights.size();i++){
            lights[i].bIsIdle = false;
        }
        
    }
    
    
    
    //update all targets
    for(int i=0;i<targets.size();i++){
        targets[i].update();
        
    }
    
    // UPDATE LIGHTS
    for(int i=0;i<lights.size();i++){
        for(int j=0;j<targets.size();j++){
            lights[i].react(&targets[j]);

        }
        
    }
    
    
    for(int i=0;i<lights.size();i++){
        lights[i].update();
        
    }
    

}

//--------------------------------------------------------------
void ofApp::draw(){
    
    //cv
    cvMan.draw();
    
    //targets
    for(int i=0;i<targets.size();i++){
        targets[i].draw();
        
    }
    
    //lights
    for(int i=0;i<lights.size();i++){
        lights[i].draw();
        
    }
    
    lightCtrlPanel.draw();
}

//--------------------------------------------------------------
void ofApp::keyPressed(int key){
    switch(key){
        case '1':
            selectedTarget=0;
            break;
        case '2':
            selectedTarget=1;
            break;
        case '3':
            selectedTarget=2;
            break;
        case '4':
            selectedTarget=3;
            break;
        case 't':
            targets.clear();
            break;
            
        case 's':
            saveXML();
            break;
            
            case 'l':
            loadXML();
            break;
            
        default:
            break;
            
    }

}

//--------------------------------------------------------------
void ofApp::keyReleased(int key){

}

//--------------------------------------------------------------
void ofApp::mouseMoved(int x, int y ){

}

//--------------------------------------------------------------
void ofApp::mouseDragged(int x, int y, int button){
    
    //targets[selectedTarget] = ofPoint(x,y);
    if(!bIsDragging)  {
        nearestPoint = getNearestPoint(x,y);
        bIsDragging = true;
    }
    
    if(nearestPoint.lightIndex>-1) moveLight(nearestPoint.lightIndex, nearestPoint.startEnd, ofPoint(x,y));
    

}

//--------------------------------------------------------------
void ofApp::mousePressed(int x, int y, int button){
    
    //targets[selectedTarget] = ofPoint(x,y);
    //bIsDragging= true;

}

//--------------------------------------------------------------
void ofApp::mouseReleased(int x, int y, int button){
    bIsDragging = false;
}

//--------------------------------------------------------------
void ofApp::mouseEntered(int x, int y){

}

//--------------------------------------------------------------
void ofApp::mouseExited(int x, int y){

}

//--------------------------------------------------------------
void ofApp::windowResized(int w, int h){

}

//--------------------------------------------------------------
void ofApp::gotMessage(ofMessage msg){
    vector<string> splitMsg = ofSplitString(msg.message, "/");
    if(splitMsg[2]=="hitMin") lights[ofToInt(splitMsg[1])].hitMin();
    if(splitMsg[2]=="hitMax") lights[ofToInt(splitMsg[1])].hitMax();
    ofLogNotice()<<"Message! "<<msg.message<<endl;

}

//--------------------------------------------------------------
void ofApp::dragEvent(ofDragInfo dragInfo){ 

}

///////////

void ofApp::saveXML(){
    
    ofxXmlSettings xml;
    for(int i=0;i<lights.size();i++){
    
        xml.setValue("lights:light_"+ofToString(i)+":"+"start"+":x", lights[i].start.x);
        xml.setValue("lights:light_"+ofToString(i)+":"+"start"+":y", lights[i].start.y);
        xml.setValue("lights:light_"+ofToString(i)+":"+"end"+":x", lights[i].end.x);
        xml.setValue("lights:light_"+ofToString(i)+":"+"end"+":y", lights[i].end.y);
        //ofLogNotice()<< ofToString(i)<<endl;

    }
    
    if(xml.saveFile("lightSettings.xml")){
        ofLogNotice("SAVE OK!");
    } else{
        ofLogError("SAVE FAILED!");
    };
    
    
}

void ofApp::loadXML(){
    
    ofxXmlSettings xml;

    if(xml.loadFile("lightSettings.xml")){
    
        String rawXml;
        xml.copyXmlToString(rawXml);
        ofLogNotice()<<rawXml<<endl;
        
        for(int i=0;i<lights.size();i++){
            ofPoint _start, _end;
            _start.x = xml.getValue("lights:light_"+ofToString(i)+":"+"start"+":x", -1.0);
            _start.y = xml.getValue("lights:light_"+ofToString(i)+":"+"start"+":y", -1.0);
            _end.x = xml.getValue("lights:light_"+ofToString(i)+":"+"end"+":x", -1.0);
            _end.y = xml.getValue("lights:light_"+ofToString(i)+":"+"end"+":y", -1.0);
            
            //ofLogNotice()<< "light:light_"+ofToString(i)+":"+"start"+":x= "<<_start.x<<endl;
            lights[i].setPoints(_start, _end);
            lights[i].current = _start;
            lights[i].moveTarget = _start;

            
        }
    } else{
        ofLogError("failed to load XML.");
        String rawXml;
        xml.copyXmlToString(rawXml);
        ofLogNotice()<<rawXml<<endl;
    }
    
}


lightTrackPoint ofApp::getNearestPoint(int _x, int _y){
    ofPoint clicked = ofPoint(_x,_y);
    lightTrackPoint _nearest;
    _nearest.lightIndex=0;
    _nearest.startEnd=START;
    
    for(int i=0;i<lights.size();i++){
        float startDistance, endDistance, nearestDistance;
        startDistance = lights[i].start.distance(clicked);
        endDistance = lights[i].end.distance(clicked);
        
        if(_nearest.startEnd==START) nearestDistance = lights[_nearest.lightIndex].start.distance(clicked);
        if(_nearest.startEnd==END) nearestDistance   = lights[_nearest.lightIndex].end.distance(clicked);
        
        if(startDistance<=nearestDistance && startDistance<endDistance){
            _nearest.lightIndex = i;
            _nearest.startEnd = START;
        } else if (endDistance<=nearestDistance) {
            _nearest.lightIndex = i;
            _nearest.startEnd = END;
        }

        
    }

    
    //check to see if within clicky range
    float nearestDistance;
    if(_nearest.startEnd==START) nearestDistance = lights[_nearest.lightIndex].start.distance(clicked);
    if(_nearest.startEnd==END) nearestDistance = lights[_nearest.lightIndex].end.distance(clicked);
    if(nearestDistance>50) _nearest.lightIndex = -1;
    return _nearest;

    
}

void ofApp::moveLight(int lightIndex, StartEnd startEnd, ofPoint location){
    if(startEnd == START) lights[lightIndex].start= location;
    if(startEnd == END) lights[lightIndex].end= location;
    lights[lightIndex].updateTrack();
}







