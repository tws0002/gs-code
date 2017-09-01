import nuke,re,os

def main():
	for n in nuke.selectedNodes('Write'):
		ext=n['file_type'].value()
		regex = re.compile("v[0-9]{2,9}")
		thisPath= nuke.root().name()
		vers=regex.findall(thisPath)[0]
		thisShotPath=thisPath.split("/work")[0]
		thisShotName=thisShotPath.split('/')[-1]
		filename=thisShotName+"_"+n.name()+"_"+vers+".####."+ext
		outPath=thisShotPath+"/render/"+n.name()+"/"+vers+"/"+filename

		n['file'].setValue(outPath)




		dirpath=os.path.dirname(outPath)
		try:
		    os.makedirs(dirpath)
		    print dirpath,' created'
		except:
		    pass