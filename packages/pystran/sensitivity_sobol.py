# -*- coding: utf-8 -*-
"""
@author: VHOEYS
development supported by Flemish Institute for Technological Research (VITO)
"""

import os
import numpy as np

from .sensitivity_base import *
from .sobol_lib import *
from .extrafunctions import *
from .latextablegenerator import *
from .plot_functions_rev import plotbar, interactionplot, plot_evolution

#(enhancement: do sobol for multiple outputs, iterating the post)
class SobolVariance(SensitivityAnalysis):
    '''
    Sobol Sensitivity Analysis Variance Based
    
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
    parset2run : ndarray
        every row is a parameter set to run the model for. All sensitivity methods have this attribute to interact with base-class running
        
    Examples
    ------------
    >>> ai=[0, 1, 4.5, 9, 99, 99, 99, 99]
    >>> alphai = 0.5 * np.ones(len(ai))
    >>> Xi = [(0.0,1.0,'par1'),(0.0,1.0,'par2'),(0.0,1.0,'par3'),(0.0,1.0,'par4'),
          (0.0,1.0,'par5'),(0.0,1.0,'par6'),(0.0,1.0,'par7'),(0.0,1.0,'par8'),]
    >>> di=np.random.random(8)
    >>> #set up sensitivity analysis
    >>> sens2 = SobolVariance(Xi, ModelType = 'testmodel')
    >>> #Sampling strategy
    >>> sens2.SobolVariancePre(1500)
    >>> #Run model + evaluate the output
    >>> sens2.runTestModel('analgfunc', [ai, alphai, di]) #here normally other model
    >>> #results in txt file 
    >>> sens2.txtresults(name='SobolTestOut.txt')
    >>> #results in tex-table 
    >>> sens2.latexresults(name='SobolTestOut.tex')
    >>> #Plots
    >>> sens2.plotSi(ec='grey',fc='grey')
    >>> sens2.plotSTi(ec='grey',fc='grey')
    >>> sens2.plotSTij()
    >>> Si_evol, STi_evol = sens2.sens_evolution(color='k')    
    
    Notes
    --------
    Calculates first and total order, and second order Total Sensitivity, 
    according to [S1]_ , higher order terms and bootstrapping is not (yet) included    
    
    References
    ------------
    ..  [S1] Saltelli, A., P. Annoni, I. Azzini, F. Campolongo, M. Ratto, 
        S. Tarantola,(2010) Variance based sensitivity analysis of model output. 
        Design and estimator for the total sensitivity index, Computer Physics 
        Communications, 181, 259–270
    ..  [S2] Saltelli, Andrea, Marco Ratto, Terry Andres, Francesca Campolongo, 
        Jessica Cariboni, Debora Gatelli, Michaela Saisana, and Stefano Tarantola. 
        Global Sensitivity Analysis, The Primer. John Wiley & Sons Ltd, 2008.
        
    '''
    
    def __init__(self, parsin, ModelType = 'pyFUSE'):
        SensitivityAnalysis.__init__(self, parsin)

        self._methodname = 'SobolVariance'
        
        if ModelType == 'pyFUSE':
            self.modeltype = 'pyFUSE'
            print( 'The analysed model is built up by the pyFUSE environment')
        elif ModelType == 'external':
            self.modeltype = 'pyFUSE'           
            print( 'The analysed model is externally run'            )
        elif ModelType == 'PCRaster':
            self.modeltype = 'PCRasterPython'
            print( 'The analysed model is a PCRasterPython Framework instance')
        elif ModelType == 'testmodel':
            self.modeltype = 'testmodel'
            print( 'The analysed model is a testmodel'            )
        else:
            raise Exception('Not supported model type')

        self.LB = np.array([el[0] for el in self._parsin])
        self.UB = np.array([el[1] for el in self._parsin])       

    def __str__(self):
        return self._methodname, 'based Sensitivity Analysis.'

    def Sobolsampling(self, nbaseruns, seedin=1):
        '''
        Performs Sobol sampling procedure, given a set of ModPar instances, 
        or by a set of (min,max) values in a list. 

        This function is mainly used as help function, but can be used to 
        perform Sobol sampling for other purposes
        
        Todo: improve seed handling, cfr. bioinspyred package
        
        Parameters
        -----------
        nbaseruns : int
            number of runs to do
        seed : int
            to et the seed point for the sobol sampling
        
        Examples
        ---------    
        >>> p1 = ModPar('tp1',2.0,4.0,3.0,'randomUniform')    
        >>> p2 = ModPar('tp2',1.0,5.0,4.0,'randomUniform')
        >>> p3 = ModPar('tp3',0.0,1.0,0.1,'randomUniform')
        >>> sobanal1 = SobolVariance([p1,p2,p3])
        >>> sobanal2 = SobolVariance([(2.0,4.0,'tp1'),(1.0,5.0,'tp2'),(0.0,1.0,'tp3')])
        >>> pars1 = sobanal.Sobolsampling(100,seed=1)
        >>> pars2 = sobanal.Sobolsampling(100,seed=1)
        
        Notes
        -------
        DO SOBOL SAMPLING ALWAYS FOR ALL PARAMETERS AT THE SAME TIME!
        
        Duplicates the entire parameter set to be able to divide in A and B
        matric        
        '''
        # generate a (N,2k) matrix with 
        FacIn = self._parsin
        FacIn.extend(FacIn)
        
        ndim2 = self._ndim*2

        Par2run = np.zeros((nbaseruns,ndim2))
        self.Par2run = np.zeros((nbaseruns,ndim2))
        
        for i in xrange(1, nbaseruns+1):   
            [r, seed_out] = i4_sobol(ndim2, seedin)
            Par2run[i-1,:] = r        
            seedin = seed_out

        for i in range(ndim2):
            self.Par2run[:,i] = rescale(Par2run[:,i], FacIn[i][0], 
                                        FacIn[i][1])

    def conditional_sampling(self, nbaseruns, cond_dict):
        '''
        parname1 need to be larger parname2
       
        '''
        parname1 = cond_dict['name1']
        parname2 = cond_dict['name2']
        condition = cond_dict['condition']
            
        #idea here, make it twice the size of the nbaseruns and past afterwards next to each other
        #to emulate the ndim *2        
        
        # generate a (N,2k) matrix with 
        FacIn = self._parsin
        FacIn.extend(FacIn)
        
        ndim2 = self._ndim*2

        Par2run = np.zeros((nbaseruns, ndim2))
        
        #HERE THE CONDITIONAL PART NEEDS TO BE ADDED
        #conservative strategy: sample random untill enough with the conditions are found
        cnt = 0
        print( 'get samples...')
        while cnt < nbaseruns:
            newset_a = np.zeros(self._ndim)
            newset_b = np.zeros(self._ndim)
            for j,par in enumerate(self.pars):
                newset_a[j] = par.avalue()
                newset_b[j] = par.avalue()
                if par.name == parname1:
                    parval_a1 = newset_a[j]
                    parval_b1 = newset_b[j]
                if par.name == parname2:
                    parval_a2 = newset_a[j]                
                    parval_b2 = newset_b[j]                
            #check is condition met
            if condition == 'lt' or condition == '<':
                #is actually the same as >
                if parval_a1 < parval_a2 and parval_a1 < parval_b2 and \
                            parval_b1 < parval_b2 and parval_b1 < parval_a1:
                    Par2run[cnt,:self._ndim] = newset_a
                    Par2run[cnt,self._ndim:] = newset_b
                    cnt +=1 

                
            elif condition == 'gt' or condition == '>':
                if parval_a1 > parval_a2 and parval_a1 > parval_b2 and \
                            parval_b1 > parval_b2 and parval_b1 > parval_a1:
                    Par2run[cnt,:self._ndim] = newset_a
                    Par2run[cnt,self._ndim:] = newset_b
                    cnt +=1   
            else:
                raise Exception("Only comparisons lt and gt are possible")

        self.Par2run = Par2run
        #put last half next to first half
#        self.Par2run = np.concatenate((Par2run[:nbaseruns,:], 
#                                          Par2run[nbaseruns:,:]), axis = 1)


    def SobolVariancePre(self, nbaseruns, seed = 1, repl = 1,
                         conditional = None):
        '''
        Set up the sampling procedure of N*(k+2) samples
        
        Parameters
        -------------
        nbaseruns : int
            number of samples for the basic analysis, total number of model runs
            is Nmc(k+2), with k the number of factors
        seed : int
            to set the seed point for the sobol sampling; enables to 
            enlarge a current sample
        repl : int
            Replicates the entire sampling procedure. Can be usefull to test if the
            current sampling size is large enough to get convergence in the 
            sensitivity results (bootstrapping is currently not included) 
            
        Notes
        ------
        Following the Global sensitivity analysis, [S2]_, 
        but updated for [S1]_ for more optimal convergence of the sensitivity
        indices
        '''       
        
        self.repl = repl
        self.nbaseruns = nbaseruns
        self.totalruns = nbaseruns*(2 + self._ndim)*repl
        self.startedseed = seed
        print( self.startedseed)

        print( 'The total cost of the analysis well be %d Monte Carlo Runs' %(nbaseruns*(2+self._ndim)*repl) )
        
        #Set up the matrices
        #---------------------
#        # generate a (N,2k) matrix with 
#        FacIn = self._parsin
#        FacIn.extend(FacIn)
        if conditional == None:
            self.Sobolsampling(self.nbaseruns*repl, seedin=self.startedseed ) #
        else:
            self.conditional_sampling(self.nbaseruns*repl, 
                                      cond_dict = conditional)
                                      
        #the resulting sobol quasi-random is not entirally the same as in paper
        #Saltelli 2012, Variance based sensitivity analysis of model output. 
        # Design and estimator for the total sensitivity index
        # But implementation cited elsewhere
        
        sAB = self.Par2run
        print( sAB.shape)
        
        Aall = sAB[:,:self._ndim] 
        Ball = sAB[:,self._ndim:]
       
    #    Ctorun = np.vstack((A,B))
    
        #take first
        A = Aall[0 : self.nbaseruns,:]
        B = Ball[0 : self.nbaseruns,:]
      
        Ctorun = np.vstack((A,B))
        for i in range(self._ndim):
            C = A.copy()
            C[:,i] = B[:,i]        
            Ctorun = np.vstack((Ctorun, C))
#        print( self.Ctorun.shape)
        
        if self.repl > 1:
            print( self.repl,' replications of analysis are used')
            for i in range(1,repl):
                A = Aall[i*self.nbaseruns : (i+1)*self.nbaseruns]
                B = Ball[i*self.nbaseruns : (i+1)*self.nbaseruns]
                Ctorun = np.vstack((Ctorun,A,B))
                for i in range(self._ndim):
                    #version 1993
            #        C = B.copy()
            #        C[:,i] = A[:,i]
            
                    #version 2010 Saltelli et al
                    C = A.copy()
                    C[:,i] = B[:,i]        
                    Ctorun = np.vstack((Ctorun, C))   
        self.Ctorun = Ctorun
        
        self.parset2run = Ctorun
        self.totalnumberruns = self.parset2run.shape[0]
        print( self.Ctorun.shape)
        #Model needs to run for everyline of the returned matrix  
        print( 'The parameter sets to calculate the model are stored in self.parset2run and can be extracted')
               

    def SobolVariancePost(self, output, repl = 1, adaptedbaserun = None, forevol=False):
        '''
        Calculate first and total indices based on model output and sampled
        values
               
        the sensmatrices for replica, 
        have repititions in the rows, columns are the factors
        
        only output => make multiple outputs (todo!!),
        by using the return, different outputs can be tested...
        
        Parameters
        -----------
        output : ndarray
            Nx1 matrix with the model outputs
        repl :  int
            number of replicates used
        adaptedbaserun : int
            number of baseruns to base calculations on  
        forevol : boolean
            True if used for evaluating the evolution
        
        Notes
        ------
        The calculation methods follows as the directions given in [S1]_
        '''

        if output.size == output.shape[0] or output.size == output.shape[1]:
            self._outputbk = output
        else:
            raise Exception('Sobol works only wit one output at a time, provide 1d array')
#        if output.shape[0] == output.size:
#            self.output2evaluate = output #needs adaptation: if given here, update, otherwise internal
#        else:
#            if forevol == False:
#                raise Exception('Sobol variance evaluation considers only 1 ouput value (1D arrays)')
        
        if not repl == self.repl:
            raise Exception('Control if your number of replicates is correct,\
                            since it does not agree with the saved number')   
        #Needed for the vonvergense test 
        if adaptedbaserun:
            baseruns = adaptedbaserun
        else:
            baseruns = self.nbaseruns            
                            
        #prepare sensitivity matrices
        self.Si = np.zeros((repl,self._ndim))
        self.STi = np.zeros((repl,self._ndim))
        if repl >1:
            self.STij = np.zeros((repl, self._ndim, self._ndim))
        else:
            self.STij = np.zeros((self._ndim, self._ndim))
            
        for i in range(repl):
            #Get outputs of A and B
    #        yA = output[0:baseruns]  
    #        yB = output[baseruns:2*baseruns]          
            yA = output[i*baseruns*(self._ndim+2) : (i+1)*baseruns+i*(self._ndim+1)*baseruns] 
            yB = output[(i+1)*baseruns+i*(self._ndim+1)*baseruns : (i+2)*baseruns+i*(self._ndim+1)*baseruns]  
            
            for fac in range(self._ndim): #for everey factor
    #            yC = output[(fac+2)*baseruns:(fac+3)*baseruns]
                yC = output[(i+fac+2)*baseruns+i*(self._ndim+1)*baseruns:(i+fac+3)*baseruns+i*(self._ndim+1)*baseruns]    
        
    #            Vtot = np.var(output[:2*baseruns])
                Vtot = np.var(output[i*baseruns*(self._ndim+2):(i+2)*baseruns+i*(self._ndim+1)*baseruns])                    
                
                #First order effect
                Vi=yB*(yC-yA)
                self.Si[i,fac] = np.mean(Vi)/Vtot
        
                #Total order effect
                VT=(yA-yC)**2
                self.STi[i,fac] = np.mean(VT)/(2*Vtot)
                
            # Total indices for pairs of factors (at same cost)
            #k(k-1)/2 interaction terms to be calculated (fills upper half of matrix)
            for fac1 in range(self._ndim):
                yC1 = output[(i+fac1+2)*baseruns+i*(self._ndim+1)*baseruns:(i+fac1+3)*baseruns+i*(self._ndim+1)*baseruns]
                for fac2 in range(fac1+1,self._ndim):
                    yC2 = output[(i+fac2+2)*baseruns+i*(self._ndim+1)*baseruns:(i+fac2+3)*baseruns+i*(self._ndim+1)*baseruns]
                    VTij = (yC1-yC2)**2  #element wise
                    if i >1:
                        self.STij[i,fac1,fac2] = np.mean(VTij)/(2*Vtot)           
                    else:
                        self.STij[fac1,fac2] = np.mean(VTij)/(2*Vtot)
        return self.Si, self.STi, self.STij

    def runTestModel(self, model, inputsmod, repl = 1):
        ''' Run a testmodel
        
        Use a testmodel to get familiar with the method and try things out. The
        implemented methods are
        * G Sobol function: testfunction with analytical solution 
        * gstarfunction: testfunction with analytical solution,
        extended version of the G sobol function
        
        Parameters
        -----------
        model : string
            name fo the testmodel
        inputsmod : list
            list with all the inputs of the model, except of the sampled stuff
        repl : int
        
        Notes
        ------
        More information on both testfunctions can be found in:
            * G Sobol function [S2]_
            * G* function [S1]_
        '''
        
        
        output = np.zeros((self.Ctorun.shape[0],1))
        
        if model == 'analgfunc':
            ai = inputsmod[0]
            #run the model
            for i in range(self.Ctorun.shape[0]):
                 output[i,:] = analgfunc(ai,self.Ctorun[i,:])

            self.output2evaluate = output
#            print( output.shape)
            self.SobolVariancePost(output, repl = repl)
            
            #Analytical to compare -> G
            Vi = np.zeros(len(ai))
            for i in range(len(ai)):
                Vi[i] = (1./3.)/(1.+ai[i])**2
            
            VTi = np.zeros(len(ai))
            for i in range(len(ai)):
                Vj = np.prod(np.delete(Vi,i)+1.)
                VTi[i] = Vi[i] * Vj
            Vtot = 1.
            for i in range(len(ai)):
                Vtot = Vtot * (1+Vi[i])
            Vtot = Vtot -1.
            
            MAESi = np.zeros(repl)
            for j in range(repl):
                MAESi[j] = np.sum(np.abs(Vi/Vtot-self.Si[j,:]))
            
            MAESTi = np.zeros(repl)
            for j in range(repl):
                MAESTi[j] = np.sum(np.abs(VTi/Vtot-self.STi[j,:]))  

            print( 'Analytical Solution for Si: \n'                )
            print( Vi/Vtot)
            print( 'Sobol solution for Si: \n'            )
            print( self.Si)
            print( 'Mean Absolute Error of Si is:', MAESi.mean())
            print( ' \n Anaytical Solution for STi:'            )
            print( VTi/Vtot)
            print( 'Sobol solution for STi: \n'            )
            print( self.STi)
            print( 'Mean Absolute Error of STi is:', MAESTi.mean())
            print( 'Sobol solution for STij: \n')
            print( self.STij)
        
        elif model == 'analgstarfunc':
            if repl > 1:
                print( 'Caution: replicates not supported on MAE calculation, results not represent')
            ai = inputsmod[0]
            alphai = inputsmod[1]
            di = inputsmod[2]
            for i in range(self.Ctorun.shape[0]):
                output[i,:] = analgstarfunc(ai, alphai, self.Ctorun[i,:], di)
            
            #run post-stuff
            self.SobolVariancePost(output, repl = repl)
            
            ###Analytical to compare -> G*
            Vi = np.zeros(len(ai))
            for i in range(len(ai)):
                Vi[i] = alphai[i]**2./((1.+2.*alphai[i])*(1.+ai[i])**2.)
            
            Vtot = 1.
            for i in range(len(ai)):
                Vtot = Vtot * (1+Vi[i])
            Vtot = Vtot -1.
            
            print( 'Anaytical Solution for Si:')
            print( Vi/Vtot)
            print( 'Sobol solution for Si:')
            print( self.Si)
            print( 'Mean Absolute Error for Si is:', np.sum(np.abs(Vi/Vtot-self.Si)))
        
        else: 
            raise Exception('Use analgfunc or analgstarfunc')
            
    def latexresults(self, name = 'Soboltable.tex'):
        '''
        Print( Results in a "deluxetable" Latex)

        Parameters
        -----------
        name : str.tex
            output file name; use .tex extension in the name
        '''
        if self.repl > 1:
            print( 'Table generates only output of first line!')
            
        fout = open(name,'w')
        t = Table(3, justs='lcc', caption='First order and Total sensitivity index', label="tab:sobol1tot")

        t.add_header_row([' ', '$S_i$', '$S_{Ti}$'])
        col1 = self._namelist[:]
        col2 = self.Si[0].tolist()
        col3 = self.STi[0].tolist()
        col1.append('SUM')
        col2.append(self.Si.sum())
        col3.append(self.STi.sum())
        
        t.add_data([col1,col2,col3], sigfigs=2) #,col3
        t.print_table(fout)
        fout.close()
        print( 'Results latex table file saved in directory %s'%os.getcwd()        )


    def txtresults(self, name = 'Sobolresults.txt'):
        '''
        Results in txt file to load in eg excel

        Parameters
        -----------
        name : str.txt
            output file name; use .txt extension in the name 
        
        '''
        if self.repl > 1:
            print( 'Table generates only output of first line!')
            
        fout = open(name,'w')
        fout.write('Par \t Si \t STi \n')
        for i in range(self._ndim):
            fout.write('%s \t %.8f \t  %.8f \n'%(self._parmap[i], self.Si[0,i], 
                                               self.STi[0,i]))
        fout.write('SUM \t %.8f \t  %.8f \n'%(self.Si.sum(), 
                                               self.STi.sum()))                                              
        fout.close()
        
        print( 'Results file saved in directory %s'%os.getcwd())


    def plotSi(self, width = 0.5, addval = True, sortit = True, 
               *args, **kwargs):
        '''
        Plot a barchart of the given Si
        
        Parameters
        -----------
        width : float (0-1)
            width of the bars in the barchart
        addval : bool
            if True, the morris mu values are added to the graph
        sortit : bool
            if True, larger values (in absolute value) are plotted closest to
            the y-axis      
        *args, **kwargs : args
            passed to the matplotlib.bar 
        
        '''
        if self.repl > 1:
            print( 'Table generates only output of first line!')
            
        fig = plt.figure() 
        ax1 = fig.add_subplot(111)
        ax1 = plotbar(ax1, self.Si[0], self._namelist, width = width, 
                      addval = addval, sortit = True, *args, **kwargs)
        ax1.set_ylabel(r'$S_i$',fontsize=20)
        ax1.yaxis.label.set_rotation('horizontal')
        ax1.yaxis.set_label_coords(-0.02, 1.)  
        plt.draw()

        return fig, ax1
          
        
    def plotSTi(self, width = 0.5, addval = True, sortit = True,
                *args, **kwargs):
        '''
        Plot a barchart of the given STi
        
        Parameters
        -----------
        width : float (0-1)
            width of the bars in the barchart
        addval : bool
            if True, the morris mu values are added to the graph
        sortit : bool
            if True, larger values (in absolute value) are plotted closest to
            the y-axis      
        *args, **kwargs : args
            passed to the matplotlib.bar 
        
        '''
        if self.repl > 1:
            print( 'Table generates only output of first line!')
            
        fig = plt.figure() 
        ax1 = fig.add_subplot(111)
        ax1 = plotbar(ax1, self.STi[0], self._namelist, width = width, 
                      addval = addval, sortit = True, *args, **kwargs)
        ax1.set_ylabel(r'$S_Ti$',fontsize=20)
        ax1.yaxis.label.set_rotation('horizontal')
        ax1.yaxis.set_label_coords(-0.02, 1.)        
        plt.draw()
        return fig, ax1      

    def plotSTij(self, linewidth = 2.):
        '''
        Plot the STij interactive terms 
        
        Parameters
        ------------
        linewidth : float
            width of the black lines of the grid        
        '''
        
        fig,ax1  = interactionplot(self.STij, self._namelist, lwidth = linewidth)
        #add text
        ax1.text(0.1,0.9,r'$ST_{ij}$', transform = ax1.transAxes, fontsize=30, 
                 verticalalignment = 'top', horizontalalignment = 'left') 
        return fig, ax1
    
    def sens_evolution(self, output = None, repl=1, labell = -0.07, *args, **kwargs):
        '''
        Check the convergence of the current sequence
        
        Parameters
        ------------
        output : optional
            if True; this output is used, elsewhere the generated output
        repl : int
            must be 1 to work
        labell : float
            aligns the ylabels
        *args, **kwargs : args
            passed to the matplotlib.plot function        
        
        Returns
        ---------
        Si_evol : ndarray
            Si of the factors in number of nbaseruns
        
        STi_evol : ndarray
            STi of the factors in number of nbaseruns                      
        '''
        if repl > 1:
            raise Exception('Not supported for replicates!')
        
        if not output == None:
            print( 'alternative output...')
            self.output2evaluate = output
        else:
            self.output2evaluate =  self._outputbk
        
        Si_evol = np.zeros((self.nbaseruns, self._ndim,))
        STi_evol = np.zeros((self.nbaseruns, self._ndim))
        for i in range(10,self.nbaseruns):
            A = self.output2evaluate[:i]
            B = self.output2evaluate[self.nbaseruns : self.nbaseruns + i]          
            C = np.vstack((A,B))
            for j in range(self._ndim):    
                nC = self.output2evaluate[(2+j)*self.nbaseruns : (2+j)*self.nbaseruns + i]
                C = np.vstack((C,nC))
            Si,STi,STij = self.SobolVariancePost(C.flatten(), repl = 1, adaptedbaserun = i)
            Si_evol[i,:] = Si
            STi_evol[i,:] = STi  
            
        self.Si_evol = Si_evol
        self.STi_evol = STi_evol
        
        self._plot_evolution(labell = labell, *args, **kwargs)
            
        return Si_evol, STi_evol

    def _plot_evolution(self, labell = -0.06, *args, **kwargs):
        '''
        Plot the convergence of the different factors;
        help function
        
        Parameters
        ------------
        labell : float
            aligns the ylabels
        *args, **kwargs : args
            used in plot function
        
        '''
        fig1, axes1 = plot_evolution(self.Si_evol, self._namelist, 
                                     labell = labell, *args, **kwargs)           
        axes1[0].set_title(r'$S_i$')
        fig2, axes2 = plot_evolution(self.STi_evol, self._namelist, 
                                     labell = labell, *args, **kwargs)        
        axes2[0].set_title(r'$S_{Ti}$')  
        return fig1, axes1, fig2, axes2
                    


                    
# Xi = [(0.0,1.0,'par1'),(0.0,1.0,'par2'),(0.0,1.0,'par3'),(0.0,1.0,'par4'),
      # (0.0,1.0,'par5'),(0.0,1.0,'par6'),(0.0,1.0,'par7'),(0.0,1.0,'par8'),]
      
# ai=[0, 1, 4.5, 9, 99, 99, 99, 99]
# sens1 = SobolVariance(Xi, ModelType = 'testmodel')
# sens1.SobolVariancePre(10000)
# sens1.runTestModel('analgfunc', [ai])

## Example 2
##############
#ai=[0, 1, 4.5, 9, 99, 99, 99, 99]
#alphai = 0.5 * np.ones(len(ai))
##Xi = [(0.0,1.0,'par1'),(0.0,1.0,'par2'),(0.0,1.0,'par3'),(0.0,1.0,'par4'),
##      (0.0,1.0,'par5'),(0.0,1.0,'par6'),(0.0,1.0,'par7'),(0.0,1.0,'par8'),]
#Xi = [(0.0,1.0,r'$X_1$'),(0.0,1.0,r'$X_2$'),(0.0,1.0,r'$X_3$'),(0.0,1.0,r'$X_4$'),
#      (0.0,1.0,r'$X_5$'),(0.0,1.0,r'$X_6$'),(0.0,1.0,r'$X_7$'),(0.0,1.0,r'$X_8$')]      
#di=np.random.random(8)
##set up sensitivity analysis
#sens2 = SobolVariance(Xi, ModelType = 'testmodel')
##Sampling strategy
#sens2.SobolVariancePre(1500)
##Run model
#sens2.runTestModel('analgfunc', [ai, alphai, di]) #here normally other model
##results in txt file 
#sens2.txtresults(name='SobolTestOut.txt')
##results in tex-table 
#sens2.latexresults(name='SobolTestOut.tex')
##Plots
#sens2.plotSi(ec='grey',fc='grey')
#sens2.plotSTi(ec='grey',fc='grey')
#sens2.plotSTij()
#Si_evol, STi_evol = sens2.sens_evolution(color='k')



   
        