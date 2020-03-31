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
# Based closely on GDALRasterPolygonEnumeratorT and GDAL's polygonize, for which many thanks.

# Differences from GDAL:
# 1. Incoming rows are only read once
# 2. Multipolygons are created instead of collections of polygons.  This is necessary for HRUs shapefiles
#    so that selecting a shape will select the whole HRU.
# Number 2 above precludes writng plygons as they are completed, so this uses more memory than GDAL.
#
# Connected8 did not work properly originally, in the sense of creating OGR-valid polygons:
# 1.  The pattern
#  X Y
#  Y X
#  left the X polygons unconnected unless left links are delayed until all right links for the second row are done.
#  This has been fixed by doing all left links after the row has been otherwise completed.
# 2.  The pattern
#  X Y X   and the pattern  X Y Y X
#  Y X Y                    Y X X Y
#  left the polygon for the upper right X unconnected to the polygon for the other Xs
#  because the right link above the (second) lower X needs to be connected at both ends when it is added.
#  This has also been fixed by checking if adding a right link can join two rings

# cython: language_level=3

from qgis.core import * # @UnusedWildImport

from collections import deque
import numpy as np
cimport numpy as np
import os

cpdef str ringToString(object ring):

    cdef:
        str res
        Vertex v1, v2
        
    res = vertexToString(ring[0]) + ': '
    for i in range(len(ring) - 1):
        v1 = ring[i]
        v2 = ring[i+1]
        if v1.x == v2.x:
            if v1.y > v2.y: res += 'u'*(v1.y - v2.y)
            else: res += 'd'*(v2.y - v1.y)
        elif v1.x > v2.x: res += 'l'*(v1.x - v2.x)
        else: res += 'r'*(v2.x - v1.x)
    return res

cpdef bint isClockwise(object ring):
    """A ring is clockwise if its leftmost vertical edge is directed up."""
    cdef: 
        int minx
        int y1 = 0
        int y2 = 0
        Vertex v1, v2
    
    if ring is None or len(ring) < 4:
        return False    
    ring = iter(ring)
    v1 = next(ring)
    # make v1 the first candidate
    minx = v1.x + 1
    try:
        while True:
            if v1.x < minx:
                v2 = next(ring)
                if v2.x == v1.x:
                    y1 = v1.y
                    y2 = v2.y
                    minx = v1.x
                v1 = v2
            else:
                v1 = next(ring)
    except StopIteration:
        return y1 > y2  
    
cpdef bint isClosed(object ring):   
    """Check last vertex == first."""
    cdef Vertex firstv, lastv
    
    if ring is None or len(ring) < 4:
        return False
    firstv = ring[0]
    lastv = ring[-1]
    return firstv.x == lastv.x and firstv.y == lastv.y


cdef struct Vertex:
    int x
    int y    

cdef str vertexToString(Vertex v):
    """Represent vertex as string."""
    return '(' + str(v.x) + ',' + str(v.y) + ')'

cdef class Polygon:

    """A polygon is a list of deques of vertices.  During construction these may not be closed.
    
    The front deque is or will become the outer ring."""

    cdef:
        readonly list rings
        bint connected4
        object fw
        
    """Class to hold possibly partially formed polygons."""
    def __init__(self, connected4, fw):
        """Initialise."""
        self.rings = []
        self.connected4 = connected4
        self.fw = fw
        
    def __str__(self):
    
        cdef:
            str res
            object ring
        
        res = ''
        for ring in self.rings:
            if ring is not None:
                res += ringToString(ring) 
            else:
                res += 'empty'
            res += '  '
        return res
        
    cpdef void coalesce(self):
        """Try to merge segments."""
        cdef:
            int iBase, i, todoCount
            object base, ring 
            bint mergeHappened
            Vertex lastv, firstv
            
        for iBase in range(len(self.rings)):
            base = self.rings[iBase]
            if base is not None:
                mergeHappened = True
                # try to merge into base until no mergers have happened
                while mergeHappened:
                    mergeHappened = False
                    for i in range(iBase+1, len(self.rings)):
                        ring = self.rings[i]
                        if ring is not None:
                            lastv = base[-1]
                            firstv = ring[0]
                            if lastv.x == firstv.x and lastv.y == firstv.y:
                                #self.fw.writeFlush('Append')
                                self.join(base, ring, iBase, True)
                                # use None rather than delete to avoid for loop crashing
                                self.rings[i] = None 
                                mergeHappened = True
                                #self.fw.writeFlush(str(self))
                            else:
                                lastv = ring[-1]
                                firstv = base[0]
                                if lastv.x == firstv.x and lastv.y == firstv.y:
                                    #self.fw.writeFlush('Prepend')
                                    self.join(ring, base, iBase, False)
                                    # base needs redefining to new value
                                    base = self.rings[iBase]
                                    self.rings[i] = None
                                    mergeHappened = True
                                    #self.fw.writeFlush(str(self))
                            
        # remove places in list of rings for merged rings
        self.rings = [ring for ring in self.rings if ring is not None]
        # rings should now be closed
        for ring in self.rings:
            assert isClosed(ring), 'Failed to close ring {0}'.format(ringToString(ring)) 
            
        # make sure first ring is clockwise
        # todoCount guards against looping if no ring is clockwise
        todoCount = len(self.rings)
        while todoCount >= 0:
            ring = self.rings[0]
            if isClockwise(ring):
                break
            self.rings.pop(0)
            self.rings.append(ring)
            todoCount -= 1
        if todoCount == 0:
            raise ValueError('No clockwise ring in polygon {0}'.format(str(self)))
            
    cdef void join(self, object firstl, object secondl, int i, bint inPlace):
        """Append second to front. Store at index i, unless inPlace"""
        
        # remove and discard last vertex of first, then extend with second
        _ = firstl.pop()
#         self.fw.writeFlush('After pop')
#         self.fw.writeFlush(str(firstl))
#         self.fw.writeFlush((str(self)))
        firstl.extend(secondl)
#         self.fw.writeFlush('After extend')
#         self.fw.writeFlush(str(firstl))
#         self.fw.writeFlush((str(self)))
        if not inPlace:
            self.rings[i] = firstl
#         self.fw.writeFlush('After assigment')
#         self.fw.writeFlush((str(self)))
            
    cpdef void addLink(self, Vertex p1, Vertex p2):
        """Add a link running from p1 to p2."""
        cdef:
            object ring
            int i
            Vertex firstv, lastv, penult, second
            
        for i in range(len(self.rings)):
            ring = self.rings[i]
            if self.connected4 and isClosed(ring):
                # with connected4 a closed ring cannot be added to
                continue
            # if a ring currently runs to p1, append p2
            lastv = ring[-1]
            if lastv.x == p1.x and lastv.y == p1.y:
                # add p2, or replace last with p2 if previous link in same direction
                # note this direction test assumes links are either horizontal or vertical
                penult = ring[-2]
                if penult.x == lastv.x and lastv.x == p2.x or \
                    penult.y == lastv.y and lastv.y == p2.y:
                    ring[-1] = p2
                else:
                    ring.append(p2)
                if not self.connected4 and p1.x < p2.x and p1.y == p2.y:
                    # with connected 8 a right link can join two down links in the previous row
                    # look for a ring starting at p2 and if found append to the current ring
                    for i2 in range(len(self.rings)):
                        if i2 != i: # probably can't happen but to be safe from self destruction
                            ring2 = self.rings[i2]
                            firstv = ring2[0]
                            if firstv.x == p2.x and firstv.y == p2.y:
                                _ = ring.pop()
                                ring.extend(ring2)
                                del self.rings[i2]
                                break
                                # now important not to resume outer loop based on indexes of self.rings
                                # as we just deleted an item, so don't remove the return two lines below
                #self.fw.writeFlush((str(self)))
                return
            else:
                # if a ring starts from p2, prepend with p1
                firstv = ring[0]
                if firstv.x == p2.x and firstv.y == p2.y:
                    # prepend p1, or replace first with p1 if ring link in same direction
                    # note this direction test assumes links are either horizontal or vertical
                    second = ring[1]
                    if second.x == firstv.x and firstv.x == p1.x or \
                        second.y == firstv.y and firstv.y == p1.y:
                        ring[0] = p1
                    else:
                        ring.appendleft(p1)
                    #self.fw.writeFlush((str(self)))
                    return
        # no existing segment found - make a new one
        self.rings.append(deque([p1, p2]))
        #self.fw.writeFlush((str(self))) 
        
    cpdef void addPoly(self, Polygon poly):
        """Add poly's rings, joining with this one's where possible."""
        cdef:
            object polyRing, ring
            Vertex polyFirst, polyLast, firstv, lastv
            int iPoly, i
        
        for iPoly in range(len(poly.rings)):
            polyRing = poly.rings[iPoly]
            polyFirst = polyRing[0]
            polyLast = polyRing[-1]
            if self.connected4 and polyFirst.x == polyLast.x and polyFirst.y == polyLast.y:
                # closed ring when using 4connectdness cannot be joined to another
                continue
            for i in range(len(self.rings)):
                ring = self.rings[i]
                firstv = ring[0]
                lastv = ring[-1]
                if self.connected4 and firstv.x == lastv.x and firstv.y == lastv.y: 
                    continue
                if lastv.x == polyFirst.x and lastv.y == polyFirst.y:
                    self.join(ring, polyRing, i, True)
                    poly.rings[iPoly] = None
                    break
                if firstv.x == polyLast.x and firstv.y == polyLast.y:
                    self.join(polyRing, ring, i, False)
                    poly.rings[iPoly] = None
                    break
        # add what is left as new rings
        self.rings.extend([ring for ring in poly.rings if ring is not None])
        # clean up
        poly.rings = None   
             
cdef class Shape:
    """A shape is a collection of polygons."""
    
    cdef:
        int nextPolyId
        readonly dict polygons
        dict polyIdMap
        bint connected4
        object fw
        public int cellCount
        
    def __init__(self, bint connected4, object fw):
        ## next identifier for a polygon 
        self.nextPolyId = 0
        ## map polyId -> Polygon
        self.polygons = dict()
        ## map polyId -> PolyId to keep track of mergers 
        # has properties:
        # 1: all used polyIds are in its domain
        # 2: that one lookup is always enough for the final result. i.e.
        # for every range value x, x -> x is in the map
        self.polyIdMap = dict()
        ## using 4 connectedness
        self.connected4 = connected4
        ## cell count
        self.cellCount = 0
        self.fw = fw
        
    def __str__(self):
    
        cdef:
            str res
            Polygon poly
        
        res = ''
        for poly in self.polygons.values():
            res += str(poly) 
            res += os.linesep
        return res
        
    cpdef int newPoly(self):
        """Add a new empty polygon and return its id."""
        cdef int polyId = self.nextPolyId
        
        self.polygons[polyId] = Polygon(self.connected4, self.fw)
        self.polyIdMap[polyId] = polyId
        self.nextPolyId += 1 
        return polyId 
    
    cpdef void checkMerge(self, int dest, int src):
        """If dest and src refer to different polygons, add the src polygon to the dest polygon and map src to dest."""
        cdef:
            int finalDest, final2, temp
        
        # short cut for common situation
        #self.fw.writeFlush('Checking dest {0} and src {1}'.format(dest, src))
        if dest == src:
            return
        finalDest = self.polyIdMap[dest]
        finalSrc = self.polyIdMap[src]
        #self.fw.writeFlush('finalDest is {0} and finalSrc is {1}'.format(finalDest, finalSrc))
        if finalDest == finalSrc:
            return
        # we need to map finalSrc to finalDest
        # and all targets of finalSrc must be changed to finalDest
        for nextSrc, nextTarg in self.polyIdMap.items():
            if nextTarg == finalSrc:
                self.polyIdMap[nextSrc] = finalDest
        #self.fw.writeFlush('PolyIdMap is {0}'.format(str(self.polyIdMap)))
        #self.fw.writeFlush('Polygons has keys {0}'.format(str(self.polygons.keys())))
        self.polygons[finalDest].addPoly(self.polygons[finalSrc])
        del self.polygons[finalSrc]   
        
    cpdef void addLink(self, int polyId, Vertex v1, Vertex v2):
        """Add a link to the polygon identifed by polyId."""
        
        self.polygons[self.polyIdMap[polyId]].addLink(v1, v2)  
        
    cpdef void  coalesce(self):     
        """Coalesce all polygons."""
        cdef Polygon poly
        
        for poly in self.polygons.values():
            #self.fw.writeFlush('Before coalesce: {0}'.format(str(poly)))
            poly.coalesce()
            #self.fw.writeFlush('After coalesce: {0}'.format(str(poly)))
                
cdef class Offset:
        
    """Holds data about conversion of grid vertices to geographic points, 
    and provides functions to calculate shape areas and geometries"""
    
    cdef:
        object origin
        double dx
        double dy
        double unitArea
        
    def __init__(self, object p, double dx, double dy):
        """Constructor."""
        ## origin
        self.origin = p
        ## x dimension of grid
        self.dx = dx
        ## y dimension of grid
        self.dy = dy
        ## area of grid cell (dx * dy)
        self.unitArea = dx * dy
        
    cdef vertexToPoint(self, Vertex v):
        """Generate a point from a Vertex."""
        return QgsPointXY(self.origin.x() + self.dx * v.x, self.origin.y() - self.dy * v.y)
        
    cpdef double area(self, Shape shape):
        """Convert the cell count to an area in square metres."""
        return shape.cellCount * self.unitArea
        
    cdef object ringToPointsRing(self, object ring):
        """Convert a ring to a ring of points."""
        return [self.vertexToPoint(v) for v in ring]
    
    cdef object ringsToPointsRings(self, list inrings):
        """Convert a list of rings to a list of points rings."""
        return [self.ringToPointsRing(inring) for inring in inrings]
    
    cdef object polygonsToPointsPolygons(self, object inpolys):
        """convert a list of polygons to a list of points polygons."""
        return [self.ringsToPointsRings(inpoly.rings) for inpoly in inpolys]
        
    cpdef object makeGeometry(self, Shape shape):
        """Create a multi-polygon geometry from a list of polygons."""
        return QgsGeometry.fromMultiPolygonXY(self.polygonsToPointsPolygons(shape.polygons.values()))

cdef class Polygonize:

    cdef:
        np.ndarray lastVals
        np.ndarray thisVals
        np.ndarray lastIds
        np.ndarray thisIds
        int rowNum
        int length
        readonly dict shapes
        bint connected4
        int noData
        Offset offset
        object fw
        
    def __init__(self, bint connected4, int numCols, int noData, object p, double dX, double dY, object fw=None):
        ## length of arrays is number of values in one row plus 2: we have noData at each end
        ## (not strictly necessary for id rows, but easier to use same indices)
        self.length = numCols + 2
        ## values data from last row read
        self.lastVals = np.empty([self.length], dtype=int)
        ## values data from current row read
        self.thisVals = np.full([self.length], noData, dtype=int)
        ## polygon ids in last row
        self.lastIds = np.empty([self.length], dtype=int)
        ## polygon ids in this row
        self.thisIds = np.full([self.length], -1, dtype=int)
        ## current row number
        self.rowNum = 0
        ## mapping from value to shape
        self.shapes = dict()
        ## flag to show if using 4connectedness (or, if false, 8)
        self.connected4 = connected4
        ## noData value
        self.noData = noData
        ## offset object for drawing shapes
        self.offset = Offset(p, dX, dY)
        self.fw = fw
        
    cpdef addRow(self, np.ndarray[np.int_t] row, int rowNum):
        """Add a row."""
        
        cdef:
            int i
            bint thisIdDone
            Vertex v1, v2
            list leftLinks
        
        self.lastVals = np.copy(self.thisVals)
        self.lastIds = np.copy(self.thisIds)
        self.rowNum = rowNum
        # preserve nodata values at each end of row
        self.thisVals[1:self.length-1] = row
        #self.fw.writeFlush('lastVals: {0}'.format(str(self.lastVals)))
        #self.fw.writeFlush('thisVals: {0}'.format(str(self.thisVals)))
        # first pass along row: assign polygon ids
        for i in range(1, self.length-1):
            # val and id arrays have an initial noData/-1 value
            # so index into input row is one less than arrays index
            colNum = i - 1
            thisIdDone = False
            thisVal = self.thisVals[i]
            if thisVal != self.noData:
                shape = self.shapes.get(thisVal, Shape(self.connected4, self.fw))
                if thisVal == self.thisVals[i-1]:
                    self.thisIds[i] = self.thisIds[i-1]
                    #self.fw.writeFlush('Id for value {3} at ({0}, {1}) set to {2} from left'.format(colNum, rowNum, self.thisIds[i], thisVal))
                    thisIdDone = True
                if thisVal == self.lastVals[i]:
                    if thisIdDone:
                        shape.checkMerge(self.thisIds[i], self.lastIds[i])
                    else:
                        self.thisIds[i] = self.lastIds[i]
                        #self.fw.writeFlush('Id for value {3} at ({0}, {1}) set to {2} from last'.format(colNum, rowNum, self.thisIds[i], thisVal))
                        thisIdDone = True
                if not self.connected4 and thisVal == self.lastVals[i-1]:
                    if thisIdDone:
                        shape.checkMerge(self.thisIds[i], self.lastIds[i-1])
                    else:
                        self.thisIds[i] = self.lastIds[i-1]
                        #self.fw.writeFlush('Id for value {3} at ({0}, {1}) set to {2} from last left'.format(colNum, rowNum, self.thisIds[i], thisVal))
                        thisIdDone = True
                if not self.connected4 and thisVal == self.lastVals[i+1]:
                    if thisIdDone:
                        shape.checkMerge(self.thisIds[i], self.lastIds[i+1])
                    else:
                        self.thisIds[i] = self.lastIds[i+1]
                        #self.fw.writeFlush('Id for value {3} at ({0}, {1}) set to {2} from last right'.format(colNum, rowNum, self.thisIds[i], thisVal))
                        thisIdDone = True
                if not thisIdDone:
                    self.thisIds[i] = shape.newPoly()
                    #self.fw.writeFlush('Id for value {3} at ({0}, {1}) set to new {2}'.format(colNum, rowNum, self.thisIds[i], thisVal))
                self.shapes[thisVal] = shape
        #self.fw.writeFlush('thisIds: {0}'.format(str(self.thisIds)))
        # with 8 connectedness need to delay inserting left links to avoid failure to attach
        # upper left to lower right polygons. so we record them and attach after rest of row
        leftLinks = []
        # add edges to polygons and count cells
        for i in range(0, self.length-1):
            thisVal = self.thisVals[i]
            lastVal = self.lastVals[i]
            nextVal = self.thisVals[i+1]
            # val and id arrays have an initial noData/-1 value
            # so index into input row is one less than arrays index
            colNum = i - 1
            if thisVal != self.noData:
                shape = self.shapes[thisVal]
                shape.cellCount += 1
            if thisVal != lastVal:
                v1 = Vertex(colNum, rowNum)
                v2 = Vertex(colNum+1, rowNum)
                if thisVal != self.noData:
                    shape.addLink(self.thisIds[i], v1, v2) # r
                if lastVal != self.noData:
                    if self.connected4:
                        self.shapes[lastVal].addLink(self.lastIds[i], v2, v1) # l
                    else:
                        # defer adding left link 
                        leftLinks.append((lastVal, self.lastIds[i], v2, v1))
            if thisVal != nextVal:
                v1 = Vertex(colNum+1, rowNum)
                v2 = Vertex(colNum+1, rowNum+1)
                if thisVal != self.noData:
                    shape.addLink(self.thisIds[i], v1, v2) # d
                if nextVal != self.noData:
                    self.shapes[nextVal].addLink(self.thisIds[i+1], v2, v1) # u
        for (val, id, v2, v1) in leftLinks:
            self.shapes[val].addLink(id, v2, v1)
        leftLinks = []
#         self.fw.writeFlush('Polygon keys {0}'.format(str(self.polygons.keys())))
#         for poly in self.polygons.values():
#             self.fw.writeFlush(str(poly))
                            
    cpdef finish(self):
        """Coalesce all polygons.  Collect polygons for each value into a shape."""
        cdef:
            Polygon poly 
            Shape shape 
            int val, i
            Vertex v1, v2
            
        # add links for final row
        for i in range(1, self.length-1):
            thisVal = self.thisVals[i]
            if thisVal != self.noData:
                colNum = i - 1
                v1 = Vertex(colNum+1, self.rowNum+1)
                v2 = Vertex(colNum, self.rowNum+1)
                self.shapes[thisVal].addLink(self.thisIds[i], v1, v2)
                
        for shape in self.shapes.values():
            shape.coalesce()
            
        #self.fw.writeFlush(self.shapesToString())
            
    cpdef object getGeometry(self, int val):
        """Return geometry for shape for val."""
        cdef Shape shape
       
        shape = self.shapes.get(val, None)
        if shape is None:
            return None
        return self.offset.makeGeometry(shape)
    
    cpdef str shapesToString(self):
        """Return string for all shapes."""
        cdef:
            int val 
            Shape shape
            str res = ''
            
        for val, shape in self.shapes.items():
            res += 'Shape for value {0}:'.format(val) 
            res += str(shape)
        return res  
    
    cpdef int cellCount(self, int val):
        """Return total cell count for val."""
        cdef:
            Shape shape
        
        shape = self.shapes.get(val, None)
        if shape is None:
            return 0
        return shape.cellCount
    
    cpdef double area(self, int val):
        """Return area for val in square metres."""
        cdef:
            Shape shape
        
        shape = self.shapes.get(val, None)
        if shape is None:
            return 0
        return self.offset.area(shape)
        
        



































