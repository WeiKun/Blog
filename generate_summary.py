#!/usr/bin/env python
# Author: weikun
# Created Time: Mon 25 Mar 2019 10:17:01 AM CST

f = open('SUMMARY.md', 'r+')
infos = f.readlines()
f.close()

dirs=[]
dirHash = {}
curDir = None
curDirName = None

for info in infos:
    info = info.strip('\n')
    if info.startswith('###'):
        curDir = []
        curDirName = info[info.find(' ') + 1:]
        dirs.append((curDirName, curDir))

    elif info.startswith('*'):
        name = info[info.find('[') + 1:info.find(']')]
        filePath = info[info.find('(') + 1:info.find(')')]
        curDir.append((name, filePath))
        if dirHash.get(filePath.split('/')[0], None) == None:
            dirHash[filePath.split('/')[0]] = (curDirName, curDir)


import os

def rebuildName(fileName):
    fileName = fileName[11:-3] #len(xxxx_xx_xx) = 11 len(.md) = 3
    fileName = fileName.replace('_', ' ')
    fileName = fileName.capitalize()
    return fileName

def checkRepeat(fileName, curDir):
    for name, fName in curDir:
        if fName == fileName:
            return False
    else:
        return True

for maindir, subdir, file_name_list in os.walk('.'):
    if not file_name_list:
        continue
    
    if '_book' in maindir:
        continue

    if not maindir.startswith('./'):
        continue

    for file_name in file_name_list:
        if not file_name.endswith('.md'):
            continue

        pathDirName = maindir[len('./'):]
        fileName = file_name
        if pathDirName in dirHash:
            curDirName, curDir = dirHash[pathDirName]
            if checkRepeat('%s/%s' % (pathDirName, fileName), curDir):
                name = rebuildName(fileName)
                curDir.append((name, '%s/%s' % (pathDirName, fileName)))
        else:
            curDirName = pathDirName.capitalize()
            curDir = []
            dirHash[pathDirName] = (curDirName, curDir)
            dirs.append((curDirName, curDir))
            name = rebuildName(fileName)
            curDir.append((name, '%s/%s' % (pathDirName, fileName)))

writeinfos = []
writeinfos.append('# Summary\n')
writeinfos.append('* [Introduction](README.md)\n')
for name, curDir in dirs:
    writeinfos.append('### %s\n' % (name))
    for d in curDir:
        writeinfos.append('* [%s](%s)' % (d[0], d[1]))
    writeinfos.append('\n')

f = open('SUMMARY.md', 'w+')
f.writelines('\n'.join(writeinfos))
f.close()
