#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      VHOEYS
#
# Created:     11/10/2011
# Copyright:   (c) VHOEYS 2011
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

##def main():
##    pass
##
##if __name__ == '__main__':
##    main()

import os
import sys

import numpy as np
from distributions import *

def SampleInputMatrix(nrows,npars,bu,bl,distname='randomUniform'):
    '''
    Create inputparameter matrix for nrows simualtions,
    for npars with bounds ub and lb (np.array from same size)
    distname gives the initial sampling ditribution (currently one for all parameters)

    returns np.array
    '''
    x=np.zeros((nrows,npars))
    bound = bu-bl
    for i in range(nrows):
        x[i,:]=bl + DistSelector([0.0,1.0,npars],distname='randomUniform')*bound
    return x

#TESTFUNCTIONS TO CHECK THE IMPLEMENTATION OF THE SCE ALGORITHM

def testfunctn1(nopt,x):
    '''
    This is the Goldstein-Price Function
    Bound X1=[-2,2], X2=[-2,2]
    Global Optimum: 3.0,(0.0,-1.0)
    '''

    x1 = x[0]
    x2 = x[1]
    u1 = (x1 + x2 + 1.0)**2
    u2 = 19. - 14.*x1 + 3.*x1**2 - 14.*x2 + 6.*x1*x2 +3.*x2**2
    u3 = (2.*x1 - 3.*x2)**2
    u4 = 18. - 32.*x1 + 12.*x1**2 + 48.*x2 -36.*x1*x2 + 27.*x2**2
    u5 = u1 * u2
    u6 = u3 * u4
    f = (1. + u5) * (30. + u6)
    return f

def testfunctn2(nopt,x):
    '''
    %  This is the Rosenbrock Function
    %  Bound: X1=[-5,5], X2=[-2,8]; Global Optimum: 0,(1,1)
        bl=[-5 -5]; bu=[5 5]; x0=[1 1];
    '''

    x1 = x[0]
    x2 = x[1]
    a = 100.0
    f = a * (x2 - x1**2)**2 + (1 - x1)**2
    return f

def testfunctn3(nopt,x):
    '''3
    %  This is the Six-hump Camelback Function.
    %  Bound: X1=[-5,5], X2=[-5,5]
    %  True Optima: -1.031628453489877, (-0.08983,0.7126), (0.08983,-0.7126)
    '''
    x1 = x[0]
    x2 = x[1]
    f = (4 - 2.1*x1**2 + x1**4/3)*x1**2 + x1*x2 + (-4 + 4*x2**2)*x2**2
    return f

def testfunctn4(nopt,x):
    '''4
    %  This is the Rastrigin Function
    %  Bound: X1=[-1,1], X2=[-1,1]
    %  Global Optimum: -2, (0,0)
    '''
    x1 = x[0]
    x2 = x[1]
    f = x1**2 + x2**2 - np.cos(18.0*x1) - np.cos(18.0*x2)
    return f

def testfunctn5(nopt,x):
    '''
    This is the Griewank Function (2-D or 10-D)
    Bound: X(i)=[-600,600], for i=1,2,...,10
    Global Optimum: 0, at origin
    '''
    if nopt==2:
        d = 200.0
    else:
        d = 4000.0

    u1 = 0.0
    u2 = 1.0
    for j in range(nopt):
        u1 = u1 + x[j]**2/d
        u2 = u2 * np.cos(x[j]/np.sqrt(float(j+1)))

    f = u1 - u2 + 1
    return f

def EvalObjF(npar,x,testcase=True,testnr=1,extra=[]):
##    print 'testnummer is %d' %testnr

    if testcase==True:
        if testnr==1:
            return testfunctn1(npar,x)
        if testnr==2:
            return testfunctn2(npar,x)
        if testnr==3:
            return testfunctn3(npar,x)
        if testnr==4:
            return testfunctn4(npar,x)
        if testnr==5:
            return testfunctn5(npar,x)
    else:
		return Modrun(npar,x,extra)          #Welk model/welke objfunctie/welke periode/.... users keuze!






