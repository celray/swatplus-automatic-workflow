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
"""
# Import the PyQt and QGIS libraries 
from qgis.PyQt.QtCore import QObject, Qt, QFileInfo, QSettings, QVariant, NULL
from qgis.PyQt.QtGui import QDoubleValidator, QIntValidator
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import Qgis, QgsUnitTypes, QgsWkbTypes, QgsCoordinateTransformContext, QgsFeature, QgsFeatureRequest, QgsField, QgsFields, QgsGeometry, QgsPointXY, QgsLayerTree, QgsLayerTreeModel, QgsLayerTreeLayer, QgsRasterLayer, QgsVectorLayer, QgsVectorFileWriter, QgsProject
from qgis.gui import QgsMapCanvas, QgsMapTool, QgsMapToolEmitPoint
from qgis.analysis import QgsRasterCalculator, QgsRasterCalculatorEntry
import os
import glob
import shutil
import math
#import subprocess
import time
from osgeo import gdal, ogr  # type: ignore
import csv
import locale
import processing  # type: ignore
from processing.core.Processing import Processing  # type: ignore # @UnresolvedImport @UnusedImport
import traceback
from typing import Optional, Tuple, Dict, Set, List, Any, TYPE_CHECKING, cast  # @UnusedImport

# Import the code for the dialog
from .delineationdialog import DelineationDialog  # type: ignore
from .TauDEMUtils import TauDEMUtils  # type: ignore
from .QSWATUtils import QSWATUtils, fileWriter, FileTypes, ListFuns, MapFuns  # type: ignore
from .QSWATTopology import QSWATTopology  # type: ignore
from .globals import GlobalVars  # type: ignore #  @UnusedImport 
from .landscape import Landscape  # type: ignore
from .outletsdialog import OutletsDialog  # type: ignore
from .selectsubs import SelectSubbasins  # type: ignore
from .parameters import Parameters  # type: ignore
from .polygonizeInC2 import Polygonize  # type: ignore # @UnresolvedImport

if TYPE_CHECKING:
    from globals import GlobalVars  # @UnresolvedImport @Reimport

## type for geotransform
Transform = Dict[int, float]

class GridData:
    
    """Data about grid cell."""
    
    def __init__(self, num: int, area: int, drainArea: float, maxAcc: int, maxRow: int, maxCol: int) -> None:
        """Constructor."""
        ## PolygonId of this grid cell
        self.num = num
        ## PolygonId of downstream grid cell
        self.downNum = -1
        ## Row in storeGrid of downstream grid cell
        self.downRow = -1
        ## Column in storeGrid of downstream grid cell
        self.downCol = -1
        ## area of this grid cell in number cells in accumulation grid
        self.area = area
        ## area being drained in sq km to start of stream in this grid cell
        self.drainArea = drainArea
        ## accumulation at maximum accumulation point
        self.maxAcc = maxAcc
        ## Row in accumulation grid of maximum accumulation point
        self.maxRow = maxRow
        ## Column in accumulation grid of maximum accumulation point
        self.maxCol = maxCol
        ## dsnodeid, or -1 if none (and initially)
        self.dsNodeId = -1
            
class Points:
    """Enumeration of inlet/outlets points."""
    _OUTLET = 0
    _INLET = 1
    _RESERVOIR = 2
    _POND = 3
    _POINTSOURCE = 4
    
    @staticmethod
    def toString(point: int) -> str:
        """String for each point."""
        if point == Points._OUTLET:
            return 'outlet'
        elif point == Points._INLET:
            return 'inlet'
        elif point == Points._RESERVOIR:
            return 'reservoir'
        elif point == Points._POND:
            return 'pond'
        else:
            return 'point source'
    
# noinspection PySimplifyBooleanCheck,PyCallByClass,PyArgumentList
class Delineation(QObject): 
    
    """Do watershed delineation."""
    
    def __init__(self, gv: GlobalVars, isDelineated: bool) -> None:
        """Initialise class variables."""
        QObject.__init__(self)
        self._gv = gv
        self._dlg = DelineationDialog()
        self._dlg.setWindowFlags(self._dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint & Qt.WindowMinimizeButtonHint)
        self._dlg.move(self._gv.delineatePos)
        ## when not all points are snapped this is set True so snapping can be rerun
        self.snapErrors = False
        self._odlg = OutletsDialog()
        self._odlg.setWindowFlags(self._odlg.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self._odlg.move(self._gv.outletsPos)
        ## Qgs vector layer for drawing inlet/outlet points
        self.drawOutletLayer: Optional[QgsVectorLayer] = None
        ## area of DEM cell in sq m
        self.areaOfCell = 0.0
        ## Width of DEM as number of cells
        self.demWidth = 0
        ## Height of DEM cell as number of cells
        self.demHeight = 0
        ## flag to prevent infinite recursion between number of cells and area
        self.changing = False
        ## inlet/outlet points, stored as map from inlet/outlet file id to QgsPoint: 
        ## used in grid model only
        self.inletOutletPoints: Dict[int, Tuple[int, QgsPointXY]] = dict()
        ## flag to show basic delineation is done, so removing subbasins, 
        ## adding reservoirs and point sources may be done
        self.isDelineated = isDelineated
        ## flag to show delineation completed successfully or not
        self.delineationFinishedOK = True
        ## flag to show if threshold or outlet file changed since loading form; 
        ## if not can assume any existing watershed is OK
        self.thresholdChanged = False
        ## flag to show finishDelineation has been run
        self.finishHasRun = False
        ## mapTool used for drawing outlets etc
        self.mapTool: Optional[QgsMapToolEmitPoint] = None
        ## flag to show if drainage for existing grid defined by attribute in grid (when true), else by streams shapefile or drainage table
        self.gridDrainage = False
        ## flag to show if drainage for existing grid defined by streams shapefile (when true) or by drainage table
        self.streamDrainage = True
        ## drainage table csv file
        self.drainageTable = ''
        ## landscape object
        self.L: Optional[Landscape] = None
        ## copy of subbasins file, set when making grids before grid file overwrites it
        # while it is the empty string the subbasins file may be used
        self.clipperFile = ''
        ## flag to show if lakes file yet to be dealt with
        self.lakesDone = True
        ## flag to show if lake inlet/outlet points added and channels split (for non-grid models)
        self.lakePointsAdded = False
        ## flag to show if grid lakes have been created from lake shapefile when using grid model
        self.gridLakesAdded = False
        
    def init(self) -> None:
        """Set connections to controls; read project delineation data."""
        settings = QSettings()
        try:
            self._dlg.numProcesses.setValue(int(settings.value('/QSWATPlus/NumProcesses')))
        except Exception:
            self._dlg.numProcesses.setValue(8)
        self._dlg.selectDemButton.clicked.connect(self.btnSetDEM)
        self._dlg.checkBurn.stateChanged.connect(self.changeBurn)
        self._dlg.useGrid.clicked.connect(self.changeUseGrid)
        self._dlg.gridBox.clicked.connect(self.changeUseGrid)
        self._dlg.burnButton.clicked.connect(self.btnSetBurn)
        self._dlg.selectOutletsButton.clicked.connect(self.btnSetOutlets)
        self._dlg.selectSubbasinsButton.clicked.connect(self.btnSetSubbasins)
        self._dlg.selectWshedButton.clicked.connect(self.btnSetWshed)
        self._dlg.selectStreamsButton.clicked.connect(self.btnSetStreams)
        self._dlg.selectExistOutletsButton.clicked.connect(self.btnSetOutlets)
        self._dlg.delinRunButton1.clicked.connect(self.runTauDEM1)
        self._dlg.delinRunButton2.clicked.connect(self.runTauDEM2)
        self._dlg.tabWidget.currentChanged.connect(self.changeExisting)
        self._dlg.drainGridButton.clicked.connect(self.setDrainage)
        self._dlg.drainStreamsButton.clicked.connect(self.setDrainage)
        self._dlg.drainTableButton.clicked.connect(self.setDrainage)
        self._dlg.existRunButton.clicked.connect(self.runExisting)
        self._dlg.useOutlets.stateChanged.connect(self.changeUseOutlets)
        self._dlg.drawOutletsButton.clicked.connect(self.drawOutlets)
        self._dlg.selectOutletsInteractiveButton.clicked.connect(self.selectOutlets)
        self._dlg.snapReviewButton.clicked.connect(self.snapReview)
        self._dlg.landscapeButton.clicked.connect(self.runLandscape)
        self._dlg.selectSubButton.clicked.connect(self.selectMergeSubbasins)
        self._dlg.mergeButton.clicked.connect(self.mergeSubbasins)
        self._dlg.selectLakesButton.clicked.connect(self.addLakesMap)
        self._dlg.removeLakeCells.clicked.connect(self.removeLakeCells)
        self._dlg.addLakeCells.clicked.connect(self.addLakeCells)
        self._dlg.taudemHelpButton.clicked.connect(TauDEMUtils.taudemHelp)
        self._dlg.OKButton.clicked.connect(self.finishDelineation)
        self._dlg.cancelButton.clicked.connect(self.doClose)
        self._dlg.numCellsCh.setValidator(QIntValidator())
        self._dlg.numCellsSt.setValidator(QIntValidator())
        self._dlg.numCellsCh.textChanged.connect(self.setAreaCh)
        self._dlg.areaCh.textChanged.connect(self.setNumCellsCh)
        self._dlg.numCellsSt.textChanged.connect(self.setAreaSt)
        self._dlg.areaSt.textChanged.connect(self.setNumCellsSt)
        self._dlg.areaCh.setValidator(QDoubleValidator())
        self._dlg.areaSt.setValidator(QDoubleValidator())
        self._dlg.areaUnitsBox.addItem(Parameters._SQKM)
        self._dlg.areaUnitsBox.addItem(Parameters._HECTARES)
        self._dlg.areaUnitsBox.addItem(Parameters._SQMETRES)
        self._dlg.areaUnitsBox.addItem(Parameters._SQMILES)
        self._dlg.areaUnitsBox.addItem(Parameters._ACRES)
        self._dlg.areaUnitsBox.addItem(Parameters._SQFEET)
        self._dlg.areaUnitsBox.activated.connect(self.changeAreaOfCell)
        self._dlg.horizontalCombo.addItem(Parameters._METRES)
        self._dlg.horizontalCombo.addItem(Parameters._FEET)
        self._dlg.horizontalCombo.addItem(Parameters._DEGREES)
        self._dlg.horizontalCombo.addItem(Parameters._UNKNOWN)
        self._dlg.verticalCombo.addItem(Parameters._METRES)
        self._dlg.verticalCombo.addItem(Parameters._FEET)
        self._dlg.verticalCombo.addItem(Parameters._CM)
        self._dlg.verticalCombo.addItem(Parameters._MM)
        self._dlg.verticalCombo.addItem(Parameters._INCHES)
        self._dlg.verticalCombo.addItem(Parameters._YARDS)
        # set vertical unit default to metres
        self._dlg.verticalCombo.setCurrentIndex(self._dlg.verticalCombo.findText(Parameters._METRES))
        self._dlg.verticalCombo.activated.connect(self.setVerticalUnits)
        self._dlg.snapThreshold.setValidator(QIntValidator())
        self._odlg.resumeButton.clicked.connect(self.resumeDrawing)
        self.readProj()
        self.changeUseGrid()
        self.thresholdChanged = False
        self.checkMPI()
        # allow for cancellation without being considered an error
        self.delineationFinishedOK = True
        # Prevent annoying "error 4 .shp not recognised" messages.
        # These should become exceptions but instead just disappear.
        # Safer in any case to raise exceptions if something goes wrong.
        gdal.UseExceptions()
        ogr.UseExceptions()
        
    def setMergeResGroups(self) -> None:
        """Allow landscape unit definition, lake definition, and merging of subbasins if delineation complete.
        
        Also set merge group only visible if not using grid model.
        """
        self._dlg.drainGroupBox.setVisible(self._gv.useGridModel)
        self._dlg.landscapeTab.setEnabled(self.isDelineated)
        self._dlg.mergeTab.setEnabled(self.isDelineated and not self._gv.useGridModel)
        self._dlg.lakesTab.setEnabled(self.isDelineated)
        self._dlg.OKButton.setEnabled(self.isDelineated)
        
    def run(self) -> int:
        """Do delineation; check done and save topology data.  Return 1 if delineation done and no errors, 2 if not delineated and nothing done, else 0."""
        self.init()
        self._dlg.show()
        _ = self._dlg.exec_()
        self._gv.delineatePos = self._dlg.pos()
        if self.delineationFinishedOK:
            if self.finishHasRun:
                self._gv.writeProjectConfig(1,0) 
                return 1
            else:
                # nothing done
                return 2
        self._gv.writeProjectConfig(0,0)
        return 0
    
    def checkMPI(self) -> None:
        """
        In Windows, try to make sure there is just one msmpi.dll, either on the path or in the TauDEM directory.
        
        TauDEM executables are built on the assumption that MPI is available.
        But they can run without MPI if msmpi.dll is placed in their directory.
        MPI will fail if there is an msmpi.dll on the path and one in the TauDEM directory 
        (unless they happen to be the same version).
        QSWAT supplies msmpi_dll in the TauDEM directory that can be renamed to provide msmpi.dll 
        if necessary.
        This function is called every time delineation is started so that if the user installs MPI
        or uninstalls it the appropriate steps are taken.
        """
        if not Parameters._ISWIN:
            return
        dll = 'msmpi.dll'
        dummy = 'msmpi_dll'
        dllPath = QSWATUtils.join(self._gv.TauDEMDir, dll)
        dummyPath = QSWATUtils.join(self._gv.TauDEMDir, dummy)
        # tried various methods here.  
        #'where msmpi.dll' succeeds if it was there and is moved or renamed - cached perhaps?
        # isfile fails similarly
        #'where mpiexec' always fails because when run interactively the path does not include the MPI directory
        # so just check for existence of mpiexec.exe and assume user will not leave msmpi.dll around
        # if MPI is installed and then uninstalled
        if os.path.isfile(self._gv.mpiexecPath):
            QSWATUtils.loginfo('mpiexec found')
            # MPI is on the path; rename the local dll if necessary
            if os.path.exists(dllPath):
                if os.path.exists(dummyPath):
                    os.remove(dllPath)
                    QSWATUtils.loginfo('dll removed')
                else:
                    os.rename(dllPath, dummyPath)
                    QSWATUtils.loginfo('dll renamed')
        else:
            QSWATUtils.loginfo('mpiexec not found')
            # we don't have MPI on the path; rename the local dummy if necessary
            if os.path.exists(dllPath):
                return
            elif os.path.exists(dummyPath):
                os.rename(dummyPath, dllPath)
                QSWATUtils.loginfo('dummy renamed')
            else:
                QSWATUtils.error('Cannot find executable mpiexec in the system or {0} in {1}: TauDEM functions will not run.  Install MPI or reinstall QSWAT+.'.format(dll, self._gv.TauDEMDir), self._gv.isBatch)

    # noinspection PyArgumentList
    def finishDelineation(self) -> None:
        """
        Finish delineation.
        
        Adds lakes if necessary, checks stream reaches and watersheds defined, sets DEM attributes, 
        checks delineation is complete, calculates flow distances,
        runs topology setup.  Writes reaches and points tables.  
        Sets delineationFinishedOK to true if all completed successfully.
        """
        if self._gv.lakeFile != '' and not self.lakesDone:
            self.addLakes()
        self.delineationFinishedOK = False
        self.finishHasRun = True
        root = QgsProject.instance().layerTreeRoot()
        layers = root.findLayers()
        chanFile = self._gv.streamFile if self._gv.useGridModel else self._gv.channelFile
        channelLayer = QSWATUtils.getLayerByFilename(layers, chanFile, FileTypes._CHANNELS, None, None, None)[0]
        if channelLayer is None:
            if self._gv.useGridModel:
                QSWATUtils.error('Grid streams layer not found.', self._gv.isBatch)
            elif self._gv.existingWshed:
                QSWATUtils.error('Channels layer not found.', self._gv.isBatch)
            else:
                QSWATUtils.error('Channels layer for {0} not found: have you run TauDEM?'.format(chanFile), self._gv.isBatch)
            return
        if not self._gv.existingWshed and self._gv.useGridModel:
            subbasinsTreeLayer = QSWATUtils.getLayerByLegend(QSWATUtils._GRIDLEGEND, layers)
            if subbasinsTreeLayer is None:
                QSWATUtils.error('Grid layer not found.', self._gv.isBatch)
                return
            else:
                subbasinsLayer = subbasinsTreeLayer.layer()
        else:
            ft = FileTypes._EXISTINGSUBBASINS if self._gv.existingWshed else FileTypes._SUBBASINS
            subbasinsLayer = QSWATUtils.getLayerByFilename(layers, self._gv.subbasinsFile, ft, None, None, None)[0]
            if subbasinsLayer is None:
                if self._gv.existingWshed:
                    QSWATUtils.error('Subbasins layer not found.', self._gv.isBatch)
                else:
                    QSWATUtils.error('Subbasins layer not found: have you run TauDEM?', self._gv.isBatch)
                return
        demLayer = QSWATUtils.getLayerByFilename(layers, self._gv.demFile, FileTypes._DEM, None, None, None)[0]
        if demLayer is None:
            QSWATUtils.error('DEM layer not found: have you removed it?', self._gv.isBatch)
            return
        if not self.setDimensions(demLayer):
            return
        if not self._gv.useGridModel and self._gv.basinFile == '':
            # must have merged some subbasins: recreate the subbasins raster
            self._gv.basinFile = self.createBasinFile(self._gv.subbasinsFile, demLayer, 'wStream', root)
            # QSWATUtils.loginfo('Recreated watershed grid as {0}'.format(self._gv.basinFile))
        self.saveProj()
        if self.checkDEMProcessed():
            recalculate = self._gv.existingWshed and self._dlg.recalcButton.isChecked()
            self.progress('Constructing topology ...')
            if self._gv.outletFile == '':
                outletLayer: Optional[QgsVectorLayer] = None
            elif not self._gv.existingWshed and os.path.exists(self._gv.snapFile):
                outletLayer = QgsVectorLayer(self._gv.snapFile, 'Snapped inlets/outlets', 'ogr')
            else:
                outletLayer = QSWATUtils.getLayerByFilename(layers, self._gv.outletFile, FileTypes._OUTLETS, None, None, None)[0]
            if os.path.exists(self._gv.lakeFile):
                lakesLayer: Optional[QgsVectorLayer] = QSWATUtils.getLayerByFilename(layers, self._gv.lakeFile, FileTypes._LAKES, None, None, None)[0]
            else:
                lakesLayer = None
            if self._gv.topo.setUp(demLayer, channelLayer, subbasinsLayer, outletLayer, lakesLayer,
                                   self._gv, self._gv.existingWshed, recalculate, 
                                   self._gv.useGridModel, self.streamDrainage, True):
                if len(self._gv.topo.inlets) == 0:
                    # no inlets, so no need to expand subbasins layer legend
                    basinsLayer: Optional[QgsLayerTreeLayer] = QSWATUtils.getLayerByLegend(QSWATUtils._SUBBASINSLEGEND, root.findLayers())
                    if basinsLayer is not None:
                        basinsLayer.setExpanded(False)
                self.makeDistancesToOutlets()
                self.delineationFinishedOK = True
                self.progress('')
                self.doClose()
                return
            else:
                self.progress('')
                return
        return
    
    def addLakes(self) -> None:
        """Add lakes from lakes shapefile."""
        
        QSWATUtils.loginfo('{0} outlets before adding lakes'.format(len(self._gv.topo.outlets)))
        if self.lakesDone or self._gv.lakeFile == '':
            return
        if not os.path.exists(self._gv.lakeFile):
            QSWATUtils.error('Cannot find lakes file {0}'.format(self._gv.lakeFile), self._gv.isBatch)
            return
        root = QgsProject.instance().layerTreeRoot()
        layers = root.findLayers()
        lakesLayer: Optional[QgsVectorLayer] = QSWATUtils.getLayerByFilename(layers, self._gv.lakeFile, FileTypes._LAKES, None, None, None)[0]
        if lakesLayer is None:
            QSWATUtils.error('Lakes layer not found.', self._gv.isBatch)
            return
        assert lakesLayer is not None
        if self._gv.useGridModel:
            channelsLayer: Optional[QgsVectorLayer] = None
        else:
            channelsLayer = QSWATUtils.getLayerByFilename(layers, self._gv.channelFile, FileTypes._CHANNELS, None, None, None)[0]
            if channelsLayer is None:
                QSWATUtils.error('Channels layer not found.', self._gv.isBatch)
                return
        demLayer: Optional[QgsRasterLayer] = QSWATUtils.getLayerByFilename(layers, self._gv.demFile, FileTypes._DEM, None, None, None)[0]
        if demLayer is None:
            QSWATUtils.error('DEM layer not found.', self._gv.isBatch)
            return
        if self._gv.isHUC:
            subbasinsLayer: Optional[QgsVectorLayer] = QSWATUtils.getLayerByFilename(layers, self._gv.subbasinsFile, FileTypes._SUBBASINS, None, None, None)[0]
            if subbasinsLayer is None:
                QSWATUtils.error('Subbasins layer not found', self._gv.isBatch)
                return
            assert subbasinsLayer is not None
            assert channelsLayer is not None
            if not self.addHUCLakes(lakesLayer, channelsLayer, subbasinsLayer, demLayer):
                QSWATUtils.error('Failed to add lakes', self._gv.isBatch)
                return
        else:
            reportErrors = not self._dlg.lakeMessagesBox.isChecked()
            if not self._gv.useGridModel and not self.lakePointsAdded and not self._gv.existingWshed:
                self.progress('Splitting lake channels ...')
                assert channelsLayer is not None  # since not grid model
                if not self.splitChannelsByLakes(lakesLayer, channelsLayer, demLayer, reportErrors):
                    QSWATUtils.error('Failed to split lake channels', self._gv.isBatch)
                    return
                # layers will have changed
                layers = root.findLayers()
                # and channelsLayer needs refreshing as has been rewritten
                channelsLayer = QSWATUtils.getLayerByFilename(layers, self._gv.channelFile, FileTypes._CHANNELS, None, None, None)[0]
                if channelsLayer is None:
                    QSWATUtils.error('Channels layer not found.', self._gv.isBatch)
                    return
            if self._gv.useGridModel or not self._gv.existingWshed:
                ft = FileTypes._GRID if self._gv.useGridModel else FileTypes._SUBBASINS
                subbasinsLayer = QSWATUtils.getLayerByFilename(layers, self._gv.subbasinsFile, ft, None, None, None)[0]
                if subbasinsLayer is None:
                    QSWATUtils.error('Subbasins layer not found: have you run TauDEM?', self._gv.isBatch)
                    return
                ft = FileTypes._GRIDSTREAMS if self._gv.useGridModel else FileTypes._STREAMS
                streamsLayer: Optional[QgsVectorLayer] = QSWATUtils.getLayerByFilename(layers, self._gv.streamFile, ft, None, None, None)[0]
                if streamsLayer is None: 
                    QSWATUtils.error('Streams layer for {0} not found.'.format(self._gv.streamFile), self._gv.isBatch)
                    return
            if self._gv.useGridModel or self._gv.existingWshed:
                chBasinsLayer: Optional[QgsVectorLayer] = None
            else:
                chBasinsLayer = QSWATUtils.getLayerByFilename(layers, self._gv.wshedFile, FileTypes._LSUS, None, None, None)[0]
                if chBasinsLayer is None:
                    chBasinsLayer = QgsVectorLayer(self._gv.wshedFile, 'chBasins', 'ogr')
            if self._gv.useGridModel and not self.gridLakesAdded:
                self.progress('Making grid lakes ...')
                assert subbasinsLayer is not None
                self.makeGridLakes(lakesLayer, subbasinsLayer)
                self.progress('')
                if lakesLayer is None:
                    QSWATUtils.error('Failed to make grid lakes', self._gv.isBatch)
                    return
        # avoid running again
        self.lakesDone = True
        self._dlg.lakesTab.setEnabled(False)
        self._dlg.mergeTab.setEnabled(False)
        self.progress('Adding lakes ...')
        self._dlg.setCursor(Qt.WaitCursor)
        self._gv.topo.lakesData.clear()
        if self._gv.useGridModel:
            self._gv.topo.addGridReservoirsPondsAndWetlands(subbasinsLayer, streamsLayer, demLayer, self._gv)
            self._gv.topo.addGridPlayas(lakesLayer, demLayer, self._gv)
        else:
            if self._gv.existingWshed:
                lakesLayer.setLabelsEnabled(True)
                lakesLayer.triggerRepaint()
                self._gv.topo.addExistingLakes(lakesLayer, channelsLayer, demLayer, self._gv)
            else:
                # make copy of subbasins shapefile before removing lakes
                QSWATUtils.copyShapefile(self._gv.subbasinsFile, 'subsNoLakes', self._gv.shapesDir)
                self._gv.subsNoLakesFile = QSWATUtils.join(self._gv.shapesDir, 'subsNoLakes.shp')
                snapThreshold = int(self._dlg.snapThreshold.text())
                self._gv.topo.addLakes(lakesLayer, subbasinsLayer, chBasinsLayer, streamsLayer, channelsLayer, 
                                       demLayer, snapThreshold, self._gv, reportErrors=reportErrors)
                self._gv.chBasinNoLakeFile = self.createBasinFile(self._gv.wshedFile, demLayer, 'wChannelNoLake', root)
        self._gv.topo.saveLakesData(self._gv.db)
        self.progress('')
        self._dlg.setCursor(Qt.ArrowCursor)
        self._gv.iface.mapCanvas().refresh()
        QSWATUtils.loginfo('{0} outlets after adding lakes'.format(len(self._gv.topo.outlets)))
        
    def splitChannelsByLakes(self, lakesLayer: QgsVectorLayer, channelsLayer: QgsVectorLayer, demLayer: QgsRasterLayer, reportErrors: bool) -> bool:
        """Split channels crossing reservoir or pond lake boundaries into two, entering/leaving and within.  
        Then rerun channel basins calculation to split into areas draining to channels and areas draining to lakes.
        
        Not used with grid models or existing watersheds."""
        
        def makeNewPoint(points: List[QgsPointXY], source: QgsPointXY, outlet: QgsPointXY, newPoints: List[QgsFeature], currentPointId: int,
                         res: int, chLink: int, lakeId: int, fields: QgsFields, transform: Dict[int, float]) -> int:
            """Select from points the nearest to source (if res is zero) or outlet and add a new point with the same geometry to newPoints.
            Return next point id used."""
            if QSWATTopology.withinPixels(1, source, outlet, transform):
                QSWATUtils.error("""Channel with LINKNO {0} crosses the boundary of lake {1} 
but is too short to allow the creation of a crossing point.  You can try rerunning delineation with a different channel threshold,
either smaller to lengthen the stream or larger to remove it.  Or if the lake is very small you may need to remove it or enlarge it."""
                                .format(chLink, lakeId), self._gv.isBatch)
                return currentPointId
            minMeasure = float('inf')
            crossingPoint = None
            # select endpoint as source or outlet
            endPoint = source if res == 0 else outlet
            for pt in points:
                measure = QSWATTopology.distanceMeasure(endPoint, pt)
                if measure < minMeasure:
                    crossingPoint = pt
                    minMeasure = measure
            if crossingPoint is None:
                QSWATUtils.error('Cannot find crossing point for channel with LINKNO {0} and lake {1}'
                                 .format(chLink, lakeId), self._gv.isBatch)
                return currentPointId
            point = QgsFeature(fields)
            currentPointId += 1
            point.setAttribute(idIndex, currentPointId)
            point.setAttribute(resIndex, res)
            point.setAttribute(inletIndex, 0)
            point.setAttribute(srcIndex, 0)
            point.setAttribute(addIndex, 1)
            # check point not too close to (in same dem pixel as) source or outlet
            # else this point will be ignored by TauDEM
            crossingPointMoved1 = QSWATTopology.separatePoints(source, crossingPoint, transform)
            crossingPointMoved2 = QSWATTopology.separatePoints(outlet, crossingPointMoved1, transform)
            point.setGeometry(QgsGeometry.fromPointXY(crossingPointMoved2))
            newPoints.append(point)
            # remove from points so if called twice same point cannot be selected
            points.remove(crossingPoint)
            if res == 0:
                self._gv.topo.lakeInlets[lakeId].add(currentPointId)
            else:
                self._gv.topo.lakeOutlets[lakeId].add(currentPointId)
                QSWATUtils.loginfo('Outlet to lake {0} on link {1} at ({2},{3})'
                                   .format(lakeId, chLink, int(crossingPointMoved2.x()), int(crossingPointMoved2.y())))
            return currentPointId
        
        lakeIdIndex, hasResOrPondOrWetland, hasPlaya = self.identifyLakes(lakesLayer)
        root = QgsProject.instance().layerTreeRoot()
        if hasPlaya:
            self._gv.playaFile = self.createPlayaFile(self._gv.lakeFile, demLayer, root)
        else:
            self._gv.playaFile = ''
        if not hasResOrPondOrWetland:  # nothing to do
            return True
        lakeResIndex = self._gv.topo.getIndex(lakesLayer, QSWATTopology._RES, ignoreMissing=True)
        if lakeIdIndex < 0:
            return False
        if not self._dlg.useOutlets.isChecked():
            # create an inlets/outlets file
            outletsFile = QSWATUtils.join(self._gv.shapesDir, 'madeoutlets.shp')
            if not Delineation.createOutletFile(outletsFile, self._gv.demFile, False, root, self._gv):
                return False
            outletsLayer = QgsVectorLayer(outletsFile, 'Outlets', 'ogr')
            outletsProvider = outletsLayer.dataProvider()
            fields = outletsProvider.fields()
            idIndex = fields.lookupField(QSWATTopology._ID)
            inletIndex = fields.lookupField(QSWATTopology._INLET)
            resIndex = fields.lookupField(QSWATTopology._RES)
            ptsourceIndex = fields.lookupField(QSWATTopology._PTSOURCE)
            ptIdIndex = fields.lookupField(QSWATTopology._POINTID)
            channelsProvider = channelsLayer.dataProvider()
            dsLinkIndex = self._gv.topo.getIndex(channelsLayer, QSWATTopology._DSLINKNO, ignoreMissing=False)
            # basin numbers should have been added to channels file by now
            basinIndex = self._gv.topo.getIndex(channelsLayer, QSWATTopology._BASINNO, ignoreMissing=False)
            dsNodeIdAdded = False
            dsNodeIndex = self._gv.topo.getIndex(channelsLayer, QSWATTopology._DSNODEID, ignoreMissing=True)
            if dsNodeIndex < 0:
                channelsProvider.addAttributes([QgsField(QSWATTopology._DSNODEID, QVariant.Int)])
                channelsLayer.updateFields()
                dsNodeIndex = channelsProvider.fieldNameIndex(QSWATTopology._DSNODEID)
                dsNodeIdAdded = True
            chMap: Dict[int, Dict[int, int]] = dict()
            outlets: List[QgsFeature] = []
            for channel in channelsLayer.getFeatures():
                subbasin = channel[basinIndex]
                if subbasin < 0 or channel[dsLinkIndex] >= 0:  # outside watershed or zero length channel or not an outlet
                    if dsNodeIdAdded:
                        # need to set new field
                        chMap[channel.id()] = {dsNodeIndex: -1}
                    continue
                # self._gv.topo.outlets should already be populated
                outletId, outletPt, _ = self._gv.topo.outlets[subbasin]
                chMap[channel.id()] = {dsNodeIndex: outletId}
                outletF = QgsFeature()
                outletF.setFields(fields)
                outletF.setAttribute(idIndex, outletId)
                outletF.setAttribute(inletIndex, 0)
                outletF.setAttribute(resIndex, 0)
                outletF.setAttribute(ptsourceIndex, 0)
                outletF.setAttribute(ptIdIndex, outletId)
                outletF.setGeometry(QgsGeometry.fromPointXY(outletPt))
                outlets.append(outletF)
            if not outletsProvider.addFeatures(outlets):
                QSWATUtils.error('Cannot add features to snapped outlets file {0}'.format(outletsFile), self._gv.isBatch)
                return False
            if not channelsProvider.changeAttributeValues(chMap):
                channelsFile = QSWATUtils.layerFilename(channelsLayer)
                QSWATUtils.error('Failed to set DSNODEIDs in channels file {0}'.format(channelsFile), self._gv.isBatch)
                return False 
            snapFile = QSWATUtils.join(self._gv.shapesDir, 'madeoutlets_snap.shp')
            # since we used channel end points for outlets snap file will be identical to outlets file
            QSWATUtils.removeLayer(snapFile, root)
            QSWATUtils.copyShapefile(outletsFile, 'madeoutlets_snap', self._gv.shapesDir)
            self._gv.outletFile = outletsFile
            self._gv.snapFile = snapFile
            # self._dlg.useOutlets.setChecked(True)
            # self._dlg.selectOutlets.setText(self._gv.outletFile)
#             QSWATUtils.error("""Since adding lakes involves adding new outlet points you must have an inlets/outlets file 
#             with at least a watershed outlet marked, or one of the new outlets will become a watershed outlet.""", self._gv.isBatch)
#             return False
        if self._gv.snapFile == '' or not os.path.exists(self._gv.snapFile):
            QSWATUtils.error('Cannot find snapped inlets/outlets file {0}'.format(self._gv.snapFile), self._gv.isBatch)
            return False
        snapLayer = QgsVectorLayer(self._gv.snapFile, 'Snapped points', 'ogr')
        snapProvider = snapLayer.dataProvider()
        fields = snapProvider.fields()
        idIndex = fields.indexFromName(QSWATTopology._ID)
        resIndex = fields.indexFromName(QSWATTopology._RES)
        inletIndex = fields.indexFromName(QSWATTopology._INLET)
        srcIndex = fields.indexFromName(QSWATTopology._PTSOURCE)
        ptIdIndex = fields.indexFromName(QSWATTopology._POINTID)
        # add ADDED field to define additional points
        addIndex = fields.indexFromName(QSWATTopology._ADDED)
        if addIndex < 0:
            snapProvider.addAttributes([QgsField(QSWATTopology._ADDED, QVariant.Int)])
            snapLayer.updateFields()
            fields = snapProvider.fields()
            addIndex = fields.indexFromName(QSWATTopology._ADDED)
        ds = gdal.Open(self._gv.demFile, gdal.GA_ReadOnly)
        transform = ds.GetGeoTransform()
        ds = None
        self._gv.topo.lakeInlets = dict()
        self._gv.topo.lakeOutlets = dict()
        currentPointId = 0
        # calculate current maximum id in snap file
        request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([ptIdIndex])
        for point in snapProvider.getFeatures(request):
            currentPointId = max(currentPointId, point[ptIdIndex])
        # First pass: replace any multipart lake geometries with a single part.  
        # Also eliminate any islands to prevent accidental crossings of channels with islands
        # This assumes that dissolving has been done to get as much as possible of lake into
        # one part, so remaining pieces are insignificant, and islands are also insignificant
        lakeProvider = lakesLayer.dataProvider()
        channelProvider = channelsLayer.dataProvider()
        channelLinkIndex = channelProvider.fieldNameIndex(QSWATTopology._LINKNO)
        areaFactor = self._gv.horizontalFactor * self._gv.horizontalFactor
        geoMap: Dict[int, QgsGeometry] = dict()
        lakesToRemove: List[int] = []
        for lake in lakeProvider.getFeatures():
            if lakeResIndex >= 0 and lake[lakeResIndex] == QSWATTopology._PLAYATYPE:
                continue
            lakeId = lake[lakeIdIndex]
            geom = lake.geometry()
            if geom.type() != QgsWkbTypes.PolygonGeometry:
                QSWATUtils.error('Lake {0} does not seem to be a polygon shape'.format(lakeId), self._gv.isBatch)
                return False
            if geom.isMultipart():
                # find the part with largest area to use as the lake
                maxArea = 0.0 
                secondArea = 0.0
                maxPart = None
                secondPart = None
                polys = geom.asMultiPolygon()
                QSWATUtils.loginfo('Lake {0} has {1} parts'.format(lakeId, len(polys)))
                partNum = 0
                for poly in polys:
                    nextPart = QgsGeometry.fromPolygonXY([poly[0]]) # removes any islands within the polygon, by using outer (first) ring only
                    nextArea = nextPart.area() * areaFactor
                    nextLen = len(poly[0])
                    partNum += 1
                    QSWATUtils.loginfo('Part {0} has {1} perimeter vertices and area {2}'.format(partNum, nextLen, int(nextArea)))
                    if nextArea > maxArea:
                        if maxArea > secondArea:
                            secondPart = maxPart
                            secondArea = maxArea
                        maxPart = nextPart
                        maxArea = nextArea
                if maxPart is None:
                    QSWATUtils.error('Lake {0} seems to be empty'.format(lakeId), self._gv.isBatch)
                    return False
                if secondPart is not None:
                    percent = int(secondArea * 100.0 / maxArea + 0.5)
                    QSWATUtils.loginfo('Second part area is {0}% of first'.format(percent))
                    if percent >= 5:
                        QSWATUtils.information('Warning: part with {0} percent of main part of lake {1} is being ignored.'.format(percent, lakeId), self._gv.isBatch, reportErrors=reportErrors)
                geoMap[lake.id()] = maxPart
            else:
                geoMap[lake.id()] = QgsGeometry.fromPolygonXY([geom.asPolygon()[0]]) # keep only outer (first) ring to remove islands
            # this does not seem to work in QGIS 3.  feature.geometry() reurns the original geometry
            # probably becase it would change the type of the features from polygon to line
#         if not lakeProvider.changeGeometryValues(geoMap):
#             QSWATUtils.error('Failed to update lake geometries in {0}'.format(self._gv.lakeFile), self.isBatch)
#             for err in lakeProvider.errors():
#                 QSWATUtils.loginfo(err)
#             return False
        newPoints: List[QgsFeature] = []
        for lake in lakeProvider.getFeatures():
            if lakeResIndex >= 0 and lake[lakeResIndex] == QSWATTopology._PLAYATYPE:
                continue
            lakeId = lake[lakeIdIndex]
            if lakeResIndex < 0:
                res = QSWATTopology._RESTYPE  # default to reservoir
            else:
                res = lake[lakeResIndex]
            geom = geoMap[lake.id()]
            self._gv.topo.lakeInlets[lakeId] = set()
            self._gv.topo.lakeOutlets[lakeId] = set()
            box = geom.boundingBox()
            # geometry was made single in first pass
            perim = QgsGeometry.fromPolylineXY(geom.asPolygon()[0])
            # channels which enter and leave the lake, with their crossing points
            # if just one of these and no other outlet will make inflowing and outflowing pair,
            # else assumed not to interact with lake
            crossingChannels: List[Tuple[QgsFeature, List[QgsPointXY]]] = []
            for channel in channelProvider.getFeatures():
                chLink = channel[channelLinkIndex]
                line = channel.geometry()
                lineBox = line.boundingBox()
                if QSWATTopology.disjointBoxes(box, lineBox):
                    continue
                intersect = line.intersection(perim)
                if intersect.isEmpty():
                    # no intersection
                    continue
                intersectType = intersect.wkbType()
                if intersectType == QgsWkbTypes.MultiPoint:
                    points = intersect.asMultiPoint()  # TODO: just to see how many points
                    # check if source and outlet are inside or outside lake
                    reachData = self._gv.topo.getReachData(channel, None)
                    outlet = QgsPointXY(reachData.lowerX, reachData.lowerY)
                    source = QgsPointXY(reachData.upperX, reachData.upperY)
                    if QSWATTopology.polyContains(outlet, geom, box):
                        if QSWATTopology.polyContains(source, geom, box):
                            QSWATUtils.information(
"""Channel with LINKNO {0}  crosses the  boundary of lake {1}
more than once.  Since it starts and terminates in the lake it
will be assumed that its crossing the lake boundary is an 
inaccuaracy of delineation and that it is internal to the lake.
""".format(chLink, lakeId), self._gv.isBatch, reportErrors=reportErrors)
                        else:
                            QSWATUtils.information(
"""Channel with LINKNO {0} crosses the  boundary of lake {1}
more than once.  Since it starts outside and terminates inside 
the lake it will be assumed that its extra crossings of the lake 
boundary are an inaccuaracy of delineation and that it enters 
the lake at its first crossing point.
""".format(chLink, lakeId), self._gv.isBatch, reportErrors=reportErrors)
                            currentPointId = makeNewPoint(points, source, outlet, newPoints, currentPointId, 0, chLink, lakeId, fields, transform)
                    else:
                        if QSWATTopology.polyContains(source, geom, box):
                            QSWATUtils.information(
"""Channel with LINKNO {0} crosses the  boundary of lake {1}
more than once.  Since it starts in the lake and terminates 
outside it will be assumed that its multiple crossings 
of the lake boundary are an inaccuaracy of delineation and 
that it flows out the lake at its last crossing point.
""".format(chLink, lakeId), self._gv.isBatch, reportErrors=reportErrors)
                            currentPointId = makeNewPoint(points, source, outlet, newPoints, currentPointId, res, chLink, lakeId, fields, transform)
                        else:
                            crossingChannels.append((channel, points))
                elif intersectType == QgsWkbTypes.Point:
                    # enters or leaves lake: add split point
                    reachData = self._gv.topo.getReachData(channel, None)
                    outlet = QgsPointXY(reachData.lowerX, reachData.lowerY)
                    source = QgsPointXY(reachData.upperX, reachData.upperY)
                    # select between source and outlet according to whether channel outlet is in lake
                    if QSWATTopology.polyContains(outlet, geom, box):
                        res1 = 0
                    else:
                        res1 = res
                    currentPointId = makeNewPoint([intersect.asPoint()], source, outlet, newPoints, currentPointId, res1, chLink, lakeId, fields, transform)
            # check for channels which cross lake if no other outlets
            numOutlets = len(self._gv.topo.lakeOutlets[lakeId])
            if numOutlets == 0 and len(crossingChannels) > 0:
                # arbtirarily select first such stream to generate the outlet
                # users told to mark stream with a reservoir or pond point if this gives undesirable choice
                channel, points = crossingChannels.pop(0)
                reachData = self._gv.topo.getReachData(channel, None)
                outlet = QgsPointXY(reachData.lowerX, reachData.lowerY)
                source = QgsPointXY(reachData.upperX, reachData.upperY)
                chLink = channel[channelLinkIndex]
                currentPointId = makeNewPoint(points, source, outlet, newPoints, currentPointId, res, chLink, lakeId, fields, transform)
                currentPointId = makeNewPoint(points, source, outlet, newPoints, currentPointId, 0, chLink, lakeId, fields, transform)
                numOutlets += 1
            for channel, points in crossingChannels:
                chLink0 = channel[channelLinkIndex]
                QSWATUtils.information(
"""Channel with LINKNO {0} enters and then leaves lake {1}.  
Since it starts and terminates outside the lake it will be 
assumed that its crossing the lake boundary is an inaccuracy. 
""".format(chLink0, lakeId), self._gv.isBatch, reportErrors=reportErrors)
            if numOutlets == 0:
                # last chance to include lake - check if it has a watershed outlet inside it
                for subbasin, (pointId, pt, _) in self._gv.topo.outlets.items():
                    if self._gv.topo.isWatershedOutlet(pointId, channelProvider) and \
                        QSWATTopology.polyContains(pt, geom, box): 
                        # outletsInLake needed for making deep aquifers later
                        self._gv.topo.outletsInLake[subbasin] = lakeId 
                        numOutlets += 1
            QSWATUtils.loginfo('Lake {0} has {1} outlets'.format(lakeId, numOutlets))
            if numOutlets == 0: 
                self._gv.iface.setActiveLayer(lakesLayer)
                lakesLayer.select(lake.id())
                self._gv.iface.actionZoomToSelected().trigger()
                msgBox = QMessageBox()
                msgBox.move(self._gv.selectOutletPos)
                msgBox.setWindowTitle('Remove lake?')
                text = """
    Failed to find any outlet points for lake {0}.
    It appears not to be on any channels.  Do you want to remove it?
    If you choose no you can try rerunning delineation with a smaller 
    channel threshold to get a channel to reach the lake, or you could
    try editing the lake boundary if it is already close to a channel, 
    or you could change it to a playa lake by setting its RES field to 4.
    """.format(lakeId)
                msgBox.setText(QSWATUtils.trans(text))
                msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)  # type: ignore
                msgBox.setWindowModality(Qt.NonModal)
                self._dlg.showMinimized()
                msgBox.show()
                result = msgBox.exec_()
                self._dlg.showNormal()
                if result == QMessageBox.Yes:
                    lakesToRemove.append(lake.id())
                lakesLayer.deselect(lake.id())
                continue
        if not snapProvider.addFeatures(newPoints):
            QSWATUtils.error('Failed to add lake inlets and outlets to {0}'.format(self._gv.snapFile), self._gv.isBatch)
            return False
        if len(lakesToRemove) > 0:
            lakeProvider.deleteFeatures(lakesToRemove)
            lakesLayer.triggerRepaint()
        root = QgsProject.instance().layerTreeRoot()
        numProcesses = self._dlg.numProcesses.value()
        mustRun = True
        (base, suffix) = os.path.splitext(self._gv.demFile)
        # AreaD8 has an outlets shapefile input, but no need to rerun as adding lake inlets and outlets will not change the watershed area
        self.progress('GridNet ...')
        gordFile = base + 'gord' + suffix
        plenFile = base + 'plen' + suffix
        tlenFile = base + 'tlen' + suffix
        ok = TauDEMUtils.runGridNet(self._gv.pFile, plenFile, tlenFile, gordFile, self._gv.snapFile, numProcesses, self._dlg.taudemOutput, mustRun=mustRun)  
        if not ok:
            self.cleanUp(3)
            return False
        srcChannelFile = base + 'srcChannel' + suffix
        QSWATUtils.removeLayer(srcChannelFile, root)
        channelThreshold = self._dlg.numCellsCh.text()
        ok = TauDEMUtils.runThreshold(self._gv.ad8File, srcChannelFile, channelThreshold, numProcesses, self._dlg.taudemOutput, mustRun=mustRun) 
        if not ok:
            self.cleanUp(3)
            return False
        self._gv.srcChannelFile = srcChannelFile
        QSWATUtils.removeLayer(self._gv.channelFile, root)
        QSWATUtils.removeLayer(self._gv.channelBasinFile, root)
        # having this as a layer results in DSNODEIDs being set to zero
        QSWATUtils.removeLayer(self._gv.snapFile, root)
        ordChannelFile = base + 'ordChannel' + suffix
        treeChannelFile = base + 'treeChannel.dat'
        coordChannelFile = base + 'coordChannel.dat'
        # if channel shapefile already exists and is a directory, set path to .shp
        self._gv.channelFile = QSWATUtils.dirToShapefile(self._gv.channelFile)
        ok = TauDEMUtils.runStreamNet(self._gv.felFile, self._gv.pFile, self._gv.ad8File, self._gv.srcChannelFile, self._gv.snapFile, ordChannelFile, treeChannelFile, coordChannelFile,
                                      self._gv.channelFile, self._gv.channelBasinFile, False, numProcesses, self._dlg.taudemOutput, mustRun=mustRun)
        if not ok:
            self.cleanUp(3)
            return False
        # if channel shapefile is a directory, set path to .shp, since not done earlier if channel did not exist then
        self._gv.channelFile = QSWATUtils.dirToShapefile(self._gv.channelFile)
        QSWATUtils.removeLayer(self._gv.wshedFile, root)
        self.createWatershedShapefile(self._gv.channelBasinFile, self._gv.wshedFile, FileTypes._WATERSHED, root)
        # make demLayer (or hillshadelayer if exists) active so channelsLayer loads above it and below outlets
        # (or use Full HRUs layer if there is one)
        fullHRUsLayer = QSWATUtils.getLayerByLegend(QSWATUtils._FULLHRUSLEGEND, root.findLayers())
        if fullHRUsLayer is not None:
            subLayer = fullHRUsLayer
        else:
            hillshadeLayer = QSWATUtils.getLayerByLegend(QSWATUtils._HILLSHADELEGEND, root.findLayers())
            if hillshadeLayer is not None:
                subLayer = hillshadeLayer
            else:
                subLayer = demLayer
        channelsLayer, loaded = QSWATUtils.getLayerByFilename(root.findLayers(), self._gv.channelFile, FileTypes._CHANNELS, 
                                                              self._gv, subLayer, QSWATUtils._WATERSHED_GROUP_NAME)
        if channelsLayer is None or not (loaded or self._gv.existingWshed):
            self.cleanUp(-1)
            return False
        if self._gv.basinFile == '':  # some subbasins were merged
            self._gv.basinFile = self.createBasinFile(self._gv.subbasinsFile, demLayer, 'wStream', root)
        self._gv.topo.addBasinsToChannelFile(channelsLayer, self._gv.basinFile)
        # recalculate tables dependent on channels
        if not self._gv.topo.saveOutletsAndSources(channelsLayer, snapLayer, False):
            return False
        self.lakePointsAdded = True
        return True
    
    def addHUCLakes(self, lakesLayer: QgsVectorLayer, channelsLayer: QgsVectorLayer, subbasinsLayer: QgsVectorLayer, demLayer: QgsRasterLayer) -> bool:
        """Add lakes in HUC models."""
        # Cannot run TauDEM as supplied channels will in general not coincide with calculated ones.
        # So we calculate new subbasins by subtracting lake from existing ones
        root = QgsProject.instance().layerTreeRoot()
        subsNoLakes = os.path.split(self._gv.subbasinsFile)[0] + '/subsNoLakes.shp'
        QSWATUtils.tryRemoveLayerAndFiles(subsNoLakes, root)
        params = {'INPUT': self._gv.subbasinsFile, 'OVERLAY': self._gv.lakeFile, 'OUTPUT': subsNoLakes}
        processing.run('native:difference', params)
        if not os.path.isfile(subsNoLakes):
            QSWATUtils.error('Failed to create {0} file'.format(subsNoLakes), self._gv.isBatch)
            return False
        QSWATUtils.removeLayer(self._gv.chBasinNoLakeFile, root)
        wChannelNoLakeFile = self.createBasinFile(subsNoLakes, demLayer, 'wChannelNoLake', root)
        if not os.path.isfile(wChannelNoLakeFile):
            QSWATUtils.error('Failed to create no lakes raster {0}'.format(wChannelNoLakeFile), self._gv.isBatch)
            return False
        self._gv.chBasinNoLakeFile = wChannelNoLakeFile
        # now populate LakeIn etc fields
        self._gv.topo.addLakeFieldsToChannels(channelsLayer)
        channelsProvider = channelsLayer.dataProvider()
        channelLinkIndex = channelsProvider.fieldNameIndex(QSWATTopology._LINKNO)
        channelDsLinkIndex = channelsProvider.fieldNameIndex(QSWATTopology._DSLINKNO1)
        channelDsNodeindex = channelsProvider.fieldNameIndex(QSWATTopology._DSNODEID1)
        channelLakeInIndex = channelsProvider.fieldNameIndex(QSWATTopology._LAKEIN)
        channelLakeOutIndex = channelsProvider.fieldNameIndex(QSWATTopology._LAKEOUT)
        channelLakeWithinIndex = channelsProvider.fieldNameIndex(QSWATTopology._LAKEWITHIN)
        channelLakeMainIndex = channelsProvider.fieldNameIndex(QSWATTopology._LAKEMAIN)
        areaFactor = self._gv.horizontalFactor * self._gv.horizontalFactor
        lakesProvider = lakesLayer.dataProvider()
        lakeIdIndex = lakesProvider.fieldNameIndex(QSWATTopology._LAKEID)
        mmap = dict()
        for lake in lakesProvider.getFeatures():
            lakeId = lake[lakeIdIndex]
            QSWATUtils.loginfo('Adding lake {0} to HUC model'.format(lakeId))
            geom = lake.geometry()
            if geom.type() != QgsWkbTypes.PolygonGeometry:
                QSWATUtils.error('Lake {0} does not seem to be a polygon shape'.format(lakeId), self._gv.isbatch)
                return False
            if geom.isMultipart():
                # find the part with largest area to use as the lake
                maxArea = 0.0 
                secondArea = 0.0
                maxPart = None
                secondPart = None
                polys = geom.asMultiPolygon()
                QSWATUtils.loginfo('Lake {0} has {1} parts'.format(lakeId, len(polys)))
                partNum = 0
                for poly in polys:
                    nextPart = QgsGeometry.fromPolygonXY([poly[0]]) # removes any islands within the polygon, by using outer (first) ring only
                    nextArea = nextPart.area() * areaFactor
                    nextLen = len(poly[0])
                    partNum += 1
                    QSWATUtils.loginfo('Part {0} has {1} perimeter vertices and area {2}'.format(partNum, nextLen, int(nextArea)))
                    if nextArea > maxArea:
                        if maxArea > secondArea:
                            secondPart = maxPart
                            secondArea = maxArea
                        maxPart = nextPart
                        maxArea = nextArea
                if maxPart is None:
                    QSWATUtils.error('Lake {0} seems to be empty'.format(lakeId), self._gv.isBatch)
                    return False
                if secondPart is not None:
                    percent = int(secondArea * 100.0 / maxArea + 0.5)
                    QSWATUtils.loginfo('Second part area is {0}% of first'.format(percent))
                    if percent >= 5:
                        QSWATUtils.information('Warning: part with {0} percent of main part of lake {1} is being ignored.'.format(percent, lakeId), self._gv.isBatch)
                perim = maxPart
            else:
                perim = QgsGeometry.fromPolygonXY([geom.asPolygon()[0]]) # keep only outer (first) ring to remove islands
            perimBox = perim.boundingBox()
            mainOutletChosen = False
            # channels that intersect with the lake: candidates for outlet
            candidates = []
            selected = []
            for channel in channelsProvider.getFeatures():
                chLink = channel[channelLinkIndex]
                line = channel.geometry()
                lineBox = line.boundingBox()
                if QSWATTopology.disjointBoxes(perimBox, lineBox):
                    continue
                intersect = line.intersection(perim)
                if intersect.isEmpty():
                    # no intersection
                    continue
                candidates.append(channel)
                channelIsWatershedOutlet = channel[channelDsLinkIndex] == -1 and channel[channelDsNodeindex] > 0
                reachData = self._gv.topo.getReachData(channel, None)
                outlet = QgsPointXY(reachData.lowerX, reachData.lowerY)
                source = QgsPointXY(reachData.upperX, reachData.upperY)
                outletInLake = QSWATTopology.polyContains(outlet, perim, perimBox)
                sourceInlake = QSWATTopology.polyContains(source, perim, perimBox)
                if outletInLake:
                    if sourceInlake:
                        if channelIsWatershedOutlet:  # watershed outlet is within lake
                            if mainOutletChosen:
                                mmap[channel.id()] = {channelLakeOutIndex: lakeId}
                                QSWATUtils.loginfo('Channel with link number {0} flows out of lake {1}'.format(chLink, lakeId))
                            else:
                                mmap[channel.id()] = {channelLakeOutIndex: lakeId, channelLakeMainIndex: lakeId}
                                QSWATUtils.loginfo('Channel with link number {0} main outlet of lake {1}'.format(chLink, lakeId))
                                mainOutletChosen = True
                        else:            
                            mmap[channel.id()] = {channelLakeWithinIndex: lakeId}
                            QSWATUtils.loginfo('Channel with link number {0} is within lake {1}'.format(chLink, lakeId))
                            selected.append(chLink)
                    else:
                        mmap[channel.id()] = {channelLakeInIndex: lakeId}
                        QSWATUtils.loginfo('Channel with link number {0} flows into lake {1}'.format(chLink, lakeId))
                        selected.append(chLink)
                elif sourceInlake:
                    if mainOutletChosen:
                        mmap[channel.id()] = {channelLakeOutIndex: lakeId}
                        QSWATUtils.loginfo('Channel with link number {0} flows out of lake {1}'.format(chLink, lakeId))
                    else:
                        # arbitrary choice of first (and probably only) outlet as main
                        mmap[channel.id()] = {channelLakeOutIndex: lakeId, channelLakeMainIndex: lakeId}
                        QSWATUtils.loginfo('Channel with link number {0} main outlet of lake {1}'.format(chLink, lakeId))
                        mainOutletChosen = True
                #===============================================================
                # # alternative method: fails probably because we can have joins outside lakes, so everything looks like an outlet
                # outletOutside = False
                # sourceOutside = False 
                # if line.isMultipart():
                #     #get returns underlying abstract geometry
                #     #constGet is faster version returning non-modifiable abstrac geometry
                #     segments = line.constGet()  # QgsMultiLineString
                # else:
                #     segments = [line.constGet()]
                # for segment in segments:
                #     # HUC flowlines have source st start
                #     source = QgsPointXY(segment[0])
                #     outlet = QgsPointXY(segment[-1])
                #     outletOutside = outletOutside or not QSWATTopology.polyContains(outlet, perim, perimBox)
                #     sourceOutside = sourceOutside or not QSWATTopology.polyContains(source, perim, perimBox)
                # if outletOutside:
                #     QSWATUtils.loginfo('{0} is an outlet'.format(chLink))
                # elif sourceOutside:
                #     QSWATUtils.loginfo('{0} is an inlet'.format(chLink))
                # else:
                #     QSWATUtils.loginfo('{0} is inside'.format(chLink))
                #===============================================================
            if not mainOutletChosen:
                if len(candidates) > 0:
                    # select a channel that is downstream from a candidate but not in candidates
                    candidateLinks = [channel[channelLinkIndex] for channel in candidates]
                    candidateDsLinks = [channel[channelDsLinkIndex] for channel in candidates]
                    # first pass: find a channel in candidates but not selected that is not upstream of amother candidate
                    for channel in channelsProvider.getFeatures():
                        chLink = channel[channelLinkIndex]
                        dsLink = channel[channelDsLinkIndex]
                        if chLink in candidateLinks and chLink not in selected and dsLink not in candidateLinks:
                            mmap[channel.id()] = {channelLakeOutIndex: lakeId, channelLakeMainIndex: lakeId}
                            QSWATUtils.loginfo('Channel with link number {0} main outlet of lake {1}'.format(chLink, lakeId))
                            mainOutletChosen = True
                            break
                    if not mainOutletChosen:
                        # second pass: find a non-candidate channel downstream from a candidate and not upstream of amother candidate
                        chLink = channel[channelLinkIndex]
                        dsLink = channel[channelDsLinkIndex]
                        for channel in channelsProvider.getFeatures():
                            if chLink not in candidateLinks and chLink in candidateDsLinks and dsLink not in candidateLinks:
                                mmap[channel.id()] = {channelLakeOutIndex: lakeId, channelLakeMainIndex: lakeId}
                                QSWATUtils.loginfo('Channel with link number {0} main outlet of lake {1}'.format(chLink, lakeId))
                                mainOutletChosen = True
                                break
            if not mainOutletChosen:
                QSWATUtils.error('Failed to find outlet for lake {0}'.format(lakeId), self._gv.isBatch, logFile=self._gv.logFile)
                return False
        if not channelsProvider.changeAttributeValues(mmap):
            QSWATUtils.error('Cannot update channels layer with lake data', self._gv.isBatch)
            return False  
        return True
    
    def identifyLakes(self, lakesLayer: QgsVectorLayer) -> Tuple[int, bool, bool]:
        """If necessary add an id attribute to the lakes shapefile.  Number lakes with water body ids.
        label lakes with the id value.  Add lake ids to lake ids combo.  Return the index to the id attribute.
        Also return true second result if lakes include reservoirs or ponds or wetlands, 
        and true third result if they include playas."""
        lakeProvider = lakesLayer.dataProvider()
        # label lakes with water body numbers
        lakeIdIndex = lakeProvider.fieldNameIndex(QSWATTopology._LAKEID)
        lakeResIndex = lakeProvider.fieldNameIndex(QSWATTopology._RES)
        request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry)
        lakeIds: List[int] = []
        hasResOrPondOrWetland = lakeResIndex < 0   # sence default is reservoir
        hasPlaya = False
        if lakeIdIndex < 0:
            if not lakeProvider.addAttributes([QgsField(QSWATTopology._LAKEID, QVariant.Int)]):
                QSWATUtils.error('Unable to edit lakes shapefile {0}'.format(self._gv.lakeFile), self._gv.isBatch)
                return -1, False, False
            lakeIdIndex = lakeProvider.fieldNameIndex(QSWATTopology._LAKEID)
            attMap: Dict[int, Dict[int, Any]] = dict()
            self._gv.topo.waterBodyId = self.getMaxWaterId()
            for lake in lakeProvider.getFeatures(request):
                if not hasResOrPondOrWetland:
                    if lake[lakeResIndex] in {QSWATTopology._RESTYPE, QSWATTopology._PONDTYPE, QSWATTopology._WETLANDTYPE}:
                        hasResOrPondOrWetland = True
                if not hasPlaya:
                    if lakeResIndex >= 0 and lake[lakeResIndex] == QSWATTopology._PLAYATYPE:
                        hasPlaya = True  
                self._gv.topo.waterBodyId += 1
                attMap[lake.id()] = {lakeIdIndex: self._gv.topo.waterBodyId}
                lakeIds.append(self._gv.topo.waterBodyId)
            if not lakeProvider.changeAttributeValues(attMap):
                QSWATUtils.error('Unable to update lakes shapefile {0}'.format(self._gv.lakeFile), self._gv.isBatch)
                return -1, False, False
            lakesLayer.updateFields()
        else:
            for lake in lakeProvider.getFeatures(request):
                lakeId = lake[lakeIdIndex]
                if not hasResOrPondOrWetland:
                    if lake[lakeResIndex] in {QSWATTopology._RESTYPE, QSWATTopology._PONDTYPE, QSWATTopology._WETLANDTYPE}:
                        hasResOrPondOrWetland = True
                if not hasPlaya:
                    if lakeResIndex >= 0 and lake[lakeResIndex] == QSWATTopology._PLAYATYPE:
                        hasPlaya = True  
                try:
                    intLakeId = int(lakeId)
                except Exception:
                    QSWATUtils.error('LakeId {0} cannot be parsed as an integer'.format(lakeId), self._gv.isBatch)
                    return -1, False, False
                if lakeId in lakeIds:
                    QSWATUtils.error('LakeId {0} appears at least twice in {1}: LakeId values must be unique'.
                                     format(lakeId, QSWATUtils.layerFilename(lakesLayer)), self._gv.isBatch)
                    return -1, False, False  
                ListFuns.insertIntoSortedList(intLakeId, lakeIds, True)
                self._gv.topo.waterBodyId = max(self._gv.topo.waterBodyId, intLakeId)
        if self._gv.useGridModel:
            if self._dlg.lakeIdCombo.count() == 0:
                self._dlg.lakeIdCombo.addItems([str(i) for i in lakeIds])
        else:
            lakesLayer.setLabelsEnabled(True)
            lakesLayer.triggerRepaint()
        return lakeIdIndex, hasResOrPondOrWetland, hasPlaya
    
    def getMaxWaterId(self) -> int:
        """Return maximum of 0 and reservoir or pond id values in inlets/outlets file if any."""
        result = 0
        if self._dlg.useOutlets.isChecked() and os.path.isfile(self._gv.outletFile):
            layer = QgsVectorLayer(self._gv.outletFile, 'Outlets', 'ogr')
            idIndex = self._gv.topo.getIndex(layer, QSWATTopology._ID)
            resIndex = self._gv.topo.getIndex(layer, QSWATTopology._RES)
            if resIndex >=0:
                request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry)
                for point in layer.getFeatures(request):
                    if point[resIndex] > 0:
                        result = max(result, point[idIndex])
        return result
                
            
    
    def populateLakeIdCombo(self, lakesLayer: QgsVectorLayer) -> None:
        """Put LakeId values into lakeIdCombo."""
        lakeIdIndex = self._gv.topo.getIndex(lakesLayer, QSWATTopology._LAKEID)
        request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([lakeIdIndex])
        lakeIds = []
        for lake in lakesLayer.getFeatures(request):
            lakeIds.append(lake[lakeIdIndex])
        self._dlg.lakeIdCombo.clear()
        self._dlg.lakeIdCombo.addItems([str(i) for i in sorted(lakeIds)])
        
    
    def makeGridLakes(self, lakesLayer: QgsVectorLayer, gridLayer: QgsVectorLayer) -> None:
        """Convert reservoir, pond and wetland lakes into collections of grid cells and mark the cells with the lake id and RES value."""
        if self.gridLakesAdded:
            return
        lakeIdIndex, _, _ = self.identifyLakes(lakesLayer)
        if lakeIdIndex < 0:
            return
        lakeResIndex = self._gv.topo.getIndex(lakesLayer, QSWATTopology._RES, ignoreMissing=True)
        if lakeResIndex < 0:
            QSWATUtils.information('No RES field in lakes shapefile {0}: assuming lakes are reservoirs'.
                                   format(QSWATUtils.layerFilename(lakesLayer)), self._gv.isBatch)
        gridProvider = gridLayer.dataProvider()
        areaIndex = self._gv.topo.getIndex(gridLayer, Parameters._AREA)
        gridLakeIdIndex = self._gv.topo.getIndex(gridLayer, QSWATTopology._LAKEID)
        gridResIndex = self._gv.topo.getIndex(gridLayer, QSWATTopology._RES, ignoreMissing=True)
        if gridResIndex < 0:
            if not gridProvider.addAttributes([QgsField(QSWATTopology._RES, QVariant.Int)]):
                QSWATUtils.error('Unable to edit grid shapefile {0}'.format(QSWATUtils.layerFilename(gridLayer)), self._gv.isBatch)
                return
            gridLayer.updateFields()
            gridResIndex = self._gv.topo.getIndex(gridLayer, QSWATTopology._RES)
        areaFactor = self._gv.horizontalFactor * self._gv.horizontalFactor
        # list of ids of lakes already added to grid
        done: List[int] = []
        mmap: Dict[int, Dict[int, Any]] = dict()
        for lake in lakesLayer.getFeatures():
            lakeId: int = lake[lakeIdIndex]
            if lakeResIndex < 0:
                waterRole = QSWATTopology._RESTYPE
            else:
                waterRole = lake[lakeResIndex]
                if waterRole == QSWATTopology._PLAYATYPE:
                    continue
            lakeGeom = lake.geometry()
            lakeBox = lakeGeom.boundingBox()
            for cell in gridLayer.getFeatures():
                cellGeom = cell.geometry()
                cellBox = cellGeom.boundingBox()
                cellAreaThreshold = 0.5 * float(cell[areaIndex]) * 1E4  # convert to square metres
                # ensure we remove old lake ids, but not lake ids already added
                try:
                    currentLakeId = int(cell[gridLakeIdIndex])
                    if currentLakeId not in done:
                        mmap[cell.id()] = {gridLakeIdIndex: NULL}
                except:
                    pass
                if QSWATTopology.disjointBoxes(lakeBox, cellBox):
                    continue
                lakePart = cellGeom.intersection(lakeGeom)
                if lakePart.isEmpty():
                    continue
                if lakePart.area() * areaFactor < cellAreaThreshold:
                    continue
                mmap[cell.id()] = {gridLakeIdIndex: lakeId, gridResIndex: waterRole}
            done.append(lakeId)
        if not gridProvider.changeAttributeValues(mmap):
            QSWATUtils.error('Cannot edit attributes of grid {0}'.format(QSWATUtils.layerFilename(gridLayer)), self._gv.isBatch)
            return
        self.gridLakesAdded = True
        return
            
    def makeDistancesToOutlets(self) -> None:
        """Create two raster files of distances to subbasin outlets and distances to channels, 
        unless they already exist or using existing watershed."""
        if not self._gv.existingWshed:
            haveDistSt = QSWATUtils.isUpToDate(self._gv.pFile, self._gv.distStFile)
            haveDistCh = self._gv.useGridModel or QSWATUtils.isUpToDate(self._gv.pFile, self._gv.distChFile)
            #  haveValleyDepths = QSWATUtils.isUpToDate(self._gv.pFile, self._gv.valleyDepthsFile)
            if haveDistSt and haveDistCh:  # and haveValleyDepths:
                return
            demBase = os.path.splitext(self._gv.demFile)[0]
            # noinspection PyArgumentList
            root = QgsProject.instance().layerTreeRoot()
            if not haveDistSt:
                self.progress('Tributary stream lengths ...')
                threshold = self._gv.topo.makeOutletThresholds(self._gv, root)
                if threshold > 0:
                    self._gv.distStFile = demBase + 'distst.tif'
                    # threshold is already double maximum ad8 value, so values anywhere near it can only occur at subbasin outlets; 
                    # use fraction of it to avoid any rounding problems
                    ok = TauDEMUtils.runDistanceToStreams(self._gv.pFile, self._gv.hd8File, 
                                                          self._gv.distStFile, str(int(threshold * 0.9)), 
                                                          self._dlg.numProcesses.value(), 
                                                          self._dlg.taudemOutput, 
                                                          mustRun=self.thresholdChanged)
                    if not ok:
                        self.cleanUp(3)
                        return
                else:
                    # Probably using existing watershed but switched tabs in delineation form
                    self._gv.distStFile = ''
            if not self._gv.useGridModel and not haveDistCh:
                self.progress('Channel flow lengths ...')
                if not QSWATUtils.isUpToDate(self._gv.demFile, self._gv.ad8File):
                    # Probably using existing watershed but switched tabs in delineation form
                    # At any rate, cannot calculate flow paths
                    QSWATUtils.error('Flow accumulation file {0} missing or out of date'.format(self._gv.ad8File), self._gv.isBatch)
                    return
                self._gv.distChFile = demBase + 'distch.tif'
                channelThreshold = self._dlg.numCellsCh.text()
                ok = TauDEMUtils.runDistanceToStreams(self._gv.pFile, self._gv.ad8File,
                                                      self._gv.distChFile, channelThreshold, 
                                                      self._dlg.numProcesses.value(), 
                                                      self._dlg.taudemOutput, 
                                                      mustRun=self.thresholdChanged)
                if not ok:
                    self.cleanUp(3)
                    return
                # estimate valley depths for tributary slopes in hrus if not calculated for floodplain
                # so don't calculate here
#             if not haveValleyDepths:
#                 self.progress('Valley depths ...')
#                 if self.L is None:
#                     self.L = Landscape(self._gv, self._dlg.taudemOutput, self._dlg.numProcesses.value(), self.progress)
#                 # mustRun probably left true by previous run: avoid unnecessary recalculation
#                 self.L.mustRun = False
#                 # this also generates valley depths
#                 threshold = int(self._dlg.numCellsSt.text()) if self._gv.useGridModel else int(self._dlg.numCellsCh.text())
#                 clipper = self._gv.subbasinsFile if self.clipperFile == '' else self.clipperFile
#                 self._dlg.setCursor(Qt.WaitCursor)
#                 self.L.calcHillslopes(threshold, clipper, root)
#                 self._dlg.setCursor(Qt.ArrowCursor)
#                 QSWATUtils.loginfo('Created valley depths file {0}'.format(self._gv.valleyDepthsFile))
            self.progress('')
        else:
            self._gv.distStFile = ''
    
    def checkDEMProcessed(self) -> bool:
        """
        Return true if using grid model or basinFile is newer than subbasinsFile if using existing watershed,
        or subbasins file is newer than slopeFile file if using grid model,
        or  subbasinsFile is newer than DEM.
        """
        if self._gv.existingWshed:
            return cast(bool, self._gv.useGridModel or QSWATUtils.isUpToDate(self._gv.subbasinsFile, self._gv.basinFile))
        if self._gv.useGridModel:
            return cast(bool, QSWATUtils.isUpToDate(self._gv.slopeFile, self._gv.subbasinsFile))
        else:
            return cast(bool, QSWATUtils.isUpToDate(self._gv.demFile, self._gv.subbasinsFile))
        
    def btnSetDEM(self) -> None:
        """Open and load DEM; set default threshold."""
        root = QgsProject.instance().layerTreeRoot()
        (demFile, demMapLayer) = QSWATUtils.openAndLoadFile(root, FileTypes._DEM, self._dlg.selectDem,
                                                            self._gv.demDir, self._gv, None, QSWATUtils._WATERSHED_GROUP_NAME)
        #QSWATUtils.printLayers(root, 1)
        if demFile and demMapLayer:
            self._gv.demFile = demFile
            self._gv.elevationNoData = demMapLayer.dataProvider().sourceNoDataValue(1)
            self.setDefaultNumCells(demMapLayer)
            # warn if large DEM
            numCells = self.demWidth * self.demHeight
            if numCells > 4E6:
                millions = int(numCells / 1E6)
                self._gv.iface.messageBar().pushMessage('Large DEM',
                                                 'This DEM has over {0!s} million cells and could take some time to process.  Be patient!'.format(millions),
                                                 level=Qgis.Warning, duration=20)
            #QSWATUtils.printLayers(root, 2)
            self.addHillshade(demFile, root, demMapLayer, self._gv)
            #QSWATUtils.printLayers(root, 6)

    @staticmethod            
    def addHillshade(demFile: str, root: QgsLayerTree, demMapLayer: QgsRasterLayer, gv: GlobalVars) -> None:
        """ Create hillshade layer and load."""
        hillshadeFile = os.path.splitext(demFile)[0] + 'hillshade.tif'
        if not QSWATUtils.isUpToDate(demFile, hillshadeFile):
            processing.run("native:hillshade", 
                           {'INPUT':demFile,
                            'BAND':1,
                            'Z_FACTOR':5,
                            'SCALE':1,
                            'AZIMUTH':315,
                            'ALTITUDE':45,
                            'COMPUTE_EDGES':False,
                            'ZEVENBERGEN':False,
                            'COMBINED':False,
                            'MULTIDIRECTIONAL':False,
                            'OPTIONS':'',
                            'EXTRA':'',
                            'OUTPUT':hillshadeFile})

            # run gdaldem to generate hillshade.tif
#             if Parameters._ISWIN:
#                 gdaldem = 'gdaldem.exe'
#             else:
#                 gdaldem = 'gdaldem'
#             QSWATUtils.tryRemoveLayerAndFiles(hillshadeFile, root)
#             command = '"{0}" hillshade -compute_edges -z 5 "{1}" "{2}"'.format(gdaldem, demFile, hillshadeFile)
#             proc = subprocess.run(command,
#                                 shell=True,
#                                 stdout=subprocess.PIPE,
#                                 stderr=subprocess.STDOUT,
#                                 universal_newlines=True)    # text=True) only in python 3.7
#             QSWATUtils.loginfo('Creating hillshade ...')
#             QSWATUtils.loginfo(command)
#             for line in  proc.stdout.split('\n'):
#                 QSWATUtils.loginfo(line)
            if not os.path.exists(hillshadeFile):
                QSWATUtils.information('Failed to create hillshade file {0}'.format(hillshadeFile), gv.isBatch)
                return
            QSWATUtils.copyPrj(demFile, hillshadeFile)
        # add hillshade above DEM
        # demLayer allowed to be None for batch running
        if demMapLayer:
            demLayer = root.findLayer(demMapLayer.id())
            #QSWATUtils.printLayers(root, 3)
            hillMapLayer = QSWATUtils.getLayerByFilename(root.findLayers(), hillshadeFile, FileTypes._HILLSHADE, 
                                                         gv, demLayer, QSWATUtils._WATERSHED_GROUP_NAME)[0]
            #QSWATUtils.printLayers(root, 4)
            if not hillMapLayer:
                QSWATUtils.information('Failed to load hillshade file {0}'.format(hillshadeFile), gv.isBatch)
                return
            # compress legend entry: need to find tree layer
            hillTreeLayer = root.findLayer(hillMapLayer.id())
            assert hillTreeLayer is not None
            hillTreeLayer.setExpanded(False)
            hillMapLayer.renderer().setOpacity(0.4)
            hillMapLayer.triggerRepaint()
            #QSWATUtils.printLayers(root, 5)
            
    def btnSetBurn(self) -> None:
        """Open and load stream network to burn in."""
        root = QgsProject.instance().layerTreeRoot()
        (burnFile, burnLayer) = QSWATUtils.openAndLoadFile(root, FileTypes._BURN, self._dlg.selectBurn, 
                                                           self._gv.shapesDir, self._gv, None, QSWATUtils._WATERSHED_GROUP_NAME)
        if burnFile and burnLayer:
            fileType = QgsWkbTypes.geometryType(burnLayer.dataProvider().wkbType())
            if fileType != QgsWkbTypes.LineGeometry:
                QSWATUtils.error('Burn in file {0} is not a line shapefile'.format(burnFile), self._gv.isBatch)
            else:
                self._gv.burnFile = burnFile
        
    def btnSetOutlets(self) -> None:
        """Open and load inlets/outlets shapefile."""
        root = QgsProject.instance().layerTreeRoot()
        if self._gv.existingWshed:
            assert self._dlg.tabWidget.currentIndex() == 1
            box = self._dlg.selectExistOutlets
        else:
            assert self._dlg.tabWidget.currentIndex() == 0
            box = self._dlg.selectOutlets
            self.thresholdChanged = True
        (outletFile, outletLayer) = QSWATUtils.openAndLoadFile(root, FileTypes._OUTLETS, box, self._gv.shapesDir,
                                                               self._gv, None, QSWATUtils._WATERSHED_GROUP_NAME)
        if outletFile and outletLayer:
            self._gv.snapFile = ''
            self._dlg.snappedLabel.setText('')
            fileType = QgsWkbTypes.geometryType(outletLayer.dataProvider().wkbType())
            if fileType != QgsWkbTypes.PointGeometry:
                QSWATUtils.error('Inlets/outlets file {0} is not a point shapefile'.format(outletFile), self._gv.isBatch) 
            else:
                self._gv.outletFile = outletFile
                
    def btnSetSubbasins(self) -> None:
        """Open and load existing subbasins shapefile."""
        root = QgsProject.instance().layerTreeRoot()
        ft = FileTypes._GRID if self._gv.useGridModel else FileTypes._EXISTINGSUBBASINS
        subbasinsFile, subbasinsLayer = QSWATUtils.openAndLoadFile(root, ft, self._dlg.selectSubbasins, self._gv.shapesDir, 
                                                                   self._gv, None, QSWATUtils._WATERSHED_GROUP_NAME)
        if subbasinsFile and subbasinsLayer:
            fileType = QgsWkbTypes.geometryType(subbasinsLayer.dataProvider().wkbType())
            if fileType != QgsWkbTypes.PolygonGeometry:
                QSWATUtils.error('Subbasins file {0} is not a polygon shapefile'.format(self._dlg.selectSubbasins.text()), self._gv.isBatch)
            else:
                self._gv.subbasinsFile = subbasinsFile
                subbasinsLayer.setLabelsEnabled(True)
                if self._gv.useGridModel:
                    # don'texpand grid layer legend
                    treeLayer = QSWATUtils.getLayerByLegend(QSWATUtils._GRIDLEGEND, root.findLayers())
                    if treeLayer is not None:
                        treeLayer.setExpanded(False)   
                
    def btnSetWshed(self) -> None:
        """Open and load existing watershed shapefile."""
        root = QgsProject.instance().layerTreeRoot()
        ft = FileTypes._EXISTINGWATERSHED
        wshedFile, wshedLayer = QSWATUtils.openAndLoadFile(root, ft, self._dlg.selectWshed, self._gv.shapesDir, 
                                                                   self._gv, None, QSWATUtils._WATERSHED_GROUP_NAME)
        if wshedFile and wshedLayer:
            fileType = QgsWkbTypes.geometryType(wshedLayer.dataProvider().wkbType())
            if fileType != QgsWkbTypes.PolygonGeometry:
                QSWATUtils.error('Subbasins file {0} is not a polygon shapefile'.format(self._dlg.selectWshed.text()), self._gv.isBatch)
            else:
                self._gv.wshedFile = wshedFile 
        
    def btnSetStreams(self) -> None:
        """Open and load existing streams shapefile or drainage table."""
        root = QgsProject.instance().layerTreeRoot()
        legend = QSWATUtils._GRIDLEGEND if self._dlg.useGrid else QSWATUtils._SUBBASINSLEGEND
        subsLayer = QSWATUtils.getLayerByLegend(legend, root.findLayers())
        if subsLayer is not None:
            self._gv.iface.setActiveLayer(subsLayer.layer())
        if self._dlg.useGrid:
            if not self.gridDrainage and not self.streamDrainage:
                ft = FileTypes._CSV
            else:
                ft = FileTypes._GRIDSTREAMS
                strng = 'Streams'
        else:
            ft = FileTypes._CHANNELS
            strng = 'Channels'
        saveDir = self._gv.shapesDir
        channelFile, channelLayer = QSWATUtils.openAndLoadFile(root, ft, self._dlg.selectStreams, saveDir, 
                                                             self._gv, subsLayer, QSWATUtils._WATERSHED_GROUP_NAME)
        if channelFile and channelLayer:
            fileType = QgsWkbTypes.geometryType(channelLayer.dataProvider().wkbType())
            if fileType != QgsWkbTypes.LineGeometry:
                QSWATUtils.error('{0} file {1} is not a line shapefile'.format(strng, self._dlg.selectStreams.text()), self._gv.isBatch)
            else:
                self._gv.channelFile = channelFile
                if self._dlg.useGrid:
                    self._gv.streamFile = channelFile
        elif ft == FileTypes._CSV and channelFile:
            self._dlg.selectStreams.setText(channelFile)
            self.drainageTable = channelFile 
    
    def runTauDEM1(self) -> None:
        """Run Taudem to create stream reach network."""
        self.runTauDEM(None, False)
       
    def runTauDEM2(self) -> None:
        """Run TauDEM to create watershed shapefile."""
        # first remove any existing shapesDir inlets/outlets file as will
        # probably be inconsistent with new subbasins
        # UNLESS the file is called arcextra.shp, when it was generated from an ArcSWAT project
        root = QgsProject.instance().layerTreeRoot()
        extraFile = os.path.join(self._gv.shapesDir, 'arcextra.shp')
        extraLayer = QSWATUtils.getLayerByFilename(root.findLayers(), extraFile, None, None, None, None)[0]
        if extraLayer is None:
            QSWATUtils.removeLayerByLegend(QSWATUtils._EXTRALEGEND, root.findLayers())
            self._gv.extraOutletFile = ''
        if not self._dlg.useOutlets.isChecked():
            self.runTauDEM(None, True)
        else:
            outletFile = self._dlg.selectOutlets.text()
            if outletFile == '' or not os.path.exists(outletFile):
                QSWATUtils.error('Please select an inlets/outlets file', self._gv.isBatch)
                return
            # remove any snapped inlets/outlets file that is visible: causes DSNODEIDs to be set to zero
            QSWATUtils.removeLayerByLegend(QSWATUtils._SNAPPEDLEGEND, root.findLayers())
            self.runTauDEM(outletFile, True)
        
    def changeExisting(self) -> None:
        """Change between using existing and delineating watershed."""
        tab = self._dlg.tabWidget.currentIndex()
        if tab > 1: # DEM properties or TauDEM output
            return # no change
        self._gv.existingWshed = (tab == 1)
        self.setDrainage()
    
    def runTauDEM(self, outletFile: Optional[str], makeWshed: bool) -> None:
        """Run TauDEM."""
        self.delineationFinishedOK = False
        demFile = self._dlg.selectDem.text()
        if demFile == '' or not os.path.exists(demFile):
            QSWATUtils.error('Please select a DEM file', self._gv.isBatch)
            return
        self.isDelineated = False
        self.lakesDone = False
        self.lakePointsAdded = False
        self.gridLakesAdded = False
        self._gv.writeProjectConfig(0, 0)
        self.setMergeResGroups()
        self._gv.demFile = demFile
        streamThreshold = self._dlg.numCellsSt.text()
        if not self._gv.useGridModel:
            channelThreshold = self._dlg.numCellsCh.text()
            try:
                streamCells = int(streamThreshold)
            except Exception:
                    QSWATUtils.exceptionError('Cannot read stream threshold cell count {0}'.format(streamThreshold), self._gv.isBatch)
                    return
            try:
                channelCells = int(channelThreshold)
            except Exception:
                    QSWATUtils.exceptionError('Cannot read channel threshold cell count {0}'.format(channelThreshold), self._gv.isBatch)
                    return
            if channelCells > streamCells:
                QSWATUtils.error('Channel threshold {0} cannot be greater than stream threshold {1}'.format(channelCells, streamCells), self._gv.isBatch)
                return
        # find dem layer (or load it)
        root = QgsProject.instance().layerTreeRoot()
        demLayer, _ = QSWATUtils.getLayerByFilename(root.findLayers(), self._gv.demFile, FileTypes._DEM,
                                                    self._gv, None, QSWATUtils._WATERSHED_GROUP_NAME)
        if not demLayer:
            QSWATUtils.error('Cannot load DEM {0}'.format(self._gv.demFile), self._gv.isBatch)
            return
        # changing default number of cells 
        if not self.setDefaultNumCells(demLayer):
            return
        # check stream and channel thresholds not inconsistent
        if not self._gv.useGridModel:
            streamThresh = int(self._dlg.numCellsSt.text())
            chanThresh = int(self._dlg.numCellsCh.text())
            if chanThresh > streamThresh:
                QSWATUtils.error('Channel threshold (currently {0} cells) cannot be greater than the stream threshold (currently {1} cells)'.
                                 format(chanThresh, streamThresh), self._gv.isBatch)
                return
        (base, suffix) = os.path.splitext(self._gv.demFile)
        baseDir, baseName = os.path.split(base)
        shapesBase = QSWATUtils.join(self._gv.shapesDir, baseName)
        # burn in if required
        if self._dlg.checkBurn.isChecked():
            burnFile = self._dlg.selectBurn.text()
            if burnFile == '':
                QSWATUtils.error('Please select a burn in stream network shapefile', self._gv.isBatch)
                return
            if not os.path.exists(burnFile):
                QSWATUtils.error('Cannot find burn in file {0}'.format(burnFile), self._gv.isBatch)
                return
            burnedDemFile = os.path.splitext(self._gv.demFile)[0] + '_burned.tif'
            if not QSWATUtils.isUpToDate(demFile, burnedDemFile) or not QSWATUtils.isUpToDate(burnFile, burnedDemFile):
                # just in case
                QSWATUtils.tryRemoveLayerAndFiles(burnedDemFile, root)
                self.progress('Burning streams ...')
                QSWATTopology.burnStream(burnFile, demFile, burnedDemFile, self._gv.burninDepth, self._gv.verticalFactor, self._gv.isBatch)
                if not os.path.exists(burnedDemFile):
                    return
            self._gv.burnedDemFile = burnedDemFile
            delineationDem = burnedDemFile
        else:
            self._gv.burnedDemFile = ''
            delineationDem = demFile
        numProcesses = self._dlg.numProcesses.value()
        mpiexecPath = self._gv.mpiexecPath
        if numProcesses > 0 and (mpiexecPath == '' or not os.path.exists(mpiexecPath)):
            QSWATUtils.information('Cannot find MPI program {0} so running TauDEM with just one process'.format(mpiexecPath), self._gv.isBatch)
            numProcesses = 0
            self._dlg.numProcesses.setValue(0)
        QSettings().setValue('/QSWATPlus/NumProcesses', str(numProcesses))
        if self._dlg.showTaudem.isChecked():
            self._dlg.tabWidget.setCurrentIndex(3)
        self._dlg.setCursor(Qt.WaitCursor)
        self._dlg.taudemOutput.clear()
        # delet old flood files if any
        self.deleteFloodFiles(root)
        felFile = base + 'fel' + suffix
        QSWATUtils.removeLayer(felFile, root)
        self.progress('PitFill ...')
        depmask = QSWATUtils.join(baseDir, 'depmask.tif')
        if not os.path.isfile(depmask):
            depmask = None
        ok = TauDEMUtils.runPitFill(delineationDem, depmask, felFile, numProcesses, self._dlg.taudemOutput)   
        if not ok:
            self.cleanUp(3)
            return
        self._gv.felFile = felFile
        sd8File = base + 'sd8' + suffix
        pFile = base + 'p' + suffix
        QSWATUtils.removeLayer(sd8File, root)
        QSWATUtils.removeLayer(pFile, root)
        self.progress('D8FlowDir ...')
        ok = TauDEMUtils.runD8FlowDir(felFile, sd8File, pFile, numProcesses, self._dlg.taudemOutput)   
        if not ok:
            self.cleanUp(3)
            return
        slpFile = base + 'slp' + suffix
        angFile = base + 'ang' + suffix
        QSWATUtils.removeLayer(slpFile, root)
        QSWATUtils.removeLayer(angFile, root)
        self.progress('DinfFlowDir ...')
        ok = TauDEMUtils.runDinfFlowDir(felFile, slpFile, angFile, numProcesses, self._dlg.taudemOutput)  
        if not ok:
            self.cleanUp(3)
            return
        ad8File = base + 'ad8' + suffix
        QSWATUtils.removeLayer(ad8File, root)
        self.progress('AreaD8 ...')
        ok = TauDEMUtils.runAreaD8(pFile, ad8File, None, None, numProcesses, self._dlg.taudemOutput, mustRun=self.thresholdChanged)   
        if not ok:
            self.cleanUp(3)
            return
        scaFile = base + 'sca' + suffix
        QSWATUtils.removeLayer(scaFile, root)
        self.progress('AreaDinf ...')
        ok = TauDEMUtils.runAreaDinf(angFile, scaFile, None, numProcesses, self._dlg.taudemOutput, mustRun=self.thresholdChanged)  
        if not ok:
            self.cleanUp(3)
            return
        gordFile = base + 'gord' + suffix
        plenFile = base + 'plen' + suffix
        tlenFile = base + 'tlen' + suffix
        QSWATUtils.removeLayer(gordFile, root)
        QSWATUtils.removeLayer(plenFile, root)
        QSWATUtils.removeLayer(tlenFile, root)
        self.progress('GridNet ...')
        ok = TauDEMUtils.runGridNet(pFile, plenFile, tlenFile, gordFile, None, numProcesses, self._dlg.taudemOutput, mustRun=self.thresholdChanged)  
        if not ok:
            self.cleanUp(3)
            return
        srcStreamFile = base + 'srcStream' + suffix
        QSWATUtils.removeLayer(srcStreamFile, root)
        self.progress('Threshold ...')
        streamThreshold = self._dlg.numCellsSt.text()
        if self._gv.isBatch:
            QSWATUtils.information('Stream threshold: {0} cells'.format(streamThreshold), True)
        ok = TauDEMUtils.runThreshold(ad8File, srcStreamFile, streamThreshold, numProcesses, self._dlg.taudemOutput, mustRun=self.thresholdChanged) 
        if not ok:
            self.cleanUp(3)
            return
        if not self._gv.useGridModel:
            srcChannelFile = base + 'srcChannel' + suffix
            QSWATUtils.removeLayer(srcChannelFile, root)
            channelThreshold = self._dlg.numCellsCh.text()
            if self._gv.isBatch:
                QSWATUtils.information('Channel threshold: {0} cells'.format(channelThreshold), True)
            ok = TauDEMUtils.runThreshold(ad8File, srcChannelFile, channelThreshold, numProcesses, self._dlg.taudemOutput, mustRun=self.thresholdChanged) 
            if not ok:
                self.cleanUp(3)
                return
        ordStreamFile = base + 'ordStream' + suffix
        streamFile = shapesBase + 'stream.shp'
        # if stream shapefile already exists and is a directory, set path to .shp
        streamFile = QSWATUtils.dirToShapefile(streamFile)
        treeStreamFile = base + 'treeStream.dat'
        coordStreamFile = base + 'coordStream.dat'
        wStreamFile = base + 'wStream' + suffix
        QSWATUtils.removeLayer(ordStreamFile, root)
        QSWATUtils.removeLayer(streamFile, root)
        QSWATUtils.removeLayer(wStreamFile, root)
        self.progress('StreamNet ...')
        ok = TauDEMUtils.runStreamNet(felFile, pFile, ad8File, srcStreamFile, None, ordStreamFile, treeStreamFile, coordStreamFile,
                                          streamFile, wStreamFile, False, numProcesses, self._dlg.taudemOutput, mustRun=self.thresholdChanged)
        if not ok:
            self.cleanUp(3)
            return
        # if stream shapefile is a directory, set path to .shp, since not done earlier if streamFile did not exist then
        streamFile = QSWATUtils.dirToShapefile(streamFile)
        QSWATUtils.copyPrj(demFile, streamFile)
        QSWATUtils.copyPrj(demFile, wStreamFile)
        if not self._gv.useGridModel:
            ordChannelFile = base + 'ordChannel' + suffix
            treeChannelFile = base + 'treeChannel.dat'
            coordChannelFile = base + 'coordChannel.dat'
            channelFile = shapesBase + 'channel.shp'
            # if channel shapefile already exists and is a directory, set path to .shp
            channelFile = QSWATUtils.dirToShapefile(channelFile)
            wChannelFile = base + 'wChannel' + suffix
            QSWATUtils.removeLayer(ordChannelFile, root)
            QSWATUtils.removeLayer(channelFile, root)
            QSWATUtils.removeLayer(wChannelFile, root)
            ok = TauDEMUtils.runStreamNet(felFile, pFile, ad8File, srcChannelFile, None, ordChannelFile, treeChannelFile, coordChannelFile,
                                              channelFile, wChannelFile, False, numProcesses, self._dlg.taudemOutput, mustRun=self.thresholdChanged)
            if not ok:
                self.cleanUp(3)
                return
            # if stream shapefile is a directory, set path to .shp, since not done earlier if streamFile did not exist then
            channelFile = QSWATUtils.dirToShapefile(channelFile)
            QSWATUtils.copyPrj(demFile, channelFile)
            QSWATUtils.copyPrj(demFile, wChannelFile)
        # load stream network
        # load above fullHRUs or hillshade or DEM
        fullHRUsLayer = QSWATUtils.getLayerByLegend(QSWATUtils._FULLHRUSLEGEND, root.findLayers())
        hillshadeLayer = QSWATUtils.getLayerByLegend(QSWATUtils._HILLSHADELEGEND, root.findLayers())
        if fullHRUsLayer is not None:
            subLayer = fullHRUsLayer
        elif hillshadeLayer is not None:
            subLayer = hillshadeLayer
        else:
            subLayer = root.findLayer(demLayer.id())
        streamLayer, loaded = QSWATUtils.getLayerByFilename(root.findLayers(), streamFile, FileTypes._STREAMS, 
                                                            self._gv, subLayer, QSWATUtils._WATERSHED_GROUP_NAME)
        if streamLayer is None or not loaded:
            self.cleanUp(-1)
            return
        self._gv.streamFile = streamFile
        self._gv.delinStreamFile = streamFile
        if not self._gv.useGridModel:
            channelLayer, loaded = QSWATUtils.getLayerByFilename(root.findLayers(), channelFile, FileTypes._CHANNELS, 
                                                                 self._gv, subLayer, QSWATUtils._WATERSHED_GROUP_NAME)
            if channelLayer is None or not loaded:
                self.cleanUp(-1)
                return
            self._gv.channelFile = channelFile
        if not makeWshed:
            self._gv.snapFile = ''
            self._dlg.snappedLabel.setText('')
            # initial run to enable placing of outlets, so finishes with load of stream network
            self._dlg.taudemOutput.append('------------------- TauDEM finished -------------------\n')
            self.saveProj()
            self.cleanUp(-1)
            return
        if self._dlg.useOutlets.isChecked():
            assert outletFile is not None
            outletBase = os.path.splitext(outletFile)[0]  
            snapFile = outletBase + '_snap.shp'
            outletLayer, loaded = QSWATUtils.getLayerByFilename(root.findLayers(), outletFile, FileTypes._OUTLETS,
                                                                self._gv, None, QSWATUtils._WATERSHED_GROUP_NAME)
            if not outletLayer:
                self.cleanUp(-1)
                return
            self.progress('SnapOutletsToStreams ...')
            chanLayer = streamLayer if self._gv.useGridModel else channelLayer
            ok = self.createSnapOutletFile(outletLayer, streamLayer, chanLayer, outletFile, snapFile, root)  
            if not ok:
                self.cleanUp(-1)
                return
            # replaced by snapping
            # outletMovedFile = outletBase + '_moved.shp'
            # QSWATUtils.removeLayer(outletMovedFile, li)
            # self.progress('MoveOutletsToStreams ...')
            # ok = TauDEMUtils.runMoveOutlets(pFile, srcFile, outletFile, outletMovedFile, numProcesses, self._dlg.taudemOutput, mustRun=self.thresholdChanged)
            # if not ok:
            #   self.cleanUp(3)
            #    return
        
            # repeat AreaD8, GridNet, Threshold and StreamNet with snapped outlets
            mustRun = self.thresholdChanged
            QSWATUtils.removeLayer(ad8File, root)
            self.progress('AreaD8 ...')
            ok = TauDEMUtils.runAreaD8(pFile, ad8File, self._gv.snapFile, None, numProcesses, self._dlg.taudemOutput, mustRun=mustRun)   
            if not ok:
                self.cleanUp(3)
                return
            self.progress('GridNet ...')
            ok = TauDEMUtils.runGridNet(pFile, plenFile, tlenFile, gordFile, self._gv.snapFile, numProcesses, self._dlg.taudemOutput, mustRun=mustRun)  
            if not ok:
                self.cleanUp(3)
                return
            QSWATUtils.removeLayer(srcStreamFile, root)
            self.progress('Threshold ...')
            ok = TauDEMUtils.runThreshold(ad8File, srcStreamFile, streamThreshold, numProcesses, self._dlg.taudemOutput, mustRun=mustRun) 
            if not ok:
                self.cleanUp(3)
                return
            if not self._gv.useGridModel:
                QSWATUtils.removeLayer(srcChannelFile, root)
                ok = TauDEMUtils.runThreshold(ad8File, srcChannelFile, channelThreshold, numProcesses, self._dlg.taudemOutput, mustRun=mustRun) 
                if not ok:
                    self.cleanUp(3)
                    return
            # for subbasins only need to consider inlets and outlets: lakes and point sources added to channels later
            ioSnapFile = self.reduceToInletsOutlets(root)
            if ioSnapFile is None:
                self.cleanUp(-1)
                return
            QSWATUtils.removeLayer(streamFile, root)
            # having this as a layer results in DSNODEIDs being set to zero
            QSWATUtils.removeLayer(ioSnapFile, root)
            self.progress('StreamNet ...')
            ok = TauDEMUtils.runStreamNet(felFile, pFile, ad8File, srcStreamFile, ioSnapFile, ordStreamFile, treeStreamFile, coordStreamFile,
                                          streamFile, wStreamFile, False, numProcesses, self._dlg.taudemOutput, mustRun=mustRun)
            if not ok:
                self.cleanUp(3)
                return
            QSWATUtils.copyPrj(demFile, streamFile)
            QSWATUtils.copyPrj(demFile, wStreamFile)
            if not self._gv.useGridModel:
                QSWATUtils.removeLayer(channelFile, root)
                # having this as a layer results in DSNODEIDs being set to zero
                QSWATUtils.removeLayer(self._gv.snapFile, root)
                ok = TauDEMUtils.runStreamNet(felFile, pFile, ad8File, srcChannelFile, self._gv.snapFile, ordChannelFile, treeChannelFile, coordChannelFile,
                                              channelFile, wChannelFile, False, numProcesses, self._dlg.taudemOutput, mustRun=mustRun)
                if not ok:
                    self.cleanUp(3)
                    return
                QSWATUtils.copyPrj(demFile, channelFile)
                QSWATUtils.copyPrj(demFile, wChannelFile)
            # load above demLayer (or hillshadelayer if exists) so streamLayer loads above it and below outlets
            # (or use Full HRUs layer if there is one)
            if fullHRUsLayer is not None:
                subLayer = fullHRUsLayer
            elif hillshadeLayer is not None:
                subLayer = hillshadeLayer
            else:
                subLayer = root.findLayer(demLayer.id())
            streamLayer, loaded = QSWATUtils.getLayerByFilename(root.findLayers(), streamFile, FileTypes._STREAMS, 
                                                                self._gv, subLayer, QSWATUtils._WATERSHED_GROUP_NAME)
            if not streamLayer or not loaded:
                self.cleanUp(-1)
                return
            if not self._gv.useGridModel:
                channelLayer, loaded = QSWATUtils.getLayerByFilename(root.findLayers(), channelFile, FileTypes._CHANNELS, 
                                                                     self._gv, subLayer, QSWATUtils._WATERSHED_GROUP_NAME)
                if not channelLayer or not loaded:
                    self.cleanUp(-1)
                    return
            # check if stream network has only one feature
            if streamLayer.featureCount() == 1:
                QSWATUtils.information('There is only one stream in your watershed, so you will only get one subbasin.  You may want to reduce the threshold.', self._gv.isBatch)
        self._dlg.taudemOutput.append('------------------- TauDEM finished -------------------\n')
        self._gv.pFile = pFile
        self._gv.ad8File = ad8File
        self._gv.basinFile = wStreamFile
        if not self._gv.useGridModel:
            self._gv.channelBasinFile = wChannelFile
        self._gv.srcChannelFile = '' if self._gv.useGridModel else srcChannelFile
        if self._dlg.checkBurn.isChecked():
            # need to make slope file from original dem
            felNoburn = base + 'felnoburn' + suffix
            QSWATUtils.removeLayer(felNoburn, root)
            self.progress('PitFill ...')
            ok = TauDEMUtils.runPitFill(demFile, depmask, felNoburn, numProcesses, self._dlg.taudemOutput)  
            if not ok:
                self.cleanUp(3)
                return
            slopeFile = base + 'slope' + suffix
            angleFile = base + 'angle' + suffix
            QSWATUtils.removeLayer(slopeFile, root)
            QSWATUtils.removeLayer(angleFile, root)
            self.progress('DinfFlowDir ...')
            ok = TauDEMUtils.runDinfFlowDir(felNoburn, slopeFile, angleFile, numProcesses, self._dlg.taudemOutput)  
            if not ok:
                self.cleanUp(3)
                return
            self._gv.slopeFile = slopeFile
        else:
            self._gv.slopeFile = slpFile
        self._gv.streamFile = streamFile
        self._gv.delinStreamFile = streamFile
        if not self._gv.useGridModel:
            self._gv.channelFile = channelFile
        self._gv.outletFile = outletFile if self._dlg.useOutlets.isChecked() else ''
        subbasinsFile = shapesBase + 'subbasins.shp'
        self.createWatershedShapefile(wStreamFile, subbasinsFile, FileTypes._SUBBASINS, root)
        self._gv.subbasinsFile = subbasinsFile
        if not self._gv.useGridModel:
            wshedFile = shapesBase + 'wshed.shp'
            self.createWatershedShapefile(wChannelFile, wshedFile, FileTypes._WATERSHED, root)
            self._gv.wshedFile = wshedFile
        if self._dlg.gridBox.isChecked():
            self.createGridShapefile(pFile, ad8File, wStreamFile)
            gridStreamLayer = QSWATUtils.getLayerByLegend(QSWATUtils._GRIDSTREAMSLEGEND, root.findLayers())
            if gridStreamLayer is None:
                QSWATUtils.error('Cannot find grid streams layer', self._gv.isBatch)
                self.cleanUp(-1)
                return
            chanLayer = gridStreamLayer.layer()  # convert TreeLayer to QgsVectorLayer
        elif not self._gv.useGridModel:
            self._gv.topo.addBasinsToChannelFile(channelLayer, self._gv.basinFile)
            chanLayer = channelLayer
        snapLayer = QgsVectorLayer(self._gv.snapFile, 'Snapped inlets/outlets', 'ogr') if self._dlg.useOutlets.isChecked() else None
        ad8Layer = QgsRasterLayer(self._gv.ad8File, 'Accumulation')
        if not self._gv.topo.setUp0(demLayer, chanLayer, snapLayer, ad8Layer, self._gv):
            self.cleanUp(-1)
            return
        QSWATUtils.loginfo('{0} outlets after setUp0'.format(len(self._gv.topo.outlets)))
        self.isDelineated = True
        self.setMergeResGroups()
        self.saveProj()
        self.cleanUp(-1)
        
    def runExisting(self) -> None:
        """Do delineation from existing streams, channels, subbasins and watershed."""
        self.delineationFinishedOK = False
        self.lakesDone = False
        demFile = self._dlg.selectDem.text()
        if demFile == '' or not os.path.exists(demFile):
            QSWATUtils.error('Please select a DEM file', self._gv.isBatch)
            return
        self._gv.demFile = demFile
        subbasinsFile = self._dlg.selectSubbasins.text()
        if subbasinsFile == '' or not os.path.exists(subbasinsFile):
            QSWATUtils.error('Please select a {0}'.format(self._dlg.selectSubbasinsLabel.text().lower()), self._gv.isBatch)
            return
        if self._gv.useGridModel:
            if not self.gridDrainage:
                if self.streamDrainage:
                    streamFile = self._dlg.selectStreams.text()
                    if streamFile == '' or not os.path.exists(streamFile):
                        QSWATUtils.error('Please select a streams shapefile', self._gv.isBatch)
                        return
                else:
                    drainageTable = self._dlg.selectStreams.text()
                    if drainageTable == '' or not os.path.exists(drainageTable):
                        QSWATUtils.error('Please select a drainage table csv file', self._gv.isBatch)
                        return
        else:        
            wshedFile = self._dlg.selectWshed.text()
            if wshedFile == '' or not os.path.exists(wshedFile):
                QSWATUtils.error('Please select a watershed shapefile', self._gv.isBatch)
                return        
            channelFile = self._dlg.selectStreams.text()
            if channelFile == '' or not os.path.exists(channelFile):
                QSWATUtils.error('Please select a channels shapefile', self._gv.isBatch)
                return
        outletFile = self._dlg.selectExistOutlets.text()
        if outletFile != '':
            if not os.path.exists(outletFile):
                QSWATUtils.error('Cannot find inlets/outlets shapefile {0}'.format(outletFile), self._gv.isBatch)
                return
        self.isDelineated = False
        self.setMergeResGroups()
        # find layers (or load them)
        root = QgsProject.instance().layerTreeRoot()
        demLayer, _ = QSWATUtils.getLayerByFilename(root.findLayers(), self._gv.demFile, FileTypes._DEM,
                                                    self._gv, None, QSWATUtils._WATERSHED_GROUP_NAME)
        if not demLayer:
            QSWATUtils.error('Cannot load DEM {0}'.format(self._gv.demFile), self._gv.isBatch)
            return
        subbasinsLayer, _ = QSWATUtils.getLayerByFilename(root.findLayers(), subbasinsFile, FileTypes._EXISTINGSUBBASINS, 
                                                               self._gv, demLayer, QSWATUtils._WATERSHED_GROUP_NAME)
        if not subbasinsLayer:
            QSWATUtils.error('Cannot load subbasins shapefile {0}'.format(subbasinsFile), self._gv.isBatch)
            return
        if not self._gv.useGridModel:
            wshedLayer, _ = QSWATUtils.getLayerByFilename(root.findLayers(), wshedFile, FileTypes._EXISTINGWATERSHED, 
                                                               self._gv, subbasinsLayer, QSWATUtils._WATERSHED_GROUP_NAME)
            if not wshedLayer:
                QSWATUtils.error('Cannot load watershed shapefile {0}'.format(wshedFile), self._gv.isBatch)
                return
            else:
                QSWATUtils.setLayerVisibility(wshedLayer, False, root)
        if outletFile != '':
            outletLayer, _ = QSWATUtils.getLayerByFilename(root.findLayers(), outletFile, FileTypes._OUTLETS,
                                                                self._gv, None, QSWATUtils._WATERSHED_GROUP_NAME)
            if not outletLayer:
                QSWATUtils.error('Cannot load inlets/outlets shapefile {0}'.format(outletFile), self._gv.isBatch)
                return
        else:
            outletLayer = None
        self._dlg.setCursor(Qt.WaitCursor)
        if self._gv.useGridModel:
            if self.gridDrainage or not self.streamDrainage:
                streamFile = self.writeDrainageStreamsShapefile(subbasinsFile, subbasinsLayer, outletLayer, root)
                if streamFile is None:
                    self.cleanUp(-1)
                    return
                ft = FileTypes._DRAINSTREAMS 
            else: 
                ft = FileTypes._GRIDSTREAMS
                # use streams for channels for grids
            channelFile = streamFile
        else:
            ft = FileTypes._CHANNELS
        channelLayer, _ = QSWATUtils.getLayerByFilename(root.findLayers(), channelFile, ft, 
                                                             self._gv, None, QSWATUtils._WATERSHED_GROUP_NAME)
        if not channelLayer:
            QSWATUtils.error('Cannot load channels shapefile {0}'.format(channelFile), self._gv.isBatch)
            self.cleanUp(-1)
            return
        # ready to start processing
        (base, suffix) = os.path.splitext(self._gv.demFile)
        numProcesses = self._dlg.numProcesses.value()
        QSettings().setValue('/QSWATPlus/NumProcesses', str(numProcesses))
        self._dlg.taudemOutput.clear()
        # create Dinf slopes
        felFile = base + 'fel' + suffix
        slpFile = base + 'slp' + suffix
        angFile = base + 'ang' + suffix
        QSWATUtils.removeLayer(slpFile, root)
        QSWATUtils.removeLayer(angFile, root)
        self.progress('DinfFlowDir ...')
        willRun = not (QSWATUtils.isUpToDate(demFile, slpFile) and QSWATUtils.isUpToDate(demFile, angFile))
        if willRun:
            if self._dlg.showTaudem.isChecked():
                self._dlg.tabWidget.setCurrentIndex(3)
            depmask = QSWATUtils.join(os.path.split(self._gv.demFile)[0], 'depmask.tif')
            if not os.path.isfile(depmask):
                depmask = None
            ok = TauDEMUtils.runPitFill(demFile, depmask, felFile, numProcesses, self._dlg.taudemOutput) 
            if not ok:
                self.cleanUp(3)
                return
            ok = TauDEMUtils.runDinfFlowDir(felFile, slpFile, angFile, numProcesses, self._dlg.taudemOutput)  
            if not ok:
                self.cleanUp(3)
                return
        if self._gv.useGridModel:
            if len(self._gv.topo.basinCentroids) == 0:
                # set centroids
                basinIndex = self._gv.topo.getIndex(subbasinsLayer, QSWATTopology._POLYGONID)
                if basinIndex < 0:
                    return
                for feature in subbasinsLayer.getFeatures():
                    basin = feature[basinIndex]
                    centroid, (xmin, xmax), (ymin, ymax) = QSWATUtils.centreGridCell(feature)
                    self._gv.topo.basinCentroids[basin] = (centroid.x(), centroid.y())
                    if self._gv.gridSize == 0: # not set from project file
                        xSize = demLayer.rasterUnitsPerPixelX()
                        ySize = demLayer.rasterUnitsPerPixelY()
                        xGridSize = int((xmax - xmin) / xSize + 0.5)
                        yGridSize = int((ymax - ymin) / ySize + 0.5)
                        if xGridSize == yGridSize:
                            self._gv.gridSize = xGridSize
                            QSWATUtils.loginfo('Grid size set to {0}'.format(self._gv.gridSize))
                        else:
                            QSWATUtils.error('Horizontal ({0}) and vertical ({1}) estimates of grid size are different.  Is your watershed shapefile a grid?'.
                                             format(xGridSize, yGridSize), self._gv.isBatch)
                            return
            # check grid size is set
            elif self._gv.gridSize == 0:
                cell = next(subbasinsLayer.getFeatures())
                _, (xmin, xmax), (ymin, ymax) = QSWATUtils.centreGridCell(cell)
                xSize = demLayer.rasterUnitsPerPixelX()
                ySize = demLayer.rasterUnitsPerPixelY()
                xGridSize = int((xmax - xmin) / xSize + 0.5)
                yGridSize = int((ymax - ymin) / ySize + 0.5)
                if xGridSize == yGridSize:
                    self._gv.gridSize = xGridSize
                    QSWATUtils.loginfo('Grid size set to {0}'.format(self._gv.gridSize))
                else:
                    QSWATUtils.error('Horizontal ({0}) and vertical ({1}) estimates of grid size are different.  Is your watershed shapefile a grid?'.
                                     format(xGridSize, yGridSize), self._gv.isBatch)
                    return
        else:
            # generate subbasins raster
            wStreamFile = base + 'wStream' + suffix
            if not (QSWATUtils.isUpToDate(demFile, wStreamFile) and QSWATUtils.isUpToDate(subbasinsFile, wStreamFile)):
                self.progress('Generating subbasins raster ...')
                wStreamFile = self.createBasinFile(subbasinsFile, demLayer, 'wStream', root)
            self._gv.basinFile = wStreamFile
            # generate watershed raster
            if not self._gv.useGridModel:
                wChannelFile = base + 'wChannel' + suffix
                if not (QSWATUtils.isUpToDate(demFile, wChannelFile) and QSWATUtils.isUpToDate(wshedFile, wChannelFile)):
                    self.progress('Generating watershed raster ...')
                    wChannelFile = self.createBasinFile(wshedFile, demLayer, 'wChannel', root)
                self._gv.channelBasinFile = wChannelFile
        self._gv.felFile = felFile
        self._gv.slopeFile = slpFile
        self._gv.subbasinsFile = subbasinsFile
        if not self._gv.useGridModel:
            self._gv.wshedFile = wshedFile
            self._gv.channelFile = channelFile
            if self._gv.isHUC:
                self._gv.streamFile = channelFile.replace('channels.shp', 'streams.shp')
        self._gv.outletFile = outletFile
        if self._gv.topo.setUp0(demLayer, channelLayer, outletLayer, None, self._gv):
            self.isDelineated = True
            self.setMergeResGroups()
            self.saveProj()
        self.cleanUp(-1)
        return
    
    def setDefaultNumCells(self, demLayer: QgsRasterLayer) -> bool:
        """Set threshold number of stream cells to default of 1% of number in grid, 
        unless already set, and similarly default channel cells to 10% of stream cells.
        """
        if not self.setDimensions(demLayer):
            return False
        # set to default number of cells unless already set
        if self._dlg.numCellsSt.text() == '':
            numCells = self.demWidth * self.demHeight
            defaultNumCellsSt = int(numCells * 0.01 + 0.5)
            self._dlg.numCellsSt.setText(str(defaultNumCellsSt))
        else:
            # already have a setting: keep same area but change number of cells according to dem cell size
            self.setNumCellsSt()
        if not self._gv.useGridModel:
            if self._dlg.numCellsCh.text() == '':
                defaultNumCellsCh = int(float(self._dlg.numCellsSt.text()) / 10 + 0.5)
                self._dlg.numCellsCh.setText(str(defaultNumCellsCh))
            else:
                self.setNumCellsCh()
        return True
            
    def setDimensions(self, demLayer: QgsRasterLayer) -> bool:
        """
        Set dimensions of DEM.
        
        Note demLayer is a map layer (not tree)
        Also sets DEM properties tab.  Return true if successful.
        """
        # can fail if demLayer is None or not projected
        try:
            self._gv.topo.setCrs(demLayer, self._gv)
            units = demLayer.crs().mapUnits()
        except Exception:
            QSWATUtils.loginfo('Failure to read DEM units: {0}'.format(traceback.format_exc()))
            return False
        provider = demLayer.dataProvider()
        self._gv.xBlockSize = provider.xBlockSize()
        self._gv.yBlockSize = provider.yBlockSize()
        QSWATUtils.loginfo('DEM horizontal and vertical block sizes are {0} and {1}'.format(self._gv.xBlockSize, self._gv.yBlockSize))
        demFile = QSWATUtils.layerFileInfo(demLayer).absoluteFilePath()
        demPrj = os.path.splitext(demFile)[0] + '.prj'
        demPrjTxt = demPrj + '.txt'
        if os.path.exists(demPrj) and not os.path.exists(demPrjTxt):
            command = 'gdalsrsinfo -p -o wkt "{0}" > "{1}"'.format(demPrj, demPrjTxt)
            os.system(command)
        if os.path.exists(demPrjTxt):
            with open(demPrjTxt) as prj:
                self._dlg.textBrowser.setText(prj.read())
        else:
            self._dlg.textBrowser.setText(demLayer.crs().toWkt()) # much poorer presentation
        try:
            epsg = demLayer.crs().authid()
            QSWATUtils.loginfo(epsg)
            rect = demLayer.extent()
            self._dlg.label.setText('Spatial reference: {0}'.format(epsg))
            # epsg has format 'EPSG:N' where N is the EPSG number
            startNum = epsg.find(':') + 1
            if self._gv.isBatch and startNum > 0:
                demDataFile = QSWATUtils.join(self._gv.projDir, 'dem_data.xml')
                if not os.path.exists(demDataFile):
                    with fileWriter(demDataFile) as f:
                        f.writeLine('<demdata>')
                        f.writeLine('<epsg>{0}</epsg>'.format(epsg[startNum:]))
                        f.writeLine('<minx>{0}</minx>'.format(rect.xMinimum()))
                        f.writeLine('<maxx>{0}</maxx>'.format(rect.xMaximum()))
                        f.writeLine('<miny>{0}</miny>'.format(rect.yMinimum()))
                        f.writeLine('<maxy>{0}</maxy>'.format(rect.yMaximum()))
                        f.writeLine('</demdata>')
        except Exception:
            # fail gracefully
            epsg = ''
        if units == QgsUnitTypes.DistanceMeters:
            self._gv.horizontalFactor = 1.0
            self._dlg.horizontalCombo.setCurrentIndex(self._dlg.horizontalCombo.findText(Parameters._METRES))
            self._dlg.horizontalCombo.setEnabled(False)
        elif units == QgsUnitTypes.DistanceFeet:
            self._gv.horizontalFactor = Parameters._FEETTOMETRES
            self._dlg.horizontalCombo.setCurrentIndex(self._dlg.horizontalCombo.findText(Parameters._FEET))
            self._dlg.horizontalCombo.setEnabled(False)
        else:
            if units == QgsUnitTypes.AngleDegrees:
                string = 'degrees'
                self._dlg.horizontalCombo.setCurrentIndex(self._dlg.horizontalCombo.findText(Parameters._DEGREES))
                self._dlg.horizontalCombo.setEnabled(False)
            else:
                string = 'unknown'
                self._dlg.horizontalCombo.setCurrentIndex(self._dlg.horizontalCombo.findText(Parameters._DEGREES))
                self._dlg.horizontalCombo.setEnabled(True)
            QSWATUtils.information('WARNING: DEM does not seem to be projected: its units are ' + string, self._gv.isBatch)
            return False
        self.demWidth = demLayer.width()
        self.demHeight = demLayer.height()
        if int(demLayer.rasterUnitsPerPixelX() + 0.5) != int(demLayer.rasterUnitsPerPixelY() + 0.5):
            QSWATUtils.information('WARNING: DEM cells are not square: {0!s} x {1!s}'.format(demLayer.rasterUnitsPerPixelX(), demLayer.rasterUnitsPerPixelY()), self._gv.isBatch)
        self._gv.topo.dx = demLayer.rasterUnitsPerPixelX() * self._gv.horizontalFactor
        self._gv.topo.dy = demLayer.rasterUnitsPerPixelY() * self._gv.horizontalFactor
        self._dlg.sizeEdit.setText('{0} x {1}'.format(locale.format_string('%.4G', self._gv.topo.dx), locale.format_string('%.4G', self._gv.topo.dy)))
        self._dlg.sizeEdit.setReadOnly(True)
        self.setAreaOfCell()
        areaM2 = float(self._gv.topo.dx * self._gv.topo.dy) / 1E4
        self._dlg.areaEdit.setText(locale.format_string('%.4G', areaM2))
        self._dlg.areaEdit.setReadOnly(True)
        self._gv.topo.demExtent = demLayer.extent()
        north = self._gv.topo.demExtent.yMaximum()
        south = self._gv.topo.demExtent.yMinimum()
        east = self._gv.topo.demExtent.xMaximum()
        west = self._gv.topo.demExtent.xMinimum()
        topLeft = self._gv.topo.pointToLatLong(QgsPointXY(west, north))
        bottomRight = self._gv.topo.pointToLatLong(QgsPointXY(east, south))
        northll = topLeft.y()
        southll = bottomRight.y()
        eastll = bottomRight.x()
        westll = topLeft.x()
        self._dlg.northEdit.setText(self.degreeString(northll))
        self._dlg.southEdit.setText(self.degreeString(southll))
        self._dlg.eastEdit.setText(self.degreeString(eastll))
        self._dlg.westEdit.setText(self.degreeString(westll))
        return True
    
    @staticmethod
    def degreeString(decDeg: float) -> str:
        """Generate string showing degrees as decimal and as degrees minuts seconds."""
        deg = int(decDeg)
        decMin = abs(decDeg - deg) * 60
        minn = int(decMin)
        sec = int((decMin - minn) * 60)
        return '{0}{1} ({2!s}{1} {3!s}\' {4!s}")'.format(locale.format_string('%.2F', decDeg), chr(176), deg, minn, sec)
            
    def setAreaOfCell(self) -> None:
        """Set area of 1 cell according to area units choice."""
        areaSqM = float(self._gv.topo.dx * self._gv.topo.dy)
        self._gv.cellArea = areaSqM
        if self._dlg.areaUnitsBox.currentText() == Parameters._SQKM:
            self.areaOfCell = areaSqM / 1E6 
        elif self._dlg.areaUnitsBox.currentText() == Parameters._HECTARES:
            self.areaOfCell = areaSqM / 1E4
        elif self._dlg.areaUnitsBox.currentText() == Parameters._SQMETRES:
            self.areaOfCell = areaSqM
        elif self._dlg.areaUnitsBox.currentText() == Parameters._SQMILES:
            self.areaOfCell = areaSqM / Parameters._SQMILESTOSQMETRES
        elif self._dlg.areaUnitsBox.currentText() == Parameters._ACRES:
            self.areaOfCell = areaSqM / Parameters._ACRESTOSQMETRES
        elif self._dlg.areaUnitsBox.currentText() == Parameters._SQFEET:
            self.areaOfCell = areaSqM * Parameters._SQMETRESTOSQFEET
            
    def changeAreaOfCell(self) -> None:
        """Set area of cell and update channel and stream unit area thresholds."""
        self.setAreaOfCell()
        if not self._gv.useGridModel:
            self.setAreaCh()
        self.setAreaSt()
        
    def setVerticalUnits(self) -> None:
        """Sets vertical units from combo box; sets corresponding factor to apply to elevations."""
        self._gv.verticalUnits = self._dlg.verticalCombo.currentText()
        self._gv.setVerticalFactor()

    def setAreaCh(self) -> None:
        """Update channel area threshold display.  Not used with grid models."""
        if self.changing: return
        try:
            numCells = int(self._dlg.numCellsCh.text())
        except Exception:
            # not currently parsable - ignore
            return
        area = numCells * self.areaOfCell
        self.changing = True
        self._dlg.areaCh.setText(locale.format_string('%.4G', area))
        self.changing = False
        self.thresholdChanged = True

    def setAreaSt(self) -> None:
        """Update stream area threshold display."""
        if self.changing: return
        try:
            numCells = int(self._dlg.numCellsSt.text())
        except Exception:
            # not currently parsable - ignore
            return
        area = numCells * self.areaOfCell
        self.changing = True
        self._dlg.areaSt.setText(locale.format_string('%.4G', area))
        self.changing = False
        self.thresholdChanged = True
            
    def setNumCellsCh(self) -> None:
        """Update number of channel cells threshold display.  Not used with grid models."""
        if self.changing: return
        # prevent division by zero
        if self.areaOfCell == 0: return
        try:
            area = locale.atof(self._dlg.areaCh.text())
        except Exception:
            # not currently parsable - ignore
            return
        numCells = int(area / self.areaOfCell)
        self.changing = True
        self._dlg.numCellsCh.setText(str(numCells))
        self.changing = False
        self.thresholdChanged = True
            
    def setNumCellsSt(self) -> None:
        """Update number of stream cells threshold display."""
        if self.changing: return
        # prevent division by zero
        if self.areaOfCell == 0: return
        try:
            area = locale.atof(self._dlg.areaSt.text())
        except Exception:
            # not currently parsable - ignore
            return
        numCells = int(area / self.areaOfCell)
        self.changing = True
        self._dlg.numCellsSt.setText(str(numCells))
        self.changing = False
        self.thresholdChanged = True
        
    def changeBurn(self) -> None:
        """Make burn option available or not according to check box state."""
        if self._dlg.checkBurn.isChecked():
            self._dlg.selectBurn.setEnabled(True)
            self._dlg.burnButton.setEnabled(True)
            if self._dlg.selectBurn.text() != '':
                self._gv.burnFile = self._dlg.selectBurn.text()
        else:
            self._dlg.selectBurn.setEnabled(False)
            self._dlg.burnButton.setEnabled(False)
            self._gv.burnFile = ''
            
    def changeUseGrid(self) -> None:
        """Change use grid setting according to check box state."""
        if self._dlg.tabWidget.currentIndex() == 0:
            self._gv.useGridModel = self._dlg.gridBox.isChecked()
        elif self._dlg.tabWidget.currentIndex() == 1:
            self._gv.useGridModel = self._dlg.useGrid.isChecked()
        # set both check boxes the same
        self._dlg.gridBox.setChecked(self._gv.useGridModel)
        self._dlg.useGrid.setChecked(self._gv.useGridModel)
        subbasinsText = 'Grid shapefile' if self._gv.useGridModel else 'Subbasins shapefile'
        self._dlg.selectSubbasinsLabel.setText(subbasinsText)
        self._dlg.selectWshedLabel.setVisible(not self._gv.useGridModel)
        self._dlg.selectWshed.setVisible(not self._gv.useGridModel)
        self._dlg.selectWshedButton.setVisible(not self._gv.useGridModel)
        self._dlg.drainGroupBox.setVisible(self._gv.useGridModel)
        self._dlg.thresholdLabelCh.setVisible(not self._gv.useGridModel)
        self._dlg.numCellsCh.setVisible(not self._gv.useGridModel)
        self._dlg.numCellsLabelCh.setVisible(not self._gv.useGridModel)
        self._dlg.areaCh.setVisible(not self._gv.useGridModel)
        self._dlg.areaLabelCh.setVisible(not self._gv.useGridModel)
        self._dlg.lakeIdCombo.setVisible(self._gv.useGridModel)
        self._dlg.lakeIdLabel.setVisible(self._gv.useGridModel)
        self._dlg.addLakeCells.setVisible(self._gv.useGridModel)
        self._dlg.removeLakeCells.setVisible(self._gv.useGridModel)
        self.setDrainage()
        self.setMergeResGroups()
            
    def setDrainage(self) -> None:
        """Update form according to drainage option."""
        if self._dlg.tabWidget.currentIndex() == 0:
            self.streamDrainage = True
            return
        if self._dlg.useGrid.isChecked():
            if self._dlg.drainGridButton.isChecked():
                self.gridDrainage = True
                self.streamDrainage = False
                self._dlg.selectStreams.setVisible(False)
                self._dlg.selectStreamsLabel.setVisible(False)
                self._dlg.selectStreamsButton.setVisible(False)
            else:
                self.gridDrainage = False
                self._dlg.selectStreams.setVisible(True)
                self._dlg.selectStreamsLabel.setVisible(True)
                self._dlg.selectStreamsButton.setVisible(True)
                if self._dlg.drainTableButton.isChecked():
                    self._dlg.selectStreams.setText(self.drainageTable)
                    self.streamDrainage = False
                    self._dlg.selectStreamsLabel.setText('Drainage table')
                else:
                    self._dlg.selectStreams.setText(self._gv.streamFile)
                    self.streamDrainage = True
                    self._dlg.selectStreamsLabel.setText('Streams shapefile')
        else:
            self._dlg.selectStreams.setVisible(True)
            self._dlg.selectStreamsLabel.setVisible(True)
            self._dlg.selectStreamsButton.setVisible(True)
            self._dlg.selectStreamsLabel.setText('Channels shapefile')
        
        
    def changeUseOutlets(self) -> None:
        """Make outlets option available or not according to check box state."""
        if self._dlg.useOutlets.isChecked():
            self._dlg.outletsWidget.setEnabled(True)
            self._dlg.selectOutlets.setEnabled(True)
            self._dlg.selectOutletsButton.setEnabled(True)
            if self._dlg.selectOutlets.text() != '':
                self._gv.outletFile = self._dlg.selectOutlets.text()
        else:
            self._dlg.outletsWidget.setEnabled(False)
            self._dlg.selectOutlets.setEnabled(False)
            self._dlg.selectOutletsButton.setEnabled(False)
            self._gv.outletFile = ''
        self.thresholdChanged = True
            
    def drawOutlets(self) -> None:
        """Allow user to create inlets/outlets in current shapefile 
        or a new one.
        """
        self._odlg.widget.setEnabled(True)
        canvas: QgsMapCanvas = self._gv.iface.mapCanvas()
        self.mapTool = QgsMapToolEmitPoint(canvas)
        assert self.mapTool is not None
        self.mapTool.canvasClicked.connect(self.getPoint)
        canvas.setMapTool(self.mapTool)
        # detect maptool change
        canvas.mapToolSet.connect(self.mapToolChanged)
        root = QgsProject.instance().layerTreeRoot()
        outletLayer = QSWATUtils.getLayerByFilenameOrLegend(root.findLayers(), self._gv.outletFile, FileTypes._OUTLETS, '', self._gv.isBatch)
        if outletLayer is not None:  # we have a current outlet layer - give user a choice 
            msgBox = QMessageBox()
            msgBox.move(self._gv.selectOutletFilePos)
            msgBox.setWindowTitle('Select inlets/outlets file to draw on')
            text = """
            Select "Current" if you wish to draw new points in the 
            existing inlets/outlets layer, which is
            {0}.
            Select "New" if you wish to make a new inlets/outlets file.
            Select "Cancel" to abandon drawing.
            """.format(self._gv.outletFile)
            msgBox.setText(QSWATUtils.trans(text))
            currentButton = msgBox.addButton(QSWATUtils.trans('Current'), QMessageBox.ActionRole)
            _ = msgBox.addButton(QSWATUtils.trans('New'), QMessageBox.ActionRole)
            msgBox.setStandardButtons(QMessageBox.Cancel)
            result = msgBox.exec_()
            self._gv.selectOutletFilePos = msgBox.pos()
            if result == QMessageBox.Cancel:
                return
            drawCurrent = msgBox.clickedButton() == currentButton
        else:
            drawCurrent = False
        if drawCurrent:
            if not self._gv.iface.setActiveLayer(outletLayer):
                QSWATUtils.error('Could not make inlets/outlets layer active', self._gv.isBatch)
                return
            self.drawOutletLayer = outletLayer
            assert self.drawOutletLayer is not None
            self.drawOutletLayer.startEditing()
        else:
            drawOutletFile = QSWATUtils.join(self._gv.shapesDir, 'drawoutlets.shp')
            # our outlet file may already be called drawoutlets.shp
            if QSWATUtils.samePath(drawOutletFile, self._gv.outletFile):
                drawOutletFile = QSWATUtils.join(self._gv.shapesDir, 'drawoutlets1.shp')
            if not Delineation.createOutletFile(drawOutletFile, self._gv.demFile, False, root, self._gv):
                return
            self.drawOutletLayer, _ = QSWATUtils.getLayerByFilename(root.findLayers(),
                                                                          drawOutletFile, FileTypes._OUTLETS, self._gv,
                                                                          None, QSWATUtils._WATERSHED_GROUP_NAME)
            if self.drawOutletLayer is None:
                QSWATUtils.error('Unable to load shapefile {0}'.format(drawOutletFile), self._gv.isBatch)
                return
            if not self._gv.iface.setActiveLayer(self.drawOutletLayer):
                QSWATUtils.error('Could not make drawing inlets/outlets layer active', self._gv.isBatch)
                return
            self.drawOutletLayer.startEditing()
        self._dlg.lower()
        self._odlg.show()
        result = self._odlg.exec_()
        self._gv.outletsPos = self._odlg.pos()
        self._dlg.raise_()
        canvas.setMapTool(None)  # type: ignore
        if result == 1:
            self.thresholdChanged = True
            # points added by drawing will have ids of -1, so fix them
            self.fixPointIds()
            if not drawCurrent:
                self._gv.outletFile = drawOutletFile
                self._dlg.selectOutlets.setText(drawOutletFile)
        else:
            if drawCurrent:
                self.drawOutletLayer.rollBack()
            else:
                # cancel - destroy drawn shapefile
                QSWATUtils.tryRemoveLayerAndFiles(drawOutletFile, root)
           
    def mapToolChanged(self, tool: QgsMapTool) -> None:  # @UndefinedVariable
        """Disable choice of point to be added to show users they must resume adding,
        unless changing to self.mapTool."""
        self._odlg.widget.setEnabled(tool == self.mapTool)
                
    def resumeDrawing(self) -> None:
        """Reset canvas' mapTool."""
        self._odlg.widget.setEnabled(True)
        self._gv.iface.setActiveLayer(self.drawOutletLayer)
        canvas = self._gv.iface.mapCanvas()
        canvas.setMapTool(self.mapTool)

    # noinspection PyCallByClass,PyCallByClass
    def getPoint(self, point: QgsPointXY, button: Any) -> None:  # @UnusedVariable button
        """Add point to drawOutletLayer."""
        isInlet = self._odlg.inletButton.isChecked() or self._odlg.ptsourceButton.isChecked()
        # can't use feature count as they can't be counted until adding is confirmed
        # so set to -1 and fix them later
        pid = -1
        inlet = 1 if isInlet else 0
        # use 2 for pond, 1 for reservoir, 0 for neither
        res = 2 if self._odlg.pondButton.isChecked() else 1 if self._odlg.reservoirButton.isChecked() else 0
        ptsource = 1 if self._odlg.ptsourceButton.isChecked() else 0
        idIndex = self._gv.topo.getIndex(self.drawOutletLayer, QSWATTopology._ID)
        inletIndex = self._gv.topo.getIndex(self.drawOutletLayer, QSWATTopology._INLET)
        resIndex = self._gv.topo.getIndex(self.drawOutletLayer, QSWATTopology._RES)
        ptsourceIndex = self._gv.topo.getIndex(self.drawOutletLayer, QSWATTopology._PTSOURCE)
        feature = QgsFeature()
        assert self.drawOutletLayer is not None
        fields = self.drawOutletLayer.dataProvider().fields()
        feature.setFields(fields)
        feature.setAttribute(idIndex, pid)
        feature.setAttribute(inletIndex, inlet)
        feature.setAttribute(resIndex, res)
        feature.setAttribute(ptsourceIndex, ptsource)
        # noinspection PyCallByClass
        feature.setGeometry(QgsGeometry.fromPointXY(point))
        self.drawOutletLayer.addFeature(feature)
        self.drawOutletLayer.triggerRepaint()
        # clicking on map may have hidden the dialog, so make it top
        self._odlg.raise_()
        
    def fixPointIds(self) -> None:
        """Give suitable point ids to drawn points."""
        assert self.drawOutletLayer is not None
        # need to commit first or appear to be no features
        self.drawOutletLayer.commitChanges()
        idIndex = self._gv.topo.getIndex(self.drawOutletLayer, QSWATTopology._ID)
        ptIdIndex = self._gv.topo.getIndex(self.drawOutletLayer, QSWATTopology._POINTID, ignoreMissing=True)
        if ptIdIndex < 0:
            ptIdIndex = QSWATTopology.makePositiveOutletIds(self.drawOutletLayer)
            if ptIdIndex < 0:
                QSWATUtils.error('Failed to add PointId field to inlets/outlets file {0}'.format(QSWATUtils.layerFilename(self.drawOutletLayer)), self._gv.isBatch)
                return
        # start editing again
        self.drawOutletLayer.startEditing()
        # find maximum existing feature id
        maxId = 0
        for feature in self.drawOutletLayer.getFeatures():
            maxId = max(maxId, feature[idIndex])
        # replace negative feature ids
        for feature in self.drawOutletLayer.getFeatures():
            pid = feature[idIndex]
            if pid < 0:
                maxId += 1
                self.drawOutletLayer.changeAttributeValue(feature.id(), idIndex, maxId)
                self.drawOutletLayer.changeAttributeValue(feature.id(), ptIdIndex, maxId)
        self.drawOutletLayer.commitChanges()
                
    def selectOutlets(self) -> None:
        """Allow user to select points in inlets/outlets layer."""
        root = QgsProject.instance().layerTreeRoot()
        selFromLayer = None
        layer = self._gv.iface.activeLayer()
        if layer is not None:
            if 'inlets/outlets' in layer.name():
                #if layer.name().startswith(QSWATUtils._SELECTEDLEGEND):
                #    QSWATUtils.error(u'You cannot select from a selected inlets/outlets layer', self._gv.isBatch)
                #    return
                selFromLayer = layer
        if not selFromLayer:
            selFromLayer = QSWATUtils.getLayerByFilenameOrLegend(root.findLayers(), self._gv.outletFile, FileTypes._OUTLETS, '', self._gv.isBatch)
            if not selFromLayer:
                QSWATUtils.error('Cannot find inlets/outlets layer.  Please choose the layer you want to select from in the layers panel.', self._gv.isBatch)
                return
        if not self._gv.iface.setActiveLayer(selFromLayer):
            QSWATUtils.error('Could not make inlets/outlets layer active', self._gv.isBatch)
            return
        self._gv.iface.actionSelectRectangle().trigger()
        msgBox = QMessageBox()
        msgBox.move(self._gv.selectOutletPos)
        msgBox.setWindowTitle('Select inlets/outlets')
        text = """
        Hold Ctrl and select the points by clicking on them.
        Selected points will turn yellow, and a count is shown 
        at the bottom left of the main window.
        If you want to start again release Ctrl and click somewhere
        away from any points; then hold Ctrl and resume selection.
        You can pause in the selection to pan or zoom provided 
        you hold Ctrl again when you resume selection.
        When finished click "Save" to save your selection, 
        or "Cancel" to abandon the selection.
        """
        msgBox.setText(QSWATUtils.trans(text))
        msgBox.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)  # type: ignore
        msgBox.setWindowModality(Qt.NonModal)
        self._dlg.lower()
        msgBox.show()
        result = msgBox.exec_()
        self._gv.selectOutletPos = msgBox.pos()
        self._dlg.raise_()
        if result != QMessageBox.Save:
            selFromLayer.removeSelection()
            return
        selectedIds = selFromLayer.selectedFeatureIds()
        # QSWATUtils.information('Selected feature ids: {0!s}'.format(selectedIds), self._gv.isBatch)
        selFromLayer.removeSelection()
        # make a copy of selected layer's file, then remove non-selected features from it
        info = QSWATUtils.layerFileInfo(selFromLayer)
        baseName = info.baseName()
        path = info.absolutePath()
        pattern = QSWATUtils.join(path, baseName) + '.*'
        for f in glob.iglob(pattern):
            base, suffix = os.path.splitext(f)
            target = base + '_sel' + suffix
            shutil.copyfile(f, target)
            if suffix == '.shp':
                self._gv.outletFile = target
        assert os.path.exists(self._gv.outletFile) and self._gv.outletFile.endswith('_sel.shp')
        # make old outlet layer invisible
        root = QgsProject.instance().layerTreeRoot()
        QSWATUtils.setLayerVisibility(selFromLayer, False, root)
        # remove any existing selected layer
        QSWATUtils.removeLayerByLegend(QSWATUtils._SELECTEDLEGEND, root.findLayers())
        # load new outletFile
        selOutletLayer, loaded = QSWATUtils.getLayerByFilename(root.findLayers(), self._gv.outletFile, FileTypes._OUTLETS,
                                                               self._gv, None, QSWATUtils._WATERSHED_GROUP_NAME)
        if not selOutletLayer or not loaded:
            QSWATUtils.error('Could not load selected inlets/outlets shapefile {0}'.format(self._gv.outletFile), 
                             self._gv.isBatch)
            return
        # remove non-selected features
        featuresToDelete = []
        for feature in selOutletLayer.getFeatures():
            fid = feature.id()
            if not fid in selectedIds:
                featuresToDelete.append(fid)
        # QSWATUtils.information('Non-selected feature ids: {0!s}'.format(featuresToDelete), self._gv.isBatch)
        selOutletLayer.dataProvider().deleteFeatures(featuresToDelete)
        selOutletLayer.triggerRepaint()
        self._dlg.selectOutlets.setText(self._gv.outletFile)
        self.thresholdChanged = True
        self._dlg.selectOutletsInteractiveLabel.setText('{0!s} selected'.format(len(selectedIds)))
        self._gv.snapFile = ''
        self._dlg.snappedLabel.setText('')

    def addLakesMap(self) -> None:
        """Allow user to select lakes shapefile."""
        root = QgsProject.instance().layerTreeRoot()
        # place above channels layer
        channelsLayer = QSWATUtils.getLayerByLegend(QSWATUtils._CHANNELSLEGEND, root.findLayers())
        if channelsLayer is not None:
            subLayer = channelsLayer
        else:
            streamsLayer = QSWATUtils.getLayerByLegend(QSWATUtils._STREAMSLEGEND, root.findLayers())
            if streamsLayer is not None:
                subLayer = streamsLayer
            else:
                subLayer = None
        (lakeFile, lakesLayer) = QSWATUtils.openAndLoadFile(root, FileTypes._LAKES, self._dlg.selectLakes, self._gv.shapesDir, 
                                                           self._gv, subLayer, QSWATUtils._WATERSHED_GROUP_NAME, runFix=True)
        if lakeFile and lakesLayer:
            lakesLayer.setLabelsEnabled(False)
            self._gv.lakeFile = lakeFile
            self.lakesDone = False
            self.lakePointsAdded = False
            if self._gv.useGridModel:
                self.gridLakesAdded = False
                ft = FileTypes._GRID
                gridLayer = QSWATUtils.getLayerByFilenameOrLegend(root.findLayers(), self._gv.subbasinsFile, ft, FileTypes.legend(ft), self._gv.isBatch)
                if gridLayer is None:
                    QSWATUtils.error('Cannot find grid layer for {0}'.format(self._gv.subbasinsFile))
                    return
                self.progress('Making grid lakes ...')
                self.makeGridLakes(lakesLayer, gridLayer)
                self.progress('')
                
    def removeLakeCells(self) -> None:
        """Allow user to remove cells from lake."""
        root = QgsProject.instance().layerTreeRoot()
        layers = root.findLayers()
        ft = FileTypes._GRID
        gridLayer = QSWATUtils.getLayerByFilenameOrLegend(layers, self._gv.subbasinsFile, ft, FileTypes.legend(ft), self._gv.isBatch)
        if gridLayer is None:
            QSWATUtils.error('Cannot find the grid layer', self._gv.isBatch)
            return
        if not self.gridLakesAdded:
            if not os.path.exists(self._gv.lakeFile):
                QSWATUtils.error('Cannot find lakes file {0}'.format(self._gv.lakeFile), self._gv.isBatch)
                return
            lakesLayer = QSWATUtils.getLayerByFilename(layers, self._gv.lakeFile, FileTypes._LAKES, None, None, None)[0]
            if lakesLayer is None:
                QSWATUtils.error('Lakes layer not found.', self._gv.isBatch)
                return
            self.progress('Making grid lakes ...')
            self.makeGridLakes(lakesLayer, gridLayer)
            self.progress('')
        self._gv.iface.setActiveLayer(gridLayer)
        self._gv.iface.actionSelect().trigger()
        msgBox = QMessageBox()
        msgBox.move(self._gv.selectOutletPos)
        msgBox.setWindowTitle('Select cells to remove from lake')
        text = """
Hold Ctrl and click on the cells you want to remove from the lake.
You can clear and start again by clicking outside the lake.  
Then click 'Ok'to confirm your selection or 'Cancel' to clear 
the selection and do nothing.
You can repeat the selection and change as many times as you like.  
If you want to start again from scratch, reload the lakes shapefile."""
        msgBox.setText(QSWATUtils.trans(text))
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)  # type: ignore
        msgBox.setWindowModality(Qt.NonModal)
        self._dlg.showMinimized()
        msgBox.show()
        result = msgBox.exec_()
        self._gv.selectOutletPos = msgBox.pos()
        self._dlg.showNormal()
        if result == QMessageBox.Ok:
            lakeIdIndex = self._gv.topo.getIndex(gridLayer, QSWATTopology._LAKEID)
            mmap = dict()
            for cell in gridLayer.selectedFeatures():
                mmap[cell.id()] = {lakeIdIndex: NULL}
            if not gridLayer.dataProvider().changeAttributeValues(mmap):
                QSWATUtils.error('Failed to edit grid layer', self._gv.isBatch)
        gridLayer.removeSelection()
        gridLayer.triggerRepaint()
        streamsLayer = QSWATUtils.getLayerByFilename(layers, self._gv.streamFile, ft, None, None, None)[0]
        if streamsLayer is None:
            QSWATUtils.error('Cannot find the streams layer', self._gv.isBatch)
            return
        demLayer = QSWATUtils.getLayerByFilename(layers, self._gv.demFile, FileTypes._DEM, None, None, None)[0]
        if demLayer is None:
            QSWATUtils.error('DEM layer not found.', self._gv.isBatch)
            return
        self._gv.topo.addGridReservoirsPondsAndWetlands(gridLayer, streamsLayer, demLayer, self._gv)
            
    def addLakeCells(self) -> None:
        """Allow user to add cells to lake."""
        root = QgsProject.instance().layerTreeRoot()
        layers = root.findLayers()
        ft = FileTypes._GRID
        gridLayer = QSWATUtils.getLayerByFilenameOrLegend(layers, self._gv.subbasinsFile, ft, FileTypes.legend(ft), self._gv.isBatch)
        if gridLayer is None:
            QSWATUtils.error('Cannot find the grid layer', self._gv.isBatch)
            return
        if not os.path.exists(self._gv.lakeFile):
            QSWATUtils.error('Cannot find lakes file {0}'.format(self._gv.lakeFile), self._gv.isBatch)
            return
        lakesLayer = QSWATUtils.getLayerByFilename(layers, self._gv.lakeFile, FileTypes._LAKES, None, None, None)[0]
        if lakesLayer is None:
            QSWATUtils.error('Lakes layer not found.', self._gv.isBatch)
            return
        if not self.gridLakesAdded:
            self.progress('Making grid lakes ...')
            self.makeGridLakes(lakesLayer, gridLayer)
            self.progress('')
        lakeId = int(self._dlg.lakeIdCombo.currentText())
        self._gv.iface.setActiveLayer(gridLayer)
        self._gv.iface.actionSelect().trigger()
        msgBox = QMessageBox()
        msgBox.move(self._gv.selectOutletPos)
        msgBox.setWindowTitle('Select cells to add to lake')
        text = """
First make sure the Lake number box shows the number of the lake 
you want to add to.
Hold Ctrl and click on the cells you want to add to the lake.
You can clear and start again by clicking outside the watershed.  
Then click 'Ok'to confirm your selection or 'Cancel' to clear 
the selection and do nothing.
You can repeat the selection and change as many times as you like.  
If you want to start again from scratch, reload the lakes shapefile."""
        msgBox.setText(QSWATUtils.trans(text))
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)  # type: ignore
        msgBox.setWindowModality(Qt.NonModal)
        self._dlg.showMinimized()
        msgBox.show()
        result = msgBox.exec_()
        self._gv.selectOutletPos = msgBox.pos()
        self._dlg.showNormal()
        if result == QMessageBox.Ok:
            lakeIdIndex = self._gv.topo.getIndex(gridLayer, QSWATTopology._LAKEID)
            mmap = dict()
            for cell in gridLayer.selectedFeatures():
                mmap[cell.id()] = {lakeIdIndex: lakeId}
            if not gridLayer.dataProvider().changeAttributeValues(mmap):
                QSWATUtils.error('Failed to edit grid layer', self._gv.isBatch)
        gridLayer.removeSelection()
        gridLayer.triggerRepaint()
        streamsLayer = QSWATUtils.getLayerByFilename(layers, self._gv.streamFile, ft, None, None, None)[0]
        if streamsLayer is None:
            QSWATUtils.error('Cannot find the streams layer', self._gv.isBatch)
            return
        demLayer = QSWATUtils.getLayerByFilename(layers, self._gv.demFile, FileTypes._DEM, None, None, None)[0]
        if demLayer is None:
            QSWATUtils.error('DEM layer not found.', self._gv.isBatch)
            return
        self._gv.topo.addGridReservoirsPondsAnsWetlands(gridLayer, streamsLayer, demLayer, self._gv)
        
#=======not used========================================================================
#     def addPointSources(self):
#         """Create extra inlets/outlets shapefile 
#         with point sources at source of every channel.
#         """
#         li = self._gv.iface.legendInterface()
# #         ft = FileTypes._EXISTINGSUBBASINS if self._gv.existingWshed else \
# #         FileTypes._GRID if self._gv.useGridModel else FileTypes._SUBBASINS
# #         subbasinsLayer = QSWATUtils.getLayerByFilenameOrLegend(li.layers(), self._gv.subbasinsFile, ft, '', self._gv.isBatch)
# #         if not subbasinsLayer:
# #             QSWATUtils.error(u'Cannot find subbasins layer', self._gv.isBatch)
# #             return
# #         subbasinsLayer.removeSelection()
#         channelLayer = QSWATUtils.getLayerByFilenameOrLegend(li.layers(), self._gv.channelFile, FileTypes._CHANNELS, '', self._gv.isBatch)
#         if not channelLayer:
#             QSWATUtils.error(u'Cannot find channels layer', self._gv.isBatch)
#             return
#         linkIndex = self._gv.topo.getIndex(channelLayer, QSWATTopology._LINKNO)
#         basinNoIndex = self._gv.topo.getIndex(channelLayer, QSWATTopology._BASINNO)
# #         reservoirIds = self.getOutletIds(QSWATTopology._RES)
# #         ptsourceIds = self.getOutletIds(QSWATTopology._PTSOURCE)
#         # QSWATUtils.information('Point source ids are {0}'.format(ptsourceIds), self._gv.isBatch)
# #         extraReservoirLinks = set()
# #         for channel in channelLayer.getFeatures():
# #             if channel[wsnoIndex] in self.extraReservoirBasins:  # TODO:
# #                 if nodeidIndex >= 0:
# #                     nodeid = channel[nodeidIndex]
# #                     if nodeid in reservoirIds:
# #                         continue  # already has a reservoir
# #                 extraReservoirLinks.add(channel[linkIndex])
#         extraOutletFile = QSWATUtils.join(self._gv.shapesDir, 'extra.shp')
#         QSWATUtils.tryRemoveLayerAndFiles(extraOutletFile, li)
#         if not self.createOutletFile(extraOutletFile, self._gv.demFile, True):
#             return
#         self._dlg.setCursor(Qt.WaitCursor)
#         extraOutletLayer = QgsVectorLayer(extraOutletFile, 'Extra inlets/outlets ({0})'.format(extraOutletFile), 'ogr')
#         idIndex = self._gv.topo.getIndex(extraOutletLayer, QSWATTopology._ID)
#         inletIndex = self._gv.topo.getIndex(extraOutletLayer, QSWATTopology._INLET)
#         resIndex = self._gv.topo.getIndex(extraOutletLayer, QSWATTopology._RES)
#         ptsourceIndex = self._gv.topo.getIndex(extraOutletLayer, QSWATTopology._PTSOURCE)
#         basinIndex = self._gv.topo.getIndex(extraOutletLayer, QSWATTopology._SUBBASIN)
#         self._gv.writeProjectConfig(0,0)
#         pid = 0
#         for reach in channelLayer.getFeatures():
#             link = reach[linkIndex]
#             data = self._gv.topo.channelsData[link]
#             point = QgsPoint(data.upperX, data.upperY)  # point source placed at source of channel
#             basin = reach[basinNoIndex]
#             feature = QgsFeature()
#             fields = extraOutletLayer.dataProvider().fields()
#             feature.setFields(fields)
#             feature.setAttribute(idIndex, pid)
#             pid += 1
#             feature.setAttribute(inletIndex, 1)
#             feature.setAttribute(resIndex, 0)
#             feature.setAttribute(ptsourceIndex, 1)
#             feature.setAttribute(basinIndex, basin)
#             feature.setGeometry(QgsGeometry.fromPoint(point))
#             extraOutletLayer.dataProvider().addFeatures([feature])
#         if pid > 0:
#             extraOutletLayer, loaded = QSWATUtils.getLayerByFilename(li.layers(), extraOutletFile, FileTypes._OUTLETS, self._gv, True)
#             if not (extraOutletLayer and loaded):
#                 QSWATUtils.error(u'Could not load extra outlets/inlets file {0}'.format(extraOutletFile), self._gv.isBatch)
#                 return
#             li.moveLayer(extraOutletLayer, self._gv.watershedGroupIndex)
#             self._gv.extraOutletFile = extraOutletFile
#         else:
#             # no extra reservoirs, inlets or point sources - clean up
#             # first release resources, else .dbf file in use stops deletion of files
#             extraOutletLayer = None
#             QSWATUtils.tryRemoveLayerAndFiles(extraOutletFile, li)
#             self._gv.extraOutletFile = ''
#         self._dlg.setCursor(Qt.ArrowCursor)
#===============================================================================
        
    #======= not used ====================================================================
    # def removeUpstreamCells(self, reach, startBasin, subbasinsLayer, streamLayer, wsnoIndex):
    #     """Remove grid cells and stream reaches upstream from basin."""
    #     basinIndex = self._gv.topo.getIndex(subbasinsLayer, QSWATTopology._POLYGONID)
    #     downIndex = self._gv.topo.getIndex(subbasinsLayer, QSWATTopology._DOWNID)
    #     provider = streamLayer.dataProvider()
    #     gridIdsToRemove = []
    #     upstreamBasins = set([startBasin])
    #     downBasin = 0
    #     count = 0
    #     numFeatures = subbasinsLayer.featureCount()
    #     time1 = time.process_time()
    #     changing = True
    #     firstLoop = True
    #     request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([basinIndex, downIndex])
    #     while changing:
    #         changing = False
    #         for f in subbasinsLayer.getFeatures(request):
    #             basin = f[basinIndex]
    #             if firstLoop and basin == startBasin:
    #                 firstLoop = False
    #                 gridIdsToRemove.append(f.id())
    #                 downBasin = f[downIndex]
    #                 # mark the downlink's basin as -1 to show it has no corresponding basin
    #                 mmap = dict()
    #                 mmap2 = dict()
    #                 mmap2[wsnoIndex] = -1
    #                 mmap[f.id()] = mmap2
    #                 OK = provider.changeAttributeValues(mmap)
    #                 if not OK:
    #                     QSWATUtils.error(u'Cannot edit values in grid streams layer', self.isBatch)
    #             elif f[downIndex] in upstreamBasins and basin not in upstreamBasins:
    #                 upstreamBasins.add(basin)
    #                 gridIdsToRemove.append(f.id())
    #                 count += 1
    #                 assert count < numFeatures, u'Loop in calculating cells upstream from inlet' 
    #                 changing = True
    #     if count > 0:
    #         upstreamBasins.discard(startBasin)
    #         streamIdsToRemove = []
    #         request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([wsnoIndex])
    #         for reach in streamLayer.getFeatures(request):
    #             if reach[wsnoIndex] in upstreamBasins:
    #                 streamIdsToRemove.append(reach.id())
    #         provider.deleteFeatures(streamIdsToRemove)
    #         provider = subbasinsLayer.dataProvider()
    #         provider.deleteFeatures(gridIdsToRemove)
    #     time2 = time.process_time()
    #     QSWATUtils.loginfo('Removing upstream grid cells took {0} seconds'.format(int(time2 - time1)))
    #     return downBasin        
    #===========================================================================
            
    def snapReview(self) -> None:
        """Load snapped inlets/outlets points."""
        root = QgsProject.instance().layerTreeRoot()
        outletLayer = QSWATUtils.getLayerByFilenameOrLegend(root.findLayers(), self._gv.outletFile,
                                                            FileTypes._OUTLETS, '', self._gv.isBatch)
        if not outletLayer:
            QSWATUtils.error('Cannot find inlets/outlets layer', self._gv.isBatch)
            return
        if self._gv.snapFile == '' or self.snapErrors:
            streamLayer = QSWATUtils.getLayerByFilenameOrLegend(root.findLayers(), self._gv.streamFile, 
                                                                FileTypes._STREAMS, '', self._gv.isBatch)
            if not streamLayer:
                QSWATUtils.error('Cannot find streams layer', self._gv.isBatch)
                return
            if self._gv.useGridModel:
                channelLayer = streamLayer
            else:
                channelLayer = QSWATUtils.getLayerByFilenameOrLegend(root.findLayers(), self._gv.channelFile, 
                                                                     FileTypes._CHANNELS, '', self._gv.isBatch)
                if not channelLayer:
                    QSWATUtils.error('Cannot find channels layer', self._gv.isBatch)
                    return
            outletBase = os.path.splitext(self._gv.outletFile)[0]
            snapFile = outletBase + '_snap.shp'
            if not self.createSnapOutletFile(outletLayer, streamLayer, channelLayer, self._gv.outletFile, snapFile, root):
                return
        # make old outlet layer invisible
        QSWATUtils.setLayerVisibility(outletLayer, False, root)
        # load snapped layer
        outletSnapLayer = QSWATUtils.getLayerByFilename(root.findLayers(), self._gv.snapFile, FileTypes._OUTLETS,
                                                        self._gv, None, QSWATUtils._WATERSHED_GROUP_NAME)[0]
        if not outletSnapLayer:  # don't worry about loaded flag as may already have the layer loaded
            QSWATUtils.error('Could not load snapped inlets/outlets shapefile {0}'.format(self._gv.snapFile), self._gv.isBatch)
            
    def selectMergeSubbasins(self) -> None:
        """Allow user to select subbasins to be merged."""
        root = QgsProject.instance().layerTreeRoot()
        ft = FileTypes._EXISTINGSUBBASINS if self._gv.existingWshed else FileTypes._SUBBASINS
        subbasinsLayer = QSWATUtils.getLayerByFilenameOrLegend(root.findLayers(), self._gv.subbasinsFile, ft, '', self._gv.isBatch)
        if not subbasinsLayer:
            QSWATUtils.error('Cannot find subbasins layer', self._gv.isBatch)
            return
        if not self._gv.iface.setActiveLayer(subbasinsLayer):
            QSWATUtils.error('Could not make subbasins layer active', self._gv.isBatch)
            return
        self._gv.iface.actionSelect().trigger()
        self._dlg.lower()
        selSubs = SelectSubbasins(self._gv, subbasinsLayer)
        selSubs.run()
        self._dlg.raise_()
        
    
    def mergeSubbasins(self) -> None:
        """Merged selected subbasin with its parent.  Not used with grid models."""
        self.delineationFinishedOK = False
        root = QgsProject.instance().layerTreeRoot()
        demLayer = QSWATUtils.getLayerByFilenameOrLegend(root.findLayers(), self._gv.demFile, FileTypes._DEM, '', self._gv.isBatch)
        if not demLayer:
            QSWATUtils.error('Cannot find DEM layer', self._gv.isBatch)
            return
        ft = FileTypes._EXISTINGSUBBASINS if self._gv.existingWshed else FileTypes._SUBBASINS
        subbasinsLayer = QSWATUtils.getLayerByFilenameOrLegend(root.findLayers(), self._gv.subbasinsFile, ft, '', self._gv.isBatch)
        if subbasinsLayer is None:
            QSWATUtils.error('Cannot find subbasins layer', self._gv.isBatch)
            return
        streamLayer = QSWATUtils.getLayerByFilenameOrLegend(root.findLayers(), self._gv.streamFile, FileTypes._STREAMS, '', self._gv.isBatch)
        if streamLayer is None:
            QSWATUtils.error('Cannot find streams layer', self._gv.isBatch)
            subbasinsLayer.removeSelection()
            return
        channelLayer = QSWATUtils.getLayerByFilenameOrLegend(root.findLayers(), self._gv.channelFile, FileTypes._CHANNELS, '', self._gv.isBatch)
        if channelLayer is None:
            QSWATUtils.error('Cannot find channels layer', self._gv.isBatch)
            subbasinsLayer.removeSelection()
            return
        selection = subbasinsLayer.selectedFeatures()
        if len(selection) == 0:
            QSWATUtils.information("Please select at least one subbasin to be merged", self._gv.isBatch)
            return
        outletLayer = QSWATUtils.getLayerByFilenameOrLegend(root.findLayers(), self._gv.outletFile, FileTypes._OUTLETS, '', self._gv.isBatch)
        
        polygonidField = self._gv.topo.getIndex(subbasinsLayer, QSWATTopology._POLYGONID)
        if polygonidField < 0:
            return
        areaField = self._gv.topo.getIndex(subbasinsLayer, Parameters._AREA, ignoreMissing=True)
        streamlinkField = self._gv.topo.getIndex(subbasinsLayer, QSWATTopology._STREAMLINK, ignoreMissing=True)
        streamlenField = self._gv.topo.getIndex(subbasinsLayer, QSWATTopology._STREAMLEN, ignoreMissing=True)
        dsnodeidwField = self._gv.topo.getIndex(subbasinsLayer, QSWATTopology._DSNODEIDW, ignoreMissing=True)
        dswsidField = self._gv.topo.getIndex(subbasinsLayer, QSWATTopology._DSWSID, ignoreMissing=True)
        us1wsidField = self._gv.topo.getIndex(subbasinsLayer, QSWATTopology._US1WSID, ignoreMissing=True)
        us2wsidField = self._gv.topo.getIndex(subbasinsLayer, QSWATTopology._US2WSID, ignoreMissing=True)
        subbasinField = self._gv.topo.getIndex(subbasinsLayer, QSWATTopology._SUBBASIN, ignoreMissing=True)
        linknoField = self._gv.topo.getIndex(streamLayer, QSWATTopology._LINKNO)
        if linknoField < 0:
            return
        dslinknoField = self._gv.topo.getIndex(streamLayer, QSWATTopology._DSLINKNO)
        if dslinknoField < 0:
            return
        uslinkno1Field = self._gv.topo.getIndex(streamLayer, QSWATTopology._USLINKNO1, ignoreMissing=True)
        uslinkno2Field = self._gv.topo.getIndex(streamLayer, QSWATTopology._USLINKNO2, ignoreMissing=True)
        dsnodeidnField = self._gv.topo.getIndex(streamLayer, QSWATTopology._DSNODEID, ignoreMissing=True)
        orderField = self._gv.topo.getIndex(streamLayer, QSWATTopology._ORDER, ignoreMissing=True)
        lengthField = self._gv.topo.getIndex(streamLayer, QSWATTopology._LENGTH, ignoreMissing=True)
        magnitudeField = self._gv.topo.getIndex(streamLayer, QSWATTopology._MAGNITUDE, ignoreMissing=True)
        ds_cont_arField = self._gv.topo.getIndex(streamLayer, QSWATTopology._DRAINAREA, ignoreMissing=True)
        if ds_cont_arField < 0:
            ds_cont_arField = self._gv.topo.getIndex(streamLayer, QSWATTopology._DRAINAREA2, ignoreMissing=True)
        dropField = self._gv.topo.getIndex(streamLayer, QSWATTopology._DROP, ignoreMissing=True)
        if dropField < 0:
            dropField = self._gv.topo.getIndex(streamLayer, QSWATTopology._DROP2, ignoreMissing=True)
        slopeField = self._gv.topo.getIndex(streamLayer, QSWATTopology._SLOPE, ignoreMissing=True)
        straight_lField = self._gv.topo.getIndex(streamLayer, QSWATTopology._STRAIGHTL, ignoreMissing=True)
        if straight_lField < 0:
            straight_lField = self._gv.topo.getIndex(streamLayer, QSWATTopology._STRAIGHTL2, ignoreMissing=True)
        us_cont_arField = self._gv.topo.getIndex(streamLayer, QSWATTopology._USCONTAR, ignoreMissing=True)
        if us_cont_arField < 0:
            us_cont_arField = self._gv.topo.getIndex(streamLayer, QSWATTopology._USCONTAR2, ignoreMissing=True)
        wsnoField = self._gv.topo.getIndex(streamLayer, QSWATTopology._WSNO)
        if wsnoField < 0:
            return
        dout_endField = self._gv.topo.getIndex(streamLayer, QSWATTopology._DOUTEND, ignoreMissing=True)
        if dout_endField < 0:
            dout_endField = self._gv.topo.getIndex(streamLayer, QSWATTopology._DOUTEND2, ignoreMissing=True)
        dout_startField = self._gv.topo.getIndex(streamLayer, QSWATTopology._DOUTSTART, ignoreMissing=True)
        if dout_startField < 0:
            dout_startField = self._gv.topo.getIndex(streamLayer, QSWATTopology._DOUTSTART2, ignoreMissing=True)
        dout_midField = self._gv.topo.getIndex(streamLayer, QSWATTopology._DOUTMID, ignoreMissing=True)
        if dout_midField < 0:
            dout_midField = self._gv.topo.getIndex(streamLayer, QSWATTopology._DOUTMID2, ignoreMissing=True)
        basinField = self._gv.topo.getIndex(channelLayer, QSWATTopology._BASINNO, ignoreMissing=True)
        if outletLayer is not None:
            nodeidField = self._gv.topo.getIndex(outletLayer, QSWATTopology._ID, ignoreMissing=True)
            srcField = self._gv.topo.getIndex(outletLayer, QSWATTopology._PTSOURCE, ignoreMissing=True)
            resField = self._gv.topo.getIndex(outletLayer, QSWATTopology._RES, ignoreMissing=True)
            inletField = self._gv.topo.getIndex(outletLayer, QSWATTopology._INLET, ignoreMissing=True)
        # collect map of deleted basin number to replacement for updating channelLayer
        changedBasins: Dict[int, int] = dict()
        # ids of the features will change as we delete them, so use polygonids, which we know will be unique
        pids: List[int] = []
        for f in selection:
            pid = f[polygonidField]
            pids.append(int(pid))
        # in the following
        # suffix A refers to the subbasin being merged
        # suffix UAs refers to the subbasin(s) upstream from A
        # suffix D refers to the subbasin downstream from A
        # suffix B refers to the othe subbasin(s) upstream from D
        # suffix M refers to the merged basin
        self._gv.writeProjectConfig(0, 0)
        for polygonidA in pids:
            subbasinA = QSWATUtils.getFeatureByValue(subbasinsLayer, polygonidField, polygonidA)
            reachA = QSWATUtils.getFeatureByValue(streamLayer, wsnoField, polygonidA)
            if not reachA:
                QSWATUtils.error('Cannot find reach with {0} value {1!s}'.format(QSWATTopology._WSNO, polygonidA), self._gv.isBatch)
                continue
            QSWATUtils.loginfo('A is reach {0!s} polygon {1!s}'.format(reachA[linknoField], polygonidA))
            AHasOutlet = False
            AHasInlet = False
            if dsnodeidnField >= 0:
                dsnodeidA = reachA[dsnodeidnField]
                if outletLayer is not None:
                    pointFeature = QSWATUtils.getFeatureByValue(outletLayer, nodeidField, dsnodeidA)
                    if pointFeature is not None:
                        if inletField >= 0 and pointFeature[inletField] == 1:
                            AHasInlet = True
                        elif resField >= 0 and pointFeature[resField] == 0:
                            AHasOutlet = True
            if AHasOutlet or AHasInlet:
                QSWATUtils.information('You cannot merge a subbasin which has an outlet or inlet.  Not merging subbasin with {0} value {1!s}'.format(QSWATTopology._POLYGONID, polygonidA), self._gv.isBatch)
                continue
            linknoA = reachA[linknoField]
            geomA = reachA.geometry()
            reachUAs = [reach for reach in streamLayer.getFeatures() if reach[dslinknoField] == linknoA]
            # check whether a reach immediately upstream from A has an inlet
            inletUpFromA = False
            if dsnodeidnField >= 0 and outletLayer:
                for reachUA in reachUAs:
                    dsnodeidUA = reachUA[dsnodeidnField]
                    pointFeature = QSWATUtils.getFeatureByValue(outletLayer, nodeidField, dsnodeidUA)
                    if pointFeature is not None:
                        if inletField >= 0 and pointFeature[inletField] == 1 and (srcField < 0 or pointFeature[srcField] == 0):
                            inletUpFromA = True
                            break
            linknoD = reachA[dslinknoField]
            reachD = QSWATUtils.getFeatureByValue(streamLayer, linknoField, linknoD)
            if not reachD:
                QSWATUtils.information('No downstream subbasin from subbasin with {0} value {1!s}: nothing to merge'.format(QSWATTopology._POLYGONID, polygonidA), self._gv.isBatch)
                continue
            polygonidD = reachD[wsnoField]
            geomD = reachD.geometry()
            QSWATUtils.loginfo('D is reach {0!s} polygon {1!s}'.format(linknoD, polygonidD))
            # reachD may be zero length, with no corresponding subbasin, so search downstream if necessary to find subbasinD
            # at the same time collect zero-length reaches for later disposal
            subbasinD = None
            nextReach: QgsFeature = reachD
            zeroReaches: List[QgsFeature] = []
            while not subbasinD:
                polygonidD = nextReach[wsnoField]
                subbasinD = QSWATUtils.getFeatureByValue(subbasinsLayer, polygonidField, polygonidD)
                if subbasinD is not None:
                    break
                # nextReach has no subbasin (it is a zero length link); step downstream and try again
                # first make a check
                if lengthField >= 0 and nextReach[lengthField] > 0:
                    QSWATUtils.error('Internal error: stream reach wsno {0!s} has positive length but no subbasin.  Not merging subbasin with {1} value {2!s}'.format(polygonidD, QSWATTopology._POLYGONID, polygonidA), self._gv.isBatch)
                    continue
                if zeroReaches:
                    zeroReaches.append(nextReach)
                else:
                    zeroReaches = [nextReach]
                nextLink = nextReach[dslinknoField]
                if nextLink < 0:
                    # reached main outlet
                    break
                nextReach = QSWATUtils.getFeatureByValue(streamLayer, linknoField, nextLink)
            if not subbasinD:
                QSWATUtils.information('No downstream subbasin from subbasin with {0} value {1!s}: nothing to merge'.format(QSWATTopology._POLYGONID, polygonidA), self._gv.isBatch)
                continue
            reachD = nextReach
            linknoD = reachD[linknoField]
            zeroLinks = [reach[linknoField] for reach in zeroReaches]
            if inletUpFromA:
                DLinks = [linknoD]
                if zeroLinks:
                    DLinks.extend(zeroLinks)
                reachBs = [reach for reach in streamLayer.getFeatures() if reach[dslinknoField] in DLinks and reach.id() != reachA.id()]
                if reachBs != []:
                    QSWATUtils.information('Subbasin with {0} value {1!s} has an upstream inlet and the downstream one has another upstream subbasin: cannot merge.'.format(QSWATTopology._POLYGONID, polygonidA), self._gv.isBatch)
                    continue
            # have reaches and watersheds A, UAs, D
            # we are ready to start editing the streamLayer
            OK = True
            try:
                OK = streamLayer.startEditing()
                if not OK:
                    QSWATUtils.error('Cannot edit stream reaches shapefile', self._gv.isBatch)
                    return
#                 if reachUAs == []:
#                     # A is a head reach (nothing upstream)
#                     # change any dslinks to zeroLinks to D as the zeroReaches will be deleted
#                     if zeroLinks:
#                         for reach in streamLayer.getFeatures():
#                             if reach[dslinknoField] in zeroLinks:
#                                 streamLayer.changeAttributeValue(reach.id(), dslinknoField, linknoD)
#                     # change USLINK1 or USLINK2 references to A or zeroLinks to -1
#                     if uslinkno1Field >= 0:
#                         Dup1 = reachD[uslinkno1Field]
#                         if Dup1 == linknoA or (zeroLinks and Dup1 in zeroLinks):
#                             streamLayer.changeAttributeValue(reachD.id(), uslinkno1Field, -1)
#                             Dup1 = -1
#                     if uslinkno2Field >= 0:
#                         Dup2 = reachD[uslinkno2Field]
#                         if Dup2 == linknoA or (zeroLinks and Dup2 in zeroLinks):
#                             streamLayer.changeAttributeValue(reachD.id(), uslinkno2Field, -1)
#                             Dup2 = -1
#                     if magnitudeField >= 0:
#                         # Magnitudes of D and below should be reduced by 1
#                         nextReach = reachD
#                         while nextReach:
#                             mag = nextReach[magnitudeField]
#                             streamLayer.changeAttributeValue(nextReach.id(), magnitudeField, mag - 1)
#                             nextReach = QSWATUtils.getFeatureByValue(streamLayer, linknoField, nextReach[dslinknoField])
#                     # do not change Order field, since streams unaffected
# #                     if orderField >= 0:
# #                         # as subbasins are merged we cannot rely on two uplinks;
# #                         # there may be several subbasins draining into D,
# #                         # so we collect these, remembering to exclude A itself
# #                         upLinks = []
# #                         for reach in streamLayer.getFeatures():
# #                             downLink = reach[dslinknoField]
# #                             reachLink = reach[linknoField] 
# #                             if downLink == linknoD and reachLink != linknoA:
# #                                 upLinks.append(reach[linknoField])
# #                         orderD = Delineation.calculateStrahler(streamLayer, upLinks, linknoField, orderField)
# #                         if orderD != reachD[orderField]:
# #                             streamLayer.changeAttributeValue(reachD.id(), orderField, orderD)
# #                             nextReach = QSWATUtils.getFeatureByValue(streamLayer, linknoField, reachD[dslinknoField])
# #                             Delineation.reassignStrahler(streamLayer, nextReach, linknoD, orderD, 
# #                                                          linknoField, dslinknoField, orderField)
#                     OK = streamLayer.deleteFeature(reachA.id())
#                     if not OK:
#                         QSWATUtils.error('Cannot edit stream reaches shapefile', self._gv.isBatch)
#                         streamLayer.rollBack()
#                         return
#                     if zeroReaches:
#                         for reach in zeroReaches:
#                             streamLayer.deleteFeature(reach.id())
#                 else:
                # create new merged stream M from D and A and add it to streams
                # prepare reachM
                reachM = QgsFeature()
                streamFields = streamLayer.dataProvider().fields()
                reachM.setFields(streamFields)
                reachM.setGeometry(geomA.combine(geomD))
                # check if we have single line
                if reachM.geometry().isMultipart():
                    QSWATUtils.loginfo('Multipart reach')
                OK = streamLayer.addFeature(reachM)
                if not OK:
                    QSWATUtils.error('Cannot add shape to stream reaches shapefile', self._gv.isBatch)
                    streamLayer.rollBack()
                    return
                idM = reachM.id()
                streamLayer.changeAttributeValue(idM, linknoField, linknoD)
                streamLayer.changeAttributeValue(idM, dslinknoField, reachD[dslinknoField])
                # change dslinks in UAs to D (= M)
                for reach in reachUAs:
                    streamLayer.changeAttributeValue(reach.id(), dslinknoField, linknoD)
                # change any dslinks to zeroLinks to D as the zeroReaches will be deleted
                if zeroLinks:
                    for reach in streamLayer.getFeatures():
                        if reach[dslinknoField] in zeroLinks:
                            streamLayer.changeAttributeValue(reach.id(), dslinknoField, linknoD)
                if uslinkno1Field >= 0:
                    Dup1 = reachD[uslinkno1Field]
                    if Dup1 == linknoA or (zeroLinks and Dup1 in zeroLinks):
                        # in general these cannot be relied on, since as we remove zero length links 
                        # there may be more than two upstream links from M
                        # At least don't leave it referring to a soon to be non-existent reach
                        Dup1 = reachA[uslinkno1Field]
                    streamLayer.changeAttributeValue(idM, uslinkno1Field, Dup1)
                if uslinkno2Field >= 0:
                    Dup2 = reachD[uslinkno2Field]
                    if Dup2 == linknoA or (zeroLinks and Dup2 in zeroLinks):
                        # in general these cannot be relied on, since as we remove zero length links 
                        # there may be more than two upstream links from M
                        # At least don't leave it referring to a soon to be non-existent reach
                        Dup2 = reachA[uslinkno2Field]
                    streamLayer.changeAttributeValue(idM, uslinkno2Field, Dup2)
                if dsnodeidnField >= 0:
                    streamLayer.changeAttributeValue(idM, dsnodeidnField, reachD[dsnodeidnField])
                if orderField >= 0:
                    streamLayer.changeAttributeValue(idM, orderField, reachD[orderField])
#                     # as subbasins are merged we cannot rely on two uplinks;
#                     # there may be several subbasins draining into M, those that drained into A or D
#                     # so we collect these, remembering to exclude A itself
#                     upLinks = []
#                     for reach in streamLayer.getFeatures():
#                         downLink = reach[dslinknoField]
#                         reachLink = reach[linknoField] 
#                         if downLink == linknoA or (downLink == linknoD and reachLink != linknoA):
#                             upLinks.append(reach[linknoField])
#                     orderM = Delineation.calculateStrahler(streamLayer, upLinks, linknoField, orderField)
#                     streamLayer.changeAttributeValue(idM, orderField, orderM)
#                     if orderM != reachD[orderField]:
#                         nextReach = QSWATUtils.getFeatureByValue(streamLayer, linknoField, reachD[dslinknoField])
#                         Delineation.reassignStrahler(streamLayer, nextReach, linknoD, orderM, 
#                                                      linknoField, dslinknoField, orderField)
                if lengthField >= 0:
                    lengthA = reachA[lengthField]
                    lengthD = reachD[lengthField]
                    streamLayer.changeAttributeValue(idM, lengthField, lengthA + lengthD)
                elif slopeField >= 0 or straight_lField >= 0 or (dout_endField >= 0 and dout_midField >= 0):
                    # we will need these lengths
                    lengthA = geomA.length()
                    lengthD = geomD.length()
                if magnitudeField >= 0:
                    streamLayer.changeAttributeValue(idM, magnitudeField, reachD[magnitudeField])
                if ds_cont_arField >= 0:
                    streamLayer.changeAttributeValue(idM, ds_cont_arField, reachD[ds_cont_arField])
                if dropField >= 0:
                    dropA = reachA[dropField]
                    dropD = reachD[dropField]
                    streamLayer.changeAttributeValue(idM, dropField, dropA + dropD)
                elif slopeField >= 0:
                    dataA = self._gv.topo.getReachData(reachA, demLayer)
                    dropA = dataA.upperZ = dataA.lowerZ
                    dataD = self._gv.topo.getReachData(reachD, demLayer)
                    dropD = dataD.upperZ = dataD.lowerZ
                if slopeField >= 0:
                    streamLayer.changeAttributeValue(idM, slopeField, (dropA + dropD) / (lengthA + lengthD))
                if straight_lField >= 0:
                    dataA = self._gv.topo.getReachData(reachA, demLayer)
                    dataD = self._gv.topo.getReachData(reachD, demLayer)
                    dx = dataA.upperX - dataD.lowerX
                    dy = dataA.upperY - dataD.lowerY
                    streamLayer.changeAttributeValue(idM, straight_lField, math.sqrt(dx * dx + dy * dy))
                if us_cont_arField >= 0:
                    streamLayer.changeAttributeValue(idM, us_cont_arField, reachA[us_cont_arField])
                streamLayer.changeAttributeValue(idM, wsnoField, polygonidD)
                if dout_endField >= 0:
                    streamLayer.changeAttributeValue(idM, dout_endField, reachD[dout_endField])
                if dout_startField >= 0:
                    streamLayer.changeAttributeValue(idM, dout_startField, reachA[dout_startField])
                if dout_endField >= 0 and dout_midField >= 0:
                    streamLayer.changeAttributeValue(idM, dout_midField, reachD[dout_endField] + (lengthA + lengthD) / 2.0)
                streamLayer.deleteFeature(reachA.id())
                streamLayer.deleteFeature(reachD.id())
                if zeroReaches:
                    for reach in zeroReaches:
                        streamLayer.deleteFeature(reach.id())
            except Exception:
                QSWATUtils.exceptionError('Exception while updating stream reach shapefile', self._gv.isBatch)
                OK = False
                streamLayer.rollBack()
                return
            else:
                if streamLayer.isEditable():
                    streamLayer.commitChanges()
                    streamLayer.triggerRepaint()
            if not OK:
                return
        
            # New watershed shapefile will be inconsistent with watershed grid, so remove grid to be recreated later.
            # Do not do it immediately because the user may remove several subbasins, so we wait until the 
            # delineation form is closed.
            # clear name as flag that it needs to be recreated
            self._gv.basinFile = ''
            try:
                OK = subbasinsLayer.startEditing()
                if not OK:
                    QSWATUtils.error('Cannot edit watershed shapefile', self._gv.isBatch)
                    return
                # create new merged subbasin M from D and A and add it to subbasins
                # prepare reachM
                subbasinM = QgsFeature()
                subbasinFields = subbasinsLayer.dataProvider().fields()
                subbasinM.setFields(subbasinFields)
                subbasinM.setGeometry(subbasinD.geometry().combine(subbasinA.geometry()))
                OK = subbasinsLayer.addFeature(subbasinM)
                if not OK:
                    QSWATUtils.error('Cannot add shape to watershed shapefile', self._gv.isBatch)
                    subbasinsLayer.rollBack()
                    return
                idM = subbasinM.id()
                subbasinsLayer.changeAttributeValue(idM, polygonidField, polygonidD) 
                if areaField >= 0:
                    areaA = subbasinA[areaField]
                    areaD = subbasinD[areaField]
                    subbasinsLayer.changeAttributeValue(idM, areaField, areaA + areaD)
                if streamlinkField >= 0:
                    subbasinsLayer.changeAttributeValue(idM, streamlinkField, subbasinD[streamlinkField])
                if streamlenField >= 0:
                    lenA = subbasinA[streamlenField]
                    lenD = subbasinD[streamlenField]
                    subbasinsLayer.changeAttributeValue(idM, streamlenField, lenA + lenD)
                if dsnodeidwField >= 0:
                    subbasinsLayer.changeAttributeValue(idM, dsnodeidwField, subbasinD[dsnodeidwField])
                if dswsidField >= 0:
                    subbasinsLayer.changeAttributeValue(idM, dswsidField, subbasinD[dswsidField])
                    # change downlinks upstream of A from A to D (= M)
                    subbasinUAs = [subbasin for subbasin in subbasinsLayer.getFeatures() if subbasin[dswsidField] == polygonidA]
                    for subbasinUA in subbasinUAs:
                        subbasinsLayer.changeAttributeValue(subbasinUA.id(), dswsidField, polygonidD) 
                if us1wsidField >= 0:
                    if subbasinD[us1wsidField] == polygonidA:
                        subbasinsLayer.changeAttributeValue(idM, us1wsidField, subbasinA[us1wsidField])
                    else:
                        subbasinsLayer.changeAttributeValue(idM, us1wsidField, subbasinD[us1wsidField])
                if us2wsidField >= 0:
                    if subbasinD[us2wsidField] == polygonidA:
                        subbasinsLayer.changeAttributeValue(idM, us2wsidField, subbasinA[us2wsidField])
                    else:
                        subbasinsLayer.changeAttributeValue(idM, us2wsidField, subbasinD[us2wsidField])
                if subbasinField >= 0:
                    subbasinsLayer.changeAttributeValue(idM, subbasinField, subbasinD[subbasinField])
                # remove A and D subbasins
                subbasinsLayer.deleteFeature(subbasinA.id())
                subbasinsLayer.deleteFeature(subbasinD.id())
                # we will replace A with D in channelLayer basinno field
                changedBasins[polygonidA] = polygonidD
            except Exception:
                QSWATUtils.exceptionError('Exception while updating watershed shapefile', self._gv.isBatch)
                OK = False
                subbasinsLayer.rollBack()
                return
            else:
                if subbasinsLayer.isEditable():
                    subbasinsLayer.commitChanges()
                    subbasinsLayer.triggerRepaint()
        # guard against B -> C, A -> B problems in changedBasins
        changedBasins = MapFuns.flattenMap(changedBasins)
        # update BASINNO field in channels shapefile
        if basinField >= 0:
            channelProvider = channelLayer.dataProvider()
            changeMap = dict()
            request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([basinField])
            for channel in channelProvider.getFeatures(request):
                for polygonIdA, polygonidD in changedBasins.items():
                    if polygonIdA == channel[basinField]:
                        changeMap[channel.id()] = {basinField: polygonidD}
            OK = channelProvider.changeAttributeValues(changeMap)
            if not OK:
                QSWATUtils.error('Failed to update {0} fields in channels shapefile'.format(QSWATTopology._BASINNO), self._gv.isBatch)
        # update chBasinToSubbasin 
        # will change dictionary so use list
        for chBasin, subbasin in list(self._gv.topo.chBasinToSubbasin.items()):
            newSubbasin = changedBasins.get(subbasin, -1)
            if newSubbasin >= 0:
                self._gv.topo.chBasinToSubbasin[chBasin] = newSubbasin
        # remove subbasin outlets
        for polygonIdA in changedBasins:
            del self._gv.topo.outlets[polygonIdA]
        QSWATUtils.loginfo('{0} outlets after merging subbasins'.format(len(self._gv.topo.outlets)))
               
          
    #==========no longer used=================================================================
    # @staticmethod      
    # def reassignStrahler(streamLayer, reach, upLink, upOrder, linknoField, dslinknoField, orderField):
    #     """Reassign Strahler numbers downstream in the network starting from reach.
    #     Stop when the new Strahler number is already stored, or the root of the tree is reached.
    #     If a link draining to reach is the same as upLink, use upOrder as its order (since it is not 
    #     yet stored in streamLayer).
    #     """
    #     if reach is None:
    #         return
    #     link = reach[linknoField]
    #     ups = [up for up in streamLayer.getFeatures() if up[dslinknoField] == link]
    #     def orderOfReach(r): return upOrder if r[linknoField] == upLink else r[orderField]
    #     orders = [orderOfReach(up) for up in ups]
    #     s = Delineation.strahlerOrder(orders)
    #     if s != reach[orderField]:
    #         streamLayer.changeAttributeValue(reach.id(), orderField, s)
    #         downReach = QSWATUtils.getFeatureByValue(streamLayer, linknoField, reach[dslinknoField])
    #         Delineation.reassignStrahler(streamLayer, downReach, link, s, linknoField, dslinknoField, orderField)
    #         
    # @staticmethod
    # def calculateStrahler(streamLayer, upLinks, linknoField, orderField):
    #     """Calculate Strahler order from upstream links upLinks."""
    #     orders = [QSWATUtils.getFeatureByValue(streamLayer, linknoField, upLink)[orderField] for upLink in upLinks]
    #     return Delineation.strahlerOrder(orders)
    #     
    # @staticmethod
    # def strahlerOrder(orders):
    #     """Calculate Strahler order from a list or orders."""
    #     if len(orders) == 0:
    #         return 1
    #     else:
    #         omax = max(orders)
    #         count = len([o for o in orders if o == omax])
    #         return omax if count == 1 else omax+1
    #===========================================================================
        
    def cleanUp(self, tabIndex: int) -> None:
        """Set cursor to Arrow, clear progress label, clear message bar, 
        and change tab index if not negative.
        """
        if tabIndex >= 0:
            self._dlg.tabWidget.setCurrentIndex(tabIndex)
        self._dlg.setCursor(Qt.ArrowCursor)
        self.progress('')
        return
     
    def createWatershedShapefile(self, wFile: str, subbasinsFile: str, ft: FileTypes, root: QgsLayerTree) -> None:
        """
        Create watershed shapefile subbasinsFile from watershed grid wFile, 
        and load it if ft is FileTypes._SUBBASINS.
        
        This function is used to create the subbasins shapefile (one basin per stream)
        and also the watershed shapefile (one basin per channel).
        The latter is intended for existing watershed use, and for the landscape units file when floodplains are not used
        (so that landscape units coincide with stream basins), and is not normally loaded.
        """
        if QSWATUtils.isUpToDate(wFile, subbasinsFile):
            return
        # create shapes from wFile
        wDs = gdal.Open(wFile, gdal.GA_ReadOnly)
        if wDs is None:
            QSWATUtils.error('Cannot open watershed grid {0}'.format(wFile), self._gv.isBatch)
            return
        wBand = wDs.GetRasterBand(1)
        noData = wBand.GetNoDataValue()
        transform = wDs.GetGeoTransform()
        numCols = wDs.RasterXSize
        numRows = wDs.RasterYSize
        isConnected4 = True
        shapes = Polygonize(isConnected4, numCols, noData, 
                            QgsPointXY(transform[0], transform[3]), transform[1], abs(transform[5]))
        for row in range(numRows):
            wBuffer = wBand.ReadAsArray(0, row, numCols, 1).astype(int)
            shapes.addRow(wBuffer.reshape([numCols]), row)
        shapes.finish()
        legend = FileTypes.legend(ft)
        if QSWATUtils.shapefileExists(subbasinsFile):
            subbasinsLayer = QSWATUtils.getLayerByFilename(root.findLayers(), subbasinsFile, ft, None, None, None)[0]
            if subbasinsLayer is None:
                subbasinsLayer = QgsVectorLayer(subbasinsFile, '{0} ({1})'.
                                                format(legend, QFileInfo(subbasinsFile).baseName()), 'ogr')
            if not QSWATUtils.removeAllFeatures(subbasinsLayer):
                QSWATUtils.error('Failed to remove old features from {0}.  Please remove the file manually.'.format(subbasinsFile), self._gv.isBatch)
                return
            fields = subbasinsLayer.fields()
        else:
            QSWATUtils.removeLayer(subbasinsFile, root)
            # create shapefile
            fields = QgsFields()
            fields.append(QgsField(QSWATTopology._POLYGONID, QVariant.Int))
            fields.append(QgsField(Parameters._AREA, QVariant.Double, len=20, prec=2))
            # for the subbasins layer we will later add the SWAT basin number
            # and for the watershed layer we will later add the SWAT channel number
            if ft == FileTypes._SUBBASINS:
                fields.append(QgsField(QSWATTopology._SUBBASIN, QVariant.Int))
            else:
                fields.append(QgsField(QSWATTopology._CHANNEL, QVariant.Int))
            writer = QgsVectorFileWriter.create(subbasinsFile, fields, QgsWkbTypes.MultiPolygon, self._gv.crsProject, 
                                                QgsCoordinateTransformContext(), self._gv.vectorFileWriterOptions)
            if writer.hasError() != QgsVectorFileWriter.NoError:
                QSWATUtils.error('Cannot create watershed shapefile {0}: {1}'. \
                                 format(subbasinsFile, writer.errorMessage()), self._gv.isBatch)
                return
            # delete the writer to flush
            if not writer.flushBuffer():
                typ = 'subbasins' if ft == FileTypes._SUBBASINS else 'watershed'
                QSWATUtils.error('Failed to complete creating {0} shapefile {1}'.format(typ, subbasinsFile), self._gv.isBatch)
            del writer
            # wFile may not have a .prj (being a .tif) so use DEM's
            QSWATUtils.copyPrj(self._gv.demFile, subbasinsFile)
            subbasinsLayer = QgsVectorLayer(subbasinsFile, '{0} ({1})'. \
                                            format(legend, QFileInfo(subbasinsFile).baseName()), 'ogr')
        provider = subbasinsLayer.dataProvider()
        basinIndex = provider.fieldNameIndex(QSWATTopology._POLYGONID)
        areaIndex = provider.fieldNameIndex(Parameters._AREA)
        if basinIndex < 0 or areaIndex < 0:
            fieldName = QSWATTopology._POLYGONID if basinIndex < 0 else Parameters._AREA
            typ = 'subbasins' if ft == FileTypes._SUBBASINS else 'watershed'
            QSWATUtils.error('Failed to find {0} field in {1} shapefile {2}'.format(fieldName, typ, subbasinsFile), self._gv.isBatch)
            return
        if ft == FileTypes._SUBBASINS:
            self._gv.topo.basinCentroids.clear()
        for basin in shapes.shapes:
            geometry = shapes.getGeometry(basin)
            geometry1 = geometry.makeValid()
            error = geometry1.lastError()
            if error != '':
                QSWATUtils.loginfo('Error in {0} forming geomtry for basin {1}: {2}'.format(subbasinsFile, basin, error))
            feature = QgsFeature(fields)
            # basin is a numpy.int32 so we need to convert it to a Python int
            feature.setAttribute(basinIndex, int(basin))
            feature.setAttribute(areaIndex, shapes.area(basin) * self._gv.horizontalFactor * self._gv.horizontalFactor / 1E4)
            feature.setGeometry(geometry1)
            if not provider.addFeatures([feature]):
                QSWATUtils.error('Unable to add feature to watershed shapefile {0}'. \
                                 format(subbasinsFile), self._gv.isBatch)
                return
            if ft == FileTypes._SUBBASINS:
                centroid = geometry.centroid().asPoint()
                self._gv.topo.basinCentroids[basin] = (centroid.x(), centroid.y())
                
        # load it if ft is FileTypes._SUBBASINS
        if ft == FileTypes._SUBBASINS:
            root = QgsProject.instance().layerTreeRoot()
            # load above DEM (or hillshade) and below streams
            # (or use Full HRUs layer if there is one)
            fullHRUsLayer = QSWATUtils.getLayerByLegend(QSWATUtils._FULLHRUSLEGEND, 
                                                        root.findLayers())
            if fullHRUsLayer is not None:
                subLayer = fullHRUsLayer
            else:
                hillshadeLayer = QSWATUtils.getLayerByLegend(QSWATUtils._HILLSHADELEGEND,
                                                             root.findLayers())
                if hillshadeLayer is not None:
                    subLayer = hillshadeLayer
                else:
                    demLayer = QSWATUtils.getLayerByFilenameOrLegend(root.findLayers(), self._gv.demFile,
                                                                     FileTypes._DEM, '', self._gv.isBatch)
                    if demLayer is not None:
                        subLayer = root.findLayer(demLayer.id())
                    else:
                        subLayer = None
            subbasinsLayer, _ = QSWATUtils.getLayerByFilename(root.findLayers(), subbasinsFile, 
                                                                   FileTypes._SUBBASINS, self._gv, 
                                                                   subLayer, QSWATUtils._WATERSHED_GROUP_NAME)
            if subbasinsLayer is None:
                QSWATUtils.error('Failed to load subbasins shapefile {0}'.format(subbasinsFile), self._gv.isBatch)
                return
            self._gv.iface.setActiveLayer(subbasinsLayer)
            # labels should be turned off, as may persist from previous run
            # we turn back on when SWAT basin numbers are calculated and stored
            # in the Subbasin field
            subbasinsLayer.setLabelsEnabled(False)
        
    def createBasinFile(self, basinsShapefile: str, demLayer: QgsRasterLayer, nameCode: str, root: QgsLayerTree) -> str:
        """Create basin file from subbasins or watershed basins shapefile."""
        demPath = QSWATUtils.layerFileInfo(demLayer).canonicalFilePath()
        wFile: str = os.path.splitext(demPath)[0] + nameCode + '.tif'
        shapeBase = os.path.splitext(basinsShapefile)[0]
        # if basename of wFile is used rasterize fails
        baseName = os.path.basename(shapeBase)
        QSWATUtils.tryRemoveLayerAndFiles(wFile, root)
        xSize = demLayer.rasterUnitsPerPixelX()
        ySize = demLayer.rasterUnitsPerPixelY()
        extent = demLayer.extent()
        # need to use extent to align basin raster cells with DEM
        command = 'gdal_rasterize -a {0} -tr {1!s} {2!s} -te {6} {7} {8} {9} -a_nodata -9999 -ot Int32 -l "{3}" "{4}" "{5}"' \
        .format(QSWATTopology._POLYGONID, xSize, ySize, baseName, basinsShapefile, wFile,
                extent.xMinimum(), extent.yMinimum(), extent.xMaximum(), extent.yMaximum())
        QSWATUtils.loginfo(command)
        os.system(command)
        assert os.path.exists(wFile)
        QSWATUtils.copyPrj(basinsShapefile, wFile)
        return wFile
    
    def createPlayaFile(self, lakeFile: str, demLayer: QgsRasterLayer, root: QgsLayerTree) -> str:
        """Create raster of Playa lakes."""
        demPath = QSWATUtils.layerFileInfo(demLayer).canonicalFilePath()
        playaFile: str = os.path.splitext(demPath)[0] + 'playa.tif'
        shapeBase = os.path.splitext(lakeFile)[0]
        # if basename of wFile is used rasterize fails
        baseName = os.path.basename(shapeBase)
        QSWATUtils.tryRemoveLayerAndFiles(playaFile, root)
        xSize = demLayer.rasterUnitsPerPixelX()
        ySize = demLayer.rasterUnitsPerPixelY()
        extent = demLayer.extent()
        # need to use extent to align basin raster cells with DEM
        where = 'RES = {0}'.format(QSWATTopology._PLAYATYPE)
        command = 'gdal_rasterize -a {0} -tr {1!s} {2!s} -te {6} {7} {8} {9} -a_nodata -9999 -ot Int32 -where "{10}" -l "{3}" "{4}" "{5}"' \
        .format(QSWATTopology._RES, xSize, ySize, baseName, lakeFile, playaFile,
                extent.xMinimum(), extent.yMinimum(), extent.xMaximum(), extent.yMaximum(), where)
        QSWATUtils.loginfo(command)
        os.system(command)
        assert os.path.exists(playaFile)
        QSWATUtils.copyPrj(lakeFile, playaFile)
        return playaFile
        
    
    def createGridShapefile(self, pFile: str, ad8File: str, wFile: str) -> None:
        """Create grid shapefile for watershed."""
        self.progress('Creating grid ...')
        self._gv.gridSize = self._dlg.gridSize.value()
        time2 = time.process_time()
        storeGrid, accTransform, minDrainArea, maxDrainArea = self.storeGridData(ad8File, wFile, self._gv.gridSize)
        time3 = time.process_time()
        QSWATUtils.loginfo('Storing grid data took {0} seconds'.format(int(time3 - time2)))
        if storeGrid is not None:
            assert accTransform is not None
            if self.addDownstreamData(storeGrid, pFile, self._gv.gridSize, accTransform):
                time4 = time.process_time()
                QSWATUtils.loginfo('Adding downstream data took {0} seconds'.format(int(time4 - time3)))
                self.writeGridShapefile(storeGrid, pFile, self._gv.gridSize, accTransform)
                time5 = time.process_time()
                QSWATUtils.loginfo('Writing grid shapefile took {0} seconds'.format(int(time5 - time4)))
                numOutlets = self.writeGridStreamsShapefile(storeGrid, pFile, minDrainArea, maxDrainArea, accTransform)
                time6 = time.process_time()
                QSWATUtils.loginfo('Writing grid streams shapefile took {0} seconds'.format(int(time6 - time5)))
                if numOutlets >= 0:
                    msg = 'Grid processing done with subbasin threshold {0} sq.km: {1} outlets'.format(self._dlg.areaSt.text(), numOutlets)
                    QSWATUtils.loginfo(msg)
                    #self._gv.iface.messageBar().pushMessage(msg, level=Qgis.Info, duration=10)
                    #if self._gv.isBatch:
                    #    print(msg)
        return
    
    def storeGridData(self, ad8File: str, basinFile: str, gridSize: int) -> Tuple[Optional[Dict[int, Dict[int, GridData]]], Optional[Transform], float, float]:
        """Create grid data in array and return it."""
        # if there are inlets, make a new ad8File with areas upstream from inlets set to no data
        inAsOutFile, hasInlet = self.hasInlets()
        if hasInlet:
            assert inAsOutFile is not None
            ad8File1 = self.reduceAccumulationFile(ad8File, inAsOutFile)
            if ad8File1 is None:
                return None, None, 0, 0
            ad8File = ad8File1
        # mask accFile with basinFile to exclude small outflowing watersheds
        ad8Layer = QgsRasterLayer(ad8File, 'P')
        entry1 = QgsRasterCalculatorEntry()
        entry1.bandNumber = 1
        entry1.raster = ad8Layer
        entry1.ref = 'P@1'        
        basinLayer = QgsRasterLayer(basinFile, 'Q')
        entry2 = QgsRasterCalculatorEntry()
        entry2.bandNumber = 1
        entry2.raster = basinLayer
        entry2.ref = 'Q@1'
        base = os.path.splitext(ad8File)[0]
        accFile = base + 'clip.tif'
        QSWATUtils.tryRemoveFiles(accFile)
        # The formula is a standard way of masking P with Q, since 
        # where Q is nodata Q / Q evaluates to nodata, and elsewhere evaluates to 1.
        # We use 'Q+1' instead of Q to avoid problems in first subbasin 
        # when PolygonId is zero so Q is zero
        formula = '((Q@1 + 1) / (Q@1 + 1)) * P@1'
        calc = QgsRasterCalculator(formula, accFile, 'GTiff', ad8Layer.extent(), ad8Layer.width(), ad8Layer.height(), [entry1, entry2],
                                   QgsCoordinateTransformContext())
        result = calc.processCalculation(feedback=None)
        if result == 0:
            assert os.path.exists(accFile), 'QGIS calculator formula {0} failed to write output'.format(formula)
            QSWATUtils.copyPrj(ad8File, accFile)
        else:
            QSWATUtils.error('QGIS calculator formula {0} failed: returned {1}'.format(formula, result), self._gv.isBatch)
            return None, None, 0, 0
        accRaster = gdal.Open(accFile, gdal.GA_ReadOnly)
        if accRaster is None:
            QSWATUtils.error('Cannot open accumulation file {0}'.format(accFile), self._gv.isBatch)
            return None, None, 0, 0
        # for now read whole accumulation file into memory
        accBand = accRaster.GetRasterBand(1)
        accTransform = accRaster.GetGeoTransform()    
        accArray = accBand.ReadAsArray(0, 0, accBand.XSize, accBand.YSize)
        unitArea = abs(accTransform[1] * accTransform[5]) * self._gv.horizontalFactor * self._gv.horizontalFactor / 1E6 # area of one cell in square km
        QSWATUtils.loginfo('Grid cell area {0!s} sq km'.format(unitArea * self._gv.gridSize * self._gv.gridSize))
        # create polygons and add to gridFile
        polyId = 0
        # grid cells will be gridSize x gridSize squares
        numGridRows = (accBand.YSize // gridSize) + 1
        numGridCols = (accBand.XSize // gridSize) + 1
        storeGrid: Dict[int, Dict[int, GridData]] = dict() # dictionary gridRow -> gridCol -> gridData
        maxDrainArea = 0
        minDrainArea = float('inf')
        for gridRow in range(numGridRows):
            startAccRow = gridRow * gridSize
            for gridCol in range(numGridCols):
                startAccCol = gridCol * gridSize
                maxAcc = 0
                maxRow = -1
                maxCol = -1
                valCount = 0
                for row in range(gridSize):
                    accRow = startAccRow + row
                    for col in range(gridSize):
                        accCol = startAccCol + col
                        if accRow < accBand.YSize and accCol < accBand.XSize:
                            accVal = accArray[accRow, accCol]
                            if accVal > 0:
                                valCount += 1
                                # can get points with same (rounded) accumulation when values are high.
                                # prefer one on edge if possible
                                if accVal > maxAcc or (accVal == maxAcc and self.onEdge(row, col, gridSize)):
                                    maxAcc = accVal
                                    maxRow = accRow
                                    maxCol = accCol
                if valCount == 0:
                    # no data for this grid
                    continue
                polyId += 1
                #if polyId <= 5:
                #    x, y = QSWATTopology.cellToProj(maxCol, maxRow, accTransform)
                #    maxAccPoint = QgsPointXY(x, y)
                #    QSWATUtils.loginfo('Grid ({0},{1}) id {6} max {4} at ({2},{3}) which is {5}'.format(gridRow, gridCol, maxCol, maxRow, maxAcc, maxAccPoint.toString(), polyId))
                drainArea = maxAcc * unitArea
                if drainArea < minDrainArea:
                    minDrainArea = drainArea
                if drainArea > maxDrainArea:
                    maxDrainArea = drainArea
                data = GridData(polyId, valCount, drainArea, maxAcc, maxRow, maxCol)
                if gridRow not in storeGrid:
                    storeGrid[gridRow] = dict()
                storeGrid[gridRow][gridCol] = data
        # add any outlet and inlet ids
        self._gv.topo.lostDsNodeIds = set()
        for ioId, (point, pt) in self.inletOutletPoints.items():
            gridCol = int((pt.x() - accTransform[0]) / (accTransform[1] * self._gv.gridSize))
            gridRow = int((pt.y() - accTransform[3]) / (accTransform[5] * self._gv.gridSize))
            # try to find an at most 'one off' grid cell: 
            # for inlets can't guarantee central one is not just outside the grid
            found = False
            for i in [0, 1, -1]:
                for j in [0, 1, -1]:
                    row = gridRow + i
                    cols = storeGrid.get(row, None)
                    if cols is not None:
                        col = gridCol + j
                        storeData = cols.get(col, None)
                        if storeData is not None:
                            if storeData.dsNodeId >= 0:
                                # cell already has a point added, and there can only be one 
                                # as only one stream link per cell
                                # TODO: should this be an error?
                                # prefer inlets as these shape the watershed
                                if point == Points._INLET:
                                    lost = storeData.dsNodeId
                                    storeData.dsNodeId = ioId
                                    QSWATUtils.loginfo('Could not retain point with id {0} in grid cell {1}:  {2} with id {3} placed there.'
                                                       .format(lost, storeData.num, Points.toString(point), storeData.dsNodeId))
                                else:
                                    lost = ioId
                                    QSWATUtils.loginfo('Could not place {0} with id {1} in grid cell {2}: point {3} already placed there.'
                                                       .format(Points.toString(point), lost, storeData.num, storeData.dsNodeId))
                                self._gv.topo.lostDsNodeIds.add(lost)
                            else:
                                storeData.dsNodeId = ioId
                                QSWATUtils.loginfo('Placed {0} with id {1} at {2!s} in grid cell {3}.'
                                                   .format(Points.toString(point), storeData.dsNodeId, pt, storeData.num))
                            found = True
                            break
                if found:
                    break        
            if not found:                
                QSWATUtils.error('Cannot place {0} with id {1} at {2!s} in grid row {3} column {4}'
                                 .format(Points.toString(point), ioId, pt, gridRow, gridCol), self._gv.isBatch)
        accRaster = None
        accArray = None
        return storeGrid, accTransform, minDrainArea, maxDrainArea
        
    def reduceToInletsOutlets(self, root: QgsLayerTree) -> Optional[str]:
        """Reduce inlets/outlets file to inlets and outlets only to delineate subbasins. Return reduced file."""
        if not self._dlg.useOutlets.isChecked():
            return None
        if self._gv.snapFile == '' or not os.path.exists(self._gv.snapFile):
            QSWATUtils.error('Cannot find snapped inlets/outlets file {0}'.format(self._gv.snapFile), self._gv.isBatch)
            return None
        snapLayer = QgsVectorLayer(self._gv.snapFile, 'Snapped points', 'ogr')
        if not snapLayer:
            return None
        # make copy of snapped inlets/outlets file
        base = os.path.splitext(self._gv.snapFile)[0]
        ioBase = base + 'io'
        pattern = base + '.*'
        for f in glob.iglob(pattern):
            fext = os.path.splitext(f)[1]
            shutil.copyfile(f, ioBase + fext)
        iOutlets: str = ioBase + '.shp'
        # remove layer if any
        QSWATUtils.removeLayer(iOutlets, root)
        ioLayer = QgsVectorLayer(iOutlets, 'inlets outlets only', 'ogr')
        inletIndex = self._gv.topo.getIndex(ioLayer, QSWATTopology._INLET)
        resIndex = self._gv.topo.getIndex(ioLayer, QSWATTopology._RES)
        ptsourceIndex = self._gv.topo.getIndex(ioLayer, QSWATTopology._PTSOURCE)
        if inletIndex < 0 or resIndex < 0 or ptsourceIndex < 0:
            return None
        others: List[int] = []
        for f in ioLayer.getFeatures():
            if f[inletIndex] == 0:
                if f[resIndex] > 0:
                    others.append(f.id())
            elif f[ptsourceIndex] > 0:
                others.append(f.id())
        if len(others) > 0:
            provider = ioLayer.dataProvider()
            provider.deleteFeatures(others)
            return iOutlets
        else:
            QSWATUtils.tryRemoveFiles(iOutlets)
            return cast(str, self._gv.snapFile)
    
    def hasInlets(self) -> Tuple[Optional[str], bool]:
        """
        If there is an inlets/outlets file with one or more inlets, returns a file with only those points
        and true, else returns None and false.
        
        Also stores ID, kind and locations of inlets and outlets."""
        self.inletOutletPoints.clear()
        if not self._dlg.useOutlets.isChecked():
            return None, False
        if self._gv.snapFile == '' or not os.path.exists(self._gv.snapFile):
            QSWATUtils.error('Cannot find snapped inlets/outlets file {0}'.format(self._gv.snapFile), self._gv.isBatch)
            return None, False
        snapLayer = QgsVectorLayer(self._gv.snapFile, 'Snapped points', 'ogr')
        if not snapLayer:
            return None, False
        idIndex = self._gv.topo.getIndex(snapLayer, QSWATTopology._ID, ignoreMissing=True)
        inletIndex = self._gv.topo.getIndex(snapLayer, QSWATTopology._INLET, ignoreMissing=True)
        resIndex = self._gv.topo.getIndex(snapLayer, QSWATTopology._RES, ignoreMissing=True)
        ptsourceIndex = self._gv.topo.getIndex(snapLayer, QSWATTopology._PTSOURCE, ignoreMissing=True)
        if idIndex < 0 or inletIndex < 0 or resIndex < 0 or ptsourceIndex < 0:
            return None, False
        # make copy of inlets/outlets file
        base = os.path.splitext(self._gv.snapFile)[0]
        iToOBase = base + 'IToO'
        pattern = base + '.*'
        for f in glob.iglob(pattern):
            fext = os.path.splitext(f)[1]
            shutil.copyfile(f, iToOBase + fext)
        iToOutlets = iToOBase + '.shp'
        iToOLayer = QgsVectorLayer(iToOutlets, 'inlets to outlets', 'ogr')
        # Remove from copy all but inlet points.
        # We could change them to outlets, but TauDEM does not take account of differences 
        # between kinds of point.
        # Also store inlets/outlets points for adding their IDs to the grid streams file.
        result = False
        others = []
        for f in iToOLayer.getFeatures():
            if f[inletIndex] == 0:
                if f[resIndex] == 0:
                    point = Points._OUTLET
                elif f[resIndex] == 1:
                    point = Points._RESERVOIR
                else:
                    point = Points._POND
                others.append(f.id())
            elif f[ptsourceIndex] == 0:
                point = Points._INLET
                result = True
            else:
                point = Points._POINTSOURCE
                others.append(f.id())
            self.inletOutletPoints[f[idIndex]] = (point, f.geometry().asPoint())
        if result:
            provider = iToOLayer.dataProvider()
            provider.deleteFeatures(others)
            return iToOutlets, True
        else:
            QSWATUtils.tryRemoveFiles(iToOutlets)
            return None, False
    
    def reduceAccumulationFile(self, accFile: str, outletFile: str) -> Optional[str]:
        """Return a new accumulation file with values of 0 for points upstream from outlets."""
        base = os.path.splitext(accFile)[0]
        base2 = base + 'IToO'
        upAccFile = base2 + 'ad8.tif'
        QSWATUtils.removeLayer(upAccFile, QgsProject.instance().layerTreeRoot())
        OK = TauDEMUtils.runAreaD8(self._gv.pFile, upAccFile, outletFile, None, self._dlg.numProcesses.value(), self._dlg.taudemOutput, contCheck=False, mustRun=True)
        if not OK:
            QSWATUtils.error('Failed to calculate accumulation upstream from inlets', self._gv.isBatch)
            return None
        # upAccFile has nodata values in the area we want to preserve in AccFile
        # need to reclassify nodata values to use in calculator, else they inevitably remain nodata
        # accumulation files have a nodata value of -1
        # we change the nodata value to -9999 to prevent -1 being regarded as nodata    
        ds = gdal.Open(upAccFile, gdal.GA_Update)
        band = ds.GetRasterBand(1)
        band.SetNoDataValue(-9999)
        ds = None
        accLayer = QgsRasterLayer(accFile, 'P')
        entry1 = QgsRasterCalculatorEntry()
        entry1.bandNumber = 1
        entry1.raster = accLayer
        entry1.ref = 'P@1'        
        acc2Layer = QgsRasterLayer(upAccFile, 'Q')
        entry2 = QgsRasterCalculatorEntry()
        entry2.bandNumber = 1
        entry2.raster = acc2Layer
        entry2.ref = 'Q@1'
        downAcc = base + 'DownAcc.tif'
        # The formula is equivalent to 'if Q@1 = -1 then P@1 else 0'
        # since Booleans expressions evaluate to 1 (true) or 0 (false).
        # The result will have positive accumulation values only below the inlets, 0 above them
        formula = '(Q@1 = -1) * P@1'
        calc = QgsRasterCalculator(formula, downAcc, 'GTiff', accLayer.extent(), accLayer.width(), accLayer.height(), [entry1, entry2],
                                   QgsCoordinateTransformContext())
        result = calc.processCalculation(feedback=None)
        if result == 0:
            assert os.path.exists(downAcc), 'QGIS calculator formula {0} failed to write output'.format(formula)
            QSWATUtils.copyPrj(accFile, downAcc)
        else:
            QSWATUtils.error('QGIS calculator formula {0} failed: returned {1}'.format(formula, result), self._gv.isBatch)
            return None     
        return downAcc
    
    @staticmethod
    def onEdge(row: int, col:int, gridSize: int) -> bool:
        """Returns true of (row, col) is on the edge of the cell."""
        return row == 0 or row == gridSize - 1 or col == 0 or col == gridSize - 1
    
    def addDownstreamData(self, storeGrid: Dict[int, Dict[int, GridData]], flowFile: str, gridSize: int, accTransform: Transform) -> bool:
        """Use flow direction flowFile to see to which grid cell a D8 step takes you from the max accumulation point and store in array."""
        pRaster = gdal.Open(flowFile, gdal.GA_ReadOnly)
        if pRaster is None:
            QSWATUtils.error('Cannot open flow direction file {0}'.format(flowFile), self._gv.isBatch)
            return False
        # for now read whole D8 flow direction file into memory
        pBand = pRaster.GetRasterBand(1)
        pTransform = pRaster.GetGeoTransform()
        if pTransform[1] != accTransform[1] or pTransform[5] != accTransform[5]:
            # problem with comparing floating point numbers
            # actually OK if the vertical/horizontal difference times the number of rows/columns
            # is less than half the depth/width of a cell
            if abs(pTransform[1] - accTransform[1]) * pBand.XSize > pTransform[1] * 0.5 or \
            abs(pTransform[5] - accTransform[5]) * pBand.YSize > abs(pTransform[5]) * 0.5:
                QSWATUtils.error('Flow direction and accumulation files must have same cell size', self._gv.isBatch)
                pRaster = None
                return False
        pArray = pBand.ReadAsArray(0, 0, pBand.XSize, pBand.YSize)
        # we know the cell sizes are sufficiently close;
        # accept the origins as the same if they are within a tenth of the cell size
        sameCoords = (pTransform == accTransform) or \
                    (abs(pTransform[0] - accTransform[0]) < pTransform[1] * 0.1 and
                     abs(pTransform[3] - accTransform[3]) < abs(pTransform[5]) * 0.1)
        for gridRow, gridCols in storeGrid.items():
            for gridCol, gridData in gridCols.items():
                if gridData.dsNodeId >= 0:
                    # check if it is an outlet
                    point = self.inletOutletPoints[gridData.dsNodeId][0]
                    if point == Points._OUTLET:
                        # nothing to do for this grid cell
                        continue
                # since we have same cell sizes, can simplify conversion from accumulation row, col to direction row, col
                if sameCoords:
                    accToPRow = 0
                    accToPCol = 0
                else:
                    accToPCol = int((accTransform[0] - pTransform[0]) / accTransform[1] + 0.5)
                    accToPRow = int((accTransform[3] - pTransform[3]) / accTransform[5] + 0.5)
                    #pRow = QSWATTopology.yToRow(QSWATTopology.rowToY(gridData.maxRow, accTransform), pTransform)
                    #pCol = QSWATTopology.xToCol(QSWATTopology.colToX(gridData.maxCol, accTransform), pTransform)
                currentPRow = gridData.maxRow + accToPRow
                currentPCol = gridData.maxCol + accToPCol
                # try to find downstream grid cell.  If we fail downstram number left as -1, which means outlet
                # rounding of large accumulation values means that the maximum accumulation point found
                # may not be at the outflow point, so we need to move until we find a new grid cell, or hit a map edge
                maxSteps = 2 * gridSize
                found = False
                while not found:
                    if 0 <= currentPRow < pBand.YSize and 0 <= currentPCol < pBand.XSize:
                        direction = pArray[currentPRow, currentPCol]
                    else:
                        break
                    # apply a step in direction
                    if 1 <= direction <= 8:
                        currentPRow = currentPRow + QSWATUtils._dY[direction - 1]
                        currentPCol = currentPCol + QSWATUtils._dX[direction - 1]
                    else:
                        break
                    currentAccRow = currentPRow - accToPRow
                    currentAccCol = currentPCol - accToPCol
                    currentGridRow = currentAccRow // gridSize
                    currentGridCol = currentAccCol // gridSize
                    found = currentGridRow != gridRow or currentGridCol != gridCol
                    if not found:
                        maxSteps -= 1
                        if maxSteps <= 0:
                            x0, y0 = QSWATTopology.cellToProj(gridData.maxCol, gridData.maxRow, accTransform)
                            x, y = QSWATTopology.cellToProj(currentAccCol, currentAccRow, accTransform)
                            QSWATUtils.error('Loop in flow directions in grid id {4} starting from ({0},{1}) and so far reaching ({2},{3})'.
                                             format(int(x0), int(y0), int(x), int(y), gridData.num), self._gv.isBatch)
                            break
                if found:
                    cols =  storeGrid.get(currentGridRow, None)
                    if cols is not None:
                        currentData = cols.get(currentGridCol, None)
                        if currentData is not None:
                            if currentData.maxAcc < gridData.maxAcc:
                                QSWATUtils.loginfo("WARNING: while calculating stream drainage, target grid cell {0} has lower maximum accumulation {1} than source grid cell {2}'s accumulation {3}"  \
                                                   .format(currentData.num, currentData.maxAcc, gridData.num, gridData.maxAcc))
                            gridData.downNum = currentData.num
                            gridData.downRow = currentGridRow
                            gridData.downCol = currentGridCol
                            #if gridData.num <= 5:
                            #    QSWATUtils.loginfo('Grid ({0},{1}) drains to acc ({2},{3}) in grid ({4},{5})'.format(gridRow, gridCol, currentAccCol, currentAccRow, currentGridRow, currentGridCol))
                            #    QSWATUtils.loginfo('{0} at {1},{2} given down id {3}'.format(gridData.num, gridRow, gridCol, gridData.downNum))
                            if gridData.downNum == gridData.num:
                                x, y = QSWATTopology.cellToProj(gridData.maxCol, gridData.maxRow, accTransform)
                                maxAccPoint = QgsPointXY(x, y)
                                QSWATUtils.loginfo('Grid ({0},{1}) id {5} at ({2},{3}) which is {4} draining to ({6},{7})'.
                                                     format(gridCol, gridRow, gridData.maxCol, gridData.maxRow, maxAccPoint.toString(),
                                                            gridData.num, currentAccCol, currentAccRow))
                                gridData.downNum = -1
                            #assert gridData.downNum != gridData.num
                            storeGrid[gridRow][gridCol] = gridData
        pRaster = None
        pArray = None
        return True

    # noinspection PyCallByClass
    def writeGridShapefile(self, storeGrid: Dict[int, Dict[int, GridData]], flowFile: str, gridSize: int, accTransform: Transform) -> None:
        """Write grid data to grid shapefile.  Also writes centroids dictionary."""
        self.progress('Writing grid ...')
        gridFile = QSWATUtils.join(self._gv.shapesDir, 'grid.shp')
        root = QgsProject.instance().layerTreeRoot()
        ft = FileTypes._GRID
        legend = FileTypes.legend(ft)
        if QSWATUtils.shapefileExists(gridFile):
            gridLayer = QSWATUtils.getLayerByFilename(root.findLayers(), gridFile, ft, 
                                                      None, None, None)[0]
            if gridLayer is None:
                gridLayer = QgsVectorLayer(gridFile, '{0} ({1})'.format(legend, QFileInfo(gridFile).baseName()), 'ogr')
            # labels can cause crashes if we try to recalculate this file
            gridLayer.setLabelsEnabled(False)
            if not QSWATUtils.removeAllFeatures(gridLayer):
                QSWATUtils.error('Failed to delete features from {0}.  Please delete the file manually and try again'.format(gridFile), self._gv.isBatch)
                return
            fields = gridLayer.fields()
        else:
            QSWATUtils.removeLayer(gridFile, root)
            fields = QgsFields()
            fields.append(QgsField(QSWATTopology._POLYGONID, QVariant.Int))
            fields.append(QgsField(QSWATTopology._DOWNID, QVariant.Int))
            fields.append(QgsField(Parameters._AREA, QVariant.Double))
            fields.append(QgsField(QSWATTopology._SUBBASIN, QVariant.Int))
            fields.append(QgsField(QSWATTopology._LAKEID, QVariant.Int))
            writer = QgsVectorFileWriter.create(gridFile, fields,  QgsWkbTypes.Polygon, self._gv.crsProject, 
                                                QgsCoordinateTransformContext(), self._gv.vectorFileWriterOptions)
            if writer.hasError() != QgsVectorFileWriter.NoError:
                QSWATUtils.error('Cannot create grid shapefile {0}: {1}'.format(gridFile, writer.errorMessage()), self._gv.isBatch)
                return
            # flush
            writer.flushBuffer()
            del writer
            QSWATUtils.copyPrj(flowFile, gridFile)
            gridLayer = QgsVectorLayer(gridFile, '{0} ({1})'.format(legend, QFileInfo(gridFile).baseName()), 'ogr')
        provider = gridLayer.dataProvider()
        idIndex = fields.indexFromName(QSWATTopology._POLYGONID)
        downIndex = fields.indexFromName(QSWATTopology._DOWNID)
        areaIndex = fields.indexFromName(Parameters._AREA)
        ul_x, x_size, _, ul_y, _, y_size = accTransform
        xDiff = x_size * gridSize * 0.5
        yDiff = y_size * gridSize * 0.5
        self._gv.topo.basinCentroids = dict()
        for gridRow, gridCols in storeGrid.items():
            # grids can be big so we'll add one row at a time
            centreY = (gridRow + 0.5) * self._gv.gridSize * y_size + ul_y
            features = list()
            for gridCol, gridData in gridCols.items():
                centreX = (gridCol + 0.5) * self._gv.gridSize * x_size + ul_x
                # this is strictly not the centroid for incomplete grid squares on the edges,
                # but will make little difference.  
                # Needs to be centre of grid for correct identification of landuse, soil and slope rows
                # when creating HRUs.
                self._gv.topo.basinCentroids[gridData.num] = (centreX, centreY)
                x1 = centreX - xDiff
                x2 = centreX + xDiff
                y1 = centreY - yDiff
                y2 = centreY + yDiff
                ring = [QgsPointXY(x1, y1), QgsPointXY(x2, y1), QgsPointXY(x2, y2), QgsPointXY(x1, y2), QgsPointXY(x1, y1)]
                feature = QgsFeature()
                feature.setFields(fields)
                feature.setAttribute(idIndex, gridData.num)
                feature.setAttribute(downIndex, gridData.downNum)
                # convert area in raster cell count to area of grid cell in hectares
                feature.setAttribute(areaIndex, abs(gridData.area * x_size * y_size * self._gv.horizontalFactor * self._gv.horizontalFactor) / 1E4)
                geometry = QgsGeometry.fromPolygonXY([ring])
                feature.setGeometry(geometry)
                features.append(feature)
            if not provider.addFeatures(features):
                QSWATUtils.error('Unable to add features to grid shapefile {0}'.format(gridFile), self._gv.isBatch)
                return
        # load grid shapefile above subbasins layer
        subbasinsLayer = QSWATUtils.getLayerByLegend(QSWATUtils._SUBBASINSLEGEND, root.findLayers())
        if subbasinsLayer is not None:
            subbasinsLayer.setItemVisibilityChecked(False)
        gridLayer = QSWATUtils.getLayerByFilename(root.findLayers(), gridFile, FileTypes._GRID, 
                                                  self._gv, subbasinsLayer, QSWATUtils._WATERSHED_GROUP_NAME)[0]
        if not gridLayer:
            QSWATUtils.error('Failed to load grid shapefile {0}'.format(gridFile), self._gv.isBatch)
            return
        gridLayer.setLabelsEnabled(False)
        # don't expand legend for grid layer
        # have to start by getting layerTreeLayer
        treeLayer = QSWATUtils.getLayerByLegend(QSWATUtils._GRIDLEGEND, root.findLayers())
        if treeLayer is not None:
            treeLayer.setExpanded(False)
        gridLayer.triggerRepaint()
        # preserve access to subbasinsFile so can use to clip when making valley depths later
        # the gridFile can be reduced if there are inlets, and its convex hull will not be appropriate
        # for flow-based analysis as we will run off the edge
        self.clipperFile = self._gv.subbasinsFile
        self._gv.subbasinsFile = gridFile
        # make sure gridFile is used for making aquifers shapefile
        self._gv.subsNoLakesFile = ''
        
    def writeGridStreamsShapefile(self, storeGrid: Dict[int, Dict[int, GridData]], flowFile: str, minDrainArea: float, maxDrainArea: float, 
                                  accTransform: Transform) -> int:
        """Write grid data to grid streams shapefile."""
        self.progress('Writing grid streams ...')
        gridStreamsFile = QSWATUtils.join(self._gv.shapesDir, 'gridstreams.shp')
        root = QgsProject.instance().layerTreeRoot()
        ft = FileTypes._GRIDSTREAMS
        legend = FileTypes.legend(ft)
        if QSWATUtils.shapefileExists(gridStreamsFile):
            gridStreamsLayer = QSWATUtils.getLayerByFilename(root.findLayers(), gridStreamsFile, ft, 
                                                      None, None, None)[0]
            if gridStreamsLayer is None:
                gridStreamsLayer = QgsVectorLayer(gridStreamsFile, '{0} ({1})'.format(legend, QFileInfo(gridStreamsFile).baseName()), 'ogr')
            if not QSWATUtils.removeAllFeatures(gridStreamsLayer):
                QSWATUtils.error('Failed to delete features from {0}.  Please delete the file manually and try again'.format(gridStreamsFile), self._gv.isBatch)
                return -1
            fields = gridStreamsLayer.fields()
        else:
            QSWATUtils.removeLayer(gridStreamsFile, root)
            fields = QgsFields()
            fields.append(QgsField(QSWATTopology._LINKNO, QVariant.Int))
            fields.append(QgsField(QSWATTopology._DSLINKNO, QVariant.Int))
            fields.append(QgsField(QSWATTopology._DSNODEID, QVariant.Int))
            fields.append(QgsField(QSWATTopology._WSNO, QVariant.Int))
            fields.append(QgsField(QSWATTopology._DRAINAGE, QVariant.Double))
            fields.append(QgsField(QSWATTopology._PENWIDTH, QVariant.Double))
            writer = QgsVectorFileWriter.create(gridStreamsFile, fields, QgsWkbTypes.LineString, self._gv.crsProject, 
                                                QgsCoordinateTransformContext(), self._gv.vectorFileWriterOptions)
            if writer.hasError() != QgsVectorFileWriter.NoError:
                QSWATUtils.error('Cannot create streams shapefile {0}: {1}'.format(gridStreamsFile, writer.errorMessage()), self._gv.isBatch)
                return -1
            # flush writer
            writer.flushBuffer()
            del writer
            QSWATUtils.copyPrj(flowFile, gridStreamsFile)
            gridStreamsLayer = QgsVectorLayer(gridStreamsFile, '{0} ({1})'.format(legend, QFileInfo(gridStreamsFile).baseName()), 'ogr')
        provider = gridStreamsLayer.dataProvider()
        linkIndex = fields.indexFromName(QSWATTopology._LINKNO)
        downIndex = fields.indexFromName(QSWATTopology._DSLINKNO)
        dsNodeIndex = fields.indexFromName(QSWATTopology._DSNODEID)
        wsnoIndex = fields.indexFromName(QSWATTopology._WSNO)
        drainIndex = fields.indexFromName(QSWATTopology._DRAINAGE)
        penIndex = fields.indexFromName(QSWATTopology._PENWIDTH)
        if maxDrainArea > minDrainArea: # guard against division by zero
            rng = maxDrainArea - minDrainArea
            areaToPenWidth = lambda x: (x - minDrainArea) * 1.8 / rng + 0.2
        else:
            areaToPenWidth = lambda _: 1.0
        numOutlets = 0
        for gridCols in storeGrid.values():
            # grids can be big so we'll add one row at a time
            features = list()
            for gridData in gridCols.values():
                downNum = gridData.downNum
                sourceX, sourceY = QSWATTopology.cellToProj(gridData.maxCol, gridData.maxRow, accTransform)
                if downNum > 0:
                    downData = storeGrid[gridData.downRow][gridData.downCol]
                    targetX, targetY = QSWATTopology.cellToProj(downData.maxCol, downData.maxRow, accTransform)
                else:
                    targetX, targetY = sourceX, sourceY
                    numOutlets += 1
                # respect default 'start at outlet' of TauDEM
                link = [QgsPointXY(targetX, targetY), QgsPointXY(sourceX, sourceY)]
                feature = QgsFeature()
                feature.setFields(fields)
                feature.setAttribute(linkIndex, gridData.num)
                feature.setAttribute(downIndex, downNum)
                feature.setAttribute(dsNodeIndex, gridData.dsNodeId)
                feature.setAttribute(wsnoIndex, gridData.num)
                # area needs coercion to float or will not write
                feature.setAttribute(drainIndex, float(gridData.drainArea))
                # set pen width to value in range 0 .. 2
                feature.setAttribute(penIndex, float(areaToPenWidth(gridData.drainArea)))
                geometry = QgsGeometry.fromPolylineXY(link)
                feature.setGeometry(geometry)
                features.append(feature)
            if not provider.addFeatures(features):
                QSWATUtils.error('Unable to add features to grid streams shapefile {0}'.format(gridStreamsFile), self._gv.isBatch)
                return -1
        # load grid streams shapefile
        # try to load above grid layer
        gridLayer = QSWATUtils.getLayerByLegend(QSWATUtils._GRIDLEGEND, root.findLayers())
        gridStreamsLayer = QSWATUtils.getLayerByFilename(root.findLayers(), gridStreamsFile, FileTypes._GRIDSTREAMS, 
                                                         self._gv, gridLayer, QSWATUtils._WATERSHED_GROUP_NAME)[0]
        if not gridStreamsLayer:
            QSWATUtils.error('Failed to load grid streams shapefile {0}'.format(gridStreamsFile), self._gv.isBatch)
            return -1
        # make stream width dependent on drainage values (drainage is accumulation, ie number of dem cells draining to start of stream)
        FileTypes.colourStreams(gridStreamsLayer, QSWATTopology._PENWIDTH, QSWATTopology._DRAINAGE)
        treeModel = QgsLayerTreeModel(root)
        gridStreamsTreeLayer = root.findLayer(gridStreamsLayer.id())
        assert gridStreamsTreeLayer is not None
        treeModel.refreshLayerLegend(gridStreamsTreeLayer)
        self._gv.streamFile = gridStreamsFile
        self.streamDrainage = True
        # remove visibility from streams layer, if any
        streamsLayer = QSWATUtils.getLayerByLegend(QSWATUtils._STREAMSLEGEND, root.findLayers())
        if streamsLayer is not None:
            streamsLayer.setItemVisibilityChecked(False)
        # remove visibility from channels layer, if any
        channelsLayer = QSWATUtils.getLayerByLegend(QSWATUtils._CHANNELSLEGEND, root.findLayers())
        if channelsLayer is not None:
            streamsLayer.setItemVisibilityChecked(False)
        self.progress('')
        return numOutlets
    
    def writeDrainageStreamsShapefile(self, subbasinsFile: str, subbasinsLayer: QgsVectorLayer, 
                                      outletLayer: Optional[QgsVectorLayer], root: QgsLayerTree) -> Optional[str]:
        """Write streams shapefile with drainage from subbasinsLayer if grid drainage, else
        from drainage defined in csv file."""
        self._dlg.setCursor(Qt.ArrowCursor)
        outlets = []
        self.inletOutletPoints = dict()
        if outletLayer is not None:
            inletIndex = self._gv.topo.getIndex(outletLayer, QSWATTopology._INLET, ignoreMissing=True)
            resIndex = self._gv.topo.getIndex(outletLayer, QSWATTopology._RES, ignoreMissing=True)
            ptsrcIndex = self._gv.topo.getIndex(outletLayer, QSWATTopology._PTSOURCE, ignoreMissing=True)
            idIndex = self._gv.topo.getIndex(outletLayer, QSWATTopology._ID, ignoreMissing=True)
            for feature in outletLayer.getFeatures():
                if inletIndex >= 0 and feature[inletIndex] == 1:
                    if ptsrcIndex >= 0 and feature[ptsrcIndex] == 1:
                        point = Points._POINTSOURCE
                    else:
                        point = Points._INLET
                elif resIndex >= 0:
                    if feature[resIndex] == 1:
                        point = Points._RESERVOIR
                    else:
                        point = Points._POND
                else:
                    point = Points._OUTLET
                    outlets.append(feature.geometry().asPoint())
                if idIndex >= 0:
                    self.inletOutletPoints[feature[idIndex]] = (point, feature.geometry().asPoint())
        if not self.gridDrainage:
            self.drainageTable = self._dlg.selectStreams.text()
            if not os.path.exists(self.drainageTable):
                QSWATUtils.error('Please select a drainage csv file', self._gv.isBatch)
                return None
        self.progress('Writing drainage grid streams ...')
        time1 = time.process_time()
        drainStreamsFile: str = QSWATUtils.join(self._gv.shapesDir, 'drainstreams.shp')
        ft = FileTypes._DRAINSTREAMS
        legend = FileTypes.legend(ft)
        if QSWATUtils.shapefileExists(drainStreamsFile):
            drainStreamsLayer = QSWATUtils.getLayerByFilename(root.findLayers(), drainStreamsFile, ft, 
                                                              None, None, None)[0]
            if drainStreamsLayer is None:
                drainStreamsLayer = QgsVectorLayer(drainStreamsFile, '{0} ({1})'.format(legend, QFileInfo(drainStreamsFile).baseName()), 'ogr')
            if not QSWATUtils.removeAllFeatures(drainStreamsLayer):
                QSWATUtils.error('Failed to delete features from {0}.  Please delete the file manually and try again'.format(drainStreamsFile), self._gv.isBatch)
                return None
            fields = drainStreamsLayer.fields()
        else:
            QSWATUtils.removeLayer(drainStreamsFile, root)
            fields = QgsFields()
            fields.append(QgsField(QSWATTopology._LINKNO, QVariant.Int))
            fields.append(QgsField(QSWATTopology._DSLINKNO, QVariant.Int))
            fields.append(QgsField(QSWATTopology._DSNODEID, QVariant.Int))
            fields.append(QgsField(QSWATTopology._WSNO, QVariant.Int))
            writer = QgsVectorFileWriter.create(drainStreamsFile, fields, QgsWkbTypes.LineString, self._gv.crsProject, 
                                                QgsCoordinateTransformContext(), self._gv.vectorFileWriterOptions)
            if writer.hasError() != QgsVectorFileWriter.NoError:
                QSWATUtils.error('Cannot create grid streams shapefile {0}: {1}'.format(drainStreamsFile, writer.errorMessage()), self._gv.isBatch)
                return None
            # flush
            writer.flushBuffer()
            del writer
            QSWATUtils.copyPrj(subbasinsFile, drainStreamsFile)
            drainStreamsLayer = QgsVectorLayer(drainStreamsFile, '{0} ({1})'.format(legend, QFileInfo(drainStreamsFile).baseName()), 'ogr')
        provider = drainStreamsLayer.dataProvider()
        linkIndex = fields.indexFromName(QSWATTopology._LINKNO)
        dslinkIndex = fields.indexFromName(QSWATTopology._DSLINKNO)
        dsnodeIndex = fields.indexFromName(QSWATTopology._DSNODEID)
        wsnoIndex = fields.indexFromName(QSWATTopology._WSNO)
        basinIndex = self._gv.topo.getIndex(subbasinsLayer, QSWATTopology._POLYGONID)
        if basinIndex < 0:
            return None
        downBasinIndex = self._gv.topo.getIndex(subbasinsLayer, QSWATTopology._DOWNID)
        if downBasinIndex < 0:
            return None
        features = list()
        self._gv.topo.basinCentroids.clear()
        toRemove: List[int] = list()
        areaFactor = self._gv.horizontalFactor * self._gv.horizontalFactor
        if self.gridDrainage:
            centroids: Dict[int, Tuple[int, QgsPointXY, Tuple[float, float], Tuple[float, float]]] = dict()
            for cell in subbasinsLayer.getFeatures():
                basin = cell[basinIndex]
                area = int(cell.geometry().area() * areaFactor)
                if area == 0:
                    # grid cells collected by clipping with aquifers can be degenerate ones at edge with close to zero area:
                    # remove them
                    toRemove.append(cell.id())
                    QSWATUtils.loginfo('Zero area grid cell {0} removed'.format(basin))
                    continue
                downBasin = cell[downBasinIndex]
                centroid, (xmin, xmax), (ymin, ymax) = QSWATUtils.centreGridCell(cell)
                centroids[basin] = (downBasin, centroid, (xmin, xmax), (ymin, ymax))
                self._gv.topo.basinCentroids[basin] = centroid
            if len(toRemove) > 0:
                subProvider = subbasinsLayer.dataProvider()
                subProvider.deleteFeatures(toRemove)
            for basin, (downBasin, source, (xmin, xmax), (ymin, ymax)) in centroids.items():
                if downBasin < 0:
                    target = QSWATUtils.nearestPoint(source, outlets)
                else:
                    down = centroids.get(downBasin, None)
                    if down is None:
                        QSWATUtils.error('Failed to find target grid cell in {0} for drain from {1} to {2}'.format(subbasinsFile, basin, downBasin), self._gv.isBatch)
                        return None
                    else:
                        target = down[1]
                dsnode = -1
                for nodeId, (point, pt) in self.inletOutletPoints.items():
                    if xmin <= pt.x() < xmax and ymin <= pt.y() < ymax:
                        QSWATUtils.loginfo('Placed {0} with id {1} at {2!s} in grid cell {3}'
                                            .format(Points.toString(point), nodeId, pt, basin))
                        dsnode = nodeId
                        break
                if dsnode >= 0: # avoid any danger of adding point twice (and speed up for future cells)
                    del self.inletOutletPoints[dsnode]
                link = [source, target]
                feature = QgsFeature()
                feature.setFields(fields)
                feature.setAttribute(linkIndex, basin)
                feature.setAttribute(dslinkIndex, downBasin)
                feature.setAttribute(dsnodeIndex, dsnode)
                feature.setAttribute(wsnoIndex, basin)
                geometry = QgsGeometry.fromPolylineXY(link)
                feature.setGeometry(geometry)
                features.append(feature)        
        else:
            if basinIndex < 0:
                return None
            centroids = dict()
            for cell in subbasinsLayer.getFeatures():
                basin = cell[basinIndex]
                downBasin = cell[downBasinIndex]
                centroid, (xmin, xmax), (ymin, ymax) = QSWATUtils.centreGridCell(cell)
                centroids[basin] = (downBasin, centroid, (xmin, xmax), (ymin, ymax))
                self._gv.topo.basinCentroids[basin] = centroid
            with open(self.drainageTable, 'r', newline='') as csvFile:
                dialect = csv.Sniffer().sniff(csvFile.read(1000))  # sample size 1000 bytes is arbitrary
                csvFile.seek(0)
                drainage = csv.reader(csvFile, dialect)
                # skip header
                next(drainage)
                for row in drainage:
                    basin = int(row[0])
                    downBasin = int(row[1])
                    assert basin != downBasin, 'Drainage has {0} downstream from itself'.format(basin)
                    # we ignore down basins data in centroids map since the drainage is determined by the table
                    (_, source, (xmin, xmax), (ymin, ymax)) = centroids.get(basin, (None, None, None, None))  # type: ignore
                    if source is None:
                        QSWATUtils.error('Failed to find source grid cell in {2} for drain from {0} to {1}'.format(basin, downBasin, subbasinsFile), self._gv.isBatch)
                        return None
                    if downBasin < 0:
                        target = QSWATUtils.nearestPoint(source, outlets)
                    else:
                        (_, target, _, _) = centroids.get(downBasin, (None, None, None, None))
                        if target is None:
                            QSWATUtils.error('Failed to find target grid cell in {2} for drain from {0} to {1}'.format(basin, downBasin, subbasinsFile), self._gv.isBatch)
                            return None
                    dsnode = -1
                    for nodeId, (point, pt) in self.inletOutletPoints.items():
                        if xmin <= pt.x() < xmax and ymin <= pt.y() < ymax:
                            QSWATUtils.loginfo('Placed {0} with id {1} at {2!s} in grid cell {3}'
                                               .format(Points.toString(point), nodeId, pt, basin))
                            dsnode = nodeId
                            break
                    if dsnode >= 0: # avoid any danger of adding point twice (and speed up for future cells)
                        del self.inletOutletPoints[dsnode]
                    link = [source, target]
                    feature = QgsFeature()
                    feature.setFields(fields)
                    feature.setAttribute(linkIndex, basin)
                    feature.setAttribute(dslinkIndex, downBasin)
                    feature.setAttribute(dsnodeIndex, dsnode)
                    feature.setAttribute(wsnoIndex, basin)
                    geometry = QgsGeometry.fromPolylineXY(link)
                    feature.setGeometry(geometry)
                    features.append(feature)
            if len(features) != subbasinsLayer.featureCount():
                QSWATUtils.information('WARNING: number of drainage links ({0}) different from number of grid cells ({1})'.format(len(features), subbasinsLayer.featureCount()), self._gv.isBatch)
        if not provider.addFeatures(features):
            QSWATUtils.error('Unable to add features to grid streams shapefile {0}'.format(drainStreamsFile), self._gv.isBatch)
            return None
        unplaced = list(self.inletOutletPoints.keys())
        if len(unplaced) > 0:
            QSWATUtils.information('Warning: failed to place inlet/outlet points with IDs {0!s}'.format(unplaced), self._gv.isBatch)
        time2 = time.process_time()
        QSWATUtils.loginfo('Wrinting drainage grid streams took {0} seconds'.format(int(time2 - time1)))
        # load grid streams shapefile
        # try to load above subbasins layer layer
        drainStreamsLayer = QSWATUtils.getLayerByFilename(root.findLayers(), drainStreamsFile, FileTypes._DRAINSTREAMS, 
                                                          self._gv, subbasinsLayer, QSWATUtils._WATERSHED_GROUP_NAME)[0]
        if not drainStreamsLayer:
            QSWATUtils.error('Failed to load grid streams shapefile {0}'.format(drainStreamsFile), self._gv.isBatch)
            return None
        self._gv.streamFile = drainStreamsFile
        # remove visibility from streams layer, if any
        streamsLayer = QSWATUtils.getLayerByLegend(QSWATUtils._STREAMSLEGEND, root.findLayers())
        if streamsLayer is not None:
            streamsLayer.setItemVisibilityChecked(False)
        # remove visibility from channels layer, if any
        channelsLayer = QSWATUtils.getLayerByLegend(QSWATUtils._CHANNELSLEGEND, root.findLayers())
        if channelsLayer is not None:
            channelsLayer.setItemVisibilityChecked(False)
        self.progress('')
        return drainStreamsFile
    
    def runLandscape(self) -> None:
        """Run the landscape dialog and create files as requested."""
        if self._gv.existingWshed:
            # will need a d8 flow direction and a channels raster
            (base, suffix) = os.path.splitext(self._gv.demFile)
            # check if we have flow direction because we are running an existing ArcSWAT project
            proj = QgsProject.instance()
            title = proj.title()
            arcPFile, found = proj.readEntry(title, 'delin/arcPFile', '')
            arcPFile = proj.readPath(arcPFile)
            root = QgsProject.instance().layerTreeRoot()
            if found and os.path.isfile(arcPFile):
                self._gv.pFile = arcPFile
            else:
                sd8File = base + 'sd8' + suffix
                pFile = base + 'p' + suffix
                QSWATUtils.removeLayer(sd8File, root)
                QSWATUtils.removeLayer(pFile, root)
                self.progress('D8FlowDir ...')
                ok = TauDEMUtils.runD8FlowDir(self._gv.felFile, sd8File, pFile, self._dlg.numProcesses.value(), self._dlg.taudemOutput)   
                if not ok:
                    self.cleanUp(3)
                    return
                self._gv.pFile = pFile
            channelraster = base + 'srcChannel' + suffix
            demLayer, _ = QSWATUtils.getLayerByFilename(root.findLayers(), self._gv.demFile, FileTypes._DEM,
                                                        self._gv, None, QSWATUtils._WATERSHED_GROUP_NAME)
            self.streamToRaster(demLayer, self._gv.channelFile, channelraster, root)
            self._gv.srcChannelFile = channelraster
        self.makeDistancesToOutlets()
        numCellsSt = int(self._dlg.numCellsSt.text())
        channelThresh = int(self._dlg.numCellsCh.text())
        # set branch method threshold to twice sqare root of stream threshold in square metres
        branchThresh = int(2 * math.sqrt(numCellsSt * self._gv.topo.dx * self._gv.topo.dy))
        clipperFile = self._gv.subbasinsFile if self.clipperFile == '' else self.clipperFile
        self.L = Landscape(self._gv, self._dlg.taudemOutput, self._dlg.numProcesses.value(), self.progress)
        self.L.run(numCellsSt, channelThresh, branchThresh, clipperFile, self.thresholdChanged)
        
    def deleteFloodFiles(self, root: QgsLayerTree) -> None:
        """Delete any files (and their layers if any) matching *flood*.* in Flood directory."""
        pattern = QSWATUtils.join(self._gv.floodDir, '*flood*.*')
        for f in glob.iglob(pattern):
            QSWATUtils.tryRemoveLayerAndFiles(f, root)
    
    @staticmethod                   
    def moveD8(row: int, col: int, direction: int) -> Tuple[int, int]:
        """Return row and column after 1 step in D8 direction."""
        if 1 <= direction <= 8:
            dir0 = direction - 1
            return row + QSWATUtils._dY[dir0], col + QSWATUtils._dX[dir0]
        else: # we have run off the edge of the direction grid
            return -1, -1 

    def streamToRaster(self, demLayer: QgsRasterLayer, streamFile: str, rasterFile: str, root: QgsLayerTree) -> None:
        """Use rasterize to generate a raster for the streams or channels, with a fixed value of 1 along the streams, zero elsewhere."""
        QSWATUtils.tryRemoveLayerAndFiles(rasterFile, root)
        assert not os.path.exists(rasterFile)
        extent = demLayer.extent()
        xMin = extent.xMinimum()
        xMax = extent.xMaximum()
        yMin = extent.yMinimum()
        yMax = extent.yMaximum()
        xSize = demLayer.rasterUnitsPerPixelX()
        ySize = demLayer.rasterUnitsPerPixelY()
        command = 'gdal_rasterize -burn 1 -init 0 -a_nodata -9999 -te {0!s} {1!s} {2!s} {3!s} -tr {4!s} {5!s} -ot Int32 "{6}" "{7}"'.format(xMin, yMin, xMax, yMax, xSize, ySize, streamFile, rasterFile)
        QSWATUtils.loginfo(command)
        os.system(command)
        assert os.path.exists(rasterFile)
        QSWATUtils.copyPrj(streamFile, rasterFile)
        
    def createSnapOutletFile(self, outletLayer: QgsVectorLayer, streamLayer: QgsVectorLayer, channelLayer: QgsVectorLayer, 
                             outletFile: str, snapFile: str, root: QgsLayerTree) -> bool:
        """
        Create inlets/outlets file with points snapped to streams or channels.
        
        Inlets and outlets are snapped to the coarser streamLayer and reservoirs and point sources to the finer channelLayer.
        """
        if outletLayer.featureCount() == 0:
            QSWATUtils.error('The outlet layer {0} has no points'.format(outletLayer.name()), self._gv.isBatch)
            return False
        try:
            snapThreshold = int(self._dlg.snapThreshold.text())
        except Exception:
            QSWATUtils.error('Cannot parse snap threshold {0} as integer.'.format(self._dlg.snapThreshold.text()), self._gv.isBatch)
            return False
        if not Delineation.createOutletFile(snapFile, outletFile, False, root, self._gv):
            return False
        if self._gv.isBatch:
            QSWATUtils.information('Snap threshold: {0!s} metres'.format(snapThreshold), self._gv.isBatch)
        snapLayer = QgsVectorLayer(snapFile, 'Snapped inlets/outlets ({0})'.format(QFileInfo(snapFile).baseName()), 'ogr')
        idIndex = self._gv.topo.getIndex(outletLayer, QSWATTopology._ID)
        inletIndex = self._gv.topo.getIndex(outletLayer, QSWATTopology._INLET)
        resIndex = self._gv.topo.getIndex(outletLayer, QSWATTopology._RES)
        ptsourceIndex = self._gv.topo.getIndex(outletLayer, QSWATTopology._PTSOURCE)
        ptIdIndex = self._gv.topo.getIndex(outletLayer, QSWATTopology._POINTID, ignoreMissing=True)
        if ptIdIndex < 0:
            ptIdIndex = QSWATTopology.makePositiveOutletIds(outletLayer)
            if ptIdIndex < 0:
                QSWATUtils.error('Failed to add PointId field to inlets/outlets file {0}'.format(QSWATUtils.layerFilename(outletLayer)), self._gv.isBatch)
                return False
        idSnapIndex = self._gv.topo.getIndex(snapLayer, QSWATTopology._ID)
        inletSnapIndex = self._gv.topo.getIndex(snapLayer, QSWATTopology._INLET)
        resSnapIndex = self._gv.topo.getIndex(snapLayer, QSWATTopology._RES)
        ptsourceSnapIndex = self._gv.topo.getIndex(snapLayer, QSWATTopology._PTSOURCE)
        # with conversion from QSWAT, snap layer may lack PointId field
        ptIdSnapIndex = self._gv.topo.getIndex(snapLayer, QSWATTopology._POINTID, ignoreMissing=True)
        snapProvider = snapLayer.dataProvider()
        if ptIdSnapIndex < 0:
            snapProvider.addAttributes([QgsField(QSWATTopology._POINTID, QVariant.Int)])
            outletLayer.updateFields()
            ptIdSnapIndex = snapProvider.fieldNameIndex(QSWATTopology._POINTID)
        fields = snapProvider.fields()
        ds = gdal.Open(self._gv.demFile, gdal.GA_ReadOnly)
        transform = ds.GetGeoTransform()
        count = 0
        errorCount = 0
        outletCount = 0
        for feature in outletLayer.getFeatures():
            pid = feature[idIndex]
            inlet = feature[inletIndex]
            res = feature[resIndex]
            ptsource = feature[ptsourceIndex]
            ptId = feature[ptIdIndex]
            inletOrOutlet = res == 0 if inlet == 0 else ptsource == 0
            reachLayer = streamLayer if inletOrOutlet else channelLayer
            point = feature.geometry().asPoint()
            point1 = QSWATTopology.snapPointToReach(reachLayer, point, snapThreshold, transform, self._gv.isBatch)
            if point1 is None: 
                errorCount += 1
                continue
            if inlet == 0 and res == 0:
                outletCount += 1
            # QSWATUtils.information('Snap point at ({0:.2F}, {1:.2F})'.format(point1.x(), point1.y()), self._gv.isBatch)
            feature1 = QgsFeature()
            feature1.setFields(fields)
            feature1.setAttribute(idSnapIndex, pid)
            feature1.setAttribute(inletSnapIndex, inlet)
            feature1.setAttribute(resSnapIndex, res)
            feature1.setAttribute(ptsourceSnapIndex, ptsource)
            feature1.setAttribute(ptIdSnapIndex, ptId)
            feature1.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(point1.x(), point1.y())))
            snapProvider.addFeatures([feature1])
            count += 1
        failMessage = '' if errorCount == 0 else ': {0!s} failed'.format(errorCount)
        self._dlg.snappedLabel.setText('{0!s} snapped{1}'.format(count, failMessage))
        if self._gv.isBatch:
            QSWATUtils.information('{0!s} snapped{1}'.format(count, failMessage), True)
        if count == 0:
            QSWATUtils.error('Could not snap any points to streams or channels', self._gv.isBatch)
            return False
        if outletCount == 0:
            QSWATUtils.error('The outlet layer {0} contains no outlets'
                                   .format(outletLayer.name()), self._gv.isBatch)
            return False
        # shows we have created a snap file
        self._gv.snapFile = snapFile
        self.snapErrors = (errorCount > 0)
        return True
    
    
    @staticmethod
    def createOutletFile(filePath: str, sourcePath: str, basinWanted: bool, root: QgsLayerTree, gv: GlobalVars) -> bool:
        """Create filePath with fields needed for outlets file, 
        copying .prj from sourcePath, and adding Subbasin field if wanted.
        """
        if QSWATUtils.shapefileExists(filePath):
            # safer to empty it than to try to create a new one
            # TODO: check it has expected fields
            ft = FileTypes._OUTLETS
            outletLayer = QSWATUtils.getLayerByFilename(root.findLayers(), filePath, ft, None, None, None)[0]
            if outletLayer is None:
                outletLayer = QgsVectorLayer(filePath, FileTypes.legend(ft), 'ogr')
            return cast(bool, QSWATUtils.removeAllFeatures(outletLayer))
        else:
            QSWATUtils.removeLayer(filePath, root)
            fields = QgsFields()
            fields.append(QgsField(QSWATTopology._ID, QVariant.Int))
            fields.append(QgsField(QSWATTopology._INLET, QVariant.Int))
            fields.append(QgsField(QSWATTopology._RES, QVariant.Int))
            fields.append(QgsField(QSWATTopology._PTSOURCE, QVariant.Int))
            fields.append(QgsField(QSWATTopology._POINTID, QVariant.Int))
            if basinWanted:
                fields.append(QgsField(QSWATTopology._SUBBASIN, QVariant.Int))
            writer = QgsVectorFileWriter.create(filePath, fields, QgsWkbTypes.Point, gv.crsProject, 
                                                QgsCoordinateTransformContext(), gv.vectorFileWriterOptions)
            if writer.hasError() != QgsVectorFileWriter.NoError:
                QSWATUtils.error('Cannot create outlets shapefile {0}: {1}'.format(filePath, writer.errorMessage()), gv.isBatch)
                return False
            writer.flushBuffer()
            QSWATUtils.copyPrj(sourcePath, filePath)
            return True
    
    #===========no longer used================================================================
    # def getOutletIds(self, field: str, root: QgsLayerTree) -> Set[int]:
    #     """Get list of ID values from inlets/outlets layer 
    #     for which field has value 1.
    #     """
    #     result: Set[int] = set()
    #     if self._gv.outletFile == '':
    #         return result
    #     outletLayer = QSWATUtils.getLayerByFilenameOrLegend(root.findLayers(), self._gv.outletFile, FileTypes._OUTLETS, '', self._gv.isBatch)
    #     if not outletLayer:
    #         QSWATUtils.error('Cannot find inlets/outlets layer', self._gv.isBatch)
    #         return result
    #     idIndex = self._gv.topo.getIndex(outletLayer, QSWATTopology._ID)
    #     fieldIndex = self._gv.topo.getIndex(outletLayer, field)
    #     for f in outletLayer.getFeatures():
    #         if f[fieldIndex] == 1:
    #             result.add(f[idIndex])
    #     return result
    #===========================================================================
    
    def progress(self, msg: str) -> None:
        """Update progress label with message; emit message for display in testing."""
        QSWATUtils.progress(msg, self._dlg.progressLabel)
#         if msg != '':
#             self.progress_signal.emit(msg)
#             
#     ## signal for updating progress label
#     progress_signal = pyqtSignal(str)
    
    def doClose(self) -> None:
        """Close form."""
        # close any landscape dialog if visible
        if self.L is not None and self.L._dlg.isVisible():
            self.L.cancel()
        self._dlg.close()

    def readProj(self) -> None:
        """Read delineation data from project file."""
        proj = QgsProject.instance()
        title = proj.title()
        root = proj.layerTreeRoot()
        self._dlg.tabWidget.setCurrentIndex(0)
        self._gv.existingWshed, found = proj.readBoolEntry(title, 'delin/existingWshed', False)
        if found and self._gv.existingWshed:
            self._dlg.tabWidget.setCurrentIndex(1)
        QSWATUtils.loginfo('Existing watershed is {0!s}'.format(self._gv.existingWshed))
        self._gv.useGridModel, found = proj.readBoolEntry(title, 'delin/useGridModel', False)
        self._dlg.useGrid.setChecked(self._gv.useGridModel)
        self._dlg.gridBox.setChecked(self._gv.useGridModel)
        QSWATUtils.loginfo('Use grid model is {0!s}'.format(self._gv.useGridModel))
        gridSize = proj.readNumEntry(title, 'delin/gridSize', 0)[0]
        self._dlg.gridSize.setValue(gridSize)
        self._gv.gridSize = gridSize
        self._dlg.drainGridButton.setChecked(proj.readBoolEntry(title, 'delin/gridDrainage', True)[0])
        self._dlg.drainStreamsButton.setChecked(proj.readBoolEntry(title, 'delin/streamDrainage', False)[0])
        drainageTable, found = proj.readEntry(title, 'delin/drainageTable', '')
        if found and drainageTable != '':
            self.drainageTable = proj.readPath(drainageTable)
        self.setDrainage()
        if self._gv.useGridModel and self._dlg.drainTableButton.isChecked():
            self._dlg.selectStreams.setText(self.drainageTable)
        demFile, found = proj.readEntry(title, 'delin/DEM', '')
        demLayer = None
        if found and demFile != '':
            demFile = proj.readPath(demFile)
            demLayer, _ = QSWATUtils.getLayerByFilename(root.findLayers(), demFile, FileTypes._DEM,
                                                        self._gv, None, QSWATUtils._WATERSHED_GROUP_NAME)
        else:
            treeLayer = QSWATUtils.getLayerByLegend(FileTypes.legend(FileTypes._DEM), root.findLayers())
            if treeLayer is not None:
                layer = treeLayer.layer()
                possFile = QSWATUtils.layerFileInfo(layer).absoluteFilePath()
                if QSWATUtils.question('Use {0} as {1} file?'.format(possFile, FileTypes.legend(FileTypes._DEM)), self._gv.isBatch, True) == QMessageBox.Yes:
                    demLayer = layer
                    demFile = possFile
        if demLayer is not None:
            self._gv.demFile = demFile
            self._dlg.selectDem.setText(self._gv.demFile)
            self.setDefaultNumCells(demLayer)
        else:
            self._gv.demFile = '' 
        verticalUnits, found = proj.readEntry(title, 'delin/verticalUnits', Parameters._METRES)
        if found:
            self._gv.verticalUnits = verticalUnits
            self._gv.setVerticalFactor()
        threshold, found = proj.readNumEntry(title, 'delin/thresholdCh', 0)
        if found and threshold > 0:
            try:
                self._dlg.numCellsCh.setText(str(threshold))
            except Exception:
                pass # leave default setting
        threshold, found = proj.readNumEntry(title, 'delin/thresholdSt', 0)
        if found and threshold > 0:
            try:
                self._dlg.numCellsSt.setText(str(threshold))
            except Exception:
                pass # leave default setting
        snapThreshold, found = proj.readNumEntry(title, 'delin/snapThreshold', 300)
        self._dlg.snapThreshold.setText(str(snapThreshold))
        subbasinsFile, found = proj.readEntry(title, 'delin/subbasins', '')
        subbasinsLayer = None
        ft = FileTypes._GRID if self._gv.useGridModel else FileTypes._EXISTINGSUBBASINS if self._gv.existingWshed else FileTypes._SUBBASINS
        if found and subbasinsFile != '':
            subbasinsFile = proj.readPath(subbasinsFile)
            subbasinsLayer, _ = QSWATUtils.getLayerByFilename(root.findLayers(), subbasinsFile, ft, 
                                                                   self._gv, None, QSWATUtils._WATERSHED_GROUP_NAME)
        else:
            treeLayer = QSWATUtils.getLayerByLegend(FileTypes.legend(ft), root.findLayers())
            if treeLayer is not None:
                layer = treeLayer.layer()
                possFile = QSWATUtils.layerFileInfo(layer).absoluteFilePath()
                if QSWATUtils.question('Use {0} as {1} file?'.format(possFile, FileTypes.legend(ft)), self._gv.isBatch, True) == QMessageBox.Yes:
                    subbasinsLayer = layer
                    subbasinsFile = possFile
        if subbasinsLayer is not None:
            self._dlg.selectSubbasins.setText(subbasinsFile)
            self._gv.subbasinsFile = subbasinsFile
        else:
            self._gv.subbasinsFile = ''
        wshedFile, found = proj.readEntry(title, 'delin/wshed', '')
        ft = FileTypes._EXISTINGWATERSHED if self._gv.existingWshed else FileTypes._WATERSHED
        if found and wshedFile != '':
            wshedFile = proj.readPath(wshedFile)
            groupName = QSWATUtils._WATERSHED_GROUP_NAME if self._gv.existingWshed else None
            _, _ = QSWATUtils.getLayerByFilename(root.findLayers(), wshedFile, ft, self._gv, None, groupName)
        elif not self._gv.useGridModel:
            treeLayer = QSWATUtils.getLayerByLegend(FileTypes.legend(ft), root.findLayers())
            if treeLayer is not None:
                layer = treeLayer.layer()
                possFile = QSWATUtils.layerFileInfo(layer).absoluteFilePath()
                if QSWATUtils.question('Use {0} as {1} file?'.format(possFile, FileTypes.legend(ft)), self._gv.isBatch, True) == QMessageBox.Yes:
                    wshedFile = possFile
        if os.path.exists(wshedFile):
            self._dlg.selectWshed.setText(wshedFile)
            self._gv.wshedFile = wshedFile
        else:
            self._gv.wshedFile = ''
        lakeFile, found = proj.readEntry(title, 'delin/lakes', '')
        ft = FileTypes._LAKES
        if found and lakeFile != '':
            lakeFile = proj.readPath(lakeFile)
            layer, _ = QSWATUtils.getLayerByFilename(root.findLayers(), lakeFile, ft, 
                                                              self._gv, None, QSWATUtils._WATERSHED_GROUP_NAME)
        else:
            treeLayer = QSWATUtils.getLayerByLegend(FileTypes.legend(ft), root.findLayers())
            if treeLayer is not None:
                layer = treeLayer.layer()
                possFile = QSWATUtils.layerFileInfo(layer).absoluteFilePath()
                if QSWATUtils.question('Use {0} as {1} file?'.format(possFile, FileTypes.legend(ft)), self._gv.isBatch, True) == QMessageBox.Yes:
                    lakeFile = possFile
        if os.path.exists(lakeFile):
            self._dlg.selectLakes.setText(lakeFile)
            self._gv.lakeFile = lakeFile
            lakeLayer = layer
        else:
            self._gv.lakeFile = ''
            lakeLayer = None
        self.lakesDone, _ = proj.readBoolEntry(title, 'delin/lakesDone', True)
        if self._gv.useGridModel:
            self.gridLakesAdded , _ = proj.readBoolEntry(title, 'delin/gridLakesAdded', False)
            if self.gridLakesAdded and lakeLayer is not None:
                self.populateLakeIdCombo(lakeLayer)
        else:
            self.lakePointsAdded, _ = proj.readBoolEntry(title, 'delin/lakePointsAdded', False)
        burnFile, found = proj.readEntry(title, 'delin/burn', '')
        burnLayer = None
        if found and burnFile != '':
            burnFile = proj.readPath(burnFile)
            burnLayer, _ = QSWATUtils.getLayerByFilename(root.findLayers(), burnFile, FileTypes._BURN, 
                                                              self._gv, None, QSWATUtils._WATERSHED_GROUP_NAME)
        else:
            treeLayer = QSWATUtils.getLayerByLegend(FileTypes.legend(FileTypes._BURN), root.findLayers())
            if treeLayer is not None:
                layer = treeLayer.layer()
                possFile = QSWATUtils.layerFileInfo(layer).absoluteFilePath()
                if QSWATUtils.question('Use {0} as {1} file?'.format(possFile, FileTypes.legend(FileTypes._BURN)), self._gv.isBatch, True) == QMessageBox.Yes:
                    burnLayer = layer
                    burnFile = possFile
        if burnLayer is not None:
            self._gv.burnFile = burnFile
            self._dlg.checkBurn.setChecked(True)
            self._dlg.selectBurn.setText(burnFile)
        else:
            self._gv.burnFile = ''
        streamFile, found = proj.readEntry(title, 'delin/net', '')
        streamLayer = None
        if self._gv.useGridModel:
            ft = FileTypes._DRAINSTREAMS if self._gv.existingWshed else FileTypes._GRIDSTREAMS
        else:
            ft = FileTypes._STREAMS
        if found and streamFile != '':
            streamFile = proj.readPath(streamFile)
            streamLayer, _ = QSWATUtils.getLayerByFilename(root.findLayers(), streamFile, ft, 
                                                                self._gv, None, QSWATUtils._WATERSHED_GROUP_NAME)
        else:
            treeLayer = QSWATUtils.getLayerByLegend(FileTypes.legend(ft), root.findLayers())
            if treeLayer is not None:
                layer = treeLayer.layer()
                possFile = QSWATUtils.layerFileInfo(layer).absoluteFilePath()
                if QSWATUtils.question('Use {0} as {1} file?'.format(possFile, FileTypes.legend(ft)), 
                                       self._gv.isBatch, True) == QMessageBox.Yes:
                    streamLayer = layer
                    streamFile = possFile
        if streamLayer is not None:
            self._gv.streamFile = streamFile
        else:
            self._gv.streamFile = ''
        self._gv.delinStreamFile, _ = proj.readEntry(title, 'delin/delinNet', '')
        if not self._gv.useGridModel:
            channelFile, found = proj.readEntry(title, 'delin/channels', '')
            channelLayer = None
            ft = FileTypes._CHANNELS
            if found and channelFile != '':
                channelFile = proj.readPath(channelFile)
                channelLayer, _ = QSWATUtils.getLayerByFilename(root.findLayers(), channelFile, ft, 
                                                                     self._gv, None, QSWATUtils._WATERSHED_GROUP_NAME)
            else:
                treeLayer = QSWATUtils.getLayerByLegend(FileTypes.legend(ft), root.findLayers())
                if treeLayer is not None:
                    layer = treeLayer.layer()
                    possFile = QSWATUtils.layerFileInfo(layer).absoluteFilePath()
                    if QSWATUtils.question('Use {0} as {1} file?'.format(possFile, FileTypes.legend(ft)), 
                                           self._gv.isBatch, True) == QMessageBox.Yes:
                        channelLayer = layer
                        channelFile = possFile
            if channelLayer is not None:
                self._dlg.selectStreams.setText(channelFile)
                self._gv.channelFile = channelFile
            else:
                self._gv.channelFile = ''
        useOutlets, found = proj.readBoolEntry(title, 'delin/useOutlets', True)
        if found:
            self._dlg.useOutlets.setChecked(useOutlets)
            self.changeUseOutlets()
        outletFile, found = proj.readEntry(title, 'delin/outlets', '')
        outletLayer = None
        if found and outletFile != '':
            outletFile = proj.readPath(outletFile)
            outletLayer, _ = QSWATUtils.getLayerByFilename(root.findLayers(), outletFile, FileTypes._OUTLETS,
                                                                self._gv, None, QSWATUtils._WATERSHED_GROUP_NAME)
        else:
            treeLayer = QSWATUtils.getLayerByLegend(FileTypes.legend(FileTypes._OUTLETS), root.findLayers())
            if treeLayer is not None:
                layer = treeLayer.layer()
                possFile = QSWATUtils.layerFileInfo(layer).absoluteFilePath()
                if QSWATUtils.question('Use {0} as {1} file?'.format(possFile, FileTypes.legend(FileTypes._OUTLETS)),
                                       self._gv.isBatch, True) == QMessageBox.Yes:
                    outletLayer = layer
                    outletFile = possFile
        if outletLayer is not None:
            self._gv.outletFile = outletFile
            if useOutlets:
                self._dlg.selectExistOutlets.setText(self._gv.outletFile)
                self._dlg.selectOutlets.setText(self._gv.outletFile)
        else:
            self._gv.outletFile = ''
        snapFile, found = proj.readEntry(title, 'delin/snapOutlets', '')
        if found and snapFile != '':
            snapFile = proj.readPath(snapFile)
            if os.path.exists(snapFile):
                self._gv.snapFile = snapFile
            else:
                self._gv.snapFile = ''
        else:
            self._gv.snapFile = ''
        # extra outlets and reservoirs not longer available
#         extraOutletFile, found = proj.readEntry(title, 'delin/extraOutlets', '')
#         extraOutletLayer = None
#         if found and extraOutletFile != '':
#             extraOutletFile = proj.readPath(extraOutletFile)
#             extraOutletLayer, _ = QSWATUtils.getLayerByFilename(root.findLayers(), extraOutletFile, FileTypes._OUTLETS,
#                                                                      self._gv, None, QSWATUtils._WATERSHED_GROUP_NAME)
#         else:
#             treeLayer = QSWATUtils.getLayerByLegend(QSWATUtils._EXTRALEGEND, root.findLayers())
#             if treeLayer is not None:
#                 layer = treeLayer.layer()
#                 possFile = QSWATUtils.layerFileInfo(layer).absoluteFilePath()
#                 if QSWATUtils.question('Use {0} as {1} file?'.format(possFile, QSWATUtils._EXTRALEGEND), self._gv.isBatch, True) == QMessageBox.Yes:
#                     extraOutletLayer = layer
#                     extraOutletFile = possFile 
#         if extraOutletLayer is not None:
#             self._gv.extraOutletFile = extraOutletFile
#             basinIndex = self._gv.topo.getIndex(extraOutletLayer, QSWATTopology._SUBBASIN)
#             resIndex = self._gv.topo.getIndex(extraOutletLayer, QSWATTopology._RES)
#             ptsrcIndex = self._gv.topo.getIndex(extraOutletLayer, QSWATTopology._PTSOURCE)
#             if basinIndex >= 0 and resIndex >= 0 and ptsrcIndex >= 0:
#                 extraPointSources = False
#                 for point in extraOutletLayer.getFeatures():
#                     if point[resIndex] == 1:
#                         self.extraReservoirBasins.add(point[basinIndex])  # TODO:
#                     elif point[ptsrcIndex] == 1:
#                         extraPointSources = True
#                 self._dlg.checkAddPoints.setChecked(extraPointSources)  # TODO:
#         else:
#             self._gv.extraOutletFile = ''
                
    def saveProj(self) -> None:
        """Write delineation data to project file."""
        proj = QgsProject.instance()
        title = proj.title()
        proj.writeEntry(title, 'delin/existingWshed', self._gv.existingWshed)
        proj.writeEntry(title, 'delin/useGridModel', self._gv.useGridModel)
        proj.writeEntry(title, 'delin/gridSize', self._gv.gridSize)
        proj.writeEntry(title, 'delin/gridDrainage', self.gridDrainage)
        proj.writeEntry(title, 'delin/streamDrainage', self.streamDrainage)
        proj.writeEntry(title, 'delin/drainageTable', proj.writePath(self.drainageTable))
        proj.writeEntry(title, 'delin/net', proj.writePath(self._gv.streamFile))
        proj.writeEntry(title, 'delin/delinNet', proj.writePath(self._gv.delinStreamFile))
        proj.writeEntry(title, 'delin/subbasins', proj.writePath(self._gv.subbasinsFile))
        if not self._gv.useGridModel:
            proj.writeEntry(title, 'delin/channels', proj.writePath(self._gv.channelFile))
            proj.writeEntry(title, 'delin/wshed', proj.writePath(self._gv.wshedFile))
        proj.writeEntry(title, 'delin/subsNoLakes', proj.writePath(self._gv.subsNoLakesFile))
        proj.writeEntry(title, 'delin/lakes', proj.writePath(self._gv.lakeFile))
        proj.writeEntry(title, 'delin/lakesDone', self.lakesDone)
        if self._gv.useGridModel:
            proj.writeEntry(title, 'delin/gridLakesAdded', self.gridLakesAdded)
        else:
            proj.writeEntry(title, 'delin/lakePointsAdded', self.lakePointsAdded)
        proj.writeEntry(title, 'delin/DEM', proj.writePath(self._gv.demFile))
        hillshadeFile = os.path.split(self._gv.demFile)[0] + '/hillshade.tif'
        if os.path.exists(hillshadeFile):
            proj.writeEntry(title, 'delin/hillshade', proj.writePath(hillshadeFile))
        proj.writeEntry(title, 'delin/useOutlets', self._dlg.useOutlets.isChecked())
        proj.writeEntry(title, 'delin/outlets', proj.writePath(self._gv.outletFile))
        proj.writeEntry(title, 'delin/snapOutlets', proj.writePath(self._gv.snapFile))
        proj.writeEntry(title, 'delin/extraOutlets', proj.writePath(self._gv.extraOutletFile)) 
        proj.writeEntry(title, 'delin/burn', proj.writePath(self._gv.burnFile))
        proj.writeEntry(title, 'delin/verticalUnits', self._gv.verticalUnits)
        try:
            numCellsCh = int(self._dlg.numCellsCh.text())
        except Exception:
            numCellsCh = 0
        proj.writeEntry(title, 'delin/thresholdCh', numCellsCh)
        try:
            numCellsSt = int(self._dlg.numCellsSt.text())
        except Exception:
            numCellsSt = 0
        proj.writeEntry(title, 'delin/thresholdSt', numCellsSt)
        try:
            snapThreshold = int(self._dlg.snapThreshold.text())
        except Exception:
            snapThreshold = 300
        proj.writeEntry(title, 'delin/snapThreshold', snapThreshold)
        proj.write()
        
        
