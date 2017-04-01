//
//  Target.hpp
//  forestControl
//
//  Created by Jesse Garrison on 11/1/16.
//
//

#ifndef Target_hpp
#define Target_hpp

#include <stdio.h>
#include "ofMain.h"

#include "Util.h"


class Target{
public:
    Target(){};
    Target(ofPoint _p){
        current = _p;
    }
    ofPoint current, target, previous;
    int label = -1;
    float influence = 0.0001;
    
    bool bDying=false;
    bool bReadyToDie=false;
    
    void update();
    void draw();
    
    bool bIsQuiet = false;
    float quietMoveThreshold = 10;
    int quietTimeThreshold = 30;
    int quietTimer = 0;
    
};


#endif /* Target_hpp */
