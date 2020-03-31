# -*- coding: utf-8 -*-
"""
@author: VHOEYS
development supported by Flemish Institute for Technological Research (VITO)
"""

import os
import numpy as np
import pandas as pd
from scipy import stats

#from utilities.FDC import *

#if evaluation: minimization
#If likelihood: maximization (openen in RSA/GLUE/..)

class FlowAnalysis(object):
    '''
    Class for analyzing the flow characteristics
    '''

    def __init__(self, observed):
        self.observed = observed

class Evaluation(FlowAnalysis):
    '''
    Class for deriving different evaluation criteria.

    References
    --------------
    ..  [E1] Gupta H.V., Sorooshian S., Yapo P.O.(1998), Toward improved
        calibration of hydrologic models: Multiple and noncommensurable
        measures of information, Water Resources Research,pp 751-763
    ..  [E2] H. Hauduc, M. B. Neumann, D. Muschalla, V. Gamerith, S. Gillot
        and P.A. Vanrolleghem (2011), Towards quantitative quality criteria
        to evaluate simulation results in wastewater treatment – A critical
        review. Proceedings 8th symposium on systems analysis and integrated
        assessment (Watermatex 2011)
    '''

    def __init__(self, observed, modelled):
         FlowAnalysis.__init__(self, observed)

         if not modelled.shape == observed.shape:
             raise Exception('Modelled and observed timeseries need \
                                 to be of the same size')

         self.modelled = modelled
         self.residuals = self.observed - self.modelled
         self.infodict()

         print('Criteria suited for model minimization, use optim=True to be sure')

    def infodict(self):
        '''
        Prepares information dictionary
        '''
        self.explainname={}
        #CAT 1
        self.explainname['PDIFF'] = 'Peak Difference'
        self.explainname['PEP'] = 'Percent Error In Peak'
        #CAT 2
        self.explainname['ME'] = 'Mean Error'
        self.explainname['MAE'] = 'Mean Absolute Error'
        self.explainname['MSE'] = 'Mean Squared Error'
        self.explainname['MSLE'] = 'Mean Squared Logarithm Error'
        self.explainname['AME'] = 'Absolute Maximum Error'
        self.explainname['MSSoE'] = 'Mean Sqaured sorted Errors'
        self.explainname['MSDE'] = 'Mean Square Derivative Error'
        self.explainname['RMSE'] = 'Root Mean Square Error'
        self.explainname['RRMSE'] = 'Relative Root Mean Square Error'
        self.explainname['RMSE_log'] = 'Root Mean Square Error with log values'
        self.explainname['RMSE_boxcox'] = 'Root Mean Square Error with boxcox values'
        self.explainname['R4MS4E'] = 'Root 4 Mean Square 4 Error'
        self.explainname['SSE'] = 'Sum of squared Errors'
        self.explainname['NSC'] = 'Number of Sign Changes of the residuals'
        #CAT 3
        self.explainname['MPE'] = 'Mean Percent Error'
        self.explainname['MRE'] = 'Mean Relative Error'
        self.explainname['MARE'] = 'Mean Absolute Relative Error'
        self.explainname['SARE'] = 'Sum of Absolute Relative Error'
        self.explainname['MeAPE'] = 'Median Absolute Percent Error'
        self.explainname['MSRE'] = 'Mean Square Relative Error'
        self.explainname['MAPE'] = 'Mean Absolute Percent Error'
        #CAT 4
        self.explainname['PBIAS'] = 'Percent Bias'
        self.explainname['APBIAS'] = 'Absolute Percent Bias'
        self.explainname['BIAS'] = 'Percent Bias'
        self.explainname['RVE'] = 'Relative Volume Error'
        self.explainname['RMAE'] = 'Relative Mean Absolute Error'
        self.explainname['ThInC'] = 'Theils Inequality Coefficient'
        #CAT 5
        self.explainname['TMC'] = 'Total Mass Controller'
        self.explainname['CrBal'] = 'Balance Criterion '
        #CAT 6
        self.explainname['NSE'] = 'Nash-Sutcliffe Efficiency criterion'
        self.explainname['NSE_sqrt'] = 'Nash-Sutcliffe Efficiency criterion with root values'
        self.explainname['NSE_log'] = 'Nash-Sutcliffe Efficiency criterion with logarithmic values'
        self.explainname['NSE_boxcox'] = 'Nash-Sutcliffe Efficiency criterion with boxcox transformed values'
        self.explainname['RAE'] = 'Relative Absolute Error'
        self.explainname['RSR'] = 'RMSE-observation standard deviation ratio'
        self.explainname['IA'] = 'index of agreement'
        self.explainname['PI'] = 'Coefficient of persistence'
        #CAT 7
        self.explainname['RFLAUT'] = 'First (or higher) lag autocorrelation'
        self.explainname['SFDCE'] = 'Calculate the Slope of the flow duration curve error'
        self.explainname['LowFDCE'] = 'Flow Duration Curve based low flow criterion'
        self.explainname['highFDCE'] = 'Flow Duration Curve based high flow criterion'
        #CAT 8
        self.explainname['NSE_BIAS'] = 'Nash-Sutcliffe & BIAS'
        self.explainname['NSE_FDClow'] = 'Nash-Sutcliffe & Flow Duration Curve low flows'
        self.explainname['NSE_FDChigh'] = 'Nash-Sutcliffe & Flow Duration Curve high flows'

###########################################################################
#CAT 1: Single event statistics:
#    In case modelling objectives require accurate simulation of events (e.g.:
#    handle storm flows, toxic peaks), criteria are needed to characterise the
#    goodness-of-fit of the model for this event. The single event statistics
#    peak difference (Gupta et al., 1998) and percent error in peak
#    (Dawson et al., 2007) aim at characterising the difference between
#    the maximum observed and the maximum modelled value.
###########################################################################

    def PDIFF(self, optim = False):
        '''
        Peak Difference

        Parameters
        -----------
        optim : bool
            if True, the objective is translated to be used in optimizations
            where a minimum value is seeked by the algorithm

        Notes
        -------
        This criterion evaluate how well the highest modelled value matches
        the highest observed value in percent. However, it does not take into
        account whether the max(Oi) and max(Pi) occur at the same time-step i.

        Consequently, in case of multiple events on the same time-series,
        first the single events must be extracted from the whole time series
        to have less chance to mix up with peaks from another event.

        * range: [-inf, inf]
        * optimum: 0
        * category: single event
        '''
        OF = np.max(self.observed)-np.max(self.modelled)

        if optim == True:
            OF = np.abs(OF)
        return OF

    def PEP(self, optim = False):
        '''
        Percent Error In Peak

        Parameters
        -----------
        optim : bool
            if True, the objective is translated to be used in optimizations
            where a minimum value is seeked by the algorithm

        Notes
        -------
        This criterion evaluate how well the highest modelled value matches
        the highest observed value in percent. However, it does not take into
        account whether the max(Oi) and max(Pi) occur at the same time-step i.

        Consequently, in case of multiple events on the same time-series,
        first the single events must be extracted from the whole time series
        to have less chance to mix up with peaks from another event.

        * range: [-inf, inf]
        * optimum: 0
        * category: single event
        '''
        OF = ((np.max(self.observed)-np.max(self.modelled))*100.)/np.max(self.observed)

        if optim == True:
            OF = np.abs(OF)

        return OF

###########################################################################
#CAT 2: Absolute criteria:
#    The absolute criteria are based on the
#    sum of residuals (difference between observed Oi and predicted Pi values
#    respectively at time step i), generally averaged by the number of data. A
#    low value of this criterion means a good agreement between observation
#    and simulation (with γ an exponent).
###########################################################################

    def ME(self, optim = False):
        '''
        Mean Error

        Parameters
        -----------
        optim : bool
            if True, the objective is translated to be used in optimizations
            where a minimum value is seeked by the algorithm

        Notes
        -------
        The mean of residuals allows highlighting the existence of systematic
        bias, i.e. characteristic of a model leading to systematic over- or
        under-prediction [E1]_. However, with this criterion errors
        can compensate each other, so no information on the magnitude of
        the errors is obtained.

        * range: [-inf, inf]
        * optimum: 0
        * category: Absolute criteria

        References
        -----------
        ..  [E3] Power M. (1993) The predictive validation of ecological and
            environmental models. Ecological Modelling, 68(1-2), 33-50.
        '''
        OF = self.residuals.mean()

        if optim == True:
            OF = np.abs(OF)

        return OF

    def MAE(self):
        '''
        Mean Absolute Error

        Notes
        -------
        The mean absolute error indicates the average magnitude of the model
        error (accuracy) [E4]_. Taking the absolute value
        avoids error compensation, but does not indicate the direction of
        the deviation.

        * range: [0, inf]
        * optimum: 0
        * category: Absolute criteria

        References
        -----------
        ..  [E4] Willmott C.J., Ackleson S.G., Davis R.E., Feddema J.J.,
            Klink K.M., Legates D.R., O'Donnell J. and Rowe C.M. (1985)
            Statistics for the evaluation and comparison of models.
            Journal of Geophysical Research, 90(C5), 8995-9005.
        '''
        OF = np.abs(self.residuals).mean()
        return OF

    def MSE(self):
        '''
        Mean Squared Error

        Notes
        -------
        The mean square error avoids error compensations and
        emphasises high errors [E4]_.

        * range: [0, inf]
        * optimum: 0
        * category: Absolute criteria

        '''
        OF = (self.residuals**2).mean()
        return OF

    def MSLE(self):
        '''
        Mean Squared Logarithm Error

        Notes
        -------
        The mean square logarithm error is the sum of the squares of
        the differences of the natural logarithm of the predicted and
        observed value [E5]_. It emphasises low magnitude
        errors.

        * range: [0, inf]
        * optimum: 0
        * category: Absolute criteria

        References
        -----------
        ..  [E5] Dawson C.W., Abrahart R.J. and See L.M. (2010) HydroTest:
            Further development of a web resource for the standardised
            assessment of hydrological models. Environmental Modelling and
            Software, 25(11), 1481-1482.

        '''
        OF = ((np.log(self.observed) - np.log(self.modelled))**2).mean()
        return OF

    def AME(self):
        '''
        Absolute Maximum Error


        Notes
        -------
        The absolute maximum error indicates the maximum error of the model
        [E1]_. This criterion is very sensitive to outliers

        * range: [0, inf]
        * optimum: 0
        * category: Absolute criteria
        '''
        OF = np.max(np.abs(self.residuals))
        return OF


    def MSSoE(self):
        '''
        Mean Sqaured sorted Errors

        Notes
        -------
        The mean square error of sorted errors is calculated based on sorted
        observed and predicted data (van Griensven and Bauwens, 2003).
        Observations and predictions are sorted independently one from the
        other. The sorted series are then compared (comparison of their
        cumulative distributions) and it is evaluated whether the model
        reproduces the same distribution as the observed data.

        The time of occurrence of a given value of the variable is not
        accounted for in the MSSoE method.

        * range: [0, inf]
        * optimum: 0
        * category: Absolute criteria, timestep independent

        References
        -----------
        ..  [E6] van Griensven A. and Bauwens W. (2003) Multiobjective
            autocalibration for semidistributed water quality models. Water
            Resources Research, 39(12), SWC91-SWC99.
        '''
        OF = ((np.sort(self.modelled) - np.sort(self.observed))**2).mean()
        return OF

    def MSDE(self):
        '''
        Mean Square Derivative Error

        Notes
        -------
        The mean square derivative error is the square of the differences
        of predicted and observed variations between two time steps [E5]_.
        This criterion penalizes noisy time series and series with
        timing error; it thus allows evaluating the peak's timing.

        * range: [0, inf]
        * optimum: 0
        * category: Absolute criteria
        '''
        dmod = self.modelled[1:]-self.modelled[:-1]
        dobs = self.observed[1:]-self.observed[:-1]
        OF = ((dobs - dmod)**2).mean()
        return OF

    def RMSE(self):
        '''
        Root Mean Square Error

        Notes
        -------
        The root mean square error is an absolute criterion that is often
        used [4]_. It indicates the overall agreement
        between predicted and observed data. The square allows avoiding
        error compensation and emphasises larger errors. The root provides
        a criterion in actual units. Consequently, this quality criterion
        can be compared to the MAE to provide information on the prominence
        of outliers in the dataset.
        '''
        OF = np.sqrt((self.residuals**2).mean())
        return OF

    def RRMSE(self):
        '''
        Relative Root Mean Square Error

        Notes
        -------
        The relative Root Mean Square Error is the Root Mean Square Error
        devided by the mean of the observations.

        See Also
        ---------
        RMSE
        '''
        OF = np.sqrt((self.residuals**2).mean())/np.mean(self.observed)
        return OF

    def RMSE_log(self, llambda = 0.25):
        '''
        Root Mean Square Error with boxcox trfd values

        Notes
        -------
        The root mean square error is an absolute criterion that is often
        used [4]_. It indicates the overall agreement
        between predicted and observed data. The square allows avoiding
        error compensation and emphasises larger errors. The root provides
        a criterion in actual units. Consequently, this quality criterion
        can be compared to the MAE to provide information on the prominence
        of outliers in the dataset.
        '''

        OF = np.sqrt(((np.log(self.observed)-np.log(self.modelled))**2).mean())
        return OF

    def RMSE_boxcox(self, llambda = 0.25):
        '''
        Root Mean Square Error with boxcox trfd values

        Notes
        -------
        The root mean square error is an absolute criterion that is often
        used [4]_. It indicates the overall agreement
        between predicted and observed data. The square allows avoiding
        error compensation and emphasises larger errors. The root provides
        a criterion in actual units. Consequently, this quality criterion
        can be compared to the MAE to provide information on the prominence
        of outliers in the dataset. Also applied in [E14]_.

        '''
        bobs=(self.observed**llambda -1)/llambda
        bmod=(self.modelled**llambda -1)/llambda

        OF = np.sqrt(((bobs-bmod)**2).mean())
        return OF


    def R4MS4E(self):
        '''
        Root 4 Mean Square 4  Error

        Notes
        -------
        To put even more emphasis on the larger errors, the fourth root mean
        quadruples error is used [E5]_

        See Also
        ---------
        RMSE
        '''
        OF = ((self.residuals**4).mean())**(1./4.)
        return OF


    def SSE(self):
        '''
        Sum of Squared Errors (of prediction)

        Notes
        -------
        * range: [0, inf]
        * optimum: 0
        * category: Absolute criteria
        '''
        OF = sum(self.residuals**2)
        return OF

    def NSC(self):
        '''
        Number of Sign Changes of the residuals

        Notes
        -------
        The number of sign changes,[E1]_, counts the number of times the
        residual (Oi-Pi) sign change. The minimum value is zero and the
        maximum n. A value close to zero indicates a systematic error
        (overestimating or under-estimating model) but a more consistent
        model. A value close to n indicates a random error.

        * range: [0, nsize]
        * optimum: /
        * category: Absolute criteria
        '''
        result = []
        count = 0
        for i, v in enumerate(self.residuals): #0 is accounted as positive!!
            if v < 0 and self.residuals[i-1] >= 0:
                change = True
                count = count+1
            elif v >= 0 and self.residuals[i-1] < 0:
                change = True
                count = count+1
            else:
                change = False
            result.append(change)
        OF=count
        return OF

###########################################################################
#CAT 3: Relative error criteria:
#    Residuals relative to observed values: At each time step, the error is
#    related to the corresponding observed or modelled value. A low value of
#    this criterion means a good agreement between observation and
#    simulation.
###########################################################################

    def MRE(self,optim = False):
        '''
        Mean Relative Error

        Parameters
        -----------
        optim : bool
            if True, the objective is translated to be used in optimizations
            where a minimum value is seeked by the algorithm

        Notes
        -------
        The mean relative error [E5]_ provide the average relative model
        error. However, negative and positive errors can compensate for
        each other.

        * range: [-inf, inf]
        * optimum: 0
        * category: Relative criteria
        '''
        OF = (self.residuals/self.observed).mean()

        if optim == True:
            OF = np.abs(OF)

        return OF

    def MPE(self,optim = False):
        '''
        Mean Percent Error

        Parameters
        -----------
        optim : bool
            if True, the objective is translated to be used in optimizations
            where a minimum value is seeked by the algorithm

        Notes
        -------
        The mean percent error [E3]_ provide the average relative model
        error. However, negative and positive errors can compensate for
        each other.

        * range: [-inf, inf]
        * optimum: 0
        * category: Relative criteria

        See Also
        ---------
        MRE
        '''
        OF = 100. *(self.residuals/self.observed).mean()

        if optim == True:
            OF = np.abs(OF)

        return OF

    def MARE(self):
        '''
        Mean Absolute Relative Error

        Notes
        -------
        The mean absolute relative error is similar to the Mean Relative Error,
        but avoids the compensation of errors [E7]_.

        * range: [0, inf]
        * optimum: 0
        * category: Relative criteria

        References
        -----------
        ..  [E7] Petersen B., Gernaey K., Henze M. and Vanrolleghem P.A.
            (2002) Evaluation of an ASM1 model calibration procedure on a
            municipal-industrial wastewater treatment plant. Journal of
            Hydroinformatics, 4(1), 15-38.
        '''
        OF = (np.abs(self.residuals)/self.observed).mean()
        return OF

    def SARE(self):
        '''
        Sum of Absolute Relative Error

        Notes
        --------

        * range: [0, inf]
        * optimum: 0
        * category: Relative criteria

        '''

        OF = (np.abs(self.residuals)/self.observed).sum()
        return OF

    def MeAPE(self):
        '''
        Median Absolute Percent Error

        Notes
        -------
        Median of the absolute relative error expressed in percentage [E5]_.
        This criterion is less affected by outliers and the errors
        distribution form as the MARE criterion.

        * range: [0, inf]
        * optimum: 0
        * category: Relative criteria

        '''
        OF = np.median((np.abs(self.residuals)*100./self.observed))
        return OF

    def MSRE(self):
        '''
        Mean Square Relative Error

        Notes
        -------
        The mean square relative error avoids compensation of errors and
        emphasises larger relative errors [E5]_.

        * range: [0, inf]
        * optimum: 0
        * category: Relative criteria

        '''
        OF = ((self.residuals/self.observed)**2).mean()
        return OF

    def MAPE(self):
        '''
        Mean Absolute Percent Error

        Notes
        -------
        The mean absolute percent error used by [E3]_  is close to MARE.
        However, the errors are relative to the predicted values instead
        of the observed values. Consequently, the under-predicted values
        are penalised (for a similar error). This is an interesting criterion
        for situations in which one wants to determine a risk to reach
        concentration limits.

        * range: [0, inf]
        * optimum: 0
        * category: Relative criteria

        '''
        OF = 100. * (np.abs(self.residuals)/(np.abs(self.modelled))).mean()
        return OF

###########################################################################
#CAT 4: Total residuals relative to total observed values:
#    For the following criteria, the sum of errors is related to the sum of
#    observed values, without any correspondence in time step. A low value of
#    this criterion means a good agreement between observation and simulation.
###########################################################################

    def PBIAS(self, optim = False):
        '''
        Percent Bias

        Parameters
        -----------
        optim : bool
            if True, the objective is translated to be used in optimizations
            where a minimum value is seeked by the algorithm

        Notes
        -------
        The percent bias [E5]_ and relative volume error are the sum of
        errors related to the sum of observed values, expressed as
        relative value or in percentage. This criterion measures an overall
        adequacy, but the errors can be compensated.

        (Also known as DEVRV,  the Deviation of runoff volumes, From
        Statistical evaluation of WATFLOOD, Angela MacLean, University of
        Waterloo)

        * range: [-inf, inf]
        * optimum: 0
        * category: Total Relative error criteria

        '''
        OF = 100. * (np.sum(self.residuals)/np.sum(self.observed))

        if optim == True:
            OF = np.abs(OF)

        return OF

    def APBIAS(self):
        '''
        Absolute Percent Bias

        Notes
        -------
        Useful in combi with PBIAS, eg if PBIAS small and APB very large one
        could conclude that volumes are ok, but timing is missing
        (continuous gap)

        * range: [0, inf]
        * optimum: 0
        * category: Total Relative error criteria

        '''
        OF = 100. * (np.sum(np.abs(self.residuals))/np.sum(self.observed))

        return OF

    def APB(self):
        #Calculate the Absolute Percent Bias (APB, %); in combi with DEVRV: eg if Dv small and APB very large one could conclude that volumes are ok, but timing is missing (continuous gap)
        #From Statistical evaluation of WATFLOOD (Angela MacLean, University of Waterloo)
        objStat = sum(np.abs(self.Err))*100/sum(self.Meas)
        return objStat

    def BIAS(self, optim = False):
        '''
        Bias E[obs-mod]

        Parameters
        -----------
        optim : bool
            if True, the objective is translated to be used in optimizations
            where a minimum value is seeked by the algorithm

        Notes
        -------
        * range: [-inf, inf]
        * optimum: 0
        * category: Total Relative error criteria
        '''
        OF=np.mean(self.residuals)

        if optim == True:
            OF = np.abs(OF)

        return OF


    def RVE(self):
        '''
        Relative Volume Error

        Notes
        -------
        The Relative volume error are the sum of errors related to the sum of
        observed values, expressed as relative value or in percentage.
        This criterion measures an overall adequacy, but the errors can be
        compensated

        * range: [-inf, inf]
        * optimum: 0
        * category: Total Relative error criteria

        '''
        OF = np.sum(self.residuals)/np.sum(self.observed)
        return OF

    def RMAE(self):
        '''
        Relative Mean Absolute Error

        Notes
        -------
        The relative mean absolute error is the sum of absolute errors related
        to the sum of observed data [E8]_. The difference with the PBIAS and
        RVE is that errors are not compensated.

        * range: [0, inf]
        * optimum: 0
        * category: Total Relative error criteria

        References
        -----------
        ..  [E8] Elliott J.A., Irish A.E., Reynolds C.S. and Tett P. (2000)
            Modelling freshwater phytoplankton communities: an exercise
            in validation. Ecological Modelling, 128(1), 19-26.
        '''
        OF = np.sum(np.abs(self.residuals))/np.sum(self.observed)
        return OF

    def ThInC(self):
        '''
        Theils Inequality Coefficient

        Notes
        -------
        Theil's inequality coefficient used by [E3]_ and [E8]_ is the mean
        square error divided by the sum of observed data. This criterion
        avoids error compensation and emphasises larger errors.

        * range: [0, inf]
        * optimum: 0
        * category: Total Relative error criteria

        '''
        OF = np.sum(np.abs(self.residuals))**2/np.sum(self.observed)**2
        return OF

###########################################################################
#CAT 5: Agreement between distributional statistics of observed and modelled data:
#    These criteria are not based on error comparison, but on a comparison
#    between cumulative modelled and observed data. These criteria originate
#    from hydrology and aim at verifying whether the total water volume has
#    been reproduced by summing the flows. In the wastewater field these
#    criteria can be relevant for influent and effluent pollutant loads by
#    summing the fluxes.
###########################################################################

    def TMC(self):
        '''
        Totel Mass Controller

        Notes
        ------
        [E6]_ use the Total Mass Controller criterion as an objective
        function. This criterion compares the cumulative predicted and
        observed values

        * range: [0, inf]
        * optimum: 0
        * category: Total Relative error criteria

        '''
        OF = 100. * np.abs((np.sum(self.observed)/np.sum(self.modelled))-1.)
        return OF

    def CrBal(self, optim = False):
        '''
        Balance Criterion

        Parameters
        -----------
        optim : bool
            if True, the objective is translated to be used in optimizations
            where a minimum value is seeked by the algorithm (1- CrBal)

        Notes
        ------
        [E9]_ use the balance criterion to measure the ability of the model
        to reproduce the same cumulative as observed. The difference between
        the inversed fractions penalises larger differences between
        observed and modelled cumulative values.

        * range: [-inf, 1]
        * optimum: 1
        * category: Total Relative error criteria

        Reference
        ------------
        ..  [E9] Perrin C., Andréassian V. and Michel C. (2006) Simple
            benchmark models as a basis for model efficiency criteria. Large
            Rivers, 17(Arch. Hydrobiol. Suppl. 161/1-2), 221-244.
        '''
        p1 = np.sqrt(self.modelled.sum()/self.observed.sum())
        p2 = np.sqrt(self.observed.sum()/self.modelled.sum())
        OF = 1. - np.abs(p1-p2)

        if optim == True:
            OF = 1. - OF

        return OF

###########################################################################
#CAT 6: Comparison of residuals with reference values and with other models:
#    These criteria compare the residuals with residuals obtained with a
#    reference model, such as a model describing the mean value or the
#    previous value
###########################################################################

    def NSE(self, optim = False):
        '''
        Nash-Sutcliffe Efficiency criterion

        Parameters
        -----------
        optim : bool
            if True, the objective is translated to be used in optimizations
            where a minimum value is seeked by the algorithm

        Notes
        --------
        Widely used criterion in hydrology, values ranging from -infty -> 1
        A zero value means the model is not better than the 'no knowledge'
        model, which is characterised by the mean of the observations.
        Sensitive to extreme values.

        * range: [-inf, 1]
        * optimum: 1
        * category: comparison with reference model

        '''
        nom = np.sum((self.residuals)**2)
        den = np.sum((self.observed - self.observed.mean())**2)
        OF = 1. - nom/den

        if optim == True:
            OF = 1. - OF

        return OF

    def NSE_sqrt(self, optim = False):
        '''
        Nash-Sutcliffe Efficiency criterion with root values

        Parameters
        -----------
        optim : bool
            if True, the objective is translated to be used in optimizations
            where a minimum value is seeked by the algorithm

        Notes
        --------
        Widely used criterion in hydrology, values ranging from -infty -> 1
        A zero value means the model is not better than the 'no knowledge'
        model, which is characterised by the mean of the observations.
        The root values of the observed and measured values are used to
        give more emphasis to the lower values

        * range: [-inf, 1]
        * optimum: 1
        * category: comparison with reference model

        '''
        nom = np.sum((np.sqrt(self.observed)-np.sqrt(self.modelled))**2)
        den = np.sum((np.sqrt(self.observed) - np.sqrt(self.observed).mean())**2)
        OF = 1. - nom/den

        if optim == True:
            OF = 1. - OF

        return OF

    def NSE_log(self, optim = False):
        '''
        Nash-Sutcliffe Efficiency criterion with logarithmic values

        Parameters
        -----------
        optim : bool
            if True, the objective is translated to be used in optimizations
            where a minimum value is seeked by the algorithm

        Notes
        --------
        Widely used criterion in hydrology, values ranging from -infty -> 1
        A zero value means the model is not better than the 'no knowledge'
        model, which is characterised by the mean of the observations.
        The log values of the observed and measured values are used to
        give more emphasis to the lower values

        * range: [-inf, 1]
        * optimum: 1
        * category: comparison with reference model

        '''
        nom = np.sum((np.log(self.observed)-np.log(self.modelled))**2)
        den = np.sum((np.log(self.observed) - np.log(self.observed).mean())**2)
        OF = 1. - nom/den

        if optim == True:
            OF = 1. - OF

        return OF

    def NSE_boxcox(self, optim = False, llambda = 0.25):
        '''
        Nash-Sutcliffe Efficiency criterion with boxcox transformed values

        Parameters
        -----------
        optim : bool
            if True, the objective is translated to be used in optimizations
            where a minimum value is seeked by the algorithm

        Notes
        --------
        Widely used criterion in hydrology, values ranging from -infty -> 1
        A zero value means the model is not better than the 'no knowledge'
        model, which is characterised by the mean of the observations.

        Model residuals typically increase with higher flowvalues. This
        means that themodel residual variance or standard deviation typically
        increases with increasing flow. It also means that the higher flow
        values receive more weight in the goodness-of-fit statistics, [E10]_.

        * range: [-inf, 1]
        * optimum: 1
        * category: comparison with reference model

        References
        --------------
        ..  [E10] Willems, P. A Time Series Tool to Support the
            Multi-criteria Performance Evaluation of Rainfall-runoff
            Models. Environmental Modelling & Software 24, no. 3 (March 2009):
            311–321.
            http://linkinghub.elsevier.com/retrieve/pii/S1364815208001606.

        '''

        bobs=(self.observed**llambda -1)/llambda
        bmod=(self.modelled**llambda -1)/llambda

        nom = np.sum((bobs-bmod)**2)
        den = np.sum((bobs - bobs.mean())**2)
        OF = 1. - nom/den

        if optim == True:
            OF = 1. - OF

        return OF

    def RAE(self):
        '''
        Relative Absolute Error

        Notes
        ----------
        The RAE compares the sum of the absolute residuals to the residuals
        of the no knowledge model (mean of observed values, [E11]_. This
        criterion does not allow error compensation.

        * range: [0, inf]
        * optimum: 0
        * category: comparison with reference model

        References
        ------------
        ..  [E11] Legates D.R. and McCabe G.J. (1999) Evaluating the use of
            'goodness-of-fit' measures in hydrologic and hydroclimatic
            model validation. Water Resources Research, 35(1), 233-241

        '''
        nom = np.sum(np.abs(self.residuals))
        den = np.sum(np.abs(self.observed - self.observed.mean()))
        OF = nom/den

        return OF

    def RSR(self):
        '''
        RMSE-observation standard deviation ratio

        Notes
        ----------
        The RMSE-observation standard deviation ratio is the RMSE of the
        predicted data divided by the RMSE of the no knowledge model
        (mean of observed values), [E12]_. It is a scaled criterion that
        emphasises larger errors and can be, as for MAE and RMSE, compared
        to the RAE to indicate the influence of larger errors.

        * range: [0, inf]
        * optimum: 0
        * category: comparison with reference model

        References
        ------------
        ..  [E12] Moriasi D.N., Arnold J.G., Van Liew M.W., Bingner R.L.,
            Harmel R.D. and Veith T.L. (2007) Model evaluation guidelines
            for systematic quantification of accuracy in watershed
            simulations. Transactions of the ASABE, 50(3), 885-900

        '''
        nom = np.sqrt(np.sum((self.residuals)**2))
        den = np.sqrt(np.sum((self.observed - self.observed.mean())**2))
        OF = nom/den

        return OF

    def IA(self, optim = False):
        '''
        Index of agreement

        Parameters
        -----------
        optim : bool
            if True, the objective is translated to be used in optimizations
            where a minimum value is seeked by the algorithm

        Notes
        ----------
        Index of agreement is te ratio of the sum of squared errors (SSE)
        and the largest potential error with respect to the mean of the
        observed values, [E4]_. This is sensitive to the model mean and to
        the peak values, and is insensitive to low magnitude values.

        * range: [0, 1]
        * optimum: 1
        * category: comparison with reference model

        '''
        nom = np.sqrt(np.sum((self.residuals)**2))
        den = np.sqrt(np.sum((self.observed - self.observed.mean())**2))
        OF = nom/den

        if optim == True:
            OF = 1. - OF

        return OF

    def PI(self, optim = False):
        '''
        Coefficient of Persistance

        Parameters
        -----------
        optim : bool
            if True, the objective is translated to be used in optimizations
            where a minimum value is seeked by the algorithm

        Notes
        --------
        The coefficient of persistence is close tot the NSE criterion, but the
        simplistic model used is th elast observed value instead of the
        mean of observed values, [E12]_.

        * range: [0, 1]
        * optimum: 1
        * category: comparison with reference model

        '''
        dobs = self.observed[1:]-self.observed[:-1]

        nom = np.sum((self.residuals)**2)
        den = np.sum((dobs)**2)
        OF = 1. - nom/den

        if optim == True:
            OF = 1. - OF

        return OF

    def RCOEF(self, optim = False):
        '''
        Correlation coefficient

        Parameters
        -----------
        optim : bool
            if True, the objective is translated to be used in optimizations
            where a minimum value is seeked by the algorithm

        Notes
        ------
        Used to describe how well a regression line fits a set of data,
        compares variability in observed and modelled values. In general not
        the best criteria to check model performance,
        see more details in [E11]_.

        * range: [0, 1]
        * optimum: 1
        * category: comparison with reference model

        '''

        OF=np.corrcoef(self.observed,self.modelled)

        if optim == True:
            OF[0,1] = 1. - OF[0,1]

        return OF[0,1]

###########################################################################
#CAT 7: Others
###########################################################################

    def RFLAUT(self, theta = 1, method = 'biomath'):
        '''
        First (or higher) lag autocorrelation, higher values of theta gives
        the higher value

        Parameters
        -----------
        theta : int
            lag to calculate
        method : biomath|gupta|anders
            method to calculate the correlation

        Notes
        --------
        Calculates the first lag of the autocorrelation of the residuals,
        according to the version proposed by [E1]_ when method 'gupta1998'
        is chosen. Default is the biomath version, as proposed by Gujer, 2008
        and more information is given in [E12]_

        * range: [0, 1]
        * optimum: 0
        * category: others

        References
        ------------
        ..  [E13] Cierkens, Katrijn. Investigating Bioprocess Model Output
        Uncertainty as Function of Input Data Quantity and Model Structure.
        Ghent University, 2010.
        '''
        if method == 'gupta':
            nom = (self.residuals[:-theta]*self.residuals[theta:]).mean()
            den = np.std(self.observed)*np.std(self.modelled)
            OF = nom/den
        elif method == 'biomath':
            r0 = (self.residuals**2).mean()
            OF = (1./r0)*(self.residuals[:-theta]*self.residuals[theta:]).mean()
        else:
            nom = ((self.residuals[:-theta]-self.residuals.mean())*(self.residuals[theta:]-self.residuals.mean())).sum()
            den = np.sum((self.residuals-self.residuals.mean())**2)
            OF = nom/den
        return OF

    def SFDCE(self):
        '''
        Slope of the flow duration curve error

        Notes
        -------
        Based on the FDC, measures how well the model captures the
        distribution of mid-level flow. The slope of a watershed's flow
        duration curve indicates the variability, or flashiness, of its
        flow magnitudes. The SFDCE metric is thus simply the absolute
        error in the slope of the flow duration curve between the 30
        and 70 percentile flows.

        References
        ------------
        ..  [E14] van Werkhoven, Kathryn, Thorsten Wagener, Patrick Reed,
            and Yong Tang. Sensitivity-guided Reduction of Parametric
            Dimensionality for Multi-objective Calibration of Watershed
            Models. Advances in Water Resources 32, no. 8 (2009): 1154–1169.
            http://dx.doi.org/10.1016/j.advwatres.2009.03.002.

        '''
        QMeas30=stats.scoreatpercentile(self.observed, 30.)
        QMeas70=stats.scoreatpercentile(self.observed, 70.)

        QMod30=stats.scoreatpercentile(self.modelled, 30.)
        QMod70=stats.scoreatpercentile(self.modelled, 70.)

        objStat = abs((QMod70-QMod30)/40-(QMeas70-QMeas30)/40)
        return objStat

    def LowFDCE(self):
        '''
        Flow Duration Curve based low flow criterion

        Notes
        -------
        Uses the lower part (highest percentiles) of the Flow Duration Curve
        to focus on low flow regimes. Always use in combination with a
        second criterion to make sure the timing of the model is also
        satifying. Used in [E15]_.

        Reference
        ------------
        Van Hoey S., van der Kwast J., Seuntjens P., Pereira F., Nopens I.
        (2012). Model structure identification based on ensemble model
        evaluation for the prediction of low and high flows in rivers,
        Water Resources Research, in review

        '''
        EP,EPMeas,EPModel = FindEPs(self.observed,self.modelled, valnum = 30,
                                    qvalmin=30.0, qvalmax=100.0)
        OF = np.sum((np.log(EPMeas)-np.log(EPModel))**2)
        return OF

    def HighFDCE(self):
        '''
        Flow Duration Curve based high flow criterion

        Notes
        -------
        Uses the upper part (lowest percentiles) of the Flow Duration Curve
        to focus on high flow regimes. Always use in combination with a
        second criterion to make sure the timing of the model is also
        satifying. Used in [E15]_.

        Reference
        ------------
        ..  [E15] Van Hoey S., van der Kwast J., Seuntjens P., Pereira F.,
            Nopens I. (2012). Model structure identification based on ensemble
            model evaluation for the prediction of low and high flows in
            rivers, Water Resources Research, in review

        '''

        EP,EPMeas,EPModel = FindEPs(self.observed, self.modelled,
                                    valnum=30, qvalmin=0.0, qvalmax=70.0)
        objStat = sum((EPMeas-EPModel)**2)
        return objStat




###########################################################################
#CAT 8: Combined criteria
#   combination can be made from the different values, but those listed here
#   do have specific relevance in model evaluation
###########################################################################

    def NSE_BIAS(self):     #Popular on the MODSIM2011 conference NSE-5(ln(1+Bias)^2.5)
        '''
        Combination of Nash Sutcliff and BIAS

        Notes
        -------
        The criterium is gaining importance by the combined effect and is
        proposed in [E16]_. Here an adaptation is implemented by taking the
        absolute value of the bias, to make the function symmetrical around
        the optimal value.


        References
        ------------
        ..  [E16] Viney, N.R., J. Perraud, J. Vaze F.H.S. Chiew, D.A. Post
            and A. Yang (2009b).  The usefulness of bias constraints in model
            calibration for regionalisation to ungauged catchments.
            Proceedings, MODSIM 200
        '''
        OF = self.NSE()- 5*(np.abs(np.log(1.0 + np.abs(self.BIAS()))))**2.5
        return OF

    def NSE_FDClow(self,w1=1.,w2=1.):
        '''
        Nash Sutcliffe (mod) + low Flow; zelfde gewichtsfactor,
        als fout groter, ook beide groter!

        Parameters
        ------------
        w1 : float (0-1)
            weighting factor 1, NSE
        w2 : float (0-1)
            weighting factor 2, FDC
        '''
        DMS = (self.residuals**2).mean()
        MMS = ((self.observed-np.mean(self.observed))**2).mean()
        objStat1=(DMS)/(MMS)

        EP,EPMeas,EPModel = FindEPs(self.observed,self.modelled, valnum=30,
                                    qvalmin=30.0, qvalmax=100.0)
        DMS2 = (sum((np.log(EPMeas)-np.log(EPModel))**2)/EPMeas.size)
        MMS2 = (sum((EPMeas-np.mean(EPMeas))**2)/EPMeas.size)
        objStat2 = (DMS2)/(MMS2)

        objStat = w1*objStat1 + w2*objStat2
        return objStat

    def NSE_FDChigh(self,w1=1.,w2=1.):
        '''
        Nash Sutcliff (mod) + high Flow; zelfde gewichtsfactor: als fout groter, ook beide groter!

        Parameters
        ------------
        w1 : float (0-1)
            weighting factor 1, NSE
        w2 : float (0-1)
            weighting factor 2, FDC
        '''
        DMS = (self.residuals**2).mean()
        MMS = ((self.observed-np.mean(self.observed))**2).mean()
        objStat1=(DMS)/(MMS)

        EP,EPMeas,EPModel = FindEPs(self.observed,self.modelled,valnum=30,qvalmin=0.0,qvalmax=70.0)
        DMS2 = (sum((EPMeas-EPModel)**2)/EPMeas.size)
        MMS2 = (sum((EPMeas-np.mean(EPMeas))**2)/EPMeas.size)
        objStat2 = (DMS2)/(MMS2)

        objStat = w1*objStat1 + w2*objStat2
        return objStat


###########################################################################
#FIGURES
###########################################################################

    def check_boxcox(self, llambda):
        '''
        Function to evaluate the effect of the box cox transformation
        applied on the data, cfr. WETSPRO tool, hydromad application

        '''
        pass

###observed data
#obsreal = np.loadtxt(os.path.join('D:\Projecten\WL\VHM\Data','Flow_Cal_Meas_13aug02_31dec05'))[:10000]
##Modres Thomas
#modreal = np.loadtxt(os.path.join('D:\Projecten\WL\VHM\Data','Modres_thomas_NAM_Cal_13aug_31dec05'))[:10000]
#of = Evaluation(obsreal,modreal)


#depreciated function: use stats.scoreatpercentile
def FDC_quantile(FlowSerie,qval=30.0):
    #Give the y-value (Flow) for a certain percentile value
    y2=np.sort(FlowSerie)
    y=y2[::-1]
    z=np.arange(0.0,y.size,1.0)
    p=z*100/(z.size+1)
    ival=np.nonzero(p>qval)[0][0]
    Qival=y.take([ival])
    return Qival

class Likelihood(FlowAnalysis):
    '''
    Class for deriving different Likelihoods,
    Informal Likelihoods -> useful for GLUE and Bayesian based approaches
    all between 0.0 and 1.0

    Todo: log-likelihood translation towards: 
	transformation by: nll = lambda *args: -lnlike(*args)

    References
    --------------
    ..  [E17] Smith, P, K Beven, and J Tawn. Informal likelihood measures in
        model assessment: Theoretic development and investigation. Advances
        in Water Resources 31, no. 8 (August 2008): 1087-1100
    '''

    def __init__(self, observed, modelled):
         FlowAnalysis.__init__(self, observed)

         if not modelled.shape == observed.shape:
             raise Exception('Modelled and observed timeseries need \
                                 to be of the same size')

         self.modelled = modelled
         self.residuals = self.observed - self.modelled
         self.infodict()

         print('Criteria suited for Likihood maximization, use optim=True\
         to use in minimzation exercise; Not adviced to use in automated\
         minimalization algorithms, because of jumps between 0 and none\
         zero values, use the evaluation class instead; use log version instead')

    def infodict(self):
        '''
        Prepares information dictionary
        '''
        self.explainname={}
        #CAT 1
        self.explainname['Inf_NSE'] = 'Nash Sutcliff Likelihood'
        self.explainname['Inf_CM'] = 'Chiew & McMahon'
        self.explainname['Inf_NSSE'] = 'Normalised Sum of Squared Errors'
        self.explainname['IOA'] = 'Index of agreement Likelihood'
        self.explainname['MCE'] = 'Mean cumulative error Likelihood'
        self.explainname['NAE'] = 'Normalised absolute error Likelihood'


    def INF_NSE(self, optim=False):
        '''
        Informal Nash-Sutcliff Measure
        '''
        DMS = np.sum(self.residuals**2)
        MMS = (np.sum((self.observed-np.mean(self.observed))**2))
        Like=max(1.0-(DMS)/(MMS),0.0)

        if optim == True:
            Like = 1. - Like

        return Like

    def INF_CM(self, optim=False):
        '''
        Chiew & McmMahon Likelihood
        '''
        DMS = np.sum((self.observed**0.5-self.modelled**0.5)**2.0)
        MMS = np.sum((self.observed**0.5-(np.mean(self.observed))**0.5)**2)
        Like = max(1.0-(DMS)/(MMS),0.0)

        if optim == True:
            Like = 1. - Like

        return Like

    def INF_NSSE(self, optim=False):
        '''
        Normalised SSE
        '''
        TT = np.sum(self.residuals**2)/(np.mean(self.observed))**2
        Like = max(1.0-TT,0.0)

        if optim == True:
            Like = 1. - Like

        return Like

    def INF_IOA(self, optim=False):
        '''
        Index of agreement Likelihood
        '''
        DMS = np.sum(self.residuals**2)
        MMS = np.sum((np.abs(self.modelled-np.mean(self.observed)) +
                np.abs(self.observed-np.mean(self.observed)))**2)
        Like = 1.-(DMS/MMS)

        if optim == True:
            Like = 1. - Like

        return Like

    def INF_MCE(self, optim=False):
        '''
        Mean cumulative error Likelihood
        '''
        DMS=np.abs(np.mean(self.modelled)-np.mean(self.observed))
        MMS = np.abs(np.mean(self.observed))
        Like=max(1.0-(DMS)/(MMS),0.0)

        if optim == True:
            Like = 1. - Like

        return Like

    def INF_NAE(self, optim=False):
        '''
        Normalised absolute error Likelihood
        '''
        DMS=np.sum(np.abs(self.residuals))
        MMS = np.sum(np.abs(self.observed-np.mean(self.observed)))
        Like=max(1.0-(DMS)/(MMS),0.0)

        if optim == True:
            Like = 1. - Like

        return Like

class evalmodselection(FlowAnalysis):
    '''
    Model Selection Criteria; Punishing the performance with the complexity
    of the model; complexity is here only measured by the number of parameters.

    Parameters
    -----------

    Notes
    --------
    These criteria are actually developed for statistical model development,
    typical regression models and distribution fitting models. The applicability
    on dynamic mathematical models is not always so valid, seen the other
    factors that need to be taken into account for model evaluation. Please use
    the results with care.

    References
    ------------
    ..  [E18] Nopens, Ingmar. Modelleren En Simuleren Van Biosystemen, 2010.
    '''

    def __init__(self, observed, modelled, npar):
         FlowAnalysis.__init__(self, observed)

         if not modelled.shape == observed.shape:
             raise Exception('Modelled and observed timeseries need \
                                 to be of the same size')

         self.modelled = modelled
         self.residuals = self.observed - self.modelled
         self.infodict()
         self.npar = npar

         print('Criteria suited for statistical model structure selection')

    def SSE(self):
        return sum(self.residuals**2)

    def infodict(self):
        '''
        Prepares information dictionary
        '''
        self.explainname={}
        #CAT 1
        self.explainname['AIC'] = 'Akaike information criterion'
        self.explainname['BIC'] = 'Bayesian information criterion'
        self.explainname['LILC'] = 'Law of Iterated Logarithm Criterion'
        self.explainname['FPE'] = 'Final Prediction Error'

    def AIC(self):
        '''
        Calculate the AIC-criterium,
        based on the SSE-algorithm (Phd Brecht Donckels)
        '''

        AIC =self.residuals.size*np.log(self.SSE()/self.residuals.size)+2*self.npar
        #AIC =self.Err.data.size*log(self.SSE/size(self.Err.data))+2*npar
        if self.residuals.size/self.npar > 40:
            objStat = AIC
        else:
            objStat = AIC + 2*self.npar*(self.npar+1)/(self.residuals.size-self.npar-1.)
        return objStat

    def BIC(self):
        '''
        Calculate the BIC-criterium, based on the SSE-algorithm
        (Phd Bracht Verbeke), wel consistent (naar 0 als datptn nr oneindig)
        '''
        objStat =self.residuals.size*np.log(self.SSE()/self.residuals.size)+self.npar*np.log(self.residuals.size)
        return objStat

    def LILC(self):
        '''
        Khinchin's law of Iterated Logarithm Criterion (Modsim_cursus)
        '''
        objStat =self.residuals.size*np.log(self.SSE()/self.residuals.size)+self.npar*np.log(np.log(self.residuals.size))
        return objStat

    def FPE(self):
        '''
        Calculate Final Prediction Error (FPE)  (Modsim_cursus)
        '''
        objStat = (self.SSE()/self.residuals.size)*(1.+(2*self.npar/(self.residuals.size-self.npar)))
        return objStat