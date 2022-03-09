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
"""
# Import the PyQt and QGIS libraries
from qgis.core import Qgis, QgsProject, QgsRasterLayer, QgsUnitTypes, QgsVectorLayer, QgsApplication
from qgis.analysis import QgsNativeAlgorithms
from qgis.PyQt.QtCore import QObject, QSettings, Qt, QTranslator, QFileInfo, QCoreApplication, qVersion
from qgis.PyQt.QtGui import QFontDatabase, QIcon, QFont
from qgis.PyQt.QtWidgets import QApplication, QInputDialog, QMessageBox, QAction, QFileDialog
import os
import subprocess
import time
import shutil
import sys
import traceback
import locale
import processing  # type: ignore @UnusedImport
from processing.core.Processing import Processing  # type: ignore

# Initialize Qt resources from file resources_rc.py
try:
    from .resources_rc import * # @UnusedWildImport
except:
    from resources_rc import *  # for convertFromArc @UnresolvedImport @UnusedWildImport
# Import the code for the dialog
# allow this to fail so no exception when loaded in wrong architecture (32 or 64 bit)
# QSWATUtils should have no further dependencies, especially in Cython modules
try:
    from .QSWATUtils import QSWATUtils, FileTypes  # @UnresolvedImport @UnusedImport type: ignore 
except:
    # for convertFromArc
    from QSWATUtils import QSWATUtils, FileTypes  # @UnresolvedImport @Reimport
try:
    txt = 'QSwatDialog'
    from .qswatdialog import QSwatDialog
    txt = 'HRUs'
    from .hrus import HRUs
    txt = 'QSWATTopology'
    from .QSWATTopology import QSWATTopology
    txt = 'GlobalVars'
    from .globals import GlobalVars
    txt = 'Delineation'
    from .delineation import Delineation
    txt = 'Parameters'
    from .parameters import Parameters
    txt = 'Visualise'
    from .visualise import Visualise
    txt = 'AboutQSWAT'
    from .about import AboutQSWAT
    txt = 'ExportTable'
    from .exporttable import ExportTable
except Exception:
    QSWATUtils.loginfo('QSWAT+ failed to import {0}: {1}'.format(txt, traceback.format_exc()))

class QSWATPlus(QObject):
    """QGIS plugin to prepare geographic data for SWAT+ Editor."""
    
    __version__ = '2.2.0'

    def __init__(self, iface):
        """Constructor."""
        
        QObject.__init__(self)
        
        # this import is a dependency on a Cython produuced .pyd or .so file which will fail if the wrong architecture
        # and so gives an immediate exit before the plugin is loaded
        ## flag to show if init ran successfully
        self.loadFailed = False
        try:
            from . import dataInC  # @UnusedImport
        except Exception:
            QSWATUtils.loginfo('Failed to load Cython module: wrong architecture?: {0}'.format(traceback.format_exc()))
            self.loadFailed = True
            return
        # uncomment next line for debugging
        # import pydevd; pydevd.settrace()
        # Save reference to the QGIS interface
        self._iface = iface
        # initialize plugin directory
        ## plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # add to PYTHONPATH
        sys.path.append(self.plugin_dir)
        settings = QSettings()
        # initialize locale
        # in testing with a dummy iface object this settings value can be None
        try:
            localeStr = settings.value("locale/userLocale")[0:2]
        except Exception:
            localeStr = 'en'
        localePath = os.path.join(self.plugin_dir, 'i18n', 'qswat_{}.qm'.format(localeStr))
        locale.setlocale(locale.LC_ALL, '')
        # set default behaviour for loading files with no CRS to prompt - the safest option
        settings.setValue('Projections/defaultBehaviour', 'prompt')
        ## translator
        if os.path.exists(localePath):
            self.translator = QTranslator()
            self.translator.load(localePath)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)
                
        self._gv = None  # set later
        # font = QFont('MS Shell Dlg 2', 8)
        try:
            pointSize = int(settings.value('/QSWATPlus/FontSize'))
        except Exception:
            pointSize = 8
        self.setUbuntuFont(pointSize)
        # an experiment - probably not use
        # self.setStyles()
        # Create the dialog (after translation) and keep reference
        self._odlg = QSwatDialog()
        self._odlg.setWindowFlags(self._odlg.windowFlags() & ~Qt.WindowContextHelpButtonHint & Qt.WindowMinimizeButtonHint)
        self._odlg.move(0, 0)
        #=======================================================================
        # font = self._odlg.font()
        # fm = QFontMetrics(font)
        # txt = 'The quick brown fox jumps over the lazy dog.'
        # family = font.family()
        # size = font.pointSize()
        # QSWATUtils.information('Family: {2}.  Point size: {3!s} (intended {4!s}).\nWidth of "{0}" is {1} pixels.'.format(txt, fm.width(txt), family, size, pointSize), False)
        #=======================================================================
        self._odlg.setWindowTitle('QSWAT+ {0}'.format(QSWATPlus.__version__))
        # flag used in initialising delineation form
        self._demIsProcessed = False
        ## deineation window
        self.delin = None
        ## create hrus window
        self.hrus = None
        ## visualise window
        self.vis = None
        
        # report QGIS version
        QSWATUtils.loginfo('QGIS version: {0}; QSWAT+ version: {1}'.format(Qgis.QGIS_VERSION, QSWATPlus.__version__))

    def initGui(self):
        """Create QSWAT button in the toolbar."""
        if self.loadFailed:
            return
        ## Action that will start plugin configuration
        self.action = QAction(
            QIcon(":/plugins/QSWATPlus/swatplus32.png"),
            '{0}'.format(QSWATUtils._QSWATNAME), self._iface.mainWindow())
        # connect the action to the run method
        self.action.triggered.connect(self.run)

        # Add toolbar button and menu item
        self._iface.addToolBarIcon(self.action)
        self._iface.addPluginToMenu('&{0}'.format(QSWATUtils._QSWATNAME), self.action)

    def unload(self):
        """Remove the QSWAT menu item and icon."""
        # allow for it not to have been loaded
        try:
            self._iface.removePluginMenu('&{0}'.format(QSWATUtils._QSWATNAME), self.action)
            self._iface.removeToolBarIcon(self.action)
        except Exception:
            pass

    def run(self):
        """Run QSWAT."""
        self._odlg.reportsBox.setVisible(False)
        self._odlg.reportsLabel.setVisible(False)
        self._odlg.reportsBox.clear()
        self._odlg.reportsBox.addItem(QSWATUtils.trans('Select report to view'))
        self._odlg.finished.connect(self.finish)
        # connect buttons
        self._odlg.aboutButton.clicked.connect(self.about)
        self._odlg.newButton.clicked.connect(self.newProject)
        self._odlg.existingButton.clicked.connect(self.existingProject)
        self._odlg.delinButton.clicked.connect(self.doDelineation)
        self._odlg.hrusButton.clicked.connect(self.doCreateHRUs)
        self._odlg.editButton.clicked.connect(self.startEditor)
        self._odlg.visualiseButton.clicked.connect(self.visualise)
        self._odlg.paramsButton.clicked.connect(self.runParams)
        self._odlg.reportsBox.activated.connect(self.showReport)
        self._odlg.exportButton.clicked.connect(self.exportTable)
        self.initButtons()
        self._odlg.projPath.setText('')
        # make sure we clear data from previous runs
        self.delin = None
        self.hrus = None
        self.vis = None
        # show the dialog
        self._odlg.show()
        # initially only new/existing project buttons visible if project not set
        proj = QgsProject.instance()
        if proj.fileName() == '':
            self._odlg.mainBox.setVisible(False)
            self._odlg.exportButton.setVisible(False)
        else:
            self._iface.mainWindow().setCursor(Qt.WaitCursor)
            self.setupProject(proj, False)
            self._iface.mainWindow().setCursor(Qt.ArrowCursor)
        # Run the dialog event loop
        result = self._odlg.exec_()
        # See if OK was pressed
        if result == 1:
            proj.write()
        
    def initButtons(self):
        """Initial button settings."""
        self._odlg.delinLabel.setText('Step 1')
        self._odlg.hrusLabel.setText('Step 2')
        self._odlg.hrusLabel.setEnabled(False)
        self._odlg.hrusButton.setEnabled(False)
        self._odlg.editLabel.setEnabled(False)
        self._odlg.editButton.setEnabled(False)
        self._odlg.visualiseLabel.setVisible(False)
        self._odlg.visualiseButton.setVisible(False)

    def about(self):
        """Show information about QSWAT."""
        form = AboutQSWAT(self._gv)
        form.run(QSWATPlus.__version__)
        
    def setUbuntuFont(self, ptSize):
        """Set Ubuntu font."""
        QFontDatabase.addApplicationFont(":/fonts/Ubuntu-B.ttf")
        QFontDatabase.addApplicationFont(":/fonts/Ubuntu-BI.ttf")
        QFontDatabase.addApplicationFont(":/fonts/Ubuntu-C.ttf")
        QFontDatabase.addApplicationFont(":/fonts/Ubuntu-L.ttf")
        QFontDatabase.addApplicationFont(":/fonts/Ubuntu-LI.ttf")
        QFontDatabase.addApplicationFont(":/fonts/Ubuntu-M.ttf")
        QFontDatabase.addApplicationFont(":/fonts/Ubuntu-MI.ttf")
        QFontDatabase.addApplicationFont(":/fonts/Ubuntu-R.ttf")
        QFontDatabase.addApplicationFont(":/fonts/Ubuntu-RI.ttf")
        ufont = QFont("Ubuntu", ptSize, 1)
        QApplication.setFont(ufont)
        QSWATUtils.loginfo('Ubuntu {0} point font set'.format(ptSize))
        
#     def setStyles(self):
#         """Set stle sheet values"""
#         QApplication.instance().setStyleSheet("""
#             QDialog[QSWATDialog=true] {
#                 background-color: white
#                 }
#             QPushButton {
#                 color: white
#                 }
#             QPushButton[browseButton=true] {
#                 color: white;
#                 background-color: blue
#                 }
#             QPushButton[okButton=true] {
#                 color: white;
#                 background-color: green
#                 }
#             QPushButton[cancelButton=true] {
#                 background-color: grey
#                 }
#         """)
        
    def newProject(self):
        """Call QGIS actions to create and name a new project."""
        settings = QSettings()
        if settings.contains('/QSWATPlus/LastInputPath'):
            path = settings.value('/QSWATPlus/LastInputPath')
        else:
            path = ''
        title = 'Select parent directory'
        parentDir = QFileDialog.getExistingDirectory(None, title, path)
        if parentDir is not None and os.path.isdir(parentDir):
            projName, ok = QInputDialog.getText(None, 'Project name', 'Please enter the project name, starting with a letter:')
            if not ok:
                return
            if not projName[0].isalpha():
                QSWATUtils.error('Project name must start with a letter', False)
                return
            projDir = QSWATUtils.join(parentDir, projName)
            if os.path.exists(projDir):
                response = QSWATUtils.question('Project directory {0} already exists.  Do you wish to delete it?'.format(projDir), False, False)
                if response != QMessageBox.Yes:
                    return
                shutil.rmtree(projDir, True)
            try: 
                os.mkdir(projDir)
            except Exception:
                QSWATUtils.exceptionError('Failed to create project directory {0}'.format(projDir), False)
                return
            self._iface.newProject()
            projFile = QSWATUtils.join(projDir, projName + '.qgs')
            proj = QgsProject.instance()
            proj.setFileName(projFile)
            QSWATUtils.loginfo('Project file is {0}'.format(projFile))
            self._iface.actionSaveProject().trigger()
            # allow time for project to be created
            time.sleep(2)
            self.initButtons()
            settings.setValue('/QSWATPlus/LastInputPath', str(projDir))
            self._odlg.raise_()
            self.setupProject(proj, False)
            self._gv.writeProjectConfig(0, 0)
        
    def existingProject(self):
        """Open an existing QGIS project."""
        self._iface.actionOpenProject().trigger()
        # allow time for project to be opened
        time.sleep(2)
        proj = QgsProject.instance()
        if proj.fileName() == '':
            QSWATUtils.error('No project opened', False)
            return
        self._odlg.raise_()
        self.setupProject(proj, False)
    
    def setupProject(self, proj, isBatch, isHUC=False, logFile=None):
        """Set up the project."""
        self._odlg.mainBox.setVisible(True)
        self._odlg.mainBox.setEnabled(False)
        self._odlg.setCursor(Qt.WaitCursor)
        self._odlg.projPath.setText('Restarting project ...')
        title = QFileInfo(proj.fileName()).baseName()
        proj.setTitle(title)
        isHUCFromProjfile, found = proj.readBoolEntry(title, 'delin/isHUC', False)
        if not found:
            # isHUC not previously set.  Use parameter above and record
            proj.writeEntryBool(title, 'delin/isHUC', isHUC)
        else:
            isHUC = isHUCFromProjfile
        # now have project so initiate global vars
        # if we do this earlier we cannot for example find the project database
        self._gv = GlobalVars(self._iface, QSWATPlus.__version__, self.plugin_dir, isBatch, isHUC, logFile)
        if self._gv.SWATPlusDir == '':
            # failed to find SWATPlus directory
            return
        self._odlg.projPath.repaint()
        self.checkReports()
        self.setLegendGroups()
        Processing.initialize()
        if 'native' not in [p.id() for p in QgsApplication.processingRegistry().providers()]:
            QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
        # enable edit button if converted from Arc with 'No GIS' option
        title = proj.title()
        choice, found = proj.readNumEntry(title, 'fromArc', -1)
        if found:
            self._gv.fromArcChoice = choice
            if choice == 2:  # NB value from convertFromArc.py
                self._odlg.editLabel.setEnabled(True)
                self._odlg.editButton.setEnabled(True)
        # also assume editor can be run if there are stream and hrus shapefiles in the results directory
        if os.path.isfile(os.path.join(self._gv.resultsDir, Parameters._RIVS + '.shp')) and \
            os.path.isfile(os.path.join(self._gv.resultsDir, Parameters._SUBS + '.shp')):
                self._odlg.editLabel.setEnabled(True)
                self._odlg.editButton.setEnabled(True)
        if self.demProcessed():
            self._demIsProcessed = True
            self.allowCreateHRU()
            self.hrus = HRUs(self._gv, self._odlg.reportsBox)
            #result = hrus.tryRun()
            #if result == 1:
            if self.hrus.HRUsAreCreated():
                # QSWATUtils.progress('Done', self._odlg.hrusLabel)
                self.showReports()
                self._odlg.editLabel.setEnabled(True)
                self._odlg.editButton.setEnabled(True)
        if os.path.exists(QSWATUtils.join(self._gv.resultsDir, Parameters._OUTPUTDB)):
            self._odlg.visualiseLabel.setVisible(True)
            self._odlg.visualiseButton.setVisible(True)
        self._odlg.projPath.setText(self._gv.projDir)
        self._odlg.mainBox.setEnabled(True)
        self._odlg.exportButton.setVisible(True)
        self._odlg.setCursor(Qt.ArrowCursor)
            
    def runParams(self):
        """Run parameters form."""
        params = Parameters(self._gv)
        params.run()
        
    def showReport(self):
        """Display selected report."""
#         if not self._odlg.reportsBox.hasFocus():
#             return
        item = self._odlg.reportsBox.currentText()
        if item == Parameters._TOPOITEM:
            report = Parameters._TOPOREPORT
        elif item == Parameters._BASINITEM:
            report = Parameters._BASINREPORT
        elif item == Parameters._HRUSITEM:
            report = Parameters._HRUSREPORT
        else:
            return
        report = QSWATUtils.join(self._gv.textDir, report)
        if not os.path.exists(report):
            QSWATUtils.error('Cannot find report {0}'.format(report))
            return
        if Parameters._ISWIN : # Windows
            os.startfile(report)  # @UndefinedVariable since not defined in Linux or Mac
        elif Parameters._ISLINUX:
            subprocess.call(['xdg-open', report])
        else:
            os.system('open "{0}"'.format(report))
        self._odlg.reportsBox.setCurrentIndex(0)
        
    def exportTable(self):
        """Run export table form."""
        export = ExportTable(self._gv)
        export.run()
        
    def checkReports(self):
        """Add existing reports to reports box and if there are some make it visible."""
        makeVisible = False
        topoReport = QSWATUtils.join(self._gv.textDir, Parameters._TOPOREPORT)
        if os.path.exists(topoReport) and self._odlg.reportsBox.findText(Parameters._TOPOITEM) < 0:
            makeVisible = True
            self._odlg.reportsBox.addItem(Parameters._TOPOITEM)
        basinReport = QSWATUtils.join(self._gv.textDir, Parameters._BASINREPORT)
        if os.path.exists(basinReport) and self._odlg.reportsBox.findText(Parameters._BASINITEM) < 0:
            makeVisible = True
            self._odlg.reportsBox.addItem(Parameters._BASINITEM)
        hrusReport = QSWATUtils.join(self._gv.textDir, Parameters._HRUSREPORT)
        if os.path.exists(hrusReport) and self._odlg.reportsBox.findText(Parameters._HRUSITEM) < 0:
            makeVisible = True
            self._odlg.reportsBox.addItem(Parameters._HRUSITEM)
        if makeVisible:
            self._odlg.reportsBox.setVisible(True)
            self._odlg.reportsLabel.setVisible(True)
            self._odlg.reportsBox.setCurrentIndex(0)

    def doDelineation(self):
        """Run the delineation dialog."""
        # avoid getting second window
        if self.delin is not None and self.delin._dlg.isEnabled():
            self.delin._dlg.close()
        self.delin = Delineation(self._gv, self._demIsProcessed)
        result = self.delin.run()
        if result == 1 and self._gv.isDelinDone():
            self._demIsProcessed = True
            self.allowCreateHRU()
            # remove old data so cannot be reused
            self._gv.db.clearTable('BASINSDATA')
            # make sure HRUs starts from scratch
            if self.hrus and self.hrus._dlg is not None:
                self.hrus._dlg.close()
            self.hrus = None
        elif result == 0:
            self._demIsProcessed = False
            self._odlg.delinLabel.setText('Step 1')
            self._odlg.hrusLabel.setText('Step 2')
            self._odlg.hrusLabel.setEnabled(False)
            self._odlg.hrusButton.setEnabled(False)
            self._odlg.editLabel.setEnabled(False)
            self._odlg.editButton.setEnabled(False)
        self._odlg.raise_()
        
    def doCreateHRUs(self):
        """Run the HRU creation dialog."""
        # avoid getting second window
        if self.hrus is not None and self.hrus._dlg.isEnabled():
            self.hrus._dlg.close()
        self.hrus = HRUs(self._gv, self._odlg.reportsBox)
        result = self.hrus.run()
        if result == 1:
            # QSWATUtils.progress('Done', self._odlg.hrusLabel)
            self._odlg.editLabel.setEnabled(True)
            self._odlg.editButton.setEnabled(True)
        self._odlg.raise_()
            
    def demProcessed(self):
        """
        Return true if we can proceed with HRU creation.
        
        Return false if any required project setting is not found 
        in the project file
        Return true if:
        Using existing watershed and watershed grid exists and 
        is newer than dem
        or
        Not using existing watershed and filled dem exists and 
        is no older than dem, and
        watershed shapefile exists and is no older than filled dem
        """
        proj = QgsProject.instance()
        if not proj:
            QSWATUtils.loginfo('demProcessed failed: no project')
            return False
        title = proj.title()
        root = proj.layerTreeRoot()
        demFile, found = proj.readEntry(title, 'delin/DEM', '')
        if not found or demFile == '':
            QSWATUtils.loginfo('demProcessed failed: no DEM')
            return False
        demFile = proj.readPath(demFile)
        demLayer, _ = QSWATUtils.getLayerByFilename(root.findLayers(), demFile, FileTypes._DEM,
                                                    self._gv, None, QSWATUtils._WATERSHED_GROUP_NAME)
        if not demLayer:
            QSWATUtils.loginfo('demProcessed failed: no DEM layer')
            return False
        self._gv.demFile = demFile
        self._gv.elevationNoData = demLayer.dataProvider().sourceNoDataValue(1)
        units = demLayer.crs().mapUnits()
        factor = 1 if units == QgsUnitTypes.DistanceMeters else Parameters._FEETTOMETRES if units == QgsUnitTypes.DistanceFeet else 0
        if factor == 0:
            QSWATUtils.loginfo('demProcessed failed: units are {0!s}'.format(units))
            return False
        self._gv.cellArea = demLayer.rasterUnitsPerPixelX() * demLayer.rasterUnitsPerPixelY() * factor * factor
        # hillshade
        Delineation.addHillshade(demFile, root, demLayer, self._gv)
        outletFile, found = proj.readEntry(title, 'delin/outlets', '')
        if found and outletFile != '':
            outletFile = proj.readPath(outletFile)
            outletLayer, _ = \
                QSWATUtils.getLayerByFilename(root.findLayers(), outletFile, FileTypes._OUTLETS,
                                              self._gv, None, QSWATUtils._WATERSHED_GROUP_NAME)
            if not outletLayer:
                QSWATUtils.loginfo('demProcessed failed: no outlet layer')
                return False
        else:
            outletLayer = None
        self._gv.outletFile = outletFile
        self._gv.existingWshed = proj.readBoolEntry(title, 'delin/existingWshed', False)[0]
        self._gv.useGridModel = proj.readBoolEntry(title, 'delin/useGridModel', False)[0]
        self._gv.useLandscapes = proj.readBoolEntry(title, 'lsu/useLandscapes', False)[0]
        streamFile, found = proj.readEntry(title, 'delin/net', '')
        if self._gv.useGridModel or not self._gv.existingWshed:
            if not found or streamFile == '':
                QSWATUtils.loginfo('demProcessed failed: no streams shapefile')
                return False
            streamFile = proj.readPath(streamFile)
            ft = FileTypes._GRIDSTREAMS if self._gv.useGridModel else FileTypes._STREAMS
            streamLayer, _ = \
                QSWATUtils.getLayerByFilename(root.findLayers(), streamFile, ft, 
                                              self._gv, None, QSWATUtils._WATERSHED_GROUP_NAME)
            if not streamLayer:
                QSWATUtils.loginfo('demProcessed failed: no streams layer')
                return False
            self._gv.streamFile = streamFile
        if self._gv.useGridModel:
            self._gv.gridSize, found = proj.readNumEntry(title, 'delin/gridSize', 0)
            if not found or self._gv.gridSize <= 0:
                QSWATUtils.loginfo('demProcessed failed: grid size not set')
                return False
        else:
            channelFile, found = proj.readEntry(title, 'delin/channels', '')
            if not found or channelFile == '':
                QSWATUtils.loginfo('demProcessed failed: no channels shapefile')
                return False
            channelFile = proj.readPath(channelFile)
            channelLayer, _ = \
                QSWATUtils.getLayerByFilename(root.findLayers(), channelFile, FileTypes._CHANNELS, 
                                              self._gv, None, QSWATUtils._WATERSHED_GROUP_NAME)
            if not channelLayer:
                QSWATUtils.loginfo('demProcessed failed: no channels layer')
                return False
            self._gv.channelFile = channelFile
        subbasinsFile, found = proj.readEntry(title, 'delin/subbasins', '')
        if not found or subbasinsFile == '':
            QSWATUtils.loginfo('demProcessed failed: no subbasins shapefile')
            return False
        subbasinsFile = proj.readPath(subbasinsFile)
        subbasinsInfo = QFileInfo(subbasinsFile)
        subbasinsTime = subbasinsInfo.lastModified()
        subbasinsLayer, _ = \
            QSWATUtils.getLayerByFilename(root.findLayers(), subbasinsFile, FileTypes._SUBBASINS, 
                                          self._gv, None, QSWATUtils._WATERSHED_GROUP_NAME)
        if not subbasinsLayer:
            QSWATUtils.loginfo('demProcessed failed: no subbasins layer')
            return False
        self._gv.subbasinsFile = subbasinsFile
        self._gv.subsNoLakesFile, _ = proj.readEntry(title, 'delin/subsNoLakes', '')
        if self._gv.subsNoLakesFile != '':
            self._gv.subsNoLakesFile = proj.readPath(self._gv.subsNoLakesFile)
        if not self._gv.useGridModel:
            wshedFile, found = proj.readEntry(title, 'delin/wshed', '')
            if not found or wshedFile == '':
                QSWATUtils.loginfo('demProcessed failed: no wshed shapefile')
                return False
            wshedFile = proj.readPath(wshedFile)
            if self._gv.existingWshed:
                wshedLayer, _ = \
                    QSWATUtils.getLayerByFilename(root.findLayers(), wshedFile, FileTypes._EXISTINGWATERSHED, 
                                                  self._gv, None, QSWATUtils._WATERSHED_GROUP_NAME)
                if not wshedLayer:
                    QSWATUtils.loginfo('demProcessed failed: no wshed layer')
                    return False
            self._gv.wshedFile = wshedFile
        demInfo = QFileInfo(demFile)
        if not demInfo.exists():
            QSWATUtils.loginfo('demProcessed failed: no DEM info')
            return False
        base = QSWATUtils.join(demInfo.absolutePath(), demInfo.baseName())
        if not self._gv.existingWshed:
            burnFile, found = proj.readEntry(title, 'delin/burn', '')
            if found and burnFile != '':
                burnFile = proj.readPath(burnFile)
                if not os.path.exists(burnFile):
                    QSWATUtils.loginfo('demProcessed failed: no burn file')
                    return False
                self._gv.slopeFile = base + 'slope.tif'
            else:
                self._gv.slopeFile = base + 'slp.tif'
        else:
            self._gv.slopeFile = base + 'slp.tif'
        if not os.path.exists(self._gv.slopeFile):
            QSWATUtils.loginfo('demProcessed failed: no slope raster')
            return False
        self._gv.basinFile = base + 'wStream.tif'
        if not self._gv.useGridModel:
            self._gv.channelBasinFile = base + 'wChannel.tif'
            self._gv.srcChannelFile = base + 'srcChannel.tif'
        streamDrainage = proj.readBoolEntry(title, 'delin/streamDrainage', False)[0]
        if self._gv.existingWshed:
            if not self._gv.useGridModel:
                if not os.path.exists(self._gv.basinFile):
                    QSWATUtils.loginfo('demProcessed failed: no subbasins raster')
                    return False
        else:
            self._gv.pFile = base + 'p.tif'
            if not os.path.exists(self._gv.pFile):
                QSWATUtils.loginfo('demProcessed failed: no p raster')
                return False
            self._gv.felFile = base + 'fel.tif'
            felInfo = QFileInfo(self._gv.felFile)
            if not (felInfo.exists() and subbasinsInfo.exists()):
                QSWATUtils.loginfo('demProcessed failed: no filled raster')
                return False
            self._gv.ad8File = base + 'ad8.tif'
            if not os.path.exists(self._gv.ad8File):
                QSWATUtils.loginfo('demProcessed failed: no D8 accumulation raster')
                return False
            demTime = demInfo.lastModified()
            felTime = felInfo.lastModified()
            if not (demTime <= felTime <= subbasinsTime):
                QSWATUtils.loginfo('demProcessed failed: not up to date')
                return False
            self._gv.distStFile = base + 'distst.tif'
            if not os.path.exists(self._gv.distStFile):
                QSWATUtils.loginfo('demProcessed failed: no distance to outlet raster')
                return False
            self._gv.distChFile = base + 'distch.tif'
            if not self._gv.useGridModel:
                if not os.path.exists(self._gv.distChFile):
                    QSWATUtils.loginfo('demProcessed failed: no distance to channel raster')
                    return False
            valleyDepthsFile = base + 'depths.tif'
            if os.path.exists(valleyDepthsFile):
                self._gv.valleyDepthsFile = valleyDepthsFile
            # no longer compulsory
#             if not os.path.exists(self._gv.valleyDepthsFile):
#                 QSWATUtils.loginfo('demProcessed failed: no valley depths raster')
#                 return False
        if not self._gv.useGridModel:
            if not os.path.exists(self._gv.channelBasinFile):
                QSWATUtils.loginfo('demProcessed failed: no channel basins raster')
                return False
        snapFile, found = proj.readEntry(title, 'delin/snapOutlets', '')
        if found and snapFile != '':
            snapFile = proj.readPath(snapFile)
            if os.path.exists(snapFile):
                self._gv.snapFile = snapFile
            else:
                snapFile = ''
        else:
            snapFile = ''
        lakeLayer = None
        lakeFile, found = proj.readEntry(title, 'delin/lakes', '')
        if found and lakeFile != '':
            lakeFile = proj.readPath(lakeFile)
            if os.path.exists(lakeFile):
                self._gv.lakeFile = lakeFile
                lakeLayer = QgsVectorLayer(lakeFile, 'Lakes', 'ogr')
                if self._gv.useGridModel:
                    gridLakesAdded = proj.readBoolEntry(title, 'delin/gridLakesAdded', False)[0]
                    if not gridLakesAdded:
                        QSWATUtils.loginfo('demProcessed failed: grid lakes not added')
                        return False
                else:
                    chBasinNoLakeFile = base + 'wChannelNoLake.tif'
                    if os.path.exists(chBasinNoLakeFile):
                        self._gv.chBasinNoLakeFile = chBasinNoLakeFile
                        if not self._gv.existingWshed:
                            lakePointsAdded = proj.readBoolEntry(title, 'delin/lakePointsAdded', False)[0]
                            if not lakePointsAdded:
                                QSWATUtils.loginfo('demProcessed failed: lake points not added')
                                return False
                    else:
                        QSWATUtils.loginfo('demProcessed failed: no channel basins without lakes raster')
                        return False
                playaFile = os.path.splitext(self._gv.demFile)[0] + 'playa.tif'
                if QSWATUtils.isUpToDate(lakeFile, playaFile):
                    self._gv.playaFile = playaFile
        snapLayer = outletLayer if snapFile == '' else QgsVectorLayer(self._gv.snapFile, 'Snapped outlets', 'ogr')
        chanLayer = streamLayer if self._gv.useGridModel else channelLayer
        if self._gv.existingWshed:
            ad8Layer = None
        else:
            ad8Layer = QgsRasterLayer(self._gv.ad8File, 'Accumulation')
        if not self._gv.topo.setUp0(demLayer, chanLayer, snapLayer, ad8Layer, self._gv):
            return False
        basinIndex = self._gv.topo.getIndex(subbasinsLayer, QSWATTopology._POLYGONID)
        if basinIndex < 0:
            return False
        for feature in subbasinsLayer.getFeatures():
            basin = feature.attributes()[basinIndex]
            centroid = feature.geometry().centroid().asPoint()
            self._gv.topo.basinCentroids[basin] = (centroid.x(), centroid.y())
        if lakeLayer is not None:
            if not self._gv.topo.readLakesData(self._gv.db):
                QSWATUtils.loginfo('demProcessed failed: lakes data not read')
                return False
        # this can go wrong if eg the streams and watershed files exist but are inconsistent
        try:
            if not self._gv.topo.setUp(demLayer, chanLayer, subbasinsLayer, snapLayer, lakeLayer,
                                       self._gv, self._gv.existingWshed, False, self._gv.useGridModel, streamDrainage, False):
                QSWATUtils.loginfo('demProcessed failed: topo setup failed')
                return False
            if len(self._gv.topo.inlets) == 0:
                # no inlets, so no need to expand subbasins layer legend
                treeSubbasinsLayer = root.findLayer(subbasinsLayer.id())
                treeSubbasinsLayer.setExpanded(False)
        except Exception:
            QSWATUtils.loginfo('demProcessed failed: topo setup raised exception: {0}'.format(traceback.format_exc()))
            return False
        return True
            
    def allowCreateHRU(self):
        """Mark delineation as Done and make create HRUs option visible."""
        # QSWATUtils.progress('Done', self._odlg.delinLabel)
        # QSWATUtils.progress('Step 2', self._odlg.hrusLabel)
        self._odlg.hrusLabel.setEnabled(True)
        self._odlg.hrusButton.setEnabled(True)
        self._odlg.editLabel.setEnabled(False)
        self._odlg.editButton.setEnabled(False)
        
    def showReports(self):
        """Show reports combo box and add items if necessary."""
        self._odlg.reportsBox.setVisible(True)
        if self._odlg.reportsBox.findText(Parameters._TOPOITEM) < 0:
            self._odlg.reportsBox.addItem(Parameters._TOPOITEM)
        if self._odlg.reportsBox.findText(Parameters._BASINITEM) < 0:
            self._odlg.reportsBox.addItem(Parameters._BASINITEM)
        if self._odlg.reportsBox.findText(Parameters._HRUSITEM) < 0:
            self._odlg.reportsBox.addItem(Parameters._HRUSITEM)
            
    def setLegendGroups(self):
        """Legend groups are used to keep legend in reasonable order.  
        Create them if necessary.
        """
        root = QgsProject.instance().layerTreeRoot()
        groups = [QSWATUtils._ANIMATION_GROUP_NAME,
                  QSWATUtils._RESULTS_GROUP_NAME,
                  QSWATUtils._WATERSHED_GROUP_NAME,
                  QSWATUtils._LANDUSE_GROUP_NAME,
                  QSWATUtils._SOIL_GROUP_NAME,
                  QSWATUtils._SLOPE_GROUP_NAME]
        for i in range(len(groups)):
            group = groups[i]
            node = root.findGroup(group)
            if node is None:
                root.insertGroup(i, group)

    def startEditor(self):
        """Start the SWAT Editor, first setting its initial parameters."""
        # self._gv.setSWATEditorParams()
        editor = self._gv.findSWATPlusEditor()
        if editor is None:
            return
        QSWATUtils.loginfo('Starting SWAT+ editor with command: "{0}" "{1}"'.format(editor, self._gv.db.dbFile))
        subprocess.call('"{0}" "{1}"'.format(editor, self._gv.db.dbFile), shell=True)
        if os.path.exists(QSWATUtils.join(self._gv.resultsDir, Parameters._OUTPUTDB)):
            self._odlg.visualiseLabel.setVisible(True)
            self._odlg.visualiseButton.setVisible(True)
        
    def visualise(self):
        """Run visualise form."""
        # avoid getting second window
        if self.vis is not None and self.vis._dlg.isEnabled():
            self.vis._dlg.close()
        self.vis = Visualise(self._gv)
        self.vis.run()
        self.vis = None
                    
    def finish(self):   
        """Close the database connections and subsidiary forms."""
        if QSWATUtils is not None:
            QSWATUtils.deleteTempFolder()
            QSWATUtils.loginfo('Closing databases')
        try:
            self.delin = None
            self.hrus = None
            self.vis = None
            if self._gv and self._gv.db:
                if self._gv.db.conn:
                    self._gv.db.conn.close()
                if self._gv.db.connRef:
                    self._gv.db.connRef.close() 
            if QSWATUtils is not None:
                QSWATUtils.loginfo('Databases closed') 
        except Exception:
            pass
        
