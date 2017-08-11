#i####################Half-Life Calculator#########################
#Program designed to take in a list of pynaa files, integrate over a  #
#peak in each, Plot the areas as a function of time, and fit to an    #
#exponential to Estimate the Half-life of the element                 #

##TO-DO##
# * Re-write so the program runs over all peaks in an experiment #
# * Have the program output a data file with peaks and associated#
#   Half-lives found for each peak using both methods            #

import sys
from scipy.optimize import fsolve
from os import listdir
import operator
import time

from .tool import mfit as mf

import numpy as np
import matplotlib.pyplot as plt

class halflife(object):
    '''
    Input is a datacollection class containing multiple
    HPGe spectra in a .npz file format. Calculates the
    half-life of a decaying peak associated with a
    region selected by the user
    '''

    def __init__(self, datatoanalyze=None):
        self.name = 'halflife'
        self.usebkgdata = False
        self.fill_datatoanalyze(datatoanalyze)
        self.current_peakdata = []

    def clear_datatoanalyze(self):
        self.datatoanalyze = None
        self.usebkgdata = False

    def fill_datatoanalyze(self,datatoanalyze):
        self.datatoanalyze = datatoanalyze
        if self.datatoanalyze.openbkgfiles: #True if bkg data files are loaded
            self.usebkgdata = True

    def run(self):
        '''
        Default is to calculate the half life using an exponential fit to
        count data of one peak.
        '''
        peakdata_dict=self.get_onepeakinfo(self.datatoanalyze.opendatafiles, \
                self.datatoanalyze.openbkgfiles)
        self.hl_expfit(peakdata_dict)
        #uncomment to calculate half-life using pairs of peak data
        #self.hl_countpairs(peakdata_dict)

###Functions used by the half-life calculator
    def __inputvalid(self, xl, xr):
        '''
        Make sure the user didn't pick any silly bounds for half-life
        calculating.
        '''
        inputokay = True
        #FIXME: Put in a check to make sure xl and xr are numbers
        if xl > xr:
            print("lower bound is higher than upper bound. Try again.")
            inputokay = False
        return inputokay

    def showSpectrum(self, datafile):
            '''
            Shows the plot of the HPGe spectrum for the input datafile.
            '''
            x,y = dfile.x, dfile.y
            plt.ion()
            plt.plot(x,y, alpha=0.8, color='r')
            plt.title('Spectrum for file: ' + str(datafile.name))
            plt.set_xlabel('Energy (keV)')
            plt.set_ylabel('Counts')
            plt.show()


    def __peakchooser(self, datafile):
        '''
        Takes in the first datafile, plots the spectrum, and allows the
        user to choose a peak region of interest.  The lower and
        upper energy of the peak region are returned.
        '''

        plt.ion()
        x,y=datafile.x,datafile.y
        plt.plot(x,y) #Uses first file for user to choose peak of interest
        plt.title('Find your peak region, then close.')
        plt.show()
        goodbounds = False
        while not goodbounds:
            xleft=float(input('Leftmost edge of peak (keV):'))
            xright=float(input('Rightmost edge of right peak (keV):'))
            if self.__inputvalid(xleft, xright):
                goodbounds = True
                plt.close()
        self.current_peakdata = []
        return xleft, xright
    
    def get_onepeakinfo(self, datafile_arr, bkddatafile_arr=None):
        '''
        Function takes in a datacollection class object and returns
        the start time, total counts, total counts scaled for if
        there was no dead time, and the total counting time taken
        for a peak region input by the user.
        '''
        scaled_counts=[] #Counts with a correction for deadtime
        scaled_counts_unc=[]
        starttimes=[] #Start time of each datafile
        counttimes=[] #Total count time of each datafile
        deadtimes=[] #Total fraction of time the HPGe was dead while
                     #collecting data
        plot=0
        for dfile in datafile_arr:
            counttimes.append(float(dfile.tstop-dfile.tstart))
            starttimes.append(float(dfile.tstart))
            x,y=dfile.x,dfile.y
            if plot==0:
                xleft, xright = self.__peakchooser(dfile)
                xmin=np.where(x<xleft)[0][-1] #point just below xleft
                xmax=np.where(x>xright)[0][0] #point just above xright
                hpw=len(x[xmin:xmax])/2 #Mid-point of peak
                plot=1
            totcounts=sum(y[xmin:xmax]) #Total counts in peak regoin
            if self.usebkgdata is True:
                #FIXME: Calculate background expected using the background
                #Files fed in.  Take the total counts in the file and scale
                #them to the time taken for this dfile.
                print("This feature not yet supported.  Defaulting to using"+\
                        "Sideband of peak for background count")
                bgl=sum(y[xmin-hpw:xmin]) #Backgrounds calculated from left and right sides of peak
                bgr=sum(y[xmax:xmax+hpw])
                bg=bgl+bgr
            else:
                bgl=sum(y[xmin-hpw:xmin]) #Backgrounds calculated from left and right sides of peak
                bgr=sum(y[xmax:xmax+hpw])
                bg=bgl+bgr
            #background subtract, and calculate uncertaineies associated with it
            signalcounts=totcounts-bg
            signalcounts_unc = np.sqrt(totcounts + bg)
            #The activity needs to be corrected to account
            #for dead time during the counting run.
            deadtime_scaler = float(dfile.deadtime)
            scaled_counts.append(signalcounts * deadtime_scaler)
            scaled_counts_unc.append(signalcounts_unc * deadtime_scaler)
       #Times are all given in reference to the last epoch. Let's
        #Scale the start times such that the first run starts at t=0
        tmin=min(starttimes)
        ttime=[]
        for v in starttimes:
            s=v-tmin
            ttime.append(s)
        #We have everything we want for the peak info. now.
        #sort everything by time
        unsorted_peakdata=zip(ttime, scaled_counts, scaled_counts_unc, \
                counttimes, starttimes)
        sorted_peakdata=sorted(unsorted_peakdata, \
                key = lambda t: t[0])#Organize peak areas chronologically
        #Now take the details of each peak and re-organize into a dictionary
        peakdata_dict = {"peak_energy_range": [xmin,xmax], 
                "starttimes": [i[0] for i in sorted_peakdata], \
                "scaled_counts": [i[1] for i in sorted_peakdata], \
                "scaled_counts_unc":[i[2] for i in sorted_peakdata],\
                "counttimes": [i[3] for i in sorted_peakdata]}
        self.current_peakdata = peakdata_dict
        return peakdata_dict

    def hl_expfit(self, pdd):
        '''
        Calculates the half life of the isotope associated with the
        selected peak region count data using an exponential fit.
        pdd = peakdata_dict output by self.choosepeak
        '''
        print('Half-life results from exponential fit of scaled activities:')
        #initialize function we will fit to
        exponential_decay = lambda p, x: p[0]*np.exp(-x*p[1])
        p0=[20.,float(1./42.)]   #Initial guess at counts and decay constant
        function_to_fit = mf.function(exponential_decay, p0, np.min(pdd["starttimes"]), \
        np.max(pdd["starttimes"]))
        print('Initial fit parameters: ' + str(function_to_fit.p0))
        #Define the graph class. Is a basic matplotlib.pyplot wrapper.
        #feed in peak info for each data set
        gr=mf.graph(np.array(pdd["starttimes"]), \
                np.array(pdd["scaled_counts"]))
        gr.adderrorbars(pdd["starttimes"], pdd["scaled_counts"], \
                pdd["scaled_counts_unc"])
        gr.settitle("Total signal counts observed in peak in each counting run")
        gr.setlabels("Time since start of first count data (seconds)", \
                "Background-subracted counts in peak region")
        #Use the fit method to fit the "fitter" mf.function to the data
        bestfit, covariance = gr.fit(function_to_fit)
        function_to_fit.draw_fit() #Draws best fit result found in gr.fit
        initial_count_fit=bestfit[0]
        decay_constant_fit=bestfit[1]
        hlt=lambda x: (1./x)*np.log(2.)
        halfl=hlt(decay_constant_fit)
        print('Fitted CPM at start of first data:' + str(initial_count_fit))
        print('Fitted half-life (in hours): ' + str(halfl/3600.))
        gr.draw() #Adds graph data to current draw space
        gr.show() #Shows current draw space
	
    def hl_countpairs(self, pdd):
        '''
        This function tries to calculate the half life associated with
        the peak given as follows: solve for the half-life with all pairs
        of peak data by relating them to the source activity at counting start.
        '''

        print('Half-life results calculated directly from activity and count times:') 
        k=0
        allhls=[]
        while k < len(pdd["starttimes"]):
            p=k	
            while p < len(pdd["starttimes"])-1:		
                p=p+1
                ti1=pdd["starttimes"][k]
                tf1=pdd["starttimes"][k]+pdd["counttimes"][k]
                ti2=pdd["starttimes"][p]
                tf2=pdd["starttimes"][p]+pdd["counttimes"][p]
                afun= lambda x, y, z: 1/(np.exp(-x*y)-np.exp(-x*z))
                coeff = lambda x: np.exp(x*(ti1-ti2)) * (pdd["scaled_counts"][k]/pdd["scaled_counts"][p])
                #fsolve: solve for x assuming the function given = 0
                lamb=float(fsolve(lambda x: coeff(x) * afun(x, ti1, tf1)-afun(x, ti2, tf2),1e-5))  #Starting point chosen arbitrarily
                hl=((1/lamb)*np.log(2)/3600) #Converted to hrs
                if hl < 0 or hl > 1.0e+09:
                    print('Unphysical half-life ' + str(hl) + 'calculated. ' +\
                            'Issue may be in background subtraction or bad ' +\
                            'peak bounds.  Ignoring value for half-life ' +\
                            'average.')
                else:
                    print('Valid half life calculated. Result: ' + str(hl))
                    allhls.append(hl)
            k=k+1		
        print('Average of all calculated half-lifes: ' + str(np.average(allhls)))
        print('Std. dev. of all calculated half-lifes: ' + str(np.std(allhls)))