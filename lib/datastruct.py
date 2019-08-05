###################DATA STRUCTURE AS USED BY halflife.py##################
# data collection is a class that holds a list of datafile classes. It   #
#Effectively acts as a container for .npz format data files.This approach#
#  makes the handling of many files more managable in                    #
# both the halflife.py library and the main script.                      #
# File originally written by Morgan Askins in the "naa" git repository on#
# MorganAskins github user repositories. Modified for use by Teal Pershing#

import os
import numpy as np


class datacollection:
    '''
    Contains collections of datafile class types and data objects
    Space for data files from an experiment, and background count data
    '''
    def __init__(self,listofdatafiles=[], listofbkgdatafiles=[]):
        self.datafilenames = listofdatafiles   #array of strings
        self.bkgfilenames = listofbkgdatafiles #array of strings
        self.opendatafiles = []                #array of datafiles
        self.openbkgfiles = []             #array of datafiles

    #Clears all file names and loaded files from the datacollection
    def clear_all(self):
        self.datafilenames = []
        self.bkgfilenames = []
        self.opendatafiles = []
        self.openbkgfiles = []

    #load in all datafiles named in self.bkgfilenames
    def load_bkgdatafiles(self):
        for filename in self.bkgfilenames:
            try:
                self.openbkgfiles.append(datafile(filename))
            except (NameError, FileNotFoundError, OSError) as er:
                print(filename + 'Was not found.  Continuing to other files')
                continue

    def get_bkgdatafile(self, filename):
        for j, name in enumerate(self.bkgfilenames):
            if filename == name:
                return self.openbkgdatafiles[j]
        print("Filename not found in currently loaded data collection.")
        return None

    #load in all datafiles named in self.datafilenames
    def load_datafiles(self):
        for filename in self.datafilenames:
            try:
                self.opendatafiles.append(datafile(filename))
            except (NameError, FileNotFoundError, OSError) as er:
                print(filename + 'Was not found.  Continuing to other files')
                continue

    def get_datafile(self, filename):
        for j, name in enumerate(self.datafilenames):
            if filename == name:
                return self.opendatafiles[j]
        print("Filename not found in currently loaded data collection.")
        return None

class datafile:
    '''
    Contains information on a single data file
    '''
    def __init__(self, filename):
        ''' filetype should be sample or background '''
        self.name = filename
        extension = self.name.split('.')[-1]
        if not os.path.isfile(self.name):
            raise FileNotFoundError(self.name+' not found ...')
        if self.name.endswith('.npz'):
            pass
        elif self.name.endswith('.h5'):
            raise NameError(extension + ' not YET supported')
        else:
            raise NameError(extension + ' not supported')
        self.prepare_data()

    def prepare_data(self):
        '''
        Loads the data from the npz file into np.arrays
        This initialized: self.data, self.x, self.y, self.nfo
        self.tstart, self.tstop, and self.deadtime
        '''
        self.data = np.load(self.name)
        self.energy, self.counts = self.data['energy'], self.data['counts']
        self.tstart = self.data['starttime']
        self.tstop = self.tstart + self.data['totaltime']
        self.livefraction = float(self.data['livetime'])/float(self.data['totaltime'])
