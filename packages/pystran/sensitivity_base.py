# -*- coding: utf-8 -*-
"""
@author: Stijn Van Hoey
Development supported by Flemish Institute for Technological Research (VITO)
"""
import os

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, MaxNLocator

from .parameter import ModPar
from .errorhandling import PystanInputError, PystanSequenceError

class SensitivityAnalysis(object):
    """
    Base class for the Sensitivity Analysis

    Parameters
    ----------
    parsin : list
        ModPar class instances in list or list of (min, max,'name')-tuples
    """

    @staticmethod
    def print_methods():
        """
        Overview of the used methods
        """
        print('''1. Sobol Variance Based:
                    first and total order''')
        print('''2. Regional Sensitivity Analysis:
                    also called Monte Carlo Filtering''')
        print('''3. Morris Screening Method:
                    with pre-optimized defined trajects and group option''')
        print('''4. Sampled-OAT:
                    Latin HYpercube or Sobol sampling with OAT sensitivity''')
        print('''5. Standardized Regression Coefficients:
                    Latin HYpercube or Sobol sampling with linear regression''')
        print('''6. DYNamic Identifiability Analysis:
                    Latin HYpercube or Sobol sampling with time-sliced based
                    evaluation''')

    def __init__(self, parsin):
        '''
        Check if all uniform distribution => ! if all -> sobol sampling
        is possible, else, only uniform and normal distribution are supported
        for using the sobol sampling... 
        '''

        if  isinstance(parsin, dict): #bridge with pyFUSE!
            dictlist = []
            for value in parsin.itervalues():
                dictlist.append(value)
            parsin = dictlist
            print(parsin)

        #control for other
        self._parsin = parsin[:]
        #dictionary linking ID and name, since dict instance has no
        #intrinsic sequence
        self._parmap = {}
        for i in range(len(parsin)):
            if isinstance(parsin[i], ModPar):
                cname = parsin[i].name
                if cname in self._parmap.values():
                    raise ValueError("Duplicate parameter name %s"%cname)
                self.pars = parsin[:]
                self._parsin[i] = (parsin[i].min, parsin[i].max, cname)
                self._parmap[i] = cname

            elif isinstance(parsin[i], tuple):
                if parsin[i][0] > parsin[i][1]:
                    raise Exception('Min value larger than max value')

                if (not isinstance(parsin[i][0], float) and
                                isinstance(parsin[i][1], float)):
                    raise Exception('Min and Max value need to be float')

                if not isinstance(parsin[i][2], str):
                    raise Exception('Name of par needs to be string')

                if parsin[i][2] in self._parmap.values():
                    raise ValueError("Duplicate parameter name %s"%parsin[i][2])
                self._parmap[i] = parsin[i][2]

                #create modpar instance of the tuple
                self.pars = []
                for par in parsin:
                    self.pars.append(ModPar(par[2], par[0], par[1],
                                            (par[0] + par[1])/2.,
                                            'randomUniform'))
            else:
                raise PystanInputError("The inputtype for parameters "
                                        "not correct,"
                                        "choose ModPar instance or "
                                        "list of (min,max)-tuples")

        self._ndim = len(parsin)

        self._namelist = []
        for i in range(self._ndim):
            self._namelist.append(self._parmap[i])

        self.parset2run = None
        self.output2evaluate = None
        self._methodname = None

    def write_parameter_sets(self, filename = 'inputparameterfile', *args,
                             **kwargs):
        """
        Parameterinputfile for external model, parameters in the columns files
        and every line the input parameters

        Parameters
        -----------
        filename : str
            name of the textfile to save
        *args, **kwargs : args
            arguments passed to the numpy savetext-function
        """
        try:
            np.savetxt(filename, self.parset2run, *args, **kwargs)
            print('file saved in directory %s' % os.getcwd())
        except PystanSequenceError:
            print('Parameter sets to run model with not yet setup.')

    def getcurrentmethod(self):
        """Check if method is defined and return name"""
        if self._methodname == None:
            print("No method defined.")
        else:
            return self._methodname

    def read_modeloutput_runs(self, filename, *args, **kwargs):
        """
        Read model outputs


        Format is: every output of the ithe MC on ith line

        output2evaluate can also be made on a other way

        Parameters
        -----------
        filename : str
            name of the textfile to load
        *args, **kwargs : args
            arguments passed to the numpy loadtext-function

        """
        self.output2evaluate = np.loadtxt(filename, *args, **kwargs)


    def run_pyfuse(self, pyfuse):
        """
        Run the Model if it's pyFUSE;
        The link with an output variable is not explicitly included and can be
        applied by the ObjFunc intance of user-defined. All outputs are available
        in the hdf5 to work with.

        Parameters
        ------------
        pyfuse : pyfuse model instance
            model created by pyfuse; make sure the hdf5-linked file is
            ready to write to
        """
#        get pyfuse model instance
#        if not isinstance(pyfuse, pyfuse_Model):
#            raise Exception('Ass a pyfuse model instance to perform  \
#                            sensitivity')

        try:
            self.pars
        except:
            raise PystanInputError("Use the modpar class when working "
                                    "with the pyfuse model environment")

        #run model, all outputs saved in hdf5
        for run in range(self.parset2run.shape[0]):
            #create pardict for pyfuse input from self._parmap
            par2pyfuse = {}
            for i in range(self._ndim):
                par2pyfuse[self._parmap[i]] = self.parset2run[run, i]
            #run the pyfuse model with new pars
            print(self._methodname, 'Run'+str(run))
            print('Simulation %d of %d is \
                    running...' % (run + 1, self.parset2run.shape[0]))
            pyfuse.run(new_pars = par2pyfuse,
                       run_id = self._methodname + 'Run' + str(run))

        print('All simulations are performed and saved in hdf5. You can now \
        transform the output data to an evaluation criterion.')

    def scattercheck(self, parsamples, output, ncols=3, *args, **kwargs):
        '''
        Plot the parvalues against one outputs of the model to evaluate the
        linearity of the relationship between the parameter and the output
        and to get a general idea of the model behavior towards this output.

        Is a useful and practical visualisation for all methods, but
        essential when useing the regression based method to check for
        linearity/monotonicity.

        Parameters
        -----------
        parsamples : ndarray
            array with the sampled parameter values
        output : 1D ndarray
            array with the output values for these parameter combinations
        ncols :  int
            number of columns to put subplots in
        *args, **kwargs :
            scatter options given tot the different scatter-subplots
        '''
        #control if output only has one col
        if output.size != output.shape[0]:
            raise Exception('Choose a single output to plot')

        #define number of rows
        numpars = parsamples.shape[1]
        nrows = np.divide(numpars, ncols)
        if np.remainder(numpars, ncols)>0:
            nrows += 1
        #prepare plots
        fig, axes = plt.subplots(nrows=nrows,
                                 ncols=ncols, figsize=(12,12))
        fig.subplots_adjust(hspace=0.25, wspace=0.02)

        i = 0
        for ax in axes.flat:
            #x0,x1 = ax.get_xlim()
            #y0,y1 = ax.get_ylim()
            #ax.set_aspect((x1-x0)/(y1-y0))
            if i < numpars:
                ax.scatter(parsamples[:, i], output, *args, **kwargs)
                ax.set_title(self._namelist[i])
                #adjust ticks
                majorlocator = FixedLocator([self._parsin[i][0],
                                             self._parsin[i][1]])
                ax.xaxis.set_major_locator(majorlocator)

                if ax.is_first_col():
                    majloc1 = MaxNLocator(nbins = 4)
                    ax.yaxis.set_major_locator(majloc1)
                else:
                    plt.setp(ax.get_yticklabels(), visible = False)

            else:
                ax.set_axis_off()
            i += 1

        return fig, axes

