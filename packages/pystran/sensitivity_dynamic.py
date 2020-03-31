# -*- coding: utf-8 -*-
"""
Created on Sat Mar 16 13:35:03 2013

@author: VHOEYS
"""
import numpy as np
import matplotlib.pyplot as plt

from .sensitivity_base import *
from .sobol_lib import *
from .extrafunctions import *
from .latextablegenerator import *
from .plot_functions_rev import plotbar
from matplotlib import colors


class DynamicSensitivity(SensitivityAnalysis):
    '''
    DYNIA approach 

  
    Parameters
    -----------
    ParsIn : list
        either a list of (min,max,'name') values, 
        [(min,max,'name'),(min,max,'name'),...(min,max,'name')]
        or a list of ModPar instances

    Attributes            
    ------------
    ndim :  intx
        number of factors examined. In case the groups are chosen the number 
        of factors is stores in NumFact and sizea becomes the number of created groups, (k)
        
    Notes
    ---------


    Examples
    ------------
    >>> Xi = [(0.0,5.0,r'$X_1$'),(4.0,7.0,r'$X_2$'),(0.0,1.0,r'$X_3$'), 
              (0.0,1.0,r'$X_4$'), (0.0,1.0,r'$X_5$'),(0.5,0.9,r'$X_6$')]
 
    References
    ------------

    
    '''
    
    def __init__(self, ParsIn, ModelType = 'external'):
        SensitivityAnalysis.__init__(self, ParsIn)

        self.methodname = 'Regression_merged'
        
        if ModelType == 'pyFUSE':
            self.modeltype = 'pyFUSE'
            print('\t - The analysed model is built up by the pyFUSE environment')
        elif ModelType == 'external':
            self.modeltype = 'pyFUSE'           
            print('\t - The analysed model is externally run'            )
        elif ModelType == 'PCRaster':
            self.modeltype = 'PCRasterPython'
            print('\t - The analysed model is a PCRasterPython Framework instance')
        elif ModelType == 'testmodel':
            self.modeltype = 'testmodel'
            print('\t - The analysed model is a testmodel'            )
        else:
            raise Exception('Not supported model type')

        self.LB = np.array([el[0] for el in self.ParsIn])
        self.UB = np.array([el[1] for el in self.ParsIn])


#    def timeserie_visualisation():
#        '''
#        If output is not a list of different outputs or Objective, functions,
#        but a timeserie output,
#        focus is on timeserie investigation of the model to get information in time
#        and decide about the objective functions to use!
#        
#        visualize the sensitivities aroudn different parameters
#        1. distribution of the SENS with different par values during time (par in y-axis)
#        2. rankings of par during time (discrete kleurcodes), pars in y-axis, discrete colors
#        3. sensitivity in y-axis