import tarfile
import argparse
import os
import subprocess as sub

def sanityCheck(szRootPath, szPlatform, szTarVersion):
    if None in (szRootPath, szPlatform, szTarVersion):
        print 'Please check arguments is None. Exit'
        exit(-1)

    szTarFile       = os.path.join(szRootPath, 'zlib-' + szTarVersion + '.tar.gz')
    szBuildDir      = os.path.join(szRootPath, 'zlib-' + szTarVersion)
    szToPerforceDir = os.path.join(szRootPath, szPlatform)

    if not os.path.isfile(szTarFile):
        print 'Specified ZLib source path is not file: %s' % szTarFile
        exit(-1)

    #if os.path.isdir(szBuildDir):
    #    print 'Try to remove output directory: %s' % szBuildDir
    #    removeTree(szBuildDir)

    #if os.path.isdir(szToPerforceDir):
    #    print 'Try to remove submit directory: %s' % szToPerforceDir
    #    removeTree(szToPerforceDir)

    print 'Create build submit directory: %s' % szToPerforceDir
    os.mkdir(szToPerforceDir)

    return szTarFile, szBuildDir, szToPerforceDir 


def extractSource(szTarFile, toWhere, mode):
    try:
        print 'Extract source: %s' % szTarFile
        tar = tarfile.open(szTarFile, "r:gz")
        tar.extractall(toWhere+'.'+mode)
        tar.close()
    except:
        print "Extract source zip file exception, exit."
        exit(-1)

def modifyMakeFile(szBuildDir, mode, szBuildType):      #build type is dynamic or static
    szMakeFile = r'win32\Makefile.msc'
    szFileFullPath = os.path.join(szBuildDir,szMakeFile)
    
    oldASFlag = 'ASFLAGS = -coff -Zi $(LOC)'
    newASFlag = 'ASFLAGS = -safeseh -coff -Zi $(LOC)'
    
    s = open(szFileFullPath).read()
    s = s.replace(oldASFlag, newASFlag)
    
    if mode == 'release' and szBuildType == 'static':
        oldCFlag = 'CFLAGS  = -nologo -MD -W3 -O2 -Oy- -Zi -Fd"zlib" $(LOC)'
        newCFlag = 'CFLAGS  = -nologo -MT -W4 -GS -O2 -Oy- -Zi -Fd"zlib" $(LOC)'
        s = s.replace(oldCFlag, newCFlag)
    elif mode == 'debug':
        if szBuildType == 'dynamic':
            oldCFlag = 'CFLAGS  = -nologo -MD -W3 -O2 -Oy- -Zi -Fd"zlib" $(LOC)'
            newCFlag = 'CFLAGS  = -nologo -MDd -W4 -GS -Od -Oy- -Zi -Fd"zlib" $(LOC)'
            s = s.replace(oldCFlag, newCFlag)
        elif szBuildType == 'static':
            oldCFlag = 'CFLAGS  = -nologo -MD -W3 -O2 -Oy- -Zi -Fd"zlib" $(LOC)'
            newCFlag = 'CFLAGS  = -nologo -MTd -W4 -GS -Od -Oy- -Zi -Fd"zlib" $(LOC)'
            s = s.replace(oldCFlag, newCFlag)
            
    f = open(szFileFullPath, 'w')
    f.write(s)
    f.close()
    
def getMSVCTool(szPlatform):
    vcVersion = szPlatform.split('-')[2][-2:]
    guessToolPath = r'C:\Program Files (x86)\Microsoft Visual Studio {}.0\VC\vcvarsall.bat'.format(vcVersion)
    guessToolPath2 = r'C:\Program Files\Microsoft Visual Studio {}.0\VC\vcvarsall.bat'.format(vcVersion)
    if os.path.isfile(guessToolPath):
        return guessToolPath
    elif os.path.isdir(guessToolPath2):
        return guessToolPath2
    print "MSVC Tool not found on guessed path, exit."
    exit(-1)

def getToolArg(szPlatform):
    if 'x86' in szPlatform:
        return 'x86'
    elif 'x64' in szPlatform:
        return 'amd64'
    else:
        print 'Unable to retrieve argument from %s, exit.'%(szPlatform)
        exit(-1)

def getNMakeArg(mode, szPlatform):
    if 'x86' in szPlatform:
        if mode == 'debug':
            return r'LOC="-DASMV -DASMINF -D_DEBUG -I." OBJA="inffas32.obj match686.obj"'
        elif mode == 'release':
            return r'LOC="-DASMV -DASMINF -DNDEBUG -I." OBJA="inffas32.obj match686.obj"'
    elif 'x64' in szPlatform:
        if mode == 'debug':
            return r'AS=ml64 LOC="-DASMV -DASMINF -D_DEBUG -I." OBJA="inffasx64.obj gvmat64.obj inffas8664.obj"'
        elif mode == 'release':
            return r'AS=ml64 LOC="-DASMV -DASMINF -DNDEBUG -I." OBJA="inffasx64.obj gvmat64.obj inffas8664.obj"'
    else:
        print 'Unable to give argument to this mode, exit.'
        exit(-1)

def buildZlibByBuildType(szBuildDir, szPlatform, mode, szBuildType):
    szMSVCTool = getMSVCTool(szPlatform)
    modifyMakeFile(szBuildDir, mode, szBuildType)
        
    makefile  = r'win32\Makefile.msc'
    szToolArg = getToolArg(szPlatform)
    szMakeArg = getNMakeArg(mode,szPlatform)
    
    cmdline = ["cmd", "/q", "/k", "echo off"]
    conn = sub.Popen(cmdline, stdin=sub.PIPE,shell=True,cwd=szBuildDir)
    batch = b"""\
    call %s %s
    nmake -f %s %s
    
    exit
    """ % (szMSVCTool, szToolArg, makefile, szMakeArg)
    print "To build Zlib by command batch: %s" % batch   
    conn.stdin.write(batch)
    conn.stdin.flush() # Must include this to ensure data is passed to child process
    stdout, stderr = conn.communicate()
    
def copyAndRename(szBuildDir, szToPerforceDir, mode, szThreadType):
    targetFileList = ['zlib.lib','zlib1.dll','zlib.pdb','zlib1.pdb']
    destFileList   = ['zlib_' +szThreadType+'.lib',
                      'zlib1_'+szThreadType+'.dll',
                      'zlib_' +szThreadType+'.pdb',
                      'zlib1_'+szThreadType+'.pdb']
    if not os.path.isdir(os.path.join(szToPerforceDir,mode)):
        os.mkdir(os.path.join(szToPerforceDir,mode))
    for i in range(len(targetFileList)):
        fromWhere = os.path.join(szBuildDir,targetFileList[i])
        toWhere = os.path.join(os.path.join(szToPerforceDir,mode), destFileList[i])
        batch = 'copy %s %s'%(fromWhere, toWhere)
        try:
            os.system(batch)
        except:
            print 'Unable to copy %s, exit.'%(fromWhere)
            exit(-1)
    
def wipeBuild(szBuildDir):
    batch = 'rd /q /s %s'%(szBuildDir)
    try:
        os.system(batch)
    except:
        print 'Unable to wipe %s'%(szBuildDir)
        exit(-1)

def buildZlibByConfig(szTarFile, szBuildDir, szToPerforceDir, szPlatform, mode, szThreadType):
    extractSource(szTarFile, szBuildDir, mode)
    szBuildDirWithMode = szBuildDir + '.' + mode
    buildZlibByBuildType(szBuildDirWithMode, szPlatform, mode, szThreadType)
    copyAndRename(szBuildDir, szToPerforceDir, mode, szThreadType)
    wipeBuild(szBuildDir)

def getArgs():
    parser = argparse.ArgumentParser(prog='ZLibBuild', usage='%(prog)s [options]', description='Process ZLib build on Windows')
    parser.add_argument('-l', '--location', dest='location', help='Specify build location')
    parser.add_argument('-p', '--platform', dest='platform', help='Specify platform, like x86-win32-vc11')
    parser.add_argument('-v', '--version' , dest='version' , help='Specify ZLib version')
    args = parser.parse_args()

    if not args.location or not args.platform or not args.version:
        print 'Not enough arguments'
        exit(-1)
        
    return args.location, args.platform, args.version

def main(szRootPath, szPlatform, szTarVersion):
    szTarFile, szBuildDir, szToPerforceDir = sanityCheck(szRootPath, szPlatform, szTarVersion)
    buildZlibByConfig(szTarFile, szBuildDir, szToPerforceDir, szPlatform, 'debug'  , 'dynamic')
    buildZlibByConfig(szTarFile, szBuildDir, szToPerforceDir, szPlatform, 'debug'  , 'static' )
    buildZlibByConfig(szTarFile, szBuildDir, szToPerforceDir, szPlatform, 'release', 'dynamic')
    buildZlibByConfig(szTarFile, szBuildDir, szToPerforceDir, szPlatform, 'release', 'static' )

if __name__ == '__main__':
    print 'Start'
    szRootPath, szPlatform, szTarVersion = getArgs()
    main(szRootPath, szPlatform, szTarVersion)
    print 'Finished'