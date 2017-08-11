#HALF-LIFE CALCULATOR FOR NAT2017 SUMMER SCHOOL - GAMMA1 and GAMMA3

The following program can be used to solve for the half-life of an isotope
associated with a gamma line chosen by the user. To see options:

python main.py --help

main.py will load in counting data and background data directories defined
at the top of main.py, initialize the data in the datacollection class for
containment, and feed the contained data to the halflife analyzer class.

When run, the halflife analyzer class will ask for a peak range of interest.
Once the user puts in the peak range, the program will find the total counts
for each peak in each data set, organize the data by time, and find the best
fit to an exponential.  The analyzer will output the best fit half life.

As of writing this, there are four directories and a main script.  A brief
Description of each, their contents, and their applications can be found below.


#################### /utils/ ###################
spe2npz.py: This script is used to convert .spe format files (fed out of the
MAESTRO program) into npz files.  These are generally easier to interact with
in python.

To use the program...

python spe2npz.py /path/to/file1.spe /path/to/file2.spe 

And so on.  To do an entire directory of .spe files, type

python spe2npz.py /all/files/in/*

*################## /data/ ################
A directory for holding all of your data associated with HPGe counting
experiments.  These directories will be pointed to in main.py for use.

################### /doc/ #################
A directory for holding any documents associated with your experiment or
the activity.  Feel free to write some notes in here, or start some
subdirectories for any tex files you want to write or whatever.

################## /lib/ ##################

This holds the main backend mechanics that are called in the main script.

lib/datastruct.py: Contains two classes.  

The datafile class takes in a 
file location (.npz format files), and loads the data into easy to access
constants (see the prepare_data function).

The datacollection class acts as a container for loading datafile classes.
The datafiles are organized into experimental data (self.opendatafiles in
the datacollection class) and background data (self.openbkgfiles in the
datacollection class).

lib/analyzers.py: Contains all classes assocated with performing data analysis.
Currently, only a halflife class is implemented.

The halflife class takes in a datacollection class on initialization.  When
halflife.run() is called, the user will be asked to input an energy range
associated with their gamma peak of interest.  The method then calculates
the background subtracted counts for each file and plots them as a function of
time (t=0 is set for the file with the earliest start time).  Finally, an
exponential is fit to the points to find the best fit decay constant.

lib/tool/mfit.py: Containes two classes.  

The function class that holds a
1D lambda function along with some constants like the function range and
initial function parameters.  Also contains a draw function to plot the
function over a graph class.

The graph class is essentially a matplotlib.pyplot wrapper for graphing 1D
data.  When a function class is fed into the fit method, the input function
is fit to the data contained in the graph class.  
