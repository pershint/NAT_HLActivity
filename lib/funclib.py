#A library of functions that could be loaded into the function class in mfit.py
#To use in main, add the following at the top of your main.py script
#import lib.tool.funclib as fl
#Then, call the function anywhere in your code using

#fl.gauss
#or whatever function you want!

import numpy as np

exponential_decay = lambda x, C, l: C*np.exp(-x*l)
exponential_decay_pcon = lambda x, C, l, a: a + (C*np.exp(-x*l))
gauss = lambda x, m, s: (s**2*2*np.pi)**(-1/2)*np.exp(-1/2*(x-m)**2/s**2)
breitwigner = lambda x, m, s: 1/( (x**2 - m**2)**2 + (m*s)**2 )
compshoulder = lambda x, m, a, b: sp.erfc((x-m)/a)*np.exp((x-m)/b)
