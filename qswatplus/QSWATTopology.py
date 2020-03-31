# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QSWAT
                                 A QGIS plugin
 Create SWAT inputs
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
from osgeo import gdal
from numpy import * # @UnusedWildImport
import os.path
import time
import csv
import traceback

try:
    from .QSWATUtils import QSWATUtils, FileTypes, ListFuns
    from .DBUtils import DBUtils
    from .parameters import Parameters
    from .raster import Raster
    from .dataInC import ReachData, MergedChannelData, LakeData  # @UnresolvedImport
except:
    # used by convertFromArc
    from QSWATUtils import QSWATUtils, FileTypes, ListFuns
    from DBUtils import DBUtils
    from parameters import Parameters
    from raster import Raster
    from dataInC import ReachData, MergedChannelData, LakeData  # @UnresolvedImport

class QSWATTopology:
    
    """Module for creating and storing topological data 
    derived from watershed delineation.
    
    Nomenclature:  From TauDEM we have channels and also streams, each with link and wsno values.
    We translate as follows:
    channel link: channel
    channel wsno: chBasin
    stream link: stream
    stream wsno: [sub]basin
    These all have numbers from zero.  To avoid zero ids in the output, a SWATchannel etc has an id
    of at least one.
    Unlike QSWAT, we do not guarantee SWAT identifiers will form a continuous range 1..n.
    """
    
    ## Value used to indicate no basin since channel is zero length and has no points.
    ## Must be negative (since TauDEM basin (WSNO) numbers go from 0 up
    ## and must not be -1 since this indicates a 'not found' in most gets, or a main outlet
    _NOBASIN = -2
    
    _RESTYPE = 1
    _PONDTYPE = 2
    
    _LINKNO = 'LINKNO'
    _DSLINKNO = 'DSLINKNO'
    _USLINKNO1 = 'USLINKNO1'
    _USLINKNO2 = 'USLINKNO2'
    _DSNODEID = 'DSNODEID'
    _DRAINAREA = 'DS_Cont_Ar' if Parameters._ISWIN else 'DSContArea'
    _DRAINAGE = 'Drainage'
    _ORDER = 'Order' if Parameters._ISWIN else 'strmOrder'
    _LENGTH = 'Length'
    _MAGNITUDE = 'Magnitude'
    _DROP = 'Drop' if Parameters._ISWIN else 'strmDrop'
    _SLOPE = 'Slope'
    _STRAIGHTL = 'Straight_L' if Parameters._ISWIN else 'StraightL'
    _USCONTAR = 'US_Cont_Ar' if Parameters._ISWIN else 'USContArea'
    _WSNO = 'WSNO'
    _DOUTEND = 'DOUT_END' if Parameters._ISWIN else 'DOUTEND'
    _DOUTSTART = 'DOUT_START' if Parameters._ISWIN else 'DOUTSTART'
    _DOUTMID =  'DOUT_MID' if Parameters._ISWIN else 'DOUTMID'
    _BASINNO = 'BasinNo'
    _ID = 'ID'
    _INLET = 'INLET'
    _RES = 'RES'
    _PTSOURCE = 'PTSOURCE'
    _POLYGONID = 'PolygonId'
    _DOWNID = 'DownId'
    _STREAMLINK = 'StreamLink'
    _STREAMLEN = 'StreamLen'
    _DSNODEIDW = 'DSNodeID'
    _DSWSID = 'DSWSID'
    _US1WSID = 'US1WSID'
    _US2WSID = 'US2WSID'
    _SUBBASIN = 'Subbasin'
    _CHANNEL = 'Channel'
    _CHANNELR = 'ChannelR'
    _LANDSCAPE = 'Landscape'
    _AQUIFER = 'Aquifer'
    _LSU = 'LSU'
    _LSUID = 'LSUID'
    _PENWIDTH = 'PenWidth'
    _HRUS = 'HRUS'
    _HRUGIS = 'HRUGIS'
    _LAKEID = 'LakeId'
    _RESERVOIR = 'Reservoir'
    _POND = 'Pond'
    _AREAC = 'AreaC'
    _LEN2 = 'Len2'
    _SLO2 = 'Slo2'
    _WID2 = 'Wid2'
    _DEP2 = 'Dep2'
    _MINEL = 'MinEl'
    _MAXEL = 'MaxEl'
    _LAKEIN = 'LakeIn'
    _LAKEOUT = 'LakeOut'
    _LAKEWITHIN = 'LakeWithin'
    _LAKEMAIN = 'LakeMain'
    
    
    def __init__(self, isBatch):
        """Initialise class variables."""
        ## Link to project database
        self.db = None
        ## True if outlet end of reach is its first point, i.e. index zero."""
        self.outletAtStart = True
        ## index to LINKNO in channel shapefile
        self.channelIndex = -1
        ## index to DSLINKNO in channel shapefile
        self.dsChannelIndex = -1
        ## relation between channel basins and subbasins
        # not used with grid models (since would be 1-1)
        self.chBasinToSubbasin = dict()
        ## WSNO does not obey SWAT rules for element numbers (> 0) 
        # so we invent and store SWATBasin numbers
        # also SWAT basins may not be empty
        # not complete: zero areas/stream lengths excluded
        self.subbasinToSWATBasin = dict()
        ##inverse map to make it easy to output in numeric order of SWAT Basins
        self.SWATBasinToSubbasin = dict()
        ## original channel links may have zero numbers and may have zero lengths
        ## so we generate SWATChannel ids
        # not complete
        self.channelToSWATChannel = dict()
        ## inverse map
        self.SWATChannelToChannel = dict()
        ## subbasin to stream mapping (wsno to link fields in streams shapefile)
        # complete
        self.subbasinToStream = dict()
        ## stream to downstream (link to dslink in streams shapefile)
        # complete
        self.downStreams = dict()
        ## stream lengths (link to length in streams shapefile).  Lengths are in metres
        # complete
        self.streamLengths = dict()
        ## LINKNO to DSLINKNO in channel shapefile
        # complete = all channel links defined
        self.downChannels = dict()
        ## zero length channels
        self.zeroChannels = set()
        ## subbasin to downstream subbasin
        # incomplete: no empty basins (zero length streams or missing wsno value in subbasins layer)
        self.downSubbasins = dict()
        ## map from channel to chBasin
        # incomplete - no zero length channels
        self.chLinkToChBasin = dict()
        ## reverse of chLinkToChBasin
        self.chBasinToChLink = dict()
        ## centroids of basins as (x, y) pairs in projected units
        self.basinCentroids = dict()
        ## channel link to channel length in metres:
        # complete
        self.channelLengths = dict()
        ## channel slopes in m/m
        # complete
        self.channelSlopes = dict()
        ## numpy array of total area draining to downstream end of channel in square metres
        self.drainAreas = None
        ## map of lake id to ids of points added to split channels entering lakes
        self.lakeInlets = dict()
        ## map of lake id to ids of points added to split channels leaving lakes
        self.lakeOutlets = dict()
        ## map of channel to ReachData: points and elevations at ends of channels, plus basin
        # not complete: zero areas/channel lengths excluded
        self.channelsData = dict()
        ## map of lake id to LakeData for lakes defined by shapefile
        self.lakesData = dict()
        ## map of channel links to lake ids: channel flowing into lake
        self.chLinkIntoLake = dict()
        ## map of channel links to lake ids: channel completely inside lake
        self.chLinkInsideLake = dict()
        ## map of channel links to lake ids: channel flowing out of lake
        self.chLinkFromLake = dict()
        ## map of subbasin to lake id for subbasins with their outlet inside a lake (non-grid models only)
        self.outletsInLake = dict()
        ## channel basin to area in square metres.  Not used with grid model.
        self.chBasinAreas = dict()
        ## current point id (for outlets, inlets and point sources)
        self.pointId = 0
        ## current water body id (for lakes, reservoirs and ponds)
        self.waterBodyId = 0
        ## channel links to reservoir or pond point ids plus water type: reservoir or pond discharges into channel
        self.chLinkToWater = dict()
        ## channel links with point sources flowing into them (defined by inlets/outlets file)
        self.chLinkToPtSrc = dict()
        ## channel links to watershed inlets (for grid models only)
        self.chLinkToInlet = dict()
        ## basins draining to inlets
        self.upstreamFromInlets = set()
        ## width of DEM cell in metres
        self.dx = 0
        ## depth of DEM cell in metres
        self.dy = 0
        ## x direction threshold for points to be considered coincident
        self.xThreshold = 0
        ## y direction threshold for points to be considered coincident
        self.yThreshold = 0
        ## multiplier to turn DEM elevations to metres
        self.verticalFactor = 1
        ## DEM nodata value
        self.demNodata = 0
        ## DEM extent
        self.demExtent = None
        ## map from subbasin to outlet pointId, point, and channel draining to it
        self.outlets = dict()
        ## map from subbasin to inlet pointId and point (not used with grid models)
        self.inlets = dict()
        ## map from channel links to point sources
        self.chPointSources = dict()
        ## reservoirs found by converting water HRUs
        self.foundReservoirs = dict()
        ## project projection (set from DEM)
        self.crsProject = None
        ## lat-long coordinate reference system
        self.crsLatLong = QgsCoordinateReferenceSystem()
        if not self.crsLatLong.createFromId(4326, QgsCoordinateReferenceSystem.EpsgCrsId):
            QSWATUtils.error('Failed to create lat-long coordinate reference system', isBatch)
        ## transform from project corrdinates to lat-long
        self.transformToLatLong = None
        ## Flag to show if batch run
        self.isBatch = isBatch
        ## table for memorizing distances from basin to join in flowpath with other basin:
        # basin -> otherBasin -> join distance in metres
        self.distancesToJoins = dict()
        ## table for use in existing non-grid models of maximum channel flow lengths in metres to subbasin outlets
        # complete
        self.maxFlowLengths = dict()
        ## number of chunks to use for rasters and their arrays; increased when memory fails
        self.chunkCount = 1
        ## dsNodeIds that cannot be retained when making grids as they would be in same grid cell as another point
        self.lostDsNodeIds = set()
        
    def setUp0(self, demLayer, channelLayer, outletLayer, ad8Layer, verticalFactor, useGridModel):
        """Set DEM size parameters and stream orientation, and store source and outlet points for stream reaches."""
        # can fail if demLayer is None or not projected
        try:
            self.setCrs(demLayer)
            units = self.crsProject.mapUnits()
        except Exception:
            QSWATUtils.loginfo('Failure to read DEM units: {0}'.format(traceback.format_exc()))
            return False
        if units == QgsUnitTypes.DistanceMeters:
            factor = 1
        elif units == QgsUnitTypes.DistanceFeet:
            factor = Parameters._FEETTOMETRES
        else:
            # unknown or degrees - will be reported in delineation - just quietly fail here
            QSWATUtils.loginfo('Failure to read DEM units: {0}'.format(str(units)))
            return False
        self.dx = demLayer.rasterUnitsPerPixelX() * factor
        self.dy = demLayer.rasterUnitsPerPixelY() * factor
        self.xThreshold = self.dx * Parameters._NEARNESSTHRESHOLD
        self.yThreshold = self.dy * Parameters._NEARNESSTHRESHOLD
        QSWATUtils.loginfo('Factor is {0}, cell width is {1}, cell depth is {2}'.format(factor, self.dx, self.dy))
        self.demExtent = demLayer.extent()
        self.verticalFactor = verticalFactor
        self.outletAtStart = self.hasOutletAtStart(channelLayer, ad8Layer)
        QSWATUtils.loginfo('Outlet at start is {0!s}'.format(self.outletAtStart))
        return self.saveOutletsAndSources(channelLayer, outletLayer, useGridModel)
    
    def setCrs(self, demLayer):
        """Set crsProject and transformToLatLong if necessary."""
        if self.crsProject is None:
            self.crsProject = demLayer.crs()
            self.transformToLatLong = QgsCoordinateTransform(self.crsProject, self.crsLatLong, QgsProject.instance())
            QgsProject.instance().setCrs(self.crsProject)
            settings = QSettings()
            settings.setValue('Projections/defaultBehaviour', 'useProject')
    
    def setUp1(self, streamLayer):
        """Establish subbasinToStream, downStreams and streamLengths dictionaries.
        
        Used when calculating ridges by branch length method and setUp has not been run yet."""
        self.subbasinToStream.clear()
        self.downStreams.clear()
        self.streamLengths.clear()
        streamIndex = self.getIndex(streamLayer, QSWATTopology._LINKNO)
        if streamIndex < 0:
            QSWATUtils.loginfo('No LINKNO field in stream layer')
            return False
        dsStreamIndex = self.getIndex(streamLayer, QSWATTopology._DSLINKNO)
        if dsStreamIndex < 0:
            QSWATUtils.loginfo('No DSLINKNO field in stream layer')
            return False
        lengthIndex = self.getIndex(streamLayer, QSWATTopology._LENGTH, True)
        wsnoIndex = self.getIndex(streamLayer, QSWATTopology._WSNO)
        if wsnoIndex < 0:
            QSWATUtils.loginfo('No WSNO field in stream layer')
            return False
        for reach in streamLayer.getFeatures():
            link = reach[streamIndex]
            dsLink = reach[dsStreamIndex]
            basin = reach[wsnoIndex]
            if lengthIndex < 0:
                length = reach.geometry().length()
            else:
                length = reach[lengthIndex]
            self.subbasinToStream[basin] = link
            self.downStreams[link] = dsLink
            self.streamLengths[link] = length
        return True
        
    def setUp(self, demLayer, channelLayer, subbasinsLayer, outletLayer, lakesLayer, gv, existing,
              recalculate, useGridModel, streamDrainage, reportErrors):
        """Create topological data from layers."""
        #QSWATUtils.loginfo('Channel layer {0}'.format(channelLayer.dataProvider().dataSourceUri()))
        #QSWATUtils.loginfo('Subbasins layer {0}'.format(subbasinsLayer.dataProvider().dataSourceUri()))
        self.db = gv.db
        self.chLinkToChBasin.clear()
        self.chBasinToChLink.clear()
        self.subbasinToSWATBasin.clear()
        self.SWATBasinToSubbasin.clear()
        self.channelToSWATChannel.clear()
        self.SWATChannelToChannel.clear()
        self.downChannels.clear()
        self.zeroChannels.clear()
        # do not clear centroids unless existing and not using grid model: 
        if existing and not useGridModel:
            self.basinCentroids.clear()
        self.channelLengths.clear()
        self.channelSlopes.clear()
        self.channelsData.clear()
        self.chLinkToWater.clear()
        self.chLinkToPtSrc.clear()
        self.chLinkToInlet.clear()
        self.distancesToJoins.clear()
        self.maxFlowLengths.clear()
        dsNodeToLink = dict()
        ignoreError = not reportErrors
        ignoreWithExisting = existing or not reportErrors
        ignoreWithGrid = useGridModel or not reportErrors
        ignoreWithGridOrExisting = ignoreWithGrid or ignoreWithExisting
        self.channelIndex = self.getIndex(channelLayer, QSWATTopology._LINKNO, ignoreMissing=ignoreError)
        if self.channelIndex < 0:
            QSWATUtils.loginfo('No LINKNO field in channels layer')
            return False
        self.dsChannelIndex = self.getIndex(channelLayer, QSWATTopology._DSLINKNO, ignoreMissing=ignoreError)
        if self.dsChannelIndex < 0:
            QSWATUtils.loginfo('No DSLINKNO field in channels layer')
            return False
        dsNodeIndex = self.getIndex(channelLayer, QSWATTopology._DSNODEID, ignoreMissing=ignoreWithExisting)
        wsnoIndex = self.getIndex(channelLayer, QSWATTopology._WSNO, ignoreMissing=ignoreError)
        if wsnoIndex < 0:
            QSWATUtils.loginfo('No WSNO field in channels layer')
            return False
        drainAreaIndex = self.getIndex(channelLayer, QSWATTopology._DRAINAREA, ignoreMissing=ignoreWithGridOrExisting)
        lengthIndex = self.getIndex(channelLayer, QSWATTopology._LENGTH, ignoreMissing=ignoreWithGridOrExisting)
        dropIndex = self.getIndex(channelLayer, QSWATTopology._DROP, ignoreMissing=ignoreWithGridOrExisting)
        polyIndex = self.getIndex(subbasinsLayer, QSWATTopology._POLYGONID, ignoreMissing=ignoreError)
        if polyIndex < 0:
            QSWATUtils.loginfo('No POLYGONID field in subbasins layer')
            return False
        subbasinIndex = self.getIndex(subbasinsLayer, QSWATTopology._SUBBASIN, ignoreMissing=ignoreWithGridOrExisting)
        if outletLayer is not None:
            if dsNodeIndex < 0:
                QSWATUtils.information('Warning: streams layer has no {0} field, so points in inlets/outlets file will be ignored'
                                       .format(QSWATTopology._DSNODEID), gv.isBatch)
            idIndex = self.getIndex(outletLayer, QSWATTopology._ID, ignoreMissing=ignoreError)
            if idIndex < 0:
                QSWATUtils.loginfo('No ID field in outlets layer')
                return False
            inletIndex = self.getIndex(outletLayer, QSWATTopology._INLET, ignoreMissing=ignoreError)
            if inletIndex < 0:
                QSWATUtils.loginfo('No INLET field in outlets layer')
                return False
            ptSourceIndex = self.getIndex(outletLayer, QSWATTopology._PTSOURCE, ignoreMissing=ignoreError)
            if ptSourceIndex < 0:
                QSWATUtils.loginfo('No PTSOURCE field in outlets layer')
                return False
            resIndex = self.getIndex(outletLayer, QSWATTopology._RES, ignoreMissing=ignoreError)
            if resIndex < 0:
                QSWATUtils.loginfo('No RES field in outlets layer')
                return False
        self.demNodata = demLayer.dataProvider().sourceNoDataValue(1)
        if not useGridModel:
            # upstream array will get very big for grid
            us = dict()
        time1 = time.process_time()
        maxChLink = 0
        SWATChannel = 0
        for channel in channelLayer.getFeatures():
            chLink = channel[self.channelIndex]
            dsChLink = channel[self.dsChannelIndex]
            chBasin = channel[wsnoIndex]
            geom = channel.geometry()
            if lengthIndex < 0 or recalculate:
                length = geom.length()
            else:
                length = channel[lengthIndex]
            data = self.getReachData(geom, demLayer)
            self.channelsData[chLink] = data
            if data and (dropIndex < 0 or recalculate):
                drop = data.upperZ - data.lowerZ
            elif dropIndex >= 0:
                drop = channel[dropIndex]
            else:
                drop = 0
            slope = 0 if length <= 0 else float(drop) / length
            dsNode = channel[dsNodeIndex] if dsNodeIndex >= 0 else -1
            if useGridModel and chBasin < 0:
                # it is the downstream channel link from an inlet, and has no basin
                pass
            else:
                # exit channels in grid model can have zero length
                if length > 0 or useGridModel: 
                    self.chLinkToChBasin[chLink] = chBasin
                    self.chBasinToChLink[chBasin] = chLink
                    SWATChannel += 1
                    self.channelToSWATChannel[chLink] = SWATChannel
                    self.SWATChannelToChannel[SWATChannel] = chLink
                else:
                    self.zeroChannels.add(chLink)
            maxChLink = max(maxChLink, chLink)
            self.downChannels[chLink] = dsChLink
            self.channelLengths[chLink] = length
            self.channelSlopes[chLink] = slope
            if dsNode >= 0:
                dsNodeToLink[dsNode] = chLink
                #QSWATUtils.loginfo('DSNode {0} mapped to channel link {1}'.format(dsNode, chLink))
            if dsChLink >= 0:
                if not useGridModel:
                    ups = us.get(dsChLink, None)
                    if ups is None:
                        us[dsChLink] = [chLink]
                    else:
                        ups.append(chLink)
                    # check we haven't just made the us relation circular
                    if QSWATTopology.reachable(dsChLink, [chLink], us):
                        QSWATUtils.error('Circular drainage network from channel link {0}'.format(dsChLink), self.isBatch)
                        return False
        time2 = time.process_time()
        QSWATUtils.loginfo('Topology setup for channels took {0} seconds'.format(int(time2 - time1)))
        if not useGridModel:
            self.setChannelBasinAreas(gv)
            if existing:
                # need to set centroids
                for polygon in subbasinsLayer.getFeatures():
                    basin = polygon[polyIndex]
                    centroid = polygon.geometry().centroid().asPoint()
                    self.basinCentroids[basin] = (centroid.x(), centroid.y())
                # find maximum channel flow length for each subbasin
                self.setMaxFlowLengths()
        time3 = time.process_time()
        QSWATUtils.loginfo('Topology setup of subbasin areas and centroids took {0} seconds'.format(int(time3 - time2)))
        if outletLayer is not None:
            features = outletLayer.getFeatures()
        else:
            features = []
        if dsNodeIndex >= 0:
            doneNodes = set()
            for point in features:
                dsNode = point[idIndex]
                if dsNode in doneNodes:
                    if reportErrors:
                        QSWATUtils.error('ID value {0} is used more than once in inlets/outlets file {1}.  Occurrences after the first are ignored'
                                         .format(dsNode, QSWATUtils.layerFilename(outletLayer)), self.isBatch)
                    chLink = -1    
                elif dsNode in self.lostDsNodeIds:
                    chLink = -1
                elif dsNode not in dsNodeToLink:
                    if reportErrors:
                        QSWATUtils.error('ID value {0} from inlets/outlets file {1} not found as DSNODEID in channels file {2}.  Will be ignored.'
                                         .format(dsNode, QSWATUtils.layerFilename(outletLayer), 
                                                QSWATUtils.layerFileInfo(channelLayer).filePath()), self.isBatch)
                    chLink = -1
                else:
                    chLink = dsNodeToLink[dsNode]
                doneNodes.add(dsNode)
                if chLink >= 0:
                    isInlet = point[inletIndex] == 1
                    isPtSource = point[ptSourceIndex] == 1
                    isReservoir = point[resIndex] == 1
                    isPond = point[resIndex] == 2
                    if lakesLayer is not None: 
                        # check if point is inside lake
                        inLake = False
                        for lake in lakesLayer.getFeatures():
                            lakeGeom = lake.geometry()
                            lakeRect = lakeGeom.boundingBox()
                            if QSWATTopology.polyContains(point.geometry().asPoint(), lakeGeom, lakeRect):
                                inLake = True
                                if isInlet:
                                    typ = 'Inlet'
                                elif isPtSource:
                                    typ = 'Point source'
                                elif isReservoir:
                                    typ = 'Reservoir'
                                elif isPond:
                                    typ = 'Pond'
                                else:
                                    # main outlets allowed within lakes
                                    break
                                lakeIdIndex = lakesLayer.fieldNameIndex(QSWATTopology._LAKEID)
                                QSWATUtils.information('{0} {1} is inside lake {2}.  Will be ignored.'.format(typ, point.id(), lake[lakeIdIndex]), self.isBatch)
                                break
                        if inLake:
                            continue
                    if isInlet:
                        if isPtSource:
                            pt = point.geometry().asPoint()
                            self.chLinkToPtSrc[chLink] = (self.nonzeroPointId(dsNode), pt)
                        elif useGridModel: # inlets collected in setUp0 for non-grids
                            pt = point.geometry().asPoint()
                            self.chLinkToInlet[chLink] = (self.nonzeroPointId(dsNode), pt)
                    elif isReservoir:
                        pt = point.geometry().asPoint()
                        self.chLinkToWater[chLink] = (self.nonzeroPointId(dsNode), pt, QSWATTopology._RESTYPE)
                    elif isPond:
                        pt = point.geometry().asPoint()
                        self.chLinkToWater[chLink] = (self.nonzeroPointId(dsNode), pt, QSWATTopology._PONDTYPE)
                    # else an outlet: nothing to do
                    
                    # check for user-defined outlets coincident with stream junctions
                    if chLink in self.zeroChannels and chLink not in self.chLinkIntoLake:
                        if isInlet: typ = 'Inlet'
                        elif isPtSource: typ = 'Point source'
                        elif isReservoir: typ = 'Reservoir'
                        elif isPond: typ = 'Pond'
                        else: typ = 'Outlet'
                        msg = '{0} with id {1} has a zero length channel leading to it: please remove or move downstream'.format(typ, dsNode)
                        if reportErrors:
                            QSWATUtils.error(msg, self.isBatch)
                        else:
                            QSWATUtils.loginfo(msg)
                        return False
        time4 = time.process_time()
        QSWATUtils.loginfo('Topology setup for inlets/outlets took {0} seconds'.format(int(time4 - time3)))
        # add any extra reservoirs and point sources
        # set drainage
        # drainAreas is a mapping from channelLink number (used as index to array) of channel basin or grid cell areas in sq m
        self.drainAreas = zeros((maxChLink + 1), dtype=float)
        if useGridModel:
            gridCellArea = self.dx * self.dy * gv.gridSize * gv.gridSize
            # try to use Drainage field from grid channels shapefile
            if streamDrainage:
                ok = self.setGridDrainageFromChannels(channelLayer)
            else:
                ok = False
            if not ok:
                self.setGridDrainageAreas(maxChLink, gridCellArea)
        else:
            # can use drain areas from TauDEM if we have them
            if drainAreaIndex >= 0:
                self.setDrainageFromChannels(channelLayer, drainAreaIndex)
            else:
                self.setDrainageAreas(us)
        time5 = time.process_time()
        QSWATUtils.loginfo('Topology drainage took {0} seconds'.format(int(time5 - time4)))
        
        #try existing subbasin numbers as SWAT basin numbers
        ok = polyIndex >= 0 and subbasinIndex >= 0 and self.tryBasinAsSWATBasin(subbasinsLayer, polyIndex, subbasinIndex)
        if not ok:
            # failed attempt may have put data in these, so clear them
            self.subbasinToSWATBasin.clear()
            self.SWATBasinToSubbasin.clear()
            if useGridModel:
                # lower limit on drainage area for outlets to be included
                # 1.5 multiplier guards against rounding errors:
                # ensures that any cell with drainage area exceeding this cannot be a singleton
                minDrainArea = gridCellArea * 1.5
                # Create SWAT basin numbers for grid
                # we ignore single cell outlets, by checking that outlets have a drainage area greater than a single cell
                SWATBasin = 0
                # for grid models, streams and channels are the same, so chBasin is the same as basin 
                # we ignore edge basins which are outlets with nothing upstream, ie they are single cell outlets,
                # by counting only those which have a downstream link or have an upstream link
                for chLink, chBasin in self.chLinkToChBasin.items():
                    dsChLink = self.downChannels[chLink] if useGridModel else self.getDownChannel(chLink)
                    if dsChLink >= 0 or self.drainAreas[chLink] > minDrainArea:
                        SWATBasin += 1
                        self.subbasinToSWATBasin[chBasin] = SWATBasin
                        self.SWATBasinToSubbasin[SWATBasin] = chBasin
            else:
                # create SWAT basin numbers
                SWATBasin = 0
                request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([polyIndex])
                for feature in subbasinsLayer.getFeatures(request):
                    subbasin = feature[polyIndex]
                    if subbasin not in self.upstreamFromInlets:
                        SWATBasin += 1
                        self.subbasinToSWATBasin[subbasin] = SWATBasin
                        self.SWATBasinToSubbasin[SWATBasin] = subbasin
            # put SWAT Basin numbers in subbasin field of subbasins shapefile
            subbasinsLayer.startEditing()
            if subbasinIndex < 0:
                # need to add subbasin field
                subbasinsLayer.dataProvider().addAttributes([QgsField(QSWATTopology._SUBBASIN, QVariant.Int)])
                subbasinsLayer.updateFields()
                subbasinIndex = subbasinsLayer.fields().indexOf(QSWATTopology._SUBBASIN)
            request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([polyIndex])
            for feature in subbasinsLayer.getFeatures(request):
                subbasin = feature[polyIndex]
                SWATBasin = self.subbasinToSWATBasin.get(subbasin, 0)
                subbasinsLayer.changeAttributeValue(feature.id(), subbasinIndex, SWATBasin)
            subbasinsLayer.commitChanges()
        time6 = time.process_time()
        QSWATUtils.loginfo('Topology setting SWATBasin numbers took {0} seconds'.format(int(time6 - time5)))
        subbasinsLayer.setLabelsEnabled(True)
        subbasinsLayer.triggerRepaint()
        if not useGridModel:
            # add SWAT channel numbers to watershed shapefile
            # in case loaded
            root = QgsProject.instance().layerTreeRoot()
            wshedLayer, _ = QSWATUtils.getLayerByFilename(root.findLayers(), gv.wshedFile, FileTypes._WATERSHED, 
                                                        None, None, None)
            if wshedLayer is None:
                wshedLayer = QgsVectorLayer(gv.wshedFile, FileTypes.legend(FileTypes._WATERSHED), 'ogr')
            wshedPolyIndex = self.getIndex(wshedLayer, QSWATTopology._POLYGONID, ignoreMissing=ignoreError)
            wshedChannelIndex = self.getIndex(wshedLayer, QSWATTopology._CHANNEL, ignoreMissing=ignoreWithGridOrExisting)
            wshedLayer.startEditing()
            if wshedChannelIndex < 0:
                wshedLayer.dataProvider().addAttributes([QgsField(QSWATTopology._CHANNEL, QVariant.Int)])
                wshedLayer.updateFields()
                wshedChannelIndex = wshedLayer.fields().indexOf(QSWATTopology._CHANNEL)
            request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([wshedPolyIndex])
            for feature in wshedLayer.getFeatures(request):
                chBasin = feature.attributes()[wshedPolyIndex]
                channel = self.chBasinToChLink.get(chBasin, -1)
                SWATChannel = self.channelToSWATChannel.get(channel, 0)
                wshedLayer.changeAttributeValue(feature.id(), wshedChannelIndex, SWATChannel)
            wshedLayer.commitChanges()
        drainageFile = QSWATUtils.join(gv.shapesDir, gv.projName + Parameters._DRAINAGECSV)
        self.writeDrainageFile(drainageFile)
        return useGridModel or lakesLayer is not None or self.checkAreas(subbasinsLayer, gv)
    
    def addLakes(self, lakesLayer, subbasinsLayer, chBasinsLayer, streamsLayer, channelsLayer, 
                 demLayer, snapThreshold, gv, reportErrors=True):
        """Add lakes from lakes shapefile layer.
        
        Not used with grid models.""" 
        lakesProvider = lakesLayer.dataProvider()
        lakeIdIndex = lakesProvider.fieldNameIndex(QSWATTopology._LAKEID)
        lakeResIndex = lakesProvider.fieldNameIndex(QSWATTopology._RES)
        if lakeResIndex < 0:
            QSWATUtils.information('No RES field in lakes shapefile {0}: assuming lakes are reservoirs'.
                                   format(QSWATUtils.layerFilename(lakesLayer)), self.isBatch)
        subsProvider =  subbasinsLayer.dataProvider()
        subsAreaIndex = subsProvider.fieldNameIndex(Parameters._AREA)
        if subsAreaIndex < 0:
            QSWATUtils.error('Cannot find {0} field in {1}'.format(Parameters._AREA, gv.subbasinsFile), self.isBatch, reportErrors=reportErrors)
            return False
        chBasinsProvider = chBasinsLayer.dataProvider()
        chBasinsPolyIndex = chBasinsProvider.fieldNameIndex(QSWATTopology._POLYGONID)
        chBasinsAreaIndex = chBasinsProvider.fieldNameIndex(Parameters._AREA)
        channelsProvider = channelsLayer.dataProvider()
        channelLinkIndex = channelsProvider.fieldNameIndex(QSWATTopology._LINKNO)
        channelDsLinkIndex = channelsProvider.fieldNameIndex(QSWATTopology._DSLINKNO)
        channelDsNodeIndex = channelsProvider.fieldNameIndex(QSWATTopology._DSNODEID)
        channelDrainAreaIndex = channelsProvider.fieldNameIndex(QSWATTopology._DRAINAREA)
        channelWSNOIndex = channelsProvider.fieldNameIndex(QSWATTopology._WSNO)
        channelLakeInIndex = channelsProvider.fieldNameIndex(QSWATTopology._LAKEIN)
        channelLakeOutIndex = channelsProvider.fieldNameIndex(QSWATTopology._LAKEOUT)
        channelLakeWithinIndex = channelsProvider.fieldNameIndex(QSWATTopology._LAKEWITHIN)
        channelLakeMainIndex = channelsProvider.fieldNameIndex(QSWATTopology._LAKEMAIN)
        fields = []
        if channelLakeInIndex < 0:
            fields.append(QgsField(QSWATTopology._LAKEIN, QVariant.Int))
        if  channelLakeOutIndex < 0:
            fields.append(QgsField(QSWATTopology._LAKEOUT, QVariant.Int))
        if  channelLakeWithinIndex < 0:
            fields.append(QgsField(QSWATTopology._LAKEWITHIN, QVariant.Int))
        if  channelLakeMainIndex < 0:
            fields.append(QgsField(QSWATTopology._LAKEMAIN, QVariant.Int))
        if len(fields) > 0:
            if not channelsProvider.addAttributes(fields):
                QSWATUtils.error('Cannot add lake fields to channels shapefile', self.isBatch)
                return False
            channelsLayer.updateFields()
            channelLakeInIndex = channelsProvider.fieldNameIndex(QSWATTopology._LAKEIN)
            channelLakeOutIndex = channelsProvider.fieldNameIndex(QSWATTopology._LAKEOUT)
            channelLakeWithinIndex = channelsProvider.fieldNameIndex(QSWATTopology._LAKEWITHIN)
            channelLakeMainIndex = self.getIndex(channelsLayer, QSWATTopology._LAKEMAIN)
        self.chLinkIntoLake = dict()
        self.chLinkInsideLake = dict()
        self.chLinkFromLake = dict()
        self.outletsInLake = dict()
        lakeAttMap = dict()
        for lake in lakesProvider.getFeatures():
            lakeGeom = lake.geometry()
            lakeRect = lakeGeom.boundingBox()
            lakeId = lake[lakeIdIndex]
            if lakeResIndex < 0:
                waterRole = QSWATTopology._RESTYPE
            else:
                waterRole = lake[lakeResIndex]
            lakeData = LakeData(lakeGeom.area(), lakeGeom.centroid().asPoint(), waterRole)
            totalElevation = 0
            # the area removed from channel basins that intersect wih the lake
            chBasinWaterArea = 0
            attMap = dict()
            geomMap = dict()
            for sub in subsProvider.getFeatures():
                subGeom = sub.geometry()
                if  QSWATTopology.intersectsPoly(subGeom, lakeGeom, lakeRect):
                    # TODO: sub inside lake
                    subId = sub.id()
                    area1 = subGeom.area()
                    newGeom = subGeom.difference(lakeGeom)
                    area2 = newGeom.area()
                    if area2 < area1:
                        QSWATUtils.loginfo('Lake {0} overlaps subbasin {1}: area reduced from {2} to {3}'.format(lakeId, subId, area1, area2))
                        geomMap[subId] = newGeom
                        attMap[subId] = {subsAreaIndex: newGeom.area() / 1E4}
            if not subsProvider.changeAttributeValues(attMap):
                QSWATUtils.error('Failed to update subbasins attributes in {0}'.format(gv.subbasinsFile), self.isBatch, reportErrors=reportErrors)
                for err in subsProvider.errors():
                    QSWATUtils.loginfo(err)
                return False
            if not subsProvider.changeGeometryValues(geomMap):
                QSWATUtils.error('Failed to update subbasin geometries in {0}'.format(gv.subbasinsFile), self.isBatch, reportErrors=reportErrors)
                for err in subsProvider.errors():
                    QSWATUtils.loginfo(err)
                return False
            # for some reason doing both changes at once fails   
#             if not subsProvider.changeFeatures(attMap, geomMap): 
#                 QSWATUtils.error(u'Failed to update {0}'.format(gv.subbasinsFile), self.isBatch)
#                 for err in subsProvider.errors():
#                     QSWATUtils.loginfo(err)
#                 return 
            attMap = dict()
            geomMap = dict()
            # map of polygon id to area that is part of the lake
            channelAreaChange = dict()
            for chBasin in chBasinsProvider.getFeatures():
                chBasinGeom = chBasin.geometry()
                polyId = chBasin[chBasinsPolyIndex]
                # if area reduced to zero because inside another lake, geometry is None
                if chBasinGeom is not None and not chBasinGeom.disjoint(lakeGeom):
                    chBasinId = chBasin.id()
                    area1 = chBasinGeom.area()
                    newGeom = chBasinGeom.difference(lakeGeom)
                    area2 = newGeom.area()
                    if area2 < area1:
                        QSWATUtils.loginfo('Lake {0} overlaps channel basin {1}: area reduced from {2} to {3}'.format(lakeId, polyId, area1, area2))
                        chBasinWaterArea += area1 - area2
                        geomMap[chBasinId] = newGeom
                        attMap[chBasinId] = {chBasinsAreaIndex: newGeom.area() / 1E4}
                        channelAreaChange[polyId] = area1 - area2
            if not chBasinsProvider.changeAttributeValues(attMap):
                QSWATUtils.error('Failed to update channel basin attributes in {0}'.format(gv.wshedFile), self.isBatch, reportErrors=reportErrors)
                for err in chBasinsProvider.errors():
                    QSWATUtils.loginfo(err)
                return False
            if not chBasinsProvider.changeGeometryValues(geomMap):
                QSWATUtils.error('Failed to update channel basin geometries in {0}'.format(gv.wshedFile), self.isBatch, reportErrors=reportErrors)
                for err in chBasinsProvider.errors():
                    QSWATUtils.loginfo(err)
                return False
            attMap = dict()
            currentDrainArea = 0
            # first pass through channels: collect inflowing and outflowing channels from DsNodes in lakeInlets and lakeOutlets
            for channel in channelsProvider.getFeatures():
                link = channel[channelLinkIndex]
                dsLink = channel[channelDsLinkIndex]
                dsNode = channel[channelDsNodeIndex]
                if dsNode > 0:
                    if dsNode in self.lakeInlets[lakeId]:
                        inflowData = self.getReachData(channel.geometry(), demLayer)
                        lakeData.inChLinks[link] = (dsNode, QgsPointXY(inflowData.lowerX, inflowData.lowerY), inflowData.lowerZ)
                        if dsLink >= 0:
                            lakeData.lakeChLinks.add(dsLink)
                            self.chLinkInsideLake[dsLink] = lakeId
                        self.chLinkIntoLake[link] = lakeId
                        totalElevation += inflowData.lowerZ
                        channelId = channel.id()
                        chBasin = channel[channelWSNOIndex]
                        areaChange = channelAreaChange.get(chBasin, 0)
                        drainArea = channel[channelDrainAreaIndex] - areaChange
                        attMap[channelId] = {channelDrainAreaIndex: drainArea}
                    elif dsNode in self.lakeOutlets[lakeId]:
                        outflowData = self.getReachData(channel.geometry(), demLayer)
                        outlet = QgsPointXY(outflowData.lowerX, outflowData.lowerY)
                        replace = True
                        if dsLink >= 0:
                            if lakeData.outPoint[2] is not None:
                                # choose point with larger drain area 
                                newDrainArea = channel[channelDrainAreaIndex]
                                if newDrainArea > currentDrainArea:
                                    currentDrainArea = newDrainArea
                                    if lakeData.outChLink >= 0:
                                        lakeData.otherOutChLinks.add(lakeData.outChLink)
                                else:
                                    replace = False
                            if replace:
                                chBasin = channel[channelWSNOIndex]
                                subbasin = self.chBasinToSubbasin[chBasin]
                                lakeData.outPoint = (subbasin, dsNode, outlet, outflowData.lowerZ)
                                lakeData.outChLink = dsLink
                            else:
                                lakeData.otherOutChLinks.add(dsLink)
                            self.chLinkFromLake[dsLink] = lakeId
                        lakeData.lakeChLinks.add(link)
                        self.chLinkInsideLake[link] = lakeId
            # check to see of a watershed outlet was marked inside the lake
            # and if so try to move it to the lake perimeter.  Else leave it as an internal outlet. 
            # we don't need to exclude outlets created to split channels flowing into and out of lake
            # because the outlets map is made from the streams before lake inlets and outlets are added to the snap file
            # and the augmented snapfile is only used to make channels
            for subbasin, (pointId, pt, ch) in self.outlets.items():
                if QSWATTopology.polyContains(pt, lakeGeom, lakeRect) and \
                    QSWATTopology.isWatershedOutlet(pointId, channelsProvider, channelDsLinkIndex, channelDsNodeIndex):
                    if not os.path.exists(gv.pFile):
                        QSWATUtils.error('Cannot find D8 flow directions file {0}'.format(gv.pFile), self.isBatch, reportErrors=reportErrors)
                        break
                    # need to give different id to outPoint, since this is used to make the reservoir point
                    # which will then route to the subbasin outlet
                    # can use outlet point id if already created
                    if lakeData.outPoint[1] >= 0:
                        newPointId = lakeData.outPoint[1]
                    else:
                        self.pointId += 1
                        newPointId = self.pointId
                    elev = QSWATTopology.valueAtPoint(pt, demLayer)
                    lakeData.outPoint = (subbasin, newPointId, pt, elev)
                    # maximum number of steps approximates to the threshold for snapping points expressed as number of DEM cells
                    maxSteps = 5 if self.dx == 0  else int(snapThreshold / self.dx + 0.5)
                    lakeOutlet, found = QSWATTopology.movePointToPerimeter(pt, lakeGeom, gv.pFile, maxSteps)
                    if found:
                        if lakeData.outPoint[2] is not None:
                            QSWATUtils.information('User marked outlet {0} chosen as main outlet for lake {1}'.
                                                   format(pointId, lakeId), gv.isBatch)
                            if lakeData.outChLink >= 0:
                                lakeData.otherOutChLinks.add(lakeData.outChLink)
                        elev = QSWATTopology.valueAtPoint(lakeOutlet, demLayer)
                        lakeData.outPoint = (subbasin, newPointId, lakeOutlet, elev)
                        QSWATUtils.loginfo('Outlet of lake {0} set to ({1}, {2})'.
                                           format(lakeId, int(lakeOutlet.x()), int(lakeOutlet.y())))
                        # update outlets map
                        self.outlets[subbasin] = (pointId, lakeOutlet, ch) 
                    else:
                        QSWATUtils.loginfo('Outlet of lake {0} set to internal point ({1}, {2})'.
                                           format(lakeId, int(lakeOutlet.x()), int(lakeOutlet.y())))
                    lakeData.outChLink = -1
                    break            
            # second pass through channels: collect channels within lake: i.e. both ends in lake
            # and set LakeIn, LakeOut, LakeWithin fields
            for channel in channelsProvider.getFeatures():
                link = channel[channelLinkIndex]
                channelId = channel.id()
                channelData = None
                channelGeom = None
                lakeIn = self.chLinkIntoLake.get(link, 0)
                lakeOut = self.chLinkFromLake.get(link, 0)
                lakeWithin = self.chLinkInsideLake.get(link, 0)
                if link not in self.chLinkIntoLake and link not in self.chLinkFromLake and link not in self.chLinkInsideLake: 
                    channelGeom = channel.geometry()
                    channelData = self.getReachData(channelGeom, None)
                    pt1 = QgsPointXY(channelData.lowerX, channelData.lowerY)
                    pt2 = QgsPointXY(channelData.upperX, channelData.upperY)
                    if QSWATTopology.polyContains(pt1, lakeGeom, lakeRect) and QSWATTopology.polyContains(pt2, lakeGeom, lakeRect):
                        lakeData.lakeChLinks.add(link)
                        self.chLinkInsideLake[link] = lakeId
                        lakeWithin = lakeId
                lakeAttMap[channelId] = {channelLakeInIndex: lakeIn, channelLakeOutIndex: lakeOut, 
                                         channelLakeWithinIndex: lakeWithin}
                if link in lakeData.lakeChLinks:
                    # remove the channel's point source
                    del self.chPointSources[link]
            # if the lake has an outlet channel with a drain area less than LAKEOUTLETCHANNELAREA percent of the lake area
            # make its channel internal
            outLinkId = None
            outLink = lakeData.outChLink
            outBasin = -1
            dsOutLink = -1
            if outLink >= 0:
                request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([channelLinkIndex, 
                                                                                                            channelWSNOIndex,
                                                                                                            channelDsLinkIndex])
                for channel in channelsProvider.getFeatures(request):
                    if channel[channelLinkIndex] == outLink:
                        outLinkId = channel.id()
                        outBasin = channel[channelWSNOIndex]
                        dsOutLink = channel[channelDsLinkIndex]
                        break
            if outBasin >= 0:
                # threshold in ha: LAKEOUTLETCHANNELAREA of lake area
                threshold = (lakeData.area / 1E6) * Parameters._LAKEOUTLETCHANNELAREA
                request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([chBasinsPolyIndex, chBasinsAreaIndex])
                for chBasin in chBasinsProvider.getFeatures():
                    if chBasin[chBasinsPolyIndex] == outBasin:
                        areaHa = chBasin[chBasinsAreaIndex]
                        if areaHa < threshold:
                            # move outlet channel inside lake
                            lakeData.lakeChLinks.add(outLink)
                            lakeData.outChLink = dsOutLink
                            del self.chLinkFromLake[outLink]
                            self.chLinkInsideLake[outLink] = lakeId
                            # mark it as within as well as being the outlet (already set)
                            lakeAttMap[outLinkId][channelLakeWithinIndex] = lakeId
                            # check if this point now inside the lake is a subbasin outlet
                            subbasin = self.chBasinToSubbasin[outBasin]
                            (_, _, outChannel) = self.outlets[subbasin]
                            if outChannel == outLink:
                                # subbasin outlet has moved inside the lake
                                self.outletsInLake[subbasin] = lakeId
                            QSWATUtils.loginfo('Channel link {0} channel basin {1} moved inside lake {2}'.
                                               format(outLink, outBasin, lakeId))
                            # remove the channel's point source
                            del self.chPointSources[outLink]
                            if dsOutLink >= 0:
                                self.chLinkFromLake[dsOutLink] = lakeId
                            break
            if lakeData.outPoint[2] is None:
                QSWATUtils.error('Failed to find outlet for lake {0}'.format(lakeId), self.isBatch, reportErrors=reportErrors)
                return False
            if lakeData.outChLink >= 0:
                chId = -1
                # find the channel's id
                request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([channelLinkIndex])
                for channel in channelsProvider.getFeatures(request):
                    if channel[channelLinkIndex] == lakeData.outChLink:
                        chId = channel.id()
                        break
                if chId >= 0:
                    lakeAttMap[chId][channelLakeMainIndex] = lakeId
                else:
                    QSWATUtils.error('Internal error: unable to find main outlet channel {0}'.
                                     format(lakeData.outChLink), self.isBatch, reportErrors=reportErrors)
                    return False
            numInflows = len(lakeData.inChLinks)
            meanElevation = totalElevation / numInflows if numInflows > 0 else lakeData.outPoint[3]
            lakeData.elevation = meanElevation 
            QSWATUtils.loginfo('Lake {0} has outlet on channel {1}, other outlets on channels {2}, inlets on channels {3} and contains channels {4}'
                               .format(lakeId,  lakeData.outChLink, lakeData.otherOutChLinks, 
                                       list(lakeData.inChLinks.keys()), lakeData.lakeChLinks))
            OK = channelsProvider.changeAttributeValues(attMap)
            OK = OK and channelsProvider.changeAttributeValues(lakeAttMap)
            if not OK:
                QSWATUtils.error('Failed to update channel attributes in {0}'.format(gv.channelFile), self.isBatch, reportErrors=reportErrors)
                for err in channelsProvider.errors():
                    QSWATUtils.loginfo(err)
                return False
            self.lakesData[lakeId] = lakeData
            lakeArea = lakeData.area
            percentChBasinWater = chBasinWaterArea / lakeArea * 100
            QSWATUtils.loginfo('Lake {0} has area {1} and channel basin water area {2}: {3}%'.format(lakeId, lakeArea, chBasinWaterArea, percentChBasinWater))
#             intPercent = int(percentChBasinWater + 0.5)
#             if percentChBasinWater < 99:
#                 QSWATUtils.information(u'WARNING: Only {0}% of the area of lake {1} is accounted for in your watershed.  There may be other channels flowing into it'
#                                        .format(intPercent, lakeId), self.isBatch)
        if len(self.lakesData) == 0:
            QSWATUtils.error('No lakes found in {0}'.format(QSWATUtils.layerFilename(lakesLayer)), self.isBatch, reportErrors=reportErrors)
            return False
        chBasinsLayer.triggerRepaint()
        streamsLayer.triggerRepaint()
        channelsLayer.triggerRepaint()
        return True
    
    @staticmethod
    def isWatershedOutlet(pointId, channelsProvider, dsLinkIndex, dsNodeIndex):
        """Return true if there is a channel with dsNode equal to pointId and with dsLink -1."""
        request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([dsLinkIndex, dsNodeIndex])
        for link in channelsProvider.getFeatures(request):
            if link[dsNodeIndex] == pointId and link[dsLinkIndex] == -1:
                return True
        return False
    
    def isOutlet(self, pointId, outletsLayer):
        """Return true if outletsLayer contains an outlet point with id pointId."""
        idIndex = self.getIndex(outletsLayer, QSWATTopology._ID, ignoreMissing=True)
        inletIndex = self.getIndex(outletsLayer, QSWATTopology._INLET, ignoreMissing=True)
        resIndex = self.getIndex(outletsLayer, QSWATTopology._RES, ignoreMissing=True)
        if idIndex < 0 or inletIndex < 0 or resIndex < 0:
            return False
        for point in outletsLayer.getFeatures():
            if point[idIndex] == pointId and point[inletIndex] == 0 and point[resIndex] == 0:
                return True
        return False

    def addGridLakes(self, gridLayer, channelsLayer, demLayer, gv, reportErrors=True): 
        """Add lakes when using grid model.  Return number of lakes (which may be zero) or -1 if error.""" 
        gridProvider =  gridLayer.dataProvider()
        gridPolyIndex = gridProvider.fieldNameIndex(QSWATTopology._POLYGONID)
        gridDownIndex = gridProvider.fieldNameIndex(QSWATTopology._DOWNID)
        gridAreaIndex = gridProvider.fieldNameIndex(Parameters._AREA)
        gridLakeIdIndex = gridProvider.fieldNameIndex(QSWATTopology._LAKEID)
        if gridLakeIdIndex < 0:
            # can be no lakes
            return 0
        gridResIndex = gridProvider.fieldNameIndex(QSWATTopology._RES)
        channelsProvider = channelsLayer.dataProvider()
        channelLinkIndex = channelsProvider.fieldNameIndex(QSWATTopology._LINKNO)
        channelDsLinkIndex = channelsProvider.fieldNameIndex(QSWATTopology._DSLINKNO)
        channelWSNOIndex = channelsProvider.fieldNameIndex(QSWATTopology._WSNO)
        # the drainage field may no exist if we are using grid or table drainage: deal with this later
        streamDrainageIndex = channelsProvider.fieldNameIndex(QSWATTopology._DRAINAGE)
        polysIntoLake = dict()
        polysInsidelake = dict()
        polysFromLake = dict()
        self.chLinkIntoLake = dict()
        self.chLinkInsideLake = dict()
        self.chLinkFromLake = dict()
        request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([gridPolyIndex, gridLakeIdIndex])
        # first make map poly -> lake id
        polyToLake = dict()
        for cell in gridProvider.getFeatures(request):
            lakeId = cell[gridLakeIdIndex]
            if lakeId != NULL:
                polyToLake[cell[gridPolyIndex]] = lakeId
                # make sure waterbody id is set to maximum lake id in case using existing grid
                self.waterBodyId = max(self.waterBodyId, lakeId)
        if len(polyToLake) == 0:
            # no lakes
            return 0
        # data for calculating centroid
        # map of lake id to (area, x moment of area, y moment)
        lakeAreaData = dict()
        for cell in gridProvider.getFeatures():
            waterRole = cell[gridResIndex]
            poly = cell[gridPolyIndex]
            downPoly = cell[gridDownIndex]
            sourceLake = cell[gridLakeIdIndex]
            targetLake = polyToLake.get(downPoly, None)
            if sourceLake != NULL:
                if sourceLake not in lakeAreaData:
                    lakeAreaData[sourceLake] = (waterRole, 0, 0, 0)
                area = cell[gridAreaIndex] * 1E4  # convert ha to m^2
                centre, _, _ = QSWATUtils.centreGridCell(cell)
                _, totalArea, xMoment, yMoment = lakeAreaData[sourceLake]
                lakeAreaData[sourceLake] = (waterRole, totalArea + area, xMoment + area * centre.x(), yMoment + area * centre.y())
                if targetLake == sourceLake:
                    # channel links two lake cells within lake
                    polysInsidelake[poly] = sourceLake
                else:
                    # exit channel
                    polysFromLake[poly] = sourceLake
            elif targetLake is not None:
                polysIntoLake[poly] = targetLake
        totalElevation = dict()
        # map of lake id to possible exit channels
        # will choose one with largest drainage
        exitData = dict()
        for lakeId, (waterRole, area, xMoment, yMoment) in lakeAreaData.items():
            centroid = QgsPointXY(float(xMoment) / area, float(yMoment) / area)
            self.lakesData[lakeId] = LakeData(area, centroid, waterRole)
            totalElevation[lakeId] = 0
            exitData[lakeId] = dict()
        # convert wsnos to links and complete LakesData
        # get maximum chLink and create downChannels map in case drainage needs calculating
        self.downChannels = dict()
        maxChLink = 0
        for channel in channelsProvider.getFeatures():
            chLink = channel[channelLinkIndex]
            maxChLink = max(maxChLink, chLink)
            dsChLink = channel[channelDsLinkIndex]
            self.downChannels[chLink] = dsChLink
            wsno = channel[channelWSNOIndex]
            lakeIdInto = polysIntoLake.get(wsno, 0)
            if lakeIdInto > 0:
                self.chLinkIntoLake[chLink] = lakeIdInto
                # since this is a grid model the grid cells form different subbasins and there will be a suitable outlet
                # point already stored in the outlets map
                pointId, point, _ = self.outlets[wsno]
                elev = QSWATTopology.valueAtPoint(point, demLayer)
                self.lakesData[lakeIdInto].inChLinks[chLink] = (pointId, point, elev)
                totalElevation[lakeIdInto] += elev
                continue
            lakeIdFrom = polysFromLake.get(wsno, 0)
            if lakeIdFrom > 0:
                # allow for no drainage field
                drainage = -1 if streamDrainageIndex < 0 else channel[streamDrainageIndex]
                data = self.getReachData(channel.geometry(), demLayer)
                exitData[lakeIdFrom][chLink] = (wsno, drainage, QgsPointXY(data.upperX, data.upperY), data.upperZ)
                continue
            lakeIdInside = polysInsidelake.get(wsno, 0)
            if lakeIdInside > 0:
                self.chLinkInsideLake[chLink] = lakeIdInside
                self.lakesData[lakeIdInside].lakeChLinks.add(chLink)
                continue
        # check if we need to calculate drainage: no drainage field and more than one exit for at least one lake
        needDrainage = False
        if streamDrainageIndex < 0:
            for data in exitData.values():
                if len(data) > 1:
                    needDrainage = True
                    break
        if needDrainage:
            self.drainAreas = zeros((maxChLink + 1), dtype=float)
            gridCellArea = self.dx * self.dy * gv.gridSize * gv.gridSize
            self.setGridDrainageAreas(maxChLink, gridCellArea)
        # find outlet with largest drainage and mark as THE outlet
        for lakeId, data in exitData.items():
            # set maxDrainage less than -1 value used for missing drainage so that first exit link registers
            # as if there is only one exit for each lake needDrainage will be false
            maxDrainage = -2 
            exLink = -1
            exWsno = -1
            exPoint = None
            exElev = 0
            for chLink, (wsno, drainage, pt, elev) in data.items():
                if needDrainage:
                    drainage = float(self.drainAreas[chLink])  # use float to convert from numpy float
                if drainage > maxDrainage:
                    maxDrainage = drainage
                    exLink = chLink
                    exWsno = wsno
                    exPoint = pt
                    exElev = elev
            if exLink < 0:
                QSWATUtils.error('There seems to be no outflow stream for lake {0}'.format(lakeId), gv.isBatch, reportErrors=reportErrors)
                return -1
            else:
                others = list(data.keys())
                others.remove(exLink)
                if others != []:
                    QSWATUtils.information(
"""Warning: Stream link {0} chosen as main outlet for all of lake {1}.  
Other possible outlet stream links are {2}.
""".format(exLink, lakeId, str([int(link) for link in others])), gv.isBatch, reportErrors=reportErrors)
                self.chLinkFromLake[exLink] = lakeId
                self.lakesData[lakeId].outChLink = exLink
                for chLink in others:
                    self.chLinkFromLake[chLink] = lakeId
                    self.lakesData[lakeId].otherOutChLinks.add(chLink)
                self.pointId += 1
                self.lakesData[lakeId].outPoint = (exWsno, self.pointId, exPoint, exElev)
        for lakeId, totalElev in totalElevation.items():
            numInLinks = len(self.lakesData[lakeId].inChLinks)
            if numInLinks > 0:
                self.lakesData[lakeId].elevation = float(totalElev) /  numInLinks
            else:
                self.lakesData[lakeId].elevation = self.lakesData[lakeId].outPoint[3]
        return len(self.lakesData) 
    
    def addExistingLakes(self, lakesLayer, channelsLayer, demLayer, gv, reportErrors=True):
        """Add lakes data to existing non-grid model.
        
        We ignore DsNodeIds for inflowing and outflowing channels since these were
        probably only added previously to the snapped inlets/outlets file
        and inlets/outlets are little use in any case with existing watersheds."""
        
        lakeIdIndex = self.getIndex(lakesLayer, QSWATTopology._LAKEID)
        lakeResIndex = self.getIndex(lakesLayer, QSWATTopology._RES)
        channelLinkIndex = self.getIndex(channelsLayer, QSWATTopology._LINKNO)
        channelDsLinkIndex = self.getIndex(channelsLayer, QSWATTopology._DSLINKNO)
        channelBasinIndex = self.getIndex(channelsLayer, QSWATTopology._BASINNO)
        channelLakeInIndex = self.getIndex(channelsLayer, QSWATTopology._LAKEIN)
        channelLakeOutIndex = self.getIndex(channelsLayer, QSWATTopology._LAKEOUT)
        channelLakeWithinIndex = self.getIndex(channelsLayer, QSWATTopology._LAKEWITHIN)
        channelLakeMainIndex = self.getIndex(channelsLayer, QSWATTopology._LAKEMAIN)
        if lakeIdIndex < 0 or channelLinkIndex < 0 or channelDsLinkIndex < 0 or channelBasinIndex < 0 or \
            channelLakeInIndex < 0 or channelLakeOutIndex < 0 or channelLakeWithinIndex < 0 or channelLakeMainIndex < 0:
            return False
        self.lakesData = dict()
        for lake in lakesLayer.getFeatures():
            lakeId = lake[lakeIdIndex]
            waterRole = lake[lakeResIndex]
            if lakeId in self.lakesData:
                QSWATUtils.error('Lake identifier {0} occurs twice in {1}.  Lakes not added.'.format(lakeId, QSWATUtils.layerFilename(lakesLayer)), 
                                 gv.isBatch, reportErrors=reportErrors)
                self.lakesData = dict()
                return False
            # to stop reuse of the same water body id
            self.waterBodyId = max(self.waterBodyId, lakeId)
            geom = lake.geometry()
            area = geom.area()
            centroid = geom.centroid().asPoint()
            self.lakesData[lakeId] = LakeData(area, centroid, waterRole)
        self.chLinkIntoLake = dict()
        self.chLinkInsideLake = dict()
        self.chLinkFromLake = dict()
        self.outletsInLake = dict()
        for channel in channelsLayer.getFeatures():
            chLink = channel[channelLinkIndex]
            dsLink = channel[channelDsLinkIndex]
            lakeIn = channel[channelLakeInIndex]
            lakeOut = channel[channelLakeOutIndex]
            lakeWithin = channel[channelLakeWithinIndex]
            lakeMain = channel[channelLakeMainIndex]
            reachData = None
            geom = None
            if lakeIn != NULL and lakeIn > 0:
                data = self.lakesData.get(lakeIn, None)
                if data is None:
                    QSWATUtils.error('Channel with LINKNO {0} flows into lake {1} not defined in {2}.  Lakes not added.'.
                                     format(chLink, lakeIn, QSWATUtils.layerFilename(lakesLayer)),
                                     gv.isBatch, reportErrors=reportErrors)
                    self.lakesData = dict()
                    return False
                geom = channel.geometry()
                reachData = self.getReachData(geom, demLayer)
                point = QgsPointXY(reachData.lowerX, reachData.lowerY)
                elev = reachData.lowerZ
                data.elevation += elev
                self.pointId += 1
                data.inChLinks[chLink] = (self.pointId, point, elev)
                self.chLinkIntoLake[chLink] = lakeIn
            elif lakeWithin != NULL and lakeWithin > 0:
                data = self.lakesData.get(lakeWithin, None)
                if data is None:
                    QSWATUtils.error('Channel with LINKNO {0} inside lake {1} not defined in {2}.  Lakes not added.'.
                                     format(chLink, lakeWithin, QSWATUtils.layerFilename(lakesLayer)),
                                     gv.isBatch, reportErrors=reportErrors)
                    self.lakesData = dict()
                    return False
                data.lakeChLinks.add(chLink)
                self.chLinkInsideLake[chLink] = lakeWithin
                if dsLink < 0:
                    # watershed outlet
                    geom = channel.geometry()
                    reachData = self.getReachData(geom, demLayer)
                    subbasin = channel[channelBasinIndex]
                    data.outChLink = -1
                    point = QgsPointXY(reachData.lowerX, reachData.lowerY)
                    elev = reachData.lowerZ
                    self.pointId += 1
                    data.outPoint = (subbasin, self.pointId, point, elev)
                    self.outletsInLake[subbasin] = lakeWithin
            if lakeOut != NULL and lakeOut > 0:
                data = self.lakesData.get(lakeOut, None)
                if data is None:
                    QSWATUtils.error('Channel with LINKNO {0} flows out of lake {1} not defined in {2}.  Lakes not added.'.
                                     format(chLink, lakeOut, QSWATUtils.layerFilename(lakesLayer)),
                                     gv.isBatch, reportErrors=reportErrors)
                    self.lakesData = dict()
                    return False
                if lakeMain != NULL and lakeMain == lakeOut:
                    # lake's main outlet
                    # channel leaves lake at upper end
                    geom = channel.geometry()
                    reachData = self.getReachData(geom, demLayer)
                    subbasin = channel[channelBasinIndex]
                    data.outChLink = chLink
                    point = QgsPointXY(reachData.upperX, reachData.upperY)
                    elev = reachData.upperZ
                    self.pointId += 1
                    data.outPoint = (subbasin, self.pointId, point, elev)
                    self.chLinkFromLake[chLink] = lakeOut
                else:
                    # other outlet
                    data.otherOutChLinks.add(chLink)
        # define lake elevation
        for data in self.lakesData.values():
            numInflows = len(data.inChLinks)
            data.elevation = data.outPoint[3] if numInflows == 0 else float(data.elevation) / numInflows
        return True
                    

    @staticmethod
    def intersectsPoly(geom, polyGeom, polyRect):
        """Returns true if any part of geom intersects any part of polyGeom, which has associated rectangle polyRect."""
        geoRect = geom.boundingBox()
        if QSWATTopology.disjointBoxes(geoRect, polyRect):
            return False
        else:
            return geom.intersects(polyGeom)
        
    @staticmethod
    def disjointBoxes(box1, box2):
        """Return True if the boxes are disjoint."""
        return box1.xMinimum() > box2.xMaximum() or \
            box1.xMaximum() < box2.xMinimum() or \
            box1.yMinimum() > box2.yMaximum() or \
            box1.yMaximum() < box2.yMinimum()
        
    @staticmethod
    def polyContains(point, polyGeom, polyRect):
        """Return true if point within polyGeom, which has associated rectangle polyRect."""
        if polyRect.xMinimum() < point.x() < polyRect.xMaximum() and \
            polyRect.yMinimum() < point.y() < polyRect.yMaximum():
            return polyGeom.contains(point)
        else:
            return False
            
    def saveLakesData(self, db): 
        """Save lakes data in project database."""
        with db.conn as conn:
            if not conn:
                return
            curs = conn.cursor()
            lakesTable = 'LAKESDATA'
            clearSQL = 'DROP TABLE IF EXISTS ' + lakesTable
            curs.execute(clearSQL)
            curs.execute(db._CREATELAKESDATA)
            linksTable = 'LAKELINKS'
            clearSQL = 'DROP TABLE IF EXISTS ' + linksTable
            curs.execute(clearSQL)
            curs.execute(db._CREATELAKELINKS)
            basinsTable = 'LAKEBASINS'
            clearSQL = 'DROP TABLE IF EXISTS ' + basinsTable
            curs.execute(clearSQL)
            curs.execute(db._CREATELAKEBASINS)
            for lakeId, lakeData in self.lakesData.items():
                curs.execute(db._INSERTLAKESDATA, (lakeId, lakeData.outPoint[0], lakeData.waterRole, lakeData.area, lakeData.elevation, lakeData.outChLink,
                                          lakeData.outPoint[1], lakeData.outPoint[2].x(), lakeData.outPoint[2].y(),
                                          lakeData.outPoint[3], lakeData.centroid.x(), lakeData.centroid.y()))
                # QSWATUtils.loginfo(str(lakeData.inChLinks.keys()))
                # QSWATUtils.loginfo(str(lakeData.lakeChLinks))
                for chLink, (pointId, pt, elev) in lakeData.inChLinks.items():
                    try:
                        curs.execute(db._INSERTLAKELINKS, (chLink, lakeId, True, False, pointId, pt.x(), pt.y(), elev))
                    except:
                        QSWATUtils.error('Failed to add in channel link {0}'.format(chLink), self.isBatch)
                for chLink in lakeData.lakeChLinks:
                    try:
                        curs.execute(db._INSERTLAKELINKS, (chLink, lakeId, False, True, None, None, None, None))
                    except:
                        QSWATUtils.error('Failed to add inside channel link {0}'.format(chLink), self.isBatch)
                for chLink in lakeData.otherOutChLinks:
                    try:
                        curs.execute(db._INSERTLAKELINKS, (chLink, lakeId, False, False, None, None, None, None))
                    except:
                        QSWATUtils.error('Failed to add other out channel link {0}'.format(chLink), self.isBatch)
            for subbasin, lakeId in self.outletsInLake.items():
                curs.execute(db._INSERTLAKEBASINS, (subbasin, lakeId))
            db.hashDbTable(conn, lakesTable)
            db.hashDbTable(conn, linksTable)
            db.hashDbTable(conn, basinsTable)
                                 
    def readLakesData(self, db):
        """Read lakes data from project database.  Return true if data read OK, false if no data or error."""
        with db.conn as conn:
            if not conn:
                return False
            self.lakesData.clear()
            self.chLinkIntoLake.clear()
            self.chLinkInsideLake.clear()
            self.chLinkFromLake.clear()
            self.outletsInLake.clear()
            curs = conn.cursor()
            lakesTable = 'LAKESDATA'
            linksTable = 'LAKELINKS'
            basinsTable = 'LAKEBASINS'
            lakeSql = db.sqlSelect(lakesTable, '*', '', '')
            linksSql = db.sqlSelect(linksTable, '*', '', 'lakeid=?')
            basinsSql = db.sqlSelect(basinsTable, '*', '', '')
            try: # in case old database without these tables
                # without fetchall this only reads first row.  Strange
                for lakeRow in curs.execute(lakeSql).fetchall():
                    lakeId = lakeRow['id']
                    self.waterBodyId = max(self.waterBodyId, lakeId)
                    self.lakesData[lakeId] = LakeData(lakeRow['area'], QgsPointXY(lakeRow['centroidx'], lakeRow['centroidy'], lakeRow['role']))
                    outChLink = lakeRow['outlink']
                    self.lakesData[lakeId].outChLink = outChLink
                    self.chLinkFromLake[outChLink] = lakeId
                    self.lakesData[lakeId].outPoint = (lakeRow['subbasin'], lakeRow['outletid'], 
                                                       QgsPointXY(lakeRow['outletx'], lakeRow['outlety']), lakeRow['outletelev'])
                    self.lakesData[lakeId].centroid = QgsPointXY(lakeRow['centroidx'], lakeRow['centroidy'])
                    self.lakesData[lakeId].elevation = lakeRow['meanelev']
                    for linkRow in curs.execute(linksSql, (lakeId,)):
                        chLink = linkRow['linkno']
                        if linkRow['inside']:
                            self.lakesData[lakeId].lakeChLinks.add(chLink)
                            self.chLinkInsideLake[chLink] = lakeId
                        elif linkRow['inlet']:
                            self.lakesData[lakeId].inChLinks[chLink] = (linkRow['inletid'], 
                                                                        QgsPointXY(linkRow['inletx'], linkRow['inlety']), linkRow['inletelev'])
                            self.chLinkIntoLake[chLink] = lakeId
                        else:
                            self.lakesData[lakeId].otherOutChLinks.add(chLink)
                            self.chLinkFromLake[chLink] = lakeId
                for basinRow in curs.execute(basinsSql).fetchall():
                    self.outletsInLake[basinRow['subbasin']] = basinRow['lakeid']
                return len(self.lakesData) > 0
            except:
                QSWATUtils.loginfo('Reading lakes data failed: {0}'.format(traceback.format_exc()))
                return False
    
    def getDownChannel(self, channel):
        """Get downstream channel, skipping zero-length channels.
        
        Returns -1 if the channel flows into a lake."""
        if channel in self.chLinkIntoLake:
            return -1
        while True:
            dsChannel = self.downChannels[channel]
            if dsChannel in self.zeroChannels:
                channel = dsChannel
            else:
                return dsChannel
    
    def setChannelBasinAreas(self, gv):
        """
        Define map chBasinAreas from channel basin to basin area in sq m.
        
        Done by counting pixels in the wChannel file (as an alternative to creating a shapefile from it).
        Not used with grid models.
        """
        self.chBasinAreas.clear()
        unitArea = self.dx * self.dy # area of une DEM pixel in sq m
        completed = False
        raster = Raster(gv.channelBasinFile, gv)
        while not completed:
            try:
                # safer to mark complete immediately to avoid danger of endless loop
                # only way to loop is then the memory error exception being raised 
                completed = True
                if not raster.open(self.chunkCount):
                    QSWATUtils.error('Failed to open channel basins raster {0}'.format(gv.channelBasinFile), gv.isBatch)
                    return
                for row in range(raster.numRows):
                    for col in range(raster.numCols):
                        val = int(raster.read(row, col))
                        if val == raster.noData:
                            continue
                        elif val in self.chBasinAreas:
                            self.chBasinAreas[val] += unitArea
                        else:
                            self.chBasinAreas[val] = unitArea
                raster.close()
            except MemoryError:
                QSWATUtils.loginfo('Out of memory calculating channel basin areas with chunk count {0}'.format(self.chunkCount))
                try:
                    raster.close()
                except Exception:
                    pass  
                completed = False
                self.chunkCount += 1
            
    def checkAreas(self, subbasinsLayer, gv):
        """
        Check total channel basin areas in each subbasin tally with subbasin areas, 
        and total watershed areaa for both tally, i.e. are the same within area of one DEM pixel.
        
        This is only done in testing ('test' in project name) and is mostly a check that
        channels are correctly assigned to subbasins.
        Not used with grid models (since channel-subbasin is one-one for grid models).
        """
        # TODO:  make work with lakes
        if 'test' in gv.projName:
            unitArea = self.dx * self.dy # area of une DEM pixel in sq m
            polyIndex = self.getIndex(subbasinsLayer, QSWATTopology._POLYGONID)
            if polyIndex < 0:
                return False
            areaIndex = self.getIndex(subbasinsLayer, Parameters._AREA, ignoreMissing=True)
            totalBasinsArea = 0
            totalChannelBasinsArea = 0
            # one percent test: using 1 pixel test instead
#             def compare(x, y): # return true if both zero or difference < 1% of x
#                 if x == 0:
#                     return y == 0
#                 else:
#                     return abs(x - y) < 0.01 * x
            for poly in subbasinsLayer.getFeatures():
                if areaIndex < 0:
                    basinArea = poly.geometry().area()
                else:
                    basinArea = poly[areaIndex] * 1E4  # areas in subbasins shapefile are in hectares
                # need to count areas of basins upstream from inlets because comparison for whole watershed
                # by using all channels will not exclude them
                totalBasinsArea += basinArea
                basin = poly[polyIndex]
                chBasins = set()
                chLinks = set()
                for chLink, chBasin in self.chLinkToChBasin.items():
                    if basin == self.chBasinToSubbasin.get(chBasin, -1):
                        chBasins.add(chBasin)
                        chLinks.add(chLink)
                area = 0
                for chBasin, chArea in self.chBasinAreas.items():
                    if chBasin in chBasins:
                        area += chArea
                if abs(basinArea - area) >= unitArea: # not using compare(basinArea, area):
                    SWATChannels = {self.channelToSWATChannel[chLink] for chLink in chLinks}
                    SWATBasin = self.subbasinToSWATBasin[basin]
                    QSWATUtils.error('Basin {0} with area {1} has channels {2} with total area {3}'.
                                     format(SWATBasin, basinArea, SWATChannels, area), True)
                    return False
            # now compare areas for whole watershed
            for _, chArea in self.chBasinAreas.items():
                totalChannelBasinsArea += chArea
            if abs(totalBasinsArea - totalChannelBasinsArea) >= unitArea: # not using compare(totalBasinsArea, totalChannelBasinsArea):
                QSWATUtils.error('Watershed area is {0} by adding subbasin areas and {1} by adding channel basin areas'.
                                 format(totalBasinsArea, totalChannelBasinsArea), True)
                return False
            QSWATUtils.loginfo('Total watershed area is {0}'.format(totalBasinsArea))
        return True
    
    @staticmethod
    def reachable(chLink, chLinks, us):
        """Return true if chLink is in chLinks or reachable from an item in chLinks via the one-many relation us."""
        if chLink in chLinks:
            return True
        for nxt in chLinks:
            if QSWATTopology.reachable(chLink, us.get(nxt, []), us):
                return True
        return False
                   
    #===========================================================================
    # def addUpstreamLinks(self, link, us):
    #     """Add to upstreamFromInlets the links upstream from link."""
    #     ups = us.get(link, None)
    #     if ups is not None:
    #         for up in ups:
    #             self.upstreamFromInlets.add(up)
    #             self.addUpstreamLinks(up, us)
    #===========================================================================
                    
    def setDrainageFromChannels(self, channelLayer, drainAreaIndex):
        """Get drain areas from channelLayer file's DS_Cont_Ar attribute."""
        inds = [self.channelIndex, drainAreaIndex]
        request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes(inds)
        for reach in channelLayer.getFeatures(request):
            channelLink = reach[self.channelIndex]
            self.drainAreas[channelLink] = reach[drainAreaIndex]
                    
    def setGridDrainageFromChannels(self, channelLayer): 
        """Get drain areas from channelLayer file's Drainage attribute.  Return True if successful."""
        channelIndex = self.getIndex(channelLayer, QSWATTopology._LINKNO, ignoreMissing=True)
        drainageIndex = self.getIndex(channelLayer, QSWATTopology._DRAINAGE, ignoreMissing=True)
        if channelIndex < 0 or drainageIndex < 0:
            return False
        inds = [channelIndex, drainageIndex]
        request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes(inds)
        for reach in channelLayer.getFeatures(request):
            channel = reach[channelIndex]
            self.drainAreas[channel] = reach[drainageIndex] * 1E6 # drainage attribute is in sq km
        return True
               
    def setGridDrainageAreas(self, maxChLink, gridCellArea):
        """Calculate and save grid drain areas in sq km."""
        self.drainAreas.fill(gridCellArea)
        # number of incoming links for each link
        incount = zeros((maxChLink + 1), dtype=int)
        for dsLink in self.downChannels.values():
            if dsLink >= 0:
                incount[dsLink] += 1
        # queue contains all links whose drainage areas have been calculated 
        # i.e. will not increase and can be propagated
        queue = [link for link in range(maxChLink + 1) if incount[link] == 0]
        while queue:
            link = queue.pop(0)
            dsLink = self.downChannels.get(link, -1)
            if dsLink >= 0:
                self.drainAreas[dsLink] += self.drainAreas[link]
                incount[dsLink] -= 1
                if incount[dsLink] == 0:
                    queue.append(dsLink)
        # incount values should now all be zero
        remainder = [link for link in range(maxChLink + 1) if incount[link] > 0]
        if remainder:
            QSWATUtils.error('Drainage areas incomplete.  There is a circularity in links {0!s}'.format(remainder), self.isBatch)
            
    def setDrainageAreas(self, us):
        """
        Calculate and save drainAreas.
        
        Not used with grid models.
        """
        for chLink, chBasin in self.chLinkToChBasin.items():
            self.setLinkDrainageArea(chLink, chBasin, us)
                
    def setLinkDrainageArea(self, chLink, chBasin, us):
        """
        Calculate and save drainArea for chLink.
        
        Not used with grid models.
        """
        if self.drainAreas[chLink] > 0:
            # already done in calculating one further downstream
            return
        ownArea = self.chBasinAreas.get(chBasin, 0)
        upsArea = 0
        ups = us.get(chLink, [])
        for up in ups:
            self.setLinkDrainageArea(up, self.chLinkToChBasin[up], us)
            upsArea += self.drainAreas[up]
        self.drainAreas[chLink] = ownArea + upsArea
        
    def getDistanceToJoin(self, basin, otherBasin):
        """Get distance in metres to join with otherBasin from outlet of basin.  Add to distancesToJoins if necessary."""
        link = self.subbasinToStream[basin]
        otherLink = self.subbasinToStream[otherBasin]
        distances = self.distancesToJoins.get(link, dict())
        distance = distances.get(otherLink, -1)
        if distance < 0:
            distance = self.distanceToJoin(link, otherLink)
            distances[otherLink] = distance
            self.distancesToJoins[link] = distances
        return distance
        
    def distanceToJoin(self, start, otherLink):
        """
        Return distance in metres from outlet of link start to point of confluence with
        flow from otherLink, or to Outlet if no confluence.
        """
        return sum([self.streamLengths[link] for link in self.pathFromJoin(start, otherLink)])
        
    def pathFromJoin(self, start, otherLink):
        """
        Return list of downstream links starting with confluence with downstream path from otherLink, 
        and finishing with link immediately downstream from start.
        
        If otherLink is immediately downstream from start, list will be [otherLink].
        If start and otherLink both flow immediately into x, list will be empty.
        If there is no confluence, list will be path from outlet to immediately downstream from start.
        """
        startPath = self.pathFromOutlet(start)
        otherPath = self.pathFromOutlet(otherLink)
        return self.removeCommonPrefix(startPath, otherPath)
        
    def pathFromOutlet(self, start):
        """List of links downstream of start, in upstream order."""
        result = []
        nxt = start
        while True:
            nxt = self.downStreams.get(nxt, -1)
            if nxt == -1:
                break
            result = [nxt] + result
        return result
    
    def removeCommonPrefix(self, path1, path2):
        """Remove from the beginning of path1 the longest sequence that starts path2."""
        i = 0
        while i < len(path1) and i < len(path2):
            if path1[i]  == path2[i]:
                i += 1
            else:
                break
        return path1[i:]
        
    def addBasinsToChannelFile(self, channelLayer, wStreamFile):
        """
        Add basinno field (if necessary) to channels shapefile and populate with values from wStreamFile.
        
        Not done with grid models.
        """
        provider = channelLayer.dataProvider()
        bsnIdx = self.getIndex(channelLayer, QSWATTopology._BASINNO, ignoreMissing=True)
        if bsnIdx < 0:
            field = QgsField(QSWATTopology._BASINNO, QVariant.Int)
            OK = provider.addAttributes([field])
            if not OK:
                QSWATUtils.error('Cannot add {0} field to channels shapefile'.format(QSWATTopology._BASINNO), self.isBatch)
                return
            channelLayer.updateFields()
            bsnIdx = self.getIndex(channelLayer, QSWATTopology._BASINNO)
        wLayer = QgsRasterLayer(wStreamFile, 'Basins')
        lenIdx = self.getIndex(channelLayer, QSWATTopology._LENGTH, ignoreMissing=True)
        chsMap = dict()
        for feature in provider.getFeatures():
            # find a point well into the channel to ensure we are not just outside the basin
            geometry = feature.geometry()
            if lenIdx < 0:
                length = geometry.length()
            else:
                length = feature[lenIdx]
            if length <= 0:
                basin = QSWATTopology._NOBASIN # value to indicate a zero-length channel
            else:
                if geometry.isMultipart():
                    lines = geometry.asMultiPolyline()
                    numLines = len(lines)
                    if numLines == 0:
                        QSWATUtils.error('Link in channel with id {0} consists of 0 lines'.format(feature.id()), self.isBatch)
                        return
                    line = lines[numLines // 2]
                else:
                    line = geometry.asPolyline()
                numPoints = len(line)
                if numPoints < 2:
                    QSWATUtils.error('Link in channel with id {0} has less than two points'.format(feature.id()), self.isBatch)
                    return
                point = line[numPoints // 2]
                basin = QSWATTopology.valueAtPoint(point, wLayer)
            fid = feature.id()
            chsMap[fid] = dict()
            chsMap[fid][bsnIdx] = basin
        OK = provider.changeAttributeValues(chsMap)
        if not OK:
            QSWATUtils.error('Cannot add basin values to channels shapefile', self.isBatch)
        return
    
    def writeDrainageFile(self, drainageFile): 
        """Write drainage csv file."""
        if os.path.exists(drainageFile):
            os.remove(drainageFile)
        with open(drainageFile, 'w', newline='') as connFile:
            writer = csv.writer(connFile)
            writer.writerow([b'Subbasin', b'DownSubbasin'])
            for subbasin, downSubbasin in self.downSubbasins.items():
                SWATBasin = self.subbasinToSWATBasin.get(subbasin, -1)
                if SWATBasin > 0:
                    downSWATBasin = self.subbasinToSWATBasin.get(downSubbasin, -1)
                    writer.writerow([str(SWATBasin),str(downSWATBasin)])
        
    def getReachData(self, geom, demLayer):
        """
        Generate ReachData record for reach geometry.  demLayer may be none, in which case elevations are set zero.
        """
        firstLine = QSWATTopology.reachFirstLine(geom, self.xThreshold, self.yThreshold)
        if firstLine is None or len(firstLine) < 1:
            QSWATUtils.error('It looks like your stream shapefile does not obey the single direction rule, that all reaches are either upstream or downstream.', self.isBatch)
            return None
        lastLine = QSWATTopology.reachLastLine(geom, self.xThreshold, self.yThreshold)
        if lastLine is None or len(lastLine) < 1:
            QSWATUtils.error('It looks like your stream shapefile does not obey the single direction rule, that all reaches are either upstream or downstream.', self.isBatch)
            return None
        pStart = firstLine[0]
        pFinish = lastLine[-1]
        if demLayer is None:
            startVal = 0
            finishVal = 0
        else:
            startVal = QSWATTopology.valueAtPoint(pStart, demLayer)
            finishVal = QSWATTopology.valueAtPoint(pFinish, demLayer)
            if startVal is None or startVal == self.demNodata:
                if finishVal is None or finishVal == self.demNodata:
    #                 QSWATUtils.loginfo(u'({0!s},{1!s}) elevation {4} to ({2!s},{3!s}) elevation {5}'
    #                                    .format(pStart.x(), pStart.y(), pFinish.x(), pFinish.y(), str(startVal), str(finishVal)))
                    return None
                else:
                    startVal = finishVal
            elif finishVal is None or finishVal == self.demNodata:
                finishVal = startVal
        if self.outletAtStart:
            maxElev = finishVal * self.verticalFactor
            minElev = startVal * self.verticalFactor
            return ReachData(pFinish.x(), pFinish.y(), maxElev, pStart.x(), pStart.y(), minElev)
        else:
            minElev = finishVal * self.verticalFactor
            maxElev = startVal * self.verticalFactor
            return ReachData(pStart.x(), pStart.y(), maxElev, pFinish.x(), pFinish.y(), minElev)
    
    @staticmethod
    def gridReachLength(data):
        """Length of reach assuming it is a single straight line."""
        dx = data.upperX - data.lowerX
        dy = data.upperY - data.lowerY
        return math.sqrt(dx * dx + dy * dy)

    def tryBasinAsSWATBasin(self, subbasinsLayer, polyIndex, subbasinIndex):
        """Return true if the subbasin field values can be used as SWAT basin numbers.
        
        The basin numbers, if any, can be used if they 
        are all positive and different.
        Also populate subbasinToSWATBasin and SWATBasinToSubbasin if successful, else these are undetermined.
        """
        assert polyIndex >= 0 and subbasinIndex >= 0 and len(self.subbasinToSWATBasin) == 0 and len(self.SWATBasinToSubbasin) == 0
        SWATBasins = set()
        request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([polyIndex, subbasinIndex])
        for polygon in subbasinsLayer.getFeatures(request):
            subbasin = polygon[polyIndex]
            if subbasin in self.upstreamFromInlets:
                continue
            SWATBasin = polygon[subbasinIndex]
            if SWATBasin <= 0:
                return False
            if SWATBasin in SWATBasins:
                return False
            self.subbasinToSWATBasin[subbasin] = SWATBasin
            self.SWATBasinToSubbasin[SWATBasin] = subbasin
            SWATBasins.add(SWATBasin)
        return True
 
    @staticmethod
    def snapPointToReach(streamLayer, point, threshold, transform, isBatch):
        """Return the nearest point on a stream segment to the input point."""
        line, pointIndex = QSWATTopology.nearestVertex(streamLayer, point)
        if pointIndex < 0:
            QSWATUtils.error('Cannot snap point ({0:.0f}, {1:.0f}) to stream network'.format(point.x(), point.y()), isBatch)
            return None
        p1, p2 = QSWATTopology.intercepts(line, pointIndex, point)
        p = QSWATTopology.nearer(p1, p2, point)
        if p is None:
            p = line[pointIndex]
            return p if QSWATTopology.distanceMeasure(p, point) <= threshold * threshold else None
        # check p is sufficiently near point
        if QSWATTopology.distanceMeasure(p, point) <= threshold * threshold:
            # before returning p, move it along the stream a little if it is on or close to a '4 corners' position
            # since TauDEM can fail to make a boundary or use its id as a DSNODEID if is so positioned
            if p1 == p2:
                # a point on the line was chosen, which is safe (points on the line are centres of DEM cells)
                return p
            else:
                floatCol = float(p.x() - transform[0]) / transform[1]
                intCol = int(floatCol + 0.5)
                floatRow = float(p.y() - transform[3]) / transform[5]
                intRow = int(floatRow + 0.5)
                if abs(floatCol - intCol) < 0.1 and abs(floatRow - intRow) < 0.1:
                    # move the point towards line[pointIndex] by about half a cell
                    p3 = QSWATTopology.shiftedPoint(p, line[pointIndex], transform, 0.4)
                    QSWATUtils.loginfo('({0:.0f},{1:.0f}) shifted to ({2:.0f},{3:.0f})'.format(p.x(), p.y(), p3.x(), p3.y()))
                    return p3
                else:
                    return p
        else:
            QSWATUtils.error('Cannot snap point ({0:.0f}, {1:.0f}) to stream network within threshold {2!s}'.format(point.x(), point.y(), threshold), isBatch)
            return None
        
    @staticmethod
    def separatePoints(p1, p2, transform):
        """If p2 is in same cell as p1 return a point in the next cell in the direction of p1 to p2.
        Else return p2."""
        # p1 is the end of a channel, so will be in the centre of a cell.  So enough
        # to move one coordinate of p2 by one cell from p1, and the other proportionately but less
        col1, row1 = QSWATTopology.projToCell(p1.x(), p1.y(), transform)
        col2, row2 = QSWATTopology.projToCell(p2.x(), p2.y(), transform)
        if col1 == col2 and row1 == row2:
            return QSWATTopology.shiftedPoint(p1, p2, transform, 1.0)
        else:
            return p2
        
    @staticmethod
    def shiftedPoint(p1, p2, transform, frac):
        """Return point at least frac of a cell away from p1 in direction p1 to p2."""
        x1 = p1.x()
        y1 = p1.y()
        x2 = p2.x()
        y2 = p2.y()
        dirx = 1 if x2 > x1 else -1
        diry = 1 if y2 > y1 else -1
        stepx = transform[1] * frac
        stepy = abs(transform[5]) * frac
        if x1 == x2:  # vertical
            shiftx = 0
            shifty = stepy * diry
        else:
            slope = abs(float(y1 - y2) / (x1 - x2))
            if slope < 1:
                shiftx = stepx * dirx
                shifty = stepy * diry * slope
            else:
                shiftx = stepx * dirx / slope
                shifty = stepy * diry
        return QgsPointXY(x1 + shiftx, y1 + shifty)
        
    @staticmethod
    def nearestVertex(streamLayer, point):
        """Find nearest vertex in streamLayer to point and 
        return the line (list of points) in the reach and 
        index of the vertex within the line.
        """
        bestPointIndex = -1
        bestLine = None
        minMeasure = float('inf')
        for reach in streamLayer.getFeatures():
            geometry = reach.geometry()
            if geometry.isMultipart():
                parts = geometry.asMultiPolyline()
            else:
                parts = [geometry.asPolyline()]
            for line in parts:
                for j in range(len(line)):
                    measure = QSWATTopology.distanceMeasure(line[j], point)
                    if measure < minMeasure:
                        minMeasure = measure
                        bestPointIndex = j
                        bestLine = line
        # distance = math.sqrt(minMeasure)
        # QSWATUtils.information(u'Nearest point at ({0:.2F}, {1:.2F}), distance {2:.2F}'.format(bestReach[bestPointIndex].x(), bestReach[bestPointIndex].y(), distance), False)
        return (bestLine, bestPointIndex)
    
    @staticmethod
    def intercepts(line, pointIndex, point):
        """Get points on segments on either side of pointIndex where 
        vertical from point meets the segment.
        """
        assert pointIndex in range(len(line))
        # first try above pointIndex
        if pointIndex == len(line) - 1:
            # We are at the upper end - no upper segment.  
            # Return just this point to avoid a tiny subbasin.
            return (line[pointIndex], line[pointIndex])
        else:
            upper = QSWATTopology.getIntercept(line[pointIndex], line[pointIndex+1], point)
        if pointIndex == 0:
            # We are at the lower end - no lower segment.  
            # Return just this point to avoid a tiny subbasin.
            return (line[0], line[0])
        else:
            lower = QSWATTopology.getIntercept(line[pointIndex], line[pointIndex-1], point)
        return (lower, upper)
    
    @staticmethod
    def getIntercept(p1, p2, p):
        """Return point on line from p1 to p2 where 
        vertical from p intercepts it, or None if there is no intercept.
        """
        x1 = p1.x()
        x2 = p2.x()
        xp = p.x()
        y1 = p1.y()
        y2 = p2.y()
        yp = p.y()
        X = x1 - x2
        Y = y1 - y2
        assert not (X == 0 and Y == 0)
        prop = (X * (x1 - xp) + Y * (y1 - yp)) / (X * X + Y * Y)
        if prop < 0:
            # intercept is off the line beyond p1
            # technically we should check for prop > 1, which means 
            # intercept is off the line beyond p2, but we can assume p is nearer to p1
            return None
        else:
            assert 0 <= prop < 1
            return QPoint(x1 - prop * X, y1 - prop * Y)
        
    @staticmethod
    def nearer(p1, p2, p):
        """Return the nearer of p1 and p2 to p."""
        if p1 is None: 
            return p2
        if p2 is None:
            return p1
        if QSWATTopology.distanceMeasure(p1, p) < QSWATTopology.distanceMeasure(p2, p):
            return p1
        else:
            return p2

    @staticmethod
    def distanceMeasure(p1, p2):
        """Return square of distance between p1 and p2."""
        dx = p1.x() - p2.x()
        dy = p1.y() - p2.y()
        return dx * dx + dy * dy
    
    def setMaxFlowLengths(self):
        """
        Write table of subbasin to maximum flow length along channels within the basin.
        
        Used for maximum flow path for existing non-grid models, and only defined for these.
        """
        channelFlowLengths = dict()
        for chLink, length in self.channelLengths.items():
            self.setChannelFlowLength(chLink, length, channelFlowLengths)
            
    def setChannelFlowLength(self, chLink, length, channelFlowLengths):
        """Add eentry for chLink to channelFlowLengths map.  Also update maxFlowLengths for chLink's subbasin.
        
        post: chLink in channelFlowLengths
        """
        if chLink in channelFlowLengths:
            return # nothing to do: set on previous recursive call
        if chLink in self.zeroChannels:
            return
        chBasin = self.chLinkToChBasin[chLink]
        subbasin = self.chBasinToSubbasin[chBasin]
        dsLink = self.downChannels[chLink]
        dsChBasin = self.chLinkToChBasin.get(dsLink, -1)
        dsBasin = self.chBasinToSubbasin.get(dsChBasin, -1)
        if dsBasin == subbasin:
            # still in same subbasin:
            # add this channel's length to downstream flow length
            dsFlowLength = channelFlowLengths.get(dsLink, -1)
            if dsFlowLength < 0:
                self.setChannelFlowLength(dsLink, self.channelLengths[dsLink], channelFlowLengths)
                dsFlowLength = channelFlowLengths[dsLink]
            flowLength = dsFlowLength + length
        else:
            # outlet channel for subbasin
            flowLength = length
        channelFlowLengths[chLink] = flowLength
        maxFlowLength = self.maxFlowLengths.get(subbasin, 0)
        if flowLength > maxFlowLength:
            self.maxFlowLengths[subbasin] = flowLength
        
                    
    def writePointsTable(self, demLayer, mergees, useGridModel):
        """Write the gis_points table in the project database."""
        with self.db.conn as conn:
            if not conn:
                return
            curs = conn.cursor()
            table = 'gis_points'
            clearSQL = 'DROP TABLE IF EXISTS ' + table
            curs.execute(clearSQL)
            curs.execute(self.db._POINTSCREATESQL)
            waterAdded = []
            # Add outlets from streams
            for subbasin, (pointId, pt, chLink) in self.outlets.items():
                if subbasin in self.upstreamFromInlets or subbasin in self.outletsInLake or \
                    chLink in self.chLinkInsideLake:
                    continue # excluded
                elev = QSWATTopology.valueAtPoint(pt, demLayer)
                self.addPoint(curs, subbasin, pointId, pt, elev, 'O')
            # Add inlets
            if useGridModel:
                for chLink, (pointId, pt) in self.chLinkToInlet.items():
                    if chLink in self.chLinkInsideLake or chLink in self.chLinkFromLake:  # shouldn't happen
                        continue
                    subbasin = self.chLinkToChBasin[chLink]
                    elev = QSWATTopology.valueAtPoint(pt, demLayer)
                    self.addPoint(curs, subbasin, pointId, pt, elev, 'I')
            else:
                for subbasin, (pointId, pt) in self.inlets.items():
                    if subbasin in self.upstreamFromInlets: 
                    # shouldn't happen, but users can be stupid
                        continue
                    elev = QSWATTopology.valueAtPoint(pt, demLayer)
                    self.addPoint(curs, subbasin, pointId, pt, elev, 'I')
            # Add point sources at heads of channels
            for chLink, (pointId, pt) in self.chLinkToPtSrc.items():
                if chLink in self.chLinkInsideLake:
                    continue
                if useGridModel:
                    if chLink in self.chLinkFromLake:
                        continue
                    subbasin = self.chLinkToChBasin[chLink]
                else:
                    chBasin = self.chLinkToChBasin.get(chLink, -1)
                    subbasin = self.chBasinToSubbasin.get(chBasin, -1)
                    if subbasin < 0 or subbasin in self.upstreamFromInlets:
                        continue
                elev = QSWATTopology.valueAtPoint(pt, demLayer)
                self.addPoint(curs, subbasin, pointId, pt, elev, 'P')
            for chLink, (pointId, pt) in self.chPointSources.items():
                if chLink in self.chLinkToPtSrc or chLink in mergees or chLink in self.chLinkInsideLake:
                    continue  # link has user-defined point source flowing into it or has been merged or is inside lake
                if useGridModel:
                    if chLink in self.chLinkFromLake:
                        continue  # channel is inside lake
                    subbasin = self.chLinkToChBasin[chLink]
                else:
                    chBasin = self.chLinkToChBasin.get(chLink, -1)
                    subbasin = self.chBasinToSubbasin.get(chBasin, -1)
                    if subbasin < 0 or subbasin in self.upstreamFromInlets:
                        continue
                elev = QSWATTopology.valueAtPoint(pt, demLayer)
                self.addPoint(curs, subbasin, pointId, pt, elev, 'P')
            # Add lakes
            for lake in self.lakesData.values():
                # outlet from lake
                subbasin, pointId, pt, elev = lake.outPoint
                chLink = lake.outChLink
                if useGridModel:
                    # subbasin for outlet will be inside lake and addPoint will fail
                    # since there will be no SWAT basin.  Use one downstream if there is one
                    downChLink = self.downChannels[chLink]
                    if downChLink >= 0:
                        subbasin = self.chLinkToChBasin[downChLink]
                elif chLink == -1:
                    # main outlet was moved inside lake, but reservoir point will still be routed to it
                    # so add its definition
                    (outletId, outPt, _) = self.outlets[subbasin]
                    self.addPoint(curs, subbasin, outletId, outPt, elev, 'O')
                self.addPoint(curs, subbasin, pointId, pt, elev, 'W')
                waterAdded.append(pointId)
                # inlets to lake.  These are outlets from streams in grid models, so not necessary
                if not useGridModel:
                    for chLink, (pointId, pt, elev) in lake.inChLinks.items():
                        chBasin = self.chLinkToChBasin[chLink]
                        subbasin = self.chBasinToSubbasin[chBasin]
                        self.addPoint(curs, subbasin, pointId, pt, elev, 'O')
            for chLink, (pointId, pt, _) in self.chLinkToWater.items():
                # reservoir points at lake outlets can appear here 
                # but already added from lakesdata
                if pointId in waterAdded:
                    continue
                if useGridModel:
                    subbasin = self.chLinkToChBasin[chLink]
                else:
                    chBasin = self.chLinkToChBasin.get(chLink, -1)
                    subbasin = self.chBasinToSubbasin.get(chBasin, -1)
                    if subbasin in self.upstreamFromInlets:
                        continue
                elev = QSWATTopology.valueAtPoint(pt, demLayer)
                self.addPoint(curs, subbasin, pointId, pt, elev, 'W')
            for channel, (_, pointId, pt) in self.foundReservoirs.items():
                if useGridModel:
                    subbasin = self.chLinkToChBasin[channel]
                else:
                    chBasin = self.chLinkToChBasin.get(channel, -1)
                    subbasin = self.chBasinToSubbasin.get(chBasin, -1)
                    if subbasin in self.upstreamFromInlets:
                        continue
                elev = QSWATTopology.valueAtPoint(pt, demLayer)
                self.addPoint(curs, subbasin, pointId, pt, elev, 'W')
#             for subbasin, (pointId, pt) in self.extraReservoirs.iteritems():
#                 if subbasin in self.upstreamFromInlets: 
#                 # shouldn't happen, but users can be stupid
#                     continue
#                 elev = QSWATTopology.valueAtPoint(pt, demLayer)
#                 self.addPoint(curs, subbasin, pointId, pt, elev, 'R')
            conn.commit()
            
    def addExtraPointsToPointsTable(self, extraPoints, useGridModel):
        """Add extra points needed to mark where channels drain into reservoirs."""
        with self.db.conn as conn:
            if not conn:
                return
            curs = conn.cursor()
            for channel, pointId in extraPoints:
                if useGridModel:
                    subbasin = self.chLinkToChBasin[channel]
                else:
                    chBasin = self.chLinkToChBasin[channel]
                    subbasin = self.chBasinToSubbasin[chBasin]
                data = self.channelsData[channel]
                pt = QgsPointXY(data.lowerX, data.lowerY)
                self.addPoint(curs, subbasin, pointId, pt, data.lowerZ, 'O')
            conn.commit()
            
    def addPoint(self, cursor, subbasin, pointId, pt, elev, typ):
        """Add point to gis_points table."""
        table = 'gis_points'
        SWATBasin = self.subbasinToSWATBasin.get(subbasin, 0)
        if SWATBasin == 0:
            return
        ptll = self.pointToLatLong(pt)
        sql = "INSERT INTO " + table + " VALUES(?,?,?,?,?,?,?,?)"
        try:
            cursor.execute(sql, (pointId, SWATBasin, typ,
                           pt.x(), pt.y(), ptll.y(), ptll.x(), elev))
        except:
            QSWATUtils.exceptionError('Internal error: unable to add point {0} type {1}'.format(pointId, typ), self.isBatch)
    
    #===========================================================================
    # def addPoint(self, cursor, link, data, pointId, typ):
    #     """Add a point to the points table."""
    #     table = 'gis_points'
    #     # inlets will be located at the upstream ends of their links
    #     # since they are attached to their downstream basins
    #     if not data:
    #         return
    #     SWATBasin = self.subbasinToSWATBasin.get(data.ru, 0)
    #     if SWATBasin == 0:
    #         return
    #     lsu = 0
    #     if typ == 'I': # inlet
    #         pt = QgsPointXY(data.upperX, data.upperY)
    #         elev = data.upperZ
    #         drainId = SWATBasin 
    #         drainCat = 'R'
    #     else:
    #         pt = QgsPointXY(data.lowerX, data.lowerY)
    #         elev = data.lowerZ
    #         if typ == 'P': # point source
    #             resId = self.linkToReservoir.get(link, 0)
    #             if resId > 0: 
    #                 # point source drains to reservoir
    #                 drainId = resId
    #                 drainCat = 'P'
    #             else:
    #                 # point source drains to link outlet
    #                 drainId = self.linkToOutlet[link]
    #                 drainCat = 'P'
    #         elif typ == 'R': # reservoir: drains to link outlet
    #             drainId = self.linkToOutlet[link]
    #             drainCat = 'P'
    #         else:
    #             assert typ == 'O', u'Unknown point type: ' + typ
    #             # outlet: drains to reach of downstream basin (if any)
    #             dsLink = self.downLinks[link]
    #             dsSWATBasin = 0
    #             while dsLink >= 0 and dsSWATBasin == 0:
    #                 dsBasin = self.linkToBasin[dsLink]
    #                 dsSWATBasin = self.subbasinToSWATBasin.get(dsBasin, 0)
    #                 if dsSWATBasin == 0:
    #                     dsLink = self.downLinks[dsLink]
    #             if dsSWATBasin > 0:
    #                 drainId = dsSWATBasin
    #                 drainCat = 'R'
    #             else:
    #                 drainId = -1
    #                 drainCat = 'X'
    #     ptll = self.pointToLatLong(pt)
    #     sql = "INSERT INTO " + table + " VALUES(?,?,?,?,?,?,?,?,?)"
    #     cursor.execute(sql, (pointId, SWATBasin, lsu, typ, \
    #                    pt.x(), pt.y(), ptll.y(), ptll.x(), elev))
    #===========================================================================
    
    def writeChannelsTable(self, mergeChannels, basins, gv):
        """
        Write the channels table in the project database, make rivs1.shp in shapes directory, and copy as results template to TablesOut directory.
        
        Changes the channel layer, so if successful, returns the new one.
        """
        root = QgsProject.instance().layerTreeRoot()
        if gv.useGridModel:
            # use streams as channels
            channelFile = gv.streamFile
            strng = 'streams'
        else:
            channelFile = gv.channelFile
            strng = 'channel'
        if not os.path.exists(channelFile):
            QSWATUtils.error('Cannot find {0} file {1}'.format(strng, channelFile), gv.isBatch)
            return
        channelLayer = QSWATUtils.getLayerByFilename(root.findLayers(), channelFile, FileTypes._CHANNELS, 
                                                     None, None, None)[0]
        if channelLayer is None: # perhaps removed by user
            channelLayer = QgsVectorLayer(channelFile, 'Channels', 'ogr')
        QSWATUtils.copyShapefile(channelFile, Parameters._RIVS1, gv.shapesDir)
        rivs1File = QSWATUtils.join(gv.shapesDir, Parameters._RIVS1 + '.shp')
        QSWATUtils.removeLayer(rivs1File, root)
        rivs1Layer = QgsVectorLayer(rivs1File, 'Channels ({0})'.format(Parameters._RIVS1), 'ogr')
        provider1 = rivs1Layer.dataProvider()
        # add Channel, ChannelR, and Subbasin fields unless already has them
        chIdx = self.getIndex(rivs1Layer, QSWATTopology._CHANNEL, ignoreMissing=True)
        chRIdx = self.getIndex(rivs1Layer, QSWATTopology._CHANNELR, ignoreMissing=True)
        subIdx = self.getIndex(rivs1Layer, QSWATTopology._SUBBASIN, ignoreMissing=True)
        if chIdx < 0:
            OK = provider1.addAttributes([QgsField(QSWATTopology._CHANNEL, QVariant.Int)])
            if not OK:
                QSWATUtils.error('Cannot add {0} field to channels shapefile {1}'.format(QSWATTopology._CHANNEL, rivs1File), self.isBatch)
                return None
        if chRIdx < 0:
            OK = provider1.addAttributes([QgsField(QSWATTopology._CHANNELR, QVariant.Int)])
            if not OK:
                QSWATUtils.error('Cannot add {0} field to channels shapefile {1}'.format(QSWATTopology._CHANNELR, rivs1File), self.isBatch)
                return None
        if subIdx < 0:
            OK = provider1.addAttributes([QgsField(QSWATTopology._SUBBASIN, QVariant.Int)])
            if not OK:
                QSWATUtils.error('Cannot add {0} field to channels shapefile {1}'.format(QSWATTopology._SUBBASIN, rivs1File), self.isBatch)
                return None
        rivs1Layer.updateFields()
        chIdx = self.getIndex(rivs1Layer, QSWATTopology._CHANNEL)
        chRIdx = self.getIndex(rivs1Layer, QSWATTopology._CHANNELR)
        subIdx = self.getIndex(rivs1Layer, QSWATTopology._SUBBASIN)
        chLinkIdx = self.getIndex(rivs1Layer, QSWATTopology._LINKNO)
        request = QgsFeatureRequest().setSubsetOfAttributes([chLinkIdx])
        if not gv.useGridModel:
            basinMerge = self.mergeChannelData(mergeChannels)
            # make map channel -> feature it is merged with for merged channels
            merges = dict()
            targets = []
            for reach in provider1.getFeatures(request):
                for channel in mergeChannels.keys():
                    target = self.finalTarget(channel, mergeChannels)
                    if target not in targets:
                        targets.append(target)
                    if reach[chLinkIdx] == target:
                        merges[channel] = reach
                        #QSWATUtils.loginfo('Channel {0} merging to target {1} with length {2}'.format(channel, target, reach.geometry().length()))
            # create geometries for merged reaches
            merged = []
            for reach in provider1.getFeatures(request):
                rid = reach.id()
                channel = reach[chLinkIdx]
                if channel in targets and rid not in merged:
                    merged.append(rid)
                mergeReach = merges.get(channel, None)
                if mergeReach is not None:
                    # add its geometry to its merger target
                    #length1 = mergeReach.geometry().length()
                    #length2 = reach.geometry().length()
                    mergeReach.setGeometry(mergeReach.geometry().combine(reach.geometry()))
                    #length3 = mergeReach.geometry().length()
                    #QSWATUtils.loginfo('Channel {0} merged to target with length {1} ({2} + {3})' \
                    #                   .format(channel, length3, length1, length2))
                    if rid not in merged:
                        merged.append(rid)
            # remove channels and targets involved in mergers
            provider1.deleteFeatures(merged)
            # add mergers
            mergers = []
            for channel, reach in merges.items():
                if reach not in mergers:
                    mergers.append(reach)
            provider1.addFeatures(mergers)
        chsMap = dict()
        zeroRids = []
        for reach in provider1.getFeatures(request):
            channel = reach[chLinkIdx]
            if gv.useGridModel:
                # subbasin and chBasin are the same
                subbasin = self.chLinkToChBasin.get(channel, -1)
                downChannel = self.downChannels[channel]
            else:
                chBasin = self.chLinkToChBasin.get(channel, -1)
                subbasin = self.chBasinToSubbasin.get(chBasin, -1)
                downChannel = self.finalDownstream(channel, mergeChannels)
            SWATBasin = self.subbasinToSWATBasin.get(subbasin, 0)
            SWATChannel = 0 if SWATBasin == 0 else self.channelToSWATChannel.get(channel, 0)                                                                                                                                                                                                                                                                                               
            downSWATChannel = self.channelToSWATChannel.get(downChannel, 0)
            rid = reach.id()
            if SWATChannel == 0:
                zeroRids.append(rid)
            chsMap[rid] = dict()
            chsMap[rid][chIdx] = SWATChannel
            chsMap[rid][chRIdx] = downSWATChannel
            chsMap[rid][subIdx] = SWATBasin
        OK = provider1.changeAttributeValues(chsMap)
        if not OK:
            QSWATUtils.error('Cannot add channel and subbasin values to channels shapefile {0}'.format(rivs1File), self.isBatch)
            return None
        if len(zeroRids) > 0:
            OK = provider1.deleteFeatures(zeroRids)
            if not OK:
                QSWATUtils.error('Cannot remove merged, zero length, or above inlet channels from channels shapefile {0}'.format(rivs1File), self.isBatch)
                return None
        # Add fields from channels table to rivs1File if less than RIV1SUBS1MAX features; otherwise takes too long.
        addToRiv1 = rivs1Layer.featureCount() <= Parameters._RIVS1SUBS1MAX
        # remove fields apart from Channel, ChannelR and Subbasin
        if addToRiv1:
            self.removeFields(provider1, [QSWATTopology._LINKNO, QSWATTopology._CHANNEL, QSWATTopology._CHANNELR, QSWATTopology._SUBBASIN], rivs1File, self.isBatch)
        if addToRiv1:
            fields = []
            fields.append(QgsField(QSWATTopology._AREAC, QVariant.Double, len=20, prec=0))
            fields.append(QgsField(QSWATTopology._LEN2, QVariant.Double))
            fields.append(QgsField(QSWATTopology._SLO2, QVariant.Double))
            fields.append(QgsField(QSWATTopology._WID2, QVariant.Double))
            fields.append(QgsField(QSWATTopology._DEP2, QVariant.Double))
            fields.append(QgsField(QSWATTopology._MINEL, QVariant.Double))
            fields.append(QgsField(QSWATTopology._MAXEL, QVariant.Double))
            fields.append(QgsField(QSWATTopology._RESERVOIR, QVariant.Int))
            fields.append(QgsField(QSWATTopology._POND, QVariant.Int))
            fields.append(QgsField(QSWATTopology._LAKEIN, QVariant.Int))
            fields.append(QgsField(QSWATTopology._LAKEOUT, QVariant.Int))
            provider1.addAttributes(fields)
            rivs1Layer.updateFields()
            linkIdx = self.getIndex(rivs1Layer, QSWATTopology._LINKNO)
            chIdx = self.getIndex(rivs1Layer, QSWATTopology._CHANNEL)
            areaCIdx = self.getIndex(rivs1Layer, QSWATTopology._AREAC)
            len2Idx = self.getIndex(rivs1Layer, QSWATTopology._LEN2)
            slo2Idx = self.getIndex(rivs1Layer, QSWATTopology._SLO2)
            wid2Idx = self.getIndex(rivs1Layer, QSWATTopology._WID2)
            dep2Idx = self.getIndex(rivs1Layer, QSWATTopology._DEP2)
            minElIdx = self.getIndex(rivs1Layer, QSWATTopology._MINEL)
            maxElIdx = self.getIndex(rivs1Layer, QSWATTopology._MAXEL)
            resIdx = self.getIndex(rivs1Layer, QSWATTopology._RESERVOIR)
            pndIdx = self.getIndex(rivs1Layer, QSWATTopology._POND)
            lakeInIdx = self.getIndex(rivs1Layer, QSWATTopology._LAKEIN)
            lakeOutIdx = self.getIndex(rivs1Layer, QSWATTopology._LAKEOUT)
            mmap = dict()
        with self.db.conn as conn:
            if not conn:
                return None
            curs = conn.cursor()
            table = 'gis_channels'
            clearSQL = 'DROP TABLE IF EXISTS ' + table
            curs.execute(clearSQL)
            curs.execute(self.db._CHANNELSCREATESQL)
            time1 = time.process_time()
            wid2Data = dict()
            floodscape = QSWATUtils._FLOODPLAIN if gv.useLandscapes else QSWATUtils._NOLANDSCAPE 
            sql = "INSERT INTO " + table + " VALUES(?,?,?,?,?,?,?,?,?)"
            if addToRiv1:
                # iterate over channels in rivs1 shapefile
                request =  QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([linkIdx, chIdx])
                generator = self.generateChannelsFromShapefile(request, provider1, linkIdx, chIdx)
            else:
                generator = self.generateChannelsFromTable()
            toDelete = []
            for fid, channel, SWATChannel in generator:
                if gv.useGridModel:
                    # basin and chBasin are the same
                    subbasin = self.chLinkToChBasin[channel]
                else:
                    chBasin = self.chLinkToChBasin.get(channel, -1)
                    subbasin = self.chBasinToSubbasin.get(chBasin, -1)
                SWATBasin = 0 if channel in self.chLinkInsideLake else self.subbasinToSWATBasin.get(subbasin, 0)
                lakeOutId = self.chLinkFromLake.get(channel, 0)
                if SWATBasin == 0 and (lakeOutId == 0 or self.downChannels.get(channel, -1) < 0):
                    toDelete.append(fid)
                    continue
                if gv.useGridModel:
                    channelData = self.channelsData[channel]
                    # drain area is a numpy float, so need to coerce, or won't get written to attributes of rivs1
                    drainAreaHa = float(self.drainAreas[channel]) / 1E4
                    length = float(self.channelLengths[channel] * gv.mainLengthMultiplier)
                    slopePercent = float(self.channelSlopes[channel] * 100 * gv.reachSlopeMultiplier / gv.mainLengthMultiplier)
                    minEl = float(channelData.lowerZ)
                    maxEl = float(channelData.upperZ)             
                else:
                    mergeData = basinMerge.get(channel, None)
                    if mergeData is None:
                        continue
                    drainAreaHa = float(mergeData.areaC / 1E4)
                    length = float(mergeData.length  * gv.mainLengthMultiplier)
                    slopePercent = float(mergeData.slope * 100 * gv.reachSlopeMultiplier) / gv.mainLengthMultiplier
                    minEl = float(mergeData.minEl)
                    maxEl = float(mergeData.maxEl)
                # possible for channel to be so short it has no pixels draining to it
                # also no LSU data when channel is outlet from lake in grid model
                basinData = basins.get(subbasin, None)
                lsuData = None if basinData is None else basinData.getLsus().get(channel, None)
                drainAreaKm = float(drainAreaHa) / 100 
                channelWidth = float(gv.channelWidthMultiplier * (drainAreaKm ** gv.channelWidthExponent))
                wid2Data[SWATChannel] = channelWidth
                channelDepth = float(gv.channelDepthMultiplier * (drainAreaKm ** gv.channelDepthExponent))
                rid = 0 if lsuData is None else self.getReservoirId(lsuData, floodscape)
                pid = 0 if lsuData is None else self.getPondId(lsuData, floodscape)
                if rid == 0 and pid == 0:
                    # omit from gis_channels channels which have become reservoirs or ponds
                    curs.execute(sql, (SWATChannel, SWATBasin, drainAreaHa, length, slopePercent, 
                                       channelWidth, channelDepth, minEl, maxEl))
                if addToRiv1:
                    lakeInId = self.chLinkIntoLake.get(channel, 0)
                    mmap[fid] = dict()
                    mmap[fid][areaCIdx] = drainAreaHa
                    mmap[fid][len2Idx] = length
                    mmap[fid][slo2Idx] = slopePercent
                    mmap[fid][wid2Idx] = channelWidth
                    mmap[fid][dep2Idx] = channelDepth
                    mmap[fid][minElIdx] = minEl
                    mmap[fid][maxElIdx] = maxEl
                    mmap[fid][resIdx] = rid
                    mmap[fid][pndIdx] = pid
                    mmap[fid][lakeInIdx] = lakeInId
                    mmap[fid][lakeOutIdx] = lakeOutId
            time2 = time.process_time()
            QSWATUtils.loginfo('Writing gis_channels table took {0} seconds'.format(int(time2 - time1)))
            conn.commit()
            self.db.hashDbTable(conn, table)
        if addToRiv1:
            if not provider1.changeAttributeValues(mmap):
                QSWATUtils.error('Cannot edit values in channels shapefile {0}'.format(rivs1File), self.isBatch)
                return None
        if len(toDelete) > 0:
            OK = provider1.deleteFeatures(toDelete)
            if not OK:
                QSWATUtils.error('Cannot remove channels in lakes from channels shapefile {0}'.format(rivs1File), self.isBatch)
                return None
        # make copy as template for stream results
        QSWATUtils.copyShapefile(rivs1File, Parameters._RIVS, gv.resultsDir)
        rivFile = QSWATUtils.join(gv.resultsDir, Parameters._RIVS + '.shp')
        rivLayer = QgsVectorLayer(rivFile, 'Channels', 'ogr')
        provider = rivLayer.dataProvider()
        # leave only the Channel, ChannelR and Subbasin attributes
        self.removeFields(provider, [QSWATTopology._CHANNEL, QSWATTopology._CHANNELR, QSWATTopology._SUBBASIN], rivFile, self.isBatch)
        # add PenWidth field to stream results template
        OK = provider.addAttributes([QgsField(QSWATTopology._PENWIDTH, QVariant.Double)])
        if not OK:
            QSWATUtils.error('Cannot add {0} field to streams results template {1}'.format(QSWATTopology._PENWIDTH, rivFile), self.isBatch)
            return None
        self.setPenWidth(wid2Data, provider)
        if gv.useGridModel:
            return channelLayer
        else:
            layers = root.findLayers()
            subLayer = root.findLayer(channelLayer.id())
            rivs1Layer = QSWATUtils.getLayerByFilename(layers, rivs1File, FileTypes._CHANNELREACHES, 
                                                      gv, subLayer, QSWATUtils._WATERSHED_GROUP_NAME)[0]
            # hide channel layer
            if channelLayer is not None:
                QSWATUtils.setLayerVisibility(channelLayer, False, root)
            if len(self.upstreamFromInlets) > 0:
                self.replaceStreamLayer(root, layers, gv)
            return rivs1Layer
        
    def generateChannelsFromShapefile(self, request, provider, linkIdx, chIdx):
        """Yield (feature id, channel, swatChammel) tupless from rivs1.shp."""
        for feature in provider.getFeatures(request):
            yield feature.id(), feature[linkIdx], feature[chIdx]
            
    def generateChannelsFromTable(self):
        """Yield (feature id, channel, swatChammel) tuples from tables."""
        for channel, SWATChannel in self.channelToSWATChannel.items():
            yield 0, channel, SWATChannel
            
    def replaceStreamLayer(self, root, layers, gv):
        """Copy stream layer, remove streams upstream from inlets, and replace stream layer."""
        streamLayer = QSWATUtils.getLayerByFilename(layers, gv.streamFile, FileTypes._STREAMREACHES, gv, None, None)[0]
        if streamLayer is not None:
            base, _ = os.path.splitext(os.path.split(gv.streamFile)[1])
            QSWATUtils.copyShapefile(gv.streamFile, base + 'act', gv.shapesDir)
            actStreamFile = QSWATUtils.join(gv.shapesDir, base + 'act.shp')
            actstreamLayer = QgsVectorLayer(actStreamFile, FileTypes.legend(FileTypes._STREAMREACHES), 'ogr')
            basinIdx = self.getIndex(actstreamLayer, QSWATTopology._WSNO)
            if basinIdx < 0:
                return
            provider = actstreamLayer.dataProvider()
            request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([basinIdx])
            toDelete = []
            for feature in provider.getFeatures(request):
                if feature[basinIdx] in self.upstreamFromInlets:
                    toDelete.append(feature.id())
            if provider.deleteFeatures(toDelete):
                subLayer = root.findLayer(streamLayer.id())
                actstreamLayer = QSWATUtils.getLayerByFilename(layers, actStreamFile, FileTypes._STREAMREACHES, gv, subLayer, 
                                                               QSWATUtils._WATERSHED_GROUP_NAME, True)[0]
                QSWATUtils.setLayerVisibility(streamLayer, False, root)
                
        
    def getReservoirId(self, channelData, floodscape):
        """Return reservoir id, if any, else 0."""
        lsuData = channelData.get(floodscape, None)
        if lsuData is not None and lsuData.waterBody is not None and lsuData.waterBody.isReservoir():
            return lsuData.waterBody.id
        return 0
    
    def getPondId(self, channelData, floodscape):
        """Return pond id, if any, else 0."""
        lsuData = channelData.get(floodscape, None)
        if lsuData is not None and lsuData.waterBody is not None and lsuData.waterBody.isPond():
            return lsuData.waterBody.id
        return 0
        
    def mergeChannelData(self, mergeChannels):
        """Generate and return map of channel to MergedChannelData."""
        
        # first pass: collect data for unmerged channels
        mergedChannelData = dict()
        for channel in self.channelToSWATChannel.keys():
            if channel not in mergeChannels:
                channelData = self.channelsData[channel]
                mergedChannelData[channel] = MergedChannelData(self.drainAreas[channel],
                                                               self.channelLengths[channel],
                                                               self.channelSlopes[channel],
                                                               channelData.lowerZ,
                                                               channelData.upperZ)
        # second pass: add data for merged channels
        for source, target in mergeChannels.items():
            channelData = self.channelsData[channel]
            final = self.finalTarget(target, mergeChannels)
            mergedChannelData[final].add(self.drainAreas[source],
                                         self.channelLengths[source],
                                         self.channelSlopes[source],
                                         channelData.lowerZ,
                                         channelData.upperZ)
        return mergedChannelData
             
    def finalTarget(self, target, mergeChannels):
        """Find final target of merges."""
        nxt = mergeChannels.get(target, -1)
        if nxt < 0:
            return target
        else:
            return self.finalTarget(nxt, mergeChannels)
                
    def finalDownstream(self, start, mergeChannels):
        """Find downstream channel from start, skipping merged channels, and return it."""
        chLink1 = self.finalTarget(start, mergeChannels)
        return self.finalTarget(self.getDownChannel(chLink1), mergeChannels)
            
    def routeChannelsOutletsAndBasins(self, basins, mergedChannels, mergees, extraPoints, gv):
        """Add channels, lakes, basins, point sources, reservoirs, inlets and outlets to main gis_routing table."""
        
        chCat = 'CH'
        subbasinCat = 'SUB'
        ptCat = 'PT'
        resCat = 'RES'
        pondCat = 'PND'
        xCat = 'X'
        # first associate any inlets, point sources and reservoirs with appropriate channels
        if gv.useGridModel:
            # no merging
            channelToInlet = self.chLinkToInlet
            channelToPtSrc = self.chLinkToPtSrc
        else:
            channelToInlet = dict()
            for subbasin, inlet in self.inlets.items():
                # find an inlet channel for this subbasin
                found = False
                for channel, data in self.channelsData.items():
                    chBasin = self.chLinkToChBasin.get(channel, -1)
                    if subbasin == self.chBasinToSubbasin.get(chBasin, -1) and \
                        QSWATTopology.coincidentPoints(QgsPointXY(data.upperX, data.upperY), 
                                                       inlet[1], self.xThreshold, self.yThreshold):
                        channelToInlet[self.finalTarget(channel, mergedChannels)] = inlet
                        found = True
                        break
                if not found:
                    QSWATUtils.error('Failed to find channel for inlet to subbasin {0}'.format(subbasin), gv.isBatch)
            # map point sources to the unmerged channels they drain into
            channelToPtSrc = dict()
            for channel, ptsrc in self.chLinkToPtSrc.items():
                channelToPtSrc[channel] = ptsrc
                #QSWATUtils.loginfo('Channel {0} merged to {1} has point source {2}'.format(channel, self.finalTarget(channel, mergedChannels), ptsrc[0]))
        # add point sources at stream sources
        for channel, ptsrc in self.chPointSources.items():
            if channel not in channelToPtSrc and channel not in mergees and \
                channel not in self.chLinkInsideLake and \
                not (gv.useGridModel and channel in self.chLinkFromLake):  # not already has a point, not merged, not inslide lake 
                channelToPtSrc[channel] = ptsrc
        # map channels to water bodies that replace them as drainage targets
        # and water bodies to channels they drain into
        floodscape = QSWATUtils._FLOODPLAIN if gv.useLandscapes else QSWATUtils._NOLANDSCAPE
        channelToWater = dict()
        for basinData in basins.values():
            for channel, channelData in basinData.getLsus().items():
                lsuData = channelData.get(floodscape, None)
                if lsuData is not None and lsuData.waterBody is not None and not lsuData.waterBody.isUnknown():
                    channelToWater[channel] = (lsuData.waterBody.id, lsuData.waterBody.waterRole)
        try:
            with self.db.conn as conn:
                curs = conn.cursor()
                routedPoints = []
                routedWater = []
                routedChannels = []
#                 routedSubbasins = []
                for channel, SWATChannel in self.channelToSWATChannel.items():
                    if channel in mergedChannels:
                        # all that is needed is to map its point source to the merge target
                        ptsrc = channelToPtSrc.get(channel, None)
                        if ptsrc is not None:
                            ptsrcId = ptsrc[0]
                            if ptsrcId not in routedPoints:
                                finalChannel = self.finalTarget(channel, mergedChannels)
                                wid, role = channelToWater.get(finalChannel, (-1, -1))
                                if wid >= 0:
                                    wCat = resCat if role == 1 else pondCat
                                    curs.execute(DBUtils._ROUTINGINSERTSQL, 
                                                 (ptsrcId, ptCat, wid, wCat, 100))
                                else:
                                    finalSWATChannel = self.channelToSWATChannel[finalChannel]
                                    curs.execute(DBUtils._ROUTINGINSERTSQL, 
                                                 (ptsrcId, ptCat, finalSWATChannel, chCat, 100))
                                routedPoints.append(ptsrcId)
                        continue
                    # if channel is lake outflow
                    # if main outflow, route lake to outlet and outlet to channel
                    # else route 0% of lake to channel
                    outLakeId = self.chLinkFromLake.get(channel, -1)
                    if outLakeId >= 0:
                        lakeData = self.lakesData[outLakeId]
                        wCat = resCat if lakeData.waterRole == 1 else pondCat
                        if channel == lakeData.outChLink:
                            # main outlet
                            outletId = lakeData.outPoint[1]
                            curs.execute(DBUtils._ROUTINGINSERTSQL, (outLakeId, wCat, outletId, ptCat, 100))
                            if outletId not in routedPoints:
                                if gv.useGridModel and self.downChannels.get(channel, -1) < 0:
                                    # we have an internal lake exit: route outlet id to watershed exit
                                    curs.execute(DBUtils._ROUTINGINSERTSQL, (outletId, ptCat, 0, xCat, 100))
                                else:
                                    curs.execute(DBUtils._ROUTINGINSERTSQL, (outletId, ptCat, SWATChannel, chCat, 100))
                            routedPoints.append(outletId)
                        else:
                            # other outlet
                            curs.execute(DBUtils._ROUTINGINSERTSQL, (outLakeId, wCat, SWATChannel, chCat, 0))
                    # check if channel routes into lake
                    inLakeId = self.chLinkIntoLake.get(channel, -1)
                    if inLakeId >= 0:
                        # route its point source to the channel
                        ptsrc = channelToPtSrc.get(channel, None)
                        if ptsrc is not None:
                            ptsrcId = ptsrc[0]
                            if ptsrcId not in routedPoints:
                                curs.execute(DBUtils._ROUTINGINSERTSQL, 
                                                 (ptsrcId, ptCat, SWATChannel, chCat, 100))
                                routedPoints.append(ptsrcId)
                        # route the channel into its outlet, and the outlet into the lake
                        lakeData = self.lakesData[inLakeId]
                        outletId = lakeData.inChLinks[channel][0]
                        wCat = resCat if lakeData.waterRole == 1 else pondCat
                        if SWATChannel not in routedChannels:
                            curs.execute(DBUtils._ROUTINGINSERTSQL, (SWATChannel, chCat, outletId, ptCat, 100))
                            routedChannels.append(SWATChannel)
                        if outletId not in routedPoints:
                            curs.execute(DBUtils._ROUTINGINSERTSQL, (outletId, ptCat, inLakeId, wCat, 100))
                            routedPoints.append(outletId)
                        if not gv.useGridModel:
                            continue # since we know it is into the lake and so cannot have a downstream channel or be a subbasin outlet
                    if gv.useGridModel:
                        subbasin = self.chLinkToChBasin[channel]
                    else:
                        chBasin = self.chLinkToChBasin.get(channel, -1)
                        subbasin = self.chBasinToSubbasin.get(chBasin, -1)
                    SWATBasin = self.subbasinToSWATBasin.get(subbasin, 0)
                    if SWATBasin == 0:
                        continue
                    # if channel is inside lake ignore it unless a lake outflow
                    if channel in self.chLinkInsideLake and outLakeId < 0:
                        continue
                    dsChannel = self.finalDownstream(channel, mergedChannels)
                    dsSWATChannel = self.channelToSWATChannel.get(dsChannel, 0)
                    wid, role = channelToWater.get(channel, (-1, -1))
                    wCat = resCat if role == 1 else pondCat
                    inlet = channelToInlet.get(channel, None)
                    if inlet is not None:
                        # route inlet to channel or water
                        if wid >= 0:
                            curs.execute(DBUtils._ROUTINGINSERTSQL, (inlet[0], ptCat, wid, wCat, 100))
                        else:
                            curs.execute(DBUtils._ROUTINGINSERTSQL, (inlet[0], ptCat, SWATChannel, chCat, 100))
                    (pointId, _, outletChannel) = self.outlets[subbasin]
                    if channel == outletChannel or gv.useGridModel:
                        # subbasin outlet: channel routes to outlet point of subbasin; outlet routes to downstream channel
                        # but with some exceptions:
                        # - if the channel is replaced by a reservoir, this is routed to the outlet instead
                        # - if subbasin has an extra point source, this is added to its outlet channel or reservoir
                        if gv.useGridModel:
                            ptsrc = channelToPtSrc.get(channel, None)
                        else:
                            ptsrc = None
#                         if ptsrc is None:
#                             ptsrc = self.extraPtSrcs.get(subbasin, None)
                        if ptsrc is not None:
                            # route it to the outlet channel, unless already routed
                            ptsrcId = ptsrc[0]
                            if ptsrcId not in routedPoints:
                                if wid < 0:
                                    curs.execute(DBUtils._ROUTINGINSERTSQL, 
                                                 (ptsrcId, ptCat, SWATChannel, chCat, 100))
                                else:
                                    curs.execute(DBUtils._ROUTINGINSERTSQL, 
                                                 (ptsrcId, ptCat, wid, wCat, 100))
                                routedPoints.append(ptsrcId)
                        if wid >= 0:
                            # need to check if this is a reservoir that is continued in the downstream subbasin
                            # to make sure we only route it once, and at its final downstream end
                            widDown, _ = channelToWater.get(dsChannel, (-1, -1))
                            if wid not in routedWater and wid != widDown:
                                # route water to water point and water point to outlet
                                (waterId, _, _) = self.chLinkToWater.get(channel, (-1, None, -1))
                                if waterId < 0:
                                    (waterId, ptId, _) = self.foundReservoirs.get(channel, (-1, -1, None))
                                else:
                                    # it is safe to use same id for reservoir and reservoir outlet point when
                                    # using DSNODEID from inlets/outlets file
                                    ptId = waterId
                                if waterId < 0:
                                    QSWATUtils.error('Cannot find water point for channel {0}'
                                                     .format(SWATChannel), gv.isBatch)
                                else:
                                    curs.execute(DBUtils._ROUTINGINSERTSQL, 
                                                 (wid, wCat, ptId, ptCat, 100))
                                    if ptId not in routedPoints:
                                        curs.execute(DBUtils._ROUTINGINSERTSQL, 
                                                     (ptId, ptCat, pointId, ptCat, 100))
                                        routedPoints.append(ptId)
                                    routedWater.append(wid)
                        elif SWATChannel not in routedChannels:    
                            curs.execute(DBUtils._ROUTINGINSERTSQL, 
                                         (SWATChannel, chCat, pointId, ptCat, 100))
                            routedChannels.append(SWATChannel)
                        if pointId not in routedPoints:
                            if dsSWATChannel > 0:
                                widDown, roleDown = channelToWater.get(dsChannel, (-1, -1))
                                if widDown >= 0:
                                    wCat = resCat if roleDown == 1 else pondCat
                                    curs.execute(DBUtils._ROUTINGINSERTSQL, 
                                                 (pointId, ptCat, widDown, wCat, 100))
                                else:
                                    curs.execute(DBUtils._ROUTINGINSERTSQL, 
                                                 (pointId, ptCat, dsSWATChannel, chCat, 100))
                            else:
                                # watershed outlet: mark point as category X
                                curs.execute(DBUtils._ROUTINGINSERTSQL, 
                                             (pointId, ptCat, 0, xCat, 100))
                            routedPoints.append(pointId)
                    else:
                        # channel and downstream channel within a subbasin: 
                        # channel routes to downstream channel unless it is replaced by water
                        # and if it has a point source this is added
                        assert dsSWATChannel > 0, 'Channel {0} has no downstream channel'.format(channel)
                        widDown, roleDown = channelToWater.get(dsChannel, (-1, -1))
                        if wid >= 0:
                            if wid not in routedWater:
                                if widDown >= 0:
                                    # if wid == widDown wid is only a part water body
                                    # and we will eventually route the one downstream
                                    if wid != widDown:
                                        # route water to water point and water point to ridDown
                                        (waterId, _, _) = self.chLinkToWater.get(channel, (-1, None))
                                        if waterId < 0:
                                            (waterId, ptId, _) = self.foundReservoirs.get(channel, (-1, -1, None))
                                        else:
                                            # it is safe to use same id for reservoir and reservoir outlet point when
                                            # using DSNODEID from inlets/outlets file
                                            ptId = waterId
                                        if waterId < 0:
                                            QSWATUtils.error('Cannot find water point for channel {0}'
                                                             .format(SWATChannel), gv.isBatch)
                                        else:
                                            curs.execute(DBUtils._ROUTINGINSERTSQL, 
                                                         (wid, wCat, ptId, ptCat, 100))
                                            if ptId not in routedPoints:
                                                wCat = resCat if roleDown == 1 else pondCat
                                                curs.execute(DBUtils._ROUTINGINSERTSQL, 
                                                             (ptId, ptCat, widDown, wCat, 100))
                                                routedPoints.append(ptId)
                                            routedWater.append(wid)
                                else:
                                    # route water to water point and water point to downstream channel
                                    (waterId, _, _) = self.chLinkToWater.get(channel, (-1, None, -1))
                                    if waterId < 0:
                                        (waterId, ptId, _) = self.foundReservoirs.get(channel, (-1, -1, None))
                                    else:
                                        # it is safe to use same id for water and water outlet point when
                                        # using DSNODEID from inlets/outlets file
                                        ptId = waterId
                                    if waterId < 0:
                                        QSWATUtils.error('Cannot find water point for channel {0}'
                                                         .format(SWATChannel), gv.isBatch)
                                    else:
                                        curs.execute(DBUtils._ROUTINGINSERTSQL, 
                                                     (wid, wCat, ptId, ptCat, 100))
                                        if ptId not in routedPoints:
                                            curs.execute(DBUtils._ROUTINGINSERTSQL, 
                                                         (ptId, ptCat, dsSWATChannel, chCat, 100))
                                            routedPoints.append(ptId)
                                        routedWater.append(wid)
                        elif SWATChannel not in routedChannels:
                            if widDown >= 0:  
                                # insert an outlet point so that channel's contribution to reservoir 
                                # is included in outputs
                                self.pointId += 1
                                extraPoints.append((channel, self.pointId))
                                curs.execute(DBUtils._ROUTINGINSERTSQL,
                                            (SWATChannel, chCat, self.pointId, ptCat, 100))
                                wCat = resCat if roleDown == 1 else pondCat
                                curs.execute(DBUtils._ROUTINGINSERTSQL,
                                            (self.pointId, ptCat, widDown, wCat, 100))
                                routedPoints.append(self.pointId)
                            else:
                                curs.execute(DBUtils._ROUTINGINSERTSQL,
                                            (SWATChannel, chCat, dsSWATChannel, chCat, 100))
                            routedChannels.append(SWATChannel)    
                    # also route point source, if any, to channel  or water
                    ptsrc = channelToPtSrc.get(channel, None)
                    if ptsrc is not None:
                        ptsrcId = ptsrc[0]
                        if ptsrcId not in routedPoints:
                            if wid > 0:
                                curs.execute(DBUtils._ROUTINGINSERTSQL, 
                                             (ptsrcId, ptCat, wid, wCat, 100))
                            else:
                                curs.execute(DBUtils._ROUTINGINSERTSQL, 
                                             (ptsrcId, ptCat, SWATChannel, chCat, 100))
                            routedPoints.append(ptsrcId)
                # route lakes without outlet channels to main outlet points
                for lakeId, lakeData in self.lakesData.items():
                    if lakeData.outChLink == -1:
                        (subbasin, lakeOutletId, _, _) = lakeData.outPoint
                        (outletId, _, _) = self.outlets[subbasin]
                        wCat = resCat if lakeData.waterRole == 1 else pondCat
                        # route the lake to its lake outlet, the lake outlet to the main outlet, and mark main outlet as category X 
                        curs.execute(DBUtils._ROUTINGINSERTSQL, (lakeId, wCat, lakeOutletId, ptCat, 100))
                        if lakeOutletId not in routedPoints:
                            curs.execute(DBUtils._ROUTINGINSERTSQL, (lakeOutletId, ptCat, outletId, ptCat, 100))
                            routedPoints.append(lakeOutletId)
                        if outletId not in routedPoints:
                            curs.execute(DBUtils._ROUTINGINSERTSQL, (outletId, ptCat, 0, xCat, 100))
                            routedPoints.append(outletId)
                # route subbasin to outlet points
                # or to lake if outlet in lake
                for subbasin, (pointId, _, chLink) in self.outlets.items():
                    SWATBasin = self.subbasinToSWATBasin.get(subbasin, 0)
                    if SWATBasin == 0:
                        continue
                    if gv.useGridModel:
                        if chLink in self.chLinkInsideLake or chLink in self.chLinkFromLake:
                            continue
                    lakeId = self.outletsInLake.get(subbasin, None)
                    if lakeId is None:
                        curs.execute(DBUtils._ROUTINGINSERTSQL, 
                                     (SWATBasin, subbasinCat, pointId, ptCat, 100))
                    else:
                        lakeData = self.lakesData[lakeId]
                        wCat = resCat if lakeData.waterRole == 1 else pondCat
                        curs.execute(DBUtils._ROUTINGINSERTSQL,
                                     (SWATBasin, subbasinCat, lakeId, wCat, 100))
            return True               
        except Exception:
            QSWATUtils.loginfo('Routing channels, outlets and subbasins failed: {0}'.format(traceback.format_exc()))
            return False
    
    @staticmethod
    def removeFields(provider, keepFieldNames, fileName, isBatch):
        """Remove fields other than keepFieldNames from shapefile fileName with provider."""
        toDelete = []
        fields = provider.fields()
        for idx in range(fields.count()):
            name = fields.field(idx).name()
            if not name in keepFieldNames:
                toDelete.append(idx)
        if len(toDelete) > 0:
            OK = provider.deleteAttributes(toDelete)
            if not OK:
                QSWATUtils.error('Cannot remove fields from shapefile {0}'.format(fileName), isBatch)
    
    def setPenWidth(self, data, provider):
        """Scale wid2 data to 1 .. 4 and write to layer."""
        minW = float('inf')
        maxW = 0
        for val in data.values():
            minW = min(minW, val)
            maxW = max(maxW, val)
        if maxW > minW: # guard against division by zero
            rng = maxW - minW
            fun = lambda x: (x - minW) * 3 / rng + 1.0
        else:
            fun = lambda _: 1.0
        chIdx = provider.fieldNameIndex(QSWATTopology._CHANNEL)
        if chIdx < 0:
            QSWATUtils.error('Cannot find {0} field in channels results template'.format(QSWATTopology._CHANNEL))
            return
        penIdx = provider.fieldNameIndex(QSWATTopology._PENWIDTH)
        if penIdx < 0:
            QSWATUtils.error('Cannot find {0} field in channels results template'.format(QSWATTopology._PENWIDTH))
            return
        request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([chIdx, penIdx])
        mmap = dict()
        for f in provider.getFeatures(request):
            ch = f[chIdx]
            width = data.get(ch, minW)
            mmap[f.id()] = {penIdx: fun(width)}
        OK = provider.changeAttributeValues(mmap)
        if not OK:
            QSWATUtils.error('Cannot edit channels results template', self.isBatch)             
            
    def makeOutletThresholds(self, gv, root):
        """
        Make file like D8 contributing area but with heightened values at subbasin outlets.  
        
        Return -1 if cannot make the file.
        """
        assert os.path.exists(gv.demFile)
        demBase = os.path.splitext(gv.demFile)[0]
        if not QSWATUtils.isUpToDate(gv.demFile, gv.ad8File):
            # Probably using existing watershed but switched tabs in delineation form
            # At any rate, cannot calculate flow paths
            QSWATUtils.loginfo('ad8 file not found or out of date')
            return -1
        assert len(self.outlets) > 0
        gv.hd8File = demBase + 'hd8.tif'
        QSWATUtils.removeLayerAndFiles(gv.hd8File, root)
        assert not os.path.exists(gv.hd8File)
        ad8Layer = QgsRasterLayer(gv.ad8File, 'D8 contributing area')
        # calculate maximum contributing area at an outlet point
        maxContrib = 0
        for (_, pt, _) in self.outlets.values():
            contrib = QSWATTopology.valueAtPoint(pt, ad8Layer)
            # assume ad8nodata is negative
            if not (contrib is None or contrib < 0):
                maxContrib = max(maxContrib, contrib)
        threshold = int(2 * maxContrib)
        ad8Layer = None
        # copy ad8 to hd8 and then set outlet point values to threshold
        ad8Ds = gdal.Open(gv.ad8File, gdal.GA_ReadOnly)
        driver = gdal.GetDriverByName('GTiff')
        hd8Ds = driver.CreateCopy(gv.hd8File, ad8Ds, 0)
        if not hd8Ds:
            QSWATUtils.error('Failed to create hd8 file {0}'.format(gv.hd8File), self.isBatch)
            return -1, None
        ad8Ds = None
        QSWATUtils.copyPrj(gv.ad8File, gv.hd8File)
        band = hd8Ds.GetRasterBand(1)
        transform = hd8Ds.GetGeoTransform()
        arr = array([[threshold]])
        for (_, pt, _) in self.outlets.values():
            x, y = QSWATTopology.projToCell(pt.x(), pt.y(), transform)
            band.WriteArray(arr, x, y)
        hd8Ds = None
        return threshold
           
    def runCalc1(self, file1, func, outFile, gv, isInt=False, fun1=None):
        """Use func as a function to calulate outFile from file1.
        
        Valid input data values have fun1 applied if it is not None"""
        if os.path.exists(outFile):
            QSWATUtils.removeLayerAndFiles(outFile, gv.iface.legendInterface())
        r1 = Raster(file1, gv)
        rout = Raster(outFile, gv, canWrite=True, isInt=isInt)
        completed = False
        while not completed:
            try:
                # safer to mark complete immediately to avoid danger of endless loop
                # only way to loop is then the memory error exception being raised 
                completed = True
                r1.open(self.chunkCount)
                noData = -99999 if isInt else r1.noData
                rout.open(self.chunkCount, numRows=r1.numRows, numCols=r1.numCols, 
                                transform=r1.ds.GetGeoTransform(), projection=r1.ds.GetProjection(), noData=noData)
                for row in range(r1.numRows):
                    for col in range(r1.numCols):
                        v1 = r1.read(row, col)
                        if fun1 is not None and v1 != r1.noData:
                            v1 = fun1(v1)
                        vout = func(v1, r1.noData, noData)
                        rout.write(row, col, vout)
                r1.close()
                rout.close()
            except MemoryError:
                QSWATUtils.loginfo('runCalc1 out of memory with chunk count {0}'.format(self.chunkCount))
                try:
                    r1.close()
                    rout.close()
                except Exception:
                    pass  
                self.chunkCount += 1
                completed = False
        if os.path.exists(outFile):
            QSWATUtils.copyPrj(file1, outFile)
            return True
        else:
            # QSWATUtils.error(u'Calculator  failed', self._gv.isBatch)
            return False
        
    def runCalc2(self, file1, file2, func, outFile, gv, isInt=False, fun1=None, fun2=None):
        """Use func as a function to calulate outFile from file1 and file2.
        
        Assumes file1 and file2 have same origina and pixel size.
        If file1/2 values are not nodata and fun1/2 are not None, they are applied before func is applied."""
        if os.path.exists(outFile):
            QSWATUtils.removeLayerAndFiles(outFile, gv.iface.legendInterface())
        r1 = Raster(file1, gv)
        r2 = Raster(file2, gv)
        rout = Raster(outFile, gv, canWrite=True, isInt=isInt)
        completed = False
        while not completed:
            try:
                # safer to mark complete immediately to avoid danger of endless loop
                # only way to loop is then the memory error exception being raised 
                completed = True
                r1.open(self.chunkCount)
                r2.open(self.chunkCount)
                noData = -1 if isInt else r1.noData
                rout.open(self.chunkCount, numRows=r1.numRows, numCols=r1.numCols, 
                            transform=r1.ds.GetGeoTransform(), projection=r1.ds.GetProjection(), noData=noData)
                for row in range(r1.numRows):
                    for col in range(r1.numCols):
                        v1 = r1.read(row, col)
                        if fun1 is not None and v1 != r1.noData:
                            v1 = fun1(v1)
                        v2 = r2.read(row, col)
                        if fun2 is not None and v2 != r2.noData:
                            v2 = fun2(v2)
                        vout = func(v1, r1.noData, v2, r2.noData, noData)
                        rout.write(row, col, vout)
                r1.close()
                r2.close()
                rout.close()
            except MemoryError:
                QSWATUtils.loginfo('runCalc2 out of memory with chunk count {0}'.format(self.chunkCount))
                try:
                    r1.close()
                    r2.close()
                    rout.close()
                except:
                    pass
                self.chunkCount += 1
                completed = False
        if os.path.exists(outFile):
            QSWATUtils.copyPrj(file1, outFile)
            return True
        else:
            # QSWATUtils.error(u'Calculator  failed', self._gv.isBatch)
            return False
        
        
    def runCalc2Trans(self, file1, file2, func, outFile, baseFile, gv, isInt=False, fun1=None, fun2=None):
        """Use func as a function to calulate outFile from file1 and file2, using rows, columns and extent of baseFile.

        If file1/2 values are not nodata and fun1/2 are not None, they are applied before func is applied."""
        if os.path.exists(outFile):
            QSWATUtils.removeLayerAndFiles(outFile, gv.iface.legendInterface())
        r1 = Raster(file1, gv)
        r2 = Raster(file2, gv)
        rout = Raster(outFile, gv, canWrite=True, isInt=isInt)
        ds = gdal.Open(baseFile, gdal.GA_ReadOnly)
        transform = ds.GetGeoTransform()
        numRows = ds.RasterYSize
        numCols = ds.RasterXSize
        projection=ds.GetProjection()
        ds = None
        completed = False
        while not completed:
            try:
                # safer to mark complete immediately to avoid danger of endless loop
                # only way to loop is then the memory error exception being raised 
                completed = True
                r1.open(self.chunkCount)
                r2.open(self.chunkCount)
                transform1 = r1.ds.GetGeoTransform()
                transform2 = r2.ds.GetGeoTransform()
                rowFun1, colFun1 = QSWATTopology.translateCoords(transform, transform1, numRows, numCols)
                rowFun2, colFun2 = QSWATTopology.translateCoords(transform, transform2, numRows, numCols)
                noData = -1 if isInt else r1.noData
                rout.open(self.chunkCount, numRows=numRows, numCols=numCols, 
                            transform=transform, projection=projection, noData=noData)
                for row in range(numRows):
                    y = QSWATTopology.rowToY(row, transform)
                    row1 = rowFun1(row, y)
                    row2 = rowFun2(row, y)
                    for col in range(numCols):
                        x = QSWATTopology.colToX(col, transform)
                        col1 = colFun1(col, x)
                        col2 = colFun2(col, x)
                        v1 = r1.read(row1, col1)
                        if fun1 is not None and v1 != r1.noData:
                            v1 =fun1(v1)
                        v2 = r2.read(row2, col2)
                        if fun2 is not None and v2 != r2.noData:
                            v2 = fun2(v2)
                        vout = func(v1, r1.noData, v2, r2.noData, noData)
                        rout.write(row, col, vout)
                r1.close()
                r2.close()
                rout.close()
            except MemoryError:
                QSWATUtils.loginfo('runCalc2Trans out of memory with chunk count {0}'.format(self.chunkCount))
                try:
                    r1.close()
                    r2.close()
                    rout.close()
                except:
                    pass
                self.chunkCount += 1
                completed = False
        if os.path.exists(outFile):
            QSWATUtils.copyPrj(baseFile, outFile)
            return True
        else:
            # QSWATUtils.error(u'Calculator  failed', self._gv.isBatch)
            return False
      
    @staticmethod      
    def burnStream(streamFile, demFile, burnFile, depth, verticalFactor, isBatch):
        """Create as burnFile a copy of demFile with points on lines streamFile reduced in height by depth metres."""
        # use vertical factor to convert from metres to vertical units of DEM
        demReduction = float(depth) / verticalFactor 
        assert not os.path.exists(burnFile)
        demDs = gdal.Open(demFile, gdal.GA_ReadOnly)
        driver = gdal.GetDriverByName('GTiff')
        burnDs = driver.CreateCopy(burnFile, demDs, 0)
        if burnDs is None:
            QSWATUtils.error('Failed to create burned-in DEM {0}'.format(burnFile), isBatch)
            return
        demDs = None
        QSWATUtils.copyPrj(demFile, burnFile)
        band = burnDs.GetRasterBand(1)
        nodata = band.GetNoDataValue()
        burnTransform = burnDs.GetGeoTransform()
        streamLayer = QgsVectorLayer(streamFile, 'Burn in streams', 'ogr')
        start = time.process_time()
        countHits = 0
        countPoints = 0
        countChanges = 0
        changed = dict()
        for reach in streamLayer.getFeatures():
            geometry = reach.geometry()
            if geometry.isMultipart():
                lines = geometry.asMultiPolyline()
            else:
                lines = [geometry.asPolyline()]
            for line in lines:
                for i in range(len(line) - 1):
                    countPoints += 1
                    p0 = line[i]
                    px0 = p0.x()
                    py0 = p0.y()
                    x0, y0 = QSWATTopology.projToCell(px0, py0, burnTransform)
                    p1 = line[i+1]
                    px1 = p1.x()
                    py1 = p1.y()
                    x1, y1 = QSWATTopology.projToCell(px1, py1, burnTransform)
                    steep = abs(y1 - y0) > abs(x1 - x0)
                    if steep:
                        x0, y0 = y0, x0
                        x1, y1 = y1, x1
                    if x0 > x1:
                        x0, x1 = x1, x0
                        y0, y1 = y1, y0
                    deltax = x1 - x0
                    deltay = abs(y1 - y0)
                    err = 0
                    deltaerr = deltay
                    y = y0
                    ystep = 1 if y0 < y1 else -1
                    arr = array([[0.0]])
                    for x in range(x0, x1+1):
                        if steep:
                            if QSWATTopology.addPointToChanged(changed, y, x):
                                arr = band.ReadAsArray(y, x, 1, 1)
                                # arr may be none if stream map extends outside DEM extent
                                if arr and arr[0,0] != nodata:
                                    arr[0,0] = arr[0,0] - demReduction
                                    band.WriteArray(arr, y, x)
                                    countChanges += 1
                            else:
                                countHits += 1
                        else:
                            if QSWATTopology.addPointToChanged(changed, x, y):
                                arr = band.ReadAsArray(x, y, 1, 1)
                                # arr may be none if stream map extends outside DEM extent
                                if arr and arr[0,0] != nodata:
                                    arr[0,0] = arr[0,0] - demReduction
                                    band.WriteArray(arr, x, y)
                                    countChanges += 1
                            else:
                                countHits += 1
                        err += deltaerr
                        if 2 * err < deltax:
                            continue
                        y += ystep
                        err -= deltax
        finish = time.process_time()
        QSWATUtils.loginfo('Created burned-in DEM {0} in {1!s} milliseconds; {2!s} points; {3!s} hits; {4!s} changes'.format(burnFile, int((finish - start)*1000), countPoints, countHits, countChanges))
        
    @staticmethod
    def addPointToChanged(changed, col, row):
        """Changed points held in dictionary column -> row-sortedlist, since it is like a sparse matrix.
        Add a point unless ready there.  Return true if added.
        """
        rows = changed.get(col, [])
        inserted = ListFuns.insertIntoSortedList(row, rows, True)
        if inserted:
            changed[col] = rows
            return True
        else:
            return False
        
    @staticmethod    
    def valueAtPoint(point, layer):
        """
        Get the band 1 value at point in a grid layer.
        
        """
        val, ok =  layer.dataProvider().sample(point, 1)
        if not ok:
            return layer.dataProvider().sourceNoDataValue(1)
        else:
            return val
         
    def isUpstreamSubbasin(self, subbasin):
        """Return true if a subbasin is upstream from an inlet."""
        return subbasin in self.upstreamFromInlets
    
    def pointToLatLong(self, point):
        """Convert a QgsPointXY to latlong coordinates and return it."""
        geom = QgsGeometry.fromPointXY(point)
        geom.transform(self.transformToLatLong)
        return geom.asPoint()
            
    def getIndex(self, layer, name, ignoreMissing=False):
        """Get the index of a shapefile layer attribute name, 
        reporting error if not found, unless ignoreMissing is true.
        """
        # field names are truncated to 10 characters when created, so only search for up to 10 characters
        # also allow any case, since using lookupField rather than indexOf
        index = layer.fields().lookupField(name[:10])
        if not ignoreMissing and index < 0:
            QSWATUtils.error('Cannot find field {0} in {1}'.format(name, QSWATUtils.layerFileInfo(layer).filePath()), self.isBatch)
        return index
            
    def getProviderIndex(self, provider, name, ignoreMissing=False):
        """Get the index of a shapefile provider attribute name, 
        reporting error if not found, unless ignoreMissing is true.
        """
        # field names are truncated to 10 characters when created, so only search for up to 10 characters
        index = provider.fieldNameIndex(name[:10])
        if not ignoreMissing and index < 0:
            QSWATUtils.error('Cannot find field {0} in provider'.format(name), self.isBatch)
        return index
    
    def makePointInLine(self, reach, percent):
        """Return a point percent along line from outlet end to next point."""
        if self.outletAtStart:
            line = QSWATTopology.reachFirstLine(reach.geometry(), self.xThreshold, self.yThreshold)
            pt1 = line[0]
            pt2 = line[1]
        else:
            line = QSWATTopology.reachLastLine(reach.geometry(), self.xThreshold, self.yThreshold)
            length = len(line)
            pt1 = line[length-1]
            pt2 = line[length-2]
        x = (pt1.x() * (100 - percent) + pt2.x() * percent) / 100.0
        y = (pt1.y() * (100 - percent) + pt2.y() * percent) / 100.0
        return QgsPointXY(x, y)
    
    def hasOutletAtStart(self, streamLayer, ad8Layer):
        """Returns true iff streamLayer lines have their outlet points at their start points.
         
        If ad8Layer is not None, we are not in an existing watershed, and can rely on accumulations.
        Accumulation will be higher at the outlet end.
        Finds shapes with a downstream connections, and 
        determines the orientation by seeing how such a shape is connected to the downstream shape.
        If they don't seem to be connected (as my happen after merging subbasins) 
        tries other shapes with downstream connections, up to 10.
        A line is connected to another if their ends are less than dx and dy apart horizontally and vertically.
        Assumes the orientation found for this shape can be used generally for the layer.
        """
        streamIndex = self.getIndex(streamLayer, QSWATTopology._LINKNO, ignoreMissing=False)
        if streamIndex < 0:
            QSWATUtils.error('No LINKNO field in stream layer', self.isBatch)
            return True # default as true for TauDEM
        dsStreamIndex = self.getIndex(streamLayer, QSWATTopology._DSLINKNO, ignoreMissing=False)
        if dsStreamIndex < 0:
            QSWATUtils.error('No DSLINKNO field in stream layer', self.isBatch)
            return True # default as true for TauDEM
        if ad8Layer is not None:  # only set to non-None if not an existing watershed
            # use accumulation difference at ends of reach (or line in reach) to decide
            for reach in streamLayer.getFeatures():
                geometry = reach.geometry()
                if geometry.isMultipart():
                    lines = geometry.asMultiPolyline()
                else:
                    lines = [geometry.asPolyline()]
                for line in lines:
                    if len(line) > 1:  # make sure we haven't picked on an empty line
                        p1 = line[0]
                        p2 = line[-1]
                        acc1 = QSWATTopology.valueAtPoint(p1, ad8Layer)
                        acc2 = QSWATTopology.valueAtPoint(p2, ad8Layer)
                        if acc1 != acc2: # degenerate single point line
                            return acc1 > acc2
        # find candidates: links with a down connection
        candidates = [] # reach, downReach pairs
        for reach in streamLayer.getFeatures():
            downLink = reach[dsStreamIndex]
            if downLink >= 0:
                # find the down reach
                downReach = QSWATUtils.getFeatureByValue(streamLayer, streamIndex, downLink)
                if downReach is not None:
                    candidates.append((reach, downReach))
                    if len(candidates) < 10:
                        continue
                    else:
                        break
                else:
                    QSWATUtils.error('Cannot find link {0!s} in {1}'.format(downLink, QSWATUtils.layerFileInfo(streamLayer).filePath()), self.isBatch)
                    return True
        if candidates == []:
            QSWATUtils.error('Cannot find link with a downstream link in {0}.  Do you only have one stream?'.format(QSWATUtils.layerFileInfo(streamLayer).filePath()), self.isBatch)
            return True
        for (upReach, downReach) in candidates:
            downGeom = downReach.geometry()
            downStart = QSWATTopology.reachFirstLine(downGeom, self.xThreshold, self.yThreshold)
            if downStart is None:
                continue
            downFinish = QSWATTopology.reachLastLine(downGeom, self.xThreshold, self.yThreshold)
            if downFinish is None:
                continue
            upGeom = upReach.geometry()
            upStart = QSWATTopology.reachFirstLine(upGeom, self.xThreshold, self.yThreshold)
            if upStart is None:
                continue
            upFinish = QSWATTopology.reachLastLine(upGeom, self.xThreshold, self.yThreshold)
            if upFinish is None:
                continue
            if QSWATTopology.pointOnLine(upStart[0], downFinish, self.xThreshold, self.yThreshold):
                return True
            if QSWATTopology.pointOnLine(upFinish[-1], downStart, self.xThreshold, self.yThreshold):
                return False
        QSWATUtils.error('Cannot find physically connected reaches in streams shapefile {0}.  Try increasing nearness threshold'.format(QSWATUtils.layerFileInfo(streamLayer).filePath()), self.isBatch)  
        return True
    
    def saveOutletsAndSources(self, channelLayer, outletLayer, useGridModel):
        """Write outlets, downSubbasins, and (unless useGridModel)
         inlets, upstreamFromInlets, and outletChannels  tables."""
        # in case called twice
        self.pointId = 0
        self.waterBodyId = 0
        self.outlets.clear()
        self.inlets.clear()
        self.chPointSources.clear()
        self.upstreamFromInlets.clear()
        self.downSubbasins.clear()
        self.chBasinToSubbasin.clear()
        chLinkToSubbasin = dict()
        downChannels = dict()
        chInlets = dict()
        chOutlets = dict()
        chLinkIndex = self.getIndex(channelLayer, QSWATTopology._LINKNO)
        dsChLinkIndex = self.getIndex(channelLayer, QSWATTopology._DSLINKNO)
        wsnoIndex = self.getIndex(channelLayer, QSWATTopology._WSNO, ignoreMissing=not useGridModel)
        if chLinkIndex < 0 or dsChLinkIndex < 0:
            return False
        # ignoreMissing for subbasinIndex necessary when useGridModel, since channelLayer is then a streams layer
        subbasinIndex = self.getIndex(channelLayer, QSWATTopology._BASINNO, ignoreMissing=useGridModel)
        if useGridModel:
            if wsnoIndex < 0:
                return False
        else:
            if subbasinIndex < 0:
                return False   
        dsNodeIndex = self.getIndex(channelLayer, QSWATTopology._DSNODEID, ignoreMissing=True)
        if outletLayer is not None:
            idIndex = self.getIndex(outletLayer, QSWATTopology._ID, ignoreMissing=False)
            inletIndex = self.getIndex(outletLayer, QSWATTopology._INLET, ignoreMissing=False)
            srcIndex = self.getIndex(outletLayer, QSWATTopology._PTSOURCE, ignoreMissing=False)
            resIndex = self.getIndex(outletLayer, QSWATTopology._RES, ignoreMissing=False)
            # set pointId to max id value in outletLayer
            # and waterBodyId to max reservoir or pond id
            request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry)
            for point in outletLayer.getFeatures(request):
                self.pointId = max(self.pointId, point[idIndex])
                if point[inletIndex] == 0 and point[resIndex] > 0:
                    self.waterBodyId = max(self.waterBodyId, point[idIndex])
        else:
            dsNodeIndex = -1
        for reach in channelLayer.getFeatures():
            chLink = reach[chLinkIndex]
            dsChLink = reach[dsChLinkIndex]
            chBasin = reach[wsnoIndex]
            geom = reach.geometry()
            # for grids, channel basins and subbasins are the same
            subbasin = chBasin if useGridModel else reach[subbasinIndex]
            chLinkToSubbasin[chLink] = subbasin
            if not useGridModel:
                self.chBasinToSubbasin[chBasin] = subbasin
            downChannels[chLink] = dsChLink
            dsNode = reach[dsNodeIndex] if dsNodeIndex >= 0 else -1
            if dsNode >= 0 and idIndex >= 0 and inletIndex >= 0 and srcIndex >= 0 and resIndex >= 0:
                outletPoint = None
                inletPoint = None
                for f in outletLayer.getFeatures():
                    if f[idIndex] == dsNode:
                        if f[inletIndex] == 0:
                            if f[resIndex] == 0:
                                outletPoint = f
                                break
                        elif f[srcIndex] == 0:
                            inletPoint = f
                            break
                if outletPoint is not None:
                    pt = outletPoint.geometry().asPoint()
                    chOutlets[chLink] = (self.nonzeroPointId(dsNode), pt)
                elif inletPoint is not None:
                    pt = inletPoint.geometry().asPoint()
                    chInlets[chLink] = (self.nonzeroPointId(dsNode), pt)
            first = QSWATTopology.reachFirstLine(geom, self.xThreshold, self.yThreshold)                
            if first is None or len(first) < 2:
                QSWATUtils.error('It looks like your channels shapefile does not obey the single direction rule, that all channels are either upstream or downstream.', self.isBatch)
                return False
            last = QSWATTopology.reachLastLine(geom, self.xThreshold, self.yThreshold)               
            if last is None or len(last) < 2:
                QSWATUtils.error('It looks like your channels shapefile does not obey the single direction rule, that all channels are either upstream or downstream.', self.isBatch)
                return False
            outId, pt = chOutlets.get(chLink, (-1, None))
            if pt is None:
                self.pointId += 1
                outId = self.pointId
            self.pointId += 1
            srcId = self.pointId
            if self.outletAtStart:
                if not useGridModel and pt is not None and not QSWATTopology.coincidentPoints(first[0], pt, self.xThreshold, self.yThreshold):
                    QSWATUtils.error('Outlet point {0} at ({1}, {2}) not coincident with start of channel link {3}'
                                     .format(outId, pt.x(), pt.y(), chLink), self.isBatch)
                chOutlets[chLink] = (outId, first[0])
                self.chPointSources[chLink] = (srcId, last[-1])
            else:
                if not useGridModel and pt is not None and not QSWATTopology.coincidentPoints(last[-1], pt, self.xThreshold, self.yThreshold):
                    QSWATUtils.error('Outlet point {0} at ({1}, {2}) not coincident with end of channel link {3}'
                                     .format(outId, pt.x(), pt.y(), chLink), self.isBatch)
                chOutlets[chLink] = (outId, last[-1])
                self.chPointSources[chLink] = (srcId, first[0])
        # now find the channels which are on subbasin boundaries,
        # i.e. their downstream channels are in different basins
        hasInlet = False
        for chLink, dsChLink in downChannels.items():
            subbasin = chLinkToSubbasin[chLink]
            if subbasin == QSWATTopology._NOBASIN: # from a zero-length channel
                continue
            dsSubbasin = chLinkToSubbasin[dsChLink] if dsChLink >= 0 else -1
            while dsSubbasin == QSWATTopology._NOBASIN:
                # skip past zero-length channels
                dsChLink = downChannels.get(dsChLink, -1)
                dsSubbasin = chLinkToSubbasin.get(dsChLink, -1)
            if subbasin != dsSubbasin:
                self.downSubbasins[subbasin] = dsSubbasin
                # collect the basin's outlet location:
                outletId, outletPt = chOutlets[chLink]
                self.outlets[subbasin] = (outletId, outletPt, chLink)
                if not useGridModel:
#                     self.extraResPoints[subbasin] = chResPoints[chLink]
#                     self.extraPtSrcPoints[subbasin] = chSources[chLink]
                    inletId, inletPt = chInlets.get(chLink, (-1, None))
                    if inletPt is not None and dsSubbasin >= 0:
                        # inlets are associated with downstream basin
                        self.inlets[dsSubbasin] = (inletId, inletPt)
                        hasInlet = True
        # collect subbasins upstream from inlets
        # this looks inefficient, repeatedly going through all basins, but probably few projects have inlets:
        if not useGridModel and hasInlet:
            for subbasin in self.inlets.keys():
                self.addUpstreamSubbasins(subbasin)
        return True
    
    def nonzeroPointId(self, dsNode):
        """Return dsNode, or next pointId if dsNode is zero.  Used to prevent a zero point id."""
        if dsNode == 0:
            self.pointId += 1
            return self.pointId
        return dsNode
    
    def addUpstreamSubbasins(self, start):
        """Add basins upstream from start to upstreamFromInlets."""
        for subbasin, downSubbasin in self.downSubbasins.items():
            if downSubbasin == start:
                self.upstreamFromInlets.add(subbasin)
                self.addUpstreamSubbasins(subbasin)
    
    def surroundingLake(self, SWATChannel, useGridModel):
        """Return id of lake containing channel, if any, else -1."""
        chLink = self.SWATChannelToChannel[SWATChannel]
        lake1 = self.chLinkInsideLake.get(chLink, -1)
        if useGridModel and lake1 < 0:
            return self.chLinkFromLake.get(chLink, -1)
        else:
            return lake1
        
    @staticmethod
    def maskFun(val, valNoData, mask, maskNoData, resNoData):
        """Result is val unless mask is nodata."""
        if val == valNoData or mask == maskNoData:
            return resNoData
        else:
            return val      
    
    @staticmethod
    def reachFirstLine(geometry, xThreshold, yThreshold):
        """Returns the line of a single polyline, 
        or a line in a multipolyline whose first point is not adjacent to a point 
        of another line in the multipolyline.
        """
        if not geometry.isMultipart():
            return geometry.asPolyline()
        mpl = geometry.asMultiPolyline()
        numLines = len(mpl)
        for i in range(numLines):
            linei = mpl[i]
            connected = False
            if linei is None or len(linei) == 0:
                continue
            else:
                start = linei[0]
                for j in range(numLines):
                    if i != j:
                        linej = mpl[j]
                        if QSWATTopology.pointOnLine(start, linej, xThreshold, yThreshold):
                            connected = True
                            break
            if not connected:
                return linei
        # should not get here
        return None
    
    @staticmethod
    def reachLastLine(geometry, xThreshold, yThreshold):
        """Returns the line of a single polyline, 
        or a line in a multipolyline whose last point is not adjacent to a point 
        of another line in the multipolyline.
        """
        if not geometry.isMultipart():
            return geometry.asPolyline()
        mpl = geometry.asMultiPolyline()
        numLines = len(mpl)
        for i in range(numLines):
            linei = mpl[i]
            connected = False
            if linei is None or len(linei) == 0:
                continue
            else:
                finish = linei[-1]
                for j in range(numLines):
                    if i != j:
                        linej = mpl[j]
                        if QSWATTopology.pointOnLine(finish, linej, xThreshold, yThreshold):
                            connected = True
                            break
            if not connected:
                return linei
        # should not get here
        return None
    
    @staticmethod
    def pointOnLine(point, line, xThreshold, yThreshold):
        """Return true if point is coincident with a point on the line. 
        
        Note this only checks if the point is close to a vertex."""
        if line is None or len(line) == 0:
            return False
        for pt in line:
            if QSWATTopology.coincidentPoints(point, pt, xThreshold, yThreshold):
                return True
        return False
    
    @staticmethod
    def coincidentPoints(pt1, pt2, xThreshold, yThreshold):
        """Return true if points are within xThreshold and yThreshold
        horizontally and vertically."""
        return abs(pt1.x() - pt2.x()) < xThreshold and \
            abs(pt1.y() - pt2.y()) < yThreshold
            
    @staticmethod
    def colToX(col, transform):
        """Convert column number to X-coordinate."""
        return (col + 0.5) * transform[1] + transform[0]
    
    @staticmethod
    def rowToY(row, transform):
        """Convert row number to Y-coordinate."""
        return (row + 0.5) * transform[5] + transform[3]
    
    #=========currently not used==================================================================
    # @staticmethod
    # def xToCol(x, transform):
    #     """Convert X-coordinate to column number."""
    #     return int((x - transform[0]) / transform[1])
    #===========================================================================
    
    #=========currently not used==================================================================
    # @staticmethod
    # def yToRow(y, transform):
    #     """Convert Y-coordinate to row number."""
    #     return int((y - transform[3]) / transform[5])
    #===========================================================================
        
    @staticmethod
    def cellToProj(col, row, transform):
        """Convert column and row numbers to (X,Y)-coordinates."""
        x = (col + 0.5) * transform[1] + transform[0]
        y = (row + 0.5) * transform[5] + transform[3]
        return (x,y)
        
    @staticmethod
    def projToCell(x, y, transform):
        """Convert (X,Y)-coordinates to column and row numbers."""
        col = int((x - transform[0]) / transform[1])
        row = int((y - transform[3]) / transform[5])
        return (col, row)
    
    #==========not currently used=================================================================
    # @staticmethod
    # def haveSameCoords(band1, transform1, transform2):
    #     """
    #     Return true if raster transform1 and transform2 are the same or sufficiently
    #     close for row/col coordinates of first to be used without reprojection
    #     as row/col coordinates of the second.
    #     
    #     Assumes second raster has sufficient extent.
    #     We could demand this, but in practice often read rasters well within their extents,
    #     because only looking at points within a watershed.
    #     """
    #     # may work, though may also fail - we are comparing float values
    #     if transform1 == transform2:
    #         return True
    #     # accept the origins as the same if they are within a tenth of the cell size
    #     # otherwise return false
    #     if (abs(transform1[0] - transform2[0]) > transform2[1] * 0.1 or \
    #         abs(transform1[3] - transform2[3]) > abs(transform2[5]) * 0.1):
    #         return False
    #     # then check if the vertical/horizontal difference in cell size times the number of rows/columns
    #     # in the first is less than half the depth/width of a cell in the second
    #     return abs(transform1[1] - transform2[1]) * band1.XSize < transform2[1] * 0.5 and \
    #             abs(transform1[5] - transform2[5]) * band1.YSize < abs(transform2[5]) * 0.5
    #===========================================================================
                
    @staticmethod
    def translateCoords(transform1, transform2, numRows1, numCols1):
        """
        Return a pair of functions:
        row, latitude -> row and column, longitude -> column
        for transforming positions in raster1 to row and column of raster2.
        
        The functions are:
        identities on the first argument if the rasters have (sufficiently) 
        the same origins and cell sizes;
        a simple shift on the first argument if the rasters have 
        the same cell sizes but different origins;
        otherwise a full transformation on the second argument.
        It is assumed that the first and second arguments are consistent, 
        ie they identify the same cell in raster1.
        """
        # may work, thuough we are comparing real values
        if transform1 == transform2:
            return (lambda row, _: row), (lambda col, _: col)
        xOrigin1, xSize1, _, yOrigin1, _, ySize1 = transform1
        xOrigin2, xSize2, _, yOrigin2, _, ySize2 = transform2
        # accept the origins as the same if they are within a tenth of the cell size
        sameXOrigin = abs(xOrigin1 - xOrigin2) < xSize2 * 0.1
        sameYOrigin = abs(yOrigin1 - yOrigin2) < abs(ySize2) * 0.1
        # accept cell sizes as equivalent if  vertical/horizontal difference 
        # in cell size times the number of rows/columns
        # in the first is less than half the depth/width of a cell in the second
        sameXSize = abs(xSize1 - xSize2) * numCols1 < xSize2 * 0.5
        sameYSize = abs(ySize1 - ySize2) * numRows1 < abs(ySize2) * 0.5
        if sameXSize:
            if sameXOrigin:
                xFun = (lambda col, _: col)
            else:
                # just needs origin shift
                # note that int truncates, i.e. rounds towards zero
                if xOrigin1 > xOrigin2:
                    colShift = int((xOrigin1 - xOrigin2) / xSize1 + 0.5)
                    xFun = lambda col, _: col + colShift
                else:
                    colShift = int((xOrigin2 - xOrigin1) / xSize1 + 0.5)
                    xFun = lambda col, _: col - colShift
        else:
            # full transformation
            xFun = lambda _, x: int((x - xOrigin2) / xSize2)
        if sameYSize:
            if sameYOrigin:
                yFun = (lambda row, _: row)
            else:
                # just needs origin shift
                # note that int truncates, i.e. rounds towards zero, and y size will be negative
                if yOrigin1 > yOrigin2:
                    rowShift = int((yOrigin2 - yOrigin1) / ySize1 + 0.5)
                    yFun = lambda row, _: row - rowShift
                else:
                    rowShift = int((yOrigin1 - yOrigin2) / ySize1 + 0.5)
                    yFun = lambda row, _: row + rowShift
        else:
            # full transformation
            yFun = lambda _, y: int((y - yOrigin2) / ySize2)
        # note row, column order of return (same as order of reading rasters)
        return yFun, xFun
    
    @staticmethod
    def sameTransform(transform1, transform2, numRows1, numCols1):
        """Return true if transforms are sufficiently close to be regarded as the same,
        i.e. row and column numbers for the first can be used without transformation to read the second.  
        Avoids relying on equality between real numbers."""
        # may work, thuough we are comparing real values
        if transform1 == transform2:
            return True
        xOrigin1, xSize1, _, yOrigin1, _, ySize1 = transform1
        xOrigin2, xSize2, _, yOrigin2, _, ySize2 = transform2
        # accept the origins as the same if they are within a tenth of the cell size
        sameXOrigin = abs(xOrigin1 - xOrigin2) < xSize2 * 0.1
        if sameXOrigin:
            sameYOrigin = abs(yOrigin1 - yOrigin2) < abs(ySize2) * 0.1
            if sameYOrigin:
                # accept cell sizes as equivalent if  vertical/horizontal difference 
                # in cell size times the number of rows/columns
                # in the first is less than half the depth/width of a cell in the second
                sameXSize = abs(xSize1 - xSize2) * numCols1 < xSize2 * 0.5
                if sameXSize:
                    sameYSize = abs(ySize1 - ySize2) * numRows1 < abs(ySize2) * 0.5
                    return sameYSize
        return False
        
    def splitReachByLake(self, lakeGeom, reachGeom, reachData):
        """lakeGeom is a polygon representing a lake.  reach is known to intersect wil the lake..
        Returns a pair of inflowing and outflowing reaches, either or both of which may be None."""
        sourcePt = QgsPointXY(reachData.upperX, reachData.upperY)
        sourceToLake = QSWATTopology.toIntersection(reachGeom, lakeGeom, sourcePt, not self.outletAtStart, self.xThreshold, self.yThreshold)
        outletPt = QgsPointXY(reachData.lowerX, reachData.lowerY)
        outletToLake = QSWATTopology.toIntersection(reachGeom, lakeGeom, outletPt, self.outletAtStart, self.xThreshold, self.yThreshold)
        return sourceToLake, outletToLake
        
    @staticmethod
    def toIntersection(reachGeom, lakeGeom, start, isUp, xThreshold, yThreshold):
        """Return geometry for sequence of points from start to one before first one that intersects with lakeGeom, 
        or None if this is empty or a singleton, or if start is within the lake.
        
        If isUp the search is from index 0 if the of the reach, else it is from the last index."""
        if lakeGeom.contains(start):
            return None
        if reachGeom.isMultipart():
            mpl = reachGeom.asMultiPolyline()
        else:
            mpl = [reachGeom.asPolyline()]
        result = []
        done = set()
        while True:
            progress = False
            for i in range(len(mpl)):
                if i not in done:
                    line = mpl[i]
                    if len(line) <= 1:
                        continue
                    if isUp:
                        if QSWATTopology.coincidentPoints(start, line[0], xThreshold, yThreshold):
                            for pt in line:
                                if lakeGeom.contains(pt):
                                    length = len(result)
                                    if length < 1:
                                        return None
                                    elif length == 1:
                                        # create zero-length line at result[0]
                                        return QgsGeometry.fromPolylineXY([result[0], result[0]])
                                    return QgsGeometry.fromPolylineXY(result)
                                result.append(pt)
                            start = line[-1]
                            done.add(i)
                            progress = True
                    else:
                        if QSWATTopology.coincidentPoints(start, line[-1], xThreshold, yThreshold):
                            for pt in reversed(line):
                                if lakeGeom.contains(pt):
                                    length = len(result)
                                    if length < 1:
                                        return None
                                    elif length == 1:
                                        # create zero-length line at result[0]
                                        return QgsGeometry.fromPolylineXY([result[0], result[0]])
                                    return QgsGeometry.fromPolylineXY(result)
                                result.insert(0, pt)
                            start = line[0]
                            done.add(i)
                            progress = True
            if not progress:
                raise Exception('Looping trying to calculate reach')
                                
#     @staticmethod
#     def splitReach(resGeom, reachGeom, source, outlet, outletAtStart, xThreshold, yThreshold):
#         """Split reachGeom into two parts, one from source to reservoir and one from reservoir to outlet.
#         
#         Assumes the reach has been split into at least two disjoint parts, one flowing from source, the other flowing to outlet.
#         Algorithm checks each line in reach geometry, moving up from source or down from outlet until reservoir is reached
#         in both cases."""
#         sourcePart = []
#         outletPart = []
#         mpl = reachGeom.asMultiPolyline()
#         done = set()
#         outletToLakeDone = False
#         sourceToLakeDone = False
#         while True:
#             reduced = False
#             for i in xrange(len(mpl)):
#                 if i not in done:
#                     line = mpl[i]
#                     start = line[0]
#                     finish = line[-1]
#                     if outletAtStart:
#                         if not outletToLakeDone and QSWATTopology.coincidentPoints(outlet, start, xThreshold, yThreshold):
#                             newLine = []
#                             for pt in line:
#                                 newLine.append(pt)
#                                 if resGeom.intersects(QgsGeometry.fromPointXY(pt)):
#                                     outletToLakeDone = True 
#                                     break
#                             outletPart.append(newLine)
#                             outlet = finish
#                             reduced = True
#                             done.add(i)
#                         elif not sourceToLakeDone and QSWATTopology.coincidentPoints(source, finish, xThreshold, yThreshold):
#                             newLine = []
#                             for pt in reversed(line):
#                                 newLine.insert(0, pt)
#                                 if resGeom.intersects(QgsGeometry.fromPointXY(pt)):
#                                     sourceToLakeDone = True 
#                                     break
#                             sourcePart.append(newLine)
#                             source = start
#                             done.add(i)
#                             reduced = True
#                     else:
#                         if not outletToLakeDone and QSWATTopology.coincidentPoints(outlet, finish, xThreshold, yThreshold):
#                             newLine = []
#                             for pt in reversed(line):
#                                 newLine.insert(0, pt)
#                                 if resGeom.intersects(QgsGeometry.fromPointXY(pt)):
#                                     outletToLakeDone = True 
#                                     break
#                             outletPart.append(line)
#                             outlet = start
#                             done.add(i)
#                             reduced = True
#                         elif QSWATTopology.coincidentPoints(source, start, xThreshold, yThreshold):
#                             newLine = []
#                             for pt in line:
#                                 newLine.append(pt)
#                                 if resGeom.intersects(QgsGeometry.fromPointXY(pt)):
#                                     sourceToLakeDone = True 
#                                     break
#                             sourcePart.append(line)
#                             source = finish
#                             done.add(i)
#                             reduced = True
#             if outletToLakeDone and sourceToLakeDone:
#                 break
#             if not reduced:
#                 raise Exception('Looping trying to split reach')
#         sourceGeom = QgsGeometry.fromPolyline(sourcePart[0]) if len(sourcePart) == 1 else QgsGeometry.fromMultiPolyline(sourcePart)
#         outletGeom = QgsGeometry.fromPolyline(outletPart[0]) if len(outletPart) == 1 else QgsGeometry.fromMultiPolyline(outletPart)
#         return sourceGeom, outletGeom
    
    @staticmethod        
    def movePointToPerimeter(pt, lakeGeom, pFile, maxSteps):
        """Point pt is contained in lake.  Move it downstream at most maxSteps
        using D8 flow direction raster pFile until it is not inside the lake,
        returning new point and true.
        
        Return original point and false if failed to find perimeter."""
        pLayer = QgsRasterLayer(pFile, 'FlowDir')
        ds = gdal.Open(pFile, gdal.GA_ReadOnly)
        pNodata = ds.GetRasterBand(1).GetNoDataValue()
        transform = ds.GetGeoTransform()
        stepCount = 0
        pt1 = pt
        while stepCount < maxSteps:
            if not lakeGeom.contains(pt1):
                return pt1, True
            dir1 = QSWATTopology.valueAtPoint(pt1, pLayer)
            if dir1 is None or dir1 == pNodata:
                QSWATUtils.loginfo('Failed to reach lake perimeter: no flow direction available.')
                return pt, False
            # dir1 is read as a float.  Also subtract 1 to get range 0..7
            dir0 = int(dir1) - 1
            col, row = QSWATTopology.projToCell(pt1.x(), pt1.y(), transform)
            col1, row1 = col + QSWATUtils._dX[dir0], row + QSWATUtils._dY[dir0]
            x1, y1 = QSWATTopology.cellToProj(col1, row1, transform)
            pt1 = QgsPointXY(x1, y1)
            stepCount += 1
        QSWATUtils.loginfo('Failed to reach lake perimeter in {0} steps.'.format(maxSteps))
        return pt, False        
            
