############################## mfit.py #########################################
############ Class to implement 1D fitting in a straight forward way #########
############ function class interacts with the graph class to achieve this####
################################################################################
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
import math
import scipy.optimize as scp
import scipy.special as sp

#Wrapper for matplotlib.pyplot with some pre-defined color and plot schemes
class graph:
    """
    Graph object that acts as a wrapper for matplotlib.pyplot.
    Can also fit an input function class to the data given.
    """
    def __init__(self, x, y, yerr=None):
        '''
        Build the graph with given x, y lists or np.arrays
        Saves the members as np.arrays for speed
        ''' 
        self.x, self.y = np.array(x), np.array(y)
        self.yerr = yerr
        self.xmin, self.xmax = 0, len(self.x)
        self.errbar_colors = 'g'
        self.data_colors = 'g'


    def settitle(self, title):
        plt.title(str(title),fontsize=34)

    def setlabels(self, xlabel, ylabel):
        plt.xlabel(str(xlabel),fontsize=20)
        plt.ylabel(str(ylabel),fontsize=20)

    def draw_data(self):
        if self.yerr is None:
            plt.plot(self.x, self.y, 'o', color=self.data_colors,label='data')
        else:
            plt.errorbar(x=self.x, y=self.y, yerr=self.yerr, marker='o', 
                    linestyle='none',color=self.errbar_colors, 
                    linewidth=2, label='data')

    def bounds(self, xmin, xmax):
        self.xmin = np.where(self.x>=xmin)[0][0]
        self.xmax = np.where(self.x<=xmax)[0][-1]

    def fit(self, func):
        '''
        Fit the input function into the data loaded into the graph class.
        Expects a function class object defined below.
        '''
        #Correlate the function's min/max with nearest data points
        xmin, xmax = np.where(self.x>=func.xmin)[0][0], np.where(self.x<=func.xmax)[0][-1]
        p0 = func.p0
        xr = self.x[xmin:(xmax+1)]
        yr = self.y[xmin:(xmax+1)]
        if self.yerr is not None: 
            yu = self.yerr[xmin:(xmax+1)]
            popt, pcov = scp.curve_fit(func.func, xr, yr, p0=p0, sigma=yr) 
        func.pfit = popt
        return popt, pcov #best parameter fits, covariance

    def show(self):
        sns.set_style("whitegrid")
        plt.ioff()
        plt.legend(loc=3) 
        plt.show()

#Class acts as a container for a lambda function, initial paramters associated
#with the function, and the range you want the function to be valid over.
class function:
    def __init__(self, func, p0=[0], xmin=0, xmax=-1):
        self.p0=p0
        self.xmin, self.xmax = xmin, xmax
        self.func = func
        self.pfit = None #fills after fitting funcion to data in the graph class
    
    def draw_fit(self, step_size=0.1):
        steps = (self.xmax-self.xmin)/step_size
        x=np.linspace(self.xmin, self.xmax, steps)
        plt.plot(x, self.func(x, self.pfit[0], self.pfit[1]),color='k',linewidth=3,label='exp_fit')

    def bounds(self, xmin, xmax):
        self.xmin = xmin
        self.xmax = xmax

    def evaluate(self, x):
        return self.func(self.p0, x)

    #Return maximum of function in current bounds
    def get_max(self, step_size=0.1):
        steps = (self.xmax-self.xmin)/step_size
        x=np.linspace(self.xmin, self.xmax, steps)
        y=self.func(self.p0, x)
        ypeak = max(y)
        xpeak = x[np.where(y==ypeak)[0][0]]
        return xpeak, ypeak
    

