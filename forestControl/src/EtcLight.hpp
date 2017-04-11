//
//  DmxLight.hpp
//  forestControl
//
//  Created by Jesse Garrison on 4/1/17.
//
//

#ifndef EtcLight_hpp
#define EtcLight_hpp

#include <stdio.h>
#include <ofMain.h>
#include "OscHandler.hpp"


class EtcLight{
    
public:
    EtcLight(){};
    EtcLight(OscHandler * _osc, int _id){
        osc = _osc;
        id = _id;
    };

    void update();
    void draw();
    
    float targetIntensity=0;
    
private:
    
    void report();
    float intensity=0;
    float lastIntensity=0;
    
    int id;
    OscHandler * osc;
};

#endif /* EtcLight_hpp */
