Option Explicit
' Installing multiple Fonts in Windows 7
' http://www.cloudtec.ch 2011

Dim objShell, objFSO, wshShell
Dim strFontSourcePath, objFolder, objFont, objNameSpace, objFile

Set objShell = CreateObject("Shell.Application")
Set wshShell = CreateObject("WScript.Shell")
Set objFSO = createobject("Scripting.Filesystemobject")

Wscript.Echo "--------------------------------------"
Wscript.Echo " Install Fonts "
Wscript.Echo "--------------------------------------"
Wscript.Echo " "

If WScript.Arguments.Count = 0 Then
    strFontSourcePath = "\\scholar\assets\Fonts\_fontinstaller"
Else
	strFontSourcePath = WScript.Arguments(0)
End If

If objFSO.FolderExists(strFontSourcePath) Then

	Set objNameSpace = objShell.Namespace(strFontSourcePath)
	Set objFolder = objFSO.getFolder(strFontSourcePath)

	For Each objFile In objFolder.files
		If LCase(right(objFile,4)) = ".ttf" OR LCase(right(objFile,4)) = ".otf" Then
			Set objFont = objNameSpace.ParseName(objFile.Name)
				If objFSO.FileExists("C:\WINDOWS\Fonts\" & objFile.Name) = False Then
					objFont.InvokeVerb("Install")
					Wscript.Echo "Installed Font: " & objFont
				Else
					Wscript.Echo "Font already installed. Skipping: " & objFont
				End If
			Set objFont = Nothing
		End If
	Next
Else
	Wscript.Echo "Font Source Path does not exist: " & strFontSourcePath
End If

Wscript.Echo "Done installing fonts."