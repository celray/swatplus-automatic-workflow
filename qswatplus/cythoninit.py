# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QSWATPlus
                                 A QGIS plugin
 Create SWATPlus inputs
                              -------------------
        begin                : 2014-07-18
        copyright            : (C) 2014 by Chris George
        email                : cgeorge@mcmaster.ca
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 
 Acknowledgement: copied from https://github.com/cython/cython/wiki/InstallingOnWindows
 """
 
import os
import numpy
import pyximport

if os.name == 'nt':
    if 'CPATH' in os.environ:
        os.environ['CPATH'] = os.environ['CPATH'] + ';C:\\PROGRA~1\\QGIS2~1.16\\apps\\Python27\\include;' + numpy.get_include()
    else:
        os.environ['CPATH'] = 'C:\\PROGRA~1\\QGIS2~1.16\\apps\\Python27\\include;' + numpy.get_include()

    # XXX: we're assuming that MinGW is installed in C:\MinGW (default)
    if 'PATH' in os.environ:
        os.environ['PATH'] = os.environ['PATH'] + ';C:/MinGW/bin'
    else:
        os.environ['PATH'] = 'C:/MinGW/bin'

    mingw_setup_args = { 'options': { 'build_ext': { 'compiler': 'mingw32' } } }
    pyximport.install(setup_args=mingw_setup_args)

elif os.name == 'posix':
    if 'CFLAGS' in os.environ:
        os.environ['CFLAGS'] = os.environ['CFLAGS'] + ' -I' + numpy.get_include()
    else:
        os.environ['CFLAGS'] = ' -I' + numpy.get_include()

    pyximport.install()