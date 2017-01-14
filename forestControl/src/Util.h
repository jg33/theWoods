//
//  Util.h
//  forestControl
//
//  Created by Jesse Garrison on 11/1/16.
//
//

#ifndef Util_h
#define Util_h

#include "ofMain.h"

struct labeledBlob{
    ofPoint center;
    int label, age;
    
};

enum StartEnd{
    START,
    END
};

struct lightTrackPoint{
    int lightIndex;
    StartEnd startEnd;
    
};
#endif /* Util_h */
