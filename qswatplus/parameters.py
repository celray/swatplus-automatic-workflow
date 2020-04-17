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
try:
    from parametersdialog import ParametersDialog
    from QSWATUtils import QSWATUtils
except:
    pass  # not needed by convertFromArc
import os.path

class Parameters:
    
    """Collect QSWAT parameters (location of SWATPlus directory and MPI) from user and save."""
    
    _ISWIN = os.name == 'nt'
    _SWATPLUSDEFAULTDIR = r'C:\SWAT\SWATPlus' if _ISWIN else os.path.expanduser('~') + '/.local/share/swatplus'
    _SWATEDITOR = 'SWATPlusEditor.exe' if _ISWIN else 'swatpluseditor'
    _SWATEDITORDIR = 'SWATPlusEditor'
    _MPIEXEC = 'mpiexec.exe' if _ISWIN else 'mpiexec'
    _MPIEXECDEFAULTDIR = r'C:\Program Files\Microsoft MPI\Bin' if _ISWIN else '/usr/bin'
    _TAUDEMDIR = 'TauDEM5Bin'
    _TAUDEMHELP = 'TauDEM_Tools.chm'  # not used in Linux
    _TAUDEMDOCS = 'http://hydrology.usu.edu/taudem/taudem5/documentation.html'
    _DBDIR = 'Databases'
    _DBPROJ = 'QSWATPlusProj2018.sqlite'
    _DBREF = 'swatplus_datasets.sqlite'
    _RESULTS = 'Results'
    _PLOTS = 'Plots'
    _TXTINOUT = 'TxtInOut'
    _SOILDB = 'swatplus_soils.sqlite'
    _SIM = 'time.sim'
    _PRT = 'print.prt'
    _OUTPUTDB = 'swatplus_output.sqlite'
    _SUBS = 'subs'
    _RIVS = 'rivs'
    _LSUS = 'lsus'
    _HRUS = 'hrus'
    _AQUIFERS = 'aquifers'
    _DEEPAQUIFERS = 'deep_aquifers'
    _SUBS1 = 'subs1'
    _RIVS1 = 'rivs1'
    _LSUS1 = 'lsus1'
    _LSUS2 = 'lsus2'
    _HRUS1 = 'hrus1'
    _HRUS2 = 'hrus2'
    _ANIMATION = 'Animation'
    _PNG = 'Png'
    _STILLPNG = 'still.png'
    
    _TOPOREPORT = 'TopoRep.txt'
    _TOPOITEM = 'Elevation'
    _BASINREPORT = 'LanduseSoilSlopeRepSwat.txt'
    _BASINITEM = 'Landuse and Soil'
    _HRUSREPORT = 'HruLanduseSoilSlopeRepSwat.txt'
    _HRUSITEM = 'HRUs'
    
    _DRAINAGECSV = 'drainage.csv'
    
    _USECSV = 'Use csv file'
    
    _LANDUSE = 'Landuse'
    _SOIL = 'Soil'
    _SLOPEBAND = 'SlopeBand'
    _AREA = 'Area'
    _PERCENTSUB = '%Subbasin'
    _PERCENTLSU = '%Landscape'
    
    _SQKM = 'sq. km'
    _HECTARES = 'hectares'
    _SQMETRES = 'sq. metres'
    _SQMILES = 'sq. miles'
    _ACRES = 'acres'
    _SQFEET = 'sq. feet'
    _METRES = 'metres'
    _FEET = 'feet'
    _CM = 'centimetres'
    _MM = 'millimetres'
    _INCHES = 'inches'
    _YARDS = 'yards'
    _DEGREES = 'degrees'
    _UNKNOWN = 'unknown'
    _FEETTOMETRES = 0.3048
    _CMTOMETRES = 0.01
    _MMTOMETRES = 0.001
    _INCHESTOMETRES = 0.0254
    _YARDSTOMETRES = 0.91441
    _SQMILESTOSQMETRES = 2589988.1
    _ACRESTOSQMETRES = 4046.8564
    _SQMETRESTOSQFEET = 10.763910
    
    ## maximum number of features for adding data to rivs1 and subs1 files
    _RIVS1SUBS1MAX = 100000
    
    ## nearness threshold: proportion of size of DEM cell used to determine if two stream points should be considered to join
    # too large a threshold and very short stream segments can apparently be circular
    # too small and connected stream segments can appear to be disconnected
    _NEARNESSTHRESHOLD = 0.5
    
    # channel width and depth in metres are computed as multiplier * (A ** exponent)
    # where A is the drain area in sq km (area includes upstream subbasins for main channel,
    # current subbasin only for tributary channels)
    # Formulae from Srini 11/01/06
    _CHANNELWIDTHMULTIPLIER = 1.29
    _CHANNELWIDTHEXPONENT = 0.6
    _CHANNELDEPTHMULTIPLIER = 0.13
    _CHANNELDEPTHEXPONENT = 0.4
    
    # amount in metres to burn in streams (reduce height of DEM)
    _BURNINDEPTH = 50
    
    # percentage of upslope HRU drainage that goes to channel (or reservoir).  Remainder goes to floodplain LSU.
    _UPSLOPEHRUDRAIN = 90
    
    # minimum percentage of the drain area of a lake outlet channel to the lake area for it not to be absorbed into the lake
    _LAKEOUTLETCHANNELAREA = 1  #TODO: add to parameters form
    
    _MULTIPLIER = 1.0
    
    
    def __init__(self, gv):
        """Initialise class variables."""
        
        settings = QSettings()
        ## SWATPlus directory
        self.SWATPlusDir = settings.value('/QSWATPlus/SWATPlusDir', Parameters._SWATPLUSDEFAULTDIR)
        ## mpiexec directory
        self.mpiexecDir = settings.value('/QSWATPlus/mpiexecDir', Parameters._MPIEXECDEFAULTDIR)
        ## number of MPI processes
        self.numProcesses = settings.value('/QSWATPlus/NumProcesses', '')
        self._gv = gv
        self._dlg = ParametersDialog()
        self._dlg.setWindowFlags(self._dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        if self._gv:
            try:   # globals may have exited prematurely if SWATPlus directory not found and needs setting
                self._dlg.move(self._gv.parametersPos)
                ## flag showing if batch run
                self.isBatch = self._gv.isBatch
            except Exception:
               self.isBatch = False 
        else:
            self.isBatch = False
        
    def run(self):
        """Run the form."""
        self._dlg.checkUseMPI.stateChanged.connect(self.changeUseMPI)
        if os.path.isdir(self.mpiexecDir):
            self._dlg.checkUseMPI.setChecked(True)
        else:
            self._dlg.checkUseMPI.setChecked(False)
        self._dlg.MPIBox.setText(self.mpiexecDir)
        self._dlg.SWATPlusBox.setText(self.SWATPlusDir)
        self._dlg.SWATPlusButton.clicked.connect(self.chooseSWATPlusDir)
        self._dlg.MPIButton.clicked.connect(self.chooseMPIDir)
        self._dlg.cancelButton.clicked.connect(self._dlg.close)
        self._dlg.saveButton.clicked.connect(self.save)
        self._dlg.burninDepth.setValidator(QIntValidator())
        self._dlg.widthMult.setValidator(QDoubleValidator())
        self._dlg.widthExp.setValidator(QDoubleValidator())
        self._dlg.depthMult.setValidator(QDoubleValidator())
        self._dlg.depthExp.setValidator(QDoubleValidator())
        self._dlg.upslopeHRUDrain.setValidator(QIntValidator())
        self.readProj()
        self._dlg.pointSizeBox.valueChanged.connect(self.changeFontSize)
        if not self.isBatch:
            self._dlg.exec_()
        if self._gv:
            self._gv.parametersPos = self._dlg.pos()
        
    def changeUseMPI(self):
        """Enable form to allow MPI setting."""
        if self._dlg.checkUseMPI.isChecked():
            self._dlg.MPIBox.setEnabled(True)
            self._dlg.MPIButton.setEnabled(True)
            self._dlg.MPILabel.setEnabled(True)
        else:
            self._dlg.MPIBox.setEnabled(False)
            self._dlg.MPIButton.setEnabled(False)
            self._dlg.MPILabel.setEnabled(False)
        
    def save(self):
        """Save parameters and close form."""
        SWATPlusDir = self._dlg.SWATPlusBox.text()
        if SWATPlusDir == '' or not os.path.isdir(SWATPlusDir):
            QSWATUtils.error('Please select the SWATPlus directory', self.isBatch)
            return
        settings = QSettings()
        settings.setValue('/QSWATPlus/SWATPlusDir', SWATPlusDir)
#         dbProjTemplate =  QSWATUtils.join(Parameters._DBDIR, Parameters._DBPROJ)
#         if not os.path.exists(dbProjTemplate):
#             QSWATUtils.error('Cannot find the default project database {0}'.format(dbProjTemplate), self.isBatch)
#             return
#         dbRefTemplate =  QSWATUtils.join(Parameters._DBDIR, Parameters._DBREF)
#         if not os.path.exists(dbRefTemplate):
#             QSWATUtils.error('Cannot find the SWAT parameter database {0}'.format(dbRefTemplate), self.isBatch)
#             return
#         TauDEMDir = Parameters._TAUDEMDIR
#         if not os.path.isdir(TauDEMDir):
#             QSWATUtils.error('Cannot find the TauDEM directory {0}'.format(TauDEMDir), self.isBatch)
#             return   
        if self._dlg.checkUseMPI.isChecked():
            mpiexecDir = self._dlg.MPIBox.text()
            if mpiexecDir == '' or not os.path.isdir(mpiexecDir):
                QSWATUtils.error('Please select the MPI bin directory', self.isBatch)
                return
            mpiexec = Parameters._MPIEXEC
            mpiexecPath = QSWATUtils.join(mpiexecDir, mpiexec)
            if not os.path.exists(mpiexecPath):
                QSWATUtils.error('Cannot find mpiexec program {0}'.format(mpiexecPath), self.isBatch)
                return
        # no problems - save parameters
        if self._gv:
            if self._gv.SWATPlusDir == '':
                # failed earlier - need to restart project
                QSWATUtils.information('The project needs to be restarted: please click the Existing Project button', self.isBatch)    
                self._dlg.close()
                return
            self._gv.mpiexecPath = mpiexecPath if self._dlg.checkUseMPI.isChecked() else ''
            self._gv.SWATPlusDir = SWATPlusDir
        self.saveProj()
        if self._dlg.checkUseMPI.isChecked():
            settings.setValue('/QSWATPlus/mpiexecDir', mpiexecDir)
            if self.numProcesses == '': # no previous setting
                settings.setValue('/QSWATPlus/NumProcesses', '8')
        else:
            if self.numProcesses == '': # no previous setting
                settings.setValue('/QSWATPlus/NumProcesses', '0')
            self.numProcesses = '0'
        # careful about changing font size too much
        pointSize = self._dlg.pointSizeBox.value()
        if 8 <= pointSize <= 12:
            result = QMessageBox.Yes
        else:
            result = QSWATUtils.question('Are you sure you want to set the QSWATPlus point size to {0}?'.format(pointSize), self.isBatch, False)
        if result == QMessageBox.Yes:
            settings.setValue('/QSWATPlus/FontSize', str(pointSize))    
        self._dlg.close()
            
    def chooseSWATPlusDir(self):
        """Choose SWATPlus directory."""
        title = QSWATUtils.trans('Select SWATPlus directory')
        if self._dlg.SWATPlusBox.text() != '':
            startDir = os.path.split(self._dlg.SWATPlusBox.text())[0]
        elif os.path.isdir(self.SWATPlusDir):
            startDir = os.path.split(self.SWATPlusDir)[0]
        else:
            startDir = None
        dlg = QFileDialog(None, title)
        if startDir is not None:
            dlg.setDirectory(startDir)
        dlg.setFileMode(QFileDialog.Directory)
        if dlg.exec_():
            dirs = dlg.selectedFiles()
            SWATPlusDir = dirs[0]
            self._dlg.SWATPlusBox.setText(SWATPlusDir)
            self.SWATPlusDir = SWATPlusDir
            
    def chooseMPIDir(self):
        """Choose MPI directory."""
        title = QSWATUtils.trans('Select MPI bin directory')
        if self._dlg.MPIBox.text() != '':
            startDir = os.path.split(self._dlg.MPIBox.text())[0]
        elif os.path.isdir(self.mpiexecDir):
            startDir = os.path.split(self.mpiexecDir)[0]
        else:
            startDir = None
        dlg = QFileDialog(None, title)
        if startDir is not None:
            dlg.setDirectory(startDir)
        dlg.setFileMode(QFileDialog.Directory)
        if dlg.exec_():
            dirs = dlg.selectedFiles()
            mpiexecDir = dirs[0]
            self._dlg.MPIBox.setText(mpiexecDir)
            self.mpiexecDir = mpiexecDir
            
    def changeFontSize(self):
        """Change font size of this form.  Will also change font size of all QSWATPlus forms when parameters form saved."""
        ufont = QFont("Ubuntu", self._dlg.pointSizeBox.value(), 1)
        self._dlg.setFont(ufont)
        #=======================================================================
        # font = self._dlg.font()
        # family = font.family()
        # size = font.pointSize()
        # QSWATUtils.information('Family: {0}.  Point size: {1!s} (intended {2!s}).'.format(family, size, self._dlg.pointSizeBox.value()), False)
        #=======================================================================
        # this does not work for showing change in font: self._dlg.repaint()
        # instead just change one label
        self._dlg.pointSizeLabel.setFont(ufont)
        self._dlg.pointSizeLabel.repaint()
            
    def readProj(self):
        """Read parameter data from project file."""
        proj = QgsProject.instance()
        title = proj.title()
        burninDepth = proj.readNumEntry(title, 'params/burninDepth', Parameters._BURNINDEPTH)[0]
        self._dlg.burninDepth.setText(str(burninDepth))
        channelWidthMultiplier = proj.readDoubleEntry(title, 'params/channelWidthMultiplier', Parameters._CHANNELWIDTHMULTIPLIER)[0]
        self._dlg.widthMult.setText(str(channelWidthMultiplier))
        channelWidthExponent = proj.readDoubleEntry(title, 'params/channelWidthExponent', Parameters._CHANNELWIDTHEXPONENT)[0]
        self._dlg.widthExp.setText(str(channelWidthExponent))
        channelDepthMultiplier = proj.readDoubleEntry(title, 'params/channelDepthMultiplier', Parameters._CHANNELDEPTHMULTIPLIER)[0]
        self._dlg.depthMult.setText(str(channelDepthMultiplier))
        channelDepthExponent = proj.readDoubleEntry(title, 'params/channelDepthExponent', Parameters._CHANNELDEPTHEXPONENT)[0]
        self._dlg.depthExp.setText(str(channelDepthExponent))
        reachSlopeMultiplier = proj.readDoubleEntry(title, 'params/reachSlopeMultiplier', Parameters._MULTIPLIER)[0]
        self._dlg.reachSlopeMultiplier.setValue(reachSlopeMultiplier)
        tributarySlopeMultiplier = proj.readDoubleEntry(title, 'params/tributarySlopeMultiplier', Parameters._MULTIPLIER)[0]
        self._dlg.tributarySlopeMultiplier.setValue(tributarySlopeMultiplier)
        meanSlopeMultiplier = proj.readDoubleEntry(title, 'params/meanSlopeMultiplier', Parameters._MULTIPLIER)[0]
        self._dlg.meanSlopeMultiplier.setValue(meanSlopeMultiplier)
        mainLengthMultiplier = proj.readDoubleEntry(title, 'params/mainLengthMultiplier', Parameters._MULTIPLIER)[0]
        self._dlg.mainLengthMultiplier.setValue(mainLengthMultiplier)
        tributaryLengthMultiplier = proj.readDoubleEntry(title, 'params/tributaryLengthMultiplier', Parameters._MULTIPLIER)[0]
        self._dlg.tributaryLengthMultiplier.setValue(tributaryLengthMultiplier)
        upslopeHRUDrain = proj.readNumEntry(title, 'params/upslopeHRUDrain', Parameters._UPSLOPEHRUDRAIN)[0]
        self._dlg.upslopeHRUDrain.setText(str(upslopeHRUDrain))
        settings = QSettings()
        if settings.contains('/QSWATPlus/FontSize'):
            self._dlg.pointSizeBox.setValue(int(settings.value('/QSWATPlus/FontSize')))
        else:
            self._dlg.pointSizeBox.setValue(10)

    def saveProj(self):
        """Write parameter data to project file."""
        proj = QgsProject.instance()
        title = proj.title()
        proj.writeEntry(title, 'params/burninDepth', self._dlg.burninDepth.text())
        proj.writeEntry(title, 'params/channelWidthMultiplier', self._dlg.widthMult.text())
        proj.writeEntry(title, 'params/channelWidthExponent', self._dlg.widthExp.text())
        proj.writeEntry(title, 'params/channelDepthMultiplier', self._dlg.depthMult.text())
        proj.writeEntry(title, 'params/channelDepthExponent', self._dlg.depthExp.text())
        proj.writeEntry(title, 'params/reachSlopeMultiplier', self._dlg.reachSlopeMultiplier.text())
        proj.writeEntry(title, 'params/tributarySlopeMultiplier', self._dlg.tributarySlopeMultiplier.text())
        proj.writeEntry(title, 'params/meanSlopeMultiplier', self._dlg.meanSlopeMultiplier.text())
        proj.writeEntry(title, 'params/mainLengthMultiplier', self._dlg.mainLengthMultiplier.text())
        proj.writeEntry(title, 'params/tributaryLengthMultiplier', self._dlg.tributaryLengthMultiplier.text())
        upslopeHRUDrain = int(self._dlg.upslopeHRUDrain.text())
        if 0 <= upslopeHRUDrain <= 100:
            proj.writeEntry(title, 'params/upslopeHRUDrain', self._dlg.upslopeHRUDrain.text())
        proj.write()
        if self._gv is not None:
            self._gv.burninDepth = int(self._dlg.burninDepth.text())
            # update channel widths and depths in affected tables
            widthMult = float(self._dlg.widthMult.text())
            widthExp = float(self._dlg.widthExp.text())
            depthMult = float(self._dlg.depthMult.text())
            depthExp = float(self._dlg.depthExp.text())
            if abs(self._gv.channelWidthMultiplier - widthMult) > .005 \
                or abs(self._gv.channelWidthExponent - widthExp) > .005 \
                or abs(self._gv.channelDepthMultiplier - depthMult) > 0.005 \
                or abs(self._gv.channelDepthExponent - depthExp) > 0.005:
                self._gv.db.changeChannelWidthAndDepth(widthMult, widthExp, depthMult, depthExp, self._gv.shapesDir)
            self._gv.channelWidthMultiplier = widthMult
            self._gv.channelWidthExponent = widthExp
            self._gv.channelDepthMultiplier = depthMult
            self._gv.channelDepthExponent = depthExp
            # update slope values in affected tables
            # avoid real equality test
            if abs(self._gv.reachSlopeMultiplier - self._dlg.reachSlopeMultiplier.value()) > 0.05:
                self._gv.db.changeReachSlopes(self._dlg.reachSlopeMultiplier.value(), self._gv.reachSlopeMultiplier, self._gv.shapesDir)
            if abs(self._gv.tributarySlopeMultiplier - self._dlg.tributarySlopeMultiplier.value()) > 0.05:
                self._gv.db.changeTributarySlopes(self._dlg.tributarySlopeMultiplier.value(), self._gv.tributarySlopeMultiplier, self._gv.shapesDir)
            if abs(self._gv.meanSlopeMultiplier - self._dlg.meanSlopeMultiplier.value()) > 0.05:
                self._gv.db.changeMeanSlopes(self._dlg.meanSlopeMultiplier.value(), self._gv.meanSlopeMultiplier, self._gv.shapesDir)
            if abs(self._gv.mainLengthMultiplier - self._dlg.mainLengthMultiplier.value()) > 0.05:
                self._gv.db.changeMainLengths(self._dlg.mainLengthMultiplier.value(), self._gv.mainLengthMultiplier, self._gv.shapesDir)
            if abs(self._gv.tributaryLengthMultiplier - self._dlg.tributaryLengthMultiplier.value()) > 0.05:
                self._gv.db.changeTributaryLengths(self._dlg.tributaryLengthMultiplier.value(), self._gv.tributaryLengthMultiplier, self._gv.shapesDir)
            self._gv.reachSlopeMultiplier = self._dlg.reachSlopeMultiplier.value()
            self._gv.tributarySlopeMultiplier = self._dlg.tributarySlopeMultiplier.value()
            self._gv.meanSlopeMultiplier = self._dlg.meanSlopeMultiplier.value()
            self._gv.mainLengthMultiplier = self._dlg.mainLengthMultiplier.value()
            self._gv.tributaryLengthMultiplier = self._dlg.tributaryLengthMultiplier.value() 
            # update upslopeHRUDrain       
            upslopeHRUDrain = int(self._dlg.upslopeHRUDrain.text())
            if upslopeHRUDrain != self._gv.upslopeHRUDrain:
                if 0 <= upslopeHRUDrain <= 100:
                    self._gv.upslopeHRUDrain = upslopeHRUDrain
                    if self._gv.useLandscapes:
                        self._gv.db.changeUpslopeHRUDrain(upslopeHRUDrain)
                else:
                    QSWATUtils.error('Upslope HRU drain percent {0} is invalid - will be ignored'.format(upslopeHRUDrain), self._gv.isBatch)
