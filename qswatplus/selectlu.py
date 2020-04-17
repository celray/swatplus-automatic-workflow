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
from selectludialog import SelectluDialog

class Selectlu:
    
    """Dialog to select a landuse from a list in listBox."""
    
    def __init__(self, gv):
        """Initialise class variables."""
        self._gv = gv
        self._dlg = SelectluDialog()
        self._dlg.setWindowFlags(self._dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self._dlg.move(self._gv.selectLuPos)
        ## selected landuse
        self._luse = ''
        
    def run(self):
        """Run the dialog and return selected landuse."""
        self._gv.db.populateAllLanduses(self._dlg.listBox, includeWATR=False)
        self._dlg.listBox.currentTextChanged.connect(self.select)
        self._dlg.show()
        result = self._dlg.exec_()
        self._gv.selectLuPos = self._dlg.pos()
        if result == 1:
            return self._luse
        else:
            return ''
        
        
    def select(self, selection):
        """
        A selection has the form 'LUSE (Description)' or 'USE (Description)'.
        This function returns 'LUSE' or 'USE': 
        namely the line up to the space before '('
        """
        length = selection.find('(')
        if length < 0:
            self._luse = selection.strip()
        else:
            self._luse = selection[ : length].strip()
        