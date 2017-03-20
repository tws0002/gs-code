#target aftereffects

// Ease and Wizz 2.1.2
// Ian Haigh 2016 (mail@ianhaigh.com)

// An After Effects adaptation of Robert Penner's easing equations.
// Installation, usage, and terms at http://aescripts.com/ease-and-wizz/
// (apologies to Jarvis Cocker: https://www.youtube.com/watch?v=AIaehhYLVZA)


function ease_and_wizz_script(ui_reference) {

	var ease_and_wizz = {}; // put all global variables on this object to avoid namespace clashes

	ease_and_wizz.EASING_FOLDER            = "easingExpressions";
	ease_and_wizz.CLEAR_EXPRESSION_BTN     = false; // this adds a button to the palette, "clear", that deletes expressions on all selected properties. Off by default.
	ease_and_wizz.VERSION                  = "2.1.2";
	ease_and_wizz.easingEquation           = "";
	ease_and_wizz.palette                  = {};

	// palette controls
	ease_and_wizz.easingList               = {};
	ease_and_wizz.typeList                 = {};
	ease_and_wizz.keysList                 = {};
	ease_and_wizz.curvaceousCheckbox       = {};

	// define values for the controls
	ease_and_wizz.keysLookup               = {
		'-all':       'All',
		'-startEnd':  'Start and end',
		'-startOnly': 'Start only'
	};

	ease_and_wizz.inOutLookup              = {
		'inOut':     'In + Out',
		'in':        'In',
		'out':       'Out'
	};

	ease_and_wizz.CURVACEOUS_SETTINGS_KEY = "curvaceous";
	ease_and_wizz.TYPE_SETTINGS_KEY = "type";
	ease_and_wizz.KEYS_SETTINGS_KEY = "keys";


	ease_and_wizz.easingTypesAry = ['Expo', 'Circ', 'Quint', 'Quart', 'Quad', 'Sine', '-', 'Bounce', 'Back', 'Elastic'];

	ease_and_wizz.strHelpText = "Ease and Wizz is a set of expressions that give you more animation options, such as exponential, elastic, and bounce. Simply select a keyframe, choose the type of easing, and click \"Apply\". The relevant expression will be attached to that property.\n" +
			"\n" +
			"Turn on the Curvaceous checkbox if you're animating mask or shape paths, or curved motion paths.\n" +
			"\n" +
			"Latest version, documentation, and videos are available from aescripts.com/ease-and-wizz/\n" +
			"\n" +
			"Thanks for using Ease and Wizz!\nIan Haigh (ianhaigh.com)"
	;

	function ew_getHashValues(hash)
	{ // {{{
		var ary = [];
		for (var key in hash) {
			if (hash.hasOwnProperty(key)) {
				ary.push(hash[key]);
			}
		}

		return ary;
	} // }}}

	function ew_getHashKeys(hash)
	{ // {{{
		var ary = [];
		for (var key in hash) {
			if (hash.hasOwnProperty(key)) {
				ary.push(key);
			}
		}

		return ary;
	} // }}}

	function ew_fetchIndex(obj, key) {
		var ary = ew_getHashValues(obj);
		for (var c = 0; c < ary.length; c++) {
			if (ary[c] === key) return c;
		}
		return 0; // nothing matched, just select the first one
	}

	function ew_main(thisObj)
	{ //{{{
		ew_createPalette(thisObj);
	} //}}}

	function ew_getPathToEasingFolder()
	{ // {{{
		// much simpler, thanks Jeff
		var folderObj = new Folder((new File($.fileName)).path + "/" + ease_and_wizz.EASING_FOLDER);
		return folderObj;

	} // }}}

	function ew_createPalette(thisObj)
	{//{{{
		var LIST_DIMENSIONS = [0, 0, 120, 15];
		var STATIC_TEXT_DIMENSIONS = [0, 0, 60, 15];

		ease_and_wizz.palette = (thisObj instanceof Panel) ? thisObj : new Window("palette", "Easing", undefined, {resizeable: true});
		ease_and_wizz.palette.margins       = 6;
		ease_and_wizz.palette.alignChildren = 'left';

		// fix the text display in the popup menu - thanks Jeff Almasol
		var winGfx          = ease_and_wizz.palette.graphics;
		var darkColorBrush  = winGfx.newPen(winGfx.BrushType.SOLID_COLOR, [0,0,0], 1);
		var lightColorBrush = winGfx.newPen(winGfx.BrushType.SOLID_COLOR, [1,1,1], 1);

		// popup menus
		// {{{

		// "easing" menu

			var	easingGrp = ease_and_wizz.palette.add('group', undefined, 'Easing group');
				var EASING_SETTINGS_KEY = "easing"; // save on typos
				easingGrp.add('statictext', STATIC_TEXT_DIMENSIONS, 'Easing:');

				ease_and_wizz.easingList                          = easingGrp.add('dropdownlist', LIST_DIMENSIONS, ease_and_wizz.easingTypesAry);
				ease_and_wizz.easingList.helpTip                  = "Choose the type of easing here. They're arranged from most dramatic (expo) to least dramatic (sine), with “special effects” (back, bounce, elastic) at the end.";
				ease_and_wizz.easingList.graphics.foregroundColor = darkColorBrush;

				if (app.settings.haveSetting("easeandwizz", EASING_SETTINGS_KEY)) {
					var key = app.settings.getSetting("easeandwizz", EASING_SETTINGS_KEY); // from the settings
					ease_and_wizz.easingList.selection = ew_fetchIndex(ease_and_wizz.easingTypesAry, key);
				} else {
					ease_and_wizz.easingList.selection                = 0; // select the first item
				}

				ease_and_wizz.easingList.onChange = function() {
					app.settings.saveSetting("easeandwizz", EASING_SETTINGS_KEY, this.selection.toString());
				}

		// "type" menu

			var	typeGrp = ease_and_wizz.palette.add('group', undefined, 'Type group');
				typeGrp.add('statictext', STATIC_TEXT_DIMENSIONS, 'Type:');

				ease_and_wizz.typeList                          = typeGrp.add('dropdownlist', LIST_DIMENSIONS, ew_getHashValues(ease_and_wizz.inOutLookup));
				ease_and_wizz.typeList.helpTip                  = "Whether the values ease in, out, or both.";
				ease_and_wizz.typeList.graphics.foregroundColor = darkColorBrush;

				if (app.settings.haveSetting("easeandwizz", ease_and_wizz.TYPE_SETTINGS_KEY)) {
					var key = app.settings.getSetting("easeandwizz", ease_and_wizz.TYPE_SETTINGS_KEY); // from the settings
					ease_and_wizz.typeList.selection = ew_fetchIndex(ease_and_wizz.inOutLookup, key);
				} else {
					ease_and_wizz.typeList.selection                = 0; // select the first item
				}

				ease_and_wizz.typeList.onChange = function() {
					app.settings.saveSetting("easeandwizz", ease_and_wizz.TYPE_SETTINGS_KEY, this.selection.toString());
				}

		// "keys" menu

			var	keysGrp = ease_and_wizz.palette.add('group', undefined, 'Keys group');
				keysGrp.add('statictext', STATIC_TEXT_DIMENSIONS, 'Keys:');

				ease_and_wizz.keysList                          = keysGrp.add('dropdownlist', LIST_DIMENSIONS, ew_getHashValues(ease_and_wizz.keysLookup));
				ease_and_wizz.keysList.graphics.foregroundColor = darkColorBrush;
				ease_and_wizz.keysList.helpTip                  = "When there are more than two keyframes, this affects whether it eases ALL of the keyframes (the default), the first and last two, or only the first two. Other keyframes will behave as usual.";
				if (app.settings.haveSetting("easeandwizz", ease_and_wizz.KEYS_SETTINGS_KEY) && ! ease_and_wizz.curvaceousCheckbox.value) {
					var key = app.settings.getSetting("easeandwizz", ease_and_wizz.KEYS_SETTINGS_KEY); // from the settings
					ease_and_wizz.keysList.selection = ew_fetchIndex(ease_and_wizz.keysLookup, key);
				} else {
					ease_and_wizz.keysList.selection                = 0; // select the first item
				}

				ease_and_wizz.keysList.onChange = function() {
					app.settings.saveSetting("easeandwizz", ease_and_wizz.KEYS_SETTINGS_KEY, this.selection.toString());
				}

		// }}}

		// curvaceous checkbox
		var	curvaceousGrp = ease_and_wizz.palette.add('group', undefined, 'Curvaceous group');

			curvaceousGrp.add('statictext', STATIC_TEXT_DIMENSIONS, '\u00A0');
			ease_and_wizz.curvaceousCheckbox         = curvaceousGrp.add('checkbox', undefined, 'Curvaceous');
			ease_and_wizz.curvaceousCheckbox.helpTip = "Turn this on if you’re easing a mask shape or shape path. Note that due to the way it works, Curvaceous automatically disables the “special” easing types, back, bounce, and elastic.";

			if (app.settings.haveSetting("easeandwizz", ease_and_wizz.CURVACEOUS_SETTINGS_KEY)) {
				if (app.settings.getSetting("easeandwizz", ease_and_wizz.CURVACEOUS_SETTINGS_KEY) === "1") {
					ease_and_wizz.curvaceousCheckbox.value = true;
				} else {
					ease_and_wizz.curvaceousCheckbox.value = false;
				}
			} else {
				// no setting, choose the default
				ease_and_wizz.curvaceousCheckbox.value = false;
			}


		// update the panel
		ease_and_wizz.curvaceousCheckbox.onClick = ew_fixMenus;


		// apply button
		// {{{

		var buttonGrp = ease_and_wizz.palette.add('group', undefined, 'Button group');
		buttonGrp.add('statictext', STATIC_TEXT_DIMENSIONS, '');

		// standard buttons
		if (ease_and_wizz.CLEAR_EXPRESSION_BTN)
		{
			var ew_clearExpressionsBtn     = buttonGrp.add('button', undefined, 'Clear expressions');
			ew_clearExpressionsBtn.onClick = ew_clearExpressions;
		}

		////////////////////
		// apply button
		////////////////////

		var applyBtn     = buttonGrp.add('button', undefined, 'Apply');
		applyBtn.onClick = ew_applyExpressions;
		var helpBtn = buttonGrp.add("button {text:'?', maximumSize:[30,30]}");
		helpBtn.onClick = function() {alert("Ease and Wizz v" + ease_and_wizz.VERSION + "\n" + ease_and_wizz.strHelpText, "Ease and Wizz")};

		// }}}

		if (ease_and_wizz.palette instanceof Window)
		{
			ease_and_wizz.palette.show();
		}
		else
		{
			ease_and_wizz.palette.layout.layout(true);
		}
		ew_fixMenus();

	}//}}}

	function ew_fixMenus () {
		if (ease_and_wizz.curvaceousCheckbox.value == true) {
			// it was checked; remove the options that aren't compatible with Curvaceous

			// reset keys menu
			if (ease_and_wizz.keysList.selection.toString() == 'Start only') {
				ease_and_wizz.keysList.selection = 0;
			}

			// before removing options, make sure a valid easing type remains selected
			var curveType = ease_and_wizz.easingList.selection.toString();
			if (curveType == 'Elastic' || curveType == 'Back') ease_and_wizz.easingList.selection = 'Expo';

			// now take 'em away
			// var aaa = ease_and_wizz.easingList;
			// debugger;
			ease_and_wizz.easingList.find("Elastic").enabled = false;
			ease_and_wizz.easingList.find("Back").enabled = false;
			ease_and_wizz.keysList.find("Start only").enabled = false;
			app.settings.saveSetting("easeandwizz", ease_and_wizz.CURVACEOUS_SETTINGS_KEY, "1");

		} else {
			// it wasn't checked, add the missing items
			ease_and_wizz.easingList.find ("Elastic").enabled = true;
			ease_and_wizz.easingList.find ("Back").enabled = true;
			ease_and_wizz.keysList.find   ("Start only").enabled = true;
			app.settings.saveSetting("easeandwizz", ease_and_wizz.CURVACEOUS_SETTINGS_KEY, "0");
		}
	} // }}}



	function ew_trace(s) { // for debugging
	//{{{
		//$.writeln(s); // writes to the ExtendScript interface
		writeLn(s); // writes in the AE info window
	} //}}}

	function ew_readFile(filename)
	{ //{{{
		var easing_folder = ew_getPathToEasingFolder();
		var file_handle   = new File(easing_folder.fsName + '/' + filename);

		if (!file_handle.exists) {
			throw("I can't find this file: '" + filename + "'. \n\nI looked in here: '" + easing_folder.fsName + "'. \n\nPlease refer to the installation guide and try installing again, or go to:\n\nhttp://aescripts.com/ease-and-wizz/\n\nfor more info.");
		}

		try {
			file_handle.open('r');
			var the_code = file_handle.read();
		} catch(e) {
			throw("I couldn't read the easing equation file: " + e);
		} finally {
			file_handle.close();
		}

		return(the_code);
	} //}}}

	function ew_applyExpressions() { // decide what external file to load
	 // {{{

		if (!ew_canProceed()) { return false; }

		app.beginUndoGroup("Ease and Wizz");

		// defaults
		var easingType              = 'inOut';
		var easeandwizzOrCurvaceous = "-easeandwizz";
		var keyframesToAffect       = "-allKeys";

		// loop through the two menu objects and see what the user's selected

		// easeAndWizz, or curvaceous?
		if (ease_and_wizz.curvaceousCheckbox.value) easeandwizzOrCurvaceous = "-curvaceous";

		// which keys should be affected?
		for ( var i in ease_and_wizz.keysLookup )
		{
			if (ease_and_wizz.keysLookup[i] == ease_and_wizz.keysList.selection.toString())
			{
				keyframesToAffect = i;
			}
		}

		// then, should the expression be In, Out, or Both?
		for ( var i in ease_and_wizz.inOutLookup )
		{
			if (ease_and_wizz.inOutLookup[i] == ease_and_wizz.typeList.selection.toString()) {
				easingType = i;
			}
		}

		var curveType = ease_and_wizz.easingList.selection.toString();
		var fileToLoad = "";

		// very hacky, sorry
		if (curveType == "AE Expo") {
			curveType = "aeExpo";
			fileToLoad = curveType + ".txt";
		} else {
			fileToLoad = easingType + curveType + easeandwizzOrCurvaceous + keyframesToAffect + '.txt';
		}

		try {
			ease_and_wizz.easingEquation = ew_readFile(fileToLoad);
		} catch(e) {
			Window.alert(e);
			return false;
		}

		ew_setProps(ease_and_wizz.easingEquation);
		app.endUndoGroup();
	} // }}}

	function ew_clearExpressions()
	{//{{{
		// TODO : "Object is invalid"
		// TODO : "null is not an object"
		var selectedProperties = activeItem.selectedProperties;
		for (var f in selectedProperties)
		{
			var currentProperty = selectedProperties[f];
			if (!currentProperty.canSetExpression) { continue; }
			currentProperty.expression = '';
		}
	}//}}}

	function ew_setProps(expressionCode)
	{ //{{{
		var selectedProperties = app.project.activeItem.selectedProperties;
		var numOfChangedProperties = 0;

		for (var f in selectedProperties)
		{
			var currentProperty = selectedProperties[f];

			if ((currentProperty.propertyValueType == PropertyValueType.SHAPE) && !ease_and_wizz.curvaceousCheckbox.value) {
				alert("It looks like you have a Mask Path selected. To apply Ease and Wizz to a Mask Path, select the ‘Curvaceous’ checkbox and try again.");
				continue;
			}

			if (!currentProperty.canSetExpression) { continue } // don't do anything if we can't set an expression
			if (currentProperty.numKeys < 2) { continue }       // likewise if there aren't at least two keyframes

			currentProperty.expression = expressionCode;
			numOfChangedProperties++;
		}
		clearOutput(); // TODO
		ew_trace("Ease and Wizz:")
		var easingType = ease_and_wizz.easingList.selection.toString();
		if (numOfChangedProperties == 1) {
			ew_trace("Applied \"" +  easingType + "\" to one property.");
		} else {
			ew_trace("Applied \"" +  easingType + "\" to " + numOfChangedProperties + " properties.");
		}
	} //}}}

	function ew_canProceed()
	{ // {{{
		var activeItem = app.project.activeItem;
		if (activeItem === null)
		{
			alert("Select a keyframe or two.");
			return false;
		}
		if (activeItem.selectedProperties == "") {
			alert("Please select at least one keyframe.")
			return false;
		}

		return true;
	} // }}}

	ew_main(ui_reference);

}

ease_and_wizz_script(this);
