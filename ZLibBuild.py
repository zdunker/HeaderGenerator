import tarfile
import argparse
import os
import subprocess as sub
import win32api

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

    print 'Create build submit directory: %s' % szToPerforceDir
    os.mkdir(szToPerforceDir)

    return szTarFile, szBuildDir, szToPerforceDir 


def extractSource(szTarFile, toWhere, mode):
    toWhere = toWhere+'.'+mode
    try:
        print 'Extracting source: %s to %s' % (szTarFile, toWhere)
        tar = tarfile.open(szTarFile)
        tar.extractall(toWhere)
        tar.close()
    except:
        print "Extract source zip file exception, exit."
        exit(-1)

def modifyMakeFile(szBuildDir, mode, szBuildType):      #build type is dynamic or static
    szMakeFile = r'win32\Makefile.msc'
    szToFile = r'win32\MakefileCM.msc'
    szFileFullPath = os.path.join(szBuildDir,szMakeFile)
    szFileFullPath2 = os.path.join(szBuildDir,szToFile)
    
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
            
    f = open(szFileFullPath2, 'w')
    f.write(s)
    f.close()
    print 'File created: %s'%(szFileFullPath2)
    
def getVcShortPath(arg_platform):
    fileList = []
    vc_long_path = None
    if "x86" in arg_platform: 
        fileList = getLongPath("vcvars32.bat", r"C:\\Program Files")
        if len(fileList) == 0 : 
            fileList = getLongPath("vcvars32.bat", r"C:\\Program Files (x86)")

    if "x64" in arg_platform: 
        fileList = getLongPath("vcvars64.bat", r"C:\\Program Files (x86)")
    
    #Parse vc version from platform, like x86-win32-vc11
    vc_version = arg_platform.split('-')[2][-2:]
    for path in fileList:
        if ("Visual Studio " + vc_version) in path: 
            vc_long_path = path 
            print "VC long path is: %s" % vc_long_path
            break

    if vc_long_path is not None:
        return getShortPath(vc_long_path)
    else: 
        print "Can not find the required VC path. Exit"
        exit(-1)


#Note: search in C:\ could be very long time, suggest to specify root_dir
def getLongPath(file_name, root_dir = r'c:\\'): 
    fileList = []
    for root, dirs, files in os.walk(root_dir):
        for name in files:
            if name == file_name:
                fileList.append(os.path.join(root, name))
    return fileList

def getShortPath(long_file_name):
    return win32api.GetShortPathName(long_file_name)

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
    szVCPath = os.path.splitext(getVcShortPath(szPlatform))[0]
    modifyMakeFile(szBuildDir, mode, szBuildType)
        
    makefile  = r'win32\MakefileCM.msc'
    szMakeArg = getNMakeArg(mode,szPlatform)
    
    cmdline = ["cmd", "/q", "/k", "echo off"]
    conn = sub.Popen(cmdline, stdin=sub.PIPE,shell=True,cwd=szBuildDir)
    batch = b"""\
    call %s
    nmake -f %s %s
    
    exit
    """ % (szVCPath, makefile, szMakeArg)
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
    if not os.path.isdir(os.path.join(szToPerforceDir,mode+'\\lib')):
        batch = 'md %s'%(os.path.join(szToPerforceDir,mode+'\\lib'))
        os.system(batch)
    for i in range(len(targetFileList)):
        fromWhere = os.path.join(szBuildDir,targetFileList[i])
        toWhere = os.path.join(os.path.join(szToPerforceDir,mode+'\\lib'), destFileList[i])
        batch = 'copy %s %s'%(fromWhere, toWhere)
        try:
            print batch
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

def copyHeaders(szBuildDirWithMode,szToPerforceDir):
    headers = ['zlib.h','zconf.h']
    if os.path.isdir(os.path.join(szToPerforceDir,'include')):
        #headers already copied
        return
    batch = 'md %s'%(os.path.join(szToPerforceDir,'include'))
    os.system(batch)
    for header in headers:
        szHeaderInSource = os.path.join(szBuildDirWithMode, header)
        szHeaderToPerforce = os.path.join(szToPerforceDir,'include')
        batch = 'copy %s %s'%(szHeaderInSource, szHeaderToPerforce)
        print batch
        os.system(batch)

def buildZlibByConfig(szTarFile, szBuildDir, szToPerforceDir, szPlatform, mode, szThreadType):
    extractSource(szTarFile, szBuildDir, mode)
    szBuildDirWithMode = szBuildDir + '.' + mode
    copyHeaders(szBuildDirWithMode,szToPerforceDir)
    buildZlibByBuildType(szBuildDirWithMode, szPlatform, mode, szThreadType)
    copyAndRename(szBuildDirWithMode, szToPerforceDir, mode, szThreadType)
    wipeBuild(szBuildDirWithMode)

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
