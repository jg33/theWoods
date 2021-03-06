#include "ofApp.h"

//--------------------------------------------------------------
void ofApp::setup(){
    ofBackground(0);
    ofSetBackgroundAuto(true);
    
    
    //Osc setup
    osc.setup();
    
    // CV Setup
    cvMan.setup();
    cvMan.gui.loadFromFile("settings.xml");
    
    // Load XML
    //loadXML();

    
    //setup lights//
    lights.push_back(Light(0,ofPoint(50,50),ofPoint(150,100)));
    
    for(int i=0;i<12;i++){
        ofPoint randoPoint = ofPoint(ofRandom(100,ofGetWidth()-100), ofRandom(100,ofGetWidth()-100) );
        
        lights.push_back(Light(i+1,ofPoint(randoPoint.x-ofRandom(75),randoPoint.y-ofRandom(75)),ofPoint(randoPoint.x+ofRandom(75),randoPoint.y+ofRandom(75))));
        
    }
    for(int i=0;i<lights.size();i++){
        lights[i].setOscPtr(&osc);
    }
    
    for(int i=0;i<8;i++){
        targets.push_back(ofPoint(0,0));
        
    }

}

//--------------------------------------------------------------
void ofApp::update(){
    //osc
    osc.update();
    
    
    //cv
    cvMan.update();

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







