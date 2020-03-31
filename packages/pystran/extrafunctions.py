# -*- coding: utf-8 -*-
"""
Created on Sat Oct 27 21:00:33 2012

@author: VHOEYS
"""
import numpy as np


def rescale(arr,vmin,vmax):
    arrout=(vmax-vmin)*arr+vmin
    return arrout

##############################################################################
## TESTFUNCTIONS TO WORK WITH
##############################################################################
    
    
def analgfunc(ai,Xi):
    Y=1.0
    for i in range(len(Xi)):
        try:
            g_Xi=(np.abs(4.*Xi[i]-2.)+ai[i,:])/(1.+ai[i,:])
        except:
            g_Xi=(np.abs(4.*Xi[i]-2.)+ai[i])/(1.+ai[i])            
        Y=Y*g_Xi
    return Y

def analgstarfunc(ai,alphai,Xi,di):
    Y=1.0
    di=np.random.random(10)
    for i in range(len(Xi)):
        g_Xi=((1.+alphai[i])*np.abs(2.*(Xi[i]+di[i]-int(Xi[i]+di[i]))-1.)**alphai[i] + ai[i])/(1.+ai[i])
        Y=Y*g_Xi
    return Y 


def simplelinear(ai,Xi):
    Y = 0.
    for i in range(len(ai)):
        Y=Y+(ai[i]*Xi[i])
    return Y

def harder(ai,Xi):
    Y = 0.
    Xii = np.random.permutation(Xi)
    for i in range(len(ai)):
        Y=Y+(ai[i]*np.exp(ai[i]+Xii[i]))
    return Y
        