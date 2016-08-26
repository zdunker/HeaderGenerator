###################################################################################################
# 3rd party library tool
# This is a Windows-based tool:
#   For those 3rd party libraries built by CM, we are also responsible to provide header files along
#   with the libraries. Especially for those components who don't have all headers in one location,
#   it could be a boring job to grab needed headers from here and there.
#   So this tool is to take care of this boring job, read directly from source and get headers from
#   there.
#
# Possible input: 
#   1: directory (contains c/c++ source code under it preferable)
#      fits those who don't provide project files
#   2: vcxproj file
#      fits those who provide project files, regardless of configuration type
#
# Desire output:
#   Create an include folder in current working directory and throw headers in
#
# Benefits:
#   automating the step of providing headers
#
# Usage:
#   HFE.py %PROJECT_FILE% %SCAN_AREA%
#   Scan area is the root directory where headers should be located inside
#
# TODO: Desire a better layout for header files
###################################################################################################
import os
import sys

szUsage1 = "usage: HeaderFileExtracter.py %FILE_OR_PATH% %SCAN_AREA%"
szUsage2 = "       -File should be vcxproj file"
szUsage3 = "       -Path should contain the C sources (this will not scan every child dir under root for now)"
szUsage4 = "       -Scan_area should be the component source folder, indicating which root would you like to"
szUsage5 = "        search in for headers"

def isProject(szPath):
    if szPath.lower().endswith(".vcxproj"):
        return True
    return False

def getProjectSource(szProjectFile,szSourceList,szHeaderList):
    szCurWorkingDir= os.path.dirname(szProjectFile)
    with open(szProjectFile) as fProj:
        szTmpContent = fProj.readlines()
    for line in szTmpContent:
        if "<ClCompile Include" in line:
            szSourceList.append(szCurWorkingDir+"\\"+line.split('"')[1])
        elif "<ClInclude Include" in line:
            szHeaderList.append(szCurWorkingDir+"\\"+line.split('"')[1])

def getDirSource(szCurWorkingDir,szSourceList):
    szTmpContent = os.listdir(szCurWorkingDir)
    for szSourceFile in szTmpContent:
        if szSourceFile.endswith(".c") or szSourceFile.endswith(".cpp") or szSourceFile.endswith(".cc"):
            szSourceList.append(szCurWorkingDir+"\\"+szSourceFile)
            
def getIncContent(szIncTmpContent):
    szContent = []
    for szLine in szIncTmpContent:
        if "#include" in szLine:
            szContent.append(szLine)
    return szContent

def firstNonSpcChar(szStr):
    for i in range(len(szStr)):
        if szStr[i] != " ":
            return szStr[i]

def getIncNames(szIncContent,szHeaderNameList):
    for szInclude in szIncContent:
        szInclude = '"'.join(szInclude.split('<'))
        szInclude = '"'.join(szInclude.split('>'))
        print szInclude
        if firstNonSpcChar(szInclude) == "#" and not szInclude.split('"')[1] in szHeaderNameList:
            szHeaderNameList.append(szInclude.split('"')[1])

def getIncFromSrc(szSourceList,szHeaderNameList):
    for szSource in szSourceList:
        with open(szSource) as szCurSource:
            szTmpContent = szCurSource.readlines()
        szIncContent = getIncContent(szTmpContent)
        getIncNames(szIncContent, szHeaderNameList)

def getIncFromHeader(szHeaderNameList,szHeaderList,szHuntingZone):
    for szHeaderName in szHeaderNameList:
        szFoundHeader = False
        for szRoot,szDirs,szFiles in os.walk(szHuntingZone):
            for szFile in szFiles:
                if szHeaderName in os.path.join(szRoot,szFile) and os.path.basename(szHeaderName) == os.path.basename(os.path.join(szRoot,szFile)):
                    szFoundHeader = True
                    if not os.path.join(szRoot,szFile) in szHeaderList:
                        szHeaderList.append(os.path.join(szRoot,szFile))
        if not szFoundHeader:
            print szHeaderName + " is not found in " + szHuntingZone

###################################################################################################
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print szUsage1
        print szUsage2
        print szUsage3
        print szUsage4
        print szUsage5
        sys.exit(1)
        
    szTmp = sys.argv[1]
    szHuntingZone = sys.argv[2]
    
    szSourceList = []
    szHeaderNameList = []
    szHeaderList = []
    
    #if this is a directory, things are pretty straight forward
    if not isProject(szTmp):
        szCurWorkingDir = szTmp
        getDirSource(szCurWorkingDir, szSourceList)
    #if this is a project file, need to read the content and hunt for itemgroup
    else:
        szProjectFile = szTmp
        getProjectSource(szProjectFile, szSourceList, szHeaderList)
    for szHeader in szHeaderList:
        print szHeader
    
    #traverse source list, pushing headers to headers name list
    getIncFromSrc(szSourceList, szHeaderNameList)
    #traverse header name list, append found headers to header list with full path
    #remember to report those non-found headers, no exit needed, but information matters
    getIncFromHeader(szHeaderNameList,szHeaderList,szHuntingZone)
    getIncFromSrc(szHeaderList,szHeaderNameList)
    getIncFromHeader(szHeaderNameList,szHeaderList,szHuntingZone)
    #for szHeaderName in szHeaderNameList:
        #print szHeaderName
    #for szHeader in szHeaderList:
        #print szHeader

        