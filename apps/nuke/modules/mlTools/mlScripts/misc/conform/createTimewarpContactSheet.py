import nuke

def main():
	tw=nuke.nodes.TimeWarp()
	tw['lookup'].setAnimated()
	frm=1
	for n in nuke.selectedNodes():
		first=n['first_frame'].value()
		last=n['last_frame'].value()
		mid=int((float(first)+float(last))/2.0)
		tw['lookup'].setValueAt(mid,frm)
		frm+=1