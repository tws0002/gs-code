var M_TITLE = "GS Render Submit";
var M_HEIGHT= 100;
var M_WIDTH = 250;
var M_XSTART = 1500;
var M_YSTART = 800;
var M_FITX = 0;
var M_FITY = 0;
var M_WRAPY = 0;
var M_PADDING = 4;
var M_PROJECTFILE = null;
var M_JOBNAME = null;
var M_FONTINSTALLERLOC = "\\\\scholar\\code\\general\\scripts\\batch\\installFont.vbs";

var M_MUSTERPY = "C:\\Python27\\python.exe \\\\scholar\\code\\general\\scripts\\python\\gs\\muster.py";
var M_FOLDER = '33409';

function createUI(thisObj) {
	var comps = Array();
	compItems = getRenderReadyCompItems();
	for(i=0; i<compItems.length; i++){
		comps[i]=compItems[i].comp.name;
	}
	if(comps == false){	return false;}
	
	var myPanel = (thisObj instanceof Panel) ? thisObj : new Window("palette",M_TITLE, [M_XSTART,M_YSTART, (M_XSTART+M_WIDTH), (M_YSTART+M_HEIGHT)]);
	myPanel.add("StaticText",fitter(38,20),"Comp:");
	myPanel.m_comp = myPanel.add("DropDownList",fitter(120,20),comps);
	myPanel.add("StaticText",fitter(38,20,true),"Start:");
	myPanel.m_start = myPanel.add("EditText",fitter(40,20),"1");
	myPanel.add("StaticText",fitter(28,20),"End:");
	myPanel.m_end = myPanel.add("EditText",fitter(40,20),"10");
	myPanel.add("StaticText",fitter(34,20),"Batch:");
	myPanel.m_batch = myPanel.add("EditText",fitter(40,20),"5");
	myPanel.add("StaticText",fitter(38,20,true),"Priority:");
	myPanel.m_priority = myPanel.add("EditText",fitter(40,20),"50");
	myPanel.add("StaticText",fitter(50,20),"(1-100)");

	// SET UP POOLS DROPDOWN
	m_musterPools = getMusterPools();
	for(var i=0; i<m_musterPools.length; i++) { if(m_musterPools[i] == "AE") {m_musterPools.move(i,0); } } // move AE pool to the beginning
	myPanel.add("StaticText",fitter(38,20,true),"Pool:");
	myPanel.m_pool = myPanel.add("DropDownList",fitter(120,20),m_musterPools);
	myPanel.m_pool.selection = myPanel.m_pool.items[0];
	myPanel.m_syncfonts = myPanel.add("Button", fitter(120,20), "Sync fonts to farm");
	
	myPanel.add("StaticText",fitter(180,20,true),"");
	myPanel.m_render = myPanel.add("Button", fitter(60,20), "Render");
	
	/*
		Set up current state.
	 */
			
	myPanel.size = [M_WIDTH,M_WRAPY+M_PADDING];
	if(myPanel instanceof Window){
		myPanel.show();
	}
	myPanel.m_comp.onChange = function() {
		var startEnd = getCompStartStop(this.selection.text);
		myPanel.m_start.text = startEnd[0];
		myPanel.m_end.text = startEnd[1];
	}

	myPanel.m_comp.selection = myPanel.m_comp.items[0];
	
	myPanel.m_syncfonts.onClick = function(){
		syncFontsToFarm(myPanel.m_pool.selection.text);
	}
	
	myPanel.m_render.onClick = function(){
		selectedindex = myPanel.m_comp.selection.index
		selectedcompfile = compItems[selectedindex].outputModule(1).file.name;
		fileext = selectedcompfile.substr(selectedcompfile.length - 3);
		if(fileext=='mov'|fileext=='aif'|fileext=='avi'|fileext=='mp3'|fileext=='mxf'|fileext=='aif'|fileext=='wav'){
			myPanel.m_batch.text = '9999999';
		}		
		sendToFarm(myPanel.m_comp.selection.text, myPanel.m_start.text, myPanel.m_end.text, myPanel.m_priority.text, myPanel.m_batch.text, myPanel.m_pool.selection.text);
		myPanel.hide();
	}
	return myPanel;
}

function fitter(width,height,force_wrap){
	M_PADDING = 4;
	if(force_wrap || (width+M_PADDING*2+M_FITX)>M_WIDTH){
		M_FITY = M_WRAPY;
		M_FITX = 0;
	}
	x1 = M_FITX+M_PADDING;
	y1 = M_FITY+M_PADDING;
	x2 = x1 + width;
	y2 = y1 + height;
	M_FITX = x2;
	if(y2>M_WRAPY){
		M_WRAPY = y2;
	}
	return [x1,y1,x2,y2];
}

Array.prototype.move = function (old_index, new_index) {
	if (new_index >= this.length) {
		var k = new_index - this.length;
		while ((k--) + 1) {
			this.push(undefined);
		}
	}
	this.splice(new_index, 0, this.splice(old_index, 1)[0]);
	return this;
};

function getMusterPools(){
	cmd = M_MUSTERCONNECT+' -q p -H 0 -S 0 -pf parent';
	cmdOutput = system.callSystem(cmd);
	
	var pools = cmdOutput.replace(/(\r)/gm,"").replace(/ /g,"").split('\n');
	pools = removeDuplicates(pools);
	pools = removeBlanks(pools);

	return pools;
}

function removeDuplicates(origArr) {
	var newArr = [],
	origLen = origArr.length, found, x, y;
	
	for ( x = 0; x < origLen; x++ ) {
		found = undefined;
		for ( y = 0; y < newArr.length; y++ ) {
			if ( origArr[x] === newArr[y] ) { found = true;
				break;
				}
		}
		if ( !found) newArr.push( origArr[x] );
	}
	return newArr;
}

function removeBlanks(origArr) {
	var newArr = [];
	for (var i=0; i<origArr.length; i++){
		if (origArr[i].replace(/^\s+/, '').replace(/\s+$/, '')){
				newArr.push(origArr[i]);
		}
	}
	return newArr;
}

function getRenderReadyCompItems(){
	var comps = Array(0);
	for (i = 1; i <= app.project.renderQueue.numItems; ++i) { 
		if(app.project.renderQueue.item(i).status==RQItemStatus.QUEUED | app.project.renderQueue.item(i).status==2615){
			comps.push(app.project.renderQueue.item(i))
		}
	}
	if(comps.length<1){
		alert("No comps ready in your render queue.",M_TITLE)
		return false
	}
	return comps;
}

function getCompStartStop(compName){
	for (i = 1; i <= app.project.renderQueue.numItems; ++i) {
		var item = app.project.renderQueue.item(i);
		if(item.comp.name == compName && item.status==2615){
			return [(item.comp.workAreaStart/item.comp.frameDuration),(item.comp.workAreaDuration/item.comp.frameDuration+item.comp.workAreaStart/item.comp.frameDuration)]
		}
	}
}


function getAELocation(){
	var ver = app.version;
	var majorVer = ver.substring(0,4);
	var aePath;
	var pathVer;
	
	switch (majorVer){
		case '11.0':
			pathVer = 'CS6';
			break;
		case '12.0':
			pathVer = 'CC';
			break;
		case '12.1':
			pathVer = 'CC';
			break;
		case '12.2':
			pathVer = 'CC';
			break;
		case '13.0':
			pathVer = 'CC 2014';
			break;
		case '13.1':
			pathVer = 'CC 2014';
			break;
		case '13.2':
			pathVer = 'CC 2014';
			break;
		case '13.5':
			pathVer = 'CC 2015';
		case '13.6':
			pathVer = 'CC 2015';
		case '13.7':
			pathVer = 'CC 2015';
			break;
	}

	aePath = "C:\\Program Files\\Adobe\\Adobe After Effects "+pathVer+"\\Support Files\\aerender.exe";
	return aePath;
}

function syncFontsToFarm(pool){
	fontFolder = "\\\\scholar\\projects\\"+M_JOBNAME+"\\03_production\\04_elements\\04_FONTS";
	var jsoncmd = {
		'"-add"'	: '"\\"cscript '+M_FONTINSTALLERLOC+' '+fontFolder+'\\""',
		'"-e"'		: '"43"',
		'"-n"'		: '"syncFonts_'+getProjectName()+'"',
		'"-parent"'	: '"'+M_FOLDER+'"',
		'"-pool"'	: '"'+pool+'"',
		'"-group"'	: '"tech"'
	};
	//cmd = M_MUSTERCONNECT+' -b '+' -e 43 '+' -n syncFonts_'+pool+' -add \"cscript '+M_FONTINSTALLERLOC+' '+fontFolder+'\"'+' -parent '+M_FOLDER+' -pool '+pool;
	cmd = M_MUSTERPY+' -j \"\"'+JSON.stringify(jsoncmd)+'\"\"';
	var cmdOutput = system.callSystem(cmd);
	alert('Sucessfully submitted job to Muster: Job#'+cmdOutput,M_TITLE);
	return;
}

function getProjectName(){
	var filePath = M_PROJECTFILE;
	var path = filePath.replace(/\\/g, "/").replace(/ /g, "\ ").toLowerCase();
	var m = /^\/\/scholar\/projects\/(.+?)\//g;
	var match = m.exec(path);
	return match[1];
}

function sendToFarm(compname,start,end,priority,batch,pool){
	var M_RENDEREXE = getAELocation();

	var jsoncmd = {
		'"-add"'	: '"\\\"'+M_RENDEREXE+'\\\"'+' -comp '+'\\"'+compname+'\\""', 
		'"-e"'		: '"1002"',
		'"-n"'		: '"'+M_PROJECTFILE.replace(/^.*[\\\/]/, '')+'_'+compname+'"',
		'"-parent"'	: '"'+M_FOLDER+'"',
		'"-pool"'	: '"'+pool+'"',
		'"-sf"'		: '"'+start+'"',
		'"-ef"'		: '"'+end+'"',
		'"-bf"'		: '"1"',
		'"-pk"'		: '"'+batch+'"',
		'"-pr"'		: '"'+priority+'"',
		'"-group"'	: '"'+getProjectName()+'"',
		'"-eca"'	: '"C:\\Python27\\python.exe //scholar/code/general/scripts/python/sensu/post_chunk_action.py"',
		'"-f"'		: '"'+M_PROJECTFILE+'"'
	}
	//cmd = M_MUSTERPY+' -b '+' -add '+'"\\\"'+M_RENDEREXE+'\\\"'+' -comp '+'\\"'+compname+'\\"\"'+' -e 1002 '+' -n '+'\"'+M_PROJECTFILE.replace(/^.*[\\\/]/, '')+'_'+compname+'\"'+' -parent '+M_FOLDER+' -pool '+pool+' -sf '+start+' -ef '+end+' -bf 1'+' -pk '+batch+' -pr '+priority+' -eca "C:\\Python27\\python.exe //scholar/code/general/scripts/python/sensu/post_chunk_action.py" -f '+'\"'+M_PROJECTFILE+'\"';
	cmd = M_MUSTERPY+' -j \"\"'+JSON.stringify(jsoncmd)+'\"\"';

	//alert(cmd);	return;
	var cmdOutput = system.callSystem(cmd);
	alert('Sucessfully submitted job to Muster: Job#'+cmdOutput,M_TITLE);
	return;
}

function main(mainOBJ){
	if (app.project.file != null){
		M_PROJECTFILE = app.project.file.fsName;
		m = /(\\\\scholar\\projects\\)(.*?)\\/i.exec(app.project.file.fsName);
		if ( m ){ M_JOBNAME = m[2] };
	}else{
		alert("Please save or load a project",M_TITLE);
		return false;
	}
	if (system.osName == "MacOS") {
		alert("Mac OS X detected. You must submit from a Windows workstation.",M_TITLE)
		return false
	}
	var submitPanel = createUI(mainOBJ);
	return submitPanel;
}

main(this)