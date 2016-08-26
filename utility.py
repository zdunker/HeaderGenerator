import os
from __builtin__ import True

#parse file's full path and retrieve its location folder
#C:\Users\STAR\Desktop\3rd_party_libraries\Xerces-c\build\..\projects\Win32\VC14\xerces-all\XercesLib\XercesLib.vcxproj
# -> C:\Users\STAR\Desktop\3rd_party_libraries\Xerces-c\build\..\projects\Win32\VC14\xerces-all\XercesLib\

def getFileDir(szFile):
    return os.path.dirname(szFile)

def isFolder(location):
    if os.path.isdir(location):
        return True
    return False

def isSolution(location):
    if location.endswith('.sln'):
        return True
    return False

def isProject(location):
    if location.endswith('.vcxproj'):
        return True
    return False