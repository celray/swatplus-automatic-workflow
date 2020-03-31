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
import qgis
from PyQt5.QtCore import *  # @UnusedWildImport
from PyQt5.QtGui import *  # @UnusedWildImport
from PyQt5.QtWidgets import * # @UnusedWildImport
from qgis.core import * # @UnusedWildImport
from qgis.gui import * # @UnusedWildImport
import os.path
from osgeo import gdal
from osgeo.gdalconst import * # @UnusedWildImport
import math
import time
import numpy
import glob
import subprocess

import sys
sys.path.append(os.environ["WF_QGIS"])
import processing  # @UnresolvedImport

# Import the code for the dialog
from .hrusdialog import HrusDialog
from .QSWATUtils import QSWATUtils, fileWriter, FileTypes, ListFuns
from .QSWATTopology import QSWATTopology
from .DBUtils import DBUtils
from .parameters import Parameters
#from .polygonize import Polygonize
from .polygonizeInC2 import Polygonize  # @UnresolvedImport
from .dataInC import CellData, BasinData, WaterBody  # @UnresolvedImport
from .exempt import Exempt
from .split import Split
from .elevationbands import ElevationBands
from .delineation import Delineation

class HRUs(QObject):
    
    """Data and functions for creating HRUs."""
    
    def __init__(self, gv, reportsCombo):
        """Initialise class variables."""
        QObject.__init__(self)
        self._gv = gv
        self._db = gv.db
        self._iface = gv.iface
        self._dlg = HrusDialog()
        self._dlg.setWindowFlags(self._dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint & Qt.WindowMinimizeButtonHint)
        self._dlg.move(self._gv.hrusPos)
        self._reportsCombo = reportsCombo
        ## Landuse grid
        self.landuseFile = ''
        ## Soil grid
        self.soilFile = ''
        ## Landuse lookup table
        self.landuseTable = ''
        ## Soil lookup table
        self.soilTable = ''
        ## Landuse grid layer
        self.landuseLayer = None
        ## Soil grid layer
        self.soilLayer = None
        ## CreateHRUs object
        self.CreateHRUs = CreateHRUs(gv, reportsCombo, self._dlg)
        ## Flag to indicate completion
        self.completed = False
        
    def init(self):
        """Set up HRUs dialog."""
        self._db.populateTableNames()
        self._dlg.selectLanduseTable.addItems(self._db.landuseTableNames)
        self._dlg.selectLanduseTable.addItem(Parameters._USECSV)
        self._dlg.selectSoilTable.addItems(self._db.soilTableNames)
        self._dlg.selectSoilTable.addItem(Parameters._USECSV)
        self.readProj()
        self.setLanduseData()
        self.setSoilData()
        self._dlg.usersoilButton.toggled.connect(self.setSoilData)
        self._dlg.STATSGOButton.toggled.connect(self.setSoilData)
        self._dlg.SSURGOButton.toggled.connect(self.setSoilData)
        self._dlg.selectPlantSoilDatabaseButton.clicked.connect(self.selectPlantSoilDatabase)
        self._gv.getExemptSplit()
        self._dlg.subbasinsLabel.setText('')
        self._dlg.channelsLabel.setText('')
        self._dlg.fullHRUsLabel.setText('')
        self._dlg.optionGroup.setEnabled(True)
        self._dlg.landuseSoilSlopeGroup.setEnabled(False)
        self._dlg.areaGroup.setEnabled(False)
        self._dlg.targetGroup.setEnabled(False)
        self._dlg.createButton.setEnabled(False)
        self._dlg.progressBar.setVisible(False)
        self._dlg.shortChannelGroup.setVisible(not self._gv.useGridModel)
        self._dlg.remerge.setVisible(not self._gv.useGridModel)
        self._dlg.channelPercentButton.toggled.connect(self.setChannelChoice)
        self._dlg.channelAreaButton.toggled.connect(self.setChannelChoice)
        self._dlg.channelMergeVal.setValidator(QIntValidator())
        self._dlg.channelMergeVal.textChanged.connect(self.readChannelThreshold)
        self._dlg.channelMergeSlider.valueChanged.connect(self.changeChannelThreshold)
        self._dlg.reservoirThreshold.valueChanged.connect(self.setRead)
        self.setRead()
        self._dlg.floodplainCombo.activated.connect(self.setToReadFromMaps)
        self._dlg.readFromMaps.toggled.connect(self.setReadChoice)
        self._dlg.readFromPrevious.toggled.connect(self.setReadChoice)
        self._dlg.dominantHRUButton.toggled.connect(self.setHRUChoice)
        self._dlg.dominantLanduseButton.toggled.connect(self.setHRUChoice)
        self._dlg.filterLanduseButton.toggled.connect(self.setHRUChoice)
        self._dlg.filterAreaButton.toggled.connect(self.setHRUChoice)
        self._dlg.targetButton.toggled.connect(self.setHRUChoice)
        self._dlg.percentButton.toggled.connect(self.setHRUChoice)
        self._dlg.areaButton.toggled.connect(self.setHRUChoice)
        self._dlg.slopeBrowser.setText(QSWATUtils.slopesToString(self._db.slopeLimits))
        self._dlg.selectLanduseButton.clicked.connect(self.getLanduseFile)
        self._dlg.selectSoilButton.clicked.connect(self.getSoilFile)
        self._dlg.selectLanduseTable.activated.connect(self.setLanduseTable)
        self._dlg.selectSoilTable.activated.connect(self.setSoilTable)
        self._dlg.selectPlantTable.activated.connect(self.setPlantTable)
        self._dlg.selectUrbanTable.activated.connect(self.setUrbanTable)
        self._dlg.selectUsersoilTable.activated.connect(self.setUsersoilTable)
        self._dlg.insertButton.clicked.connect(self.insertSlope)
        self._dlg.slopeBand.setValidator(QDoubleValidator())
        self._dlg.floodplainCombo.addItem('Select floodplain map (optional)')
        self._dlg.floodplainCombo.setCurrentIndex(0)
        self.initFloodplain()
        # if as here you use returnPressed setting in a LineEdit box make sure all buttons in the 
        # dialog have default and autoDefault set to False (use QT designer, which 
        # by default sets autoDefault to True)
        self._dlg.slopeBand.returnPressed.connect(self.insertSlope)
        self._dlg.clearButton.clicked.connect(self.clearSlopes)
        self._dlg.readButton.clicked.connect(self.readFiles)
        self._dlg.createButton.clicked.connect(self.calcHRUs)
        self._dlg.cancelButton.clicked.connect(self._dlg.close)
        self._dlg.areaVal.textChanged.connect(self.readAreaThreshold)
        self._dlg.areaSlider.valueChanged.connect(self.changeAreaThreshold)
        self._dlg.landuseVal.textChanged.connect(self.readLanduseThreshold)
        self._dlg.landuseSlider.valueChanged.connect(self.changeLanduseThreshold)
        self._dlg.soilVal.textChanged.connect(self.readSoilThreshold)
        self._dlg.soilSlider.valueChanged.connect(self.changeSoilThreshold)
        self._dlg.targetVal.textChanged.connect(self.readTargetThreshold)
        self._dlg.targetSlider.valueChanged.connect(self.changeTargetThreshold)
        self._dlg.slopeVal.textChanged.connect(self.readSlopeThreshold)
        self._dlg.slopeSlider.valueChanged.connect(self.changeSlopeThreshold)
        self._dlg.landuseButton.clicked.connect(self.setLanduseThreshold)
        self._dlg.soilButton.clicked.connect(self.setSoilThreshold)
        self._dlg.exemptButton.clicked.connect(self.doExempt)
        self._dlg.splitButton.clicked.connect(self.doSplit)
        self._dlg.elevBandsButton.clicked.connect(self.doElevBands)
        
    def initFloodplain(self):
        """
        Add floodplain rasters to floodplainCombo.  Disable the combo if there are none.
        
        Potential floodplain rasters are of the form *flood*.tif in the flood directory.
        Also sets combo current item according to (previously read) project file.
        """
        pattern = QSWATUtils.join(self._gv.floodDir, '*.tif')
        fs = glob.glob(pattern)
        if len(fs) == 0:
            self._dlg.floodplainCombo.setEnabled(False)
            self._gv.useLandscapes = False
        for f in fs:
            self._dlg.floodplainCombo.addItem(os.path.split(f)[1])
        if self._gv.useLandscapes:
            index = self._dlg.floodplainCombo.findText(os.path.split(self._gv.floodFile)[1])
            if index > 0:
                self._dlg.floodplainCombo.setCurrentIndex(index)
        
    def run(self):
        """Run HRUs dialog."""
        self.init()
        self._dlg.show()
        self.progress('')
        result = self._dlg.exec_()  # @UnusedVariable
        # TODO: result is always zero. Need to reset to discover if CreateHRUs was run successfully
        self._gv.hrusPos = self._dlg.pos()
        if self.completed:
            return 1
        else:
            return 0
        
    def HRUsAreCreated(self):
        """Return true if HRUs are up to date, else false.
        
        Requires:
        - subs.shp used by visualize no earlier than watershed shapefile
        - gis_hrus table in project database no earlier than watershed shapefile
        - project_config table says hrus done
        """
        try:
            if not self._gv.useGridModel:
                # TODO: currently grid model does not write the subs.shp file
                # first check subsFile is up to date
                subsFile = QSWATUtils.join(self._gv.resultsDir, Parameters._SUBS + '.shp')
                #===================================================================
                # return QSWATUtils.isUpToDate(self._gv.wshedFile, subsFile) and \
                #         self._db.tableIsUpToDate(self._gv.wshedFile, 'Watershed') and \
                #         self._db.tableIsUpToDate(self._gv.wshedFile, 'hrus')
                #===================================================================
                if not QSWATUtils.isUpToDate(self._gv.basinFile, subsFile):
                    QSWATUtils.loginfo('HRUSAreCreated failed: subs.shp not up to date')
                    return False
            if not self._db.hasData('gis_hrus'):
                QSWATUtils.loginfo('HRUSAreCreated failed: hrus table missing or empty')
                return False
            return self._gv.isHRUsDone()
        except Exception:
            return False
            
    # no longer used - too slow for large BASINSDATA files   
#===============================================================================
#     def tryRun(self):
#         """Try rerunning with existing data and choices.  Fail quietly and return false if necessary, else return true."""
#         try:
#             self.init()
#             if not self._db.hasData('BASINSDATA'): 
#                 QSWATUtils.loginfo('HRUs tryRun failed: no basins data')
#                 return False
#             if not self.initLanduses(self.landuseTable):
#                 QSWATUtils.loginfo('HRUs tryRun failed: cannot initialise landuses')
#                 return False
#             if not self.initSoils(self.soilTable):
#                 QSWATUtils.loginfo('HRUs tryRun failed: cannot initialise soils')
#                 return False
#             time1 = time.process_time()
#             self.CreateHRUs.basins, OK = self._db.regenerateBasins(True) 
#             if not OK:
#                 QSWATUtils.loginfo('HRUs tryRun failed: could not regenerate basins')
#                 return False
#             time2 = time.process_time()
#             QSWATUtils.loginfo('Reading from database took {0} seconds'.format(int(time2 - time1)))
#             self.CreateHRUs.saveAreas(True)
#             if self._gv.useGridModel:
#                 self.rewriteWHUTables()
#             else:
#                 self._reportsCombo.setVisible(True)
#                 if self._reportsCombo.findText(Parameters._TOPOITEM) < 0:
#                     self._reportsCombo.addItem(Parameters._TOPOITEM)
#                 if self._reportsCombo.findText(Parameters._BASINITEM) < 0:
#                     self._reportsCombo.addItem(Parameters._BASINITEM)
#                 if self.CreateHRUs.isMultiple:
#                     if self.CreateHRUs.isArea:
#                         self.CreateHRUs.removeSmallHRUsByArea()
#                     elif self.CreateHRUs.isTarget:
#                         self.CreateHRUs.removeSmallHRUsbyTarget()
#                     else:
#                         if len(self._db.slopeLimits) == 0: self.CreateHRUs.slopeVal = 0
#                         # allow too tight thresholds, since we guard against removing all HRUs from a subbasin
#                         # if not self.CreateHRUs.cropSoilAndSlopeThresholdsAreOK():
#                         #     QSWATUtils.error('Internal error: problem with tight thresholds', self._gv.isBatch)
#                         #     return
#                         if self.CreateHRUs.useArea:
#                             self.CreateHRUs.removeSmallHRUsByThresholdArea()
#                         else:
#                             self.CreateHRUs.removeSmallHRUsByThresholdPercent()
#                     if not self.CreateHRUs.splitHRUs():
#                         return False
#                 self.CreateHRUs.saveAreas(False)
#                 self.CreateHRUs.basinsToHRUs()
#                 if self._reportsCombo.findText(Parameters._HRUSITEM) < 0:
#                     self._reportsCombo.addItem(Parameters._HRUSITEM)
#                 time1 = time.process_time()
#                 self.CreateHRUs.writeSubbasinsAndLandscapeTables()
#                 time2 = time.process_time()
#                 QSWATUtils.loginfo('Writing subbasins and lsus tables took {0} seconds'.format(int(time2 - time1)))
#             self._gv.writeProjectConfig(-1, 1)
#             return True
#         except Exception as e:
#             QSWATUtils.loginfo('HRUs tryRun failed: {0}'.format(repr(e)))
#             return False
#===============================================================================
    
    def readFiles(self):
        """Read landuse and soil data from files 
        or from previous run stored in project database
        or redo merge of short channels.
        """
        if self._dlg.remerge.isChecked():
            self.setChannelMergeChoice()
            if self._dlg.channelMergeSlider.value() > 0:
                self.CreateHRUs.mergeChannels()
            else:
                # remove all channel merges
                for basinData in self.CreateHRUs.basins.values():
                    basinData.mergedLsus = None
            self.CreateHRUs.printBasins(False, None)
            self._dlg.channelsLabel.setText('Channels count: {0}'.format(self.CreateHRUs.countChannels()))
            self._dlg.fullHRUsLabel.setText('Full HRUs count: {0}'.format(self.CreateHRUs.countHRUs()))
            # write landuse, soil, landscape choices in case of failure later
            self.saveProjPart1()
            self._dlg.hruChoiceGroup.setEnabled(True)
            self._dlg.areaPercentChoiceGroup.setEnabled(True)
            self._dlg.splitButton.setEnabled(True)
            self._dlg.exemptButton.setEnabled(True)
            self.setHRUChoice()
            return
        root = QgsProject.instance().layerTreeRoot()
        # check with user if there is a visible floodplain layer but no floodplain raster selected
        if not self._gv.isBatch and self._dlg.readFromMaps.isChecked() and \
            self._dlg.floodplainCombo.currentIndex() == 0 and self.hasVisibleFloodplainLayer(root):
            res = QSWATUtils.question('You have at least one floodplain map available.  Would you like to select one?', False, False)
            if res == QMessageBox.Yes:
                return
        # check if there is a slope limit not yet inserted
        if not self._gv.isBatch and self._dlg.readFromMaps.isChecked() and self._dlg.slopeBand.text() != '':
            res = QSWATUtils.question('You seem to be about to insert a slope limit.  Would you like to complete that?', False, False)
            if res == QMessageBox.Yes:
                return
        self._gv.writeProjectConfig(-1, 0)
        # don't hide undefined soil and landuse errors from previous run
        self._db._undefinedLanduseIds = []
        self._gv._undefinedSoilIds = []
        self._dlg.slopeGroup.setEnabled(False)
        self._dlg.generateFullHRUs.setEnabled(False)
        self._dlg.elevBandsButton.setEnabled(False)
        if not os.path.exists(self.landuseFile):
            QSWATUtils.error('\t ! Please select a landuse file', self._gv.isBatch)
            return
        if not os.path.exists(self.soilFile):
            QSWATUtils.error('\t ! Please select a soil file', self._gv.isBatch)
            return
        self._gv.landuseFile = self.landuseFile
        self._gv.soilFile = self.soilFile
        if self._gv.isBatch:
            # use names from project file settings
            luse = self.landuseTable
            soil = self.soilTable
        else: # allow user to choose
            luse = ''
            soil = ''
        self.progress('\t - Checking landuses ...')
        self._dlg.setCursor(Qt.WaitCursor)
        if not self.initLanduses(luse):
            self._dlg.setCursor(Qt.ArrowCursor)
            self.progress('')
            return
        #QSWATUtils.information('Using {0} as landuse table'.format(self.landuseTable), self._gv.isBatch)
        self.progress('\t - Checking soils ...')
        if not self.initSoils(soil):
            self._dlg.setCursor(Qt.ArrowCursor)
            self.progress('')
            return
        # write landuse, soil, landscape choices in case of failure later
        self.saveProjPart1()
        #QSWATUtils.information('Using {0} as soil table'.format(self.soilTable), self._gv.isBatch)
        if self._gv.isBatch:
            QSWATUtils.information('\t - Landuse file: {0}'.format(os.path.split(self.landuseFile)[1]), True)
            QSWATUtils.information('\t - Landuse lookup table: {0}'.format(self.landuseTable), True)
            QSWATUtils.information('\t - Soil file: {0}'.format(os.path.split(self.soilFile)[1]), True)
            QSWATUtils.information('\t - Soil lookup table: {0}'.format(self.soilTable), True)
        if self._dlg.readFromPrevious.isChecked():
            # read from database
            self.progress('\t - Reading basin data from database ...')
            time1 = time.process_time()
            (self.CreateHRUs.basins, OK) = self._db.regenerateBasins()
            time2 = time.process_time()
            QSWATUtils.loginfo('Reading from previous took {0} seconds'.format(int(time2 - time1)))
            self.progress('')
            if OK:
                self.CreateHRUs.saveAreas(True)
                if not self._gv.useGridModel:
                    if self._dlg.channelMergeSlider.value() > 0:
                        self.setChannelMergeChoice()
                        self.CreateHRUs.mergeChannels()
                self.CreateHRUs.printBasins(False, None)
                self._reportsCombo.setVisible(True)
                if self._reportsCombo.findText(Parameters._TOPOITEM) < 0:
                    self._reportsCombo.addItem(Parameters._TOPOITEM)
                if self._reportsCombo.findText(Parameters._BASINITEM) < 0:
                    self._reportsCombo.addItem(Parameters._BASINITEM)
        else:
            self.progress('\t - Reading rasters ...')
            self._gv.useLandscapes = False
            if self._dlg.floodplainCombo.isEnabled() and self._dlg.floodplainCombo.currentIndex() > 0:
                floodFile = self._dlg.floodplainCombo.currentText()
                floodPath = QSWATUtils.join(self._gv.floodDir, floodFile)
                if os.path.exists(floodPath):
                    self._gv.useLandscapes = True
                    self._gv.floodFile = floodPath
            self._dlg.progressBar.setValue(0)
            self._dlg.progressBar.setVisible(True)
            root = QgsProject.instance().layerTreeRoot()
            QSWATUtils.tryRemoveLayerAndFiles(self._gv.fullLSUsFile, root)
            QSWATUtils.tryRemoveLayerAndFiles(self._gv.actLSUsFile, root)
            if self._dlg.generateFullHRUs.isChecked():
                self.CreateHRUs.fullHRUsWanted = True
                QSWATUtils.tryRemoveLayerAndFiles(self._gv.fullHRUsFile, root)
                QSWATUtils.tryRemoveLayerAndFiles(self._gv.actHRUsFile, root)
            else:
                # remove any full and actual HRUs layers and files
                self.CreateHRUs.fullHRUsWanted = False
                treeLayer = QSWATUtils.getLayerByLegend(QSWATUtils._FULLHRUSLEGEND, root.findLayers())
                if treeLayer is not None:
                    fullHRUsLayer = treeLayer.layer()
                    fullHRUsFile = QSWATUtils.layerFileInfo(fullHRUsLayer).absoluteFilePath()
                    QSWATUtils.tryRemoveLayerAndFiles(fullHRUsFile, root)
                    treeLayer = QSWATUtils.getLayerByLegend(QSWATUtils._ACTHRUSLEGEND, root.findLayers())
                    if treeLayer is not None:
                        actHRUsLayer = treeLayer.layer()
                        actHRUsFile = QSWATUtils.layerFileInfo(actHRUsLayer).absoluteFilePath()
                        QSWATUtils.removeLayerAndFiles(actHRUsFile, root)
            time1 = time.process_time()
            OK = self.CreateHRUs.generateBasins(self._dlg.progressBar, root)
            time2 = time.process_time()
            QSWATUtils.loginfo('Reading from files took {0} seconds'.format(int(time2 - time1)))
            self.progress('')
            # now have occurrences of landuses, so can make proper colour scheme and legend entry
            # soils will be done after HRU creation, since only uses occurring soils
            FileTypes.colourLanduses(self.landuseLayer, self._db)
            treeModel = QgsLayerTreeModel(root)
            landuseTreeLayer = root.findLayer(self.landuseLayer.id())
            treeModel.refreshLayerLegend(landuseTreeLayer)
            if len(self._db.slopeLimits) > 0:
                slopeBandsLayer, _ = QSWATUtils.getLayerByFilename(root.findLayers(), self._gv.slopeBandsFile, FileTypes._SLOPEBANDS, 
                                                                        self._gv, None, QSWATUtils._SLOPE_GROUP_NAME)
                if slopeBandsLayer is not None:
                    slopeBandsTreeLayer = root.findLayer(slopeBandsLayer.id())
                    treeModel.refreshLayerLegend(slopeBandsTreeLayer)
            if OK:
                if not self._gv.useGridModel:
                    if self._dlg.channelMergeSlider.value() > 0:
                        self.setChannelMergeChoice()
                        self.CreateHRUs.mergeChannels()
                if self._gv.isBatch:
                    QSWATUtils.information('\t - Writing landuse and soil report ...', True)
                self.CreateHRUs.printBasins(False, None)
            self._dlg.progressBar.setVisible(False)
        self._dlg.setCursor(Qt.ArrowCursor)
        if OK:
            self._dlg.readFromPrevious.setEnabled(True)
            self._dlg.subbasinsLabel.setText('Subbasins count: {0}'.format(len(self.CreateHRUs.basins)))
            self._dlg.channelsLabel.setText('Channels count: {0}'.format(self.CreateHRUs.countChannels()))
            self._dlg.fullHRUsLabel.setText('Full HRUs count: {0}'.format(self.CreateHRUs.countHRUs()))
            if not self._gv.useGridModel:
                self._dlg.remerge.setEnabled(True)
                self._dlg.remerge.setChecked(True)
            self._dlg.hruChoiceGroup.setEnabled(True)
            self._dlg.areaPercentChoiceGroup.setEnabled(True)
            self._dlg.splitButton.setEnabled(True)
            self._dlg.exemptButton.setEnabled(True)
            self.setHRUChoice()
            self.saveProj()
            
    def hasVisibleFloodplainLayer(self, root):
        """Return true if there is a visible layer with a name starting 'Floodplain'."""
        for layer in root.findLayers():
            if layer.name().startswith('Floodplain') and layer.isVisible():
                return True
        return False
            
    def initLanduses(self, table):
        """Set up landuse lookup tables."""
        self._db.landuseVals = set()
        if table == '':
            self.landuseTable = self._dlg.selectLanduseTable.currentText()
            if self.landuseTable not in self._db.landuseTableNames:
                QSWATUtils.error('\t ! Please select a landuse table', self._gv.isBatch)
                return False
        else: # doing tryRun and table already read from project file
            self.landuseTable = table
        return self._db.populateLanduseCodes(self.landuseTable)
        
    def initSoils(self, table):
        """Set up soil lookup tables."""
        if not os.path.exists(self._db.plantSoilDatabase):
            QSWATUtils.information('\t - Warning: landuse and soil database {0} does not seeme to exist'
                                   .format(self._db.plantSoilDatabase), self._gv.isBatch)
        elif not self._db.useSTATSGO and not self._db.useSSURGO:
            if not self._db.hasTable(self._db.plantSoilDatabase, self._db.usersoilTable):
                QSWATUtils.information('\t - Warning: table {0} not found in landuse and soil database {1}'
                                       .format(self._db.usersoilTable, self._db.plantSoilDatabase), self._gv.isBatch)
        if self._db.useSSURGO: # no lookup table needed
            self._db.ssurgoSoils = set()
            return True
        else:
            self._db.usedSoilNames = dict()
        if table == '':
            self.soilTable = self._dlg.selectSoilTable.currentText()
            if self.soilTable not in self._db.soilTableNames:
                QSWATUtils.error('\t ! Please select a soil table', self._gv.isBatch)
                return False
        else: # doing tryRun and table already read from project file
            self.soilTable = table
        return self._db.populateSoilNames(self.soilTable)
    
    def calcHRUs(self):
        """Create HRUs."""
        self._gv.writeProjectConfig(-1, 0)
        time1 = time.process_time()
        try:
            self._dlg.setCursor(Qt.WaitCursor)
            self._dlg.slopeSlider.setEnabled(False)
            self._dlg.slopeVal.setEnabled(False)
            self._dlg.areaGroup.setEnabled(False)
            self._dlg.targetGroup.setEnabled(False)
            self._dlg.landuseSoilSlopeGroup.setEnabled(False)
            self.CreateHRUs.HRUNum = 0
            self.CreateHRUs.isDominantHRU = self._dlg.dominantHRUButton.isChecked()
            self.CreateHRUs.isMultiple = \
                not self._dlg.dominantHRUButton.isChecked() and not self._dlg.dominantLanduseButton.isChecked()
            self.CreateHRUs.useArea = self._dlg.areaButton.isChecked()
            self.CreateHRUs.reservoirThreshold = self._dlg.reservoirThreshold.value() 
            self.CreateHRUs.addReservoirs()
            if not self._gv.saveExemptSplit():
                return 
            if self.CreateHRUs.isMultiple:
                if self.CreateHRUs.isArea:
                    self.CreateHRUs.removeSmallHRUsByArea()
                elif self.CreateHRUs.isTarget:
                    self.CreateHRUs.removeSmallHRUsbyTarget()
                else:
                    if len(self._db.slopeLimits) == 0: self.CreateHRUs.slopeVal = 0
                    # allow too tight thresholds, since we guard against removing all HRUs from a subbasin
                    # if not self.CreateHRUs.cropSoilAndSlopeThresholdsAreOK():
                    #     QSWATUtils.error('Internal error: problem with tight thresholds', self._gv.isBatch)
                    #     return
                    if self.CreateHRUs.useArea:
                        self.CreateHRUs.removeSmallHRUsByThresholdArea()
                    else:
                        self.CreateHRUs.removeSmallHRUsByThresholdPercent()
                if not self.CreateHRUs.splitHRUs():
                    return
            else:
                if self.CreateHRUs.isDominantHRU:
                    self.CreateHRUs.selectDominantHRUs()
                else:
                    self.CreateHRUs.selectDominantLanduseSoilSlope()
            self.CreateHRUs.saveAreas(False)
            root = QgsProject.instance().layerTreeRoot()
            fullHRUsLayer = QSWATUtils.getLayerByFilename(root.findLayers(), self._gv.fullHRUsFile, None, None, None, None)[0]
            if self._gv.isBatch:
                QSWATUtils.information('\t - Writing HRUs report ...', True)
            self.CreateHRUs.writeWaterBodiesTable()
            self.CreateHRUs.printBasins(True, fullHRUsLayer)
            if not self.CreateHRUs.mergeLSUs(root):
                QSWATUtils.error('\t ! Failed to create actual LSUs shapefile {0}'.format(self._gv.actLSUsFile), self._gv.isBatch)
            if self.CreateHRUs.writeSubbasinsAndLandscapeTables():
                # can now provide soil layer legend
                soilLayer = QSWATUtils.getLayerByFilename(root.findLayers(), self._gv.soilFile, None, None, None, None)[0]
                if soilLayer is not None:
                    FileTypes.colourSoils(soilLayer, self._db)
                    treeModel = QgsLayerTreeModel(root)
                    soilTreeLayer = root.findLayer(soilLayer.id())
                    treeModel.refreshLayerLegend(soilTreeLayer)
                if self._db.writeSoilsTable() and self._db.writeLanduseTables():
                    self.completed = True
                    self._gv.writeProjectConfig(-1, 1)
                    self._dlg.readFromPrevious.setEnabled(True)
                    msg = '\t - HRUs done: {0!s} HRUs formed with {1!s} channels in {2!s} subbasins.'.format(self.CreateHRUs.HRUNum, 
                                                                                                self.CreateHRUs.countChannels(), 
                                                                                                len(self._gv.topo.subbasinToSWATBasin))
                    self._iface.messageBar().pushMessage(msg, level=Qgis.Info, duration=10)
                    if self._gv.isBatch:
                        print(msg)
        except Exception:
            QSWATUtils.exceptionError('Failed to create HRUs', self._gv.isBatch)
        finally:
            self.saveProj()
            time2 = time.process_time()
            QSWATUtils.loginfo('Calculating HRUs took {0} seconds'.format(int(time2 - time1)))
            self._dlg.setCursor(Qt.ArrowCursor)
            if self.completed:
                self._dlg.close()
                
    def setLanduseData(self):
        """Set plant and urban comboBoxes."""
        if not self._db.plantSoilDatabaseSelected:
            self._dlg.plantSoilDatabase.setText(self._db.dbFile)
            self._db.plantSoilDatabase = self._db.dbFile
        self._db.plantTableNames = self._db.collectPlantSoilTableNames('plant', self._dlg.selectPlantTable)
        plantSearch = self._db.plantTable if 'plant' in self._db.plantTable else 'plant'
        plantIndex = self._dlg.selectPlantTable.findText(plantSearch, Qt.MatchExactly)
        if plantIndex >= 0:
            self._dlg.selectPlantTable.setCurrentIndex(plantIndex)
        self._db.plantTable = self._dlg.selectPlantTable.currentText()
        self._db.urbanTableNames = self._db.collectPlantSoilTableNames('urban', self._dlg.selectUrbanTable)
        urbanSearch = self._db.urbanTable if 'urban' in self._db.urbanTable else 'urban'
        urbanIndex = self._dlg.selectUrbanTable.findText(urbanSearch, Qt.MatchExactly)
        if urbanIndex >= 0:
            self._dlg.selectUrbanTable.setCurrentIndex(urbanIndex)
        self._db.urbanTable = self._dlg.selectUrbanTable.currentText()
                
    def setSoilData(self):
        """Read usersoil/STATSGO/SSURGO choice and set variables."""
        if self._dlg.usersoilButton.isChecked():
            self._dlg.dbLabel.setText('Select landuse and soil database')
            self._db.useSTATSGO = False
            self._db.useSSURGO = False
            self._dlg.soilTableLabel.setEnabled(True)
            self._dlg.selectSoilTable.setEnabled(True)
            self._dlg.selectUsersoilTable.setVisible(True)
            self._dlg.selectUsersoilTableLabel.setVisible(True)
            if not self._db.plantSoilDatabaseSelected:
                self._dlg.plantSoilDatabase.setText(self._db.dbFile)
                self._db.plantSoilDatabase = self._db.dbFile
            self._db.usersoilTableNames = self._db.collectPlantSoilTableNames('usersoil', self._dlg.selectUsersoilTable)
            searchTable = self._db.usersoilTable if 'usersoil' in self._db.usersoilTable else 'usersoil'
            usersoilIndex = self._dlg.selectUsersoilTable.findText(searchTable, Qt.MatchExactly)
            if usersoilIndex >= 0:
                self._dlg.selectUsersoilTable.setCurrentIndex(usersoilIndex)
            self._db.usersoilTable = self._dlg.selectUsersoilTable.currentText()
        elif self._dlg.STATSGOButton.isChecked():
            self._dlg.dbLabel.setText('Select landuse database')
            self._db.useSTATSGO = True
            self._db.useSSURGO = False
            self._dlg.soilTableLabel.setEnabled(True)
            self._dlg.selectSoilTable.setEnabled(True)
            self._dlg.selectUsersoilTable.setVisible(False)
            self._dlg.selectUsersoilTableLabel.setVisible(False)
            self._db.usersoilTable = 'statsgo'
            self._db.soildatabase = QSWATUtils.join(self._gv.dbPath, Parameters._SOILDB)
        elif self._dlg.SSURGOButton.isChecked():
            self._dlg.dbLabel.setText('Select landuse database')
            self._db.useSTATSGO = False
            self._db.useSSURGO = True
            self._dlg.soilTableLabel.setEnabled(False)
            self._dlg.selectSoilTable.setEnabled(False)
            self._dlg.selectUsersoilTable.setVisible(False)
            self._dlg.selectUsersoilTableLabel.setVisible(False)
            self._db.usersoilTable = 'ssurgo'
            self._db.soildatabase = QSWATUtils.join(self._gv.dbPath, Parameters._SOILDB)
            
    def selectPlantSoilDatabase(self):
        """Allow user to select plant and soil database."""
        settings = QSettings()
        if settings.contains('/QSWATPlus/LastInputPath'):
            path = str(settings.value('/QSWATPlus/LastInputPath'))
        else:
            path = ''
        ft = FileTypes._SQLITE
        db, _ = QFileDialog.getOpenFileName(None, 'Select landuse and soil database', path, FileTypes.filter(ft))
        if db is not None and db != '':
            self._dlg.plantSoilDatabase.setText(db)
            self._db.plantSoilDatabase = db
            self._db.plantSoilDatabaseSelected = True
            self._db.plantTableNames = self._db.collectPlantSoilTableNames('plant', self._dlg.selectPlantTable)
            self._db.urbanTableNames = self._db.collectPlantSoilTableNames('urban', self._dlg.selectUrbanTable)
            # combo boxes may have changed, so reset plant, urban and usersoil choices
            # according to first entry in combo box
            self.setPlantTable()
            self.setUrbanTable()
            if not (self._db.useSTATSGO or self._db.useSSURGO):
                self._db.usersoilTableNames = self._db.collectPlantSoilTableNames('usersoil', self._dlg.selectUsersoilTable)
                self.setUsersoilTable()
        
    def setRead(self):
        """Set dialog to read from maps or from previous run."""
        if self._db.hasData('BASINSDATA'):
            self._dlg.readFromPrevious.setEnabled(True)
            self._dlg.readFromPrevious.setChecked(True)
        else:
            self._dlg.readFromMaps.setChecked(True)
            self._dlg.readFromPrevious.setEnabled(False)
        self.setReadChoice()
        
    def setToReadFromMaps(self):
        """Remove 'read from previous' option."""
        self._dlg.readFromMaps.setChecked(True)
        self._dlg.readFromPrevious.setEnabled(False)
            
    def setReadChoice(self):
        """Read read choice and set variables."""
        if self._dlg.readFromMaps.isChecked():
            self._dlg.slopeGroup.setEnabled(True)
            self._dlg.generateFullHRUs.setEnabled(True)
            self._dlg.elevBandsButton.setEnabled(True)
            if self._dlg.floodplainCombo.count() > 1:
                self._dlg.floodplainCombo.setEnabled(True)
        else:
            self._dlg.slopeGroup.setEnabled(False)
            self._dlg.generateFullHRUs.setEnabled(False)
            self._dlg.elevBandsButton.setEnabled(False)
            self._dlg.floodplainCombo.setEnabled(False)
        self._dlg.splitButton.setEnabled(False)
        self._dlg.exemptButton.setEnabled(False)
        self._dlg.hruChoiceGroup.setEnabled(False)
        self._dlg.areaPercentChoiceGroup.setEnabled(False)
        self._dlg.landuseSoilSlopeGroup.setEnabled(False)
        self._dlg.areaGroup.setEnabled(False)
        self._dlg.targetGroup.setEnabled(False)
        self._dlg.createButton.setEnabled(False)
        #self._dlg.subbasinsLabel.setText('')
        #self._dlg.channelsLabel.setText('')
        #self._dlg.fullHRUsLabel.setText('')
        
    def setChannelMergeChoice(self):
        """Save channel merge parameters."""
        self.CreateHRUs.channelMergeByPercent = self._dlg.channelPercentButton.isChecked()
        self.CreateHRUs.channelMergeThreshold = self._dlg.channelMergeSlider.value()
        
    def setHRUChoice(self):
        """Set dialog according to choice of multiple/single HRUs."""
        if self._dlg.dominantHRUButton.isChecked() or self._dlg.dominantLanduseButton.isChecked():
            self.CreateHRUs.isMultiple = False
            self.CreateHRUs.isDominantHRU = self._dlg.dominantHRUButton.isChecked()
            self._dlg.stackedWidget.setCurrentIndex(-1)
            self._dlg.areaPercentChoiceGroup.setEnabled(False)
            self._dlg.landuseSoilSlopeGroup.setEnabled(False)
            self._dlg.areaGroup.setEnabled(False)
            self._dlg.targetGroup.setEnabled(False)
            self._dlg.createButton.setEnabled(True)
        else:
            self._dlg.areaPercentChoiceGroup.setEnabled(True)
            self.CreateHRUs.isMultiple = True
            if self._dlg.filterLanduseButton.isChecked():
                self._dlg.stackedWidget.setCurrentIndex(0)
                self._dlg.landuseSoilSlopeGroup.setEnabled(True)
                self._dlg.landuseSlider.setEnabled(True)
                self._dlg.landuseVal.setEnabled(True)
                self._dlg.landuseButton.setEnabled(True)
                self._dlg.soilSlider.setEnabled(False)
                self._dlg.soilVal.setEnabled(False)
                self._dlg.soilButton.setEnabled(False)
                self._dlg.slopeSlider.setEnabled(False)
                self._dlg.slopeVal.setEnabled(False)
                self._dlg.areaGroup.setEnabled(False)
                self._dlg.targetGroup.setEnabled(False)
                self._dlg.createButton.setEnabled(False)
                self.CreateHRUs.isArea = False
                self.CreateHRUs.isTarget = False
            elif self._dlg.filterAreaButton.isChecked():
                self._dlg.stackedWidget.setCurrentIndex(1)
                self._dlg.landuseSoilSlopeGroup.setEnabled(False)
                self._dlg.areaGroup.setEnabled(True)
                self._dlg.targetGroup.setEnabled(False)
                self._dlg.createButton.setEnabled(True)
                self.CreateHRUs.isArea = True
                self.CreateHRUs.isTarget = False
            else:
                self._dlg.landuseSoilSlopeGroup.setEnabled(False)
                self._dlg.areaGroup.setEnabled(False)
                self._dlg.stackedWidget.setCurrentIndex(2)
                self._dlg.targetGroup.setEnabled(True)
                self._dlg.createButton.setEnabled(True)
                self.CreateHRUs.isArea = False
                self.CreateHRUs.isTarget = True
            self.setAreaPercentChoice()
        
    def setAreaPercentChoice(self):
        """Set dialog according to choice of area or percent thresholds."""
        if not self.CreateHRUs.isMultiple:
            return
        self.CreateHRUs.useArea = self._dlg.areaButton.isChecked()
        if self.CreateHRUs.useArea:
            self._dlg.landuseLabel.setText('Landuse (ha)')
            self._dlg.soilLabel.setText('Soil (ha)')
            self._dlg.slopeLabel.setText('Slope (ha)')
            self._dlg.areaLabel.setText('Area (ha)')
        else:
            self._dlg.landuseLabel.setText('Landuse (%)')
            self._dlg.soilLabel.setText('Soil (%)')
            self._dlg.slopeLabel.setText('Slope (%)')
            self._dlg.areaLabel.setText('Area (%)')
        if self.CreateHRUs.isArea:
            displayMaxArea = int(self.CreateHRUs.maxLandscapeArea()) if self.CreateHRUs.useArea else 100
            self._dlg.areaMax.setText(str(displayMaxArea))
            self._dlg.areaSlider.setMaximum(displayMaxArea)
            if 0 < self.CreateHRUs.areaVal <= displayMaxArea:
                self._dlg.areaSlider.setValue(int(self.CreateHRUs.areaVal))
        elif self.CreateHRUs.isTarget:
            # Setting the minimum for the slider changes the slider value
            # which in turn changes CreateHRUs.targetVal.
            # So we remember the value of CreateHRUs.targetVal and restore it later.
            target = self.CreateHRUs.targetVal
            if self._gv.useLandscapes:
                minHRUs = self.CreateHRUs.countLsus()
            else:
                minHRUs = len(self._gv.topo.SWATBasinToSubbasin)
            self._dlg.targetSlider.setMinimum(minHRUs)
            self._dlg.targetMin.setText(str(minHRUs))
            numHRUs = self.CreateHRUs.countHRUs()
            self._dlg.targetSlider.setMaximum(numHRUs)
            self._dlg.targetMax.setText(str(numHRUs))
            # restore the target and use it to set the slider
            self.CreateHRUs.targetVal = target
            if minHRUs <= self.CreateHRUs.targetVal <= numHRUs:
                self._dlg.targetSlider.setValue(int(self.CreateHRUs.targetVal))
        else:
            minCropVal = int(self.CreateHRUs.minMaxCropVal(self.CreateHRUs.useArea))
            self._dlg.landuseMax.setText(str(minCropVal))
            self._dlg.landuseSlider.setMaximum(minCropVal)
            if 0 <= self.CreateHRUs.landuseVal <= minCropVal:
                self._dlg.landuseSlider.setValue(int(self.CreateHRUs.landuseVal))
            
    def getLanduseFile(self):
        """Load landuse file."""
        root = QgsProject.instance().layerTreeRoot()
        QSWATUtils.removeLayerByLegend(FileTypes.legend(FileTypes._LANDUSES), root.findLayers())
        (landuseFile, landuseLayer) = \
            QSWATUtils.openAndLoadFile(root, FileTypes._LANDUSES, 
                                       self._dlg.selectLanduse, self._gv.landuseDir, 
                                       self._gv, None, QSWATUtils._LANDUSE_GROUP_NAME, clipToDEM=True)
        if landuseFile and landuseLayer:
            self.landuseFile = landuseFile
            self.landuseLayer = landuseLayer
        
    def getSoilFile(self):
        """Load soil file."""
        root = QgsProject.instance().layerTreeRoot()
        QSWATUtils.removeLayerByLegend(FileTypes.legend(FileTypes._SOILS), root.findLayers()) 
        (soilFile, soilLayer) = \
            QSWATUtils.openAndLoadFile(root, FileTypes._SOILS, 
                                       self._dlg.selectSoil, self._gv.soilDir, 
                                       self._gv, None, QSWATUtils._SOIL_GROUP_NAME, clipToDEM=True)
        if soilFile and soilLayer:
            self.soilFile = soilFile
            self.soilLayer = soilLayer
        
    def setLanduseTable(self):
        """Set landuse table."""
        table = self._dlg.selectLanduseTable.currentText()
        if table == Parameters._USECSV:
            table = self._db.readLanduseCsv()
            if table != '':
                self._dlg.selectLanduseTable.insertItem(0, table)
                self._dlg.selectLanduseTable.setCurrentIndex(0)
        self.landuseTable = table
        self.setToReadFromMaps()
        
    def setSoilTable(self):
        """Set soil table."""
        table = self._dlg.selectSoilTable.currentText()
        if table == Parameters._USECSV:
            table = self._db.readSoilCsv()
            if table != '':
                self._dlg.selectSoilTable.insertItem(0, table)
                self._dlg.selectSoilTable.setCurrentIndex(0)
        self.soilTable = table
        self.setToReadFromMaps()
        
    def setPlantTable(self):
        """Set plant table."""
        table = self._dlg.selectPlantTable.currentText()
        if table == Parameters._USECSV:
            table = self._db.readPlantCsv()
            if table != '':
                self._dlg.selectPlantTable.insertItem(0, table)
                self._dlg.selectPlantTable.setCurrentIndex(0)
        self._db.plantTable = table
        
    def setUrbanTable(self):
        """Set urban table."""
        table = self._dlg.selectUrbanTable.currentText()
        if table == Parameters._USECSV:
            table = self._db.readUrbanCsv()
            if table != '':
                self._dlg.selectUrbanTable.insertItem(0, table)
                self._dlg.selectUrbanTable.setCurrentIndex(0)
        self._db.urbanTable = table
        
    def setUsersoilTable(self):
        """Set usersoil table."""
        table = self._dlg.selectUsersoilTable.currentText()
        if table == Parameters._USECSV:
            table = self._db.readUsersoilCsv()
            if table != '':
                self._dlg.selectUsersoilTable.insertItem(0, table)
                self._dlg.selectUsersoilTable.setCurrentIndex(0)
        self._db.usersoilTable = table
            
    def readChannelThreshold(self):
        """Read channel merge threshold."""
        string = self._dlg.channelMergeVal.text()
        if string == '':
            return
        try:
            val = int(string)
            if self._dlg.channelAreaButton.isChecked() and val > self._dlg.channelMergeSlider.maximum():
                self._dlg.channelMergeSlider.setMaximum(2 * val)
            self._dlg.channelMergeSlider.setValue(val)
            self._dlg.channelMergeVal.moveCursor(QTextCursor.End)
        except Exception:
            return
        
    def changeChannelThreshold(self):
        """Change channel merge threshold."""
        val = self._dlg.channelMergeSlider.value()
        self._dlg.channelMergeVal.setText(str(val))
        
    def setChannelChoice(self):
        """Set maximum value for short channel merge slider for percent or hectares."""
        if self._dlg.channelPercentButton.isChecked():
            self._dlg.channelMergeSlider.setMaximum(100)
        else:
            self._dlg.channelMergeSlider.setMaximum(int(self._gv.channelThresholdArea // 10000))
        
    def readAreaThreshold(self):
        """Read area threshold."""
        string = self._dlg.areaVal.text()
        if string == '':
            return
        try:
            val = int(string)
            # allow values outside slider range
            if self._dlg.areaSlider.minimum() <= val <= self._dlg.areaSlider.maximum():
                self._dlg.areaSlider.setValue(val)
            self.CreateHRUs.areaVal = val
            self._dlg.areaVal.moveCursor(QTextCursor.End)
        except Exception:
            return
        self._dlg.createButton.setEnabled(True)
        
    def changeAreaThreshold(self):
        """Change area threshold and slider."""
        val = self._dlg.areaSlider.value()
        self._dlg.areaVal.setText(str(val))
        self._dlg.createButton.setEnabled(True)
        self.CreateHRUs.areaVal = val
        
    def readLanduseThreshold(self):
        """Read landuse value."""
        string = self._dlg.landuseVal.text()
        if string == '':
            return
        try:
            val = int(string)
            # allow values outside slider range
            if self._dlg.landuseSlider.minimum() <= val <= self._dlg.landuseSlider.maximum():
                self._dlg.landuseSlider.setValue(val)
            self.CreateHRUs.landuseVal = val
            self._dlg.landuseVal.moveCursor(QTextCursor.End)
        except Exception:
            return
        
    def changeLanduseThreshold(self):
        """Change landuse value and slider."""
        val = self._dlg.landuseSlider.value()
        self._dlg.landuseVal.setText(str(val))
        self.CreateHRUs.landuseVal = val
        
    def readSoilThreshold(self):
        """Read soil value."""
        string = self._dlg.soilVal.text()
        if string == '':
            return
        try:
            val = int(string)
            # allow values outside slider range
            if self._dlg.soilSlider.minimum() <= val <= self._dlg.soilSlider.maximum():
                self._dlg.soilSlider.setValue(val)
            self.CreateHRUs.soilVal = val
            self._dlg.soilVal.moveCursor(QTextCursor.End)
        except Exception:
            return
        
    def changeSoilThreshold(self):
        """Change soil value and slider."""
        val = self._dlg.soilSlider.value()
        self._dlg.soilVal.setText(str(val))
        self.CreateHRUs.soilVal = val
        
    def readSlopeThreshold(self):
        """Read slope value."""
        string = self._dlg.slopeVal.text()
        if string == '':
            return
        try:
            val = int(string)
            # allow values outside slider range
            if self._dlg.slopeSlider.minimum() <= val <= self._dlg.slopeSlider.maximum():
                self._dlg.slopeSlider.setValue(val)
            self.CreateHRUs.slopeVal = val
            self._dlg.slopeVal.moveCursor(QTextCursor.End)
        except Exception:
            return
        
    def changeSlopeThreshold(self):
        """Change slope value and slider."""
        val = self._dlg.slopeSlider.value()
        self._dlg.slopeVal.setText(str(val))
        self.CreateHRUs.slopeVal = val
        
    def readTargetThreshold(self):
        """Read slope value."""
        string = self._dlg.targetVal.text()
        if string == '':
            return
        try:
            val = int(string)
            self._dlg.targetSlider.setValue(val)
            self.CreateHRUs.targetVal = val
            self._dlg.targetVal.moveCursor(QTextCursor.End)
        except Exception:
            return
        
    def changeTargetThreshold(self):
        """Change slope value and slider."""
        val = self._dlg.targetSlider.value()
        self._dlg.targetVal.setText(str(val))
        self.CreateHRUs.targetVal = val
        
    def setLanduseThreshold(self):
        """Set threshold for soil according to landuse value."""
        if self.CreateHRUs.useArea:
            minSoilVal = int(self.CreateHRUs.minMaxSoilArea())
        else:
            minSoilVal = int(self.CreateHRUs.minMaxSoilPercent(self.CreateHRUs.landuseVal))
        self._dlg.landuseSlider.setEnabled(False)
        self._dlg.landuseVal.setEnabled(False)
        self._dlg.landuseButton.setEnabled(False)
        self._dlg.soilSlider.setEnabled(True)
        self._dlg.soilVal.setEnabled(True)
        self._dlg.soilButton.setEnabled(True)
        self._dlg.soilSlider.setMaximum(minSoilVal)
        self._dlg.soilMax.setText(str(minSoilVal))
        if 0 <= self.CreateHRUs.soilVal <= minSoilVal:
            self._dlg.soilSlider.setValue(int(self.CreateHRUs.soilVal))
        
    def setSoilThreshold(self):
        """Set threshold for slope according to landuse and soil values."""
        self._dlg.soilSlider.setEnabled(False)
        self._dlg.soilVal.setEnabled(False)
        self._dlg.soilButton.setEnabled(False)
        if len(self._db.slopeLimits) > 0:
            if self.CreateHRUs.useArea:
                minSlopeVal = int(self.CreateHRUs.minMaxSlopeArea())
            else:
                minSlopeVal = int(self.CreateHRUs.minMaxSlopePercent(self.CreateHRUs.landuseVal, self.CreateHRUs.soilVal))
            self._dlg.slopeSlider.setEnabled(True)
            self._dlg.slopeVal.setEnabled(True)
            self._dlg.slopeSlider.setMaximum(minSlopeVal)
            self._dlg.slopeMax.setText(str(minSlopeVal))
            if 0 <= self.CreateHRUs.slopeVal <=  minSlopeVal:
                self._dlg.slopeSlider.setValue(int(self.CreateHRUs.slopeVal))
        self._dlg.createButton.setEnabled(True)
        
    def insertSlope(self):
        """Insert a new slope limit."""
        txt = self._dlg.slopeBand.text()
        if txt == '':
            return
        try:
            num = float(txt)
        except Exception:
            QSWATUtils.information('\t - Cannot parse {0} as a number'.format(txt), self._gv.isBatch)
            return
        ListFuns.insertIntoSortedList(num, self._db.slopeLimits, True)
        self._dlg.slopeBrowser.setText(QSWATUtils.slopesToString(self._db.slopeLimits))
        self._dlg.slopeBand.clear()
        
        
    def clearSlopes(self):
        """Reset to no slope bands."""
        self._db.slopeLimits = []
        self._dlg.slopeBrowser.setText('[0, 9999]')
        self._dlg.slopeBand.clear()
        
    def doExempt(self):
        """Run the exempt dialog."""
        dlg = Exempt(self._gv)
        dlg.run()
        
    def doSplit(self):
        """Run the split dialog."""
        dlg = Split(self._gv)
        dlg.run()
        
    def doElevBands(self):
        """Run the elevation bands dialog."""
        dlg = ElevationBands(self._gv)
        dlg.run()
    
    def progress(self, msg):
        """Update progress label with message; emit message for display in testing."""
        QSWATUtils.progress(msg, self._dlg.progressLabel)
        if msg != '':
            self.progress_signal.emit(msg)
       
    ## signal for indicating progress     
    progress_signal = pyqtSignal(str)
        
    def readProj(self):
        """Read landuse, soil, LSU, HRU settings from the project file."""
        proj = QgsProject.instance()
        title = proj.title()
        root = proj.layerTreeRoot()
        landuseFile, found = proj.readEntry(title, 'landuse/file', '')
        landuseLayer = None
        if found and landuseFile != '':
            landuseFile = proj.readPath(landuseFile)
            landuseLayer, _ = \
                QSWATUtils.getLayerByFilename(root.findLayers(), landuseFile, FileTypes._LANDUSES, 
                                              self._gv, None, QSWATUtils._LANDUSE_GROUP_NAME)
        else:
            treeLayer = QSWATUtils.getLayerByLegend(FileTypes.legend(FileTypes._LANDUSES), root.findLayers())
            if treeLayer is not None:
                layer = treeLayer.layer()
                possFile = QSWATUtils.layerFileInfo(layer).absoluteFilePath()
                if QSWATUtils.question('Use {0} as {1} file?'.format(possFile, FileTypes.legend(FileTypes._LANDUSES)), self._gv.isBatch, True) == QMessageBox.Yes:
                    landuseLayer = layer
                    landuseFile = possFile
        if landuseLayer is not None: 
            self._dlg.selectLanduse.setText(landuseFile)
            self.landuseFile = landuseFile
            self.landuseLayer = landuseLayer
        soilFile, found = proj.readEntry(title, 'soil/file', '')
        soilLayer = None
        if found and soilFile != '':
            soilFile = proj.readPath(soilFile)
            soilLayer, _  = \
                QSWATUtils.getLayerByFilename(root.findLayers(), soilFile, FileTypes._SOILS, 
                                              self._gv, None, QSWATUtils._SOIL_GROUP_NAME)
        else:
            treeLayer = QSWATUtils.getLayerByLegend(FileTypes.legend(FileTypes._SOILS), root.findLayers())
            if treeLayer is not None:
                layer = treeLayer.layer()
                possFile = QSWATUtils.layerFileInfo(layer).absoluteFilePath()
                if QSWATUtils.question('Use {0} as {1} file?'.format(possFile, FileTypes.legend(FileTypes._SOILS)), self._gv.isBatch, True) == QMessageBox.Yes:
                    soilLayer = layer
                    soilFile = possFile
        if soilLayer is not None:
            self._dlg.selectSoil.setText(soilFile)
            self.soilFile = soilFile
            self.soilLayer = soilLayer
        self._db.useSTATSGO, found = proj.readBoolEntry(title, 'soil/useSTATSGO', False)
        if found and self._db.useSTATSGO:
            self._dlg.STATSGOButton.setChecked(True)
        self._db.useSSURGO, found = proj.readBoolEntry(title, 'soil/useSSURGO', False)
        if found and self._db.useSSURGO:
            self._dlg.SSURGOButton.setChecked(True)
        landuseTable, found = proj.readEntry(title, 'landuse/table', '')
        if found and landuseTable != '':
            index = self._dlg.selectLanduseTable.findText(landuseTable)
            if index >= 0:
                self._dlg.selectLanduseTable.setCurrentIndex(index)
            self.landuseTable = landuseTable
        self._db.waterLanduse, _ = proj.readNumEntry(title, 'landuse/water', -1)
        plantTable, found = proj.readEntry(title, 'landuse/plant', '')
        if found and plantTable != '':
            index = self._dlg.selectPlantTable.findText(plantTable)
            if index >= 0:
                self._dlg.selectPlantTable.setCurrentIndex(index)
        else:
            plantTable = 'plant'
        self._db.plantTable = plantTable
        urbanTable, found = proj.readEntry(title, 'landuse/urban', '')
        if found and urbanTable != '':
            index = self._dlg.selectUrbanTable.findText(urbanTable)
            if index >= 0:
                self._dlg.selectUrbanTable.setCurrentIndex(index)
        else:
            urbanTable = 'urban'
        self._db.urbanTable = urbanTable
        soilTable, found = proj.readEntry(title, 'soil/table', '')
        if found and soilTable != '':
            index = self._dlg.selectSoilTable.findText(soilTable)
            if index >= 0:
                self._dlg.selectSoilTable.setCurrentIndex(index)
            self.soilTable = soilTable
        plantSoilDatabase, found = proj.readEntry(title, 'soil/database', '')
        if found and plantSoilDatabase != '':
            plantSoilDatabase = proj.readPath(plantSoilDatabase)
            self._db.plantSoilDatabase = plantSoilDatabase
            self._db.plantSoilDatabaseSelected = True
        else:
            self._db.plantSoilDatabase = self._db.dbFile
        self._dlg.plantSoilDatabase.setText(self._db.plantSoilDatabase)
        self._db.soilDatabase = QSWATUtils.join(self._gv.dbPath, Parameters._SOILDB)
        usersoilTable, found = proj.readEntry(title, 'soil/databaseTable', '')
        if found and usersoilTable != '':
            self._db.usersoilTable = usersoilTable
        else:
            if self._db.useSSURGO:
                self._db.usersoilTable = 'ssurgo'
            elif self._db.useSTATSGO:
                self._db.usersoilTable = 'statsgo'
            else:
                self._db.usersoilTable = 'usersoil'
        useLandscapes, found = proj.readBoolEntry(title, 'lsu/useLandscapes', False)
        if found:
            self._gv.useLandscapes = useLandscapes
        useLeftRight, found = proj.readBoolEntry(title, 'lsu/useLeftRight', False)
        if found:
            self._gv.useLeftRight = useLeftRight
        floodFile, found = proj.readEntry(title, 'lsu/floodplainFile', '')
        if found:
            floodFile =  proj.readPath(floodFile)
            if os.path.exists(floodFile):
                self._gv.floodFile = floodFile
        reservoirThresholdNoLandscape, _ = proj.readNumEntry(title, 'lsu/thresholdResNoFlood', 101)
        reservoirThresholdFloodplain, _ = proj.readNumEntry(title, 'lsu/thresholdResFlood', 101)
        if useLandscapes:
            self._dlg.reservoirThreshold.setValue(reservoirThresholdFloodplain)
        else:   
            self._dlg.reservoirThreshold.setValue(reservoirThresholdNoLandscape)
        channelThresholdArea, found = proj.readNumEntry(title, 'delin/thresholdCh', 0)
        if found and channelThresholdArea > 0:
            self._gv.channelThresholdArea = channelThresholdArea * self._gv.cellArea
        channelMergeByPercent, _ = proj.readBoolEntry(title, 'lsu/channelMergeByPercent', True)
        if channelMergeByPercent:
            self._dlg.channelPercentButton.setChecked(True)
        else:
            self._dlg.channelAreaButton.setChecked(True)
        channelMergeVal, _ = proj.readNumEntry(title, 'lsu/channelMergeVal', 0)
        self._dlg.channelMergeVal.setText(str(channelMergeVal))
        self.readChannelThreshold()
        elevBandsThreshold, found = proj.readNumEntry(title, 'hru/elevBandsThreshold', 0)
        if found:
            self._gv.elevBandsThreshold = elevBandsThreshold
        numElevBands, found = proj.readNumEntry(title, 'hru/numElevBands', 0)
        if found:
            self._gv.numElevBands = numElevBands
        slopeBands, found = proj.readEntry(title, 'hru/slopeBands', '')
        if found and slopeBands != '':
            self._db.slopeLimits = QSWATUtils.parseSlopes(slopeBands)
        slopeBandsFile, found = proj.readEntry(title, 'hru/slopeBandsFile', '')
        slopeBandsLayer = None
        if found and slopeBandsFile != '':
            slopeBandsFile = proj.readPath(slopeBandsFile)
            slopeBandsLayer, _ = \
                QSWATUtils.getLayerByFilename(root.findLayers(), slopeBandsFile, FileTypes._SLOPEBANDS,
                                              self._gv, None, QSWATUtils._SLOPE_GROUP_NAME)
        else:
            treeLayer = QSWATUtils.getLayerByLegend(FileTypes.legend(FileTypes._SLOPEBANDS), root.findLayers())
            if treeLayer is not None:
                layer = treeLayer.layer()
                possFile = QSWATUtils.layerFileInfo(layer).absoluteFilePath()
                if QSWATUtils.question('Use {0} as {1} file?'.format(possFile, FileTypes.legend(FileTypes._SLOPEBANDS)), 
                                       self._gv.isBatch, True) == QMessageBox.Yes:
                    slopeBandsLayer = layer
                    slopeBandsFile = possFile
        if slopeBandsLayer is not None:
            self._gv.slopeBandsFile = slopeBandsFile
        else:
            self._gv.slopeBandsFile = ''
        self.CreateHRUs.isMultiple, found = proj.readBoolEntry(title, 'hru/isMultiple', False)
        self.CreateHRUs.isDominantHRU, found = proj.readBoolEntry(title, 'hru/isDominantHRU', True)
        self.CreateHRUs.isArea, found = proj.readBoolEntry(title, 'hru/isArea', False)
        self.CreateHRUs.isTarget, found = proj.readBoolEntry(title, 'hru/isTarget', False)
        self.CreateHRUs.useArea, found = proj.readBoolEntry(title, 'hru/useArea', False)
        if self.CreateHRUs.isMultiple:
            if self.CreateHRUs.isArea:
                self._dlg.filterAreaButton.setChecked(True)
            elif self.CreateHRUs.isTarget:
                self._dlg.targetButton.setChecked(True) 
            else:
                self._dlg.filterLanduseButton.setChecked(True) 
        elif self.CreateHRUs.isDominantHRU:
            self._dlg.dominantHRUButton.setChecked(True)
        else:
            self._dlg.dominantLanduseButton.setChecked(True)
        if self.CreateHRUs.useArea:
            self._dlg.areaButton.setChecked(True)
        else:
            self._dlg.percentButton.setChecked(True)
        self.CreateHRUs.areaVal, found = proj.readNumEntry(title, 'hru/areaVal', 0)
        if found and self.CreateHRUs.areaVal > 0:
            self._dlg.areaVal.setText(str(self.CreateHRUs.areaVal))
        self.CreateHRUs.landuseVal, found = proj.readNumEntry(title, 'hru/landuseVal', 0)
        if found and self.CreateHRUs.landuseVal > 0:
            self._dlg.landuseVal.setText(str(self.CreateHRUs.landuseVal))
        self.CreateHRUs.soilVal, found = proj.readNumEntry(title, 'hru/soilVal', 0)
        if found and self.CreateHRUs.soilVal > 0:
            self._dlg.soilVal.setText(str(self.CreateHRUs.soilVal))
        self.CreateHRUs.slopeVal, found = proj.readNumEntry(title, 'hru/slopeVal', 0)
        if found and self.CreateHRUs.slopeVal > 0:
            self._dlg.slopeVal.setText(str(self.CreateHRUs.slopeVal))
        self.CreateHRUs.targetVal, found = proj.readNumEntry(title, 'hru/targetVal', 0)
        if found and self.CreateHRUs.targetVal > 0:
            self._dlg.targetVal.setText(str(self.CreateHRUs.targetVal))
            
    def saveProjPart1(self):
        """Write landuse, soil, and landscape choices to project file."""
        proj = QgsProject.instance()
        self.saveEntries1(proj)
        proj.write()
        
    def saveEntries1(self, proj):
        """Write entries for landuse, soil, and landscape choices to project file."""
        title = proj.title()
        proj.writeEntry(title, 'landuse/file', proj.writePath(self.landuseFile))
        proj.writeEntry(title, 'soil/file', proj.writePath(self.soilFile))
        proj.writeEntry(title, 'landuse/table', self.landuseTable)
        proj.writeEntry(title, 'landuse/plant', self._db.plantTable)
        proj.writeEntry(title, 'landuse/urban', self._db.urbanTable)
        proj.writeEntry(title, 'landuse/water', self._db.waterLanduse)
        proj.writeEntry(title, 'soil/table', self.soilTable)
        proj.writeEntry(title, 'soil/useSTATSGO', self._db.useSTATSGO)
        proj.writeEntry(title, 'soil/useSSURGO', self._db.useSSURGO)
        proj.writeEntry(title, 'soil/database', proj.writePath(self._db.plantSoilDatabase))
        proj.writeEntry(title, 'soil/databaseTable', self._db.usersoilTable)
        proj.writeEntry(title, 'lsu/useLandscapes', self._gv.useLandscapes)
        if self._gv.useLandscapes:
            proj.writeEntry(title, 'lsu/thresholdResFlood', self._dlg.reservoirThreshold.value())
        else:    
            proj.writeEntry(title, 'lsu/thresholdResNoFlood', self._dlg.reservoirThreshold.value())
        proj.writeEntry(title, 'lsu/useLeftRight', self._gv.useLeftRight)
        proj.writeEntry(title, 'lsu/floodplainFile', proj.writePath(self._gv.floodFile))
        proj.writeEntry(title, 'lsu/channelMergeByPercent', self._dlg.channelPercentButton.isChecked())
        proj.writeEntry(title, 'lsu/channelMergeVal', self._dlg.channelMergeSlider.value())
            
    def saveProj(self):
        """Write settings to the project file."""
        proj = QgsProject.instance()
        self.saveEntries1(proj)
        self.saveEntries2(proj)
        proj.write()
        
    def saveEntries2(self, proj):
        """Write entries for hru choices to project file."""
        title = proj.title()
        proj.writeEntry(title, 'hru/elevBandsThreshold', self._gv.elevBandsThreshold)
        proj.writeEntry(title, 'hru/numElevBands', self._gv.numElevBands)
        proj.writeEntry(title, 'hru/slopeBands', QSWATUtils.slopesToString(self._db.slopeLimits))
        proj.writeEntry(title, 'hru/slopeBandsFile', proj.writePath(self._gv.slopeBandsFile))
        proj.writeEntry(title, 'hru/isMultiple', self.CreateHRUs.isMultiple)
        proj.writeEntry(title, 'hru/isDominantHRU', self.CreateHRUs.isDominantHRU)
        proj.writeEntry(title, 'hru/isArea', self.CreateHRUs.isArea)
        proj.writeEntry(title, 'hru/isTarget', self.CreateHRUs.isTarget)
        proj.writeEntry(title, 'hru/useArea', self.CreateHRUs.useArea)
        proj.writeEntry(title, 'hru/areaVal', self.CreateHRUs.areaVal)
        proj.writeEntry(title, 'hru/landuseVal', self.CreateHRUs.landuseVal)
        proj.writeEntry(title, 'hru/soilVal', self.CreateHRUs.soilVal)
        proj.writeEntry(title, 'hru/slopeVal', self.CreateHRUs.slopeVal)
        proj.writeEntry(title, 'hru/targetVal', self.CreateHRUs.targetVal)
            
class CreateHRUs(QObject):
    
    ''' Generate HRU data for SWAT.  Inputs are basins, landuse, soil and slope grids.'''
    
    '''
    This version assumes
    1.  Basins grid is in an equal area projection, so cell area is product
        of dimensions in square meters.
    2.  Landuse, soil and slope grids either have the same projection, or method of
        - (x,y) to coords in basins map
        - coords to (x,y) in landuse/soil/slope map plus lookup in that map
        is correct.
    
    Can generate one HRU for each subbasin,
    or one HRU for each (landuse,soil,slope) combination in each subbasin
    
    The algorithm is intended to be fast: grids may be large 
    and should only be read once.
    1.  Assembles a basins map basinnumber to basindata for each subbasin, 
        where basindata is (ignoring some data not necessary to the main algortihm)
        - a map from channel number to landscape category (0 (none), 1 (floodplain) or 2 (upslope))
          to landscape unit (lsu) data.  Landscape units drain to a single channel,
          and may optionally be divided into floodplain and upslope regions.
          
    2.  Landscape unit data is
        - cell count
        - area
        - map of hru number to cell count, area, total longitude and latitude, 
          and total slope values.
        - map of landuse number to soil number to slope number to hru number
        This is done in one loop which reads the four grids in step.
        Storing both cell count and area allows for future development 
        to accept projections where different
        latitudes may have different cell areas (eg lat-long).
        hru numbers are local to each lsu.
        Note the range of the second map must be equal to the domain of the first.
    
    3.  HRUs can be removed according to user-specified thresholds.  
        This may be an area, in which case HRUs below the area are removed 
        and their areas added proprtionately to other
        HRUs in the landscape unit until none are below the threshold.  
        Or it may be percentage thresholds for landuse, soil and slope, 
        in which case it removes landuse, then soil, then slope HRUs
        below percentage thresholds, adding their areas proportionately 
        to the other HRUs within the subbasin.
        At least one HRU is retained in each landscape unit, regardless of thresholds.
    '''
    
    def __init__(self, gv, reportsCombo, dialog):
        """Constructor."""
        QObject.__init__(self)
        ## Map of basin number to basin data
        self.basins = dict()
        self._gv = gv
        self._db = gv.db
        self._iface = gv.iface
        self._reportsCombo = reportsCombo
        self._dlg = dialog
        self._progressLabel = self._dlg.progressLabel
        ## number of HRUs created in watershed
        self.HRUNum = 0
        ## Minimum elevation in watershed
        self.minElev = 0
        ## Array of elevation frequencies for whole watershed
        # Index i in array corresponds to elevation elevationGrid.Minimum + i.
        # Used to generate elevation report.
        self.elevMap = None
        ## Map from basin number to array of elevation frequencies.
        # Index i in array corresponds to elevation minElev + i.
        # Used to generate elevation report.
        # not used for grid model
        self.basinElevMap = dict()
        ## Map from SWAT basin number to list of (start of band elevation, percent of subbasin area) pairs.
        # List is None if bands not wanted or maximum elevation of subbasin below threshold.
        self.basinElevBands= dict()
        # LSU parameters
        ## Flag indicating short channels to be merged by percent or area
        self.channelMergeByPercent = True
        ## channel merge threshold
        self.channelMergeThreshold = 0
        # HRU parameters
        ## Flag indicating multiple/single HRUs per subbasin
        self.isMultiple = False
        ## For single HRU, flag indicating if dominant
        self.isDominantHRU = True
        ## Flag indicationg if filtering by area
        self.isArea = False
        ## Flag indicating if filtering  by target number of HRUs
        self.isTarget = False
        ## Flag indicating selection by area (else by percentage)
        self.useArea = False
        ## Current value of area slider
        self.areaVal = 0
        ## Current value of landuse slider
        self.landuseVal = 0
        ## Current value of soil slider
        self.soilVal = 0
        ## Current value of slope slider
        self.slopeVal = 0
        ## Current value of target slider
        self.targetVal = 0
        ## Flag indicating if full HRUs file to be generated
        self.fullHRUsWanted = False
        ## merged channels mapped to channel they were merged with
        self.mergedChannels = dict()
        ## channels merged into (range of self.mergedChannels)
        self.mergees = set()
        ## threshold (% of lsu area) for water landuse to form a reservoir
        self.reservoirThreshold = 0
        ## default nodata value used for crop and soil maps with no defined noData value (which would otherwise be None)
        self.defaultNoData = -32768
     
    ## Signal for progress messages       
    progress_signal = pyqtSignal(str)
    
    def progress(self, msg):
        """Update progress label with message; emit message for display in testing."""
        QSWATUtils.progress(msg, self._progressLabel)
        if msg != '':
            self.progress_signal.emit(msg)
        
    def generateBasins(self, progressBar, root):
        """Generate basin data from watershed, landuse, soil and slope grids.
        
        Also generate lsus shapefile, and fullHRUs shapefile if requested."""
        # in case this is a rerun
        self.basins.clear()
        elevationDs = gdal.Open(self._gv.demFile, GA_ReadOnly)
        if not elevationDs:
            QSWATUtils.error('\t ! Cannot open DEM {0}'.format(self._gv.demFile), self._gv.isBatch)
            return False
        if not self._gv.useGridModel:
            basinFile = self._gv.chBasinNoLakeFile if os.path.exists(self._gv.chBasinNoLakeFile) else self._gv.channelBasinFile
            basinDs = gdal.Open(basinFile, gdal.GA_ReadOnly)
            if not basinDs:
                QSWATUtils.error('\t ! Cannot open watershed raster {0}'.format(basinFile), self._gv.isBatch)
                return False
            basinNumberRows = basinDs.RasterYSize
            basinNumberCols = basinDs.RasterXSize
            fivePercent = basinNumberRows // 20
            basinTransform = basinDs.GetGeoTransform()
            basinBand = basinDs.GetRasterBand(1)
            basinNoData = basinBand.GetNoDataValue()
        if not self._gv.existingWshed:
            distStDs = gdal.Open(self._gv.distStFile, GA_ReadOnly)
            if not distStDs:
                QSWATUtils.error('\t ! Cannot open distance to outlets file {0}'.format(self._gv.distStFile), self._gv.isBatch)
                return False
            if not self._gv.useGridModel:
                distChDs = gdal.Open(self._gv.distChFile, GA_ReadOnly)
                if not distChDs:
                    QSWATUtils.error('\t ! Cannot open distance to channel file {0}'.format(self._gv.distChFile), self._gv.isBatch)
                    return False
        cropDs = gdal.Open(self._gv.landuseFile, GA_ReadOnly)
        if not cropDs:
            QSWATUtils.error('\t ! Cannot open landuse file {0}'.format(self._gv.landuseFile), self._gv.isBatch)
            return False
        soilDs = gdal.Open(self._gv.soilFile, GA_ReadOnly)
        if not soilDs:
            QSWATUtils.error('\t ! Cannot open soil file {0}'.format(self._gv.soilFile), self._gv.isBatch)
            return False
        slopeDs = gdal.Open(self._gv.slopeFile, GA_ReadOnly)
        if not slopeDs:
            QSWATUtils.error('\t ! Cannot open slope file {0}'.format(self._gv.slopeFile), self._gv.isBatch)
            return False
        if self._gv.useLandscapes:
            floodDs = gdal.Open(self._gv.floodFile, GA_ReadOnly)
            if not floodDs:
                QSWATUtils.error('\t ! Cannot open floodplain file {0}'.format(self._gv.floodFile), self._gv.isBatch)
                return False
        # Loop reading grids is MUCH slower if these are not stored locally
        if not self._gv.existingWshed:
            distStNumberRows = distStDs.RasterYSize
            distStNumberCols = distStDs.RasterXSize
            if not self._gv.useGridModel:
                distChNumberRows = distChDs.RasterYSize
                distChNumberCols = distChDs.RasterXSize
        cropNumberRows = cropDs.RasterYSize
        cropNumberCols = cropDs.RasterXSize
        soilNumberRows = soilDs.RasterYSize
        soilNumberCols = soilDs.RasterXSize
        slopeNumberRows = slopeDs.RasterYSize
        slopeNumberCols = slopeDs.RasterXSize
        elevationNumberRows = elevationDs.RasterYSize
        elevationNumberCols = elevationDs.RasterXSize
        if self._gv.useLandscapes:
            floodNumberRows = floodDs.RasterYSize
            floodNumberCols = floodDs.RasterXSize
        
        if not self._gv.existingWshed:
            distStTransform = distStDs.GetGeoTransform()
            if not self._gv.useGridModel:
                distChTransform = distChDs.GetGeoTransform()
        cropTransform = cropDs.GetGeoTransform()
        soilTransform = soilDs.GetGeoTransform()
        slopeTransform = slopeDs.GetGeoTransform()
        elevationTransform = elevationDs.GetGeoTransform()
        if self._gv.useLandscapes:
            floodTransform = floodDs.GetGeoTransform()
        
        # if grids have same coords we can use (col, row) from one in another
        if self._gv.useGridModel:
            cropRowFun, cropColFun = \
                QSWATTopology.translateCoords(elevationTransform, cropTransform, 
                                              elevationNumberRows, elevationNumberCols)
            soilRowFun, soilColFun = \
                QSWATTopology.translateCoords(elevationTransform, soilTransform, 
                                              elevationNumberRows, elevationNumberCols)
            slopeRowFun, slopeColFun = \
                QSWATTopology.translateCoords(elevationTransform, slopeTransform, 
                                              elevationNumberRows, elevationNumberCols)
            if self._gv.useLandscapes:
                floodRowFun, floodColFun = \
                    QSWATTopology.translateCoords(elevationTransform, floodTransform, 
                                                  elevationNumberRows, elevationNumberCols)
            if not self._gv.existingWshed:
                distStRowFun, distStColFun = \
                    QSWATTopology.translateCoords(elevationTransform, distStTransform, 
                                                  elevationNumberRows, elevationNumberCols)
        else:
            if not self._gv.existingWshed:
                distStRowFun, distStColFun = \
                    QSWATTopology.translateCoords(basinTransform, distStTransform, 
                                                  basinNumberRows, basinNumberCols)
                distChRowFun, distChColFun = \
                    QSWATTopology.translateCoords(basinTransform, distChTransform, 
                                                  basinNumberRows, basinNumberCols)
            cropRowFun, cropColFun = \
                QSWATTopology.translateCoords(basinTransform, cropTransform, 
                                              basinNumberRows, basinNumberCols)
            soilRowFun, soilColFun = \
                QSWATTopology.translateCoords(basinTransform, soilTransform, 
                                              basinNumberRows, basinNumberCols)
            slopeRowFun, slopeColFun = \
                QSWATTopology.translateCoords(basinTransform, slopeTransform, 
                                              basinNumberRows, basinNumberCols)
            elevationRowFun, elevationColFun = \
                QSWATTopology.translateCoords(basinTransform, elevationTransform, 
                                              basinNumberRows, basinNumberCols)
            if self._gv.useLandscapes:
                floodRowFun, floodColFun = \
                    QSWATTopology.translateCoords(basinTransform, floodTransform, 
                                                  basinNumberRows, basinNumberCols)
        
        if not self._gv.existingWshed:
            distStBand = distStDs.GetRasterBand(1)
            if not self._gv.useGridModel:
                distChBand = distChDs.GetRasterBand(1)
        cropBand = cropDs.GetRasterBand(1)
        soilBand = soilDs.GetRasterBand(1)
        slopeBand = slopeDs.GetRasterBand(1)
        elevationBand = elevationDs.GetRasterBand(1)
        if self._gv.useLandscapes:
            floodBand = floodDs.GetRasterBand(1)
        
        elevationNoData = elevationBand.GetNoDataValue()
        distStNoData = elevationNoData
        distChNoData = elevationNoData
        if not self._gv.existingWshed:
            distStNoData = distStBand.GetNoDataValue()
            if not self._gv.useGridModel:
                distChNoData = distChBand.GetNoDataValue()
        cropNoData = cropBand.GetNoDataValue()
        if cropNoData is None:
            cropNoData = self.defaultNoData
        soilNoData = soilBand.GetNoDataValue()
        if soilNoData is None:
            soilNoData = self.defaultNoData
        slopeNoData = slopeBand.GetNoDataValue()
        if not self._gv.useGridModel:
            self._gv.basinNoData = basinNoData
        self._gv.distStNoData = distStNoData
        self._gv.distChNoData = distChNoData
        self._gv.cropNoData = cropNoData
        self._gv.soilNoData = soilNoData
        self._gv.slopeNoData = slopeNoData
        self._gv.elevationNoData = elevationNoData
        if self._gv.useLandscapes:
            floodNoData = floodBand.GetNoDataValue()
            self._gv.floodNoData = floodNoData
        
        # counts to calculate landuse and soil overlaps
        landuseCount = 0
        landuseNoDataCount = 0
        soilCount = 0
        soilNoDataCount = 0
        
        # prepare slope bands grid
        if len(self._db.slopeLimits) > 0:
            proj = slopeDs.GetProjection()
            driver = gdal.GetDriverByName('GTiff')
            self._gv.slopeBandsFile = os.path.splitext(self._gv.slopeFile)[0] + '_bands.tif'
            QSWATUtils.removeLayerAndFiles(self._gv.slopeBandsFile, root)
            slopeBandsDs = driver.Create(self._gv.slopeBandsFile, slopeNumberCols, slopeNumberRows, 1, gdal.GDT_Byte)
            slopeBandsBand = slopeBandsDs.GetRasterBand(1)
            slopeBandsNoData = -1
            slopeBandsBand.SetNoDataValue(slopeBandsNoData)
            slopeBandsDs.SetGeoTransform(slopeTransform)
            slopeBandsDs.SetProjection(proj)
            QSWATUtils.copyPrj(self._gv.slopeFile, self._gv.slopeBandsFile)
        
        self.minElev = elevationBand.GetMinimum()
        maxElev = elevationBand.GetMaximum()
        if self.minElev is None or maxElev is None:
            (self.minElev, maxElev) = elevationBand.ComputeRasterMinMax(1)
        # convert to metres
        self.minElev *= self._gv.verticalFactor
        maxElev *= self._gv.verticalFactor
        # have seen minInt for minElev, so let's play safe
        # else can get absurdly large list of elevations
        globalMinElev = -419 # dead sea min minus 1
        globalMaxElev = 8849 # everest plus 1
        self.minElev = max(int(self.minElev), globalMinElev)
        maxElev = min(int(maxElev), globalMaxElev)
        elevMapSize = 1 + maxElev - self.minElev
        self.elevMap = [0] * elevMapSize
        
        # We read raster data in complete rows, using several rows for the grid model if necessary.
        # Complete rows should be reasonably efficient, and for the grid model
        # reading all rows necessary for each row of grid cells avoids rereading any row
        if self._gv.useGridModel:
            elevationReadRows = self._gv.gridSize
            # estimate of maximum distance to outlet
            diag = math.sqrt(self._gv.topo.dx * self._gv.topo.dx + self._gv.topo.dy * self._gv.topo.dy) * self._gv.gridSize
            # estimate of maximum distance to channel
            halfDiag = diag / 2.0
            elevationRowDepth = float(elevationReadRows) * elevationTransform[5]
            # we add an extra 2 rows since edges of rows may not
            # line up with elevation map.
            cropReadRows = max(1, int(elevationRowDepth / cropTransform[5] + 2))
            cropActReadRows = cropReadRows
            soilReadRows = max(1, int(elevationRowDepth / soilTransform[5] + 2))
            soilActReadRows = soilReadRows
            slopeReadRows = max(1, int(elevationRowDepth / slopeTransform[5] + 2))
            slopeActReadRows = slopeReadRows
            if not self._gv.existingWshed:
                distStReadRows = max(1, int(elevationRowDepth / distStTransform[5] + 2))
            else:
                distStReadRows = 0
            distStActReadRows = distStReadRows
            if self._gv.useLandscapes:
                floodReadRows = max(1, int(elevationRowDepth / floodTransform[5] + 2))
            else:
                floodReadRows = 0
            floodActReadRows = floodReadRows
            QSWATUtils.loginfo('{0}, {1}, {2}, {3}, {4} rows of landuse, soil, slope, distance to stream and flood for each grid cell' \
                               .format(cropReadRows, soilReadRows, slopeReadRows, distStReadRows, floodReadRows))
        else:
            elevationReadRows = 1
            cropReadRows = 1
            soilReadRows = 1
            slopeReadRows = 1
            basinReadRows = 1
            if not self._gv.existingWshed:
                distStReadRows = 1
                distChReadRows = 1
            if self._gv.useLandscapes:
                floodReadRows = 1
        
            # create empty arrays to hold raster data when read
            # to avoid danger of allocating and deallocating with main loop
            # currentRow is the top row when using grid model
            basinCurrentRow = -1
            basinData = numpy.empty([basinReadRows, basinNumberCols], dtype=float)
            if not self._gv.existingWshed:
                distChCurrentRow = -1
                distChData = numpy.empty([distChReadRows, distChNumberCols], dtype=float)
            if self._gv.useLandscapes:
                floodCurrentRow = -1
                floodData = numpy.empty([floodReadRows, floodNumberCols], dtype=int)
        if self._gv.useLandscapes or self.fullHRUsWanted:
            subbasinChannelLandscapeCropSoilSlopeNumbers = dict()
            # last HRU number used
            lastHru = 0
            if self._gv.useLandscapes:
                # use LSU ids to make LSU polygon shapefile (otherwise can use subbasins)
                # grid models are based on the DEM raster, and non-grid models on the basins grid
                if self._gv.useGridModel:
                    transform = elevationTransform
                    lsuRows = numpy.full([elevationReadRows, elevationNumberCols], -1, dtype=int)  # @UndefinedVariable
                else:
                    transform = basinTransform
                    lsuRow = numpy.empty((basinNumberCols,), dtype=int)
                lsuShapes = Polygonize(True, elevationNumberCols, -1, QgsPointXY(transform[0], transform[3]), transform[1], abs(transform[5]))
            if self.fullHRUsWanted:
                # grid models are based on the DEM raster, and non-grid models on the basins grid
                if self._gv.useGridModel:
                    transform = elevationTransform
                    hruRows = numpy.full([elevationReadRows, elevationNumberCols], -1, dtype=int)  # @UndefinedVariable
                else:
                    transform = basinTransform
                    hruRow = numpy.empty((basinNumberCols,), dtype=int)
                hruShapes = Polygonize(True, elevationNumberCols, -1, QgsPointXY(transform[0], transform[3]), transform[1], abs(transform[5]))
        cropCurrentRow = -1
        cropData = numpy.empty([cropReadRows, cropNumberCols], dtype=int)
        soilCurrentRow = -1
        soilData = numpy.empty([soilReadRows, soilNumberCols], dtype=int)
        slopeCurrentRow = -1
        slopeData = numpy.empty([slopeReadRows, slopeNumberCols], dtype=float)
        elevationCurrentRow = -1
        elevationData = numpy.empty([elevationReadRows, elevationNumberCols], dtype=float)
        if not self._gv.existingWshed:
            distStCurrentRow = -1
            distStData = numpy.empty([distStReadRows, distStNumberCols], dtype=float)
        if self._gv.useLandscapes:
            floodCurrentRow = -1
            floodData = numpy.empty([floodReadRows, floodNumberCols], dtype=int)
        progressCount = 0
        
        with self._db.conn as conn:
            cursor = conn.cursor()
            if self._gv.useGridModel:
                time1 = time.process_time()
                fivePercent = len(self._gv.topo.subbasinToSWATBasin) // 20
                gridCount = 0
                for chLink, chBasin in self._gv.topo.chLinkToChBasin.items():
                    if chLink in self._gv.topo.chLinkInsideLake or chLink in self._gv.topo.chLinkFromLake:
                        continue
                    # since this is for grid models
                    subbasin = chBasin
                    SWATBasin = self._gv.topo.subbasinToSWATBasin.get(chBasin, 0)
                    if SWATBasin == 0:
                        continue
                    if progressCount == fivePercent:
                        progressBar.setValue(progressBar.value() + 5)
                        progressBar.update()
                        QCoreApplication.processEvents(QEventLoop.ExcludeUserInputEvents)
                        progressCount = 1
                    else:
                        progressCount += 1
                    gridCount += 1                    
                    # centroid was taken from accumulation grid, but does not matter since in projected units
                    centreX, centreY = self._gv.topo.basinCentroids[chBasin]
                    n = elevationReadRows
                    # each grid subbasin contains n x n DEM cells
                    if n % 2 == 0:
                        # even number of rows and columns - start half a row and column NW of centre
                        (centreCol, centreRow) = QSWATTopology.projToCell(centreX - elevationTransform[1] / 2.0, centreY - elevationTransform[5] / 2.0, elevationTransform)
                        elevationTopRow = centreRow - (n - 2) // 2
                        # beware of rows or columns not dividing by n:
                        # last grid row or column may be short
                        rowRange = range(elevationTopRow, min(centreRow + (n + 2) // 2, elevationNumberRows))
                        colRange = range(centreCol - (n - 2) // 2, min(centreCol + (n + 2) // 2, elevationNumberCols))
                    else:
                        # odd number of rows and columns
                        (centreCol, centreRow) = QSWATTopology.projToCell(centreX, centreY, elevationTransform)
                        elevationTopRow = centreRow - (n - 1) // 2
                        # beware of rows or columns not dividing by n:
                        # last grid row or column may be short
                        rowRange = range(elevationTopRow, min(centreRow + (n + 1) // 2, elevationNumberRows))
                        colRange = range(centreCol - (n - 1) // 2, min(centreCol + (n + 1) // 2, elevationNumberCols))
                    data = BasinData(self._db.waterLanduse, -1)
                    # read data if necessary
                    if elevationTopRow != elevationCurrentRow:
                        if self._gv.useLandscapes:
                            for rowNum in range(n):
                                lsuShapes.addRow(lsuRows[rowNum], elevationCurrentRow + rowNum)
                            lsuRows.fill(-1)
                        if self.fullHRUsWanted and lastHru > 0: # something has been written to hruRows
                            for rowNum in range(n):
                                hruShapes.addRow(hruRows[rowNum], elevationCurrentRow + rowNum)
                            hruRows.fill(-1)
                        elevationData = elevationBand.ReadAsArray(0, elevationTopRow, elevationNumberCols, min(elevationReadRows, elevationNumberRows - elevationTopRow))
                        elevationCurrentRow = elevationTopRow
                    topY = QSWATTopology.rowToY(elevationTopRow, elevationTransform)
                    cropTopRow = cropRowFun(elevationTopRow, topY)
                    if cropTopRow != cropCurrentRow:
                        if 0 <= cropTopRow <= cropNumberRows - cropReadRows:
                            cropData = cropBand.ReadAsArray(0, cropTopRow, cropNumberCols, cropReadRows)
                            cropActReadRows = cropReadRows
                            cropCurrentRow = cropTopRow
                        elif cropNumberRows - cropTopRow < cropReadRows:
                            # runnning off the bottom of crop map
                            cropActReadRows = cropNumberRows - cropTopRow
                            if cropActReadRows >= 1:
                                cropData = cropBand.ReadAsArray(0, cropTopRow, cropNumberCols, cropActReadRows)
                                cropCurrentRow = cropTopRow
                        else:
                            cropActReadRows = 0
                    soilTopRow = soilRowFun(elevationTopRow, topY)
                    if soilTopRow != soilCurrentRow:
                        if 0 <= soilTopRow <= soilNumberRows - soilReadRows:
                            soilData = soilBand.ReadAsArray(0, soilTopRow, soilNumberCols, soilReadRows)
                            soilActReadRows = soilReadRows
                            soilCurrentRow = soilTopRow
                        elif soilNumberRows - soilTopRow < soilReadRows:
                            # runnning off the bottom of soil map
                            soilActReadRows = soilNumberRows - soilTopRow
                            if soilActReadRows >= 1:
                                soilData = soilBand.ReadAsArray(0, soilTopRow, soilNumberCols, soilActReadRows)
                                soilCurrentRow = soilTopRow
                        else:
                            soilActReadRows = 0
                    slopeTopRow = slopeRowFun(elevationTopRow, topY)
                    if slopeTopRow != slopeCurrentRow:
                        if 0 <= slopeTopRow <= slopeNumberRows - slopeReadRows:
                            slopeData = slopeBand.ReadAsArray(0, slopeTopRow, slopeNumberCols, slopeReadRows)
                            slopeActReadRows = slopeReadRows
                            slopeCurrentRow = slopeTopRow
                        elif slopeNumberRows - slopeTopRow < slopeReadRows:
                            # runnning off the bottom of slope map
                            slopeActReadRows = slopeNumberRows - slopeTopRow
                            if slopeActReadRows >= 1:
                                slopeData = slopeBand.ReadAsArray(0, slopeTopRow, slopeNumberCols, slopeActReadRows)
                                slopeCurrentRow = slopeTopRow
                        else:
                            slopeActReadRows = 0
                    if not self._gv.existingWshed:
                        distStTopRow = distStRowFun(elevationTopRow, topY)
                        if distStTopRow != distStCurrentRow:
                            if 0 <= distStTopRow <= distStNumberRows - distStReadRows:
                                distStData = distStBand.ReadAsArray(0, distStTopRow, distStNumberCols, distStReadRows)
                                distStActReadRows = distStReadRows
                                distStCurrentRow = distStTopRow
                            elif distStNumberRows - distStTopRow < distStReadRows:
                                # runnning off the bottom of distSt map
                                distStActReadRows = distStNumberRows - distStTopRow
                                if distStActReadRows >= 1:
                                    distStData = distStBand.ReadAsArray(0, distStTopRow, distStNumberCols, distStActReadRows)
                                    distStCurrentRow = distStTopRow
                            else:
                                distStActReadRows = 0
                    if self._gv.useLandscapes:
                        floodTopRow = floodRowFun(elevationTopRow, topY)
                        if floodTopRow != floodCurrentRow:
                            if 0 <= floodTopRow <= floodNumberRows - floodReadRows:
                                floodData = floodBand.ReadAsArray(0, floodTopRow, floodNumberCols, floodReadRows)
                                floodActReadRows = floodReadRows
                                floodCurrentRow = floodTopRow
                            elif floodNumberRows - floodTopRow < floodReadRows:
                                # runnning off the bottom of flood map
                                floodActReadRows = floodNumberRows - floodTopRow
                                if floodActReadRows >= 1:
                                    floodData = floodBand.ReadAsArray(0, floodTopRow, floodNumberCols, floodActReadRows)
                                    floodCurrentRow = floodTopRow
                            else:
                                floodActReadRows = 0
                    for row in rowRange:
                        y = QSWATTopology.rowToY(row, elevationTransform)
                        cropRow = cropRowFun(row, y)
                        soilRow = soilRowFun(row, y)
                        slopeRow = slopeRowFun(row, y)
                        if not self._gv.existingWshed:
                            distStRow = distStRowFun(row, y)
                        if self._gv.useLandscapes:
                            floodRow = floodRowFun(row, y)
                        for col in colRange:
                            elevation = elevationData[row - elevationTopRow, col] * self._gv.verticalFactor
                            if elevation != elevationNoData:
                                elevation = int(elevation)
                                index = elevation - self.minElev
                                # can have index too large because max not calculated properly by gdal
                                if index >= elevMapSize:
                                    extra = 1 + index - elevMapSize
                                    self.elevMap += [0] * extra
                                    elevMapSize += extra
                                self.elevMap[index] += 1
                            if self._gv.useLandscapes or self.fullHRUsWanted:
                                channelLandscapeCropSoilSlopeNumbers = subbasinChannelLandscapeCropSoilSlopeNumbers.get(subbasin, None)
                                if channelLandscapeCropSoilSlopeNumbers is None:
                                    channelLandscapeCropSoilSlopeNumbers = dict()
                                    subbasinChannelLandscapeCropSoilSlopeNumbers[subbasin] = channelLandscapeCropSoilSlopeNumbers
                            x = QSWATTopology.colToX(col, elevationTransform)
                            if 0 <= cropRow - cropTopRow < cropActReadRows:
                                cropCol = cropColFun(col, x)
                                if 0 <= cropCol < cropNumberCols:
                                    crop = cropData[cropRow - cropTopRow, cropCol]
                                else:
                                    crop = cropNoData 
                            else:
                                crop = cropNoData
                            # no data read from map is None if no noData value defined 
                            if crop is None or crop == cropNoData:
                                landuseNoDataCount += 1
                                # when using grid model small amounts of
                                # no data for crop, soil or slope could lose subbasin
                                crop = self._db.defaultLanduse
                            else:
                                landuseCount += 1
                            # use an equivalent landuse if any
                            crop = self._db.translateLanduse(int(crop))
                            if 0 <= soilRow - soilTopRow < soilActReadRows:
                                soilCol = soilColFun(col, x)
                                if 0 <= soilCol < soilNumberCols:
                                    soil = soilData[soilRow - soilTopRow, soilCol]
                                else:
                                    soil = soilNoData 
                            else:
                                soil = soilNoData
                            if soil is None or soil == soilNoData:
                                soilNoDataCount += 1
                                # when using grid model small amounts of
                                # no data for crop, soil or slope could lose subbasin
                                soil = self._db.defaultSoil
                            else:
                                soilCount += 1
                            # use an equivalent soil if any
                            soil = self._db.translateSoil(int(soil))
                            if 0 <= slopeRow - slopeTopRow < slopeActReadRows:
                                slopeCol = slopeColFun(col, x)
                                if 0 <= slopeCol < slopeNumberCols:
                                    slopeValue = slopeData[slopeRow - slopeTopRow, slopeCol]
                                else:
                                    slopeValue = slopeNoData 
                            else:
                                slopeValue = slopeNoData
                            if slopeValue != slopeNoData:
                                slope = self._db.slopeIndex(slopeValue * 100)
                            else:
                                # when using grid model small amounts of
                                # no data for crop, soil or slope could lose subbasin
                                slopeValue = 0.005
                                slope = 0
                            distSt = diag
                            distCh = halfDiag
                            if not self._gv.existingWshed:
                                if 0 <= distStRow - distStTopRow < distStActReadRows:
                                    distStCol = distStColFun(col, x)
                                    if 0 <= distStCol < distStNumberCols:
                                        distSt = distStData[distStRow - distStTopRow, distStCol]
                            if self._gv.useLandscapes:
                                if 0 <= floodRow - floodTopRow < floodActReadRows:
                                    floodCol = floodColFun(col, x)
                                    if 0 <= floodCol < floodNumberCols:
                                        flood = floodData[floodRow - floodTopRow, floodCol]
                                    else:
                                        flood = floodNoData 
                                else:
                                    flood = floodNoData
                                # floodplain maps use 1 for the floodplain and nodata elsewhere (for display purposes)
                                # We reset this to a landscape value
                                landscape = QSWATUtils._FLOODPLAIN if flood == 1 else QSWATUtils._UPSLOPE
                                SWATChannel = self._gv.topo.channelToSWATChannel.get(chLink, 0)
                                if SWATChannel > 0:
                                    lsuId = QSWATUtils.landscapeUnitId(SWATChannel, landscape)
                                    lsuRows[row - elevationTopRow, col] = lsuId
                            else:
                                landscape = QSWATUtils._NOLANDSCAPE
                            data.addCell(chLink, landscape, crop, soil, slope, self._gv.cellArea, elevation, slopeValue, distSt, distCh, x, y, self._gv)
                            self.basins[subbasin] = data
                            if self._gv.useLandscapes or self.fullHRUsWanted:
                                if crop != cropNoData and soil != soilNoData and slope != slopeNoData:
                                    hru = BasinData.getHruNumber(channelLandscapeCropSoilSlopeNumbers, lastHru, chLink, landscape, crop, soil, slope)
                                    if hru > lastHru:
                                        # new HRU number: store it
                                        lastHru = hru
                                    if self.fullHRUsWanted:
                                        hruRows[row - elevationTopRow, col] = hru
                if self._gv.useLandscapes:
                    # write final rows
                    for rowNum in range(elevationReadRows):
                        lsuShapes.addRow(lsuRows[rowNum], elevationCurrentRow + rowNum)
                if self.fullHRUsWanted:
                    # write final rows
                    for rowNum in range(elevationReadRows):
                        hruShapes.addRow(hruRows[rowNum], elevationCurrentRow + rowNum)
                time2 = time.process_time()
                QSWATUtils.loginfo('Reading grid model files took {0} seconds'.format(int(time2 - time1)))
            else:  # not grid model          
                for row in range(basinNumberRows):
                    if progressCount == fivePercent:
                        progressBar.setValue(progressBar.value() + 5)
                        progressBar.update()
                        QCoreApplication.processEvents(QEventLoop.ExcludeUserInputEvents)
                        progressCount = 1
                    else:
                        progressCount += 1
                    if row != basinCurrentRow:
                        basinData = basinBand.ReadAsArray(0, row, basinNumberCols, 1)
                    y = QSWATTopology.rowToY(row, basinTransform)
                    if not self._gv.existingWshed:
                        distStRow = distStRowFun(row, y)
                        if 0 <= distStRow < distStNumberRows and distStRow != distStCurrentRow:
                            distStCurrentRow = distStRow
                            distStData = distStBand.ReadAsArray(0, distStRow, distStNumberCols, 1)
                        distChRow = distChRowFun(row, y)
                        if 0 <= distChRow < distChNumberRows and distChRow != distChCurrentRow:
                            distChCurrentRow = distChRow
                            distChData = distChBand.ReadAsArray(0, distChRow, distChNumberCols, 1)
                    cropRow = cropRowFun(row, y)
                    if 0 <= cropRow < cropNumberRows and cropRow != cropCurrentRow:
                        cropCurrentRow = cropRow
                        cropData = cropBand.ReadAsArray(0, cropRow, cropNumberCols, 1)
                    soilRow = soilRowFun(row, y)
                    if 0 <= soilRow < soilNumberRows and soilRow != soilCurrentRow:
                        soilCurrentRow = soilRow
                        soilData = soilBand.ReadAsArray(0, soilRow, soilNumberCols, 1)
                    slopeRow = slopeRowFun(row, y)
                    if 0 <= slopeRow < slopeNumberRows and slopeRow != slopeCurrentRow:
                        if len(self._db.slopeLimits) > 0 and 0 <= slopeCurrentRow < slopeNumberRows:
                            # generate slope bands data and write it before reading next row
                            for i in range(slopeNumberCols):
                                slopeValue = slopeData[0, i]
                                slopeData[0, i] = self._db.slopeIndex(slopeValue * 100) if slopeValue != slopeNoData else slopeBandsNoData
                            slopeBandsBand.WriteArray(slopeData, 0, slopeCurrentRow)
                        slopeCurrentRow = slopeRow
                        slopeData = slopeBand.ReadAsArray(0, slopeRow, slopeNumberCols, 1)
                    elevationRow = elevationRowFun(row, y)
                    if 0 <= elevationRow < elevationNumberRows and elevationRow != elevationCurrentRow:
                        elevationCurrentRow = elevationRow
                        elevationData = elevationBand.ReadAsArray(0, elevationRow, elevationNumberCols, 1)
                    if self._gv.useLandscapes:
                        floodRow = floodRowFun(row, y)
                        if 0 <= floodRow < floodNumberRows and floodRow != floodCurrentRow:
                            floodCurrentRow = floodRow
                            floodData = floodBand.ReadAsArray(0, floodRow, floodNumberCols, 1)
                    for col in range(basinNumberCols):
                        chBasin = basinData[0, col]
                        if chBasin == basinNoData:
                            if self._gv.useLandscapes:
                                lsuRow[col] = -1
                            if self.fullHRUsWanted:
                                hruRow[col] = -1
                            continue
                        chBasin = int(chBasin)
                        chLink = self._gv.topo.chBasinToChLink.get(chBasin, -1)
                        SWATChannel = self._gv.topo.channelToSWATChannel.get(chLink, 0)
                        if SWATChannel == 0:
                            if self._gv.useLandscapes:
                                lsuRow[col] = -1
                            if self.fullHRUsWanted:
                                hruRow[col] = -1
                            continue
                        subbasin = self._gv.topo.chBasinToSubbasin.get(chBasin, -1)
                        if not self._gv.topo.isUpstreamSubbasin(subbasin):
                            if self._gv.useLandscapes or self.fullHRUsWanted:
                                channelLandscapeCropSoilSlopeNumbers = subbasinChannelLandscapeCropSoilSlopeNumbers.get(subbasin, None)
                                if channelLandscapeCropSoilSlopeNumbers is None:
                                    channelLandscapeCropSoilSlopeNumbers = dict()
                                    subbasinChannelLandscapeCropSoilSlopeNumbers[subbasin] = channelLandscapeCropSoilSlopeNumbers
                            x = QSWATTopology.colToX(col, basinTransform)
                            if not self._gv.existingWshed:
                                distStCol = distStColFun(col, x)
                                if 0 <= distStCol < distStNumberCols and 0 <= distStRow < distStNumberRows:
                                    # coerce dist to float else considered to be a numpy float
                                    distSt = float(distStData[0, distStCol])
                                else:
                                    distSt = distStNoData
                                distChCol = distChColFun(col, x)
                                if 0 <= distChCol < distChNumberCols and 0 <= distChRow < distChNumberRows:
                                    # coerce dist to float else considered to be a numpy float
                                    distCh = float(distChData[0, distChCol])
                                else:
                                    distCh = distChNoData
                            else:
                                distSt = distStNoData
                                distCh = distChNoData
                            cropCol = cropColFun(col, x)
                            if 0 <= cropCol < cropNumberCols and 0 <= cropRow < cropNumberRows:
                                crop = cropData[0, cropCol]
                                if crop is None:
                                    crop = cropNoData
                            else:
                                crop = cropNoData
                            if crop == cropNoData:
                                landuseNoDataCount += 1
                            else:
                                landuseCount += 1
                                # use an equivalent landuse if any
                                crop = self._db.translateLanduse(int(crop))
                            soilCol = soilColFun(col, x)
                            if 0 <= soilCol < soilNumberCols and 0 <= soilRow < soilNumberRows:
                                soil = soilData[0, soilCol]
                                if soil is None:
                                    soil = soilNoData
                            else:
                                soil = soilNoData
                            if soil == soilNoData:
                                soilNoDataCount += 1
                            else:
                                soilCount += 1
                                # use an equivalent soil if any
                                soil = self._db.translateSoil(int(soil))
                            slopeCol = slopeColFun(col, x)
                            if 0 <= slopeCol < slopeNumberCols and 0 <= slopeRow < slopeNumberRows:
                                slopeValue = slopeData[0, slopeCol]
                            else:
                                slopeValue = slopeNoData
                            if slopeValue != slopeNoData:
                                slope = self._db.slopeIndex(slopeValue * 100)
                            else:
                                slope = slopeBandsNoData
                            elevationCol = elevationColFun(col, x)
                            if 0 <= elevationCol < elevationNumberCols and 0 <= elevationRow < elevationNumberRows:
                                elevation = elevationData[0, elevationCol] * self._gv.verticalFactor
                            else:
                                elevation = elevationNoData
                            if elevation != elevationNoData:
                                elevation = int(elevation)
                            if self._gv.useLandscapes:
                                floodCol = floodColFun(col, x)
                                if 0 <= floodCol < floodNumberCols and 0 <= floodRow < floodNumberRows:
                                    flood = floodData[0, floodCol]
                                else:
                                    flood = floodNoData
                                # floodplain maps use 1 for the floodplain and nodata elsewhere (for display purposes)
                                # We reset this to a landscape value
                                landscape = QSWATUtils._FLOODPLAIN if flood == 1 else QSWATUtils._UPSLOPE
                                lsuId = QSWATUtils.landscapeUnitId(SWATChannel, landscape)
                                lsuRow[col] = lsuId
                            else:
                                landscape = QSWATUtils._NOLANDSCAPE
                            data = self.basins.get(subbasin, None)
                            if not data:
                                # new basin
                                self.basinElevMap[subbasin] = [0] * elevMapSize
                                if self._gv.existingWshed:
                                    farDistance = self._gv.topo.maxFlowLengths[subbasin]
                                else:
                                    # set initially negative so even the smallest actual distance will exceed it
                                    farDistance = -1
                                data = BasinData(self._db.waterLanduse, farDistance)
                                self.basins[subbasin] = data
                            data.addCell(chLink, landscape, crop, soil, slope, self._gv.cellArea, elevation, slopeValue, distSt, distCh, x, y, self._gv)
                            self.basins[subbasin] = data
                            if elevation != elevationNoData:
                                index = int(elevation) - self.minElev
                                # can have index too large because max not calculated properly by gdal
                                if index >= elevMapSize:
                                    extra = 1 + index - elevMapSize
                                    for b in list(self.basinElevMap.keys()):
                                        self.basinElevMap[b] += [0] * extra
                                    self.elevMap += [0] * extra
                                    elevMapSize += extra
                                try:
                                    self.basinElevMap[subbasin][index] += 1
                                except Exception:
                                    QSWATUtils.error('\t ! Problem in basin {0!s} reading elevation {1!s} at ({5!s}, {6!s}).  Minimum: {2!s}, maximum: {3!s}, index: {4!s}'.format(subbasin, elevation, self.minElev, maxElev, index, x, y), self._gv.isBatch)
                                    break
                                self.elevMap[index] += 1
                            if self._gv.useLandscapes or self.fullHRUsWanted:
                                if crop != cropNoData and soil != soilNoData and slope != slopeNoData:
                                    hru = BasinData.getHruNumber(channelLandscapeCropSoilSlopeNumbers, lastHru, chLink, landscape, crop, soil, slope)
                                    if hru > lastHru:
                                        # new HRU number: store it
                                        lastHru = hru
                                    if self.fullHRUsWanted:
                                        hruRow[col] = hru
                                elif self.fullHRUsWanted:
                                    hruRow[col] = -1
                        else:
                            if self._gv.useLandscapes:
                                lsuRow[col] = -1
                            if self.fullHRUsWanted:
                                hruRow[col] = -1
                    if self._gv.useLandscapes:
                        lsuShapes.addRow(lsuRow, row)
                    if self.fullHRUsWanted:
                        hruShapes.addRow(hruRow, row)
                if len(self._db.slopeLimits) > 0 and 0 <= slopeCurrentRow < slopeNumberRows:
                    # write final slope bands row
                    for i in range(slopeNumberCols):
                        slopeValue = slopeData[0, i]
                        slopeData[0, i] = self._db.slopeIndex(slopeValue * 100) if slopeValue != slopeNoData else slopeBandsNoData
                    slopeBandsBand.WriteArray(slopeData, 0, slopeCurrentRow)
            # clear some memory
            elevationDs = None
            if not self._gv.existingWshed and not self._gv.useGridModel:
                distStDs = None
                distChDs = None
            slopeDs = None
            soilDs = None
            cropDs = None
            if self._gv.useLandscapes:
                floodDs = None
            if len(self._db.slopeLimits) > 0:
                # will also flush
                slopeBandsDs = None 
            # check landuse and soil overlaps
            if landuseCount + landuseNoDataCount == 0:
                landusePercent = 0
            else:
                landusePercent = (landuseCount / (landuseCount + landuseNoDataCount)) * 100
            QSWATUtils.loginfo('Landuse cover percent: {:.1F}'.format(landusePercent))
            if landusePercent < 95:
                QSWATUtils.information('\t - WARNING: only {:.1F} percent of the watershed has defined landuse values.\n If this percentage is zero check your landuse map has the same projection as your DEM.'.format(landusePercent), self._gv.isBatch)
            if soilCount + soilNoDataCount == 0:
                soilPercent = 0
            else:
                soilPercent = (soilCount / (soilCount + soilNoDataCount)) * 100
            QSWATUtils.loginfo('Soil cover percent: {:.1F}'.format(soilPercent))
            if soilPercent < 95:
                QSWATUtils.information('\t - WARNING: only {:.1F} percent of the watershed has defined soil values.\n If this percentage is zero check your soil map has the same projection as your DEM.'.format(soilPercent), self._gv.isBatch)
            if not self.noCropOrSoilLSUs():
                return False
            if self._gv.useLandscapes:
                self.progress('\t - Creating landscape units shapes ...')
                lsuShapes.finish()
                self.progress('\t - Writing landscape units shapes ...')
                lsusLayer = self.createLSUShapefileFromShapes(lsuShapes, subbasinChannelLandscapeCropSoilSlopeNumbers)
            else:
                self.progress('\t - Writing landscape units shapes ...')
                lsusLayer = self.createLSUShapefileFromWshed()
            if lsusLayer is not None and not self._gv.useGridModel:
                # insert above dem (or hillshade if exists) in legend, so subbasin still visible
                legend = QSWATUtils._FULLLSUSLEGEND
                proj = QgsProject.instance()
                root = proj.layerTreeRoot()
                layers = root.findLayers()
                group = root.findGroup(QSWATUtils._WATERSHED_GROUP_NAME)
                demLayer = QSWATUtils.getLayerByFilename(layers, self._gv.demFile, FileTypes._DEM, None, None, None)[0]
                hillshadeLayer = QSWATUtils.getLayerByLegend(QSWATUtils._HILLSHADELEGEND, layers)
                if hillshadeLayer is not None:
                    subLayer = hillshadeLayer
                elif demLayer is not None:
                    subLayer = root.findLayer(demLayer.id())
                else:
                    subLayer = None
                if subLayer is None:
                    index: int = 0
                else:
                    index = QSWATUtils.groupIndex(group, subLayer)
                QSWATUtils.removeLayerByLegend(legend, layers)
                fullLSUsLayer = proj.addMapLayer(lsusLayer, False)
                if group is not None:
                    group.insertLayer(index, fullLSUsLayer)
                fullLSUsLayer.loadNamedStyle(QSWATUtils.join(self._gv.plugin_dir, 'lsus.qml'))
            self.progress('')
            if self.fullHRUsWanted:
                self.progress('\t - Creating FullHRUs shapes ...')
                hruShapes.finish()
                #QSWATUtils.loginfo(hruShapes.makeString())
                self.progress('\t - Writing FullHRUs shapes ...')
                if not self.createFullHRUsShapefile(hruShapes, subbasinChannelLandscapeCropSoilSlopeNumbers, progressBar, lastHru):
                    QSWATUtils.error('\t ! Unable to create FullHRUs shapefile', self._gv.isBatch)
                    self.progress('')
                else:
                    self.progress('\t - FullHRUs shapefile finished')
            # clear memory
            if not self._gv.useGridModel:
                basinDs = None
            self.saveAreas(True)
            self.progress('\t - Writing HRU data to database ...')
            if not self._db.createBasinsDataTables(cursor):
                return False
            self._db.writeBasinsData(self.basins, cursor)
            cursor = None
            conn.commit()
            self.progress('\t - Writing topographic report ...')
            self.writeTopoReport()
            self.progress('')
        return True
    
    def noCropOrSoilLSUs(self):
        """Give an error message and return false if any LSUs have no crop and soil data, nor a waterbody."""
        for basin, basinData in self.basins.items():
            for channel, channelData in basinData.lsus.items():
                for lscape, lsuData in channelData.items():
                    if len(lsuData.cropSoilSlopeNumbers) == 0 and lsuData.waterBody is None:
                        SWATBasin = self._gv.topo.subbasinToSWATBasin[basin]
                        SWATChannel = self._gv.topo.channelToSWATChannel[channel]
                        msg1 = 'There is no crop or soil data for '
                        if lscape == QSWATUtils._NOLANDSCAPE:
                            msg2 = ''
                        elif lscape == QSWATUtils._FLOODPLAIN:
                            msg2 = 'the floodplain of '
                        else:
                            msg2 = 'the upslape of '
                        msg3 = 'channel {0} in subbasin {1} (and perhaps others)'.format(SWATChannel, SWATBasin)
                        QSWATUtils.error(msg1 + msg2 + msg3, self._gv.isBatch)
                        return False
        return True
    
    def mergeChannels(self):
        """Merge channels in each basin until none are below threshold or no more can be merged.
        
        Note merging is always downstream, and this is assumed in a number of places,
        e.g. the outlet of a merged channel is the same as the outlet of the merge target,
        which has the same channel number as the target."""   
                
        def mergeCandidate(basin, lsus, channel, mergedToWaterOrPtSrc, isSmall, threshold):
            """Return a channel within the basin into which channel can be merged, else -1.
            For a candidate to be successful, channel must not be a lake or marked reservoir outlet;
            channel my not have a user defined reservoir or point source;
            channel or candidate must be small (area below threshold).
            
            Note that mergeCandidates are always downstream, and this is assumed in a number of places"""
            
            def isLakeInlet(channel):
                """Return true if channel flows into a lake."""
                for lakeData in self._gv.topo.lakesData.values():
                    if channel in lakeData.inChLinks:
                        return True
                return False
            
            def isLakeOutlet(channel):
                """Return true if a lake flows into the channel."""
                for lakeData in self._gv.topo.lakesData.values():
                    if channel == lakeData.outChLink:
                        return True
                return False
    
            def isWaterOutlet(channel):
                """Return true if there is a user-marked water body flowing directly into channel."""
                for chLink in self._gv.topo.chLinkToWater.keys():
                    if self._gv.topo.getDownChannel(chLink) == channel:
                        return True
                return False 
            
            if isWaterOutlet(channel):
                # cannot merge down because could pull outlets of channels joining downstream up into water body
                return -1
            if isLakeInlet(channel):
                # downstream channel would be in lake
                return -1
            # try downstream channel
            dsChannel = -1 if channel in mergedToWaterOrPtSrc else self._gv.topo.getDownChannel(channel)
            if dsChannel < 0:
                return -1
            else:
                nextChannel = self.mergedChannels.get(dsChannel, -1)
                if nextChannel >= 0:
                    # downstream channel dsChannel already merged with nextChannel further downstream: 
                    # try starting with dsChannel
                    return mergeCandidate(basin, lsus, dsChannel, mergedToWaterOrPtSrc, 
                                          isSmall, threshold)
            if dsChannel >= 0:
                if isLakeOutlet(dsChannel):
                    # reject as if channel inside or flowing into lake merged with one leaving
                    # its flow would no longer be into lake
                    return -1
                dsChannelData = lsus.get(dsChannel, None)
                if dsChannelData is None:
                    # different basin
                    return -1
                if not isSmall:
                    # candidate must be small:
                    if BasinData.channelArea(dsChannelData) >= threshold:
                        return -1
                return dsChannel
            return -1
        
        self.mergedChannels.clear()
        self.mergees.clear()
        # keep list of channels with water bodies or point sources,
        # and extend this list as merges are made
        mergedToWaterOrPtSrc = []
        for channel in self._gv.topo.chLinkToWater.keys():
            mergedToWaterOrPtSrc.append(channel)
        for channel in self._gv.topo.chLinkToPtSrc.keys():
            mergedToWaterOrPtSrc.append(channel)
        for basin, basinData in self.basins.items():
            lsus = basinData.getLsus()
            if len(lsus) == 1:
                # only one channel: no merge possible
                continue
            # calculate threshold for channel area in square metres
            if self.channelMergeByPercent:
                threshold = basinData.subbasinArea() * float(self.channelMergeThreshold) / 100
            else:
                threshold = float(self.channelMergeThreshold) * 1E4
            merging = True
            # replace any previous merge
            basinData.copyLsus()
            hasMerge = False
            SWATBasin = self._gv.topo.subbasinToSWATBasin[basin]
            while merging:
                merging = False
                for channel, channelData in basinData.mergedLsus.items():
                    if channel not in self.mergedChannels:
                        isSmall = BasinData.channelArea(channelData) < threshold
                        candidate = mergeCandidate(basin, basinData.mergedLsus, channel, mergedToWaterOrPtSrc, 
                                                   isSmall, threshold)
                        if candidate < 0:
                            continue
                        else:
                            SWATChannel = self._gv.topo.channelToSWATChannel[channel]
                            SWATTarget = self._gv.topo.channelToSWATChannel[candidate]
                            QSWATUtils.loginfo('Merging channel {0} ({1}) into {2} ({3}) in basin {4}'.format(SWATChannel, channel, SWATTarget, candidate, SWATBasin))
                            self.mergedChannels[channel] = candidate
                            self.mergees.add(candidate)
#                             for landscape, lsuData in channelData.iteritems():
#                                 CreateHRUs.checkConsistent(lsuData, basin, channel, landscape, 1)
#                             for landscape, lsuData in basinData.mergedLsus[candidate].iteritems():
#                                 CreateHRUs.checkConsistent(lsuData, basin, candidate, landscape, 2)
                            basinData.merge(channel, candidate)
                            #TODO: merge FullHRUs and LSUs shapefiles
#                             for landscape, lsuData in basinData.mergedLsus[candidate].iteritems():
#                                 CreateHRUs.checkConsistent(lsuData, basin, candidate, landscape, 3)
                            # if channel has a point source or reservoir, mark merged one similarly
                            if channel in mergedToWaterOrPtSrc:
                                mergedToWaterOrPtSrc.append(candidate)
                            # continue looking for merges
                            merging = True
                            # remember to retain merge
                            hasMerge = True
                            break
            if not hasMerge:
                # no merges: remove merged data
                basinData.mergedLsus = None
                
    @staticmethod        
    def checkConsistent(lsuData, basin, channel, landscape, posn):
        """Assert consistency of hru numbers between cropSoilSlopeNumbers and hru map."""
        
        hruList1 = []
        for soilSlopeNumbers in lsuData.cropSoilSlopeNumbers.values():
            for slopeNumbers in soilSlopeNumbers.values():
                for hru in slopeNumbers.values():
                    hruList1.append(hru)
        hruSet1 = set(hruList1)
        hruList2 = list(lsuData.hruMap.keys())
        assert hruSet1 == set(hruList2) and len(hruSet1) == len(hruList1), \
                '{5}: numbers {0} not consistent with hru map keys {1} for basin {2} channel {3} landscape {4}'.format(lsuData.cropSoilSlopeNumbers, hruList2, basin, channel, landscape, posn)
    
    def addReservoirs(self):
        """Add reservoirs."""
        
        def mergeDownstream(floodscape):
            """Merge floodplain reservoirs downstream."""
                
            def findDownstreamReservoir(channel, floodscape):
                """Find downstream channel reservoir that can be merged with this channel's.
                
                Can pass through channel where landscape has a non-outlet empty reservoir, as this has already been moved downstream."""
                
                dsChannel = self._gv.topo.finalDownstream(channel, self.mergedChannels)
                chBasin = self._gv.topo.chLinkToChBasin.get(dsChannel, -1)
                basin = self._gv.topo.chBasinToSubbasin.get(chBasin, -1)
                basinData = self.basins.get(basin, None)
                if basinData is not None:
                    dsChannelData = basinData.getLsus().get(dsChannel, None)
                    if dsChannelData is not None:
                        dsLsuData = dsChannelData.get(floodscape, None)
                        if dsLsuData is not None:
                            dsWaterBody = dsLsuData.waterBody
                            if dsWaterBody is not None and dsWaterBody.isReservoir():
                                if dsWaterBody.isOutlet():
                                    return None
                                if dsWaterBody.cellCount > 0:
                                    return dsWaterBody
                                else: 
                                    # continue downstream: dsChannel's reservoir has already been merged
                                    return findDownstreamReservoir(dsChannel, floodscape)
                return None
        
            for basinData in self.basins.values():
                for channel, channelData in basinData.getLsus().items():
                    lsuData = channelData.get(floodscape, None)
                    waterBody = None if lsuData is None else lsuData.waterBody
                    if waterBody is not None and waterBody.isReservoir() and not waterBody.isInlet() and waterBody.cellCount > 0:
                        dsWaterBody = findDownstreamReservoir(channel, floodscape)
                        if dsWaterBody is not None:
                            dsWaterBody.addWater(waterBody, True)
                            # leave empty water body rather than make None, so later downstream search can pass through
                            waterBody.cellCount = 0
                            
        reservoirChannels = set()
        floodscape = QSWATUtils._FLOODPLAIN if self._gv.useLandscapes else QSWATUtils._NOLANDSCAPE
        # mark water bodies, either by being user-defined or by exceeding reservoir threshold
        # then merge reservoirs
        for basinData in self.basins.values():
            for channel, channelData in basinData.getLsus().items():
                if channel in self._gv.topo.chLinkIntoLake or channel in self._gv.topo.chLinkInsideLake or channel in self._gv.topo.chLinkFromLake:
                    continue
                lsuData = channelData.get(floodscape, None)
                if lsuData is None: # eg only upslope lsu, which happens with grid model
                    continue
                waterBody = lsuData.waterBody
                wid, _, role = self._gv.topo.chLinkToWater.get(channel, (-1, None, -1))
                if wid >= 0:
                    if waterBody is None:
                        # Make an empty water body so upstream waterbodies can be merged with it.
                        # channelsData is not up to date after merging
                        # (and should not be changed by merging to allow re-merging)
                        # but the channel a water body is on can only be merged with channels upstream
                        # so its outlet data is still correct
                        channelData = self._gv.topo.channelsData[channel]
                        waterBody = WaterBody(0, 0, channelData.lowerZ, channelData.lowerX, channelData.lowerY)
                        lsuData.waterBody = waterBody
                    waterBody.id = wid
                    waterBody.setInlet()  # prevent merging downstream
                    if role == QSWATTopology._RESTYPE:
                        waterBody.setReservoir()
                    else:
                        waterBody.setPond()
                if waterBody is not None and waterBody.isUnknown():
                    # make reservoir if exceeds threshold
                    lsuData.makeReservoir(self.reservoirThreshold)
                    if waterBody.isReservoir():
                        reservoirChannels.add(channel)
        for channel in reservoirChannels:
            QSWATUtils.loginfo('Reservoir water body in channel {0} ({1})'.format(self._gv.topo.channelToSWATChannel[channel], channel))
        mergeDownstream(floodscape)
        
    def insertLSUFeatures(self, layer, fields, shapes, subbasinChannelLandscapeCropSoilSlopeNumbers):
        """ Create and add features to lsus shapefile layer.  Return True if OK."""
        lsuIndx = fields.indexFromName(QSWATTopology._LSUID)
        if lsuIndx < 0: 
            QSWATUtils.error('\t ! Cannot find field {0} in {1}'.format(QSWATTopology._LSUID, self._gv.fullLSUsFile), self._gv.isBatch)
            return False
        subIndx = fields.indexFromName(QSWATTopology._SUBBASIN)
        if subIndx < 0: 
            QSWATUtils.error('\t ! Cannot find field {0} in {1}'.format(QSWATTopology._SUBBASIN, self._gv.fullLSUsFile), self._gv.isBatch)
            return False
        chIndx = fields.indexFromName(QSWATTopology._CHANNEL)
        if chIndx < 0: 
            QSWATUtils.error('\t ! Cannot find field {0} in {1}'.format(QSWATTopology._CHANNEL, self._gv.fullLSUsFile), self._gv.isBatch)
            return False
        catIndx = fields.indexFromName(QSWATTopology._LANDSCAPE)
        if catIndx < 0: 
            QSWATUtils.error('\t ! Cannot find field {0} in {1}'.format(QSWATTopology._LANDSCAPE, self._gv.fullLSUsFile), self._gv.isBatch)
            return False
        areaIndx = fields.indexFromName(Parameters._AREA)
        if areaIndx < 0: 
            QSWATUtils.error('\t ! Cannot find field {0} in {1}'.format(Parameters._AREA, self._gv.fullLSUsFile), self._gv.isBatch)
            return False
        percentSubIndx = fields.indexFromName(Parameters._PERCENTSUB)
        if percentSubIndx < 0: 
            QSWATUtils.error('\t ! Cannot find field {0} in {1}'.format(Parameters._PERCENTSUB, self._gv.fullLSUsFile), self._gv.isBatch)
            return False
        provider = layer.dataProvider()
        for subbasin, channelLandscapeCropSoilSlopeNumbers in subbasinChannelLandscapeCropSoilSlopeNumbers.items():
            SWATBasin = self._gv.topo.subbasinToSWATBasin.get(subbasin, 0)
            if SWATBasin > 0:
                basinData = self.basins[subbasin]
                subbasinArea = basinData.subbasinArea()
                for channel, landscapeCropSoilSlopeNumbers in channelLandscapeCropSoilSlopeNumbers.items():
                    SWATChannel = self._gv.topo.channelToSWATChannel.get(channel, 0)
                    if SWATChannel > 0:
                        for landscape in landscapeCropSoilSlopeNumbers.keys():
                            lsuId = QSWATUtils.landscapeUnitId(SWATChannel, landscape)
                            geometry = shapes.getGeometry(lsuId)
                            if geometry is None:
                                QSWATUtils.error('\t ! No geometry for lsuid {0} in {1}'.format(lsuId, self._gv.fullLSUsFile), self._gv.isBatch)
                                return False
                            feature = QgsFeature()
                            feature.setFields(fields)
                            feature.setAttribute(lsuIndx, lsuId)
                            feature.setAttribute(subIndx, SWATBasin)
                            feature.setAttribute(chIndx, SWATChannel)
                            feature.setAttribute(catIndx, QSWATUtils.landscapeName(landscape, self._gv.useLeftRight, notEmpty=True))
                            shapeArea = shapes.area(lsuId)
                            feature.setAttribute(areaIndx, shapeArea / 1E4)
                            if subbasinArea == 0:
                                QSWATUtils.error('\t ! SWAT basin {0} seems to be empty'.format(SWATBasin), self._gv.isBatch)
                                percentSub = 0
                            else:
                                percentSub = (shapeArea / subbasinArea) * 100
                            feature.setAttribute(percentSubIndx, percentSub)
                            feature.setGeometry(geometry)
                            if not provider.addFeatures([feature]):
                                QSWATUtils.error('\t ! Unable to add feature to LSUs shapefile {0}'.format(self._gv.fullLSUsFile), self._gv.isBatch)
                                return False
        return True
    
    def insertHRUFeatures(self, layer, fields, shapes, subbasinChannelLandscapeCropSoilSlopeNumbers, progressBar, lastHru):
        """ Create and add features to FullHRUs shapefile.  Return True if OK."""
        subIndx = fields.indexFromName(QSWATTopology._SUBBASIN)
        if subIndx < 0: return False
        chIndx = fields.indexFromName(QSWATTopology._CHANNEL)
        if chIndx < 0: return False
        catIndx = fields.indexFromName(QSWATTopology._LANDSCAPE)
        if catIndx < 0: return False
        luseIndx = fields.indexFromName(Parameters._LANDUSE)
        if luseIndx < 0: return False
        soilIndx = fields.indexFromName(Parameters._SOIL)
        if soilIndx < 0: return False
        slopeIndx = fields.indexFromName(Parameters._SLOPEBAND)
        if slopeIndx < 0: return False
        areaIndx = fields.indexFromName(Parameters._AREA)
        if areaIndx < 0: return False
        percentSubIndx = fields.indexFromName(Parameters._PERCENTSUB)
        if percentSubIndx < 0: return False
        percentLsuIndx = fields.indexFromName(Parameters._PERCENTLSU)
        if percentLsuIndx < 0: return False
        hrusIndx = fields.indexFromName(QSWATTopology._HRUS)
        if hrusIndx < 0: return False
        linkIndx = fields.indexFromName(QSWATTopology._LINKNO)
        if linkIndx < 0: return False
        progressBar.setVisible(True)
        progressBar.setValue(0)
        fivePercent = lastHru // 20
        progressCount = 0
        progressBar.setVisible(True)
        progressBar.setValue(0)
        provider = layer.dataProvider()
        for subbasin, channelLandscapeCropSoilSlopeNumbers in subbasinChannelLandscapeCropSoilSlopeNumbers.items():
            SWATBasin = self._gv.topo.subbasinToSWATBasin.get(subbasin, 0)
            if SWATBasin > 0:
                basinData = self.basins[subbasin]
                # use original lsus
                lsus = basinData.lsus
                subbasinArea = basinData.subbasinArea()
                for channel, landscapeCropSoilSlopeNumbers in channelLandscapeCropSoilSlopeNumbers.items():
                    SWATChannel = self._gv.topo.channelToSWATChannel.get(channel, 0)
                    for landscape, cropSoilSlopeNumbers in landscapeCropSoilSlopeNumbers.items():
                        lsuArea = lsus[channel][landscape].area
                        for crop, soilSlopeNumbers in cropSoilSlopeNumbers.items():
                            for soil, slopeNumbers in soilSlopeNumbers.items():
                                for slope, hru in slopeNumbers.items():
                                    geometry = shapes.getGeometry(hru)
                                    if geometry is None:
                                        return False
                                    feature = QgsFeature()
                                    feature.setFields(fields)
                                    feature.setAttribute(subIndx, SWATBasin)
                                    feature.setAttribute(chIndx, SWATChannel)
                                    feature.setAttribute(catIndx, QSWATUtils.landscapeName(landscape, self._gv.useLeftRight, notEmpty=True))
                                    feature.setAttribute(luseIndx, self._db.getLanduseCode(crop))
                                    feature.setAttribute(soilIndx, self._db.getSoilName(soil))
                                    feature.setAttribute(slopeIndx, self._db.slopeRange(slope))
                                    shapeArea = shapes.area(hru)
                                    feature.setAttribute(areaIndx, shapeArea / 1E4)
                                    if subbasinArea == 0:
                                        QSWATUtils.error('\t ! SWAT basin {0} seems to be empty'.format(SWATBasin), self._gv.isBatch)
                                        percentSub = 0
                                    else:
                                        percentSub = (shapeArea / subbasinArea) * 100
                                    feature.setAttribute(percentSubIndx, percentSub)
                                    if lsuArea == 0:
                                        QSWATUtils.error('\t ! LSU {0} seems to be empty'.format(QSWATUtils.landscapeUnitId(SWATChannel, landscape)), self._gv.isBatch)
                                        percentLsu = 0
                                    else:
                                        percentLsu = (shapeArea / lsuArea) * 100
                                    feature.setAttribute(percentLsuIndx, percentLsu)
                                    feature.setAttribute(hrusIndx, 'NA')
                                    feature.setAttribute(linkIndx, channel)
                                    feature.setGeometry(geometry)
                                    if not provider.addFeatures([feature]):
                                        QSWATUtils.error('\t ! Unable to add feature to FullHRUs shapefile {0}'.format(self._gv.fullHRUsFile), self._gv.isBatch)
                                        progressBar.setVisible(False)
                                        return False
                                    if progressCount == fivePercent:
                                        progressBar.setValue(progressBar.value() + 5)
                                        progressCount = 1
                                    else:
                                        progressCount += 1
        progressBar.setVisible(False)
        return True
    
    def createLSUShapefileFromWshed(self):
        """Create lsus shapefile when landscapes are not in use, copying the 
        geometry from the wshed shapefile or from subbasins shapefile if using grid model.  Return lsus shapefile layer"""
        # copy wshed or subbasins shapefile 
        direc, fileName = os.path.split(self._gv.fullLSUsFile)
        baseName = os.path.splitext(fileName)[0]
        sourceShapefile = self._gv.subbasinsFile if self._gv.useGridModel else self._gv.wshedFile
        QSWATUtils.copyShapefile(sourceShapefile, baseName, direc)
        lsusLayer = QgsVectorLayer(self._gv.fullLSUsFile, 
                                   '{0} ({1})'.format(QSWATUtils._FULLLSUSLEGEND, Parameters._LSUS1),
                                   'ogr')
        fields = QgsFields()
        fields.append(QgsField(QSWATTopology._LSUID, QVariant.Int))
        # If grid model we should have subbasin, if not grid we should have channel
        lsusFields = lsusLayer.fields()
        subIndx = lsusFields.indexOf(QSWATTopology._SUBBASIN)
        if subIndx < 0:
            if self._gv.useGridModel:
                QSWATUtils.error('\t ! Cannot find field {0} in {1}'.format(QSWATTopology._SUBBASIN, sourceShapefile), self._gv.isBatch)
                return None
            fields.append(QgsField(QSWATTopology._SUBBASIN, QVariant.Int))
        chIndx = lsusFields.indexOf(QSWATTopology._CHANNEL)
        if chIndx < 0:
            if not self._gv.useGridModel:
                QSWATUtils.error('\t ! Cannot find field {0} in {1}'.format(QSWATTopology._CHANNEL, sourceShapefile), self._gv.isBatch)
                return None
            fields.append(QgsField(QSWATTopology._CHANNEL, QVariant.Int))
        fields.append(QgsField(QSWATTopology._LANDSCAPE, QVariant.String, len=20))
        areaIndx = lsusFields.indexOf(Parameters._AREA)
        if areaIndx < 0:
            fields.append(QgsField(Parameters._AREA, QVariant.Double, len=20, prec=2))
        fields.append(QgsField(Parameters._PERCENTSUB, QVariant.Double, len=20, prec=1))
        provider = lsusLayer.dataProvider()
        if not provider.addAttributes(fields):
            QSWATUtils.error('\t ! Cannot add fields to lsus shapefile {0}'.format(self._gv.fullLSUsFile), self._gv.isBatch)
            return None
        lsusLayer.updateFields()
        lsuIndx = provider.fieldNameIndex(QSWATTopology._LSUID)
        if lsuIndx < 0: 
            QSWATUtils.error('\t ! Cannot find field {0} in {1}'.format(QSWATTopology._LSUID, self._gv.fullLSUsFile), self._gv.isBatch)
            return None
        subIndx = provider.fieldNameIndex(QSWATTopology._SUBBASIN)
        if subIndx < 0: 
            QSWATUtils.error('\t ! Cannot find field {0} in {1}'.format(QSWATTopology._SUBBASIN, self._gv.fullLSUsFile), self._gv.isBatch)
            return None
        chIndx = provider.fieldNameIndex(QSWATTopology._CHANNEL)
        if chIndx < 0:  
            QSWATUtils.error('\t ! Cannot find field {0} in {1}'.format(QSWATTopology._CHANNEL, self._gv.fullLSUsFile), self._gv.isBatch)
            return None
        lscapeIndx = provider.fieldNameIndex(QSWATTopology._LANDSCAPE)
        if lscapeIndx < 0:  
            QSWATUtils.error('\t ! Cannot find field {0} in {1}'.format(QSWATTopology._LANDSCAPE, self._gv.fullLSUsFile), self._gv.isBatch)
            return None
        areaIndx = provider.fieldNameIndex(Parameters._AREA)
        if areaIndx < 0:
            QSWATUtils.error('\t ! Cannot find field {0} in {1}'.format(Parameters._AREA, self._gv.fullLSUsFile), self._gv.isBatch)
            return None
        percentIndx = provider.fieldNameIndex(Parameters._PERCENTSUB)
        if percentIndx < 0:  
            QSWATUtils.error('\t ! Cannot find field {0} in {1}'.format(Parameters._PERCENTSUB, self._gv.fullLSUsFile), self._gv.isBatch)
            return None
        polyIndx = provider.fieldNameIndex(QSWATTopology._POLYGONID)
        if polyIndx < 0: 
            QSWATUtils.error('\t ! Cannot find field {0} in {1}'.format(QSWATTopology._POLYGONID, self._gv.fullLSUsFile), self._gv.isBatch)
            return None
        if self._gv.useGridModel:
            downIndx = provider.fieldNameIndex(QSWATTopology._DOWNID)
            if downIndx < 0: 
                QSWATUtils.error('\t ! Cannot find field {0} in {1}'.format(QSWATTopology._DOWNID, self._gv.fullLSUsFile), self._gv.isBatch)
                return None
        request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([polyIndx, subIndx, chIndx, areaIndx])
        mmap = dict()
        toDelete = []
        for f in provider.getFeatures(request):
            if self._gv.useGridModel:
                basin = f[polyIndx]
                chLink = self._gv.topo.chBasinToChLink[basin]
                if chLink in self._gv.topo.chLinkInsideLake or chLink in self._gv.topo.chLinkFromLake:
                    toDelete.append(f.id())
                    continue
                SWATBasin = f[subIndx]
                if SWATBasin == 0:
                    toDelete.append(f.id())
                    continue
                channel = self._gv.topo.chBasinToChLink[basin]
                SWATChannel = self._gv.topo.channelToSWATChannel.get(channel, 0)
                if SWATChannel == 0:
                    toDelete.append(f.id())
                    continue
            else:
                chBasin = f[polyIndx]
                area = f[areaIndx]
                SWATChannel = f[chIndx]
                # area can be zero if LSU within lake
                if SWATChannel == 0 or area == 0:
                    toDelete.append(f.id())
                    continue
                channel = self._gv.topo.SWATChannelToChannel[SWATChannel]
                basin = self._gv.topo.chBasinToSubbasin.get(chBasin, -1)
                SWATBasin = self._gv.topo.subbasinToSWATBasin.get(basin, 0)
                if SWATBasin == 0:
                    toDelete.append(f.id())
                    continue
            basinData = self.basins.get(basin, None)
            if basinData is not None:
                subbasinCells = basinData.subbasinCellCount()
                # use original lsus
                lsus = basinData.lsus
                if channel not in lsus:
                    # too small?
                    if self._gv.useGridModel:
                        area = f.geometry().area() / 1E4
                    QSWATUtils.loginfo('Ignoring LSU for link {0} with area {1}'.format(channel, area))
                    toDelete.append(f.id())
                    continue
                lsuData = lsus[channel][QSWATUtils._NOLANDSCAPE]
                lsuCells = lsuData.cellCount
                lsuAreaHa = lsuData.area / 1E4
                if subbasinCells == 0:
                    QSWATUtils.error('\t ! SWAT basin {0} seems to be empty'.format(SWATBasin), self._gv.isBatch)
                    percentSub = 0
                else:
                    percentSub = (lsuCells / subbasinCells) * 100
                lsuId = QSWATUtils.landscapeUnitId(SWATChannel, QSWATUtils._NOLANDSCAPE)
                mmap2 = dict()
                mmap2[lsuIndx] = lsuId
                mmap2[subIndx] = SWATBasin
                mmap2[chIndx] = SWATChannel
                mmap2[lscapeIndx] = QSWATUtils.landscapeName(QSWATUtils._NOLANDSCAPE, self._gv.useLeftRight, notEmpty=True)
                mmap2[areaIndx] = lsuAreaHa
                mmap2[percentIndx] = percentSub
                mmap[f.id()] = mmap2
        if not provider.changeAttributeValues(mmap):
            QSWATUtils.error('\t ! Cannot change attributes of LSUs shapefile {0}'.format(self._gv.fullLSUsFile), self._gv.isBatch)
            return None
        if len(toDelete) > 0:
            if not provider.deleteFeatures(toDelete):
                QSWATUtils.error('\t ! Failed to delete redundant features from LSUs shapefile {0}'.format(self._gv.fullLSUsFile), self._gv.isBatch)
                return None
        # delete PolygonId field, plus DownId if using grid model
        if self._gv.useGridModel:
            deletions = [polyIndx, downIndx]
        else:
            deletions = [polyIndx]
        provider.deleteAttributes(deletions)
        lsusLayer.updateFields()
        return lsusLayer
    
    def createLSUShapefileFromShapes(self, lsuShapes, subbasinChannelLandscapeCropSoilSlopeNumbers):
        """Create LSU shapefile when landscapes in use.  Return LSU shapefile layer if successful, else None"""
        root = QgsProject.instance().layerTreeRoot()
        ft = FileTypes._LSUS
        legend = QSWATUtils._FULLLSUSLEGEND
        if QSWATUtils.shapefileExists(self._gv.fullLSUsFile):
            layer = QSWATUtils.getLayerByFilename(root.findLayers(), self._gv.fullLSUsFile, ft, 
                                                              None, None, None)[0]
            if layer is None:
                layer = QgsVectorLayer(self._gv.fullLSUsFile, '{0} ({1})'.format(legend, Parameters._LSUS1), 'ogr')
            if not QSWATUtils.removeAllFeatures(layer):
                QSWATUtils.error('\t ! Failed to delete features from {0}.  Please delete the file manually and try again'.format(self._gv.fullLSUsFile), self._gv.isBatch)
                return
            fields = layer.fields()
        else:
            QSWATUtils.tryRemoveLayerAndFiles(self._gv.fullLSUsFile, root)
            fields = QgsFields()
            fields.append(QgsField(QSWATTopology._LSUID, QVariant.Int))
            fields.append(QgsField(QSWATTopology._SUBBASIN, QVariant.Int))
            fields.append(QgsField(QSWATTopology._CHANNEL, QVariant.Int))
            fields.append(QgsField(QSWATTopology._LANDSCAPE, QVariant.String, len=20))
            fields.append(QgsField(Parameters._AREA, QVariant.Double, len=20, prec=2))
            fields.append(QgsField(Parameters._PERCENTSUB, QVariant.Double, len=20, prec=1))
            writer = QgsVectorFileWriter(self._gv.fullLSUsFile, 'CP1250', fields, QgsWkbTypes.MultiPolygon, self._gv.topo.crsProject, 'ESRI Shapefile')
            if writer.hasError() != QgsVectorFileWriter.NoError:
                QSWATUtils.error('\t ! Cannot create LSUs shapefile {0}: {1}'.format(self._gv.fullLSUsFile, writer.errorMessage()), self._gv.isBatch)
                return None
            # delete the writer to flush
            writer.flushBuffer()
            del writer
            QSWATUtils.copyPrj(self._gv.basinFile, self._gv.fullLSUsFile)
            layer = QgsVectorLayer(self._gv.fullLSUsFile, '{0} ({1})'.format(legend, Parameters._LSUS1), 'ogr')
        if self.insertLSUFeatures(layer, fields, lsuShapes, subbasinChannelLandscapeCropSoilSlopeNumbers):
            return layer
        else:
            return None
    
    def createFullHRUsShapefile(self, hruShapes, subbasinChannelLandscapeCropSoilSlopeNumbers, progressBar, lastHru):
        """Create FullHRUs shapefile."""
        root = QgsProject.instance().layerTreeRoot()
        ft = FileTypes._HRUS
        legend = QSWATUtils._FULLHRUSLEGEND
        if QSWATUtils.shapefileExists(self._gv.fullHRUsFile):
            layer = QSWATUtils.getLayerByFilename(root.findLayers(), self._gv.fullHRUsFile, ft, 
                                                              None, None, None)[0]
            if layer is None:
                layer = QgsVectorLayer(self._gv.fullHRUsFile, '{0} ({1})'.format(legend, QFileInfo(self._gv.fullHRUsFile).baseName()), 'ogr')
            if not QSWATUtils.removeAllFeatures(layer):
                QSWATUtils.error('\t ! Failed to delete features from {0}.  Please delete the file manually and try again'.format(self._gv.fullHRUsFile), self._gv.isBatch)
                return
            fields = layer.fields()
        else:
            QSWATUtils.removeLayerAndFiles(self._gv.fullHRUsFile, root)
            fields = QgsFields()
            fields.append(QgsField(QSWATTopology._SUBBASIN, QVariant.Int))
            fields.append(QgsField(QSWATTopology._CHANNEL, QVariant.Int))
            fields.append(QgsField(QSWATTopology._LANDSCAPE, QVariant.String, len=20))
            fields.append(QgsField(Parameters._LANDUSE, QVariant.String, len=20))
            fields.append(QgsField(Parameters._SOIL, QVariant.String, len=20))
            fields.append(QgsField(Parameters._SLOPEBAND, QVariant.String, len=20))
            fields.append(QgsField(Parameters._AREA, QVariant.Double, len=20, prec=2))
            fields.append(QgsField(Parameters._PERCENTSUB, QVariant.Double, len=20, prec=1))
            fields.append(QgsField(Parameters._PERCENTLSU, QVariant.Double, len=20, prec=1))
            fields.append(QgsField(QSWATTopology._HRUS, QVariant.String, len=20))
            fields.append(QgsField(QSWATTopology._LINKNO, QVariant.Int))
            writer = QgsVectorFileWriter(self._gv.fullHRUsFile, 'CP1250', fields, QgsWkbTypes.MultiPolygon, self._gv.topo.crsProject, 'ESRI Shapefile')
            if writer.hasError() != QgsVectorFileWriter.NoError:
                QSWATUtils.error('\t ! Cannot create FullHRUs shapefile {0}: {1}'.format(self._gv.fullHRUsFile, writer.errorMessage()), self._gv.isBatch)
                return False
            # delete the writer to flush
            writer.flushBuffer()
            del writer
            QSWATUtils.copyPrj(self._gv.demFile, self._gv.fullHRUsFile)
            layer = QgsVectorLayer(self._gv.fullHRUsFile, '{0} ({1})'.format(legend, QFileInfo(self._gv.fullHRUsFile).baseName()), 'ogr')
        if self.insertHRUFeatures(layer, fields, hruShapes, subbasinChannelLandscapeCropSoilSlopeNumbers, progressBar, lastHru):
            # insert above dem (or hillshade if exists) in legend, so streams and watershed still visible
            proj = QgsProject.instance()
            root = proj.layerTreeRoot()
            layers = root.findLayers()
            demLayer = QSWATUtils.getLayerByFilename(layers, self._gv.demFile, FileTypes._DEM, None, None, None)[0]
            hillshadeLayer = QSWATUtils.getLayerByLegend(QSWATUtils._HILLSHADELEGEND, layers)
            if hillshadeLayer is not None:
                subLayer = hillshadeLayer
            elif demLayer is not None:
                subLayer = root.findLayer(demLayer.id())
            else:
                subLayer = None
            group = root.findGroup(QSWATUtils._WATERSHED_GROUP_NAME)
            index = QSWATUtils.groupIndex(group, subLayer)
            QSWATUtils.removeLayerByLegend(legend, layers)
            fullHRUsLayer = proj.addMapLayer(layer, False)
            if group is not None:
                group.insertLayer(index, fullHRUsLayer)
            styleFile = 'fullhrus.qml'
            fullHRUsLayer.loadNamedStyle(QSWATUtils.join(self._gv.plugin_dir, styleFile))
            return True
        else:
            return False
        
    def countHRUs(self):
        """Count HRUs in watershed."""
        count = 0
        for data in self.basins.values():
            for channelData in data.getLsus().values():
                for lsuData in channelData.values():
                    count += len(lsuData.hruMap)
        return count
    
    def countChannels(self):
        """Count channels in watershed.
        
        Note this includes channels in lakes."""
        count = 0
        for data in self.basins.values():
            count += len(data.getLsus())
        return count
    
    def countChannelsInLake(self):
        """Count channels inside lakes that have not been merged."""
        count = 0
        for ch in self._gv.topo.chLinkInsideLake.keys():
            if ch not in self.mergedChannels:
                count += 1
        return count
        
    def countLsus(self):
        """Count landscape units in watershed."""
        count = 0
        for data in self.basins.values():
            for channelData in data.getLsus().values():
                count += len(channelData)
        return count
        
    def saveAreas(self, isOriginal):
        """Create area maps for each subbasin."""
        if self._gv.useGridModel:
            chLinksByLakes = list(self._gv.topo.chLinkIntoLake.keys()) + list(self._gv.topo.chLinkInsideLake.keys()) + list(self._gv.topo.chLinkFromLake.keys())
        else:
            chLinksByLakes = list(self._gv.topo.chLinkIntoLake.keys()) + list(self._gv.topo.chLinkInsideLake.keys())
        for data in self.basins.values():
            data.setAreas(isOriginal, chLinksByLakes, self._gv.db.waterLanduse)
        
    def maxLandscapeArea(self):
        """
        Return the maximum landscape area in hectares.
        """
        maximum = 0
        for basinData in self.basins.values():
            for channelData in basinData.getLsus().values():
                for lsuData in channelData.values():
                    area = lsuData.area
                    if area > maximum: maximum = area
        return maximum / 10000 # convert to hectares
    
    def minMaxCropVal(self, useArea):
        """
        Return the minimum across the watershed of the largest percentage (or area in hectares)
        of a crop within each landscape unit.
        
        Finds the least percentage (or area) across the landscape units of the percentages 
        (or areas) of the dominant crop in the landscape units.  This is the maximum percentage (or area)
        acceptable for the minuimum crop percentage (or area) to be used to form multiple HRUs.  
        If the user could choose a percentage (or area) above this figure then at
        least one landscape unit would have no HRU.
        This figure is only advisory since limits are checked during removal.
        """
        minMax = float('inf') if useArea else 100
        for basinData in self.basins.values():
            for channel, channelData in basinData.getLsus().items():
                for landscape, lsuData in channelData.items():
                    cropAreas = lsuData.originalCropAreas
                    crop, maxArea = BasinData.dominantKey(cropAreas)
                    if crop < 0:
                        # empty map - perhaps all water
                        continue
                    if useArea:
                        val = maxArea / 1E4
                    elif lsuData.cropSoilSlopeArea == 0:
                        SWATChannel = self._gv.topo.channelToSWATChannel[channel]
                        QSWATUtils.error('\t ! LSU {0} seems to have no land area'.format(QSWATUtils.landscapeUnitId(SWATChannel, landscape)), self._gv.isBatch)
                        val = 0
                    else:
                        val = (maxArea / lsuData.cropSoilSlopeArea) * 100
                    # QSWATUtils.loginfo('Max crop value {0} for landscape {2} in basin {1}'.format(int(val), self._gv.topo.subbasinToSWATBasin[basin], landscape))
                    if val < minMax: minMax = val
        return minMax
    
    def minMaxSoilArea(self):
        """
        Return the minimum across the watershed of the largest area in hectares
        of a soil within each landscape unit.
        
        Finds the least area across the landscape units of the areas of the dominant soil
        in the landscape units.  This is the maximum area
        acceptable for the minuimum soil area to be used to form multiple HRUs.  
        If the user could choose an area above this figure then at
        least one landscape unit would have no HRU.
        This figure is only advisory since limits are checked during removal.
        """
        minMax = float('inf')
        for basinData in self.basins.values():
            for channelData in basinData.getLsus().values():
                for lsuData in channelData.values():
                    soilAreas = lsuData.originalSoilAreas
                    soil, maxArea = BasinData.dominantKey(soilAreas)
                    if soil < 0:
                        # empty map - perhaps all water
                        continue
                    val = maxArea / 10000
                    # QSWATUtils.loginfo('Max soil area {0} for landscape {2} in basin {1}'.format(int(val), self._gv.topo.subbasinToSWATBasin[basin], landscape))
                    if val < minMax: minMax = val
        return minMax
    
    def minMaxSlopeArea(self):
        """
        Return the minimum across the watershed of the largest area in hectares
        of a slope within each landscape unit.
        
        Finds the least area across the landscape units of the areas of the dominant slope
        in the subbasins.  This is the maximum area
        acceptable for the minuimum slope area to be used to form multiple HRUs.  
        If the user could choose an area above this figure then at
        least one landscape unit would have no HRU.
        This figure is only advisory since limits are checked during removal.
        """
        minMax = float('inf')
        for basinData in self.basins.values():
            for channelData in basinData.getLsus().values():
                for lsuData in channelData.values():
                    slopeAreas = lsuData.originalSlopeAreas
                    slope, slopeArea = BasinData.dominantKey(slopeAreas)
                    if slope < 0:
                        # empty map - perhaps all water
                        continue
                    val = slopeArea / 10000
                    # QSWATUtils.loginfo('Max slope area {0} for landsacape {2} in basin {1}'.format(int(val), self._gv.topo.subbasinToSWATBasin[basin], landscape))
                    if val < minMax: minMax = val
        return minMax        

    def minMaxSoilPercent(self, minCropVal):
        """
        Return the minimum across the watershed of the percentages
        of the dominant soil in the crops included by minCropVal.

        Finds the least percentage across the watershed of the percentages 
        of the dominant soil in the crops included by minCropVal.  
        This is the maximum percentage acceptable for the minimum soil
        percentage to be used to form multiple HRUs.  
        If the user could choose a percentage above this figure then
        at least one soil in one landscape unit would have no HRU.
        This figure is only advisory since limits are checked during removal.
        """
        minMax = 100
        for basinData in self.basins.values():
            for channel, channelData in basinData.getLsus().items():
                for landscape, lsuData in channelData.items():
                    cropAreas = lsuData.originalCropAreas
                    for (crop, cropArea) in cropAreas.items():
                        if lsuData.cropSoilSlopeArea == 0:
                            SWATChannel = self._gv.topo.channelToSWATChannel[channel]
                            QSWATUtils.error('\t ! LSU {0} seems to have no land area'.format(QSWATUtils.landscapeUnitId(SWATChannel, landscape)), self._gv.isBatch)
                            cropVal = 0
                        else:
                            cropVal = (cropArea / lsuData.cropSoilSlopeArea) * 100
                        if cropVal >= minCropVal:
                            # crop will be included.  Find the maximum area or percentage for soils for this crop.
                            maximum = 0
                            soilSlopeNumbers = lsuData.cropSoilSlopeNumbers[crop]
                            for slopeNumbers in soilSlopeNumbers.values():
                                area = 0
                                for hru in slopeNumbers.values():
                                    cellData = lsuData.hruMap[hru]
                                    area += cellData.area
                                if cropArea == 0:
                                    SWATChannel = self._gv.topo.channelToSWATChannel[channel]
                                    cropName = self._db.getLanduseCode(crop)
                                    QSWATUtils.error('\t ! crop {0} in LSU {1} seems to have no area'.format(cropName, QSWATUtils.landscapeUnitId(SWATChannel, landscape)), self._gv.isBatch)
                                    soilVal = 0.0
                                else:
                                    soilVal = (area / cropArea) * 100
                                if soilVal > maximum: maximum = soilVal
                            if maximum < minMax: minMax = maximum
        return minMax

    def minMaxSlopePercent(self, minCropVal, minSoilVal):
        """
        Return the minimum across the watershed of the percentages 
        of the dominant slope in the crops and soils included by 
        minCropPercent and minSoilPercent.
        
        Finds the least percentage across the watershed of the percentages 
        of the dominant slope in the crops and soils included by 
        minCropVal and minSoilVal.
        This is the maximum percentage  acceptable for the minimum slope
        percentage to be used to form multiple HRUs.  
        If the user could choose a percentage above this figure then
        at least one slope in one landscape unit would have no HRU.
        This figure is only advisory since limits are checked during removal.
        """
        minMax = 100
        for basinData in self.basins.values():
            for channel, channelData in basinData.getLsus().items():
                for landscape, lsuData in channelData.items():
                    cropAreas = lsuData.originalCropAreas
                    for (crop, cropArea) in cropAreas.items():
                        if lsuData.cropSoilSlopeArea == 0:
                            SWATChannel = self._gv.topo.channelToSWATChannel[channel]
                            QSWATUtils.error('\t ! LSU {0} seems to have no land area'.format(QSWATUtils.landscapeUnitId(SWATChannel, landscape)), self._gv.isBatch)
                            cropVal = 0
                        else:
                            cropVal = (cropArea / lsuData.cropSoilSlopeArea) * 100
                        if cropVal >= minCropVal:
                            # crop will be included.
                            soilSlopeNumbers = lsuData.cropSoilSlopeNumbers[crop]
                            for soil, slopeNumbers in soilSlopeNumbers.items():
                                # first find if this soil is to be included
                                soilArea = 0
                                for hru in slopeNumbers.values():
                                    cellData = lsuData.hruMap[hru]
                                    soilArea += cellData.area
                                if cropArea == 0:
                                    SWATChannel = self._gv.topo.channelToSWATChannel[channel]
                                    cropName = self._db.getLanduseCode(crop)
                                    QSWATUtils.error('\t ! crop {0} in LSU {1} seems to have no area'.format(cropName, QSWATUtils.landscapeUnitId(SWATChannel, landscape)), self._gv.isBatch)
                                    soilVal = 0
                                else:
                                    soilVal = (soilArea / cropArea) * 100
                                if soilVal >= minSoilVal:
                                    # soil will be included.
                                    # Find the maximum percentage area for slopes for this soil.
                                    maximum = 0
                                    for hru in slopeNumbers.values():
                                        cellData = lsuData.hruMap[hru]
                                        if soilArea == 0:
                                            SWATChannel = self._gv.topo.channelToSWATChannel[channel]
                                            soilName = self._db.getSoilName(soil)
                                            QSWATUtils.error('\t ! soil {0} in LSU {1} seems to have no area'.format(soilName, QSWATUtils.landscapeUnitId(SWATChannel, landscape)), self._gv.isBatch)
                                            slopeVal = 0
                                        else:
                                            slopeVal = (cellData.area / soilArea) * 100
                                            if slopeVal > maximum: maximum = slopeVal
                                    if maximum < minMax: minMax = maximum
        return minMax

# beware = this function is no longer used and is also out of date because 
# it has not been revised to allow for both area and percentages as thresholds
# nor does it include landscapes
#===============================================================================
#     def cropSoilAndSlopeThresholdsAreOK(self):
#         """
#         Check that at least one hru will be left in each subbasin 
#         after applying thresholds.
#         
#         This is really a precondition for removeSmallHRUsByThreshold.
#         It checks that at least one crop will be left
#         in each subbasin, that at least one soil will be left for each crop,
#         and that at least one slope will be left for each included crop and 
#         soil combination.
#         """
#         minCropVal = self.landuseVal
#         minSoilVal = self.soilVal
#         minSlopeVal = self.slopeVal
# 
#         for basinData in self.basins.itervalues():
#             cropAreas = basinData.originalCropAreas
#             cropFound = False
#             minCropArea = minCropVal * 10000 if self.useArea else (float(basinData.landscapeCropSoilSlopeArea) * minCropVal) / 100
#             for (crop, area) in cropAreas.iteritems():
#                 cropFound = cropFound or (area >= minCropArea)
#                 if area >= minCropArea:
#                     # now check soils for this crop
#                     soilFound = False
#                     minSoilArea = minSoilVal * 10000 if self.useArea else (float(area) * minSoilVal) / 100
#                     soilSlopeNumbers = basinData.cropSoilSlopeNumbers[crop]
#                     for slopeNumbers in soilSlopeNumbers.itervalues():
#                         soilArea = 0
#                         for hru in slopeNumbers.itervalues():
#                             cellData = basinData.hruMap[hru]
#                             soilArea += cellData.area
#                         soilFound = soilFound or (soilArea >= minSoilArea)
#                         if soilArea >= minSoilArea:
#                             # now sheck for slopes for this soil
#                             slopeFound = False
#                             minSlopeArea = minSlopeVal * 10000 if self.useArea else (float(soilArea) * minSlopeVal) / 100
#                             for hru in slopeNumbers.itervalues():
#                                 cellData = basinData.hruMap[hru]
#                                 slopeFound = (cellData.area >= minSlopeArea)
#                                 if slopeFound: break
#                             if not slopeFound: return False
#                     if not soilFound: return False
#             if not cropFound: return False
#         return True
#===============================================================================

    def selectDominantHRUs(self):
        """Create in each landscape unit a single HRU with the crop, soil and slope of the largest HRU."""
        for basin, basinData in self.basins.items():
            for channel, channelData in basinData.getLsus().items():
                for landscape, lsuData in channelData.items():
                    allowWaterHRU = lsuData.waterBody is None or lsuData.waterBody.isUnknown()
                    (crop, soil, slope) = lsuData.getDominantHRU(self._gv.db.waterLanduse, allowWaterHRU)
                    if crop < 0:
                        raise ValueError('No crop data for channel {2!s} landscape unit {1!s} in basin {0!s}'.format(basin, landscape, channel))
                    if allowWaterHRU:
                        cellCount = lsuData.cellCount
                        area = lsuData.area
                        frac = 1
                    else:
                        # fraction of lsu that is HRU
                        frac = 1.0 - lsuData.waterBody.originalArea / lsuData.area
                        # water body cellCount may have been made zero, so reconstruct
                        cellCount = int(lsuData.cellCount * frac + 0.5)
                        area = lsuData.area - lsuData.waterBody.originalArea
                    cellData = CellData(cellCount, area, lsuData.totalElevation * frac, lsuData.totalSlope * frac,
                                        lsuData.totalLongitude * frac, lsuData.totalLatitude * frac, crop)
                    lsuData.hruMap = dict()
                    lsuData.hruMap[1] = cellData
                    lsuData.cropSoilSlopeNumbers = dict()
                    lsuData.cropSoilSlopeNumbers[crop] = dict()
                    lsuData.cropSoilSlopeNumbers[crop][soil] = dict()
                    lsuData.cropSoilSlopeNumbers[crop][soil][slope] = 1
                
    def selectDominantLanduseSoilSlope(self): 
        """Create in each landscape unit a single HRU with the dominant landuse, soil and slope."""
        for basin, basinData in self.basins.items():
            for channel, channelData in basinData.getLsus().items(): 
                for landscape, lsuData in channelData.items():
                    allowWaterHRU = lsuData.waterBody is None or lsuData.waterBody.isUnknown() 
                    cropAreas =  lsuData.originalCropAreas
                    if not allowWaterHRU:
                        cropAreas.pop(self._gv.db.waterLanduse, None)       
                    crop, _ = BasinData.dominantKey(cropAreas)
                    if crop < 0:
                        raise ValueError('No crop data for channel {2!s} landscape unit {1!s} in basin {0!s}'.format(basin, landscape, channel))
                    soil, _ = BasinData.dominantKey(lsuData.originalSoilAreas)
                    if soil < 0:
                        raise ValueError('No soil data for channel {2!s} landscape unit {1!s} in basin {0!s}'.format(basin, landscape, channel))
                    slope, _ = BasinData.dominantKey(lsuData.originalSlopeAreas)
                    if slope < 0:
                        raise ValueError('No slope data for channel {2!s} landscape unit {1!s} in basin {0!s}'.format(basin, landscape, channel))
                    if allowWaterHRU:
                        cellCount = lsuData.cellCount
                        area = lsuData.area
                        frac = 1
                    else:
                        # fraction of lsu that is HRU
                        frac = 1.0 - lsuData.waterBody.originalArea / lsuData.area
                        # water body cellCount may have been made zero, so reconstruct
                        cellCount = int(lsuData.cellCount * frac + 0.5)
                        area = lsuData.area - lsuData.waterBody.originalArea
                    cellData = CellData(cellCount, area, lsuData.totalElevation * frac, lsuData.totalSlope * frac,
                                        lsuData.totalLongitude * frac, lsuData.totalLatitude * frac, crop)
                    lsuData.hruMap = dict()
                    lsuData.hruMap[1] = cellData
                    lsuData.cropSoilSlopeNumbers = dict()
                    lsuData.cropSoilSlopeNumbers[crop] = dict()
                    lsuData.cropSoilSlopeNumbers[crop][soil] = dict()
                    lsuData.cropSoilSlopeNumbers[crop][soil][slope] = 1
    
    def removeSmallHRUsByArea(self):
        """
        Remove from basins data HRUs that are below the minimum area or minumum percent.
        
        Removes from basins data HRUs that are below areaVal 
        (which is in hectares if useArea is true, else is a percentage) 
        and redistributes their areas and slope 
        totals in proportion to the other HRUs.
        Crop, soil, and slope nodata cells are also redistributed, 
        so the total area of the retained HRUs should eventually be the 
        total area of the subbasin's landscape units.
        
        The algorithm removes one HRU at a time, the smallest, 
        redistributing its area to the others, until all are above the 
        threshold or only one is left.  So an HRU that was initially below the
        threshold may be retained because redistribution from smaller 
        ones lifts its area above the threshold.
        
        The area of a landscape unit can be below the minimum area, 
        in which case the dominant HRU will finally be left.
        """
            
        for basin, basinData in self.basins.items():
            for channel, channelData in basinData.getLsus().items(): 
                for landscape, lsuData in channelData.items():
                    count = len(lsuData.hruMap)
                    # self.areaVal is either an area in hectares or a percentage of the subbasin
                    # in either case convert to square metres
                    threshold = self.areaVal * 10000 if self.useArea else (lsuData.cropSoilSlopeArea * self.areaVal) / 100
                    exemptWater = lsuData.waterBody is not None and not lsuData.waterBody.isUnknown()
                    hruArea = lsuData.area
                    areaToRedistribute = 0
                    unfinished = True
                    while unfinished:
                        # find smallest non-exempt HRU
                        minCrop = 0
                        minSoil = 0
                        minSlope = 0
                        minHru = 0
                        minArea = threshold
                        for (crop, soilSlopeNumbers) in lsuData.cropSoilSlopeNumbers.items():
                            if not self._gv.isExempt(crop) and not (crop == self._gv.db.waterLanduse and exemptWater):
                                for (soil, slopeNumbers) in soilSlopeNumbers.items():
                                    for (slope, hru) in slopeNumbers.items():
                                        cellData = lsuData.hruMap[hru]
                                        if cellData.area < minArea:
                                            minArea = cellData.area
                                            minHru = hru
                                            minCrop = crop
                                            minSoil = soil
                                            minSlope = slope
                        if minArea < threshold:
                            # Don't remove last hru.
                            # This happens when the subbasin area is below the area threshold
                            if count > 1:
                                lsuData.removeHRU(minHru, minCrop, minSoil, minSlope)
                                count -= 1
                                areaToRedistribute += minArea
                            else: # count is 1; ensure termination after redistributing
                                unfinished = False
                            if areaToRedistribute > 0:
                                # make sure we don't divide by zero
                                if hruArea - areaToRedistribute == 0:
                                    raise ValueError('No HRUs for channel {2!s} landscape {1!s} in basin {0!s}'.format(basin, landscape, channel))
                                redistributeFactor = hruArea / (hruArea - areaToRedistribute)
                                lsuData.redistribute(redistributeFactor)
                                areaToRedistribute = 0
                        else:
                            unfinished = False
        
    def removeSmallHRUsByThresholdPercent(self):
        """
        Remove HRUs that are below the minCropVal, minSoilVal, 
        or minSlopeVal, where the values are percentages.

        Remove from basins data HRUs that are below the minCropVal,
        minSoilVal, or minSlopeVal, where the values are percentages, and 
        redistribute their areas in proportion to the other HRUs in the same landscape unit.
        Do not remove the last HRU.  
        Crop, soil, and slope nodata cells are also redistributed, 
        so the total area of the retained HRUs in all landscape units should eventually be the total
        area of the subbasin, provided landscape units don't have landscape no data values.
        """
        
        minCropPercent = self.landuseVal
        minSoilPercent = self.soilVal
        minSlopePercent = self.slopeVal

        for basin, basinData in self.basins.items():
            for channel, channelData in basinData.getLsus().items(): 
                for landscape, lsuData in channelData.items():
                    cropAreas = lsuData.originalCropAreas
                    exemptWater = lsuData.waterBody is not None and not lsuData.waterBody.isUnknown()
                    hruArea = lsuData.area
                    areaToRedistribute = 0
                    minCropArea = (lsuData.cropSoilSlopeArea * minCropPercent) / 100
                    # reduce area if necessary to avoid removing all crops
                    if not self.hasExemptCrop(lsuData):
                        minCropArea = min(minCropArea, self.maxValue(cropAreas))
                    for (crop, area) in cropAreas.items():
                        if not self._gv.isExempt(crop) and not (crop == self._gv.db.waterLanduse and exemptWater):
                            if area < minCropArea:
                                areaToRedistribute += area
                                # remove this crop
                                # going to change maps so use lists
                                soilSlopeNumbers = lsuData.cropSoilSlopeNumbers[crop]
                                for (soil, slopeNumbers) in list(soilSlopeNumbers.items()):
                                    for (slope, hru) in list(slopeNumbers.items()):
                                        lsuData.removeHRU(hru, crop, soil, slope)
                    if areaToRedistribute > 0:
                        # just to make sure we don't divide by zero
                        if hruArea - areaToRedistribute == 0:
                            raise ValueError('No landuse data for channel {2!s} landscape {1!s} in basin {0!s}'.format(basin, landscape, channel))
                        redistributeFactor = hruArea / (hruArea - areaToRedistribute)
                        lsuData.redistribute(redistributeFactor)
                    # Now have to remove soil areas within each crop area that are
                    # less than minSoilVal for that crop.
                    # First create crop areas map (not overwriting the original)
                    lsuData.setCropAreas(False)
                    for (crop, soilSlopeNumbers) in lsuData.cropSoilSlopeNumbers.items():
                        cropArea = lsuData.cropAreas[crop]
                        minArea = (cropArea * minSoilPercent) / 100
                        soilAreas = lsuData.cropSoilAreas(crop)
                        # reduce area if necessary to avoid removing all soils for this crop
                        minArea = min(minArea, self.maxValue(soilAreas))
                        soilAreaToRedistribute = 0
                        # Cannot use original soilSlopeNumbers as we will remove domain elements, so make list
                        for (soil, slopeNumbersCopy) in list(soilSlopeNumbers.items()):
                            # first calculate area for this soil
                            soilArea = soilAreas[soil]
                            if soilArea < minArea:
                                # add to area to redistribute
                                soilAreaToRedistribute += soilArea
                                # remove hrus
                                for (slope, hru) in list(slopeNumbersCopy.items()):
                                    lsuData.removeHRU(hru, crop, soil, slope)
                        if soilAreaToRedistribute > 0:
                            # now redistribute
                            # just to make sure we don't divide by zero
                            if cropArea - soilAreaToRedistribute == 0:
                                raise ValueError('No soil data for landuse {1!s} in channel {3!s} landscape {2!s} in basin {0!s}'.format(basin, crop, landscape, channel))
                            soilRedistributeFactor = cropArea / (cropArea - soilAreaToRedistribute)
                            for slopeNumbers in soilSlopeNumbers.values():
                                for hru in slopeNumbers.values():
                                    cellData = lsuData.hruMap[hru]
                                    cellData.multiply(soilRedistributeFactor)
                                    lsuData.hruMap[hru] = cellData
                    # Now we remove the slopes for each remaining crop/soil combination
                    # that fall below minSlopePercent.
                    for (crop, soilSlopeNumbers) in lsuData.cropSoilSlopeNumbers.items():
                        for (soil, slopeNumbers) in soilSlopeNumbers.items():
                            # first calculate area for the soil
                            soilArea = 0
                            for hru in slopeNumbers.values():
                                cellData = lsuData.hruMap[hru]
                                soilArea += cellData.area
                            minArea = (soilArea * minSlopePercent) / 100
                            slopeAreas = lsuData.cropSoilSlopeAreas(crop, soil)
                            # reduce minArea if necessary to avoid removing all slopes for this crop and soil
                            minArea = min(minArea, self.maxValue(slopeAreas))
                            slopeAreaToRedistribute = 0
                            # Make list as we will remove domain elements from original
                            for (slope, hru) in list(slopeNumbers.items()):
                                # first calculate the area for this slope
                                slopeArea = slopeAreas[slope]
                                if slopeArea < minArea:
                                    # add to area to redistribute
                                    slopeAreaToRedistribute += slopeArea
                                    # remove hru
                                    lsuData.removeHRU(hru, crop, soil, slope)
                            if slopeAreaToRedistribute > 0:
                                # Now redistribute removed slope areas
                                # just to make sure we don't divide by zero
                                if soilArea - slopeAreaToRedistribute == 0:
                                    raise ValueError('No slope data for landuse {1!s} and soil {2!s} in channel {3!s} landscape {4!s} in basin {0!s}'.format(basin, crop, soil, channel, landscape))
                                slopeRedistributeFactor = soilArea / (soilArea - slopeAreaToRedistribute)
                                for hru in slopeNumbers.values():
                                    cellData = lsuData.hruMap[hru]
                                    cellData.multiply(slopeRedistributeFactor)
                                    lsuData.hruMap[hru] = cellData
        
    def removeSmallHRUsByThresholdArea(self):
        """
        Remove HRUs that are below the minCropVal, minSoilVal, 
        or minSlopeVal, where the values are areas in hectares.

        Remove from basins data HRUs that are below the minCropVal,
        minSoilVal, or minSlopeVal, where the values are areas, and 
        redistribute their areas in proportion to the other HRUs.  
        Do not remove the last HRU.  
        Crop, soil, and slope nodata cells are also redistributed, 
        so the total area of the retained HRUs should eventually be the total
        area of the subbasin.
        """
        # convert threshold areas to square metres
        minCropAreaBasin = self.landuseVal * 10000
        minSoilAreaBasin = self.soilVal * 10000
        minSlopeAreaBasin = self.slopeVal * 10000

        for basin, basinData in self.basins.items():
            for channel, channelData in basinData.getLsus().items(): 
                for landscape, lsuData in channelData.items():
                    cropAreas = lsuData.originalCropAreas
                    # reduce area if necessary to avoid removing all crops
                    if not self.hasExemptCrop(lsuData):
                        minCropArea = min(minCropAreaBasin, self.maxValue(cropAreas))
                    else:
                        minCropArea = minCropAreaBasin
                    exemptWater = lsuData.waterBody is not None and not lsuData.waterBody.isUnknown()
                    hruArea = lsuData.area
                    areaToRedistribute = 0
                    for (crop, area) in cropAreas.items():
                        if not self._gv.isExempt(crop) and not (crop == self._gv.db.waterLanduse and exemptWater):
                            if area < minCropArea:
                                # remove this crop
                                # going to change maps so make lists
                                soilSlopeNumbers = lsuData.cropSoilSlopeNumbers.get(crop, None)
                                if soilSlopeNumbers is not None:
                                    for (soil, slopeNumbers) in list(soilSlopeNumbers.items()):
                                        for (slope, hru) in list(slopeNumbers.items()):
                                            if len(lsuData.hruMap) == 1:
                                                break # don't remove last
                                            areaToRedistribute += lsuData.hruMap[hru].area
                                            lsuData.removeHRU(hru, crop, soil, slope)
                    # Now have to remove soil areas that are
                    # less than minSoilArea
                    soilAreas = lsuData.originalSoilAreas
                    # reduce area if necessary to avoid removing all soils
                    minSoilArea = min(minSoilAreaBasin, self.maxValue(soilAreas))
                    for (soil, area) in soilAreas.items():
                        if area < minSoilArea:
                            # remove this soil
                            # going to change maps so make lists
                            for (crop, soilSlopeNumbers) in list(lsuData.cropSoilSlopeNumbers.items()):
                                # guard against soil having gone by crop deletions earlier
                                slopeNumbers = soilSlopeNumbers.get(soil, None)
                                if slopeNumbers is not None:
                                    for (slope, hru) in list(slopeNumbers.items()):
                                        if len(lsuData.hruMap) == 1:
                                            break  # don't remove last
                                        areaToRedistribute += lsuData.hruMap[hru].area
                                        lsuData.removeHRU(hru, crop, soil, slope)
                    # Now we remove the slopes that are less than minSlopeArea
                    slopeAreas = lsuData.originalSlopeAreas
                    # reduce area if necessary to avoid removing all slopes
                    minSlopeArea = min(minSlopeAreaBasin, self.maxValue(slopeAreas))
                    for (slope, area) in slopeAreas.items():
                        if area < minSlopeArea:
                            # remove this slope
                            # going to change maps so make lists
                            for (crop, soilSlopeNumbers) in list(lsuData.cropSoilSlopeNumbers.items()):
                                for (soil, slopeNumbers) in list(soilSlopeNumbers.items()):
                                    # guard against slope having gone by crop and soil deletions earlier
                                    hru = slopeNumbers.get(slope, -1)
                                    if hru != -1:
                                        if len(lsuData.hruMap) == 1:
                                            break  # don't remove last
                                        areaToRedistribute += lsuData.hruMap[hru].area
                                        lsuData.removeHRU(hru, crop, soil, slope)
                    if areaToRedistribute > 0:
                        # Now redistribute removed areas
                        # just to make sure we don't divide by zero
                        if hruArea - areaToRedistribute == 0:
                            raise ValueError('Cannot redistribute area of {3:.2F} ha for channel {2!s} landscape {1!s} in basin {0!s}'.format(basin, landscape, channel, (areaToRedistribute / 10000)))
                        redistributeFactor = hruArea / (hruArea - areaToRedistribute)
                        lsuData.redistribute(redistributeFactor)
                
    def hasExemptCrop(self, lsuData):
        """Return true if landscape unit has an exempt crop."""
        if lsuData.waterBody is not None and not lsuData.waterBody.isUnknown() and self._gv.db.waterLanduse in lsuData.cropSoilSlopeNumbers:
            return True
        for crop in lsuData.cropSoilSlopeNumbers.keys():
            if self._gv.isExempt(crop):
                return True
        return False
    
    @staticmethod
    def maxValue(mapv):
        """Return maximum value in map."""
        maxm = 0
        for val in mapv.values():
            if val > maxm: maxm = val
        return maxm
    
    @staticmethod
    def mapSum(mapv):
        """Return sum of values in a map."""
        total = 0
        for val in mapv.values():
            total += val
        return total
                            
    def removeSmallHRUsbyTarget(self):
        """Try to reduce the number of HRUs to targetVal, 
        removing them in increasing order of size.
        
        Size is measured by area (if useArea is true) or by fraction
        of subbasin.
        The target may not be met if the order is by area and it would cause
        one or more subbasins to have no HRUs.
        The strategy is to make a list of all potential HRUs and their sizes 
        for which the landuses are not exempt, sort this list by increasing size, 
        and remove HRUs according to this list until the target is met.
        """
        # first make a list of (basin, hru, channel, landscape, crop, soil, slope, size) tuples
        removals = []
        for basin, basinData in self.basins.items():
            for channel, channelData in basinData.getLsus().items(): 
                for landscape, lsuData in channelData.items():
                    exemptWater = lsuData.waterBody is not None and not lsuData.waterBody.isUnknown()
                    for crop, soilSlopeNumbers in lsuData.cropSoilSlopeNumbers.items():
                        if not self._gv.isExempt(crop) and not (crop == self._gv.db.waterLanduse and exemptWater):
                            for soil, slopeNumbers in soilSlopeNumbers.items():
                                for slope, hru in slopeNumbers.items():
                                    hruArea = lsuData.hruMap[hru].area
                                    if self.useArea:
                                        size = hruArea
                                    elif lsuData.cropSoilSlopeArea == 0:
                                        SWATChannel = self._gv.topo.channelToSWATChannel[channel]
                                        QSWATUtils.error('\t ! LSU {0} seems to have no land area'.format(QSWATUtils.landscapeUnitId(SWATChannel, landscape)), self._gv.isBatch)
                                        size = 0
                                    else:
                                        size =  hruArea / lsuData.cropSoilSlopeArea
                                    removals.append((basin, hru, channel, landscape, crop, soil, slope, size))
        # sort by increasing size
        sortFun = lambda item: item[7]
        removals.sort(key=sortFun)
        # remove HRUs
        # if some are exempt and target is small, can try to remove more than all in removals, so check for this
        numToRemove = min(self.countHRUs() - self.targetVal, len(removals))
        for i in range(numToRemove):
            nextItem = removals[i]
            self.removeHru(nextItem[0], nextItem[1], nextItem[2], nextItem[3], nextItem[4], nextItem[5], nextItem[6])
            
    def removeHru(self, basin, hru, channel, landscape, crop, soil, slope):
        """Remove an HRU and redistribute its area within its landscape unit."""
        basinData = self.basins[basin]
        lsuData = basinData.getLsus()[channel][landscape]
        CreateHRUs.checkConsistent(lsuData, basin, channel, landscape, 4)
        hrus = lsuData.hruMap
        if len(hrus) == 1:
            # last HRU - do not remove
            return
        if hru not in hrus:
            QSWATUtils.loginfo('HRU {1} not found in basin {0} channel {2} landscape {3} crop {4} soil {5} slope {6}'.format(basin, hru, channel, landscape, crop, soil, slope))
            return
        areaToRedistribute = hrus[hru].area
        lsuData.removeHRU(hru, crop, soil, slope)
        if areaToRedistribute > 0:
            # make sure we don't divide by zero
            if lsuData.area - areaToRedistribute == 0:
                raise ValueError('No HRUs for channel {2!s} landscape {1!s} in basin {0!s}'.format(basin, landscape, channel))
            redistributeFactor = lsuData.cropSoilSlopeArea / (lsuData.cropSoilSlopeArea - areaToRedistribute)
            lsuData.redistribute(redistributeFactor)
        CreateHRUs.checkConsistent(lsuData, basin, channel, landscape, 5)

    def splitHRUs(self):
        """Split HRUs according to split landuses."""
        for (landuse, split) in self._gv.splitLanduses.items():
            crop = self._db.getLanduseCat(landuse)
            if crop < 0: # error already reported
                return False
            for basinData in self.basins.values():
                for channelData in basinData.getLsus().values(): 
                    for lsuData in channelData.values():
                        soilSlopeNumbers = lsuData.cropSoilSlopeNumbers.get(crop, None)
                        if soilSlopeNumbers is not None:
                            # have some hrus to split
                            # Make a new cropSoilSlopeNumbers map for the new crops
                            newcssn = dict()
                            for luse in split.keys():
                                newssn = dict()
                                crop1 = self._db.getLanduseCat(luse)
                                if crop1 < 0: # error already reported
                                    return False
                                newcssn[crop1] = newssn
                            # generally we will remove crop from cropSoilSlopeNumbers
                            # exception is when crop is named as a sublanduse of itself
                            retainCrop = False
                            for (soil, slopeNumbers) in soilSlopeNumbers.items():
                                # add soils to new dictionary
                                for newssn in newcssn.values():
                                    newsn = dict()
                                    newssn[soil] = newsn
                                for (slope, hru) in slopeNumbers.items():
                                    cd = lsuData.hruMap[hru]
                                    # remove hru from hruMap
                                    del lsuData.hruMap[hru]
                                    for (subluse, percent) in split.items():
                                        subcrop = self._db.getLanduseCat(subluse)
                                        oldssn = lsuData.cropSoilSlopeNumbers.get(subcrop, None)
                                        if oldssn is not None:
                                            # existing crop
                                            if subcrop != crop:
                                                # add to an existing crop
                                                # if have HRU with same soil and slope, add to it
                                                oldhru = -1
                                                sn = oldssn.get(soil, None)
                                                if sn is not None:
                                                    oldhru = sn.get(slope, -1)
                                                    if oldhru >= 0:
                                                        oldcd = lsuData.hruMap[oldhru]
                                                        cd1 = CellData(cd.cellCount, cd.area, cd.totalElevation, cd.totalSlope, \
                                                                       cd.totalLongitude, cd.totalLatitude, crop)
                                                        cd1.multiply(percent/100)
                                                        oldcd.addCells(cd1)
                                                if oldhru < 0:
                                                    # have to add new HRU to existing crop
                                                    # keep original crop number in cell data
                                                    cd1 = CellData(cd.cellCount, cd.area, cd.totalElevation, cd.totalSlope, \
                                                                   cd.totalLongitude, cd.totalLatitude, crop)
                                                    cd1.multiply(percent/100)
                                                    newhru = lsuData.nextHruNumber()
                                                    # add the new hru to hruMap
                                                    lsuData.hruMap[newhru] = cd1
                                                    # add hru to existing data for this crop
                                                    oldsn = oldssn.get(soil, None)
                                                    if not oldsn:
                                                        oldsn = dict()
                                                        oldssn[soil] = oldsn
                                                    oldsn[slope] = newhru
                                            else:
                                                # reducing an existing crop
                                                # replace with same hru number
                                                # but don't change cd as being used in other code branches
                                                cd1 = CellData(cd.cellCount, cd.area, cd.totalElevation, cd.totalSlope, \
                                                               cd.totalLongitude, cd.totalLatitude, crop)
                                                cd1.multiply(percent/100)
                                                lsuData.hruMap[hru] = cd1
                                                retainCrop = True
                                        else:
                                            # the subcrop is new to the basin
                                            # keep original crop number in cell data
                                            cd1 = CellData(cd.cellCount, cd.area, cd.totalElevation, cd.totalSlope, \
                                                           cd.totalLongitude, cd.totalLatitude, crop)
                                            cd1.multiply(percent/100)
                                            newhru = lsuData.nextHruNumber()
                                            # add the new hru to hruMap
                                            lsuData.hruMap[newhru] = cd1
                                            # add slope and hru number to new dictionary
                                            newssn = newcssn[subcrop]
                                            newsn = newssn[soil]
                                            newsn[slope] = newhru
                            # remove crop from cropSoilSlopeNumbers unless to be retained
                            if not retainCrop:
                                del lsuData.cropSoilSlopeNumbers[crop]
                            # add new cropSoilSlopeNumbers to original
                            for (newcrop, newssn) in newcssn.items():
                                # existing subcrops already dealt with
                                if not newcrop in lsuData.cropSoilSlopeNumbers:
                                    lsuData.cropSoilSlopeNumbers[newcrop] = newssn
        return True
            
    def writeTopoReport(self):
        """Write topographic report file."""
        topoPath = QSWATUtils.join(self._gv.textDir, Parameters._TOPOREPORT)
        line = '------------------------------------------------------------------------------'
        with fileWriter(topoPath) as fw:
            fw.writeLine('')
            fw.writeLine(line)
            fw.writeLine(QSWATUtils.trans('Elevation report for the watershed'.ljust(40) +
                                      QSWATUtils.date() + ' ' + QSWATUtils.time()))
            fw.writeLine('')
            fw.writeLine(line)
            self.writeTopoReportSection(self.elevMap, fw, 'watershed')
            fw.writeLine(line)
            if not self._gv.useGridModel:
                for SWATBasin in sorted(self._gv.topo.SWATBasinToSubbasin):
                    fw.writeLine('Subbasin {0!s}'.format(SWATBasin))
                    basin = self._gv.topo.SWATBasinToSubbasin[SWATBasin]
                    mapp = self.basinElevMap.get(basin, None)
                    if mapp is not None:
                        try:
                            bands = self.writeTopoReportSection(mapp, fw, 'subbasin')
                        except Exception:
                            QSWATUtils.exceptionError('Internal error: cannot write topo report for SWAT basin {0} (basin {1})'.format(SWATBasin, basin), self._gv.isBatch)
                            bands = None
                    else:
                        bands = None
                    fw.writeLine(line)
                    self.basinElevBands[SWATBasin] = bands
        self._reportsCombo.setVisible(True)
        if self._reportsCombo.findText(Parameters._TOPOITEM) < 0:
            self._reportsCombo.addItem(Parameters._TOPOITEM)
        self._db.writeElevationBands(self.basinElevBands, self._gv.numElevBands)
                
    def writeTopoReportSection(self, mapp, fw, string):
        """Write topographic report file section for 1 subbasin."""
        fw.writeLine('')
        fw.writeLine(QSWATUtils.trans('Statistics: All elevations reported in meters'))
        fw.writeLine('-----------')
        fw.writeLine('')
        (minimum, maximum, totalFreq, mean, stdDev) = self.analyseElevMap(mapp)
        fw.writeLine(QSWATUtils.trans('Minimum elevation: ').rjust(21) + str(minimum+self.minElev))
        fw.writeLine(QSWATUtils.trans('Maximum elevation: ').rjust(21) + str(maximum+self.minElev))
        fw.writeLine(QSWATUtils.trans('Mean elevation: ').rjust(21) + '{:.2F}'.format(mean))
        fw.writeLine(QSWATUtils.trans('Standard deviation: ').rjust(21) + '{:.2F}'.format(stdDev))
        fw.writeLine('')
        fw.write(QSWATUtils.trans('Elevation').rjust(23))
        fw.write(QSWATUtils.trans('% area up to elevation').rjust(32))
        fw.write(QSWATUtils.trans('% area of ').rjust(14) + string)
        fw.writeLine('')
        summ = 0.0
        if string == 'subbasin' and self._gv.elevBandsThreshold > 0  and \
        self._gv.numElevBands > 0 and maximum + self.minElev > self._gv.elevBandsThreshold:
            bandWidth = (maximum - minimum) / self._gv.numElevBands
            bands = [(minimum + self.minElev, 0.0)]
            nextBand = minimum + self.minElev + bandWidth
        else:
            bands = None
        for i in range(minimum, maximum+1):
            freq = mapp[i]
            summ += freq
            elev = i + self.minElev
            if totalFreq == 0:
                raise ValueError('Total frequency for {0} is zero'.format(string))
            upto = (summ / totalFreq) * 100.0
            percent = (freq / totalFreq) * 100.0
            if bands is not None:
                if elev > nextBand: # start a new band
                    bands.append((nextBand, percent))
                    nextBand += bandWidth
                else: 
                    el, frac = bands[-1]
                    bands[-1] = (el, frac + percent)
            fw.write(str(elev).rjust(20))
            fw.write(('{:.2F}'.format(upto)).rjust(25))
            fw.writeLine(('{:.2F}'.format(percent)).rjust(25))
        fw.writeLine('')
        return bands 
               
    def analyseElevMap(self, mapp):
        """Calculate statistics from map elevation -> frequency."""
        # find index of first non-zero frequency
        minimum = 0
        while mapp[minimum] == 0:
            minimum += 1
        # find index of last non-zero frequency
        maximum = len(mapp) - 1
        while mapp[maximum] == 0:
            maximum -= 1
        # calculate mean elevation and total of frequencies
        summ = 0.0
        totalFreq = 0.0
        for i in range(minimum, maximum + 1):
            freq = mapp[i]
            summ += i * freq
            totalFreq += freq
        # just to avoid dvision by zero
        if totalFreq == 0:
            return (minimum, maximum, 0, 0, 0)
        mapMean = summ / totalFreq
        mean = mapMean + self.minElev
        variance = 0
        for i in range(minimum, maximum + 1):
            diff = i - mapMean
            variance += diff * diff * mapp[i]
        stdDev = math.sqrt(variance/totalFreq)
        return (minimum, maximum, totalFreq, mean, stdDev)
    

    
    def printBasins(self, withHRUs, fullHRUsLayer):
        """
        Print report on crops, soils, and slopes for watershed.
        
        Also assigns HRU numbers and writes gis_hrus table if withHRUs.
        """
        fileName = Parameters._HRUSREPORT if withHRUs else Parameters._BASINREPORT
        path = QSWATUtils.join(self._gv.textDir, fileName)

        with fileWriter(path) as fw:
            if withHRUs:
                horizLine = '-----------------------------------------------------------------------------------------------------------'
            else:
                horizLine = '------------------------------------------------------------------------------'
            landscapeString = 'Landscape/' if self._gv.useLandscapes else ''
            HRUString = 'and HRU ' if withHRUs else ''
            fw.writeLine('{0}Landuse/Soil/Slope {1}Distribution'.format(landscapeString, HRUString).ljust(57) + \
                             QSWATUtils.date() + ' ' + QSWATUtils.time())
            fw.writeLine('')
            if self._gv.useGridModel:
                fw.writeLine('Grid model')
            else:
                if self.channelMergeThreshold > 0:
                    units = '%' if self.channelMergeByPercent else ' ha'
                    fw.writeLine('Short channel merge threshold {0:d}{1}'.format(self.channelMergeThreshold, units))
                else:
                    fw.writeLine('No short channel merge')
            if withHRUs:
                if self.isDominantHRU:
                    fw.writeLine('Dominant HRU option')
                    if self._gv.isBatch:
                        QSWATUtils.information('\t - Dominant HRU option', True)
                elif not self.isMultiple:
                    fw.writeLine('Dominant Landuse/Soil/Slope option')
                    if self._gv.isBatch:
                        QSWATUtils.information('\t - Dominant Landuse/Soil/Slope option', True)
                else: # multiple
                    if self.useArea:
                        method = 'Using area in hectares'
                        units = 'ha'
                    else:
                        method = 'Using percentage of subbasin'
                        units = '%'
                    if self.isTarget:
                        line1 = method + ' as a measure of size'
                        line2 = 'Target number of HRUs option'.ljust(47) + \
                                     'Target {0}'.format(self.targetVal)
                    elif self.isArea:
                        line1 = method + ' as threshold'
                        line2 = 'Multiple HRUs Area option'.ljust(47) + \
                                     'Threshold: {:d} {:s}'.format(self.areaVal, units)
                    else:
                        line1 = method + ' as a threshold'
                        line2 = 'Multiple HRUs Landuse/Soil/Slope option'.ljust(47) + \
                                     'Thresholds: {0:d}/{1:d}/{2:d} [{3}]'.format(self.landuseVal, self.soilVal, self.slopeVal, units)
                    fw.writeLine(line1)
                    if self._gv.isBatch:
                         QSWATUtils.information('\t - ' + line1, True)
                    fw.writeLine(line2)
                    if self._gv.isBatch:
                         QSWATUtils.information('\t - ' + line2, True)
            fw.writeLine('Number of subbasins: {0!s}'.format(len(self.basins)))
            fw.writeLine('Number of channels: {0!s}'.format(self.countChannels()))
            fw.writeLine('Number of LSUs: {0!s}'.format(self.countLsus()))
            numLakes = len(self._gv.topo.lakesData)
            if numLakes > 0:
                fw.writeLine('Number of lakes: {0!s}'.format(numLakes))
            if withHRUs:
                fw.writeLine('Number of HRUs: {0!s}'.format(self.countHRUs()))
            if withHRUs and self.isMultiple:
                if len(self._gv.exemptLanduses) > 0:
                    fw.write('Landuses exempt from thresholds: ')
                    for landuse in self._gv.exemptLanduses:
                        fw.write(landuse.rjust(6))
                    fw.writeLine('')
                if len(self._gv.splitLanduses) > 0:
                    fw.writeLine('Split landuses: ')
                    for (landuse, splits) in self._gv.splitLanduses.items():
                        fw.write(landuse.rjust(6))
                        fw.write(' split into ')
                        for use, percent in splits.items():
                            fw.write('{0} : {1!s}%  '.format(use, percent))
                        fw.writeLine('')
            lakesArea = self.totalLakesArea()
            waterBodiesArea = self.totalWaterBodiesArea()
            if lakesArea > 0:
                fw.writeLine('')
                if lakesArea > 0:
                    fw.writeLine('Area of watershed includes lakes; other areas do not include lakes.')
#                     subsString = ''
#                 else:
#                     subsString = 'watershed, '
#                 if waterBodiesArea > 0:
#                     fw.writeLine('Areas of {0}subbasins, landscape units and channels include ponds and reservoirs.'.format(subsString))
#                     hruString = ', slope ranges and HRUs' if withHRUs else ' and slope ranges'
#                     fw.writeLine('Areas of landuses, soils{0} exclude ponds and reservoirs.'.format(hruString))
            if withHRUs:
                fw.writeLine('')
                fw.writeLine('Numbers in parentheses are corresponding values before HRU creation')
            fw.writeLine('')
            fw.writeLine(horizLine)
            st1 = 'Area [ha]'
            st2 = '%Watershed'
            col2just = 33 if withHRUs else 18
            fw.writeLine(st1.rjust(45))
            basinHa = (self.totalBasinsArea() + lakesArea) / 1E4
            assert basinHa > 0, 'Watershed seems to have no area'
            fw.writeLine('Watershed' +  '{:.2F}'.format(basinHa).rjust(36))
            fw.writeLine(horizLine)
            fw.writeLine(st1.rjust(45) + st2.rjust(col2just))
            fw.writeLine('')
            if self._gv.useLandscapes:
                fw.writeLine('Landscape units')
                landscapeAreas = self.totalLandscapeAreas()
                self.printLandscapeAreas(landscapeAreas, withHRUs, basinHa, 0, fw)
                fw.writeLine('')
            fw.writeLine('Landuse')
            cropAreas, originalCropAreas = self.totalCropAreas(withHRUs)
            self.printCropAreas(cropAreas, originalCropAreas, basinHa, 0, fw)
            fw.writeLine('')
            fw.writeLine('Soil')
            soilAreas, originalSoilAreas = self.totalSoilAreas(withHRUs)
            self.printSoilAreas(soilAreas, originalSoilAreas, basinHa, 0, fw)
            fw.writeLine('')
            fw.writeLine('Slope')
            slopeAreas, originalSlopeAreas = self.totalSlopeAreas(withHRUs)
            self.printSlopeAreas(slopeAreas, originalSlopeAreas, basinHa, 0, fw)
            if lakesArea > 0:
                fw.writeLine('')
                self.printLakeArea(lakesArea, basinHa, 0, withHRUs, fw)
            if waterBodiesArea > 0:
                fw.writeLine('')
                self.printWaterArea(waterBodiesArea, basinHa, 0, withHRUs, fw)
            fw.writeLine(horizLine)
            fw.writeLine(horizLine)
            if lakesArea > 0:
                st1 = 'Area [ha]'
                st2 = '%Watershed'
                just2 = 33 if withHRUs else 18
                fw.writeLine(st1.rjust(45) + st2.rjust(just2))
                lakeAreas = self.getLakeAreas()
                for n in sorted(lakeAreas.keys()):
                    self.printLakeArea(lakeAreas[n], basinHa, n, withHRUs, fw)
                fw.writeLine(horizLine)
                
            if withHRUs:
                with self._db.conn as conn:
                    if not conn:
                        return
                    curs = conn.cursor()
                    self.progress('\t - Writing channels table ...')
                    self._gv.topo.writeChannelsTable(self.mergedChannels, self.basins, self._gv)
                    demLayer = QgsRasterLayer(self._gv.demFile, 'DEM')
                    self.progress('\t - Writing points, routing and hrus tables ...')
                    self._gv.topo.writePointsTable(demLayer, self.mergees, self._gv.useGridModel)
                    if not self._db.createRoutingTable():
                        QSWATUtils.error('\t ! Failed to create table gis_routing in project database', self._gv.isBatch)
                        return
                    time1 = time.process_time()
                    # list of channel, pointId pairs for extra points at outlet of channel between channel
                    # and reservoir it flows into
                    extraPoints = []
                    if not self._gv.topo.routeChannelsOutletsAndBasins(self.basins, self.mergedChannels, self.mergees, extraPoints, self._gv):
                        QSWATUtils.error('\t ! Failed to route channels and subbasins in table gis_routing in project database', self._gv.isBatch)
                        return
                    self._gv.topo.addExtraPointsToPointsTable(extraPoints, self._gv.useGridModel)
                    table = 'gis_hrus'
                    clearSQL = 'DROP TABLE IF EXISTS ' + table
                    curs.execute(clearSQL)
                    curs.execute(self._db._HRUSCREATESQL)
                    self.printBasinsDetails(basinHa, True, fw, curs, fullHRUsLayer, horizLine)
                    self.progress('')
                    time2 = time.process_time()
                    QSWATUtils.loginfo('Writing gis_points, gis_hrus and gis_routing tables took {0} seconds'.format(int(time2-time1)))
                    conn.commit()
                    self._db.hashDbTable(conn, 'gis_points')
                    self._db.hashDbTable(conn, 'gis_hrus')
                    self._db.hashDbTable(conn, 'gis_routing')
                    
            else:
                self.printBasinsDetails(basinHa, False, fw, None, fullHRUsLayer, horizLine)
        self._reportsCombo.setVisible(True)
        if withHRUs:
            if self._reportsCombo.findText(Parameters._HRUSITEM) < 0:
                self._reportsCombo.addItem(Parameters._HRUSITEM)
        else:
            if self._reportsCombo.findText(Parameters._BASINITEM) < 0:
                self._reportsCombo.addItem(Parameters._BASINITEM)
               
    def printBasinsDetails(self, basinHa, withHRUs, fw, curs, fullHRUsLayer, horizLine):
        """Print report on crops, soils, and slopes for subbasin."""
        setHRUS = withHRUs and fullHRUsLayer
        if setHRUS:
            subIndx = self._gv.topo.getIndex(fullHRUsLayer, QSWATTopology._SUBBASIN)
            if subIndx < 0: setHRUS = False
            chIndx = self._gv.topo.getIndex(fullHRUsLayer, QSWATTopology._CHANNEL)
            if chIndx < 0: return False
            catIndx = self._gv.topo.getIndex(fullHRUsLayer, QSWATTopology._LANDSCAPE)
            if catIndx < 0: setHRUS = False
            luseIndx = self._gv.topo.getIndex(fullHRUsLayer, Parameters._LANDUSE)
            if luseIndx < 0: setHRUS = False
            soilIndx = self._gv.topo.getIndex(fullHRUsLayer, Parameters._SOIL)
            if soilIndx < 0: setHRUS = False
            slopeIndx = self._gv.topo.getIndex(fullHRUsLayer, Parameters._SLOPEBAND)
            if slopeIndx < 0: setHRUS = False
            areaIndx = self._gv.topo.getIndex(fullHRUsLayer, Parameters._AREA)
            if areaIndx < 0: setHRUS = False
            hrusIndx = self._gv.topo.getIndex(fullHRUsLayer, QSWATTopology._HRUS)
            if hrusIndx < 0: setHRUS = False
            linkIndx = self._gv.topo.getIndex(fullHRUsLayer, QSWATTopology._LINKNO)
            if linkIndx < 0: setHRUS = False
        if setHRUS:
            OK = fullHRUsLayer.startEditing()
            if not OK:
                QSWATUtils.error('\t ! Cannot edit FullHRUs shapefile', self._gv.isBatch)
                setHRUS = False
        # set HRUS field for all shapes for this basin to NA
        # and reset channels to originals
        # (in case rerun with different HRU settings or different merges)
        if setHRUS: 
            self.clearHRUSNums(fullHRUsLayer, hrusIndx, chIndx, linkIndx)
        noLanduseReported = False
        noSoilReported = False
        for SWATBasin in sorted(self._gv.topo.SWATBasinToSubbasin):
            basin = self._gv.topo.SWATBasinToSubbasin[SWATBasin]
            if self._gv.useGridModel:
                chLink = self._gv.topo.chBasinToChLink[basin]
                if chLink in self._gv.topo.chLinkInsideLake or chLink in self._gv.topo.chLinkFromLake:
                    continue
            basinData = self.basins[basin]
            subHa = basinData.subbasinArea() / 1E4
            assert subHa > 0, 'SWAT basin {0} seems to be empty'.format(SWATBasin)
            # basinHa earlier asserted to be positive
            percent = (subHa / basinHa) * 100
            st1 = 'Area [ha]'
            st2 = '%Watershed'
            st3 = '%Subbasin'
            col2just = 33 if withHRUs else 18
            col3just = 23 if withHRUs else 15
            if withHRUs:
                st4 = '%Landscape unit'
                col4just = 23
                fw.writeLine(st1.rjust(45) + st2.rjust(col2just) + st3.rjust(col3just) + st4.rjust(col4just))
            else:
                fw.writeLine(st1.rjust(45) + st2.rjust(col2just) + st3.rjust(col3just))
            fw.writeLine('')
            fw.writeLine('Subbasin {0!s}'.format(SWATBasin).ljust(30) + \
                         '{:.2F}'.format(subHa).rjust(15) + \
                         '{:.2F}'.format(percent).rjust(col2just-3))
            fw.writeLine('')
            fw.writeLine('Landuse')
            originalCropAreas = basinData.cropAreas(True)
            basinWaterBodiesArea = self.basinWaterBodiesArea(basinData)
            if not withHRUs and len(originalCropAreas) == 0:
                hasCrop = False
                if basinWaterBodiesArea == 0:
                    subMsg = ' (and perhaps others)' if self._gv.useGridModel else ''
                    msg = 'There is no landuse data for subbasin {0}{1}.  Check your landuse map.'.format(SWATBasin, subMsg)
                    if noLanduseReported:
                        QSWATUtils.loginfo(msg)
                    else:
                        QSWATUtils.error(msg, self._gv.isBatch)
                        noLanduseReported = True
            else:
                hasCrop = True
            self.printCropAreas(basinData.cropAreas(False), originalCropAreas, basinHa, subHa, fw)
            fw.writeLine('')
            fw.writeLine('Soil')
            originalSoilAreas = basinData.soilAreas(True)
            # soilAreas will be empty if cropAreas is, so avoid knock-on message
            if not withHRUs and hasCrop and len(originalSoilAreas) == 0:
                subMsg = ' (and perhaps others)' if self._gv.useGridModel else ''
                msg = 'There is no soil data for subbasin {0}{1}.  Check your soil map.'.format(SWATBasin, subMsg)
                if noSoilReported:
                    QSWATUtils.loginfo(msg)
                else:
                    QSWATUtils.error(msg, self._gv.isBatch)
                    noSoilReported = True
            self.printSoilAreas(basinData.soilAreas(False), originalSoilAreas, basinHa, subHa, fw)
            fw.writeLine('')
            fw.writeLine('Slope')
            self.printSlopeAreas(basinData.slopeAreas(False), basinData.slopeAreas(True), basinHa, subHa, fw)
            fw.writeLine('')
            if basinWaterBodiesArea > 0:
                self.printWaterArea(basinWaterBodiesArea, basinHa, subHa, withHRUs, fw)
                fw.writeLine('')
            if withHRUs:
                fw.writeLine('HRUs:')
            self.printChannelHRUs(basinData, withHRUs, basinHa, subHa, fw, curs)
            fw.writeLine(horizLine)
        if setHRUS:
            self.addHRUSNums(fullHRUsLayer, subIndx, chIndx, catIndx, luseIndx, soilIndx, slopeIndx, hrusIndx, linkIndx)
            OK = fullHRUsLayer.commitChanges()
            if not OK:
                QSWATUtils.error('\t ! Cannot commit changes to FullHRUs shapefile', self._gv.isBatch)
            self.writeActHRUs(fullHRUsLayer, subIndx, chIndx, catIndx, areaIndx, hrusIndx)
            
    def printChannelHRUs(self, basinData, withHRUs, basinHa, subHa, fw, curs):
        """Print channel number, landscape and (if with HRUs) HRUs for each channel."""
        for channel, channelData in basinData.getLsus().items():
            SWATChannel = self._gv.topo.channelToSWATChannel[channel]
            landscapeAreas = {landscape: channelData[landscape].area for landscape in channelData}
            self.printChannelArea(SWATChannel, self.mapSum(landscapeAreas), withHRUs, basinHa, subHa, fw)
            self.printLandscapeAreas(landscapeAreas, withHRUs, basinHa, subHa, fw)
            if withHRUs:
                self.printLandscapeHRUs(SWATChannel, channelData, basinHa, subHa, fw, curs)
                fw.writeLine('')
            
    def printLandscapeHRUs(self, SWATChannel, channelData, basinHa, subHa, fw, curs):
        '''Print HRUs for each landscape.'''
        for landscape, lsuData in channelData.items():
            lsuId = QSWATUtils.landscapeUnitId(SWATChannel, landscape)
            # identity of the floodplain water body if any
            wid = 0
            wCat = 'unknown'
            # treat as upslope if is upslope and floodplain LSU exists
            # as in grids may all be upslope
            treatAsUpslope = landscape == QSWATUtils._UPSLOPE and QSWATUtils._FLOODPLAIN in channelData
            # true if this is upslope and the floodplain lsu is all water body
            downAllWater = False
            # Route LSU
            if treatAsUpslope:
                downLsuId = QSWATUtils.landscapeUnitId(SWATChannel, QSWATUtils._FLOODPLAIN)
                downLsuData = channelData[QSWATUtils._FLOODPLAIN]
                if downLsuData.waterBody is not None and not downLsuData.waterBody.isUnknown():
                    wid = downLsuData.waterBody.id
                    # if floodplain LSU is all water, route into the water body
                    if downLsuData.cropSoilSlopeArea == downLsuData.waterBody.originalArea:
                        downAllWater = True
                        wCat = 'RES' if downLsuData.waterBody.isReservoir() else 'PND'
                        curs.execute(DBUtils._ROUTINGINSERTSQL, 
                                     (lsuId, 'LSU', wid, wCat, 100))
                    else:
                        curs.execute(DBUtils._ROUTINGINSERTSQL, 
                                     (lsuId, 'LSU', downLsuId, 'LSU', 100))
                else:
                    curs.execute(DBUtils._ROUTINGINSERTSQL, 
                                 (lsuId, 'LSU', downLsuId, 'LSU', 100))
            else:
                if lsuData.waterBody is not None and not lsuData.waterBody.isUnknown():
                    if lsuData.cropSoilSlopeArea > lsuData.waterBody.originalArea:  # else all water
                        wid = lsuData.waterBody.id
                        wCat = 'RES' if lsuData.waterBody.isReservoir() else 'PND'
                        curs.execute(DBUtils._ROUTINGINSERTSQL, 
                                     (lsuId, 'LSU', wid, wCat, 100))
                else:
                    lake = self._gv.topo.surroundingLake(SWATChannel, self._gv.useGridModel)
                    if lake > 0:
                        lakeData = self._gv.topo.lakesData[lake]
                        lCat = 'RES' if lakeData.waterRole == 1 else 'PND'
                        curs.execute(DBUtils._ROUTINGINSERTSQL, 
                                     (lsuId, 'LSU', lake, lCat, 100))
                    else: 
                        curs.execute(DBUtils._ROUTINGINSERTSQL, 
                                     (lsuId, 'LSU', SWATChannel, 'CH', 100))
            if self._gv.useLandscapes:
                landscapeName = QSWATUtils.landscapeName(landscape, self._gv.useLeftRight)
                fw.writeLine('{0} (LSU {1!s}):'.format(landscapeName, lsuId))
            self.printLSUHRUs(lsuId, SWATChannel, landscape, lsuData, channelData, wid, wCat, downAllWater, basinHa, subHa, fw, curs)

    def printLSUHRUs(self, lsuId, SWATChannel, landscape, lsuData, channelData, wid, wCat, downAllWater, basinHa, subHa, fw, curs):
        '''Print and route HRUs and water bodies for an LSU.'''
        lake = self._gv.topo.surroundingLake(SWATChannel, self._gv.useGridModel)
        if lake > 0:
            lakeData = self._gv.topo.lakesData[lake]
            lCat = 'RES' if lakeData.waterRole == 1 else 'PND'
        floodTarget, floodCat = (lake, lCat) if lake > 0 else (wid, wCat) if wid > 0 else (SWATChannel, 'CH')
        arlsuHa = float(lsuData.area) / 1E4
        routeWaterAsWaterBody = lsuData.waterBody is not None and not lsuData.waterBody.isUnknown()
        for (crop, soilSlopeNumbers) in lsuData.cropSoilSlopeNumbers.items():
            if crop != self._gv.db.waterLanduse or not routeWaterAsWaterBody:
                arluse = lsuData.cropAreas[crop] / 10000
                for (soil, slopeNumbers) in soilSlopeNumbers.items():
                    arso = lsuData.cropSoilArea(crop, soil) / 10000
                    for (slope, landscape_hru) in slopeNumbers.items():
                        self.HRUNum += 1
                        cellData = lsuData.hruMap[landscape_hru]
                        cellData.actHRUNum = self.HRUNum
                        luse = self._db.getLanduseCode(crop)
                        snam = self._db.getSoilName(soil)
                        slp = self._db.slopeRange(slope)
                        cropSoilSlope = luse + '/' + snam + '/' + slp
                        # use cellArea rather than cellCount to calculate means
                        # cellCounts are integer and inaccurate (even zero) for small HRUs
                        if cellData.area == 0:
                            QSWATUtils.error('\t ! HRU {0} in LSU {1} has zero area'.format(self.HRUNum, lsuId), self._gv.isBatch)
                            meanMultiplier = 1
                        else:
                            meanMultiplier = self._gv.cellArea / cellData.area
                        meanSlopePercent = cellData.totalSlope * meanMultiplier * 100
                        hruha = cellData.area / 10000
                        arslp = hruha
                        fw.write(str(self.HRUNum).ljust(5) + cropSoilSlope.rjust(25) + \
                                     '{:.2F}'.format(hruha).rjust(15))
                        if basinHa > 0:
                            percent1 = (hruha / basinHa) * 100
                            fw.write('{:.2F}'.format(percent1).rjust(30))
                        if subHa > 0:
                            percent2 = (hruha / subHa) * 100
                            fw.write('{:.2F}'.format(percent2).rjust(23))
                        if arlsuHa > 0:
                            percent3 = (hruha / arlsuHa) * 100
                            fw.write('{:.2F}'.format(percent3).rjust(23))
                        fw.writeLine('')
    
                        meanElevation = cellData.totalElevation * meanMultiplier
                        centroid = QgsPointXY(cellData.totalLongitude * meanMultiplier, cellData.totalLatitude * meanMultiplier)
                        centroidll = self._gv.topo.pointToLatLong(centroid)
                        lat = centroidll.y()
                        if math.isnan(lat):
                            QSWATUtils.error('\t ! Cannot compue latitude for {0} on channel {1}'.format(cellData.totalLatitude * meanMultiplier, SWATChannel), self._gv.isBatch)
                            lat = 0
                        lon = centroidll.x()
                        if math.isnan(lon):
                            QSWATUtils.error('\t ! Cannot compue longitude for {0} on channel {1}'.format(cellData.totalLongitude * meanMultiplier, SWATChannel), self._gv.isBatch)
                            lon = 0
                        curs.execute(DBUtils._HRUSINSERTSQL, 
                                     (self.HRUNum, lsuId, subHa, arlsuHa, luse, arluse, snam, arso, slp,
                                      arslp, meanSlopePercent, lat, lon, meanElevation))
                        # route HRU
                        if landscape == QSWATUtils._NOLANDSCAPE or landscape == QSWATUtils._FLOODPLAIN or \
                            QSWATUtils._FLOODPLAIN not in channelData: # upslope with no floodplain; can happen in grid models
                            curs.execute(DBUtils._ROUTINGINSERTSQL, 
                                          (self.HRUNum, 'HRU', floodTarget, floodCat, 100))
                        else:
                            if downAllWater:
                                curs.execute(DBUtils._ROUTINGINSERTSQL, 
                                              (self.HRUNum, 'HRU', floodTarget, floodCat, 100))
                            else:
                                curs.execute(DBUtils._ROUTINGINSERTSQL, 
                                             (self.HRUNum, 'HRU', floodTarget, floodCat, self._gv.upslopeHRUDrain))
                                floodLsuId = QSWATUtils.landscapeUnitId(SWATChannel, QSWATUtils._FLOODPLAIN)
                                curs.execute(DBUtils._ROUTINGINSERTSQL, 
                                              (self.HRUNum, 'HRU', floodLsuId, 'LSU', 100 - self._gv.upslopeHRUDrain))
        waterBody = lsuData.waterBody                    
        if waterBody is not None and routeWaterAsWaterBody:
            # water area is original - prior to merging of reservoirs
            waterHa = waterBody.originalArea / 10000
            if waterBody.isReservoir():
                # reservoir cellCount is zero if it has been merged
                if waterBody.cellCount > 0:
                    string1 = 'Reservoir {0}'.format(waterBody.id)
                else:
                    string1 = 'Reservoir {0} (part)'.format(waterBody.id)
            else:
                string1 = 'Pond {0}'.format(waterBody.id)
            string2 = '{:.2F}'.format(waterHa)
            fw.write(string1.ljust(30) + string2.rjust(15))
            if basinHa > 0:
                percent1 = (waterHa / basinHa) * 100
                fw.write('{:.2F}'.format(percent1).rjust(30))
            if subHa > 0:
                percent2 = (waterHa / subHa) * 100
                fw.write('{:.2F}'.format(percent2).rjust(23))
            if arlsuHa > 0:
                percent3 = (waterHa / arlsuHa) * 100
                fw.write('{:.2F}'.format(percent3).rjust(23))
            fw.writeLine('')
            # for actual reservoir print total area
            if waterBody.isReservoir():
                if waterBody.cellCount > 0:
                    areaHa = waterBody.area / 10000
                    fw.writeLine('Total reservoir area:'.rjust(30) + '{:.2F}'.format(areaHa).rjust(15))
                    # reservoirs and ponds were routed with channels
        return

    def clearHRUSNums(self, fullHRUsLayer, hrusIndx, chIndx, linkIndx):
        """Set HRUS values to NA, and reset SWAT channel numbers to originals (before any channel merges)."""
        request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([linkIndx])
        for feature in fullHRUsLayer.getFeatures(request):
            fid = feature.id()
            chLink = feature[linkIndx]
            SWATChannel = self._gv.topo.channelToSWATChannel.get(chLink, 0)
            fullHRUsLayer.changeAttributeValue(fid, chIndx, SWATChannel)
            fullHRUsLayer.changeAttributeValue(fid, hrusIndx, 'NA')
        OK = fullHRUsLayer.commitChanges()
        if not OK:
            QSWATUtils.error('\t ! Cannot commit changes to FullHRUs shapefile', self._gv.isBatch)
        # start editing again for assignment of new HRUS values
        OK = fullHRUsLayer.startEditing()
        if not OK:
            QSWATUtils.error('\t ! Cannot edit FullHRUs attribute table', self._gv.isBatch)
           
    def addHRUSNums(self, fullHRUsLayer, subIndx, chIndx, catIndx, luseIndx, soilIndx, slopeIndx, hrusIndx, linkIndx):
        """Add HRUS values to fullHRUsLayer for actual HRUs, and change channel field to reflect channel merges.
        
        Do not merge HRUs according to channel merges, so that the merges can be changed without having
        to recompute the geometries.  ActHRUs wil be given merged geometries for merged channels."""
        for feature in fullHRUsLayer.getFeatures():
            fid = feature.id()
            SWATBasin = feature[subIndx]
            category = QSWATUtils.landscapeFromName(feature[catIndx])
            origCropCode = feature[luseIndx]
            soilName = feature[soilIndx] 
            slopeRange = feature[slopeIndx]
            basin = self._gv.topo.SWATBasinToSubbasin[SWATBasin]
            basinData = self.basins[basin]
            channel = feature[linkIndx]
            # FullHRUS file created before channel merging, so based on original channels, which might have been merged
            targetChannel = self._gv.topo.finalTarget(channel, self.mergedChannels)
            lsuData = basinData.getLsus()[targetChannel][category]
            if lsuData.waterBody is not None and origCropCode == 'WATR' and not lsuData.waterBody.isUnknown():
                if lsuData.waterBody.isReservoir():
                    hruNum = 'RES {0}'.format(lsuData.waterBody.id)
                else:
                    hruNum = 'PND {0}'.format(lsuData.waterBody.id)
            else:
                hruNum = None
                for soilSlopeNumbers in lsuData.cropSoilSlopeNumbers.values():
                    for soil, slopeNumbers in soilSlopeNumbers.items():
                        if self._db.getSoilName(soil) == soilName:
                            for slope, hru in slopeNumbers.items():
                                cellData = lsuData.hruMap[hru]
                                if self._db.getLanduseCode(cellData.crop) == origCropCode and self._db.slopeRange(slope) == slopeRange:
                                    if hruNum is None:
                                        hruNum = str(cellData.actHRUNum)
                                    else:
                                        hruNum = hruNum + ', {0}'.format(cellData.actHRUNum)
            OK = hruNum is None or fullHRUsLayer.changeAttributeValue(fid, hrusIndx, hruNum)
            if OK and targetChannel != channel:
                targetSWATChannel = self._gv.topo.channelToSWATChannel[targetChannel]
                OK = fullHRUsLayer.changeAttributeValue(fid, chIndx, targetSWATChannel)
            if not OK:
                QSWATUtils.error('\t ! Cannot write to FullHRUs attribute table', self._gv.isBatch)
                return
                    
    def writeActHRUs(self, fullHRUsLayer, subIndx, chIndx, catIndx, areaIndx, hrusIndx):
        """Create and load the actual HRUs file, with deselected HRUs removed and HRUs merged according to channel merges."""
        actHRUsBasename = Parameters._HRUS2
        actHRUsFilename = actHRUsBasename + '.shp'
        QSWATUtils.copyShapefile(self._gv.fullHRUsFile, actHRUsBasename, self._gv.shapesDir)
        actHRUsFile = QSWATUtils.join(self._gv.shapesDir, actHRUsFilename)
        legend = QSWATUtils._ACTHRUSLEGEND
        layer = QgsVectorLayer(actHRUsFile, '{0} ({1})'.format(legend, actHRUsBasename), 'ogr')
        provider = layer.dataProvider()
        fidsToBeMerged = dict() # map of fid to the fid it is to be merged with
        fidsToMerge = set() # range of fidsToBeMerged
        self.findMerges(provider, hrusIndx, fidsToMerge, fidsToBeMerged)
        # now merge any merged channels, plus ponds and reservoirs
        if not self.mergeActHRUs(provider, subIndx, chIndx, catIndx, areaIndx, hrusIndx, fidsToMerge, fidsToBeMerged):
            QSWATUtils.error('\t ! Failed to complete acxtual HRUs shapefile', self._gv.isBatch)
            return
        # insert above FullHRUs in legend
        proj = QgsProject.instance()
        root = proj.layerTreeRoot()
        group = root.findGroup(QSWATUtils._WATERSHED_GROUP_NAME)
        index = QSWATUtils.groupIndex(group, root.findLayer(fullHRUsLayer.id()))
        QSWATUtils.removeLayerByLegend(legend, root.findLayers())
        # seems we have to completely relinquish hold on actHRUsFile for changes to take effect
        layer = None
        actHRUsLayer = QgsVectorLayer(actHRUsFile, '{0} ({1})'.format(legend, actHRUsBasename), 'ogr')
        actHRUsLayer = proj.addMapLayer(actHRUsLayer, False)
        if group is not None:
            group.insertLayer(index, actHRUsLayer)
        styleFile = 'fullhrus.qml'
        actHRUsLayer.loadNamedStyle(QSWATUtils.join(self._gv.plugin_dir, styleFile))
        # make selected HRUs active and remove visibility from FullHRUs layer
        self._gv.iface.setActiveLayer(actHRUsLayer)
        QSWATUtils.setLayerVisibility(fullHRUsLayer, False, root)
        # copy actual HRUs file as template for visualisation
        self.createHrusResultsFile(actHRUsFile)
            
    def findMerges(self, provider, hrusIndx, fidsToMerge, fidsToBeMerged):
        """Build table of HRU fids to merge."""
        hrusToFid = dict()
        request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([hrusIndx])
        for feature in provider.getFeatures(request):
            fid = feature.id()
            hrus = feature[hrusIndx]
            if hrus == 'NA':
                continue
            else:  # check if this hrus field has already occurred
                fid1 = hrusToFid.get(hrus, None)
                if fid1 is None:
                    hrusToFid[hrus] = fid
                else:  # fid will be merged into fid1
                    fidsToMerge.add(fid1)
                    fidsToBeMerged[fid] = fid1
    
    def mergeActHRUs(self, provider, subIndx, chIndx, catIndx, areaIndx, hrusIndx, fidsToMerge, fidsToBeMerged):
        """Merge HRUs in ActHRUs file according to merged fids.  Also sets area and percent fields to reflext
        changes in these because of HRU removal and area reallocation.
        
        Must be run after addHRUSNums as depends on merging HRUs with same HRUS values,
        and after removeDeselectedHRUs which makes fidsToMerge and fidsToBeMerged."""
        percentSubIndx = provider.fieldNameIndex(Parameters._PERCENTSUB)
        if percentSubIndx < 0: return False
        percentLSUIndx = provider.fieldNameIndex(Parameters._PERCENTLSU)
        if percentLSUIndx < 0: return False
        # map featureId to attributes to be used for updating non-merged features
        amap = dict()
        fields = provider.fields()
        fidsToDelete = []
        mergers = dict()  # map of fid to tuple (feature, list of geometries to merge with feature)
        for feature in provider.getFeatures():
            fid = feature.id()
            hrus = feature[hrusIndx]
            if hrus == 'NA':
                fidsToDelete.append(fid)
                continue
            # updates for area, percent of subbasin and percent of LSU stored in amap
            basin = self._gv.topo.SWATBasinToSubbasin[feature[subIndx]]
            basinData = self.basins[basin]
            subArea = basinData.subbasinArea()
            SWATChannel = feature[chIndx]
            channel = self._gv.topo.SWATChannelToChannel[SWATChannel]
            lscape = QSWATUtils.landscapeFromName(feature[catIndx])
            # use final lsus
            lsuData = basinData.getLsus()[channel][lscape]
            lsuArea = lsuData.area
            area = self.hrusArea(hrus, lsuData)
            areaHa = area / 1E4
            if subArea == 0:
                QSWATUtils.error('\t ! SWAT basin {0} seems to be empty'.format(feature[subIndx]), self._gv.isBatch)
                percentSub = 0
            else:
                percentSub = (area / subArea) * 100
            if lsuArea == 0:
                QSWATUtils.error('\t ! LSU {0} seems to be empty'.format(QSWATUtils.landscapeUnitId(SWATChannel, lscape)), self._gv.isBatch)
                percentLSU = 0
            else:
                percentLSU = (area / lsuArea) * 100
            if fid in fidsToMerge:
                # fid will have other geometries added to it.  Define a new feature for it, to be added later
                (_, feats) = mergers.get(fid, (None, []))
                geom = feature.geometry()
                newFeature = QgsFeature(fields)
                newFeature.setAttributes(feature.attributes())
                newFeature[areaIndx] = areaHa
                newFeature[percentSubIndx] = percentSub
                newFeature[percentLSUIndx] = percentLSU
                newFeature.setGeometry(geom)
                mergers[fid] = (newFeature, feats)
                fidsToDelete.append(fid)
            else:
                fid1 = fidsToBeMerged.get(fid, None)
                if fid1 is None:
                    # not involved in any mergers: will be updated
                    amap[fid] = {areaIndx: areaHa, percentSubIndx: percentSub, percentLSUIndx: percentLSU}
                else: # add feature to list of features to be merged with fid1's new feature
                    (feat, feats) = mergers.get(fid1, (None, []))
                    feats.append(feature)
                    mergers[fid1] = (feat, feats)
                    fidsToDelete.append(fid)
        newFeatures = self.mergeGeometries(mergers)
        OK = len(amap) == 0 or provider.changeAttributeValues(amap)
        if OK:
            OK = len(newFeatures) == 0 or provider.addFeatures(newFeatures)
        if OK:
            OK = len(fidsToDelete) == 0 or provider.deleteFeatures(fidsToDelete)
        return OK
    
    def mergeGeometries(self, mergers):
        """Mergers is a map fid to pair (feature, feature list).  Merge geometries in list into feature, and finally retun list of features."""
        result = []
        for (feature, feats) in mergers.values():
            geom = feature.geometry()
            for feat in feats:
                geom1 = feat.geometry()
                geom2 = geom.combine(geom1)
                if geom2 is None:
                    # hru features can contain one polygon inside another
                    # and this is regarded as invalid by ogr: combine returns None
                    # fix this by simply extending the first list of polygons with the second
                    geom2 = QSWATUtils.polyCombine(geom, geom1)
                geom = geom2
            feature.setGeometry(geom)
            result.append(feature)
        return result
    
    def hrusArea(self, hrus, lsuData):
        """Return total area of hrus in square metres."""
        area = 0
        for hru in hrus.split(','):
            area += self.hruArea(hru.strip(), lsuData)
        return area
    
    def hruArea(self, hru, lsuData):
        """Return area of hru in square metres."""
        try:
            if hru.startswith('RES') or hru.startswith('PND'):
                return lsuData.waterBody.area
            else:
                hruNum = int(hru)
                # find hru with this number
                for cellData in lsuData.hruMap.values():
                    if cellData.actHRUNum == hruNum:
                        return cellData.area
                QSWATUtils.error('\t ! Cannot find hru {0}'.format(hru), self._gv.isBatch)
                return 0
        except Exception:
            QSWATUtils.error('\t ! Cannot parse {0} as an hru reference'.format(hru), self._gv.isBatch)
            return 0
        
    def createHrusResultsFile(self, actHRUsFile):
        """Copy actual hrus file to results folder; remove fields except HRUS."""
        QSWATUtils.copyShapefile(actHRUsFile, Parameters._HRUS, self._gv.resultsDir)
        hrusFile = QSWATUtils.join(self._gv.resultsDir, Parameters._HRUS + '.shp')
        hrusLayer = QgsVectorLayer(hrusFile, 'hrus', 'ogr')
        QSWATTopology.removeFields(hrusLayer.dataProvider(), [QSWATTopology._HRUS], hrusFile, self._gv.isBatch)
    
    def mergeLSUs(self, root):
        """Merge LSUs in lsus shapefile according to channel merges, making lsus2.  Return true if successful."""
        if not os.path.exists(self._gv.fullLSUsFile):
            return False
        legend = QSWATUtils._ACTLSUSLEGEND
        QSWATUtils.removeLayerByLegend(legend, root.findLayers())
        QSWATUtils.copyShapefile(self._gv.fullLSUsFile, Parameters._LSUS2, self._gv.shapesDir)
        layer = QgsVectorLayer(self._gv.actLSUsFile, '{0} ({1})'.format(legend, QFileInfo(self._gv.actLSUsFile).baseName()), 'ogr')  
        if self._gv.useGridModel or len(self.mergedChannels) == 0:
            # no merging to do
            return True
        provider = layer.dataProvider()
        lsuIndx = provider.fieldNameIndex(QSWATTopology._LSUID)
        if lsuIndx < 0: return False
        chIndx = provider.fieldNameIndex(QSWATTopology._CHANNEL)
        if chIndx < 0: return False
        catIndx = provider.fieldNameIndex(QSWATTopology._LANDSCAPE)
        if catIndx < 0: return False
        areaIndx = provider.fieldNameIndex(Parameters._AREA)
        if areaIndx < 0: return False
        percentSubIndx = provider.fieldNameIndex(Parameters._PERCENTSUB)
        if percentSubIndx < 0: return False
        # first make a set of final target channels
        finalTargets = set()
        for channel in self.mergedChannels:
            finalTargets.add(self._gv.topo.finalTarget(channel, self.mergedChannels))
        amap = dict()
        fields = provider.fields()
        # map of target channel -> landscape -> newFeature
        mergeMap = dict()
        toDelete = []
        # populate mergeMap
        for target in finalTargets:
            SWATChannel = self._gv.topo.channelToSWATChannel.get(target, 0)
            if SWATChannel > 0: # defensive programming
                expr = QgsExpression('"{0}" = {1}'.format(QSWATTopology._CHANNEL, SWATChannel))
                request = QgsFeatureRequest(expr)
                for targetFeature in provider.getFeatures(request):
                    newFeature = QgsFeature(fields)
                    newFeature.setAttributes(targetFeature.attributes())
                    newFeature.setGeometry(targetFeature.geometry())
                    lscape = targetFeature[catIndx]
                    if target in mergeMap:
                        mergeMap[target][lscape] = newFeature
                    else:
                        mergeMap[target] = {lscape: newFeature}
                    toDelete.append(targetFeature.id())
        # find merged channels, add merge details to newFeature, and list them for deletion
        for channel in self.mergedChannels:
            SWATChannel = self._gv.topo.channelToSWATChannel.get(channel, 0)
            if SWATChannel > 0: # defensive programming
                expr = QgsExpression('"{0}" = {1}'.format(QSWATTopology._CHANNEL, SWATChannel))
                request = QgsFeatureRequest(expr)
                for feature in provider.getFeatures(request):
                    fid = feature.id()
                    target = self._gv.topo.finalTarget(channel, self.mergedChannels)
                    lscape = feature[catIndx]
                    if target in mergeMap:
                        if lscape in mergeMap[target]:
                            newFeature = mergeMap[target][lscape]
                            newFeature[areaIndx] += feature[areaIndx]
                            newFeature[percentSubIndx] += feature[percentSubIndx]
                            geom1 = newFeature.geometry()
                            geom2 = feature.geometry()
                            geom3 = geom1.combine(geom2)
                            if geom3 is None:
                                # LSU geometries can fail to combine
                                # fix this by simply extending the first list of polygons with the second
                                geom3 = QSWATUtils.polyCombine(geom1, geom2)
                            newFeature.setGeometry(geom3)
                            toDelete.append(fid)
                        else:
                            # there is no lsu to merge with (eg this is upslope but merge target is all floodplain)
                            # just need to update this feature's lsuid and channel
                            tSWATChannel = self._gv.topo.channelToSWATChannel[target]
                            lsuid = QSWATUtils.landscapeUnitId(tSWATChannel, QSWATUtils.landscapeFromName(lscape))
                            amap[fid] = {lsuIndx: lsuid, chIndx: tSWATChannel}
        # make changes to lsus shapefile
        OK = len(amap) == 0 or provider.changeAttributeValues(amap)
        if OK:
            for mergers in mergeMap.values():
                OK = OK and provider.addFeatures(list(mergers.values()))
        if OK:
            OK = len(toDelete) == 0 or provider.deleteFeatures(toDelete)
        if OK and not self._gv.useGridModel:
            # load in place of full lsus
            proj = QgsProject.instance()
            root = proj.layerTreeRoot()
            layers = root.findLayers()
            fullLSUsLayer = QSWATUtils.getLayerByLegend(QSWATUtils._FULLLSUSLEGEND, layers)
            group = root.findGroup(QSWATUtils._WATERSHED_GROUP_NAME)
            if fullLSUsLayer is None:
                subsLayer = QSWATUtils.getLayerByLegend(QSWATUtils._SUBBASINSLEGEND, layers)
                if subsLayer is None:
                    index = 0
                else:
                    index = QSWATUtils.groupIndex(group, subsLayer)
            else:
                index = QSWATUtils.groupIndex(group, fullLSUsLayer)
            proj.addMapLayer(layer, False)
            if group is not None:
                group.insertLayer(index, layer)
            layer.loadNamedStyle(QSWATUtils.join(self._gv.plugin_dir, 'lsus.qml'))
            if fullLSUsLayer is not None:
                fullLSUsLayer.setItemVisibilityChecked(False)
        return OK               
    
    def writeSubbasinsAndLandscapeTables(self):
        """Write gis_subbasins and gis_lsus tables in project database, 
        make subs1.shp in shapes directory, 
        copy subs1.shp and lsus2.shp as results templates to Results directory,
        and add fields to subs1.shp and lsus2.shp."""
        QSWATUtils.copyShapefile(self._gv.subbasinsFile, Parameters._SUBS1, self._gv.shapesDir)
        subs1File = QSWATUtils.join(self._gv.shapesDir, Parameters._SUBS1 + '.shp')
        subs1Layer = QgsVectorLayer(subs1File, 'Subbasins ({0})'.format(Parameters._SUBS1), 'ogr')
        subsProvider1 = subs1Layer.dataProvider()
        lsus2File = QSWATUtils.join(self._gv.shapesDir, Parameters._LSUS2 + '.shp')
        # remove features with 0 subbasin value
        exp = QgsExpression('"{0}" = 0'.format(QSWATTopology._SUBBASIN))
#         context = QgsExpressionContext()
#         context.appendScope(QgsExpressionContextUtils.layerScope(subs1Layer))
#         exp.prepare(context)
        idsToDelete = []
        for feature in subsProvider1.getFeatures(QgsFeatureRequest(exp).setFlags(QgsFeatureRequest.NoGeometry)):
            idsToDelete.append(feature.id())
        OK = subsProvider1.deleteFeatures(idsToDelete)
        if not OK:
            QSWATUtils.error('\t ! Cannot edit subbasins shapefile {0}'.format(subs1File), self._gv.isBatch)
            return False
        # Add fields from Watershed table to subs1File if less than RIVS1SUBS1MAX features; otherwise takes too long.
        addToSubs1 = subs1Layer.featureCount() <= Parameters._RIVS1SUBS1MAX
        # If we are adding fields to subs1 we need to
        # 1. remove fields apart from Subbasin from subs1
        # 2. copy to make results template
        # and if not we need to 
        # 1. copy to make results template
        # 2. remove fields apart from Subbasin from template
        # In the case of lsus1 we have demwshed but that differs from lsus1 in not reflecting stream mergers,
        # so we 
        # 1. copy lsus1 to results directory
        # 2. remove fields from copy except LSUID
        # 3. add fields from gis_lsus to lsus1, using same condition addToSubs1 to decide if this should be done
        if addToSubs1:
            QSWATTopology.removeFields(subsProvider1, [QSWATTopology._POLYGONID, QSWATTopology._SUBBASIN], subs1File, self._gv.isBatch)
        # make copy as template for stream results
        # first relinquish all references to subs1File for changes to take effect
        subs1Layer = None
        QSWATUtils.copyShapefile(subs1File, Parameters._SUBS, self._gv.resultsDir)
        if not addToSubs1:
            subsFile = QSWATUtils.join(self._gv.resultsDir, Parameters._SUBS + '.shp')
            subsLayer = QgsVectorLayer(subsFile, 'Subbasins', 'ogr')
            QSWATTopology.removeFields(subsLayer.dataProvider(), [QSWATTopology._SUBBASIN], subsFile, self._gv.isBatch)
        # copy lsus2 to results directory and remove fields other than LSUID
        QSWATUtils.copyShapefile(lsus2File, Parameters._LSUS, self._gv.resultsDir)
        lsusFile = QSWATUtils.join(self._gv.resultsDir, Parameters._LSUS + '.shp')
        lsusLayer = QgsVectorLayer(lsusFile, 'LSUs', 'ogr')
        QSWATTopology.removeFields(lsusLayer.dataProvider(), [QSWATTopology._LSUID], lsusFile, self._gv.isBatch)
        if addToSubs1:
            # add fields from gis_subbasins table to subs1
            subFields = []
            subFields.append(QgsField(Parameters._AREA, QVariant.Double, len=20, prec=1))
            subFields.append(QgsField('Slo1', QVariant.Double, len=20, prec=2))
            subFields.append(QgsField('Len1', QVariant.Double, len=20, prec=2))
            subFields.append(QgsField('Sll', QVariant.Double, len=20, prec=2))
            subFields.append(QgsField('Lat', QVariant.Double, len=20, prec=2))
            subFields.append(QgsField('Lon', QVariant.Double, len=20, prec=2))
            subFields.append(QgsField('Elev', QVariant.Double, len=20, prec=2))
            subFields.append(QgsField('ElevMin', QVariant.Double, len=20, prec=2))
            subFields.append(QgsField('ElevMax', QVariant.Double, len=20, prec=2))
            subs1Layer = QgsVectorLayer(subs1File, 'Subbasins ({0})'.format(Parameters._SUBS1), 'ogr')
            subsProvider1 = subs1Layer.dataProvider()
            subsProvider1.addAttributes(subFields)
            subs1Layer.updateFields()
            polyIdx = self._gv.topo.getIndex(subs1Layer, QSWATTopology._POLYGONID)
            subIdx = self._gv.topo.getIndex(subs1Layer, QSWATTopology._SUBBASIN)
            areasubIdx = self._gv.topo.getIndex(subs1Layer, Parameters._AREA)
            slo1subIdx = self._gv.topo.getIndex(subs1Layer, 'Slo1')
            len1subIdx = self._gv.topo.getIndex(subs1Layer, 'Len1')
            sllsubIdx = self._gv.topo.getIndex(subs1Layer, 'Sll')
            latsubIdx = self._gv.topo.getIndex(subs1Layer, 'Lat')
            lonsubIdx = self._gv.topo.getIndex(subs1Layer, 'Lon')
            elevsubIdx = self._gv.topo.getIndex(subs1Layer, 'Elev')
            elevMinsubIdx = self._gv.topo.getIndex(subs1Layer, 'ElevMin')
            elevMaxsubIdx = self._gv.topo.getIndex(subs1Layer, 'ElevMax')
            subMap = dict()
            # add fields from gis_lsus table to lsus2
            lsuFields = []
            lsuFields.append(QgsField('Category', QVariant.Int))
            lsuFields.append(QgsField('Slope', QVariant.Double, len=20, prec=2))
            lsuFields.append(QgsField('Len1', QVariant.Double, len=20, prec=2))
            lsuFields.append(QgsField('Csl', QVariant.Double, len=20, prec=2))
            lsuFields.append(QgsField('Wid1', QVariant.Double, len=20, prec=2))
            lsuFields.append(QgsField('Dep1', QVariant.Double, len=20, prec=2))
            lsuFields.append(QgsField('Lat', QVariant.Double, len=20, prec=2))
            lsuFields.append(QgsField('Lon', QVariant.Double, len=20, prec=2))
            lsuFields.append(QgsField('Elev', QVariant.Double, len=20, prec=2))
            lsus2Layer = QgsVectorLayer(lsus2File, 'LSUs ({0})'.format(Parameters._LSUS2), 'ogr')
            lsusProvider2 = lsus2Layer.dataProvider()
            lsusProvider2.addAttributes(lsuFields)
            lsus2Layer.updateFields()
            lsuIdx = self._gv.topo.getIndex(lsus2Layer, QSWATTopology._LSUID)
            catlsuIdx = self._gv.topo.getIndex(lsus2Layer, 'Category')
            slopelsuIdx = self._gv.topo.getIndex(lsus2Layer, 'Slope')
            len1lsuIdx = self._gv.topo.getIndex(lsus2Layer, 'Len1')
            csllsuIdx = self._gv.topo.getIndex(lsus2Layer, 'Csl')
            wid1lsuIdx = self._gv.topo.getIndex(lsus2Layer, 'Wid1')
            dep1lsuIdx = self._gv.topo.getIndex(lsus2Layer, 'Dep1')
            latlsuIdx = self._gv.topo.getIndex(lsus2Layer, 'Lat')
            lonlsuIdx = self._gv.topo.getIndex(lsus2Layer, 'Lon')
            elevlsuIdx = self._gv.topo.getIndex(lsus2Layer, 'Elev')
            saveLSUMap = dict()
        with self._db.conn as conn:
            if not conn:
                return False
            curs = conn.cursor()
            if self._gv.existingWshed:
                # allow for no valley depths file, but use if found
                if self._gv.valleyDepthsFile == '':
                    base, suffix = os.path.splitext(self._gv.demFile)
                    valleyDepthsFile = base + 'depths' + suffix
                    if os.path.exists(valleyDepthsFile):
                        QSWATUtils.loginfo('Using {0} as valley depths file'.format(valleyDepthsFile))
                        self._gv.valleyDepthsFile = valleyDepthsFile
                if os.path.exists(self._gv.valleyDepthsFile):
                    valleyDepthsLayer = QgsRasterLayer(self._gv.valleyDepthsFile, 'Valley depths')
                else:
                    valleyDepthsLayer = None
            else:
                if not os.path.exists(self._gv.valleyDepthsFile):
                    if self._gv.useLandscapes:
                        # should be valley depths file unless using a buffer for floodplain
                        if os.path.split(self._gv.floodFile)[1].startswith('bufferflood'):
                            valleyDepthsLayer = None
                        else:
                            QSWATUtils.error('\t ! Cannot find valley depths raster {0}'.format(self._gv.valleyDepthsFile), self._gv.isBatch)
                            return False
                    else:
                        valleyDepthsLayer = None
                else:
                    valleyDepthsLayer = QgsRasterLayer(self._gv.valleyDepthsFile, 'Valley depths')
            subtable = 'gis_subbasins'
            clearSQL = 'DROP TABLE IF EXISTS ' + subtable
            curs.execute(clearSQL)
            curs.execute(self._db._SUBBASINSCREATESQL)
            lsutable = 'gis_lsus'
            clearSQL = 'DROP TABLE IF EXISTS ' + lsutable
            curs.execute(clearSQL)
            curs.execute(self._db._LSUSCREATESQL)
            if addToSubs1:
                request =  QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([polyIdx, subIdx])
                generator = self.generateBasinsFromShapefile(request, subsProvider1, polyIdx, subIdx)
            else:
                generator = self.generateBasinsFromTable()
            for fid, basin, SWATBasin, basinData in generator:
                if basinData is None or SWATBasin == 0:
                    continue
                # some values will be float64 and will not write unless coerced to float
                areaKm = basinData.subbasinArea() / 1E6  # area in square km.
                areaHa = areaKm * 100
                cellCount = basinData.subbasinCellCount()
                assert cellCount > 0, 'Basin {0!s} has zero cell count'.format(SWATBasin)
                meanSlope = (basinData.totalSlope() / cellCount) * self._gv.meanSlopeMultiplier
                meanSlopePercent = meanSlope * 100
                farDistance = basinData.farDistance * self._gv.tributaryLengthMultiplier
                slsubbsn = QSWATUtils.getSlsubbsn(meanSlope)
                centreX, centreY = self._gv.topo.basinCentroids[basin]
                centroidll = self._gv.topo.pointToLatLong(QgsPointXY(centreX, centreY))
                lat = centroidll.y()
                lon = centroidll.x()
                meanElevation = basinData.totalElevation() / cellCount
                elevMin = basinData.minElevation
                elevMax = basinData.maxElevation
                if addToSubs1:
                    subMap[fid] = dict()
                    amap = subMap[fid]
                    amap[areasubIdx] = areaHa
                    amap[slo1subIdx] = meanSlopePercent
                    amap[len1subIdx] = farDistance
                    amap[sllsubIdx] = slsubbsn
                    amap[elevsubIdx] = meanElevation 
                    amap[latsubIdx] = lat
                    amap[lonsubIdx] = lon
                    amap[elevMinsubIdx] = elevMin 
                    amap[elevMaxsubIdx] = elevMax
                curs.execute(DBUtils._SUBBASINSINSERTSQL, 
                             (SWATBasin, areaHa, meanSlopePercent, 
                              farDistance, slsubbsn,
                              lat, lon, meanElevation, elevMin, elevMax))
                for channel, channelData in basinData.getLsus().items():
                    SWATChannel = self._gv.topo.channelToSWATChannel[channel]
                    floodDrop = 0
                    floodLen = 0
                    floodLsuData = channelData.get(QSWATUtils._FLOODPLAIN, None) if self._gv.useLandscapes else channelData.get(QSWATUtils._NOLANDSCAPE, None)
                    if floodLsuData is not None:
                        dropToSource = floodLsuData.farElevation - floodLsuData.sourceElevation
                        if valleyDepthsLayer is None:
                            floodDrop = None
                        else:
                            floodDrop = QSWATTopology.valueAtPoint(QgsPointXY(floodLsuData.farPointX, floodLsuData.farPointY), valleyDepthsLayer)
                        if floodDrop is None:
                            # estimate it
                            floodDrop = abs(dropToSource * 0.25 if self._gv.useLandscapes else dropToSource)
                        floodLen = floodLsuData.farDistance
                    for landscape, lsuData in channelData.items():
                        if lsuData.cropSoilSlopeArea == 0:
                            # was all water
                            continue
                        lsuId = QSWATUtils.landscapeUnitId(SWATChannel, landscape)
                        if landscape  == QSWATUtils._UPSLOPE:
                            tribDistance = (lsuData.farDistance - floodLen) * self._gv.tributaryLengthMultiplier
                            if valleyDepthsLayer is None:
                                slopeDrop = None
                            else:
                                slopeDrop = QSWATTopology.valueAtPoint(QgsPointXY(lsuData.farPointX, lsuData.farPointY), valleyDepthsLayer)
                            if slopeDrop is None:
                                # estimate it
                                slopeDrop = abs(lsuData.farElevation - lsuData.sourceElevation)
                            tribDrop = abs(slopeDrop - floodDrop)
                        else:
                            tribDistance = floodLen * self._gv.tributaryLengthMultiplier
                            tribDrop = abs(floodDrop)
                        areaHa = lsuData.area / 1E4
                        if areaHa == 0:
                            QSWATUtils.error('\t ! LSU {0} in subbasin {1} has zero area'.format(lsuId, SWATBasin), self._gv.isBatch)
                        areaKm = areaHa / 100
                        assert lsuData.cellCount > 0, 'LSU {0!s} has zero cell count'.format(lsuId)
                        meanSlopePercent = (lsuData.totalSlope / lsuData.cellCount) \
                                            * 100 * self._gv.meanSlopeMultiplier
                        tribSlopePercent = 0 if tribDistance < 1 else (tribDrop / tribDistance) \
                                                                    * 100 * self._gv.tributarySlopeMultiplier
                        tribWidth = self._gv.channelWidthMultiplier * (areaKm ** self._gv.channelWidthExponent)
                        tribDepth = self._gv.channelDepthMultiplier * (areaKm ** self._gv.channelDepthExponent)
                        centroid = self._gv.topo.pointToLatLong(QgsPointXY(lsuData.totalLongitude / lsuData.cellCount, 
                                                                         lsuData.totalLatitude / lsuData.cellCount))
                        lat = centroid.y()
                        lon = centroid.x()
                        meanElev = lsuData.totalElevation / lsuData.cellCount
                        curs.execute(DBUtils._LSUSINSERTSQL, (lsuId, landscape, SWATChannel, areaHa, meanSlopePercent, 
                                           tribDistance, tribSlopePercent, tribWidth, tribDepth, lat, lon, meanElev))
                        if addToSubs1:
                            # save LSU data for adding to lsus2 shapefile (saves searching it for each item)
                            saveLSUMap[lsuId] = dict()
                            amap = saveLSUMap[lsuId]
                            amap[catlsuIdx] = landscape
                            amap[slopelsuIdx] = meanSlopePercent
                            amap[len1lsuIdx] = tribDistance
                            amap[csllsuIdx] = tribSlopePercent
                            amap[wid1lsuIdx] = tribWidth
                            amap[dep1lsuIdx] = tribDepth
                            amap[latlsuIdx] = lat
                            amap[lonlsuIdx] = lon
                            amap[elevlsuIdx] = meanElev
            conn.commit()
            self._db.hashDbTable(conn, lsutable) 
            self._db.hashDbTable(conn, subtable) 
        if addToSubs1:
            OK = subsProvider1.changeAttributeValues(subMap)
            if not OK:
                QSWATUtils.error('\t ! Cannot write data to {0}'.format(subs1File), self._gv.isBatch)
            lsuMap = dict()
            toDelete = []
            request =  QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([lsuIdx])
            for feature in lsus2Layer.getFeatures(request):
                fid = feature.id()
                lsuId = feature[lsuIdx]
                if lsuId in saveLSUMap:
                    lsuMap[fid] = saveLSUMap[lsuId]
                else:
                    # was all water
                    toDelete.append(fid)
            OK = lsusProvider2.changeAttributeValues(lsuMap)
            if not OK:
                QSWATUtils.error('\t ! Cannot write data to {0}'.format(lsus2File), self._gv.isBatch)
            else:
                lsusProvider2.deleteFeatures(toDelete)
        # add subs1 layer in place of watershed layer, unless using grid model
        if not self._gv.useGridModel:
            root = QgsProject.instance().layerTreeRoot()
            subbasinsLayer = QSWATUtils.getLayerByFilename(root.findLayers(), self._gv.subbasinsFile, None, None, None, None)[0]
            if subbasinsLayer is not None:
                subLayer = root.findLayer(subbasinsLayer.id())
            else:
                subLayer = None
            ft = FileTypes._EXISTINGSUBBASINS if self._gv.existingWshed else FileTypes._SUBBASINS
            subs1Layer = QSWATUtils.getLayerByFilename(root.findLayers(), subs1File, ft, 
                                                       self._gv, subLayer, QSWATUtils._WATERSHED_GROUP_NAME)[0]
            subs1Layer.setLabelsEnabled(True)
            # no need to expand legend since any subbasins upstream from inlets have been removed
            subs1TreeLayer = root.findLayer(subs1Layer.id())
            subs1TreeLayer.setExpanded(False)
            if subbasinsLayer is not None:
                QSWATUtils.setLayerVisibility(subbasinsLayer, False, root)
            self.createAquifers(root)
        # TODO: create aquifers for grid models
        return True
    
    def createAquifers(self, root):
        """Creat aquifers shapefile."""
        
        def addNewField(layer, fileName, newFieldname, oldFieldname, fun):
            """Add new integer field to shapefile; set field to fun applied to value in old integer field; remove other fields."""
            fields = [QgsField(newFieldname, QVariant.Int)]
            provider = layer.dataProvider()
            provider.addAttributes(fields)
            layer.updateFields()
            oldIndex = self._gv.topo.getIndex(layer, oldFieldname)
            newIndex = self._gv.topo.getIndex(layer, newFieldname)
            request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([oldIndex, newIndex])
            mmap = dict()
            for f in provider.getFeatures(request):
                oldVal = int(f[oldIndex])
                mmap[f.id()] = {newIndex: fun(oldVal)}
            if not provider.changeAttributeValues(mmap):
                QSWATUtils.error('\t ! Cannot write data to {0}'.format(fileName), self._gv.isBatch)
            QSWATTopology.removeFields(provider, [newFieldname], fileName, self._gv.isBatch)
            
        def runProcess(command):
            """Run command"""
            try:
                subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                QSWATUtils.error("""Command {0} failed: 
{1}; 
{2}
""".format(command, e.stdout, e.stderr), self._gv.isBatch)
                
        def findOutlet(basin, downBasins):
            """downBasins maps basin to downstream basin or -1 if none.  Return final basin starting from basin."""
            downBasin = downBasins.get(basin, -1)
            if downBasin < 0:
                return basin
            else:
                return findOutlet(downBasin, downBasins)
            
        subsFile = QSWATUtils.join(self._gv.resultsDir, Parameters._SUBS + '.shp')
        if not os.path.exists(subsFile):
            return
        aqFile = QSWATUtils.join(self._gv.resultsDir, Parameters._AQUIFERS + '.shp')
        QSWATUtils.tryRemoveLayerAndFiles(aqFile, root)
        if self._dlg.floodplainCombo.currentIndex() == 0:
            # use subbasins shapefile as aquifers shapefile
            QSWATUtils.copyShapefile(subsFile, Parameters._AQUIFERS, self._gv.resultsDir)
            aqLayer = QgsVectorLayer(aqFile, 'Aquifers', 'ogr')
            addNewField(aqLayer, aqFile, QSWATTopology._AQUIFER, QSWATTopology._SUBBASIN,  lambda x: 10 * x)
        else:
            try:
                # create context to make processing turn off detection of what it claims are invalid shapes
                # as shapefiles generated from rasters, like the subbasins shapefile, often have such shapes
                context = QgsProcessingContext()
                context.setInvalidGeometryCheck(QgsFeatureRequest.GeometryNoCheck)
                QSWATUtils.loginfo('Context invalid geometry setting is {0}'.format(context.invalidGeometryCheck()))
                # first convert floodplain to polygons
                floodFile = self._dlg.floodplainCombo.currentText()
                floodPath = QSWATUtils.join(self._gv.floodDir, floodFile)
                floodShapefile = QSWATUtils.join(self._gv.shapesDir, 'flood.shp')
                QSWATUtils.tryRemoveLayerAndFiles(floodShapefile, root)
                command = 'python3 -m gdal_polygonize {0} {1} -b 1 -f "ESRI Shapefile" flood DN'. \
                        format(floodPath, floodShapefile)
                runProcess(command)
                
                # upslope aquifers are subbasins minus the floodplain
                upAqFile = QSWATUtils.tempFile('.shp')
                processing.run("native:difference", {'INPUT': subsFile, 'OVERLAY': floodShapefile, 'OUTPUT': upAqFile}, context=context)
                # add Aquifer field and seto to 10 * subbasin + 2
                upAqLayer = QgsVectorLayer(upAqFile, 'UpAquifers', 'ogr')
                addNewField(upAqLayer, upAqFile, QSWATTopology._AQUIFER, QSWATTopology._SUBBASIN,  lambda x: 10 * x + 2)
                
                # downslope aquifers are subbasins intersected with floodplain
                downAqFile = QSWATUtils.tempFile('.shp')
                processing.run("native:intersection", 
                               {'INPUT': subsFile, 'OVERLAY': floodShapefile, 'INPUT_FIELDS': [], 
                                'OVERLAY_FIELDS': [], 'OUTPUT': downAqFile}, context=context)
                # add Aquifer field and seto to 10 * subbasin + 1
                downAqLayer = QgsVectorLayer(downAqFile, 'DownAquifers', 'ogr')
                addNewField(downAqLayer, downAqFile, QSWATTopology._AQUIFER, QSWATTopology._SUBBASIN,  lambda x: 10 * x + 1)
                
                bothAqFile = QSWATUtils.tempFile('.shp')
                # merge up and down aquifers
                processing.run("native:mergevectorlayers", 
                               {'LAYERS': [upAqFile, downAqFile], 'CRS': None, 'OUTPUT': bothAqFile}, context=context)
                processing.run("native:dissolve", 
                               {'INPUT': bothAqFile, 'FIELD': [QSWATTopology._AQUIFER], 'OUTPUT': aqFile}, context=context)
                # merge adds some extra fields that we can lose
                aqLayer = QgsVectorLayer(aqFile, 'Aquifers', 'ogr')
                aqProvider = aqLayer.dataProvider()
                QSWATTopology.removeFields(aqProvider, [QSWATTopology._AQUIFER], aqFile, self._gv.isBatch)
                
                # create deep aquifer file by dissolving subbasins file
                # make map of subbasin to outlet subbasin in each watershed:
                outletSubbasins = dict()
                for basin in self._gv.topo.downSubbasins.keys():
                    SWATBasin = self._gv.topo.subbasinToSWATBasin.get(basin, 0)
                    if SWATBasin > 0:
                        outletSubbasins[SWATBasin] = self._gv.topo.subbasinToSWATBasin[findOutlet(basin, self._gv.topo.downSubbasins)]
                QSWATUtils.loginfo('Outlet subbasins: {0!s}'.format(outletSubbasins))
                deepAqFile = QSWATUtils.join(self._gv.resultsDir, Parameters._DEEPAQUIFERS + '.shp')
                QSWATUtils.tryRemoveLayerAndFiles(deepAqFile, root)
                QSWATUtils.copyShapefile(subsFile, 'deep_temp', self._gv.resultsDir)
                tempDeepAqFile = QSWATUtils.join(self._gv.resultsDir, 'deep_temp.shp')
                tempLayer = QgsVectorLayer(tempDeepAqFile, 'temp', 'ogr')
                # add Aquifer field, set to number of outlet subbasin
                addNewField(tempLayer, tempDeepAqFile, QSWATTopology._AQUIFER, QSWATTopology._SUBBASIN, lambda x: outletSubbasins[x])
                # dissolve on Aquifer field
                processing.run("native:dissolve", 
                               {'INPUT': tempDeepAqFile, 'FIELD': [QSWATTopology._AQUIFER], 'OUTPUT': deepAqFile}, context=context)
                # remove other fields
                deepLayer = QgsVectorLayer(deepAqFile, 'Deep Aquifer', 'ogr')
                deepProvider = deepLayer.dataProvider()
                QSWATTopology.removeFields(deepProvider, [QSWATTopology._AQUIFER], deepAqFile, self._gv.isBatch)
                QSWATUtils.tryRemoveFiles(tempDeepAqFile)
            except Exception as ex:
                QSWATUtils.information('\t - Failed to generate aquifers shapefile: aquifer result visualisation will not be possible: {0}'
                                       .format(repr(ex)), self._gv.isBatch)

    def generateBasinsFromShapefile(self, request, provider, polyIdx, subIdx):
        """Yield (feature id, basin, SWATBasin, basinData) tuples from subs1.shp."""
        for feature in provider.getFeatures(request):
            basin = feature[polyIdx]
            basinData = self.basins.get(basin, None)
            yield feature.id(), basin, feature[subIdx], basinData
            
    def generateBasinsFromTable(self):
        """Yield (feature id, basin, SWATBasin, basinData) tuples from tables."""
        for basin, basinData in self.basins.items():
            SWATBasin = self._gv.topo.subbasinToSWATBasin.get(basin, 0)
            yield 0, basin, SWATBasin, basinData
                
    def writeWaterBodiesTable(self):
        """Write gis_water table.  Also creates new reservoirs as needed."""
        self._gv.topo.foundReservoirs = dict()
        root = QgsProject.instance().layerTreeRoot()
        channelLayer, _ = QSWATUtils.getLayerByFilename(root.findLayers(), self._gv.channelFile, FileTypes._CHANNELS, 
                                                        None, None, None)
        if channelLayer is None:
            # perhaps user removed it
            channelLayer = QgsVectorLayer(self._gv.channelFile, 'Channels', 'ogr')
        with self._db.conn as conn:
            if not conn:
                return
            curs = conn.cursor()
            clearSQL = 'DROP TABLE IF EXISTS gis_water'
            curs.execute(clearSQL)
            curs.execute(self._db._WATERCREATESQL)
            # add lakes 
            for lakeId, lakeData in self._gv.topo.lakesData.items():
                lCat = 'RES' if lakeData.waterRole == 1 else 'PND'
                lsuId = 0  # no LSU for a lake
                (subbasin, _, _, _) = lakeData.outPoint
                SWATBasin = self._gv.topo.subbasinToSWATBasin[subbasin]
                areaHa = lakeData.area / 1E4
                centroid = lakeData.centroid
                centroidll = self._gv.topo.pointToLatLong(centroid)
                elev = lakeData.elevation
                curs.execute(self._db._WATERINSERTSQL, (lakeId, lCat, lsuId, SWATBasin, areaHa, centroid.x(), centroid.y(),
                                                        centroidll.y(), centroidll.x(), elev))
            # add reservoirs and ponds
            floodscape = QSWATUtils._FLOODPLAIN if self._gv.useLandscapes else QSWATUtils._NOLANDSCAPE
            for basinData in self.basins.values():
                for channel, channelData in basinData.getLsus().items():
                    SWATChannel = self._gv.topo.channelToSWATChannel.get(channel, -1)
                    for landscape, lsuData in channelData.items():
                        waterBody = lsuData.waterBody
                        if waterBody is not None and not waterBody.isUnknown():
                            if waterBody.cellCount == 0: 
                                if waterBody.isInlet(): # user-defined water body
                                    cat = 'reservoir' if waterBody.isReservoir() else 'pond'
                                    QSWATUtils.information('\t - WARNING: {0} on channel {1} has zero area'.format(cat, SWATChannel), self._gv.isBatch)
                                else:
                                    continue # upper part of reservoir
                            # set id if necessary:
                            if waterBody.id == 0:
                                self._gv.topo.waterBodyId += 1
                                waterBody.id = self._gv.topo.waterBodyId
                            if waterBody.isReservoir():
                                self.propagateReservoirId(channel, waterBody.id, floodscape)
                                wCat = 'RES'
                            else:
                                wCat = 'PND'
                            channel = self._gv.topo.finalTarget(channel, self.mergedChannels)
                            lsuId = QSWATUtils.landscapeUnitId(self._gv.topo.channelToSWATChannel[channel], landscape)
                            if self._gv.useGridModel:
                                basin = self._gv.topo.chLinkToChBasin[channel]
                            else:
                                chBasin = self._gv.topo.chLinkToChBasin[channel]
                                basin = self._gv.topo.chBasinToSubbasin[chBasin]
                            SWATBasin = self._gv.topo.subbasinToSWATBasin[basin]
                            area = waterBody.area / 1E4 # area in ha
                            # avoid division by zero for zero-area reservoirs
                            if waterBody.cellCount == 0:
                                x = waterBody.totalLongitude
                                y = waterBody.totalLatitude
                                meanElev = waterBody.totalElevation
                            else:
                                x = waterBody.totalLongitude / waterBody.cellCount
                                y = waterBody.totalLatitude / waterBody.cellCount
                                meanElev = waterBody.totalElevation / waterBody.cellCount
                            pt = QgsPointXY(x, y)
                            centroidll = self._gv.topo.pointToLatLong(pt)
                            curs.execute(self._db._WATERINSERTSQL, (waterBody.id, wCat, lsuId, SWATBasin, area, x, y,
                                                                       centroidll.y(), centroidll.x(), meanElev))
                            if waterBody.isReservoir() and not waterBody.isInlet():
                                # place reservoir point at channel outlet
                                channelData = self._gv.topo.channelsData[channel]
                                self._gv.topo.pointId += 1
                                resPt = QgsPointXY(channelData.lowerX, channelData.lowerY)
                                self._gv.topo.foundReservoirs[channel] = (waterBody.id, self._gv.topo.pointId, resPt)
            self._db.hashDbTable(conn, 'gis_water')
        reservoirsFile = QSWATUtils.join(self._gv.shapesDir, 'reservoirs.shp')
        # for some reason cannot rewrite this layer if rerun
        # QGIS has a lock on the .shp and .dbf files from somewhere
        # so instead always create a new file
        reservoirsFileN, _ = QSWATUtils.nextFileName(reservoirsFile, 0)
        if Delineation.createOutletFile(reservoirsFileN, self._gv.demFile, False, root, self._gv.isBatch):
            self.addReservoirsToFile(self._gv.topo.chPointSources, self.mergees, self._gv.topo.foundReservoirs, reservoirsFileN, root)
            
    def addReservoirsToFile(self, ptSources, mergees, reservoirs, outletFile, root):
        """Add reservoirs and point sources to outletFile.  Load as layer if not already loaded."""
        layer = QgsVectorLayer(outletFile, 'resandptsrc', 'ogr')
        provider = layer.dataProvider()
        fields = provider.fields()
        idIndex = provider.fieldNameIndex(QSWATTopology._ID)
        inletIndex = provider.fieldNameIndex(QSWATTopology._INLET)
        resIndex = provider.fieldNameIndex(QSWATTopology._RES)
        ptsourceIndex = provider.fieldNameIndex(QSWATTopology._PTSOURCE)
        for _, pointId, point in reservoirs.values():
            feature = QgsFeature()
            feature.setFields(fields)
            feature.setAttribute(idIndex, pointId)
            feature.setAttribute(inletIndex, 0)
            feature.setAttribute(resIndex, 1)
            feature.setAttribute(ptsourceIndex, 0)
            feature.setGeometry(QgsGeometry.fromPointXY(point))
            provider.addFeatures([feature])
        for channel, (pointId, point) in ptSources.items():
            # check channel not merged with one upstream
            # and not inside lake
            if channel not in mergees and \
               channel not in self._gv.topo.chLinkInsideLake and \
               not (self._gv.useGridModel and channel in self._gv.topo.chLinkFromLake):
                chBasin = self._gv.topo.chLinkToChBasin.get(channel, -1)
                subbasin = self._gv.topo.chBasinToSubbasin.get(chBasin, -1)
                if subbasin < 0 or subbasin in self._gv.topo.upstreamFromInlets:
                    continue
                feature = QgsFeature()
                feature.setFields(fields)
                feature.setAttribute(idIndex, pointId)
                feature.setAttribute(inletIndex, 1)
                feature.setAttribute(resIndex, 0)
                feature.setAttribute(ptsourceIndex, 1)
                feature.setGeometry(QgsGeometry.fromPointXY(point))
                provider.addFeatures([feature])
        addReservoirLayer, _ = QSWATUtils.getLayerByFilename(root.findLayers(), outletFile, FileTypes._EXTRAPTSRCANDRES,
                                                             self._gv, None, QSWATUtils._WATERSHED_GROUP_NAME)
        if not addReservoirLayer:
            QSWATUtils.error('\t ! Could not load reservoir file {0}'.format(outletFile), self._gv.isBatch)
            return
        
    def propagateReservoirId(self, start, rid, floodscape):
        """Set water body id to rid for upstream components of this reservoir."""
        for channel in self._gv.topo.channelToSWATChannel.keys():
            dsChannel = self._gv.topo.finalDownstream(channel, self.mergedChannels)
            if dsChannel == start:
                chBasin = self._gv.topo.chLinkToChBasin.get(channel, -1)
                subbasin = self._gv.topo.chBasinToSubbasin.get(chBasin, -1)
                basinData = self.basins.get(subbasin, None)
                if basinData is not None:
                    channelData = basinData.getLsus().get(channel, None)
                    if channelData is not None:
                        lsuData = channelData.get(floodscape, None)
                        if lsuData is not None:
                            waterBody = lsuData.waterBody
                            if waterBody is not None and waterBody.isReservoir() and waterBody.cellCount == 0 and waterBody.id == 0:
                                waterBody.id = rid
                                self.propagateReservoirId(channel, rid, floodscape)
                        
    def totalBasinsArea(self):
        """Return sum of areas of subbasins (land and water) in square metres."""
        total = 0
        for bd in self.basins.values():
            for channelData in bd.getLsus().values():
                for lsuData in channelData.values():
                    total += lsuData.area
        return total
    
    def totalLandscapeAreas(self):
        """Return a map landscape unit -> area (land and water) in square metres across all subbasins."""
        result = dict()
        for bd in self.basins.values():
            for channelData in bd.getLsus().values():
                for landscape, lsuData in channelData.items():
                    area = result.get(landscape, 0)
                    result[landscape] = area + lsuData.area
        return result
    
    def totalCropAreas(self, withHRUs):
        """
        Return maps of crop -> area in square metres across all subbasins.
        
        If withHRUs, return updated and original values.
        Otherise return the original values, and first map is None
        
        Ignore WATR if there is a pond or reservoir in the LSU
        
        """
        result1 = dict() if withHRUs else None
        result2 = dict()
        for bd in self.basins.values():
            for channelData in bd.getLsus().values():
                for lsuData in channelData.values():
                    map1 = lsuData.cropAreas if withHRUs else None
                    map2 =  lsuData.originalCropAreas
                    if map1 is not None:
                        for (crop, area) in map1.items():
                            if crop in result1:
                                result1[crop] += area
                            else:
                                result1[crop] = area
                    for (crop, area) in map2.items():
                        if crop in result2:
                            result2[crop] += area
                        else:
                            result2[crop] = area
        return (result1, result2)
    
    def totalSoilAreas(self, withHRUs):
        """Return map of soil -> area in square metres across all subbasins.
        
        If withHRUs, return updated and original values.
        Otherise return the original values, and first map is None
        
        """
        result1 = dict() if withHRUs else None
        result2 = dict()
        for bd in self.basins.values():
            for channelData in bd.getLsus().values():
                for lsuData in channelData.values():
                    map1 = lsuData.soilAreas if withHRUs else None
                    map2 = lsuData.originalSoilAreas
                    if map1 is not None:
                        for (soil, area) in map1.items():
                            if soil in result1:
                                result1[soil] += area
                            else:
                                result1[soil] = area
                    for (soil, area) in map2.items():
                        if soil in result2:
                            result2[soil] += area
                        else:
                            result2[soil] = area
        return (result1, result2)
    
    def totalSlopeAreas(self, withHRUs):
        """Return map of slope -> area in square metres across all subbasins.
        
        If withHRUs, return updated and original values.
        Otherise return the original values, and first map is None
        
        """
        result1 = dict() if withHRUs else None
        result2 = dict()
        for bd in self.basins.values():
            for channelData in bd.getLsus().values():
                for lsuData in channelData.values():
                    map1 = lsuData.slopeAreas if withHRUs else None
                    map2 = lsuData.originalSlopeAreas
                    if map1 is not None:
                        for (slope, area) in map1.items():
                            if slope in result1:
                                result1[slope] += area
                            else:
                                result1[slope] = area
                    for (slope, area) in map2.items():
                        if slope in result2:
                            result2[slope] += area
                        else:
                            result2[slope] = area
        return (result1, result2)
    
    def totalLakesArea(self):
        """Return total lakes area in square metres."""
        result = 0
        for lakeData in self._gv.topo.lakesData.values():
            result += lakeData.area
        return result
    
    def getLakeAreas(self):
        """Return map of lake id to lake area in square metres."""
        result = dict()
        for lakeId, lakeData in self._gv.topo.lakesData.items():
            result[lakeId] = lakeData.area
        return result
    
    def totalWaterBodiesArea(self):
        """Return total water bodies (reservoirs and ponds) area in square metres across all subbasins."""
        result = 0
        for basinData in self.basins.values():
            for channelData in basinData.getLsus().values():
                for lsuData in channelData.values():
                    if lsuData.waterBody is not None and not lsuData.waterBody.isUnknown():
                        result += lsuData.waterBody.originalArea
        return result
    
    def basinWaterBodiesArea(self, basinData):
        """Return water bodies (reservoirs and ponds) area for basinData."""
        result = 0
        for channelData in basinData.getLsus().values():
            for lsuData in channelData.values():
                if lsuData.waterBody is not None and not lsuData.waterBody.isUnknown():
                    result += lsuData.waterBody.originalArea
        return result
    
    def printChannelArea(self, SWATChannel, areaSqM, withHRUs, total1, total2, fw):
        """Print a line containing the channel identifier, area in hectares.
        percent of total1, , percent of total2 (unless zero)"""
        width1 = 30 if withHRUs else 15
        width2 = 23 if withHRUs else 15
        area = areaSqM / 10000
        channelId = 'Channel {0!s}'.format(SWATChannel)
        string0 = '{:.2F}'.format(area).rjust(15)
        if self._gv.useLandscapes:
            fw.write(channelId.ljust(30) + string0)
        else:
            lsuId = QSWATUtils.landscapeUnitId(SWATChannel, QSWATUtils._NOLANDSCAPE)
            fw.write('{0} (LSU {1})'.format(channelId, lsuId).ljust(30) + string0)
        if total1 > 0:
            percent1 = (area / total1) * 100
            string1 = '{:.2F}'.format(percent1).rjust(width1)
            fw.write(string1)
            if total2 > 0:
                percent2 = (area / total2) * 100
                string2 = '{:.2F}'.format(percent2).rjust(width2)
                fw.write(string2)
        fw.writeLine('')
    
    def printLandscapeAreas(self, landscapeAreas, withHRUs, total1, total2, fw):
        """ Print a line containing landscape name, area in hectares, 
        percent of total1, percent of total2 (unless zero)."""
        width1 = 30 if withHRUs else 15
        width2 = 23 if withHRUs else 15
        # seems natural to list these in numeric order
        for landscape in [QSWATUtils._FLOODPLAIN, QSWATUtils._UPSLOPE]:
            areaM = landscapeAreas.get(landscape, 0)
            if areaM > 0:
                lsuName = QSWATUtils.landscapeName(landscape, self._gv.useLeftRight)
                area = areaM / 1E4
                string0 = '{:.2F}'.format(area).rjust(15)
                fw.write(lsuName.rjust(30) + string0)
                if total1 > 0:
                    percent1 = (area / total1) * 100
                    string1 = '{:.2F}'.format(percent1).rjust(width1)
                    fw.write(string1)
                    if total2 > 0:
                        percent2 = (area / total2) * 100
                        string2 = '{:.2F}'.format(percent2).rjust(width2)
                        fw.write(string2)
                fw.writeLine('')

    def printCropAreas(self, cropAreas, originalCropAreas, total1, total2, fw):
        """ Print a line containing crop, area in hectares, 
        percent of total1, percent of total2.
        
        If cropAreas is not None, use its figures and add original figures in bracket for comparison.
        """
        if cropAreas is None or len(cropAreas) == 0:
            main = originalCropAreas
            original = None
        else:
            main = cropAreas
            original = originalCropAreas
        for (crop, areaM) in main.items():
            landuseCode = self._db.getLanduseCode(crop)
            area = areaM / 10000
            string0 = '{:.2F}'.format(area).rjust(15)
            if original is not None:
                # crop may not have been in original because of splitting
                originalArea = original.get(crop, 0) / 10000
                string0 += '({:.2F})'.format(originalArea).rjust(15)  
            fw.write(landuseCode.rjust(30) + string0)
            if total1 > 0:
                percent1 = (area / total1) * 100
                string1 = '{:.2F}'.format(percent1).rjust(15)
                if original:
                    opercent1 = (originalArea / total1) * 100
                    string1 += '({:.2F})'.format(opercent1).rjust(8)
                fw.write(string1)
                if total2 > 0:
                    percent2 = (area / total2) * 100
                    string2 = '{:.2F}'.format(percent2).rjust(15)
                    if original:
                        opercent2 = (originalArea / total2) * 100
                        string2 += '({:.2F})'.format(opercent2).rjust(8)
                    fw.write(string2)
            fw.writeLine('')
        # if have original, add entries for originals that have been removed
        if original is not None:
            for (crop, areaM) in original.items():
                if crop not in main:
                    landuseCode = self._db.getLanduseCode(crop)
                    originalArea = areaM / 10000
                    fw.write(landuseCode.rjust(30) + '({:.2F})'.format(originalArea).rjust(30))
                    if total1 > 0:
                        opercent1 = (originalArea / total1) * 100
                        fw.write('({:.2F})'.format(opercent1).rjust(23))
                    if total2 > 0:
                        opercent2 = (originalArea / total2) * 100
                        fw.write('({:.2F})'.format(opercent2).rjust(23))
                    fw.writeLine('')
       
    def printSoilAreas(self, soilAreas, originalSoilAreas, total1, total2, fw):
        """ Print a line containing soil, area in hectares, 
        percent of total1, percent of total2.
        
        If soilAreas is not None, use its figures and add original figures in bracket for comparison.
        """
        if soilAreas is None or len(soilAreas) == 0:
            main = originalSoilAreas
            original = None
        else:
            main = soilAreas
            original = originalSoilAreas
        for (soil, areaM) in main.items():
            soilName = self._db.getSoilName(soil)
            area = areaM / 10000
            string0 = '{:.2F}'.format(area).rjust(15)
            if original:
                originalArea = original[soil] / 10000
                string0 += '({:.2F})'.format(originalArea).rjust(15)  
            fw.write(soilName.rjust(30) + string0)
            if total1 > 0:
                percent1 = (area / total1) * 100
                string1 = '{:.2F}'.format(percent1).rjust(15)
                if original:
                    opercent1 = (originalArea / total1) * 100
                    string1 += '({:.2F})'.format(opercent1).rjust(8)
                fw.write(string1)
                if total2 > 0:
                    percent2 = (area / total2) * 100
                    string2 = '{:.2F}'.format(percent2).rjust(15)
                    if original:
                        opercent2 = (originalArea / total2) * 100
                        string2 += '({:.2F})'.format(opercent2).rjust(8)
                    fw.write(string2)
            fw.writeLine('')
        # if have original, add entries for originals that have been removed
        if original:
            for (soil, areaM) in original.items():
                if soil not in main:
                    soilName = self._db.getSoilName(soil)
                    originalArea = areaM / 10000
                    fw.write(soilName.rjust(30) + '({:.2F})'.format(originalArea).rjust(30))
                    if total1 > 0:
                        opercent1 = (originalArea / total1) * 100
                        fw.write('({:.2F})'.format(opercent1).rjust(23))
                    if total2 > 0:
                        opercent2 = (originalArea / total2) * 100
                        fw.write('({:.2F})'.format(opercent2).rjust(23))
                    fw.writeLine('')
        
    def printSlopeAreas(self, slopeAreas, originalSlopeAreas, total1, total2, fw):
        """ Print a line containing slope, area in hectares, 
        percent of total1, percent of total2.
        
        If slopeAreas is not None, use its figures and add original figures in bracket for comparison.
        """
        if slopeAreas is None or len(slopeAreas) == 0:
            main = originalSlopeAreas
            original = None
        else:
            main = slopeAreas
            original = originalSlopeAreas
        # seems natural to list these in increasing order
        for i in range(len(self._db.slopeLimits) + 1):
            if i in main:
                slopeRange = self._db.slopeRange(i)
                area = main[i] / 10000
                string0 = '{:.2F}'.format(area).rjust(15)
                if original:
                    originalArea = original[i] / 10000
                    string0 += '({:.2F})'.format(originalArea).rjust(15)  
                fw.write(slopeRange.rjust(30) + string0)
                if total1 > 0:
                    percent1 = (area / total1) * 100
                    string1 = '{:.2F}'.format(percent1).rjust(15)
                    if original:
                        opercent1 = (originalArea / total1) * 100
                        string1 += '({:.2F})'.format(opercent1).rjust(8)
                    fw.write(string1)
                    if total2 > 0:
                        percent2 = (area / total2) * 100
                        string2 = '{:.2F}'.format(percent2).rjust(15)
                        if original:
                            opercent2 = (originalArea / total2) * 100
                            string2 += '({:.2F})'.format(opercent2).rjust(8)
                        fw.write(string2)
                fw.writeLine('')
        # if have original, add entries for originals that have been removed
        if original:
            for i in range(len(self._db.slopeLimits) + 1):
                if i in original and i not in main:
                    slopeRange = self._db.slopeRange(i)
                    originalArea = original[i] / 10000
                    fw.write(slopeRange.rjust(30) + '({:.2F})'.format(originalArea).rjust(30))
                    if total1 > 0:
                        opercent1 = (originalArea / total1) * 100
                        fw.write('({:.2F})'.format(opercent1).rjust(23))
                    if total2 > 0:
                        opercent2 = (originalArea / total2) * 100
                        fw.write('({:.2F})'.format(opercent2).rjust(23))
                    fw.writeLine('')
                    
    def printLakeArea(self, area, total, num, withHRUs, fw):
        """Print a line for lake num (or lakes if num is zero) with area in hectares and percent of total."""
        areaHa = area / 1E4
        if total > 0:
            string0 = 'Lake {0}'.format(num) if num > 0 else 'Lakes'
            string1 = '{:.2F}'.format(areaHa).rjust(15)
            percent = (areaHa / total) * 100
            just2 = 30 if withHRUs else 15
            string2 = '{:.2F}'.format(percent).rjust(just2)
            fw.writeLine(string0.ljust(30) + string1 + string2)
        
    def printWaterArea(self, area, total1, total2, withHRUs, fw):
        """Print a line containing area in hectares,  
        percent of total1, percent of total2.
        
        Bracketed figures are unnecessary because we know water area does not change when HRUs are formed."""
        areaHa = area / 10000
        if total1 > 0:
            string0 = '{:.2F}'.format(areaHa).rjust(15)
            fw.write('Reservoirs and ponds'.ljust(30) + string0)
            percent1 = (areaHa / total1) * 100
            just1 = 30 if withHRUs else 15
            string1 = '{:.2F}'.format(percent1).rjust(just1)
            fw.write(string1)
            if total2 > 0:
                percent2 = (areaHa / total2) * 100
                just2 = 23 if withHRUs else 15
                string2 = '{:.2F}'.format(percent2).rjust(just2)
                fw.write(string2)
        fw.writeLine('')
        
