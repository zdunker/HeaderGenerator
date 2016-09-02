##################################################################################################
# This is main file of HeaderGenerator
# Usage: HeaderGenerator.py -f (folder , solution file or project file) -d destination(optional)
##################################################################################################
import argparse
import re
import os
import shutil
import time

slnFileSyntax = re.compile(r'''Project(\(\S+\)) = \"(.*?)\", \"(.*?)\"''')#group3 contains location
projectSourceFileSyntax = re.compile(r'''<ClCompile Include="(.*?)"''')#group1 contains location
includeSyntax = re.compile(r'''^#include [<|"](.*?)[>|"]''')#group1 contains location
sourceSuffixes = (".c",".cc",".cpp")

def getProjects(solutionFile):
    projectList = []
    solutionDir = os.path.dirname(solutionFile)
    
    if not os.path.exists(solutionFile):
        print "%s does not exits, exit"%(solutionFile)
        exit(-1)
    
    with open(solutionFile) as rf:
        slnContent = rf.readlines()
    for line in slnContent:
        if "Project(" in line:
            mo = slnFileSyntax.search(line)
            if os.path.exists(os.path.join(solutionDir,mo.group(3))):
                projectList.append(os.path.normpath(os.path.join(solutionDir,mo.group(3))))
            else:
                print "Notice: %s can not be found"%(os.path.join(solutionDir,mo.group(3)))
                
    return projectList

def getFiles(projectFile):
    sourceList = []
    projectDir = os.path.dirname(projectFile)
    
    if not os.path.exists(projectFile):
        print "%s does not exits, exit"%(projectFile)
        exit(-1)
    
    with open(projectFile) as rf:
        projectContent = rf.readlines()
    for line in projectContent:
        if "<ClCompile Include=" in line:
            mo = projectSourceFileSyntax.search(line)
            if os.path.exists(os.path.join(projectDir,mo.group(1))):
                sourceList.append(os.path.normpath(os.path.join(projectDir,mo.group(1))))
            else:
                print "Notice: %s can not be found"%(os.path.join(projectDir,mo.group(1)))
                
    return sourceList

def determineLocation(location, suffix=''):
    if not suffix:
        return os.path.isdir(location)
    else:
        return location.endswith(suffix)

def getSourceList(fileLocation):
    sourceList = []
    for root, dirs, files in os.walk(fileLocation):
        for file in files:
            if file.endswith(sourceSuffixes):
                sourceList.append(os.path.join(root,file))
    return sourceList

def getHeaderList(sourceList, root):
    headerList = []
    for source in sourceList:
        headerList += getHeaders(source, root)
    return list(set(headerList))

def getProjectsSources(projectList):
    sourcelist = []
    for project in projectList:
        sourcelist += getFiles(project)
    return list(set(sourcelist))

#To use this recursive function: source you are passing in should be full path
#                                and the location you throw in should be the root directory
#                                a.k.a. the search interval this function will scan in
#                                I do not recommand general location like 'C:\'
def getHeaders(source, location, headerList=[]):
    inputHeaderListLen = len(headerList)
    with open(source) as rf:
        sourceContent = rf.readlines()
    for line in sourceContent:
        mo  = includeSyntax.search(line)
        if mo:
            for root, dirs, files in os.walk(location):
                for file in files:
                    if (os.path.normpath(mo.group(1)) in os.path.join(root, file) and 
                        not os.path.join(root, file) in headerList):
                        print "Appending : %s"%(os.path.join(root, file))
                        headerList.append(os.path.join(root, file))
    modifiedHeaderListLen = len(headerList)
    if modifiedHeaderListLen - inputHeaderListLen > 0:
        for i in range(len(headerList)):
            return getHeaders(headerList[i],location, headerList)
    elif modifiedHeaderListLen - inputHeaderListLen == 0:
        return headerList

def copyHeaders(headerList, root, copyDestination):
    for header in headerList:
        toWhere = os.path.join(copyDestination, os.path.relpath(header, root))
        if not os.path.exists(os.path.dirname(toWhere)):
            os.makedirs(os.path.dirname(toWhere))
        shutil.copy2(header, toWhere)
    print "Done copying"

def folderOperation(fileLocation, root, copyDestination):
    sourceList = getSourceList(fileLocation)
    headerList = getHeaderList(sourceList, root)
    copyHeaders(headerList, root, copyDestination)

def solutionOperation(fileLocation, root, copyDestination):
    projectList = getProjects(fileLocation)
    sourceList  = getProjectsSources(projectList)
    headerList  = getHeaderList(sourceList, root)
    copyHeaders(headerList, root, copyDestination)

def projectOperation(fileLocation, root, copyDestination):
    sourceList = getFiles(fileLocation)
    #normally a project shouldn't have duplicated C/C++ source files
    headerList = getHeaderList(sourceList, root)
    copyHeaders(headerList, root, copyDestination)

def getArgs():
    parser = argparse.ArgumentParser(prog="HeaderGenerator", usage="%(prog)s [options]",
                                    description="Generate header files from input location/file")
    
    parser.add_argument("-f",  dest="location",    help="Specify file/folder location")
    parser.add_argument("-r",  dest="root",        help="Specify scanning root")
    parser.add_argument("-d",  dest="destination", help="Specify where headers are copying to, if not specified, copy to current location")
    args = parser.parse_args()
    
    if not args.location or not args.root:
        print 'Invalid input'
        exit(-1)
    
    if args.destination:
        print 'Will copy headers to {}'.format(args.destination)
    
    return args.location, args.root, args.destination

def main(fileLocation, root, copyDestination):
    if determineLocation(fileLocation):
        print "Performing folder operations"
        folderOperation(fileLocation, root, copyDestination)
        
    elif determineLocation(fileLocation, ".sln"):
        print "Performing solution operations"
        solutionOperation(fileLocation, root, copyDestination)
        
    elif determineLocation(fileLocation, ".vcxproj"):
        print "Performing project operations"
        projectOperation(fileLocation, root, copyDestination)
        
    else:
        print "%s does not fit in any scenario, exit"%(fileLocation)
        exit(-1)

if __name__ == '__main__':
    fileLocation, root, copyDestination = getArgs()
    #if no destination is passed in, copy to current directory by default.
    if copyDestination == None:
        copyDestination = os.path.dirname(fileLocation)+'\\testInclude'
    startTime = time.time()
    print "Start"
    main(fileLocation, root, copyDestination)
    print "Finish"
    print time.time() - startTime