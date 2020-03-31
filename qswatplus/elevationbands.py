# -*- coding: utf-8 -*-
'''
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
 *   This program is free software you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
'''
# Import the PyQt and QGIS libraries
from PyQt5.QtCore import * # @UnusedWildImport
from PyQt5.QtGui import * # @UnusedWildImport
from qgis.core import * # @UnusedWildImport
# Import the code for the dialog
from .elevationbandsdialog import ElevatioBandsDialog
from .QSWATUtils import QSWATUtils

class ElevationBands:
    
    """Form and functions for defining elevation bands."""
    
    def __init__(self, gv):
        """Initialise class variables."""
        self._gv = gv
        self._dlg = ElevatioBandsDialog()
        self._dlg.setWindowFlags(self._dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self._dlg.move(self._gv.elevationBandsPos)
        self._dlg.okButton.clicked.connect(self.setBands)
        self._dlg.cancelButton.clicked.connect(self._dlg.close)
        if self._gv.elevBandsThreshold > 0:
            self._dlg.elevBandsThreshold.setText(str(self._gv.elevBandsThreshold))
            if 2 <= self._gv.numElevBands <= 10:
                self._dlg.numElevBands.setValue(self._gv.numElevBands)
        
    def run(self):
        """Run the form."""
        self._dlg.show()
        self._dlg.exec_()
        self._gv.elevationBandsPos = self._dlg.pos()
        
    def setBands(self):
        """Save bands definition."""
        text = self._dlg.elevBandsThreshold.text()
        if text == '':
            # clear elevation bands
            self._gv.elevBandsThreshold = 0
            self._gv.numElevBands = 0
            self._dlg.close()
            return
        try:
            self._gv.elevBandsThreshold = int(text)
        except Exception:
            QSWATUtils.error('Cannot parse threshold {0} as an integer'.format(text), self._gv.isBatch)
            return
        self._gv.numElevBands = self._dlg.numElevBands.value()
        self._dlg.close()
        
