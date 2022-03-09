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
from qgis.PyQt.QtCore import QSettings, QVariant
#from qgis.PyQt.QtGui import *  # @UnusedWildImport type: ignore 
from qgis.core import QgsCoordinateReferenceSystem, QgsUnitTypes, QgsCoordinateTransform, QgsProject, QgsFeatureRequest, QgsField, QgsFeature, QgsVectorLayer, QgsPointXY, QgsRasterLayer, QgsExpression, QgsGeometry, QgsVectorDataProvider, QgsRectangle, QgsLayerTreeGroup,  QgsLayerTreeLayer, QgsJsonExporter
from osgeo import gdal  # type: ignore
from numpy import * # @UnusedWildImport
import os.path
import time
import csv
import traceback
from typing import Set, List, Dict, Tuple, Iterable, Iterator, cast, Any, Optional, Union, Callable, TYPE_CHECKING  # @UnusedImport @Reimport

# if TYPE_CHECKING:
#     from globals import Any

try:
    from .QSWATUtils import QSWATUtils, FileTypes, ListFuns   # type: ignore # @UnusedImport
    from .DBUtils import DBUtils  # type: ignore  # @UnusedImport  
    from .parameters import Parameters  # type: ignore #  @UnusedImport  
    from .raster import Raster  # type: ignore  # @UnusedImport  
    from .dataInC import ReachData, MergedChannelData, LakeData, LSUData, BasinData  # type: ignore #  @UnusedImport @UnresolvedImport  
except:
    # used by convertFromArc
    from QSWATUtils import QSWATUtils, FileTypes, ListFuns  # @UnresolvedImport @Reimport
    from DBUtils import DBUtils  # @UnresolvedImport @Reimport
    from parameters import Parameters  # @UnresolvedImport @Reimport
    from raster import Raster  # @UnresolvedImport @Reimport
    from dataInC import ReachData, MergedChannelData, LakeData, LSUData, BasinData  # @UnresolvedImport @Reimport

    
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
    
    # lake water roles
    _RESTYPE = 1
    _PONDTYPE = 2
    _WETLANDTYPE = 3
    _PLAYATYPE = 4
    
    # flow types (hyd_typ in gis_routing)
    _TOTAL = 'tot'
    _RECHARGE = 'rhg'
    _SURFACE = 'sur'
    _LATERAL = 'lat'
    _TILE = 'til'
    
    _LINKNO = 'LINKNO'
    _DSLINKNO = 'DSLINKNO'
    _DSLINKNO1 = 'DSLINKNO1'
    _DSLINKNO2 = 'DSLINKNO2'
    _USLINKNO1 = 'USLINKNO1'
    _USLINKNO2 = 'USLINKNO2'
    _DSNODEID = 'DSNODEID'
    _DSNODEID1 = 'DSNODEID1'
    _DSNODEID2 = 'DSNODEID2'
    _DRAINAREA = 'DSContArea'
    _DRAINAREA2 = 'DS_Cont_Ar' # for tauDEM 5.1.2
    _DRAINAGE = 'Drainage'
    _ORDER =  'strmOrder'
    _ORDER2 = 'Order' # for tauDEM 5.1.2
    _ORDERHUC = 'streamorde'  # for HUC models
    _LENGTH = 'Length'
    _MAGNITUDE = 'Magnitude'
    _DROP = 'strmDrop'
    _DROP2 = 'Drop' # for tauDEM 5.1.2
    _SLOPE = 'Slope'
    _STRAIGHTL = 'StraightL'
    _STRAIGHTL2 = 'Straight_L'  # for tauDEM 5.1.2
    _USCONTAR = 'USContArea'
    _USCONTAR2 = 'US_Cont_Ar'  # for tauDEM 5.1.2
    _WSNO = 'WSNO'
    _DOUTEND = 'DOUTEND'
    _DOUTEND2 = 'DOUT_END'  # for tauDEM 5.1.2
    _DOUTSTART = 'DOUTSTART'
    _DOUTSTART2 = 'DOUT_START' # for tauDEM 5.1.2
    _DOUTMID =  'DOUTMID'
    _DOUTMID2 =  'DOUT_MID' # for tauDEM 5.1.2
    _BASINNO = 'BasinNo'
    _ID = 'ID'
    _INLET = 'INLET'
    _RES = 'RES'
    _PTSOURCE = 'PTSOURCE'
    _ADDED = 'ADDED'
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
    _POINTID = 'PointId'
    _SOURCEX = 'SourceX'
    _SOURCEY = 'SourceY'
    _OUTLETX = 'OutletX'
    _OUTLETY = 'OutletY'
    _TOTDASQKM = 'TotDASqKm'
    
    _HUCPointId = 100000  # for HUC models all point ids are this number or greater (must match value in HUC12Models.py in HUC12Watersheds 
    
    
    def __init__(self, isBatch: bool, isHUC: bool) -> None:
        """Initialise class variables."""
        ## Link to project database
        self.db: Optional[DBUtils] = None
        ## True if outlet end of reach is its first point, i.e. index zero."""
        self.outletAtStart = True
        ## index to LINKNO in channel shapefile
        self.channelIndex = -1
        ## index to DSLINKNO in channel shapefile
        self.dsChannelIndex = -1
        ## index to WSNO in channel shapefile (value commonly called channel basin)
        self.wsnoIndex = -1
        ## relation between channel basins and subbasins
        # not used with grid models (since would be 1-1)
        self.chBasinToSubbasin: Dict[int, int] = dict()
        ## WSNO does not obey SWAT rules for element numbers (> 0) 
        # so we invent and store SWATBasin numbers
        # also SWAT basins may not be empty
        # not complete: zero areas/stream lengths excluded
        self.subbasinToSWATBasin: Dict[int, int] = dict()
        ##inverse map to make it easy to output in numeric order of SWAT Basins
        self.SWATBasinToSubbasin: Dict[int, int] = dict()
        ## original channel links may have zero numbers and may have zero lengths
        ## so we generate SWATChannel ids
        # not complete
        self.channelToSWATChannel: Dict[int, int] = dict()
        ## inverse map
        self.SWATChannelToChannel: Dict[int, int] = dict()
        ## subbasin to stream mapping (wsno to link fields in streams shapefile)
        # complete
        self.subbasinToStream: Dict[int, int] = dict()
        ## stream to downstream (link to dslink in streams shapefile)
        # complete
        self.downStreams: Dict[int, int] = dict()
        ## stream lengths (link to length in streams shapefile).  Lengths are in metres
        # complete
        self.streamLengths: Dict[int, float] = dict()
        ## LINKNO to DSLINKNO in channel shapefile
        # complete = all channel links defined
        self.downChannels: Dict[int, int] = dict()
        ## zero length channels
        self.zeroChannels: Set[int] = set()
        ## subbasin to downstream subbasin
        # incomplete: no empty basins (zero length streams or missing wsno value in subbasins layer)
        self.downSubbasins: Dict[int, int] = dict()
        ## map from channel to chBasin
        # incomplete - no zero length channels
        self.chLinkToChBasin: Dict[int, int] = dict()
        ## reverse of chLinkToChBasin
        self.chBasinToChLink: Dict[int, int] = dict()
        ## centroids of basins as (x, y) pairs in projected units
        self.basinCentroids: Dict[int, Tuple[float, float]] = dict()
        ## channel link to channel length in metres:
        # complete
        self.channelLengths: Dict[int, float] = dict()
        ## channel slopes in m/m
        # complete
        self.channelSlopes: Dict[int, float] = dict()
        ## numpy array of total area draining to downstream end of channel in square metres
        self.drainAreas: numpy.ndarray[float] = None  # type: ignore # @UndefinedVariable  
        ## numpy array of Strahler order of channels
        self.strahler: numpy.ndarray[int] = None  # type: ignore # @UndefinedVariable 
        ## map of lake id to ids of points added to split channels entering lakes
        self.lakeInlets: Dict[int, List[int]] = dict()
        ## map of lake id to ids of points added to split channels leaving lakes
        self.lakeOutlets: Dict[int, List[int]] = dict()
        ## map of channel to ReachData: points and elevations at ends of channels, plus basin
        # not complete: zero areas/channel lengths excluded
        self.channelsData: Dict[int, ReachData] = dict()
        ## map of lake id to LakeData for lakes defined by shapefile
        self.lakesData: Dict[int, LakeData] = dict()
        ## map of channel links to lake ids: channel flowing into lake
        self.chLinkIntoLake: Dict[int, int] = dict()
        ## map of channel links to lake ids: channel completely inside lake
        self.chLinkInsideLake: Dict[int, int] = dict()
        ## map of channel links to lake ids: channel flowing out of lake
        self.chLinkFromLake: Dict[int, int] = dict()
        ## map of subbasin to lake id for subbasins with their outlet inside a lake (non-grid models only)
        self.outletsInLake: Dict[int, int] = dict()
        ## channel basin to area in square metres.  Not used with grid model.
        self.chBasinAreas: Dict[int, float] = dict()
        # original of chBasinAreas for use after chBasinAreas affected by merging, in case merging repeated
        self.origChBasinAreas: Dict[int, float] = dict()
        ## current point id (for outlets, inlets and point sources)
        self.pointId = 0
        ## current water body id (for lakes, reservoirs and ponds)
        self.waterBodyId = 0
        ## channel links to reservoir or pond point ids plus water type: reservoir or pond discharges into channel
        self.chLinkToWater: Dict[int, Tuple[int, QgsPointXY, int]] = dict()
        ## channel links with point sources flowing into them (defined by inlets/outlets file)
        self.chLinkToPtSrc: Dict[int, Tuple[int, QgsPointXY]] = dict()
        ## channel links to watershed inlets (for grid models only)
        self.chLinkToInlet: Dict[int, Tuple[int, QgsPointXY]] = dict()
        ## basins draining to inlets
        self.upstreamFromInlets: Set[int] = set()
        ## width of DEM cell in metres
        self.dx: float = 0
        ## depth of DEM cell in metres
        self.dy: float = 0
        ## x direction threshold for points to be considered coincident
        self.xThreshold = 0
        ## y direction threshold for points to be considered coincident
        self.yThreshold = 0
        ## multiplier to turn DEM distances to metres
        self.horizontalFactor = 1
        ## multiplier to turn DEM elevations to metres
        self.verticalFactor = 1
        ## DEM nodata value
        self.demNodata: float = 0
        ## DEM extent
        self.demExtent = None
        ## map from subbasin to outlet pointId, point, and channel(s) draining to it
        self.outlets: Dict[int, Tuple[int, QgsPointXY, List[int]]] = dict()
        ## map from subbasin to inlet pointId and point (not used with grid models)
        self.inlets: Dict[int, Tuple[int, QgsPointXY]] = dict()
        ## map from channel links to outlet end
        self.chOutlets: Dict[int, Tuple[int, QgsPointXY]] = dict()
        ## map from channel links to point sources
        self.chPointSources: Dict[int, Tuple[int, QgsPointXY]] = dict()
        ## reservoirs found by converting water HRUs
        self.foundReservoirs: Dict[int, Tuple[int, int, QgsPointXY]] = dict()
        ## lat-long coordinate reference system
        self.crsLatLong = QgsCoordinateReferenceSystem('EPSG:4326')
        ## transform from project corrdinates to lat-long
        self.transformToLatLong: Optional[QgsCoordinateTransform] = None
        ## Flag to show if batch run
        self.isBatch = isBatch
        ## flag for HUC projects
        self.isHUC = isHUC
        ## table for memorizing distances from basin to join in flowpath with other basin:
        # basin -> otherBasin -> join distance in metres
        self.distancesToJoins: Dict[int, Dict[int, float]] = dict()
        ## table for use in existing non-grid models of maximum channel flow lengths in metres to subbasin outlets
        # complete
        self.maxFlowLengths: Dict[int, float] = dict()
        ## number of chunks to use for rasters and their arrays; increased when memory fails
        self.chunkCount = 1
        ## dsNodeIds that cannot be retained when making grids as they would be in same grid cell as another point
        self.lostDsNodeIds: Set[int] = set()
        
    def setUp0(self, demLayer: QgsRasterLayer, channelLayer: QgsVectorLayer, 
               outletLayer: Optional[QgsVectorLayer], ad8Layer: QgsRasterLayer, gv: Any) -> bool:
        """Set DEM size parameters and stream orientation, and store source and outlet points for stream reaches."""
        # can fail if demLayer is None or not projected
        try:
            self.setCrs(demLayer, gv)
            assert gv.crsProject is not None
            units = gv.crsProject.mapUnits()
        except Exception:
            QSWATUtils.loginfo('Failure to read DEM units: {0}'.format(traceback.format_exc()))
            return False
        if units == QgsUnitTypes.DistanceMeters:
            gv.horizontalFactor = 1
        elif units == QgsUnitTypes.DistanceFeet:
            gv.horizontalFactor = Parameters._FEETTOMETRES
        else:
            # unknown or degrees - will be reported in delineation - just quietly fail here
            QSWATUtils.loginfo('Failure to read DEM units: {0}'.format(str(units)))
            return False
        self.demNodata = demLayer.dataProvider().sourceNoDataValue(1)
        self.dx = demLayer.rasterUnitsPerPixelX() * gv.horizontalFactor
        self.dy = demLayer.rasterUnitsPerPixelY() * gv.horizontalFactor
        self.xThreshold = self.dx * Parameters._NEARNESSTHRESHOLD
        self.yThreshold = self.dy * Parameters._NEARNESSTHRESHOLD
        QSWATUtils.loginfo('Factor is {0}, cell width is {1}, cell depth is {2}'.format(gv.horizontalFactor, self.dx, self.dy))
        self.demExtent = demLayer.extent()  # type: ignore
        self.horizontalFactor = gv.horizontalFactor
        self.verticalFactor = gv.verticalFactor
        self.outletAtStart = self.hasOutletAtStart(channelLayer, ad8Layer)
        QSWATUtils.loginfo('Outlet at start is {0!s}'.format(self.outletAtStart))
        self.outletsInLake.clear()
        return self.saveOutletsAndSources(channelLayer, outletLayer, gv.useGridModel)
    
    def setCrs(self, demLayer: QgsRasterLayer, gv: Any) -> None:
        """Set crsProject and transformToLatLong if necessary."""
        if gv.crsProject is None:
            gv.crsProject = demLayer.crs()
            self.transformToLatLong = QgsCoordinateTransform(gv.crsProject, self.crsLatLong, QgsProject.instance())
            QgsProject.instance().setCrs(gv.crsProject)
            settings = QSettings()
            settings.setValue('Projections/defaultBehaviour', 'useProject')
    
    def setUp1(self, streamLayer: QgsVectorLayer) -> bool:
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
        lengthIndex = self.getIndex(streamLayer, QSWATTopology._LENGTH, ignoreMissing=True)
        wsnoIndex = self.getIndex(streamLayer, QSWATTopology._WSNO)
        if wsnoIndex < 0:
            QSWATUtils.loginfo('No WSNO field in stream layer')
            return False
        for reach in streamLayer.getFeatures():
            link = reach[streamIndex]
            dsLink = reach[dsStreamIndex]
            basin = reach[wsnoIndex]
            if lengthIndex < 0:
                length = reach.geometry().length() * self.horizontalFactor
            else:
                length = reach[lengthIndex] * self.horizontalFactor
            self.subbasinToStream[basin] = link
            self.downStreams[link] = dsLink
            self.streamLengths[link] = length
        return True
        
    def setUp(self, demLayer: QgsRasterLayer, channelLayer: QgsVectorLayer, subbasinsLayer: QgsVectorLayer, 
              outletLayer: Optional[QgsVectorLayer], lakesLayer: Optional[QgsVectorLayer], gv: Any, 
              existing: bool, recalculate: bool, useGridModel: bool, streamDrainage: bool, reportErrors: bool) -> bool:
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
        dsNodeToLink: Dict[int, int] = dict()
        ignoreError = not reportErrors
        ignoreWithExisting = existing or not reportErrors
        ignoreWithGrid = useGridModel or not reportErrors
        ignoreWithGridOrExisting = ignoreWithGrid or ignoreWithExisting
        ignoreWithGridOrExistingOrWin = ignoreWithGridOrExisting or Parameters._ISWIN
        ignoreTotDA = not self.isHUC
        self.channelIndex = self.getIndex(channelLayer, QSWATTopology._LINKNO, ignoreMissing=ignoreError)
        if self.channelIndex < 0:
            QSWATUtils.loginfo('No LINKNO field in channels layer')
            return False
        DSLINKNO = QSWATTopology._DSLINKNO1 if self.isHUC else QSWATTopology._DSLINKNO
        self.dsChannelIndex = self.getIndex(channelLayer, DSLINKNO, ignoreMissing=ignoreError)
        if self.dsChannelIndex < 0:
            QSWATUtils.loginfo('No DSLINKNO field in channels layer')
            return False
        DSNODEID = QSWATTopology._DSNODEID1 if self.isHUC else QSWATTopology._DSNODEID
        dsNodeIndex = self.getIndex(channelLayer, DSNODEID, ignoreMissing=ignoreWithExisting)
        dsNode2Index = self.getIndex(channelLayer, QSWATTopology._DSNODEID2, ignoreMissing=not self.isHUC)
        self.wsnoIndex = self.getIndex(channelLayer, QSWATTopology._WSNO, ignoreMissing=ignoreError)
        if self.wsnoIndex < 0:
            QSWATUtils.loginfo('No WSNO field in channels layer')
            return False
        if self.isHUC:
            orderIndex = self.getIndex(channelLayer, QSWATTopology._ORDERHUC, ignoreMissing=False)
        else:
            orderIndex = self.getIndex(channelLayer, QSWATTopology._ORDER, ignoreMissing=ignoreWithGridOrExistingOrWin)
            if orderIndex < 0 and ignoreWithGridOrExistingOrWin:
                orderIndex = self.getIndex(channelLayer, QSWATTopology._ORDER2, ignoreMissing=ignoreWithGridOrExisting)
        drainAreaIndex = self.getIndex(channelLayer, QSWATTopology._DRAINAREA, ignoreMissing=ignoreWithGridOrExistingOrWin)
        if drainAreaIndex < 0 and ignoreWithGridOrExistingOrWin:
            drainAreaIndex = self.getIndex(channelLayer, QSWATTopology._DRAINAREA2, ignoreMissing=ignoreWithGridOrExisting)
        lengthIndex = self.getIndex(channelLayer, QSWATTopology._LENGTH, ignoreMissing=ignoreWithGridOrExisting)
        dropIndex = self.getIndex(channelLayer, QSWATTopology._DROP, ignoreMissing=ignoreWithGridOrExistingOrWin)
        if dropIndex < 0 and ignoreWithGridOrExistingOrWin:
            dropIndex = self.getIndex(channelLayer, QSWATTopology._DROP2, ignoreMissing=ignoreWithGridOrExisting)
        totDAIndex = self.getIndex(channelLayer, QSWATTopology._TOTDASQKM, ignoreMissing=ignoreTotDA)
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
            ptIdIndex = self.getIndex(outletLayer, QSWATTopology._POINTID, ignoreMissing=ignoreError)
            if ptIdIndex < 0:
                QSWATUtils.loginfo('No PointId field in outlets layer')
                return False
            # ADDED field only used with lakes: may be missing
            addIndex = self.getIndex(outletLayer, QSWATTopology._ADDED, ignoreMissing=True)
        # upstream links
        us: Dict[int, List[int]] = dict()
        time1 = time.process_time()
        maxChLink = 0
        SWATChannel = 0
        # drainAreas is a mapping from link number (used as index to array) of grid cell areas in sq m
        if self.isHUC:
            # make it a dictionary rather than a numpy array because there is a big gap
            # between most basin numbers and the nunbers for inlets (100000 +)
            # and we need to do no calculation
            # create it here for HUC models as we set it up from totDASqKm field in channelLayer
            self.drainAreas = dict()
        for channel in channelLayer.getFeatures():
            chLink: int = channel[self.channelIndex]
            dsChLink: int = channel[self.dsChannelIndex]
            chBasin: int = channel[self.wsnoIndex]
            geom: QgsGeometry = channel.geometry()
            if lengthIndex < 0 or recalculate:
                length = geom.length() * gv.horizontalFactor
            else:
                length = channel[lengthIndex] * gv.horizontalFactor
            if self.isHUC and length == 0:  # allow for zero length inlet channels
                data = None
            else:
                data = self.getReachData(channel, demLayer)
                self.channelsData[chLink] = data
            # don'use TauDEM drops: affected by burn-in
            # if data and (dropIndex < 0 or recalculate):
            #     drop = data.upperZ - data.lowerZ
            # elif dropIndex >= 0:
            #     drop = channel[dropIndex]
            # else:
            #     drop = 0
            if data:
                drop = data.upperZ - data.lowerZ
            else:
                drop = 0
            slope = 0 if length <= 0 or drop < 0 else float(drop) / length
            dsNode = channel[dsNodeIndex] if dsNodeIndex >= 0 else -1
            dsNode2 = channel[dsNode2Index] if dsNode2Index >= 0 else -1
            if useGridModel and chBasin < 0:
                # it is the downstream channel link from an inlet, and has no basin
                pass
            else:
                self.chLinkToChBasin[chLink] = chBasin
                self.chBasinToChLink[chBasin] = chLink
                # exit channels in grid model can have zero length
                if length > 0 or useGridModel: 
                    SWATChannel += 1
                    self.channelToSWATChannel[chLink] = SWATChannel
                    self.SWATChannelToChannel[SWATChannel] = chLink
                # inlets in HUC models are zero length channels, and these have positive DSNODEIDs
                elif dsNode < 0 or self.isHUC:
                    self.zeroChannels.add(chLink)
            maxChLink = max(maxChLink, chLink)
            self.downChannels[chLink] = dsChLink
            self.channelLengths[chLink] = length
            self.channelSlopes[chLink] = slope
            if dsNode >= 0:
                dsNodeToLink[dsNode] = chLink
                #QSWATUtils.loginfo('DSNode {0} mapped to channel link {1}'.format(dsNode, chLink))
            if dsNode2 >= 0:
                dsNodeToLink[dsNode2] = chLink
                #QSWATUtils.loginfo('Minor DSNode {0} mapped to channel link {1}'.format(dsNode2, chLink))
            if dsChLink >= 0 and not (self.isHUC and chLink >= QSWATTopology._HUCPointId):  # keep HUC links out of us map
                ups = us.setdefault(dsChLink, [])
                ups.append(chLink)
                if not useGridModel:  # try later to fix circularities in grid models
                    # check we haven't just made the us relation circular
                    if QSWATTopology.reachable(dsChLink, [chLink], us):
                        QSWATUtils.error('Circular drainage network from channel link {0}'.format(dsChLink), self.isBatch)
                        return False
            if self.isHUC:
                self.drainAreas[chLink] = channel[totDAIndex] * 1E6  # sq km to sq m
        time2 = time.process_time()
        QSWATUtils.loginfo('Topology setup for channels took {0} seconds'.format(int(time2 - time1)))
        if not useGridModel:
            self.setChannelBasinAreas(gv)
            self.origChBasinAreas = QSWATTopology.copyBasinAreas(self.chBasinAreas)
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
            doneNodes: Set[int] = set()
            for point in features:
                # ignore HUC reservoir and pond points: only for display
                if self.isHUC and point[resIndex] > 0:
                    continue
                dsNode = point[idIndex]
                if dsNode in doneNodes:
                    if reportErrors:
                        QSWATUtils.error('ID value {0} is used more than once in inlets/outlets file {1}.  Occurrences after the first are ignored'
                                         .format(dsNode, QSWATUtils.layerFilename(outletLayer)), self.isBatch)
                    chLink = -1    
                elif dsNode in self.lostDsNodeIds:
                    chLink = -1
                elif dsNode not in dsNodeToLink:
                    if self.isHUC:  # extra points can occur, typically duplicates: ignore
                        continue
                    if reportErrors:
                        QSWATUtils.error("""ID value {0} from inlets/outlets file {1} not found as DSNODEID in channels file {2}.  Will be ignored.
                        This can be caused by an occasional error in delineation: try rerunning 'Create watershed'."""
                                         .format(dsNode, QSWATUtils.layerFilename(outletLayer), 
                                                QSWATUtils.layerFileInfo(channelLayer).filePath()), self.isBatch)
                    chLink = -1
                else:
                    chLink = dsNodeToLink[dsNode]
                doneNodes.add(dsNode)
                if chLink >= 0:
                    if point[inletIndex] == 1:
                        if point[ptSourceIndex] == 1:
                            isPtSource = True
                            isInlet = False
                        else:
                            isPtSource = False
                            isInlet = True
                    else:
                        isPtSource = False
                        isInlet = False
                    isReservoir = point[resIndex] == 1
                    isPond = point[resIndex] == 2
                    isAdded = addIndex >= 0 and point[addIndex] == 1
                    if not isAdded and lakesLayer is not None: 
                        # check if point is inside lake
                        for lake in lakesLayer.getFeatures():
                            lakeGeom = lake.geometry()
                            lakeRect = lakeGeom.boundingBox()
                            if QSWATTopology.polyContains(point.geometry().asPoint(), lakeGeom, lakeRect):
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
                                lakeIdIndex = lakesLayer.dataProvider().fieldNameIndex(QSWATTopology._LAKEID)
                                lakeId = int(lake[lakeIdIndex])
                                QSWATUtils.information('{0} {1} is inside lake {2}.  Will be ignored.'.format(typ, dsNode, lakeId), self.isBatch)
                                break
                    if isInlet:
                        if isPtSource:
                            pt = point.geometry().asPoint()
                            self.chLinkToPtSrc[chLink] = (point[ptIdIndex], pt)
                        elif useGridModel: # inlets collected in setUp0 for non-grids
                            pt = point.geometry().asPoint()
                            self.chLinkToInlet[chLink] = (point[ptIdIndex], pt)
                    elif isReservoir:
                        pt = point.geometry().asPoint()
                        self.chLinkToWater[chLink] = (point[ptIdIndex], pt, QSWATTopology._RESTYPE)
                    elif isPond:
                        pt = point.geometry().asPoint()
                        self.chLinkToWater[chLink] = (point[ptIdIndex], pt, QSWATTopology._PONDTYPE)
                    # else an outlet: nothing to do
                    
                    # check for user-defined outlets coincident with stream junctions
                    if chLink in self.zeroChannels and chLink not in self.chLinkIntoLake and not (isInlet and self.isHUC):
                        if isInlet: typ = 'Inlet'
                        elif isPtSource: typ = 'Point source'
                        elif isReservoir: typ = 'Reservoir'
                        elif isPond: typ = 'Pond'
                        else: typ = 'Outlet'
                        if typ != 'Outlet':
                            msg = '{0} with id {1} has a zero length channel leading to it: please remove or move downstream'.format(typ, dsNode)
                            if reportErrors:
                                QSWATUtils.error(msg, self.isBatch)
                            else:
                                QSWATUtils.loginfo(msg)
                            return False
        time4 = time.process_time()
        QSWATUtils.loginfo('Topology setup for inlets/outlets took {0} seconds'.format(int(time4 - time3)))
        # add any extra reservoirs and point sources
        # create drainAreas here for non-HUC models as we now have maxChLink value to size the numpy array
        if not self.isHUC:
            self.drainAreas = zeros((maxChLink + 1), dtype=float)
            if useGridModel:
                gridCellArea = self.dx * self.dy * gv.gridSize * gv.gridSize
                # try to use Drainage field from grid channels shapefile
                if streamDrainage:
                    ok = self.setGridDrainageFromChannels(channelLayer, subbasinsLayer, maxChLink, us)
                else:
                    ok = False
                if not ok:
                    self.setGridDrainageAreas(channelLayer, subbasinsLayer, maxChLink, us, gridCellArea)
            else:
                # can use drain areas from TauDEM if we have them
                if drainAreaIndex >= 0:
                    self.setDrainageFromChannels(channelLayer, drainAreaIndex)
                else:
                    self.setDrainageAreas(us)
        time5 = time.process_time()
        QSWATUtils.loginfo('Topology drainage took {0} seconds'.format(int(time5 - time4)))
        # Strahler order
        if self.isHUC:
            # use dict because of range of channel links, as we did for drainAreas
            self.strahler = dict()
        else:
            self.strahler = zeros((maxChLink + 1), dtype=int)
        if orderIndex >= 0:
            self.setStrahlerFromChannels(channelLayer, orderIndex)
        elif useGridModel:
            self.setStrahlerFromGrid(us)
        else:
            self.setStrahler(us)
        #try existing subbasin numbers as SWAT basin numbers
        ok = polyIndex >= 0 and subbasinIndex >= 0 and self.tryBasinAsSWATBasin(subbasinsLayer, polyIndex, subbasinIndex, useGridModel)
        if not ok:
            # failed attempt may have put data in these, so clear them
            self.subbasinToSWATBasin.clear()
            self.SWATBasinToSubbasin.clear()
            # create SWAT basin numbers
            SWATBasin = 0
            request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([polyIndex])
            for feature in subbasinsLayer.getFeatures(request):
                subbasin = feature[polyIndex]
                if subbasin not in self.upstreamFromInlets and (useGridModel or subbasin in self.chBasinToSubbasin.values()):  # else was removed by chBasin being within a lake
                    SWATBasin += 1
                    self.subbasinToSWATBasin[subbasin] = SWATBasin
                    self.SWATBasinToSubbasin[SWATBasin] = subbasin
            # put SWAT Basin numbers in subbasin field of subbasins shapefile
            subbasinsProvider = subbasinsLayer.dataProvider()
            if subbasinIndex < 0:
                # need to add subbasin field
                subbasinsProvider.addAttributes([QgsField(QSWATTopology._SUBBASIN, QVariant.Int)])
                subbasinsLayer.updateFields()
                subbasinIndex = subbasinsProvider.fieldNameIndex(QSWATTopology._SUBBASIN)
            mmap: Dict[int, Dict[int, int]] = dict()
            request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([polyIndex])
            for feature in subbasinsProvider.getFeatures(request):
                subbasin = feature[polyIndex]
                SWATBasin = self.subbasinToSWATBasin.get(subbasin, 0)
                mmap[feature.id()] = {subbasinIndex: SWATBasin}
            subbasinsProvider.changeAttributeValues(mmap)
            # put SWAT Basin numbers in subbasin field of subsNoLakes shapefile if exists
            if os.path.isfile(gv.subsNoLakesFile):
                subsNoLakesLayer = QgsVectorLayer(gv.subsNoLakesFile, 'subsNoLakes', 'ogr')
                subsNoLakesProvider = subsNoLakesLayer.dataProvider()
                subbasinIndex = subsNoLakesProvider.fieldNameIndex(QSWATTopology._SUBBASIN)
                if subbasinIndex < 0:
                    # need to add subbasin field
                    subsNoLakesProvider.addAttributes([QgsField(QSWATTopology._SUBBASIN, QVariant.Int)])
                    subsNoLakesLayer.updateFields()
                    subbasinIndex = subsNoLakesProvider.fieldNameIndex(QSWATTopology._SUBBASIN)
                request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([polyIndex])
                mmap = dict()
                for feature in subsNoLakesProvider.getFeatures(request):
                    subbasin = feature[polyIndex]
                    SWATBasin = self.subbasinToSWATBasin.get(subbasin, 0)
                    mmap[feature.id()] = {subbasinIndex: SWATBasin}
                subsNoLakesProvider.changeAttributeValues(mmap)
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
                chBasin = feature[wshedPolyIndex]
                chLink = self.chBasinToChLink.get(chBasin, -1)
                SWATChannel = self.channelToSWATChannel.get(chLink, 0)
                wshedLayer.changeAttributeValue(feature.id(), wshedChannelIndex, SWATChannel)
            wshedLayer.commitChanges()
        drainageFile = QSWATUtils.join(gv.shapesDir, gv.projName + Parameters._DRAINAGECSV)
        self.writeDrainageFile(drainageFile)
        return useGridModel or lakesLayer is not None or self.checkAreas(subbasinsLayer, gv)
    
    def addLakes(self, lakesLayer: QgsVectorLayer, subbasinsLayer: QgsVectorLayer, chBasinsLayer: QgsVectorLayer, 
                 streamsLayer: QgsVectorLayer, channelsLayer: QgsVectorLayer, 
                 demLayer: QgsRasterLayer, snapThreshold: float, gv: Any, reportErrors: bool=True) -> bool:
        """Add lakes from lakes shapefile layer.
        
        Not used with grid models.""" 
        errorCount = 0
        lakesProvider = lakesLayer.dataProvider()
        lakeIdIndex = lakesProvider.fieldNameIndex(QSWATTopology._LAKEID)
        lakeResIndex = lakesProvider.fieldNameIndex(QSWATTopology._RES)
        lakeAreaIndex = lakesProvider.fieldNameIndex(Parameters._AREA)
        if lakeResIndex < 0:
            QSWATUtils.information('No RES field in lakes shapefile {0}: assuming lakes are reservoirs'.
                                   format(QSWATUtils.layerFilename(lakesLayer)), self.isBatch, reportErrors=reportErrors)
        subsProvider =  subbasinsLayer.dataProvider()
        subsPolyIndex = subsProvider.fieldNameIndex(QSWATTopology._POLYGONID)
        subsAreaIndex = subsProvider.fieldNameIndex(Parameters._AREA)
        if subsAreaIndex < 0:
            QSWATUtils.error('Cannot find {0} field in {1}'.format(Parameters._AREA, gv.subbasinsFile), self.isBatch)
            return False
        chBasinsProvider = chBasinsLayer.dataProvider()
        chBasinsPolyIndex = chBasinsProvider.fieldNameIndex(QSWATTopology._POLYGONID)
        chBasinsAreaIndex = chBasinsProvider.fieldNameIndex(Parameters._AREA)
        channelsProvider = channelsLayer.dataProvider()
        channelLinkIndex = channelsProvider.fieldNameIndex(QSWATTopology._LINKNO)
        DSLINKNO = QSWATTopology._DSLINKNO1 if self.isHUC else QSWATTopology._DSLINKNO
        channelDsLinkIndex = channelsProvider.fieldNameIndex(DSLINKNO)
        DSNODEID = QSWATTopology._DSNODEID1 if self.isHUC else QSWATTopology._DSNODEID
        channelDsNodeIndex = channelsProvider.fieldNameIndex(DSNODEID)
        channelDrainAreaIndex = channelsProvider.fieldNameIndex(QSWATTopology._DRAINAREA)
        if channelDrainAreaIndex < 0:
            channelDrainAreaIndex = channelsProvider.fieldNameIndex(QSWATTopology._DRAINAREA2)
        channelWSNOIndex = channelsProvider.fieldNameIndex(QSWATTopology._WSNO)
        channelBasinIndex = channelsProvider.fieldNameIndex(QSWATTopology._BASINNO)
        self.addLakeFieldsToChannels(channelsLayer)
        channelLakeInIndex = channelsProvider.fieldNameIndex(QSWATTopology._LAKEIN)
        channelLakeOutIndex = channelsProvider.fieldNameIndex(QSWATTopology._LAKEOUT)
        channelLakeWithinIndex = channelsProvider.fieldNameIndex(QSWATTopology._LAKEWITHIN)
        channelLakeMainIndex = self.getIndex(channelsLayer, QSWATTopology._LAKEMAIN)
        self.chLinkIntoLake = dict()
        self.chLinkInsideLake = dict()
        self.chLinkFromLake = dict()
        areaFactor = gv.horizontalFactor * gv.horizontalFactor
        lakeAttMap: Dict[int, Dict[int, int]] = dict()
        for lake in lakesProvider.getFeatures():
            lakeGeom = lake.geometry()
            lakeRect = lakeGeom.boundingBox()
            lakeId = int(lake[lakeIdIndex])
            lakeCentroid = lakeGeom.centroid().asPoint()
            lakeArea = lakeGeom.area() * areaFactor
            lakeOverrideArea = lakeArea
            if lakeResIndex < 0:
                waterRole = QSWATTopology._RESTYPE
            else:
                waterRole = lake[lakeResIndex]
            if lakeAreaIndex >= 0:
                try:
                    lakeOverrideArea = float(lake[lakeAreaIndex]) * 1E4  # convert ha to m^2
                except:
                    pass
            lakeData = LakeData(lakeArea, lakeOverrideArea, lakeCentroid, waterRole)
            # reservoirs, ponds and wetlands are removed from subbasins and LSUs maps; playas will make HRUs
            if waterRole == QSWATTopology._PLAYATYPE:
                lakeData.elevation = QSWATTopology.valueAtPoint(lakeCentroid, demLayer)
                self.lakesData[lakeId] = lakeData
                continue
            totalElevation = 0.0
            elevPointCount = 0
            # the area removed from channel basins that intersect wih the lake
            chBasinWaterArea = 0.0
            attMap: Dict[int, Dict[int, float]] = dict()
            geomMap: Dict[int, QgsGeometry] = dict()
            polysToRemove: List[int] = []
            minArea = self.dx * self.dy  # area of one pixel in sq metres
            for sub in subsProvider.getFeatures():
                subGeom = sub.geometry()
                if  QSWATTopology.intersectsPoly(subGeom, lakeGeom, lakeRect):
                    subId = sub.id()
                    area1 = subGeom.area() * areaFactor
                    newGeom = subGeom.difference(lakeGeom)
                    area2 = newGeom.area() * areaFactor
                    if area2 < area1:
                        subPoly = sub[subsPolyIndex]
                        QSWATUtils.loginfo('Lake {0} overlaps subbasin polygon {1}: area reduced from {2} to {3}'.format(lakeId, subPoly, area1, area2))
                        if area2 < minArea:
                            polysToRemove.append(subId)
                            # remove subbasin from range of chBasinToSubbasin
                            chBasinsToRemove: Set[int] = set()
                            for chBasin, subbasin in self.chBasinToSubbasin.items():
                                if subbasin == subPoly:
                                    chBasinsToRemove.add(chBasin)
                            for chBasin in chBasinsToRemove:
                                del self.chBasinToSubbasin[chBasin]
                            QSWATUtils.loginfo('Subbasin polygon {0} removed'.format(subPoly))
                        else:
                            geomMap[subId] = newGeom
                            attMap[subId] = {subsAreaIndex: area2 / 1E4}
            # change attributes and topology BEFORE removing the zero area ones, as removal changes ids of the others
            if not subsProvider.changeAttributeValues(attMap):
                QSWATUtils.error('Failed to update subbasins attributes in {0}'.format(gv.subbasinsFile), self.isBatch)
                for err in subsProvider.errors():
                    QSWATUtils.loginfo(err)
                return False
            if not subsProvider.changeGeometryValues(geomMap):
                QSWATUtils.error('Failed to update subbasin geometries in {0}'.format(gv.subbasinsFile), self.isBatch)
                for err in subsProvider.errors():
                    QSWATUtils.loginfo(err)
                return False
            # for some reason doing both changes at once fails   
#             if not subsProvider.changeFeatures(attMap, geomMap): 
#                 QSWATUtils.error(u'Failed to update {0}'.format(gv.subbasinsFile), self.isBatch)
#                 for err in subsProvider.errors():
#                     QSWATUtils.loginfo(err)
#                 return 
            if len(polysToRemove) > 0:
                if not subsProvider.deleteFeatures(polysToRemove):
                    QSWATUtils.error('Failed to remove polygons from {0}'.format(gv.subbasinsFile), self.isBatch)
                    for err in subsProvider.errors():
                        QSWATUtils.loginfo(err)
            attMap = dict()
            geomMap = dict()
            # map of polygon id to area that is part of the lake
            channelAreaChange: Dict[int, float] = dict()
            for chBasinFeature in chBasinsProvider.getFeatures():
                chBasinGeom = chBasinFeature.geometry()
                polyId = chBasinFeature[chBasinsPolyIndex]
                # if area reduced to zero because inside another lake, geometry is None
                if chBasinGeom is not None and QSWATTopology.intersectsPoly(chBasinGeom, lakeGeom, lakeRect):
                    chBasinId = chBasinFeature.id()
                    area1 = chBasinGeom.area() * areaFactor
                    newGeom = chBasinGeom.difference(lakeGeom)
                    area2 = newGeom.area() * areaFactor
                    if area2 < area1:
                        QSWATUtils.loginfo('Lake {0} overlaps channel basin {1}: area reduced from {2} to {3}'.format(lakeId, polyId, area1, area2))
                        chBasinWaterArea += area1 - area2
                        geomMap[chBasinId] = newGeom
                        attMap[chBasinId] = {chBasinsAreaIndex: area2 / 1E4}
                        channelAreaChange[polyId] = area1 - area2
                        if area2 < minArea:
                            # channel basin disappears into lake: remove its mapping to subbasin
                            # may already have been removed because all subbasin in lake
                            subbasin = self.chBasinToSubbasin.get(polyId, -1)
                            if subbasin >= 0:
                                del self.chBasinToSubbasin[polyId]
                                QSWATUtils.loginfo('Channel basin {0} (subbasin {1}) removed'.format(polyId, subbasin))
            if not chBasinsProvider.changeAttributeValues(attMap):
                QSWATUtils.error('Failed to update channel basin attributes in {0}'.format(gv.wshedFile), self.isBatch)
                for err in chBasinsProvider.errors():
                    QSWATUtils.loginfo(err)
                return False
            if not chBasinsProvider.changeGeometryValues(geomMap):
                QSWATUtils.error('Failed to update channel basin geometries in {0}'.format(gv.wshedFile), self.isBatch)
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
                        inflowData = self.getReachData(channel, demLayer)
                        assert inflowData is not None
                        elev = inflowData.lowerZ
                        lakeData.inChLinks[link] = (dsNode, QgsPointXY(inflowData.lowerX, inflowData.lowerY), elev)
                        if dsLink >= 0:
                            lakeData.lakeChLinks.add(dsLink)
                            self.chLinkInsideLake[dsLink] = lakeId
                        self.chLinkIntoLake[link] = lakeId
                        if not math.isclose(elev, gv.elevationNoData, rel_tol=1e-06):  # type: ignore
                            totalElevation += elev
                            elevPointCount += 1
                        channelId: int = channel.id()
                        wsno: int = channel[channelWSNOIndex]
                        areaChange = channelAreaChange.get(wsno, 0)
                        drainArea = channel[channelDrainAreaIndex] * areaFactor - areaChange
                        attMap[channelId] = {channelDrainAreaIndex: drainArea}
                    elif dsNode in self.lakeOutlets[lakeId]:
                        outflowData = self.getReachData(channel, demLayer)
                        assert outflowData is not None
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
                                # don't use WSNO as route to subbasin as channel basin may have been deleted
                                # wsno = channel[channelWSNOIndex]
                                # subbasin = self.chBasinToSubbasin[wsno]
                                subbasin = channel[channelBasinIndex]
                                lakeData.outPoint = (subbasin, dsNode, outlet, outflowData.lowerZ)
                                lakeData.outChLink = dsLink
                            else:
                                lakeData.otherOutChLinks.add(dsLink)
                            self.chLinkFromLake[dsLink] = lakeId
                        lakeData.lakeChLinks.add(link)
                        self.chLinkInsideLake[link] = lakeId
            # check to see if a watershed outlet was marked inside the lake
            # and if so try to move it to the lake perimeter.  Else leave it as an internal outlet. 
            # we don't need to exclude outlets created to split channels flowing into and out of lake
            # because the outlets map is made from the streams before lake inlets and outlets are added to the snap file
            # and the augmented snapfile is only used to make channels
            for subbasin, (pointId, pt, chs) in self.outlets.items():
                if QSWATTopology.polyContains(pt, lakeGeom, lakeRect) and \
                    self.isWatershedOutlet(pointId, channelsProvider):
                    if not os.path.exists(gv.pFile):
                        QSWATUtils.error('Cannot find D8 flow directions file {0}'.format(gv.pFile), self.isBatch)
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
                    if elev is None:
                        elev = 0
                    lakeData.outPoint = (subbasin, newPointId, pt, elev)
                    # maximum number of steps approximates to the threshold for snapping points expressed as number of DEM cells
                    maxSteps = 5 if self.dx == 0  else int(snapThreshold / self.dx + 0.5)
                    lakeOutlet, found = QSWATTopology.movePointToPerimeter(pt, lakeGeom, gv.pFile, maxSteps)
                    if found:
                        if lakeData.outPoint[2] is not None:
                            QSWATUtils.information('User marked outlet {0} chosen as main outlet for lake {1}'.
                                                   format(pointId, lakeId), gv.isBatch, reportErrors=reportErrors)
                            if lakeData.outChLink >= 0:
                                lakeData.otherOutChLinks.add(lakeData.outChLink)
                        elev = QSWATTopology.valueAtPoint(lakeOutlet, demLayer)
                        if elev is None:
                            elev = 0
                        lakeData.outPoint = (subbasin, newPointId, lakeOutlet, elev)
                        QSWATUtils.loginfo('Outlet of lake {0} set to ({1}, {2})'.
                                           format(lakeId, int(lakeOutlet.x()), int(lakeOutlet.y())))
                        # update outlets map 
                        self.outlets[subbasin] = (pointId, lakeOutlet, chs) 
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
                lakeIn = self.chLinkIntoLake.get(link, 0)
                lakeOut = self.chLinkFromLake.get(link, 0)
                lakeWithin = self.chLinkInsideLake.get(link, 0)
                if link not in self.chLinkIntoLake and link not in self.chLinkFromLake and link not in self.chLinkInsideLake:
                    channelData = self.getReachData(channel, None)
                    assert channelData is not None
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
            # and dsNode negative (to avoid pulling a point inside the lake) make its channel internal
            outLinkId = -1
            outLink = lakeData.outChLink
            outBasin = -1
            dsOutLink = -1
            dsNodeOutLink = -1
            if outLink >= 0:
                exp = QgsExpression('"{0}" = {1}'.format(QSWATTopology._LINKNO, outLink))
                request = QgsFeatureRequest(exp)
                channel = list(channelsProvider.getFeatures(request))[0]
                outLinkId = channel.id()
                outBasin = channel[channelWSNOIndex]
                dsOutLink = channel[channelDsLinkIndex]
                dsNodeOutLink = channel[channelDsNodeIndex]
            if dsNodeOutLink < 0 and outBasin >= 0:
                # threshold in ha: LAKEOUTLETCHANNELAREA of lake area
                threshold = (lakeData.area / 1E6) * Parameters._LAKEOUTLETCHANNELAREA
                request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([chBasinsPolyIndex, chBasinsAreaIndex])
                for chBasinFeature in chBasinsProvider.getFeatures(request):
                    if chBasinFeature[chBasinsPolyIndex] == outBasin:
                        areaHa = chBasinFeature[chBasinsAreaIndex]
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
                            (_, _, outChannels) = self.outlets[subbasin]
                            if outLink in outChannels:
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
                QSWATUtils.error('Failed to find outlet for lake {0}'.format(lakeId), self.isBatch)
                errorCount += 1
            if lakeData.outChLink >= 0:
                chId = -1
                # find the channel's id
                exp = QgsExpression('"{0}" = {1}'.format(QSWATTopology._LINKNO, lakeData.outChLink))
                request = QgsFeatureRequest(exp)
                channel = list(channelsProvider.getFeatures(request))[0]
                chId = channel.id()
                lakeAttMap[chId][channelLakeMainIndex] = lakeId
            meanElevation = totalElevation / elevPointCount if elevPointCount > 0 else lakeData.outPoint[3]
            lakeData.elevation = meanElevation 
            QSWATUtils.loginfo('Lake {0} has outlet on channel {1}, other outlets on channels {2}, inlets on channels {3} and contains channels {4}'
                               .format(lakeId,  lakeData.outChLink, lakeData.otherOutChLinks, 
                                       list(lakeData.inChLinks.keys()), lakeData.lakeChLinks))
            OK = channelsProvider.changeAttributeValues(attMap)
            OK = OK and channelsProvider.changeAttributeValues(lakeAttMap)
            if not OK:
                QSWATUtils.error('Failed to update channel attributes in {0}'.format(gv.channelFile), self.isBatch)
                for err in channelsProvider.errors():
                    QSWATUtils.loginfo(err)
                return False
            self.lakesData[lakeId] = lakeData
            lakeArea = lakeData.area
            percentChBasinWater = chBasinWaterArea / lakeArea * 100
            QSWATUtils.loginfo('Lake {0} has area {1} and channel basin water area {2}: {3}%'.format(lakeId, lakeArea, chBasinWaterArea, percentChBasinWater))
            intPercent = int(percentChBasinWater + 0.5)
            if percentChBasinWater < 99 or percentChBasinWater > 101:
                QSWATUtils.information(u"""WARNING: Only {0}% of the area of lake {1} is accounted for in your watershed.
                You should carefully check the messages concerning this lake in the QSWAT+ log in the QGIS log messages panel."""
                                       .format(intPercent, lakeId), self.isBatch, reportErrors=reportErrors)
        if len(self.lakesData) == 0:
            QSWATUtils.error('No lakes found in {0}'.format(QSWATUtils.layerFilename(lakesLayer)), self.isBatch)
            return False
        chBasinsLayer.triggerRepaint()
        streamsLayer.triggerRepaint()
        channelsLayer.triggerRepaint()
        return errorCount == 0
    
    def addLakeFieldsToChannels(self, channelsLayer: QgsVectorLayer) -> None:
        """Add LakeIn etc fields to channelsLayer if necessary."""
        channelsProvider = channelsLayer.dataProvider()
        channelLakeInIndex = channelsProvider.fieldNameIndex(QSWATTopology._LAKEIN)
        channelLakeOutIndex = channelsProvider.fieldNameIndex(QSWATTopology._LAKEOUT)
        channelLakeWithinIndex = channelsProvider.fieldNameIndex(QSWATTopology._LAKEWITHIN)
        channelLakeMainIndex = channelsProvider.fieldNameIndex(QSWATTopology._LAKEMAIN)
        fields: List[QgsField] = []
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
                return
            channelsLayer.updateFields()
    
    def isWatershedOutlet(self, pointId: int, channelsProvider: QgsVectorDataProvider) -> bool:
        """Return true if there is a channel with dsNode equal to pointId and with dsLink -1."""
        DSLINKNO = QSWATTopology._DSLINKNO1 if self.isHUC else QSWATTopology._DSLINKNO
        channelDsLinkIndex = channelsProvider.fieldNameIndex(DSLINKNO)
        DSNODEID = QSWATTopology._DSNODEID1 if self.isHUC else QSWATTopology._DSNODEID
        exp = QgsExpression('"{0}" = {1}'.format(DSNODEID, pointId))
        request = QgsFeatureRequest(exp).setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([channelDsLinkIndex])
        for link in channelsProvider.getFeatures(request):
            if link[channelDsLinkIndex] == -1:
                return True
        return False
        
#     def isOutlet(self, pointId: int, outletsLayer: QgsVectorLayer) -> bool:
#         """Return true if outletsLayer contains an outlet point with id pointId."""
#         idIndex = self.getIndex(outletsLayer, QSWATTopology._ID, ignoreMissing=True)
#         inletIndex = self.getIndex(outletsLayer, QSWATTopology._INLET, ignoreMissing=True)
#         resIndex = self.getIndex(outletsLayer, QSWATTopology._RES, ignoreMissing=True)
#         if idIndex < 0 or inletIndex < 0 or resIndex < 0:
#             return False
#         exp = QgsExpression('"{0}" = {1}'.format(QSWATTopology._ID, pointId))
#         request = QgsFeatureRequest(exp).setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([inletIndex, resIndex])
#         for point in outletsLayer.dataProvider().getFeatures(request):
#             if point[inletIndex] == 0 and point[resIndex] == 0:
#                 return True
#         return False

    def addGridReservoirsPondsAndWetlands(self, gridLayer: QgsVectorLayer, channelsLayer: QgsVectorLayer, demLayer: QgsRasterLayer, 
                     gv: Any, reportErrors: bool=True) -> int: 
        """Add reservoir, pond and wetland lakes when using grid model.  Return number of lakes (which may be zero) or -1 if error.""" 
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
        # the drainage field may not exist if we are using grid or table drainage: deal with this later
        streamDrainageIndex = channelsProvider.fieldNameIndex(QSWATTopology._DRAINAGE)
        polysIntoLake: Dict[int, int] = dict()
        polysInsidelake: Dict[int, int] = dict()
        polysFromLake: Dict[int, int] = dict()
        self.chLinkIntoLake = dict()
        self.chLinkInsideLake = dict()
        self.chLinkFromLake = dict()
        request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([gridPolyIndex, gridLakeIdIndex])
        # first make map poly -> lake id
        polyToLake: Dict[int, int] = dict()
        for cell in gridProvider.getFeatures(request):
            try:
                lakeId = int(cell[gridLakeIdIndex])
                polyToLake[cell[gridPolyIndex]] = lakeId
                # make sure waterbody id is set to maximum lake id in case using existing grid
                self.waterBodyId = max(self.waterBodyId, lakeId)
            except:
                # lakeId was presumably null
                # QSWATUtils.loginfo('At polygonId {0} lakeId has type {1} and value {2}'.format(cell[gridPolyIndex], type(cell[gridLakeIdIndex]), cell[gridLakeIdIndex]))
                pass
        if len(polyToLake) == 0:
            # no lakes
            return 0
        # data for calculating centroid
        # map of lake id to (area, x moment of area, y moment)
        lakeAreaData: Dict[int, Tuple[int, float, float, float]] = dict()
        for cell in gridProvider.getFeatures():
            waterRole = cell[gridResIndex]
            poly = cell[gridPolyIndex]
            downPoly = cell[gridDownIndex]
            sourceLake = polyToLake.get(poly, None)
            targetLake = polyToLake.get(downPoly, None)
            if sourceLake is not None:
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
                    if targetLake is not None:
                        # also entry channel
                        polysIntoLake[poly] = targetLake
            elif targetLake is not None:
                polysIntoLake[poly] = targetLake
        totalElevation: Dict[int, float] = dict()
        # map of lake id to possible exit channels
        # will choose one with largest drainage
        exitData: Dict[int, Dict[int, Tuple[int, float, QgsPointXY, float]]] = dict()
        for lakeId, (waterRole, area, xMoment, yMoment) in lakeAreaData.items():
            centroid = QgsPointXY(float(xMoment) / area, float(yMoment) / area)
            self.lakesData[lakeId] = LakeData(area, area, centroid, waterRole)  # overridearea TODO:
            totalElevation[lakeId] = 0
            exitData[lakeId] = dict()
        # convert wsnos to links and complete LakesData
        # get maximum chLink and create downChannels map and link to basin map in case drainage needs calculating
        self.downChannels = dict()
        self.chLinkToChBasin = dict()
        maxChLink = 0
        for channel in channelsProvider.getFeatures():
            chLink: int = channel[channelLinkIndex]
            maxChLink = max(maxChLink, chLink)
            dsChLink = channel[channelDsLinkIndex]
            self.downChannels[chLink] = dsChLink
            wsno = channel[channelWSNOIndex]
            self.chLinkToChBasin[chLink] = wsno
            lakeIdInto = polysIntoLake.get(wsno, 0)
            if lakeIdInto > 0:
                self.chLinkIntoLake[chLink] = lakeIdInto
                # since this is a grid model the grid cells form different subbasins and there will be a suitable outlet
                # point already stored in the outlets map
                pointId, point, _ = self.outlets[wsno]
                elev = QSWATTopology.valueAtPoint(point, demLayer)
                if elev is None:
                    elev = 0
                self.lakesData[lakeIdInto].inChLinks[chLink] = (pointId, point, elev)
                totalElevation[lakeIdInto] += elev
                # if different lake cells abut, channel can be into one and from the other 
                # continue
            lakeIdFrom = polysFromLake.get(wsno, 0)
            if lakeIdFrom > 0:
                # allow for no drainage field
                drainage = -1 if streamDrainageIndex < 0 else channel[streamDrainageIndex]
                data = self.getReachData(channel, demLayer)
                if data is None:
                    QSWATUtils.loginfo('No reach data for channel link {0}'.format(chLink))
                else:
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
            # us parameter is set to None here because it is not yet calculated
            # and if there are any circularities they will be removed from the channels shapefile
            # and us will be calculated from that shapefile.
            self.setGridDrainageAreas(channelsLayer, gridLayer, maxChLink, None, gridCellArea)
        # count lakes with multiple outlets 
        multipleOutletCount = 0
        for data in exitData.values():
            if len(data) > 1:
                multipleOutletCount += 1 
        multipleOutletsInteractive = multipleOutletCount <= 5
        if not multipleOutletsInteractive:
            QSWATUtils.information(
                'For information on {0} lakes with multiple possible outlets see the QSWAT+ log'.
                format(multipleOutletCount), gv.isBatch, reportErrors=reportErrors)
        # find outlet with largest drainage and mark as THE outlet
        for lakeId, data in exitData.items():
            # set maxDrainage less than -1 value used for missing drainage so that first exit link registers
            # as if there is only one exit for each lake needDrainage will be false
            maxDrainage = -2.0 
            exLink = -1
            exWsno = -1
            exPoint = None
            exElev = 0.0
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
                # should be at least one internal channel.  Select an arbitrary one, since linked anyway.
                exLink = -1
                for chLink in self.lakesData[lakeId].lakeChLinks:
                    exLink = chLink
                    break
                if exLink < 0:
                    QSWATUtils.error('Failed to make outlet for lake {0}'.format(lakeId), gv.isBatch, reportErrors=reportErrors)
                    continue
                else:
                    # remove chLink from internal links
                    self.lakesData[lakeId].lakeChLinks.remove(exLink)
                    # remove from map of internal channels
                    del self.chLinkInsideLake[exLink]
                    # add as an exit
                    # first find the channel
                    exp = QgsExpression('"{0}" = {1}'.format(QSWATTopology._LINKNO, exLink))
                    channel = list(channelsProvider.getFeatures(QgsFeatureRequest(exp)))[0]
                    reachData = self.getReachData(channel, demLayer)
                    if reachData is None:
                        QSWATUtils.loginfo('No reach data for channel link {0}'.format(exLink))
                    else:
                        exWsno = channel[channelWSNOIndex]
                        drainage = float(self.drainAreas[exLink]) if streamDrainageIndex < 0 else float(channel[streamDrainageIndex])
                        exPoint = QgsPointXY(reachData.upperX, reachData.upperY)
                        exElev = reachData.upperZ
                        if math.isclose(exElev, gv.elevationNoData, rel_tol=1e-06):  # type: ignore
                            exElev = 0
                        data[exLink] = (exWsno, drainage, exPoint, exElev)
            others = list(data.keys())
            others.remove(exLink)
            if others != []:
                msg = """Warning: Stream link {0} chosen as main outlet for all of lake {1}.  
                        Other possible outlet stream links are {2}.""".format(exLink, lakeId, str([int(link) for link in others]))
                if multipleOutletsInteractive:
                    QSWATUtils.information(msg, gv.isBatch, reportErrors=reportErrors)
                else:
                    QSWATUtils.loginfo(msg)
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
    
    def addGridPlayas(self, lakesLayer: QgsVectorLayer, demLayer: QgsRasterLayer, gv: Any) -> None: 
        """Add playas to grid model."""
        lakeIdIndex = self.getIndex(lakesLayer, QSWATTopology._LAKEID)
        lakeResIndex = self.getIndex(lakesLayer, QSWATTopology._RES)
        if lakeResIndex < 0:
            # cannot be anything but reservoirs, so nothing to do
            return
        lakeAreaIndex = self.getIndex(lakesLayer, Parameters._AREA, ignoreMissing=True)
        areaFactor = gv.horizontalFactor * gv.horizontalFactor
        for lake in lakesLayer.getFeatures():
            waterRole = lake[lakeResIndex]
            if waterRole != QSWATTopology._PLAYATYPE:
                continue
            lakeGeom = lake.geometry()
            lakeId = int(lake[lakeIdIndex])
            lakeCentroid = lakeGeom.centroid().asPoint()
            lakeArea = lakeGeom.area() * areaFactor
            lakeOverrideArea = lakeArea
            if lakeAreaIndex >= 0:
                try:
                    lakeOverrideArea = float(lake[lakeAreaIndex]) * 1E4  # convert ha to m^2
                except:
                    pass
            lakeData = LakeData(lakeArea, lakeOverrideArea, lakeCentroid, waterRole)
            lakeData.elevation = QSWATTopology.valueAtPoint(lakeCentroid, demLayer)
            self.lakesData[lakeId] = lakeData
        
    
    def addExistingLakes(self, lakesLayer: QgsVectorLayer, channelsLayer: QgsVectorLayer, demLayer: QgsRasterLayer, 
                         gv: Any, reportErrors: bool=True) -> bool:
        """Add lakes data to existing non-grid model.
        
        We ignore DsNodeIds for inflowing and outflowing channels since these were
        probably only added previously to the snapped inlets/outlets file
        and inlets/outlets are little use in any case with existing watersheds."""
        
        lakeIdIndex = self.getIndex(lakesLayer, QSWATTopology._LAKEID)
        lakeResIndex = self.getIndex(lakesLayer, QSWATTopology._RES, ignoreMissing=True)
        if lakeResIndex < 0:
            QSWATUtils.information('No RES field in lakes shapefile {0}: assuming lakes are reservoirs'.
                                   format(QSWATUtils.layerFilename(lakesLayer)), self.isBatch)
        lakeAreaIndex = self.getIndex(lakesLayer, Parameters._AREA, ignoreMissing=True)
        channelLinkIndex = self.getIndex(channelsLayer, QSWATTopology._LINKNO)
        DSLINKNO = QSWATTopology._DSLINKNO1 if self.isHUC else QSWATTopology._DSLINKNO
        channelDsLinkIndex = self.getIndex(channelsLayer, DSLINKNO)
        channelBasinIndex = self.getIndex(channelsLayer, QSWATTopology._BASINNO)
        channelLakeInIndex = self.getIndex(channelsLayer, QSWATTopology._LAKEIN)
        channelLakeOutIndex = self.getIndex(channelsLayer, QSWATTopology._LAKEOUT)
        channelLakeWithinIndex = self.getIndex(channelsLayer, QSWATTopology._LAKEWITHIN)
        channelLakeMainIndex = self.getIndex(channelsLayer, QSWATTopology._LAKEMAIN)
        if lakeIdIndex < 0 or channelLinkIndex < 0 or channelDsLinkIndex < 0 or channelBasinIndex < 0 or \
            channelLakeInIndex < 0 or channelLakeOutIndex < 0 or channelLakeWithinIndex < 0 or channelLakeMainIndex < 0:
            return False
        self.lakesData = dict()
        areaFactor = gv.horizontalFactor * gv.horizontalFactor
        for lake in lakesLayer.getFeatures():
            lakeId = int(lake[lakeIdIndex])
            if lakeResIndex < 0:
                waterRole = QSWATTopology._RESTYPE
            else:
                waterRole = int(lake[lakeResIndex])
            if lakeId in self.lakesData:
                QSWATUtils.error('Lake identifier {0} occurs twice in {1}.  Lakes not added.'.format(lakeId, QSWATUtils.layerFilename(lakesLayer)), 
                                 gv.isBatch, reportErrors=reportErrors)
                self.lakesData = dict()
                return False
            # to stop reuse of the same water body id
            self.waterBodyId = max(self.waterBodyId, lakeId)
            geom = lake.geometry()
            area = geom.area() * areaFactor
            centroid = geom.centroid().asPoint()
            overrideArea = area
            if lakeAreaIndex >= 0:
                try:
                    overrideArea = float(lake[lakeAreaIndex]) * 1E4  # convert ha to m^2
                except:
                    pass
            self.lakesData[lakeId] = LakeData(area, overrideArea, centroid, waterRole)
        self.chLinkIntoLake = dict()
        self.chLinkInsideLake = dict()
        self.chLinkFromLake = dict()
        for channel in channelsLayer.getFeatures():
            chLink = channel[channelLinkIndex]
            dsLink = channel[channelDsLinkIndex]
            lakeIn = channel[channelLakeInIndex]
            lakeOut = channel[channelLakeOutIndex]
            lakeWithin = channel[channelLakeWithinIndex]
            lakeMain = channel[channelLakeMainIndex]
            reachData = None
            if lakeIn > 0:
                data = self.lakesData.get(lakeIn, None)
                if data is None:
                    QSWATUtils.error('Channel with LINKNO {0} flows into lake {1} not defined in {2}.  Lakes not added.'.
                                     format(chLink, lakeIn, QSWATUtils.layerFilename(lakesLayer)),
                                     gv.isBatch, reportErrors=reportErrors)
                    self.lakesData = dict()
                    return False
                if data.waterRole == QSWATTopology._PLAYATYPE:
                    QSWATUtils.information('Channel with LINKNO {0} flows into {1} lake {2}.  This is ignored.'.
                                           format(chLink, QSWATTopology.lakeCategory(data.waterRole), lakeIn), 
                                           gv.isBatch, reportErrors=reportErrors)
                else:
                    reachData = self.getReachData(channel, demLayer)
                    assert reachData is not None
                    point = QgsPointXY(reachData.lowerX, reachData.lowerY)
                    elev = reachData.lowerZ
                    data.elevation += elev
                    self.pointId += 1
                    data.inChLinks[chLink] = (self.pointId, point, elev)
                    self.chLinkIntoLake[chLink] = lakeIn
            elif lakeWithin > 0:
                data = self.lakesData.get(lakeWithin, None)
                if data is None:
                    QSWATUtils.error('Channel with LINKNO {0} inside lake {1} not defined in {2}.  Lakes not added.'.
                                     format(chLink, lakeWithin, QSWATUtils.layerFilename(lakesLayer)),
                                     gv.isBatch, reportErrors=reportErrors)
                    self.lakesData = dict()
                    return False
                if data.waterRole == QSWATTopology._PLAYATYPE:
                    QSWATUtils.information('Channel with LINKNO {0} inside {1} lake {2}.  This is ignored.'.
                                           format(chLink, QSWATTopology.lakeCategory(data.waterRole), lakeIn), 
                                           gv.isBatch, reportErrors=reportErrors)
                else:
                    data.lakeChLinks.add(chLink)
                    self.chLinkInsideLake[chLink] = lakeWithin
                    if dsLink < 0:
                        # watershed outlet
                        reachData = self.getReachData(channel, demLayer)
                        assert reachData is not None
                        subbasin = channel[channelBasinIndex]
                        data.outChLink = -1
                        point = QgsPointXY(reachData.lowerX, reachData.lowerY)
                        elev = reachData.lowerZ
                        self.pointId += 1
                        data.outPoint = (subbasin, self.pointId, point, elev)
                        self.outletsInLake[subbasin] = lakeWithin
            if lakeOut > 0:
                data = self.lakesData.get(lakeOut, None)
                if data is None:
                    QSWATUtils.error('Channel with LINKNO {0} flows out of lake {1} not defined in {2}.  Lakes not added.'.
                                     format(chLink, lakeOut, QSWATUtils.layerFilename(lakesLayer)),
                                     gv.isBatch, reportErrors=reportErrors)
                    self.lakesData = dict()
                    return False
                if data.waterRole == QSWATTopology._PLAYATYPE:
                    QSWATUtils.information('Channel with LINKNO {0} flows out of {1} lake {2}.  This is ignored.'.
                                           format(chLink, QSWATTopology.lakeCategory(data.waterRole), lakeIn), 
                                           gv.isBatch, reportErrors=reportErrors)
                else:
                    if lakeMain == lakeOut:
                        # lake's main outlet
                        # channel leaves lake at upper end
                        reachData = self.getReachData(channel, demLayer)
                        assert reachData is not None
                        subbasin = channel[channelBasinIndex]
                        data.outChLink = chLink
                        elev = reachData.upperZ
                        self.pointId += 1
                        point = QgsPointXY(reachData.upperX, reachData.upperY)
                        QSWATUtils.loginfo('Added point {0} for channel link {1} flowing from lake {2}'.format(self.pointId, chLink, lakeOut))
                        data.outPoint = (subbasin, self.pointId, point, elev)
                        self.chLinkFromLake[chLink] = lakeOut
                    else:
                        # other outlet
                        data.otherOutChLinks.add(chLink)
        # define lake elevation
        for data in self.lakesData.values():
            if data.waterRole == QSWATTopology._PLAYATYPE:
                data.elevation = QSWATTopology.valueAtPoint(data.centroid, demLayer)
            else:
                numInflows = len(data.inChLinks)
                data.elevation = data.outPoint[3] if numInflows == 0 else float(data.elevation) / numInflows
        return True
                    
    def isLakeInletOrOutlet(self, chLink: int) -> bool:
        for lakeData in self.lakesData.values():
            if lakeData.waterRole == QSWATTopology._PLAYATYPE:
                continue
            if chLink in lakeData.inChLinks or chLink == lakeData.outChLink or chLink in lakeData.otherOutChLinks:
                return True
        return False

    @staticmethod
    def intersectsPoly(geom: QgsGeometry, polyGeom: QgsGeometry, polyRect: QgsRectangle) -> bool:
        """Returns true if any part of geom intersects any part of polyGeom, or geom is within polyGeom. polyGeom has associated rectangle polyRect."""
        geoRect = geom.boundingBox()
        if QSWATTopology.disjointBoxes(geoRect, polyRect):
            return False
        else:
            return not geom.disjoint(polyGeom) # geom.overlaps(polyGeom) or geom.within(polyGeom) or polyGeom.within(geom)
        
    @staticmethod
    def disjointBoxes(box1: QgsRectangle, box2: QgsRectangle) -> bool:
        """Return True if the boxes are disjoint."""
        return box1.xMinimum() > box2.xMaximum() or \
            box1.xMaximum() < box2.xMinimum() or \
            box1.yMinimum() > box2.yMaximum() or \
            box1.yMaximum() < box2.yMinimum()
        
    @staticmethod
    def polyContains(point: QgsPointXY, polyGeom: QgsGeometry, polyRect: QgsRectangle) -> bool:
        """Return true if point within polyGeom, which has associated rectangle polyRect."""
        if polyRect.xMinimum() < point.x() < polyRect.xMaximum() and \
            polyRect.yMinimum() < point.y() < polyRect.yMaximum():
            return polyGeom.contains(point)
        else:
            return False
            
    def saveLakesData(self, db: DBUtils) -> None: 
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
                point = lakeData.outPoint[2]
                if point is None:
                    if lakeData.waterRole in {QSWATTopology._RESTYPE, QSWATTopology._PONDTYPE, QSWATTopology._WETLANDTYPE}:
                        QSWATUtils.loginfo('No outpoint for lake {0}'.format(lakeId))
                    x = 0
                    y = 0
                else:
                    x = lakeData.outPoint[2].x()
                    y = lakeData.outPoint[2].y()
                curs.execute(db._INSERTLAKESDATA, (lakeId, lakeData.outPoint[0], lakeData.waterRole, lakeData.area, 
                                                   lakeData.overrideArea, lakeData.elevation, lakeData.outChLink,
                                                   lakeData.outPoint[1], x, y,
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
                                 
    def readLakesData(self, db: DBUtils) -> bool:
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
                    lakeId = int(lakeRow['id'])
                    self.waterBodyId = max(self.waterBodyId, lakeId)
                    self.lakesData[lakeId] = LakeData(lakeRow['area'], lakeRow['overridearea'], QgsPointXY(lakeRow['centroidx'], lakeRow['centroidy']), lakeRow['role'])
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
    
    def getDownChannel(self, channel: int) -> int:
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
    
    def setChannelBasinAreas(self, gv: Any) -> None:
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
                        if val in self.chBasinAreas:
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
                
    @staticmethod
    def copyBasinAreas(areas: Dict[int, float]) -> Dict[int, float]:
        """Return copy of areas."""
        areas2 = dict()
        for i, val in areas.items():
            areas2[i] = val
        return areas2
            
    def checkAreas(self, subbasinsLayer: QgsVectorLayer, gv: Any) -> bool:
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
            totalBasinsArea = 0.0
            totalChannelBasinsArea = 0.0
            # one percent test: using 1 pixel test instead
#             def compare(x, y): # return true if both zero or difference < 1% of x
#                 if x == 0:
#                     return y == 0
#                 else:
#                     return abs(x - y) < 0.01 * x
            areaFactor = gv.horizontalFactor * gv.horizontalFactor
            for poly in subbasinsLayer.getFeatures():
                if areaIndex < 0:
                    basinArea = poly.geometry().area() * areaFactor
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
                area = 0.0
                for chBasin, chArea in self.chBasinAreas.items():
                    if chBasin in chBasins:
                        area += chArea
                if abs(basinArea - area) >= unitArea: # not using compare(basinArea, area):
                    SWATChannels = {self.channelToSWATChannel[chLink] for chLink in chLinks}
                    SWATBasin = self.subbasinToSWATBasin[basin]
                    QSWATUtils.error('Basin {0} with area {1} has channels {2} with total area {3}'.
                                     format(SWATBasin, basinArea, SWATChannels, area), gv.isBatch)
                    # return true so run continue if user regards error as small
                    return True
            # now compare areas for whole watershed
            for _, chArea in self.chBasinAreas.items():
                totalChannelBasinsArea += chArea
            if abs(totalBasinsArea - totalChannelBasinsArea) >= unitArea: # not using compare(totalBasinsArea, totalChannelBasinsArea):
                QSWATUtils.error('Watershed area is {0} by adding subbasin areas and {1} by adding channel basin areas'.
                                 format(totalBasinsArea, totalChannelBasinsArea), gv.isBatch)
                # return true so run continue if user regards error as small
                return True
            QSWATUtils.loginfo('Total watershed area is {0}'.format(totalBasinsArea))
        return True
    
    @staticmethod
    def reachable(chLink: int, chLinks: List[int], us: Dict[int, List[int]]) -> bool:
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
                    
    def setDrainageFromChannels(self, channelLayer: QgsVectorLayer, drainAreaIndex: int) -> None:
        """Get drain areas from channelLayer file's DS_Cont_Ar attribute."""
        inds = [self.channelIndex, drainAreaIndex]
        areaFactor = self.horizontalFactor * self.horizontalFactor
        request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes(inds)
        for reach in channelLayer.getFeatures(request):
            channelLink = reach[self.channelIndex]
            self.drainAreas[channelLink] = reach[drainAreaIndex] * areaFactor
                    
    def setGridDrainageFromChannels(self, channelLayer: QgsVectorLayer, subbasinsLayer: QgsVectorLayer, maxChLink: int, us: Dict[int, List[int]]) -> bool: 
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
        self.checkDrainage(channelLayer, subbasinsLayer, maxChLink, us, False)
        return True
               
    def setGridDrainageAreas(self, channelLayer: QgsVectorLayer, subbasinsLayer: QgsVectorLayer, maxChLink: int, us: Optional[Dict[int, List[int]]], gridCellArea: float) -> None:
        """Calculate and save grid drain areas in sq km."""
        # check to see if drain areas already calculated - may have been done with lakes
        if self.drainAreas is None:
            return
        for link in self.downChannels.keys():
            if self.drainAreas[link] > gridCellArea:
                return
        self.drainAreas.fill(gridCellArea)
        self.checkDrainage(channelLayer, subbasinsLayer, maxChLink, us, True)
        
    def checkDrainage(self, channelLayer: QgsVectorLayer, subbasinsLayer: QgsVectorLayer, maxChLink: int, us: Optional[Dict[int, List[int]]], needDrainage: bool) -> None:
        """Check drainage as defined by downChannels map is not circular: attempt to fix if so.  Also calculate drainage in 
        self.drainAreas if needDrainage is true.  If so, assume it is initialised with area of grid cell.
        
        Only used in grid models.
        Changes the channel and the grid shapefiles, plus the downChannels and downSubbasins mappings, plus the upchannel map us if not None."""
        # number of incoming links for each link
        incount: ndarray[int] = zeros((maxChLink + 1), dtype=int)
        for dsLink in self.downChannels.values():
            if dsLink >= 0:
                incount[dsLink] += 1  # type: ignore
        # queue contains all links whose drainage areas have been calculated 
        # i.e. will not increase and can be propagated
        queue = [link for link in range(maxChLink + 1) if incount[link] == 0]
        while queue:
            link = queue.pop(0)
            dsLink = self.downChannels.get(link, -1)
            if dsLink >= 0:
                if needDrainage:
                    self.drainAreas[dsLink] += self.drainAreas[link]
                incount[dsLink] -= 1  # type: ignore
                if incount[dsLink] == 0:
                    queue.append(dsLink)
        # incount values should now all be zero
        remainder = [link for link in range(maxChLink + 1) if incount[link] > 0]
        if remainder:
            QSWATUtils.loginfo('Drainage areas incomplete.  There is a circularity in links {0!s}'.format(remainder))
            # remainder may contain a number of circles.
            rings: List[List[int]] = []
            nextRing: List[int] = []
            link = remainder.pop(0)
            while True:
                nextRing.append(link)
                dsLink = self.downChannels[link]
                if dsLink in nextRing:
                    # complete the ring
                    nextRing.append(dsLink)
                    rings.append(nextRing)
                    if remainder:
                        nextRing = []
                        link = remainder.pop(0)
                    else:
                        break
                else:
                    # continue
                    remainder.remove(dsLink)
                    link = dsLink
            numRings = len(rings)
            if numRings > 0:
                channelMap: Dict[int, Dict[int, int]] = dict()
                polyMap: Dict[int, Dict[int, int]] = dict()
                channelProvider = channelLayer.dataProvider()
                linkIndex = channelProvider.fieldNameIndex(QSWATTopology._LINKNO)
                DSLINKNO = QSWATTopology._DSLINKNO1 if self.isHUC else QSWATTopology._DSLINKNO
                dsLinkIndex = channelProvider.fieldNameIndex(DSLINKNO)
                subProvider = subbasinsLayer.dataProvider()
                dsPolyIndex = subProvider.fieldNameIndex(QSWATTopology._DOWNID)
                QSWATUtils.information('Drainage areas incomplete.  There are {0} circularities.  Will try to remove them.  See the QSWAT+ log for details'.
                                 format(numRings), self.isBatch)
                for ring in rings:
                    QSWATUtils.loginfo('Circularity in links {0!s}'.format(ring))
                    # fix the circularity by making the largest drainage link an exit in the downChannels map
                    maxDrainage = 0
                    maxLink = -1
                    for link in ring:
                        drainage = self.drainAreas[link]
                        if drainage > maxDrainage:
                            maxLink = link
                            maxDrainage = drainage
                    if maxLink < 0:
                        QSWATUtils.error('Failed to find link with largest drainage in circle {0!s}'.format(ring), self.isBatch)
                    else:
                        self.downChannels[maxLink] = -1
                        linkExpr = QgsExpression('"{0}" = {1}'.format(QSWATTopology._LINKNO, maxLink))
                        linkRequest = QgsFeatureRequest(linkExpr).setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([linkIndex, dsLinkIndex])
                        for feature in channelProvider.getFeatures(linkRequest):
                            channelMap[feature.id()] = {dsLinkIndex: -1}
                            if us is not None:
                                link = feature[linkIndex]
                                dsLink = feature[dsLinkIndex]
                                us[dsLink].remove(link)
                        # also need to fix downSubbasins map
                        # subbasin same as chBasin since grid model
                        basin = self.chLinkToChBasin[maxLink]
                        self.downSubbasins[basin] = -1
                        polyExpr = QgsExpression('"{0}" = {1}'.format(QSWATTopology._POLYGONID, basin))
                        polyRequest = QgsFeatureRequest(polyExpr).setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([])
                        for feature in subProvider.getFeatures(polyRequest):
                            polyMap[feature.id()] = {dsPolyIndex: -1}
                        QSWATUtils.loginfo('Link {0} and polygon {1} made into an exit'.format(maxLink, basin))
                        # if there is a lake with the exit link internal to it we should make it the lake outlet
                        lakeId = self.chLinkInsideLake.get(maxLink, -1)
                        if lakeId > 0:
                            lakeData = self.lakesData[lakeId]
                            if lakeData.outChLink >= 0:
                                # add old outlet to other outlets
                                oldOutLink = lakeData.outChLink
                                lakeData.otherOutChLinks.add(oldOutLink)
                                # change maxLink from internal to outlet
                                lakeData.lakeChLinks.remove(maxLink)
                                lakeData.outChLink = maxLink
                                QSWATUtils.loginfo('Outlet of lake {0} changed from link {1} to link {2}'.
                                                   format(lakeId, oldOutLink, maxLink))
                                self.chLinkFromLake[maxLink] = lakeId
                                del self.chLinkInsideLake[maxLink]
                        # and if the channel flows into a lake we should remove it from the lake's inlets
                        lakeId = self.chLinkIntoLake.get(maxLink, -1)
                        if lakeId > 0:
                            lakeData = self.lakesData[lakeId]
                            del lakeData.inChLinks[maxLink]
                            del self.chLinkIntoLake[maxLink]
                channelProvider.changeAttributeValues(channelMap)
                subProvider.changeAttributeValues(polyMap)
            
    def setDrainageAreas(self, us: Dict[int, List[int]]) -> None:
        """
        Calculate and save drainAreas.
        
        Not used with grid models.
        """
        for chLink, chBasin in self.chLinkToChBasin.items():
            self.setLinkDrainageArea(chLink, chBasin, us)
                
    def setLinkDrainageArea(self, chLink: int, chBasin: int, us: Dict[int, List[int]]) -> None:
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
        
    def setStrahlerFromChannels(self, channelLayer: QgsVectorLayer, orderIndex: int) -> None:
        """Get Strahler order from channelLayer file's order attribute."""
        inds: List[int] = [self.channelIndex, orderIndex]
        request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes(inds)
        for reach in channelLayer.getFeatures(request):
            channelLink = reach[self.channelIndex]
            self.strahler[channelLink] = reach[orderIndex]
            
    def setStrahler(self, us: Dict[int, List[int]]) -> None:
        """Set Strahler orders using upstream map from each outlet.
        
        Not used with grid models"""
        
        def setStrahlerLink(link: int) -> int:
            """Recursively set Strahler order for link and those upstream from it."""
            ups = us.get(link, [])
            if ups == []:
                self.strahler[link] = 1
                return 1
            orders = [setStrahlerLink(up) for up in ups]
            omax = max(orders)
            count = len([o for o in orders if o == omax])
            order = omax if count == 1 else omax+1
            self.strahler[link] = order
            return order
        
        for _,_,links in self.outlets.values():
            for link in links:
                setStrahlerLink(link)
        pass
            
    def setStrahlerFromGrid(self, us: Dict[int, List[int]]) -> None:
        """Set Strahler orders for channels using upstream map us.
        
        Non-recusive as used in grid models."""
        # continue looping as long as an order is calculated
        changed = True
        while changed:
            changed = False
            for link in self.downChannels.keys():
                if self.strahler[link] > 0:
                    # already calculated
                    continue
                else:
                    ups = us.get(link, [])
                    if ups == []:
                        self.strahler[link] = 1
                        changed = True
                    else:
                        orders = [self.strahler[up] for up in ups]
                        if 0 in orders:
                            # at least one yet to be calculated
                            continue
                        else:
                            omax = max(orders)
                            count = len([o for o in orders if o == omax])
                            order = omax if count == 1 else omax+1
                            self.strahler[link] = order
                            changed = True
            
    def getDistanceToJoin(self, basin: int, otherBasin: int) -> float:
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
        
    def distanceToJoin(self, start: int, otherLink: int) -> float:
        """
        Return distance in metres from outlet of link start to point of confluence with
        flow from otherLink, or to Outlet if no confluence.
        """
        return sum([self.streamLengths[link] for link in self.pathFromJoin(start, otherLink)])
        
    def pathFromJoin(self, start: int, otherLink: int) -> List[int]:
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
        
    def pathFromOutlet(self, start: int) -> List[int]:
        """List of links downstream of start, in upstream order."""
        result: List[int] = []
        nxt = start
        while True:
            nxt = self.downStreams.get(nxt, -1)
            if nxt == -1:
                break
            result = [nxt] + result
        return result
    
    def removeCommonPrefix(self, path1: List[int], path2: List[int]) -> List[int]:
        """Remove from the beginning of path1 the longest sequence that starts path2."""
        i = 0
        while i < len(path1) and i < len(path2):
            if path1[i]  == path2[i]:
                i += 1
            else:
                break
        return path1[i:]
        
    def addBasinsToChannelFile(self, channelLayer: QgsVectorLayer, wStreamFile: str) -> None:
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
        wNoData = wLayer.dataProvider().sourceNoDataValue(1)
        lenIdx = self.getIndex(channelLayer, QSWATTopology._LENGTH, ignoreMissing=True)
        chsMap: Dict[int, Dict[int, int]] = dict()
        for feature in provider.getFeatures():
            # find a point well into the channel to ensure we are not just outside the basin
            geometry = feature.geometry()
            if lenIdx < 0:
                length = geometry.length() * self.horizontalFactor
            else:
                length = feature[lenIdx] * self.horizontalFactor
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
                wVal = QSWATTopology.valueAtPoint(point, wLayer)
                if wVal is None or math.isclose(wVal, wNoData, rel_tol=1e-06):  # type: ignore # outside watershed  
                    basin = -1
                else:
                    basin = cast(int, wVal)
            fid = feature.id()
            chsMap[fid] = dict()
            chsMap[fid][bsnIdx] = basin
        OK = provider.changeAttributeValues(chsMap)
        if not OK:
            QSWATUtils.error('Cannot add basin values to channels shapefile', self.isBatch)
        return
    
    def writeDrainageFile(self, drainageFile: str) -> None: 
        """Write drainage csv file."""
        if os.path.exists(drainageFile):
            os.remove(drainageFile)
        with open(drainageFile, 'w', newline='') as connFile:
            writer = csv.writer(connFile)
            writer.writerow(['PolygonId', 'DownId'])
            for subbasin, downSubbasin in self.downSubbasins.items():
                writer.writerow([str(subbasin), str(downSubbasin)])
        
    def getReachData(self, reach: QgsFeature, demLayer: Optional[QgsRasterLayer]) -> Optional[ReachData]:
        """
        Generate ReachData record for reach geometry.  demLayer may be none, or point may give nodata for elevation, in which case elevations are set zero.
        """
        if self.isHUC:
            wsno = reach[self.wsnoIndex]
            pStart = self.chPointSources[wsno][1]
            pFinish = self.chOutlets[wsno][1]
        else:
            geom = reach.geometry()
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
            startVal: Optional[float] = 0.0
            finishVal: Optional[float] = 0.0
        else:
            startVal = QSWATTopology.valueAtPoint(pStart, demLayer)
            finishVal = QSWATTopology.valueAtPoint(pFinish, demLayer)
            # with grid models centre of cell at edage can have no data for elevation
            if startVal is None:
                startVal = 0.0
            if finishVal is None:
                finishVal = 0.0
        assert startVal is not None
        assert finishVal is not None
        if self.outletAtStart:
            maxElev = finishVal * self.verticalFactor
            minElev = startVal * self.verticalFactor
            return ReachData(pFinish.x(), pFinish.y(), maxElev, pStart.x(), pStart.y(), minElev)
        else:
            minElev = finishVal * self.verticalFactor
            maxElev = startVal * self.verticalFactor
            return ReachData(pStart.x(), pStart.y(), maxElev, pFinish.x(), pFinish.y(), minElev)
    
    @staticmethod
    def gridReachLength(data: ReachData) -> float:
        """Length of reach assuming it is a single straight line."""
        dx = data.upperX - data.lowerX
        dy = data.upperY - data.lowerY
        return math.sqrt(dx * dx + dy * dy)  # type: ignore

    def tryBasinAsSWATBasin(self, subbasinsLayer: QgsVectorLayer, polyIndex: int, subbasinIndex: int, useGridModel: bool) -> bool:
        """Return true if the subbasin field values can be used as SWAT basin numbers.
        
        The basin numbers, if any, can be used if they 
        are all positive and different.
        Also populate subbasinToSWATBasin and SWATBasinToSubbasin if successful, else these are undetermined.
        """
        assert polyIndex >= 0 and subbasinIndex >= 0 and len(self.subbasinToSWATBasin) == 0 and len(self.SWATBasinToSubbasin) == 0
        SWATBasins: Set[int] = set()
        request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([polyIndex, subbasinIndex])
        for polygon in subbasinsLayer.getFeatures(request):
            subbasin = polygon[polyIndex]
            if subbasin in self.upstreamFromInlets or not (useGridModel or subbasin in self.chBasinToSubbasin.values()):  # removed by chBasin being within a lake
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
    def makePositiveOutletIds(outletLayer: QgsVectorLayer) -> int:
        """Add PointId field if necessary and set to id or largest id + 1 if id is zero.  Return index of PointId."""
        outletProvider = outletLayer.dataProvider()
        ptIdIndex = outletProvider.fieldNameIndex(QSWATTopology._POINTID)
        if ptIdIndex < 0:
            outletProvider.addAttributes([QgsField(QSWATTopology._POINTID, QVariant.Int)])
            outletLayer.updateFields()
            ptIdIndex = outletProvider.fieldNameIndex(QSWATTopology._POINTID)
        idIndex = outletProvider.fieldNameIndex(QSWATTopology._ID)
        maxId = 0
        zeroId = -1
        request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([idIndex, ptIdIndex])
        mmap: Dict[int, Dict[int, int]] = dict()
        for point in outletProvider.getFeatures(request):
            pid = point.id()
            pointId = point[idIndex]
            if pointId == 0:
                zeroId = pid
            else:
                mmap[pid] = {ptIdIndex: pointId}
                maxId = max(maxId, pointId)
        if zeroId >= 0:
            mmap[zeroId] = {ptIdIndex: maxId + 1}
        if outletProvider.changeAttributeValues(mmap):
            return ptIdIndex
        else:
            return -1
 
    @staticmethod
    def snapPointToReach(streamLayer: QgsVectorLayer, point: QgsPointXY, threshold: float, transform: Dict[int, float], isBatch: bool) -> Optional[QgsPointXY]:
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
    def withinPixels(numPixels: int, p1: QgsPointXY, p2: QgsPointXY, transform: Dict[int, float]) -> bool:
        """Return true if points not separated by more than numPixels pixels."""
        col1, row1 = QSWATTopology.projToCell(p1.x(), p1.y(), transform)
        col2, row2 = QSWATTopology.projToCell(p2.x(), p2.y(), transform)
        return abs(col1 - col2) <= numPixels and abs(row1 - row2) <= numPixels
        
    @staticmethod
    def separatePoints(p1: QgsPointXY, p2: QgsPointXY, transform: Dict[int, float]) -> QgsPointXY:
        """If p2 is in same cell as p1 return a point in the next cell in the direction of p1 to p2.
        Else return p2."""
        # p1 is the end of a channel, so will be in the centre of a cell.  So enough
        # to move one coordinate of p2 by one cell from p1, and the other proportionately but less
        if QSWATTopology.withinPixels(0, p1, p2, transform):
            return QSWATTopology.shiftedPoint(p1, p2, transform, 1.0)
        else:
            return p2
        
    @staticmethod
    def shiftedPoint(p1: QgsPointXY, p2: QgsPointXY, transform: Dict[int, float], frac: float) -> QgsPointXY:
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
            shiftx = 0.0
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
    def nearestVertex(streamLayer: QgsVectorLayer, point: QgsPointXY) -> Tuple[List[QgsPointXY], int]:
        """Find nearest vertex in streamLayer to point and 
        return the line (list of points) in the reach and 
        index of the vertex within the line.
        """
        bestPointIndex = -1
        bestLine: List[QgsPointXY] = []
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
    def intercepts(line: List[QgsPointXY], pointIndex: int, point: QgsPointXY) -> Tuple[Optional[QgsPointXY], Optional[QgsPointXY]]:
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
    def getIntercept(p1: QgsPointXY, p2: QgsPointXY, p: QgsPointXY) -> Optional[QgsPointXY]:
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
            return QgsPointXY(x1 - prop * X, y1 - prop * Y)
        
    @staticmethod
    def nearer(p1: Optional[QgsPointXY], p2: Optional[QgsPointXY], p: QgsPointXY) -> Optional[QgsPointXY]:
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
    def distanceMeasure(p1: QgsPointXY, p2: QgsPointXY) -> float:
        """Return square of distance between p1 and p2."""
        dx = p1.x() - p2.x()
        dy = p1.y() - p2.y()
        return dx * dx + dy * dy
    
    def setMaxFlowLengths(self) -> None:
        """
        Write table of subbasin to maximum flow length along channels within the basin.
        
        Used for maximum flow path for existing non-grid models, and only defined for these.
        """
        channelFlowLengths: Dict[int, float] = dict()
        for chLink, length in self.channelLengths.items():
            self.setChannelFlowLength(chLink, length, channelFlowLengths)
            
    def setChannelFlowLength(self, chLink: int, length: float, channelFlowLengths: Dict[int, float]) -> None:
        """Add entry for chLink to channelFlowLengths map.  Also update maxFlowLengths for chLink's subbasin.
        
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
        
                    
    def writePointsTable(self, demLayer: QgsRasterLayer, mergees: List[int], useGridModel: bool, existingWshed: bool) -> None:
        """Write the gis_points table in the project database."""
        assert isinstance(self.db, DBUtils)
        with self.db.conn as conn:
            if not conn:
                return
            curs = conn.cursor()
            table = 'gis_points'
            clearSQL = 'DROP TABLE IF EXISTS ' + table
            curs.execute(clearSQL)
            curs.execute(self.db._POINTSCREATESQL)
            waterAdded: List[int] = []
            # Add outlets from streams
            for subbasin, (pointId, pt, _) in self.outlets.items():
                if subbasin in self.upstreamFromInlets:
                    continue # excluded
                elev = QSWATTopology.valueAtPoint(pt, demLayer)
                if elev is None:
                    elev = 0
                self.addPoint(curs, subbasin, pointId, pt, elev, 'O')
            # Add inlets
            if useGridModel:
                for chLink, (pointId, pt) in self.chLinkToInlet.items():
                    if chLink in self.chLinkInsideLake or chLink in self.chLinkFromLake:  # shouldn't happen
                        continue
                    subbasin = self.chLinkToChBasin[chLink]
                    elev = QSWATTopology.valueAtPoint(pt, demLayer)
                    if elev is None:
                        elev = 0
                    self.addPoint(curs, subbasin, pointId, pt, elev, 'I')
            else:
                for subbasin, (pointId, pt) in self.inlets.items():
                    if subbasin in self.upstreamFromInlets: 
                    # shouldn't happen, but users can be stupid
                        continue
                    elev = QSWATTopology.valueAtPoint(pt, demLayer)
                    if elev is None:
                        elev = 0
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
                if elev is None:
                    elev = 0
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
                if elev is None:
                    elev = 0
                self.addPoint(curs, subbasin, pointId, pt, elev, 'P')
            # Add lakes
            for lake in self.lakesData.values():
                if lake.waterRole in {QSWATTopology._RESTYPE, QSWATTopology._PONDTYPE, QSWATTopology._WETLANDTYPE}:
                    # outlet from lake
                    subbasin, pointId, pt, elev = lake.outPoint
                    assert elev is not None
                    chLink = lake.outChLink
                    # unnecessary as will be in self.outlets
                    #if not useGridModel and chLink == -1:
                    #    # main outlet was moved inside lake, but reservoir point will still be routed to it
                    #    # so add its definition
                    #    (outletId, outPt, _) = self.outlets[subbasin]
                    #    self.addPoint(curs, subbasin, outletId, outPt, elev, 'O')
                    self.addPoint(curs, subbasin, pointId, pt, elev, 'W')
                    waterAdded.append(pointId)
                    # inlets to lake.  These are outlets from streams in grid models, so not necessary
                    if not useGridModel:
                        for chLink, (pointId, pt, elev) in lake.inChLinks.items():
                            chBasin = self.chLinkToChBasin[chLink]
                            subbasin = self.chBasinToSubbasin[chBasin]
                            assert elev is not None
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
                if elev is None:
                    elev = 0
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
                if elev is None:
                    elev = 0
                self.addPoint(curs, subbasin, pointId, pt, elev, 'W')
#             for subbasin, (pointId, pt) in self.extraReservoirs.iteritems():
#                 if subbasin in self.upstreamFromInlets: 
#                 # shouldn't happen, but users can be stupid
#                     continue
#                 elev = QSWATTopology.valueAtPoint(pt, demLayer)
#                 self.addPoint(curs, subbasin, pointId, pt, elev, 'R')
            conn.commit()
            
    def addExtraPointsToPointsTable(self, extraPoints: List[Tuple[int, int]], useGridModel: bool) -> None:
        """Add extra points needed to mark where channels drain into reservoirs."""
        assert isinstance(self.db, DBUtils)
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
            
    def addPoint(self, cursor: Any, subbasin: int, pointId: int, pt: QgsPointXY, elev: float, typ: str)-> None:
        """Add point to gis_points table."""
        table = 'gis_points'
        SWATBasin = self.subbasinToSWATBasin.get(subbasin, 0)
        # include points without SWAT basin since points within lakes may not have one
        #if SWATBasin == 0:
        #    return
        ptll = self.pointToLatLong(pt)
        sql = "INSERT INTO " + table + " VALUES(?,?,?,?,?,?,?,?)"
        try:
            cursor.execute(sql, (pointId, SWATBasin, typ,
                           pt.x(), pt.y(), ptll.y(), ptll.x(), elev))
            assert isinstance(self.db, DBUtils)
            self.db.addKey(table, pointId)
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
    
    def writeChannelsTable(self, mergeChannels: Dict[int, int], basins: Dict[int, BasinData], gv: Any) -> Optional[QgsVectorLayer]:
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
            return None
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
            targets: List[int] = []
            for reach in provider1.getFeatures(request):
                for channel in mergeChannels.keys():
                    target = self.finalTarget(channel, mergeChannels)
                    if target not in targets:
                        targets.append(target)
                    if reach[chLinkIdx] == target:
                        merges[channel] = reach
                        #QSWATUtils.loginfo('Channel {0} merging to target {1} with length {2}'.format(channel, target, reach.geometry().length()))
            # create geometries for merged reaches
            merged: List[int] = []
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
            mergers: List[QgsFeature] = []
            for channel, reach in merges.items():
                if reach not in mergers:
                    mergers.append(reach)
            provider1.addFeatures(mergers)
        chsMap: Dict[int, Dict[int, int]] = dict()
        zeroRids: List[int] = []
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
            self.removeFields(rivs1Layer, [QSWATTopology._LINKNO, QSWATTopology._CHANNEL, QSWATTopology._CHANNELR, QSWATTopology._SUBBASIN], rivs1File, self.isBatch)
        if addToRiv1:
            fields = []
            fields.append(QgsField(QSWATTopology._AREAC, QVariant.Double, len=20, prec=0))
            fields.append(QgsField(QSWATTopology._ORDER, QVariant.Int))
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
            orderIdx = self.getIndex(rivs1Layer, QSWATTopology._ORDER)
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
            mmap: Dict[int, Dict[int, Union[int, float]]] = dict()
        assert isinstance(self.db, DBUtils)
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
            sql = "INSERT INTO " + table + " VALUES(?,?,?,?,?,?,?,?,?,?,?,?)"
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
                    order = int(self.strahler[channel])
                    length = float(self.channelLengths[channel] * gv.mainLengthMultiplier)
                    slopePercent = float(self.channelSlopes[channel] * 100 * gv.reachSlopeMultiplier / gv.mainLengthMultiplier)
                    minEl = float(channelData.lowerZ)
                    maxEl = float(channelData.upperZ)             
                else:
                    mergeData = basinMerge.get(channel, None)
                    if mergeData is None:
                        continue
                    drainAreaHa = float(mergeData.areaC / 1E4)
                    order = int(mergeData.order)
                    length = float(mergeData.length  * gv.mainLengthMultiplier)
                    slopePercent = float(mergeData.slope * 100 * gv.reachSlopeMultiplier) / gv.mainLengthMultiplier
                    minEl = float(mergeData.minEl)
                    maxEl = float(mergeData.maxEl)
                # possible for channel to be so short it has no pixels draining to it
                # also no LSU data when channel is outlet from lake in grid model
                basinData = basins.get(subbasin, None)
                channelData = None if basinData is None else basinData.getLsus().get(channel, None)
                lsuData = None if channelData is None else channelData.get(floodscape, None)
                drainAreaKm = float(drainAreaHa) / 100 
                channelWidth = float(gv.channelWidthMultiplier * (drainAreaKm ** gv.channelWidthExponent))
                wid2Data[SWATChannel] = channelWidth
                channelDepth = float(gv.channelDepthMultiplier * (drainAreaKm ** gv.channelDepthExponent))
                if lsuData is None:
                    rid = 0
                    pid = 0
                    channelData = self.channelsData[channel]
                    midPointX = (channelData.lowerX + channelData.upperX) / 2
                    midPointY = (channelData.lowerY + channelData.upperY) / 2
                else:
                    rid = self.getReservoirId(lsuData)
                    pid = self.getPondId(lsuData)
                    midPointX = lsuData.midPointX
                    midPointY = lsuData.midPointY
                midll = self.pointToLatLong(QgsPointXY(midPointX, midPointY))
                midLat = midll.y()
                midLong = midll.x()
                if rid == 0 and pid == 0:
                    # omit from gis_channels channels which have become reservoirs or ponds
                    curs.execute(sql, (SWATChannel, SWATBasin, drainAreaHa, order, length, slopePercent, 
                                       channelWidth, channelDepth, minEl, maxEl, midLat, midLong))
                    self.db.addKey(table, SWATChannel)
                if addToRiv1:
                    lakeInId = self.chLinkIntoLake.get(channel, 0)
                    mmap[fid] = dict()
                    mmap[fid][areaCIdx] = drainAreaHa
                    mmap[fid][orderIdx] = order
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
        rivJson = QSWATUtils.join(gv.resultsDir, Parameters._RIVS + '.json')
        rivLayer = QgsVectorLayer(rivFile, 'Channels', 'ogr')
        provider = rivLayer.dataProvider()
        exporter = QgsJsonExporter(rivLayer)
        QSWATUtils.removeLayer(rivJson, root)
        with open(rivJson, 'w') as jsonFile:
            jsonFile.write(exporter.exportFeatures(provider.getFeatures()))
        # remove channels that are reservoirs or ponds
        exp = QgsExpression('"{0}" > 0 OR "{1}" > 0'.format(QSWATTopology._RESERVOIR, QSWATTopology._POND))
        idsToDelete: List[int] = []
        for feature in provider.getFeatures(QgsFeatureRequest(exp).setFlags(QgsFeatureRequest.NoGeometry)):
            idsToDelete.append(feature.id())
        OK = provider.deleteFeatures(idsToDelete)
        if not OK:
            QSWATUtils.error('Cannot edit streams results template {0}.'.format(rivFile), self.isBatch)
            return None
        # leave only the Channel, ChannelR and Subbasin attributes
        self.removeFields(rivLayer, [QSWATTopology._CHANNEL, QSWATTopology._CHANNELR, QSWATTopology._SUBBASIN], rivFile, self.isBatch)
        # add PenWidth field to stream results template
        OK = provider.addAttributes([QgsField(QSWATTopology._PENWIDTH, QVariant.Double)])
        if not OK:
            QSWATUtils.error('Cannot add {0} field to streams results template {1}'.format(QSWATTopology._PENWIDTH, rivFile), self.isBatch)
            return None
        self.setPenWidth(wid2Data, 1.0, 4.0, provider)
        if gv.useGridModel:
            provider1.addAttributes([QgsField(QSWATTopology._PENWIDTH, QVariant.Double)])
            self.setPenWidth(wid2Data, 0.2, 2.0, provider1)
        layers = root.findLayers()
        subLayer = QSWATUtils.getLayerByLegend(QSWATUtils._GRIDLEGEND, layers) if gv.useGridModel else root.findLayer(channelLayer.id())
        if gv.useGridModel:
            if gv.existingWshed:
                ft = FileTypes._DRAINSTREAMS
            else:
                ft = FileTypes._GRIDSTREAMS
        else:
            ft = FileTypes._CHANNELREACHES
        rivs1Layer = QSWATUtils.getLayerByFilename(layers, rivs1File, ft, gv, subLayer, QSWATUtils._WATERSHED_GROUP_NAME)[0]
        if gv.useGridModel:
            FileTypes.colourStreams(rivs1Layer, QSWATTopology._PENWIDTH, QSWATTopology._AREAC)
        else:
            # hide channel layer
            if channelLayer is not None:
                QSWATUtils.setLayerVisibility(channelLayer, False, root)
            if len(self.upstreamFromInlets) > 0:
                self.replaceStreamLayer(root, layers, gv)
        return rivs1Layer
        
    def generateChannelsFromShapefile(self, request: QgsFeatureRequest, provider: QgsVectorDataProvider, linkIdx: int, chIdx: int) -> Iterator[Tuple[int, int, int]]:
        """Yield (feature id, channel, swatChammel) tupless from rivs1.shp."""
        for feature in provider.getFeatures(request):
            yield feature.id(), feature[linkIdx], feature[chIdx]
            
    def generateChannelsFromTable(self) -> Iterator[Tuple[int, int, int]]:
        """Yield (feature id, channel, swatChammel) tuples from tables."""
        for channel, SWATChannel in self.channelToSWATChannel.items():
            yield 0, channel, SWATChannel
            
    def replaceStreamLayer(self, root: QgsLayerTreeGroup, layers: List[QgsLayerTreeLayer], gv: Any) -> None:
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
                
        
    def getReservoirId(self, lsuData: LSUData) -> int:
        """Return reservoir id, if any, else 0."""
        if lsuData.waterBody is not None and lsuData.waterBody.isReservoir():
            return cast(int, lsuData.waterBody.id)
        return 0
    
    def getPondId(self, lsuData: LSUData) -> int:
        """Return pond id, if any, else 0."""
        if lsuData.waterBody is not None and lsuData.waterBody.isPond():
            return cast(int, lsuData.waterBody.id)
        return 0
        
    def mergeChannelData(self, mergeChannels: Dict[int, int]) -> Dict[int, MergedChannelData]:
        """Generate and return map of channel to MergedChannelData."""
        
        # first pass: collect data for unmerged channels
        mergedChannelData: Dict[int, MergedChannelData] = dict()
        for channel in self.channelToSWATChannel.keys():
            if channel not in mergeChannels:
                channelData = self.channelsData[channel]
                mergedChannelData[channel] = MergedChannelData(self.drainAreas[channel],
                                                               self.strahler[channel],
                                                               self.channelLengths[channel],
                                                               self.channelSlopes[channel],
                                                               channelData.lowerZ,
                                                               channelData.upperZ)
        # second pass: add data for merged channels
        for source, target in mergeChannels.items():
            channelData = self.channelsData[source]
            final = self.finalTarget(target, mergeChannels)
            mergedChannelData[final].add(self.drainAreas[source],
                                         self.strahler[source],
                                         self.channelLengths[source],
                                         self.channelSlopes[source],
                                         channelData.lowerZ,
                                         channelData.upperZ)
        return mergedChannelData
             
    def finalTarget(self, target: int, mergeChannels: Dict[int, int]) -> int:
        """Find final target of merges."""
        nxt = mergeChannels.get(target, -1)
        if nxt < 0:
            return target
        else:
            return self.finalTarget(nxt, mergeChannels)
                
    def finalDownstream(self, start: int, mergeChannels: Dict[int, int]) -> int:
        """Find downstream channel from start, skipping merged channels, and return it."""
        chLink1 = self.finalTarget(start, mergeChannels)
        return self.finalTarget(self.getDownChannel(chLink1), mergeChannels)
            
    def routeChannelsOutletsAndBasins(self, basins: Dict[int, BasinData], mergedChannels: Dict[int, int], 
                                      mergees: List[int], extraPoints: List[Tuple[int, int]], gv: Any) -> bool:
        """Add channels, lakes, basins, aquifers, point sources, reservoirs, inlets and outlets to main gis_routing table."""
        
        chCat = 'CH'
        subbasinCat = 'SUB'
        ptCat = 'PT'
        resCat = 'RES'
        pondCat = 'PND'
        wetlandCat = 'WETL'
        xCat = 'X'
        # first associate any inlets, point sources and reservoirs with appropriate channels
        if gv.useGridModel:
            # no merging
            channelToInlet: Dict[int, Tuple[int, QgsPointXY]] = self.chLinkToInlet
            channelToPtSrc: Dict[int, Tuple[int, QgsPointXY]] = self.chLinkToPtSrc
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
            for channel, ptsrcPair in self.chLinkToPtSrc.items():
                channelToPtSrc[channel] = ptsrcPair
                #QSWATUtils.loginfo('Channel {0} merged to {1} has point source {2}'.format(channel, self.finalTarget(channel, mergedChannels), ptsrc[0]))
        # add point sources at stream sources
        for channel, ptsrcPair in self.chPointSources.items():
            if channel not in channelToPtSrc and channel not in mergees and \
                channel not in self.chLinkInsideLake and \
                not (gv.useGridModel and channel in self.chLinkFromLake):  # not already has a point, not merged, not inslide lake 
                channelToPtSrc[channel] = ptsrcPair
        # map channels to water bodies that replace them as drainage targets
        # and water bodies to channels they drain into
        floodscape = QSWATUtils._FLOODPLAIN if gv.useLandscapes else QSWATUtils._NOLANDSCAPE
        channelToWater: Dict[int, Tuple[int, int]] = dict()
        for basinData in basins.values():
            for channel, channelData in basinData.getLsus().items():
                lsuData = channelData.get(floodscape, None)
                if lsuData is not None and lsuData.waterBody is not None and not lsuData.waterBody.isUnknown():
                    channelToWater[channel] = (lsuData.waterBody.id, lsuData.waterBody.waterRole)
        try:
            assert isinstance(self.db, DBUtils)
            with self.db.conn as conn:
                curs = conn.cursor()
                routedPoints: List[int] = []
                routedWater: List[int] = []
                routedChannels: List[int] = []
#                 routedSubbasins = []
                for channel, SWATChannel in self.channelToSWATChannel.items():
                    if channel in mergedChannels:
                        # all that is needed is to map its point source to the merge target
                        ptsrcId, ptsrc = channelToPtSrc.get(channel, (-1, None))
                        if ptsrc is not None:
                            if ptsrcId not in routedPoints:
                                finalChannel = self.finalTarget(channel, mergedChannels)
                                wid, role = channelToWater.get(finalChannel, (-1, -1))
                                if wid >= 0:
                                    wCat = resCat if role == 1 else pondCat if role == 2 else wetlandCat
                                    self.db.addToRouting(curs, ptsrcId, ptCat, wid, wCat, QSWATTopology._TOTAL, 100)
                                else:
                                    finalSWATChannel = self.channelToSWATChannel[finalChannel]
                                    self.db.addToRouting(curs, ptsrcId, ptCat, finalSWATChannel, chCat, QSWATTopology._TOTAL, 100)
                                routedPoints.append(ptsrcId)
                        continue
                    # if channel is lake outflow
                    # if main outflow, route lake to outlet and outlet to channel
                    # else route 0% of lake to channel
                    outLakeId = self.chLinkFromLake.get(channel, -1)
                    if outLakeId >= 0:
                        lakeData = self.lakesData[outLakeId]
                        wCat = resCat if lakeData.waterRole == 1 else pondCat if lakeData.waterRole == 2 else wetlandCat
                        if channel == lakeData.outChLink:
                            # main outlet
                            outletId = lakeData.outPoint[1]
                            self.db.addToRouting(curs, outLakeId, wCat, outletId, ptCat, QSWATTopology._TOTAL, 100)
                            if outletId not in routedPoints:
                                if gv.useGridModel and self.downChannels.get(channel, -1) < 0:
                                    # we have an internal lake exit: route outlet id to watershed exit
                                    self.db.addToRouting(curs, outletId, ptCat, 0, xCat, QSWATTopology._TOTAL, 100)
                                else:
                                    self.db.addToRouting(curs, outletId, ptCat, SWATChannel, chCat, QSWATTopology._TOTAL, 100)
                            routedPoints.append(outletId)
                        else:
                            # other outlet
                            self.db.addToRouting(curs, outLakeId, wCat, SWATChannel, chCat, QSWATTopology._TOTAL, 0)
                    # check if channel routes into lake
                    inLakeId = self.chLinkIntoLake.get(channel, -1)
                    if inLakeId >= 0:
                        # route its point source to the channel
                        ptsrcId, ptsrc = channelToPtSrc.get(channel, (-1, None))
                        if ptsrc is not None:
                            if ptsrcId not in routedPoints:
                                self.db.addToRouting(curs, ptsrcId, ptCat, SWATChannel, chCat, QSWATTopology._TOTAL, 100)
                                routedPoints.append(ptsrcId)
                        # route the channel into its outlet, and the outlet into the lake
                        lakeData = self.lakesData[inLakeId]
                        outletId = lakeData.inChLinks[channel][0]
                        wCat = resCat if lakeData.waterRole == 1 else pondCat if lakeData.waterRole == 2 else wetlandCat
                        if SWATChannel not in routedChannels:
                            self.db.addToRouting(curs, SWATChannel, chCat, outletId, ptCat, QSWATTopology._TOTAL, 100)
                            routedChannels.append(SWATChannel)
                        if outletId not in routedPoints:
                            self.db.addToRouting(curs, outletId, ptCat, inLakeId, wCat, QSWATTopology._TOTAL, 100)
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
                    wCat = resCat if role == 1 else pondCat if role == 2 else wetlandCat
                    inletId, inletPt = channelToInlet.get(channel, (-1, None))
                    if inletPt is not None:
                        # route inlet to channel or water
                        if wid >= 0:
                            self.db.addToRouting(curs, inletId, ptCat, wid, wCat, QSWATTopology._TOTAL, 100)
                        else:
                            self.db.addToRouting(curs, inletId, ptCat, SWATChannel, chCat, QSWATTopology._TOTAL, 100)
                    (pointId, _, outletChannels) = self.outlets[subbasin]
                    if channel in outletChannels or gv.useGridModel:
                        # subbasin outlet: channel routes to outlet point of subbasin; outlet routes to downstream channel
                        # but with some exceptions:
                        # - if the channel is replaced by a reservoir, this is routed to the outlet instead
                        # - if subbasin has an extra point source, this is added to its outlet channel or reservoir
                        if gv.useGridModel:
                            ptsrcId, ptsrc = channelToPtSrc.get(channel, (-1, None))
                        else:
                            ptsrcId = -1
                            ptsrc = None
#                         if ptsrc is None:
#                             ptsrc = self.extraPtSrcs.get(subbasin, None)
                        if ptsrc is not None:
                            # route it to the outlet channel, unless already routed
                            if ptsrcId not in routedPoints:
                                if wid < 0:
                                    self.db.addToRouting(curs, ptsrcId, ptCat, SWATChannel, chCat, QSWATTopology._TOTAL, 100)
                                else:
                                    self.db.addToRouting(curs, ptsrcId, ptCat, wid, wCat, QSWATTopology._TOTAL, 100)
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
                                    self.db.addToRouting(curs, wid, wCat, ptId, ptCat, QSWATTopology._TOTAL, 100)
                                    if ptId not in routedPoints:
                                        self.db.addToRouting(curs, ptId, ptCat, pointId, ptCat, QSWATTopology._TOTAL, 100)
                                        routedPoints.append(ptId)
                                    routedWater.append(wid)
                        elif SWATChannel not in routedChannels:    
                            self.db.addToRouting(curs, SWATChannel, chCat, pointId, ptCat, QSWATTopology._TOTAL, 100)
                            routedChannels.append(SWATChannel)
                        if pointId not in routedPoints:
                            if dsSWATChannel > 0:
                                widDown, roleDown = channelToWater.get(dsChannel, (-1, -1))
                                if widDown >= 0:
                                    wCat = resCat if roleDown == 1 else pondCat if roleDown == 2 else wetlandCat
                                    self.db.addToRouting(curs, pointId, ptCat, widDown, wCat, QSWATTopology._TOTAL, 100)
                                else:
                                    self.db.addToRouting(curs, pointId, ptCat, dsSWATChannel, chCat, QSWATTopology._TOTAL, 100)
                            else:
                                # watershed outlet: mark point as category X
                                self.db.addToRouting(curs, pointId, ptCat, 0, xCat, QSWATTopology._TOTAL, 100)
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
                                            self.db.addToRouting(curs, wid, wCat, ptId, ptCat, QSWATTopology._TOTAL, 100)
                                            if ptId not in routedPoints:
                                                wCat = resCat if roleDown == 1 else pondCat if roleDown == 2 else wetlandCat
                                                self.db.addToRouting(curs, ptId, ptCat, widDown, wCat, QSWATTopology._TOTAL, 100)
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
                                        self.db.addToRouting(curs, wid, wCat, ptId, ptCat, QSWATTopology._TOTAL, 100)
                                        if ptId not in routedPoints:
                                            self.db.addToRouting(curs, ptId, ptCat, dsSWATChannel, chCat, QSWATTopology._TOTAL, 100)
                                            routedPoints.append(ptId)
                                        routedWater.append(wid)
                        elif SWATChannel not in routedChannels:
                            if widDown >= 0:  
                                # insert an outlet point so that channel's contribution to reservoir 
                                # is included in outputs
                                self.pointId += 1
                                extraPoints.append((channel, self.pointId))
                                self.db.addToRouting(curs, SWATChannel, chCat, self.pointId, ptCat, QSWATTopology._TOTAL, 100)
                                wCat = resCat if roleDown == 1 else pondCat if roleDown == 2 else wetlandCat
                                self.db.addToRouting(curs, self.pointId, ptCat, widDown, wCat, QSWATTopology._TOTAL, 100)
                                routedPoints.append(self.pointId)
                            else:
                                self.db.addToRouting(curs, SWATChannel, chCat, dsSWATChannel, chCat, QSWATTopology._TOTAL, 100)
                            routedChannels.append(SWATChannel)    
                    # also route point source, if any, to channel  or water
                    ptsrcId, ptsrc = channelToPtSrc.get(channel, (-1, None))
                    if ptsrc is not None:
                        if ptsrcId not in routedPoints:
                            if wid > 0:
                                self.db.addToRouting(curs, ptsrcId, ptCat, wid, wCat, QSWATTopology._TOTAL, 100)
                            else:
                                self.db.addToRouting(curs, ptsrcId, ptCat, SWATChannel, chCat, QSWATTopology._TOTAL, 100)
                            routedPoints.append(ptsrcId)
                # route reservoir and pond lakes without outlet channels to main outlet points
                for lakeId, lakeData in self.lakesData.items():
                    if lakeData.waterRole in {QSWATTopology._RESTYPE, QSWATTopology._PONDTYPE} and lakeData.outChLink == -1:
                        (subbasin, lakeOutletId, _, _) = lakeData.outPoint
                        (outletId, _, _) = self.outlets[subbasin]
                        wCat = resCat if lakeData.waterRole == 1 else pondCat if lakeData.waterRole == 2 else wetlandCat
                        # route the lake to its lake outlet, the lake outlet to the main outlet, and mark main outlet as category X 
                        self.db.addToRouting(curs, lakeId, wCat, lakeOutletId, ptCat, QSWATTopology._TOTAL, 100)
                        if lakeOutletId not in routedPoints:
                            self.db.addToRouting(curs, lakeOutletId, ptCat, outletId, ptCat, QSWATTopology._TOTAL, 100)
                            routedPoints.append(lakeOutletId)
                        if outletId not in routedPoints:
                            self.db.addToRouting(curs, outletId, ptCat, 0, xCat, QSWATTopology._TOTAL, 100)
                            routedPoints.append(outletId)
                # route subbasin to outlet points
                # or to lake if outlet in lake
                for subbasin, (pointId, _, chLinks) in self.outlets.items():
                    SWATBasin = self.subbasinToSWATBasin.get(subbasin, 0)
                    if SWATBasin == 0:
                        continue
                    # with grid models chLinks is always a singleton list
                    if gv.useGridModel:
                        if chLinks[0] in self.chLinkInsideLake or chLinks[0] in self.chLinkFromLake:
                            continue
                    lakeId = self.outletsInLake.get(subbasin, -1)
                    # if one chLink is inside lake, all will be, since they share their outlet point
                    if lakeId < 0:
                        lakeId = self.chLinkInsideLake.get(chLinks[0], -1)
                    if lakeId < 0:
                        self.db.addToRouting(curs, SWATBasin, subbasinCat, pointId, ptCat, QSWATTopology._TOTAL, 100)
                    else:
                        lakeData = self.lakesData[lakeId]
                        wCat = resCat if lakeData.waterRole == 1 else pondCat if lakeData.waterRole == 2 else wetlandCat
                        self.db.addToRouting(curs, SWATBasin, subbasinCat, lakeId, wCat, QSWATTopology._TOTAL, 100)
                    
            return True               
        except Exception:
            QSWATUtils.loginfo('Routing channels, outlets and subbasins failed: {0}'.format(traceback.format_exc()))
            return False
    
    @staticmethod
    def removeFields(layer: QgsVectorLayer, keepFieldNames: List[str], fileName: str, isBatch: bool) -> None:
        """Remove fields other than keepFieldNames from shapefile fileName with provider."""
        toDelete = []
        provider = layer.dataProvider()
        fields = provider.fields()
        keepLower = [name.casefold() for name in keepFieldNames]
        for idx in range(fields.count()):
            name = fields.field(idx).name()
            if not name.casefold() in keepLower:
                toDelete.append(idx)
        if len(toDelete) > 0:
            OK = provider.deleteAttributes(toDelete)
            layer.updateFields()
            if not OK:
                QSWATUtils.error('Cannot remove fields from shapefile {0}'.format(fileName), isBatch)
    
    def setPenWidth(self, data: Dict[int, float], a: float, b: float, provider: QgsVectorDataProvider) -> None:
        """Scale wid2 data to a .. b and write to layer."""
        base = a
        mult = b - a
        minW = float('inf')
        maxW = 0.0
        for val in data.values():
            minW = min(minW, val)
            maxW = max(maxW, val)
        if maxW > minW: # guard against division by zero
            rng = maxW - minW
            fun = lambda x: (x - minW) * mult / rng + base
        else:
            fun = lambda _: 1.0
        chIdx = provider.fieldNameIndex(QSWATTopology._CHANNEL)
        if chIdx < 0:
            QSWATUtils.error('Cannot find {0} field in channels results template'.format(QSWATTopology._CHANNEL), self.isBatch)
            return
        penIdx = provider.fieldNameIndex(QSWATTopology._PENWIDTH)
        if penIdx < 0:
            QSWATUtils.error('Cannot find {0} field in channels results template'.format(QSWATTopology._PENWIDTH), self.isBatch)
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
            
    def makeOutletThresholds(self, gv: Any, root: QgsLayerTreeGroup) -> int:
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
        maxContrib = 0.0
        for (_, pt, _) in self.outlets.values():
            contrib = QSWATTopology.valueAtPoint(pt, ad8Layer)
            if contrib is not None:
                maxContrib = max(maxContrib, contrib)
        threshold = int(2 * maxContrib)
        del ad8Layer
        # copy ad8 to hd8 and then set outlet point values to threshold
        ad8Ds = gdal.Open(gv.ad8File, gdal.GA_ReadOnly)
        driver = gdal.GetDriverByName('GTiff')
        hd8Ds = driver.CreateCopy(gv.hd8File, ad8Ds, 0)
        if not hd8Ds:
            QSWATUtils.error('Failed to create hd8 file {0}'.format(gv.hd8File), self.isBatch)
            return -1
        ad8Ds = None
        QSWATUtils.copyPrj(gv.ad8File, gv.hd8File)
        band = hd8Ds.GetRasterBand(1)
        transform = hd8Ds.GetGeoTransform()
        arr: ndarray[float] = array([[threshold]])
        for (_, pt, _) in self.outlets.values():
            x, y = QSWATTopology.projToCell(pt.x(), pt.y(), transform)
            band.WriteArray(arr, x, y)
        hd8Ds = None
        return threshold
           
    def runCalc1(self, file1: str, func: Callable[[float, float, float], float], outFile: str, 
                 gv: Any, isInt: bool=False, 
                 fun1: Optional[Callable[[float], float]]=None) -> bool:
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
        
    def runCalc2(self, file1: str, file2: str, func: Callable[[float, float, float, float, float], float], 
                 outFile: str, gv: Any, isInt: bool=False, fun1: Optional[Callable[[float], float]]=None, 
                 fun2: Optional[Callable[[float], float]]=None) -> bool:
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
        
        
    def runCalc2Trans(self, file1: str, file2: str, func: Callable[[float, float, float, float, float], float], 
                      outFile: str, baseFile:str, gv: Any, isInt: bool=False, 
                      fun1: Optional[Callable[[float], float]]=None, fun2: Optional[Callable[[float], float]]=None) -> bool:
        """Use func as a function to calulate outFile from file1 and file2, using numbers of rows and columns of baseFile.

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
    def burnStream(streamFile: str, demFile: str, burnFile: str, depth: float, verticalFactor: float, isBatch: bool) -> None:
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
        changed: Dict[int, List[int]] = dict()
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
                    arr: ndarray[float] = array([[0.0]])
                    for x in range(x0, x1+1):
                        if steep:
                            if QSWATTopology.addPointToChanged(changed, y, x):
                                # read can raise exception if coordinates outside extent
                                try:
                                    arr = band.ReadAsArray(y, x, 1, 1)
                                    # arr may be none if stream map extends outside DEM extent
                                    if arr and arr[0,0] != nodata:
                                        arr[0,0] = arr[0,0] - demReduction
                                        band.WriteArray(arr, y, x)
                                        countChanges += 1
                                except:
                                    pass
                            else:
                                countHits += 1
                        else:
                            if QSWATTopology.addPointToChanged(changed, x, y):
                                # read can raise exception if coordinates outside extent
                                try:
                                    arr = band.ReadAsArray(x, y, 1, 1)
                                    # arr may be none if stream map extends outside DEM extent
                                    if arr and arr[0,0] != nodata:
                                        arr[0,0] = arr[0,0] - demReduction
                                        band.WriteArray(arr, x, y)
                                        countChanges += 1
                                except:
                                    pass   
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
    def addPointToChanged(changed: Dict[int, List[int]], col: int, row: int) -> bool:
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
    def valueAtPoint(point: QgsPointXY, layer: QgsRasterLayer) -> Optional[float]:
        """
        Get the band 1 value at point in a grid layer.  Return None if no value, eg NoData
        
        """
        val, ok =  layer.dataProvider().sample(point, 1)
        if not ok:
            return None
        else:
            return val
         
    def isUpstreamSubbasin(self, subbasin: int) -> bool:
        """Return true if a subbasin is upstream from an inlet."""
        return subbasin in self.upstreamFromInlets
    
    def pointToLatLong(self, point: QgsPointXY) -> QgsPointXY: 
        """Convert a QgsPointXY to latlong coordinates and return it."""
        geom = QgsGeometry.fromPointXY(point)
        assert self.transformToLatLong is not None
        geom.transform(self.transformToLatLong)
        return geom.asPoint()
            
    def getIndex(self, layer: QgsVectorLayer, name: str, ignoreMissing: bool=False) -> int:
        """Get the index of a shapefile layer attribute name, 
        reporting error if not found, unless ignoreMissing is true.
        """
        # field names are truncated to 10 characters when created, so only search for up to 10 characters
        # also allow any case, since using lookupField rather than indexOf
        index: int = layer.fields().lookupField(name[:10])
        if not ignoreMissing and index < 0:
            QSWATUtils.error('Cannot find field {0} in {1}'.format(name, QSWATUtils.layerFileInfo(layer).filePath()), self.isBatch)
            raise Exception
        return index
            
    def getProviderIndex(self, provider: QgsVectorDataProvider, name: str, ignoreMissing: bool=False) -> int:
        """Get the index of a shapefile provider attribute name, 
        reporting error if not found, unless ignoreMissing is true.
        """
        # field names are truncated to 10 characters when created, so only search for up to 10 characters
        index = provider.fieldNameIndex(name[:10])
        if not ignoreMissing and index < 0:
            QSWATUtils.error('Cannot find field {0} in provider'.format(name), self.isBatch)
        return index
    
#     def makePointInLine(self, reach: QgsFeature, percent: float) -> QgsPointXY:
#         """Return a point percent along line from outlet end to next point."""
#         if self.outletAtStart:
#             line = QSWATTopology.reachFirstLine(reach.geometry(), self.xThreshold, self.yThreshold)
#             pt1 = line[0]
#             pt2 = line[1]
#         else:
#             line = QSWATTopology.reachLastLine(reach.geometry(), self.xThreshold, self.yThreshold)
#             length = len(line)
#             pt1 = line[length-1]
#             pt2 = line[length-2]
#         x = (pt1.x() * (100 - percent) + pt2.x() * percent) / 100.0
#         y = (pt1.y() * (100 - percent) + pt2.y() * percent) / 100.0
#         return QgsPointXY(x, y)
    
    def hasOutletAtStart(self, streamLayer: QgsVectorLayer, ad8Layer: QgsRasterLayer) -> bool:
        """Returns true iff streamLayer lines have their outlet points at their start points.
         
        If ad8Layer is not None, we are not in an existing watershed, and can rely on accumulations.
        Accumulation will be higher at the outlet end.
        Finds shapes with a downstream connections, and 
        determines the orientation by seeing how such a shape is connected to the downstream shape.
        If they don't seem to be connected (as my happen after merging subbasins) 
        tries other shapes with downstream connections, up to 10.
        A line is connected to another if their ends are less than dx and dy apart horizontally and vertically.
        Assumes the orientation found for this shape can be used generally for the layer.
        For HUC models just returns False immediately as NHD flowlines start from source end.
        """
        if self.isHUC:
            return False
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
                        if acc1 is not None and acc2 is not None and acc1 != acc2:
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
    
    def saveOutletsAndSources(self, channelLayer: QgsVectorLayer, outletLayer: Optional[QgsVectorLayer], useGridModel: bool) -> bool:
        """Write outlets, downSubbasins, and (unless useGridModel)
         inlets, upstreamFromInlets, and outletChannels  tables."""
        # in case called twice
        self.pointId = 0
        self.waterBodyId = 0
        self.outlets.clear()
        self.inlets.clear()
        self.chOutlets.clear()
        self.chPointSources.clear()
        self.upstreamFromInlets.clear()
        self.downSubbasins.clear()
        self.chBasinToSubbasin.clear()
        chLinkToSubbasin = dict()
        downChannels = dict()
        chInlets: Dict[int, Tuple[int, QgsPointXY]] = dict()
        chLinkIndex = self.getIndex(channelLayer, QSWATTopology._LINKNO)
        DSLINKNO = QSWATTopology._DSLINKNO1 if self.isHUC else QSWATTopology._DSLINKNO
        dsChLinkIndex = self.getIndex(channelLayer, DSLINKNO)
        self.wsnoIndex = self.getIndex(channelLayer, QSWATTopology._WSNO, ignoreMissing=not useGridModel and not self.isHUC)
        sourceXIndex = self.getIndex(channelLayer, QSWATTopology._SOURCEX, ignoreMissing=not self.isHUC)
        sourceYIndex = self.getIndex(channelLayer, QSWATTopology._SOURCEY, ignoreMissing=not self.isHUC)
        outletXIndex = self.getIndex(channelLayer, QSWATTopology._OUTLETX, ignoreMissing=not self.isHUC)
        outletYIndex = self.getIndex(channelLayer, QSWATTopology._OUTLETY, ignoreMissing=not self.isHUC)
        if chLinkIndex < 0 or dsChLinkIndex < 0:
            return False
        # ignoreMissing for subbasinIndex necessary when useGridModel, since channelLayer is then a streams layer
        subbasinIndex = self.getIndex(channelLayer, QSWATTopology._BASINNO, ignoreMissing=useGridModel)
        if useGridModel:
            if self.wsnoIndex < 0:
                return False
        else:
            if subbasinIndex < 0:
                return False   
        dsNodeIndex = self.getIndex(channelLayer, QSWATTopology._DSNODEID, ignoreMissing=True)
        if outletLayer is not None:
            outletProvider = outletLayer.dataProvider()
            idIndex = self.getProviderIndex(outletProvider, QSWATTopology._ID, ignoreMissing=False)
            inletIndex = self.getProviderIndex(outletProvider, QSWATTopology._INLET, ignoreMissing=False)
            srcIndex = self.getProviderIndex(outletProvider, QSWATTopology._PTSOURCE, ignoreMissing=False)
            resIndex = self.getProviderIndex(outletProvider, QSWATTopology._RES, ignoreMissing=False)
            ptIdIndex = self.getProviderIndex(outletProvider, QSWATTopology._POINTID, ignoreMissing=True)
            if ptIdIndex < 0:
                outletProvider.addAttributes([QgsField(QSWATTopology._POINTID, QVariant.Int)])
                outletLayer.updateFields()
                ptIdIndex = outletProvider.fieldNameIndex(QSWATTopology._POINTID)
            # set pointId to max id value in outletLayer
            # and waterBodyId to max reservoir or pond id
            # copy original id to PointId field, unless zero, when change to max id + 1
            ptIdMap: Dict[int, Dict[int, int]] = dict()
            zeroIndex = -1  # feature id of point with zero id
            request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry)
            for point in outletLayer.getFeatures(request):
                ptId = point[idIndex]
                if ptId == 0:
                    zeroIndex = point.id()
                else:
                    ptIdMap[point.id()] = {ptIdIndex: ptId}
                self.pointId = max(self.pointId, ptId)
                if point[inletIndex] == 0 and point[resIndex] > 0:
                    self.waterBodyId = max(self.waterBodyId, ptId)
            if zeroIndex >= 0:
                self.pointId += 1
                ptIdMap[zeroIndex] = {ptIdIndex: self.pointId}
            outletProvider.changeAttributeValues(ptIdMap)
        else:
            dsNodeIndex = -1
        for reach in channelLayer.getFeatures():
            chLink = reach[chLinkIndex]
            dsChLink = reach[dsChLinkIndex]
            chBasin = reach[self.wsnoIndex]
            # for grids, channel basins and subbasins are the same
            subbasin = chBasin if useGridModel else reach[subbasinIndex]
            chLinkToSubbasin[chLink] = subbasin
            if not useGridModel:
                self.chBasinToSubbasin[chBasin] = subbasin
            downChannels[chLink] = dsChLink
            dsNode = reach[dsNodeIndex] if dsNodeIndex >= 0 else -1
            if dsNode >= 0 and idIndex >= 0 and inletIndex >= 0 and srcIndex >= 0 and resIndex >= 0 and ptIdIndex >= 0:
                outletPoint = None
                inletPoint = None
                assert outletLayer is not None  # else dsNodeIndex = -1, so dsNode = -1
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
                    self.chOutlets[chLink] = (outletPoint[ptIdIndex], pt)
                elif inletPoint is not None:
                    pt = inletPoint.geometry().asPoint()
                    chInlets[chLink] = (inletPoint[ptIdIndex], pt)
            if self.isHUC:
                first: Optional[List[QgsPointXY]] = [QgsPointXY(reach[sourceXIndex], reach[sourceYIndex])]
                last: Optional[List[QgsPointXY]] = [QgsPointXY(reach[outletXIndex], reach[outletYIndex])]
            else:
                geom = reach.geometry()
                first = QSWATTopology.reachFirstLine(geom, self.xThreshold, self.yThreshold)                
                if first is None or len(first) < 2:
                    QSWATUtils.error('It looks like your channels shapefile does not obey the single direction rule, that all channels are either upstream or downstream.', self.isBatch)
                    return False
                last = QSWATTopology.reachLastLine(geom, self.xThreshold, self.yThreshold)               
                if last is None or len(last) < 2:
                    QSWATUtils.error('It looks like your channels shapefile does not obey the single direction rule, that all channels are either upstream or downstream.', self.isBatch)
                    return False
            outId, outPt = self.chOutlets.get(chLink, (-1, None))
            if outPt is None:
                self.pointId += 1
                outId = self.pointId
            self.pointId += 1
            srcId = self.pointId
            assert first is not None
            assert last is not None
            if self.outletAtStart:
                if not useGridModel and outPt is not None and not QSWATTopology.coincidentPoints(first[0], outPt, self.xThreshold, self.yThreshold):
                    QSWATUtils.error('Outlet point {0} at ({1}, {2}) not coincident with start of channel link {3}'
                                     .format(outId, outPt.x(), outPt.y(), chLink), self.isBatch)
                self.chOutlets[chLink] = (outId, first[0])
                self.chPointSources[chLink] = (srcId, last[-1])
            else:
                if not useGridModel and outPt is not None and not QSWATTopology.coincidentPoints(last[-1], outPt, self.xThreshold, self.yThreshold):
                    QSWATUtils.error('Outlet point {0} at ({1}, {2}) not coincident with end of channel link {3}'
                                     .format(outId, outPt.x(), outPt.y(), chLink), self.isBatch)
                self.chOutlets[chLink] = (outId, last[-1])
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
                outletId, outletPt = self.chOutlets[chLink]
                existOutlets = self.outlets.get(subbasin, None)
                if existOutlets is None:
                    self.outlets[subbasin] = (outletId, outletPt, [chLink])
                else:
                    outletid0, outletPt0, chLinks = existOutlets
                    if not QSWATTopology.coincidentPoints(outletPt0, outletPt, self.xThreshold, self.yThreshold):
                        QSWATUtils.error('Polygon {0} has separate outlets at ({1}, {2}) and ({3}, {4}): ignoring second'.
                                         format(subbasin, outletPt0.x(), outletPt0.y(), outletPt.x(), outletPt.y()), self.isBatch)
                    else:
                        self.chOutlets[chLink] = outletid0, outletPt0
                        self.outlets[subbasin] = outletid0, outletPt0, chLinks + [chLink]
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
    
    def nonzeroPointId(self, dsNode: int) -> int:
        """Return dsNode, or next pointId if dsNode is zero.  Used to prevent a zero point id."""
        if dsNode == 0:
            self.pointId += 1
            return self.pointId
        return dsNode
    
    def addUpstreamSubbasins(self, start: int) -> None:
        """Add basins upstream from start to upstreamFromInlets."""
        for subbasin, downSubbasin in self.downSubbasins.items():
            if downSubbasin == start:
                self.upstreamFromInlets.add(subbasin)
                self.addUpstreamSubbasins(subbasin)
    
    def surroundingLake(self, SWATChannel: int, useGridModel: bool) -> int:
        """Return id of lake containing channel, if any, else -1."""
        chLink = self.SWATChannelToChannel[SWATChannel]
        lake1 = self.chLinkInsideLake.get(chLink, -1)
        if useGridModel and lake1 < 0:
            return self.chLinkFromLake.get(chLink, -1)
        else:
            return lake1
        
    @staticmethod
    def maskFun(val: float, valNoData: float, mask: float, maskNoData: float, resNoData: float) -> float:
        """Result is val unless mask is nodata."""
        if val == valNoData or mask == maskNoData:
            return resNoData
        else:
            return val      
    
    @staticmethod
    def reachFirstLine(geometry: QgsGeometry, xThreshold: float, yThreshold: float) -> Optional[List[QgsPointXY]]:
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
    def reachLastLine(geometry: QgsGeometry, xThreshold: float, yThreshold: float) -> Optional[List[QgsPointXY]]:
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
    def pointOnLine(point: QgsPointXY, line: List[QgsPointXY], xThreshold: float, yThreshold: float) -> bool:
        """Return true if point is coincident with a point on the line. 
        
        Note this only checks if the point is close to a vertex."""
        if line is None or len(line) == 0:
            return False
        for pt in line:
            if QSWATTopology.coincidentPoints(point, pt, xThreshold, yThreshold):
                return True
        return False
    
    @staticmethod
    def coincidentPoints(pt1: QgsPointXY, pt2: QgsPointXY, xThreshold: float, yThreshold: float) -> bool:
        """Return true if points are within xThreshold and yThreshold
        horizontally and vertically."""
        return abs(pt1.x() - pt2.x()) < xThreshold and \
            abs(pt1.y() - pt2.y()) < yThreshold
            
    @staticmethod
    def colToX(col: int, transform: Dict[int, float]) -> float:
        """Convert column number to X-coordinate."""
        return (col + 0.5) * transform[1] + transform[0]
    
    @staticmethod
    def rowToY(row: int, transform: Dict[int, float]) -> float:
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
    def cellToProj(col: int, row: int, transform: Dict[int, float]) -> Tuple[float, float]:
        """Convert column and row numbers to (X,Y)-coordinates."""
        x = (col + 0.5) * transform[1] + transform[0]
        y = (row + 0.5) * transform[5] + transform[3]
        return (x,y)
        
    @staticmethod
    def projToCell(x: float, y: float, transform: Dict[int, float]) -> Tuple[int, int]:
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
    def translateCoords(transform1: Dict[int, float], transform2: Dict[int, float], 
                        numRows1: int, numCols1: int) -> Tuple[Callable[[int, float], int], Callable[[int, float], int]]:
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
    def sameTransform(transform1: Dict[int, float], transform2: Dict[int, float], numRows1: int, numCols1: int) -> bool:
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
        
    def splitReachByLake(self, lakeGeom: QgsGeometry, reachGeom: QgsGeometry, reachData: ReachData) -> Tuple[Optional[QgsGeometry], Optional[QgsGeometry]]:
        """lakeGeom is a polygon representing a lake.  reach is known to intersect with the lake..
        Returns a pair of inflowing and outflowing reaches, either or both of which may be None."""
        sourcePt = QgsPointXY(reachData.upperX, reachData.upperY)
        sourceToLake = QSWATTopology.toIntersection(reachGeom, lakeGeom, sourcePt, not self.outletAtStart, self.xThreshold, self.yThreshold)
        outletPt = QgsPointXY(reachData.lowerX, reachData.lowerY)
        outletToLake = QSWATTopology.toIntersection(reachGeom, lakeGeom, outletPt, self.outletAtStart, self.xThreshold, self.yThreshold)
        return sourceToLake, outletToLake
        
    @staticmethod
    def toIntersection(reachGeom: QgsGeometry, lakeGeom: QgsGeometry, start: QgsPointXY, isUp: bool, 
                       xThreshold: float, yThreshold: float) -> Optional[QgsGeometry]:
        """Return geometry for sequence of points from start to one before first one that intersects with lakeGeom, 
        or None if this is empty or a singleton, or if start is within the lake.
        
        If isUp the search is from index 0 if the of the reach, else it is from the last index."""
        if lakeGeom.contains(start):
            return None
        if reachGeom.isMultipart():
            mpl = reachGeom.asMultiPolyline()
        else:
            mpl = [reachGeom.asPolyline()]
        result: List[QgsPointXY] = []
        done: Set[int] = set()
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
    def movePointToPerimeter(pt: QgsPointXY, lakeGeom: QgsGeometry, pFile: str, maxSteps: int) -> Tuple[QgsPointXY, bool]:
        """Point pt is contained in lake.  Move it downstream at most maxSteps
        using D8 flow direction raster pFile until it is not inside the lake,
        returning new point and true.
        
        Return original point and false if failed to find perimeter."""
        pLayer = QgsRasterLayer(pFile, 'FlowDir')
        ds = gdal.Open(pFile, gdal.GA_ReadOnly)
        transform = ds.GetGeoTransform()
        stepCount = 0
        pt1 = pt
        while stepCount < maxSteps:
            if not lakeGeom.contains(pt1):
                return pt1, True
            dir1 = QSWATTopology.valueAtPoint(pt1, pLayer)
            if dir1 is None:
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
            
    @staticmethod 
    def lakeCategory(waterRole: int) -> str:
        if waterRole == QSWATTopology._RESTYPE:
            return 'reservoir'
        elif waterRole == QSWATTopology._PONDTYPE:
            return 'pond'
        elif waterRole == QSWATTopology._WETLANDTYPE:
            return 'wetland'
        else:
            return 'playa'
