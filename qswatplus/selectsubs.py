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
from qgis.PyQt.QtGui import QDoubleValidator
#from qgis.PyQt.QtGui import * # @UnusedWildImport
#from qgis.core import * # @UnusedWildImport
import locale
# Import the code for the dialog
from .selectsubsdialog import SelectSubbasinsDialog
from .QSWATUtils import QSWATUtils # type: ignore 
from .parameters import Parameters

class SelectSubbasins:
    
    """Dialog to select subbasins."""
    
    def __init__(self, gv, subbasinsLayer):
        """Initialise class variables."""
        self._gv = gv
        self._dlg = SelectSubbasinsDialog()
        self._dlg.setWindowFlags(self._dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self._dlg.move(self._gv.selectSubsPos)
        ## Subbasins layer
        self.subbasinsLayer = subbasinsLayer
        ## Index of AREA field in watershed layer
        self.areaIndx = self._gv.topo.getIndex(subbasinsLayer, Parameters._AREA)
        ## mean area of subbasins in watershed
        self.meanArea = self.layerMeanArea()
        
    def init(self):
        """Set up the dialog."""
        self._dlg.pushButton.clicked.connect(self.selectByThreshold)
        self._dlg.checkBox.stateChanged.connect(self.switchSelectSmall)
        self.subbasinsLayer.selectionChanged.connect(self.setCount)
        self._dlg.saveButton.clicked.connect(self.save)
        self._dlg.cancelButton.clicked.connect(self.cancel)
        self._dlg.checkBox.setChecked(False)
        self._dlg.groupBox.setVisible(False)
        self._dlg.areaButton.setChecked(False)
        self._dlg.percentButton.setChecked(True)
        self._dlg.threshold.setValidator(QDoubleValidator())
        self._dlg.threshold.setText('5')
        
    def run(self):
        """Run the dialog."""
        self.init()
        self._dlg.show()
        self._dlg.exec_()
        self._gv.selectSubsPos = self._dlg.pos()
        
    def switchSelectSmall(self):
        """Set visibility of threshold controls by check box state."""
        self._dlg.groupBox.setVisible(self._dlg.checkBox.isChecked())
            
    def selectByThreshold(self):
        """Select subbasins below the threshold, interpreted as area or percentage."""
        num = self._dlg.threshold.text()
        if num == '':
            QSWATUtils.error('No threshold is set', self._gv.isBatch)
            return
        try:
            threshold = locale.atof(num)
        except Exception:
            QSWATUtils.error('Cannot parse {0} as a number'.format(num), self._gv.isBatch)
            return
        if self._dlg.areaButton.isChecked():
            thresholdM2 = threshold * 1E4 # convert to square metres
        else:
            thresholdM2 = (self.meanArea * threshold) / 100
        toAdd = set()
        for f in self.subbasinsLayer.getFeatures():
            area = f[self.areaIndx] * 1E4 # convert to square metres
            if area < thresholdM2:
                toAdd.add(f.id())
        ids = self.subbasinsLayer.selectedFeatureIds()
        for i in toAdd:
            ids.append(i)
        self.subbasinsLayer.select(ids)
        
    def layerMeanArea(self):
        """Return mean area of watershed layer subbasins in square metres."""
        count = self.subbasinsLayer.featureCount()
        # avoid division by zero
        if count == 0:
            return 0
        total = 0
        for f in self.subbasinsLayer.getFeatures():
            total += f[self.areaIndx] * 1E4 # convert to square metres
        return float(total) / count
    
    def setCount(self):
        """Set count text."""
        self._dlg.count.setText('{0!s} selected'.format(self.subbasinsLayer.selectedFeatureCount()))
        
    def save(self):
        """Close the dialog."""
        self._dlg.close()
        
    def cancel(self): 
        """Cancel selection and close."""  
        self.subbasinsLayer.removeSelection()
        self._dlg.close()
