
###python efficiencyFactors_plestina_width.py --dir=/scratch/osghpc/dsperka/Analyzer/SubmitArea_8TeV/Trees_HZZFiducialSamples_Nov22/ --obsName=mass4l --obsBins="|105.0|140.0|" -l -q -b --modelName=SM
import sys, os, string, re, pwd, commands, ast, optparse, shlex, time
from array import array
from math import *
from decimal import *
import pprint
global sample_shortnames
#from sample_shortnames_width import *
from sample_shortnames import *

from lib.util.Logger import *
from lib.util.UniversalConfigParser import UniversalConfigParser
from lib.plotting.RootPlotters import SimplePlotter

grootargs = []
def callback_rootargs(option, opt, value, parser):
    grootargs.append(opt)

### Define function for parsing options
def parseOptions():

    global opt, args, runAllSteps

    usage = ('usage: %prog [options]\n'
             + '%prog -h for help')
    parser = optparse.OptionParser(usage)

    # input options
    parser.add_option('-d', '--dir',    dest='SOURCEDIR',  type='string',default='./', help='run from the SOURCEDIR as working area, skip if SOURCEDIR is an empty string')
    parser.add_option('',   '--obsName',dest='OBSNAME',    type='string',default='',   help='Name of the observalbe, supported: "mass4l", "pT4l", "massZ2", "rapidity4l", "cosThetaStar", "nets_reco_pt30_eta4p7"')
    parser.add_option('',   '--obsBins',dest='OBSBINS',    type='string',default='',   help='Bin boundaries for the diff. measurement separated by "|", e.g. as "|0|50|100|", use the defalut if empty string')
    parser.add_option('-f', '--doFit', action="store_true", dest='DOFIT', default=False, help='doFit, default false')
    parser.add_option('-p', '--doPlots', action="store_true", dest='DOPLOTS', default=False, help='doPlots, default false')
    parser.add_option('-g', '--generate',    dest='GENERATE_N',  type='float',default=0, help='Generate <N> events and use as fitting dataset.')
    parser.add_option('-s', '--finalState',dest='FINAL_STATE',    type='string', default='',   help='Comma separated list of final states, e.g. 2e2mu,2mu2e,4e,4mu Default: none')
    parser.add_option('', '--doDatasets', action="store_true", dest='DO_DATASETS', default=False, help='Creates datasets and stores them to a workspace, default false')
    parser.add_option('',   '--closureParams',dest='CLOSURE_TEST',    type='string',default='',   help='Provide parametrization dictionary (cfg file, e.g. YAML).')
    parser.add_option('', '--doClosure', action="store_true", dest='DOCLOSURE', default=False, help='doPlots, default false')
    parser.add_option("-l",action="callback",callback=callback_rootargs)
    parser.add_option("-q",action="callback",callback=callback_rootargs)
    parser.add_option("-b",action="callback",callback=callback_rootargs)

    # store options and arguments as global variables
    global opt, args
    (opt, args) = parser.parse_args()

# parse the arguments and options
global opt, args, runAllSteps
parseOptions()
sys.argv = grootargs

doFit = opt.DOFIT
doPlots = opt.DOPLOTS

if (not os.path.exists("plots") and doPlots):
    os.system("mkdir plots")

from ROOT import *
from LoadData_dsperka_DCB_parameters import *
LoadData(opt.SOURCEDIR)
save = ""

RooMsgService.instance().setGlobalKillBelow(RooFit.WARNING)

if (opt.DOPLOTS and os.path.isfile('tdrStyle.py')):
    from tdrStyle import setTDRStyle
    setTDRStyle()



class SignalSpectrumFitter(object):
    """Calculating the efficiencies, acceptances.
    Fitting of the m4l distribution.
    Plotting components for the cross section study.
    """
    def __init__(self,channel=None, List=None, m4l_bins=None, m4l_low=None, m4l_high=None, obs_reco=None, obs_gen=None, obs_bins=None, recobin=None, genbin=None):
        """Basic definitin, initializtion"""
        self.log = Logger().getLogger(self.__class__.__name__, 10)
        self.pp = pprint.PrettyPrinter(indent=4)
        self.DEBUG = True
        #Class data
        self.channel = channel
        self.List = List
        self.m4l_bins = m4l_bins
        self.m4l_low = m4l_low
        self.m4l_high = m4l_high
        self.obs_reco = obs_reco
        self.obs_gen = obs_gen
        self.obs_bins = obs_bins
        self.recobin = recobin
        self.genbin = genbin
        self.use_dataset_from_ws = False
        self.chi_square_values = [] #list of (mH, chiSqare) points

    def __repr__(self):
        return 'SignalSpectrumFitter(channel=%s, List=%s, m4l_bins=%s, m4l_low=%s, m4l_high=%s, obs_reco=%s, obs_gen=%s, obs_bins=%s, recobin=%s, genbin=%s)' % (self.channel, self.List, self.m4l_bins, self.m4l_low, self.m4l_high, self.obs_reco, self.obs_gen, self.obs_bins, self.recobin, self.genbin)

    def set_samples(self,samples):
        """Provide a list of samples as type(list) or one as string"""
        samples_list = []
        if type(samples)==str:
            samples_list.append(samples)
            self.log.info("Added one samples to the list: {0}".format(samples))
        self.List = samples_list
        self.log.debug("Listof samples: self.List = {0}".format(self.List))

    def datasets_exists(self, exists):
        """
        If set, the RooDataSet from a workspace is expected.
        """
        self.use_dataset_from_ws = exists


    def _draw_CMS_label(self, canv, label = 'Simulation', x=0.22, y=0.85):
        """
        Adds CMS to the canvas 'canv' and bellow adds 'label' bellow.
        """
        latex2 = TLatex()
        latex2.SetNDC()
        latex2.SetTextSize(0.6*canv.GetTopMargin())
        latex2.SetTextFont(62)
        latex2.SetTextAlign(11) # align right
        latex2.DrawLatex(x, y, "CMS")
        latex2.SetTextSize(0.4*canv.GetTopMargin())
        latex2.SetTextFont(52)
        latex2.SetTextAlign(11)
        latex2.DrawLatex(x, y-0.05, "Simulation")


    def _set_cuts(self,channel=None, Sample=None):
        """Setup selection of different components with string cuts used normally by ROOT."""
        if channel == None: channel = self.channel
        if Sample == None: Sample = self.Sample


        self.recoweight = "eventMCWeight"
        #self.recoweight = "totalWeight"
        #self.recoweight = "1.0"


        self.obs_reco_low = self.obs_bins[self.recobin]
        self.obs_reco_high = self.obs_bins[self.recobin+1]

        self.obs_gen_low = self.obs_bins[self.genbin]
        self.obs_gen_high = self.obs_bins[self.genbin+1]

        self.obs_gen_lowest = self.obs_bins[0]
        self.obs_gen_highest = self.obs_bins[len(self.obs_bins)-1]

        self.cut_2e2mu_ord= '(abs(idL1)==abs(idL2) && abs(idL3)==abs(idL4) && (abs(idL1)==11 && abs(idL3)==13))'
        self.cut_2mu2e_ord= '(abs(idL1)==abs(idL2) && abs(idL3)==abs(idL4) && (abs(idL1)==13 && abs(idL3)==11))'

        self.cutobs_reco = "("+self.obs_reco+">="+str(self.obs_reco_low)+" && "+self.obs_reco+"<"+str(self.obs_reco_high)+")"
        self.cutobs_gen = "("+self.obs_gen+">="+str(self.obs_gen_low)+" && "+self.obs_gen+"<"+str(self.obs_gen_high)+")"
        if (("jet" in opt.OBSNAME) or ("Jet" in opt.OBSNAME)):
            self.cutobs_reco_jesup = "("+self.obs_reco+"_jesup"+">="+str(self.obs_reco_low)+" && "+self.obs_reco+"_jesup"+"<"+str(self.obs_reco_high)+")"
            self.cutobs_reco_jesdn = "("+self.obs_reco+"_jesdn"+">="+str(self.obs_reco_low)+" && "+self.obs_reco+"_jesdn"+"<"+str(self.obs_reco_high)+")"

        self.cutobs_gen_otherfid = "(("+self.obs_gen+"<"+str(self.obs_gen_low)+" && "+self.obs_gen+">="+str(self.obs_gen_lowest)+") || ("+self.obs_gen+">="+str(self.obs_gen_high)+" && "+self.obs_gen+"<="+str(self.obs_gen_highest)+"))"
        #cutm4l_gen     = "(GENmZ1Z2>"+str(self.m4l_low)+" && GENmZ1Z2<"+str(self.m4l_high)+")"
        self.cutm4l_gen     = "(GENmZ1Z2>"+str(self.m4l_low)+" && GENmZ1Z2<"+str(self.m4l_high)+")"
        self.cutm4l_reco    = "(mass4l>"+str(self.m4l_low)+" && mass4l<"+str(self.m4l_high)+")"

        if (channel == "4l"):
            self.cutchan_gen      = "((abs(GENidLS3[GENlepIndex1])==11 || abs(GENidLS3[GENlepIndex1])==13) && (abs(GENidLS3[GENlepIndex3])==11 || abs(GENidLS3[GENlepIndex3])==13))"
            self.cutchan_gen_out  = "((Z1daughtersId==11 || Z1daughtersId==13) && (Z2daughtersId==11 || Z2daughtersId==13))"
            #self.cutm4l_gen       = "(GENmZ1Z2>"+str(self.m4l_low)+" && GENmZ1Z2<"+str(self.m4l_high)+" && @GENidLS3.size()==4)"
            #self.cutm4l_reco      = "(mass4l>"+str(self.m4l_low)+" && mass4l<"+str(self.m4l_high)+" && nextraLep==0)"
            self.cutm4l_gen       = "(GENmZ1Z2>"+str(self.m4l_low)+" && GENmZ1Z2<"+str(self.m4l_high)+")"
            self.cutm4l_reco      = "(mass4l>"+str(self.m4l_low)+" && mass4l<"+str(self.m4l_high)+")"
        if (channel == "4e"):
            self.cutchan_gen      = "(abs(GENidLS3[GENlepIndex1])==11 && abs(GENidLS3[GENlepIndex3])==11)"
            self.cutchan_gen_out  = "(Z1daughtersId==11 && Z2daughtersId==11)"
            #self.cutm4l_gen       = "(GENmZ1Z2>"+str(self.m4l_low)+" && GENmZ1Z2<"+str(self.m4l_high)+" && @GENidLS3.size()==4)"
            #self.cutm4l_reco      = "(mass4e>"+str(self.m4l_low)+" && mass4e<"+str(self.m4l_high)+" && nextraLep==0)"
            self.cutm4l_gen       = "(GENmZ1Z2>"+str(self.m4l_low)+" && GENmZ1Z2<"+str(self.m4l_high)+")"
            self.cutm4l_reco      = "(mass4e>"+str(self.m4l_low)+" && mass4e<"+str(self.m4l_high)+")"
        if (channel == "4mu"):
            self.cutchan_gen      = "(abs(GENidLS3[GENlepIndex1])==13 && abs(GENidLS3[GENlepIndex3])==13)"
            self.cutchan_gen_out  = "(Z1daughtersId==13 && Z2daughtersId==13)"
            #self.cutm4l_gen       = "(GENmZ1Z2>"+str(self.m4l_low)+" && GENmZ1Z2<"+str(self.m4l_high)+" && @GENidLS3.size()==4)"
            #self.cutm4l_reco      = "(mass4mu>"+str(self.m4l_low)+" && mass4mu<"+str(self.m4l_high)+" && nextraLep==0)"
            self.cutm4l_gen       = "(GENmZ1Z2>"+str(self.m4l_low)+" && GENmZ1Z2<"+str(self.m4l_high)+")"
            self.cutm4l_reco      = "(mass4mu>"+str(self.m4l_low)+" && mass4mu<"+str(self.m4l_high)+")"
        if (channel == "2e2mu_inclusive"):
            #self.cutchan_gen      = "(abs(abs(GENidLS3[GENlepIndex1])-abs(GENidLS3[GENlepIndex3]))==2)"
            #self.cutchan_gen_out  = "(abs(Z1daughtersId-Z2daughtersId)==2)"
            self.cutchan_gen      = "((abs(GENidLS3[GENlepIndex1])==11 && abs(GENidLS3[GENlepIndex3])==13) || (abs(GENidLS3[GENlepIndex1])==13 && abs(GENidLS3[GENlepIndex3])==11))"
            self.cutchan_gen_out  = "((Z1daughtersId==11 && Z2daughtersId==13) || (Z1daughtersId==13 && Z2daughtersId==11))"
            #self.cutm4l_gen       = "(GENmZ1Z2>"+str(self.m4l_low)+" && GENmZ1Z2<"+str(self.m4l_high)+" && @GENidLS3.size()==4)"
            #self.cutm4l_reco      = "(mass2e2mu>"+str(self.m4l_low)+" && mass2e2mu<"+str(self.m4l_high)+" && nextraLep==0)"
            self.cutm4l_gen       = "(GENmZ1Z2>"+str(self.m4l_low)+" && GENmZ1Z2<"+str(self.m4l_high)+")"
            self.cutm4l_reco      = "(mass2e2mu>"+str(self.m4l_low)+" && mass2e2mu<"+str(self.m4l_high)+")"

        if (channel == "2e2mu"):
            #self.cutchan_gen      = "(abs(abs(GENidLS3[GENlepIndex1])-abs(GENidLS3[GENlepIndex3]))==2)"
            #self.cutchan_gen_out  = "(abs(Z1daughtersId-Z2daughtersId)==2)"
            self.cutchan_gen      = "((abs(GENidLS3[GENlepIndex1])==11 && abs(GENidLS3[GENlepIndex3])==13))"
            self.cutchan_gen_out  = "(Z1daughtersId==11 && Z2daughtersId==13)"
            #self.cutm4l_gen       = "(GENmZ1Z2>"+str(self.m4l_low)+" && GENmZ1Z2<"+str(self.m4l_high)+" && @GENidLS3.size()==4)"
            #self.cutm4l_reco      = "(mass2e2mu>"+str(self.m4l_low)+" && mass2e2mu<"+str(self.m4l_high)+" && nextraLep==0)"
            self.cutm4l_gen       = "(GENmZ1Z2>"+str(self.m4l_low)+" && GENmZ1Z2<"+str(self.m4l_high)+")"
            self.cutm4l_reco      = "(mass2e2mu>"+str(self.m4l_low)+" && mass2e2mu<"+str(self.m4l_high)+") && ((Z1daughtersId==11 && Z2daughtersId==13) || (abs(idL1)==abs(idL2) && abs(idL3)==abs(idL4) && (abs(idL1)==11 && abs(idL3)==13)))"
            #self.cutm4l_reco      = "(mass2e2mu>"+str(self.m4l_low)+" && mass2e2mu<"+str(self.m4l_high)+") && (Z1daughtersId==11 && Z2daughtersId==13)"
            #self.cutm4l_reco      = "(mass2e2mu>"+str(self.m4l_low)+" && mass2e2mu<"+str(self.m4l_high)+")"
        if (channel == "2mu2e"):
            #self.cutchan_gen      = "(abs(abs(GENidLS3[GENlepIndex1])-abs(GENidLS3[GENlepIndex3]))==2)"
            #self.cutchan_gen_out  = "(abs(Z1daughtersId-Z2daughtersId)==2)"
            self.cutchan_gen      = "((abs(GENidLS3[GENlepIndex1])==13 && abs(GENidLS3[GENlepIndex3])==11))"
            self.cutchan_gen_out  = "((Z1daughtersId==13 && Z2daughtersId==11))"
            #self.cutm4l_gen       = "(GENmZ1Z2>"+str(self.m4l_low)+" && GENmZ1Z2<"+str(self.m4l_high)+" && @GENidLS3.size()==4)"
            #self.cutm4l_reco      = "(mass2e2mu>"+str(self.m4l_low)+" && mass2e2mu<"+str(self.m4l_high)+" && nextraLep==0)"
            self.cutm4l_gen       = "(GENmZ1Z2>"+str(self.m4l_low)+" && GENmZ1Z2<"+str(self.m4l_high)+")"
            self.cutm4l_reco      = "(mass2e2mu>"+str(self.m4l_low)+" && mass2e2mu<"+str(self.m4l_high)+") && ((Z1daughtersId==13 && Z2daughtersId==11) || (abs(idL1)==abs(idL2) && abs(idL3)==abs(idL4) && (abs(idL1)==13 && abs(idL3)==11)))"
            #self.cutm4l_reco      = "(mass2e2mu>"+str(self.m4l_low)+" && mass2e2mu<"+str(self.m4l_high)+") && (Z1daughtersId==13 && Z2daughtersId==11)"
            #self.cutm4l_reco      = "(mass2e2mu>"+str(self.m4l_low)+" && mass2e2mu<"+str(self.m4l_high)+")"



        self.cuth4l_gen  = "(GENisfromHLS3[GENlepIndex1]==1 && GENisfromHLS3[GENlepIndex2]==1 && GENisfromHLS3[GENlepIndex3]==1 && GENisfromHLS3[GENlepIndex4]==1)"
        self.cuth4l_reco = "(isFromH_L1==1 && MomID_L1==23 && isFromH_L2==1 && MomID_L2==23 && isFromH_L3==1 && MomID_L3==23 && isFromH_L4==1 && MomID_L4==23)"
        if (("ZG" in Sample) or ("GG" in Sample)):
            self.cuth4l_gen = "(passedFiducialTopology==1)"

        self.cutnoth4l_gen  = "(!"+self.cuth4l_gen+")"
        self.cutnoth4l_reco = "(!"+self.cuth4l_reco+")"

        if Sample.startswith("ZH"):
            if (channel == "4l"):
                self.cutchan_gen_out  = "((Z1momId==25 && Z2momId==25 && (Z1daughtersId==11 || Z1daughtersId==13) && (Z2daughtersId==11 || Z2daughtersId==13)) || (Z1momId==25 && Z3momId==25 && (Z1daughtersId==11 || Z3daughtersId==13) && (Z3daughtersId==11 || Z3daughtersId==13)) || (Z2momId==25 && Z3momId==25 && (Z2daughtersId==11 || Z2daughtersId==13) && (Z3daughtersId==11 || Z3daughtersId==13)))"
            if (channel == "4e"):
                self.cutchan_gen_out  = "((Z1momId==25 && Z2momId==25 && Z1daughtersId==11 && Z2daughtersId==11) || (Z1momId==25 && Z3momId==25 && Z1daughtersId==11 && Z3daughtersId==11) || (Z2momId==25 && Z3momId==25 && Z2daughtersId==11 && Z3daughtersId==11))"
            if (channel == "4mu"):
                self.cutchan_gen_out  = "((Z1momId==25 && Z2momId==25 && Z1daughtersId==13 && Z2daughtersId==13) || (Z1momId==25 && Z3momId==25 && Z1daughtersId==13 && Z3daughtersId==13) || (Z2momId==25 && Z3momId==25 && Z2daughtersId==13 && Z3daughtersId==13))"
            if (channel == "2e2mu_inclusive"):
                self.cutchan_gen_out  = "((Z1momId==25 && (Z1daughtersId==11 || Z1daughtersId==13) && Z2momId==25 && (Z2daughtersId==11 || Z2daughtersId==13) && Z1daughtersId!=Z2daughtersId) || (Z1momId==25 && (Z1daughtersId==11 || Z1daughtersId==13) && Z3momId==25 && (Z3daughtersId==11 || Z3daughtersId==13) && Z1daughtersId!=Z3daughtersId) || (Z2momId==25 && (Z2daughtersId==11 || Z2daughtersId==13) && Z3momId==25 && (Z3daughtersId==11 || Z3daughtersId==13) && Z2daughtersId!=Z3daughtersId))"
                #WARNING WARNING fix cuts below
            if (channel == "2e2mu"):
                self.cutchan_gen_out  = "((Z1momId==25 && (Z1daughtersId==11 || Z1daughtersId==13) && Z2momId==25 && (Z2daughtersId==11 || Z2daughtersId==13) && Z1daughtersId!=Z2daughtersId) || (Z1momId==25 && (Z1daughtersId==11 || Z1daughtersId==13) && Z3momId==25 && (Z3daughtersId==11 || Z3daughtersId==13) && Z1daughtersId!=Z3daughtersId) || (Z2momId==25 && (Z2daughtersId==11 || Z2daughtersId==13) && Z3momId==25 && (Z3daughtersId==11 || Z3daughtersId==13) && Z2daughtersId!=Z3daughtersId))"
            if (channel == "2mu2e"):
                self.cutchan_gen_out  = "((Z1momId==25 && (Z1daughtersId==11 || Z1daughtersId==13) && Z2momId==25 && (Z2daughtersId==11 || Z2daughtersId==13) && Z1daughtersId!=Z2daughtersId) || (Z1momId==25 && (Z1daughtersId==11 || Z1daughtersId==13) && Z3momId==25 && (Z3daughtersId==11 || Z3daughtersId==13) && Z1daughtersId!=Z3daughtersId) || (Z2momId==25 && (Z2daughtersId==11 || Z2daughtersId==13) && Z3momId==25 && (Z3daughtersId==11 || Z3daughtersId==13) && Z2daughtersId!=Z3daughtersId))"



    def _prepare_datasets(self, Sample, channel, massHiggs):
        """
        Extract RooDataSet from a tree with given cuts for given final state.
        """
        self.log.info('Extracting RooDataSet: sample={0}, channel={1}, MH={2}'.format(Sample, channel, int(massHiggs)) )

        if (not Sample in TreesPassedEvents): return
        if (not TreesPassedEvents[Sample]): return

        self._set_cuts(channel, Sample)

        self.rrv_recoweight = RooRealVar(self.recoweight, self.recoweight, 0.0, 10.0)

        if (self.recoweight=="totalWeight"): genweight = "19712.0*scaleWeight/"+str(nEvents[Sample])
        else: genweight = "1.0"


        if (self.obs_reco.startswith('abs')):
            self.obs_reco_noabs = self.obs_reco.replace('abs(','').replace(')','')
            observable = RooRealVar(self.obs_reco_noabs, self.obs_reco_noabs, -1.0*max(float(self.obs_reco_high), float(self.obs_gen_high)), max(float(self.obs_reco_high), float(self.obs_gen_high)))
        else:
            observable = RooRealVar(self.obs_reco, self.obs_reco, max(float(self.obs_reco_low), float(self.obs_gen_low)), max(float(self.obs_reco_high), float(self.obs_gen_high)))

        dataset_name = 'dataset_sig_{0}_{1}'.format(channel, int(massHiggs))

        if (channel == "4e"):
            dataset_sig  = RooDataSet(dataset_name,dataset_name, TreesPassedEvents[Sample].CopyTree("passedFullSelection==1"), RooArgSet(self.mass4l,self.rrv_recoweight,observable), self.cutobs_reco.replace("abs","fabs").replace('mass4l','mass4e'), self.rrv_recoweight.GetName())

        if (channel == "4mu"):
            dataset_sig  = RooDataSet(dataset_name,dataset_name, TreesPassedEvents[Sample].CopyTree("passedFullSelection==1"), RooArgSet(self.mass4l,self.rrv_recoweight,observable), self.cutobs_reco.replace("abs","fabs").replace('mass4l','mass4mu'), self.rrv_recoweight.GetName())

        if (channel == "2e2mu_inclusive"):
            dataset_sig  = RooDataSet(dataset_name,dataset_name, TreesPassedEvents[Sample].CopyTree("passedFullSelection==1"), RooArgSet(self.mass4l,self.rrv_recoweight,observable), self.cutobs_reco.replace("abs","fabs"), self.rrv_recoweight.GetName())
        if (channel == "2e2mu"):
            dataset_sig  = RooDataSet(dataset_name,dataset_name, TreesPassedEvents[Sample].CopyTree("passedFullSelection==1 && ({0})".format(self.cut_2e2mu_ord)), RooArgSet(self.mass4l,self.rrv_recoweight,observable), self.cutobs_reco.replace("abs","fabs"), self.rrv_recoweight.GetName())
        if (channel == "2mu2e"):
            dataset_sig  = RooDataSet(dataset_name,dataset_name, TreesPassedEvents[Sample].CopyTree("passedFullSelection==1 && ({0})".format(self.cut_2mu2e_ord)), RooArgSet(self.mass4l,self.rrv_recoweight,observable), self.cutobs_reco.replace("abs","fabs"), self.rrv_recoweight.GetName())

        self.log.info('Created the dataset: Sample={0}, channel={1}, is_weighted={2}, sum_entries={3}'.format(Sample, channel,dataset_sig.isWeighted(), dataset_sig.sumEntries()))
        if self.DEBUG:
            dataset_sig.Print('v')
        return dataset_sig


    def make_chisqaure_plot(self, name, values, x_title='x', y_title='y'):
        """
        Plot 2D graph from 'values' provided as list of 2D tuples.
        """
        self.log.info('Making chi-square plot.')
        plotter = SimplePlotter()
        sorted_values = sorted(values,key=lambda x: x[0])

        X_vals = list(zip(*sorted_values)[0])
        Y_vals = list(zip(*sorted_values)[1])
        gr = plotter.getGraph( X_vals, Y_vals, user_style = {} )
        #style = {'linecolor' : kBlack, 'linestyle':1, 'linewidth':2, 'markersize':0.5, 'markerstyle':20}
        setup = {'y_axis' : {'title' : '#chi^{2}/ndof', 'range': [0,5]},
                 'x_axis' : {'title' : 'm_{H}'},
                 }
        plotter.arrangeAxis(gr,setup)
        gr.SetTitle('')

        canv = TCanvas("canv","canv",750,750)
        gr.Draw('APL')

        canv.SaveAs(name+'.png')
        canv.SaveAs(name+'.pdf')

        return





    def fit_simultaneously(self, channel, samples):
        """
        Perform simultaneous fit on multiple signal masses to get the Doube Crystal-Ball
        parameters, actually, the parameters of their mass dependence (e.g. p0 and p1)
        """

        ROOT.gSystem.AddIncludePath("-I$CMSSW_BASE/src/ ");
        ROOT.gSystem.Load("$CMSSW_BASE/lib/slc5_amd64_gcc472/libHiggsAnalysisCombinedLimit.so");
        ROOT.gSystem.AddIncludePath("-I$ROOFITSYS/include");

        #define p0, p1 paremeters for each DCB parameter  (these will be fit )

        if channel in ['2e2mu_inclusive', '2e2mu', '2mu2e','4e','4mu']: #FIXME for the moment they all have the same parameter range

            #idea is to make a linear expansion around mH=125p6
            #*_p0 is an intersection with y-axis of parametere(mH-125) dependance
            #*_p1 is a slope of parametere(mH-125) dependance
            mean_p0 = RooRealVar('mean_p0','mean_p0', 125, 120, 130)
            mean_p1 = RooRealVar('mean_p1','mean_p1', 1, 0.9, 1.1)
            #mean_p1.setConstant(True)

            sigma_p0 = RooRealVar('sigma_p0','sigma_p0', 1.63, 1, 3)
            sigma_p1 = RooRealVar('sigma_p1','sigma_p1', 0,-0.5, 0.5)
            #sigma_p1.setConstant(True)

            alpha_p0 = RooRealVar('alpha_p0','alpha_p0', 0.96, 0, 10)
            alpha_p1 = RooRealVar('alpha_p1','alpha_p1', 0, -0.5, 0.5)
            #alpha_p1.setConstant(True)

            n_p0 = RooRealVar('n_p0','n_p0', 4.51, 0, 10)
            n_p1 = RooRealVar('n_p1','n_p1', 0, -10, 10)
            #n_p1.setConstant(True)

            alpha2_p0 = RooRealVar('alpha2_p0','alpha2_p0', 1.4, 0, 10)
            alpha2_p1 = RooRealVar('alpha2_p1','alpha2_p1', 0, -0.5, 0.5)
            #alpha2_p1.setConstant(True)

            n2_p0 = RooRealVar('n2_p0','n2_p0', 20, -50, 50)
            n2_p1 = RooRealVar('n2_p1','n2_p1', 0, -0.5, 0.5)

            #define parameter lists (will use for 125 GeV fits and freezing)
            slope_params        = RooArgList(mean_p1, sigma_p1, alpha_p1, n_p1, alpha2_p1, n2_p1)
            intersection_params = RooArgList(mean_p0, sigma_p0, alpha_p0, n_p0, alpha2_p0, n2_p0)


        #find central mass point (to get diffs)

        mass_suffix = channel
        if channel in ["2e2mu_inclusive", "2e2mu","2mu2e"]:
                mass_suffix = "2e2mu"
        self.mass4l = RooRealVar("mass"+mass_suffix, "mass"+mass_suffix, m4l_low, m4l_high)

        ext_pdf_list = RooArgList()
        signals_dict = {}
        MH = None
        rds_all_signals = None
        #loop on mass points

        rc_signals = RooCategory('signals','signals')


        for Sample in self.List:

            sample_name = sample_shortnames[Sample]
            signals_dict[sample_name] = {}
            mh = sample_name.split("_")
            mass = ""
            for i in range(len(mh)):
                if mh[i].startswith("1"): mass = mh[i]
            if (mass=="125p6"): mass="125.6"

            massHiggs = ast.literal_eval(mass)
            signals_dict[sample_name]['MH'] = massHiggs

            if not MH:
                MH = RooRealVar("MH", "MH", massHiggs)

            delta_MH = massHiggs - MH.getVal()
            signals_dict[sample_name]['delta_MH'] = delta_MH
            self.log.debug('Sample = {0}, MH = {1}, delta_MH = {2}'.format(Sample, massHiggs, delta_MH))

            self.processBin = sample_name+'_'+channel+'_'+opt.OBSNAME+'_genbin'+str(self.genbin)+'_recobin'+str(self.recobin)
            signals_dict[sample_name]['processBin'] = self.processBin

            #define RooFormulaVar for DCB CB_parameters (including mass diff from central)
            self.log.info('Defining the DCB parameters as formulas')
            #general_formula = "@0+(@1)*(@2+({0}))".format(delta_MH)
            general_formula = "@0+(@1)*(@2+({0})-125)".format(delta_MH)  #we make expansion around mH=125

            signals_dict[sample_name]['rfv_mean_CB']  = RooFormulaVar("mean_{0}".format(int(massHiggs)),general_formula , RooArgList(mean_p0, mean_p1,MH))
            signals_dict[sample_name]['rfv_mean_CB'].SetTitle('#mu')
            signals_dict[sample_name]['rfv_sigma_CB'] = RooFormulaVar("sigma_{0}".format(int(massHiggs)),general_formula , RooArgList(sigma_p0, sigma_p1,MH))
            signals_dict[sample_name]['rfv_sigma_CB'].SetTitle('#sigma')
            signals_dict[sample_name]['rfv_alpha_CB'] = RooFormulaVar("alpha_{0}".format(int(massHiggs)),general_formula , RooArgList(alpha_p0, alpha_p1,MH))
            signals_dict[sample_name]['rfv_alpha_CB'].SetTitle('#alpha')
            signals_dict[sample_name]['rfv_n_CB']     = RooFormulaVar("n_{0}".format(int(massHiggs)),general_formula , RooArgList(n_p0, n_p1,MH))
            signals_dict[sample_name]['rfv_n_CB'].SetTitle('n')

            signals_dict[sample_name]['rfv_alpha2_CB'] = RooFormulaVar("alpha2_{0}".format(int(massHiggs)),general_formula , RooArgList(alpha2_p0, alpha2_p1,MH))
            signals_dict[sample_name]['rfv_alpha2_CB'].SetTitle('#alpha_{2}')
            signals_dict[sample_name]['rfv_n2_CB']     = RooFormulaVar("n2_{0}".format(int(massHiggs)),general_formula , RooArgList(n2_p0, n2_p1,MH))
            signals_dict[sample_name]['rfv_n2_CB'].SetTitle('n_{2}')



            #create model for each signal (for extended p.d.f. get the norm from dataset)
            signals_dict[sample_name]['pdf'] = RooDoubleCB("signal_{0}".format(int(massHiggs)),"signal_{0}".format(int(massHiggs)),
                                                            self.mass4l,
                                                            signals_dict[sample_name]['rfv_mean_CB'],
                                                            signals_dict[sample_name]['rfv_sigma_CB'],
                                                            signals_dict[sample_name]['rfv_alpha_CB'],
                                                            signals_dict[sample_name]['rfv_n_CB'],
                                                            signals_dict[sample_name]['rfv_alpha2_CB'],
                                                            signals_dict[sample_name]['rfv_n2_CB']
                                                            )


            #create RooDataSet for current Sample
            signals_dict[sample_name]['cat_name'] = 'cat_signal_{0}'.format(int(massHiggs))
            rc_signals.defineType(signals_dict[sample_name]['cat_name'])

            dataset_name = 'dataset_sig_{0}_{1}'.format(channel, int(massHiggs))
            if self.use_dataset_from_ws:


                f_win = TFile.Open('sim_fit_ws_{0}.root'.format(channel))

                win = f_win.Get('w')
                signals_dict[sample_name]['dataset'] = win.data(dataset_name)
                self.log.info('Using datasets {1} from workspace: {0}/w'.format(f_win.GetName(),signals_dict[sample_name]['dataset'].GetName()))
                self._set_cuts(channel, Sample)

            else:
                signals_dict[sample_name]['dataset'] = self._prepare_datasets(Sample, channel, massHiggs)
                #signals_dict[sample_name]['dataset'] = signals_dict[sample_name]['pdf'].generate(RooArgSet(self.mass4l),1000)

            signals_dict[sample_name]['dataset'].SetNameTitle(dataset_name,dataset_name)

            ##extended pdf

            #n_truesig = signals_dict[sample_name]['dataset'].sumEntries()
            #signals_dict[sample_name]['nsig']    = RooRealVar("N_sig_{0}".format(int(massHiggs)),"N_sig_{0}".format(int(massHiggs)), n_truesig, 0.5*n_truesig, 1.5*n_truesig)
            #signals_dict[sample_name]['nsig'].setConstant(True)

            ##we define extended but we don't use it for the fit finally (caould be removed)
            #signals_dict[sample_name]['ext_pdf']  = RooExtendPdf("esig_{0}".format(int(massHiggs)),"esig_{0}".format(int(massHiggs)), signals_dict[sample_name]['pdf'], signals_dict[sample_name]['nsig'])
            #if self.DEBUG: signals_dict[sample_name]['ext_pdf'].Print('v')
            #ext_pdf_list.add(signals_dict[sample_name]['ext_pdf'])


        #if self.DEBUG:
            #self.log.debug('The dictionary with all signals information.')
            #self.pp.pprint(signals_dict)
            #ext_pdf_list.Print()

        #----------------------------------------------------------------------------------------------------------
        #before simultaneous fit, we will fix intesection parametrs to those obtained from fit to mH=125 GeV sample
        #----------------------------------------------------------------------------------------------------------
        #we freeze slopes for this pourpose
        self.log.info('Freezing slope parameters for fits to 125 GeV point.')
        for idx in range(slope_params.getSize()):
            slope_params[idx].setConstant(True)

        #prepare fitting
        r_125 = RooFitResult()
        for key, val in signals_dict.iteritems():
            #find the pdf, dataset for 125 GeV
            #print key, val
            if val['MH'] == 125:
                self.log.debug('Found 125 GeV signal.= in signals_dict.')
                sig_125 = val
        try:
            sig_125
        except NameError:
            raise NameError, 'There is no 125 GeV signal pdf, dataset loaded into signals_dict.'

        #now we will make a fit of 125 GeV sample
        self.log.info('Fitting 125 GeV signal for channel={0}'.format(channel))
        r_125 = sig_125['pdf'].fitTo(sig_125['dataset'],
                                RooFit.Save(kTRUE),
                                RooFit.SumW2Error(kTRUE),
                                RooFit.Verbose(kFALSE),
                                RooFit.PrintLevel(-1),
                                RooFit.Warnings(kFALSE),
                                RooFit.NumCPU(12),RooFit.Timer(kTRUE)
                                )
        print "RooFitResult for 125 GeV signal:"
        r_125.Print()
        fit_results_file = TFile("plots/TEST11_FITRESULT_SIM125_"+channel+'_'+opt.OBSNAME+'_genbin'+str(self.genbin)+'_recobin'+str(self.recobin)+"_effs_"+self.recoweight+".root", "RECREATE")
        r_125.Write('fit_result')
        #sum.Print()
        self.log.info('Retrieving correlation matrix.')
        correlation_matrix = r_125.correlationHist()
        correlation_matrix.Write('correlation_matrix')
        c = TCanvas("c","c",750,750)
        SetOwnership(c,False)
        correlation_matrix.Draw("colz")
        c.SaveAs("plots/TEST11_SIM125_correlation_matrix_"+channel+'_'+opt.OBSNAME+'_genbin'+str(self.genbin)+'_recobin'+str(self.recobin)+"_effs_"+self.recoweight+".png")
        c.SaveAs("plots/TEST11_SIM125_correlation_matrix_"+channel+'_'+opt.OBSNAME+'_genbin'+str(self.genbin)+'_recobin'+str(self.recobin)+"_effs_"+self.recoweight+".pdf")

        #plot the fit and display parameters and also the chiSquare
        self.log.info('Plotting the 125 GeV fit and displaying parameters.')
        self.frame = RooPlot()
        self.frame = self.mass4l.frame(RooFit.Title(self.mass4l.GetTitle().replace('mass','m')),RooFit.Bins(self.m4l_bins))

        sig_125['dataset'].plotOn(self.frame, RooFit.LineColor(kRed), RooFit.MarkerSize(0))
        sig_125['pdf'].plotOn(self.frame, RooFit.LineColor(kRed) )

        self.frame.Draw()
        self.frame.Print('v')
        self.log.info('ChiSquare/ndof (ndof={0}) = {1}'.format(r_125.floatParsFinal().getSize(),
                                                                self.frame.chiSquare(r_125.floatParsFinal().getSize())))
        self._draw_CMS_label(c, label = 'Simulation', x=0.2, y=0.8)
        latex2 = TLatex()
        latex2.SetNDC()
        latex2.SetTextSize(0.4*c.GetTopMargin())
        latex2.SetTextAlign(11)
        latex2.SetTextFont(42)
        latex2.SetTextSize(0.3*c.GetTopMargin())
        latex2.DrawLatex(0.15, 0.64, "#chi^{{2}}/ndof = {0:3.2f} ({1})".format(self.frame.chiSquare(r_125.floatParsFinal().getSize()), r_125.floatParsFinal().getSize()))
        dy = 0
        self.log.info('Getting intesection parameters from fit results and fixing them to 125 GeV best-fit values.')
        for idx in range(intersection_params.getSize()):
            #print to the plot
            par = intersection_params[idx]
            par_name = par.GetName()
            r_125_float_params = r_125.floatParsFinal()
            if not r_125_float_params.find(par_name):
                raise RuntimeError, 'Cannot find parameter {0} in RooFitResult floated parameters.'.format(par_name)

            self.log.debug('Found matching parameters in fit result: {0} = {1:3.3f} +/- {2:3.3f} ...'.format(par_name,
                                                                                                     r_125_float_params.find(par_name).getVal(),
                                                                                                     r_125_float_params.find(par_name).getError() ))

            par.setVal(r_125_float_params.find(par_name).getVal())
            par.setError(r_125_float_params.find(par_name).getError())
            par.setRange(par.getVal()-par.getError(), par.getVal()+par.getError())

            if self.DEBUG: par.Print()
            latex2.DrawLatex(0.15, 0.6+dy, " {0} = {1:3.2f} #pm {2:3.2f}".format(par.GetTitle().rstrip('_p0'),
                                                                                 r_125_float_params.find(par_name).getVal(),
                                                                                 r_125_float_params.find(par_name).getError()))
            dy -= 0.04

        c.SaveAs("plots/TEST11_SIM125_"+channel+'_'+opt.OBSNAME+'_genbin'+str(self.genbin)+'_recobin'+str(self.recobin)+"_effs_"+self.recoweight+".png")
        c.SaveAs("plots/TEST11_SIM125_"+channel+'_'+opt.OBSNAME+'_genbin'+str(self.genbin)+'_recobin'+str(self.recobin)+"_effs_"+self.recoweight+".pdf")



        #unfreeze the slopes and freeze intesections after setting to the ones from 125 GeV fit
        self.log.info('Unfreezing slope parameters...')
        for idx in range(slope_params.getSize()):
            slope_params[idx].setConstant(False)
            if self.DEBUG: slope_params[idx].Print()

        sim_fit_frozen_params = RooArgList(
                                            mean_p0,
                                            sigma_p0,
                                            alpha_p0,
                                            #n_p0,
                                            #alpha2_p0,
                                            n2_p0,
                                            alpha2_p1,
                                            alpha_p1,
                                            n_p1  #added on Oct06 for TEST7 version
                                            )

        self.log.info('Freezing parameters {0}.'.format(sim_fit_frozen_params))
        for idx in range(sim_fit_frozen_params.getSize()):
            sim_fit_frozen_params[idx].setConstant(True)
            if self.DEBUG: sim_fit_frozen_params[idx].Print()


        #return

        ##make RooAddPdf of all signals and prepare fitting.
        self.sim_pdf = RooSimultaneous('sim_pdf', 'Simultaneous pdf', rc_signals)
        import_rds_cmd = ''

        wout = RooWorkspace('w')
        #self.log.debug('Joining the dataset for signals. Size={0}'.format(len(self.List))) #6
        #for Sample in self.List:
            #sample_name = sample_shortnames[Sample]
            ##self.sim_pdf.addPdf(signals_dict[sample_name]['ext_pdf'], signals_dict[sample_name]['cat_name'])
            #self.sim_pdf.addPdf(signals_dict[sample_name]['pdf'], signals_dict[sample_name]['cat_name'])
            #import_rds_cmd+=",RooFit.Import(signals_dict['{0}']['cat_name'],signals_dict['{0}']['dataset'])".format(sample_name)
            #for key in signals_dict[sample_name].keys():
                #if key in ['pdf','dataset', 'rfv_mean_CB','rfv_sigma_CB','rfv_alpha2_CB', 'rfv_alpha_CB','rfv_n_CB','rfv_n_CB']:
                    #getattr(wout,'import')(signals_dict[sample_name][key],RooFit.RecycleConflictNodes())


        #self.rrv_recoweight = RooRealVar(self.recoweight, self.recoweight, 0.0, 10.0)
        #rds_all_signals_create_cmd = 'rds_all_signals = RooDataSet("all_signals","All signals",RooArgSet(self.mass4l,self.rrv_recoweight), RooFit.Index(rc_signals){0},RooFit.WeightVar(self.rrv_recoweight.GetName()))'.format(import_rds_cmd)
        #self.log.debug('rds_all_signals_create_cmd : {0}'.format(rds_all_signals_create_cmd))
        #exec(rds_all_signals_create_cmd)

        for Sample in self.List:
            sample_name = sample_shortnames[Sample]
            self.sim_pdf.addPdf(signals_dict[sample_name]['pdf'], signals_dict[sample_name]['cat_name'])
            for key in signals_dict[sample_name].keys():
                if key in ['pdf','dataset', 'rfv_mean_CB','rfv_sigma_CB','rfv_alpha2_CB', 'rfv_alpha_CB','rfv_n_CB','rfv_n_CB']:
                    getattr(wout,'import')(signals_dict[sample_name][key],RooFit.RecycleConflictNodes())

        #join datasets
        self.log.debug('Joining the dataset for signals. Size={0}'.format(len(self.List))) #6 is largest
        self.rrv_recoweight = RooRealVar(self.recoweight, self.recoweight, 0.0, 10.0)


        #for Sample in self.List:
            #sample_name = sample_shortnames[Sample]
            #import_rds_cmd+=",RooFit.Import(signals_dict['{0}']['cat_name'],signals_dict['{0}']['dataset'])".format(sample_name)

        #rds_all_signals_create_cmd = 'rds_all_signals = RooDataSet("all_signals","All signals",RooArgSet(self.mass4l,self.rrv_recoweight), RooFit.Index(rc_signals),RooFit.WeightVar(self.rrv_recoweight.GetName()){0})'.format(import_rds_cmd)
        #self.log.debug('rds_all_signals_create_cmd : {0}'.format(rds_all_signals_create_cmd))
        #exec(rds_all_signals_create_cmd)

        rds_signals = []
        for i_rds in range(int(ceil(len(self.List)/5.0))):
            import_rds_cmd = ''
            for Sample in self.List[5*i_rds:5*(i_rds+1)]:
                sample_name = sample_shortnames[Sample]
                import_rds_cmd+=",RooFit.Import(signals_dict['{0}']['cat_name'],signals_dict['{0}']['dataset'])".format(sample_name)

            #pdb.set_trace()
            if not import_rds_cmd: break
            rds_signals_create_cmd = 'this_rds = RooDataSet("all_signals_{1}","All signals {1}",RooArgSet(self.mass4l,self.rrv_recoweight), RooFit.Index(rc_signals),RooFit.WeightVar(self.rrv_recoweight.GetName()){0})'.format(import_rds_cmd, i_rds)
            self.log.debug('rds_all_signals_create_cmd : {0}'.format(rds_signals_create_cmd))
            exec(rds_signals_create_cmd)
            rds_signals.append(this_rds)

        rds_all_signals = rds_signals[0]
        for rds in rds_signals[1:]:
            rds_all_signals.append(rds)

        #pdb.set_trace()

        getattr(wout,'import')(rds_all_signals, RooFit.RecycleConflictNodes())
        getattr(wout,'import')(self.sim_pdf, RooFit.RecycleConflictNodes())
        wout.writeToFile('sim_fit_ws_{0}.root'.format(channel))
        if self.DEBUG: self.sim_pdf.Print('v')

        if self.DEBUG:
            print 100*'-'
            self.log.debug('Total all signals RooDataSet:')
            rds_all_signals.Print('v')
            print 100*'-'


        #prepare fit results and fit
        if doFit:
            self.r = RooFitResult()
            self.r = self.sim_pdf.fitTo(rds_all_signals,
                                        RooFit.Save(kTRUE),
                                        RooFit.SumW2Error(kTRUE),
                                        RooFit.Verbose(kFALSE),
                                        RooFit.PrintLevel(-1),
                                        RooFit.Warnings(kFALSE),
                                        RooFit.NumCPU(12),RooFit.Timer(kTRUE)
                                        )
            print "RooFitResult:"
            self.r.Print()

            fit_results_file = TFile("plots/TEST11_FITRESULT_SIM_"+channel+'_'+opt.OBSNAME+'_genbin'+str(self.genbin)+'_recobin'+str(self.recobin)+"_effs_"+self.recoweight+".root", "RECREATE")
            self.r.Write('fit_result')
            #sum.Print()
            correlation_matrix = self.r.correlationHist()
            correlation_matrix.Write('correlation_matrix')

            #print results into formula
            self.log.info('Printing formulas for {0}'.format(channel))
            for cb_par in ['mean', 'sigma', 'alpha', 'n', 'alpha2', 'n2']:
                output_formula = ''
                if abs(intersection_params.find(cb_par+'_p0').getVal()) > 0.0:
                    p0_part = '{0}'.format(intersection_params.find(cb_par+'_p0').getVal())
                    output_formula += p0_part
                if abs(slope_params.find(cb_par+'_p1').getVal()) > 0.0:
                    p1_part = '({0})*(@0-125)'.format(slope_params.find(cb_par+'_p1').getVal())
                    if output_formula: output_formula += '+'
                    output_formula+= p1_part
                print cb_par+' = \''+output_formula+'\''


        #plot all signals
        c = TCanvas("c","c",750,750)
        SetOwnership(c,False)
        c.cd()
        if doFit:
            correlation_matrix.Draw("colz")
            c.SaveAs("plots/TEST11_SIM_correlation_matrix_"+channel+'_'+opt.OBSNAME+'_genbin'+str(self.genbin)+'_recobin'+str(self.recobin)+"_effs_"+self.recoweight+".png")
            c.SaveAs("plots/TEST11_SIM_correlation_matrix_"+channel+'_'+opt.OBSNAME+'_genbin'+str(self.genbin)+'_recobin'+str(self.recobin)+"_effs_"+self.recoweight+".pdf")
            c.Clear()

        tmp_argsets = RooArgSet(rc_signals)

        chi_square_values = []
        color_shift=0
        for Sample in self.List:
            c.Clear()
            sample_name = sample_shortnames[Sample]
            self.frame = self.mass4l.frame(RooFit.Title('mH = {0}'.format(signals_dict[sample_name]['MH']))#,
                                           #RooFit.Bins(self.m4l_bins)
                                           )
            self.frame.GetXaxis().SetTitle('m_{2e2#mu}')
            rds_all_signals.plotOn(self.frame, RooFit.LineColor(kBlack),
                                   RooFit.MarkerSize(0),
                                   RooFit.Cut('signals==signals::{0}'.format(signals_dict[sample_name]['cat_name'])))
            if doFit:
                self.sim_pdf.plotOn(self.frame,
                                    RooFit.Slice(rc_signals,signals_dict[sample_name]['cat_name']),
                                    RooFit.ProjWData(tmp_argsets,rds_all_signals),
                                    RooFit.LineColor(ROOT.kPink+color_shift)
                                    )

            color_shift+=1





            if doFit:
                self.log.info('ChiSquare/ndof (ndof={0}) = {1}'.format(self.r.floatParsFinal().getSize(),
                                                                    self.frame.chiSquare(self.r.floatParsFinal().getSize())
                                                                    #self.frame.chiSquare('sum_Norm[mass2e2mu]', 'h_dataset_sig', self.r.floatParsFinal().getSize())
                                                                    ))
                chi_square_values.append(( signals_dict[sample_name]['MH'], self.frame.chiSquare(self.r.floatParsFinal().getSize())))
            self.frame.Draw()
            #self.frame.Draw()
            #self.frame.Print('v')

            self._draw_CMS_label(c, label = 'Simulation', x=0.15, y=0.8)

            latex2 = TLatex()
            latex2.SetNDC()
            latex2.SetTextAlign(11)
            latex2.SetTextFont(42)
            latex2.SetTextSize(0.3*c.GetTopMargin())
            if doFit:
                latex2.DrawLatex(0.6, 0.84, "\chi^{{2}}/ndof = {0:3.2f} ({1})".format(self.frame.chiSquare(self.r.floatParsFinal().getSize()), self.r.floatParsFinal().getSize()))
                #latex2.DrawLatex(0.15, 0.47, "ndof = {0}".format(self.r.floatParsFinal().getSize()))
                dy = 0
                for key in sorted(signals_dict[sample_name].keys()):
                    if key.startswith('rfv_'):
                        rfv = signals_dict[sample_name][key]
                        latex2.DrawLatex(0.6, 0.8+dy, " {0} = {1:3.2f} ".format(rfv.GetTitle(), rfv.getVal()))
                        dy -= 0.04
            latex2.DrawLatex(0.6, 0.8+dy, " n_{{data}} = {0:3.2f}".format(rds_all_signals.sumEntries('signals==signals::{0}'.format(signals_dict[sample_name]['cat_name']))))



            c.SaveAs("plots/TEST11_SIM_"+signals_dict[sample_name]['processBin']+"_effs_"+self.recoweight+".png")
            c.SaveAs("plots/TEST11_SIM_"+signals_dict[sample_name]['processBin']+"_effs_"+self.recoweight+".pdf")

            self.make_chisqaure_plot("plots/TEST11_SIM_chisquare_"+channel+'_'+opt.OBSNAME+'_genbin'+str(self.genbin)+'_recobin'+str(self.recobin)+"_effs_"+self.recoweight,
                                    chi_square_values, x_title = 'm_H')


        if doFit:
            fit_results_file.Close()
        return



    def closure_test_fit(self, channel, samples, params_dict, tag):
        """
        Perform closure test of the Doube Crystal-Ball parameters
        from an already established DCB_parametrization writen as
        formula strings in 'parametization_cfg'
        """

        ROOT.gSystem.AddIncludePath("-I$CMSSW_BASE/src/ ");
        ROOT.gSystem.Load("$CMSSW_BASE/lib/slc5_amd64_gcc472/libHiggsAnalysisCombinedLimit.so");
        ROOT.gSystem.AddIncludePath("-I$ROOFITSYS/include");


        #find central mass point (to get diffs)

        mass_suffix = channel
        if channel in ["2e2mu_inclusive", "2e2mu","2mu2e"]:
                mass_suffix = "2e2mu"
        self.mass4l = RooRealVar("mass"+mass_suffix, "mass"+mass_suffix, m4l_low, m4l_high)

        ext_pdf_list = RooArgList()
        signals_dict = {}
        MH = None
        rds_all_signals = None
        #loop on mass points

        rc_signals = RooCategory('signals','signals')
        chi_square_values = {}
        for cfg_id, cfg in enumerate(sorted(params_dict.keys())):
            chi_square_values[cfg] = []

        for Sample in self.List:

            sample_name = sample_shortnames[Sample]

            mh = sample_name.split("_")
            mass = ""
            for i in range(len(mh)):
                if mh[i].startswith("1"): mass = mh[i]
            if (mass=="125p6"): mass="125.6"

            massHiggs = ast.literal_eval(mass)
            MH = RooRealVar("MH", "MH", massHiggs)
            signals_dict[sample_name] = {}
            for cfg_id, cfg in enumerate(sorted(params_dict.keys())):
                signals_dict[sample_name][cfg] = {}
                signals_dict[sample_name][cfg]['MH'] = massHiggs

                self.processBin = sample_name+'_'+channel+'_'+opt.OBSNAME+'_genbin'+str(self.genbin)+'_recobin'+str(self.recobin)
                signals_dict[sample_name][cfg]['processBin'] = self.processBin


                #define RooFormulaVar for DCB CB_parameters (including mass diff from central)
                self.log.info('Defining the DCB parameters as formulas')


                signals_dict[sample_name][cfg]['rfv_mean_CB']  = RooFormulaVar("mean_{0}_{1}".format(int(massHiggs), cfg_id),params_dict[cfg]['mean'], RooArgList(MH))
                signals_dict[sample_name][cfg]['rfv_mean_CB'].SetTitle('#mu')
                signals_dict[sample_name][cfg]['rfv_sigma_CB'] = RooFormulaVar("sigma_{0}_{1}".format(int(massHiggs), cfg_id),params_dict[cfg]['sigma'], RooArgList(MH))
                signals_dict[sample_name][cfg]['rfv_sigma_CB'].SetTitle('#sigma')
                signals_dict[sample_name][cfg]['rfv_alpha_CB'] = RooFormulaVar("alpha_{0}_{1}".format(int(massHiggs), cfg_id),params_dict[cfg]['alpha'], RooArgList(MH))
                signals_dict[sample_name][cfg]['rfv_alpha_CB'].SetTitle('#alpha')
                signals_dict[sample_name][cfg]['rfv_n_CB']     = RooFormulaVar("n_{0}_{1}".format(int(massHiggs), cfg_id),params_dict[cfg]['n'], RooArgList(MH))
                signals_dict[sample_name][cfg]['rfv_n_CB'].SetTitle('n')

                signals_dict[sample_name][cfg]['rfv_alpha2_CB'] = RooFormulaVar("alpha2_{0}_{1}".format(int(massHiggs), cfg_id),params_dict[cfg]['alpha2'], RooArgList(MH))
                signals_dict[sample_name][cfg]['rfv_alpha2_CB'].SetTitle('#alpha_{2}')
                signals_dict[sample_name][cfg]['rfv_n2_CB']     = RooFormulaVar("n2_{0}_{1}".format(int(massHiggs), cfg_id),params_dict[cfg]['n2'], RooArgList(MH))
                signals_dict[sample_name][cfg]['rfv_n2_CB'].SetTitle('n_{2}')



                #create model for each signal (for extended p.d.f. get the norm from dataset)
                signals_dict[sample_name][cfg]['pdf'] = RooDoubleCB("signal_{0}_{1}".format(int(massHiggs), cfg_id),"signal_{0}_{1}".format(int(massHiggs), cfg_id),
                                                                self.mass4l,
                                                                signals_dict[sample_name][cfg]['rfv_mean_CB'],
                                                                signals_dict[sample_name][cfg]['rfv_sigma_CB'],
                                                                signals_dict[sample_name][cfg]['rfv_alpha_CB'],
                                                                signals_dict[sample_name][cfg]['rfv_n_CB'],
                                                                signals_dict[sample_name][cfg]['rfv_alpha2_CB'],
                                                                signals_dict[sample_name][cfg]['rfv_n2_CB']
                                                                )


                #create RooDataSet for current Sample
                signals_dict[sample_name][cfg]['cat_name'] = 'cat_signal_{0}'.format(int(massHiggs), cfg_id)
                rc_signals.defineType(signals_dict[sample_name][cfg]['cat_name'])

                dataset_name = 'dataset_sig_{0}_{1}'.format(channel, int(massHiggs))
                if self.use_dataset_from_ws:


                    f_win = TFile.Open('sim_fit_ws_{0}.root'.format(channel))

                    win = f_win.Get('w')
                    signals_dict[sample_name][cfg]['dataset'] = win.data(dataset_name)
                    self.log.info('Using datasets {1} from workspace: {0}/w'.format(f_win.GetName(),signals_dict[sample_name][cfg]['dataset'].GetName()))
                    self._set_cuts(channel, Sample)

                else:
                    signals_dict[sample_name][cfg]['dataset'] = self._prepare_datasets(Sample, channel, massHiggs)
                    #signals_dict[sample_name][cfg]['dataset'] = signals_dict[sample_name][cfg]['pdf'].generate(RooArgSet(self.mass4l),1000)

                signals_dict[sample_name][cfg]['dataset'].SetNameTitle(dataset_name,dataset_name)

                #extended pdf

                n_truesig = signals_dict[sample_name][cfg]['dataset'].sumEntries()
                signals_dict[sample_name][cfg]['nsig']    = RooRealVar("N_sig_{0}_{1}".format(int(massHiggs), cfg_id),"N_sig_{0}_{1}".format(int(massHiggs), cfg_id), n_truesig, 0.5*n_truesig, 1.5*n_truesig)

                #signals_dict[sample_name][cfg]['nsig'].setConstant(True)

                #we define extended but we don't use it for the fit finally (caould be removed)
                signals_dict[sample_name][cfg]['ext_pdf']  = RooExtendPdf("esig_{0}_{1}".format(int(massHiggs), cfg_id),"esig_{0}_{1}".format(int(massHiggs), cfg_id), signals_dict[sample_name][cfg]['pdf'], signals_dict[sample_name][cfg]['nsig'])
                if self.DEBUG: signals_dict[sample_name][cfg]['ext_pdf'].Print('v')
                #ext_pdf_list.add(signals_dict[sample_name][cfg]['ext_pdf'])


                #prepare fit results and fit
                if doFit:
                    signals_dict[sample_name][cfg]['fit_result'] = RooFitResult()
                    signals_dict[sample_name][cfg]['fit_result'] = signals_dict[sample_name][cfg]['ext_pdf'].fitTo(signals_dict[sample_name][cfg]['dataset'],
                                                RooFit.Save(kTRUE),
                                                RooFit.SumW2Error(kTRUE),
                                                RooFit.Verbose(kFALSE),
                                                RooFit.PrintLevel(-1),
                                                RooFit.Warnings(kFALSE),
                                                RooFit.NumCPU(12),RooFit.Timer(kTRUE)
                                                )
                    print "RooFitResult:"
                    signals_dict[sample_name][cfg]['fit_result'].Print()

                    fit_results_file = TFile("plots/TEST11_FITRESULT_CLOSURE_"+str(cfg_id)+"_"+signals_dict[sample_name][cfg]['processBin']+"_effs_"+self.recoweight+'_'+tag+".root", "RECREATE")
                    signals_dict[sample_name][cfg]['fit_result'].Write('fit_result')
                    #sum.Print()

            #plot all signals
            c = TCanvas("c","c",750,750)
            SetOwnership(c,False)
            c.cd()
            c.SetLogy(1)
            tmp_argsets = RooArgSet(rc_signals)


            c.Clear()
            sample_name = sample_shortnames[Sample]
            first_cfg = sorted(params_dict.keys())[0]

            self.frame = self.mass4l.frame(RooFit.Title('mH = {0}'.format(signals_dict[sample_name][first_cfg]['MH']))#,
                                            #RooFit.Bins(self.m4l_bins)
                                            )
            self.frame.GetXaxis().SetTitle('m_{2e2#mu}')
            signals_dict[sample_name][first_cfg ]['dataset'].plotOn(self.frame, RooFit.LineColor(kBlack),
                                    RooFit.MarkerSize(0))
            for cfg_id, cfg in enumerate(sorted(params_dict.keys())):

                signals_dict[sample_name][cfg]['ext_pdf'].plotOn(self.frame,
                                    #RooFit.LineColor(ROOT.kViolet+cfg_id*2)
                                    RooFit.LineColor(params_dict[cfg]['color'])
                                    )

                self.log.info('ChiSquare/ndof (ndof={0}) = {1}'.format(signals_dict[sample_name][cfg]['fit_result'].floatParsFinal().getSize(),
                                                                    self.frame.chiSquare(signals_dict[sample_name][cfg]['fit_result'].floatParsFinal().getSize())
                                                                    #self.frame.chiSquare('sum_Norm[mass2e2mu]', 'h_dataset_sig', self.r.floatParsFinal().getSize())
                                                                    ))
                chi_square_values[cfg].append(( signals_dict[sample_name][cfg]['MH'], self.frame.chiSquare(signals_dict[sample_name][cfg]['fit_result'].floatParsFinal().getSize())))
                signals_dict[sample_name][cfg]['dataset'].plotOn(self.frame, RooFit.LineColor(kBlack),RooFit.MarkerSize(0))
            self.frame.Draw()
            #self.frame.Draw()
            #self.frame.Print('v')

            #self._draw_CMS_label(c, label = 'Simulation', x=0.15, y=0.8)

            latex2 = TLatex()
            latex2.SetNDC()
            latex2.SetTextAlign(11)
            latex2.SetTextFont(42)
            latex2.SetTextSize(0.3*c.GetTopMargin())
            #latex2.DrawLatex(0.15, 0.5, "Closure test")

            x_positions = [0.67, 0.2, 0.67, 0.2]
            y_positions = [0.84, 0.84,0.5, 0.5 ]
            for cfg_id, cfg in enumerate(sorted(params_dict.keys())):

                x_0, y_0 = x_positions[cfg_id], y_positions[cfg_id]
                latex2.SetTextColor(params_dict[cfg]['color'])
                #latex2.DrawLatex(x_0-0.04, y_0, "Parametrization {0}:".format(cfg_id))
                latex2.DrawLatex(x_0-0.04, y_0, params_dict[cfg]['parametrization_name'])
                #latex2.DrawLatex(x_0, y_0-0.04, "\chi^{{2}}/ndof = {0:3.2f} ({1})".format(
                    #self.frame.chiSquare(signals_dict[sample_name][cfg]['fit_result'].floatParsFinal().getSize()),
                    #signals_dict[sample_name][cfg]['fit_result'].floatParsFinal().getSize()))
                #latex2.DrawLatex(0.15, 0.47, "ndof = {0}".format(self.r.floatParsFinal().getSize()))
                dy = -0.04
                for key in sorted(signals_dict[sample_name][cfg].keys()):
                    if key.startswith('rfv_'):
                        rfv = signals_dict[sample_name][cfg][key]
                        latex2.DrawLatex(x_0, y_0+dy, " {0} = {1:3.2f} ".format(rfv.GetTitle(), rfv.getVal()))
                        dy -= 0.04
                #latex2.DrawLatex(x_0, y_0+dy, " n_{{data}} = {0:3.2f} ".format(signals_dict[sample_name][cfg]['dataset'].sumEntries()))
                #latex2.DrawLatex(x_0, y_0+dy, " n_{{data}} = {0:3.2f} {1:3.2f}".format(
                    #signals_dict[sample_name][cfg]['fit_result'].floatParsFinal().find(signals_dict[sample_name][cfg]['nsig'].GetName()).getVal(),
                    #signals_dict[sample_name][cfg]['dataset'].sumEntries()))


            c.SaveAs("plots/TEST11_CLOSURE_"+signals_dict[sample_name][cfg]['processBin']+"_effs_"+self.recoweight+'_'+tag+".png")
            c.SaveAs("plots/TEST11_CLOSURE_"+signals_dict[sample_name][cfg]['processBin']+"_effs_"+self.recoweight+'_'+tag+".pdf")

        for cfg_id, cfg in enumerate(sorted(params_dict.keys())):
            tag_single =  string.split(cfg,'.')[0]
            self.make_chisqaure_plot("plots/TEST11_SIM_chisquare_closure"+channel+'_'+opt.OBSNAME+'_genbin'+str(self.genbin)+'_recobin'+str(self.recobin)+"_effs_"+self.recoweight+'_'+tag_single,
                                        chi_square_values[cfg], x_title = 'm_H')

            #fit_results_file.Close()
        return





#if __name__ == "__main__":

m4l_bins = 50
m4l_low = 100.0
m4l_high = 150.0

# Default to inclusive cross section
obs_reco = 'mass4l'
obs_gen = 'GENmZ1Z2'
obs_reco_low = 100.0
obs_reco_high = 150.0
obs_gen_low = 100.0
obs_gen_high = 150.0


m4l_bins = 50
m4l_low = 100.0
m4l_high = 150.0

# Default to inclusive cross section
obs_reco = 'mass4l'
obs_gen = 'GENmZ1Z2'
obs_reco_low = 100.0
obs_reco_high = 150.0
obs_gen_low = 100.0
obs_gen_high = 150.0


#obs_bins = {0:(opt.OBSBINS.split("|")[1:((len(opt.OBSBINS)-1)/2)]),1:['0','inf']}[opt.OBSNAME=='inclusive']
obs_bins = opt.OBSBINS.split("|")
if (not (obs_bins[0] == '' and obs_bins[len(obs_bins)-1]=='')):
    print 'BINS OPTION MUST START AND END WITH A |'
obs_bins.pop()
obs_bins.pop(0)

List = []
for long, short in sample_shortnames.iteritems():
    print long,short
    List.append(long)

#for long, short in sample_shortnames.iteritems():
    #List.append(long)

print List

if (obs_reco=="mass4l"):
    #chans = ['4e','4mu','2e2mu','4l']
    chans = string.split(opt.FINAL_STATE, ',')
    print 'Running on channels:', chans
else:
    chans = ['4e','4mu','2e2mu','2mu2e','2e2mu_inclusive']

dummy_file = TFile("dummy_file.root","RECREATE")  #Created to fix the ROOT feature of memory resident trees.
pp = pprint.PrettyPrinter(indent=4)
for chan in chans:
    for recobin in range(len(obs_bins)-1):
        for genbin in range(len(obs_bins)-1):
            #geteffs(chan,List, m4l_bins, m4l_low, m4l_high, obs_reco, obs_gen, obs_bins, recobin, genbin)
            m4l_tool = SignalSpectrumFitter(chan,List, m4l_bins, m4l_low, m4l_high, obs_reco, obs_gen, obs_bins, recobin, genbin)
            print m4l_tool
            m4l_tool.datasets_exists(not opt.DO_DATASETS)
            if opt.GENERATE_N:
                m4l_tool.generate_dataset(opt.GENERATE_N)
            if not opt.DOCLOSURE:
                m4l_tool.fit_simultaneously(chan, List)
            else:
                if opt.CLOSURE_TEST:
                    params_cfgs = string.split(opt.CLOSURE_TEST,',')

                else:
                    params_cfgs = ['DCB_parametrization.yaml']
                print 'Parameterization cfgs: {0}'.format(params_cfgs)
                params_dict={}
                tag_for_closure_plots = ''
                #read all the configurations for the closure test.
                for params_cfg in params_cfgs:
                    cfg_reader = UniversalConfigParser(cfg_type="YAML",file_list = params_cfg)
                    params_dict[params_cfg] = cfg_reader.get_dict()[chan]
                    tag_for_closure_plots += os.path.splitext(params_cfg)[0]
                    tag_for_closure_plots+='_'
                pp.pprint(params_dict)
                m4l_tool.closure_test_fit(chan, List, params_dict, tag_for_closure_plots)

dummy_file.Close()
