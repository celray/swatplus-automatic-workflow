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
from qgis.PyQt.QtCore import Qt
#from PyQt5.QtGui import * # @UnusedWildImport
#from qgis.core import * # @UnusedWildImport
# Import the code for the dialog
from .exemptdialog import ExemptDialog
from .QSWATUtils import ListFuns # type: ignore 

class Exempt:
    """Allow user to define landuses to be exempt from removal as under threshold."""
    def __init__(self, gv):
        """Initialise class variables."""
        self._gv = gv
        self._dlg = ExemptDialog()
        self._dlg.setWindowFlags(self._dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self._dlg.move(self._gv.exemptPos)
        ## landuse codes occurring in landuse map, or used for a split, and not exempt
        self.landuses = []
        ## landuse codes marked for exemption
        self.exemptLanduses = []
      
    def run(self):
        """Run exempt dialog."""
        for landuseVal in self._gv.db.landuseVals:
            landuse = self._gv.db.getLanduseCode(landuseVal)
            ListFuns.insertIntoSortedList(landuse, self.landuses, True)
        for subs in self._gv.splitLanduses.values():
            for landuse in subs.keys():
                ListFuns.insertIntoSortedList(landuse, self.landuses, True)
        for landuse in self._gv.exemptLanduses:
            ListFuns.insertIntoSortedList(landuse, self.exemptLanduses, True)
            # defensive coding
            if landuse in self.landuses:
                self.landuses.remove(landuse)
        self.fillBoxes()
        self._dlg.chooseBox.activated.connect(self.addExempt)
        self._dlg.cancelExemptionButton.clicked.connect(self.delExempt)
        self._dlg.show()
        result = self._dlg.exec_()
        self._gv.exemptPos = self._dlg.pos()
        if result == 1:
            self._gv.exemptLanduses = self.exemptLanduses
        
    def fillBoxes(self):
        """Initialise dialog combo boxes."""
        self._dlg.chooseBox.clear()
        self._dlg.chooseBox.addItems(self.landuses)
        self._dlg.chooseBox.setCurrentIndex(-1)
        self._dlg.exemptBox.clear()
        self._dlg.exemptBox.addItems(self.exemptLanduses)
        
    def addExempt(self):
        """Add an exemption."""
        landuse = self._dlg.chooseBox.currentText()
        # should be present but better safe than sorry
        if landuse in self.landuses:
            self.landuses.remove(landuse)
        ListFuns.insertIntoSortedList(landuse, self.exemptLanduses, True)
        self.fillBoxes()
        
    def delExempt(self):
        """Remove an exemption."""
        if self._dlg.exemptBox.currentItem() is None: return
        landuse = self._dlg.exemptBox.currentItem().text()
        # should be present but better safe than sorry
        if landuse in self.exemptLanduses:
            self.exemptLanduses.remove(landuse)
        ListFuns.insertIntoSortedList(landuse, self.landuses, True)
        self.fillBoxes()
        
