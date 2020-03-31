# -*- coding: utf-8 -*-
"""
Created on Mon Mar 11 11:55:05 2013

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

class GlobalOATSensitivity(SensitivityAnalysis):
    '''
    A merged apporach of sensitivity analysis;
    also extended version of the LH-OAT approach
    
    Parameters
    -----------
    parsin : list
        either a list of (min,max,'name') values, 
        [(min,max,'name'),(min,max,'name'),...(min,max,'name')]
        or a list of ModPar instances

    Attributes            
    ------------
    _ndim :  intx
        number of factors examined. In case the groups are chosen the number 
        of factors is stores in NumFact and sizea becomes the number of created groups, (k)
        
    Notes
    ---------
    Original method described in [OAT1]_, but here generalised in the framework,
    by adding different measures of sensitivity making the sampling method
    adjustable (lh or Sobol pseudosampling) and adding the choice of 
    numerical approach to derive the derivative.

    Examples
    ------------
    >>> #EXAMPLE WITH ANALG-FUNCTION
    >>> #variables and parameters
    >>> ai=np.array([78, 12, 0.5, 2, 97, 33])
    >>> Xi = [(0.0,1.0,r'$X_1$'),(0.0,1.0,r'$X_2$'),(0.0,1.0,r'$X_3$'),
              (0.0,1.0,r'$X_4$'), (0.0,1.0,r'$X_5$'),(0.,1,r'$X_6$')]    
    >>> #prepare model class
    >>> goat=GlobalOATSensitivity(Xi)
    >>> #prepare the parameter sample
    >>> goat.PrepareSample(100,0.01, 
                           samplemethod='lh', 
                           numerical_approach='central')
    >>> #calculate model outputs                   
    >>> output = np.zeros((goat.parset2run.shape[0],1))
    >>> for i in range(goat.parset2run.shape[0]):
            output[i,:] = analgfunc(ai,goat.parset2run[i,:])
    >>> #evaluate sensitivitu
    >>> goat.Calc_sensitivity(output)
    >>> #transform sensitivity into ranking
    >>> goat.Get_ranking() 
    >>> #plot the partial effect based sensitivity
    >>> goat.plotsens(indice='PE', ec='grey',fc='grey')
    >>> #plot the rankmatrix
    >>> goat.plot_rankmatrix(outputnames)              
 
    References
    ------------
    ..  [OAT1] van Griensven, Ann, T. Meixner, S. Grunwald, T. Bishop, 
        M. Diluzio, and R. Srinivasan. 'A Global Sensitivity Analysis Tool 
        for the Parameters of Multi-variable Catchment Models' 324 (2006): 10–23.
    ..  [OAT2] Pauw, Dirk D E, D E Leenheer Decaan, and V A N Langenhove 
        Promotor. OPTIMAL EXPERIMENTAL DESIGN FOR CALIBRATION OF BIOPROCESS 
        MODELS : A VALIDATED SOFTWARE TOOLBOX OPTIMAAL EXPERIMENTEEL ONTWERP 
        VOOR KALIBRERING VAN BIOPROCESMODELLEN : EEN GEVALIDEERDE SOFTWARE 
        TOOLBOX BIOPROCESS MODELS : A VALIDATED SOFTWARE TOOLBOX, 2005.
    '''
    
    def __init__(self, parsin, ModelType = 'external'):
        SensitivityAnalysis.__init__(self, parsin)

        self._methodname = 'LHOAT_merged'
        
        if ModelType == 'pyFUSE':
            self.modeltype = 'pyFUSE'
            print('\t - The analysed model is built up by the pyFUSE environment')
        elif ModelType == 'external':
            self.modeltype = 'pyFUSE'           
            print('\t - The analysed model is externally run'    )        
        elif ModelType == 'PCRaster':
            self.modeltype = 'PCRasterPython'
            print('\t - The analysed model is a PCRasterPython Framework instance')
        elif ModelType == 'testmodel':
            self.modeltype = 'testmodel'
            print('\t - The analysed model is a testmodel'        )    
        else:
            raise Exception('Not supported model type')

        self.LB = np.array([el[0] for el in self._parsin])
        self.UB = np.array([el[1] for el in self._parsin])


    def PrepareSample(self, nbaseruns, perturbation_factor, 
                      samplemethod='Sobol', 
                      numerical_approach='central',seedin=1):
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
        perturbation_factor : float or list
            if only one number, all parameters get the same perturbation factor
            otherwise, _ndim elements in list
        samplemethod : 'sobol' or 'lh'
            sampling method to use for the sampling
        numerical_approach : 'central' or 'single'
            central approach needs n(2*k) runs, singel only n(k+1) runs;
            OAT calcluation depends on this.
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
        * More information about the central or single numerical choice is given
        in [OAT2]_.
        
        '''
        #Prepare the baseruns
        Par2run = np.zeros((nbaseruns,self._ndim))
        if samplemethod=='Sobol' or samplemethod=='sobol':
            self.nbaseruns = nbaseruns
            # generate a (N,2k) matrix with 
            FacIn = self._parsin
    
#            Par2run = np.zeros((nbaseruns,self._ndim))
            
            for i in xrange(1, nbaseruns+1):   
                [r, seed_out] = i4_sobol(self._ndim, seedin)
                Par2run[i-1,:] = r        
                seedin = seed_out
    
            for i in range(self._ndim):
                Par2run[:,i] = rescale(Par2run[:,i], FacIn[i][0], 
                                            FacIn[i][1]) 
            self.seed_out = seed_out
            print('Last seed pointer is ',seed_out)

        elif samplemethod=='lh':
            self.nbaseruns = nbaseruns
            i=0
            for par in self.pars:
                Par2run[:,i] = par.latinhypercube(nbaseruns)
                i+=1
        else:
            raise Exception('Only Sobol and Latin HYpercube sampling is provided to ensure optimal coverage of the parameter space')

        #Extend to calculate the central relative sensitivity
        #1.convert value to value+pertfactor*value; 2. add a value-pertfactor*value
        self.perturbation_factor = perturbation_factor
        if numerical_approach=='central':
            self.numerical_approach = 'central'
            Par2runall = np.zeros((nbaseruns*(self._ndim*2),self._ndim))
            for i in range(nbaseruns):
                #paste in baserun in block
                Par2runall[i*self._ndim*2:i*self._ndim*2+2*self._ndim,:] = np.tile(Par2run[i,:], (2*self._ndim, 1))
                for j in range(self._ndim):
                    Par2runall[i*self._ndim*2+j*2,j] = Par2run[i,j]+Par2run[i,j]*perturbation_factor
                    Par2runall[i*self._ndim*2+j*2+1,j] = Par2run[i,j]-Par2run[i,j]*perturbation_factor
                    
        elif numerical_approach=='single':
            self.numerical_approach = 'single'
            #this means a traject is made through the parameter space, 
            #so each value goes one further, based on previous step (cfr. Morris and van Griensven)
            Par2runall = np.zeros((nbaseruns*(self._ndim+1),self._ndim))
            for i in range(nbaseruns):
                Par2runall[i*(self._ndim+1),:] = Par2run[i,:]
                for j in range(self._ndim):
                    Par2runall[i*(self._ndim+1)+j+1,:] = Par2runall[i*(self._ndim+1)+j,:]
                    Par2runall[i*(self._ndim+1)+j+1,j] = Par2run[i,j]+Par2run[i,j]*perturbation_factor
        else:
            raise Exception('Choose between central of single numerical approximation')
        
        self.baseruns=Par2run
        self.parset2run = Par2runall
        self.totalnumberruns = self.parset2run.shape[0]               

    def Calc_sensitivity(self,output):
        '''
        Calculate the Central or Single Absolute Sensitvity (CAS),
        the Central or Single Total Sensitivity (CTRS) and the Partial Effect
        (PE) of the different outputs given. These outputs can be either
        a set of model objective functions or a timerserie output
        
        Parameters
        ------------
        output: Nxndim array
            array with the outputs for the different outputs of the model;
            this can be an Objective function, or a timeserie of the model output

        Attributes
        ------------
        CAS_SENS:
            Central/Single Absolute Sensitivity
        CTRS_SENS:
            Central/Single Total Sensitivity
        PE_SENS:
            Partial effect (van Griensven)
        
        Notes
        ------
        PE is described in [OAT1]_, the other two are just global extensions
        of the numercial approach to get local sensitivity results, 
        see [OAT2]_.
        
        '''
        try:
            output.shape[1]
        except:
            output = np.atleast_2d(output).transpose()
            
        self.CAS = np.zeros((self.nbaseruns*self._ndim,output.shape[1]))
        self.CTRS = np.zeros((self.nbaseruns*self._ndim,output.shape[1]))
        self.PE = np.zeros((self.nbaseruns*self._ndim,output.shape[1]))          
        
        if self.numerical_approach=='central':
            #control size, length needs to be the same
            if not output.shape[0] == self.parset2run.shape[0]:
                raise Exception('Size of output matrix does not fit the input matrix; control the method of numerical calculation, central or single')
                
            for i in range(self.nbaseruns):
                for j in range(self._ndim):
                    self.CAS[i*self._ndim+j,:] = (output[i*self._ndim*2+j*2,:]-output[i*self._ndim*2+j*2+1,:])/(2.*self.perturbation_factor*self.baseruns[i,j])
                    average_out = (output[i*self._ndim*2+j*2,:]+output[i*self._ndim*2+j*2+1,:])/2.
                    self.CTRS[i*self._ndim+j,:] = self.CAS[i*self._ndim+j]*self.baseruns[i,j]/average_out
                    self.PE[i*self._ndim+j,:] = np.abs((100.*(output[i*self._ndim*2+j*2,:]-output[i*self._ndim*2+j*2+1,:])/((output[i*self._ndim*2+j*2,:]+output[i*self._ndim*2+j*2+1,:])/2.))/self.perturbation_factor)
        
        elif self.numerical_approach=='single':    
            for i in range(self.nbaseruns):
                for j in range(self._ndim):
                    self.CAS[i*self._ndim+j,:] = (output[i*(self._ndim+1)+j+1,:]-output[i*(self._ndim+1)+j,:])/(self.perturbation_factor*self.baseruns[i,j])
                    average_out = (output[i*(self._ndim+1)+j+1,:]+output[i*(self._ndim+1)+j,:])/2.
                    self.CTRS[i*self._ndim+j,:] = self.CAS[i*self._ndim+j]*self.baseruns[i,j]/average_out
                    self.PE[i*self._ndim+j,:] = np.abs((100.*(output[i*(self._ndim+1)+j+1,:]-output[i*(self._ndim+1)+j,:])/((output[i*(self._ndim+1)+j+1,:]+output[i*(self._ndim+1)+j,:])/2.))/self.perturbation_factor)
                    
        else:
            raise Exception('numerical_approach not set correctly')
        
        
        #averages as in vanGriensven (percentage)
        self.PE_SENS = np.zeros((self._ndim,output.shape[1]))
        self.CAS_SENS = np.zeros((self._ndim,output.shape[1]))
        self.CTRS_SENS = np.zeros((self._ndim,output.shape[1]))
        for i in range(self._ndim):
            self.PE_SENS[i,:] = self.PE[i::self._ndim].mean(axis=0)
            self.CAS_SENS[i,:] = self.CAS[i::self._ndim].mean(axis=0)
            self.CTRS_SENS[i,:] = self.CTRS[i::self._ndim].mean(axis=0)
            
        print('Use PE_SENS for ranking purposes; since it uses the absolute value of the change; giving no compensation between positive and negative partial effects')
        
    def Get_ranking(self, choose_output=False):        
        '''
        Only possible if Calc_sensitivity is already finished;
        every columns gets is one ranking and the overall_importance is calculated based on
        the lowest value of the other rankings (cfr. Griensven)
        
        rankmatrix: defines the rank of the parameter
        self.rankdict: defines overall rank of the parameters with name
        
        Parameters
        ------------
        choose_output: integer
            starting from 1 as the first output
        
        Attributes
        -----------
        rankdict (only when single output selected):
            Dictionary giving the ranking of the parameter
        rankmatrix:
            Main output: gives for each parameter (rows) the ranking for the
            different outputs
        overall_importance: 
            Returns the summarized importance of the parameter over the different
            outputs, by checking the minimal ranking of the parameters

        Notes
        ------
        TODO make a dataframe of pandas as output: rows is par, cols is output
        '''
        
        RANK = np.argsort(-self.PE_SENS,axis=0)
                     
        #define the rankin, to plot like in paper van Griensven
        self.rankmatrix=np.empty_like(RANK)
        for j in range(RANK.shape[1]):
            for i in range(1,self._ndim+1):
                place = RANK[i-1,j]
                self.rankmatrix[place,j]=i
                
        #get it clean in dictionary
        if RANK.size == RANK.shape[0]: #only one output
            print('Ranking for the singls output')
            i=1
            self.rankdict={}
            for rank in RANK:
                print(rank)
                self.rankdict[str(i)] = self._namelist[rank[0]]
                print(str(i),' : ',self._namelist[rank[0]])
                i+=1
            return self.rankmatrix, self.rankdict
                
        else: #multiple outputs
            self.overall_importance = self.rankmatrix.min(axis=1)
            if choose_output == False:
                print('Combined ranking, by taking minimum ranking of the parameters over the different outputs')
                i=0
                for rank in self.overall_importance:
                    print(self._namelist[i],' : ', str(rank))
                    i+=1            
            else:
                print('Ranking for selected output')
                i=1
                self.rankdict={}
                for rank in RANK[:,choose_output-1]:
                    self.rankdict[str(i)] = self._namelist[rank]
                    print(str(i),' : ',self._namelist[rank])
                    i+=1     
            return self.rankmatrix        

    def latexresults(self, outputnames, name = 'GlobalOATtable.tex'):
        '''
        print(results rankmatrix in a "deluxetable" Latex)
        
        Parameters
        -----------
        outputnames : list of strings
            The names of the outputs in the colomns
        name : str.tex
            output file name; use .tex extension in the name
        '''

        #set an empty elment for the table above the parnames column        
        outputnames.insert(0,'')
                
        no=self.rankmatrix.shape[1]               
        
        fout = open(name,'w')
        t = Table(no+1, justs='l'+'c'*no, caption='Global OAT parameter ranking', label="tab:globaloatrank")

        t.add_header_row(outputnames)
        col = [self._namelist[:]]
        
        if self.rankmatrix.shape[1]==1: #only ONE output
            col.append(self.rankmatrix[:,0].tolist())
        else:                           #MULTIPLE outputs
            for i in range(self.rankmatrix.shape[1]):
                col.append(self.rankmatrix[:,i].tolist())
        print(col)
        
        t.add_data(col, sigfigs=2) #,col3
        t.print_table(fout)
        fout.close()
        print('Latex Results latex table file saved in directory %s'%os.getcwd()    )    


    def txtresults(self, outputnames, name='GlobalOATresults.txt'):
        '''
        Results rankmatrix in txt file to load in eg excel
        
        Parameters
        -----------
        outputnames : list of strings
            The names of the outputs in the colomns
        name : str.txt
            output file name; use .txt extension in the name 
        
        '''       
            
        fout = open(name,'w')
        #Write output names
#        fout.write('Par \t mu \t mustar \t sigma \n')
        ott = ['\t '+i for i in outputnames]
        ostring=''
        for oname in ott:
            ostring+=oname
        
        fout.write('Par'+ostring+'\n')
        for i in range(self._ndim):
            ntt = ['\t '+str(j) for j in self.rankmatrix[i,:]]
            nstring=''
            for nname in ntt:
                nstring+=nname           
            fout.write('%s %s \n' %(self._parmap[i],nstring))                                            
        fout.close()
        print('txt Results file saved in directory %s'%os.getcwd())
                        
    def plotsens(self, indice='PE', width = 0.5, addval = True, sortit = True, outputid = 0,
                *args, **kwargs):
        '''
        Plot a barchart of either CAS, CTRS or PE based Senstivitity
        
        Parameters
        -----------
        indice: PE, CAS or CTRS
            choose which indice you want to show
        width : float (0-1)
            width of the bars in the barchart
        addval : bool
            if True, the sensitivity values are added to the graph
        sortit : bool
            if True, larger values (in absolute value) are plotted closest to
            the y-axis      
        outputid : int
            the output to use whe multiple are compared; starts with 0
        *args, **kwargs : args
            passed to the matplotlib.bar
        
        Returns
        ----------
        fig : matplotlib.figure.Figure object
            figure containing the output
        ax1 : axes.AxesSubplot object
            the subplot
        '''
        if indice == 'PE':
            indtoplot = self.PE_SENS[:,outputid]
        elif indice == 'CAS':
            indtoplot = self.CAS_SENS[:,outputid]
        elif indice == 'CTRS':
            indtoplot = self.CTRS_SENS[:,outputid]            
        else:
            raise Exception('Choose either PE, CAS or CTRS')

        
        fig = plt.figure() 
        ax1 = fig.add_subplot(111)
        ax1 = plotbar(ax1, indtoplot, self._namelist, width = width, 
                      addval = addval, sortit = True, *args, **kwargs)
        ax1.set_ylabel(indice,fontsize=20)
        ax1.yaxis.label.set_rotation('horizontal')
        ax1.yaxis.set_label_coords(-0.02, 1.)
        plt.draw()
        return fig, ax1

    def plot_rankmatrix(self,outputnames,fontsize=14):
        '''
        Make an overview plot of the resulting ranking of the different parameters
        for the different outputs
        
        Parameters
        ------------
        outputnames : list of strings
            The names of the outputs in the colomns
        fontsize: int
            size of the numbers of the ranking

        '''
        
        if len(outputnames) > 20.:
            print('Consider to split up the outputs to get nicer overview')
        try:
            self.rankmatrix
        except:
            self.Get_ranking()          
            
        xplaces=np.arange(0,self.rankmatrix.shape[1],1)
        yplaces=np.arange(0,self.rankmatrix.shape[0],1)
        
        fig = plt.figure()
        ax1 = fig.add_subplot(111)
        #make adapted matrix so only top three is highlighted
        XX=self.rankmatrix.copy()
        XX[XX > 3] = 0
        cmap = colors.ListedColormap(['1.','0.3', '0.5','0.9'])
        bounds=[0,1,2,3,4]
        norm = colors.BoundaryNorm(bounds, cmap.N)
        #plot tje colors for the frist tree parameters
        ax1.matshow(XX,cmap=cmap,norm=norm)
        
        #Plot the rankings in the matrix
        for i in range(self.rankmatrix.shape[1]):
            for j in range(self.rankmatrix.shape[0]):
                ax1.text(xplaces[i], yplaces[j], str(self.rankmatrix[j,i]), 
                         fontsize=fontsize, horizontalalignment='center', 
                         verticalalignment='center')
                
        #place ticks and labels
        ax1.set_xticks(xplaces)
        ax1.set_xbound(-0.5,xplaces.size-0.5)
        ax1.set_xticklabels(outputnames[-xplaces.size:], rotation = 30, ha='left')
        
        ax1.set_yticks(yplaces)
        ax1.set_ybound(yplaces.size-0.5,-0.5)
        ax1.set_yticklabels(self._namelist)
        
        ax1.spines['bottom'].set_color('none')
        ax1.spines['right'].set_color('none')
        ax1.xaxis.set_ticks_position('none')
        
        return fig,ax1

# ------------------------------
# EXAMPLE WITH MULTIPLE OUTPUTS
# ------------------------------
#ai_or=np.array([78, 12, 0.5, 2, 97, 33])
#ai=np.array([78, 12, 0.5, 2, 97, 33])
#ai=ai.reshape((6,1))
#for i in range(10):
#    aip = np.random.permutation(ai_or).reshape((6,1))
#    ai = np.hstack((ai,aip))
##
###ai=[78, 0.001, 0.5, 1.5, 0.7, 1.]      
###ai=[0.1, 0.8, 0.5, 0.2, 97,1.1]        
#Xi = [(0.0,5.0,r'$X_1$'),(4.0,7.0,r'$X_2$'),(0.0,1.0,r'$X_3$'),
#      (0.0,1.0,r'$X_4$'), (0.0,1.0,r'$X_5$'),(0.5,0.9,r'$X_6$')]        
##Xi = [(0.0,1.0,r'$X_1$'),(0.0,1.0,r'$X_2$'),(0.0,1.0,r'$X_3$'),
##      (0.0,1.0,r'$X_4$'), (0.0,1.0,r'$X_5$'),(0.,1,r'$X_6$')]        
#test=GlobalOATSensitivity(Xi)
#test.PrepareSample(100,0.01, 
#                   samplemethod='lh', 
#                   numerical_approach='single')
#try:
#    output = np.zeros((test.parset2run.shape[0],ai.shape[1]))
#except:
#    output = np.zeros((test.parset2run.shape[0],1))
##    
#for i in range(test.parset2run.shape[0]):
#     output[i,:] = analgfunc(ai,test.parset2run[i,:])
#test.Calc_sensitivity(output)
#test.Get_ranking()        
###
#test.latexresults(outputnames=['o1','o2','o3','o4','o5','o6','o7','o8','o9','o10','o11'])
#test.txtresults(outputnames=['o1','o2','o3','o4','o5','o6','o7','o8','o9','o10','o11'])
#test.plotsens(indice='PE',outputid = 0,ec='grey',fc='grey')
##
####matshow
#outputnames=['o1','o2','o3','o4','o5','o6','o7','o8','o9','o10','o11']
#test.plot_rankmatrix(outputnames)


#for dynamic classes
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
#        '''








