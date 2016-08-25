# a solution file comes in, a list of contained projects is expected to return

import re

#template below
#Project("{8BC9CEB8-8B4A-11D0-8D11-00A0C91BC942}") = "all", "all\all.vcxproj", "{E305E46C-9D74-4755-BF57-29DEAEF4DCDD}"
slnFileSyntax = re.compile('Project(\(\S+\)) = \"(.*?)\", \"(.*?)\"')

def getProjects(solutionFile):
    retList = []
    with open(solutionFile) as rf:
        szSlnContent = rf.readlines()
    for line in szSlnContent:
        if 'Project(' in line:
            mo = slnFileSyntax.search(line)
            if mo.group(3):
                retList.append(mo.group(3))
    return retList
