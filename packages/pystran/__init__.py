# -*- coding: utf-8 -*-
"""
@author: Stijn Van Hoey

pySTAN: python STRucture ANalyst
"""

import numpy as np

import matplotlib
matplotlib.use('agg')

import matplotlib.pyplot as plt

from .evaluationfunctions import Evaluation, Likelihood

from .sensitivity_base import SensitivityAnalysis
from .sensitivity_dynamic import DynamicSensitivity
from .sensitivity_globaloat import GlobalOATSensitivity
from .sensitivity_morris import MorrisScreening
from .sensitivity_regression import SRCSensitivity
from .sensitivity_sobol import SobolVariance
from .sensitivity_rsa import RegionalSensitivity

__version__ = "0.0.2"


if __name__ == '__main__':
    print('pySTAN: python STRucture ANalyst (Van Hoey S. 2012)')
