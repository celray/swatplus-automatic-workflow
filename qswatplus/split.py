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
from PyQt5.QtWidgets import * # @UnusedWildImport
from qgis.core import * # @UnusedWildImport
# Import the code for the dialog
from splitdialog import SplitDialog
from selectlu import Selectlu
from QSWATUtils import QSWATUtils

class Split:
    
    """Dialog and methods for defining split landuses."""
    
    def __init__(self, gv):
        """Initialise class variables."""
        self._gv = gv
        self._dlg = SplitDialog()
        self._dlg.setWindowFlags(self._dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self._dlg.move(self._gv.splitPos)
        self._splitLanduses = dict()
        
    def run(self):
        """Setup and run the dialog."""
        self._dlg.table.setColumnWidth(0, 55)
        self._dlg.table.setColumnWidth(1, 75)
        self._dlg.table.setColumnWidth(2, 50)
        self._dlg.table.setHorizontalHeaderLabels(['Landuse', 'Sub-landuse', 'Percent'])
        self._dlg.addButton.clicked.connect(self.add)
        self._dlg.deleteButton.clicked.connect(self.deleteRow)
        self._dlg.deleteSplitButton.clicked.connect(self.deleteSplit)
        self._dlg.cancelEditButton.clicked.connect(self.cancelEdit)
        self._dlg.saveEditButton.clicked.connect(self.saveEdit)
        self._dlg.saveSplitsButton.clicked.connect(self.saveSplits)
        self._dlg.cancelButton.clicked.connect(self.cancel)
        self.populateCombos()
        self._dlg.newCombo.setCurrentIndex(-1)
        self._dlg.splitCombo.setCurrentIndex(-1)
        self._dlg.newCombo.activated.connect(self.addNew)
        self._dlg.splitCombo.activated.connect(self.selectSplit)
        self._dlg.show()
        self._dlg.exec_()
        self._gv.splitPos = self._dlg.pos()
        
    def add(self):
        """Add a new sub-landuse to the table."""
        if self._dlg.table.rowCount() < 1: return
        self.addSplitRow(self._dlg.table.item(0, 0).text())
        
    def addSplitRow(self, luse):
        """Add a new row to the table."""
        slu = Selectlu(self._gv)
        subluse = slu.run()
        if subluse == '':
            return
        for i in range(self._dlg.table.rowCount()):
            if self._dlg.table.item(i, 1).text() == subluse:
                QSWATUtils.information('Sub-landuse {0} already used in this split'.format(subluse), self._gv.isBatch)
                return
        self.addSplitItems(luse, subluse, 100)
        
    def addSplitItems(self, luse, subluse, percent):
        """Populate last row items."""
        numRows = self._dlg.table.rowCount()
        luse1 = luse if numRows == 0 else ''
        self._dlg.table.insertRow(numRows)
        self._dlg.table.setItem(numRows, 0, QTableWidgetItem(luse1, QTableWidgetItem.Type))
        self._dlg.table.setItem(numRows, 1, QTableWidgetItem(subluse, QTableWidgetItem.Type))
        self._dlg.table.setItem(numRows, 2, QTableWidgetItem(str(percent), QTableWidgetItem.Type))
    
    def deleteRow(self):
        """Delete selected row from the table."""
        row = self._dlg.table.currentRow()
        numRows = self._dlg.table.rowCount()
        if row < 0 or row >= numRows:
            QSWATUtils.information('Please select a row to delete', self._gv.isBatch)
            return
        if row == 0:
            if numRows == 1:
                # whole split will be deleted
                self.deleteSplit()
            else:
                # need to copy luse being split into second row
                luse = self._dlg.table.item(0, 0).text()
                self._dlg.table.setItem(1, 0, QTableWidgetItem(luse, QTableWidgetItem.Type))
        self._dlg.table.removeRow(row)
        # leaves currentRow set, so make current row negative
        self._dlg.table.setCurrentCell(-1, 0)
            
    def deleteSplit(self):
        """Delete a split landuse."""
        count = self._dlg.table.rowCount()
        if count < 1:
            QSWATUtils.information('No split to delete', self._gv.isBatch)
            return
        luse = self._dlg.table.item(0, 0).text()
        self.clearTable()
        self.addItemToCombo(luse, self._dlg.newCombo)
        self.removeItemFromCombo(luse, self._dlg.splitCombo)
        self._dlg.newCombo.setCurrentIndex(-1)
        self._dlg.splitCombo.setCurrentIndex(-1)
        if luse in self._splitLanduses:
            del self._splitLanduses[luse]
    
    def cancelEdit(self):
        """Clear the table."""
        self.clearTable()
        self._dlg.newCombo.setCurrentIndex(-1)
        self._dlg.splitCombo.setCurrentIndex(-1)
    
    def saveEdit(self):
        """Check the percentages sum to 100, save the data in the table,
        and clear it.  Return True if OK
        """
        numRows = self._dlg.table.rowCount()
        if numRows == 0:
            return True
        # check total percentages
        totalPercent = 0
        try:
            for row in range(numRows):
                totalPercent += int(self._dlg.table.item(row, 2).text())
        except Exception:
            QSWATUtils.error('Cannot parse percentages as integers', self._gv.isBatch)
            return False
        if totalPercent != 100:
            QSWATUtils.error('Percentages must sum to 100', self._gv.isBatch)
            return False
        luse = self._dlg.table.item(0, 0).text()
        self._splitLanduses[luse] = dict()
        for row in range(numRows):
            subluse = self._dlg.table.item(row, 1).text()
            percent = int(self._dlg.table.item(row, 2).text())
            self._splitLanduses[luse][subluse] = percent
        self.addItemToCombo(luse, self._dlg.splitCombo)
        self.removeItemFromCombo(luse, self._dlg.newCombo)
        self._dlg.newCombo.setCurrentIndex(-1)
        self._dlg.splitCombo.setCurrentIndex(-1)
        self.clearTable()
        return True
        
    def cancel(self):
        """Close the dialog."""
        self._dlg.close()
    
    def saveSplits(self):
        """Save the split landuses data and close the table."""
        if self._dlg.table.rowCount() > 0:
            result = QSWATUtils.question('Save split currently in table?', self._gv.isBatch, True)
            if result == QMessageBox.Yes:
                if not self.saveEdit():
                    return
            else:
                self.clearTable()
        # copy data to globals
        # clear globals first
        self._gv.splitLanduses.clear()
        for luse, subs in self._splitLanduses.items():
            self._gv.splitLanduses[luse] = dict()
            for subluse, percent in subs.items():
                self._gv.splitLanduses[luse][subluse] = percent
        self._dlg.close()
    
    def addNew(self):
        """Start a new landuse split."""
        if self._dlg.table.rowCount() > 0:
            result = QSWATUtils.question('Save split currently in table?', self._gv.isBatch, True)
            if result == QMessageBox.Yes:
                self.saveEdit()
            else:
                self.clearTable()
        self._dlg.splitCombo.setCurrentIndex(-1)
        self.addSplitRow(self._dlg.newCombo.currentText())
    
    def selectSplit(self):
        """Populate the table with an existing split to be edited."""
        luse = self._dlg.splitCombo.currentText()
        if self._dlg.table.rowCount() > 0 and self._dlg.table.item(0, 0).text() != luse:
            result = QSWATUtils.question('Save split currently in table?', self._gv.isBatch, True)
            if result == QMessageBox.Yes:
                self.saveEdit()
            else:
                self.clearTable()
        for subluse, percent in self._splitLanduses[luse].items():
            self.addSplitItems(luse, subluse, percent)
        self._dlg.splitCombo.setCurrentIndex(-1)
    
    def populateCombos(self):
        """Populate the combo boxes from global data."""
        self._gv.db.populateMapLanduses(self._gv.db.landuseVals, self._dlg.newCombo, includeWATR=False)
        self._gv.populateSplitLanduses(self._dlg.splitCombo)
        for i in range(self._dlg.splitCombo.count()):
            luse = self._dlg.splitCombo.itemText(i)
            j = self._dlg.newCombo.findText(luse)
            if j >= 0:
                self._dlg.newCombo.removeItem(j)
        # copy any data from globals
        for luse, subs in self._gv.splitLanduses.items():
            self._splitLanduses[luse] = dict()
            for subluse, percent in subs.items():
                self._splitLanduses[luse][subluse] = percent
               
    def clearTable(self):
        """Clear the table."""
        self._dlg.table.clearContents()
        self._dlg.table.setRowCount(0)
        
    @staticmethod 
    def addItemToCombo(txt, combo):
        """Add an item to a combo if not already present."""
        index = combo.findText(txt)
        if index < 0:
            combo.addItem(txt)
            
    @staticmethod
    def removeItemFromCombo(txt, combo):
        """Remove an item from a combo, or do nothing if not present."""
        index = combo.findText(txt)
        if index >= 0:
            combo.removeItem(index)
        
