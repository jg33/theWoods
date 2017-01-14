var msg="";

function message(char){
	msg+=char;
	
	
	}
	
function space(){
	msg+=" ";
	}
	
function bang(){
	outlet(0,msg);
	msg="";
	}