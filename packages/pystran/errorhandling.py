# -*- coding: utf-8 -*-
"""
Created on Sat Oct 19 22:19:33 2013

@author: VHOEYS
"""

##############################################################################
## pySTAN error functions
##############################################################################

class PystanError(Exception):
    """Base class for exceptions in this module."""
    pass

class PystanInputError(PystanError):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class PystanSequenceError(PystanError):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)