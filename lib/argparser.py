#WARNING: This library is deprecated.  If you're writing some code,
#You should look into using optparse

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--debug", action="store_true",default="False", \
        help="Print out more information and plots")
parser.add_argument("--useseaborn", action="store_true",default="False", \
        help="Will use seaborn options to prettify plots")
args = parser.parse_args()
DEBUG = args.debug
USESEABORN = args.useseaborn

