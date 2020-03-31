"""
Created on Wed Oct 10 16:37:52 2012
@author: VHOEYS

PROBABILITY DISTRIBUTIONS

A more extended set of distributions is available in the scipy.stats library,
http://docs.scipy.org/doc/scipy/reference/stats.html
or by pymc: https://pymc-devs.github.io/pymc/distributions.html
"""

#Import general packages
import math
import numpy as np

def NormalizePDF(inputs):
    '''
    Sum of all elements becomes 1
    '''
    normed = inputs/inputs.sum()
    return normed

def Normalize(inputs):
    '''
    Normalization, values recalculated between 0 and 1
    '''
    Normed=(inputs-min(inputs))/(max(inputs)-min(inputs))
    return Normed

#########################################################################
# PDF   Get probability value for a certain input!                     ##
#########################################################################

def UniformDistribution(x, left=0.0, right=1.0, val=1.0):
    '''
    Probability is 1. when in the region
    '''
    if left<=x<=right:
        px=val
    else:
        px=0.0
    return px

def TriangularDistribution(x,left,mode,right):
    '''
    Calculates the "weight factor" of triangular, based on a certain inputvalue

    see numpy manual (or Beven_book: left=0, right=1)
    '''
    if mode>right:
        print('right en mode zijn omgewisseld!!')
    if left<=x<=mode:
        px=2*(x-left)/((right-left)*(mode-left))
    elif mode<=x<=right:
        px=2*(right-x)/((right-left)*(right-mode))
    else:
        px=0.0
    return px

def TrapezoidalDistribution(x,left,mode1,mode2,right):
    '''
    Calculates the "weight factor" of trapezoidal
     based on a certain inputvalue
    '''
    if mode1>right:
        print('right en mode1 zijn omgewisseld!!')
    if mode2>right:
        print('right en mode2 zijn omgewisseld!!')
    if mode1>mode2:
        print('mode1 en mode2 zijn omgewisseld!!')

    u=2/(right+mode2-mode1-left)

    if left<=x<=mode1:
        px=u*(x-left)/(mode1-left)
    elif mode1<=x<=mode2:
        px=u
    elif mode2<=x<=right:
        px=u*(right-x)/(right-mode2)
    else:
        px=0.0
    return px

def NormalDistribution(x, mu=0.0, sigma=1.0, wholePDF=True,left=None,right=None):
    if wholePDF == True:
        px=1*np.exp(- (x - mu)**2 / (2 * sigma**2)) /(sigma * np.sqrt(2 * np.pi))
    else:           #cut boundaries to use it as membership function
        if left<=x<=right:
            px=1*np.exp(- (x - mu)**2 / (2 * sigma**2)) /(sigma * np.sqrt(2 * np.pi))
        else:
            px=0.0
    return px

def LogNormalDistribution(x, mu=0.0, sigma=1.0, wholePDF=True,left=0.0,right=None):
    if wholePDF == True:
        px = np.exp(-(np.log(x) - mu)**2 / (2 * sigma**2))/(x * sigma * np.sqrt(2 * np.pi))
    else:
        if left<=x<=right:
            px = np.exp(-(np.log(x) - mu)**2 / (2 * sigma**2))/(x * sigma * np.sqrt(2 * np.pi))
        else:
            px=0.0
    return px

##########################################################################
##RANDOM SAMPLING                                                       ##
##########################################################################

#Uniform
def randomUniform(left=0.0,right=1.0,rnsize=None):
    '''
    link to uniform sampling of numpy, to remain consistency in names
    of the pyFUSE module

    Parameters
    ----------
    left: float
        lower value
    right: float
        upper value
    rnsize: int
        number of samples

    See Also
    ---------
    numpy.random.uniform
    '''
    rn=np.random.uniform(left,right,rnsize)
    return rn

#triangular
def randomTriangular(left=0.0, mode=None, right=1.0, rnsize=None):
    '''
    link to triangular sampling of numpy, to remain consistency in names
    of the pyFUSE module

    Parameters
    ----------
    left: float
        lower value
    mode: float
        value between left and right, highest probability
    right: float
        upper value
    rnsize: int
        number of samples

    See Also
    ---------
    numpy.random.triangular
    '''

    if mode==None:
        print('Triangular needs mode-value')
    rn=np.random.triangular(left, mode, right, rnsize)
    return rn

#trapezoidal
def randomTrapezoidal(left=0.0, mode1=None, mode2=None,
                      right=1.0, rnsize=None):
    '''
    random sampling from trapezoidal function

    Parameters
    ----------
    left: float
        lower value
    mode1: float
        value between left and right, highest probability left side
    mode2: float
        value between left and right, highest probability right side
    right: float
        upper value
    rnsize: int
        number of samples

    '''
    if mode1==None:
        print('Triangular needs 2 mode-values')
    if mode1==None:
        print('Triangular needs 2 mode-values')

    rn=np.zeros(rnsize)
    for i in range(np.size(rn)):
        y = np.random.uniform(0.0,1.0,1)
        h=2/(right+mode2-mode1-left)

        a=left
        b=right
        c=mode1
        d=mode2

        if 0.0<=y<=(h*(c-a)/2):
            rn[i]=a+np.sqrt(2*(c-a)/h)*np.sqrt(y)
        elif (h*(c-a)/2)<=y<=(1-h*(b-d)/2):
            rn[i]=(a+c)/2 + y/h
        elif (1-h*(b-d)/2)<=y<=1.0:
            rn[i]=b-np.sqrt(2*(b-d)/h)*np.sqrt(1-y)
        else:
            print('not in correct range')
    return rn

#Normal
def randomNormal(mu=0.0, sigma=1.0, rnsize=None):
    '''
    link to sampling of normal distribution of numpy, to remain consistency in names
    of the pyFUSE module

    Parameters
    ----------
    mu: float
        mean value
    sigma: float
        Standard deviation (spread or 'width') of the distribution
    rnsize: int
        number of samples

    See Also
    ---------
    numpy.random.normal
    '''

    rn=np.random.normal(mu, sigma, rnsize)
    return rn

#lognormal
def randomLogNormal(mu=0.0, sigma=1.0, rnsize=None):
    '''
    link to sampling of lognormal distribution of numpy, to remain consistency in names
    of the pyFUSE module

    Parameters
    ----------
    mu: float
        Mean value of the underlying normal distribution
    sigma: float
        Standard deviation of the underlying normal distribution
    rnsize: int
        number of samples

    See Also
    ---------
    numpy.random.lognormal
    '''

    rn=np.random.lognormal(mu, sigma, rnsize)
    return rn

#distribution selector
def DistSelector(args,distname='randomUniform'):
    if distname =='randomUniform':
        return randomUniform(left=args[0],right=args[1],rnsize=args[2])
    elif distname =='randomTriangular':
        return randomTriangular(left=args[0], mode=args[1], right=args[2], rnsize=args[3])
    elif distname =='randomTrapezoidal':
        return randomTrapezoidal(left=args[0],mode1=args[1],mode2=args[2],right=args[3],rnsize=args[4])
    elif distname =='randomNormal':
        return randomNormal(mu=args[0], sigma=args[1], rnsize=args[2])
    elif distname =='randomLogNormal':
        return randomLogNormal(mu=args[0], sigma=args[0], rnsize=args[0])
    else:
        raise Exception("""
                        Wrong ditribution name; choose from:
                        randomUniform, randomTriangular,
                        randomTrapezoidal, randomNormal,
                        randomLogNormal
                        """)

##########################################################################
##INVERSE DISTRIBUTIONS (from uniform to other distributions sampling)  ##
##########################################################################

def stnorm2norm(stn,mu,sigma):
    return sigma*stn + mu

def ltqnorm(p):
    """
    Modified from the author's original perl code (original comments follow below)
    by dfield@yahoo-inc.com.  May 3, 2004.

    Lower tail quantile for standard normal distribution function.

    This function returns an approximation of the inverse cumulative
    standard normal distribution function.  I.e., given P, it returns
    an approximation to the X satisfying P = Pr{Z <= X} where Z is a
    random variable from the standard normal distribution.

    The algorithm uses a minimax approximation by rational functions
    and the result has a relative error whose absolute value is less
    than 1.15e-9.

    Author:      Peter John Acklam
    Time-stamp:  2000-07-19 18:26:14
    E-mail:      pjacklam@online.no
    WWW URL:     http://home.online.no/~pjacklam
    """

    if p <= 0 or p >= 1:
        # The original perl code exits here, we'll throw an exception instead
        raise ValueError( "Argument to ltqnorm %f must be in open interval (0,1)" % p )

    # Coefficients in rational approximations.
    a = (-3.969683028665376e+01,  2.209460984245205e+02, \
         -2.759285104469687e+02,  1.383577518672690e+02, \
         -3.066479806614716e+01,  2.506628277459239e+00)
    b = (-5.447609879822406e+01,  1.615858368580409e+02, \
         -1.556989798598866e+02,  6.680131188771972e+01, \
         -1.328068155288572e+01 )
    c = (-7.784894002430293e-03, -3.223964580411365e-01, \
         -2.400758277161838e+00, -2.549732539343734e+00, \
          4.374664141464968e+00,  2.938163982698783e+00)
    d = ( 7.784695709041462e-03,  3.224671290700398e-01, \
          2.445134137142996e+00,  3.754408661907416e+00)

    # Define break-points.
    plow  = 0.02425
    phigh = 1 - plow

    # Rational approximation for lower region:
    if p < plow:
       q  = math.sqrt(-2*math.log(p))
       return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
               ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)

    # Rational approximation for upper region:
    if phigh < p:
       q  = math.sqrt(-2*math.log(1-p))
       return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
                ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)

    # Rational approximation for central region:
    q = p - 0.5
    r = q*q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
           (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)

def ltqnormarr(parr, mu=0.0, sigma=1.):
    stnorm=np.array([ltqnorm(p) for p in parr])
    print(type(stnorm))
    return stnorm2norm(stnorm, mu, sigma)
