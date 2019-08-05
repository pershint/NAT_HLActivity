#i####################Half-Life Calculator#########################
#Program designed to take in a list of pynaa files, integrate over a  #
#peak in each, Plot the areas as a function of time, and fit to an    #
#exponential to Estimate the Half-life of the element                 #

##TO-DO##
# * Re-write so the program runs over all peaks in an experiment #
# * Have the program output a data file with peaks and associated#
#   Half-lives found for each peak using both methods            #

import sys
import scipy.optimize as scp
from scipy.optimize import fsolve
from os import listdir
import operator
import time
from . import funclib as fl
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

class halflife(object):
    '''
    Input is a datacollection class containing multiple
    HPGe spectra in a .npz file format. Calculates the
    half-life of a decaying peak associated with a
    region selected by the user
    '''

    def __init__(self):
        self.name = 'halflife'
        self.usebkgdata = False
        self.current_peakdata = {}
        self.peak_left = None
        self.peak_right = None


    def run_analysis(self,datacollection):
        '''
        Default is to calculate the half life using an exponential fit to
        count data of one peak.
        '''
        peakdata_dict=self.analyze_peak(datacollection.opendatafiles, \
                datacollection.openbkgfiles)
        self.hl_expfit(peakdata_dict)
        #uncomment to calculate half-life using pairs of peak data
        #self.hl_countpairs(peakdata_dict)

###Functions used by the half-life calculator
    def _inputvalid(self, xl, xr):
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

    def show_spectrum(self, datafile):
            '''
            Shows the plot of the HPGe spectrum for the input datafile.
            '''
            x,y = dfile.x, dfile.y
            sns.set_style("whitegrid")
            xkcd_colors = ['black','purple']
            sns.set_palette(sns.xkcd_palette(xkcd_colors))

            plt.ion()
            plt.plot(x,y, alpha=0.8, color='r')
            plt.title('Spectrum for file: ' + str(datafile.name))
            plt.set_xlabel('Energy (keV)')
            plt.set_ylabel('Counts')
            plt.show()

    def _calc_deadtcorrcounts(self, bkgdatafile_arr, counttime, peakrange):
        '''
        Given some time interval, the detector was only able to see counts when not
        acquiring data (dead time).  Returns the background counts expected
        if the detector had no dead time for the given peak range.
        '''
        #FIXME: I should calculate the error on the bkg measurement here.
        #Currently, I'm overestimating errors on the bkg.
        timecorrected_bkgcounts = []
        for bfile in bkgdatafile_arr:
            x,y=bfile.energy, bfile.counts
            bkg_counts=np.sum(y[peakrange[0]:peakrange[1]])
            timecorr = float(bkg_counts) * (float(counttime)/float(bfile.tstop - bfile.tstart))
            timecorrected_bkgcounts.append(timecorr)
        #Now, average your background values
        bcounts = np.average(np.array(timecorrected_bkgcounts))
        return bcounts

    def choose_peak(self,xleft,xright):
        '''
        Inputs choose the peak region to perform the analysis over.
        '''
        if not self._inputvalid(xleft, xright):
            print("Input left and right bins are not valid.  Please give valid entries.")
            return
        self.peak_left = xleft
        self.peak_right = xright
    
    def show_stackplot(self, opendatafiles,x_range=None):
        '''
        Loops through all data in the datacollection class and plots the x,y
        data for all datafiles.
        '''
        sns.set_style("whitegrid")
        sns.set_context("poster")
        fig=plt.figure(figsize=(20,20))
        plt.ion()
        for dfile in opendatafiles: #Loop overy every data file for peak info
            x,y=dfile.energy,dfile.counts
            plt.plot(x,y) #Uses first file for user to choose peak of interest
        plt.xlabel("Energy (keV)",fontsize=20)
        plt.ylabel("Counts",fontsize=20)
        plt.title('Stack plot of all data in data collection.',fontsize=30)
        if x_range is not None:
            plt.xlim(x_range[0],x_range[1])
        plt.show()
    
    def analyze_peak(self, datafile_arr, bkgdatafile_arr=None):
        '''
        Function takes in a datacollection class object and returns
        the start time, total counts, total counts deadtcorr for if
        there was no dead time, and the total counting time taken
        for a peak region input by the user.
        '''
        if self.peak_left is None or self.peak_right is None:
            print("Please choose your peak bounds prior to running.")
            return
        deadtcorr_totcnts=[] #Counts with a correction for deadtime
        bkgcounts=[]
        starttimes=[] #Start time of each datafile
        counttimes=[] #Total count time of each datafile
        deadtimes=[] #Total fraction of time the HPGe was dead while
                     #collecting data
        have_peakmid = False
        for dfile in datafile_arr: #Loop overy every data file for peak info
            counttime = float(dfile.tstop-dfile.tstart)
            counttimes.append(counttime)
            starttimes.append(float(dfile.tstart))
            x,y=dfile.energy,dfile.counts
            if not have_peakmid:
                xleft=self.peak_left
                xright=self.peak_right
                xmin=np.where(x<self.peak_left)[0][-1] #array index of point just below xleft
                xmax=np.where(x>self.peak_right)[0][0] #arr index of point just above xright
                hpw=int(len(x[xmin:xmax])/2) #Mid-point of peak
                have_peakmid=True
            totcounts=float(np.sum(y[xmin:xmax])) #Total counts in peak regoin
            #The activity needs to be corrected to account
            #for dead time during the counting run.
            deadtime_scaler = float(dfile.livefraction) 
            deadtcorr_totcnts.append(totcounts *  deadtime_scaler)
            #Calculate bakground rate of peak
            if self.usebkgdata is True:
                bkg = self._calc_deadtcorrcounts(bkgdatafile_arr, \
                        counttime, [xmin,xmax])
            else:
                bgl=sum(y[(xmin-hpw):xmin]) #Backgrounds calculated from left and right sides of peak
                bgr=sum(y[xmax:(xmax+hpw)])
                bg=bgl+bgr
                bkg = (bg * deadtime_scaler)
            bkgcounts.append(float(bkg))
        #Times are all given in reference to the last epoch. Let's
        #Scale the start times such that the first run starts at t=0
        tmin=min(starttimes)
        ttimes=[]
        for v in starttimes:
            s=v-tmin
            ttimes.append(float(s))
        #We have everything we want for the peak info. now.
        #sort everything by time
        unsorted_peakdata=zip(ttimes, deadtcorr_totcnts, bkgcounts, \
                counttimes, starttimes)
        sorted_peakdata=sorted(unsorted_peakdata, \
                key = lambda t: t[0])#Organize peak areas chronologically
        #Now take the details of each peak and re-organize into a dictionary
        peakdata_dict = {"peak_energy_range": [xleft,xright], 
                "starttimes": [i[0] for i in sorted_peakdata], \
                "deadtcorr_totcnts": [i[1] for i in sorted_peakdata], \
                "bkgcounts":[i[2] for i in sorted_peakdata],\
                "counttimes": [i[3] for i in sorted_peakdata]}
        self.current_peakdata = peakdata_dict
        return peakdata_dict

    def peakcounts_vstime(self, pdd):
        '''
        Plots the integral of peak counts with background subtraction included. 
        '''
        bksub_rates = (np.array(pdd["deadtcorr_totcnts"]) - \
                np.array(pdd["bkgcounts"]))/ np.array(pdd["counttimes"])
        bksub_rates_unc = np.sqrt(np.array(pdd["deadtcorr_totcnts"]) + \
                np.array(pdd["bkgcounts"])) / np.array(pdd["counttimes"])
        plt.errorbar(x=(np.array(pdd["starttimes"])+(np.array(pdd["counttimes"])/2.)), \
                y=bksub_rates,yerr=bksub_rates_unc, marker='o', 
                    linestyle='none',color='g', 
                    linewidth=2, label='data')
        plt.title("Total signal counts observed\n in peak in each counting run")
        plt.xlabel("Time since start of first count data (seconds)")
        plt.ylabel("Background-subracted counts per second \n in peak region")
        plt.show() #Shows current draw space

    def hl_expfit(self, pdd, fitrange = None):
        '''
        Calculates the half life of the isotope associated with the
        selected peak region count data using an exponential fit.
        pdd = peakdata_dict output by self.choosepeak
        '''
        print('Half-life results from exponential fit of deadtcorr activities:')
        bksub_rates = (np.array(pdd["deadtcorr_totcnts"]) - \
                np.array(pdd["bkgcounts"]))/ np.array(pdd["counttimes"])
        bksub_rates_unc = np.sqrt(np.array(pdd["deadtcorr_totcnts"]) + \
                np.array(pdd["bkgcounts"])) / np.array(pdd["counttimes"])
        timebins = (np.array(pdd["starttimes"])+(np.array(pdd["counttimes"])/2.))
        plt.errorbar(x=timebins, \
                y=bksub_rates,yerr=bksub_rates_unc, marker='o', 
                    linestyle='none',color='g', 
                    linewidth=2, label='data')
        plt.title("Total signal counts observed\n in peak in each counting run")
        plt.xlabel("Time since start of first count data (seconds)")
        plt.ylabel("Background-subracted counts per second \n in peak region")
        
        #Now, perform the fit across the entire range 
        fit_function=fl.exponential_decay
        xmin = 0 
        xmax = len(timebins) - 1
        if fitrange is not None:
            xmin, xmax = np.where(timebins>=fitrange[0])[0][0], np.where(timebins<=fitrange[1])[0][-1]
        p0=[np.average(bksub_rates),float(1./42000.)]   #Initial guess at counts and decay constant
        xr = timebins[xmin:(xmax+1)]
        yr = bksub_rates[xmin:(xmax+1)]
        yu = bksub_rates_unc[xmin:(xmax+1)]
        popt, pcov = scp.curve_fit(fit_function, xr, yr, p0=p0, sigma=yu)
        step_size = 0.1
        steps = (timebins[xmax]-timebins[xmin])/step_size
        fit_x=np.linspace(timebins[xmin], timebins[xmax], steps)
        plt.plot(fit_x, fit_function(fit_x, popt[0], popt[1]),color='k',linewidth=3,label='exp_fit')
        plt.show()
        #Display the fit results
        initial_count_fit=popt[0]
        decay_constant_fit=popt[1]
        #residual_fit = bestfit[2]
        hlt=lambda x: (1./x)*np.log(2.)
        hltunc = lambda x,xunc: (float(xunc)/float(x**2))*np.log(2.) 
        halfl=hlt(decay_constant_fit)
        halflunc = hltunc(decay_constant_fit, np.sqrt(np.diag(pcov))[1])
        print('Fitted CPS at start of first data:' + str(initial_count_fit))
        print('Fitted half-life (in hours): ' + str(halfl/3600.))
        #print('Fitted const. offset (CPM): ' + str(str(bestfit[2]))) 
        print('Covariance matrix for fitted parameters: ' + str(pcov))
        print('Standard error of initial CPS fitted: ' + str(np.sqrt(np.diag(pcov))[0]))
        print('Standard error of half-life: ' + str(halflunc/3600.))
	
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
                bksub_rates = (np.array(pdd["deadtcorr_bkgcnts"]) - \
                        np.array(pdd["counts"]))/ \
                        np.array(pdd["counttimes"])
                coeff = lambda x: np.exp(x*(ti1-ti2)) * (subrates[k]/ \
                        subrates[p])
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
