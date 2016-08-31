##################################################################################################
# This is main file of HeaderGenerator
# Usage: HeaderGenerator.py -f (folder , solution file or project file) -d destination(optional)
##################################################################################################
import argparse
import re
import os

slnFileSyntax = re.compile(r'''Project(\(\S+\)) = \"(.*?)\", \"(.*?)\"''')#group2 contains location
projectSourceFileSyntax = re.compile(r'''<ClCompile Include="(.*?)"''')#group1 contains location
includeSyntax = re.compile(r'''^#include [<|"](.*?)[>|"]''')#group1 contains location
sourceSuffixList = ('.c','.cc','.cpp')

def getProjects(solutionFile):
    retList = []
    solutionDir = getFileDir(solutionFile)
    with open(solutionFile) as rf:
        szSlnContent = rf.readlines()
    for line in szSlnContent:
        if 'Project(' in line:
            mo = slnFileSyntax.search(line)
            if mo.group(3) and os.path.isfile(os.path.join(solutionDir,mo.group(3))):
                retList.append(os.path.normpath(os.path.join(solutionDir,mo.group(3))))
    return retList

def getFiles(projectFile):
    sourceList = []
    projectDir = getFileDir(projectFile)
    with open(projectFile) as rf:
        projectContent = rf.readlines()
    for line in projectContent:
        if '<ClCompile Include=' in line:
            mo = projectSourceFileSyntax.search(line)
            sourceList.append(os.path.normpath(os.path.join(projectDir,mo.group(1))))
    return sourceList

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

def getFileDir(szFile):
    return os.path.dirname(szFile)

def getSourceList(fileLocation):
    sourceList = []
    for root, dirs, files in os.walk(fileLocation):
        for file in files:
            if file.endswith(sourceSuffixList):
                sourceList.append(os.path.join(root,file))
    return sourceList

def getHeaderList(szSourceList):
    szHeaderList = []
    for source in szSourceList:
        szHeaderList += getHeaders(source, root)
    return list(set(szHeaderList))

def getProjectsSources(szProjectList):
    szSourcelist = []
    for project in szProjectList:
        szSourcelist += getFiles(project)
    szSourcelist = list(set(szSourcelist))
    return szSourcelist

#To use this recursive function: source you are passing in should be full path
#                                and the location you throw in should be the root directory
#                                a.k.a. the search interval this function will scan in
#                                I do not recommand general location like 'C:\'
def getHeaders(source, location,headerList = []):
    inputHeaderListLen = len(headerList)
    with open(source) as rf:
        sourceContent = rf.readlines()
    for line in sourceContent:
        mo  = includeSyntax.search(line)
        if mo:
            for root, dirs, files in os.walk(location):
                for file in files:
                    if os.path.normpath(mo.group(1)) in os.path.join(root, file) and not os.path.join(root, file) in headerList:
                        print "Appending : %s"%(os.path.join(root, file))
                        headerList.append(os.path.join(root, file))
    modifiedHeaderListLen = len(headerList)
    if modifiedHeaderListLen - inputHeaderListLen > 0:
        for i in range(len(headerList)):
            return getHeaders(headerList[i],location, headerList)
    elif modifiedHeaderListLen - inputHeaderListLen == 0:
        return headerList

def copyHeaders(szHeaderList, root, copyDestination):
    for header in szHeaderList:
        toWhere = os.path.join(copyDestination, os.path.relpath(header, root))
        if not os.path.exists(getFileDir(toWhere)):
            #os.mkdir(getFileDir(toWhere))
            dir = getFileDir(toWhere)
            batch = r'md %s'%(dir)
            os.system(batch)
        batch = r'copy %s %s'%(header, toWhere)
        os.system(batch)
        print batch
    print 'Done copying'

def folderOperation(fileLocation, root, copyDestination):
    szSourceList = getSourceList(fileLocation)
    szHeaderList = getHeaderList(szSourceList)
    copyHeaders(szHeaderList, root, copyDestination)

def solutionOperation(fileLocation, root, copyDestination):
    szProjectList = getProjects(fileLocation)
    szSourceList = getProjectsSources(szProjectList)
    szHeaderList = getHeaderList(szSourceList)
    copyHeaders(szHeaderList, root, copyDestination)

def projectOperation(fileLocation, root, copyDestination):
    szSourceList = getFiles(fileLocation)
    #normally a project shouldn't have duplicated C/C++ source files
    szHeaderList = getHeaderList(szSourceList)
    copyHeaders(szHeaderList, root, copyDestination)

def getArgs():
    parser = argparse.ArgumentParser(prog='HeaderGenerator', usage='%(prog)s [options]',
                                    description='Generate header files from input location/file')
    parser.add_argument('-f', dest='location', help='Specify file/folder location')
    parser.add_argument('-r', dest='root', help='Specify scanning root')
    parser.add_argument('-d', dest='destination', help='Specify where headers are copying to, if not specified, copy to current location')
    args = parser.parse_args()
    
    if not args.location or not args.root:
        print 'Invalid input'
        exit(-1)
    
    if args.destination:
        print 'Will copy headers to {}'.format(args.destination)
    
    return args.location, args.root, args.destination

def main(fileLocation, root, copyDestination):
    if isFolder(fileLocation):
        print "Performing folder operations"
        folderOperation(fileLocation, root, copyDestination)
    elif isSolution(fileLocation):
        print "Performing solution operations"
        solutionOperation(fileLocation, root, copyDestination)
    elif isProject(fileLocation):
        print "Performing project operations"
        projectOperation(fileLocation, root, copyDestination)
    else:
        print "%s does not fit in any scenario, stopping process..."%(fileLocation)
        exit(-1)

if __name__ == '__main__':
    fileLocation, root, copyDestination = getArgs()
    #if no destination is passed in, copy to current directory by default.
    if copyDestination == None:
        copyDestination = getFileDir(fileLocation)+'\\testInclude'
    print "Start"
    main(fileLocation, root, copyDestination)
    print "Finish"
    