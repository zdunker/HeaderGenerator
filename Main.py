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
includeSyntax = re.compile(r'''^#include (\S+)''')#group1 contains location
sourceSuffixes = (".c",".cc",".cpp")
standardHeaderClosings = ('"','>')

# return a list of projects from reading solution file
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
            matchedObject = slnFileSyntax.search(line)
            if os.path.exists(os.path.join(solutionDir,matchedObject.group(3))):
                projectList.append(os.path.normpath(os.path.join(solutionDir,matchedObject.group(3))))
            else:
                print "Notice: %s can not be found"%(os.path.join(solutionDir,matchedObject.group(3)))
                
    return projectList

#return a list of source files from reading project file
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
            matchedObject = projectSourceFileSyntax.search(line)
            if os.path.exists(os.path.join(projectDir,matchedObject.group(1))):
                sourceList.append(os.path.normpath(os.path.join(projectDir,matchedObject.group(1))))
            else:
                print "Notice: %s can not be found"%(os.path.join(projectDir,matchedObject.group(1)))
                
    return sourceList

# determine user-defined location is a folder or a certain type of file
def determineLocation(location, suffix=''):
    if not suffix:
        return os.path.isdir(location)
    else:
        return location.endswith(suffix)

# this function executes only if user threw in a folder, it's hard to tell which source to compile
# so just push every source file to list, suggestions are welcome
def getSourceList(fileLocation):
    sourceList = []
    for root, dirs, files in os.walk(fileLocation):
        for file in files:
            if file.endswith(sourceSuffixes):
                sourceList.append(os.path.join(root,file))
    return sourceList

# return a list of headers
def getHeaderList(sourceList, root):
    headerList = []
    for source in sourceList:
        getHeaders(source, root, headerList)
    return list(set(headerList))

# this function is an extra step for solution file only, return a list of projects
def getProjectsSources(projectList):
    sourcelist = []
    for project in projectList:
        sourcelist += getFiles(project)
    return list(set(sourcelist))

# read source file and use what's after #include to find headers
# check depth 1 and 2 of referenced headers, and push distinct headers into list
def getHeaders(source, location, headerList=[], level = 0):
    level += 1
    with open(source) as rf:
        sourceContent  = rf.readlines()
    for line in sourceContent:
        mo = includeSyntax.search(line)
        if mo and (mo.group(1))[-1] in standardHeaderClosings:
            # clean up mo.group(1)
            targetHeader = mo.group(1)[1:len(mo.group(1))-1]
            # standard ratio
            for root, dirs, files in os.walk(location):
                for file in files:
                    if (os.path.normpath(targetHeader) in os.path.join(root, file) and
                        not os.path.join(root, file) in headerList):
                        print "Appending : %s"%(os.path.join(root, file))
                        headerList.append(os.path.join(root, file))
                        # end on depth 2
                        if level < 2:
                            getHeaders(os.path.join(root, file), location, headerList, level)
        elif mo and not (mo.group(1))[-1] in standardHeaderClosings:
            # macro ratio
            # developing
            print "%s might be a macro..."%(mo.group(1))
            
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

def errorCommandProtector(sleepSeconds):
    while sleepSeconds > 0:    
        print "If not as expected, please interrupt in %d seconds"%(sleepSeconds)
        sleepSeconds -= 1
        sleep(1)

# three arguments are required, location is the input folder/file
#                               root is the directory tells automation where to start looking for headers
#                               destination is the directory where headers are copying to
# root argument is an ugly one, any suggestion can help get rid of it is welcome
def getArgs():
    parser = argparse.ArgumentParser(prog="HeaderGenerator", usage="%(prog)s [options]",
                                    description="Generate header files from input location/file")
    
    parser.add_argument("-f",  dest="location",    help="Specify file/folder location")
    parser.add_argument("-r",  dest="root",        help="Specify scanning root")
    parser.add_argument("-d",  dest="destination", help="Specify where headers are copying to, if not specified, copy to current location")
    args = parser.parse_args()
    
    if not args.location or not args.root:
        print "Invalid input"
        exit(-1)
    
    if args.destination:
        print "Will copy headers to %s"%(args.destination)
    if not args.destination:
        print "Will copy headers to %s\\testInclude"%(args.location)
        errorCommandProtector(5)
    
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
        print "%s file type not supported, exit"%(fileLocation)
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