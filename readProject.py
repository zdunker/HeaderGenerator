#read in a vcxproj file and extract compile and include files
#<ClCompile >     and      <ClInclude >

# alongside the project file throwing in, two important lists should be pushed in as well
# one is the list contains c source file, the other is the list contains header files.
# attention: passing-in projects should be in absolute paths
import re
#template: <ClCompile Include="..\..\..\..\..\src\xercesc\validators\common\ContentLeafNameTypeVector.cpp" />

projectSourceFileSyntax = re.compile(r'<ClCompile Include="(.*?)"')
projectIncludeFileSyntax = re.compile(r'<ClInclude Include="(.*?)"')

def getFiles(projectFile, sourceList, headerList):
    with open(projectFile) as rf:
        projectContent = rf.readlines()
    for line in projectContent:
        if '<ClCompile Include=' in line:
            mo = projectSourceFileSyntax.search(line)
            sourceList.append(mo.group(1))
        elif '<ClInclude Include=' in line:
            mo = projectIncludeFileSyntax.search(line)
            headerList.append(mo.group(1))            


#Known side cases to be considered:
#    There are some sources or headers are included or excluded from certain build
#    In addition, some files are also included while customBuild option is on
#    During resource compiling, there are some additional include directories


#if __name__ == "__main__":
#    sourceList = []
#    headerList = []
#    getFiles(projectFile, sourceList, headerList)