#!/usr/bin/python

import argparse
import json
import sys
import distutils.util
import os

# update info
current_script_version = 1
version_info_url = "http://static.tumult.com/hype/export-scripts/Sizmek/latest_script_version.txt" # only returns a version number
download_url = "http://tumult.com/hype/export-scripts/Sizmek/" # gives a user info to download and install
minimum_update_check_duration_in_seconds = 60 * 60 * 24 # once a day
defaults_bundle_identifier = "com.tumult.Hype2.hype-export.Sizmek"

# html insertions
insert_at_head_start = """
	<meta name="ad.size" content="width=${width},height=${height}">
	${EBModulesToLoad}
	<script type="text/javascript" src="./EBLoader.js"></script>
"""

insert_at_head_end = """
	<script>
	
	(function () {
		
		var thisHypeDocument = null;
	
		function preInit() {
			if(EB.isInitialized()) {
				init();
			} else {
				EB.addEventListener(EBG.EventName.EB_INITIALIZED, init);
			}
		}
	
		function init() {
			show();
		}
	
		function show() {
			if(thisHypeDocument != null) {
				thisHypeDocument.showSceneNamed(thisHypeDocument.sceneNames()[0]);
			}
		}
	
		function hypeDocumentLoadCallback(hypeDocument, element, event) {
			thisHypeDocument = hypeDocument;
			if(!EB.isInitialized() ) {
				// don't load the Hype document until Sizmek EBLoader has loaded
				return false;
			} 
			return true;
		}

		if("HYPE_eventListeners" in window === false) {
			window.HYPE_eventListeners = Array();
		}
		window.HYPE_eventListeners.push({"type":"HypeDocumentLoad", "callback":hypeDocumentLoadCallback});
	
		window.addEventListener('load', preInit);

	})();
	
	function hypeAdExit(identifier, url) {
		if(identifier != null && url != null) {
			EB.clickthrough(identifier, url);
		} else {
			EB.clickthrough();
		}
	}
	
	function hypeAdCounter(identifier) {
		EB.userActionCounter(identifier);
	}
	
	function hypeAdAutoEventCounter(identifier) {
		EB.automaticEventCounter(identifier);
	}
	
	function hypeAdStartTimer(identifier) {
		EB.startTimer(identifier);
	}
	
	function hypeAdStopTimer(identifier) {
		EB.stopTimer(identifier);
	}
	
	function hypeAdDummyInteractions() {
		${dummy_interactions}
	}
		
	</script>
"""

insert_at_body_start = ""
insert_at_body_end = ""

function_name_mapping = { "hypeAdExit" : "EB.clickthrough", "hypeAdCounter" : "EB.userActionCounter", "hypeAdAutoEventCounter" : "EB.automaticEventCounter", "hypeAdStartTimer" : "EB.startTimer", "hypeAdStopTimer" : "EB.stopTimer" }
def construct_dummy_interaction(function_name, arguments):	
	if function_name in function_name_mapping:
		replaced_function_name = function_name_mapping[function_name]
	else:
		return None	
	return "" + replaced_function_name + "(" + ",".join(arguments) + ")"


class HypeURLType:
	Unknown = 0
	HypeJS = 1
	Resource = 2
	Link = 3
	ResourcesFolder = 4

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('--hype_version')
	parser.add_argument('--hype_build')
	parser.add_argument('--export_uid')

	parser.add_argument('--get_options', action='store_true')

	parser.add_argument('--replace_url')
	parser.add_argument('--url_type')
	parser.add_argument('--is_reference', default="False")
	parser.add_argument('--should_preload')
	
	parser.add_argument('--modify_staging_path')
	parser.add_argument('--destination_path')
	parser.add_argument('--export_info_json_path')
	parser.add_argument('--is_preview', default="False")

	parser.add_argument('--check_for_updates', action='store_true')

	args, unknown = parser.parse_known_args()
	

	## --get_options
	##		return arguments to be presented in the Hype UI as a dictionary:
	##		'export_options' is a dictionary of key/value pairs that make modifications to Hype's export/preview system. Some useful ones:
	##			'exportShouldInlineHypeJS' : boolean
	##			'exportShouldInlineDocumentLoader' : boolean
	##			'exportShouldUseExternalRuntime' : boolean
	##			'exportExternalRuntimeURL' : string
	##			'exportShouldSaveHTMLFile' : boolean
	##			'indexTitle' : string
	##			'exportShouldBustBrowserCaching' : boolean
	##			'exportShouldIncludeTextContents' : boolean
	##			'exportShouldIncludePIE' : boolean
	##			'exportSupportInternetExplorer6789' : boolean
	##			'initialSceneIndex' : integer
	##		'save_options' is a dictionary of key/value pairs that for determining when/how to export. valid keys:
	##			'file_extension' : the final extension when exported (ex. "zip")
	##			'allows_export' : should show up in the File > Export as HTML5 menu and Advanced Export
	##			'allows_preview' : should show up in the Preview menu, if so --is_preview True is passed into the --modify_staging_path call
	##		'document_arguments' should be an array of keys, these will be passed to subsequent calls via --key value
	##		'extra_actions' should be an array of dictionaries
	##			'label': string that is the user presented name
	##			'function': javascript function to call if this action is triggered, just the name of it
	##			'arguments': array of dictionaries that represent arguments passed into the function
	##				'label': string that is presented to Hype UI
	##				'type': string that is either "String" (will be quoted and escaped) or "Expression" (passed directly to function argument as-is)
	if args.get_options:		
		def export_options():
			#cdnPath = "https://secure-ds.serving-sys.com/BurstingcachedScripts/libraries/hype/" + args.hype_build
		
			return {
				"exportShouldInlineHypeJS" : True,
				"exportShouldInlineDocumentLoader" : True,
				"exportShouldUseExternalRuntime" : False,
				#"exportExternalRuntimeURL" : cdnPath,
				"exportShouldSaveHTMLFile" : True,
				"exportShouldNameAsIndexDotHTML" : True,
				#"indexTitle" : "",
				"exportShouldBustBrowserCaching" : False,
				"exportShouldIncludeTextContents" : False,
				"exportShouldIncludePIE" : False,
				"exportSupportInternetExplorer6789" : False,
			}

		def save_options():
			return {
				"file_extension" : "zip",
				"allows_export" : True,
				"allows_preview" : True,
			}

		def extra_actions():
			return [
				{"label" : "ClickThrough", "function" : "hypeAdExit"},
				{"label" : "Custom ClickThrough", "function" : "hypeAdExit", "arguments":[{"label":"intName", "type": "String"}, {"label":"clickURL", "type": "String"}]},
				{"label" : "User Action Counter", "function" : "hypeAdCounter", "arguments":[{"label":"intName", "type": "String"}]},
				{"label" : "Automatic Event Counter", "function" : "hypeAdAutoEventCounter", "arguments":[{"label":"intName", "type": "String"}]},
				{"label" : "Start Timer", "function" : "hypeAdStartTimer", "arguments":[{"label":"intName", "type": "String"}]},
				{"label" : "Stop Timer", "function" : "hypeAdStopTimer", "arguments":[{"label":"intName", "type": "String"}]},				
			]
		
		options = {
			"export_options" : export_options(),
			"save_options" : save_options(),
			"extra_actions" : extra_actions(),
		}
	
		print json.dumps({"result" : options})
		sys.exit(0)


	## --replace_url [url] --url_type [HypeURLType] --is_reference [True|False] --should_preload [None|True|False] --export_uid [identifier]
	##		return a dictionary with "url", "is_reference", and optional "should_preload" keys
	##		if HypeURLType.ResourcesFolder, you can set the url to "." so there is no .hyperesources folder and everything
	##		is placed next to the .html file
	##		should_preload may be None type in cases where it won't be used
	elif args.replace_url != None:
		url_info = {}
		url_info['is_reference'] = bool(distutils.util.strtobool(args.is_reference))
		if args.should_preload != None:
			url_info['should_preload'] = bool(distutils.util.strtobool(args.should_preload))
		
		if int(args.url_type) == HypeURLType.ResourcesFolder:
			url_info['url'] = "."
		else:
			url_info['url'] = args.replace_url
		
		print json.dumps({"result" : url_info})
		sys.exit(0)


	## --modify_staging_path [filepath] --destination_path [filepath] --export_info_json_path [filepath] --is_preview [True|False] --export_uid [identifier]
	##		return True if you moved successfully to the destination_path, otherwise don't return anything and Hype will make the move
	##		make any changes you'd like before the save is complete
	##		for example, if you are a zip, you need to zip and write to the destination_path
	##		or you may want to inject items into the HTML file
	##		if it is a preview, you shouldn't do things like zip it up, as Hype needs to know where the index.html file is
	##		export_info_json_path is a json object holding keys:
	##			html_filename: string that is the filename for the html file which you may want to inject changes into
	##			main_container_width: number representing the width of the document in pixels
	##			main_container_height: number representing the height of the document in pixels
	##			document_arguments: dictionary of key/value pairs based on what was passed in from the earlier --get_options call
	##			extra_actions: array of dictionaries for all usages of the extra actions. There is no guarantee these all originated from this script or version.
	##				function: string of function name (as passed in from --get_options)
	##				arguments: array of strings	elif args.modify_staging_path != None:
	elif args.modify_staging_path != None:
		import os
		import string
		
		is_preview = bool(distutils.util.strtobool(args.is_preview))
		
		# read export_info.json file
		export_info_file = open(args.export_info_json_path)
		export_info = json.loads(export_info_file.read())
		export_info_file.close()
		
		# write out EBLoader
		writeEBLoader(args.modify_staging_path)
				
		# determine if there is any video and then make sure this module is set to be loaded
		global insert_at_head_start
		template = string.Template(insert_at_head_start)
		if folder_contains_file_of_types(args.modify_staging_path, ["mp4", "ogv", "webm", "avi", "mov", "ogg", "m4v"]):
			modulesToLoad = '<script type="text/javascript"> EBModulesToLoad = [\'Video\']; </script>';
		else:
			modulesToLoad = '';
		insert_at_head_start = template.substitute({'width' : export_info['main_container_width'], 'height' : export_info['main_container_height'], "EBModulesToLoad" : modulesToLoad })
		
		# insert interactions for dummy code so it is picked up by ad parsers		
		global insert_at_head_end
		template = string.Template(insert_at_head_end)
		dummy_interactions = ""
		for actionInfo in export_info['extra_actions']:
			dummy_interaction = construct_dummy_interaction(actionInfo["function"], actionInfo["arguments"])
			if dummy_interaction == None:
				continue
			dummy_interactions = dummy_interactions + "\t\t" + dummy_interaction + ";\n"
		insert_at_head_end = template.substitute({"dummy_interactions" : dummy_interactions})

		# rewrite HTML file
		index_path = os.path.join(args.modify_staging_path, export_info['html_filename'])
		perform_html_additions(index_path)

		# move to final location and zip up if not a preview
		import shutil
		shutil.rmtree(args.destination_path, ignore_errors=True)
		
		if is_preview == True:
			shutil.move(args.modify_staging_path, args.destination_path)
			print json.dumps({"result" : True})
		else:
			zip(args.modify_staging_path, args.destination_path)
			print json.dumps({"result" : True})
		sys.exit(0)

	## --check_for_updates
	##		return a dictionary with "url", "from_version", and "to_version" keys if there is an update, otherwise don't return anything and exit
	##		it is your responsibility to decide how often to check
	elif args.check_for_updates:
		import subprocess
		import urllib2
		
		last_check_timestamp = None
		try:
			last_check_timestamp = subprocess.check_output(["defaults", "read", defaults_bundle_identifier, "last_check_timestamp"]).strip()
		except:
			pass

		try:
			timestamp_now = subprocess.check_output(["date", "+%s"]).strip()
			if (last_check_timestamp == None) or ((int(timestamp_now) - int(last_check_timestamp)) > minimum_update_check_duration_in_seconds):
				subprocess.check_output(["defaults", "write", defaults_bundle_identifier, "last_check_timestamp", timestamp_now])
				latest_script_version = int(urllib2.urlopen(version_info_url).read().strip())
				if latest_script_version > current_script_version:
					print json.dumps({"result" : {"url" : download_url, "from_version" : str(current_script_version), "to_version" : str(latest_script_version)}})
		except:
			pass

		sys.exit(0)

def writeEBLoader(folder_path):
	eb_loader_script_contents = """
	(function() {
	  document.write("<script src='" + (document.location.protocol === "https:" ? "https://secure-" : "http://") + "ds.serving-sys.com/BurstingScript/EBLoader.js'><\/script>");
	})();
	"""	
	eb_loader_path = os.path.join(folder_path, "EBLoader.js")
	if os.path.exists(eb_loader_path) == False:
		eb_loader_file = open(eb_loader_path, "w")
		eb_loader_file.write(eb_loader_script_contents)
		eb_loader_file.close()


# HTML FILE MODIFICATION

def perform_html_additions(index_path):
	index_contents = None
	with open(index_path, 'r') as target_file:
		index_contents = target_file.read()
		
	if index_contents == None:
		return
		
	import re
	if insert_at_head_start != None:
		head_start = re.search("<head.*?>", index_contents, re.IGNORECASE).end()
		index_contents = index_contents[:head_start] + insert_at_head_start + index_contents[head_start:]
	if insert_at_head_end != None:
		head_end = re.search("</head", index_contents, re.IGNORECASE).start()
		index_contents = index_contents[:head_end] + insert_at_head_end + index_contents[head_end:]
	if insert_at_body_start != None:
		body_start = re.search("<body.*?>", index_contents, re.IGNORECASE).end()
		index_contents = index_contents[:body_start] + insert_at_body_start + index_contents[body_start:]
	if insert_at_body_end != None:
		body_end = re.search("</body", index_contents, re.IGNORECASE).start()
		index_contents = index_contents[:body_end] + insert_at_body_end + index_contents[body_end:]

	with open(index_path, 'w') as target_file:
		target_file.write(index_contents)


# UTILITIES

def folder_contains_file_of_types(folder_path, extensions):
	from os import walk
	for dirpath, dirnames, files in os.walk(folder_path):
		for name in files:
			for extension in extensions:
				if name.lower().endswith(extension):
					return True
	return False


# from http://stackoverflow.com/questions/14568647/create-zip-in-python
def zip(src, dst):
	import os
	import zipfile
	zf = zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED)
	abs_src = os.path.abspath(src)
	for dirname, subdirs, files in os.walk(src):
		for filename in files:
			absname = os.path.abspath(os.path.join(dirname, filename))
			arcname = absname[len(abs_src) + 1:]
			zf.write(absname, arcname)
	zf.close()


if __name__ == "__main__":
	main()
