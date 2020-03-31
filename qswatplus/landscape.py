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
 
 ***************************************************************************
 Acknowledgement: this code was inspired by the Hillslopes module of the 
 WhiteBox toolset of John Lindsay: 
          http://www.uoguelph.ca/~hydrogeo/Whitebox/index.html
 ***************************************************************************
"""
# Import the PyQt and QGIS libraries
from PyQt5.QtCore import *  # @UnusedWildImport
from PyQt5.QtGui import *  # @UnusedWildImport
from PyQt5.QtWidgets import *  # @UnusedWildImport
from qgis.core import *  # @UnusedWildImport
from qgis.gui import *  # @UnusedWildImport 
from qgis.analysis import QgsRasterCalculator, QgsRasterCalculatorEntry  # @UnresolvedImport
import os.path
import subprocess
import time
from osgeo import gdal

from .TauDEMUtils import TauDEMUtils
from .QSWATTopology import QSWATTopology
from .QSWATUtils import QSWATUtils, FileTypes
from .landscapedialog import LandscapeDialog
from .floodplain import Floodplain
from .parameters import Parameters
from .raster import Raster


class Landscape(QObject):
    
    """
    Generate raster  of left and right hillslopes plus headwater area from channel raster  and d8 flow directions.
    Also generate raster  of floodplain/upslope areas.
    """
    
    def __init__(self, gv, taudemOutput, numProcesses, progress):
        """Initialise class variables."""
        QObject.__init__(self)
        self._gv = gv
        self._dlg = LandscapeDialog()
        self._dlg.setWindowFlags(self._dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint & Qt.WindowMinimizeButtonHint)
        self._dlg.move(self._gv.landscapePos)
        ## TauDEM output buffer
        self.taudemOutput = taudemOutput
        ## number of MPI processes to use
        self.numProcesses = numProcesses
        ## progress report function
        self._progress = progress
        ## flag set to true if must run even if files seem to be up to date
        self.mustRun = False
        ## channel accumulation threshold
        self.channelThresh = 0
        ## ridge accumulation threshold
        self.ridgeThresh = 0
        ## branch length threshold
        self.branchThresh = 0
        ## Slope position threshold 
        self.floodThresh = 0
        ## clipper file: file used for clipping
        self.clipperFile = ''
        ## number of chunks to use for rasters and their arrays; increased when memory fails
        self.chunkCount = 1
        ## raster  transform
        self.transform = None
        ## channels raster 
        self.channelsRaster = None
        ## output raster  no data value 
        self.noData = -32768
        ## raster  projection
        self.projection = None
        ## clipped filled DEM raster 
        self.demRaster = None
        ## clipped flow raster 
        self.flowRaster = None
        ## number of rows in output raster 
        self.numRows = 0
        ## number of columns in output rastert
        self.numCols = 0
        ## identifier number for reaches
        self.reachIdentifier = 0
        ## map of (row, col) to (ident, isHead) for points which are channel heads or starts of reaches
        self.heads = None
        ## map of (row, col) to (6*ident, elev) for head point, (6*ident + 2, elev) on left, (6*ident + 4, elev) on right of points draining directly to channel reaches
        self.sides = None
        ## valley depths raster 
        self.valleyDepthsRaster = None
        ## hillslope raster 
        self.hillslopeRaster = None
        ## FloodPlain object
        self.FP = None
        ## area of DEM cell in currently chosen units
        self.areaOfCell = 0
        ## flag to show area being changed to prevent loop between setting cells and setting area
        self.changing = False
        
    def init(self):
        """Set connections to controls."""
        # for now hillslopes not available, and form will assume floodplain
        self._dlg.hillslopesCheckBox.setVisible(False)
        self._dlg.floodplainCheckBox.setVisible(False)
        # self._dlg.hillslopesCheckBox.stateChanged.connect(self.hillslopesCheck)
        # self._dlg.floodplainCheckBox.stateChanged.connect(self.floodplainCheck)
        self._dlg.ridgeThresholdCells.setValidator(QIntValidator())
        self._dlg.ridgeThresholdCells.textChanged.connect(self.setRidgeArea)
        self._dlg.ridgeThresholdArea.textChanged.connect(self.setRidgeCells)
        self._dlg.ridgeThresholdArea.setValidator(QDoubleValidator())
        self._dlg.areaUnitsBox.addItem(Parameters._SQKM)
        self._dlg.areaUnitsBox.addItem(Parameters._HECTARES)
        self._dlg.areaUnitsBox.addItem(Parameters._SQMETRES)
        self._dlg.areaUnitsBox.addItem(Parameters._SQMILES)
        self._dlg.areaUnitsBox.addItem(Parameters._ACRES)
        self._dlg.areaUnitsBox.addItem(Parameters._SQFEET)
        self._dlg.areaUnitsBox.activated.connect(self.changeRidgeArea)
        self._dlg.methodTab.currentChanged.connect(self.methodTabCheck)
        self._dlg.branchThreshold.textChanged.connect(self.parameterChange)
        self._dlg.branchThreshold.setValidator(QDoubleValidator())
        self._dlg.createButton.clicked.connect(self.generate)
        self._dlg.doneButton.clicked.connect(self.cancel)
        # if distances to outlets not generated (eg existing watershed) then branch method is not available
        if not os.path.exists(self._gv.distStFile):
            self._dlg.methodTab.setTabEnabled(2, False)
        
    def run(self, numCellsSt, channelThresh, branchThresh, clipperFile, mustRun):
        """Run landscape using filled dem, channels, d8Flow and either 
        ridgep and ridges rasters, or subbasins and distances rasters."""
        self.init()
        self._dlg.bufferMultiplier.setValue(10)  # typical value
        # use channel threshold as default for ridge threshold
        self._dlg.areaUnitsBox.setCurrentIndex(0)  # square km
        self.channelThresh = channelThresh
        self._dlg.ridgeThresholdCells.setText(str(numCellsSt))
        self.changeRidgeArea()
        self._dlg.branchThreshold.setText(str(branchThresh))
        self.clipperFile = clipperFile
        self._dlg.slopePositionSpinBox.setValue(0.1)  # typical value
        self._dlg.methodTab.setCurrentIndex(1)  # default method is inverted DEM
        self.methodTabCheck()
        self.mustRun = mustRun
        self._dlg.show()
        self._dlg.exec_()
        self._gv.landscapePos = self._dlg.pos()
        return 0
    
    def setAreaOfCell(self):
        """Set area of cell in currently selected area units."""
        areaSqM = float(self._gv.topo.dx * self._gv.topo.dy)
        self.areaOfCell = areaSqM
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
            
    def setRidgeArea(self):
        """Update area threshold display."""
        if self.changing: return
        try:
            numCells = float(self._dlg.ridgeThresholdCells.text())
        except Exception:
            # not currently parsable - ignore
            return
        area = numCells * self.areaOfCell
        self.changing = True
        self._dlg.ridgeThresholdArea.setText('{0:.4G}'.format(area))
        self.changing = False
        self.parameterChange()
            
    def setRidgeCells(self):
        """Update number of cells threshold display."""
        if self.changing: return
        # prevent division by zero
        if self.areaOfCell == 0: return
        try:
            area = float(self._dlg.ridgeThresholdArea.text())
        except Exception:
            # not currently parsable - ignore
            return
        numCells = int(area / self.areaOfCell)
        self.changing = True
        self._dlg.ridgeThresholdCells.setText(str(numCells))
        self.changing = False
        self.parameterChange()
    
    def changeRidgeArea(self):
        """Set area of cell and update area threshold display."""
        self.setAreaOfCell()
        self.setRidgeArea()
        
    def clipRaster(self, inFile, clipperFile, root):
        """
        Clip inFile with clipperFile.  Return clipped file, plus flag True if generated.
        
        This makes floodplain calculation much faster.
        Note there might seem little need to clip other rasters as they are only read where DEM has data
        but in fact is a bit faster - perhaps because of reduced storage.
        Also if we clip all files with same shapefile we can use common (row, col) indexes to arrays when we read them.
        """
        isNewFile = False
        base, suffix = os.path.splitext(inFile)
        clipFile = base + 'clip' + suffix
        # originally used convex hull to clip because of gdalwarp problems,
        # but now use GDALWARP_IGNORE_BAD_CUTLINE flag to prevent these
#         base, suffix = os.path.splitext(clipperFile)
#         hullFile = base + 'hull' + suffix
        if self.mustClip(clipperFile, inFile, clipFile):
            if os.path.exists(clipFile):
                QSWATUtils.tryRemoveLayerAndFiles(clipFile, root)
            command = 'gdalwarp --config GDALWARP_IGNORE_BAD_CUTLINE YES -dstnodata {3} -q -overwrite -cutline "{0}" -crop_to_cutline -of GTiff "{1}" "{2}"'.format(clipperFile, inFile, clipFile, self.noData)
            proc = subprocess.run(command,  # @UnusedVariable
                                    shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    universal_newlines=True)    # text=True) only in python 3.7
            #for line in  proc.stdout.split('\n'):
            #    QSWATUtils.loginfo(line)
            QSWATUtils.copyPrj(inFile, clipFile)
            assert os.path.exists(clipFile), 'Failed to create clipped raster  {2} by clipping {0} with {1}'.format(inFile, clipperFile, clipFile)
            # gdalwarp can leave file untouched if it already existed, so we (effectively) touch it
            os.utime(clipFile, None)
            isNewFile = True
        return clipFile, isNewFile
            
    def calcHillslopes(self, channelThresh, clipperFile, root):
        """Generate hillslopes and valley depths rasters."""
        # channelThresh needed in spite of being module variable since can be called directly from delineation
        # clipperFile similarly enables original subbasins shapefile to be used for grids
        
        base, suffix = os.path.splitext(self._gv.demFile)
        if not os.path.exists(self._gv.felFile):
            QSWATUtils.error('Cannot find pit filled DEM {0}'.format(self._gv.felFile), self._gv.isBatch)
            return False
        if self._gv.useGridModel and self._gv.srcChannelFile == '':
            self.makeSrcChannelRaster(channelThresh, root)
        if not os.path.exists(self._gv.srcChannelFile):
            QSWATUtils.error('Cannot find channels raster {0}'.format(self._gv.srcChannelFile), self._gv.isBatch)
            return False
        self._dlg.setCursor(Qt.WaitCursor)
        dem, isNew = self.clipRaster(self._gv.felFile, clipperFile, root)
        self.mustRun = self.mustRun or isNew
        channels, isNew = self.clipRaster(self._gv.srcChannelFile, clipperFile, root)
        self.mustRun = self.mustRun or isNew
        d8Flow, isNew = self.clipRaster(self._gv.pFile, clipperFile, root)
        self.mustRun = self.mustRun or isNew
        gdal.AllRegister()
        self._gv.valleyDepthsFile = base + 'depths' + suffix
        self._gv.clearOpenRasters()
        completed = False
        while not completed:
            try:
                # safer to mark complete immediately to avoid danger of endless loop
                # only way to loop is then the memory error exception being raised 
                completed = True
                self.demRaster = Raster(dem, self._gv, canWrite=False, isInt=False)
                res = self.demRaster.open(self.chunkCount)
                if not res:
                    return False
                self.numRows = self.demRaster.numRows
                self.numCols = self.demRaster.numCols
                self.transform = self.demRaster.ds.GetGeoTransform()
                self.projection = self.demRaster.ds.GetProjection()
                hillslopeFile = base + 'slopes' + suffix
                if self.mustRun or \
                    not QSWATUtils.isUpToDate(dem, self._gv.valleyDepthsFile) or \
                    not QSWATUtils.isUpToDate(channels, self._gv.valleyDepthsFile) or \
                    not QSWATUtils.isUpToDate(d8Flow, self._gv.valleyDepthsFile) or \
                    not QSWATUtils.isUpToDate(dem, hillslopeFile) or \
                    not QSWATUtils.isUpToDate(channels, hillslopeFile) or \
                    not QSWATUtils.isUpToDate(d8Flow, hillslopeFile):
                    self.channelsRaster = Raster(channels, self._gv, canWrite=False, isInt=True)
                    res = self.channelsRaster.open(self.chunkCount)
                    if not res:
                        self._gv.closeOpenRasters()
                        return False
                    self.flowRaster = Raster(d8Flow, self._gv, canWrite=False, isInt=True)
                    res = self.flowRaster.open(self.chunkCount)
                    if not res:
                        self._gv.closeOpenRasters()
                        return False
                    # Require D8 flow raster  and channels raster  to have same geometry as dem,
                    # else, for example, 1 step downstream in flow raster  could stay in same channel pixel, or skip a channel pixel.
                    # Could probably live with just same pixel size, but they should both come from TauDEM using same DEM anyway.
                    if not QSWATTopology.sameTransform(self.transform, self.flowRaster.ds.GetGeoTransform(), self.numRows, self.numCols):
                        QSWATUtils.error('Clipped flow directions raster  {0} and clipped DEM raster {1} must have same geometry'.format(d8Flow, dem), self._gv.isBatch)
                        self._gv.closeOpenRasters()
                        return False
                    if not QSWATTopology.sameTransform(self.transform, self.channelsRaster.ds.GetGeoTransform(), self.numRows, self.numCols):
                        QSWATUtils.error('Clipped channels raster  {0} and clipped DEM raster {1} must have same geometry'.format(channels, dem), self._gv.isBatch)
                        self._gv.closeOpenRasters()
                        return False
                    self._progress('Hillslopes ...')
                    self.valleyDepthsRaster = self.openResult(self._gv.valleyDepthsFile, root, isInt=False)
                    if self.valleyDepthsRaster is None:
                        self._gv.closeOpenRasters()
                        return False
                    self.findHeads()
                    self.findSides()
                    self.hillslopeRaster = self.openResult(hillslopeFile, root, isInt=True)
                    if self.hillslopeRaster is None:
                        self._gv.closeOpenRasters()
                        return False
                    self.fillResult()
                    self.channelsRaster.close()
                    self.flowRaster.close()
                    self.hillslopeRaster.close()
                        ## fixing aux.xml file seems unnecessary in QGIS 2.16
#                     # now fix maximum hillslope value, otherwise is often zero, in aux.xml file
#                     # else if loaded has legend 0 to nan and display is all black
#                     xmlFile = self.hillslopeRaster.fileName + '.aux.xml'
#                     maxVal = unicode(str(6 * self.reachIdentifier + 4))
#                     ok, err = QSWATUtils.setXMLValue(xmlFile, u'MDI', u'key', u'STATISTICS_MAXIMUM', maxVal)
#                     if not ok:
#                         QSWATUtils.error(err, self._gv.isBatch)
                    # close depths raster  to flush it, then reopen readonly later
                    self.valleyDepthsRaster.close()
                    self._dlg.setCursor(Qt.ArrowCursor)
            except MemoryError:
                QSWATUtils.loginfo('Out of memory with chunk count {0}'.format(self.chunkCount))
                self._gv.closeOpenRasters()
                completed = False
                self.chunkCount += 1
        return True
                
    def makeSrcChannelRaster(self, channelThresh, root):
        """Make channel raster."""
        base, suffix = os.path.splitext(self._gv.demFile)
        srcChannelFile = base + 'srcChannel' + suffix
        if self._gv.ad8File == '':
            # can happen with existing watershed; try to find it
            ad8File = base + 'ad8' + suffix
            if not QSWATUtils.isUpToDate(self._gv.demFile, ad8File):
                QSWATUtils.error('Cannot find flow accumulation file: looking for {0}'.format(ad8File), self._gv.isBatch)
                return False
            else:
                self._gv.ad8File = ad8File
        QSWATUtils.removeLayer(srcChannelFile, root)
        if not TauDEMUtils.runThreshold(self._gv.ad8File, srcChannelFile, str(channelThresh),
                                      self.numProcesses, self.taudemOutput, mustRun=True):
            QSWATUtils.error('Failed to run TauDEM Threshold on {0}'.format(self._gv.ad8File), self._gv.isBatch)
            return False
        self._gv.srcChannelFile = srcChannelFile
        return True
        
    def makeChannelShapefile(self, channelThresh, root):
        """Make channel shapefile."""
        if self._gv.useGridModel and self._gv.srcChannelFile == '':
            if not self.makeSrcChannelRaster(channelThresh):
                return False
        base, suffix = os.path.splitext(self._gv.demFile)
        baseName = os.path.split(base)[1]
        shapesBase = QSWATUtils.join(self._gv.shapesDir, baseName)
        ordChannelFile = base + 'ordChannel' + suffix
        treeChannelFile = base + 'treeChannel.dat'
        coordChannelFile = base + 'coordChannel.dat'
        channelFile = shapesBase + 'channel.shp'
        wChannelFile = base + 'wChannel' + suffix
        QSWATUtils.removeLayer(ordChannelFile, root)
        QSWATUtils.removeLayer(channelFile, root)
        QSWATUtils.removeLayer(wChannelFile, root)
        if not TauDEMUtils.runStreamNet(self._gv.felFile, self._gv.pFile, self._gv.ad8File, self._gv.srcChannelFile, None, ordChannelFile, treeChannelFile, coordChannelFile,
                                          channelFile, wChannelFile, False, self.numProcesses, self.taudemOutput, mustRun=True):     
            QSWATUtils.error('Failed to run TauDEM Threshold on {0}, {1} and {2}'.format(self._gv.felFile, self._gv.pFile,
                                                                                          self._gv.ad8File), self._gv.isBatch)
            return False
        QSWATUtils.copyPrj(self._gv.felFile, channelFile)
        self._gv.channelFile = channelFile
        return True
                
    def calcFloodplainBuffer(self, root):
        """Generate floodplain raster by buffering the channels."""
        if not os.path.exists(self._gv.channelFile):
            if self._gv.useGridModel:
                if not self.makeChannelShapefile(self.channelThresh, root):
                    return
            if not os.path.exists(self._gv.channelFile):    
                QSWATUtils.error('Cannot find channels shapefile {0}'.format(self._gv.channelFile), self._gv.isBatch)
                return
        channels = self._gv.channelFile
        bufferShapefile = QSWATUtils.join(self._gv.shapesDir, 'bufferflood.shp')
        ft = FileTypes._BUFFERFLOOD
        legend = FileTypes.legend(ft)
        if QSWATUtils.shapefileExists(bufferShapefile):
            bufferShapefileLayer = QSWATUtils.getLayerByFilename(root.findLayers(), bufferShapefile, ft, 
                                                              None, None, None)[0]
            if bufferShapefileLayer is None:
                bufferShapefileLayer = QgsVectorLayer(bufferShapefile, '{0} ({1})'.format(legend, QFileInfo(bufferShapefile).baseName()), 'ogr')
            if not QSWATUtils.removeAllFeatures(bufferShapefileLayer):
                QSWATUtils.error('Failed to delete features from {0}.  Please delete the file manually and try again'.format(bufferShapefile), self._gv.isBatch)
                return
            fields = bufferShapefileLayer.fields()
        else:
            QSWATUtils.removeLayerAndFiles(bufferShapefile, root)
            fields = QgsFields()
            writer = QgsVectorFileWriter(bufferShapefile, 'CP1250', fields, QgsWkbTypes.MultiPolygon, self._gv.topo.crsProject, 'ESRI Shapefile')
            if writer.hasError() != QgsVectorFileWriter.NoError:
                QSWATUtils.error('Cannot create channels buffer shapefile {0}: {1}'.format(bufferShapefile, writer.errorMessage()), self._gv.isBatch)
                return
            # delete the writer to flush
            writer.flushBuffer()
            del writer
            QSWATUtils.copyPrj(channels, bufferShapefile)
            bufferShapefileLayer = QgsVectorLayer(bufferShapefile, '{0} ({1})'.format(legend, QFileInfo(bufferShapefile).baseName()), 'ogr')
        if self._gv.useGridModel:
            channelsLayer = QgsVectorLayer(self._gv.channelFile, 'Channels', 'ogr')
        else:
            channelsLayer = QSWATUtils.getLayerByFilename(root.findLayers(), channels, FileTypes._CHANNELS,
                                                          None, None, None)[0]
        drainAreaIndex = self._gv.topo.getIndex(channelsLayer, QSWATTopology._DRAINAREA, ignoreMissing=True)
        if drainAreaIndex < 0:
            # try for AreaC - used in ESRI stream files
            drainAreaIndex = self._gv.topo.getIndex(channelsLayer, 'AreaC', ignoreMissing=True)
            if drainAreaIndex >= 0:
                areaToSqKm = 1E2 # AreaC is in hectares
        else:
            areaToSqKm = 1E6 # DS_Cont_Ar is in sqaure metres
        provider = bufferShapefileLayer.dataProvider()
        features = list()
        for reach in channelsLayer.getFeatures():
            if drainAreaIndex < 0:
                drainAreaKm = 100 # TODO; roughly a 10 x 10 km watershed at its outlet
            else:
                drainAreaKm = reach[drainAreaIndex] / areaToSqKm
            bufferWidth = (self._gv.channelWidthMultiplier * drainAreaKm ** self._gv.channelWidthExponent) * self._dlg.bufferMultiplier.value()
            bufferGeometry = reach.geometry().buffer(bufferWidth, 4)
            feature = QgsFeature()
            feature.setFields(fields)
            feature.setGeometry(bufferGeometry)
            features.append(feature)
        if not provider.addFeatures(features):
            QSWATUtils.error('Unable to add features to buffer shapefile {0}'.format(bufferShapefile), self._gv.isBatch)
            return
        bufferRasterFile = QSWATUtils.join(self._gv.floodDir, 'bufferflood' + str(self._dlg.bufferMultiplier.value()) + '.tif')
        QSWATUtils.tryRemoveLayerAndFiles(bufferRasterFile, root)
        assert not os.path.exists(bufferRasterFile)
        basinLayer = QgsRasterLayer(self._gv.basinFile, 'subbasins')
        extent = basinLayer.extent()
        xMin = extent.xMinimum()
        xMax = extent.xMaximum()
        yMin = extent.yMinimum()
        yMax = extent.yMaximum()
        xSize = basinLayer.rasterUnitsPerPixelX()
        ySize = basinLayer.rasterUnitsPerPixelY()
        command = 'gdal_rasterize -burn 1 -a_nodata {8!s} -te {0!s} {1!s} {2!s} {3!s} -tr {4!s} {5!s} -ot Int32 "{6}" "{7}"' \
        .format(xMin, yMin, xMax, yMax, xSize, ySize, bufferShapefile, bufferRasterFile, self.noData)
        QSWATUtils.loginfo(command)
        os.system(command)
        assert os.path.exists(bufferRasterFile)
        QSWATUtils.copyPrj(bufferShapefile, bufferRasterFile)
        # load flood abaove DEM
        demLayer = QSWATUtils.getLayerByLegend(FileTypes.legend(FileTypes._DEM), root.findLayers())
        floodLayer, _ = QSWATUtils.getLayerByFilename(root.findLayers(), bufferRasterFile, FileTypes._BUFFERFLOOD,
                                          self._gv, demLayer, QSWATUtils._WATERSHED_GROUP_NAME)
        if floodLayer is None:
            QSWATUtils.error('Failed to load buffer floodplain {0}'.format(bufferRasterFile), self._gv.isBatch)
        
    def calcFloodplain(self, useInversion, root):
        """Generate floodplain raster using DEM inversion or branch length method."""
        self._dlg.setCursor(Qt.WaitCursor)
        if useInversion:
            # generate inverted flow accumulation to get ridge flow directions and slopes
            time1 = time.process_time()
            ridgesResult = self.calcRidges()
            if ridgesResult is None:
                return
            time2 = time.process_time()
            QSWATUtils.loginfo('Inverted ridges slope and accumulation took {0} seconds'.format(int(time2 - time1)))
            d8Inv, accInv = ridgesResult
            ridgep, isNew = self.clipRaster(d8Inv, self.clipperFile, root)
            self.mustRun = self.mustRun or isNew
            ridges, isNew = self.clipRaster(accInv, self.clipperFile, root)
            self.mustRun = self.mustRun or isNew
            subbasins = None
            distances = None
            slopeDir = None
            flowAcc = None
        else:
            base, ext = os.path.splitext(self._gv.demFile)
            subbasins, isNew = self.clipRaster(self._gv.basinFile, self.clipperFile, root)
            self.mustRun = self.mustRun or isNew
            distances, isNew = self.clipRaster(self._gv.distStFile, self.clipperFile, root)
            self.mustRun = self.mustRun or isNew
            slopeDir, isNew = self.clipRaster(self._gv.pFile, self.clipperFile, root)
            self.mustRun = self.mustRun or isNew
            ad8File = base + 'ad8' + ext
            flowAcc, isNew = self.clipRaster(ad8File, self.clipperFile, root)
            self.mustRun = self.mustRun or isNew
            ridgep = None
            ridges = None
        self.FP = Floodplain(self._gv, self._progress, self.chunkCount)
        self.FP.run(self.demRaster, self._gv.valleyDepthsFile, self.ridgeThresh, self.floodThresh, self.branchThresh, subbasins, distances, slopeDir, flowAcc, ridgep, ridges, self.noData, self.mustRun)
        self._dlg.setCursor(Qt.ArrowCursor)
        
    @staticmethod
    def mustClip(clipFile, inFile, outFile):
        """Return true if outFile does not exist, or is earlier than clipFile or inFile."""
        return not (QSWATUtils.isUpToDate(clipFile, outFile) and QSWATUtils.isUpToDate(inFile, outFile))
    
    def methodTabCheck(self):
        """Changes to reflect different method selections."""
        if self._dlg.methodTab.currentIndex() == 0:
            # buffer method
            self._dlg.slopePositionSpinBox.setVisible(False)
            self._dlg.slopePositionLabel.setVisible(False)
        else:
            self._dlg.slopePositionSpinBox.setVisible(True)
            self._dlg.slopePositionLabel.setVisible(True)
    
    def hillslopesCheck(self):
        """Enable dialog items or not according to hillslopes check box state."""
        if self._dlg.hillslopesCheckBox.isChecked() or self._dlg.methodTab.currentIndex() == 0:
            self._dlg.floodplainCheckBox.setEnabled(True)
        else:
            self._dlg.floodplainCheckBox.setEnabled(False)
        self.floodplainCheck()
        
    def floodplainCheck(self):
        """Enable dialog items or not according to floodplain check box state."""
        if self._dlg.floodplainCheckBox.isChecked():
            self._dlg.methodTab.setEnabled(True)
            self._dlg.slopePositionSpinBox.setEnabled(True)
            self._dlg.slopePositionLabel.setEnabled(True)
        else:
            self._dlg.methodTab.setEnabled(False)
            self._dlg.slopePositionSpinBox.setEnabled(False)
            self._dlg.slopePositionLabel.setEnabled(False)
        self.methodTabCheck()
        
    def parameterChange(self):
        """A parameter has changed, so must generate files."""
        self.mustRun = True
        
    def generate(self):
        """Run landscape generation."""
        doHillslopes = self._dlg.hillslopesCheckBox.isChecked()
        doFloodplain = self._dlg.floodplainCheckBox.isChecked()
        if not doHillslopes and not doFloodplain:
            self._dlg.close()
        useBuffer = False
        useInversion = False
        index = self._dlg.methodTab.currentIndex()
        if doFloodplain:
            if index == 0:
                useBuffer = True
            elif index == 1:
                try:
                    self.ridgeThresh = int(self._dlg.ridgeThresholdCells.text())
                    useInversion = True
                    doHillslopes = True
                except Exception:
                    QSWATUtils.information('Please set a ridge threshold (an integer number of cells)')
                    return
            else:
                try:
                    self.branchThresh = int(self._dlg.branchThreshold.text())
                    doHillslopes = True
                except Exception:
                    QSWATUtils.information('Please set a branch length threshold (an integer number of metres)')
                    return
        root = QgsProject.instance().layerTreeRoot()
        if doHillslopes or doFloodplain and not useBuffer:
            self.calcHillslopes(self.channelThresh, self.clipperFile, root)
        if doFloodplain:
            if useBuffer:
                self.calcFloodplainBuffer(root)
            else:
                self.floodThresh = self._dlg.slopePositionSpinBox.value()
                self.calcFloodplain(useInversion, root)
        if not self.demRaster is None:
            self.demRaster.close()
            
    def cancel(self):
        """Close the dialog."""
        self._gv.closeOpenRasters()
        if not self.valleyDepthsRaster is None:
            self.valleyDepthsRaster.close()
        if not self.hillslopeRaster is None:
            self.hillslopeRaster.close()
        if self.FP is not None:
            if not self.FP.valleyDepthsRaster is None:
                self.FP.valleyDepthsRaster.close()
            if not self.FP.ridgeHeightsRaster is None:
                self.FP.ridgeHeightsRaster.close()
            if not self.FP.ridgeDistancesRaster is None:
                self.FP.ridgeDistancesRaster.close()
            if not self.FP.floodplainRaster is None:
                self.FP.floodplainRaster.close()
        self._dlg.setCursor(Qt.ArrowCursor)
        self._dlg.close()
        
    #======No longer used - results poor=====================================================================
    # def calcRidges(self):
    #     """
    #     Create the ridges raster as flow accumulations.
    #     
    #     This is done by reversing the D8 flow directions and recalculating accumulation.
    #     This is faster than inverting the DEM and running from PitFill, 
    #     and safe as there is a loop in the reversed directions iff there is a loop in the original.
    #     """
    #     base, ext = os.path.splitext(self._gv.demFile)
    #     assert os.path.exists(self._gv.pFile), u'Cannot find d8 flow directions file'
    #     dirInv = base + 'invp' + ext
    #     accInv = base + 'invad8' + ext
    #     if not QSWATUtils.isUpToDate(self._gv.pFile, dirInv) or not QSWATUtils.isUpToDate(self._gv.pFile, accInv):
    #         pLayer = QgsRasterLayer(self._gv.pFile, 'P')
    #         entry = QgsRasterCalculatorEntry()
    #         entry.bandNumber = 1
    #         entry.raster = pLayer
    #         entry.ref = 'P@1'
    #         # The formula is equivalent to 'if P@1 <= 4 then P@1 + 4 else P@1 - 4'
    #         # since Booleans expressions evaluate to 1 (true) or 0 (false).
    #         # It reverses the TauDEM D8 direction P@1
    #         formula = '((P@1 <= 4) * (P@1 + 4) + (P@1 > 4) * (P@1 - 4))'
    #         calc = QgsRasterCalculator(formula, dirInv, 'GTiff', pLayer.extent(), pLayer.width(), pLayer.height(), [entry])
    #         result = calc.processCalculation(feedback=None)
    #         if result == 0:
    #             assert os.path.exists(dirInv), u'QGIS calculator formula {0} failed to write output'.format(formula)
    #             QSWATUtils.copyPrj(self._gv.pFile, dirInv)
    #         else:
    #             QSWATUtils.error(u'QGIS calculator formula {0} failed: returned {1}'.format(formula, result), self._gv.isBatch)
    #             return None     
    #         if not TauDEMUtils.runAreaD8(dirInv, accInv, None, None, self.numProcesses, self.taudemOutput, contCheck=False, mustRun=False):
    #             QSWATUtils.error(u'Failed to run TauDEM AreaD8 on {0}'.format(dirInv), self._gv.isBatch)
    #             return None
    #     return dirInv, accInv
    #===========================================================================
        
    def calcRidges(self):
        """
        Create the ridges raster as flow accumulations.
        
        This is done by negating the DEM and recalculating accumulation
        via PitFill, D8FlowDir and AreaD8.
        """
        base, ext = os.path.splitext(self._gv.demFile)
        dirInv = base + 'invp' + ext
        accInv = base + 'invad8' + ext
        if not QSWATUtils.isUpToDate(self._gv.demFile, dirInv) or not QSWATUtils.isUpToDate(self._gv.demFile, accInv):
            demLayer = QgsRasterLayer(self._gv.demFile, 'D')
            entry = QgsRasterCalculatorEntry()
            entry.bandNumber = 1
            entry.raster = demLayer
            entry.ref = 'D@1'
            formula = '0 - D@1'
            demInv = base + 'inv' + ext
            calc = QgsRasterCalculator(formula, demInv, 'GTiff', demLayer.extent(), demLayer.width(),
                                       demLayer.height(), [entry])
            result = calc.processCalculation(feedback=None)
            if result == 0:
                assert os.path.exists(demInv), 'QGIS calculator formula {0} failed to write output'.format(formula)
                QSWATUtils.copyPrj(self._gv.demFile, demInv)
            else:
                QSWATUtils.error('QGIS calculator formula {0} failed: returned {1}'.format(formula, result), self._gv.isBatch)
                return None
            invFel = base + 'invFel' + ext
            if not TauDEMUtils.runPitFill(demInv, invFel, self.numProcesses, self.taudemOutput):
                QSWATUtils.error('Failed to run TauDEM PitFill on {0}'.format(demInv), self._gv.isBatch)
                return None 
            sd8Inv = base + 'invsd8' + ext 
            if not TauDEMUtils.runD8FlowDir(invFel, sd8Inv, dirInv, self.numProcesses, self.taudemOutput):
                QSWATUtils.error('Failed to run TauDEM D8FlowDir on {0}'.format(invFel), self._gv.isBatch)
                return None 
            if not TauDEMUtils.runAreaD8(dirInv, accInv, None, None,
                                         self.numProcesses, self.taudemOutput, contCheck=False, mustRun=False):
                QSWATUtils.error('Failed to run TauDEM AreaD8 on {0}'.format(dirInv), self._gv.isBatch)
                return None 
        return dirInv, accInv
        
    def findHeads(self):
        """Populate heads dictionary for starts of reaches."""
        self.heads = dict()
        self.reachIdentifier = 0
        for row in range(self.numRows):
            for col in range(self.numCols):
                if self.channelsRaster.read(row, col) > 0:
                    count = self.upSlopeChannelPointsCount(row, col)
                    if count == 0:
                        # head of channel
                        self.reachIdentifier += 1
                        self.heads[(row, col)] = (self.reachIdentifier, True)
                    elif count > 1:
                        # junction - new reach starts
                        self.reachIdentifier += 1
                        self.heads[(row, col)] = (self.reachIdentifier, False)
                        
    def findSides(self):
        """
        Add to sides dictionary map of (row, col) -> (val, elevation) for head points, right and left side points of channels.
        
        val is 6 * ident for head points, 6 * ident + 2 for left side points, 6 * ident + 4 for right side points,
        where ident is the value in the heads map.
        """
        self.sides = dict()
        for ((row, col), (ident, isHead)) in self.heads.items():
            if isHead:
                # find a point draining in to here to use for elevation (hoping to avoid burned-in points)
                dir0 = self.flowRaster.read(row, col) - 1
                if not 0 <= dir0 < 8:
                    break
                n = dir0
                # loop clockwise (arbitrary - could go other way)
                while True:
                    n = (n - 1) % 8
                    if n == dir0:
                        # no point not on some channel drains into here - can use own elevation
                        elev = self.demRaster.read(row, col)
                        break
                    x = col + QSWATUtils._dX[n]
                    y = row + QSWATUtils._dY[n]
                    if not self.pointInMap(y, x):
                        continue
                    if self.downSlopePoint(y, x) == (row, col):  # (y, x) drains directly to (row, col)
                        if self.channelsRaster.read(y, x) > 0:  # found an upslope channel point
                            continue
                        elev = self.demRaster.read(y, x)
                        break
                self.sides[(row, col)] = (6 * ident, elev)
                # start one step down
                (row, col) = self.downSlopePoint(row, col)
            # If we are starting from a junction we will keep looking on left until meet last incoming channel
            # else may miss points between incoming channels.
            # This arbitrarily puts such points on the left side; could have chosen the right
            if isHead:
                pointsToIgnore = 0
            else:
                pointsToIgnore = self.upSlopeChannelPointsCount(row, col) - 1
            # loop through points on reach
            while True:
                if not self.pointInMap(row, col):
                    break
                dir0 = self.flowRaster.read(row, col) - 1
                if not 0 <= dir0 < 8:
                    break
                n = dir0
                # loop clockwise to find left side points
                while True:
                    n = (n - 1) % 8
                    if n == dir0:
                        break
                    x = col + QSWATUtils._dX[n]
                    y = row + QSWATUtils._dY[n]
                    if not self.pointInMap(y, x):
                        continue
                    if self.downSlopePoint(y, x) == (row, col):  # (y, x) drains directly to (row, col)
                        if self.channelsRaster.read(y, x) > 0:  # found upslope channel point
                            if pointsToIgnore == 0:
                                break
                            else:
                                pointsToIgnore -= 1
                        else: 
                            self.sides[(y, x)] = (6 * ident + 2, self.demRaster.read(y, x))
                # loop anticlockwise to find right side points
                n = dir0
                while True:
                    n = (n + 1) % 8
                    if n == dir0:
                        break
                    x = col + QSWATUtils._dX[n]
                    y = row + QSWATUtils._dY[n]
                    if not self.pointInMap(y, x):
                        continue
                    if self.downSlopePoint(y, x) == (row, col):  # (y, x) drains directly to (row, col)
                        if self.channelsRaster.read(y, x) > 0:  # found upslope channel point
                            break
                        else:
                            self.sides[(y, x)] = (6 * ident + 4, self.demRaster.read(y, x))
                # move to next point downstream
                downChannelPoint = self.downSlopePoint(row, col)
                if downChannelPoint is None or downChannelPoint in self.heads:
                    # off map or next reach
                    break
                row = downChannelPoint[0]
                col = downChannelPoint[1]
                if self.channelsRaster.read(row, col) <= 0:
                    # off end of reach: outlet
                    break
                
    def fillResult(self):
        """Fill hillslope raster with values of points in sides that each point drains to,
        and valleyDepthsRaster with point elevation - elevation of point in side it drains to."""
        channelsNoData = self.channelsRaster.band.GetNoDataValue()
        for row in range(self.numRows):
            for col in range(self.numCols):
                if self.channelsRaster.read(row, col) != channelsNoData:
                    (val, elev, path) = self.drainsTo(row, col)
                    self.propagate(val, elev, path)
                    
    def openResult(self, fileName, root, isInt=True):
        """Open raster  for writing and return it if OK."""
        if os.path.exists(fileName):
            QSWATUtils.tryRemoveLayerAndFiles(fileName, root)
        raster = Raster(fileName, self._gv, canWrite=True, isInt=isInt)
        res = raster.open(self.chunkCount, numRows=self.numRows, numCols=self.numCols,
                          transform=self.transform, projection=self.projection,
                          noData=self.noData)
        if res:
            return raster
        else:
            return None
        
    def drainsTo(self, row, col):
        """Return drainage value, valley floor elevation and drainage path for (row, col)."""
        path = []
        while True:
            val = self.hillslopeRaster.read(row, col)
            if val >= 0:  # already done this point
                # if, eg, this point is 100m in elevation, and its valley depth is 60m, its valley floor point is at 40m
                return (val, self.demRaster.read(row, col) - self.valleyDepthsRaster.read(row, col), path)
            val, elev = self.sides.get((row, col), (-1, 0))
            if val > 0:  # found the headwater or side drainage point
                path.append((row, col))
                return (val, elev, path)
            if self.channelsRaster.read(row, col) > 0:
                if len(path) > 0:
                    (startRow, startCol) = path[0]
                    startX, startY = QSWATTopology.cellToProj(startCol, startRow, self.transform)
                    x, y = QSWATTopology.cellToProj(col, row, self.transform)
                    QSWATUtils.error('Hit channel at ({0}, {1}) from ({2}, {3})'.format(x, y, startX, startY), self._gv.isBatch)
                    return (-1, 0, [])
                else:
                    return (0, self.demRaster.read(row, col), [(row, col)])  # set channel points (apart from head points) as zero
            if (row, col) in path:
                (startRow, startCol) = path[0]
                startX, startY = QSWATTopology.cellToProj(startCol, startRow, self.transform)
                x, y = QSWATTopology.cellToProj(col, row, self.transform)
                QSWATUtils.error('Loop to ({0}, {1}) from ({2}, {3})'.format(x, y, startX, startY), self._gv.isBatch)
                return (-1, 0, [])
            path.append((row, col))
            pt = self.downSlopePoint(row, col)
            if pt is None:
                (startRow, startCol) = path[0]
                startX, startY = QSWATTopology.cellToProj(startCol, startRow, self.transform)
                x, y = QSWATTopology.cellToProj(col, row, self.transform)
                QSWATUtils.error('Dead end at ({0}, {1}) from ({2}, {3})'.format(x, y, startX, startY), self._gv.isBatch)
                return (-1, 0, [])
            (row, col) = pt
        
    def propagate(self, val, elev, path):
        """Set points on path in hillslopeRaster to val, and in valleyDepthsRaster to point elevation - elev."""
        if path is not None:
            for (row, col) in path:
                self.hillslopeRaster.write(row, col, val)
                self.valleyDepthsRaster.write(row, col, self.demRaster.read(row, col) - elev)
                    
    def upSlopeChannelPointsCount(self, row, col):
        """Return number of points flowing into (row, col) that are on the channel."""
        count = 0
        for n in range(8):
            rown = row + QSWATUtils._dY[n]
            coln = col + QSWATUtils._dX[n]
            if self.pointInMap(rown, coln):
                if self.downSlopePoint(rown, coln) == (row, col) and self.channelsRaster.read(rown, coln) > 0:
                    count += 1
        return count
        
    def downSlopePoint(self, row, col):
        """Return point down slope from (row, col)."""
        dir0 = self.flowRaster.read(row, col) - 1
        if 0 <= dir0 < 8:
            row1 = row + QSWATUtils._dY[dir0]
            col1 = col + QSWATUtils._dX[dir0]
            if self.pointInMap(row1, col1):
                return (row1, col1)
            else:
                return None
        else:
            return None
        
    def pointInMap(self, row, col):
        """Return true if row and col are in the limits for the channel raster  array."""
        return 0 <= row < self.numRows and 0 <= col < self.numCols
