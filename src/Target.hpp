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
    ofPoint current, target;
    int label = -1;
    float influence =0.0001;
    
    bool bDying=false;
    bool bReadyToDie=false;
    
    void update();
    void draw();
};


#endif /* Target_hpp */
