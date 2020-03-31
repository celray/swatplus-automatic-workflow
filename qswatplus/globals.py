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
from PyQt5.QtCore import * # @UnusedWildImport
from PyQt5.QtGui import * # @UnusedWildImport
from qgis.core import * # @UnusedWildImport
from qgis.gui import QgisInterface  # @UnresolvedImport
import os.path
# import xml.etree.ElementTree as ET
from typing import Dict, List, Set  # @UnusedImport

from .QSWATTopology import QSWATTopology
from .QSWATUtils import QSWATUtils
from .DBUtils import DBUtils
from .TauDEMUtils import TauDEMUtils
from .parameters import Parameters
from .raster import Raster  # @UnusedImport

class GlobalVars:
    """Data used across across the plugin, and some utilities on it."""
    def __init__(self, iface: QgisInterface, version: str, plugin_dir: str, isBatch: bool) -> None:
        """Initialise class variables."""
        settings = QSettings()
        if settings.contains('/QSWATPlus/SWATPlusDir'):
            SWATPlusDir = settings.value('/QSWATPlus/SWATPlusDir')
        else:
            SWATPlusDir = Parameters._SWATPLUSDEFAULTDIR
            if os.path.isdir(SWATPlusDir):
                settings.setValue('/QSWATPlus/SWATPlusDir', Parameters._SWATPLUSDEFAULTDIR)
        if not os.path.isdir(SWATPlusDir):
            QSWATUtils.error('''Cannot find SWATPlus directory, expected to be {0}.
Please use the Parameters form to set its location.'''.format(SWATPlusDir), isBatch)
            self.SWATPlusDir = ''
            return
        ## SWATPlus directory
        self.SWATPlusDir = SWATPlusDir
        ## Directory containing QSWAT plugin
        self.plugin_dir = plugin_dir
        ## Databases directory: part of plugin
        # containing template project and reference databases, plus soil database for STATSGO and SSURGO
        self.dbPath = QSWATUtils.join(self.SWATPlusDir, Parameters._DBDIR)
        ## Path of template project database
        self.dbProjTemplate =  QSWATUtils.join(self.dbPath, Parameters._DBPROJ)
        ## Path of template reference database
        self.dbRefTemplate = QSWATUtils.join(self.dbPath, Parameters._DBREF)
        ## Directory of TauDEM executables
        self.TauDEMDir = TauDEMUtils.findTauDEMDir(settings, not isBatch)
        ## Path of mpiexec
        self.mpiexecPath = TauDEMUtils.findMPIExecPath(settings)
        proj = QgsProject.instance()
        title = proj.title()
        ## QGIS interface
        self.iface = iface
        ## Stream burn-in depth
        self.burninDepth = proj.readNumEntry(title, 'params/burninDepth', Parameters._BURNINDEPTH)[0]
        ## Channel width multiplier
        self.channelWidthMultiplier = proj.readDoubleEntry(title, 'params/channelWidthMultiplier', Parameters._CHANNELWIDTHMULTIPLIER)[0]
        ## Channel width exponent
        self.channelWidthExponent = proj.readDoubleEntry(title, 'params/channelWidthExponent', Parameters._CHANNELWIDTHEXPONENT)[0]
        ## Channel depth multiplier
        self.channelDepthMultiplier = proj.readDoubleEntry(title, 'params/channelDepthMultiplier', Parameters._CHANNELDEPTHMULTIPLIER)[0]
        ## Channel depth exponent
        self.channelDepthExponent = proj.readDoubleEntry(title, 'params/channelDepthExponent', Parameters._CHANNELDEPTHEXPONENT)[0]
        ## reach slope multiplier
        self.reachSlopeMultiplier = proj.readDoubleEntry(title, 'params/reachSlopeMultiplier', Parameters._MULTIPLIER)[0]
        ## tributary slope multiplier
        self.tributarySlopeMultiplier = proj.readDoubleEntry(title, 'params/tributarySlopeMultiplier', Parameters._MULTIPLIER)[0]
        ## mean slope multiplier
        self.meanSlopeMultiplier = proj.readDoubleEntry(title, 'params/meanSlopeMultiplier', Parameters._MULTIPLIER)[0]
        ## main length multiplier
        self.mainLengthMultiplier = proj.readDoubleEntry(title, 'params/mainLengthMultiplier', Parameters._MULTIPLIER)[0]
        ## tributary length multiplier
        self.tributaryLengthMultiplier = proj.readDoubleEntry(title, 'params/tributaryLengthMultiplier', Parameters._MULTIPLIER)[0]
        ## upslope HRU drain percent
        self.upslopeHRUDrain = proj.readNumEntry(title, 'params/upslopeHRUDrain', Parameters._UPSLOPEHRUDRAIN)[0]
        ## Index of slope group in Layers panel
        self.slopeGroupIndex = -1
        ## Index of landuse group in Layers panel
        self.landuseGroupIndex = -1
        ## Index of soil group in Layers panel
        self.soilGroupIndex = -1
        ## Index of watershed group in Layers panel
        self.watershedGroupIndex = -1
        ## Index of results group in Layers panel
        self.resultsGroupIndex = -1
        ## Index of animation group in Layers panel
        self.animationGroupIndex = -1
        ## Flag showing if using existing watershed
        self.existingWshed = False
        ## Flag showing if using grid model
        self.useGridModel = False
        ## flag to show if using landscape units
        self.useLandscapes = False
        ## flag to show if dividing into left/right/headwater landscape units
        self.useLeftRight = False
        ## Path of DEM raster
        self.demFile = ''
        ## Path of filled DEM raster
        self.felFile = ''
        ## Path of stream burn-in shapefile
        self.burnFile = ''
        ## Path of DEM after burning-in
        self.burnedDemFile = ''
        ## Path of D8 flow direction raster
        self.pFile = ''
        ## Path of D8 flow accumulation raster
        self.ad8File = ''
        ## Path of subbasins raster
        self.basinFile = ''
        ## path of channel basins raster
        self.channelBasinFile = ''
        ## path of channel basins file with lakes masked out
        self.chBasinNoLakeFile = ''
        ## Path of channel raster
        self.srcChannelFile = ''
        ## Path of valleyDepthsFile
        # value at each point in this raster is the drop in metres
        # from the point to where its D8 flow path meets a channel
        # Channel elevations are measured at points adjacent to the channel
        # to avoid problems caused by burning-in
        self.valleyDepthsFile = ''
        ## Path of outlets shapefile
        self.outletFile = ''
        ## path of snapped outlets file
        self.snapFile = ''
        ## Path of outlets shapefile for extra reservoirs and point sources
        self.extraOutletFile = ''
        ## Path of stream shapefile
        self.streamFile = ''
        ## Path of stream shapefile calculated by delineation
        # since streamFile is set to streams from grid when using a grid model
        self.delinStreamFile = ''
        ## Path of channel shapefile
        self.channelFile = ''
        ## Path of subbasins shapefile or grid file when using grids
        self.subbasinsFile = ''
        ## Path of watershed shapefile: shows channel basins.  Not used with grid models.
        self.wshedFile = ''
        ## Path of file like D8 contributing area but with heightened values at subbasin outlets
        self.hd8File = ''
        ## Path of distance to stream outlets raster
        self.distStFile = ''
        ## Path of distance to channel raster
        self.distChFile = ''
        ## Path of slope raster
        self.slopeFile = ''
        ## path of lakes shapefile
        self.lakeFile = ''
        ## Path of slope bands raster
        self.slopeBandsFile = ''
        ## Path of landuse raster
        self.landuseFile = ''
        ## Path of soil raster
        self.soilFile = ''
        ## path of floodplain raster
        self.floodFile = ''
        ## Nodata value for DEM
        self.elevationNoData = 0
        ## DEM horizontal block size
        self.xBlockSize = 0
        ## DEM vertical block size
        self.yBlockSize = 0
        ## Nodata value for basins raster
        self.basinNoData = 0
        ## Nodata value for distance to outlets raster
        self.distStNoData = 0
        ## Nodata value for distance to channel raster
        self.distChNoData = 0
        ## Nodata value for slope raster
        self.slopeNoData = 0
        ## Nodata value for landuse raster
        self.cropNoData = 0
        ## Nodata value for soil raster
        self.soilNoData = 0
        ## Nodata value for floodplain raster
        self.floodNoData = -1 
        ## Area of DEM cell in square metres
        self.cellArea = 0.0
        ## channel threshold in square metres
        self.channelThresholdArea = 10000000 # 1000 hectares default
        ## gridSize as count of DEM cells per side (grid model only)
        self.gridSize = 0
        ## list of landuses exempt from HRU removal
        self.exemptLanduses: List[str] = []
        ## table of landuses being split
        self.splitLanduses: Dict[str, Dict[str, float]] = dict()
        ## Elevation bands threshold in metres
        self.elevBandsThreshold = 0
        ## Number of elevation bands
        self.numElevBands = 0
        ## Topology object
        self.topo = QSWATTopology(isBatch)
        projFile = proj.fileName()
        projPath = QFileInfo(projFile).canonicalFilePath()
        pdir, base = os.path.split(projPath)
        ## Project name
        self.projName = os.path.splitext(base)[0]
        ## Project directory
        self.projDir = pdir
        ## QSWAT+ version
        self.version = version
        ## DEM directory
        self.demDir = ''
        ## Landuse directory
        self.landuseDir = ''
        ## Soil directory
        self.soilDir = ''
        ## Landscape directory
        self.landscapeDir = ''
        ## Floodplain directory
        self.floodDir = ''
        ## text directory
        self.textDir = ''
        ## Rasters directory
        self.rastersDir = ''
        ## Shapes directory
        self.shapesDir = ''
        ## Scenarios directory
        self.scenariosDir = ''
        ## Results directory
        self.resultsDir = ''
        ## Plots directory
        self.plotsDir = ''
        ## png directory for storing png images used to create animation videos
        self.pngDir = ''
        ## animation directory for storing animation files
        self.animationDir = ''
        self.createSubDirectories()
        ## path of full lsus shapefile
        self.fullLSUsFile = QSWATUtils.join(self.shapesDir, Parameters._LSUS1 + '.shp')
        ## path of actual lsus shapefile (after channel mergers
        self.actLSUsFile = QSWATUtils.join(self.shapesDir, Parameters._LSUS2 + '.shp')
        ## Path of FullHRUs shapefile
        self.fullHRUsFile = QSWATUtils.join(self.shapesDir, Parameters._HRUS1 + '.shp')
        ## Path of ActHRUs shapefile
        self.actHRUsFile = QSWATUtils.join(self.shapesDir, Parameters._HRUS2 + '.shp')
        ## Flag to show if running in batch mode
        self.isBatch = isBatch
        ## Path of project database
        self.db = DBUtils(self.projDir, self.projName, self.dbProjTemplate, self.dbRefTemplate, self.isBatch)
        ## multiplier to turn elevations to metres
        self.verticalFactor = 1
        ## vertical units
        self.verticalUnits = Parameters._METRES
        # positions of sub windows
        ## Position of delineation form
        self.delineatePos = QPoint(0, 100)
        ## Position of HRUs form
        self.hrusPos = QPoint(0, 100)
        ## Position of parameters form
        self.parametersPos = QPoint(50, 100)
        ## Position of landscape form
        self.landscapePos = QPoint(50, 80)
        ## Position of select subbasins form
        self.selectSubsPos = QPoint(50, 100)
        ## Position of select reservoirs form
        self.selectResPos = QPoint(50, 100)
        ## Position of about form
        self.aboutPos = QPoint(50, 100)
        ## Position of elevation bands form
        self.elevationBandsPos = QPoint(50, 100)
        ## Position of split landuses form
        self.splitPos = QPoint(50, 100)
        ## Position of select landuses form
        self.selectLuPos = QPoint(50, 100)
        ## Position of exempt landuses form
        self.exemptPos = QPoint(50, 100)
        ## Position of outlets form
        self.outletsPos = QPoint(50, 100)
        ## Position of select outlets file form
        self.selectOutletFilePos = QPoint(50, 100)
        ## Position of select outlets form
        self.selectOutletPos = QPoint(50, 100)
        ## Position of visualise form
        self.visualisePos = QPoint(0, 100)
        ## rasters open that need to be closed if memory exception occurs
        self.openRasters: Set[Raster] = set()
        ## will set to choice made when converting from ArcSWAT, if that was how the project file was created
        # 0: Full
        # 1: Existing
        # 2: No GIS
        # NB These values are defined in convertFromArc.py
        self.fromArcChoice = -1
        
    def createSubDirectories(self):
        """Create subdirectories under project file's directory."""
        if not os.path.exists(self.projDir):
            os.makedirs(self.projDir)
        watershedDir = QSWATUtils.join(self.projDir, 'Watershed')
        if not os.path.exists(watershedDir):
            os.makedirs(watershedDir)
        rastersDir = QSWATUtils.join(watershedDir, 'Rasters')
        if not os.path.exists(rastersDir):
            os.makedirs(rastersDir)
        self.demDir = QSWATUtils.join(rastersDir, 'DEM')
        if not os.path.exists(self.demDir):
            os.makedirs(self.demDir)
        self.soilDir = QSWATUtils.join(rastersDir, 'Soil')
        if not os.path.exists(self.soilDir):
            os.makedirs(self.soilDir)
        self.landuseDir = QSWATUtils.join(rastersDir, 'Landuse')
        if not os.path.exists(self.landuseDir):
            os.makedirs(self.landuseDir)
        self.landscapeDir = QSWATUtils.join(rastersDir, 'Landscape')
        if not os.path.exists(self.landscapeDir):
            os.makedirs(self.landscapeDir)    
        self.floodDir = QSWATUtils.join(self.landscapeDir, 'Flood')
        if not os.path.exists(self.floodDir):
            os.makedirs(self.floodDir)
        self.scenariosDir = QSWATUtils.join(self.projDir, 'Scenarios')
        if not os.path.exists(self.scenariosDir):
            os.makedirs(self.scenariosDir)
        defaultDir = QSWATUtils.join(self.scenariosDir, 'Default')
        if not os.path.exists(defaultDir):
            os.makedirs(defaultDir)
        txtInOutDir = QSWATUtils.join(defaultDir, 'TxtInOut')
        if not os.path.exists(txtInOutDir):
            os.makedirs(txtInOutDir)
        self.resultsDir = QSWATUtils.join(defaultDir, Parameters._RESULTS)
        if not os.path.exists(self.resultsDir):
            os.makedirs(self.resultsDir)
        self.plotsDir = QSWATUtils.join(self.resultsDir, Parameters._PLOTS)
        if not os.path.exists(self.plotsDir):
            os.makedirs(self.plotsDir)
        self.animationDir = QSWATUtils.join(self.resultsDir, Parameters._ANIMATION)
        if not os.path.exists(self.animationDir):
            os.makedirs(self.animationDir)
        self.pngDir = QSWATUtils.join(self.animationDir, Parameters._PNG)
        if not os.path.exists(self.pngDir):
            os.makedirs(self.pngDir)
        self.textDir = QSWATUtils.join(watershedDir, 'Text')
        if not os.path.exists(self.textDir):
            os.makedirs(self.textDir)
        self.shapesDir = QSWATUtils.join(watershedDir, 'Shapes')
        if not os.path.exists(self.shapesDir):
            os.makedirs(self.shapesDir)
            
    def setVerticalFactor(self):
        """Set vertical conversion factor according to vertical units."""
        if self.verticalUnits == Parameters._METRES:
            self.verticalFactor = 1
        elif self.verticalUnits == Parameters._FEET:
            self.verticalFactor = Parameters._FEETTOMETRES
        elif self.verticalUnits == Parameters._CM:
            self.verticalFactor = Parameters._CMTOMETRES
        elif self.verticalUnits == Parameters._MM:
            self.verticalFactor = Parameters._MMTOMETRES
        elif self.verticalUnits == Parameters._INCHES:
            self.verticalFactor = Parameters._INCHESTOMETRES
        elif self.verticalUnits == Parameters._YARDS:
            self.verticalFactor = Parameters._YARDSTOMETRES
     
    def isExempt(self, landuseId):
        """Return true if landuse is exempt 
        or is part of a split of an exempt landuse.
        """
        landuse = self.db.getLanduseCode(landuseId)
        if landuse in self.exemptLanduses:
            return True
        for landuse1, subs in self.splitLanduses.items():
            if landuse1 in self.exemptLanduses and landuse in subs:
                return True
        return False
    
    def saveExemptSplit(self):
        """Save landuse exempt and split details in project database."""
        exemptTable = 'gis_landexempt'
        splitTable = 'gis_splithrus'
        with self.db.conn as conn:
            if not conn:
                return False
            cursor = conn.cursor()
            clearSql = 'DROP TABLE IF EXISTS {0}'
            cursor.execute(clearSql.format(exemptTable))
            cursor.execute(self.db._LANDEXEMPTCREATESQL)
            for landuse in self.exemptLanduses:
                cursor.execute(self.db._LANDEXEMPTINSERTSQL, (landuse,))
            cursor.execute(clearSql.format(splitTable))
            cursor.execute(self.db._SPLITHRUSCREATESQL)
            for landuse, subs in self.splitLanduses.items():
                for sublanduse, percent in subs.items():
                    cursor.execute(self.db._SPLITHRUSINSERTSQL, (landuse, sublanduse, percent))
            conn.commit()
            self.db.hashDbTable(conn, exemptTable)
            self.db.hashDbTable(conn, splitTable)
        return True
        
    def getExemptSplit(self):
        """Get landuse exempt and split details from project database."""
        # in case called twice
        self.exemptLanduses = []
        self.splitLanduses = dict()
        exemptTable = 'gis_landexempt'
        splitTable = 'gis_splithrus'
        # allow for old database
        if self.db.hasTable(self.db.dbFile, exemptTable) and self.db.hasTable(self.db.dbFile, splitTable):
            with self.db.conn as conn:
                if not conn:
                    return
                cursor = conn.cursor()
                sql = self.db.sqlSelect(exemptTable, 'landuse', '', '')
                for row in cursor.execute(sql):
                    self.exemptLanduses.append(row['landuse'])
                sql = self.db.sqlSelect(splitTable, 'landuse, sublanduse, percent', '', '')
                for row in cursor.execute(sql):
                    landuse = row['landuse']
                    if landuse not in self.splitLanduses:
                        self.splitLanduses[landuse] = dict()
                    self.splitLanduses[landuse][row['sublanduse']] = int(row['percent'])
                
    def populateSplitLanduses(self, combo):
        """Put currently split landuse codes into combo."""
        for landuse in self.splitLanduses.keys():
            combo.addItem(landuse)
               
    def writeProjectConfig(self, doneDelin, doneHRUs):
        """
        Write information to project_config table.
         
        done parameters may be -1 (leave as is) 0 (not done, initial default) or 1 (done)
        """
        with self.db.conn as conn:
            if conn is None:
                return
            cur = conn.cursor()
            table = 'project_config'
            proj = QgsProject.instance()
            projectName = self.projName
            projectDirectory = self.projDir
            projectDb = proj.writePath(self.db.dbFile)  # relativise to project directory
            referenceDb = proj.writePath(self.db.dbRefFile)
            # only need to set weather data directory if weather data stored by conversion from ArcSWAT
            weatherDataDir = proj.writePath(os.path.join(self.scenariosDir, r'Default\TxtInOut'))  if self.fromArcChoice >= 0 else None 
            gisType = 'qgis'
            gisVersion = self.version
            row = cur.execute(self.db.sqlSelect(table, '*', '', '')).fetchone()
            if row is not None:
                if doneDelin == -1:
                    doneDelinNum = row['delineation_done']
                else:
                    doneDelinNum = doneDelin
                if doneHRUs == -1:
                    doneHRUsNum = row['hrus_done']
                else:
                    doneHRUsNum = doneHRUs
                # always update version in case running old project
                sql = 'UPDATE ' + table + ' SET gis_version=?,delineation_done=?,hrus_done=?'
                cur.execute(sql, (gisVersion, doneDelinNum, doneHRUsNum))
            else:
                if doneDelin == -1:
                    doneDelinNum = 0
                else:
                    doneDelinNum = doneDelin
                if doneHRUs == -1:
                    doneHRUsNum = 0
                else:
                    doneHRUsNum = doneHRUs
                cur.execute('DROP TABLE IF EXISTS {0}'.format(table))
                cur.execute(DBUtils._CREATEPROJECTCONFIG)
                cur.execute(DBUtils._INSERTPROJECTCONFIG, 
                            (1, projectName, projectDirectory, None, 
                            gisType, gisVersion, projectDb, referenceDb, None, None, weatherDataDir, None, None, None, None, 
                            doneDelinNum, doneHRUsNum, DBUtils._SOILS_SOL_NAME, DBUtils._SOILS_SOL_LAYER_NAME,
                            None, 0, 0))
            conn.commit()
  
    def isDelinDone(self):
        """Return true if delineation done according to project_config table."""
        with self.db.conn as conn:
            if not conn:
                return False
            table = 'project_config'
            try:
                row = conn.execute(self.db.sqlSelect(table, 'delineation_done', '', '')).fetchone()
            except Exception:
                return False
            if row is None:
                return False
            else:
                return int(row['delineation_done']) == 1
                    
    def isHRUsDone(self):
        """Return true if HRU creation is done according to project_config table."""
        with self.db.conn as conn:
            if not conn:
                return False
            table = 'project_config'
            try:
                row = conn.execute(self.db.sqlSelect(table, 'hrus_done', '', '')).fetchone()
            except Exception:
                return False
            if row is None:
                return False
            else:
                return int(row['hrus_done']) == 1
            
    def findSWATPlusEditor(self):
        """Return path to SWAT+ editor, looking first in current setting, then according to registry settings, then in user's home directory."""
        editorDir1 = QSWATUtils.join(self.SWATPlusDir, Parameters._SWATEDITORDIR)
        editor1 = QSWATUtils.join(editorDir1, Parameters._SWATEDITOR)
        if os.path.exists(editor1):
            return editor1
        settings = QSettings()
        SWATPlusDir = settings.value('/QSWATPlus/SWATPlusDir', Parameters._SWATPLUSDEFAULTDIR)
        editorDir2 = QSWATUtils.join(SWATPlusDir, Parameters._SWATEDITORDIR)
        editor2 = QSWATUtils.join(editorDir2, Parameters._SWATEDITOR)
        if os.path.exists(editor2):
            return editor2
        if Parameters._ISWIN:
            QSWATUtils.information(r'''Cannot find {0} in {1} or {2}.  
Have you installed SWAT+ as a different directory from C:\SWAT\SWATPlus?
If so use the QSWAT+ Parameters form to set the correct location.'''
                               .format(Parameters._SWATEDITOR, editorDir1, editorDir2), self.isBatch)
        else:
            QSWATUtils.information('''Cannot find {0} in {1} or {2}.  
Have you installed SWATPlus?'''
                               .format(Parameters._SWATEDITOR, editorDir1, editorDir2), self.isBatch)
        return None
            
    # old stuff from QSWAT        
#     def setSWATEditorParams(self):  # TODO: when SWATPlus editor designed
#         """Save SWAT Editor initial parameters in its configuration file."""
#         return # TODO: nothing at present
#         path = QSWATUtils.join(self.SWATEditorDir, Parameters._SWATEDITOR) + '.config'
#         tree = ET.parse(path)
#         root = tree.getroot()
#         projDbKey = 'SwatEditor_ProjGDB'
#         refDbKey = 'SwatEditor_SwatGDB'
#         soilDbKey = 'SwatEditor_SoilsGDB'
#         exeKey = 'SwatEditor_SwatEXE'
#         for item in root.iter('add'):
#             key = item.get('key')
#             if key == projDbKey:
#                 item.set('value', self.db.dbFile)
#             elif key == refDbKey:
#                 item.set('value', self.db.dbRefFile)
#             elif key == soilDbKey:
#                 soilDb = Parameters._SOILDB
#                 item.set('value', QSWATUtils.join(self.dbPath, soilDb))
#             elif key == exeKey:
#                 item.set('value', self.SWATEditorDir + '/')
#         tree.write(path)
        
    def closeOpenRasters(self):
        """Close open rasters (to enable them to be reopened with new chunk size)."""
        for raster in self.openRasters.copy():
            try:
                raster.close()
                self.openRasters.discard(raster)
            except Exception:
                pass  

    def clearOpenRasters(self):
        """Clear list of open rasters."""
        self.openRasters.clear()
