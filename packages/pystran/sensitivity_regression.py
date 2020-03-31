# -*- coding: utf-8 -*-
"""
Created on Mon Mar 18 14:25:58 2013

@author: VHOEYS
"""

import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

from .sensitivity_base import *
from .sobol_lib import *
from .extrafunctions import *
from .latextablegenerator import *
from .plot_functions_rev import TornadoSensPlot, plotbar


class SRCSensitivity(SensitivityAnalysis):
    '''
    The regression sensitivity analysis:
    MC based sampling in combination with a SRC calculation; the rank based
    approach (less dependent on linearity) is also included in the SRC 
    calculation and is called SRRC
    
    The model is proximated by a linear model of the same parameterspace and the
    influences of the parameters on the model output is evaluated.
    
    Parameters
    -----------
    parsin : list
        Either a list of (min,max,'name') values, 
        [(min,max,'name'),(min,max,'name'),...(min,max,'name')]
        or a list of ModPar instances

    Attributes            
    ------------
    _ndim :  intx
        number of factors examined. In case the groups are chosen the number 
        of factors is stores in NumFact and sizea becomes the number of created groups, (k)
        
    Notes
    ---------
    Rank transformation: 
        Rank transformation of the data can be used to transform a nonlinear 
        but monotonic relationship to a linear relationship. When using rank 
        transformation the data is replaced with their corresponding ranks.
        Ranks are defined by assigning 1 to the smallest value,
        2 to the second smallest and so-on, until the largest
        value has been assigned the rank N.

    Examples
    ------------
    >>> ai=np.array([10,20,15,1,2,7])
    >>> Xi = [(8.0,9.0,r'$X_1$'),(7.0,10.0,r'$X_2$'),(6.0,11.0,r'$X_3$'),
    >>>       (5.0,12.0,r'$X_4$'), (4.0,13.0,r'$X_5$'),(3.0,4.,r'$X_6$')]      
    >>> #prepare method
    >>> reg=SRCSensitivity(Xi)
    >>> #prepare parameter samples
    >>> reg.PrepareSample(1000)  
    >>> #run model and get outputs for all MC samples
    >>> output = np.zeros((reg.parset2run.shape[0],1))
    >>> for i in range(reg.parset2run.shape[0]):
    >>>     output[i,:] = simplelinear(ai,reg.parset2run[i,:])
    >>> #Calc SRC without using rank-based approach
    >>> reg.Calc_SRC(output, rankbased=False)
    >>> #check if the sum of the squared values approaches 1
    >>> print reg.sumcheck
    >>> [ 1.00555193]
    >>> reg.plot_tornado(outputid = 0, ec='grey',fc='grey')
 
    References
    ------------
    
    '''
    
    def __init__(self, parsin, ModelType = 'external'):
        SensitivityAnalysis.__init__(self, parsin)

        self._methodname = 'Regression_merged'
        
        if ModelType == 'pyFUSE':
            self.modeltype = 'pyFUSE'
            print('The analysed model is built up by the pyFUSE environment')
        elif ModelType == 'external':
            self.modeltype = 'pyFUSE'           
            print('The analysed model is externally run'            )
        elif ModelType == 'PCRaster':
            self.modeltype = 'PCRasterPython'
            print('The analysed model is a PCRasterPython Framework instance')
        elif ModelType == 'testmodel':
            self.modeltype = 'testmodel'
            print('The analysed model is a testmodel'            )
        else:
            raise Exception('Not supported model type')

        self.LB = np.array([el[0] for el in self._parsin])
        self.UB = np.array([el[1] for el in self._parsin])

    def PrepareSample(self, nbaseruns, samplemethod='Sobol', seedin=1):
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
        samplemethod : 'sobol' or 'lh'
            sampling method to use for the sampling
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
        - Do the Sobol sampling always for the entire parameter space at the 
        same time, for LH this doesn't matter!
        - Never extend the sampling size with using the same seed, since this
        generates duplicates of the samples!
        '''
        #Prepare the baseruns
        self.parset2run = np.zeros((nbaseruns,self._ndim))
        if samplemethod=='Sobol':
            self.nbaseruns = nbaseruns
            # generate a (N,2k) matrix with 
            FacIn = self._parsin           
            for i in xrange(1, nbaseruns+1):   
                [r, seed_out] = i4_sobol(self._ndim, seedin)
                self.parset2run[i-1,:] = r        
                seedin = seed_out
    
            for i in range(self._ndim):
                self.parset2run[:,i] = rescale(self.parset2run[:,i], FacIn[i][0], 
                                            FacIn[i][1]) 
            self.seed_out = seed_out
            print ('Last seed pointer is ',seed_out)

        elif samplemethod=='lh':
            self.nbaseruns = nbaseruns
            i=0
            for par in self.pars:
                self.parset2run[:,i] = par.latinhypercube(nbaseruns)
                i+=1
        else:
            raise Exception('Only Sobol and Latin HYpercube sampling is provided to ensure optimal coverage of the parameter space')
        
        self.totalnumberruns = self.parset2run.shape[0]

    def quickscatter(self,output):
        '''
        Quick link to the general scatter function, by passing to the general
        scattercheck plot of the sensitivity base-class
        
        Parameters
        -----------
        output: ndimx1 array
            array with the output for one output of the model;
            this can be an Objective function or an other model statistic
            
        Notes
        ------
        Used to check linearity of the input/output relation in order to evaluate
        the usefulness of the SRC-regression based technique
        
        Examples
        ----------
        >>> reg.quickscatter(output)
        
        '''
        self.scattercheck(self.parset2run, output, ncols=3, marker='o', 
                          edgecolor='black', facecolor='none', s=30)
    

    def _standardize(self,output):
        '''
        To get the Standardized Regression Coefficients (SRC), we need to 
        standardize the variables (outputs and parameters)        
        '''
        print ('calculating standardized values...')
        parmean, parstd = self.parset2run.mean(axis=0), self.parset2run.std(axis=0)
        outmean, outstd = output.mean(axis=0), output.std(axis=0)
        
        self.parscaled = (self.parset2run - parmean)/parstd
        self.outputscaled = (output - outmean)/outstd        
        print ('...done')

    def _transform2rank(self, pars, output):
        '''
        hidden definition for rank transformation
        '''        
        print ('calclulating standardized values...')
        
        parranked = np.empty_like(pars)
        for i in range(pars.shape[1]):
            parranked[:,i] = stats.rankdata(pars[:,i])
        
        outputranked = np.empty_like(output)            
        for i in range(output.shape[1]):
            outputranked[:,i] = stats.rankdata(output[:,i])
        
        return parranked, outputranked

    def Calc_SRC(self,output, rankbased = False):
        '''
        SRC sensitivity calculation for multiple outputs
        
        Check is done on the Rsq value (higher than 0.7?) and the sum of SRC's
        for the usefulness of the method.
        
        Parameters
        -----------
        output : Nxm ndarray
            array with the model outputs (N MC simulations and m different 
            outputs)
        
        rankbased : boolean
            if True, SRC values are transformed into SRRC values; using ranks 
            instead of values itself
        
        Attributes
        ------------
        SRC : ndimxnoutputs narray
            Standardized Regression Coefficients
        cova : 
            variance-Covariance matrix
        core : 
            correlation matrix
        sumcheck : noutput narray
            chek for linearity by summing the SRC values
                        
        Notes
        ------
        Least squares Estimation theory, 
        eg. http://www.stat.math.ethz.ch/~geer/bsa199_o.pdf
        '''
        #prepare SRC matrix
        self.SRC = np.zeros((self._ndim,output.shape[1]))
        self.SRRC = np.zeros((self._ndim,output.shape[1]))
        self.cova = np.zeros((self._ndim,self._ndim,output.shape[1]))
        self.corre = np.zeros((self._ndim,self._ndim,output.shape[1]))
        self.sumcheck = np.zeros(output.shape[1])
     
        #standardize variables/parameters
        self._standardize(output)
        
        if rankbased == True:
            self.parrankscaled , self.outputrankscaled = self._transform2rank(self.parscaled, self.outputscaled)
            
        
        #calcluate SRC values for each output
        for i in range(output.shape[1]):
            print ('--------------------------')
            print ('Working on column ',i,'...')
            #the res is the sum(res**2) value; functional for covariance calculation
            self.SRC[:,i], res, rank, s = np.linalg.lstsq(self.parscaled,self.outputscaled[:,i])
            if rankbased == True:
                self.SRRC[:,i], res, rank, s = np.linalg.lstsq(self.parrankscaled,self.outputrankscaled[:,i])
            
            #correlation coefficient to check linear assumption
            Yi = np.dot(self.parscaled,self.SRC[:,i]) #matrix multiplication
            R = np.corrcoef(self.outputscaled[:,i],Yi)
            Rsq = R**2
            print ('Rsq (for SRC calculation) = ', Rsq[0,1])
                                           
            #another possibility to get Rsq based on residuals (OLS theory)
            #Rsq_2 = 1. - res / sum((self.outputscaled - self.outputscaled.mean())**2)            
    
            #The 0.7 threshold is a rule of thumb used in literature
            if Rsq[0,1] < 0.7:
                print ('''ATTENTION: the coefficient of determination, Rsq, i.e. the fraction of the output variance that is explained by the regression model, is lower than 0.7. for SRC calcluation. Consider using a method which is less dependent on the assumption of linearity and evaluate SRRC result.''')
            else:
                print ('''Assumption of linearity is assumed valid with the Rsq value higer than 0.7''')
            
            if rankbased == True:
                Yi = np.dot(self.parrankscaled,self.SRRC[:,i]) #matrix multiplication
                R = np.corrcoef(self.outputrankscaled[:,i],Yi)
                Rsq = R**2
                print ('Rsq (for SRRC calculation) = ',Rsq[0,1] )

            #another check: sum of the SRC^2 should be 1!! 
            self.sumcheck[i] = np.dot(self.SRC[:,i].transpose(),self.SRC[:,i])
            print ('Sum of squared sensitivities should approach 1, for SRC: ',self.sumcheck[i])
            
            if rankbased == True:
                sumcheck = np.dot(self.SRRC[:,i].transpose(),self.SRRC[:,i])
                print ('Sum of squared sensitivities should approach 1, for SRRC: ',sumcheck)
            
            #Calculates the Parameter variance-covariance  matrix
			#variances on the diagonal, covariances of factors on the non-diagonal 
            #residuals = sum((self.outputscaled[:,i] - Yi)**2) #same as res from lstsq function
            n,p =self.parscaled.shape
            s2 = res/(n-p)   #estimator for variance; better to do n-p-1?
            self.cova[:,:,i] = s2 * np.linalg.inv(np.dot(self.parscaled.transpose(),self.parscaled))  #(X'X)-1 s2
            
            print ('Confidence intervals can be calculated based on covariance matrix, only done for SRC')

            #calculate the correlation matrix            
            for k in range(p):
                for l in range(p):
                    self.corre[k,l,i] = self.cova[k,l,i]/(np.sqrt(self.cova[k,k,i])*np.sqrt(self.cova[l,l,i]))
            print ('output of column ',i,' done.')
            print ('--------------------------')
    
        #combine results in a ranking    
        RANK = np.argsort(-self.SRC,axis=0)
                         
        #define the ranking, based on the SRC results
        self.rankmatrix=np.empty_like(RANK)
        for j in range(RANK.shape[1]):
            for i in range(1,self._ndim+1):
                place = RANK[i-1,j]
                self.rankmatrix[place,j]=i
        
        if rankbased == True:
            #combine results in a ranking    
            RANK = np.argsort(-self.SRRC,axis=0)
                             
            #define the ranking, based on the SRC results
            self.rankmatrixSRRC=np.empty_like(RANK)
            for j in range(RANK.shape[1]):
                for i in range(1,self._ndim+1):
                    place = RANK[i-1,j]
                    self.rankmatrixSRRC[place,j]=i            
        
#        return self.SRC, self.cova, self.corre, self.rankmatrix

    def plot_tornado(self, outputid = 0, SRC = True, *args, **kwargs):
        '''
        Make a Tornadplot of the parameter influence on the output;
        SRC must be calculated first before plotting
        
        Parameters
        -----------
        outputid : int
            output for which the tornado plot is made, starting from 0
        SRC : boolean
            SRC true means that SRC values are used, otherwise 
            the SRRC (ranked!) is used
        *args, **kwargs : 
                arguments passed to the TornadoSensPlot function of the 
                plotfunctions_rev data
        
        Notes
        ------
        The parameters for the tornadosensplot are:
            gridbins: int, number of gridlines
            midwidth: float, width between the two axis, adapt to parameter names
            setequal: boolean, if True, axis are equal lengths
            plotnumb: boolean, if True, sensitiviteis are plotted
            parfontsize: int, font size of the parameter names
            bandwidth: width of the band
        
        Examples
        ---------
        >>> reg.plot_tornado(outputid = 0,gridbins=3, midwidth=0.2, 
                             setequal=True, plotnumb=True, parfontsize=12, 
                             bandwidth=0.75)
        '''
        if SRC == True:
            fig, axleft, axright  = TornadoSensPlot(self._namelist, 
                                                self.SRC[:,outputid],
                                                *args, **kwargs )
        else:
            fig, axleft, axright  = TornadoSensPlot(self._namelist, 
                                                self.SRRC[:,outputid],
                                                *args, **kwargs )
        
    def plot_SRC(self, width = 0.2, addval = True, sortit = True, outputid = 'all',
                ncols = 3, outputnames=[], *args, **kwargs):
        '''
        Plot a barchart of the SRC values; actually a Tornadoplot in the 
        horizontal direction. More in the style of the other methods.
        
        TODO: make for subset of outputs, also in other methods; currently all or 1
        
        Parameters
        -----------
        width : float (0-1)
            width of the bars in the barchart
        addval : bool
            if True, the sensitivity values are added to the graph
        sortit : bool
            if True, larger values (in absolute value) are plotted closest to
            the y-axis      
        outputid : int or all
            the output to use whe multiple are compared; starts with 0
            if all, the different outputs are plotted in subplots
        ncols : int
            number of columns to put the subplots in
        outputnames :  list of strings
            [] to plot no outputnames, otherwise list of strings equal to the
            number of outputs
        *args, **kwargs : args
            passed to the matplotlib.bar
        
        Returns
        ----------
        fig : matplotlib.figure.Figure object
            figure containing the output
        ax1 : axes.AxesSubplot object
            the subplot
        
        Examples
        ---------
        >>> #plot single SRC
        >>> reg.plot_SRC(outputid=0, width=0.3, sortit = True, 
                         ec='grey',fc='grey')
        >>> #plot single SRC (assume 4 outputs)      
        >>> reg.plot_SRC(outputid = 'all' , ncols = 2, 
                          outputnames=['o1','o2','o3','o4'], ec='grey', fc='grey')
        '''
        if outputid == 'all':
                    #define number of rows
            numsrc = self.SRC.shape[1]
            nrows = np.divide(numsrc,ncols)
            if np.remainder(numsrc,ncols)>0:
                nrows+=1
            #prepare plots
            fig, axes = plt.subplots(nrows = nrows, ncols = ncols, figsize=(40,40), facecolor = 'white')
            fig.subplots_adjust(hspace=0.25, wspace=0.2)
        
            i=0
            for ax in axes.flat:
                if i<numsrc:
                    ax = plotbar(ax, self.SRC[:,i], self._namelist, 
                                 width = width, addval = addval, 
                                 sortit = True, *args, **kwargs)
                    ax.set_ylabel('SRC',fontsize=15)
                    ax.yaxis.label.set_rotation('horizontal')
                    ax.yaxis.set_label_coords(-0.02, 1.)
                    if outputnames:
                        ax.set_title(outputnames[i])
                else:
                    ax.set_axis_off()
                i+=1
        else:
            print ('SRC values of output ',outputid,' is shown in graph')
            fig = plt.figure() 
            ax1 = fig.add_subplot(111)
            ax1 = plotbar(ax1, self.SRC[:,outputid], self._namelist, width = width, 
                          addval = addval, sortit = True, *args, **kwargs)
            ax1.set_ylabel('SRC',fontsize=20)
            ax1.yaxis.label.set_rotation('horizontal')
            ax1.yaxis.set_label_coords(-0.02, 1.)
            plt.draw()
            
            return fig, ax1

    def latexresults(self, outputnames, rank = False, name = 'SRCtable.tex'):
        '''
        Print results SRC values or ranks in a "deluxetable" Latex
        
        Parameters
        -----------
        outputnames : list of strings
            The names of the outputs in the colomns
        rank : boolean
            if rank is True, rankings or plotted in tabel instead of the 
            SRC values
        name : str.tex
            output file name; use .tex extension in the name
        '''
        #set an empty elment for the table above the parnames column        
        outputnames.insert(0,'')

        if rank == True:
            towrite = self.rankmatrix
            captowrite = 'Global SRC parameter ranking'
        else:
            towrite = self.SRC
            captowrite = 'Standardized Regression Coefficients (SRC)'
                
        no = self.rankmatrix.shape[1]               
        
        fout = open(name,'w')
        t = Table(no+1, justs='l'+'c'*no, caption=captowrite, label="tab:SRCresult")

        t.add_header_row(outputnames)
        col = [self._namelist[:]]
        
        if self.rankmatrix.shape[1]==1: #only ONE output
            col.append(towrite[:,0].tolist())
        else:                           #MULTIPLE outputs
            for i in range(self.rankmatrix.shape[1]):
                col.append(towrite[:,i].tolist())
        print (col)
        
        t.add_data(col, sigfigs=2) #,col3
        t.print_table(fout)
        fout.close()
        print ('Latex Results latex table file saved in directory %s'%os.getcwd()        )

    def txtresults(self, outputnames, rank = False, name = 'SRCresults.txt'):
        '''
        Results rankmatrix in txt file to load in eg excel
        
        Parameters
        -----------
        outputnames : list of strings
            The names of the outputs in the colomns
        rank : boolean
            if rank is True, rankings or plotted in tabel instead of the 
            SRC values            
        name : str.txt
            output file name; use .txt extension in the name 

        '''     
        #set an empty elment for the table above the parnames column        

        if rank == True:
            towrite = self.rankmatrix
        else:
            towrite = self.SRC      
            
        fout = open(name,'w')
        #Write output names
#        fout.write('Par \t mu \t mustar \t sigma \n')
        
        ott = ['\t '+i for i in outputnames]
        ostring=''
        for oname in ott:
            ostring+=oname
        
        fout.write('Par'+ostring+'\n')
        for i in range(self._ndim):
            ntt = ['\t '+str(j) for j in towrite[i,:]]
            nstring=''
            for nname in ntt:
                nstring+=nname           
            fout.write('%s %s \n' %(self._parmap[i],nstring))                                            
        fout.close()
        print ('txt Results file saved in directory %s'%os.getcwd())



#LINALG MODEL
#ai=np.array([78, 12, 0.5, 2, 97, 33])
#ai=[78, 0.001, 0.5, 1.5, 0.7, 1.]      
#ai=[0.1, 0.8, 0.5, 0.2, 97,1.1]              
#Xi = [(0.0,1.0,r'$X_1$'),(0.0,1.0,r'$X_2$'),(0.0,1.0,r'$X_3$'),
#      (0.0,1.0,r'$X_4$'), (0.0,1.0,r'$X_5$'),(0.,1,r'$X_6$')]        
#reg=RegressionSensitivity(Xi)
#reg.PrepareSample(1000)  
#output = np.zeros((reg.parset2run.shape[0],1))
#for i in range(reg.parset2run.shape[0]):
#    output[i,:] = analgfunc(ai,reg.parset2run[i,:])

##SIMPLE LINEAR
#ai=np.array([10,10,10,10,10,10])
#Xi = [(8.0,9.0,r'$X_1$'),(7.0,10.0,r'$X_2$'),(6.0,11.0,r'$X_3$'),
#      (5.0,12.0,r'$X_4$'), (4.0,13.0,r'$X_5$'),(3.0,4.,r'$X_6$')]      
#reg=SRCSensitivity(Xi)
#reg.PrepareSample(1000)  
#output = np.zeros((reg.parset2run.shape[0],1))
#for i in range(reg.parset2run.shape[0]):
#    output[i,:] = simplelinear(ai,reg.parset2run[i,:])
##    output[i,:] = harder(ai,reg.parset2run[i,:])
##
##muloutput=np.tile(output,5)
#reg.Calc_SRC(output, rankbased=True)
#print reg.sumcheck
##print  reg.SRRC
##
###reg.plot_tornado()
#reg.SRC[2,0]=-0.6
#reg.SRC[2,3]=-0.2
###TornadoSensPlot(reg.namelist,reg.SRC[:,0], gridbins=3, midwidth=0.2, setequal=True, plotnumb=True, parfontsize=16, bandwidth=0.3) 
#reg.plot_SRC(outputid = 'all' ,ncols = 2, outputnames=['o1','o2','o3','o4','o5'], ec='grey',fc='grey')
#reg.latexresults(owutputnames=['o1','o2','o3','o4','o5'],rank=True)
#reg.txtresults(outputnames=['o1','o2','o3','o4','o5'],rank=False)
#reg.quickscatter(output)
#reg.scattercheck(reg.parset2run, output, ncols=3, marker='o', 
#                          edgecolor='black', facecolor='none', s=30)
#reg.Calc_SRC(output, rankbased=False)
#
##reg.plot_tornado(outputid = 0,gridbins=3, midwidth=0.2, setequal=True, plotnumb=True, parfontsize=12, bandwidth=0.75)
#reg.plot_SRC(outputid=0, width=0.3, sortit = True, ec='grey',fc='grey')