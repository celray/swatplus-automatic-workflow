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
from PyQt5.QtCore import *  # @UnusedWildImport
from PyQt5.QtGui import * # @UnusedWildImport
from PyQt5.QtWidgets import * # @UnusedWildImport
from PyQt5.QtXml import * # @UnusedWildImport
from qgis.core import * # @UnusedWildImport
import os.path
import posixpath
import ntpath
import glob
import shutil
import random
import time
import datetime
import sys
from osgeo import gdal, ogr
from typing import List, Dict, Tuple, Callable, TypeVar, Any, Optional, Generic
from builtins import int
import traceback

class QSWATUtils:
    """Various utilities."""
        
    _DATEFORMAT = '%d %B %Y'
    _QSWATNAME: str = 'QSWAT+'
    
    _SLOPE_GROUP_NAME: str = 'Slope'
    _LANDUSE_GROUP_NAME: str = 'Landuse'
    _SOIL_GROUP_NAME: str = 'Soil'
    _WATERSHED_GROUP_NAME: str = 'Watershed'
    _RESULTS_GROUP_NAME: str = 'Results'
    _ANIMATION_GROUP_NAME: str = 'Animations'
    
    _SNAPPEDLEGEND: str = 'Snapped inlets/outlets'
    _SELECTEDLEGEND: str = 'Selected inlets/outlets'
    _DRAWNLEGEND: str = 'Drawn inlets/outlets'
    _EXTRALEGEND: str = 'Extra inlets/outlets'
    _LAKESLEGEND: str = 'Lakes'
    _RESANDPTSRCLEGEND: str = 'Reservoirs and point sources'
    _FULLHRUSLEGEND: str = 'Full HRUs'
    _ACTHRUSLEGEND: str = 'Actual HRUs'
    _HILLSHADELEGEND: str = 'Hillshade'
    _STREAMSLEGEND: str = 'Streams'
    _CHANNELSLEGEND: str = 'Channels'
    _SUBBASINSLEGEND: str = 'Subbasins'
    _WATERSHEDLEGEND: str = 'Watershed'
    _GRIDLEGEND: str = 'Watershed grid'
    _GRIDSTREAMSLEGEND: str = 'Grid streams'
    _DRAINSTREAMSLEGEND: str = 'Drainage streams'
    _BUFFERFLOODLEGEND: str = 'Floodplain by buffer'
    _INVFLOODLEGEND: str = 'Floodplain by inversion'
    _BRANCHFLOODLEGEND: str = 'Floodplain by branch'
    _FULLLSUSLEGEND: str = 'Full LSUs'
    _ACTLSUSLEGEND: str = 'Actual LSUs'
    _EXTRAPTSRCANDRESLEGEND: str = 'Pt sources and reservoirs'
    ## x-offsets for TauDEM D8 flow directions, which run 1-8, so we use dir - 1 as index
    _dX: List[int] = [1, 1, 0, -1, -1, -1, 0, 1]
    ## y-offsets for TauDEM D8 flow directions, which run 1-8, so we use dir - 1 as index
    _dY: List[int] = [0, -1, -1, -1, 0, 1, 1, 1]
    
    _NOLANDSCAPE: int = 0
    _FLOODPLAIN: int = 1
    _UPSLOPE: int = 2
    
    @staticmethod
    def qgisName():
        """QGIS name as used in QGIS prefix path.
        
        Find it using the path of qgis.  It is the name of the directory following 'apps"""
        try:
            import qgis
            dirs = qgis.__file__.split('/')  
            for i in range(len(dirs)):
                if dirs[i] == 'apps':
                    return dirs[i+1]
            QSWATUtils.loginfo('Failed to find qgis name: default to "qgis"')
            return 'qgis'    
        except Exception:
            QSWATUtils.loginfo('Failed to find qgis name: default to "qgis": {0}'.format(traceback.format_exc()))
            return 'qgis'
            
    @staticmethod
    def error(msg: str, isBatch: bool, reportErrors=True) -> None:
        """Report msg as an error.  If not reportErrors merely log the message."""
        QSWATUtils.logerror(msg)
        if not reportErrors:
            return
        if isBatch:
            # in batch mode we generally only look at stdout 
            # (to avoid distracting messages from gdal about .shp files not being supported)
            # so report to stdout
            sys.stdout.write('ERROR: {0}\n'.format(msg))
        else:
            msgbox: QMessageBox = QMessageBox()
            msgbox.setWindowTitle(QSWATUtils._QSWATNAME)
            msgbox.setIcon(QMessageBox.Critical)
            msgbox.setText(QSWATUtils.trans(msg))
            msgbox.exec_()
        return
    
    @staticmethod
    def exceptionError(msg: str, isBatch: bool) -> None:
        QSWATUtils.error('{0}: {1}'.format(msg, traceback.format_exc()), isBatch)
        return
    
    @staticmethod
    def question(msg: str, isBatch: bool, affirm: bool) -> QMessageBox.StandardButton:
        """Ask msg as a question, returning Yes or No."""
        # only ask question if interactive
        if not isBatch:
            questionBox: QMessageBox = QMessageBox()
            questionBox.setWindowTitle(QSWATUtils._QSWATNAME)
            questionBox.setIcon(QMessageBox.Question)
            questionBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            questionBox.setText(QSWATUtils.trans(msg))
            result: QMessageBox.StandardButton = questionBox.exec_()
        else: # batch: use affirm parameter
            if affirm:
                result = QMessageBox.Yes
            else:
                result = QMessageBox.No
        if result == QMessageBox.Yes:
            res = ' Yes'
        else:
            res = ' No'
        QSWATUtils.loginfo(msg + res)
        if isBatch:
            sys.stdout.write('{0}\n'.format(msg + res))
        return result
    
    @staticmethod
    def information(msg, isBatch, reportErrors=True):
        """Report msg as information."""
        QSWATUtils.loginfo(msg)
        if not reportErrors:
            return
        if isBatch:
            sys.stdout.write('{0}\n'.format(msg))
        else:
            msgbox: QMessageBox = QMessageBox()
            msgbox.setWindowTitle(QSWATUtils._QSWATNAME)
            msgbox.setIcon(QMessageBox.Information)
            msgbox.setText(QSWATUtils.trans(msg))
            msgbox.exec_()
        return
    
    @staticmethod
    def loginfo(msg: str) -> None:
        """Log message as information."""
        app = QgsApplication.instance()
        # allow to fail if no application
        if app is not None:
            log: QgsMessageLog = QgsApplication.instance().messageLog()
            log.logMessage(msg, QSWATUtils._QSWATNAME, Qgis.Info)
        
    @staticmethod
    def logerror(msg: str) -> None:
        """Log message as error."""
        app = QgsApplication.instance()
        # allow to fail if no application
        if app is not None:
            log: QgsMessageLog = QgsApplication.instance().messageLog()
            log.logMessage(msg, QSWATUtils._QSWATNAME, Qgis.Critical)
        
    @staticmethod
    def trans(msg: str) -> str:
        """Translate msg according to current locale."""
        return QApplication.translate("QSWATPlus", msg, None)
    
    @staticmethod
    def join(path: str, fileName: str) -> str:
        """Use appropriate path separator."""
        if os.name == 'nt':
            return ntpath.join(path, fileName)
        else:
            return posixpath.join(path, fileName)
        
    @staticmethod
    def samePath(p1: str, p2: str)-> bool:
        """Return true if absolute paths of the two paths are the same."""
        return os.path.abspath(p1) == os.path.abspath(p2)
    
    @staticmethod
    def copyPrj(inFile: str, outFile: str) -> None:
        """
        Copy .prj file, if it exists, from inFile to .prj file of outFile,
        unless outFile is .dat.
        """
        inBase: str = os.path.splitext(inFile)[0]
        outBase, outSuffix = os.path.splitext(outFile)
        if not outSuffix == '.dat':
            inPrj: str = inBase + '.prj'
            outPrj: str = outBase + '.prj'
            if os.path.exists(inPrj):
                shutil.copy(inPrj, outPrj)
            
    @staticmethod
    def isUpToDate(inFile: str, outFile: str) -> bool:
        """Return true (outFile is up to date) if inFile exists, outFile exists and is no younger than inFile."""
        if not os.path.exists(inFile):
            return False
        if os.path.exists(outFile):
            if os.path.getmtime(outFile) >= os.path.getmtime(inFile):
                return True
        return False
    
    @staticmethod
    def progress(text: str, label: QLabel) -> None:
        """Set label text and repaint."""
        if text == '':
            label.clear()
            label.update()
        else:
            label.setText(text)
            # shows on console if visible; more useful in testing when appears on standard output
            print(text)
            # calling processEvents after label.clear can cause QGIS to hang
            label.update()
            QCoreApplication.processEvents(QEventLoop.ExcludeUserInputEvents)
        
    @staticmethod
    def layerFileInfo(mapLayer: QgsMapLayer) -> Optional[QFileInfo]:
        """Return QFileInfo of raster or vector layer."""
        provider: QgsDataProvider = mapLayer.dataProvider()
        if isinstance(mapLayer, QgsRasterLayer):
            return QFileInfo(provider.dataSourceUri())
        elif isinstance(mapLayer, QgsVectorLayer):
            path: str = provider.dataSourceUri()
            # vector data sources have additional "|layerid=0"
            pos: int = path.find('|')
            if pos >= 0:
                path = path[:pos]
            return QFileInfo(path)
        return None
    
    @staticmethod
    def layerFilename(layer):
        """Return path of raster or vector layer."""
        provider = layer.dataProvider()
        if isinstance(layer, QgsRasterLayer):
            return provider.dataSourceUri()
        elif isinstance(layer, QgsVectorLayer):
            path  = provider.dataSourceUri()
            # vector data sources have additional "|layerid=0"
            pos = path .find('|')
            if pos >= 0:
                path = path [:pos]
            return path
        return ''
      
    @staticmethod
    def removeLayerAndFiles(fileName: str, root: QgsLayerTreeGroup) -> None:
        """Remove any layers for fileName; delete files with same basename 
        regardless of suffix.
        """
        QSWATUtils.removeLayer(fileName, root)
        # wait for layers to be removed
        QApplication.processEvents()
        QSWATUtils.removeFiles(fileName)
      
    @staticmethod
    def tryRemoveLayerAndFiles(fileName: str, root: QgsLayerTreeGroup) -> None:
        """Remove any layers for fileName; delete files with same basename 
        regardless of suffix, but allow deletions to fail.
        """
        QSWATUtils.removeLayer(fileName, root)
        # wait for layers to be removed
        QApplication.processEvents()
        QSWATUtils.tryRemoveFiles(fileName)
          
    @staticmethod  
    def removeLayer(fileName: str, root: QgsLayerTreeGroup) -> None:
        """Remove any layers for fileName."""
        fileInfo: QFileInfo = QFileInfo(fileName)
        lIds: List[str] = []
        layers = []
        for layer in root.findLayers():
            info: QFileInfo = QSWATUtils.layerFileInfo(layer.layer())
            if info == fileInfo:
                lIds.append(layer.layerId())
                layers.append(layer)
        QgsProject.instance().removeMapLayers(lIds)
        for layer in layers:
            del layer
     
    @staticmethod
    def removeLayerByLegend(legend: str, treeLayers: List[QgsLayerTreeLayer]) -> None:
        """Remove any tree layers whose legend name starts with the legend."""
        lIds: List[str] = []
        for treeLayer in treeLayers:
            name: str = treeLayer.name()
            if name.startswith(legend):
                lIds.append(treeLayer.layerId())
        QgsProject.instance().removeMapLayers(lIds)
        
    @staticmethod
    def removeAllFeatures(layer: QgsVectorLayer):
        """Remove all features from layer."""
        provider = layer.dataProvider()
        request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry)
        ids = [feature.id() for feature in provider.getFeatures(request)]
        return provider.deleteFeatures(ids)
        
    @staticmethod
    def setLayerVisibility(layer: QgsMapLayer, visibility: bool, root: QgsLayerTreeGroup) -> None:
        """Set map layer visible or not according to visibility."""
        try:
            treeLayer: QgsLayerTreeLayer = root.findLayer(layer.id())
            treeLayer.setItemVisibilityChecked(visibility)
        except Exception:
            # layer probably removed - just exit
            return

    @staticmethod
    def getLayerByLegend(legend: str, treeLayers: List[QgsLayerTreeLayer])-> Optional[QgsLayerTreeLayer]:
        """Find a tree layer if any whose legend name starts with the legend."""
        for layer in treeLayers:
            if layer.name().startswith(legend):
                return layer
        return None
    
    @staticmethod
    def getLayersInGroup(group: str, root: QgsLayerTreeGroup, visible: bool =False) -> List[QgsLayerTreeLayer]:
        """Return list of tree layers in group, restricted to visible if visible is true."""
        treeGroup = root.findGroup(group)
        if treeGroup is None:
            return []
        if visible:
            return [layer for layer in treeGroup.findLayers() if layer.isVisible()]
        else:
            return treeGroup.findLayers()
    
    @staticmethod
    def countLayersInGroup(group: str, root: QgsLayerTreeGroup) -> int:
        """Return number of layers in group."""
        count = 0
        treeGroup = root.findGroup(group)
        if treeGroup is None:
            return 0
        for _ in treeGroup.findLayers():
            count += 1
        return count
                
    @staticmethod
    def removeFiles(fileName: str) -> None:
        """
        Delete all files with same root as fileName, 
        i.e. regardless of suffix.
        """
        pattern = os.path.splitext(fileName)[0] + '.*'
        for f in glob.iglob(pattern):
            os.remove(f)
                
    @staticmethod
    def tryRemoveFiles(fileName: str) -> None:
        """
        Delete all files with same root as fileName, 
        i.e. regardless of suffix, but allow deletions to fail.
        """
        pattern: str = os.path.splitext(fileName)[0] + '.*'
        for f in glob.iglob(pattern):
            try:
                os.remove(f)
            except:
                pass
            
    @staticmethod
    def copyFiles(inInfo: QFileInfo, saveDir: str) -> None:
        """
        Copy files with same basename as file with info  inInfo to saveDir, 
        i.e. regardless of suffix.
        """
        inFile: str = inInfo.fileName()
        inPath: str = inInfo.path()
        if inFile == 'sta.adf' or inFile == 'hdr.adf':
            # ESRI grid: need to copy top directory of inInfo to saveDir
            inDirName: str = inInfo.dir().dirName()
            savePath: str = QSWATUtils.join(saveDir, inDirName)
            # guard against trying to copy to itself
            inPath = os.path.normcase(os.path.abspath(inPath))
            savePath = os.path.normcase(os.path.abspath(savePath))
            if inPath != savePath:
                if os.path.exists(savePath):
                    shutil.rmtree(savePath)
                shutil.copytree(inPath, savePath, True, None)
        else:
            pattern: str = QSWATUtils.join(inPath, inInfo.baseName()) + '.*'
            for f in glob.iglob(pattern):
                shutil.copy(f, saveDir)
                
    @staticmethod
    def copyShapefile(infile: str, outbase: str, outdir: str) -> None:
        """Copy files with same basename as infile to outdir, setting basename to outbase."""
        pattern: str = os.path.splitext(infile)[0] + '.*'
        for f in glob.iglob(pattern):
            suffix: str = os.path.splitext(f)[1]
            outfile: str = QSWATUtils.join(outdir, outbase + suffix)
            shutil.copy(f, outfile)
            
    @staticmethod
    def shapefileExists(infile: str) -> bool:
        """Assuming infile is.shp, check existence of .shp. .shx and .dbf."""
        if not os.path.isfile(infile):
            return False
        shxFile = infile.replace('.shp', '.shx')
        if not os.path.isfile(shxFile):
            return False
        dbfFile = infile.replace('.shp', '.dbf')
        if not os.path.isfile(dbfFile):
            return False
        return True
        
            
    @staticmethod
    def nextFileName(baseFile, n):
        """If baseFile takes form X.Y, returns Xz.Y, z where z is the smallest integer >= n such that Xz.Y does not exist."""
        base, suffix = os.path.splitext(baseFile)
        nextFile = base + str(n) + suffix
        while os.path.exists(nextFile):
            n += 1
            nextFile = base + str(n) + suffix
        return nextFile, n
                
    @staticmethod
    def getLayerByFilenameOrLegend(treeLayers: List[QgsLayerTreeLayer], 
                                   fileName: str, ft: int, legend: str, isBatch: bool) -> Optional[QgsMapLayer]:
        """
        Look for file that should have a map layer and return it. 
        If not found by filename, try legend, either as given or by file type ft.
        """
        layer: QgsMapLayer = QSWATUtils.getLayerByFilename(treeLayers, fileName, ft, None, None, None)[0]
        if layer is not None:
            return layer
        lgnd: str = FileTypes.legend(ft) if legend == '' else legend
        treeLayer: QgsLayerTreeLayer = QSWATUtils.getLayerByLegend(lgnd, treeLayers)
        if treeLayer is not None:
            layer = treeLayer.layer()
            possFile: str = QSWATUtils.layerFileInfo(layer).absoluteFilePath()
            if QSWATUtils.question('Use {0} as {1} file?'.format(possFile, lgnd), isBatch, True) == QMessageBox.Yes:
                return layer
        return None
    
    @staticmethod
    def clipLayerToDEM(treeLayers: List[QgsLayerTreeLayer], rasterLayer: QgsRasterLayer, fileName: str, legend: str, gv: Any) -> QgsRasterLayer:
        """Clip layer to just outside DEM if it is 10 or more pixels bigger."""
        extent: QgsRectangle = rasterLayer.extent()
        yMax: float = extent.yMaximum()
        yMin: float = extent.yMinimum()
        xMax: float = extent.xMaximum()
        xMin: float = extent.xMinimum()
        units: QgsUnitTypes.DistanceUnit = rasterLayer.crs().mapUnits()
        if units == QgsUnitTypes.DistanceMeters:
            factor: float = 1
        elif units == QgsUnitTypes.DistanceFeet:
            factor = 0.0348
        else: # something odd has happened - probably in lat-long - reported elsewhere
            return rasterLayer
        xSize: float = rasterLayer.rasterUnitsPerPixelX() * factor
        ySize: float = rasterLayer.rasterUnitsPerPixelY() * factor
        # excesses are number of columns or rows extending outside DEM extent
        leftExcess: int = int((gv.topo.demExtent.xMinimum() - xMin) // xSize)
        rightExcess: int = int((xMax - gv.topo.demExtent.xMaximum()) // xSize)
        topExcess: int = int((yMax - gv.topo.demExtent.yMaximum()) // ySize)
        bottomExcess: int = int((gv.topo.demExtent.yMinimum() - yMin) // ySize)
        excesses: List[int] = [leftExcess, rightExcess, topExcess, bottomExcess]
        # if no excesses are bigger than 10 little point in spending time clipping
        # if any excesses are zero or negative, too tight to clip
        if max(excesses) < 10 or min(excesses) <= 0:
            return rasterLayer
        nodata: float = rasterLayer.dataProvider().sourceNoDataValue(1)
        numCols: int = rasterLayer.width() - (leftExcess + rightExcess)
        numRows: int = rasterLayer.height() - (topExcess + bottomExcess)
        direc, base = os.path.split(fileName)
        if base == 'sta.adf' or base == 'hdr.adf':
            baseName: str = direc
        else:
            baseName = os.path.splitext(fileName)[0]
        clipName: str = baseName + '_clip.tif'
        QSWATUtils.removeLayerByLegend(legend, treeLayers)
        QSWATUtils.tryRemoveFiles(clipName)
        command: str = 'gdal_translate -a_nodata {0!s} -of GTiff -srcwin {1} {2} {3} {4} "{5}" "{6}"' \
                        .format(nodata, leftExcess, topExcess, numCols, numRows, fileName, clipName)
        QSWATUtils.loginfo(command)
        os.system(command)
        assert os.path.exists(clipName), 'Failed to clip raster {0} to make {1}'.format(fileName, clipName)
        QSWATUtils.copyPrj(fileName, clipName)
        return QgsRasterLayer(clipName, '{0} ({1})'.format(legend, os.path.split(clipName)[1]))
    
    @staticmethod
    def checkAdequateForWshed(layers, fileName, xMin, xMax, yMin, yMax, xSize, ySize, gv):
        """Check extent is sufficient to cover subbasins."""
        subbasinsLayer = QSWATUtils.getLayerByFilename(layers, gv.subbasinsFile, FileTypes._SUBBASINS, None, False)[0]
        if subbasinsLayer is None:
            return
        subExtent = subbasinsLayer.extent()
        # need at least a cell around subbasins
        if xMin > (subExtent.xMinimum() - xSize) or \
            xMax < (subExtent.xMaximum() + xSize) or \
            yMin > (subExtent.yMinimum() - abs(ySize)) or \
            yMax < (subExtent.yMaximum() + abs(ySize)):
                QSWATUtils.information('{0} the extent of {0} does not seem adequate to cover the watershed.  Have you clipped it too much?'.format(fileName),
                                       gv.isBatch)
        return
            
    @staticmethod        
    def getLayerByFilename(treeLayers: List[QgsLayerTreeLayer], fileName: str, ft: int, gv: Any, 
                           subLayer: Optional[QgsLayerTreeLayer], groupName: Optional[str], clipToDEM: bool =False) \
                            -> Tuple[Optional[QgsMapLayer], bool]:
        """
        Return map layer for this fileName and flag to indicate if new layer, 
        loading it if necessary if groupName is not None.
        
        If subLayer is not none, finds its index and inserts the new layer immediately above it.
        """
        fileInfo: QFileInfo = QFileInfo(fileName)
        for treeLayer in treeLayers:
            mapLayer = treeLayer.layer()
            if QSWATUtils.layerFileInfo(mapLayer) == fileInfo:
                return (mapLayer, False)
        # not found: load layer if requested
        if groupName is not None:
            legend: str = FileTypes.legend(ft)
            styleFile: str = FileTypes.styleFile(ft)
            baseName: str = fileInfo.baseName()
            if fileInfo.suffix() == 'adf':
                # ESRI grid: use directory name as baseName
                baseName = fileInfo.dir().dirName()
            if ft == FileTypes._OUTLETS:
                if baseName.endswith('_snap'):
                    legend = QSWATUtils._SNAPPEDLEGEND
                elif baseName.endswith('_sel'):
                    legend = QSWATUtils._SELECTEDLEGEND
                elif baseName.endswith('extra'):  # note includes arcextra
                    legend = QSWATUtils._EXTRALEGEND
                elif baseName == 'drawoutlets':
                    legend = QSWATUtils._DRAWNLEGEND
                elif baseName == 'resandptsrc':
                    legend = QSWATUtils._RESANDPTSRCLEGEND
            if not FileTypes.multipleLayersAllowed(ft):
                QSWATUtils.removeLayerByLegend(legend, treeLayers)
            proj: QgsProject = QgsProject.instance()
            root: QgsLayerTreeGroup = proj.layerTreeRoot()
            group: QgsLayerTreeGroup = root.findGroup(groupName)
            if group is None:
                QSWATUtils.information('Internal error: cannot find group {0].'.format(groupName), gv.isBatch)
                return None, False
            if subLayer is None:
                index: int = 0
            else:
                index = QSWATUtils.groupIndex(group, subLayer)
            if FileTypes.isRaster(ft):
                layer: QgRasterLayer = QgsRasterLayer(fileName, '{0} ({1})'.format(legend, baseName))
                if clipToDEM:
                    layer = QSWATUtils.clipLayerToDEM(treeLayers, layer, fileName, legend, gv)
            else: 
                ogr.RegisterAll()
                layer = QgsVectorLayer(fileName, '{0} ({1})'.format(legend, baseName), 'ogr')
            layer: QgsMapLayer = proj.addMapLayer(layer, False)
            if layer is not None and group is not None:
                group.insertLayer(index, layer)
            if layer is not None and layer.isValid():
                # this function does not seem to work:
                # replaced by code above to set the layer insertion point
                # layer = QSWATUtils.moveLayerToGroup(layer, groupName, root, gv)
                fun: Callable[[QgsMapLayer, Any], None] = FileTypes.colourFun(ft)
                if fun is not None:
                    fun(layer, gv.db)
                if not (styleFile is None or styleFile == ''):
                    # note thic causes 'Calling appendChild() on a null node does nothing.' to be output
                    layer.loadNamedStyle(QSWATUtils.join(gv.plugin_dir, styleFile))
                # save qml form of DEM style file if batch (no support for sld form for rasters)
                if gv.isBatch and ft == FileTypes._DEM:
                    qmlFile: str = QSWATUtils.join(gv.projDir, 'dem.qml')
                    msg, OK = layer.saveNamedStyle(qmlFile)
                    if not OK:
                        QSWATUtils.error('Failed to create dem.qml: {0}'.format(msg), gv.isBatch)
                return (layer, True)
            else:
                if layer is not None:
                    err: QgsError = layer.error()
                    msg: str = err.summary()
                else:
                    msg = 'layer is None'
                QSWATUtils.error('Failed to load {0}: {1}'.format(fileName, msg), gv.isBatch)
        return (None, False)
    
    @staticmethod
    def groupIndex(group: Optional[QgsLayerTreeGroup], layer: QgsLayerTreeLayer) -> int:
        """Find index of tree layer in group's children, defaulting to 0."""
        index = 0
        if group is None:
            return index
        for child in group.children():
            if QgsLayerTree.isLayer(child) and child == layer:
                return index
            index += 1
        return 0
    
    @staticmethod 
    def moveLayerToGroup(layer: QgsMapLayer, groupName: str, 
                         root: QgsLayerTreeGroup, gv: Any) -> QgsMapLayer:
        """Move map layer to start of group unless already in it, and return it."""
        QSWATUtils.loginfo('Moving {0} to group {1}'.format(layer.name(), groupName))
        group: QgsLayerTreeGroup = root.findGroup(groupName)
        if group is None:
            QSWATUtils.information('Internal error: cannot find group {0].'.format(groupName), gv.isBatch)
            return layer
        layerId: str = layer.id()
        # redundant code, but here to make a fast exit from usual situation of already in right group
        if group.findLayer(layerId) is not None:
            QSWATUtils.loginfo('Found layer in group {}'.format(groupName))
            return layer
        # find the group the layer is in
        currentGroup: QgsLayerTreeGroup = root
        currentLayer: QgsLayerTreeLayer = root.findLayer(layerId)
        if currentLayer is None:
            # not at the top level: check top level groups
            currentGroup = None
            for node in root.children():
                if QgsLayerTree.isGroup(node):
                    currentLayer = node.findLayer(layerId)
                    if currentLayer is not None:
                        if node == group: # already in required group
                            return layer
                        else:
                            currentGroup = node
                            break
        if currentGroup is None:
            # failed to find layer
            QSWATUtils.information(f'Trying to move layer {layer.name()} to group {groupName} but failed to find layer',
                                   gv.isBatch)
            return layer
        QSWATUtils.loginfo('Found layer in group {0}'.format(currentGroup.name()))
        # need to move from currentGroup to group
        QSWATUtils.loginfo('Layer to be cloned is {0}'.format(repr(layer)))
        cloneLayer: QgsLayerTreeLayer = layer.clone()
        QSWATUtils.loginfo('Cloned map layer is {0}'.format(repr(cloneLayer)))
        movedLayer: QgsLayerTreeLayer = group.insertLayer(0, cloneLayer)
        currentGroup.removeLayer(layer)
        QSWATUtils.loginfo('Moved tree layer is {0}'.format(repr(movedLayer)))
        QSWATUtils.loginfo('Moved map layer is {0}'.format(repr(movedLayer.layer())))
        return movedLayer.layer()
    
    @staticmethod  
    def printLayers(root: QgsLayerTreeGroup, n: int) -> None:
        """Debug function for displaying tre and map laers."""
        layers: List[Tuple[str, QgsLayerTreeLayer]] = [(layer.name(), layer) for layer in root.findLayers()]
        mapLayers: List[Tuple[str, QgsMapLayer]] = \
            [(layer.layer().name(), layer.layer()) for layer in root.findLayers()]
        QSWATUtils.loginfo('{0}: layers: {1}'.format(n, repr(layers)))
        QSWATUtils.loginfo('{0}: map layers: {1}'.format(n, repr(mapLayers)))
        
    @staticmethod    
    def openAndLoadFile(root: QgsLayerTreeGroup, ft: int,
                        box: QTextEdit, saveDir: str, gv: Any, 
                        subLayer: QgsLayerTreeLayer, groupName: str, clipToDEM: bool =False) \
                            -> Tuple[Optional[str], Optional[QgsMapLayer]]:
        """
        Use dialog to open file of FileType ft chosen by user, 
        add a layer for it if necessary, 
        clip if clipToDEM is true and substantially larger than DEM,
        copy files to saveDir, write path to box,
        and return file path and layer.
        """
        settings: QSettings = QSettings()
        if settings.contains('/QSWATPlus/LastInputPath'):
            path: str = str(settings.value('/QSWATPlus/LastInputPath'))
        else:
            path = ''
        title: str = QSWATUtils.trans(FileTypes.title(ft))
        inFileName, _ = QFileDialog.getOpenFileName(None, title, path, FileTypes.filter(ft))
        #QSWATUtils.information('File is |{0}|'.format(inFileName), False)
        if inFileName is not None and inFileName != '':
            settings.setValue('/QSWATPlus/LastInputPath', os.path.dirname(str(inFileName)))
            # copy to saveDir if necessary
            inInfo: QFileInfo = QFileInfo(inFileName)
            inDir: QDir = inInfo.absoluteDir()
            outDir: QDir = QDir(saveDir)
            if inDir != outDir:
                inFile: str = inInfo.fileName()
                if inFile == 'sta.adf' or inFile == 'hdr.adf':
                    # ESRI grid - whole directory will be copied to saveDir
                    inDirName: str = inInfo.dir().dirName()
                    if ft == FileTypes._DEM:
                        # will be converted to .tif, so make a .tif name
                        outFileName: str = QSWATUtils.join(saveDir, inDirName) + '.tif'
                    else:
                        outFileName = QSWATUtils.join(QSWATUtils.join(saveDir, inDirName), inFile)
                else:
                    outFileName = QSWATUtils.join(saveDir, inFile)
                    if ft == FileTypes._DEM:
                        # will be converted to .tif, so convert to .tif name
                        outFileName = os.path.splitext(outFileName)[0] + '.tif'
                # remove any existing layer for this file, else cannot copy to it
                QSWATUtils.removeLayer(outFileName, root)
                if ft == FileTypes._DEM:
                    # use GDAL CreateCopy to ensure result is a GeoTiff
                    inDs = gdal.Open(inFileName, gdal.GA_ReadOnly)
                    driver: gdal.Driver = gdal.GetDriverByName('GTiff')
                    # QSWATUtils.information('Creating {0}'.format(outFileName), gv.isBatch)
                    outDs = driver.CreateCopy(outFileName, inDs, 0)
                    if outDs is None:
                        QSWATUtils.error('Failed to create dem in geoTiff format', gv.isBatch)
                        return (None, None)
                    # may not have got projection information, so if any copy it
                    QSWATUtils.copyPrj(inFileName, outFileName)
                    del inDs
                    del outDs
                else:
                    QSWATUtils.copyFiles(inInfo, saveDir)
            else:
                outFileName = inFileName
            if ft == FileTypes._CSV or ft == FileTypes._CHANNELBASINSRASTER:
                # not to be loaded into QGIS
                return (outFileName, None)
            # this function will add layer if necessary
            layer = QSWATUtils.getLayerByFilename(root.findLayers(), outFileName, ft, 
                                                  gv, subLayer, groupName, clipToDEM)[0]
            if not layer:
                return (None, None)
            if clipToDEM:
                # file name has changed if clipped
                outFileName = layer.dataProvider().dataSourceUri()
            if box is not None:
                box.setText(outFileName)
            # if no .prj file, try to create one
            # this is needed, for example, when DEM is created from ESRI grid
            # or if DEM is made by clipping
            QSWATUtils.writePrj(outFileName, layer)
            return (outFileName, layer)
        else:
            return (None, None)
        
    @staticmethod
    def getFeatureByValue(layer: QgsVectorLayer, indx: int, val) -> Optional[QgsFeature]:
        """Return feature in features whose attribute with index indx has value val."""
        for f in layer.getFeatures():
            v = f[indx]
            if v == val:
                # QSWATUtils.loginfo('Looking for {0!s} found {1!s}: finished'.format(val, v))
                return f
            # QSWATUtils.loginfo('Looking for {0!s} found {1!s}: still looking'.format(val, v))
        return None
        
    @staticmethod
    def writePrj(fileName: str, layer: QgsMapLayer) -> None:
        """If no .prj file exists for fileName, try to create one from the layer's crs."""
        prjFile: str = os.path.splitext(fileName)[0] + '.prj'
        if os.path.exists(prjFile):
            return
        try:
            srs: QgsCoordinateReferenceSystem = layer.crs()
            wkt: str = srs.toWkt()
            if not wkt:
                raise ValueError('Could not make WKT from CRS.')
            with fileWriter(prjFile) as fw:
                fw.writeLine(wkt)
        except Exception:
            QSWATUtils.information(f"""Unable to make .prj file for {fileName}.  
            You may need to set this map's projection manually""", False)
        
    @staticmethod
    def tempFolder():
        """Make temporary QSWAT folder and return its absolute path."""
        tempDir = QSWATUtils.join(str(QDir.tempPath()), 'QSWAT')
        if not QDir(tempDir).exists():
            QDir().mkpath(tempDir)
        return tempDir
    
    @staticmethod
    def tempFile(suffix):
        """Make a new temporary file in tempFolder with suffix."""
        base = 'tmp' + str(time.clock()).replace('.','')
        folder = QSWATUtils.tempFolder()
        fil = QSWATUtils.join(folder, base + suffix)
        if os.path.exists(fil):
            time.sleep(1)
            return QSWATUtils.tempFile(suffix)
        return fil
        
    @staticmethod
    def deleteTempFolder():
        """Delete the temporary folder and its contents."""
        folder = QSWATUtils.tempFolder()
        if QDir(folder).exists():
            shutil.rmtree(folder, True)
        
    @staticmethod
    def makeCurrent(strng: str, combo: QComboBox) -> None:
        """Add string to combo box if not already present, and make it current."""
        index: int = combo.findText(strng)
        if index < 0:
            combo.addItem(strng)
            combo.setCurrentIndex(combo.count() - 1)
        else:
            combo.setCurrentIndex(index) 
        
    @staticmethod
    def parseSlopes(strng: str) -> List[float]:
        """
        Parse a slope limits string to list of intermediate limits.
        For example '[min, a, b, max]' would be returned as [a, b].
        """
        slopeLimits = []
        nums = strng.split(',')
        # ignore first and last
        for i in range(1, len(nums) - 1):
            slopeLimits.append(float(nums[i]))
        return slopeLimits
        
    @staticmethod
    def slopesToString(slopeLimits: List[float]) -> str:
        """
        Return a slope limits string made from a string of intermediate limits.
        For example [a, b] would be returned as '[0, a, b, 9999]'.
        """
        str1 = '[0, '
        for i in slopeLimits:
            # lose the decimal point if possible
            d = int(i)
            if i == d:
                str1 += ('{0!s}, '.format(d))
            else:
                str1 += ('{0!s}, '.format(i))
        return str1 + '9999]'

    @staticmethod
    def pointInGridCell(point: QgsPointXY, cell: QgsFeature) -> bool:
        """Return true if point is within (assumed rectangular) cell."""
        points: List[QgsPointXY] = cell.geometry().asPolygon()[0]
        corner1: QgsPointXY = points[0]
        corner2: QgsPointXY = points[2]
        x1: float = corner1.x()
        x2: float = corner2.x()
        y1: float = corner1.y()
        y2: float = corner2.y()
        if x1 < x2:
            inX: bool = x1 <= point.x() <= x2
        else:
            inX = x2 <= point.x() <= x1
        if inX:
            if y1 < y2:
                return y1 <= point.y() <= y2
            else:
                return y2 <= point.y() <= y1
        else:
            return False
     
    @staticmethod   
    def centreGridCell(cell: QgsFeature):
        """Return centre point of (assumed rectangular) cell, 
        plus extent as minimum and maximum x and y values."""
        geom = cell.geometry()
        if geom.isMultipart():
            poly = geom.asMultiPolygon()[0]
        else:
            poly = geom.asPolygon()
        points: List[QgsPointXY] = poly[0]
        corner1: QgsPointXY = points[0]
        corner2: QgsPointXY = points[2]
        x1: float = corner1.x()
        x2: float = corner2.x()
        y1: float = corner1.y()
        y2: float = corner2.y()
        return \
            QgsPointXY((x1 + x2) / 2.0, (y1 + y2) / 2.0), \
            (x1, x2) if x1 <= x2 else (x2, x1), (y1, y2) if y1 <= y2 else (y2, y1)
        
    @staticmethod
    def date() -> str:
        """Retun today's date as day month year."""
        return datetime.date.today().strftime(QSWATUtils._DATEFORMAT)
    
    @staticmethod
    def time() -> str:
        """Return the time now as hours.minutes."""
        return datetime.datetime.now().strftime('%H.%M')
    
    @staticmethod
    def fileBase(SWATBasin: int, relhru: int) -> str:
        """
        Return the string used to name SWAT input files 
        from basin and relative HRU number.
        """
        return '{0:05d}{1:04d}'.format(SWATBasin, relhru)
    
    @staticmethod
    def getSlsubbsn(meanSlope: float) -> int:
        """Estimate the average slope length in metres from the mean slope."""     
        if meanSlope < 0.01: return 120
        elif meanSlope < 0.02: return 100
        elif meanSlope < 0.03: return 90
        elif meanSlope < 0.05: return 60
        else: return 30
        
    @staticmethod
    def setXMLValue(xmlFile: str, tag: str, attName: str, attVal: str, tagVal: str) -> Tuple[bool, str]:
        """
        In xmlFile, sets the value of node tag with attName equal to attVal to tagVal.
        
        Return true and empty string if ok, else false and an error string.
        """
        doc: QDomDocument = QDomDocument()
        f: QFile = QFile(xmlFile)
        done = False
        if f.open(QIODevice.ReadWrite):
            if doc.setContent(f):
                tagNodes: QDomNodeList = doc.elementsByTagName(tag)
                for i in range(tagNodes.length()):
                    tagNode: QDomNode = tagNodes.item(i)
                    atts: QDomNamedNodeMap = tagNode.attributes()
                    key: QDomNode = atts.namedItem(attName)
                    if key is not None:
                        att: QDomAttr = key.toAttr()
                        val: str = att.value()
                        if val == attVal:
                            textNode: QDomText = tagNode.firstChild().toText()
                            textNode.setNodeValue(tagVal)
                            newVal: str = tagNode.firstChild().toText().nodeValue()
                            if newVal != tagVal:
                                return False, 'found new XML value of {0} instead of {1}'.format(newVal, val)
                            done = True
                            break
                if not done:
                    return False, 'Failed to find {0} node with {1}={2} in {3}'.format(tag, attName, attVal, xmlFile)
            else:
                return False, 'Failed to read XML file {0}'.format(xmlFile)
        else:
            return False, 'Failed to open XML file {0}'.format(xmlFile)
        f.resize(0)
        strm: QTextStream = QTextStream(f)
        doc.save(strm, 4)
        f.close()
        return True, ''
    
    @staticmethod
    def nearestPoint(point: QgsPointXY, points: List[QgsPointXY]) -> QgsPointXY:
        """Return point in points nearest to point, or point itself if points is empty."""
        if points is None or len(points) == 0:
            return point
        if len(points) == 1:
            return points[0]
        minm: float = float('inf')
        nearest: QgsPointXY = point
        pointx: float = point.x()
        pointy: float = point.y()
        for pt in points:
            dx: float = pt.x() - pointx
            dy: float = pt.y() - pointy
            measure: float = dx * dx + dy * dy
            if measure < minm:
                minm = measure
                nearest = pt
        return nearest
    
    @staticmethod
    def getPluginPath() -> str:
        """Get path of plugin."""
        return os.path.dirname(os.path.realpath(__file__))

    @staticmethod              
    def landscapeUnitId(SWATChannel: int, landscape: int) -> int:
        """Calculate landscape unit id from SWAT channel and landscape."""
        
        # SWATVhannel is alreay unique across the watershed
        # Currently landscape ia zero (no landscape division)
        # else 1 (floodplain) or 2 (upslope)
        # This method allows for further landscape divisions in future, e.g.left/right
        # If this method is changed landscapeIdIsUpslope needs to be changed
        return SWATChannel * 10 + landscape
    
    @staticmethod
    def landscapeUnitIdIsUpslope(lsuId):
        """Return true if landscape id is for an upslope landscape."""
        # note this depends on the encoding used in landscapeUnitId and landscapeName
        lscape = lsuId % 10
        return lscape != 0 and lscape % 2 == 0
    
    @staticmethod
    def landscapeName(lscape: int, useLeftRight: bool, notEmpty=False):
        """Return landscape unit name."""
        if lscape == QSWATUtils._NOLANDSCAPE: result = 'NA' if notEmpty else ''
        elif lscape == QSWATUtils._FLOODPLAIN: result = 'Left floodplain' if useLeftRight else 'Floodplain'
        elif lscape == QSWATUtils._UPSLOPE: result = 'Left upslope' if useLeftRight else 'Upslope'
        elif lscape == 3: result = 'Right floodplain'
        elif lscape == 4: result = 'Right upslope'
        elif lscape == 5: result = 'Head floodplain'
        elif lscape == 6: result = 'Head upslope'
        else:
            raise ValueError('Unknown landscape unit {0}'.format(lscape))
        #return result + ' ({0})'.format(QSWATUtils.landscapeAbbreviation(lscape, useLeftRight))
        return result
    
    @staticmethod
    def landscapeFromName(name: QVariant) -> int:
        """Return landscape code."""
        if name is None or name == '' or name == 'NA': return QSWATUtils._NOLANDSCAPE
        elif name == 'Floodplain': return QSWATUtils._FLOODPLAIN
        elif name == 'Upslope': return QSWATUtils._UPSLOPE
        else:
            raise ValueError('Unknown landscape name {0}'.format(name))  # TODO: complete this when left/right in use
    
    # currently not used    
    @staticmethod
    def landscapeAbbreviation(lsu: int, useLeftRight: bool) -> str:
        """Return landscape unit abbreviated name."""
        if lsu == QSWATUtils._NOLANDSCAPE: return ''
        elif lsu == QSWATUtils._FLOODPLAIN: return 'LFlood' if useLeftRight else 'Flood'
        elif lsu == QSWATUtils._UPSLOPE: return 'LUp' if useLeftRight else 'Up'
        elif lsu == 3: return 'RFlood'
        elif lsu == 4: return 'RUp'
        elif lsu == 5: return 'HFlood'
        else: return 'HUp'
        
    @staticmethod
    def polyCombine(geom1, geom2):
        """Combines two polygon or multipolygon geometries by simply appending one list to the other.
        
        Not ideal, as polygons may abut and this leaves a line between them, 
        but usful when QgsGeometry.combine fails.
        Assumes both geomtries are polygon or multipolygon type"""
        if geom1.wkbType() == QgsWkbTypes.Polygon:
            list1 = [geom1.asPolygon()]
        else:
            list1 = geom1.asMultiPolygon() 
        if geom2.wkbType() == QgsWkbTypes.MultiPolygon:
            list2 = [geom2.asPolygon()]
        else:
            list2 = geom2.asMultiPolygon()
        return QgsGeometry.fromMultiPolygonXY(list1 + list2)

        
T = TypeVar('T', str, int, float)
 
 
class ListFuns(Generic[T]):
    """Inserted list function."""  
 
    @staticmethod
    def insertIntoSortedList(val: T, vals: List[T], unique: bool) -> bool:
        """
        Insert val into assumed sorted list vals.  
        If unique is true and val already in vals do nothing.
        Return true if insertion made.
         
        Note function is polymorphic: used for lists of integers and lists of strings
        """
        for index in range(len(vals)):
            nxt: T = vals[index]
            if nxt == val:
                if unique:
                    return False
                else:
                    vals.insert(index, val)
                    return True
            if nxt > val:
                vals.insert(index, val)
                return True
        vals.append(val)
        return True
 
 
U = TypeVar('U')
 
 
class MapFuns(Generic[U]):
    """Map flattening function."""
     
    @staticmethod
    def flattenMap(mmap: Dict[U, U]) -> Dict[U, U]:
        """
        Map each domain element to its final target.  If for example we have [A->B, B->C] then return [A->C, B->C].
        """
        result: Dict[U, U] = dict()
        for a, b in mmap.items():
            result[a] = MapFuns.transApply(b, mmap)
        return result
     
    @staticmethod
    def transApply(b: U, mmap: Dict[U, U]) -> U:
        """
        b is a range element.  If it is not a domain element, return it.
        Else continue with mmap[b] as the next range element.
         
        mmap is assumed not to be circular.
        """
        nxt: U = mmap.get(b, None)
        if nxt is None:
            return b
        else:
            return MapFuns.transApply(nxt, mmap)


class fileWriter:
    
    """
    Class effectively extending writer with a writeLine method
    """
    
    # should be automatically changed for Windows, but isn't
    _END_LINE = os.linesep # '\r\n' for Windows
    
    def __init__(self, path):
        """Initialise class variables."""
        ## writer
        self.writer = open(path, 'w')
        ## write method
        self.write = self.writer.write
        ## close
        self.close = self.writer.close
    
    def writeLine(self, string):
        """Write string plus end-of-line."""
        self.writer.write(string + '\n')
        
    def __enter__(self):
        """Return self."""
        return self
        
    def __exit__(self, typ, value, traceback):  # @UnusedVariable
        """Close."""
        self.writer.close()
        
class FileTypes:
    
    """File types for various kinds of file that will be loaded, 
    and utility functions.
    """
    
    _DEM = 0
    _MASK = 1
    _BURN = 2
    _OUTLETS = 3
    _STREAMS = 4
    _SUBBASINS = 5
    _LANDUSES = 6
    _SOILS = 7
    _SLOPEBANDS = 8
    _CHANNELREACHES = 9
    _WATERSHED = 10
    _EXISTINGSUBBASINS = 11
    _EXISTINGWATERSHED = 12
    _HILLSHADE = 13
    _GRID = 14
    _GRIDSTREAMS = 15
    _DRAINSTREAMS = 16
    _BUFFERSHAPE = 17
    _BUFFERFLOOD = 18
    _INVFLOOD = 19
    _BRANCHFLOOD = 20
    _CSV = 21
    _SQLITE = 22
    _CHANNELS = 23
    _CHANNELBASINSRASTER = 24
    _LSUS = 25
    _STREAMREACHES = 26
    _LAKES = 27
    _EXTRAPTSRCANDRES = 28
    _HRUS = 29
    _OTHER = 99
    
    @staticmethod
    def filter(ft: int) -> str:
        """Return filter for open file dialog according to file type."""
        if ft == FileTypes._DEM or ft == FileTypes._LANDUSES or ft == FileTypes._SOILS or \
            ft == FileTypes._HILLSHADE or ft == FileTypes._BUFFERFLOOD or ft == FileTypes._CHANNELBASINSRASTER:
            return QgsProviderRegistry.instance().fileRasterFilters()
        elif ft == FileTypes._MASK:
            return 'All files (*)' # TODO: use dataprovider.fileRasterFilters + fileVectorFilters
        elif ft == FileTypes._BURN or ft == FileTypes._OUTLETS or \
                    ft == FileTypes._STREAMS or ft == FileTypes._SUBBASINS or \
                    ft == FileTypes._CHANNELREACHES or ft == FileTypes._STREAMREACHES or ft == FileTypes._WATERSHED or \
                    ft == FileTypes._EXISTINGSUBBASINS or ft == FileTypes._EXISTINGWATERSHED or \
                    ft == FileTypes._GRID or ft == FileTypes._GRIDSTREAMS or ft == FileTypes._DRAINSTREAMS or \
                    ft == FileTypes._BUFFERSHAPE or ft == FileTypes._CHANNELS or ft == FileTypes._LAKES or \
                    ft == FileTypes._EXTRAPTSRCANDRES:
            return QgsProviderRegistry.instance().fileVectorFilters()
        elif ft == FileTypes._CSV:
            return 'CSV files (*.csv);;All files (*)'
        elif ft == FileTypes._SQLITE:
            return 'SQLite files (*.sqlite *.db *.sdb *.db3 *.s3db *.sqlite3 *.sl3);;All files (*)'
        else:
            return 'All files (*)'
    
    @staticmethod
    def isRaster(ft: int) -> bool:
        if ft == FileTypes._DEM or ft == FileTypes._LANDUSES or ft == FileTypes._SOILS or \
                ft == FileTypes._SLOPEBANDS or ft == FileTypes._HILLSHADE or ft == FileTypes._BUFFERFLOOD or \
                ft == FileTypes._INVFLOOD or ft == FileTypes._BRANCHFLOOD or ft == FileTypes._CHANNELBASINSRASTER:
            return True
        else:
            return False
        
    @staticmethod
    def legend(ft: int) -> str:
        """Legend entry string for file type ft."""
        if ft == FileTypes._DEM:
            return 'DEM'
        elif ft == FileTypes._MASK:
            return 'Mask'
        elif ft == FileTypes._BURN:
            return 'Stream burn-in'
        elif ft == FileTypes._OUTLETS:
            return 'Inlets/outlets'
        elif ft == FileTypes._STREAMS:
            return QSWATUtils._STREAMSLEGEND
        elif ft == FileTypes._SUBBASINS or ft == FileTypes._EXISTINGSUBBASINS:
            return QSWATUtils._SUBBASINSLEGEND
        elif ft == FileTypes._LANDUSES:
            return 'Landuses'
        elif ft == FileTypes._SOILS:
            return 'Soils'
        elif ft == FileTypes._SLOPEBANDS:
            return 'Slope bands'
        elif ft == FileTypes._WATERSHED or ft == FileTypes._EXISTINGWATERSHED:
            return QSWATUtils._WATERSHEDLEGEND
        elif ft == FileTypes._CHANNELREACHES:
            return 'Channel reaches'
        elif ft == FileTypes._STREAMREACHES:
            return 'Stream reaches'
        elif ft == FileTypes._HILLSHADE:
            return QSWATUtils._HILLSHADELEGEND
        elif ft == FileTypes._GRID:
            return QSWATUtils._GRIDLEGEND
        elif ft == FileTypes._GRIDSTREAMS:
            return QSWATUtils._GRIDSTREAMSLEGEND
        elif ft == FileTypes._DRAINSTREAMS:
            return QSWATUtils._DRAINSTREAMSLEGEND
        elif ft == FileTypes._BUFFERFLOOD or ft == FileTypes._BUFFERSHAPE:
            return QSWATUtils._BUFFERFLOODLEGEND
        elif ft == FileTypes._INVFLOOD:
            return QSWATUtils._INVFLOODLEGEND
        elif ft == FileTypes._BRANCHFLOOD:
            return QSWATUtils._BRANCHFLOODLEGEND
        elif ft == FileTypes._CHANNELS:
            return QSWATUtils._CHANNELSLEGEND
        elif ft == FileTypes._LAKES:
            return QSWATUtils._LAKESLEGEND
        elif ft == FileTypes._EXTRAPTSRCANDRES:
            return QSWATUtils._EXTRAPTSRCANDRESLEGEND
        else:
            return ''
        
    @staticmethod
    def styleFile(ft: int) -> Optional[str]:
        """.qml file, if any, for file type ft."""
        if ft == FileTypes._DEM:
            return None
        elif ft == FileTypes._MASK:
            return None
        elif ft == FileTypes._BURN:
            return None
        elif ft == FileTypes._OUTLETS:
            return 'outlets.qml'
        elif ft == FileTypes._STREAMS or ft == FileTypes._STREAMREACHES:
            return 'stream.qml'
        elif ft == FileTypes._CHANNELS or ft == FileTypes._GRIDSTREAMS:
            return 'channel.qml'
        elif ft == FileTypes._CHANNELREACHES:
            return 'channelandreservoir.qml'
        elif ft == FileTypes._SUBBASINS:
            return 'wshed.qml'
        elif ft == FileTypes._EXISTINGSUBBASINS:
            return 'existingwshed.qml'
        elif ft == FileTypes._WATERSHED or ft == FileTypes._EXISTINGWATERSHED:
            return 'lsus.qml'
        elif ft == FileTypes._GRID:
            return 'grid.qml'
        elif ft == FileTypes._DRAINSTREAMS:
            return 'drainchannels.qml'
        elif ft == FileTypes._EXTRAPTSRCANDRES:
            return 'ptsrcandreservoir.qml'
        elif ft == FileTypes._LANDUSES:
            return None
        elif ft == FileTypes._SOILS:
            return None
        elif ft == FileTypes._SLOPEBANDS:
            return None
        elif ft == FileTypes._HILLSHADE:
            return None
        elif ft == FileTypes._BUFFERFLOOD or ft == FileTypes._INVFLOOD or ft == FileTypes._BRANCHFLOOD:
            return 'flood.qml'
        elif ft == FileTypes._LAKES:
            return 'lakes.qml'
        else:
            return None

    @staticmethod
    def title(ft: int) -> str:
        """Title for open file dialog for file type ft."""
        if ft == FileTypes._DEM:
            return 'Select DEM'
        elif ft == FileTypes._MASK:
            return 'Select mask'
        elif ft == FileTypes._BURN:
            return 'Select stream reaches shapefile to burn-in'
        elif ft == FileTypes._OUTLETS:
            return 'Select inlets/outlets shapefile'
        elif ft == FileTypes._STREAMS:
            return 'Select streams shapefile'
        elif ft == FileTypes._CHANNELS:
            return 'Select channels shapefile'
        elif ft == FileTypes._SUBBASINS or ft == FileTypes._EXISTINGSUBBASINS:
            return 'Select subbasins shapefile'
        elif ft == FileTypes._WATERSHED or ft == FileTypes._EXISTINGWATERSHED:
            return 'Select watershed shapefile'
        elif ft == FileTypes._LANDUSES:
            return 'Select landuses file'
        elif ft == FileTypes._SOILS:
            return 'Select soils file'
        elif ft == FileTypes._SLOPEBANDS or ft == FileTypes._CHANNELREACHES or ft == FileTypes._STREAMREACHES or \
                ft == FileTypes._HILLSHADE or ft == FileTypes._GRID:
            return ''
        elif ft == FileTypes._CSV:
            return 'Select drainage csv file'
        elif ft == FileTypes._SQLITE:
            return 'Select SQLite database'
        elif ft == FileTypes._CHANNELBASINSRASTER:
            return 'Select channel basins raster'
        elif ft ==FileTypes._LAKES:
            return 'Select lakes shapefile'
        else:
            return ''
        
    @staticmethod
    def multipleLayersAllowed(ft: int) -> bool:
        """True if more than one layer can exist with the same legend."""
        if ft == FileTypes._BUFFERFLOOD:
            return True
        elif ft == FileTypes._INVFLOOD:
            return True
        elif ft == FileTypes._BRANCHFLOOD:
            return True
        return False
        
    @staticmethod
    def colourFun(ft: int) -> Optional[Callable[[QgsRasterLayer, Any], None]]:
        """Layer colouring function for raster layer of file type ft."""
        if ft == FileTypes._DEM:
            return FileTypes.colourDEM
        elif ft == FileTypes._LANDUSES:
            return FileTypes.colourLanduses
        elif ft == FileTypes._SOILS:
            return FileTypes.colourSoils
        elif ft == FileTypes._SLOPEBANDS:
            return FileTypes.colourSlopes
        elif ft == FileTypes._BUFFERFLOOD or ft == FileTypes._INVFLOOD or ft == FileTypes._BRANCHFLOOD:
            return FileTypes.colourFlood
        else:
            return None

    @staticmethod
    def colourDEM(layer: QgsRasterLayer, _) -> None:
        """Layer colouring function for DEM."""
        shader: QgsRasterShader = QgsRasterShader()
        stats: QgsRasterBandStats = layer.dataProvider().bandStatistics(1,
                                                                        QgsRasterBandStats.Min | QgsRasterBandStats.Max)
        minVal: int = int(stats.minimumValue + 0.5)
        maxVal: int = int(stats.maximumValue + 0.5)
        mean: int = (minVal + maxVal) // 2
        s1: str = str((minVal * 2 + maxVal) // 3)
        s2: str = str((minVal + maxVal * 2) // 3)
        item0: QgsColorRampShader.ColorRampItem = \
            QgsColorRampShader.ColorRampItem(minVal, QColor(10, 100, 10), str(minVal) + ' - ' + s1)
        item1: QgsColorRampShader.ColorRampItem = \
            QgsColorRampShader.ColorRampItem(mean, QColor(153, 125, 25), s1 + ' - ' + s2)
        item2: QgsColorRampShader.ColorRampItem = \
            QgsColorRampShader.ColorRampItem(maxVal, QColor(255, 255, 255), s2 + ' - ' + str(maxVal))
        fcn: QgsColorRampShader = QgsColorRampShader(minVal, maxVal)
        fcn.setColorRampType(QgsColorRampShader.Interpolated)
        fcn.setColorRampItemList([item0, item1, item2])
        shader.setRasterShaderFunction(fcn)
        renderer: QgsSingleBandPseudoColorRenderer = QgsSingleBandPseudoColorRenderer(layer.dataProvider(), 1, shader)
        layer.setRenderer(renderer)
        
        layer.triggerRepaint()
        
    @staticmethod
    def colourLanduses(layer: QgsRasterLayer, db: Any) -> None:
        """Layer colouring function for landuse grid."""
        shader: QgsRasterShader = QgsRasterShader()
        items: List[QgsColorRampShader.ColorRampItem] = []
        for i in db.landuseVals:
            luse: str = db.getLanduseCode(i)
            item: QgsColorRampShader.ColorRampItem = \
                QgsColorRampShader.ColorRampItem(int(i), FileTypes.randColor(), luse)
            items.append(item)
        fcn: QgsColorRampShader = QgsColorRampShader()
        fcn.setColorRampType(QgsColorRampShader.Discrete)
        fcn.setColorRampItemList(items)
        shader.setRasterShaderFunction(fcn)
        renderer: QgsSingleBandPseudoColorRenderer = \
            QgsSingleBandPseudoColorRenderer(layer.dataProvider(), 1, shader)
        layer.setRenderer(renderer)
        layer.triggerRepaint()
    
    @staticmethod
    def colourSoils(layer: QgsRasterLayer, db: Any) -> None:
        """Layer colouring function for soil grid."""
        shader: QgsRasterShader = QgsRasterShader()
        items: List[QgsColorRampShader.ColorRampItem] = []
        if db.useSSURGO:
            for i in db.ssurgoSoils:
                item: QgsColorRampShader.ColorRampItem = \
                    QgsColorRampShader.ColorRampItem(int(i), FileTypes.randColor(), str(i))
                items.append(item)    
        else:
            for i, name in db.usedSoilNames.items():
                item = QgsColorRampShader.ColorRampItem(int(i), FileTypes.randColor(), name)
                items.append(item)
        fcn: QgsColorRampShader = QgsColorRampShader()
        fcn.setColorRampType(QgsColorRampShader.Discrete)
        fcn.setColorRampItemList(items)
        shader.setRasterShaderFunction(fcn)
        renderer: QgsSingleBandPseudoColorRenderer = \
            QgsSingleBandPseudoColorRenderer(layer.dataProvider(), 1, shader)
        layer.setRenderer(renderer)
        layer.triggerRepaint()
        
    @staticmethod
    def colourSlopes(layer: QgsRasterLayer, db: Any) -> None:
        """Layer colouring for slope bands grid."""
        shader: QgsRasterShader = QgsRasterShader()
        items: List[QgsColorRampShader.ColorRampItem] = []
        numItems: int = len(db.slopeLimits) + 1
        for n in range(numItems):
            colour: int = int(5 + float(245) * (numItems - 1 - n) / (numItems - 1))
            item: QgsColorRampShader.ColorRampItem = \
                QgsColorRampShader.ColorRampItem(n, QColor(colour, colour, colour), db.slopeRange(n))
            items.append(item)
        fcn: QgsColorRampShader = QgsColorRampShader()
        fcn.setColorRampType(QgsColorRampShader.Discrete)
        fcn.setColorRampItemList(items)
        shader.setRasterShaderFunction(fcn)
        renderer: QgsSingleBandPseudoColorRenderer = \
            QgsSingleBandPseudoColorRenderer(layer.dataProvider(), 1, shader)
        layer.setRenderer(renderer)
        layer.triggerRepaint()
        
    @staticmethod
    def colourFlood(layer: QgsRasterLayer, _) -> None:
        """Layer colouring for floodplain rasters."""
        renderer: QgsSingleBandGrayRenderer = QgsSingleBandGrayRenderer(layer.dataProvider(), 1)
        renderer.setGradient(QgsSingleBandGrayRenderer.BlackToWhite)
        enhancement: QgsContrastEnhancement = QgsContrastEnhancement()
        enhancement.setMinimumValue(0)
        enhancement.setMaximumValue(1)
        renderer.setContrastEnhancement(enhancement)
        layer.setRenderer(renderer)
        layer.triggerRepaint()
    
    @staticmethod
    def randColor() -> QColor:
        """Return random QColor."""
        return QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    
