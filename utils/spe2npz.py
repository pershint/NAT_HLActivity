# Use this module to convert naa spe text files to npz
# data files containing energy, bin, info

import sys
import numpy as np
import time

def convert(files):
    spe = '.Spe'
    files = [ v for v in files[:] if v.endswith(spe) ]
    for f in files:
        info = grab_info(f)
        x, y = make_data_not_suck(info)
        livetime, totaltime, starttime = make_info_not_suck(info)
        np.savez(f.split(spe)[0], info=info, x=x, y=y, livetime=livetime,
                 totaltime=totaltime, starttime=starttime)
        print('wrote:', f.split(spe)[0])

def grab_info(fname):
    key, value = [], []
    delim = '$'
    value_str = ''
    key_str = 'NULL_KEY'
    with open(fname, 'r') as f:
        for line in f:
            if line.startswith(delim):
                if key_str != 'NULL_KEY':
                    key.append(key_str.rstrip('\r\n')) 
                    value.append(value_str)
                key_str=line.rsplit(delim)[1]
                value_str=''                  #Clear the value
            else:
                value_str+=line
    d=dict(zip(key, value))
    return dict(zip(key, value))

def make_info_not_suck(webster):
    # I want to grab true time, live time, start time
    live_time_str = webster['MEAS_TIM:']
    livetime = int(live_time_str.split()[0])
    totaltime = int(live_time_str.split()[1])

    start_time_str = webster['DATE_MEA:']
    print(start_time_str)
    strtime = start_time_str.split('\r\n')[0]
    timestruct = time.strptime(strtime, '%m/%d/%Y %H:%M:%S')
    starttime = time.mktime(timestruct)
    return livetime, totaltime, starttime

def make_data_not_suck(webster):
    # First line of data is the data range
    data_str = webster['DATA:']
    del(webster['DATA:'])
    data = data_str.split('\r\n')
    e_range = [ int(v) for v in data[0].split(' ') if v != '' ]
    # Remove that first data point
    data = data[1:]
    data = [ v for v in data[:] if v != '' ]
    # Turn the strings into integers in a list
    yaxis = [ int(v.lstrip().rstrip('\r\n')) for v in data[:] ]
    xaxis = np.arange(e_range[0], e_range[1]+1, 1)
    correction = (webster['MCA_CAL:'].split('\n'))[1]
    cfunc = lambda x, k: k[0] + x*k[1] + x*x*k[2]
    k = correction.split()[0:3]
    k = [ float(v) for v in k[:] ]
    xaxis = [ cfunc(v, k) for v in xaxis[:] ]
    
    return xaxis, yaxis    

if __name__ == '__main__':
    convert(files = sys.argv)
