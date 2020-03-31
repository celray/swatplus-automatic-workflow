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
import webbrowser

# Import the code for the dialog
from .aboutdialog import aboutDialog
from .QSWATUtils import QSWATUtils
from .globals import GlobalVars

class AboutQSWAT:
    
    """Provide basic information about QSWAT, including version, and link to SWAT website."""
    
    def __init__(self, gv: GlobalVars) -> None:
        """Initialise."""
        self._gv = gv
        self._dlg = aboutDialog()
        self._dlg.setWindowFlags(self._dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        if self._gv:
            self._dlg.move(self._gv.aboutPos)
        
    def run(self, version: str) -> None:
        """Run the form."""
        self._dlg.SWATHomeButton.clicked.connect(self.openSWATUrl)
        self._dlg.closeButton.clicked.connect(self._dlg.close)
        text = """
{0} version: {1}

Minimum QGIS version: 3.0

Python version: 3.7

Current restrictions:
- Windows and Linux only
        """.format(QSWATUtils._QSWATNAME, version)
        self._dlg.textBrowser.setText(text)
        self._dlg.exec_()
        if self._gv:
            self._gv.aboutPos = self._dlg.pos()
        
    def openSWATUrl(self) -> None:
        """OPen SWAT website."""
        webbrowser.open('http://swat.tamu.edu/')
        
        