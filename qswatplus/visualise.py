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
from qgis.PyQt.QtCore import QFile, QIODevice, QObject, QRectF, Qt, QTimer, QVariant
from qgis.PyQt.QtGui import QColor, QKeySequence, QGuiApplication, QFont, QFontMetricsF, QPainter, QTextDocument, QIntValidator, QDoubleValidator
from qgis.PyQt.QtWidgets import QAbstractItemView, QComboBox, QFileDialog, QListWidget, QListWidgetItem, QMessageBox, QTableWidgetItem, QWidget, QShortcut, QStyleOptionGraphicsItem
from qgis.PyQt.QtXml import QDomDocument
from qgis.core import QgsLineSymbol, QgsFillSymbol, QgsColorRamp, QgsFields, QgsPrintLayout, QgsProviderRegistry, QgsRendererRange, QgsRendererRangeLabelFormat, QgsStyle, QgsGraduatedSymbolRenderer, QgsField, QgsMapLayer, QgsVectorLayer, QgsProject, QgsLayerTree, QgsReadWriteContext, QgsLayoutExporter, QgsSymbol, QgsExpression, QgsFeatureRequest, QgsRectangle  # @UnresolvedImport
from qgis.gui import QgsMapCanvas, QgsMapCanvasItem  # @UnresolvedImport
import os
# import random
import numpy
import sqlite3
import subprocess
import glob
from datetime import date
# from PIL import Image
import math
import csv
import traceback
import locale
# from collections import OrderedDict
from typing import Dict, List, Set, Tuple, Optional, Union, Any, TYPE_CHECKING, cast  # @UnusedImport

# Import the code for the dialog
from .visualisedialog import VisualiseDialog  # type: ignore
from .QSWATUtils import QSWATUtils, FileTypes  # type: ignore
from .QSWATTopology import QSWATTopology  # type: ignore
from .swatgraph import SWATGraph  # type: ignore
from .parameters import Parameters  # type: ignore
from .jenks import jenks    # type: ignore # @UnresolvedImport 
from .globals import GlobalVars  # type: ignore # @UnusedImport 
# from .images2gif import writeGif
if TYPE_CHECKING:
    from globals import GlobalVars  # @UnresolvedImport @Reimport
if not TYPE_CHECKING:
    from . import imageio

class Visualise(QObject):
    """Support visualisation of SWAT outputs, using data in SWAT output database."""
    
    _TOTALS = 'Totals'
    _DAILYMEANS = 'Daily means'
    _MONTHLYMEANS = 'Monthly means'
    _ANNUALMEANS = 'Annual means'
    _MAXIMA = 'Maxima'
    _MINIMA = 'Minima'
    _AREA = 'AREAkm2'
    _MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    _NORTHARROW = 'wind_roses/WindRose_01.svg'
    _EFLOWTABLE = 'channel_sdmorph_day'
    
    def __init__(self, gv: GlobalVars):
        """Initialise class variables."""
        QObject.__init__(self)
        self._gv = gv
        self._dlg = VisualiseDialog()
        self._dlg.setWindowFlags(self._dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint & Qt.WindowMinimizeButtonHint)
        self._dlg.move(self._gv.visualisePos)
        ## variables found in various tables that do not contain values used in results
        # note we also exclude variables that do not have typr REAL
        self.ignoredVars = ['id', 'output_type_id', 'output_interval_id', 'time', 'year', 'unit', 'plantnm', 'ob_typ', 
                            'props', 'type', 'obj_type', 'hyd_typ', 'resnum', 'hru', 'area', 'vol']
        ## tables not suitable for visualisation
        self.ignoredTables = ['crop_yld_', 'deposition_', 'hydin_', 'hydout_', 'ru_', 'basin_psc_', 'recall_']
        ## tables only included when plotting
        self.plotOnlyTables = ['reservoir_', 'wetland_']
        ## current scenario
        self.scenario = ''
        ## Current output database
        self.db = ''
        ## Current connection
        self.conn: Any = None
        ## Current table
        self.table = ''
        ## Number of subbasins in current watershed TODO:
        self.numSubbasins = 0
        ## number of landscape units in current watershed TODO:
        self.numLSUs = 0
        ## number of HURUs in current watershed TODO:
        self.numHRUs = 0
#         ## map SWATBasin -> SWATBasin -> SWATChannel -> LSUId -> hruNum-set
#         self.topology = None 
#         ## map SWATBasin -> SWATChannel -> LSUId -> reservoir number
#         self.reservoirs = None 
#         ## map SWATBasin -> SWATChannel -> LSUId -> pond number
#         self.ponds = None
        ## flag to show if there is a HRUs shaefile available
        self.hasHRUs = False
        ## Data read from db table
        #
        # data takes the form
        # layerId -> gis_id -> variable_name -> year -> time -> value
        self.staticData: Dict[str, Dict[int, Dict[str,  Dict[int, Dict[int, float]]]]] = dict()
        ## Data to write to shapefile
        #
        # takes the form subbasin number -> variable_name -> value for static use
        # takes the form layerId -> date -> subbasin number -> val for animation
        # where date is YYYY or YYYYMM or YYYYDDD according to period of input
        self.resultsData: Union[Dict[int, Dict[str, float]], Dict[str, Dict[int, Dict[int, float]]]] = dict()  # type: ignore
        ## Areas of subbasins (drainage area for reaches)
        self.areas: Dict[int, float] = dict()
#         ## Flag to indicate areas available
#         self.hasAreas = False
        ## true if output is daily
        self.isDaily = False
        ## true if output is monthly
        self.isMonthly = False
        ## true if output is annual
        self.isAnnual = False
        ## true if output is average annual
        self.isAA = False
        ## julian start day
        self.julianStartDay = 0
        ## julian finish day
        self.julianFinishDay = 0
        ## start year of period (of output: includes any nyskip)
        self.startYear = 0
        ## start month of period
        self.startMonth = 0
        ## start day of period
        self.startDay = 0
        ## finish year of period
        self.finishYear = 0
        ## finish month of period
        self.finishMonth = 0
        ## finish day of period
        self.finishDay = 0
        ## length of simulation in days
        self.periodDays = 0
        ## length of simulation in months (may be fractional)
        self.periodMonths = 0.0
        ## length of simulation in years (may be fractional)
        self.periodYears = 0.0
        ## print interval
        self.interval = 1 # default value
        ## map canvas title
        self.mapTitle: Optional[MapTitle] = None
        ## flag to decide if we need to create a new results file:
        # changes to summary method or result variable don't need a new file
        self.resultsFileUpToDate = False
        ## flag to decide if we need to reread data because period has changed
        self.periodsUpToDate = False
        ## current streams results layer
        self.rivResultsLayer: Optional[QgsVectorLayer] = None
        ## current aquifers results layer
        self.aquResultsLayer: Optional[QgsVectorLayer] = None
        ## current deep aquifers results layer
        self.deepAquResultsLayer: Optional[QgsVectorLayer] = None
        ## current subbasins results layer
        self.subResultsLayer: Optional[QgsVectorLayer] = None
        ## current LSUs results layer
        self.lsuResultsLayer: Optional[QgsVectorLayer] = None
        ## current HRUs results layer
        self.hruResultsLayer: Optional[QgsVectorLayer] = None
        ## current results layer: equal to one of the riv, sub, lsu or hruResultsLayer
        self.currentResultsLayer: Optional[QgsVectorLayer] = None
        ## current resultsFile
        self.resultsFile = ''
        ## flag to indicate if summary has changed since last write to results file
        self.summaryChanged = True
        ## current animation layer
        self.animateLayer: Optional[QgsVectorLayer] = None
        ## current animation file (a temporary file)
        self.animateFile = ''
        ## map layerId -> index of animation variable in results file
        self.animateIndexes: Dict[str, int] = dict()
        ## all values involved in animation, for calculating Jenks breaks
        self.allAnimateVals: List[float] = []
        ## timer used to run animation
        self.animateTimer = QTimer()
        ## flag to indicate if animation running
        self.animating = False
        ## flag to indicate if animation paused
        self.animationPaused = False
        ## animation variable
        self.animateVar = ''
        ## flag to indicate if capturing video
        self.capturing = False
        ## base filename of capture stills
        self.stillFileBase = ''
        ## name of latest video file
        self.videoFile = ''
        ## number of next still frame
        self.currentStillNumber = 0
        ## flag to indicate if stream renderer being changed by code
        self.internalChangeToRivRenderer = False
        ## flag to indicate if subbasin renderer being changed by code
        self.internalChangeToSubRenderer = False
        ## flag to indicate if LSU renderer being changed by code
        self.internalChangeToLSURenderer = False
        ## flag to indicate if HRU renderer being changed by code
        self.internalChangeToHRURenderer = False
        ## flag to indicate if aquifer renderer being changed by code
        self.internalChangeToAquRenderer = False
        ## flag to indicate if deep aquifer renderer being changed by code
        self.internalChangeToDeepAquRenderer = False
        ## flag to indicate if colours for rendering streams should be inherited from existing results layer
        self.keepRivColours = False
        ## flag to indicate if colours for rendering subbasins should be inherited from existing results layer
        self.keepSubColours = False
        ## flag to indicate if colours for rendering LSUs should be inherited from existing results layer
        self.keepLSUColours = False
        ## flag to indicate if colours for rendering HRUs should be inherited from existing results layer
        self.keepHRUColours = False
        ## flag to indicate if colours for rendering aquifers should be inherited from existing results layer
        self.keepAquColours = False
        ## flag to indicate if colours for rendering deep aquifers should be inherited from existing results layer
        self.keepDeepAquColours = False
        ## map sub -> LSU -> HRU numbers
        self.hruNums: Dict[int, Dict[int, int]] = dict()
        ## file with observed data for plotting
        self.observedFileName = ''
        ## project title
        self.title = ''
        ## count to keep layout titles unique
        self.compositionCount = 0
        ## animation layout
        self.animationLayout: Optional[QgsPrintLayout] = None
        ## animation template DOM document
        self.animationDOM: Optional[QDomDocument] = None
        ## animation template file
        self.animationTemplate = ''
        ## flag to show when user has perhaps changed the animation template
        self.animationTemplateDirty = False
        ## map from subbasin to outlet channel
        self.subbasinOutletChannels: Dict[int, int] = dict()
        ## last file used for Qq results
        self.lastQqResultsFile = ''
        ## last file used for dQp results
        self.lastdQpResultsFile = ''
        ## last file used for Qb results
        self.lastQbResultsFile = ''
        ## dQp result
        self.dQpResult = -1.0  # negative means not yet calculated
        ## Qb result
        self.QbResult = -1.0
        # empty animation and png directories
        self.clearAnimationDir()
        self.clearPngDir()
        
    def init(self) -> None:
        """Initialise the visualise form."""
        self._dlg.tabWidget.setCurrentIndex(0)
        self._dlg.QtabWidget.setCurrentIndex(0)
        self.setSummary()
        self.fillScenarios()
        self._dlg.scenariosCombo.activated.connect(self.setupDb)
        self._dlg.scenariosCombo.setCurrentIndex(self._dlg.scenariosCombo.findText('Default'))
        if self.db == '':
            self.setupDb()
        self.initQResults()
        self._dlg.variableList.setMouseTracking(True)
        self._dlg.outputCombo.activated.connect(self.setVariables)
        self._dlg.variableCombo.activated.connect(self.changeVariableCombo)
        self._dlg.startYear.setValidator(QIntValidator())
        self._dlg.finishYear.setValidator(QIntValidator())
        self._dlg.unitEdit.setValidator(QIntValidator())
        self._dlg.summaryCombo.activated.connect(self.changeSummary)
        self._dlg.addButton.clicked.connect(self.addClick)
        self._dlg.allButton.clicked.connect(self.allClick)
        self._dlg.delButton.clicked.connect(self.delClick)
        self._dlg.clearButton.clicked.connect(self.clearClick)
        self._dlg.resultsFileButton.clicked.connect(self.setResultsFile)
        self._dlg.tabWidget.currentChanged.connect(self.modeChange)
        self._dlg.saveButton.clicked.connect(self.makeResults)
        self._dlg.printButton.clicked.connect(self.printResults)
        self._dlg.canvasAnimation.clicked.connect(self.changeAnimationMode)
        self._dlg.printAnimation.clicked.connect(self.changeAnimationMode)
        self.changeAnimationMode()
        self._dlg.animationVariableCombo.activated.connect(self.setupAnimateLayer)
        self._dlg.slider.valueChanged.connect(self.changeAnimate)
        self._dlg.slider.sliderPressed.connect(self.pressSlider)
        self._dlg.playCommand.clicked.connect(self.doPlay)
        self._dlg.pauseCommand.clicked.connect(self.doPause)
        self._dlg.rewindCommand.clicked.connect(self.doRewind)
        self._dlg.recordButton.clicked.connect(self.record)
        self._dlg.recordButton.setStyleSheet("background-color: green; border: none;")
        self._dlg.playButton.clicked.connect(self.playRecording)
        self._dlg.spinBox.valueChanged.connect(self.changeSpeed)
        self.animateTimer.timeout.connect(self.doStep)
        self.setupTable()
        self._dlg.unitPlot.activated.connect(self.plotSetUnit)
        self._dlg.unitPlot.highlighted.connect(self.plotSelectUnit)
        self._dlg.unitEdit.textEdited.connect(self.plotEditUnit)
        self._dlg.unitEdit.returnPressed.connect(self.plotEditUnit)
        self._dlg.variablePlot.activated.connect(self.plotSetVar)
        self._dlg.addPlot.clicked.connect(self.doAddPlot)
        self._dlg.deletePlot.clicked.connect(self.doDelPlot)
        self._dlg.copyPlot.clicked.connect(self.doCopyPlot)
        self._dlg.upPlot.clicked.connect(self.doUpPlot)
        self._dlg.downPlot.clicked.connect(self.doDownPlot)
        self._dlg.observedFileButton.clicked.connect(self.setObservedFile)
        self._dlg.addObserved.clicked.connect(self.addObervedPlot)
        self._dlg.plotButton.clicked.connect(self.writePlotData)
        self._dlg.QqSubbasin.activated.connect(self.setQqTableHead)
        self._dlg.QqSpin.valueChanged.connect(self.setQqTableHead)
        self._dlg.QqCalculate.clicked.connect(self.calculateQq)
        self._dlg.QqSave.clicked.connect(self.saveQq)
        self._dlg.dQpSubbasin.activated.connect(self.cleardQpResult)
        self._dlg.dQpStartMonth.activated.connect(self.cleardQpResult)
        self._dlg.dQpSpinD.valueChanged.connect(self.cleardQpResult)
        self._dlg.dQpSpinP.valueChanged.connect(self.cleardQpResult)
        self._dlg.dQpPercentile.toggled.connect(self.dQpButtons)
        self._dlg.dQpMean.toggled.connect(self.dQpButtons)
        self._dlg.dQpCalculate.clicked.connect(self.calculatedQp)
        self._dlg.dQpSave.clicked.connect(self.savedQp)
        self._dlg.QbSubbasin.activated.connect(self.setQbTableHead)
        self._dlg.QbStartMonth.activated.connect(self.setQbTableHead)
        self._dlg.QbCalculate.clicked.connect(self.calculateQb)
        self._dlg.QbSave.clicked.connect(self.saveQb)
        self._dlg.closeButton.clicked.connect(self.doClose)
        self._dlg.destroyed.connect(self.doClose)
        proj = QgsProject.instance()
        root = proj.layerTreeRoot()
        self.setBackgroundLayers(root)
        leftShortCut = QShortcut(QKeySequence(Qt.Key_Left), self._dlg)
        rightShortCut = QShortcut(QKeySequence(Qt.Key_Right), self._dlg)
        leftShortCut.activated.connect(self.animateStepLeft)  # type: ignore
        rightShortCut.activated.connect(self.animateStepRight)  # type: ignore
        self.title = proj.title()
        observedFileName, found = proj.readEntry(self.title, 'observed/observedFile', '')
        if found:
            self.observedFileName = observedFileName
            self._dlg.observedFileEdit.setText(observedFileName)
        animationGroup = root.findGroup(QSWATUtils._ANIMATION_GROUP_NAME)
        assert animationGroup is not None
        animationGroup.visibilityChanged.connect(self.setAnimateLayer)
        animationGroup.removedChildren.connect(self.setAnimateLayer)
        animationGroup.addedChildren.connect(self.setAnimateLayer)
        resultsGroup = root.findGroup(QSWATUtils._RESULTS_GROUP_NAME)
        assert resultsGroup is not None
        resultsGroup.visibilityChanged.connect(self.setResultsLayer)
        resultsGroup.removedChildren.connect(self.setResultsLayer)
        resultsGroup.addedChildren.connect(self.setResultsLayer)
        # in case restart with existing animation layers
        self.setAnimateLayer()
        # in case restart with existing results layers
        self.setResultsLayer()
            
    def run(self) -> None:
        """Do visualisation."""
        self.init()
        self._dlg.show()
        self._dlg.exec_()
        self._gv.visualisePos = self._dlg.pos()
        
    def fillScenarios(self) -> None:
        """Put scenarios in scenariosCombo and months in start and finish month combos."""
        pattern = QSWATUtils.join(self._gv.scenariosDir, '*')
        for direc in glob.iglob(pattern):
            db = QSWATUtils.join(QSWATUtils.join(direc, Parameters._RESULTS), Parameters._OUTPUTDB)
            if os.path.exists(db):
                self._dlg.scenariosCombo.addItem(os.path.split(direc)[1])
        for month in Visualise._MONTHS:
            m = QSWATUtils.trans(month)
            self._dlg.startMonth.addItem(m)
            self._dlg.finishMonth.addItem(m)
        for i in range(31):
            self._dlg.startDay.addItem(str(i+1))
            self._dlg.finishDay.addItem(str(i+1))
            
    def setBackgroundLayers(self, root: QgsLayerTree) -> None:
        """Reduce visible layers to channels, LSUs, HRUs, aquifers and subbasins by making all others not visible,
        loading LSUs, HRUs, aquifers if necessary.
        Leave Results group in case we already have some layers there."""
        slopeGroup = root.findGroup(QSWATUtils._SLOPE_GROUP_NAME)
        if slopeGroup is not None:
            slopeGroup.setItemVisibilityCheckedRecursive(False)
        soilGroup = root.findGroup(QSWATUtils._SOIL_GROUP_NAME)
        if soilGroup is not None:
            soilGroup.setItemVisibilityCheckedRecursive(False)
        landuseGroup = root.findGroup(QSWATUtils._LANDUSE_GROUP_NAME)
        if landuseGroup is not None:
            landuseGroup.setItemVisibilityCheckedRecursive(False)
        # laod HRUS, LSUS and Aquifers layers if necessary
        hrusLayer = QSWATUtils.getLayerByLegend(QSWATUtils._FULLHRUSLEGEND, root.findLayers())
        hrusFile = QSWATUtils.join(self._gv.resultsDir, Parameters._HRUS + '.shp')
        hasHRUs = os.path.isfile(hrusFile)
        lsusLayer = QSWATUtils.getLayerByLegend(QSWATUtils._FULLLSUSLEGEND, root.findLayers())
        aquifersLayer = QSWATUtils.getLayerByLegend(QSWATUtils._AQUIFERSLEGEND, root.findLayers())
        if (hrusLayer is None and hasHRUs) or lsusLayer is None or aquifersLayer is None:
            # set sublayer as hillshade or DEM
            hillshadeLayer = QSWATUtils.getLayerByLegend(QSWATUtils._HILLSHADELEGEND, root.findLayers())
            demLayer = QSWATUtils.getLayerByLegend(QSWATUtils._DEMLEGEND, root.findLayers())
            subLayer = None
            if hillshadeLayer is not None:
                subLayer = hillshadeLayer
            elif demLayer is not None:
                subLayer = demLayer
            if hrusLayer is None and hasHRUs:
                hrusLayer = QSWATUtils.getLayerByFilename(root.findLayers(), hrusFile, FileTypes._HRUS, 
                                                            self._gv, subLayer, QSWATUtils._WATERSHED_GROUP_NAME)
            if lsusLayer is None:
                lsusFile = QSWATUtils.join(self._gv.resultsDir, Parameters._LSUS + '.shp')
                lsusLayer = QSWATUtils.getLayerByFilename(root.findLayers(), lsusFile, FileTypes._LSUS, 
                                                            self._gv, subLayer, QSWATUtils._WATERSHED_GROUP_NAME)
            if aquifersLayer is None:
                aquifersFile = QSWATUtils.join(self._gv.resultsDir, Parameters._AQUIFERS + '.shp')
                aquifersLayer = QSWATUtils.getLayerByFilename(root.findLayers(), aquifersFile, FileTypes._AQUIFERS, 
                                                            self._gv, subLayer, QSWATUtils._WATERSHED_GROUP_NAME)
        watershedLayers = QSWATUtils.getLayersInGroup(QSWATUtils._WATERSHED_GROUP_NAME, root)
        # make subbasins, channels, LSUs, HRUs and aquifers visible
        if self._gv.useGridModel:
            keepVisible = lambda n: n.startswith(QSWATUtils._GRIDSTREAMSLEGEND) or \
                                    n.startswith(QSWATUtils._DRAINSTREAMSLEGEND) or \
                                    n.startswith(QSWATUtils._GRIDLEGEND) or \
                                    n.startswith(QSWATUtils._AQUIFERSLEGEND) or \
                                    n.startswith(QSWATUtils._LSUSLEGEND) or \
                                    n.startswith(QSWATUtils._HRUSLEGEND)
        else:  
            keepVisible = lambda n: n.startswith(QSWATUtils._SUBBASINSLEGEND) or \
                                    n.startswith(QSWATUtils._CHANNELREACHESLEGEND) or \
                                    n.startswith(QSWATUtils._ACTLSUSLEGEND) or \
                                    n.startswith(QSWATUtils._ACTHRUSLEGEND) or \
                                    n.startswith(QSWATUtils._AQUIFERSLEGEND)
        for layer in watershedLayers:
            layer.setItemVisibilityChecked(keepVisible(layer.name()))
    
    def setupDb(self) -> None:
        """Set current database and connection to it; put table names in outputCombo."""
        self.resultsFileUpToDate = False
        self.scenario = self._dlg.scenariosCombo.currentText()
        self.setConnection(self.scenario)
        scenDir = QSWATUtils.join(self._gv.scenariosDir, self.scenario)
        txtInOutDir = QSWATUtils.join(scenDir, Parameters._TXTINOUT)
        resultsDir = QSWATUtils.join(scenDir, Parameters._RESULTS)
        self.db = QSWATUtils.join(resultsDir, Parameters._OUTPUTDB)
        self.hasHRUs = os.path.exists(QSWATUtils.join(resultsDir, Parameters._HRUS + '.shp'))
        self.conn =  sqlite3.connect(self.db)
        if self.conn is None:
            QSWATUtils.error('Failed to connect to output database {0}'.format(self.db), self.isBatch)
        else:
            self.conn.row_factory = sqlite3.Row
        simFile = QSWATUtils.join(txtInOutDir, Parameters._SIM)
        if not os.path.exists(simFile):
            QSWATUtils.error('Cannot find simulation file {0}'.format(simFile), self._gv.isBatch)
            return
        prtFile = QSWATUtils.join(txtInOutDir, Parameters._PRT)
        if not os.path.exists(prtFile):
            QSWATUtils.error('Cannot find print file {0}'.format(prtFile), self._gv.isBatch)
            return
        self.readPrt(prtFile, simFile)
#         self.topology, self.reservoirs, self.ponds = self._gv.db.createTopology()
        self.populateOutputTables()

    def populateOutputTables(self) -> None:
        """Add daily, monthly and annual output tables to output combo.
        For post processing find subbasin outlet channels."""
        self._dlg.outputCombo.clear()
        self._dlg.outputCombo.addItem('')
        tables: List[str] = []
        # if we are plotting and have at least one non-observed row, only include tables of same frequency
        isPlot = self._dlg.tabWidget.currentIndex() == 2
        plotTable = self.getPlotTable() if isPlot else ''
        keepDaily = plotTable == '' or Visualise.tableIsDaily(plotTable)
        if keepDaily:
            self.addTablesByTerminator(tables, '_day')
        keepMonthly = plotTable == '' or Visualise.tableIsMonthly(plotTable)
        if keepMonthly:
            self.addTablesByTerminator(tables, '_mon')
        keepYearly = plotTable == '' or Visualise.tableIsYearly(plotTable)
        if keepYearly:
            self.addTablesByTerminator(tables, '_yr')
            if self._dlg.tabWidget.currentIndex() == 0:  # static
                self.addTablesByTerminator(tables, '_aa')
        for table in tables:
            self._dlg.outputCombo.addItem(table)
        self.makeDeepAquiferTables()
        self._dlg.outputCombo.setCurrentIndex(0)
        self.table = ''
        self.plotSetUnit()
        self._dlg.variablePlot.clear()
        self._dlg.variablePlot.addItem('')
        self.updateCurrentPlotRow(0)
        if self._dlg.tabWidget.currentIndex() == 3:
            self.setSubbasinOutletChannels()
        model = self._dlg.outputCombo.model()
        view = self._dlg.outputCombo.view()
        view.setMouseTracking(True)
        # ignore first row since it is empty
        for row in range(1, self._dlg.outputCombo.count()):
            item = model.item(row)
            tip = self.getTableTip(self._dlg.outputCombo.itemText(row))
            if tip != '':
                item.setToolTip(tip)
                
    def makeDeepAquiferTables(self) -> None:
        """For every table aquifer_... in output tables, if there is no corresponding deep_aquifer
        table, create it by removing deepe aquifer entries from first table."""
        count = self._dlg.outputCombo.count()
        # ignore first row since it is empty
        row = 1
        while row < count:
            txt = self._dlg.outputCombo.itemText(row)
            if txt.startswith('aquifer_'):
                deeptxt = 'deep_' + txt
                deepIndx = self._dlg.outputCombo.findText(deeptxt, Qt.MatchExactly)
                if deepIndx < 0:
                    sql1 = "CREATE TABLE {0} AS SELECT * FROM {1} WHERE name LIKE 'aqu_deep%'".format(deeptxt, txt)
                    self.conn.execute(sql1)
                    sql2 = "DELETE FROM {0} WHERE name LIKE 'squ_deep%'".format(txt)
                    self.conn.execute(sql2)
                    row += 1
                    self._dlg.outputCombo.insertItem(row, deeptxt)
                    count += 1
            row += 1     
            
    def setConnection(self, scenario: str) -> None:
        """Set connection to scenario output database."""
        scenDir = QSWATUtils.join(self._gv.scenariosDir, scenario)
        outDir = QSWATUtils.join(scenDir, Parameters._RESULTS)
        self.db = QSWATUtils.join(outDir, Parameters._OUTPUTDB)
        self.conn =  sqlite3.connect(self.db)
        if self.conn is None:
            QSWATUtils.error('Failed to connect to output database {0}'.format(self.db), self._gv.isBatch)
        else:
            #self.conn.isolation_level = None # means autocommit
            self.conn.row_factory = sqlite3.Row
        
    def addTablesByTerminator(self, tables: List[str], terminator: str) -> None:
        """Add to tables table names terminating with terminator, provided they have data.
        
        The names added are sorted."""
        sql = 'SELECT name FROM sqlite_master WHERE TYPE="table"'
        tempTables: List[str] = []
        for row in self.conn.execute(sql):
            table = row[0]
            if self._dlg.tabWidget.currentIndex() != 2 and table.startswith('basin_'):
                continue
            if not self.hasHRUs and self._dlg.tabWidget.currentIndex() != 2 and table.startswith('hru_'):
                continue
            if table.endswith(terminator):
                ignore = False
                # check table is not ignored
                for ignored in self.ignoredTables:
                    if table.startswith(ignored):
                        ignore = True
                        break
                if ignore:
                    continue
                for plotOnly in self.plotOnlyTables:
                    if table.startswith(plotOnly):
                        ignore = self._dlg.tabWidget.currentIndex() != 2
                        break
                if ignore:
                    continue
                # check table has data and a gis_id
                sql2 = self._gv.db.sqlSelect(table, '*', '', '')
                row2 = self.conn.execute(sql2).fetchone()
                if row2 is not None and 'gis_id' in row2.keys():
                    tempTables.append(table)
        tables.extend(sorted(tempTables))    
        
    def restrictOutputTablesByTerminator(self, terminator: str) -> None:
        """RestrictOutputTables combo to those ending with terminator."""
        toDelete: List[int] = []
        for indx in range(self._dlg.outputCombo.count()):
            txt = self._dlg.outputCombo.itemText(indx)
            if txt == '' or txt.endswith(terminator):
                continue
            toDelete.append(indx)
        # remove from bottom as indexes affected by removal
        for indx in reversed(toDelete):
            self._dlg.outputCombo.removeItem(indx)
        
    def setupTable(self) -> None:
        """Initialise the plot table."""
        # designer makes this false
        self._dlg.tableWidget.horizontalHeader().setVisible(True)
        self._dlg.tableWidget.setHorizontalHeaderLabels(['Scenario', 'Table', 'Unit', 'Variable'])
        self._dlg.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._dlg.tableWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self._dlg.tableWidget.setColumnWidth(0, 100)
        self._dlg.tableWidget.setColumnWidth(1, 100)
        self._dlg.tableWidget.setColumnWidth(2, 45)
        self._dlg.tableWidget.setColumnWidth(4, 90)
        
    def setVariables(self) -> None:
        """Fill variables combos from selected table; set default results file name."""
        table = self._dlg.outputCombo.currentText()
        self.table = table 
        if self.table == '':
            self._dlg.outputCombo.setToolTip('')
            return
        if not self.conn:
            return
        self._dlg.outputCombo.setToolTip(self.getTableTip(table))
        self.isDaily, self.isMonthly, self.isAnnual, self.isAA = Visualise.tableIsDailyMonthlyOrAnnual(self.table)
        scenDir = QSWATUtils.join(self._gv.scenariosDir, self.scenario)
        outDir = QSWATUtils.join(scenDir, Parameters._RESULTS)
        outFile = QSWATUtils.join(outDir, self.table + 'results.shp')
        self._dlg.resultsFileEdit.setText(outFile)
        self.resultsFileUpToDate = False
        self._dlg.summaryBox.setVisible(not self.isAA)
        # add gis id numbers to unitPlot combo
        self.setGisIdPlot()
        self._dlg.variableCombo.clear()
        self._dlg.animationVariableCombo.clear()
        self._dlg.animationVariableCombo.addItem('')
        self._dlg.variablePlot.clear()
        self._dlg.variablePlot.addItem('')
        self._dlg.variableList.clear()
        sql = 'PRAGMA TABLE_INFO({0})'.format(table)
        for row in self.conn.execute(sql):
            var = row[1]
            varType = row[2]
            # only include fields of type REAL
            if varType == 'REAL' and not var in self.ignoredVars:
                self._dlg.variableCombo.addItem(var)
                self._dlg.animationVariableCombo.addItem(var)
                self._dlg.variablePlot.addItem(var)
        self.setVarComboTips(self._dlg.variableCombo, 'Select variable to be added to list')
        self.setVarComboTips(self._dlg.animationVariableCombo, 'Select variable for animation')
        self.setVarComboTips(self._dlg.variablePlot, 'Select the current plot\'s variable')
        self.updateCurrentPlotRow(1)
        
    def changeVariableCombo(self) -> None:
        """Set tool tip according to selection."""
        var = self._dlg.variableCombo.currentText()
        if var == '':
            self._dlg.variableCombo.setToolTip('Select variable to be added to list')
        else:
            self._dlg.variableCombo.setToolTip(self.getVarTip(var))
        
    def setVarComboTips(self, combo: QComboBox, initTip: str) -> None:
        """Set tool tips for each variable in combo."""
        model = combo.model()
        view = combo.view()
        view.setMouseTracking(True)
        for row in range(combo.count()):
            var = combo.itemText(row)
            if var != '':
                item = cast(QListWidget, model).item(row)
                tip = self.getVarTip(var)
                if tip != '':
                    item.setToolTip(tip)
        if combo.currentText() == '':
            combo.setToolTip(initTip)
        else:
            combo.setToolTip(self.getVarTip(combo.currentText()))
        
    def plotting(self) -> bool:
        """Return true if plot tab open and plot table has a selected row."""
        if self._dlg.tabWidget.currentIndex() != 2:
            return False
        indexes = self._dlg.tableWidget.selectedIndexes()
        return indexes is not None and len(indexes) > 0
                
    def setSummary(self) -> None:
        """Fill summary combo."""
        self._dlg.summaryCombo.clear()
        self._dlg.summaryCombo.addItem(Visualise._TOTALS)
        self._dlg.summaryCombo.addItem(Visualise._DAILYMEANS)
        self._dlg.summaryCombo.addItem(Visualise._MONTHLYMEANS)
        self._dlg.summaryCombo.addItem(Visualise._ANNUALMEANS)
        self._dlg.summaryCombo.addItem(Visualise._MAXIMA)
        self._dlg.summaryCombo.addItem(Visualise._MINIMA)
        
    def readSim(self, simFile: str) -> bool:
        """Read time.sim file.  This just sets outer limits for start and end dates.  Return true if no errors."""
        try:
            with open(simFile, 'r') as sim:
                # skip first line
                sim.readline()
                # skip headings
                sim.readline()
                dates = sim.readline().split()
                self.julianStartDay = int(dates[0])
                # interpret 0 as 1
                if self.julianStartDay == 0:
                    self.julianStartDay = 1
                self.startYear = int(dates[1])
                self.julianFinishDay = int(dates[2])
                self.finishYear = int(dates[3])
                # interpret Julian 0 as last day of year
                if self.julianFinishDay == 0:
                    self.julianFinishDay = 366 if self.isLeap(self.finishYear) else 365
                # STEP can be ignored - does not affect outputs
                return True
        except Exception:
            QSWATUtils.exceptionError('Failed to read {0}'.format(simFile), self._gv.isBatch)
            return False
                    

    def readPrt(self, prtFile: str, simFile: str) -> bool:
        """Read print.prt file to get print period and print interval.  Return true if no errors."""
        # first read time.sim to reset start/finish dates to simulation
        if not self.readSim(simFile):
            return False
        try:
            with open(prtFile, 'r') as prt:
                # skip first line
                prt.readline()
                # skip headings
                prt.readline()
                dates = prt.readline().split()
                nyskip = int(dates[0])
                self.startYear += nyskip
                startDay = int(dates[1])
                if startDay > 0 and startDay >  self.julianStartDay:
                    self.julianStartDay = startDay
                finishDay = int(dates[3])
                if finishDay > 0 and finishDay < self.julianFinishDay:
                    self.julianFinishDay = finishDay
                startYear = int(dates[2])
                if startYear > 0 and startYear > self.startYear:
                    self.startYear  = startYear
                finishYear = int(dates[4])
                if finishYear > 0 and finishYear < self.finishYear:
                    self.finishYear = finishYear
                # make sure finish day matches the year if set to year end
                if self.julianFinishDay in {365, 366}:
                    self.julianFinishDay = 366 if self.isLeap(self.finishYear) else 365
                self.interval = int(dates[5])
                if self.interval == 0:
                    self.interval = 1 # defensive coding
            self.setDates()
            return True
        except Exception:
            QSWATUtils.exceptionError('Failed to read {0}: {1}'.format(prtFile, traceback.format_exc()), self._gv.isBatch)
            return False
        
    def setDates(self) -> None:
        """Set requested start and finish dates to smaller period of length of scenario and requested dates (if any)."""
        startDate = self.julianToDate(self.julianStartDay, self.startYear)
        finishDate = self.julianToDate(self.julianFinishDay, self.finishYear)
        requestedStartDate = self.readStartDate()
        if requestedStartDate is None:
            self.setStartDate(startDate)
        else:
            if requestedStartDate < startDate:
                QSWATUtils.information('Chosen period starts earlier than scenario {0} period: changing chosen start'.format(self.scenario), self._gv.isBatch)
                self.setStartDate(startDate)
        requestedFinishDate = self.readFinishDate()
        if requestedFinishDate is None:
            self.setFinishDate(finishDate)
        else:
            if requestedFinishDate > finishDate:
                QSWATUtils.information('Chosen period finishes later than scenario {0} period: changing chosen finish'.format(self.scenario), self._gv.isBatch)
                self.setFinishDate(finishDate)
        
    def setPeriods(self) -> bool:
        """Define period of current scenario in days, months and years.  Return true if OK."""
        requestedStartDate = self.readStartDate()
        requestedFinishDate = self.readFinishDate()
        if requestedStartDate is None or requestedFinishDate is None:
            QSWATUtils.error('Cannot read chosen period', self._gv.isBatch)
            return False
        if requestedFinishDate <= requestedStartDate:
            QSWATUtils.error('Finish date must be later than start date', self._gv.isBatch)
            return False
        self.periodsUpToDate = self.startDay == requestedStartDate.day and \
            self.startMonth == requestedStartDate.month and \
            self.startYear == requestedStartDate.year and \
            self.finishDay == requestedFinishDate.day and \
            self.finishMonth == requestedFinishDate.month and \
            self.finishYear == requestedFinishDate.year
        if self.periodsUpToDate:
            return True
        self.startDay = requestedStartDate.day
        self.startMonth = requestedStartDate.month
        self.startYear = requestedStartDate.year
        self.finishDay = requestedFinishDate.day
        self.finishMonth = requestedFinishDate.month
        self.finishYear = requestedFinishDate.year
        self.julianStartDay = int(requestedStartDate.strftime('%j'))
        self.julianFinishDay = int(requestedFinishDate.strftime('%j'))
        self.periodDays = 0
        self.periodMonths = 0
        self.periodYears = 0
        for year in range(self.startYear, self.finishYear + 1):
            leapAdjust = 1 if self.isLeap(year) else 0
            yearDays = 365 + leapAdjust
            start = self.julianStartDay if year == self.startYear else 1
            finish = self.julianFinishDay if year == self.finishYear else yearDays
            numDays = finish - start + 1
            self.periodDays += numDays
            fracYear = numDays / yearDays
            self.periodYears += fracYear
            self.periodMonths += fracYear * 12
        # QSWATUtils.loginfo('Period is {0} days, {1} months, {2} years'.format(self.periodDays, self.periodMonths, self.periodYears))
        return True
                
    def  readStartDate(self) -> Optional[date]:
        """Return date from start date from form.  None if any problems."""
        try:
            day = int(self._dlg.startDay.currentText())
            month = Visualise._MONTHS.index(self._dlg.startMonth.currentText()) + 1
            year = int(self._dlg.startYear.text())
            return date(year, month, day)
        except Exception:
            return None
                
    def  readFinishDate(self) -> Optional[date]:
        """Return date from finish date from form.  None if any problems."""
        try:
            day = int(self._dlg.finishDay.currentText())
            month = Visualise._MONTHS.index(self._dlg.finishMonth.currentText()) + 1
            year = int(self._dlg.finishYear.text())
            return date(year, month, day)
        except Exception:
            return None
        
    def setStartDate(self, date: date) -> None:
        """Set start date on form."""
        self._dlg.startDay.setCurrentIndex(date.day - 1)
        self._dlg.startYear.setText(str(date.year))
        self._dlg.startMonth.setCurrentIndex(date.month - 1)
            
    def setFinishDate(self, date: date) -> None:
        """Set finish date on form."""        
        self._dlg.finishDay.setCurrentIndex(date.day - 1)
        self._dlg.finishYear.setText(str(date.year))
        self._dlg.finishMonth.setCurrentIndex(date.month - 1)
            
        
    def addClick(self) -> None:
        """Append item to variableList."""
        self.resultsFileUpToDate = False
        var = self._dlg.variableCombo.currentText()
        items = self._dlg.variableList.findItems(var, Qt.MatchExactly)
        if not items or items == []:
            item = QListWidgetItem()
            item.setText(var)
            tip = self.getVarTip(var)
            if tip != '':
                item.setToolTip(tip)
            self._dlg.variableList.addItem(item)
            
    def allClick(self) -> None:
        """Clear variableList and insert all items from variableCombo."""
        self.resultsFileUpToDate = False
        self._dlg.variableList.clear()
        for i in range(self._dlg.variableCombo.count()):
            item = QListWidgetItem()
            var = self._dlg.variableCombo.itemText(i)
            item.setText(var)
            tip = self.getVarTip(var)
            if tip != '':
                item.setToolTip(tip)
            self._dlg.variableList.addItem(item)
        
    def delClick(self) -> None:
        """Delete item from variableList."""
        self.resultsFileUpToDate = False
        items = self._dlg.variableList.selectedItems()
        if len(items) > 0:
            row = self._dlg.variableList.indexFromItem(items[0]).row()
            self._dlg.variableList.takeItem(row)
    
    def clearClick(self) -> None:
        """Clear variableList."""
        self.resultsFileUpToDate = False
        self._dlg.variableList.clear()
        
    def getVarTip(self, var: str) -> str:
        """Return tool tip based on units and description from looking up current table and var in table column_description."""
        sql = 'SELECT [units], [description] FROM column_description WHERE table_name=? AND column_name=?'
        try:
            row = self.conn.execute(sql, (self.table, var)).fetchone()
            str1 = '' if row[0] is None else 'Units: {0}'.format(row[0])
            str2 = '' if row[1] is None else 'Description: {0}'.format(row[1])
            return str2 if str1 == '' else str1 if str2 == '' else '{0} {1}'.format(str1, str2)
        except Exception:
            return ''
        
    def getTableTip(self, table: str) -> str:
        """Return tool tip based on description from looking up table in table table_description."""
        sql = 'SELECT [description] FROM table_description WHERE table_name=?'
        try:
            row = self.conn.execute(sql, (table,)).fetchone()
            return '' if row[0] is None else '{0}'.format(row[0])
        except Exception:
            return ''
        
    def doClose(self) -> None:
        """Close the db connection, timer, clean up from animation, remove title, and close the form."""
        self.animateTimer.stop()
        # empty animation and png directories
        self.clearAnimationDir()
        self.clearPngDir()
        self.clearMapTitle()
        # remove animation layers
        proj = QgsProject.instance()
        for animation in QSWATUtils.getLayersInGroup(QSWATUtils._ANIMATION_GROUP_NAME, proj.layerTreeRoot()):
            proj.removeMapLayer(animation.layerId())
        # only close connection after removing animation layers as the map title is affected and recalculation needs connection
        self.conn = None
        self._dlg.close()
        
    def plotSetUnit(self) -> None:
        """Update the unitEdit box and set the unit value in the current row."""
        unitStr = self._dlg.unitPlot.currentText()
        self._dlg.unitEdit.setText(unitStr)
        self.updateCurrentPlotRow(2)
        
    def plotSelectUnit(self, index: int) -> None:
        """Load file for showing unit as a selection if necessary.  Select chosen unt."""
        if index < 1 or self.conn is None or self.table == '':
            return
        QSWATUtils.loginfo('Index is {0}'.format(index))
        root = QgsProject.instance().layerTreeRoot()
        if self.table.startswith('channel'):
            if self._gv.useGridModel:
                treeLayer = QSWATUtils.getLayerByLegend(QSWATUtils._GRIDSTREAMSLEGEND, root.findLayers())
                if treeLayer is None:
                    treeLayer = QSWATUtils.getLayerByLegend(QSWATUtils._DRAINSTREAMSLEGEND, root.findLayers())
                layer = None if treeLayer is None else treeLayer.layer()
                field = QSWATTopology._LINKNO
            else:
                treeLayer = QSWATUtils.getLayerByLegend(QSWATUtils._CHANNELREACHESLEGEND, root.findLayers())
                layer = None if treeLayer is None else treeLayer.layer()
                field = QSWATTopology._CHANNEL
        elif self.table.startswith('lsunit'):
            if self._gv.useGridModel:
                treeLayer = QSWATUtils.getLayerByLegend(QSWATUtils._LSUSLEGEND, root.findLayers())
                layer = None if treeLayer is None else treeLayer.layer()
            else:
                lsuFile = QSWATUtils.join(self._gv.shapesDir, 'lsus2.shp')
                if not os.path.isfile(lsuFile):
                    lsuFile = QSWATUtils.join(self._gv.shapesDir, 'lsus1.shp')
                layer, _ = QSWATUtils.getLayerByFilename(root.findLayers(), lsuFile, FileTypes._LSUS, 
                                                                  None, None, None)
            field = QSWATTopology._LSUID
        elif self.table.startswith('aquifer'):
            aquFile = QSWATUtils.join(self._gv.resultsDir, 'aquifers.shp')
            layer, _ = QSWATUtils.getLayerByFilename(root.findLayers(), aquFile, FileTypes._AQUIFERS, 
                                                     None, None, None)
            field = QSWATTopology._AQUIFER
        elif self.table.startswith('hru'):
            if self._gv.useGridModel:
                treeLayer = QSWATUtils.getLayerByLegend(QSWATUtils._HRUSLEGEND, root.findLayers())
                layer = None if treeLayer is None else treeLayer.layer()
            else:
                hruFile = QSWATUtils.join(self._gv.shapesDir, 'hrus2.shp')
                if not os.path.isfile(hruFile):
                    hruFile = QSWATUtils.join(self._gv.shapesDir, 'hrus1.shp')
                    if not os.path.isfile(hruFile):
                        return
                layer, _ = QSWATUtils.getLayerByFilename(root.findLayers(), hruFile, FileTypes._HRUS, 
                                                         None, None, None)
            field = QSWATTopology._HRUS
        else:
            return
        if layer is None:
            return
        QSWATUtils.loginfo('Layer is {0!s}'.format(layer))
        val = self._dlg.unitPlot.itemText(index)
        QSWATUtils.loginfo('Value is {0}'.format(val))
        QSWATUtils.setLayerVisibility(layer, True, root)
        layer.removeSelection()
        QSWATUtils.loginfo('Selection removed')
        if field == QSWATTopology._HRUS:
            # need to match n or n1, n2 or n1, n2, n3
            strng = '"{0}" = {1} OR "{0}" LIKE \'{1},%\' OR  "{0}" LIKE \'%, {1}\' OR  "{0}"  LIKE \'%, {1},%\''.format(field, val)
        else:
            strng = '"{0}" = {1}'.format(field, val)
        expr = QgsExpression(strng)
        request = QgsFeatureRequest(expr).setFlags(QgsFeatureRequest.NoGeometry)
        featureId = None
        for targetFeature in layer.getFeatures(request):
            featureId = targetFeature.id()
            QSWATUtils.loginfo('Feature id is {0!s}'.format(featureId))
            layer.select(featureId)
        
    def plotEditUnit(self) -> None:
        """If the unitEdit contains a string in the unitPlot combo box, 
        Update the current index of the combo box, and set the unit value in the current row."""
        unitStr = self._dlg.unitEdit.text()
        index = self._dlg.unitPlot.findText(unitStr)
        if index >= 1: # avoid initial empty text as well as 'not found' value of -1
            self._dlg.unitPlot.setCurrentIndex(index)
            self.updateCurrentPlotRow(2)
        
    def plotSetVar(self) -> None:
        """Update the variable in the current plot row."""
        var = self._dlg.variablePlot.currentText()
        if var == '':
            self._dlg.variablePlot.setToolTip('Select the current plot\'s variable')
        else:
            self._dlg.variablePlot.setToolTip(self.getVarTip(var))
        self.updateCurrentPlotRow(3)
        
    def writePlotData(self) -> None:
        """Write data for plot rows to csv file."""
        if not self.conn:
            return
        if not self.setPeriods():
            return
        if not self.checkFrequencyConsistent():
            QSWATUtils.error(u'All rows in the table must have the same frequency: annual, monthly or daily', self._gv.isBatch)
            return
        numRows = self._dlg.tableWidget.rowCount()
        plotData: Dict[int, List[str]] = dict()
        labels: Dict[int, str] = dict()
        dates: List[str] = []
        datesDone = False
        for i in range(numRows):
            plotData[i] = []
            scenario = self._dlg.tableWidget.item(i, 0).text()
            table = self._dlg.tableWidget.item(i, 1).text()
            gisId = self._dlg.tableWidget.item(i, 2).text()
            var = self._dlg.tableWidget.item(i, 3).text()
            if scenario == '' or table == '' or gisId == '' or var == '':
                QSWATUtils.information('Row {0!s} is incomplete'.format(i+1), self._gv.isBatch)
                return
            if scenario == 'observed' and table == '-':
                if os.path.exists(self.observedFileName):
                    labels[i] = 'observed-{0}'.format(var.strip()) # last label has an attached newline, so strip it
                    plotData[i] = self.readObservedFile(var)
                else:
                    QSWATUtils.error('Cannot find observed data file {0}'.format(self.observedFileName), self._gv.isBatch)
                    return
            else:
                num = int(gisId)
                where = 'gis_id={0}'.format(num)
                labels[i] = '{0}-{1}-{2!s}-{3}'.format(scenario, table, num, var)
                if scenario != self.scenario:
                    # need to change database
                    self.setConnection(scenario)
                    if not self.readData('', False, table, var, where):
                        return
                    # restore database
                    self.setConnection(self.scenario)
                else:
                    if not self.readData('', False, table, var, where):
                        return
                isDaily, isMonthly, isAnnual, _ = Visualise.tableIsDailyMonthlyOrAnnual(table)
                (year, tim) = self.startYearTime(isDaily, isMonthly)
                (finishYear, finishTime) = self.finishYearTime(isDaily, isMonthly)
                layerData = self.staticData['']
                while year < finishYear or (year == finishYear and tim <= finishTime):
                    if not num in layerData:
                        QSWATUtils.error('Insufficient data for unit {0} for plot {1!s}'.format(num, i+1), self._gv.isBatch)
                        return
                    unitData = layerData[num]
                    if not var in unitData:
                        QSWATUtils.error('Insufficient data for variable {0} for plot {1!s}'.format(var, i+1), self._gv.isBatch)
                        return
                    varData = unitData[var]
                    if not year in varData:
                        QSWATUtils.error('Insufficient data for year {0} for plot {1!s}'.format(year, i+1), self._gv.isBatch)
                        return
                    yearData = varData[year]
                    if isAnnual:
                        # time values in yearData are arbitrary and should be ignored
                        # there should be just one record
                        if len(yearData) == 0:
                            QSWATUtils.error(u'Insufficient data for year {0} for plot {1!s}'.format(year, i+1), self._gv.isBatch)
                            return
                        for val in yearData.values():
                            break
                    else:
                        if not tim in yearData:
                            if isDaily:
                                ref = 'day {0!s}'.format(tim)
                            else:
                                ref = 'month {0!s}'.format(tim)
                            QSWATUtils.error(u'Insufficient data for {0} for year {1} for plot {2!s}'.format(ref, year, i+1), self._gv.isBatch)
                            return
                        val = yearData[tim]
                    plotData[i].append('{:.3g}'.format(val))
                    if not datesDone:
                        if isDaily:
                            dates.append(str(year * 1000 + tim))
                        elif isAnnual:
                            dates.append(str(year))
                        else:
                            dates.append(str(year) + '/' + str(tim))
                    (year, tim) = self.nextDate(year, tim, isDaily, isMonthly, isAnnual)
                datesDone = True
        # data all collected: write csv file
        csvFile, _ = QFileDialog.getSaveFileName(None, 'Choose a csv file', self._gv.scenariosDir, 'CSV files (*.csv)')
        if csvFile == '':
            return
        with open(csvFile, 'w', newline='') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)  # quote fields containing delimeter or other special characters 
            headers = ['Date']
            for i in range(numRows):
                headers.append(str(labels[i]))
            writer.writerow(headers)
            for d in range(len(dates)):
                row = [str(dates[d])]
                for i in range(numRows):
                    if not i in plotData:
                        QSWATUtils.error('Missing data for plot {0!s}'.format(i+1), self._gv.isBatch)
                        writer.writerow(row)
                        return
                    if not d in range(len(plotData[i])):
                        QSWATUtils.error('Missing data for date {0} for plot {1!s}'.format(dates[d], i+1), self._gv.isBatch)
                        writer.writerow(row)
                        return
                    row.append(str(plotData[i][d]))
                writer.writerow(row)
        graph = SWATGraph(csvFile)
        graph.run()
    
    def readData(self, layerId: str, isStatic: bool, table: str, var: str, where: str) -> bool:
        """Read data from database table into staticData.  Return True if no error detected."""
        if not self.conn:
            return False
        # clear existing data for layerId
        self.staticData[layerId] = dict()
        layerData = self.staticData[layerId]
        #self.areas = dict()
        #self.hasAreas = False
        if isStatic:
            varz = self.varList(True)
        else:
            cast(Dict[str, Dict[int, Dict[int, float]]], self.resultsData)[layerId] = dict()
            varz = ['[' + var + ']']
        numVars = len(varz)
        isDaily = Visualise.tableIsDaily(table)
        isMonthly = Visualise.tableIsMonthly(table)
        if isDaily:
            selectString = '[jday], [yr], [gis_id], ' + ', '.join(varz)
            sql = self._gv.db.sqlSelect(table, selectString, '[yr], [jday]', where)
            preLen = 3
        elif isMonthly:
            selectString = '[mon], [yr], [gis_id], ' + ', '.join(varz)
            sql = self._gv.db.sqlSelect(table, selectString, '[yr], [mon]', where)
            preLen = 3
        else: # annual or average annual
            selectString = '[yr], [gis_id], ' + ', '.join(varz)
            sql = self._gv.db.sqlSelect(table, selectString, '[yr]', where)
            preLen = 2
        cursor = self.conn.cursor()
        # QSWATUtils.information('SQL: {0}'.format(sql), self._gv.isBatch)
        for row in cursor.execute(sql):
            if isDaily or isMonthly:
                tim = int(row[0])
                year = int(row[1])
                gisId = int(row[2])
            else:
                tim = int(row[0])
                year = tim
                gisId = int(row[1])
            if not self.inPeriod(year, tim, table, isDaily, isMonthly):
                continue
#             if self.hasAreas:
#                 area = float(row[3])
#             if isStatic and self.hasAreas and not unit in self.areas:
#                 self.areas[unit] = area
            if not gisId in layerData:
                layerData[gisId] = dict()
            for i in range(numVars):
                # remove square brackets from each var
                var = varz[i][1:-1]
                rawVal = row[i+preLen]
                if rawVal is None:
                    val = 0.0
                else:
                    val = float(rawVal)
                if not var in layerData[gisId]:
                    layerData[gisId][var] = dict()
                if not year in layerData[gisId][var]:
                    layerData[gisId][var][year] = dict()
                layerData[gisId][var][year][tim] = val
        if len(layerData) == 0:
            QSWATUtils.error('No data has nbeen read.  Perhaps your dates are outside the dates of the table', self._gv.isBatch)
            return False
        self.summaryChanged = True
        return True
        
#     def readDailyFlowData(self, table: str, channel: int, monthData):
#         """Read data from table for channel, organised by month."""
        
        
    def inPeriod(self, year: int, tim: int, table: str, isDaily: bool, isMonthly: bool) -> bool:
        """
        Return true if year and tim are within requested period.
        
        Assumes self.[julian]startYear/Month/Day and self.[julian]finishYear/Month/Day already set.
        Assumes tim is within 1..365/6 when daily, and within 1..12 when monthly.
        """
        if year < self.startYear or year > self.finishYear:
            return False
        if Visualise.tableIsYearly(table):
            return True
        if isDaily:
            if year == self.startYear:
                return tim >= self.julianStartDay
            if year == self.finishYear:
                return tim <= self.julianFinishDay
            return True
        if isMonthly:
            if year == self.startYear:
                return tim >= self.startMonth
            if year == self.finishYear:
                return tim <= self.finishMonth
            return True
        # annual or average annual
        return True
    
    def checkFrequencyConsistent(self) -> bool:
        """Check all non-observed rows are daily, monthly or annual."""
        isDaily = False
        isMonthly = False
        isAnnual = False
        frequencySet = False
        numRows = self._dlg.tableWidget.rowCount()
        for i in range(numRows):
            table = self._dlg.tableWidget.item(i, 1).text()
            if table == '-':  # observed
                continue
            if Visualise.tableIsMonthly(table):
                if frequencySet:
                    if not isMonthly:
                        return False
                else:
                    isMonthly = True
                    frequencySet = True
            elif Visualise.tableIsAnnual(table):
                if frequencySet:
                    if not isAnnual:
                        return False
                else:
                    isAnnual = True
                    frequencySet = True
            elif Visualise.tableIsDaily(table):
                if frequencySet:
                    if not isDaily:
                        return False
                else:
                    isDaily = True
                    frequencySet = True
            else:
                # can we get here?  Assume it is OK
                pass
        return True  # no problem found
            
                
    def summariseData(self, layerId: str, isStatic: bool) -> None:
        """if isStatic, summarise data in staticData, else store all data for animate variable, saving in resultsData."""
        layerData = self.staticData[layerId]
        if isStatic:
            for index, vym in layerData.items():
                for var, ym in vym.items():
                    val = self.summarise(ym)
                    self.resultsData = cast(Dict[int, Dict[str, float]], self.resultsData)
                    if index not in self.resultsData:
                        self.resultsData[index] = dict()
                    self.resultsData[index][var] = val
        else:
            self.allAnimateVals = []
            self.resultsData = cast(Dict[str, Dict[int, Dict[int, float]]], self.resultsData)
            if not layerId in self.resultsData:
                self.resultsData[layerId] = dict()
            results = self.resultsData[layerId]
            for index, vym in layerData.items():
                for ym in vym.values():
                    for y, mval in ym.items():
                        for m, val in mval.items():
                            dat = self.makeDate(y, m)
                            if not dat in results:
                                results[dat] = dict()
                            results[dat][index] = val
                            self.allAnimateVals.append(val)
                            
    def makeDate(self, year: int, tim: int) -> int:
        """
        Make date number from year and tim according to period.
        
        tim is time field, which may be year, month or day according to period.
        """
        if self.isDaily:
            return year * 1000 + tim
        elif self.isMonthly:
            return year * 100 + tim
        else: # annual or average annual
            return year
            
        
    def startYearTime(self, isDaily: bool, isMonthly: bool) -> Tuple[int, int]:
        """Return (year, tim) pair for start date according to period."""
        if isDaily:
            return (self.startYear, self.julianStartDay)
        elif isMonthly:
            return (self.startYear, self.startMonth)
        else: # annual or average annual
            return (self.startYear, self.startYear)
            
        
    def finishYearTime(self, isDaily: bool, isMonthly: bool) -> Tuple[int, int]:
        """Return (year, tim) pair for finish date according to period."""
        if isDaily:
            return (self.finishYear, self.julianFinishDay)
        elif isMonthly:
            return (self.finishYear, self.finishMonth)
        else: # annual or average annual
            return (self.finishYear, self.finishYear)
            
        
    def nextDate(self, year: int, tim: int, isDaily: bool, isMonthly: bool, isAnnual: bool) -> Tuple[int, int]:
        """Get next (year, tim) pair according to period.
        
        self.interval only used for daily data"""
        if isAnnual:
            return (year + 1, year + 1)
        elif isDaily:
            tim += self.interval
            yearLength = 366 if self.isLeap(year) else 365
            while tim > yearLength:
                year += 1
                tim -= yearLength
                yearLength = 366 if self.isLeap(year) else 365
            return (year, tim)
        elif isMonthly:
            tim += 1
            if tim == 13:
                year += 1
                tim = 1
            return (year, tim)
        else:
            return (year, tim)
    
    @staticmethod
    def tableIsDailyMonthlyOrAnnual(table: str) -> Tuple[bool, bool, bool, bool]:
        """Return isdaily, isMonthly, isAnnual, isAverageAnnual tuple of booleans for table."""
        return Visualise.tableIsDaily(table), Visualise.tableIsMonthly(table), \
            Visualise.tableIsAnnual(table), Visualise.tableIsAvAnnual(table)
    
    @staticmethod
    def tableIsDaily(table: str) -> bool:
        """Return true if daily."""
        return table.endswith('_day')
    
    @staticmethod
    def tableIsMonthly(table: str) -> bool:
        """Return true if monthly."""
        return table.endswith('_mon')
    
    @staticmethod
    def tableIsAnnual(table: str) -> bool:
        """Return true if annual."""
        return table.endswith('_yr')
    
    @staticmethod
    def tableIsAvAnnual(table: str) -> bool:
        """Return true if average annual."""
        return table.endswith('_aa')
    
    @staticmethod
    def tableIsYearly(table: str) -> bool:
        """Return true if annual or average annual."""
        return Visualise.tableIsAnnual(table) or Visualise.tableIsAvAnnual(table)
        
    def summarise(self, data: Dict[Any, Dict[Any, float]]) -> float:
        """Summarise values according to summary method."""
        if self.isAA:
            # there will only be one value, so total will simply return it
            return self.summariseTotal(data)
        if self._dlg.summaryCombo.currentText() == Visualise._TOTALS:
            return self.summariseTotal(data)
        elif self._dlg.summaryCombo.currentText() == Visualise._ANNUALMEANS:
            return self.summariseAnnual(data)
        elif self._dlg.summaryCombo.currentText() == Visualise._MONTHLYMEANS:
            return self.summariseMonthly(data)
        elif self._dlg.summaryCombo.currentText() == Visualise._DAILYMEANS:
            return self.summariseDaily(data)
        elif self._dlg.summaryCombo.currentText() == Visualise._MAXIMA:
            return self.summariseMaxima(data)
        elif self._dlg.summaryCombo.currentText() == Visualise._MINIMA:
            return self.summariseMinima(data)
        else:
            QSWATUtils.error('Internal error: unknown summary method: please report', self._gv.isBatch)
            return 0
            
    def summariseTotal(self, data: Dict[Any, Dict[Any, float]]) -> float:
        """Sum values and return."""
        total = 0.0
        for mv in data.values():
            for v in mv.values():
                total += v
        return total
        
    def summariseAnnual(self, data: Dict[Any, Dict[Any, float]]) -> float:
        """Return total divided by period in years."""
        return self.summariseTotal(data) / self.periodYears
        
    def summariseMonthly(self, data: Dict[Any, Dict[Any, float]]) -> float:
        """Return total divided by period in months."""
        return self.summariseTotal(data) / self.periodMonths
        
    def summariseDaily(self, data: Dict[Any, Dict[Any, float]]) -> float:
        """Return total divided by period in days."""
        return self.summariseTotal(data) / self.periodDays
        
    def summariseMaxima(self, data: Dict[Any, Dict[Any, float]]) -> float:
        """Return maximum of values."""
        maxv = 0.0
        for mv in data.values():
            for v in mv.values():
                maxv = max(maxv, v)
        return maxv
        
    def summariseMinima(self, data: Dict[Any, Dict[Any, float]]) -> float:
        """Return minimum of values."""
        minv = float('inf')
        for mv in data.values():
            for v in mv.values():
                minv = min(minv, v)
        return minv
                
    @staticmethod
    def isLeap(year: int) -> bool:
        """Return true if year is a leap year."""
        if year % 4 == 0:
            if year % 100 == 0:
                return year % 400 == 0
            else:
                return True
        else:
            return False
            
    def setGisIdPlot(self) -> None:
        """Add gis id numbers to unitPlot combo."""
        if self.conn is None or self.table == '':
            return
        self._dlg.unitPlot.clear()
        self._dlg.unitPlot.addItem('')
        sql = 'SELECT [gis_id] FROM {0}'.format(self.table)
        firstId = None
        try:
            for row in self.conn.execute(sql):
                gisId = row[0]
                if firstId is None:
                    firstId = gisId
                elif gisId == firstId:
                    return
                self._dlg.unitPlot.addItem(str(gisId))
            self._dlg.unitPlot.setCurrentIndex(0)
        except sqlite3.OperationalError:
            QSWATUtils.error('Table {0} in {1} has no gis_id column'.format(self.table, self.db), self._gv.isBatch)
            
    def varList(self, bracket: bool) -> List[str]:
        """Return variables in variableList as a list of strings, with square brackets if bracket is true."""
        result: List[str] = []
        numRows = self._dlg.variableList.count()
        for row in range(numRows):
            var = self._dlg.variableList.item(row).text()
            # bracket variables when using in sql, to avoid reserved words and '/'
            if bracket:
                var = '[' + var + ']'
            result.append(var)
        return result
    
    def setResultsFile(self) -> None:
        """Set results file by asking user."""
        try:
            path = os.path.split(self._dlg.resultsFileEdit.text())[0]
        except Exception:
            path = ''
        base = self.selectBase()
        if base is None:
            return
        resultsFileName, _ = QFileDialog.getSaveFileName(None, base + 'results', path, QgsProviderRegistry.instance().fileVectorFilters())
        if resultsFileName == '':
            return
        direc, resName = os.path.split(resultsFileName)
        direcUp, direcName = os.path.split(direc)
        if direcName == Parameters._RESULTS:
            ## check we are not overwriting a template
            direcUpUp = os.path.split(direcUp)[0]
            if QSWATUtils.samePath(direcUpUp, self._gv.scenariosDir):
                base = os.path.splitext(resName)[0]
                if base in {Parameters._SUBS, Parameters._RIVS, Parameters._HRUS, Parameters._LSUS, Parameters._AQUIFERS, Parameters._DEEPAQUIFERS}:
                    QSWATUtils.information('The file {0} should not be overwritten: please choose another file name.'.format(os.path.splitext(resultsFileName)[0] + '.shp'), self._gv.isBatch)
                    return
        elif direcName == Parameters._ANIMATION:
            ## check we are not using the Animation directory
            direcUpUp = os.path.split(direcUp)[0]
            if QSWATUtils.samePath(direcUpUp, self._gv.resultsDir):
                QSWATUtils.information('Please do not use {0} for results as it can be overwritten by animation.'.format(os.path.splitext(resultsFileName)[0] + '.shp'), self._gv.isBatch)
                return
        self._dlg.resultsFileEdit.setText(resultsFileName)
        self.resultsFileUpToDate = False
        
    def setObservedFile(self) -> None:
        """Get an observed data file from the user."""
        try:
            path = os.path.split(self._dlg.observedFileEdit.text())[0]
        except Exception:
            path = ''
        observedFileName, _ = QFileDialog.getOpenFileName(None, 'Choose observed data file', path, 'CSV files (*.csv);;Any file (*.*)')
        if observedFileName == '':
            return
        self.observedFileName = observedFileName
        self._dlg.observedFileEdit.setText(observedFileName)
        proj = QgsProject.instance()
        proj.writeEntry(self.title, 'observed/observedFile', self.observedFileName)
        proj.write()
        
    def selectBase(self) -> Optional[str]:
        """Return base name of shapefile used for results according to table name and availability of actual hrus file"""
        if self.table.startswith('channel_'):
            return cast(str, Parameters._RIVS)
        if self.table.startswith('aquifer_'):
            return cast(str, Parameters._AQUIFERS)
        if self.table.startswith('deep_aquifer_'):
            return cast(str, Parameters._DEEPAQUIFERS)
        if self.table.startswith('lsunit_'):
            return cast(str, Parameters._LSUS)
        if self.table.startswith('hru_'):
            if self.hasHRUs:
                return cast(str, Parameters._HRUS)
            else:
                QSWATUtils.error('Cannot show results for HRUs since no full HRUs file was created', self._gv.isBatch)
                return None
        QSWATUtils.error('Do not know how to show results for table {0}'.format(self.table), self._gv.isBatch)
        return None
        
    def createResultsFile(self) -> bool:
        """
        Create results shapefile.
        
        Assumes:
        - resultsFileEdit contains suitable text for results file name
        - one or more variables is selected in variableList (and uses the first one)
        - resultsData is suitably populated
        """
        nextResultsFile = self._dlg.resultsFileEdit.text()
        proj = QgsProject.instance()
        root = proj.layerTreeRoot()
        if os.path.exists(nextResultsFile):
            reply = QSWATUtils.question('Results file {0} already exists.  Do you wish to overwrite it?'.format(nextResultsFile), self._gv.isBatch, True)
            if reply != QMessageBox.Yes:
                return False
            if nextResultsFile == self.resultsFile:
                # remove existing layer so new one replaces it
                QSWATUtils.removeLayer(self.resultsFile, root)
            else:
                self.resultsFile = nextResultsFile
        else:
            self.resultsFile = nextResultsFile
        resultsDir = os.path.split(self.db)[0]
        baseName = self.selectBase()
        if baseName is None:
            return False
        resultsBase = QSWATUtils.join(resultsDir, baseName) + '.shp'
        outdir, outfile = os.path.split(self.resultsFile)
        outbase = os.path.splitext(outfile)[0]
        QSWATUtils.copyShapefile(resultsBase, outbase, outdir)
        selectVar = self._dlg.variableList.selectedItems()[0].text()[:10]
        summary = Visualise._ANNUALMEANS if self.isAA else self._dlg.summaryCombo.currentText()
        legend = '{0} {1} {2}'.format(self.scenario, selectVar, summary)
        if baseName == Parameters._SUBS:
            self.subResultsLayer = QgsVectorLayer(self.resultsFile, legend, 'ogr')
            self.subResultsLayer.rendererChanged.connect(self.changeSubRenderer)
            self.internalChangeToSubRenderer = True
            self.keepSubColours = False
            self.currentResultsLayer = self.subResultsLayer
        elif baseName == Parameters._LSUS:
            self.lsuResultsLayer = QgsVectorLayer(self.resultsFile, legend, 'ogr')
            self.lsuResultsLayer.rendererChanged.connect(self.changeLSURenderer)
            self.internalChangeToLSURenderer = True
            self.keepLSUColours = False
            self.currentResultsLayer = self.lsuResultsLayer
        elif baseName == Parameters._HRUS:
            self.hruResultsLayer = QgsVectorLayer(self.resultsFile, legend, 'ogr')
            self.hruResultsLayer.rendererChanged.connect(self.changeHRURenderer)
            self.internalChangeToHRURenderer = True
            self.keepHRUColours = False
            self.currentResultsLayer = self.hruResultsLayer
        elif baseName == Parameters._AQUIFERS:
            self.aquResultsLayer = QgsVectorLayer(self.resultsFile, legend, 'ogr')
            self.aquResultsLayer.rendererChanged.connect(self.changeAquRenderer)
            self.internalChangeToAquRenderer = True
            self.keepAquColours = False
            self.currentResultsLayer = self.aquResultsLayer
        elif baseName == Parameters._DEEPAQUIFERS:
            self.deepAquResultsLayer = QgsVectorLayer(self.resultsFile, legend, 'ogr')
            self.deepAquResultsLayer.rendererChanged.connect(self.changeDeepAquRenderer)
            self.internalChangeToDeepAquRenderer = True
            self.keepDeepAquColours = False
            self.currentResultsLayer = self.deepAquResultsLayer
        else:
            self.rivResultsLayer = QgsVectorLayer(self.resultsFile, legend, 'ogr')
            self.rivResultsLayer.rendererChanged.connect(self.changeRivRenderer)
            self.internalChangeToRivRenderer = True
            self.keepRivColours = False
            self.currentResultsLayer = self.rivResultsLayer
#         if self.hasAreas:
#             field = QgsField(Visualise._AREA, QVariant.Double, len=20, prec=0)
#             if not layer.dataProvider().addAttributes([field]):
#                 QSWATUtils.error('Could not add field {0} to results file {1}'.format(Visualise._AREA, self.resultsFile), self._gv.isBatch)
#                 return False
        varz = self.varList(False)
        for var in varz:
            field = QgsField(var, QVariant.Double)
            if not self.currentResultsLayer.dataProvider().addAttributes([field]):
                QSWATUtils.error('Could not add field {0} to results file {1}'.format(var, self.resultsFile), self._gv.isBatch)
                return False
        self.currentResultsLayer.updateFields()
        self.updateResultsFile() 
        
        self.currentResultsLayer = cast(QgsVectorLayer, proj.addMapLayer(self.currentResultsLayer, False))
        resultsGroup = root.findGroup(QSWATUtils._RESULTS_GROUP_NAME)
        assert resultsGroup is not None
        resultsGroup.insertLayer(0, self.currentResultsLayer)
        self._gv.iface.setActiveLayer(self.currentResultsLayer)
        if baseName == Parameters._SUBS:
            # add labels
            self.currentResultsLayer.loadNamedStyle(QSWATUtils.join(self._gv.plugin_dir, 'subresults.qml'))
            self.internalChangeToSubRenderer = False
            baseMapTip = FileTypes.mapTip(FileTypes._SUBBASINS)
        elif baseName == Parameters._LSUS:
            self.internalChangeToLSURenderer = False
            baseMapTip = FileTypes.mapTip(FileTypes._LSUS)
        elif baseName == Parameters._HRUS:
            self.internalChangeToHRURenderer = False
            baseMapTip = FileTypes.mapTip(FileTypes._HRUS)
        elif baseName == Parameters._AQUIFERS:
            self.internalChangeToAquRenderer = False
            baseMapTip = FileTypes.mapTip(FileTypes._AQUIFERS)
        elif baseName == Parameters._DEEPAQUIFERS:
            self.internalChangeToDeepAquRenderer = False
            baseMapTip = FileTypes.mapTip(FileTypes._AQUIFERS)
        else:
            self.internalChangeToRivRenderer = False
            baseMapTip = FileTypes.mapTip(FileTypes._CHANNELREACHES)
        self.currentResultsLayer.setMapTipTemplate(baseMapTip + '<br/><b>{0}:</b> [% "{0}" %]'.format(selectVar))
        self.currentResultsLayer.updatedFields.connect(self.addResultsVars)
        return True
        
    def updateResultsFile(self) -> None:
        """Write resultsData to resultsFile."""
        base = self.selectBase()
        if base is None:
            return
        layer = self.subResultsLayer if base == Parameters._SUBS \
                else self.lsuResultsLayer if base == Parameters._LSUS \
                else self.hruResultsLayer if base == Parameters._HRUS \
                else self.aquResultsLayer if base == Parameters._AQUIFERS \
                else self.deepAquResultsLayer if base == Parameters._DEEPAQUIFERS \
                else self.rivResultsLayer
        varz = self.varList(False)
        varIndexes = dict()
#         if self.hasAreas:
#             varIndexes[Visualise._AREA] = self._gv.topo.getIndex(layer, Visualise._AREA)
        for var in varz:
            varIndexes[var] = self._gv.topo.getIndex(layer, var)
        assert layer is not None
        layer.startEditing()
        for f in layer.getFeatures():
            fid = f.id()
            if base == Parameters._HRUS:
                # May be split HRUs; just use first
                # This is inadequate for some variables, but no way to know of correct val is sum of vals, mean, etc.
                unitText = f[QSWATTopology._HRUS]
                if 'PND' in unitText or 'RES' in unitText:
                    continue
                unit = int(unitText.split(',')[0]) 
            elif base == Parameters._LSUS:
                unit = f[QSWATTopology._LSUID]
            elif base == Parameters._SUBS:
                unit = f[QSWATTopology._SUBBASIN]
            elif base == Parameters._AQUIFERS or base == Parameters._DEEPAQUIFERS:
                unit = f[QSWATTopology._AQUIFER]
            else:
                unit = f[QSWATTopology._CHANNEL]
#             if self.hasAreas:
#                 area = self.areas.get(unit, None)
#                 if area is None:
#                     if base == Parameters._HRUS:
#                         ref = 'HRU {0!s}'.format(unit)
#                     elif base == Parameters._LSUS:
#                         ref = 'LSU {0!s}'.format(unit)
#                     else:
#                         ref = 'subbasin {0!s}'.format(unit)
#                     QSWATUtils.error('Cannot get area for {0}: have you run SWAT and saved data since running QSWAT?'.format(ref), self._gv.isBatch)
#                     return
#                 if not layer.changeAttributeValue(fid, varIndexes[Visualise._AREA], float(area)):
#                     QSWATUtils.error('Could not set attribute {0} in results file {1}'.format(Visualise._AREA, self.resultsFile), self._gv.isBatch)
#                     return
            for var in varz:
                subData = cast(Dict[int, Dict[str, float]], self.resultsData).get(unit, None)
                if subData is not None:
                    data = subData.get(var, None)
                else:
                    data = None
                if data is None:
                    if base == Parameters._HRUS:
                        ref = 'HRU {0!s}'.format(unit)
                    elif base == Parameters._LSUS:
                        ref = 'LSU {0!s}'.format(unit)
                    elif base == Parameters._SUBS:
                        ref = 'subbasin {0!s}'.format(unit)
                    elif base == Parameters._AQUIFERS:
                        ref = 'aquifer {0!s}'.format(unit)
                    elif base == Parameters._DEEPAQUIFERS:
                        ref = 'deep aquifer {0!s}'.format(unit)
                    else:
                        ref = 'channel {0!s}'.format(unit)
                    QSWATUtils.error('Cannot get data for variable {0} for {1} in table {2} in {3}: have you run SWAT+ and saved data since running QSWAT+?'.
                                     format(var, ref, self.table, self.db), self._gv.isBatch)
                    return
                if not layer.changeAttributeValue(fid, varIndexes[var], float(data) if isinstance(data, numpy.float64) else data):
                    QSWATUtils.error('Could not set attribute {0} in results file {1}'.format(var, self.resultsFile), self._gv.isBatch)
                    return
        layer.commitChanges()
        self.summaryChanged = False
        
    def colourResultsFile(self) -> None:
        """
        Colour results layer according to current results variable and update legend.
        
        if createColour is false the existing colour ramp and number of classes can be reused
        """
        base = self.selectBase()
        if base is None:
            return
        if base == Parameters._SUBS:
            layer = self.subResultsLayer
            keepColours = self.keepSubColours
            symbol: QgsSymbol = QgsFillSymbol()
        elif base == Parameters._LSUS:
            layer = self.lsuResultsLayer
            keepColours = self.keepLSUColours
            symbol = QgsFillSymbol()
        elif base == Parameters._HRUS:
            layer = self.hruResultsLayer
            keepColours = self.keepHRUColours
            symbol = QgsFillSymbol()
        elif base == Parameters._AQUIFERS:
            layer = self.aquResultsLayer
            keepColours = self.keepAquColours
            symbol = QgsFillSymbol()
        elif base == Parameters._DEEPAQUIFERS:
            layer = self.deepAquResultsLayer
            keepColours = self.keepDeepAquColours
            symbol = QgsFillSymbol()
        else:
            layer = self.rivResultsLayer
            keepColours = self.keepRivColours
            props = {'width_expression': QSWATTopology._PENWIDTH}
            symbol = QgsLineSymbol.createSimple(props)
            symbol.setWidth(1.0)
        selectVar = self._dlg.variableList.selectedItems()[0].text()
        selectVarShort = selectVar[:10]
        summary = Visualise._ANNUALMEANS if self.isAA else self._dlg.summaryCombo.currentText()
        assert layer is not None
        layer.setName('{0} {1} {2}'.format(self.scenario, selectVar, summary))
        if not keepColours:
            count = 5
            opacity = 1.0 if base == Parameters._RIVS else 0.65
        else:
            # same layer as currently - try to use same range size and colours, and same opacity
            try:
                oldRenderer = cast(QgsGraduatedSymbolRenderer, layer.renderer())
                oldRanges = oldRenderer.ranges()
                count = len(oldRanges)
                ramp = oldRenderer.sourceColorRamp()
                opacity = layer.opacity()
            except Exception:
                # don't care if no suitable colours, so no message, just revert to defaults
                keepColours = False
                count = 5
                opacity = 1.0 if base == Parameters._RIVS else 0.65
        if not keepColours:
            ramp = self.chooseColorRamp(self.table, selectVar)
        labelFmt = QgsRendererRangeLabelFormat('%1 - %2', 0)
        renderer = QgsGraduatedSymbolRenderer.createRenderer(layer, selectVarShort, count, 
                                                             QgsGraduatedSymbolRenderer.Jenks, symbol, 
                                                             ramp, labelFmt)
        renderer.calculateLabelPrecision()
        # previous line should be enough to update precision, but in practice seems we need to recreate renderer
        precision = renderer.labelFormat().precision()
        QSWATUtils.loginfo('Precision: {0}'.format(precision))
        # default seems too high
        labelFmt = QgsRendererRangeLabelFormat('%1 - %2', precision-1)
        # should be enough to update labelFmt, but seems to be necessary to make renderer again to reflect new precision
        renderer = QgsGraduatedSymbolRenderer.createRenderer(layer, selectVarShort, count, 
                                                             QgsGraduatedSymbolRenderer.Jenks, symbol, 
                                                             ramp, labelFmt)
        # new method causes crash
#         method = QgsClassificationJenks()
#         method.setLabelFormat('%1 - %2')
#         classes = method.classes(layer, selectVarShort, count)
#         ranges = [QgsRendererRange(clas, symbol) for clas in classes]
#         renderer = QgsGraduatedSymbolRenderer(selectVarShort, ranges)
#         renderer.setSourceColorRamp(ramp)
#         renderer.setClassificationMethod(method)
#         renderer.updateColorRamp(ramp)
        if base == Parameters._SUBS:
            self.internalChangeToSubRenderer = True
        elif base == Parameters._LSUS:
            self.internalChangeToLSURenderer = True
        elif base == Parameters._HRUS:
            self.internalChangeToHRURenderer = True
        elif base == Parameters._AQUIFERS:
            self.internalChangeToAquRenderer = True
        elif base == Parameters._DEEPAQUIFERS:
            self.internalChangeToDeepAquRenderer = True
        else:
            self.internalChangeToRivRenderer = True
        layer.setRenderer(renderer)
        layer.setOpacity(opacity)
        layer.triggerRepaint()
        self._gv.iface.layerTreeView().refreshLayerSymbology(layer.id())
        canvas = self._gv.iface.mapCanvas()
        self.clearMapTitle()
        self.mapTitle = MapTitle(self.conn, canvas, self.table, self.title, layer)
        canvas.refresh()
        if base == Parameters._SUBS:
            self.internalChangeToSubRenderer = False
            self.keepSubColours = keepColours
        elif base == Parameters._LSUS:
            self.internalChangeToLSURenderer = False
            self.keepLSUColours = keepColours
        elif base == Parameters._HRUS:
            self.internalChangeToHRURenderer = False
            self.keepHRUColours = keepColours
        elif base == Parameters._AQUIFERS:
            self.internalChangeToAquRenderer = False
            self.keepAquColours = keepColours
        elif base == Parameters._DEEPAQUIFERS:
            self.internalChangeToDeepAquRenderer = False
            self.keepDeepAquColours = keepColours
        else:
            self.internalChangeToRivRenderer = False
            self.keepRivColours = keepColours
            
    def addResultsVars(self) -> None:
        """Add any extra fields to variableList."""
        if not self.resultsLayerExists():
            return
        newVars = []
        assert self.currentResultsLayer is not None
        fields = self.currentResultsLayer.fields()
        indexes = fields.allAttributesList()
        for i in indexes:
            if fields.fieldOrigin(i) == QgsFields.OriginEdit:  # added by editing
                newVars.append(fields.at(i).name())
        for var in newVars:
            items = self._dlg.variableList.findItems(var, Qt.MatchExactly)
            if not items or items == []:
                # add var to variableList
                item = QListWidgetItem()
                item.setText(var)
                self._dlg.variableList.addItem(item)
            
    def resultsLayerExists(self) -> bool:
        """Return true if current results layer has not been removed."""
#         base = self.selectBase()
#         if base is None:
#             return False
#         if base == Parameters._SUBS:
#             layer = self.subResultsLayer
#         if base == Parameters._LSUS:
#             layer = self.lsuResultsLayer
#         elif base == Parameters._HRUS:
#             layer = self.hruResultsLayer
#         else:
#             layer = self.rivResultsLayer
        if self.currentResultsLayer is None:
            return False
        try:
            # a removed layer will fail with a RuntimeError 
            self.currentResultsLayer.objectName()
            return True
        except RuntimeError:
            return False
        
    def createAnimationLayer(self) -> bool:
        """
        Create animation with new shapefile or existing one.
        
        Assumes:
        - animation variable is set
        """
        proj = QgsProject.instance()
        root = proj.layerTreeRoot()
        base = self.selectBase()
        if base is None:
            return False
        resultsBase = QSWATUtils.join(self._gv.resultsDir, base) + '.shp'
        animateFileBase = QSWATUtils.join(self._gv.animationDir, base) + '.shp'
        animateFile, num = QSWATUtils.nextFileName(animateFileBase, 0)
        QSWATUtils.copyShapefile(resultsBase, base + str(num), self._gv.animationDir)
        if not self.stillFileBase or self.stillFileBase == '':
            self.stillFileBase = QSWATUtils.join(self._gv.pngDir, Parameters._STILLPNG)
        self.currentStillNumber = 0
        animateLayer = QgsVectorLayer(animateFile, '{0} {1}'.format(self.scenario, self.animateVar), 'ogr')
        provider = animateLayer.dataProvider()
        field = QgsField(self.animateVar, QVariant.Double)
        if not provider.addAttributes([field]):
            QSWATUtils.error(u'Could not add field {0} to animation file {1}'.format(self.animateVar, animateFile), self._gv.isBatch)
            return False
        animateLayer.updateFields()
        animateIndex = self._gv.topo.getProviderIndex(provider, self.animateVar)
        # place layer at top of animation group if new,
        # else above current animation layer, and mark that for removal
        animationGroup = root.findGroup(QSWATUtils._ANIMATION_GROUP_NAME)
        assert animationGroup is not None
        layerToRemoveId = None
        index = 0
        if self._dlg.currentAnimation.isChecked():
            animations = animationGroup.findLayers()
            if len(animations) == 1:
                layerToRemoveId = animations[0].layerId()
                index = 0
            else:
                currentLayer = self._gv.iface.activeLayer()
                assert currentLayer is not None
                currentLayerId = currentLayer.id()
                for i in range(len(animations)):
                    if animations[i].layerId() == currentLayerId:
                        index = i 
                        layerToRemoveId = currentLayerId
                        break
        self.animateLayer = cast(QgsVectorLayer, proj.addMapLayer(animateLayer, False))
        assert self.animateLayer is not None
        animationGroup.insertLayer(index, self.animateLayer)
        self._gv.iface.setActiveLayer(self.animateLayer)
        if layerToRemoveId is not None:
            proj.removeMapLayer(layerToRemoveId)
        self.animateIndexes[self.animateLayer.id()] = animateIndex
        # add labels if based on subbasins
        if base == Parameters._SUBS:
            self.animateLayer.loadNamedStyle(QSWATUtils.join(self._gv.plugin_dir, 'subsresults.qml'))
            baseMapTip = FileTypes.mapTip(FileTypes._SUBBASINS)
        elif base == Parameters._LSUS:
            baseMapTip = FileTypes.mapTip(FileTypes._LSUS)
        elif base == Parameters._HRUS:
            baseMapTip = FileTypes.mapTip(FileTypes._HRUS)
        elif base == Parameters._AQUIFERS or base == Parameters._DEEPAQUIFERS:
            baseMapTip = FileTypes.mapTip(FileTypes._AQUIFERS)
        else:
            baseMapTip = FileTypes.mapTip(FileTypes._CHANNELREACHES)
        self.animateLayer.setMapTipTemplate(baseMapTip + '<br/><b>{0}:</b> [% "{0}" %]'.format(self.animateVar))
        return True
            
    def colourAnimationLayer(self) -> None:
        """Colour animation layer.
        
        Assumes allAnimateVals is suitably populated.
        """
        base = self.selectBase()
        if base is None:
            return
        count = 5
        opacity = 1.0 if base == Parameters._RIVS else 0.65
        ramp = self.chooseColorRamp(self.table, self.animateVar)
        # replaced by Cython code
        #=======================================================================
        # breaks, minimum = self.getJenksBreaks(self.allAnimateVals, count)
        # QSWATUtils.loginfo('Breaks: {0!s}'.format(breaks))
        #=======================================================================
        cbreaks = jenks(self.allAnimateVals, count)
        QSWATUtils.loginfo('Breaks: {0!s}'.format(cbreaks))
        rangeList = []
        for i in range(count):
            # adjust min and max by 1% to avoid rounding errors causing values to be outside the range
            minVal = cbreaks[0] * 0.99 if i == 0 else cbreaks[i]
            maxVal = cbreaks[count] * 1.01 if i == count-1 else cbreaks[i+1]
            colourVal = i / (count - 1)
            colour = ramp.color(colourVal)
            rangeList.append(self.makeSymbologyForRange(minVal, maxVal, colour, 4))
        # deprecated but works
        renderer = QgsGraduatedSymbolRenderer(self.animateVar[:10], rangeList)
        renderer.setMode(QgsGraduatedSymbolRenderer.Custom)
        renderer.calculateLabelPrecision()
        precision = renderer.labelFormat().precision()
        # new method but fails when repainting    
#         method = QgsClassificationCustom()
#         renderer = QgsGraduatedSymbolRenderer(self.animateVar[:10], rangeList)
#         renderer.setClassificationMethod(method)
#         renderer.calculateLabelPrecision()
#         precision = renderer.classificationMethod().labelPrecision()       
        QSWATUtils.loginfo('Animation precision: {0}'.format(precision-1))
        # repeat with calculated precision - 1
        rangeList = []
        for i in range(count):
            # adjust min and max by 1% to avoid rounding errors causing values to be outside the range
            minVal = cbreaks[0] * 0.99 if i == 0 else cbreaks[i]
            maxVal = cbreaks[count] * 1.01 if i == count-1 else cbreaks[i+1]
            colourVal = i / (count - 1)
            colour = ramp.color(colourVal)
            # default precision too high
            rangeList.append(self.makeSymbologyForRange(minVal, maxVal, colour, precision-1))
        renderer = QgsGraduatedSymbolRenderer(self.animateVar[:10], rangeList)
        renderer.setMode(QgsGraduatedSymbolRenderer.Custom)
        # new method but fails when repainting 
#         renderer.setSourceColorRamp(ramp)
#         #renderer.classificationMethod().setLabelPrecision(precision-1)
#         renderer.updateColorRamp(ramp)
#         renderer.updateRangeLabels()        
        assert self.animateLayer is not None
        self.animateLayer.setRenderer(renderer)
        self.animateLayer.setOpacity(opacity)
        self._gv.iface.layerTreeView().refreshLayerSymbology(self.animateLayer.id())
        self._gv.iface.setActiveLayer(self.animateLayer)
#         animations = QSWATUtils.getLayersInGroup(QSWATUtils._ANIMATION_GROUP_NAME, li, visible=True)
#         if len(animations) > 0:
#             canvas = self._gv.iface.mapCanvas()
#             if self.mapTitle is not None:
#                 canvas.scene().removeItem(self.mapTitle)
#                 canvas.refresh()
#             self.mapTitle = MapTitle(self.conn, canvas, self.table, self.title, animations[0])
#             canvas.refresh()
        
    def createAnimationComposition(self) -> None:
        """Create print composer to capture each animation step."""
        proj = QgsProject.instance()
        root = proj.layerTreeRoot()
        animationLayers = QSWATUtils.getLayersInGroup(QSWATUtils._ANIMATION_GROUP_NAME, root)
        watershedLayers = QSWATUtils.getLayersInGroup(QSWATUtils._WATERSHED_GROUP_NAME, root, visible=True)
        # choose template file and set its width and height
        # width and height here need to be updated if template file is changed
        count = self._dlg.composeCount.value()
        isLandscape = self._dlg.composeLandscape.isChecked()
        if count == 1:
            if isLandscape:
                templ = '1Landscape.qpt'
                width = 230.0
                height = 160.0
            else:
                templ = '1Portrait.qpt'
                width = 190.0
                height = 200.0
        elif count == 2:
            if isLandscape:
                templ = '2Landscape.qpt'
                width = 125.0
                height = 120.0
            else:
                templ = '2Portrait.qpt'
                width = 150.0
                height = 120.0
        elif count == 3:
            if isLandscape:
                templ = '3Landscape.qpt'
                width = 90.0
                height = 110.0
            else:
                templ = '3Portrait.qpt'
                width = 150.0
                height = 80.0
        elif count == 4:
            if isLandscape:
                templ = '4Landscape.qpt'
                width = 95.0
                height = 80.0
            else:
                templ = '4Portrait.qpt'
                width = 85.0
                height = 85.0
        elif count == 6:
            if isLandscape:
                templ = '6Landscape.qpt'
                width = 90.0
                height = 40.0
            else:
                templ = '6Portrait.qpt'
                width = 55.0
                height = 80.0
        else:
            QSWATUtils.error('There are composition templates only for 1, 2, 3, 4 or 6 result maps, not for {0}'.format(count), self._gv.isBatch)
            return
        templateIn = QSWATUtils.join(self._gv.plugin_dir, 'PrintTemplate' + templ)
        self.animationTemplate = QSWATUtils.join(self._gv.resultsDir, 'AnimationTemplate.qpt')
        # make substitution table
        subs = dict()
        northArrow = self.findNorthArrow()
        if not os.path.isfile(northArrow):
            QSWATUtils.error('Failed to find north arrow {0}.  You will need to repair the layout.'.format(northArrow), self._gv.isBatch)
        subs['%%NorthArrow%%'] = northArrow
        subs['%%ProjectName%%'] = self.title
        numLayers = len(animationLayers)
        if count > numLayers:
            QSWATUtils.error(u'You want to make a print of {0} maps, but you only have {1} animation layers'.format(count, numLayers), self._gv.isBatch)
            return
        extent = self._gv.iface.mapCanvas().extent()
        xmax = extent.xMaximum()
        xmin = extent.xMinimum()
        ymin = extent.yMinimum()
        ymax = extent.yMaximum()
        QSWATUtils.loginfo('Map canvas extent {0}, {1}, {2}, {3}'.format(str(int(xmin + 0.5)), str(int(ymin + 0.5)), 
                                                                         str(int(xmax + 0.5)), str(int(ymax + 0.5))))
        # need to expand either x or y extent to fit map shape
        xdiff = ((ymax - ymin) / height) * width - (xmax - xmin)
        if xdiff > 0:
            # need to expand x extent
            xmin = xmin - xdiff / 2
            xmax = xmax + xdiff / 2
        else:
            # expand y extent
            ydiff = (((xmax - xmin) / width) * height) - (ymax - ymin)
            ymin = ymin - ydiff / 2
            ymax = ymax + ydiff / 2
        QSWATUtils.loginfo('Map extent set to {0}, {1}, {2}, {3}'.format(str(int(xmin + 0.5)), str(int(ymin + 0.5)), 
                                                                         str(int(xmax + 0.5)), str(int(ymax + 0.5))))
        # estimate of segment size for scale
        # aim is approx 10mm for 1 segment
        # we make size a power of 10 so that segments are 1km, or 10, or 100, etc.
        segSize = 10 ** int(math.log10((xmax - xmin) / (width / 10)) + 0.5)
        layerStr = '<Layer source="{0}" provider="ogr" name="{1}">{2}</Layer>'
        for i in range(count):
            layer = animationLayers[i].layer()
            subs['%%LayerId{0}%%'.format(i)] = layer.id()
            subs['%%LayerName{0}%%'.format(i)] = layer.name()
            subs['%%YMin{0}%%'.format(i)] = str(ymin)
            subs['%%XMin{0}%%'.format(i)] = str(xmin)
            subs['%%YMax{0}%%'.format(i)] = str(ymax)
            subs['%%XMax{0}%%'.format(i)] = str(xmax)
            subs['%%ScaleSegSize%%'] = str(segSize)
            subs['%%Layer{0}%%'.format(i)] = layerStr.format(QSWATUtils.layerFilename(layer), layer.name(), layer.id())
        for i in range(6):  # 6 entries in template for background layers
            if i < len(watershedLayers):
                wLayer = watershedLayers[i].layer()
                subs['%%WshedLayer{0}%%'.format(i)] = layerStr.format(QSWATUtils.layerFilename(wLayer), wLayer.name(), wLayer.id())
            else:  # remove unused ones
                subs['%%WshedLayer{0}%%'.format(i)] = ''
        # seems to do no harm to leave unused <Layer> items with original pattern, so we don't bother removing them
        with open(templateIn, 'rU') as inFile:
            with open(self.animationTemplate, 'w') as outFile:
                for line in inFile:
                    outFile.write(Visualise.replaceInLine(line, subs))
        QSWATUtils.loginfo('Print layout template {0} written'.format(self.animationTemplate))
        self.animationDOM = QDomDocument()
        f = QFile(self.animationTemplate)
        if f.open(QIODevice.ReadOnly):
            OK = self.animationDOM.setContent(f)[0]
            if not OK:
                QSWATUtils.error('Cannot parse template file {0}'.format(self.animationTemplate), self._gv.isBatch)
                return
        else:
            QSWATUtils.error('Cannot open template file {0}'.format(self.animationTemplate), self._gv.isBatch) 
            return 
        if not self._gv.isBatch:
            QSWATUtils.information("""
            The layout designer is about to start, showing the current layout for the animation.
            
            You can change the layout as you wish, and then you should 'Save as Template' in the designer menu, using {0} as the template file.  
            If this file already exists: you will have to confirm overwriting it.
            Then close the layout designer.
            If you don't change anything you can simply close the layout designer without saving.
            
            Then start the animation running.
            """.format(self.animationTemplate), False) 
            title = 'Animation base'
            # remove layout from layout manager, in case still there
            try:
                assert self.animationLayout is not None
                proj.layoutManager().removeLayout(self.animationLayout)
            except:
                pass
            # clean up in case previous one remains
            self.animationLayout = None
            self.animationLayout = QgsPrintLayout(proj)
            self.animationLayout.initializeDefaults()
            self.animationLayout.setName(title)
            self.setDateInTemplate()
            items = self.animationLayout.loadFromTemplate(self.animationDOM, QgsReadWriteContext())  # @UnusedVariable
            ok = proj.layoutManager().addLayout(self.animationLayout)
            if not ok:
                QSWATUtils.error('Failed to add animation layout to layout manager.  Try removing some.', self._gv.isBatch)
                return
            designer = self._gv.iface.openLayoutDesigner(layout=self.animationLayout)  # @UnusedVariable
            self.animationTemplateDirty = True
                                           
    def rereadAnimationTemplate(self) -> None:
        """Reread animation template file."""
        self.animationTemplateDirty = False
        self.animationDOM = QDomDocument()
        f = QFile(self.animationTemplate)
        if f.open(QIODevice.ReadOnly):
            OK = self.animationDOM.setContent(f)[0]
            if not OK:
                QSWATUtils.error('Cannot parse template file {0}'.format(self.animationTemplate), self._gv.isBatch)
                return
        else:
            QSWATUtils.error('Cannot open template file {0}'.format(self.animationTemplate), self._gv.isBatch) 
            return
        
    def setDateInTemplate(self) -> None:
        """Set current animation date in title field."""
        assert self.animationDOM is not None
        itms = self.animationDOM.elementsByTagName('LayoutItem')
        for i in range(itms.length()):
            itm = itms.item(i)
            attr = itm.attributes().namedItem('id').toAttr()
            if attr is not None and attr.value() == 'Date':
                title = itm.attributes().namedItem('labelText').toAttr()
                if title is None:
                    QSWATUtils.error('Cannot find template date label', self._gv.isBatch)
                    return
                title.setValue(self._dlg.dateLabel.text())
                return
        QSWATUtils.error('Cannot find template date label', self._gv.isBatch)
        return

#     def setDateInComposer(self):
#         """Set current animation date in title field."""
#         labels = self.animationDOM.elementsByTagName('ComposerLabel')
#         for i in range(labels.length()):
#             label = labels.item(i)
#             item = label.namedItem('ComposerItem')
#             attr = item.attributes().namedItem('id').toAttr()
#             if attr is not None and attr.value() == 'Date':
#                 title = label.attributes().namedItem('labelText').toAttr()
#                 if title is None:
#                     QSWATUtils.error('Cannot find composer date label', self._gv.isBatch)
#                     return
#                 title.setValue(self._dlg.dateLabel.text())
#                 return
#         QSWATUtils.error('Cannot find composer date label', self._gv.isBatch)
#         return
        
    def changeAnimate(self) -> None:
        """
        Display animation data for current slider value.
        
        Get date from slider value; read animation data for date; write to animation file; redisplay.
        """
        try:
            if self._dlg.animationVariableCombo.currentText() == '':
                QSWATUtils.information('Please choose an animation variable', self._gv.isBatch)
                self.doRewind()
                return
            if self.capturing:
                self.capture()
            dat = self.sliderValToDate()
            date = self.dateToString(dat)
            self._dlg.dateLabel.setText(date)
            if self._dlg.canvasAnimation.isChecked():
                animateLayers = [self.animateLayer]
            else:
                root = QgsProject.instance().layerTreeRoot()
                animateTreeLayers = QSWATUtils.getLayersInGroup(QSWATUtils._ANIMATION_GROUP_NAME, root, visible=False)
                animateLayers = [layer.layer() for layer in animateTreeLayers if layer is not None]
            for animateLayer in animateLayers:
                if animateLayer is None:
                    continue
                layerId = animateLayer.id()
                self.resultsData = cast(Dict[str, Dict[int, Dict[int, float]]], self.resultsData)
                data = self.resultsData[layerId][dat]
                assert self.mapTitle is not None
                self.mapTitle.updateLine2(date)
                provider = animateLayer.dataProvider()
                path = provider.dataSourceUri()
                # vector data sources have additional "|layerid=0"
                pos = path.find('|')
                if pos >= 0:
                    path = path[:pos]
                fileName = os.path.split(path)[1]
                if fileName.startswith(Parameters._HRUS):
                    base = Parameters._HRUS
                    fieldName = QSWATTopology._HRUS
                elif fileName.startswith(Parameters._LSUS):
                    base = Parameters._LSUS
                    fieldName = QSWATTopology._LSUID
                elif fileName.startswith(Parameters._SUBS):
                    base = Parameters._SUBS
                    fieldName = QSWATTopology._SUBBASIN
                elif fileName.startswith(Parameters._RIVS):
                    base = Parameters._RIVS
                    fieldName = QSWATTopology._CHANNEL
                elif fileName.startswith(Parameters._AQUIFERS):
                    base = Parameters._AQUIFERS
                    fieldName = QSWATTopology._AQUIFER
                elif fileName.startswith(Parameters._DEEPAQUIFERS):
                    base = Parameters._DEEPAQUIFERS
                    fieldName = QSWATTopology._AQUIFER
                else:
                    return
                animateIndex = self.animateIndexes[layerId]
                unitIdx = provider.fieldNameIndex(fieldName)
                if unitIdx < 0:
                    QSWATUtils.error('Cannot find {0} field in {1}'.format(fieldName, path), self._gv.isBatch)
                    continue
                mmap = dict()
                for f in provider.getFeatures():
                    fid = f.id()
                    if base == Parameters._HRUS:
                        # May be split HRUs; just use first
                        # This is inadequate for some variables, but no way to know if correct val is sum of vals, mean, etc.
                        unitText = f[unitIdx]
                        if 'PND' in unitText:
                            continue
                        unit = int(unitText.split(',')[0])
                    else:
                        unit = f[unitIdx]
                    if unit in data:
                        val = data[unit]
                    else:
                        if base == Parameters._HRUS:
                            ref = 'HRU {0!s}'.format(unit)
                        elif base == Parameters._LSUS:
                            ref = 'LSU {0!s}'.format(unit)
                        elif base == Parameters._SUBS:
                            ref = 'subbasin {0!s}'.format(unit)
                        else:
                            ref = 'channel {0!s}'.format(unit)
                        QSWATUtils.error('Cannot get data for {0}: have you run SWAT+ and saved data since running QSWAT+?'.format(ref), self._gv.isBatch)
                        return
                    mmap[fid] = {animateIndex: float(val) if isinstance(val, numpy.float64) else val}
                if not provider.changeAttributeValues(mmap):
                    source = animateLayer.publicSource()
                    QSWATUtils.error('Could not set attribute {0} in animation file {1}'.format(self.animateVar, source), self._gv.isBatch)
                    self.animating = False
                    return
                animateLayer.triggerRepaint()
            self._dlg.dateLabel.repaint()
        except Exception:
            self.animating = False
            raise
        
    def capture(self) -> None:
        """Make image file of current canvas."""
        if self.animateLayer is None:
            return
        self.animateLayer.triggerRepaint()
        canvas = self._gv.iface.mapCanvas()
        canvas.refresh()
        self.currentStillNumber += 1
        base, suffix = os.path.splitext(self.stillFileBase)
        nextStillFile = base + '{0:05d}'.format(self.currentStillNumber) + suffix
        # this does not capture the title
        #self._gv.iface.mapCanvas().saveAsImage(nextStillFile)
        composingAnimation = self._dlg.printAnimation.isChecked()
        if composingAnimation:
            proj = QgsProject.instance()
            # remove layout if any
            try:
                assert self.animationLayout is not None
                proj.layoutManager().removeLayout(self.animationLayout)
            except:
                pass
            # clean up old layout
            self.animationLayout = None
            if self.animationTemplateDirty:
                self.rereadAnimationTemplate()
            title = 'Animation {0}'.format(self.compositionCount)
            self.compositionCount += 1
            self.animationLayout = QgsPrintLayout(proj)
            self.animationLayout.initializeDefaults()
            self.animationLayout.setName(title)
            self.setDateInTemplate()
            assert self.animationDOM is not None
            _ = self.animationLayout.loadFromTemplate(self.animationDOM, QgsReadWriteContext())
            ok = proj.layoutManager().addLayout(self.animationLayout)
            if not ok:
                QSWATUtils.error('Failed to add animation layout to layout manager.  Try removing some.', self._gv.isBatch)
                return
            exporter = QgsLayoutExporter(self.animationLayout)
            settings = QgsLayoutExporter.ImageExportSettings()
            settings.exportMetadata = False
            res = exporter.exportToImage(nextStillFile,  settings)
            if res != QgsLayoutExporter.Success:
                QSWATUtils.error('Failed with result {1} to save layout as image file {0}'.format(nextStillFile, res), self._gv.isBatch)
        else:
            # tempting bot omits canvas title
            # but on Mac the alternative grabs the whole screen
            if Parameters._ISMAC:
                canvas.saveAsImage(nextStillFile)
            else:
                canvasId = canvas.winId()
                screen = QGuiApplication.primaryScreen()
                pixMap = screen.grabWindow(canvasId)
                pixMap.save(nextStillFile)
        
        # no longer used
    #===========================================================================
    # def minMax(self, layer, var):
    #     """
    #     Return minimum and maximum of values for var in layer.
    #     
    #     Subbasin values of 0 indicate subbasins upstream from inlets and are ignored.
    #     """
    #     minv = float('inf')
    #     maxv = 0
    #     for f in layer.getFeatures():
    #         sub = f.attribute(QSWATTopology._SUBBASIN)
    #         if sub == 0:
    #             continue
    #         val = f.attribute(var)
    #         minv = min(minv, val)
    #         maxv = max(maxv, val)
    #     # increase/decrease by 1% to ensure no rounding errors cause values to be outside all ranges
    #     maxv *= 1.01
    #     minv *= 0.99
    #     return minv, maxv
    #===========================================================================
    
    # no longer used
    #===========================================================================
    # def dataList(self, var):
    #     """Make list of data values for var from resultsData for creating Jenks breaks."""
    #     res = []
    #     for subvals in self.resultsData.values():
    #         res.append(subvals[var])
    #     return res
    #===========================================================================
    
    def makeSymbologyForRange(self, minv: float, maxv: float, colour: QColor, precision: float) -> QgsRendererRange:
        """Create a range from minv to maxv with the colour."""
        base = self.selectBase()
        if base == Parameters._RIVS:
            props = {'width_expression': QSWATTopology._PENWIDTH}
            symbol: QgsSymbol = QgsLineSymbol.createSimple(props)
            cast(QgsLineSymbol, symbol).setWidth(1.0)
        else:
            symbol = QgsFillSymbol()
        symbol.setColor(colour)
        if precision >= 0:
            strng = '{0:.' + str(precision) + 'F} - {1:.' + str(precision) + 'F}'
            # minv and maxv came from numpy: make them normal floats
            title = strng.format(float(minv), float(maxv))
        else:
            factor = int(10 ** abs(precision))
            minv1 = int(minv / factor + 0.5) * factor
            maxv1 = int(maxv / factor + 0.5) * factor
            title = '{0} - {1}'.format(minv1, maxv1)
        rng = QgsRendererRange(minv, maxv, symbol, title)
        return rng
    
    def chooseColorRamp(self, table: str, var: str) -> QgsColorRamp:
        """Select a colour ramp."""
        chaWater = ['flo_in', 'flo_out', 'evap', 'tloss', 'aqu_in', 'peakr']
        aqWater = ['flo', 'stor', 'rchrg', 'seep', 'revap' 'flo_cha', 'flo_res', 'flo_ls']
        wbWater = ['snowmlt', 'sq_gen', 'latq', 'wtryld', 'perc', 'tloss', 'sq_cont', 'sw', 
                   'qtile', 'irr', 'sq_run', 'lq_run', 'ovbank', 'surqcha', 'surqres', 
                   'surq_ls', 'latq_cha', 'latq_res', 'latq_ls']
        wbPrecip = ['prec', 'snow', 'et', 'eplant', 'esoil', 'pet']
        style = QgsStyle().defaultStyle()
        if table.startswith('channel') and var not in chaWater or \
            (table.startswith('aquifer') or table.startswith('deep_aquifer')) and var not in aqWater or \
            '_ls_' in table or \
            '_nb_' in table or \
            '_wb_' in table and var not in wbWater and var not in wbPrecip:
            # sediments and pollutants
            ramp = style.colorRamp('RdYlGn').clone()
            ramp.invert()
            return ramp
        elif table.startswith('channel') and var in chaWater or \
            (table.startswith('aquifer') or table.startswith('deep_aquifer')) and var in aqWater or \
            '_wb_' in table and var in wbWater:
            # water
            return style.colorRamp('YlGnBu')
        elif '_wb_' in table and var in wbPrecip:
            # precipitation and transpiration:
            return style.colorRamp('GnBu')
        else:
            return style.colorRamp('YlOrRd')
        
    def modeChange(self) -> None:
        """Main tab has changed.  Show/hide Animation group.  Repopulate output tables."""
        root = QgsProject.instance().layerTreeRoot()
        expandAnimation = self._dlg.tabWidget.currentIndex() == 1
        animationGroup = root.findGroup(QSWATUtils._ANIMATION_GROUP_NAME)
        assert animationGroup is not None
        animationGroup.setItemVisibilityCheckedRecursive(expandAnimation)
        # model = QgsLayerTreeModel(root)
        # view = self._gv.iface.layerTreeView()
        # TODO: how to link model and view so as to be able to expand the animation group? 
        # tables available can depend on tab, so repopulate
        currentTable = self._dlg.outputCombo.currentText()
        self.populateOutputTables()
        if currentTable != '':
            self._dlg.outputCombo.setCurrentText(currentTable)
            self.setVariables()
            
    def makeResults(self) -> None:
        """
        Create a results file and display.
        
        Only creates a new file if the variables have changed.
        If variables unchanged, only makes and writes summary data if necessary.
        """
        if self.table == '':
            QSWATUtils.information('Please choose a SWAT output table', self._gv.isBatch)
            return
        if self._dlg.resultsFileEdit.text() == '':
            QSWATUtils.information('Please choose a results file', self._gv.isBatch)
            return
        if self._dlg.variableList.count() == 0:
            QSWATUtils.information('Please choose some variables', self._gv.isBatch)
            return
        if len(self._dlg.variableList.selectedItems()) == 0:
            QSWATUtils.information('Please select a variable for display', self._gv.isBatch)
            return
        if not self.setPeriods():
            return
        self._dlg.setCursor(Qt.WaitCursor)
        self.resultsFileUpToDate = self.resultsFileUpToDate and self.resultsFile == self._dlg.resultsFileEdit.text()
        if not self.resultsFileUpToDate or not self.periodsUpToDate:
            if not self.readData('', True, self.table, '', ''):
                return
            self.periodsUpToDate = True
        if self.summaryChanged:
            self.summariseData('', True)
        if self.resultsFileUpToDate and self.resultsLayerExists():
            if self.summaryChanged:
                self.updateResultsFile()
        else:
            if self.createResultsFile():
                self.resultsFileUpToDate = True
            else:
                return
        self.colourResultsFile()
        self._dlg.setCursor(Qt.ArrowCursor)
        
    def printResults(self) -> None:
        """Create print composer by instantiating template file."""
        proj = QgsProject.instance()
        root = proj.layerTreeRoot()
        resultsLayers = QSWATUtils.getLayersInGroup(QSWATUtils._RESULTS_GROUP_NAME, root)
        watershedLayers = QSWATUtils.getLayersInGroup(QSWATUtils._WATERSHED_GROUP_NAME, root, visible=True)
        # choose template file and set its width and height
        # width and height here need to be updated if template file is changed
        count = self._dlg.printCount.value()
        if count == 1:
            if self._dlg.landscapeButton.isChecked():
                templ = '1Landscape.qpt'
                width = 230.0
                height = 160.0
            else:
                templ = '1Portrait.qpt'
                width = 190.0
                height = 200.0
        elif count == 2:
            if self._dlg.landscapeButton.isChecked():
                templ = '2Landscape.qpt'
                width = 125.0
                height = 120.0
            else:
                templ = '2Portrait.qpt'
                width = 150.0
                height = 120.0
        elif count == 3:
            if self._dlg.landscapeButton.isChecked():
                templ = '3Landscape.qpt'
                width = 90.0
                height = 110.0
            else:
                templ = '3Portrait.qpt'
                width = 150.0
                height = 80.0
        elif count == 4:
            if self._dlg.landscapeButton.isChecked():
                templ = '4Landscape.qpt'
                width = 95.0
                height = 80.0
            else:
                templ = '4Portrait.qpt'
                width = 85.0
                height = 85.0
        elif count == 6:
            if self._dlg.landscapeButton.isChecked():
                templ = '6Landscape.qpt'
                width = 90.0
                height = 40.0
            else:
                templ = '6Portrait.qpt'
                width = 55.0
                height = 80.0
        else:
            QSWATUtils.error('There are composition templates only for 1, 2, 3, 4 or 6 result maps, not for {0}'.format(count), self._gv.isBatch)
            return
        templateIn = QSWATUtils.join(self._gv.plugin_dir, 'PrintTemplate' + templ)
        templateOut = QSWATUtils.join(self._gv.resultsDir, self.title + templ)
        # make substitution table
        subs = dict()
        northArrow = self.findNorthArrow()
        if not os.path.isfile(northArrow):
            QSWATUtils.error('Failed to find north arrow {0}.  You will need to repair the layout.'.format(northArrow), self._gv.isBatch)
        subs['%%NorthArrow%%'] = northArrow
        subs['%%ProjectName%%'] = self.title
        numLayers = len(resultsLayers)
        if count > numLayers:
            QSWATUtils.error(u'You want to make a print of {0} maps, but you only have {1} results layers'.format(count, numLayers), self._gv.isBatch)
            return
        extent = self._gv.iface.mapCanvas().extent()
        xmax = extent.xMaximum()
        xmin = extent.xMinimum()
        ymin = extent.yMinimum()
        ymax = extent.yMaximum()
        QSWATUtils.loginfo('Map canvas extent {0}, {1}, {2}, {3}'.format(str(int(xmin + 0.5)), str(int(ymin + 0.5)), 
                                                                         str(int(xmax + 0.5)), str(int(ymax + 0.5))))
        # need to expand either x or y extent to fit map shape
        xdiff = ((ymax - ymin) / height) * width - (xmax - xmin)
        if xdiff > 0:
            # need to expand x extent
            xmin = xmin - xdiff / 2
            xmax = xmax + xdiff / 2
        else:
            # expand y extent
            ydiff = (((xmax - xmin) / width) * height) - (ymax - ymin)
            ymin = ymin - ydiff / 2
            ymax = ymax + ydiff / 2
        QSWATUtils.loginfo('Map extent set to {0}, {1}, {2}, {3}'.format(str(int(xmin + 0.5)), str(int(ymin + 0.5)), 
                                                                         str(int(xmax + 0.5)), str(int(ymax + 0.5))))
        # estimate of segment size for scale
        # aim is approx 10mm for 1 segment
        # we make size a power of 10 so that segments are 1km, or 10, or 100, etc.
        segSize = 10 ** int(math.log10((xmax - xmin) / (width / 10)) + 0.5)
        layerStr = '<Layer source="{0}" provider="ogr" name="{1}">{2}</Layer>'
        for i in range(count):
            layer = resultsLayers[i].layer()
            subs['%%LayerId{0}%%'.format(i)] = layer.id()
            subs['%%LayerName{0}%%'.format(i)] = layer.name()
            subs['%%YMin{0}%%'.format(i)] = str(ymin)
            subs['%%XMin{0}%%'.format(i)] = str(xmin)
            subs['%%YMax{0}%%'.format(i)] = str(ymax)
            subs['%%XMax{0}%%'.format(i)] = str(xmax)
            subs['%%ScaleSegSize%%'] = str(segSize)
            subs['%%Layer{0}%%'.format(i)] = layerStr.format(QSWATUtils.layerFilename(layer), layer.name(), layer.id())
        for i in range(6):  # 6 entries in template for background layers
            if i < len(watershedLayers):
                wLayer = watershedLayers[i].layer()
                subs['%%WshedLayer{0}%%'.format(i)] = layerStr.format(QSWATUtils.layerFilename(wLayer), wLayer.name(), wLayer.id())
            else:  # remove unused ones
                subs['%%WshedLayer{0}%%'.format(i)] = ''
        # seems to do no harm to leave unused <Layer> items with original pattern, so we don't bother removing them
        with open(templateIn, 'rU') as inFile:
            with open(templateOut, 'w') as outFile:
                for line in inFile:
                    outFile.write(Visualise.replaceInLine(line, subs))
        QSWATUtils.loginfo('Print composer template {0} written'.format(templateOut))
        templateDoc = QDomDocument()
        f = QFile(templateOut)
        if f.open(QIODevice.ReadOnly):
            OK = templateDoc.setContent(f)[0]
            if not OK:
                QSWATUtils.error('Cannot parse template file {0}'.format(templateOut), self._gv.isBatch)
                return
        else:
            QSWATUtils.error('Cannot open template file {0}'.format(templateOut), self._gv.isBatch) 
            return 
        title = '{0}{1} {2}'.format(self.title, templ, str(self.compositionCount))
        self.compositionCount += 1
        layout = QgsPrintLayout(proj)
        layout.initializeDefaults()
        layout.setName(title)
        items = layout.loadFromTemplate(templateDoc, QgsReadWriteContext())  # @UnusedVariable
        ok = proj.layoutManager().addLayout(layout)
        if not ok:
            QSWATUtils.error('Failed to add layout to layout manager.  Try removing some.', self._gv.isBatch)
            return
        designer = self._gv.iface.openLayoutDesigner(layout=layout)  # @UnusedVariable
        # if you quit from layout manager and then try to make another layout, 
        # the pointer gets reused and there is a 'destroyed by C==' error
        # This prevents the reuse.
        layout = None  # type: ignore
        
    def findNorthArrow(self) -> str:
        """Find and return northarrow svg file."""
        northArrow = ''  # for mypy
        if Parameters._ISWIN:
            northArrow = QSWATUtils.join(os.getenv('OSGEO4W_ROOT'), QSWATUtils.join(Parameters._SVGDIR, Visualise._NORTHARROW))
            if not os.path.isfile(northArrow):
                # may be qgis-ltr for example
                svgDir = Parameters._SVGDIR[:].replace('qgis', QSWATUtils.qgisName(), 1)
                northArrow = QSWATUtils.join(os.getenv('OSGEO4W_ROOT'), QSWATUtils.join(svgDir, Visualise._NORTHARROW))
        else:  # Linux and Mac
            northArrow = QSWATUtils.join(Parameters._SVGDIR, Visualise._NORTHARROW)
        return northArrow
        
    @staticmethod
    def replaceInLine(inLine: str, table: Dict[str, str]) -> str:
        """Use table of replacements to replace keys with items in returned line."""
        for patt, sub in table.items():
            inLine = inLine.replace(patt, sub)
        return inLine
    
    def changeAnimationMode(self) -> None:
        """Reveal or hide compose options group."""
        if self._dlg.printAnimation.isChecked():
            self._dlg.composeOptions.setVisible(True)
            root = QgsProject.instance().layerTreeRoot()
            self._dlg.composeCount.setValue(QSWATUtils.countLayersInGroup(QSWATUtils._ANIMATION_GROUP_NAME, root))
        else:
            self._dlg.composeOptions.setVisible(False)
               
    def setupAnimateLayer(self) -> None:
        """
        Set up for animation.
        
        Collect animation data from database table according to animation variable; 
        set slider minimum and maximum;
        create animation layer;
        set speed accoring to spin box;
        set slider at minimum and display data for start time.
        """
        var = self._dlg.animationVariableCombo.currentText()
        if var == '':
            self._dlg.animationVariableCombo.setToolTip('Select variable for animation')
            return
        self._dlg.animationVariableCombo.setToolTip(self.getVarTip(var))
        # can take a while so set a wait cursor
        self._dlg.setCursor(Qt.WaitCursor)
        self.doRewind()
        self._dlg.calculateLabel.setText('Calculating breaks ...')
        self._dlg.repaint()
        try:
            if not self.setPeriods():
                return
            self.animateVar = var
            if not self.createAnimationLayer():
                return
            assert self.animateLayer is not None
            lid = self.animateLayer.id()
            if not self.readData(lid, False, self.table, self.animateVar, ''):
                return
            self.summariseData(lid, False)
            if self.isDaily:
                animateLength = self.periodDays
            elif self.isAnnual:
                animateLength = int(self.periodYears + 0.5)
            elif self.isMonthly:
                animateLength = int(self.periodMonths + 0.5)
            else:
                animateLength = 0
            self._dlg.slider.setMinimum(1)
            self._dlg.slider.setMaximum(animateLength)
            self.colourAnimationLayer()
            self._dlg.slider.setValue(1)
            sleep = self._dlg.spinBox.value()
            self.changeSpeed(sleep)
            self.resetSlider()
            self.changeAnimate()
        finally:
            self._dlg.calculateLabel.setText('')
            self._dlg.setCursor(Qt.ArrowCursor)
            
    def saveVideo(self) -> None:
        """Save animated GIF if still files found."""
        # capture final frame
        self.capture()
        # remove animation layout
        try:
            assert self.animationLayout is not None
            QgsProject.instance().layoutManager().removeLayout(self.animationLayout)
        except:
            pass
        fileNames = sorted((fn for fn in os.listdir(self._gv.pngDir) if fn.endswith('.png')))
        if fileNames == []:
            return
        if self._dlg.printAnimation.isChecked():
            base = QSWATUtils.join(self._gv.resultsDir, 'Video.gif')
            self.videoFile = QSWATUtils.nextFileName(base, 0)[0]
        else:
            resultsDir = os.path.split(self.db)[0]
            self.videoFile = QSWATUtils.join(resultsDir, self.animateVar + 'Video.gif')
        try:
            os.remove(self.videoFile)
        except Exception:
            pass
        period = 1.0 / self._dlg.spinBox.value()
        try:
            with imageio.get_writer('file://' + self.videoFile, mode='I', loop=1, duration=period) as writer:  # type: ignore
                for filename in fileNames:
                    image = imageio.imread(QSWATUtils.join(self._gv.pngDir, filename))  # type: ignore
                    writer.append_data(image)
            # clear the png files:
            self.clearPngDir()
            QSWATUtils.information('Animated gif {0} written'.format(self.videoFile), self._gv.isBatch)
        except Exception:
            self.videoFile = ''
            QSWATUtils.error("""
            Failed to generate animated gif: {0}.
            The .png files are in {1}: suggest you try using GIMP.
            """.format(traceback.format_exc(), self._gv.pngDir), self._gv.isBatch)
        
    def doPlay(self) -> None:
        """Set animating and not pause."""
        if self._dlg.animationVariableCombo.currentText() == '':
            QSWATUtils.information('Please choose an animation variable', self._gv.isBatch)
            return
        self.animating = True
        self.animationPaused = False
        
    def doPause(self) -> None:
        """If animating change pause from on to off, or off to on."""
        if self.animating:
            self.animationPaused = not self.animationPaused
            
    def doRewind(self) -> None:
        """Turn off animating and pause and set slider to minimum."""
        self.animating = False
        self.animationPaused = False
        self.resetSlider()
        
    def doStep(self) -> None:
        """Move slide one step to right unless at maximum."""
        if self.animating and not self.animationPaused:
            val = self._dlg.slider.value()
            if val < self._dlg.slider.maximum():
                self._dlg.slider.setValue(val + 1)
                
    def animateStepLeft(self) -> None:
        """Stop any running animation and if possible move the animation slider one step left."""
        if self._dlg.tabWidget.currentIndex() == 1:
            self.animating = False
            self.animationPaused = False
            val = self._dlg.slider.value()
            if val > self._dlg.slider.minimum():
                self._dlg.slider.setValue(val - 1)
                
    def animateStepRight(self) -> None:
        """Stop any running animation and if possible move the animation slider one step right."""
        if self._dlg.tabWidget.currentIndex() == 1:
            self.animating = False
            self.animationPaused = False
            val = self._dlg.slider.value()
            if val < self._dlg.slider.maximum():
                self._dlg.slider.setValue(val + 1)
    
    def changeSpeed(self, val: int) -> None:
        """
        Starts or restarts the timer with speed set to val.
        
        Runs in a try ... except so that timer gets stopped if any exception.
        """
        try:
            self.animateTimer.start(1000 // val)
        except Exception:
            self.animating = False
            self.animateTimer.stop()
            # raise last exception again
            raise
           
    def pressSlider(self) -> None:
        """Turn off animating and pause."""
        self.animating = False
        self.animationPaused = False
        
    def resetSlider(self) -> None:
        """Move slide to minimum."""
        self._dlg.slider.setValue(self._dlg.slider.minimum())
        
    def sliderValToDate(self) -> int:
        """Convert slider value to date."""
        if self.isDaily:
            return self.addDays(self.julianStartDay + self._dlg.slider.value() - 1,  self.startYear)
        elif self.isAnnual:
            return  self.startYear + cast(int, self._dlg.slider.value()) - 1
        elif self.isMonthly:
            totalMonths =  self.startMonth + cast(int, self._dlg.slider.value()) - 2
            year = totalMonths // 12
            month = totalMonths % 12 + 1
            return (self.startYear + year) * 100 + month
        else:
            return self.startYear
            
    def addDays(self, days: int, year: int) -> int:
        """Make Julian date from year + days."""
        leapAdjust = 1 if self.isLeap(year) else 0
        lenYear = 365 + leapAdjust
        if days <= lenYear:
            return (year) * 1000 + days
        else:
            return self.addDays(days - lenYear, year + 1)
            
    def julianToDate(self, day: int, year: int) -> date:
        """
        Return datetime.date from year and number of days.
        
        The day may exceed the length of year, in which case a later year
        will be returned.
        """
        if day <= 31:
            return date(year, 1, day)
        day -= 31
        leapAdjust = 1 if self.isLeap(year) else 0
        if day <= 28 + leapAdjust:
            return date(year, 2, day)
        day -= 28 + leapAdjust
        if day <= 31:
            return date(year, 3, day)
        day -= 31
        if day <= 30:
            return date(year, 4, day)
        day -= 30
        if day <= 31:
            return date(year, 5, day)
        day -= 31
        if day <= 30:
            return date(year, 6, day)
        day -= 30
        if day <= 31:
            return date(year, 7, day)
        day -= 31
        if day <= 31:
            return date(year, 8, day)
        day -= 31
        if day <= 30:
            return date(year, 9, day)
        day -= 30
        if day <= 31:
            return date(year, 10, day)
        day -= 31
        if day <= 30:
            return date(year, 11, day)
        day -= 30
        if day <= 31:
            return date(year, 12, day)
        else:
            return self.julianToDate(day - 31, year + 1)
        
    def dateToString(self, dat: int) -> str:
        """Convert integer date to string."""
        if self.isDaily:
            return self.julianToDate(dat%1000, dat//1000).strftime(QSWATUtils._DATEFORMAT)
        if self.isMonthly:
            return date(dat//100, dat%100, 1).strftime("%B %Y")
        # annual or average annual
        return str(dat)

    def record(self) -> None:
        """Switch between recording and not."""
        self.capturing = not self.capturing
        if self.capturing:
            # clear any existing png files (can be left eg if making gif failed)
            self.clearPngDir()
            if self._dlg.printAnimation.isChecked():
                self.createAnimationComposition()
            self._dlg.recordButton.setStyleSheet('background-color: red; border: none;')
            self._dlg.recordLabel.setText('Stop recording')
            self._dlg.playButton.setEnabled(False)
        else:
            self._dlg.setCursor(Qt.WaitCursor)
            self._dlg.recordButton.setStyleSheet('background-color: green; border: none;')
            self._dlg.recordLabel.setText('Start recording')
            self.saveVideo()
            self._dlg.playButton.setEnabled(True)
            self._dlg.setCursor(Qt.ArrowCursor)
    
    def playRecording(self) -> None:
        """Use default application to play video file (an animated gif)."""
        # stop recording if necessary
        if self.capturing:
            self.record()
        if not os.path.exists(self.videoFile):
            QSWATUtils.information('No video file for {0} exists at present'.format(self.animateVar), self._gv.isBatch)
            return
        if Parameters._ISWIN: # Windows
            os.startfile(self.videoFile)  # @UndefinedVariable since not defined in Linux
        elif Parameters._ISLINUX:
            subprocess.call(('xdg-open', self.videoFile))
        else:
            # default on Mac is Preview which shows all pngs as thumbnails and does not animate
            # so use Safari
            import webbrowser
            w = webbrowser.get('safari')
            w.open('file://{0}'.format(self.videoFile))
    
    def changeSummary(self) -> None:
        """Flag change to summary method."""
        self.summaryChanged = True
        
    def changeAquRenderer(self) -> None:
        """If user changes the aquifer renderer, flag to retain colour scheme."""
        if not self.internalChangeToAquRenderer:
            self.keepAquColours = True
        
    def changeDeepAquRenderer(self) -> None:
        """If user changes the deep aquifer renderer, flag to retain colour scheme."""
        if not self.internalChangeToDeepAquRenderer:
            self.keepDeepAquColours = True
        
    def changeRivRenderer(self) -> None:
        """If user changes the stream renderer, flag to retain colour scheme."""
        if not self.internalChangeToRivRenderer:
            self.keepRivColours = True
        
    def changeSubRenderer(self) -> None:
        """If user changes the subbasin renderer, flag to retain colour scheme."""
        if not self.internalChangeToSubRenderer:
            self.keepSubColours = True
        
    def changeLSURenderer(self) -> None:
        """If user changes the LSU renderer, flag to retain colour scheme."""
        if not self.internalChangeToLSURenderer:
            self.keepLSUColours = True
        
    def changeHRURenderer(self) -> None:
        """If user changes the HRU renderer, flag to retain colour scheme."""
        if not self.internalChangeToHRURenderer:
            self.keepHRUColours = True
            
    def updateCurrentPlotRow(self, colChanged: int) -> None:
        """
        Update current plot row according to the colChanged index.
        
        If there are no rows, first makes one.
        """
        if not self.plotting():
            return
        indexes = self._dlg.tableWidget.selectedIndexes()
        if not indexes or indexes == []:
            self.doAddPlot()
            indexes = self._dlg.tableWidget.selectedIndexes()
        row = indexes[0].row()
        if colChanged == 0:
            self._dlg.tableWidget.item(row, 0).setText(self.scenario)
        elif colChanged == 1:
            if self._dlg.tableWidget.item(row, 1).text() == '-':
                # observed plot: do not change
                return
            self._dlg.tableWidget.item(row, 1).setText(self.table)
            self._dlg.unitLabel.setText(self.tableUnitName(self.table))
            self._dlg.tableWidget.item(row, 2).setText('')
            self._dlg.tableWidget.item(row, 3).setText('')
        elif colChanged == 2:
            self._dlg.tableWidget.item(row, 2).setText(self._dlg.unitPlot.currentText())
        else:
            self._dlg.tableWidget.item(row, 3).setText(self._dlg.variablePlot.currentText())
            
    _unitNames = {'basin_': 'Basin',
                  'lsunit_': 'LSU',
                  'hru_': 'HRU',
                  'region_': 'Region',
                  'channel_sd_': 'Channel_SD',
                  'channel_sdmorph_': 'Channel_SDMorph',
                  #'_sd': 'HRU-LTE',
                  'channel_': 'Channel',
                  'aquifer_': 'Aquifer',
                  'deep_aquifer_': 'Deep aquifer',
                  'reservoir_': 'Reservoir',
                  'wetland_': 'Wetland',
                  'hydin_': 'Hydrograph in',
                  'hydout_': 'Hydrograph out',
                  'ru_': 'Routing unit'}
            
    def tableUnitName(self, table: str) -> str:
        """Return name for table unit."""
        for key, uname in self._unitNames.items():
            if key in table:
                return uname 
        return 'Unknown'
    
    def countPlots(self) -> int:
        """Return number of non-observed plots."""
        size = self._dlg.tableWidget.rowCount()
        result = cast(int, size)
        for row in range(size):
            if self._dlg.tableWidget.item(row, 1).text() == '-':
                # observed row
                result -= 1
        return result
            
    def doAddPlot(self) -> None:
        """Add a plot row and make it current."""
        unit = self._dlg.unitPlot.currentText()
        size = self._dlg.tableWidget.rowCount()
        if size > 0 and self._dlg.tableWidget.item(size-1, 1).text() == '-':
            # last plot was observed: need to reset variables
            self.setVariables()
        var = self._dlg.variablePlot.currentText()
        self._dlg.tableWidget.insertRow(size)
        self._dlg.tableWidget.setItem(size, 0, QTableWidgetItem(self.scenario))
        self._dlg.tableWidget.setItem(size, 1, QTableWidgetItem(self.table))
        self._dlg.tableWidget.setItem(size, 2, QTableWidgetItem(unit))
        self._dlg.tableWidget.setItem(size, 3, QTableWidgetItem(var))
        for col in range(4):
            self._dlg.tableWidget.item(size, col).setTextAlignment(Qt.AlignCenter)
        self._dlg.tableWidget.selectRow(size)
        if self.countPlots() == 1:
            # just added first row - reduce tables to those with same frequency
            if Visualise.tableIsDaily(self.table):
                self.restrictOutputTablesByTerminator('_day')
            elif Visualise.tableIsMonthly(self.table):
                self.restrictOutputTablesByTerminator('_mon')
            elif Visualise.tableIsAnnual(self.table):
                self.restrictOutputTablesByTerminator('_yr')
                
    def getPlotTable(self) -> str:
        """Return the table of a non-observed plot, or empty string if none."""
        for row in range(self._dlg.tableWidget.rowCount()):
            table = cast(str, self._dlg.tableWidget.item(row, 1).text())
            if table == '-':  # observed
                continue
            else:
                return table
        return ''
        
    def doDelPlot(self) -> None:
        """Delete current plot row."""
        indexes = self._dlg.tableWidget.selectedIndexes()
        if not indexes or indexes == []:
            QSWATUtils.information('Please select a row for deletion', self._gv.isBatch)
            return
        row = indexes[0].row()
        if row in range(self._dlg.tableWidget.rowCount()):
            self._dlg.tableWidget.removeRow(row)
        if self.countPlots() == 0:
            # no non-observed plots - restore output tables combo so any frequency can be chosen
            self.populateOutputTables()
        
    def doCopyPlot(self) -> None:
        """Add a copy of the current plot row and make it current."""
        indexes = self._dlg.tableWidget.selectedIndexes()
        if not indexes or indexes == []:
            QSWATUtils.information('Please select a row to copy', self._gv.isBatch)
            return
        row = indexes[0].row()
        size = self._dlg.tableWidget.rowCount()
        if row in range(size):
            self._dlg.tableWidget.insertRow(size)
            for col in range(4):
                self._dlg.tableWidget.setItem(size, col, QTableWidgetItem(self._dlg.tableWidget.item(row, col)))
        self._dlg.tableWidget.selectRow(size)
        
    def doUpPlot(self) -> None:
        """Move current plot row up 1 place and keep it current."""
        indexes = self._dlg.tableWidget.selectedIndexes()
        if not indexes or indexes == []:
            QSWATUtils.information('Please select a row to move up', self._gv.isBatch)
            return
        row = indexes[0].row()
        if 1 <= row < self._dlg.tableWidget.rowCount():
            for col in range(4):
                item = self._dlg.tableWidget.takeItem(row, col)
                self._dlg.tableWidget.setItem(row, col, self._dlg.tableWidget.takeItem(row-1, col))
                self._dlg.tableWidget.setItem(row-1, col, item)
        self._dlg.tableWidget.selectRow(row-1)
                
    def doDownPlot(self) -> None:
        """Move current plot row down 1 place and keep it current."""
        indexes = self._dlg.tableWidget.selectedIndexes()
        if not indexes or indexes == []:
            QSWATUtils.information('Please select a row to move down', self._gv.isBatch)
            return
        row = indexes[0].row()
        if 0 <= row < self._dlg.tableWidget.rowCount() - 1:
            for col in range(4):
                item = self._dlg.tableWidget.takeItem(row, col)
                self._dlg.tableWidget.setItem(row, col, self._dlg.tableWidget.takeItem(row+1, col))
                self._dlg.tableWidget.setItem(row+1, col, item)
        self._dlg.tableWidget.selectRow(row+1)
        
    def addObervedPlot(self) -> None:
        """Add a row for an observed plot, and make it current."""
        if not os.path.exists(self.observedFileName):
            return
        self.setObservedVars()
        size = self._dlg.tableWidget.rowCount()
        self._dlg.tableWidget.insertRow(size)
        self._dlg.tableWidget.setItem(size, 0, QTableWidgetItem('observed'))
        self._dlg.tableWidget.setItem(size, 1, QTableWidgetItem('-'))
        self._dlg.tableWidget.setItem(size, 2, QTableWidgetItem('-'))
        self._dlg.tableWidget.setItem(size, 3, QTableWidgetItem(self._dlg.variablePlot.currentText()))
        for col in range(4):
            self._dlg.tableWidget.item(size, col).setTextAlignment(Qt.AlignHCenter)
        self._dlg.tableWidget.selectRow(size)
        
    def setObservedVars(self) -> None:
        """Add variables from 1st line of observed data file, ignoring 'date' if it occurs as the first column."""
        with open(self.observedFileName, 'r') as obs:
            line = obs.readline()
            varz = line.split(',')
            if len(varz) == 0:
                QSWATUtils.error('Cannot find variables in first line of observed data file {0}'.format(self.observedFileName), self._gv.isBatch)
                return
            col1 = varz[0].strip().lower()
            start = 1 if col1 == 'date' else 0
            self._dlg.variablePlot.clear()
            for var in varz[start:]:
                self._dlg.variablePlot.addItem(var.strip())
            
    def readObservedFile(self, var: str) -> List[str]:
        """
        Read data for var from observed data file, returning a list of data as strings.
        
        Note that dates are not checked even if present in the observed data file.
        """
        result: List[str] = []
        with open(self.observedFileName, 'r') as obs:
            line = obs.readline()
            varz = [var1.strip() for var1 in line.split(',')]
            if len(varz) == 0:
                QSWATUtils.error('Cannot find variables in first line of observed data file {0}'.format(self.observedFileName), self._gv.isBatch)
                return result
            try:
                idx = varz.index(var)
            except Exception:
                QSWATUtils.error('Cannot find variable {0} in first line of observed data file {1}'.format(var, self.observedFileName), self._gv.isBatch)
                return result
            while line:
                line = obs.readline()
                vals = line.split(',')
                if 0 <= idx < len(vals):
                    result.append(vals[idx].strip()) # strip any newline
                else:
                    break # finish if e.g. a blank line
        return result
        
        
    # code from http://danieljlewis.org/files/2010/06/Jenks.pdf
    # described at http://danieljlewis.org/2010/06/07/jenks-natural-breaks-algorithm-in-python/
    # amended following style of http://www.macwright.org/simple-statistics/docs/simple_statistics.html#section-116
 
    # no longer used - replaced by Cython
    #===========================================================================
    # @staticmethod
    # def getJenksBreaks( dataList, numClass ):
    #     """Return Jenks breaks for dataList with numClass classes."""
    #     if not dataList:
    #         return [], 0
    #     # Use of sample unfortunate because gives poor animation results.
    #     # Tends to overestimate lower limit and underestimate upper limit, and areas go white in animation.
    #     # But can take a long time to calculate!
    #     # QGIS internal code uses 1000 here but 4000 runs in reasonable time
    #     maxSize = 4000
    #     # use a sample if size exceeds maxSize
    #     size = len(dataList)
    #     if size > maxSize:
    #         origSize = size
    #         size = max(maxSize, size / 10)
    #         QSWATUtils.loginfo('Jenks breaks: using a sample of size {0!s} from {1!s}'.format(size, origSize))
    #         sample = random.sample(dataList, size)
    #     else:
    #         sample = dataList
    #     sample.sort()
    #     # at most one class: return singleton list
    #     if numClass <= 1:
    #         return [sample.last()]
    #     if numClass >= size:
    #         # nothing useful to do
    #         return sample
    #     lowerClassLimits = []
    #     varianceCombinations = []
    #     variance = 0
    #     for i in range(0,size+1):
    #         temp1 = []
    #         temp2 = []
    #         # initialize with lists of zeroes
    #         for j in range(0,numClass+1):
    #             temp1.append(0)
    #             temp2.append(0)
    #         lowerClassLimits.append(temp1)
    #         varianceCombinations.append(temp2)
    #     for i in range(1,numClass+1):
    #         lowerClassLimits[1][i] = 1
    #         varianceCombinations[1][i] = 0
    #         for j in range(2,size+1):
    #             varianceCombinations[j][i] = float('inf')
    #     for l in range(2,size+1):
    #         # sum of values seen so far
    #         summ = 0
    #         # sum of squares of values seen so far
    #         sumSquares = 0
    #         # for each potential number of classes. w is the number of data points considered so far
    #         w = 0
    #         i4 = 0
    #         for m in range(1,l+1):
    #             lowerClassLimit = l - m + 1
    #             val = float(sample[lowerClassLimit-1])
    #             w += 1
    #             summ += val
    #             sumSquares += val * val
    #             variance = sumSquares - (summ * summ) / w
    #             i4 = lowerClassLimit - 1
    #             if i4 != 0:
    #                 for j in range(2,numClass+1):
    #                     # if adding this element to an existing class will increase its variance beyond the limit, 
    #                     # break the class at this point, setting the lower_class_limit.
    #                     if varianceCombinations[l][j] >= (variance + varianceCombinations[i4][j - 1]):
    #                         lowerClassLimits[l][j] = lowerClassLimit
    #                         varianceCombinations[l][j] = variance + varianceCombinations[i4][j - 1]
    #         lowerClassLimits[l][1] = 1
    #         varianceCombinations[l][1] = variance
    #     k = size
    #     kclass = []
    #     for i in range(0,numClass+1):
    #         kclass.append(0)
    #     kclass[numClass] = float(sample[size - 1])
    #     countNum = numClass
    #     while countNum >= 2:#print "rank = " + str(lowerClassLimits[k][countNum])
    #         idx = int((lowerClassLimits[k][countNum]) - 2)
    #         #print "val = " + str(sample[idx])
    #         kclass[countNum - 1] = sample[idx]
    #         k = int((lowerClassLimits[k][countNum] - 1))
    #         countNum -= 1
    #     return kclass, sample[0]
    #===========================================================================
    
    # copied like above but not used
#===============================================================================
#     @staticmethod
#     def getGVF( sample, numClass ):
#         """
#         The Goodness of Variance Fit (GVF) is found by taking the
#         difference between the squared deviations
#         from the array mean (SDAM) and the squared deviations from the
#         class means (SDCM), and dividing by the SDAM
#         """
#         breaks = Visualise.getJenksBreaks(sample, numClass)
#         sample.sort()
#         size = len(sample)
#         listMean = sum(sample)/size
#         print listMean
#         SDAM = 0.0
#         for i in range(0,size):
#             sqDev = (sample[i] - listMean)**2
#             SDAM += sqDev
#         SDCM = 0.0
#         for i in range(0,numClass):
#             if breaks[i] == 0:
#                 classStart = 0
#             else:
#                 classStart = sample.index(breaks[i])
#             classStart += 1
#             classEnd = sample.index(breaks[i+1])
#             classList = sample[classStart:classEnd+1]
#         classMean = sum(classList)/len(classList)
#         print classMean
#         preSDCM = 0.0
#         for j in range(0,len(classList)):
#             sqDev2 = (classList[j] - classMean)**2
#             preSDCM += sqDev2
#             SDCM += preSDCM
#         return (SDAM - SDCM)/SDAM
# 
#     # written by Drew
#     # used after running getJenksBreaks()
#     @staticmethod
#     def classify(value, breaks):
#         """
#         Return index of value in breaks.
#         
#         Returns i such that
#         breaks = [] and i = -1, or
#         value < breaks[1] and i = 1, or 
#         breaks[i-1] <= value < break[i], or
#         value >= breaks[len(breaks) - 1] and i = len(breaks) - 1
#         """
#         for i in range(1, len(breaks)):
#             if value < breaks[i]:
#                 return i
#         return len(breaks) - 1 
#===============================================================================

    def clearMapTitle(self) -> None:
        """Can often end up with more than one map title.  Remove all of them from the canvas, prior to resetting one required."""
        canvas = self._gv.iface.mapCanvas()
        scene = canvas.scene()
        if self.mapTitle is not None:
            scene.removeItem(self.mapTitle)
            self.mapTitle = None
            # scene.items() causes a crash for some users.
            # this code seems unnecessary in any case
#         for item in scene.items():
#             # testing by isinstance is insufficient as a MapTitle item can have a wrappertype
#             # and the test returns false
#             #if isinstance(item, MapTitle):
#             try:
#                 if item is None:
#                     isMapTitle = False
#                 else:
#                     isMapTitle = item.identifyMapTitle() == 'MapTitle'
#             except Exception:
#                 isMapTitle = False
#             if isMapTitle:
#                 scene.removeItem(item)
#         self.mapTitle = None
        canvas.refresh()

    def setAnimateLayer(self) -> None:
        """Set self.animateLayer to first visible layer in Animations group, retitle as appropriate."""
        canvas = self._gv.iface.mapCanvas()
        root = QgsProject.instance().layerTreeRoot()
        animationLayers = QSWATUtils.getLayersInGroup(QSWATUtils._ANIMATION_GROUP_NAME, root, visible=True)
        if len(animationLayers) == 0:
            self.animateLayer = None
            self.setResultsLayer()
            return
        for treeLayer in animationLayers:
            mapLayer = treeLayer.layer()
            if self.mapTitle is None:
                self.mapTitle = MapTitle(self.conn, canvas, self.table, self.title, mapLayer)
                canvas.refresh()
                self.animateLayer = mapLayer
                return
            elif mapLayer == self.mapTitle.layer:
                # nothing to do
                return
            else:
                # first visible animation layer not current titleLayer
                self.clearMapTitle()
                dat = self.sliderValToDate()
                date = self.dateToString(dat)
                self.mapTitle = MapTitle(self.conn, canvas, self.table, self.title, mapLayer, line2=date)
                canvas.refresh()
                self.animateLayer = mapLayer
                return
        # if we get here, no visible animation layers
        self.clearMapTitle()
        self.animateLayer = None
        return     
    
    def setResultsLayer(self) -> None:
        """Set self.currentResultsLayer to first visible layer in Results group, retitle as appropriate."""
        canvas = self._gv.iface.mapCanvas()
        root = QgsProject.instance().layerTreeRoot()
        # only change results layer and title if there are no visible animate layers
        animationLayers = QSWATUtils.getLayersInGroup(QSWATUtils._ANIMATION_GROUP_NAME, root, visible=True)
        if len(animationLayers) > 0:
            return
        self.clearMapTitle()
        resultsLayers = QSWATUtils.getLayersInGroup(QSWATUtils._RESULTS_GROUP_NAME, root, visible=True) 
        if len(resultsLayers) == 0:
            self.currentResultsLayer = None
            return
        else:
            for treeLayer in resultsLayers:
                mapLayer = treeLayer.layer()
                self.currentResultsLayer = mapLayer
                assert self.currentResultsLayer is not None
                self.mapTitle = MapTitle(self.conn, canvas, self.table, self.title, mapLayer)
                canvas.refresh()
                return 
    
    def clearAnimationDir(self) -> None:
        """Remove shape files from animation directory."""
        if os.path.exists(self._gv.animationDir):
            pattern = QSWATUtils.join(self._gv.animationDir, '*.shp')
            for f in glob.iglob(pattern):
                QSWATUtils.tryRemoveFiles(f)
                
    def clearPngDir(self) -> None:
        """Remove .png files from Png directory."""
        if os.path.exists(self._gv.pngDir):
            pattern = QSWATUtils.join(self._gv.pngDir, '*.png')
            for f in glob.iglob(pattern):
                try:
                    os.remove(f)
                except Exception:
                    pass
            if Parameters._ISMAC:  #also need to remove .pgw files
                pattern = QSWATUtils.join(self._gv.pngDir, '*.pgw')
                for f in glob.iglob(pattern):
                    try:
                        os.remove(f)
                    except Exception:
                        pass
        self.currentStillNumber = 0
        
    def setSubbasinOutletChannels(self) -> None:
        """Fill subbasinOutletChannels from rivs shapefile unless already done.  Fill QqSubbasins combo."""
        if len(self.subbasinOutletChannels) > 0:
            return
        scenDir = QSWATUtils.join(self._gv.scenariosDir, self.scenario)
        resultsDir = QSWATUtils.join(scenDir, Parameters._RESULTS)
        rivsFile = QSWATUtils.join(resultsDir, Parameters._RIVS) + '.shp'
        if not os.path.isfile(rivsFile):
            QSWATUtils.error('Cannot find channels shapefile {0}'.format(rivsFile), self._gv.isBatch)
            return
        rivLayer = QgsVectorLayer(rivsFile, 'Channels', 'ogr')
        fields = rivLayer.fields()
        chIdx = fields.lookupField(QSWATTopology._CHANNEL)
        chRIdx = fields.lookupField(QSWATTopology._CHANNELR)
        subIdx = fields.lookupField(QSWATTopology._SUBBASIN)
        if chRIdx < 0 or subIdx < 0:
            rivs1File = QSWATUtils.join(self._gv.shapesDir, Parameters._RIVS1) + '.shp'
            if os.path.isfile(rivs1File):
                rivLayer = QgsVectorLayer(rivs1File, 'Channels', 'ogr')
                fields = rivLayer.fields()
                chIdx = fields.lookupField(QSWATTopology._CHANNEL)
                chRIdx = fields.lookupField(QSWATTopology._CHANNELR)
                subIdx = fields.lookupField(QSWATTopology._SUBBASIN)
                if chIdx >= 0 and chRIdx >= 0 and subIdx >= 0:
                    QSWATUtils.information('''Cannot find ChannelR or Subbasin fields in {0}.  
                    Will use {1}.
                    This is because your model was built with an older version of QSWAT+.
                    There will be no harm if your subbasins and channels have not chenged.
                    Otherwise you should rebuild and rerun your model.'''.format(rivsFile, rivs1File), self._gv.isBatch)
                    rivsFile = rivs1File
                else:
                    QSWATUtils.error('Cannot find ChannelR or Subbasin fields in {0}'.format(rivsFile), self._gv.isBatch)
                    return
        request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([chIdx, chRIdx, subIdx])
        downChannel = dict()
        channelToSubbasin = dict()
        for channel in rivLayer.getFeatures(request):
            chNum = channel[chIdx]
            downChannel[chNum] = channel[chRIdx]
            channelToSubbasin[chNum] = channel[subIdx]
        mainOutlet = 0
        for ch, chR in downChannel.items():
            sub = channelToSubbasin[ch]
            subR = channelToSubbasin.get(chR, -1)  # chR may be a reservoir
            if chR == 0 or (subR >= 0 and sub != subR):
                self.subbasinOutletChannels[sub] = ch
            if chR == 0:
                mainOutlet = sub
        self._dlg.QqSubbasin.clear()
        self._dlg.QqSubbasin.addItems(map(str, sorted(self.subbasinOutletChannels.keys())))
        self._dlg.dQpSubbasin.clear()
        self._dlg.dQpSubbasin.addItems(map(str, sorted(self.subbasinOutletChannels.keys())))
        self._dlg.QbSubbasin.clear()
        self._dlg.QbSubbasin.addItems(map(str, sorted(self.subbasinOutletChannels.keys())))
        # preselect main outlet subbasin
        if mainOutlet > 0:
            self._dlg.QqSubbasin.setCurrentText(str(mainOutlet))
            self._dlg.dQpSubbasin.setCurrentText(str(mainOutlet))
            self._dlg.QbSubbasin.setCurrentText(str(mainOutlet))
        self.setQqTableHead()
        self.cleardQpResult()
        self.setQbTableHead()
            
    def setQqTableHead(self) -> None:
        """Clears results table.  Sets header."""
        self._dlg.QqResults.clearContents()
        self._dlg.QqResults.setHorizontalHeaderLabels(['Q' + str(self._dlg.QqSpin.value())])
            
    def setQbTableHead(self) -> None:
        """Clears results table.  Sets header."""
        self._dlg.QbAnnualResult.setText('Annual result: ')
        self._dlg.QbResults.clearContents()
        self._dlg.QbResults.setHorizontalHeaderLabels(['Qb'])
        
    def initQResults(self) -> None:
        """Initialise post processing results tables."""
        self._dlg.QqResults.setVerticalHeaderLabels(Visualise._MONTHS)
        self._dlg.QbResults.setVerticalHeaderLabels(Visualise._MONTHS)
        # designer makes these false
        self._dlg.QqResults.verticalHeader().setVisible(True)
        self._dlg.QqResults.horizontalHeader().setVisible(True)
        self._dlg.dQpStartMonth.clear()
        self._dlg.dQpStartMonth.addItems(Visualise._MONTHS)
        self._dlg.dQpStartMonth.setCurrentIndex(-1)
        self._dlg.QbResults.verticalHeader().setVisible(True)
        self._dlg.QbResults.horizontalHeader().setVisible(True)
        self._dlg.QbStartMonth.clear()
        self._dlg.QbStartMonth.addItems(Visualise._MONTHS)
        self._dlg.QbStartMonth.setCurrentIndex(-1)
        
    def calculateQq(self) -> None:
        """Calcualte Qq results."""
        if not self.setPeriods():
            return
        startDate = date(self.startYear, self.startMonth, self.startDay)
        finishDate = date(self.finishYear, self.finishMonth, self.finishDay)
        flowDataTable = Visualise._EFLOWTABLE
        if not self._gv.db.hasDataConn(flowDataTable, self.conn):
            QSWATUtils.error('Table {0} is missing or empty'.format(flowDataTable), self._gv.isBatch)
            return
        monthData: Dict[int, List[float]] = {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [], 8: [], 9: [], 10: [], 11: [], 12: []}
        selectString = '[mon], [day], [yr], [flo_out]'
        where = 'gis_id = {0!s}'.format(self.subbasinOutletChannels[int(self._dlg.QqSubbasin.currentText())])
        sql = self._gv.db.sqlSelect(flowDataTable, selectString, '', where)
        for row in self.conn.execute(sql).fetchall():
            thisDay = date(row[2], row[0], row[1])
            if thisDay < startDate or finishDate < thisDay:
                continue
            monthData[row[0]].append(row[3])
        for m, l in monthData.items():
            if len(l) > 0:
                l.sort()
                percentile = Visualise.percentile(l, (100 - self._dlg.QqSpin.value()) / 100)
                assert percentile is not None
                self._dlg.QqResults.setItem(m-1, 0, QTableWidgetItem(locale.format_string('%.2F', percentile)))
#         QqStore = QSWATUtils.join(self._gv.resultsDir, 'q{0!s}.txt'.format(self._dlg.QqSpin.value()))
#         with open(QqStore, 'w', newline='') as f:
#             for m, l in monthData.items():
#                 f.write(Visualise._MONTHS[m-1])
#                 f.write('\n')
#                 f.write(str(l))
#                 f.write('\n')
                
    def saveQq(self) -> None:
        if self._dlg.QqResults.item(0, 0) is None:
            QSWATUtils.information('Please calculate before saving', self._gv.isBatch)
            return
        if self.lastQqResultsFile != '':
            startDir = os.path.split(self.lastQqResultsFile)[0]
        else:
            scenDir = QSWATUtils.join(self._gv.scenariosDir, self.scenario)
            startDir = QSWATUtils.join(scenDir, Parameters._RESULTS)
        if self._dlg.QqAppend.isChecked():
            fun = QFileDialog.getOpenFileName
            mode = 'a'
        else:
            fun = QFileDialog.getSaveFileName
            mode = 'w'
        resultsFile, _ = fun(None, 'Choose results file', startDir, 'Text files (*.txt);;Any file (*.*)')
        if resultsFile == '':
            return
        with open(resultsFile, mode, newline='') as f:
            startDate = date(self.startYear, self.startMonth, self.startDay).strftime(QSWATUtils._DATEFORMAT)
            finishDate = date(self.finishYear, self.finishMonth, self.finishDay).strftime(QSWATUtils._DATEFORMAT)
            f.write('Q{0!s} for {1} to {2}\n'.format(self._dlg.QqSpin.value(), startDate, finishDate))
            subbasin = self._dlg.QqSubbasin.currentText()
            f.write('Subbasin {0};  Channel {1}\n'.format(subbasin, self.subbasinOutletChannels[int(subbasin)]))
            for m in range(12):
                f.write(Visualise._MONTHS[m].ljust(12))
                f.write(self._dlg.QqResults.item(m, 0).text())
                f.write('\n')
            f.write('\n') 
        self.lastQqResultsFile = resultsFile 
        
    def cleardQpResult(self) -> None:
        """Clear dQp result."""
        self._dlg.dQpResult.setText('Result:')
        self.dQpResult = -1
        
    def dQpButtons(self) -> None:
        """Enable or not the percentile setting and clear the result."""
        self._dlg.dQpSpinP.setEnabled(self._dlg.dQpPercentile.isChecked())
        self.cleardQpResult()
        
    def calculatedQp(self) -> None:
        """Calculate dQp result."""
        if not self.setPeriods():
            return
        startDate = date(self.startYear, self.startMonth, self.startDay)
        finishDate = date(self.finishYear, self.finishMonth, self.finishDay)
        flowDataTable = Visualise._EFLOWTABLE
        if not self._gv.db.hasDataConn(flowDataTable, self.conn):
            QSWATUtils.error('Table {0} is missing or empty'.format(flowDataTable), self._gv.isBatch)
            return
        startMonth = self._dlg.dQpStartMonth.currentIndex() + 1
        if startMonth <= 0:
            QSWATUtils.information('Please choose start month', self._gv.isBatch)
            return
        # data has structure yearIndex -> flow value list
        flowData: Dict[int, List[float]] = dict()
        yearIndex = -1
        count = 0  # don't like using variable defined inside loop after completion, so define these here
        expectedLength = 0 
        # in case startmonth starts in output after day 1.  This data will be ignored.
        currentFlowData: List[float] = []
        selectString = '[mon], [day], [yr], [flo_out]'
        where = 'gis_id = {0!s}'.format(self.subbasinOutletChannels[int(self._dlg.dQpSubbasin.currentText())])
        orderBy = '[yr], [jday]'
        sql = self._gv.db.sqlSelect(flowDataTable, selectString, orderBy, where)
        for row in self.conn.execute(sql).fetchall():
            mon = row[0]
            day = row[1]
            year = row[2]
            val = row[3]
            thisDay = date(row[2], row[0], row[1])
            if thisDay < startDate or finishDate < thisDay:
                continue
            if year == self.startYear and mon < startMonth:
                continue
            if mon == startMonth and day == 1:
                # start new year
                count = 0
                expectedLength = 366 if (startMonth <= 2 and Visualise.isLeap(year)) or (startMonth > 2 and Visualise.isLeap(year+1)) else 365
                yearIndex = yearIndex + 1
                flowData[yearIndex] = []
                currentFlowData = flowData[yearIndex]
            currentFlowData.append(val)
            count += 1
        if count < expectedLength:
            # last year incomplete: delete it
            del flowData[yearIndex]
        if len(flowData) == 0:
            QSWATUtils.error('There is insufficient data.  There must be at least a yesr starting from 1 {0} {1}.'.
                             format(self._dlg.dQpStartMonth.currentText(), self.startYear), self._gv.isBatch)
            return
        d = self._dlg.dQpSpinD.value()
        # compute minimum moving total for each year: no point in dividing by d until the end
        totals: List[float] = []
#         dQpStore = QSWATUtils.join(self._gv.resultsDir, '{0!s}Q{1!s}.txt'.format(self._dlg.dQpSpinD.value(), self._dlg.dQpSpinP.value()))
#         f =  open(dQpStore, 'w', newline='')
        for yearIndex, flowVals in flowData.items():
#             f.write('Year: {0!s}'.format(self.startYear + yearIndex))
#             f.write('\n')
#             f.write('Flows out: \n')
#             f.write(str(flowVals))
#             f.write('\n')
            currentTotal = sum(flowVals[0:d]) # initial total for first d values
            minTotal = currentTotal
            for i in range(len(flowVals) - d): 
                lastTotal = currentTotal
                currentTotal = lastTotal - flowVals[i] + flowVals[i+d]
                if currentTotal < minTotal:
                    minTotal = currentTotal
            totals.append(minTotal)
        totals.sort()
#         f.write('Sorted totals:\n')
#         f.write(str(totals))
#         f.write('\n')
        # return percentile or mean according to final selection choice
        # remember we need to return a moving average, not a moving total
        if self._dlg.dQpPercentile.isChecked():
            p = self._dlg.dQpSpinP.value()
            fraction = p / 100
            self.dQpResult = Visualise.percentile(totals, fraction) / d
            self._dlg.dQpResult.setText('Result: {0}Q{1} is {2}'.format(d, p, locale.format_string('%.2F', self.dQpResult))) 
        else:
            self.dQpResult = (sum(totals) / len(totals)) / d
            self._dlg.dQpResult.setText('Result: {0}Qm is {1}'.format(d, locale.format_string('%.2F', self.dQpResult)))
#         f.write('Result: {0!s}'.format(self.dQpResult))
#         f.write('\n')
#         f.close()
                
    def savedQp(self) -> None:
        if self.dQpResult < 0:
            QSWATUtils.information('Please calculate before saving', self._gv.isBatch)
            return
        if self.lastdQpResultsFile != '':
            startDir = os.path.split(self.lastdQpResultsFile)[0]
        else:
            scenDir = QSWATUtils.join(self._gv.scenariosDir, self.scenario)
            startDir = QSWATUtils.join(scenDir, Parameters._RESULTS)
        if self._dlg.dQpAppend.isChecked():
            fun = QFileDialog.getOpenFileName
            mode = 'a'
        else:
            fun = QFileDialog.getSaveFileName
            mode = 'w'
        resultsFile, _ = fun(None, 'Choose results file', startDir, 'Text files (*.txt);;Any file (*.*)')
        if resultsFile == '':
            return
        with open(resultsFile, mode, newline='') as f:
            startDate = date(self.startYear, self.startMonth, self.startDay).strftime(QSWATUtils._DATEFORMAT)
            finishDate = date(self.finishYear, self.finishMonth, self.finishDay).strftime(QSWATUtils._DATEFORMAT)
            if self._dlg.dQpPercentile.isChecked():
                f.write('{0!s}Q{1!s} for {2} to {3}\n'.
                        format(self._dlg.dQpSpinD.value(), self._dlg.dQpSpinP.value(), startDate, finishDate))
            else:
                f.write('{0!s}Qm for {1} to {2}\n'.
                        format(self._dlg.dQpSpinD.value(), startDate, finishDate))
            subbasin = self._dlg.dQpSubbasin.currentText()
            month = self._dlg.dQpStartMonth.currentText()
            f.write('Subbasin {0};  Channel {1};  Starting in {2};  Result: {3}\n'.
                    format(subbasin, self.subbasinOutletChannels[int(subbasin)], month, locale.format_string('%.2F', self.dQpResult)))
            f.write('\n') 
        self.lastdQpResultsFile = resultsFile 
        
    def calculateQb(self) -> None:
        """Calculate Qb results."""
        if not self.setPeriods():
            return
        startDate = date(self.startYear, self.startMonth, self.startDay)
        finishDate = date(self.finishYear, self.finishMonth, self.finishDay)
        flowDataTable = Visualise._EFLOWTABLE
        if not self._gv.db.hasDataConn(flowDataTable, self.conn):
            QSWATUtils.error('Table {0} is missing or empty'.format(flowDataTable), self._gv.isBatch)
            return
        startMonth = self._dlg.QbStartMonth.currentIndex() + 1
        if startMonth <= 0:
            QSWATUtils.information('Please choose start month', self._gv.isBatch)
            return
        # data has structure yearIndex -> flow value list
        flowData: Dict[int, List[float]] = dict()
        monthData: Dict[int, List[float]] = {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [], 8: [], 9: [], 10: [], 11: [], 12: []}
        yearIndex = -1
        count = 0  # don't like using variable defined inside loop after completion, so define these here
        expectedLength = 0 
        selectString = '[mon], [day], [yr], [flo_out]'
        where = 'gis_id = {0!s}'.format(self.subbasinOutletChannels[int(self._dlg.QbSubbasin.currentText())])
        orderBy = '[yr], [jday]'
        sql = self._gv.db.sqlSelect(flowDataTable, selectString, orderBy, where)
        # in case startmonth starts in output after day 1.  This data will be ignored.
        currentFlowData: List[float] = []
        for row in self.conn.execute(sql).fetchall():
            mon = row[0]
            day = row[1]
            year = row[2]
            val = row[3]
            thisDay = date(row[2], row[0], row[1])
            if thisDay < startDate or finishDate < thisDay:
                continue
            if year == self.startYear and mon < startMonth:
                continue
            if mon == startMonth and day == 1:
                # start new year
                count = 0
                expectedLength = 366 if (startMonth <= 2 and Visualise.isLeap(year)) or (startMonth > 2 and Visualise.isLeap(year+1)) else 365
                yearIndex = yearIndex + 1
                flowData[yearIndex] = []
                currentFlowData = flowData[yearIndex]
            currentFlowData.append(val)
            count += 1
            monthData[mon].append(val)
        if count < expectedLength:
            # last year incomplete: delete it
            del flowData[yearIndex]
        if len(flowData) == 0:
            QSWATUtils.error('There is insufficient data.  There must be at least a yesr starting from 1 {0} {1}.'.
                             format(self._dlg.QbStartMonth.currentText(), self.startYear), self._gv.isBatch)
            return
        # compute minimum moving averages with highest rate of change for 1 to 100 days for each year
        avs: List[float] = []
        for yearIndex, flowVals in flowData.items():
            numVals = len(flowVals)  # days in this year
            maxRateOfIncrease = 0.0  # maximum rate of increase of minimum moving avaerage for i compared to i-1
            avForMaxRateOfIncrease = 0.0  # corresponding minimum moving average for i
            lastAv = 0.0  # minimum moving average for i-1.  Must be initialised to zero
            # compute with increasing i so that last value for i - 1 available when doing i
            for i in range(1, 101):
                minTotal = sum(flowVals[0:i])  # initial total for first i values
                lastTotal = minTotal  # remember total for j-1
                for j in range(numVals - i):  
                    currentTotal = lastTotal - flowVals[j] + flowVals[j+i]  # total from j+1 to j+i inclusive
                    if currentTotal < minTotal:
                        minTotal = currentTotal
                    lastTotal = currentTotal
                currentAv = minTotal / i
                if lastAv > 0:  # note this avoids i = 1 since lastAv initialised to zero, as well as preventing division by zero
                    rateOfIncrease = (currentAv - lastAv) / lastAv
                    if rateOfIncrease > maxRateOfIncrease:
                        maxRateOfIncrease = rateOfIncrease
                        avForMaxRateOfIncrease = currentAv
                lastAv = currentAv
            avs.append(avForMaxRateOfIncrease)
        self.QbResult = sum(avs) / len(avs)
#         # calculate Q85 for each month
#         q85s = dict()
#         minQ85 = float('inf')
#         for m, l in monthData.items():
#             if len(l) > 0:
#                 l.sort()
#                 q85 = Visualise.percentile(l, 0.85)
#                 q85s[m] = q85
#                 if q85 < minQ85:
#                     minQ85 = q85
        # calculate mean for each month
        means: Dict[int, float] = dict()
        minMean = float('inf')
        for m, l in monthData.items():
            if len(l) > 0:
                mean = sum(l) / len(l)
                means[m] = mean
                if mean < minMean:
                    minMean = mean
        self._dlg.QbAnnualResult.setText('Annual result: {0}'.format(locale.format_string('%.2F', self.QbResult)))
        # result for each month is Qb * variation factor
        # variation factor is square root of ratio of Q85 for month to minimum Q85
        # replace above with sqaure root of monthly mean to minimal monthly mean
#         for m, q85m in q85s.items():
#             factor = 1 if minQ85 == 0 else math.sqrt(q85m / minQ85)
        for m, mean in means.items():
            factor = 1 if minMean == 0 else math.sqrt(mean / minMean)
            Qbm = self.QbResult * factor
            self._dlg.QbResults.setItem(m-1, 0, QTableWidgetItem(locale.format_string('%.2F', Qbm)))
            
    def saveQb(self) -> None:
        if self._dlg.QbResults.item(0, 0) is None:
            QSWATUtils.information('Please calculate before saving', self._gv.isBatch)
            return
        if self.lastQbResultsFile != '':
            startDir = os.path.split(self.lastQbResultsFile)[0]
        else:
            scenDir = QSWATUtils.join(self._gv.scenariosDir, self.scenario)
            startDir = QSWATUtils.join(scenDir, Parameters._RESULTS)
        if self._dlg.QbAppend.isChecked():
            fun = QFileDialog.getOpenFileName
            mode = 'a'
        else:
            fun = QFileDialog.getSaveFileName
            mode = 'w'
        resultsFile, _ = fun(None, 'Choose results file', startDir, 'Text files (*.txt);;Any file (*.*)')
        if resultsFile == '':
            return
        with open(resultsFile, mode, newline='') as f:
            startDate = date(self.startYear, self.startMonth, self.startDay).strftime(QSWATUtils._DATEFORMAT)
            finishDate = date(self.finishYear, self.finishMonth, self.finishDay).strftime(QSWATUtils._DATEFORMAT)
            f.write('Qb for {0} to {1}\n'.format(startDate, finishDate))
            subbasin = self._dlg.QbSubbasin.currentText()
            month = self._dlg.QbStartMonth.currentText()
            f.write('Subbasin {0};  Channel {1};  Starting in {2}\n'.format(subbasin, self.subbasinOutletChannels[int(subbasin)], month))
            f.write('Annual      {0}\n'.format(locale.format_string('%.2F', self.QbResult)))
            for m in range(12):
                f.write(Visualise._MONTHS[m].ljust(12))
                f.write(self._dlg.QbResults.item(m, 0).text())
                f.write('\n')
            f.write('\n') 
        self.lastQbResultsFile = resultsFile 
                
    @staticmethod
    def percentile(N: List[float], percent: float) -> Optional[float]:
        """
        Find the percentile of a sorted list of values.
    
        N - is a list of values. Note N MUST BE already sorted.
        percent - a float value from 0.0 to 1.0.
    
        return - the percentile of the values
        """
        if not N:
            return None
        k = (len(N)-1) * percent
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return N[int(k)]
        d0 = N[int(f)] * (c-k)
        d1 = N[int(c)] * (k-f)
        return d0+d1
        

class MapTitle(QgsMapCanvasItem):
    
    """Item for displaying title at top left of map canvas."""
    
    def __init__(self, conn: Any, canvas: QgsMapCanvas, table: str, title: str, 
                 layer: QgsMapLayer, line2: Optional[str]=None) -> None:
        """Initialise rectangle for displaying project name, layer name,  plus line2, if any, below them."""
        super().__init__(canvas)
        ## normal font
        self.normFont = QFont()
        ## normal metrics object
        self.metrics = QFontMetricsF(self.normFont)
        # bold metrics object
        boldFont = QFont()
        boldFont.setBold(True)
        metricsBold = QFontMetricsF(boldFont)
        ## titled layer
        self.layer = layer
        ## project line of title
        self.line0 = 'Project: {0}'.format(title)
        ## First line of title
        # replace var with description and units if available
        items = layer.name().split()
        var = items[1]
        if conn is None:
            row = None
        else:
            sql = 'SELECT [units], [description] FROM column_description WHERE table_name=? AND column_name=?'
            row = conn.execute(sql, (table, var)).fetchone()
        # units can be '---'; also protect against NULL
        units = '' if row is None or row[0] is None or row[0] == '---' else ' ({0})'.format(row[0])
        description = var if row is None or row[1] is None else row[1]
        self.line1 = '{0} {1}'.format(items[0], description + units)
        # items has 3 or more components for static results, 2 for animation
        # add the rest
        for i in range(2, len(items)):
            self.line1 += ' {0}'.format(items[i])
        ## second line of title (or None)
        self.line2 = line2
        rect0 = metricsBold.boundingRect(self.line0)
        rect1 = self.metrics.boundingRect(self.line1)
        ## bounding rectange of first 2 lines 
        self.rect01 = QRectF(0, rect0.top() + rect0.height(),
                            max(rect0.width(), rect1.width()),
                            rect0.height() + rect1.height())
        ## bounding rectangle
        self.boundingRectangle = None
        if line2 is None:
            self.boundingRectangle = self.rect01
        else:
            self.updateLine2(line2)
    
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None) -> None:  # type: ignore # @UnusedVariable
        """Paint the text."""
#         if self.line2 is None:
#             painter.drawText(self.rect, Qt.AlignLeft, '{0}\n{1}'.format(self.line0, self.line1))
#         else:
#             painter.drawText(self.boundingRectangle, Qt.AlignLeft, '{0}\n{1}\n{2}'.format(self.line0, self.line1, self.line2))
        text = QTextDocument()
        text.setDefaultFont(self.normFont)
        if self.line2 is None:
            text.setHtml('<p><b>{0}</b><br/>{1}</p>'.format(self.line0, self.line1))
        else:
            text.setHtml('<p><b>{0}</b><br/>{1}<br/>{2}</p>'.format(self.line0, self.line1, self.line2))
        text.drawContents(painter)

    # def boundingRect(self) -> QRectF:
    #     """Return the bounding rectangle."""
    #     assert self.boundingRectangle is not None
    #     return self.boundingRectangle
    
    def updateLine2(self, line2: str) -> None:
        """Change second line."""
        self.line2 = line2
        rect2 = self.metrics.boundingRect(self.line2)
        self.boundingRectangle = QRectF(0, self.rect01.top(), 
                            max(self.rect01.width(), rect2.width()), 
                            self.rect01.height() + rect2.height())
    
    def identifyMapTitle(self) -> str:
        """Function used to identify a MapTitle object even when it has a wrapper."""    
        return 'MapTitle'
          
    
