# Example of how to use the half-life class to analyze data
import os, sys
import lib.argparser as p
import lib.datastruct as ds
import lib.analyzers as an
import glob


DEBUG = p.DEBUG

#Define your experiment data and background counting data file locations
MAINDIR = os.path.dirname(__file__)
DATADIR = os.path.abspath(os.path.join(MAINDIR, "data", "ThoriatedLAB_Teal_2017"))
BKGDATADIR = os.path.abspath(os.path.join(MAINDIR, "data","NAT2017_Backgrounds"))

def main():
    listofdatafiles = glob.glob(DATADIR + '/*.npz')
    listofbkgfiles = glob.glob(BKGDATADIR + '/*.npz')

    if DEBUG is True:
        print("PRINTING LIST OF DATA FILES, THEN BACKGROUND FILES")
        print(listofdatafiles)
        print(listofbkgfiles)

    # First, initialize your data structure with all desired data file
    # and background file locations
    alldatafiles = ds.datacollection(listofdatafiles, listofbkgfiles)

    # Load the current list of data files into data to be analyzed
    alldatafiles.load_datafiles()
    #Loads in bkg files for use. Uncomment to calculate bkgs w/ peak sidebands
    alldatafiles.load_bkgdatafiles()

    #FIXME: If DEBUG, show the spectra in the data

    #Now, initialize the analysis class with our data and isotope database
    hl_analyzer = an.halflife(datatoanalyze=alldatafiles)

    #Run will try to calculate the half-life of the selected peak two ways:
    #1) Exponential fit of peak height in all spectra
    #2) Solve for the half-life using each pair of data sets, average over
    #   them, and get the standard deviation of all calculated
    #For details on each algorithm, see the halflife class in /lib/analyzers.py

    hl_analyzer.run()
    if DEBUG is True:
        print("The peak data dictionary found after running is here: ")
        print(hl_analyzer.current_peakdata)



if __name__ == '__main__':
    main()
