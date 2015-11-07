from ROOT import *
import ROOT as root
import os


def hadd(output, input):
    if not isinstance(input, list):
        raise TypeError, "hadd:  The input has to be a list."
    input  = " ".join([j for j in input])
    print "-------> Root hadd in progress. Output file: {0}".format(output)
    os.system("hadd -f %s %s" % (output,input))
    
