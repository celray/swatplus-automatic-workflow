# -*- coding: utf-8 -*-
"""
@author: VHOEYS
"""
import os

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from mpl_toolkits.axes_grid1.inset_locator import zoomed_inset_axes
from mpl_toolkits.axes_grid1.inset_locator import mark_inset
from matplotlib.transforms import offset_copy

from .sensitivity_base import *
from .extrafunctions import *
from .plot_functions_rev import plotbar, scatterwithtext
from .latextablegenerator import *

class MorrisScreening(SensitivityAnalysis):
    '''
    Morris screening method, with the improved sampling strategy,
    selecting a subset of the trajectories to improve the sampled space.
    Working with groups is possible.

    Parameters
    -----------
    parsin : list
        either a list of (min,max,'name') values,
        [(min,max,'name'),(min,max,'name'),...(min,max,'name')]
        or a list of ModPar instances
    ModelType : pyFUSE | PCRaster | external
        Give the type of model working withµ

    Attributes
    ------------
    _ndim :  int
        number of factors examined. In case the groups are chosen the number of factors is stores in NumFact and sizea becomes the number of created groups, (k)
    NumFact : int
        number of factors examined in the case when groups are chosen
    intervals(p) : int
        number of intervals considered in (0, 1)
    UB : ndarray
        Upper Bound for each factor in list or array, (sizea,1)
    LB : ndarray
        Lower Bound for each factor in list or array, (sizea,1)
    GroupNumber : int
        Number of groups (eventually 0)
    GroupMat : ndarray
        Array which describes the chosen groups. Each column represents
        a group and its elements are set to 1 in correspondence of the
        factors that belong to the fixed group. All the other elements
        are zero, (NumFact,GroupNumber)
    Delta : float
        jump value to calculate screening
    intervals : int
        number of intervals used in the sampling
    noptimized : int
        r-value of the number of base runs are done in the optimize sampling
    OutMatrix : ndarray
        not-optimized sample matrix
    OutFact : ndarray
        not-optimzed matrix of changing factors
    Groupnumber : int
        number of groups used
    sizeb : int
        when using groups, sizeb is determined by the number of groups,
        otherwise the number of factors
    OptMatrix_b : ndarray
        the not-adapted version of the OptMatrix, with all sampled values
        between, 0 and 1
    parset2run : ndarrar
        every row is a parameter set to run the model for. All sensitivity
        methods have this attribute to interact with base-class running

    Notes
    ---------
    Original Matlab code from:
        http://sensitivity-analysis.jrc.it/software/index.htm

    Original method described in [M1]_, improved by the optimization of [M2]_.
    The option to work with groups is added, as described in [M2]_.

    Examples
    ------------
    >>> Xi = [(0.0,5.0,r'$X_1$'),(4.0,7.0,r'$X_2$'),(0.0,1.0,r'$X_3$'),
              (0.0,1.0,r'$X_4$'), (0.0,1.0,r'$X_5$'),(0.5,0.9,r'$X_6$')]
    >>> # Set up the morris class instance with uncertain factors Xi
    >>> sm = MorrisScreening(Xi,ModelType = 'external')
    >>> # calculate an optimized set of parameter sets to run model
    >>> OptMatrix, OptOutVec = sm.Optimized_Groups(nbaseruns=100,
                                               intervals = 4, noptimized=4,
                                               Delta = 0.4)
    >>> # Check the quality of the selected trajects
    >>> sm.Optimized_diagnostic(width=0.15)
    >>> #RUN A MODEL AND GET OUTPUT (EXTERNAL) -> get output
    >>> #Calculate the Morris screening diagnostics
    >>> sm.Morris_Measure_Groups(output)
    >>> #plot a barplot of mu, mustar and sigma (edgecolor and facecolor grey)
    >>> sm.plotmu(ec='grey',fc='grey')
    >>> sm.plotmustar(outputid = 1,ec='grey',fc='grey')
    >>> sm.plotsigma(ec='grey',fc='grey')
    >>> #plot the mu* sigma plain
    >>> sm.plotmustarsigma(zoomperc = 0.05, outputid = 1, loc = 2)
    >>> #export the results in txt file
    >>> sm.txtresults(name='MorrisTestOut.txt')
    >>> #export the results in tex-table
    >>> sm.latexresults(name='MorrisTestOut.tex')


    References
    ------------
    ..  [M1] Morris, Max D. Factorial Sampling Plans for Preliminary Computational
        Experiments. Technometrics 33, no. 2 (1991): 161–174.

    ..  [M2] Campolongo, Francesca, Jessica Cariboni, and Andrea Saltelli.
        An Effective Screening Design for Sensitivity Analysis of Large Models.
        Environmental Modelling & Software 22, no. 10 (October 2007): 1509–1518.
        http://linkinghub.elsevier.com/retrieve/pii/S1364815206002805.

    ..  [M3] Saltelli, Andrea, Marco Ratto, Terry Andres, Francesca Campolongo,
        Jessica Cariboni, Debora Gatelli, Michaela Saisana, and Stefano Tarantola.
        Global Sensitivity Analysis, The Primer. John Wiley & Sons Ltd, 2008.
    '''

    def __init__(self, parsin, ModelType = 'external'):
        SensitivityAnalysis.__init__(self, parsin)

        self._methodname = 'MorrisScreening'

        if ModelType == 'pyFUSE':
            self.modeltype = 'pyFUSE'
            print('The analysed model is built up by the pyFUSE environment')
        elif ModelType == 'external':
            self.modeltype = 'pyFUSE'
            print('The analysed model is externally run')
        elif ModelType == 'PCRaster':
            self.modeltype = 'PCRasterPython'
            print('The analysed model is a PCRasterPython Framework instance')
        elif ModelType == 'testmodel':
            self.modeltype = 'testmodel'
            print('The analysed model is a testmodel')
        else:
            raise Exception('Not supported model type')

        self.LB = np.array([el[0] for el in self._parsin])
        self.UB = np.array([el[1] for el in self._parsin])

    def Sampling_Function_2(self, nbaseruns, LB, UB):
        '''
        Python version of the Morris sampling function

        Parameters
        -----------
        nbaseruns : int
            sample size

        Returns
        ---------
        OutMatrix(sizeb*r, sizea) :
            for the entire sample size computed In(i,j) matrices, values to
            run model for
        OutFact(sizea*r,1) :
            for the entire sample size computed Fact(i,1) vectors, indicates
            the factor changing at specific line

        Notes
        -------
        B0 is constructed as in Morris design when groups are not considered.
        When groups are considered the routine follows the following steps

        1. Creation of P0 and DD0 matrices defined in Morris for the groups.
        This means that the dimensions of these 2 matrices are
        (GroupNumber,GroupNumber).

        2. Creation of AuxMat matrix with (GroupNumber+1,GroupNumber)
        elements.

        3. Definition of GroupB0 starting from AuxMat, GroupMat
        and P0.

        4. The final B0 for groups is obtained as [ones(sizeb,1)*x0' + GroupB0].
        The P0 permutation is present in GroupB0 and it's not necessary to
        permute the matrix (ones(sizeb,1)*x0') because it's already randomly
        created.

        Adapted from the matlab version of 15 November 2005 by J.Cariboni

        References
        -------------
        ..  [M4] A. Saltelli, K. Chan, E.M. Scott, Sensitivity Analysis
            on page 68 ss
        ..  [M5] F. Campolongo, J. Cariboni, JRC - IPSC Ispra, Varese, IT

        '''

        #The integration in class version not optimal, therefor this mapping
        k = self._ndim
        self.nbaseruns = nbaseruns
        r = nbaseruns
        p = self.intervals
        GroupMat = self.GroupMat

        # Parameters and initialisation of the output matrix
        sizea = k
        Delta = self.Delta
        NumFact = sizea
        if GroupMat.shape[0]==GroupMat.size:
            Groupnumber=0
        else:
            Groupnumber = GroupMat.shape[1]    #size(GroupMat,2)
            sizea = GroupMat.shape[1]

        sizeb = sizea + 1
        #    sizec = 1

        Outmatrix = np.zeros(((sizea+1)*r,NumFact))
        OutFact = np.zeros(((sizea+1)*r,1))
        # For each i generate a trajectory
        for i in range(r):
            Fact=np.zeros(sizea+1)
            # Construct DD0
            DD0 = np.matrix(np.diagflat(np.sign(np.random.random(k)*2-1)))

            # Construct B (lower triangular)
            B = np.matrix(np.tri((sizeb), sizea,k=-1, dtype=int))

            # Construct A0, A
            A0 = np.ones((sizeb,1))
            A = np.ones((sizeb,NumFact))

            # Construct the permutation matrix P0. In each column of P0 one randomly chosen element equals 1
            # while all the others equal zero.
            # P0 tells the order in which order factors are changed in each
            # Note that P0 is then used reading it by rows.
            I = np.matrix(np.eye(sizea))
            P0 = I[:,np.random.permutation(sizea)]

            # When groups are present the random permutation is done only on B. The effect is the same since
            # the added part (A0*x0') is completely random.
            if Groupnumber != 0:
                B = B * (np.matrix(GroupMat)*P0.transpose()).transpose()

            # Compute AuxMat both for single factors and groups analysis. For Single factors analysis
            # AuxMat is added to (A0*X0) and then permutated through P0. When groups are active AuxMat is
            # used to build GroupB0. AuxMat is created considering DD0. If the element on DD0 diagonal
            # is 1 then AuxMat will start with zero and add Delta. If the element on DD0 diagonal is -1
            # then DD0 will start Delta and goes to zero.
            AuxMat = Delta* 0.5 *((2*B - A) * DD0 + A)

            #----------------------------------------------------------------------
            # a --> Define the random vector x0 for the factors. Note that x0 takes value in the hypercube
            # [0,...,1-Delta]*[0,...,1-Delta]*[0,...,1-Delta]*[0,...,1-Delta]
            xset=np.arange(0.0,1.0-Delta,1.0/(p-1))
            try:
                x0 = np.matrix(xset.take(list(np.ceil(np.random.random(k)*np.floor(p/2))-1)))  #.transpose()
            except:
                raise Exception('invalid p (intervals) and Delta combination, please adapt')

            #----------------------------------------------------------------------
            # b --> Compute the matrix B*, here indicated as B0. Each row in B0 is a
            # trajectory for Morris Calculations. The dimension  of B0 is (Numfactors+1,Numfactors)
            if Groupnumber != 0:
                B0 = (A0*x0 + AuxMat)
            else:
                B0 = (A0*x0 + AuxMat)*P0

            #----------------------------------------------------------------------
            # c --> Compute values in the original intervals
            # B0 has values x(i,j) in [0, 1/(p -1), 2/(p -1), ... , 1].
            # To obtain values in the original intervals [LB, UB] we compute
            # LB(j) + x(i,j)*(UB(j)-LB(j))
            In=np.tile(LB, (sizeb,1)) + np.array(B0)*np.tile((UB-LB), (sizeb,1)) #array!! ????

            # Create the Factor vector. Each component of this vector indicate which factor or group of factor
            # has been changed in each step of the trajectory.
            for j in range(sizea):
                Fact[j] = np.where(P0[j,:])[1]
            Fact[sizea] = int(-1)  #Enkel om vorm logisch te houden. of Fact kleiner maken

            #append the create traject to the others
            Outmatrix[i*(sizea+1):i*(sizea+1)+(sizea+1),:]=np.array(In)
            OutFact[i*(sizea+1):i*(sizea+1)+(sizea+1)]=np.array(Fact).reshape((sizea+1,1))

        return Outmatrix, OutFact

    def Optimized_Groups(self, nbaseruns=500, intervals = 4, noptimized=10,
                         GroupMat=np.array([]), Delta = 'default'):
        '''
        Optimization in the choice of trajectories for the Morris experiment.
        Starting from an initial set of nbaseruns, a set of noptimized runs
        is selected to use for the screening techique

        Groups can be used to evaluate parameters together

        Parameters
        ------------
        nbaseruns : int (default 500)
            Total number of trajectories
        intervals : int (default 4)
            Number of levels
        noptimized : int (default 10)
            Final number of optimal trajectories
        GroupMat : [NumFact,NumGroups]
            Matrix describing the groups. Each column represents a group and
            its elements are set to 1 in correspondence of the factors that
            belong to the fixed group. All the other elements are zero.
        Delta : 'default'|float (0-1)
            When default, the value is calculated from the p value (intervals),
            otherwise the given number is taken

        Returns
        --------
        OptMatrix/ self.OptOutMatrix : ndarray
            Optimized sampled values giving the matrix too run the model for

        OptOutVec/ self.OptOutFact : ndarray
            Optimized sampled values giving the matrix indicating the factor
            changed at a specific line


        Notes
        -----
        The combination of Delta and intervals is important to get an
        good overview. The user is directed to [M3]_

        '''
        #number of trajectorie (r)
        N = nbaseruns

        #check the p and Delta value workaround
        if not intervals%2==0:
            print('It is adviced to use an even number for the p-value, number \
            of intervals, since currently not all levels are explored')

        if Delta == 'default':
            self.Delta = intervals/(2.*(intervals-1.))
        else:
            if Delta > 0.0 and Delta < 1.0:
                self.Delta = Delta
            else:
                raise Exception('Invalid Delta value, please use default or float number')

        self.intervals = intervals

#        p = intervals
        self.noptimized = noptimized
        r = noptimized
        self.GroupMat = GroupMat
        NumFact = self._ndim

        LBt = np.zeros(NumFact)
        UBt = np.ones(NumFact)

        OutMatrix, OutFact = self.Sampling_Function_2(nbaseruns, LBt, UBt) #Version with Groups

        #again mapping (not optimal)
        self.OutMatrix = OutMatrix
        self.OutFact = OutFact

        try:
            Groupnumber = GroupMat.shape[1]
        except:
            Groupnumber = 0

        self.Groupnumber = Groupnumber

        if Groupnumber != 0:
            sizeb = Groupnumber +1
        else:
            sizeb = NumFact +1

        self.sizeb = sizeb

        Dist = np.zeros((N,N))
        Diff_Traj = np.arange(0.0,N,1.0)

        # Compute the distance between all pair of trajectories (sum of the distances between points)
        # The distance matrix is a matrix N*N
        # The distance is defined as the sum of the distances between all pairs of points
        # if the two trajectories differ, 0 otherwise
        for j in range(N):   #combine all trajectories: eg N=3: 0&1; 0&2; 1&2 (is not dependent from sequence)
            for z in range(j+1,N):
                MyDist = np.zeros((sizeb,sizeb))
                for i in range(sizeb):
                    for k in range(sizeb):
                        MyDist[i,k] = (np.sum((OutMatrix[sizeb*(j)+i,:]-OutMatrix[sizeb*(z)+k,:])**2))**0.5 #indices aan te passen
                if np.where(MyDist==0)[0].size == sizeb:
                    # Same trajectory. If the number of zeros in Dist matrix is equal to
                    # (NumFact+1) then the trajectory is a replica. In fact (NumFact+1) is the maximum numebr of
                    # points that two trajectories can have in common
                    Dist[j,z] = 0.
                    Dist[z,j] = 0.

                    # Memorise the replicated trajectory
                    Diff_Traj[z] = -1.  #the z value identifies the duplicate
                else:
                    # Define the distance between two trajectories as
                    # the minimum distance among their points
                    Dist[j,z] = np.sum(MyDist)
                    Dist[z,j] = np.sum(MyDist)

        #prepare array with excluded duplicates (alternative would be deleting rows)
        dupli=np.where(Diff_Traj == -1)[0].size
        New_OutMatrix = np.zeros(((sizeb)*(N-dupli),NumFact))
        New_OutFact = np.zeros(((sizeb)*(N-dupli),1))

        # Eliminate replicated trajectories in the sampled matrix
        ID=0
        for i in range(N):
            if Diff_Traj[i]!= -1.:
                New_OutMatrix[ID*sizeb:ID*sizeb+sizeb,:] = OutMatrix[i*(sizeb) : i*(sizeb) + sizeb,:]
                New_OutFact[ID*sizeb:ID*sizeb+sizeb,:] = OutFact[i*(sizeb) : i*(sizeb) + sizeb,:]
                ID+=1

        # Select in the distance matrix only the rows and columns of different trajectories
        Dist_Diff = Dist[np.where(Diff_Traj != -1)[0],:] #moet 2D matrix zijn... wis rijen ipv hou bij
        Dist_Diff = Dist_Diff[:,np.where(Diff_Traj != -1)[0]] #moet 2D matrix zijn... wis rijen ipv hou bij
        #    Dist_Diff = np.delete(Dist_Diff,np.where(Diff_Traj==-1.)[0])
        New_N = np.size(np.where(Diff_Traj != -1)[0])

        # Select the optimal set of trajectories
        Traj_Vec = np.zeros((New_N, r))
        OptDist = np.zeros((New_N, r))
        for m in range(New_N):                  #each row in Traj_Vec
            Traj_Vec[m,0]=m

            for z in range(1,r):              #elements in columns after first
                Max_New_Dist_Diff = 0.0

                for j in range(New_N):
                    # Check that trajectory j is not already in
                    Is_done = False
                    for h in range(z):
                        if j == Traj_Vec[m,h]:
                            Is_done=True

                    if Is_done == False:
                        New_Dist_Diff = 0.0

                        #compute distance
                        for k in range(z):
                            New_Dist_Diff = New_Dist_Diff + (Dist_Diff[Traj_Vec[m, k],j])**2

                        # Check if the distance is greater than the old one
                        if New_Dist_Diff**0.5 > Max_New_Dist_Diff:
                            Max_New_Dist_Diff = New_Dist_Diff**0.5
                            Pippo = j

                # Set the new trajectory
                Traj_Vec[m,z] = Pippo
                OptDist[m,z] = Max_New_Dist_Diff

        # Construct optimal matrix
        SumOptDist = np.sum(OptDist, axis=1)
        # Find the maximum distance
        Pluto = np.where(SumOptDist == np.max(SumOptDist))[0]
        Opt_Traj_Vec = Traj_Vec[Pluto[0],:]

        OptMatrix = np.zeros(((sizeb)*r,NumFact))
        OptOutVec = np.zeros(((sizeb)*r,1))

        for k in range(r):
            OptMatrix[k*(sizeb):k*(sizeb)+(sizeb),:]= New_OutMatrix[(sizeb)*(Opt_Traj_Vec[k]):(sizeb)*(Opt_Traj_Vec[k]) + sizeb,:]
            OptOutVec[k*(sizeb):k*(sizeb)+(sizeb)]= New_OutFact[(sizeb)*(Opt_Traj_Vec[k]):(sizeb)*(Opt_Traj_Vec[k])+ sizeb,:]

        #----------------------------------------------------------------------
        # Compute values in the original intervals
        # Optmatrix has values x(i,j) in [0, 1/(p -1), 2/(p -1), ... , 1].
        # To obtain values in the original intervals [LB, UB] we compute
        # LB(j) + x(i,j)*(UB(j)-LB(j))
        self.OptMatrix_b = OptMatrix.copy()
        OptMatrix=np.tile(self.LB, (sizeb*r,1)) + OptMatrix*np.tile((self.UB-self.LB), (sizeb*r,1))

        self.OptOutMatrix = OptMatrix
        self.OptOutFact = OptOutVec

        self.parset2run = OptMatrix
        self.totalnumberruns = self.parset2run.shape[0]

        return OptMatrix, OptOutVec

    def Optimized_diagnostic(self, width = 0.1):
        '''
        Evaluate the optimized trajects in their space distirbution,
        evaluation is done based on the [0-1] boundaries of the sampling

        Returns quality measure and 2 figures to compare the optimized version

        Parameters
        -----------
        width : float
            width of the bars in the plot (default 0.1)

        Examples
        ---------
        >>> sm.Optimized_diagnostic()
        The quality of the sampling strategy changed from 0.76 with the old
        strategy to 0.88 for the optimized strategy
        '''
        NumFact = self._ndim
        sizeb = self.sizeb
        p = self.intervals
        r = self.noptimized
        # Clean the trajectories from repetitions and plot the histograms
        hplot=np.zeros((2*r,NumFact))

        for i in range(NumFact):
            for j in range(r):
                # select the first value of the factor
                hplot[j*2,i] = self.OptMatrix_b[j*sizeb,i]

                # search the second value
                for ii in range(1,sizeb):
                    if self.OptMatrix_b[j*sizeb+ii,i] != self.OptMatrix_b[j*sizeb,i]:
                        kk = 1
                        hplot[j*2+kk,i] = self.OptMatrix_b[j*sizeb+ii,i]

        fig=plt.figure()
        fig.subplots_adjust(hspace=0.3,wspace = 0.1)
        fig.suptitle('Optimized sampling')
#        DimPlots = np.round(NumFact/2)
        DimPlots = int(np.ceil(NumFact/2.))
#        print hplot.shape
        for i in range(NumFact):
            ax=fig.add_subplot(DimPlots,2,i+1)
#            n, bins, patches = ax.hist(hplot[:,i], p, color='k',ec='white')
            n, bin_edges = np.histogram(hplot[:,i], bins = p,)

            bwidth = width
            xlocations = np.linspace(0.,1.,self.intervals)-bwidth/2.
            ax.bar(xlocations, n, width = bwidth, color='k')

            majloc1 = MaxNLocator(nbins=4, prune='lower', integer=True)
            ax.yaxis.set_major_locator(majloc1)
            for tick in ax.yaxis.get_major_ticks():
                tick.label.set_fontsize(10)

            ax.set_xlim([-0.25,1.25])
            ax.set_ylim([0,n.max()+n.max()*0.1])
            ax.xaxis.set_ticks([0.0,1.0])
            for tick in ax.xaxis.get_major_ticks():
                tick.label.set_fontsize(10)
            ax.set_xlabel(self._namelist[i],fontsize=10)
            ax.xaxis.set_label_coords(0.5, -0.08)

        # Plot the histogram for the original sampling strategy
        # Select the matrix
        OrigSample = self.OutMatrix[:r*(sizeb),:]
        Orihplot = np.zeros((2*r,NumFact))

        for i in range(NumFact):
            for j in range(r):
                # select the first value of the factor
                Orihplot[j*2,i] = OrigSample[j*sizeb,i]

                # search the second value
                for ii in range(1,sizeb):
                    if OrigSample[j*sizeb+ii,i] != OrigSample[j*sizeb,i]:
                        kk = 1
                        Orihplot[j*2+kk,i] = OrigSample[j*sizeb+ii,i]

        fig=plt.figure()
        fig.subplots_adjust(hspace=0.25,wspace=0.1)
        fig.suptitle('Original sampling')
#        DimPlots = np.round(NumFact/2)
        DimPlots = int(np.ceil(NumFact/2.))
        for i in range(NumFact):
            ax=fig.add_subplot(DimPlots,2,i+1)
            n, bin_edges = np.histogram(Orihplot[:,i], bins = p,)

            bwidth = width
            xlocations = np.linspace(0.,1.,self.intervals)-bwidth/2.
            ax.bar(xlocations, n, width = bwidth, color='k')

            majloc1 = MaxNLocator(nbins=4, prune='lower', integer=True)
            ax.yaxis.set_major_locator(majloc1)
            for tick in ax.yaxis.get_major_ticks():
                tick.label.set_fontsize(10)

            ax.set_xlim([-0.25,1.25])
            ax.set_ylim([0,n.max()+n.max()*0.1])
            ax.xaxis.set_ticks([0.0,1.0])
            for tick in ax.xaxis.get_major_ticks():
                tick.label.set_fontsize(10)
            ax.set_xlabel(self._namelist[i],fontsize=10)
            ax.xaxis.set_label_coords(0.5, -0.08)

        # Measure the quality of the sampling strategy
        levels = np.arange(0.0, 1.1, 1.0/(p-1))
        NumSPoint = np.zeros((NumFact,p))
        NumSOrigPoint=np.zeros((NumFact,p))
        for i in range(NumFact):
            for j in range(p):
                # For each factor and each level count the number of times the factor is on the level
                #This for the new and original sampling
                NumSPoint[i,j] = np.where(np.abs(hplot[:,i]-np.tile(levels[j], hplot.shape[0]))<1e-5)[0].size
                NumSOrigPoint[i,j] = np.where(np.abs(Orihplot[:,i]-np.tile(levels[j], Orihplot.shape[0]))<1e-5)[0].size

        # The optimal sampling has values uniformly distributed across the levels
        OptSampl = 2.*r/p
        QualMeasure = 0.
        QualOriMeasure = 0.
        for i in range(NumFact):
            for j in range(p):
                QualMeasure = QualMeasure + np.abs(NumSPoint[i,j]-OptSampl)
                QualOriMeasure = QualOriMeasure + np.abs(NumSOrigPoint[i,j]-OptSampl)

        QualMeasure = 1. - QualMeasure/(OptSampl*p*NumFact)
        QualOriMeasure = 1. - QualOriMeasure/(OptSampl*p*NumFact)

        self.QualMeasure = QualMeasure
        self.QualOriMeasure = QualOriMeasure

        print('The quality of the sampling strategy changed from %.3f with the old strategy to %.3f for the optimized strategy' %(QualOriMeasure,QualMeasure))

    def Morris_Measure_Groups(self, Output):
        '''
        Calculates the Morris measures mu, mustar and sigma,
        the calculations with groups are in beta-version!

        Can be used for multiple outputs

        Parameters
        ------------
        Output : ndarray
            if multiple outputs, every output in different column; the length
            of the outputs is the same as the optmatrix sampled

        Returns
        ----------
        SAmeas : ndarray (_ndim*number of outputs, noptimized)
            matrix with the elemenary effects, the factors in the rows,
            with different outputs after eachother; the columns take the
            repititions

        OutMatrix : ndarray
            Matrix of the output(s) values in correspondence of each point
            of each trajectory. For every output column, the factors are
            calculated and [Mu*, Mu, StDev] are put in the row
            When using groups, only Mu* for every group is given

        Notes
        --------
        The algorithm uses the self.OptOutMatrix and self.OptOutFact as the
        input calculations, but these can be given other input combinations too
        as long as it follows the Morris-method

        '''

        self.output2evaluate = Output

        NumFact = self._ndim
        #TO CHECK!!! sample nemen als de factor-grenzen of als de 0-1 grenzen?
        #vroeger sample = self.OptMatrix; ik denk self.OptMatrix_b; maakt niet uit
        Sample = self.OptOutMatrix
        OutFact = self.OptOutFact
#        p = self.intervals
        Group = self.GroupMat

        try:
            NumGroups = Group.shape[1]
            print('%d Groups are used' %NumGroups)
        except:
            NumGroups = 0
            print('No Groups are used')
        print(NumGroups, type(NumGroups))
#        Delt = p/(2.*(p-1.))
        Delt = self.Delta

        if NumGroups != 0:
            sizea=NumGroups
            sizeb=sizea+1
            GroupMat=Group
            GroupMat = GroupMat.transpose()
            print(NumGroups)
        else:
            sizea = NumFact
            sizeb=sizea+1

        r = Sample.shape[0]/(sizea+1)

        try:
            NumOutp = Output.shape[1] #outputs combined in columns
        except:
            NumOutp = 1
            Output=Output.reshape((Output.size,1))


        # For each Output
        if NumGroups == 0:
            OutMatrix=np.zeros((NumOutp*NumFact,3)) #for every output: every factor is a line, columns are mu*,mu and std
        else:
            OutMatrix=np.zeros((NumOutp*NumFact,1)) #for every output: every factor is a line, column is mu*

        SAmeas_out=np.zeros((NumOutp*NumFact,r))

        for k in range(NumOutp):
            OutValues=Output[:,k]

            #For each trajectory
            SAmeas=np.zeros((NumFact,r)) #vorm afhankelijk maken van group of niet...
            for i in range(r):
                # For each step j in the trajectory
                # Read the orientation matrix fact for the r-th sampling
                # Read the corresponding output values
                # read the line of changing factors

                Single_Sample = Sample[i*(sizeb):i*(sizeb)+(sizeb),:]
                Single_OutValues = OutValues[i*(sizeb):i*(sizeb)+(sizeb)]
                Single_Facts = OutFact[i*(sizeb):i*(sizeb)+(sizeb)] #gives factor in change (or group)

                A = (Single_Sample[1:sizeb,:]-Single_Sample[:sizea,:]).transpose()
                Delta=A[np.where(A)] #AAN TE PASSEN?

                # For each point of the fixed trajectory compute the values of the Morris function.
                for j in range(sizea):
                    if NumGroups != 0:  #work with groups
                        Auxfind=A[:,j]
                        Change_factor = np.where(np.abs(Auxfind)>1e-010)[0]
                        for gk in Change_factor:
                            SAmeas[gk,i] = np.abs((Single_OutValues[j] - Single_OutValues[j+1])/Delt)   #nog niet volledig goe

                    else:
                        if Delta[j]> 0.0:
                            SAmeas[int(Single_Facts[j]),i] = (Single_OutValues[j+1] - Single_OutValues[j])/Delt
                        else:
                            SAmeas[int(Single_Facts[j]),i] = (Single_OutValues[j] - Single_OutValues[j+1])/Delt

            # Compute Mu AbsMu and StDev
            if np.isnan(SAmeas).any():
                AbsMu = np.zeros(NumFact)
                Stdev = np.zeros(NumFact)
                Mu=np.zeros(NumFact)

                for j in range(NumFact):
                    SAm=SAmeas[j,:]
                    SAm=SAm[~np.isnan(SAm)]
                    rr=np.float(SAm.size)
                    AbsMu[j] = np.sum(np.abs(SAm))/rr
                    if NumGroups == 0:
                        Mu[j] = SAm.mean()
                        Stdev[j] = np.std(SAm, dtype=np.float64, ddof=1) #ddof: /N-1 instead of /N
            else:
                AbsMu = np.sum(np.abs(SAmeas),axis=1)/r
                if NumGroups == 0:
                    Mu = SAmeas.mean(axis=1)
                    Stdev = np.std(SAmeas, dtype=np.float64, ddof=1,axis=1) #ddof: /N-1 instead of /N
                else:
                    Stdev=np.zeros(NumFact)
                    Mu=np.zeros(NumFact)

            OutMatrix[k*NumFact:k*NumFact+NumFact,0]=AbsMu
            if NumGroups == 0:
                OutMatrix[k*NumFact:k*NumFact+NumFact,1]=Mu
                OutMatrix[k*NumFact:k*NumFact+NumFact,2]=Stdev

            SAmeas_out[k*NumFact:k*NumFact+NumFact,:]=SAmeas

            self.SAmeas_out = SAmeas_out
            self.OutMatrix = OutMatrix
            # if no groups
            if NumGroups == 0:
                self.mustar = OutMatrix[:,0]
                self.mu = OutMatrix[:,1]
                self.sigma = OutMatrix[:,2] #for every output: every factor is a line, columns are mu*,mu and std
                if self.sigma.shape[0] > self._ndim:
                    print('Different outputs are used, so split them in comparing the output, by using outputid')
            else:
                self.mustar = OutMatrix[:]



        return SAmeas_out, OutMatrix

    def runTestModel(self, ai):
        ''' Run a testmodel

        Use a testmodel to get familiar with the method and try things out. The
        implemented model is the G Sobol function: testfunction with
        analytical solution, moire information, see [M3]_

        Parameters
        -----------
        ai : list
            list with the input factors (equal size as number of factors)

        Examples
        ---------
        >>> ai=[78, 12, 0.5, 2, 97, 33]
        >>> Xi = [(0.0,1.0,r'$X_1$'),(0.0,1.0,r'$X_2$'),(0.0,1.0,r'$X_3$'),
                  (0.0,1.0,r'$X_4$'),(0.0,1.0,r'$X_5$'),(0.0,1.0,r'$X_6$')]
        >>> #set up the morris screening class
        >>> sm = MorrisScreening(Xi,ModelType = 'testmodel')
        >>> #Get an optimized set of trajectories
        >>> OptMatrix, OptOutVec = sm.Optimized_Groups(nbaseruns=100,
                                                       intervals = 4,
                                                       noptimized=4,
                                                       Delta = 0.4)
        >>> #compare the selected trajects with the general
        >>> sm.Optimized_diagnostic(width=0.15)
        >>> #run a testmodel and get the outputs
        >>> sm.runTestModel(ai)

        '''

        output = np.zeros((sm.OptOutMatrix.shape[0],1))
        for i in range(sm.OptOutMatrix.shape[0]):
             output[i,:] = analgfunc(ai,sm.OptOutMatrix[i,:])

        SAmeas_out, OutMatrix = self.Morris_Measure_Groups(output)

        print('Higher values of ai correspond to lower importance of Xi \n')

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

        print('Morris gives only qualitive measures of importance, \n')
        print('a correspondance between STi and mustar is expected \n')
        print('and compared here \n')
        print(' \n')

        print('Analytical Solution for STi: \n')
        print(VTi/Vtot)
        print('The Morris mu* results: \n')
        print(self.mustar)

        print('A barplot is generated...')
        fig, ax1 = self.plotmustar(width=0.15, ec='grey',fc='grey')
        ax1.set_title('Morris screening result')
        fig2 = plt.figure()
        ax2 = fig2.add_subplot(111)
        ax2 = plotbar(ax2, VTi/Vtot, self._namelist, width = 0.15,
                      addval = True, sortit = True, ec='grey',fc='grey')
        ax2.set_title('Analytical result')


    def latexresults(self, outputid=0, name = 'Morristable.tex'):
        '''
        Print Results in a "deluxetable" Latex

        Parameters
        -----------
        outputid : int
            teh output to use when evaluation for multiple outputs are calculated
        name : str.tex
            output file name; use .tex extension in the name
        '''
        print('tex: The %d th output evaluation criterion is used'%(outputid+1))

        mu2use = self.mu[outputid*self._ndim:(outputid+1)*self._ndim]
        mustar2use = self.mustar[outputid*self._ndim:(outputid+1)*self._ndim]
        sigma2use = self.sigma[outputid*self._ndim:(outputid+1)*self._ndim]

        fout = open(name,'w')
        t = Table(4, justs='lccc', caption='Morris evaluation criteria', label="tab:morris1tot")

        t.add_header_row([' ', '$\mu$', '$\mu^*$', '$\sigma$'])
        col1 = self._namelist[:]
        col2 = mu2use.tolist()
        col3 = mustar2use.tolist()
        col4 = sigma2use.tolist()

        t.add_data([col1,col2,col3,col4], sigfigs=2) #,col3
        t.print_table(fout)
        fout.close()
        print('Latex Results latex table file saved in directory %s'%os.getcwd())


    def txtresults(self, outputid=0, name = 'Morrisresults.txt'):
        '''
        Results in txt file to load in eg excel

        Parameters
        -----------
        outputid : int
            the output to use when evaluation for multiple outputs are calculated
        name : str.txt
            output file name; use .txt extension in the name

        '''
        print('txt: The %d th output evaluation criterion is used'%(outputid+1))

        mu2use = self.mu[outputid*self._ndim:(outputid+1)*self._ndim]
        mustar2use = self.mustar[outputid*self._ndim:(outputid+1)*self._ndim]
        sigma2use = self.sigma[outputid*self._ndim:(outputid+1)*self._ndim]

        fout = open(name,'w')
        fout.write('Par \t mu \t mustar \t sigma \n')
        for i in range(self._ndim):
            fout.write('%s \t %.8f \t  %.8f \t  %.8f \n'%(self._parmap[i],
                                                          mu2use[i],
                                                          mustar2use[i],
                                                          sigma2use[i]))
        fout.close()
        print('txt Results file saved in directory %s'%os.getcwd())

    def plotmu(self, width = 0.5, addval = True, sortit = True, outputid = 0,
                *args, **kwargs):
        '''
        Plot a barchart of the given mu
        
        mu is a measure for the first-order effect on the model output. However
        the use of mu can be tricky because if the model is non-monotonic
        negative elements can be in the parameter distribution and by taking the
        mean of the variance (= mu!) the netto effect is cancelled out! Should
        always be used together with plotsigma in order to see whether higher
        order effects are occuring, high sigma values with low mu values can 
        be caused by non-monotonicity of functions. In order to check this use
        plotmustar and/or plotmustarsigma

        Parameters
        -----------
        width : float (0-1)
            width of the bars in the barchart
        addval : bool
            if True, the morris mu values are added to the graph
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
        fig = plt.figure()
        ax1 = fig.add_subplot(111)
        ax1 = plotbar(ax1, self.mu[outputid*self._ndim:(outputid+1)*self._ndim], self._namelist, width = width,
                      addval = addval, sortit = True, *args, **kwargs)
        ax1.set_ylabel(r'$\mu$',fontsize=20)
        ax1.yaxis.label.set_rotation('horizontal')
        ax1.yaxis.set_label_coords(-0.02, 1.)
        plt.draw()
        return fig, ax1

    def plotmustar(self, width = 0.5, addval = True, sortit = True, outputid = 0,
                *args, **kwargs):
        '''
        Plot a barchart of the given mustar
        
        mu* is a measure for the first-order effect on the model output.
        By taking the average of the absolute values of the parameter
        distribution, the absolute effect on the output can be calculated. This
        is very useful when you are working with non-monotonic functions. The
        drawback is that you lose information about the direction of influence 
        (is this factor influencing the output in a positive or negative way?).
        For the direction of influence use plotmustar!

        Parameters
        -----------
        width : float (0-1)
            width of the bars in the barchart
        addval : bool
            if True, the morris values are added to the graph
        sortit : bool
            if True, larger values (in absolute value) are plotted closest to
            the y-axis
        outputid : int
            the output to use whe multiple are compared; starts with 0
        *args, **kwargs : args
            passed to the matplotlib.bar; width is already used

        Returns
        ----------
        fig: matplotlib.figure.Figure object
            figure containing the output
        ax1: axes.AxesSubplot object
            the subplot
        '''

        fig = plt.figure()
        ax1 = fig.add_subplot(111)
        ax1 = plotbar(ax1, self.mustar[outputid*self._ndim:(outputid+1)*self._ndim], self._namelist, width = width,
                      addval = addval, sortit = True, *args, **kwargs)
        ax1.set_ylabel(r'$\mu*$',fontsize=20)
        ax1.yaxis.label.set_rotation('horizontal')
        ax1.yaxis.set_label_coords(-0.02, 1.)
        plt.draw()
        return fig, ax1

    def plotsigma(self, width = 0.5, addval = True, sortit = True, outputid = 0,
                *args, **kwargs):
        '''
        Plot a barchart of the given sigma
        
        sigma is a measure for the higher order effects (e.g. curvatures and 
        interactions). High sigma values typically occurs when for example 
        parameters are correlated, the model is non linear,... The sum of all
        these effects is sigma. For linear models without any correlation sigma
        should be approximately zero.        
        

        Parameters
        -----------
        width : float (0-1)
            width of the bars in the barchart
        addval : bool
            if True, the morris values are added to the graph
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
        fig = plt.figure()
        ax1 = fig.add_subplot(111)
        ax1 = plotbar(ax1, self.sigma[outputid*self._ndim:(outputid+1)*self._ndim], self._namelist, width = width,
                      addval = addval, sortit = True, *args, **kwargs)
        ax1.set_ylabel(r'$\sigma$',fontsize=20)
        ax1.yaxis.label.set_rotation('horizontal')
        ax1.yaxis.set_label_coords(-0.02, 1.)
        plt.draw()
        return fig, ax1

    def plotmustarsigma(self, outputid = 0, zoomperc = 0.05, loc = 2):
        '''
        Plot the mu* vs sigma chart to interpret the combined effect of both.
        

        Parameters
        -----------
        zoomperc : float (0-1)
            the percentage of the output range to show in the zoomplot,
            if 'none', no zoom plot is added
        loc : int
            matplotlib.pyplot.legend: location code (0-10)
        outputid : int
            the output to use whe multiple are compared; starts with 0

        Returns
        ---------
        fig : matplotlib.figure.Figure object
            figure containing the output
        ax1 : axes.AxesSubplot object
            the subplot
        txtobjects : list of textobjects
            enbales the ad hoc replacement of labels when overlapping

        Notes
        -------
        Visualization as proposed by [M2]_
        '''

        mustar2use = self.mustar[outputid*self._ndim:(outputid+1)*self._ndim]
        sigma2use = self.sigma[outputid*self._ndim:(outputid+1)*self._ndim]

        fig = plt.figure()
        ax1 = fig.add_subplot(111)
        axs, txtobjects = scatterwithtext(ax1, mustar2use, sigma2use,
                                          self._namelist, 'ks', markersize = 8)

        ax1.set_xlabel(r'$\mu^*$', fontsize=20)
        ax1.set_ylabel(r'$\sigma$', fontsize=20)
        ax1.grid()
        ax1.yaxis.grid(linestyle = '--', color = '0.75')
        ax1.xaxis.grid(linestyle = '--', color = '0.75')
        ax1.set_xlim((0.0, mustar2use.max()+mustar2use.max()*0.1))
        ax1.set_ylim((0.0, sigma2use.max()+sigma2use.max()*0.1))

        majloc1 = MaxNLocator(nbins=4, prune='lower')
        ax1.yaxis.set_major_locator(majloc1)
        majloc2 = MaxNLocator(nbins=4)
        ax1.xaxis.set_major_locator(majloc2)

        if zoomperc != 'none':
            #the zooming box size is ad hoc and can be improved
            axins = zoomed_inset_axes(ax1, np.floor(1./zoomperc/2.5),
                                      loc = loc)

            axins.plot(mustar2use, sigma2use, 'ks', markersize = 3)
            transOffset2 = offset_copy(axins.transData, fig=plt.gcf(),
                                       x = -0.05, y=0.10, units='inches')
            #plot in the subplot
            ct2=0
            txtobjects2=[]
            for x, y in zip(mustar2use, sigma2use):
                if x < mustar2use.max()*zoomperc and y < sigma2use.max()*zoomperc:
                    axins.plot((x,),(y,), 'ks', markersize = 3)
                    ls = axins.text(x, y, '%s' %self._namelist[ct2],
                                  transform=transOffset2, color='k')
                    txtobjects2.append(ls)
                ct2+=1

            #zoomplot with labels right
            axins.yaxis.set_ticks_position('right')
            #set the limits of the zoom plot
            axins.set_xlim((0.0, mustar2use.max()*zoomperc))
            axins.set_ylim((0.0, sigma2use.max()*zoomperc))
            #only minor number of ticks for cleaner overview
            majloc3 = MaxNLocator(nbins=3, prune='lower')
            axins.yaxis.set_major_locator(majloc3)
            majloc4 = MaxNLocator(nbins=3, prune='lower')
            axins.xaxis.set_major_locator(majloc4)
            #smaller size for the ticklabels (different is actually not needed)
            for tickx in axins.xaxis.get_major_ticks():
                tickx.label.set_fontsize(10)
            for label in axins.yaxis.get_majorticklabels():
                label.set_fontsize(10)
                label.set_rotation('vertical')

            #create the subarea-plot in main frame and connect
            mark_inset(ax1, axins, loc1=2, loc2=4, fc='none', ec='0.8')
            axins.grid()
            axins.yaxis.grid(linestyle = '--', color = '0.85')
            axins.xaxis.grid(linestyle = '--', color = '0.85')
        return fig, ax1, txtobjects

    def plot3partbar(self):
        '''
        gebruikt voor paper en hier nog in te brengen..
        '''
        pass


#####teststuff
#####################
#ai=[78, 12, 0.5, 2, 97, 33]
#ai=[50, 45, 52, 68, 51, 63]
#Xi = [(0.0,1.0,r'$X_1$'),(0.0,1.0,r'$X_2$'),(0.0,1.0,r'$X_3$'),(0.0,1.0,r'$X_4$'),
#      (0.0,1.0,r'$X_5$'),(0.0,1.0,r'$X_6$')]
#
#sm = MorrisScreening(Xi,ModelType = 'testmodel')
#OptMatrix, OptOutVec = sm.Optimized_Groups(nbaseruns=100,
#                                           intervals = 4, noptimized=4, Delta = 0.4)
#sm.Optimized_diagnostic(width=0.15)
#sm.runTestModel(ai)

##run the model
#output = np.zeros((sm.OptOutMatrix.shape[0],1))
#for i in range(sm.OptOutMatrix.shape[0]):
#     output[i,:] = analgfunc(ai,sm.OptOutMatrix[i,:])
#output2 = output*2
#
##two outputs
#sm.Morris_Measure_Groups(np.hstack((output,np.sqrt(output)*2)))

#fig1,ax1 =sm.plotmu(ec='grey',fc='grey')
#sm.plotmustar(outputid = 1,ec='grey',fc='grey')
##sm.plotsigma(ec='grey',fc='grey')
#fig, axs1, txtobjects = sm.plotmustarsigma(zoomperc = 0.05, outputid = 1, loc = 2)
##results in txt file
#sm.txtresults(name='MorrisTestOut.txt')
##results in tex-table
#sm.latexresults(name='MorrisTestOut.tex')

#plt.figure()
#plt.bar(np.linspace(0,6,6),sm.mustar)
#plt.figure()
#plt.bar(np.linspace(0,6,6),sm.mu)

#def plotbar(Outmatrix,factornames=[]):
#    ind = np.arange(Outmatrix.shape[0])
#
#    fig = plt.figure()
#    ax = fig.add_subplot(111)
#    width = 0.35
#    ax.bar(ind, Outmatrix[:,0],width)
#
#
#    ax.set_ylabel(r'$\mu$*')
#    ax.set_xlabel(r'Factors')
#    ax.set_xticks(ind+width/2)
#    if len(factornames)>0:
#        ax.set_xticklabels( factornames )

##2##
#Xi = [(0.0,6.0,r'$X_1$'),(0.2,0.8,r'$X_2$'),(0.0,1.0,r'$X_3$'),(0.0,1.0,r'$X_4$'),
#      (1.0,2.0,r'$X_5$'),(2.0,10.0,r'$X_6$'),(0.0,1.0,r'$X_7$'),(0.0,1.0,r'$X_8$')]
#sm = MorrisScreening(Xi)
#OptMatrix, OptOutVec = sm.Optimized_Groups(nbaseruns=1000,
#                                           intervals = 4, noptimized=20)
#sm.Optimized_diagnostic(width=0.15)

#OM TE LOPEN:
#pre
#ParMatrix, OptOutVec=Optimized_Groups(NumFact,LB,UB,N=1000,p=4,r=Nr,GroupMat=np.array([]),Diagnostic=0)
