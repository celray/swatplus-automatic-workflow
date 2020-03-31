# -*- coding: utf-8 -*-
"""
@author: VHOEYS
development supported by Flemish Institute for Technological Research (VITO)
"""

import itertools
import os

import numpy as np
#import scipy as sp
from scipy import stats

import pylab as p
import matplotlib
import matplotlib.mlab as mlab
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import matplotlib.patches as patches

from matplotlib.patches import Rectangle, Polygon
from matplotlib.colors import Normalize
from matplotlib.transforms import offset_copy

from matplotlib.ticker import MaxNLocator, LinearLocator, NullLocator
from mpl_toolkits.axes_grid1 import make_axes_locatable

#p.rc('mathtext', default='regular')

def _logplot(flowserie, ax = None):
    """
    """
    if ax:
        flowserie.plot(logy=True, ax = ax)
    else:
        fig, ax = plt.subplots()
        flowserie.plot(logy=True, ax = ax)
    return ax


def _slopes_on_plot(ax):
    """
    """
    xvalues = ax.get_xticks()
    ylim = ax.get_ybound()
    xlim = ax.get_xbound()

    #startpunt
    ax.get_xaxis().get_major_locator()

    return ax

###############################
## Model output evaluations
###############################

def Autocorr(axs, data, maxlags = 25, signlevel=0.05):
    '''
    Autocorrelation plot with critical line (for 5%), calculated as
    +/- N(0,1)/np.sqrt(N).

    At a significance level of 0.05, this means that only 5% of
    the calculated autocorrelations may be larger than (=1.96/sqrt(N)).
    When a higher percentage of the calculated autocorrelations exceed
    the limit, the residuals are considered to be not independent [1].

    Parameters
    -----------
    axs: axes.AxesSubplot object
        an subplot instance where the graph will be located,
        this supports the use of different subplots
    data: array
        data to represent, mostly residuals
    maxlags: int
        default = 25, number of lags to consider in the analysis
    signlevel: float [0.0 - 0.5]
        significance level to check the dependence of the array, when 0.05,
        the level is set to 0.025 and 0.975

    Returns
    --------
    axs

    Examples
    ---------
    >>> x = 2 *np.random.random(100) - 1
    >>> fig = plt.figure(figsize=(15,6))
    >>> axs = fig.add_subplot(111)
    >>> AutoCorr(axs, x)

    References
    -----------
    [1] Dochain, D., and P. A. Vanrolleghem, 2001, Dynamical modelling and
    estimation in wastewater treatment processes., IWA Publishing.

    '''
    acorout = axs.acorr(data, usevlines=True, color='0.2', normed=True,
              maxlags = maxlags, linewidth=4)

#    axs.grid(True,'major', color='0.75', linestyle='dotted',
#                   linewidth = 0.8)

    lheigth = stats.norm.ppf(1.-signlevel/2)/np.sqrt(data.size)
    #line above zero
    axs.axhline(lheigth, color='0.3', lw=1.5, linestyle = '--')
    #line below zero
    if np.any(acorout[1].min()<0.0):
        axs.axhline(-lheigth, color='0.3', lw=1.5, linestyle = '--')
        axs.set_yticks([-1,-0.5, 0, 0.5, 1])
    else:
        axs.set_yticks([0, 0.5, 1])

    axs.set_xlim(0,maxlags)
    axs.grid(b='off')

    return axs

def definedec(nummin,nummax):
    '''
    Help function to define the number of shown decimals
    '''
    diff = nummax - nummin
    predec = len(str(diff).split('.')[0])
    if predec > 1:
        dec = -(predec-1)
    else:
        if str(diff)[0] != '0':
            dec = 1
        else:
            cnt = 1
            for char in str(diff).split('.')[1]:
                if char == '0':
                    cnt+=1
            dec = cnt
    return dec


def scatterplot_matrix(data1, plottext=None, data2 = False, limin = False,
                             limax = False, diffstyle1 = None,
                             diffstyle2 = None, plothist = False,
                             mstyles=['o','v','^','<','>','1\
                             ','2','3','4','s','x','+',',','_','|'],
                             *args, **kwargs):
    """
    Plots a scatterplot matrix of subplots.  Each row of "data" is plotted
    against other rows, resulting in a nrows by nrows grid of subplots.

    Parameters
    -----------
    data1: ndarray
        numvars rows and numdata columns datapoints to compare,
        when only this dataset is given, the dat is plotted twice in the
        graph
    data2: ndarray
        optional second dataset to put in the upper-part, whereas the
        first dataset is putted in the lower part
    plottext: None | list
        list of strings woth the text to put for the variables, when no
        histograms are needed
    limin: False | list
        List of user defined minimal values for the different
        variables. When False, the min/max values are calculated
    limax: False | list
        List of user defined maximal values for the different
        variables. When False, the min/max values are calculated
    diffstyle1: None |list
        when every variable contains sub-groups, the diffstyle list gives
        the number of elements to group the elements, different groups are
        given different color/style caracteristics automatically
    diffstyle2: None |list
        analgue to diffstyle1
    mstyles: list
        list of user defined symbols to use for different groups
    plothist: bool
        histogram is plotted in the middle of the data1 when True
    *args, **kwargs: arg
        arguments passed to the scatter method

    Returns
    ---------
    fig: matplotlib.figure.Figure object
        figure containing the output
    axes: array of matplotlib.axes.AxesSubplot object
        enabled post-processing of the ax-elements

    Examples
    ---------
    >>> np.random.seed(1977)
    >>> numvars, numdata = 4, 1111
    >>> data1 = 5 * np.random.normal(loc=3.,scale=2.0,size=(numvars, numdata))
    >>> data2 = 50 * np.random.random((numvars, numdata))
    >>> fig,axes = scatterplot_matrix(data1, data2 = False,
            linestyle='none', marker='o', color='black', mfc='none',
            diffstyle1=[555,556], plothist = True, plottext=['A','B','C','D'])
    >>> ax2add = axes[0,0]
    >>> ax2add.text(0.05,0.8,r'$SSE_{\alpha}$',transform = ax2add.transAxes,
                    fontsize=20)
    >>>
    >>> fig,axes = scatterplot_matrix(data1, data2 = data2,
            linestyle='none', marker='o', color='black', mfc='none',
            diffstyle1=False, plothist = False, plottext=['A','B','C','D'])

    Notes
    ------
    typically used for comparing objective functions outputs, or parameter
    distributions

    When using two datasets, only useful ticks when the datalimits
    are more or less the same, since otherwise the plot won't show both nicely
    """

    databoth = False
    if isinstance(data2, np.ndarray):
        databoth = True

    #TODO: control for dtypes inputs

    numvars, numdata = data1.shape
    fig, axes = plt.subplots(nrows=numvars, ncols=numvars, figsize=(40,40))
    fig.subplots_adjust(hspace=0.05, wspace=0.03)

    for ax in axes.flat:
        # Hide all ticks and labels
        ax.xaxis.set_visible(False)
        ax.yaxis.set_visible(False)

        # Set up ticks only on one side for the "edge" subplots...
        if ax.is_first_col():
            ax.yaxis.set_ticks_position('left')
        if ax.is_last_col():
            ax.yaxis.set_ticks_position('right')
        if ax.is_first_row():
            ax.xaxis.set_ticks_position('top')
        if ax.is_last_row():
            ax.xaxis.set_ticks_position('bottom')
        #adjust the ticker lengths and position
        ax.tick_params(direction = 'out', pad=8, length = 5.,
                       color = 'black', which = 'major')
        ax.tick_params(length = 3., which = 'minor')

    #calc datalimits
    if not isinstance(limin, list) or not isinstance(limax,list):
        limin=[]
        limax=[]
        for i in range(data1.shape[0]):
            if databoth == True:
                dec1 = definedec(np.min(data1[i]),np.max(data1[i]))
                dec2 = definedec(np.min(data2[i]),np.max(data2[i]))
                limin1=np.around(np.min(data1[i]),decimals = dec1)
                limax1=np.around(np.max(data1[i]),decimals = dec1)
                limin2=np.around(np.min(data2[i]),decimals = dec2)
                limax2=np.around(np.max(data2[i]),decimals = dec2)
                print(dec2)
                limin.append(min(limin1,limin2))
                limax.append(max(limax1,limax2))

                if np.abs(limin1 - limin2) > min(limin1,limin2):
                    print(np.abs(limin1 - limin2), min(limin1,limin2),'min')
                    print('potentially the datalimits of two datasets are \
                    too different for presenting results')
                if np.abs(limax1 - limax2) > min(limax1,limax2):
                    print(np.abs(limax1 - limax2), min(limax1,limax2),'max')
                    print('potentially the datalimits of two datasets are\
                    too different for acceptabel results')
            else:
                dec1 = definedec(np.min(data1[i]),np.max(data1[i]))
                limin.append(np.around(np.min(data1[i]),decimals = dec1))
                limax.append(np.around(np.max(data1[i]),decimals = dec1))
        print('used limits are', limin,'and', limax)
    else:
        print('used limits are', limin,'and', limax)

    # Plot the data.
    for i, j in zip(*np.triu_indices_from(axes, k=1)):
#        for x, y in [(i,j), (j,i)]:
        for x, y in [(j,i)]: #low
            if diffstyle1:
                cls=np.linspace(0.0,0.5,len(diffstyle1))
                dfc=np.cumsum(np.array(diffstyle1))
                dfc=np.insert(dfc,0,0)
                if dfc[-1] != data1.shape[1]:
                    raise Exception('sum of element in each subarray is\
                    not matching the total data size')
                if len(diffstyle1)>15:
                    raise Exception('Not more than 15 markers provided')
                for ig in range(len(diffstyle1)):
                    axes[x,y].plot(data1[y][dfc[ig]:dfc[ig+1]],
                                    data1[x][dfc[ig]:dfc[ig+1]],
                                    marker=mstyles[ig], markersize = 6.,
                                    linestyle='none', markerfacecolor='none', markeredgewidth=0.7,#color=str(cls[ig]),
                                    markeredgecolor=str(cls[ig]))
                axes[x,y].set_ylim(limin[x],limax[x])
                axes[x,y].set_xlim(limin[y],limax[y])

            else:
                axes[x,y].plot(data1[y], data1[x], *args, **kwargs)
                axes[x,y].set_ylim(limin[x],limax[x])
                axes[x,y].set_xlim(limin[y],limax[y])


        if databoth == True: #plot data2
            for x, y in [(i,j)]:
                if diffstyle2:
                    cls=np.linspace(0.0,0.5,len(diffstyle2))
                    dfc=np.cumsum(np.array(diffstyle2))
                    dfc=np.insert(dfc,0,0)
                    if dfc[-1] != data2.shape[1]:
                        raise Exception('sum of element in each subarray\
                        is not matching the total data size')
                    if len(diffstyle1)>15:
                        raise Exception('Not more than 15 markers provided')
                    for ig in range(len(diffstyle2)):
                        axes[x,y].plot(data2[y][dfc[ig]:dfc[ig+1]],
                                        data2[x][dfc[ig]:dfc[ig+1]],
                                        marker=mstyles[ig], markersize = 6,
                                        linestyle='none', markerfacecolor='none', markeredgewidth=0.7,
                                        markeredgecolor=str(cls[ig]))
                    axes[x,y].set_ylim(limin[x],limax[x])
                    axes[x,y].set_xlim(limin[y],limax[y])
                else:
                    axes[x,y].plot(data2[y], data2[x], *args, **kwargs)
                    axes[x,y].set_ylim(limin[x],limax[x])
                    axes[x,y].set_xlim(limin[y],limax[y])

        else: #plot the data1 again
            for x, y in [(i,j)]:
                if diffstyle1:
                    cls=np.linspace(0.0,0.5,len(diffstyle1))
                    dfc=np.cumsum(np.array(diffstyle1))
                    dfc=np.insert(dfc,0,0)
                    if dfc[-1] != data1.shape[1]:
                        raise Exception('sum of element in each subarray\
                        is not matching the total data size')
                    if len(diffstyle1)>15:
                        raise Exception('Not more than 15 markers provided')
                    for ig in range(len(diffstyle1)):
                        axes[x,y].plot(data1[y][dfc[ig]:dfc[ig+1]],
                                        data1[x][dfc[ig]:dfc[ig+1]],
                                        marker=mstyles[ig], markersize = 6,
                                        linestyle='none', markerfacecolor='none', markeredgewidth=0.7,
                                        markeredgecolor=str(cls[ig]))
                    axes[x,y].set_ylim(limin[x],limax[x])
                    axes[x,y].set_xlim(limin[y],limax[y])
                else:
                    axes[x,y].plot(data1[y], data1[x], *args, **kwargs)
                    axes[x,y].set_ylim(limin[x],limax[x])
                    axes[x,y].set_xlim(limin[y],limax[y])


    #PLOT histograms  and variable names
    #    for i, label in enumerate(plottext):
    for i in range(numvars):
        if not plothist and plottext:
            label = plottext[i]
            axes[i,i].annotate(label, (0.5, 0.5), xycoords='axes fraction',
                    ha='center', va='center')
        else: #plot histogram in center
            if diffstyle1:
                dfc=np.cumsum(np.array(diffstyle1))
                dfc=np.insert(dfc,0,0)
                if dfc[-1] != data1.shape[1]:
                    raise Exception('sum of element in each subarray is\
                    not matching the total data size')
                cls=np.linspace(0.0,0.5,len(diffstyle1))

                for ig in range(len(diffstyle1)):
                    axes[i,i].hist(data1[i][dfc[ig]:dfc[ig+1]],
                                    facecolor = 'none', bins=20,
                                    edgecolor=str(cls[ig]), linewidth = 1.5)
                axes[i,i].set_xlim(limin[i],limax[i])
                print(limin[i],limax[i])
            else:
                axes[i,i].hist(data1[i],bins=20,color='k')
                axes[i,i].set_xlim(limin[i],limax[i])
                print(limin[i],limax[i])

    if plothist:
        print('plottext is not added')

    # Turn on the proper x or y axes ticks.
    for i, j in zip(range(numvars), itertools.cycle((-1, 0))):
        axes[j,i].xaxis.set_visible(True)
        axes[i,j].yaxis.set_visible(True)

        majorLocator = LinearLocator(3)
        axes[j,i].xaxis.set_major_locator(majorLocator)
        axes[i,j].yaxis.set_major_locator(majorLocator)

        minorLocator  = LinearLocator(11)
        axes[j,i].xaxis.set_minor_locator(minorLocator)
        axes[i,j].yaxis.set_minor_locator(minorLocator)

    #When uneven, some changes needed to properly put the ticks and tickslabels
    #since the ticks next to the histogram need to take the others y-scale
    #solved by adding a twinx taking over the last limits

    if not numvars%2==0:# and plothist==False:
        if plothist == False:
            #create dummy info when no histogram is added
            axes[numvars-1,numvars-1].set_xlim(limin[numvars-1],
                                        limax[numvars-1])
            axes[numvars-1,numvars-1].set_ylim(limin[numvars-1],
                                        limax[numvars-1])

        axextra = axes[numvars-1,numvars-1].twinx()
        axextra.set_ylim(limin[numvars-1],limax[numvars-1])
        axextra.yaxis.set_minor_locator(minorLocator)
        axextra.yaxis.set_major_locator(majorLocator)
        axes[numvars-1,numvars-1].yaxis.set_ticks([])
        axes[numvars-1,numvars-1].yaxis.set_minor_locator(NullLocator())

        axes[numvars-1,numvars-1].xaxis.set_major_locator(majorLocator)
        axes[numvars-1,numvars-1].xaxis.set_minor_locator(minorLocator)
    return fig, axes

def Spread_diagram(axs,obs, mod, infobox = True, *args, **kwargs):
    '''
    Plot a scatter plot comparing the modelled and observed datasets in a
    scatter plot.

    Parameters
    -----------
    axs : axes.AxesSubplot object
        an subplot instance where the graph will be located,
        this supports the use of different subplots
    obs : ndarray
        1D array of the observed data
    mod : ndarray
        1D array of the modelled output
    infobox : bool True|False
        defines if a infobox with the regression info is added or not
    *args, **kwargs : args
        argument passed to the matplotlib scatter command

    Returns
    --------
    axs

    Examples
    ---------
    >>> obs = 20*np.random.random(200)
    >>> mod = 0.8*obs + 2 * np.random.random(200) -1
    >>> fig = plt.figure()
    >>> axs = fig.add_subplot(111)
    >>> axs = Spread_diagram(axs, obs, mod, infobox = True,
                             marker='o', facecolor='none',
                             edgecolor = 'k')
    >>> axs.set_xlabel(r'observed ($m^3 s^{-1}$)')
    >>> axs.set_ylabel(r'modelled ($m^3 s^{-1}$)')

    '''
    p.rc('mathtext', default='regular')

    axs.scatter(obs,mod, *args, **kwargs)
    axs.set_aspect('equal')

    getmax = max(obs.max(),mod.max())*1.1
    getmin = min(obs.min(),mod.min())*0.9
    axs.plot([getmin,getmax],[getmin,getmax],'k--', linewidth = 0.5)

    slope, intercept, r_value, p_value, std_err = stats.linregress(obs, mod)
#    m,b = p.polyfit(obs, mod, 1)
    forplot = np.arange(getmin,getmax,0.01)
    axs.plot(forplot, slope*forplot+intercept, '-', color='grey',
             linewidth = 0.5)
    axs.set_xlim(left = getmin, right=getmax)
    axs.set_ylim(bottom = getmin, top=getmax)

    rmse = np.sqrt((np.sum((obs-mod)**2))/obs.size)
    rrmse = np.sqrt((np.sum(((obs-mod)/obs)**2))/obs.size)


    #for infobox
    if infobox == True:
        patch=Rectangle((0., 0.65), .35, 0.35, facecolor = 'white',
                        edgecolor='k', transform=axs.transAxes)
        axs.add_patch(patch)
        axs.set_axisbelow(True)

        textinfo = ({'transform' : axs.transAxes, 'verticalalignment':'center',
                    'horizontalalignment':'left', 'fontsize':12})

        axs.text(0.05, 0.95, r'$\bar{x}\ $', textinfo)
        axs.text(0.05, 0.90, r'$\bar{y}\ $', textinfo)
        axs.text(0.05, 0.85, r'$rico\ $', textinfo)
        axs.text(0.05, 0.8, r'$intc.\ $', textinfo)
        axs.text(0.05, 0.75, r'$R^2\ $', textinfo)
        axs.text(0.05, 0.70, r'$RMSE\ $', textinfo)

        axs.text(0.2, 0.95, r': %.2f'%obs.mean(), textinfo)
        axs.text(0.2, 0.90, r': %.2f'%mod.mean(), textinfo)
        axs.text(0.2, 0.85, r': %.2f'%slope, textinfo)
        axs.text(0.2, 0.8, r': %.2f'%intercept, textinfo)
#        axs.text(0.2, 0.75, r': %.2f'%r_value, textinfo)
        axs.text(0.2, 0.75, r': %.2f'%rrmse, textinfo)
        axs.text(0.2, 0.70, r': %.2f'%rmse, textinfo)

    return axs

###############################
## Methods with outputs of parameter posterior distributions
###############################

def TornadoComparePar(axs, parval1, parval2, parnames, plotfreq = True,
                      plotminmax = True, plotinfotext = True,
                      *args,  **kwargs):
    '''
    Compare 2 parameter distributions in a Tornado-style plot

    Parameters
    -------------
    axs : axes.AxesSubplot object
        an subplot instance where the graph will be located,
        this supports the use of different subplots
    parval1 : array
        values of the first parameter
    parval2 : array
        values of the second parameter
    parnames : list of strings
        parameter names to show with graph
    plotfreq : bool, True|False
        frequency numbers plotted on top of the bins or not
        (this is less relevant when using density plots)
    plotminmax : bool, True|False
        indicate the min and max values of the parameters
    plotinfotext : str
        if False, nothing is shown, else a text with info is puted on top
    *args, **kwargs :
        These argument are directed to the numpy.histogram() function
        eg. density, number of bins,...

    Returns
    --------
    axes.AxesSubplot object

    Notes
    -------
    Plotting the frequencies on y-axis is not supported, since the lower graph
    would get negative frequencies

    Examples
    ---------

    >>> nMC = 1000
    >>> parval1 = np.random.gamma(5.5,size=nMC)
    >>> parval2 = np.random.gamma(8.0,size=nMC)
    >>> parnames = ['par1','par2']
    >>> fig = plt.figure(figsize=(15,6))
    >>> axs = plt.subplot(111, axisbelow=True)
    >>> axs = TornadoComparePar(axs,parval1,parval2,parnames,plotfreq =True,
                                plotminmax=True,
                                plotinfotext = 'Posterior distributions',
                                bins=25,density=False)
    '''

    hist, bin_edges = np.histogram(parval1, *args, **kwargs)
    hist2, bin_edges2 = np.histogram(parval2, *args, **kwargs)

    parmin1 = parval1.min()
    parmax1 = parval1.max()
    parmin2 = parval2.min()
    parmax2 = parval2.max()

    bwidth = bin_edges[1]-bin_edges[0]
    axs.bar(bin_edges[:-1], hist, width=(bin_edges[1]-bin_edges[0])*0.95,
            facecolor='0.3', edgecolor='white')

    if plotfreq == True:
        for i in range(hist.size):
            if hist[i] > 0.0:
                plt.text(bin_edges[i]+bwidth/2, hist[i]+0.025*hist2.max(),
                         "%.1f"%hist[i], color='0.3', size=8,
                         horizontalalignment='center',
                         verticalalignment='bottom')

    bwidth2 = bin_edges2[1]-bin_edges2[0]
    axs.bar(bin_edges2[:-1], -hist2, width=(bin_edges2[1]-bin_edges2[0])*0.95,
            facecolor='0.5', edgecolor='white')

    if plotfreq == True:
        for i in range(hist2.size):
            if hist2[i] > 0.0:
                plt.text(bin_edges2[i]+bwidth2/2, -hist2[i]-0.025*hist2.max(),
                         "%.1f"%hist2[i], color='0.5', size=8,
                         horizontalalignment='center',
                         verticalalignment='top')

    if plotminmax == True:
        #Plot the place where the parameter minimum and maximum
        #values are located
        plt.text(parmin1, hist.max()/2., 'min', color='0.3', size=12,
                         horizontalalignment='center',
                         verticalalignment='bottom')

        xspot, yspot = np.array([[parmin1, parmin1],
                        [0.0, hist.max()*0.9/2.]])

        axs.add_line(mlines.Line2D(xspot, yspot, linestyle='--',
                            linewidth=1., color='0.3'))

        plt.text(parmax1, hist.max()/2., 'max', color='0.3', size=12,
                         horizontalalignment='center',
                         verticalalignment='bottom')

        xspot, yspot = np.array([[parmax1, parmax1],
                        [0.0, hist.max()*0.9/2.]])
        axs.add_line(mlines.Line2D(xspot, yspot, linestyle='--',
                              linewidth=1. , color='0.3'))

        plt.text(parmin2, -hist2.max()/2., 'min', color='0.5', size=12,
                         horizontalalignment='center',
                         verticalalignment='top')

        xspot, yspot = np.array([[parmin2, parmin2],
                         [0.0, -hist2.max()*0.9/2.]])

        axs.add_line(mlines.Line2D(xspot, yspot, linestyle='--',
                              linewidth=1. , color='0.5'))

        plt.text(parmax2, -hist2.max()/2., 'max', color='0.5', size=12,
                         horizontalalignment='center',
                         verticalalignment='top')

        xspot, yspot = np.array([[parmax2, parmax2],
                        [0.0,-hist2.max()*0.9/2.]])

        axs.add_line(mlines.Line2D(xspot, yspot, linestyle='--',
                            linewidth=1., color='0.5'))

    axs.set_ylim([-hist2.max(), +hist.max()])
    axs.set_xticks([])
    axs.set_yticks([+hist.max()/2., -hist2.max()/2.])
    axs.set_yticklabels([parnames[0], parnames[1]], size=20)
    labels = axs.get_yticklabels()
    labels[0].set_rotation(90)
    labels[0].set_color('0.3')
    labels[1].set_rotation(90)
    labels[1].set_color('0.5')

    axs.spines['top'].set_color('none')
#    axs.spines['left'].set_color('none')
    axs.spines['right'].set_color('none')
    axs.spines['bottom'].set_color('none')
    axs.yaxis.set_ticks_position('left')

    if plotinfotext:
        axs.text(bin_edges[-1]*0.7, hist.max(), plotinfotext,
                 color='black', size=24,
                 horizontalalignment='left',
                 verticalalignment='top')

#        Change this to add extra text information
#        axs.text(bin_edges[-1]*0.7,hist.max()*0.8,
#                 "Comparison of two structures", color='.4', size=14,
#                 horizontalalignment='left', verticalalignment='top')

    return axs

def Scatter_hist(data1, data2, data1b=False, data2b=False, binwidth = 0.5,
                 cleanstyle = False, *args,  **kwargs):
    '''
    Three-parts plot with the two parameter sitdirbutions plotted on the sides

    Parameters
    -----------
    data1: ndarray
        dataset 1 for x-axis
    data2: ndarray
        dataset 2 for y-axis
    data1b: ndarray
        dataset to plot along the data 1 set
    data2b: ndarray
        dataset to plot along the data 2 set
    binwidth: float
        defines the width of the bins relative to the data used
    cleanstyle: bool True|False
        if True, a more minimalistic version of the plot is given
    *args,  **kwargs: args
        arguments given toi the scatter plot
        example: s=15, marker='o', edgecolors= 'k',facecolor = 'white'

    Returns
    ---------
    fig: matplotlib.figure.Figure object
        the resulting figure
    axScatter: matplotlib.axes.AxesSubplot object
        the scatter plot with the datapoints, can be used to add labels or
        change the current ticks settings
    axHistx: matplotlib.axes.AxesSubplot object
        the x-axis histogram
    axHisty: matplotlib.axes.AxesSubplot object
        the y-axis histogram

    Examples
    ----------
    >>> nMC = 1000
    >>> parval1 = np.random.gamma(5.5,size=nMC)
    >>> parval2 = np.random.gamma(8.0,size=nMC)
    >>> parnames = ['par1','par2']
    >>> fig,axScatter,axHistx,axHisty = Scatter_hist(parval1,parval2,
                                                 cleanstyle = True, s=48,
                                                 marker='o', edgecolors= 'k',
                                                 facecolor = 'none',alpha=0.7)
    >>> parval1b = np.random.uniform(low=0.0, high=30.0,size=nMC)
    >>> parval2b = np.random.uniform(low=0.0, high=30.0,size=nMC)
    >>> fig,axScatter,axHistx,axHisty = Scatter_hist(parval1,parval2,parval1b,
                                                 parval2b, cleanstyle = True,
                                                 s=48, marker='o',
                                                 edgecolors= 'k',
                                                 facecolor = 'none',
                                                 alpha=0.7)

    Notes
    ------
    Typical application is to check the dependency of two posterior
    parameter distrbutions, eventually compared with their selected posteriors

    If a second dataset is added to compare, the style options of the scatter
    plot are fixed and the *args, **kwargs have no influence

    '''
    if not isinstance(data1, np.ndarray):
        raise Exception('dataset 1 need to be numpy ndarray')
    if not isinstance(data2, np.ndarray):
        raise Exception('dataset 2 need to be numpy ndarray')

    if isinstance(data1b, np.ndarray):
        if not isinstance(data2b, np.ndarray):
            raise Exception('Always combine the data of both')
    if isinstance(data2b, np.ndarray):
        if not isinstance(data1b, np.ndarray):
            raise Exception('Always combine the data of both')

    fig = plt.figure(figsize=(10,10))
    axScatter = plt.subplot(111)
    divider = make_axes_locatable(axScatter)
    #axScatter.set_aspect('equal')
    axScatter.set_autoscale_on(True)

    # create a new axes with  above the axScatter
    axHistx = divider.new_vertical(1.5, pad=0.0001, sharex=axScatter)

    # create a new axes on the right side of the
    # axScatter
    axHisty = divider.new_horizontal(1.5, pad=0.0001, sharey=axScatter)

    fig.add_axes(axHistx)
    fig.add_axes(axHisty)

    # now determine nice limits by hand:
    binwidth = binwidth
    xmin = np.min(data1)
    xmax = np.max(data1)
    ymin = np.min(data2)
    ymax = np.max(data2)
    #xymax = np.max( [np.max(np.fabs(data1)), np.max(np.fabs(data2))] )
    #lim = (int(xymax/binwidth) + 1) * binwidth

    binsx = np.arange(xmin, xmax + binwidth, binwidth)
    binsy = np.arange(ymin, ymax + binwidth, binwidth)
    #bins = np.arange(-lim, lim + binwidth, binwidth)

    # the scatter plot:
    if isinstance(data1b, np.ndarray):
        print('*args, **kwargs do not have any influcence when using two\
        options')
        axScatter.scatter(data1, data2, facecolor = 'none',
                          edgecolor='k',s=25)
        axScatter.scatter(data1b, data2b, facecolor='none',
                          edgecolor='grey',s=25)

        xminb = np.min(data1b)
        xmaxb = np.max(data1b)
        yminb = np.min(data2b)
        ymaxb = np.max(data2b)
        binsxb = np.arange(xminb, xmaxb + binwidth, binwidth)
        binsyb = np.arange(yminb, ymaxb + binwidth, binwidth)

        axHistx.hist(data1b, bins=binsxb, edgecolor='None',
                     color='grey',normed=True)
        axHisty.hist(data2b, bins=binsyb, orientation='horizontal',
                     edgecolor='None', color='grey', normed=True)

        axHistx.hist(data1, bins=binsx, edgecolor='None',
                     color='k', normed=True)
        axHisty.hist(data2, bins=binsy, orientation='horizontal',
                     edgecolor='None', color='k', normed=True)


    else:
        axScatter.scatter(data1, data2, c= 'black', *args,  **kwargs)

        axHistx.hist(data1, bins=binsx, edgecolor='None', color='k')
        axHisty.hist(data2, bins=binsy, orientation='horizontal',
                     edgecolor='None', color='k')



    # the xaxis of axHistx and yaxis of axHisty are shared with axScatter,
    # thus there is no need to manually adjust the xlim and ylim of these
    # axis.

    majloc1 = MaxNLocator(nbins=4, prune='lower')
    axScatter.yaxis.set_major_locator(majloc1)
    majloc2 = MaxNLocator(nbins=4)
    axScatter.xaxis.set_major_locator(majloc2)

    axScatter.grid(linestyle = 'dashed', color = '0.75',linewidth = 1.)
    axScatter.set_axisbelow(True)
    axHisty.set_axisbelow(True)
    axHistx.set_axisbelow(True)

    # The 'clean' environment
    if cleanstyle == True:
        plt.setp(axHistx.get_xticklabels() + axHisty.get_yticklabels(),
                 visible=False)
        plt.setp(axHistx.get_yticklabels() + axHisty.get_xticklabels(),
                 visible=False)
        axHisty.set_xticks([])
        axHistx.set_yticks([])
        axHistx.xaxis.set_ticks_position('bottom')
        axHisty.yaxis.set_ticks_position('left')

        axHisty.spines['right'].set_color('none')
        axHisty.spines['top'].set_color('none')
        axHisty.spines['bottom'].set_color('none')
        axHisty.spines['left'].set_color('none')

        axHistx.spines['top'].set_color('none')
        axHistx.spines['right'].set_color('none')
        axHistx.spines['left'].set_color('none')
        axHistx.spines['bottom'].set_color('none')
        axScatter.spines['top'].set_color('none')
        axScatter.spines['right'].set_color('none')
    else:
        plt.setp(axHistx.get_xticklabels() + axHisty.get_yticklabels(),
                 visible=False)
        for tl in axHisty.get_yticklabels():
            tl.set_visible(False)
        for tlp in axHisty.get_xticklabels():
            tlp.set_rotation(-90)

        majloc3 = MaxNLocator(nbins=4, prune='lower')
        axHistx.yaxis.set_major_locator(majloc3)
        axHistx.yaxis.tick_right()
        majloc4 = MaxNLocator(nbins=4, prune='lower')
        axHisty.xaxis.set_major_locator(majloc4)
        axHisty.xaxis.tick_top()

        axHisty.yaxis.grid(linestyle = 'dashed', color = '0.75',linewidth = 1.)
        axHistx.xaxis.grid(linestyle = 'dashed', color = '0.75',linewidth = 1.)

    return fig,axScatter,axHistx,axHisty

def _check_binwidth(name,binwidth,minimum=None,maximum=None):
    if maximum and minimum:
        if binwidth > np.abs(maximum - minimum):
            raise Exception('The relative {0} ({1}) is too high (should be lower than {2})'.format(
                name, binwidth, np.abs(maximum - minimum)))
        if binwidth < np.abs(maximum - minimum)/1000:
            raise Exception('The absolute {0} ({1}) is too low (should be larger than {2})'.format(
                name, binwidth, (maximum - minimum)/1000))
    else:
        if binwidth > 1.:
            raise Exception('The relative {0} ({1}) is too high (should be lower than {2})'.format(
                name, binwidth, 1.))
        if binwidth < 1./1000:
            raise Exception('The relative {0} ({1}) is too low (should be larger than {2})'.format(
                name, binwidth, 1./1000))


def Scatter_hist_withOF(data1, data2, data1b=False, data2b=False, xbinwidth = 0.5,
                 ybinwidth=0.5, relative = False, SSE=None, SSEb=None, vmin=None, vmax=None, colormaps=cm.YlOrBr,
                 cleanstyle = False, roodlichter=0.5, *args,  **kwargs):
    '''
    Three-parts plot with the two parameter sitdirbutions plotted on the sides

    Parameters
    -----------
    data1: ndarray
        dataset 1 for x-axis
    data2: ndarray
        dataset 2 for y-axis
    data1b: ndarray
        dataset to plot along the data 1 set
    data2b: ndarray
        dataset to plot along the data 2 set
    xbinwidth: float
        defines the width of the xbin to the data used
    ybinwidth: float
        defines the width of the ybin to the data used
    relative: float
        defines whether the bins are used in a relative or absolute way. The
        number of bins is restricted to a maximum of 1000.
    vmin, vmax : scalar, optional, default None
        min and max to use in the color range. If either are None, the min and max
        of the color array (`SSE`) is used (matplotlib keywords of `scatter`).
    cleanstyle: bool True|False
        if True, a more minimalistic version of the plot is given
    *args,  **kwargs: args
        arguments given toi the scatter plot
        example: s=15, marker='o', edgecolors= 'k',facecolor = 'white'

    Returns
    ---------
    fig: matplotlib.figure.Figure object
        the resulting figure
    axScatter: matplotlib.axes.AxesSubplot object
        the scatter plot with the datapoints, can be used to add labels or
        change the current ticks settings
    axHistx: matplotlib.axes.AxesSubplot object
        the x-axis histogram
    axHisty: matplotlib.axes.AxesSubplot object
        the y-axis histogram

    Examples
    ----------
    >>> #PLOT POSTERIORS
    >>> treshold=20.
    >>> SSE = np.loadtxt(os.path.join(datapath,'SSE_zoom1.txt'))
    >>> pars = np.loadtxt(os.path.join(datapath,'Parameters_zoom1.txt'))
    >>> behavpars = pars[np.where(SSE<treshold)]
    >>> behavSSE = SSE[np.where(SSE<treshold)]
    >>> fig,axScatter,axHistx,axHisty,sc1 = Scatter_hist(behavpars[:,0], behavpars[:,1], data1b=pars[:,0],data2b=pars[:,1],
                 xbinwidth = 15, ybinwidth=0.03,
                 cleanstyle = True, s=25, marker='o', SSE=behavSSE, SSEb=SSE,
                 vmax=treshold+treshold*1.5, colormaps= colormapss, roodlichter=1.0)
    >>> axScatter.set_ylabel(r'r$_H$',fontsize=16)
    >>> axScatter.set_xlabel(r'v$_0$',fontsize=16)
    >>> cbar = fig.colorbar(sc1, ax=axScatter, cmap=colormapss, orientation='vertical',ticks=[treshold,treshold+treshold*1.5],shrink=1.)
    >>> cbar.ax.set_yticklabels(['<'+str(treshold),'> '+str(treshold+treshold*1.5)])

    Notes
    ------
    Typical application is to check the dependency of two posterior
    parameter distrbutions, eventually compared with their selected posteriors

    If a second dataset is added to compare, the style options of the scatter
    plot are fixed and the *args, **kwargs have no influence

    '''
    if not isinstance(data1, np.ndarray):
        raise Exception('dataset 1 need to be numpy ndarray')
    if not isinstance(data2, np.ndarray):
        raise Exception('dataset 2 need to be numpy ndarray')

    if isinstance(data1b, np.ndarray):
        if not isinstance(data2b, np.ndarray):
            raise Exception('Always combine the data of both')
    if isinstance(data2b, np.ndarray):
        if not isinstance(data1b, np.ndarray):
            raise Exception('Always combine the data of both')

    fig = plt.figure(figsize=(10,10))
    axScatter = plt.subplot(111)
    divider = make_axes_locatable(axScatter)
    #axScatter.set_aspect('equal')
    axScatter.set_autoscale_on(True)

    # create a new axes with  above the axScatter
    axHistx = divider.new_vertical(1.5, pad=0.0001, sharex=axScatter)

    # create a new axes on the right side of the
    # axScatter
    axHisty = divider.new_horizontal(1.5, pad=0.0001, sharey=axScatter)

    fig.add_axes(axHistx)
    fig.add_axes(axHisty)

    # now determine nice limits by hand:
#    binwidth = binwidth
    xmin = np.min(data1)
    xmax = np.max(data1)
    ymin = np.min(data2)
    ymax = np.max(data2)

    #xymax = np.max( [np.max(np.fabs(data1)), np.max(np.fabs(data2))] )
    #lim = (int(xymax/binwidth) + 1) * binwidth
    if relative:
        _check_binwidth('xbinwidth', xbinwidth)
        xbinwidth_abs = (xmax-xmin)*xbinwidth
        binsx = np.arange(xmin,xmax+xbinwidth_abs,xbinwidth_abs)
        _check_binwidth('ybinwidth', ybinwidth)
        ybinwidth_abs = (ymax-ymin)*ybinwidth
        binsy = np.arange(ymin,ymax+ybinwidth_abs,ybinwidth_abs)
    else:
        _check_binwidth('xbinwidth', xbinwidth, minimum=xmin, maximum=xmax)
        binsx = np.arange(xmin, xmax + xbinwidth, xbinwidth)
        _check_binwidth('ybinwidth', ybinwidth, minimum=ymin, maximum=ymax)
        binsy = np.arange(ymin, ymax + ybinwidth, ybinwidth)
    #bins = np.arange(-lim, lim + binwidth, binwidth)

    # the scatter plot:
    if isinstance(data1b, np.ndarray): #TWO DATA ENTRIES
        xminb = np.min(data1b)
        xmaxb = np.max(data1b)
        yminb = np.min(data2b)
        ymaxb = np.max(data2b)
        if not relative:
            _check_binwidth('xbinwidth', xbinwidth, minimum=xminb, maximum=xmaxb)
            binsxb = np.arange(xminb, xmaxb + xbinwidth, xbinwidth)
            _check_binwidth('ybinwidth', ybinwidth, minimum=yminb, maximum=ymaxb)
            binsyb = np.arange(yminb, ymaxb + ybinwidth, ybinwidth)
        else:
            xbinwidth_abs = (xmaxb-xminb)*xbinwidth
            binsxb = np.arange(xminb,xmaxb+xbinwidth_abs,xbinwidth_abs)
            ybinwidth_abs = (ymaxb-yminb)*ybinwidth
            binsyb = np.arange(yminb,ymaxb+ybinwidth_abs,ybinwidth_abs)

        if SSE == None:
            print('*args, **kwargs do not have any influence when using two\
            options')
            sc1 = axScatter.scatter(data1, data2, facecolor = 'none',
                              edgecolor='k',s=25)
            axScatter.scatter(data1b, data2b, facecolor='none',
                              edgecolor='grey',s=25)
            #First plot all data
            axHistx.hist(data1, bins=binsx, edgecolor='None',
                         color='k', normed=True)
            axHisty.hist(data2, bins=binsy, orientation='horizontal',
                         edgecolor='None', color='k', normed=True)

            #Afterwards plot behaviourals on top
            axHistx.hist(data1b, bins=binsxb, edgecolor='None',
                         color='grey',normed=True, alpha = roodlichter)
            axHisty.hist(data2b, bins=binsyb, orientation='horizontal',
                         edgecolor='None', color='grey', normed=True, alpha = roodlichter)

        else:
            print('*args, **kwargs do not have any influence when using two\
            options')
            sc1 = axScatter.scatter(data1, data2, c=SSE, vmin=vmin, vmax=vmax,
                              edgecolors= 'none', cmap = colormaps, *args,  **kwargs)

            axScatter.scatter(data1b, data2b, c=SSEb, vmin=vmin, vmax=vmax, alpha=roodlichter,
                              edgecolors= 'none', cmap = colormaps, *args,  **kwargs)
            #First plot all data
            axHistx.hist(data1, bins=binsx, edgecolor='None',
                         color=colormaps(1.), normed=True)
            axHisty.hist(data2, bins=binsy, orientation='horizontal',
                         edgecolor='None', color=colormaps(1.), normed=True)

            #Afterwards plot behaviourals on top
            axHistx.hist(data1b, bins=binsxb, edgecolor='None',
                         color=colormaps(0.),normed=True, alpha = roodlichter)
            axHisty.hist(data2b, bins=binsyb, orientation='horizontal', color=colormaps(0.),
                         edgecolor='None', normed=True, alpha = roodlichter)

    else:  #ONLY ONE DATA1 and DATA2
        if SSE == None:
            sc1 = axScatter.scatter(data0, data2, c= 'black', *args,  **kwargs)
            axHistx.hist(data1, bins=binsx, edgecolor='None', color='k')
            axHisty.hist(data2, bins=binsy, orientation='horizontal',
                         edgecolor='None', color='k')
        else:
            sc1 = axScatter.scatter(data1, data2, c=SSE, vmin=vmin, vmax=vmax,
                              edgecolors= 'none', cmap = colormaps, *args,  **kwargs)
            axHistx.hist(data1, bins=binsx, edgecolor='None', color='k')
            axHisty.hist(data2, bins=binsy, orientation='horizontal',
                         edgecolor='None', color='k')



    # the xaxis of axHistx and yaxis of axHisty are shared with axScatter,
    # thus there is no need to manually adjust the xlim and ylim of these
    # axis.

    majloc1 = MaxNLocator(nbins=4, prune='lower')
    axScatter.yaxis.set_major_locator(majloc1)
    majloc2 = MaxNLocator(nbins=4)
    axScatter.xaxis.set_major_locator(majloc2)

    axScatter.grid(linestyle = 'dashed', color = '0.75',linewidth = 1.)
    axScatter.set_axisbelow(True)
    axHisty.set_axisbelow(True)
    axHistx.set_axisbelow(True)

    # The 'clean' environment
    if cleanstyle == True:
        plt.setp(axHistx.get_xticklabels() + axHisty.get_yticklabels(),
                 visible=False)
        plt.setp(axHistx.get_yticklabels() + axHisty.get_xticklabels(),
                 visible=False)
        axHisty.set_xticks([])
        axHistx.set_yticks([])
        axHistx.xaxis.set_ticks_position('bottom')
        axHisty.yaxis.set_ticks_position('left')

        axHisty.spines['right'].set_color('none')
        axHisty.spines['top'].set_color('none')
        axHisty.spines['bottom'].set_color('none')
        axHisty.spines['left'].set_color('none')

        axHistx.spines['top'].set_color('none')
        axHistx.spines['right'].set_color('none')
        axHistx.spines['left'].set_color('none')
        axHistx.spines['bottom'].set_color('none')
        axScatter.spines['top'].set_color('none')
        axScatter.spines['right'].set_color('none')
    else:
        plt.setp(axHistx.get_xticklabels() + axHisty.get_yticklabels(),
                 visible=False)
        for tl in axHisty.get_yticklabels():
            tl.set_visible(False)
        for tlp in axHisty.get_xticklabels():
            tlp.set_rotation(-90)

        majloc3 = MaxNLocator(nbins=4, prune='lower')
        axHistx.yaxis.set_major_locator(majloc3)
        axHistx.yaxis.tick_right()
        majloc4 = MaxNLocator(nbins=4, prune='lower')
        axHisty.xaxis.set_major_locator(majloc4)
        axHisty.xaxis.tick_top()

        axHisty.yaxis.grid(linestyle = 'dashed', color = '0.75',linewidth = 1.)
        axHistx.xaxis.grid(linestyle = 'dashed', color = '0.75',linewidth = 1.)

    return fig,axScatter,axHistx,axHisty,sc1

###############################
## Output sensitivity Analysis
###############################

def TornadoSensPlot(parnames, parvals, gridbins=4, midwidth=0.5,
                    setequal=False, plotnumb=True, parfontsize=12,
                    bandwidth=0.75):
    '''
    Plot to show sensitivity analysis results of a global sensitivity analysis,
    data is sorted by the algorithm

    Dependencies= numpy, matplotlib

    Parameters
    ------------
    parnames: list
        list of strings with the different parameter names in
    parvals: array
        array with the sensitivity outputs
    gridbins: int
        maximum number of gridlines on the axis ticks (default 4)
    midwidth: float
        define width between the two subplots to adjust to parname-length
    setequal: True | False
        Set positive and negative value ax equal (True) of not (False)
    plotnumb: True | False
        Plot the sensitivity values at the end of the bars
    parfontsize: integer
        default=12, but with latex symbols, larger values is appropriate
    bandwidth: float
        default=0.75, defines the width of the bars, range [0.0,1.0]

    Returns
    --------
    Tornado plot fig

    Examples
    ---------

    >>> rtndval = 100 #between -100 en 100
    >>> parnames = ['par1','par2','par3','par4','par5','par6','par7',
                    'par8','par9','par10']
    >>> parvals = (rtndval+rtndval) * np.random.random_sample(10) - rtndval
    >>> TornadoSensPlot(parnames, parvals, gridbins=5, midwidth=0.4,
                        setequal=True, plotnumb=True,
                        parfontsize=12, bandwidth=0.4)

    Notes
    --------
    To achieve a 2-line parameter values use a slash-n in the parameter names

    Contact for information: Stijn Van Hoey
    '''

    pars = parnames
    #sort the data and pars-list
    ids = np.argsort(np.abs(parvals))
    parssort = [pars[i] for i in ids]
    parvalssort = parvals[ids]

    #differentiate positive and negative effects
    posval = np.where(parvalssort >= 0, parvalssort, 0)
    negval = np.where(parvalssort < 0, parvalssort, 0)

    #use white backgrounds and lines
    matplotlib.rc('axes', facecolor = 'white')
#    matplotlib.rc('figure.subplot', wspace=.65)
    matplotlib.rc('grid', color = 'white')
    matplotlib.rc('grid', linewidth = 1.5)


    # Make figure background the same colors as axes
    fig = plt.figure(figsize = (10, 6), facecolor = 'white')

    # --- Negative effects --- left
    if not negval.any():
        print('no negative sensitivities; axis are made equal')
        setequal = True

    axleft  = fig.add_subplot(121)

    # Keep only top and right spines
    axleft.spines['left'].set_color('none')
    axleft.spines['bottom'].set_color('none')
    axleft.xaxis.set_ticks_position('top')
    axleft.yaxis.set_ticks_position('right')
    axleft.spines['top'].set_position(('axes', 1.0))
    axleft.spines['top'].set_color('w')

    # Set axes limits
    if setequal == True:
        axleft.set_xlim(-max(posval.max(), np.abs(negval).max()), 0)
    else:
        axleft.set_xlim(negval.min(), 0)
    axleft.set_ylim(0, len(pars))
    #Labels
    majorlocator = MaxNLocator(nbins=gridbins)
    axleft.xaxis.set_major_locator(majorlocator)
    axleft.get_xticklines()[-1].set_markeredgewidth(0)
    for label in axleft.get_xticklabels():
        label.set_fontsize(10)
    axleft.set_yticks([])

    # Plot data
    for i in range(len(pars)):
        value = negval[i]
        p = patches.Rectangle((0, i+(1.-bandwidth)/2.), value,
                              bandwidth, fill=True,
                              transform=axleft.transData,
                              lw=0, facecolor='grey', alpha=0.8)

        #plot numbers as text on end of bars
        if plotnumb == True:
            if value < 0.0:
                axleft.text(value+0.15*negval.min(),
                            i+bandwidth/2.+(1.-bandwidth)/2.,
                            str(np.round(value,decimals=2)),
                            family='Helvetica Neue', size=10, color='0.',
                            horizontalalignment="center",
                            verticalalignment="center")
        axleft.add_patch(p)
    # Add a grid
    axleft.grid()

    # --- Positive effects ---
    if not posval.any():
        print('no positive sensitivities; axis are made equal')
        setequal = True

    axright = fig.add_subplot(122, sharey=axleft)
    fig.subplots_adjust(wspace=midwidth)
    # Keep only top and left spines
    axright.spines['right'].set_color('none')
    axright.spines['bottom'].set_color('none')
    axright.xaxis.set_ticks_position('top')
    axright.yaxis.set_ticks_position('left')
    axright.spines['top'].set_position(('axes', 1.0))
    axright.spines['top'].set_color('w')
    # Set axes limits
    if setequal == True:
        axright.set_xlim(0, max(posval.max(), np.abs(negval).max()))
    else:
        axright.set_xlim(0, posval.max())

    axright.set_ylim(0, len(pars))
    #Labels
    majorlocator2 = MaxNLocator(nbins = gridbins)
    axright.xaxis.set_major_locator(majorlocator2)
    for label in axright.get_xticklabels():
        label.set_fontsize(10)
    axright.get_xticklines()[1].set_markeredgewidth(0)

    #set ticks between the bars
    axright.set_yticks(np.arange(0, len(parnames), 1))
    axright.set_yticklabels([], visible=False)
    # Plot data
    for i in range(len(pars)):
        value = posval[i]
        p = patches.Rectangle((0, i+(1.-bandwidth)/2.), value, bandwidth,
                              fill=True, transform=axright.transData,
                              lw=0, facecolor='grey', alpha=0.8)

        #plot numbers as text on end of bars
        if plotnumb == True:
            if value > 0.0:
                axright.text(value+0.1*posval.max(),
                             i+bandwidth/2.+(1.-bandwidth)/2.,
                            str(np.round(value, decimals = 2)),
                            family='Helvetica Neue', size = 10, color = '0.',
                            horizontalalignment = "center",
                            verticalalignment = "center")
        axright.add_patch(p)
    # Add a grid
    axright.grid()

    # Y axis labels
    # We want them to be exactly in the middle of the two y spines
    for i in range(len(pars)):
        x1, y1 = axleft.transData.transform_point((0, i+.5))
        x2, y2 = axright.transData.transform_point((0, i+.5))
        x, y = fig.transFigure.inverted().transform_point(((x1+x2)/2., y1))
        plt.text(x, y, parssort[i], transform=fig.transFigure,
                 size=parfontsize, horizontalalignment='center',
                 verticalalignment='center')
    return fig, axleft, axright

def plotbar(ax1, values, names, width = 0.5, addval = True, sortit = False,
            *args, **kwargs):
    '''
    Plot a barchart of the given values

    Parameters
    -----------
    ax1: axes.AxesSubplot object
        an subplot instance where the graph will be located,
        this supports the use of different subplots
    values: list/array
        values to make barplot
    names: list
        list of strings with the names of the barplot, equal size as values
    width: float
        [0-1], width of the barplots
    addval: bool
        if True, the values are plotted above the bars
    sortit: bool
        if True, parameters ar sorted along their index
    *args, **kwargs: args
        passed to the matplotlib.bar; width is already given above

    Returns
    --------
    ax1

    Examples
    ----------
    >>> fig = plt.figure()
    >>> ax1 = fig.add_subplot(111)
    >>> values = np.random.random(5)
    >>> names = ['a',r'$\beta$','k', 'l', 's']
    >>> plotbar(ax1, values, names, width = 0.87, addval = True, sortit = True,
                color='grey', ec='grey')
    '''
    if sortit ==True:
        ids = np.argsort(np.abs(values))[::-1]
        parssort = [names[i] for i in ids]
        parvalssort = values[ids]
        values = parvalssort
        names = parssort

    ax1.spines['top'].set_color('none')
    ax1.spines['right'].set_color('none')
    ax1.spines['bottom'].set_position('zero')

    bwidth = width
    xlocations = np.array(range(len(values))) + 0.25
    ax1.bar(xlocations, values, width = bwidth, *args, **kwargs)

    if addval == True:
        for i in range(len(values)):
            if values[i] > 0.0:
                if values[i] < 0.001:
                    ax1.text(xlocations[i]+bwidth/2., values[i]+0.025*np.abs(values).max(),
                                         "< 0.001", color='0.5', size=10,
                                         horizontalalignment='center',
                                         verticalalignment='bottom')
                else:
                    ax1.text(xlocations[i]+bwidth/2., values[i]+0.025*np.abs(values).max(),
                                         "%.3f"%values[i], color='0.5', size=10,
                                         horizontalalignment='center',
                                         verticalalignment='bottom')
            else:
                if values[i] > -0.001:
                    ax1.text(xlocations[i]+bwidth/2., values[i]-0.025*np.abs(values).max(),
                                         "< 0.001", color='0.5', size=10,
                                         horizontalalignment='center',
                                         verticalalignment='top')
                else:
                    ax1.text(xlocations[i]+bwidth/2., values[i]-0.025*np.abs(values).max(),
                                         "%.3f"%values[i], color='0.5', size=10,
                                         horizontalalignment='center',
                                         verticalalignment='top')

    if values.max() > 0.0:
        ax1.set_ylim(top = values.max() + 0.08*np.abs(values).max())
    if values.min() < 0.0:
        ax1.set_ylim(bottom = values.min() - 0.08*np.abs(values).max())


    majloc = MaxNLocator(nbins=4, prune='lower')
    ax1.yaxis.set_major_locator(majloc)
    ax1.xaxis.tick_bottom()
    ax1.yaxis.tick_left()
    ax1.set_xlim(left=0.,right=xlocations[-1]+bwidth+0.25)

    #adjust the ticks to be plotted in function of the sign of the values
    ax1.set_xticks(xlocations + bwidth/2., names) #, rotation = 30)
    ax1.set_xticks(xlocations + bwidth/2.)
    ax1.set_xticklabels(names)

    cnt = 0
    for tklabel in ax1.get_xticklabels():
        if values[cnt] > 0.:
            pass
        else:
            #this needs improvement:
            poss = np.abs(ax1.get_ylim()[0])*0.05 + np.abs(ax1.get_ylim()[1])*0.08
            tklabel.set_verticalalignment('center')
            tklabel.set_position((0.,poss))
        cnt+=1
    return ax1

def plothbar(ax1, values, names, width = 0.5, addval = True, sortit = False,
            *args, **kwargs):
    '''
    Plot a barchart of the given values

    Parameters
    -----------
    ax1: axes.AxesSubplot object
        an subplot instance where the graph will be located,
        this supports the use of different subplots
    values: list/array
        values to make barplot
    names: list
        list of strings with the names of the barplot, equal size as values
    width: float
        [0-1], width of the barplots
    addval: bool
        if True, the values are plotted above the bars
    sortit: bool
        if True, parameters ar sorted along their index
    *args, **kwargs: args
        passed to the matplotlib.bar; width is already given above

    Returns
    --------
    ax1

    Examples
    ----------
    >>> fig = plt.figure()
    >>> ax1 = fig.add_subplot(111)
    >>> values = np.random.random(5)
    >>> names = ['a',r'$\beta$','k', 'l', 's']
    >>> plotbar(ax1, values, names, width = 0.87, addval = True, sortit = True,
                color='grey', ec='grey')
    '''
    if sortit ==True:
        ids = np.argsort(np.abs(values))#[::-1]
        parssort = [names[i] for i in ids]
        parvalssort = values[ids]
        values = parvalssort
        names = parssort

    ax1.spines['bottom'].set_color('none')
    ax1.spines['right'].set_color('none')
    ax1.spines['bottom'].set_position('zero')

    bwidth = width
    ylocations = np.array(range(len(values))) + 0.25
    ax1.barh(ylocations, values,  height = width, *args, **kwargs)

    if addval == True:
        for i in range(len(values)):
            if values[i] > 0.0:
                if values[i] < 0.001:
                    ax1.text(values[i]+0.025*np.abs(values).max(), ylocations[i]+bwidth/2.,
                                         "< 0.001", color='0.5', size=10,
                                         horizontalalignment='left',
                                         verticalalignment='center')
                else:
                    ax1.text(values[i]+0.025*np.abs(values).max(), ylocations[i]+bwidth/2.,
                                         "%.3f"%values[i], color='0.5', size=10,
                                         horizontalalignment='left',
                                         verticalalignment='center')

            else:
                if values[i] > -0.001:
                    ax1.text(values[i]-0.025*np.abs(values).max(),ylocations[i]+bwidth/2.,
                                         "< 0.001", color='0.5', size=10,
                                         horizontalalignment='left',
                                         verticalalignment='right')
                else:
                    ax1.text(values[i]-0.025*np.abs(values).max(), ylocations[i]+bwidth/2.,
                                         "%.3f"%values[i], color='0.5', size=10,
                                         horizontalalignment='center',
                                         verticalalignment='right')

    if values.max() > 0.0:
        ax1.set_xlim(right = values.max() + 0.08*np.abs(values).max())
    if values.min() < 0.0:
        ax1.set_xlim(left= values.min() - 0.08*np.abs(values).max())


    majloc = MaxNLocator(nbins=4, prune='lower')
    ax1.xaxis.set_major_locator(majloc)
    ax1.xaxis.tick_top()
    ax1.yaxis.tick_left()
    ax1.set_ylim(bottom=0., top = ylocations[-1]+bwidth+0.25)

    #adjust the ticks to be plotted in function of the sign of the values
    ax1.set_yticks(ylocations + bwidth/2., names) #, rotation = 30)
    ax1.set_yticks(ylocations + bwidth/2.)
    ax1.set_yticklabels(names)

    cnt = 0
    for tklabel in ax1.get_yticklabels():
        if values[cnt] > 0.:
            pass
        else:
            #this needs improvement:
            poss = np.abs(ax1.get_xlim()[0])*0.05 + np.abs(ax1.get_xlim()[1])*0.08
            tklabel.set_verticalalignment('center')
            tklabel.set_position((0.,poss))
        cnt+=1
    return ax1

#def coor2box(poss, txt_height, txt_width):
#    '''
#    help function to transform point coordinates to a box around the points
#    poss is  [x,y]
#    returns [xmin,xmax,ymin,ymax]
#    '''
#    return [poss[0]-txt_width/2., poss[0]+txt_width/2., poss[1]-txt_height/2.,
#            poss[1]+txt_height/2.]
#
#def checkifinbox(poss, boxcoord, txt_height, txt_width):
#    '''
#    help function
#    boxcoord is: [[xmin,xmax,ymin,ymax],[xmin,xmax,ymin,ymax],...]
#    poss is  [x,y]
#    '''
#    newbox = coor2box(poss, txt_height, txt_width)
#    print newbox,'nb'
#    noprob=True
#    ids=0
#    if len(boxcoord) > 0:
#        for boxs in boxcoord:
#            int_left  = max(boxs[0], newbox[0])
#            int_right  = min(boxs[1], newbox[1])
#            int_bottom = min(boxs[2], newbox[2])
#            int_top = max(boxs[3], newbox[3])
#            if int_right > int_left or int_bottom > int_top:
#                noprob = False
#                idprob = ids
#            else:
#                idprob = 0
#            ids+=1
#    else:
#        idprob = 0
#
#    return noprob,idprob


def scatterwithtext(axs, xval, yval, names, *args, **kwargs):
    '''
    Plot a scatter diagram with text plotted next to the points

    Parameters
    -----------
    axs: axes.AxesSubplot object
        an subplot instance where the graph will be located,
        this supports the use of different subplots
    xval: ndarray or list
        x values
    yval: ndarray or list
        y values
    names: list
        list of string values
    *args, **kwargs: args
        extra arguments used in the plot-function of the data points

    Notes
    -------
    Not the matplotlib.scatter is used, but the plot function for adding
    the data-points

    The general output is not very clean in terms of axis limits, to remain
    optimal flexibility in the user-defined properties

    Examples
    ---------
    >>> fig = plt.figure()
    >>> ax1 = fig.add_subplot(111)
    >>> ax1 = scatterwithtext(ax1, [1.0,3.0,2.0,7.0,0.2], [3.,8.,1.,4.,5.0],
                      [r'$X_1$',r'$X_2$',r'$X_3$',r'$X_4$',r'$X_5$'],'ks')

    '''
    if not len(xval) == len(yval) == len(names):
        raise Exception('xval,yval and names need to be of the same length')

    #Calculation of the offset of the points to put text next to marker
    transOffset = offset_copy(axs.transData, fig=plt.gcf(), x = -0.05, y=0.10, units='inches')
    ct2=0
    txtobjects=[]
    for x, y in zip(xval, yval):
        axs.plot((x,),(y,), *args, **kwargs)
        if x > 0.001 or x< -0.001:
            ls = axs.text(x, y, '%s' %names[ct2], transform=transOffset, color='k')
            txtobjects.append(ls)
        ct2+=1

    return axs, txtobjects

def plot_evolution(values, names, labell = -0.06, *args, **kwargs):
    '''
    Plot the evolution of the different values, with in the rows the
    change in value and the columns the different factors to evaluate

    Parameters
    -----------
    values: ndarray
        2D array (Nxvals) of the N outputs of values
    names: list
        list of strings of the value names
    labell: float
        negative value (distance) to align the ylabels
    *args, **kwargs: args
        passed to the matplotlib.plot function

    Returns
    --------
    fig: matplotlib.figure.Figure object
        figure containing the output

    axes: array of matplotlib.axes.AxesSubplot object
        enabled post-processing of the ax-elements

    Examples
    ----------
    >>> values=np.random.random((1000,5))
    >>> names=['par1','par2','par3','par4','par5']
    >>> plot_evolution(values, names,c='k')

    '''
    if values.shape[1] != len(names):
        raise Exception('Number of values is not mathcing name length')

    numvars = values.shape[1]
    fig, axes = plt.subplots(nrows=numvars, ncols=1,
                             figsize=(40,10), sharex='col')
    fig.subplots_adjust(hspace=0.05, wspace=2.)

    cnt = 0
    for ax in axes.flat:
        #hide labels, except of last row graph
        ax.xaxis.set_visible(False)
        if ax.is_last_row():
                ax.xaxis.set_ticks_position('bottom')
                ax.xaxis.set_visible(True)

        #plot the data
        ax.plot(values[:,cnt], *args, **kwargs)

        majorLocator = MaxNLocator(nbins=4,prune='both')
        ax.yaxis.set_major_locator(majorLocator)

        for tick in ax.yaxis.get_major_ticks():
            tick.label.set_fontsize(10)

        ax.set_ylabel(names[cnt])
        ax.yaxis.set_label_coords(labell, 0.5)
        cnt+=1

    return fig,axes

def interactionplot(values, names, lwidth = 2.):
    '''
    2D plot of intactive terms between a set of N factors

    Parameters
    ------------
    values: ndarray
        2D array (NxN) of the interactive values, with half of the matrix without
        values, namely the lower half. Upper (left half) is having the results
    names: list of string
        names of the N factors
    lwidth: float
        width of the black lines of the grid

    Returns
    --------
    fig:
        fig object

    ax1: axes.AxesSubplot object

    Parameters
    -----------
    >>> facs = 7
    >>> values = np.zeros((facs,facs))
    >>> for i in range(facs):
    >>>     for j in range(i+1,facs):
    >>>         values[i,j] = np.random.random()
    >>> names = ['A','B','C','D','E','F','G']
    >>> fig, ax1 = interactionplot(values, names, lwidth = 2.)
    >>> ax1.text(0.1,0.9,r'$ST_{ij}$', transform = ax1.transAxes, fontsize=30,
             verticalalignment = 'top', horizontalalignment = 'left')

    '''
    if values.shape[0] != values.shape[1]:
        raise Exception('Number of rows and columsn need to be the same')

    nsize = values.shape[0]

    fig = plt.figure()
    ax1 = fig.add_subplot(111)

    plt.pcolor(values, cmap=cm.gray_r, edgecolors='k',
               norm = Normalize(), linewidths=lwidth)
    plt.colorbar(pad = 0.10)
    xlocations = np.array(range(nsize)) + 0.5
    ax1.yaxis.tick_right()
    plt.xticks(xlocations, names, rotation = 30)
    plt.yticks(xlocations, names, rotation = 30) #, size='small'
    ax1.xaxis.tick_bottom()
    ax1.spines['top'].set_color('none')
    ax1.spines['left'].set_color('none')

    polygon = Polygon(np.array([[0.,0.],[nsize,nsize],[0.,nsize]]),
                      facecolor='white', ec='white', lw=0.001)
    ax1.add_patch(polygon)
    line = mlines.Line2D([0.,nsize], [0.,nsize],c='k',lw=lwidth)
    ax1.add_line(line)
    return fig, ax1

###############################
## Climate/Timerie Visualisation
###############################

def PolarYear(axs, data, tticks, tickspos = 1, ticksrounder = -1,
              tickscolor = '1.', textcenter = False):
    '''
    Polar plot of 12 datapoints representing a monthly output

    Parameters
    ------------
    axs: axes.AxesSubplot object
        an subplot instance where the graph will be located,
        this supports the use of different subplots
    data: narray
        monthly data point, from january till december
    tticks: narray
        the places (datapoints) where to put gridlines and tick, the last
        element is only used to make grid, no number plotted to prevent from
        disturbance with monthly numbers
    tickspos: int (1-12)
        the month on which the ticks are plotted, 1=jan,..., 12=dec
    ticksrounder: int
        the decimal to round the maximum value to define max-value
        of the plot, default -1
    tickscolor: color
        the color of the ticks, in function of the background month selected
    textcenter: str|False
        if textstring, this is placed in centre of the graph
        on white background

    Returns
    ---------
    axes.AxesSubplot object

    Examples
    ---------

    >>> vals = (120) * np.random.random_sample(12)
    >>> tticks = np.around(np.linspace(0,120,5+2)[1:],-1)
    >>> fig = plt.figure(figsize=(10,10), facecolor='white')
    >>> axs = fig.add_subplot(1,1,1, polar=True, axisbelow=False)
    >>> axs = PolarYear(axs,vals,tticks,tickspos=vals.argmax()+1,tickscolor='1.')
    >>> axs.set_title('2002')

    '''
    labels = ['January', 'Feburary', 'March', 'April', 'May', 'June',
          'July', 'August', 'September', 'October', 'November', 'December']

    n = len(labels)
    # Put labels on outer
    T = np.arange(np.pi/n, 2*np.pi, 2*np.pi/n)
    maxi = np.around(data.max(), ticksrounder)
    R = np.ones(n)*maxi
    width = 2*np.pi/n

    # Labels
    for i in range(T.size):
        theta = T[n-1-i]+np.pi/n + 2*np.pi/n
        plt.text(theta, maxi*1.15, labels[-i], rotation = 180*theta/np.pi-90,
                 size=12, horizontalalignment = "center",
                 verticalalignment = "center")

        plt.text(theta, maxi*1.05, str(np.round(data[-i], decimals = 1)),
                 rotation = 180*theta/np.pi-90, size=10, color = '0.',
                 horizontalalignment = "center", verticalalignment = "center")

    # Data
    R = data
    bars2 = axs.bar(T, R, width = width, bottom = 0.0 , linewidth = 1,
                    facecolor = '0.75', edgecolor = '1.00')

    rcol = (R-R.min()*0.6)/(maxi-R.min()*0.6)
    for i, bart in enumerate(bars2):
        bart.set_facecolor(plt.cm.Greys(rcol[i]))

    #place the ticks manually
    #    theta = T[n-1-tickspos] + 2.7*np.pi/n
    if tickspos == 1:
        theta = T[11] + 2.7*np.pi/n
    else:
        theta = T[tickspos-2] + 2.7*np.pi/n

    for i in range(tticks.size-1):
        #place labels manually
        plt.text(theta, tticks[i], int(np.around(tticks[i], decimals = 0)),
                 size = 10, color = tickscolor,
                 horizontalalignment = "center",
                 verticalalignment = "center")

    #put text in center
    if textcenter:
        axs.bar(T, 20*np.ones(T.size), width = width, bottom = 0.0,
                          linewidth = 2, facecolor = '1.',
                         edgecolor = '1.00', alpha = 0.9)
        ##Text i the center
        plt.text(1*np.pi/2, 0.05, textcenter,
                 size = 20, horizontalalignment = "center",
                 verticalalignment = "bottom")

    # Set ticks, tick labels and grid
    axs.set_ylim(0, maxi*1.2)
    axs.set_xticks(T)
    axs.set_yticks(tticks)
    plt.grid()
    axs.yaxis.grid(linestyle = '-', color = '0.75')
    axs.set_xticklabels([], visible = False)
    axs.set_yticklabels([], visible = False)

    return axs

###############################
## Others
###############################

def Hist_withfit(axs, data, NormalFit=False, addinfo = False,
                 *args, **kwargs):
    '''
    Histogram of a variable with a normal distribution fit,
    if a normal distirbution is used.

    Parameters
    ------------
    axs: axes.AxesSubplot object
        an subplot instance where the graph will be located,
        this supports the use of different subplots
    data: narray
        numpy array with the data
    NormalFit: bool True|False
        defines it a fit to normal distribution is added or not
    addinfo: bool True|False
        add the mean and variance on the plot
    *args, **kwargs: arg
        passed to the plt.hist function

    Examples
    ---------
    >>> y=np.random.normal(size = 1000)
    >>> fig=plt.figure()
    >>> axs = fig.add_subplot(111)
    >>> axs = Hist_withfit(axs, y, NormalFit=True, addinfo = True,
                       normed=True, color='0.6',edgecolor = 'white', bins=20,
                       cumulative = False)

    '''
    mu = np.mean(data)
    sigma = np.std(data)

    # the histogram of the data
    n, bins, patches = axs.hist(data, *args, **kwargs)

    #test if cumulative or not
    ln = n.tolist()
    lln = [ln[i+1]>=ln[i] for i in range(len(ln)-1)]
    if False in lln:
        cum=False
    else:
        cum=True

    if np.any(n>1.001):
        raise Exception('Fitting only to normed distribution, \
        use the normed option for the histogram')

    if NormalFit ==True:
        t = np.arange((mu-3*sigma),(mu+3*sigma),(6*sigma/bins.size))
        y = mlab.normpdf(t, mu, sigma)
        if cum == True:
            raise Exception('Fitting only to histograms pdf, not to cdf')
        else:
            axs.plot(t, y, '--', color = 'grey', linewidth=1.)

    #set ticks
    if cum == True:
        axs.set_ylim(top=1.01)
    majorlocator = MaxNLocator(nbins = 5, prune = 'lower')
    axs.yaxis.set_major_locator(majorlocator)

#    axs.set_ylabel(r'$\mathrm{Frequency}$')
#    axs.set_title(r'$\mathrm{Histogram\ of\ Output:}\ \mu=%f,\ \sigma=%f$' %(mu,sigma))  #mathrm geeft het in roman style weer...
    if addinfo == True:
        axs.text(0.1,0.9,'$\mu=%f$\n$\sigma=%f$' %(mu,sigma),
                 transform = axs.transAxes, fontsize = 12,
                 horizontalalignment='left', verticalalignment='center')
    return axs

def Contour_ofspace(axs, Z, xmin, xmax, ymin, ymax, NumberLines=6,
                addinline = False, colormapt=False, *args, **kwargs):
    '''
    Contourplot made easier and nicer

    Parameters
    ------------
    axs: axes.AxesSubplot object
        an subplot instance where the graph will be located,
        this supports the use of different subplots
    Z: narray 2D
        array to translate in controu lines
    xmin: float
        minimal x value
    xmax: float
        maximal x value
    ymin: float
        minimal y value
    ymax: float
        miaximal y value
    Numberlines: int
        number of levels t plot the contout lines
    addinline: bool
        if True, the labels of the lines are added
    colormapt: bool
        if True a colormap is added
    *args, **kwargs: arg
        passed to the plt.contour function

    Returns
    --------
    axs instance

    Examples
    ----------
    >>> fig = plt.figure()
    >>> axs = fig.add_subplot(111)
    >>> Z=np.random.random((10,10))
    >>> xmin,xmax,ymin,ymax = 0.0,1.0,0.,1.
    >>> ContourPlot(axs,Z,xmin,xmax,ymin,ymax,NumberLines=3,
                addinline = True, colormapt=True, colors='k', linestyle = ':')

    '''
    #calculates step to use for number of elements
    delta1 =(float(xmax)-float(xmin))/float((Z.shape[1]-1))
    delta2 =(float(ymax)-float(ymin))/float((Z.shape[0]-1))
    #make grid
    x = np.arange(xmin, xmax+1e-10, delta1)
    y = np.arange(ymin, ymax+1e-10, delta2)
    X, Y = np.meshgrid(x, y)

##    #handmatig de levels ingeven, waar je lijn wil hebben...
##    levels = np.arange(-1.2, 1.6, 0.2)
##    CS = plt.contour(Z, levels,origin='lower',linewidths=2,
#                       extent=(-3,3,-2,2))
        #enkel werkzaam als X,Y niet opgegeven in contour

    CS = axs.contour(X, Y, Z, NumberLines, *args,
                     **kwargs) #, origin='lower', colors='k'

    if addinline == True:
        axs.clabel(CS, fontsize=9, inline=1)

    #always plotting colormap, but adapting alpha
    #makes sure that the boundaries are correct
    if colormapt == True:
        alphat = 0.85
    else:
        alphat = 0.0

    #colormap for image
    im = axs.imshow(Z, interpolation='bilinear', origin='lower',
                    cmap=cm.gray, extent=(xmin, xmax, ymin, ymax),
                    alpha=alphat)
    if colormapt==True:
        plt.colorbar(im, orientation='horizontal', shrink=0.8)

    return axs
