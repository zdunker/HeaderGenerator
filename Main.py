##################################################################################################
# This is main file of HeaderGenerator
# Usage: HeaderGenerator.py -f (folder , solution file or project file) -d destination(optional)
##################################################################################################
import argparse

from utility import getFileDir

def getArgs():
    parser = argparse.ArgumentParser(prog='HeaderGenerator', usage='%(prog)s [options]',
                                    description='Generate header files from input location/file')
    parser.add_argument('-f', dest='location', help='Specify file/folder location')
    parser.add_argument('-d', dest='destination', help='Specify where headers are copying to, if not specified, copy to current location')
    args = parser.parse_args()
    
    if not args.location:
        print 'No file location told'
    
    if args.destination:
        print 'Will copy headers to {}'.format(args.destination)
    
    return args.location, args.destination

if __name__ == '__main__':
    fileLocation, copyDestination = getArgs()
    if copyDestination == None:
        copyDestination = getFileDir(fileLocation)