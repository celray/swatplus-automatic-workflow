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
 
 Cython version of parts of hrus
'''

# cython: language_level=3

# Import the PyQt and QGIS libraries
from PyQt5.QtCore import *  # @UnusedWildImport
from PyQt5.QtGui import *  # @UnusedWildImport
from qgis.core import * # @UnusedWildImport
from qgis.gui import * # @UnusedWildImport

cdef class CellData:

    cdef:
        public int cellCount
        public double area
        public double totalElevation
        public double totalSlope
        public double totalLatitude
        public double totalLongitude
        public int crop
        public int actHRUNum
    
    """Data collected about cells in watershed grid that make an HRU."""
    def __init__(self, int count, double area, double elevation, double slope, double x, double y, int crop):
        """Constructor."""
        ## Cell count
        self.cellCount = count
        ## Total area in square metres
        self.area = area
        ## Total elevation (for calculating mean elevation)
        self.totalElevation = elevation
        ## Total slope (for calculating mean slope)
        self.totalSlope = slope
        ## total latitude (in projected units) for calculating centroid
        self.totalLatitude = y
        ## total longitude (in projected units) for calculating centroid
        self.totalLongitude = x
        ## Original crop number (for use with split landuses)
        self.crop = crop
        ## Actual HRU number (set when making HRUs, within printBasins)
        self.actHRUNum = 0
        
    cdef void addCell(self, double area, double elevation, double slope, double x, double y):
        """Add data for 1 cell."""
        self.cellCount += 1
        self.area += area
        self.totalElevation += elevation
        self.totalSlope += slope
        self.totalLatitude += y
        self.totalLongitude += x
        
    cpdef void addCells(self, CellData cd):
        """Add a cell data to this one."""
        self.cellCount += cd.cellCount
        self.area += cd.area
        self.totalElevation += cd.totalElevation
        self.totalSlope += cd.totalSlope
        self.totalLatitude += cd.totalLatitude
        self.totalLongitude += cd.totalLongitude
        
    cpdef void multiply(self, double factor):
        """Multiply cell values by factor."""
        self.cellCount = int(self.cellCount * factor + 0.5) 
        self.area *= factor
        self.totalSlope *= factor 
        self.totalElevation *= factor
        self.totalLatitude *= factor
        self.totalLongitude *= factor
        
# Roles a channel can play for a reservoir:
# INNER means channel is part of reservoir: drainage to channel replaced by drainage to reservoir
# OUTLET means channel is reservoir's outlet.  
# OUTLET was intended to be used when multiple INNER channels drain into non-inner to avoid 
# multiple separate reservoirs, but currently not implemented
# INLET means a reservoir was located at the outlet end of a channel by the user, and cannot be merged downstream
cdef enum ChannelRole:
    _INNER = 0
    _OUTLET = 1
    _INLET = 2
    
cdef enum WaterRole:
    _UNKNOWN = 0
    _RESERVOIR = 1
    _POND = 2
        
cdef class WaterBody:

    cdef:
        public int cellCount
        public double area
        public double originalArea
        public double totalElevation
        public double totalLatitude
        public double totalLongitude
        public int id
        public int channelRole
        public int waterRole
        
    """Data about areas with landuse WATR."""
    def __init__(self, int count, double area, double elevation, double x, double y):
        """Constructor."""
        ## Cell count
        self.cellCount = count
        ## Total area in square metres
        self.area = area
        ## Original area before any merging
        self.originalArea = area
        ## Total elevation (for calculating mean elevation)
        self.totalElevation = elevation
        ## total latitude (in projected units) for calculating centroid
        self.totalLatitude = y
        ## total longitude (in projected units) for calculating centroid
        self.totalLongitude = x
        ## id set later
        self.id = 0
        ## role of channel: _INNER is default
        self.channelRole = _INNER
        ## water role
        self.waterRole = _UNKNOWN
        
    cdef void addCell(self, double area, double elevation, double x, double y):
        """Add data for 1 cell."""
        self.cellCount += 1
        self.area += area
        self.originalArea += area
        self.totalElevation += elevation
        self.totalLatitude += y
        self.totalLongitude += x
        
#     cpdef void addCells(self, CellData cd):
#         """Add an hru to this one."""
#         self.cellCount += cd.cellCount
#         self.area += cd.area
#         self.originalArea += cd.area
#         self.totalElevation += cd.totalElevation
#         self.totalLatitude += cd.totalLatitude
#         self.totalLongitude += cd.totalLongitude
        
    cpdef void addWater(self, WaterBody wb, bint keepOriginal):
        """Add water body to this one, keeping original area, if keepOriginal is true."""
        self.cellCount += wb.cellCount
        self.area += wb.area
        if not keepOriginal:
            self.originalArea += wb.originalArea
        self.totalElevation += wb.totalElevation
        self.totalLatitude += wb.totalLatitude
        self.totalLongitude += wb.totalLongitude
        
    cpdef void multiply(self, double factor):
        """Multiply water body values by factor."""
        self.cellCount = int(self.cellCount * factor + 0.5) 
        self.area *= factor
        self.originalArea *= factor
        self.totalElevation *= factor
        self.totalLatitude *= factor
        self.totalLongitude *= factor
        
    cpdef void setInlet(self):
        """Set  to inlet.  provents merging downstream"""
        self.channelRole = _INLET
        
    cpdef void setOutlet(self):
        """Set  to outlet."""
        self.channelRole = _OUTLET
        
    cpdef void setReservoir(self):
        """Set to reservoir."""
        self.waterRole = _RESERVOIR
        
    cpdef void setPond(self):
        """Set to pond."""
        self.waterRole = _POND
        
    cpdef bint isInlet(self):
        """Return true if  is inlet."""
        return self.channelRole == _INLET
    
    cpdef bint isOutlet(self):
        """Return true if  is outlet."""
        return self.channelRole == _OUTLET
    
    cpdef bint isUnknown(self):
        """Return true if water role is unknown."""
        return self.waterRole == _UNKNOWN
    
    cpdef bint isReservoir(self):
        """Return true if is reservoir."""
        return self.waterRole == _RESERVOIR
    
    cpdef bint isPond(self):
        """Return true if is pond."""
        return self.waterRole == _POND
    
    cpdef WaterBody copy(self):
    
        cdef:
            WaterBody result
            
        result = WaterBody(self.cellCount, self.area, self.totalElevation, self.totalLongitude, self.totalLatitude)
        result.originalArea = self.originalArea
        result.channelRole = self.channelRole
        result.waterRole = self.waterRole
        result.id = self.id
        return result
        
cdef class LSUData:
    
    cdef:
        public int cellCount
        public double area
        public double outletElevation
        public double sourceElevation
        public double channelLength
        public double farElevation
        public double farDistance
        public double farPointX
        public double farPointY
        public double totalElevation
        public double totalSlope
        public double totalLatitude
        public double totalLongitude
        public double cropSoilSlopeArea
        public dict hruMap
        public dict cropSoilSlopeNumbers
        public dict cropAreas
        public dict originalCropAreas
        public dict soilAreas
        public dict originalSoilAreas
        public dict slopeAreas
        public dict originalSlopeAreas
        public WaterBody waterBody
        public int lastHru
    
    """Data held about landscape unit.
    
    Note that pixels of landuse WATR appear in both the main LSU data and also in the water body component.
    A decision is made later according to the water role:
    if the water role is a reservoir or pond then the water body is added to the model as reservoir or pond, and WATR HRUs are removed.
    If the water role ins _UNKNOWN then the water body is ignored and the WATR HRUs included. 
    """
    def __init__(self):
        """Initialise class variables."""
        ## Number of cells
        self.cellCount = 0
        ## Area in square metres
        self.area = 0
        ## elevation at outlet
        self.outletElevation = 0
        ## source of channel elevation
        self.sourceElevation = 0
        ## channel length in m
        self.channelLength = 0
        ## elevation of point with longest flow distance 
        self.farElevation = 0
        ## longest flow distance to channel
        # set negative so even a zero distance will be recorded
        self.farDistance = -1
        ## longitude (in projected units) of point with longest flow distance
        self.farPointX = 0
        ## latitude (in projected units) of point with longest flow distance
        self.farPointY = 0
        ## Total of elevation values (to compute mean)
        self.totalElevation = 0
        ## total of latitudes (in projected units) (to compute centroid)
        self.totalLatitude = 0
        ## total of longitudes (in projected units) (to compute centroid)
        self.totalLongitude = 0
        ## Total of slope values (to compute mean)
        self.totalSlope = 0
        ## area in square metres with not-Nodata crop, soil, and slope values.
        self.cropSoilSlopeArea = 0
        ## Map hru (relative) number -> CellData.
        self.hruMap = dict()
        ## Nested map crop -> soil -> slope -> hru number.
        # Range of cropSoilSlopeNumbers must be same as domain of hruMap
        self.cropSoilSlopeNumbers = dict()
        ## Map of crop to area of crop in landscape unit.
        #
        # This and the similar maps for soil and slope are duplicated:
        # an original version created after basin data is calculated and 
        # before HRUs are created, and another after HRUs are created.
        # HRU creation occurs within landscape units if these are used,
        # so landscape areas do not change when HRUs are created.
        self.cropAreas = dict()
        ## Original crop area map
        self.originalCropAreas = dict()
        ## Map of soil to area of soil in landscape unit.
        self.soilAreas = dict()
        ## Original soil area map
        self.originalSoilAreas = dict()
        ## Map of slope to area of slope in landscape unit.
        self.slopeAreas = dict()
        ## Original slope area map
        self.originalSlopeAreas = dict()
        ## water body if any
        self.waterBody = None
        ## last HRU number used
        self.lastHru = 0
                        
    cpdef dict cropSoilAreas(self, int crop):
        '''Map of soil -> area in square metres for particular crop.'''
        cdef:
            dict csmap = dict()
            int soil
        
#         assert crop in self.cropSoilSlopeNumbers
        for soil in self.cropSoilSlopeNumbers[crop].keys():
            csmap[soil] = self.cropSoilArea(crop, soil)
        return csmap
    
    cpdef double cropSoilArea(self, int crop, int soil):
        '''Area in square metres for crop-soil combination.'''
        cdef:
            double area = 0
            int hru 
        
#         assert crop in self.cropSoilSlopeNumbers and soil in self.cropSoilSlopeNumbers[crop]
        slopeNumbers = self.cropSoilSlopeNumbers[crop][soil]
        for hru in slopeNumbers.values():
            cellData = self.hruMap[hru]
            area += cellData.area
        return area
    
    cdef double cropArea(self, int crop):
        '''Area in square metres for crop.'''
        cdef:
            double area = 0
            dict slopeNumbers
            int hru 
            CellData cellData
        
        # use when cropAreas may not be set
#         assert crop in self.cropSoilSlopeNumbers, u'Landuse {0} not in basin data'.format(crop)
        for slopeNumbers in self.cropSoilSlopeNumbers[crop].values():
            for hru in slopeNumbers.values():
                cellData = self.hruMap[hru]
                area += cellData.area
        return area
    
    cpdef dict cropSoilSlopeAreas(self, int crop, int soil):
        '''Map of slope -> area in square metres for this crop and soil.'''
        cdef: 
            dict cssmap = dict()
            int slope 
            int hru 
        
#         assert crop in self.cropSoilSlopeNumbers and soil in self.cropSoilSlopeNumbers[crop]
        for (slope, hru) in self.cropSoilSlopeNumbers[crop][soil].items():
            cssmap[slope] = self.hruMap[hru].area
        return cssmap
    
    cpdef object getDominantHRU(self, waterLanduse, allowWater):
        '''Find the HRU with the largest area, 
        and return its crop, soil and slope.  
        If allowWater is False, waterLanduse crop is ignored.
        '''
        cdef:
            double maxArea = 0
            int maxCrop = -1
            int maxSoil = -1
            int maxSlope = -1
            CellData cellData
            double area
        
        for (crop, soilSlopeNumbers) in self.cropSoilSlopeNumbers.items():
            if crop != waterLanduse or allowWater:
                for (soil, slopeNumbers) in soilSlopeNumbers.items():
                    for (slope, hru) in slopeNumbers.items():
                        cellData = self.hruMap[hru]
                        area = cellData.area
                        if area > maxArea:
                            maxArea = area
                            maxCrop = crop
                            maxSoil = soil
                            maxSlope = slope
        return (maxCrop, maxSoil, maxSlope)
            
    cpdef void redistribute(self, double factor):
        '''Multiply all the HRU areas by factor.'''
        cdef:
            int hru 
            CellData cellData 
        
        for (hru, cellData) in self.hruMap.items():
            cellData.multiply(factor)
            self.hruMap[hru] = cellData
        # keep area of water hrus and water body consistent
        if self.waterBody is not None:
            self.waterBody.multiply(factor)
            
    cpdef void redistributeNodataAndWater(self, int chLink, int lscape, list chLinksByLakes, int waterLanduse):
        """Add nodata areas proportionately to originalareas. 
         
        Also removes water body if not a separate reservoir or pond 
        and channel flows into or is inside lake and lscape is nolandscape or floodplain."""
        cdef:
            double areaToRedistribute, redistributeFactor
        
        # water bodies adjacent to lakes are counted as part of lakes, and whole lsu area is counted as land 
        # but beware making area zero if all is water
        if self.waterBody is not None and self.cropSoilSlopeArea > self.waterBody.originalArea and \
            self.waterBody.isUnknown() and chLink in chLinksByLakes and \
            lscape in {0, 1}:  # {QSWATUtils._NOLANDSCAPE, QSWATUtils._FLOODPLAIN}
            # self.removeWaterHRUs(waterLanduse)
            self.waterBody = None
        areaToRedistribute = self.area - self.cropSoilSlopeArea
        if self.area > areaToRedistribute > 0:
            redistributeFactor = self.area / (self.area - areaToRedistribute)
            self.redistribute(redistributeFactor)
            
    cpdef void removeHRU(self, int hru, int crop, int soil, int slope):
        '''Remove an HRU from the hruMap and the cropSoilSlopeNumbers map.'''
#         assert crop in self.cropSoilSlopeNumbers and \
#             soil in self.cropSoilSlopeNumbers[crop] and \
#             slope in self.cropSoilSlopeNumbers[crop][soil] and \
#             hru == self.cropSoilSlopeNumbers[crop][soil][slope]
        del self.hruMap[hru]
        del self.cropSoilSlopeNumbers[crop][soil][slope]
        if len(self.cropSoilSlopeNumbers[crop][soil]) == 0:
            del self.cropSoilSlopeNumbers[crop][soil]
            if len(self.cropSoilSlopeNumbers[crop]) == 0:
                del self.cropSoilSlopeNumbers[crop]
                
    cpdef void removeWaterHRUs(self, int waterLanduse):
        """Remove HRUs with landuse water"""
        cdef:
            int crop 
            dict soilSlopeNumbers
            int soil
            dict slopeNumbers
            int slope
            int hru 
            
        # note use of list as dictionaries changed within loop
        for crop, soilSlopeNumbers in list(self.cropSoilSlopeNumbers.items()):
            if crop == waterLanduse:
                for soil, slopeNumbers in list(soilSlopeNumbers.items()):
                    for slope, hru in list(slopeNumbers.items()):
                        self.cropSoilSlopeArea -= self.hruMap[hru].area
                        self.removeHRU(hru, crop, soil, slope)
                  
    cpdef void setCropAreas(self, bint isOriginal):
        '''Make map crop -> area from hruMap and cropSoilSlopeNumbers.'''
        cdef:
            dict cmap 
            int crop 
            dict soilSlopeNumbers
            double area 
            dict slopeNumbers
            int hru 
            CellData cellData 
            
        cmap = self.originalCropAreas if isOriginal else self.cropAreas
        cmap.clear()
        for crop, soilSlopeNumbers in self.cropSoilSlopeNumbers.items():
            area = 0
            for slopeNumbers in soilSlopeNumbers.values():
                for hru in slopeNumbers.values():
                    cellData = self.hruMap[hru]
                    area += cellData.area
            cmap[crop] = area
        
    cpdef void setSoilAreas(self, bint isOriginal):
        '''Make map soil -> area from hruMap and cropSoilSlopeNumbers.'''
        cdef:
            dict smap 
            int soil 
            dict slopeNumbers 
            int hru 
            CellData cellData 
            double area 
            
        smap = self.originalSoilAreas if isOriginal else self.soilAreas
        smap.clear()
        for soilSlopeNumbers in self.cropSoilSlopeNumbers.values():
            for soil, slopeNumbers in soilSlopeNumbers.items():
                for hru in slopeNumbers.values():
                    cellData = self.hruMap[hru]
                    area = smap.get(soil, 0)
                    smap[soil] = area + cellData.area
    
    cpdef void setSlopeAreas(self, bint isOriginal):
        '''Make map slope -> area from hruMap and cropSoilSlopeNumbers.'''
        cdef:
            dict smap 
            int slope 
            dict soilSlopeNumbers 
            dict slopeNumbers
            int hru 
            CellData cellData 
            double area  
            
        smap = self.originalSlopeAreas if isOriginal else self.slopeAreas
        smap.clear()
        for soilSlopeNumbers in self.cropSoilSlopeNumbers.values():
            for slopeNumbers in soilSlopeNumbers.values():
                for slope, hru in slopeNumbers.items():
                    cellData = self.hruMap[hru]
                    area = smap.get(slope, 0)
                    smap[slope] = area + cellData.area  
                    
    cpdef int nextHruNumber(self):
        """Return a new HRU number for use, incrementing last HRU number used."""
        
        self.lastHru += 1
        return self.lastHru
                    
    cdef int getHruNumber(self, int crop, int soil, int slope):
        """
        Return HRU number (new if necessary, adding one to last hru used for the landscape unit) 
        for the crop/soil/slope combination.
        """
        cdef:
            dict soilSlopeNumbers
            dict slopeNumbers 
            int hru 
        
        soilSlopeNumbers = self.cropSoilSlopeNumbers.get(crop, None)
        if soilSlopeNumbers is None:
            # new crop
            self.lastHru += 1
            slopeNumbers = dict()
            slopeNumbers[slope] = self.lastHru
            soilSlopeNumbers = dict()
            soilSlopeNumbers[soil] = slopeNumbers
            self.cropSoilSlopeNumbers[crop] = soilSlopeNumbers
        else:
            slopeNumbers = soilSlopeNumbers.get(soil, None)
            if slopeNumbers is None:
                # new soil for existing crop
                self.lastHru += 1
                slopeNumbers = dict()
                slopeNumbers[slope] = self.lastHru
                soilSlopeNumbers[soil] = slopeNumbers
            else:
                hru = slopeNumbers.get(slope, -1)
                if hru < 0:
                    # new slope for existing crop and soil
                    self.lastHru += 1
                    slopeNumbers[slope] = self.lastHru
                else:
                    return hru
        return self.lastHru
    
    cpdef LSUData copy(self):
        """Return deep copy of self."""
        
        cdef:
            LSUData result = LSUData()
            
        result.cellCount = self.cellCount
        result.area = self.area
        result.outletElevation = self.outletElevation
        result.sourceElevation = self.sourceElevation
        result.channelLength = self.channelLength
        result.farElevation = self.farElevation
        result.farDistance = self.farDistance
        result.farPointX = self.farPointX
        result.farPointY = self.farPointY
        result.totalElevation = self.totalElevation
        result.totalSlope = self.totalSlope
        result.totalLatitude = self.totalLatitude
        result.totalLongitude = self.totalLongitude
        result.cropSoilSlopeArea = self.cropSoilSlopeArea
        result.hruMap = self.copyHRUMap()
        result.cropSoilSlopeNumbers = self.copyCropSoilSlopeNumbers()
        result.cropAreas = LSUData.copyAreaMap(self.cropAreas)
        result.originalCropAreas = LSUData.copyAreaMap(self.originalCropAreas)
        result.soilAreas = LSUData.copyAreaMap(self.soilAreas)
        result.originalSoilAreas = LSUData.copyAreaMap(self.originalSoilAreas)
        result.slopeAreas = LSUData.copyAreaMap(self.slopeAreas)
        result.originalSlopeAreas = LSUData.copyAreaMap(self.originalSlopeAreas)
        if self.waterBody is not None:
            result.waterBody = self.waterBody.copy()
        result.lastHru = self.lastHru
        return result
    
    cdef dict copyHRUMap(self):
        """Return deep copy of hruMap."""
        
        cdef:
            dict result = dict()
            int hru 
            CellData cellData
            
        for hru, cellData in self.hruMap.items():
            result[hru] = CellData(cellData.cellCount, cellData.area, cellData.totalElevation, 
                                   cellData.totalSlope, cellData.totalLongitude, cellData.totalLatitude, cellData.crop)
        return result
    
    cdef dict copyCropSoilSlopeNumbers(self):
        """Return deep copy of cropSoilSlopeNumbers."""
        
        cdef:
            dict result = dict()
            int crop 
            int soil 
            int slope 
            int hru
            dict soilSlopeNumbers
            dict slopeNumbers
            
        for crop, soilSlopeNumbers in self.cropSoilSlopeNumbers.items():
            result[crop] = dict()
            for soil, slopeNumbers in soilSlopeNumbers.items():
                result[crop][soil] = dict()
                for slope, hru in slopeNumbers.items():
                    result[crop][soil][slope] = hru
        return result
    
    @staticmethod
    cdef dict copyAreaMap(dict amap):
        """Return deep copy of int -> double amap."""
        
        cdef:
            dict result = dict()
            int key
            double val
            
        for key, val in amap.items():
            result[key] = val 
        return result
    
    cpdef void merge(self, LSUData lsuData):
        """Merge lsuData into this data."""
        
        cdef:
            int crop
            int soil
            int slope
            int hru
            int nextHruNum
            dict soilSlopeNumbers
            dict slopeNumbers
        
        self.cellCount += lsuData.cellCount
        self.area += lsuData.area
        # merge is always down, i.e. LSUData is being merged downstream into self
        self.sourceElevation = lsuData.sourceElevation
        if self.farDistance < lsuData.farDistance + self.channelLength:
            self.farElevation = lsuData.farElevation
            self.farPointX = lsuData.farPointX
            self.farPointY = lsuData.farPointY
            self.farDistance = lsuData.farDistance + self.channelLength
        self.channelLength += lsuData.channelLength
        self.totalElevation += lsuData.totalElevation
        self.totalSlope += lsuData.totalSlope
        self.totalLatitude += lsuData.totalLatitude
        self.totalLongitude += lsuData.totalLongitude
        self.cropSoilSlopeArea += lsuData.cropSoilSlopeArea
        for crop, soilSlopeNumbers in lsuData.cropSoilSlopeNumbers.items():
            mySoilSlopeNumbers = self.cropSoilSlopeNumbers.setdefault(crop, dict())
            for soil, slopeNumbers in soilSlopeNumbers.items():
                mySlopeNumbers = mySoilSlopeNumbers.setdefault(soil, dict())
                for slope, hru in slopeNumbers.items():
                    myHru = mySlopeNumbers.get(slope, -1)
                    if myHru < 0:
                        self.lastHru += 1
                        mySlopeNumbers[slope] = self.lastHru
                        self.hruMap[self.lastHru] = lsuData.hruMap[hru]
                    else:
                        self.hruMap[myHru].addCells(lsuData.hruMap[hru])
        LSUData.mergeMaps(self.cropAreas, lsuData.cropAreas)
        LSUData.mergeMaps(self.originalCropAreas, lsuData.originalCropAreas)
        LSUData.mergeMaps(self.soilAreas, lsuData.soilAreas)
        LSUData.mergeMaps(self.originalSoilAreas, lsuData.originalSoilAreas)
        LSUData.mergeMaps(self.slopeAreas, lsuData.slopeAreas)
        LSUData.mergeMaps(self.originalSlopeAreas, lsuData.originalSlopeAreas)
        if self.waterBody is None:
            self.waterBody = lsuData.waterBody
        elif lsuData.waterBody is not None:
            self.waterBody.addWater(lsuData.waterBody, False)
        
    cpdef makeReservoir(self, double threshold):
        """Set water body to a reservoir if water area exceeds threshold percent of LSU."""
       
        if self.waterBody is not None and self.waterBody.area > threshold * self.area / 100:
            self.waterBody.waterRole = _RESERVOIR
        
    @staticmethod
    cdef void mergeMaps(dict map1, dict map2):
        """Add data from map2 to map1.  Two maps assumed to have int domain type and double range type."""
        
        cdef:
            int key
            double val

        for key, val in map2.items():
            if key not in map1:
                map1[key] = val
            else:
                map1[key] += val
    
cdef class BasinData:
    """Data held about subbasin."""
    
    cdef:
        public dict lsus
        public dict mergedLsus
        public double farDistance
        public double minElevation
        public double maxElevation
        public int waterLanduse
    
    def __init__(self, waterLanduse, farDistance):
        """Initialise class variables."""
        ## Map channel -> landscape category -> LSUData
        self.lsus = dict()
        ## results of doing merges
        self.mergedLsus = None
        ## Elevation in metres of lowest point in the subbasin
        self.minElevation = 8849 # everest plus 1
        ## Elevation in metres of highest point in the subbasin
        self.maxElevation =  -419 # dead sea min minus 1
        ## longest flow length to subbasin outlet
        # initialised for existing non-grid watershed to maximum channel flow length
        # otherwise to -1 so later values passed by addCell will update it
        self.farDistance = farDistance
        ## landuse (crop) value for WATR
        self.waterLanduse = waterLanduse
        
    cpdef dict getLsus(self):
        """Return mergedLsus if it exists, else lsus."""
        return self.lsus if self.mergedLsus is None else self.mergedLsus
        
    cpdef void addCell(self, int channel, int landscape, int crop, int soil, int slope, double area, 
                      double elevation, double slopeValue, double distSt, double distCh, double x, double y, object _gv):
        """Add data for 1 cell in watershed grid."""
        
        cdef:
            dict channelData
            ReachData reachData
            LSUData lsuData 
            CellData cellData 
            int hru 
            
        channelData = self.lsus.get(channel, None)
        if channelData is None:
            self.lsus[channel] = dict()
            channelData = self.lsus[channel]
        if landscape in channelData:
            lsuData = channelData[landscape]
        else:
            lsuData = LSUData()
            reachData = _gv.topo.channelsData[channel]
            lsuData.outletElevation = reachData.lowerZ
            lsuData.sourceElevation = reachData.upperZ
            lsuData.channelLength = _gv.topo.channelLengths[channel]
            if _gv.existingWshed:
                lsuData.farDistance = lsuData.channelLength
                lsuData.farElevation = lsuData.sourceElevation
            channelData[landscape] = lsuData
        lsuData.cellCount += 1
        lsuData.area += area
        lsuData.totalLatitude += y
        lsuData.totalLongitude += x
        if slopeValue != _gv.slopeNoData:
            lsuData.totalSlope += slopeValue
        if elevation != _gv.elevationNoData:
            lsuData.totalElevation += elevation
            if distSt != _gv.distStNoData and distSt > self.farDistance:
                # We have found a new  farthest (by flow distance) point from the subbasin outlet:
                # store distance
                self.farDistance = distSt
            if distCh != _gv.distChNoData and distCh > lsuData.farDistance:
                # We have found a new farthest (by flow distance) point from the channel:
                # store distance, its elevation and its location
                lsuData.farDistance = distCh
                lsuData.farElevation = elevation
                lsuData.farPointX = x
                lsuData.farPointY = y
            self.maxElevation = max(self.maxElevation, elevation)
            self.minElevation = min(self.minElevation, elevation)
        if crop == self.waterLanduse:
            if lsuData.waterBody is None:
                lsuData.waterBody = WaterBody(1, area, elevation, x, y)
            else:
                lsuData.waterBody.addCell(area, elevation, x, y)
        if (crop != _gv.cropNoData) and (soil != _gv.soilNoData) and (slopeValue != _gv.slopeNoData):
            lsuData.cropSoilSlopeArea += area
            hru = lsuData.getHruNumber(crop, soil, slope)
            cellData = lsuData.hruMap.get(hru, None)
            if cellData is None:
                # new hru
                cellData = CellData(1, area, elevation, slopeValue, x, y, crop)
                lsuData.hruMap[hru] = cellData
            else:
                cellData.addCell(area, elevation, slopeValue, x, y)
                lsuData.hruMap[hru] = cellData
    
    @staticmethod
    def getHruNumber(dict channelLandscapeCropSoilSlopeNumbers, int lastHru, int channel, int landscape, int crop, int soil, int slope):
        """
        Return HRU number (new if necessary, adding one to current hru count for the landscape unit) 
        for the channel/landscape/crop/soil/slope combination.
        """
        
        cdef:
            int resultHru
            dict cropSoilSlopeNumbers
            dict soilSlopeNumbers
            dict slopeNumbers 
            int hru 
            
        resultHru = lastHru
        landscapeCropSoilSlopeNumbers = channelLandscapeCropSoilSlopeNumbers.get(channel, None)
        if landscapeCropSoilSlopeNumbers is None:
            # new channel
            resultHru += 1
            slopeNumbers = dict()
            slopeNumbers[slope] = resultHru
            soilSlopeNumbers = dict()
            soilSlopeNumbers[soil] = slopeNumbers
            cropSoilSlopeNumbers = dict()
            cropSoilSlopeNumbers[crop] = soilSlopeNumbers
            landscapeCropSoilSlopeNumbers = dict()
            landscapeCropSoilSlopeNumbers[landscape] = cropSoilSlopeNumbers
            channelLandscapeCropSoilSlopeNumbers[channel] = landscapeCropSoilSlopeNumbers
        else:
            cropSoilSlopeNumbers = landscapeCropSoilSlopeNumbers.get(landscape, None)
            if cropSoilSlopeNumbers is None:
                # new landscape unit
                resultHru += 1
                slopeNumbers = dict()
                slopeNumbers[slope] = resultHru
                soilSlopeNumbers = dict()
                soilSlopeNumbers[soil] = slopeNumbers
                cropSoilSlopeNumbers = dict()
                cropSoilSlopeNumbers[crop] = soilSlopeNumbers
                landscapeCropSoilSlopeNumbers[landscape] = cropSoilSlopeNumbers
            else:
                soilSlopeNumbers = cropSoilSlopeNumbers.get(crop, None)
                if soilSlopeNumbers is None:
                    # new crop
                    resultHru += 1
                    slopeNumbers = dict()
                    slopeNumbers[slope] = resultHru
                    soilSlopeNumbers = dict()
                    soilSlopeNumbers[soil] = slopeNumbers
                    cropSoilSlopeNumbers[crop] = soilSlopeNumbers
                else:
                    slopeNumbers = soilSlopeNumbers.get(soil, None)
                    if slopeNumbers is None:
                        # new soil for existing crop
                        resultHru += 1
                        slopeNumbers = dict()
                        slopeNumbers[slope] = resultHru
                        soilSlopeNumbers[soil] = slopeNumbers
                    else:
                        hru = slopeNumbers.get(slope, -1)
                        if hru < 0:
                            # new slope for existing crop and soil
                            resultHru += 1
                            slopeNumbers[slope] = resultHru
                        else:
                            return hru
        return resultHru
    
    cpdef void merge(self, int channel, int target):
        "Merge channel into target.  Assumed both channels initially in domain of mergedLsus.  Finally only target is."
        
        cdef:
            dict channelData
            dict targetData
            int landscape
            LSUData lsuData
            
        channelData = self.mergedLsus[channel]
        targetData = self.mergedLsus[target]
        for landscape, lsuData in channelData.items():
            if landscape in targetData:
                targetData[landscape].merge(lsuData)
            else:
                targetData[landscape] = lsuData
        del self.mergedLsus[channel]
    
    cpdef void setAreas(self, bint isOriginal, list chLinksByLakes, int waterLanduse):
        """Set area maps for crop, soil and slope."""
        
        cdef:
            dict channelData
            LSUData lsuData 
        
        for chLink, channelData in self.getLsus().items():
            for lscape, lsuData in channelData.items():
                if isOriginal:
                    # nodata area is included in final areas: need to add to original
                    # so final and original tally
                    # also remove water bodies that should be incorporated into lakes
                    lsuData.redistributeNodataAndWater(chLink, lscape, chLinksByLakes, waterLanduse)
                    # remove WATR HRUs if the LSU's water body is a reservoir or pond
                    # if lsuData.waterBody is not None and not lsuData.waterBody.isUnknown():
                    #     lsuData.removeWaterHRUs(waterLanduse)
                lsuData.setCropAreas(isOriginal)
                lsuData.setSoilAreas(isOriginal)
                lsuData.setSlopeAreas(isOriginal)
            
    cpdef dict cropAreas(self, bint isOriginal):
        """Return map of crop to area in square metres across subbasin, before HRU calculation if isOriginal."""
        
        cdef:
            dict result = dict()
            dict channelData
            LSUData lsuData 
            dict cropAreas
            int crop 
            double area 
            double cropArea 
            
        for channelData in self.getLsus().itervalues():
            for lsuData in channelData.itervalues():
                cropAreas = lsuData.originalCropAreas if isOriginal else lsuData.cropAreas
                for crop, area in cropAreas.items():
                    cropArea = result.get(crop, 0)
                    result[crop] = cropArea + area
        return result
            
    cpdef dict soilAreas(self, bint isOriginal):
        """Return map of soil to area in square metres across subbasin, before HRIU calculation if isOriginal."""
        
        cdef:
            dict result = dict()
            dict channelData
            LSUData lsuData 
            dict soilAreas
            int soil 
            double area 
            double soilArea 
            
        for channelData in self.getLsus().values():
            for lsuData in channelData.values():
                soilAreas = lsuData.originalSoilAreas if isOriginal else lsuData.soilAreas
                for soil, area in soilAreas.items():
                    soilArea = result.get(soil, 0)
                    result[soil] = soilArea + area
        return result
            
    cpdef dict slopeAreas(self, bint isOriginal):
        """Return map of slope to area in square metres across subbasin, before HRU calculation if isOriginal."""
        
        cdef:
            dict result = dict()
            dict channelData
            LSUData lsuData 
            dict slopeAreas
            int slope 
            double area 
            double slopeArea 
            
        for channelData in self.getLsus().values():
            for lsuData in channelData.values():
                slopeAreas = lsuData.originalSlopeAreas if isOriginal else lsuData.slopeAreas
                for slope, area in slopeAreas.items():
                    slopeArea = result.get(slope, 0)
                    result[slope] = slopeArea + area
        return result
    
    cpdef int subbasinCellCount(self):
        """Return total cell count of all landscape units in the subbasin."""
        
        cdef:
            int count = 0
            dict channelData
            LSUData lsuData 
            
        for channelData in self.getLsus().values():
            for lsuData in channelData.values():
                count += lsuData.cellCount
        return count
    
    cpdef double subbasinArea(self):
        """Return total area of the subbasin (land and water) in square metres."""
        
        cdef:
            double area = 0
            dict channelData
            LSUData lsuData 
            
        for channelData in self.getLsus().values():
            for lsuData in channelData.values():
                area += lsuData.area
        return area
    
    cpdef double totalElevation(self):
        """Total elevation of all pixels in subbasin."""
        cdef: 
            double totalEl = 0
            dict channelData
            LSUData lsuData 
        
        for channelData in self.getLsus().values():
            for lsuData in channelData.values():
                totalEl += lsuData.totalElevation
        return totalEl
    
    cpdef double totalSlope(self):
        """Total slope of all pixels in subbasin."""
        cdef:
            double totalSl = 0
            dict channelData
            LSUData lsuData 
        
        for channelData in self.getLsus().values():
            for lsuData in channelData.values():
                totalSl += lsuData.totalSlope
        return totalSl
    
    cpdef void copyLsus(self):
        """Make deep copy mergedLsus of lsus.  deepcopy in copy module does not do this adequately."""
        
        cdef:
            int channel 
            int landscape
            dict channelData
            LSUData lsuData
        
        self.mergedLsus = dict()
        for channel, channelData in self.lsus.items():
            self.mergedLsus[channel] = dict()
            for landscape, lsuData in channelData.items():
                self.mergedLsus[channel][landscape] = lsuData.copy()
    
    @staticmethod
    def channelArea(dict channelData):
        """Return area (land and water) draining to channel: the sum of the areas of the channel's landscape units."""
        
        cdef:
            double areaCh = 0
            LSUData lsuData 
        
        for lsuData in channelData.values():
            areaCh += lsuData.area
        return areaCh       
    
    @staticmethod
    def dominantKey(dict table):
        '''Find the dominant key for a dictionary table of numeric values, 
        i.e. the key to the largest value.  Values are assumed to be non-negative.
        '''
        cdef:
            int maxKey = -1
            double maxVal = 0
            int key 
            double val 
            
        for (key, val) in table.items():
            if val > maxVal:
                maxKey = key
                maxVal = val
        return maxKey, maxVal

cdef class ReachData:
    """Location and elevation of points at ends of reach, 
    draining from upper to lower.
    """
    
    cdef:
        public double upperX
        public double upperY
        public double upperZ
        public double lowerX
        public double lowerY
        public double lowerZ
        
    def __init__(self, double x1, double y1, double z1, double x2, double y2, double z2):
        """Initialise class variables."""
        ## x coordinate of upper end
        self.upperX = x1
        ## y coordinate of upper end
        self.upperY = y1
        ## elevation of upper end
        self.upperZ = z1
        ## x coordinate of lower end
        self.lowerX = x2
        ## y coordinate of lower end
        self.lowerY = y2
        ## elevation of lower end
        self.lowerZ = z2
        
cdef class MergedChannelData:
    """Drainage area in square metres, length in metres, and slope in m/m for a collection of merged channels.
    """
    
    cdef:
        public double areaC
        public double length
        public double slope
        public double minEl
        public double maxEl
    
    def __init__(self, double areaC, double length, double slope, double minEl, double maxEl):
        """Initialise class variables for first channel."""
        ## total drainage area in square metres
        self.areaC = areaC
        ## total length in metres
        self.length = length
        ## mean slope in m/m for merged channels
        self.slope = slope
        ## minimum elevation in metres
        self.minEl = minEl
        ## maximum elevation in metres
        self.maxEl = maxEl
        
    cpdef void add(self, double areaC, double length, double slope, double minEl, double maxEl):
        """Add a channel's data."""
        self.areaC = max(self.areaC, areaC)
        if length > 0:
            newLength = self.length + length
            self.slope = (self.slope * self.length + slope * length) / newLength
            self.length = newLength
        self.minEl = min(self.minEl, minEl)
        self.maxEl = max(self.maxEl, maxEl)
        
cdef class LakeData:
    """Data about lake defined by shapefile."""
    
    cdef:
        public dict inChLinks
        public set lakeChLinks
        public int outChLink
        public tuple outPoint
        public set otherOutChLinks
        public double area
        public double elevation
        public object centroid
        public int waterRole
        
    def __init__(self, area, centroid, waterRole):
        ## linknos of inflowing channels mapped to point id, point and elevation of channel outlet
        self.inChLinks = dict()
        ## linknos of channels within lake
        self.lakeChLinks = set()
        ## linkno of outflowing stream. -1 means no outlet stream; outlet is a main outlet
        self.outChLink = -1
        ## subbasin, point id, point and elevation of outflow point
        self.outPoint = (-1, -1, None, 0)
        ## linknos of other outflowing channels
        self.otherOutChLinks = set()
        ## area in square metres
        self.area = area
        ## elvation (mean elevation of incoming stream outlets)
        self.elevation = 0
        ##centroid
        self.centroid = centroid
        ## pond or reservoir
        self.waterRole = waterRole
        
        
