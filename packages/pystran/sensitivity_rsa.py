# -*- coding: utf-8 -*-
"""
@author: VHOEYS
development supported by Flemish Institute for Technological Research (VITO)
"""

import os
import numpy as np
import numpy.ma as ma

from .sensitivity_base import *


from .sobol_lib import *
from .extrafunctions import *

class RegionalSensitivity(SensitivityAnalysis):
    '''
    Regional Sensitivity Analysis (Monte Carlo Filtering).
    
    Parameters
    -----------
    ParsIn : list
        either a list of (min,max,'name') values, 
        [(min,max,'name'),(min,max,'name'),...(min,max,'name')]
        or a list of ModPar instances
        
    ModelType : pyFUSE | PCRaster | external
        Give the type of model working with
        
    Attributes
    -------------

        
    Examples
    ------------

    
    Notes
    --------
    The method basically ranks/selects parameter sets based on a evaluation 
    criterion and checks the marginal influence of the different parameters
    on this criterion. In literature, the method is known as Regional 
    Sensitivity Analysis (RSA, [R1]_), but also describe in [R2]_ and referred
    to as Monte Carlo Filtering. Intially introduced by [R1]_ with a split
    between behavioural and non-behavioural accombined with a Kolmogorov-
    smirnov rank test (necessary, but nof sufficient to determine insensitive),
    applied with ten-bins split of the behavioural by [R3]_ and a ten bins
    split of the entire parameter range by [R4]_.
    
    The method is directly connected to the GLUE approach, using the 
    behavioural simulation to define prediction limits of the model output. 
    Therefore, this class is used as baseclass for the GLUE uncertainty.

    References
    ------------
    ..  [R1] Hornberger, G.M., and R.C. Spear. An Approach to the Preliminary 
        Analysis of Environmental Systems. Journal of Environmental 
        Management 12 (1981): 7–18.
    ..  [R2] Saltelli, Andrea, Marco Ratto, Terry Andres, Francesca Campolongo, 
        Jessica Cariboni, Debora Gatelli, Michaela Saisana, and Stefano 
        Tarantola. Global Sensitivity Analysis, The Primer. 
        John Wiley & Sons Ltd, 2008.
    ..  [R3] Freer, Jim, Keith Beven, and Bruno Ambroise. Bayesian Estimation 
        of Uncertainty in Runoff Prediction and the Value of Data: An 
        Application of the GLUE Approach. Water Resources Research 32, 
        no. 7 (1996): 2161. 
        http://www.agu.org/pubs/crossref/1996/95WR03723.shtml.
    ..  [R4] Wagener, Thorsten, D. P. Boyle, M. J. Lees, H. S. Wheater, 
        H. V. Gupta, and S. Sorooshian. A Framework for Development and 
        Application of Hydrological Models. Hydrology and Earth System 
        Sciences 5, no. 1 (2001): 13–26.
 
    '''
    
    def __init__(self, parsin, ModelType = 'pyFUSE'):
        SensitivityAnalysis.__init__(self, parsin)

        self._methodname = 'RegionalSensitivityAnalysis'
        
        if ModelType == 'pyFUSE':
            self.modeltype = 'pyFUSE'
            print ('The analysed model is built up by the pyFUSE environment')
        elif ModelType == 'external':
            self.modeltype = 'pyFUSE'           
            print ('The analysed model is externally run'            )
        elif ModelType == 'PCRaster':
            self.modeltype = 'PCRasterPython'
            print ('The analysed model is a PCRasterPython Framework instance')
        elif ModelType == 'testmodel':
            self.modeltype = 'testmodel'
            print ('The analysed model is a testmodel'            )
        else:
            raise Exception('Not supported model type')
        
    def PrepareSample(self, nbaseruns, seedin=1):
        '''
        Sampling of the parameter space. No specific sampling preprocessing
        procedure is needed, only a general Monte Carlo sampling of the 
        parameter space is expected. To improve the sampling procedure, 
        Latin Hypercube or Sobol pseudo-random sampling can be preferred. The 
        latter is used in the pySTAN framework, but using the ModPar class
        individually enables Latin Hypercube and random sampling.
        
        Currently only uniform distributions are supported by the framework,
        but the Modpar class enables other dsitributions to sample the 
        parameter space and bypassing the sampling here.
        
        Parameters
        ------------
        nbaseruns : int
            number of samples to take for the analysis; highly dependent from
            the total number of input factors. range of 10000s is minimum.
        seedin : int
            seed to start the Sobol sampling from. This enables to increase
            the sampling later on, by starting from the previous seedout.

        Returns
        ---------
        seed_out : int
            the last seed, useful for later use
        parset2run : ndarray
            parameters to run the model (nbaseruns x ndim)
            
        Notes
        -------
        * Do the Sobol sampling always for the entire parameter space at the 
        same time, for LH this doesn't matter
        * Never extend the sampling size with using the same seed, since this
        generates duplicates of the samples
        
        '''
        self.nbaseruns = nbaseruns
        # generate a (N,2k) matrix with 
        FacIn = self._parsin

        Par2run = np.zeros((nbaseruns,self._ndim))
        
        for i in xrange(1, nbaseruns+1):   
            [r, seed_out] = i4_sobol(self._ndim, seedin)
            Par2run[i-1,:] = r        
            seedin = seed_out

        for i in range(self._ndim):
            Par2run[:,i] = rescale(Par2run[:,i], FacIn[i][0], 
                                        FacIn[i][1])    
        self.parset2run = Par2run
        
        return seed_out        
        
# In the new version of GLUE, the idea is that the the output-matrix is put 
# in memory and no copy is made by deleting certain rows. 
# Selecting certain criteria only prepares a mask for the masked 
# array 

#other possibility is the use of the hdf5-stuff, waarbij gesaved en dan telkens
# lijnen nemen naar believen..

    #first delete the outputs with OF=nan or OF= inf/-inf
    def checkprobs(arrtocheck):
        '''
        '''
        
        np.isnan(arrtocheck).any()
        np.isinf(tt).any()

    def select_behavioural(self, output, method='treshold', threshold=0.0, 
                           percBest=0.2, norm=True , mask = True): #ofwel gewoon beide op None en wat niet None, dat doorrekenen
        '''
        Select bevahvioural parameter sets, based on output evaluation 
        criterion used. 
        w
        The algorithm makes only a 'mask' for further operation, in order to
        avoid memory overload by copying matrices
        
        Parameters
        -----------
        threshold : 
        
        output : ndarray
            Nx1
        
        
        
        Method can be 'treshold' based or 'percentage' based
        All arrays must have same dimension in 0-direction (vertical); output-function only 1 column
        InputPar is nxnpar; output is nx1; Output nxnTimesteps
        this most be done for each structure independently

        Output of OFfunctions/Likelihoods normalised or not (do it if different likelihoods have to be plotted together)
        '''
        #by using copy, reference is used and no copy (memory-use)
        #keep_mask is false, so every value is used
        #first mask the outputs with OF=nan or OF= inf/-inf
        if mask == True:
            #self.ma_output = ma.masked_invalid(output, copy=False, keep_mask = False)
            #self.ma_pars = ma.masked_invalid(self.parset2run, copy=False, keep_mask = False)
    
            self.ma_output = ma.masked_invalid(output, copy=False)
            self.ma_pars = ma.masked_invalid(self.parset2run, copy=False)
        else:
            self.ma_output = output
            self.ma_pars = self.parset2run


        if method == 'treshold':
            if mask == True:
                self.ma_output = ma.masked_where(self.ma_output < threshold, self.ma_output, copy=False)
                self.ma_pars = ma.masked_where(self.ma_output < threshold, self.ma_pars, copy=False)
            else:
                self.ma_output = self.ma_output < threshold, self.ma_output
                self.ma_pars = self.ma_output < threshold, self.ma_pars
            InputPar_Behav = self.ma_pars
            output_Behav = self.ma_output

        elif method == 'percentage':
            nr = np.size(InputPar,0)
            ind = argsort(output)  #Geeft indices van de slechtste eerst weer
            NbIndic=int(round((1-percBest)*ind.size))  #Percentage Indices selecteren
            indBad=ind[:NbIndic]   #Slechtste bepalen om weg te doen
            output_Behav=np.delete(output, indBad, 0)
            InputPar_Behav=np.delete(InputPar, indBad, 0)

        else:
            print( ' Choose appropriate method: treshold or percentage')

        #Normaliseren van de Objectieffunctie 1!
        if norm==True:
            Tempor=output_Behav.sum()/output_Behav
            output_Behav=Tempor/Tempor.sum()
        #print ('controle voor de som: %f' %output_Behav.sum())

        return [InputPar_Behav,output_Behav]

   


#ai=[78, 12, 0.5, 2, 97, 33]
#Xi = [(2.0,5.0,r'$X_1$'),(0.0,1.0,r'$X_2$'),(0.0,1.0,r'$X_3$'),(0.0,1.0,r'$X_4$'),
#      (0.0,1.0,r'$X_5$'),(0.0,1.0,r'$X_6$')]
#     
#sm = RegionalSensitivity(Xi,ModelType = 'testmodel')
#sm.PrepareSample(nbaseruns=1000)

                                                                                   
##sm.Optimized_diagnostic(width=0.15)
#sm.runTestModel(ai)

##run the model
#output = np.zeros((sm.OptOutMatrix.shape[0],1))
#for i in range(sm.OptOutMatrix.shape[0]):
#     output[i,:] = analgfunc(ai,sm.OptOutMatrix[i,:])
        
        
        
        
        
        
        
        
        
        
        
        
        
        

