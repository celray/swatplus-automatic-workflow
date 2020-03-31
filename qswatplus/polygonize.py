1# -*- coding: utf-8 -*-
'''
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
 *   This program is free software you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
'''
# Import the PyQt and QGIS libraries
from PyQt5.QtCore import *  # @UnusedWildImport
from PyQt5.QtGui import *  # @UnusedWildImport
from qgis.core import * # @UnusedWildImport
from qgis.gui import * # @UnusedWildImport
# from multiprocessing import Pool
import time
from .QSWATUtils import QSWATUtils


    
    ## Convert grids to rectilinear polygons.
    #
    # Rectilinear polygons are polygons with only vertical or horizontal lines in their perimeters.
    # Lists of rectilinear  polygons are the parts of a shape.
    # Each collection of parts is associated with a particular integer index,
    # representing a particular grid value.
    # The algorithm to make the polygons from a grid of cells,
    # each polygon indexed by the grid value it belongs to is:
    # 1. Make the basic (horizontal) boxes for each index.  
    # These boxes are unit height and integer width, and located by row and column number,
    # so that the nxt two steps only require integer arithmetic.
    # 2. Merge the boxes for each index
    # 3. Make the holes for each index
    # 4. Convert the polygons into lists of points, the format for a shape in a shapefile
    # Note that grids have the origin at the top left, 
    # so down direction for example corresponds to an increasing y value, 
    # and right corresponds to an increasing x value.
class Polygonize:
    
    ## directions
    # note that the definition of reverse uses the integer encoding: beware of changing it
    _UP = 0
    _RIGHT = 1
    _DOWN = 2
    _LEFT = 3
    
    def __init__(self, p, dX, dY):
        """Initialise class variables."""
        ## shapes data
        self.shapesTable = dict()
        ## Top left corner and dimensions of grid
        self.offset = Polygonize.OffSet(p, dX, dY)
        ## last error message
        self.lastError = ''
        
    ## Links are unit length directed lines, positioned in a cartesian grid using integer coordinates.
    #
    # Links are modeled as triples, (column, row, direction) where (column, row) is the start point of the link
       
    @staticmethod
    def reverse(d):
        """Return the reverse of direction.  This uses the encoding of directions as integers modulo 4."""
        return (d + 2) % 4
    
    @staticmethod
    def dc(d):
        """Return a character indicating the direction."""
        if d == Polygonize._UP:
            return 'u'
        elif d == Polygonize._DOWN:
            return 'd'
        elif d == Polygonize._LEFT:
            return 'l'
        else:
            return 'r'
    
    @staticmethod
    def finish(link):
        """Return the finish point of a link."""
        (x,y,d) = link
        if d == Polygonize._UP:
            return (x, y-1)
        elif d == Polygonize._DOWN:
            return (x, y+1)
        elif d == Polygonize._LEFT:
            return (x-1, y)
        else:
            return (x+1, y)
            
    @staticmethod
    ## return true if one link is the complement (reversal) of the other
    #
    # we only need to be concerned with left-right links  because initial boxes 
    # consumed any up-down complementary links
    def complements(link1, link2):
        (x1,y1,d1) = link1
        (x2, y2, d2) = link2
        if d1 == Polygonize._LEFT and d2 == Polygonize._RIGHT and x1 == x2 + 1 and y1 == y2:
            return True
        if d1 == Polygonize._RIGHT and d2 == Polygonize._LEFT and x1 == x2 - 1 and y1 == y2:
            return True
        return False
#         return d1 == Polygonize.reverse(d2) and (x1, y1) == Polygonize.finish((x2, y2, d2))
    
    @staticmethod
    def continues(link1, link2):
        """Return true if second link continues the first."""
        (x2,y2,_) = link2
        return Polygonize.finish(link1) == (x2,y2)
       
    @staticmethod
    def disjoint(bounds1, bounds2):
        """Return true if the rectangles do not touch or overlap."""
        (xmin1, xmax1, ymin1, ymax1) = bounds1
        (xmin2, xmax2, ymin2, ymax2) = bounds2
        return xmin1 > xmax2 or xmin2 > xmax1 or ymin1 > ymax2 or ymin2 > ymax1  
        
    class Ring:
        
        """A ring is stored as a chain of links forming its perimeter, plus its bounds."""
        
        def __init__(self, perimeter, bounds):
            """Constructor."""
            ## chain of links forming perimeter of ring
            self.perimeter = perimeter
            ## extent of ring: tuple (xmin, xmax, ymin, ymax)
            self.bounds = bounds
            
    @staticmethod
    def findIndex(p, start, finish, f):
        """
        Return the first index of p in range(start, finish) for which the item satisfies the predicate f, else -1.
        
        Assumes start .. finish-1 is a subrange of the indexes of l
        """
        for i in  range(start, finish):
            if f(p[i]):
                return i
        return -1
            
    @staticmethod
    def boxToRing(box):
        """Make a ring from a box to top left corner at (x,y), width width, and depth 1."""
        (x, y, width) = box
        perimeter = []
        for i in range(width):
            perimeter.append((x+i, y, Polygonize._RIGHT))
        perimeter.append((x + width, y, Polygonize._DOWN))
        for i in range(width, 0, -1):
            perimeter.append((x + i, y + 1, Polygonize._LEFT))
        perimeter.append((x, y+1, Polygonize._UP))
        return Polygonize.Ring(perimeter, (x, x + width, y, y + 1))
                        
    @staticmethod
    def merge(p1, i1, p2, i2):
        """
        Make a single ring from two rings with a common point.
        
        Start points of links at index i1 of p1 and index i2 of p2 are the same.
        Also removes complementary links in the result.
        """
        len2 = len(p2.perimeter)
        l = p1.perimeter[:i1]
        l.extend(p2.perimeter[i2:])
        l.extend(p2.perimeter[:i2])
        l.extend(p1.perimeter[i1:])
        # Can get complementary pairs at the joins, so we remove them.
        Polygonize.removePairs(l, i1 + len2 - 1)
        # j = Polygonize.findComplements(l)
        # if j >= 0:
        #     len1 = len(p1.perimeter)
        #     QSWATUtils.information('Merge at {0!s} length {1!s} and {2!s} length {3!s} leaves pair at {4!s}'.format(i1, len1, i2, len2, j), False)
        xmin1, xmax1, ymin1, ymax1 = p1.bounds
        xmin2, xmax2, ymin2, ymax2 = p2.bounds
        return Polygonize.Ring(l, (min(xmin1,xmin2), max(xmax1,xmax2), min(ymin1,ymin2), max(ymax1,ymax2)))

    @staticmethod
    def canMerge(p1, p2):
        """Return indexes i1 and i2 for starts of links in p1 and p2 which are the same point, if any, else (-1,-1)."""
        if Polygonize.disjoint(p1.bounds, p2.bounds):
            return (-1, -1)
        for i1 in range(len(p1.perimeter)):
            x, y, _ = p1.perimeter[i1]
            f = lambda lnk: x == lnk[0] and y == lnk[1]
            i2 = Polygonize.findIndex(p2.perimeter, 0, len(p2.perimeter), f)
            if i2 >= 0:
                return(i1, i2)
        return (-1, -1)

    @staticmethod
    def removePairs(l, i):
        """
        If links at indexes i and i+1 are complementary, remove them.
        
        Recurses on links originally at i-1 and i+2 if i > 0 and i < len(l) - 2
        Precondition: 0 <= i < len(l) - 1, ie i and i+1 are indexes of l.
        """
        limit = len(l) - 1
        assert 0 <= i < limit
        if Polygonize.complements(l[i], l[i+1]):
            del l[i:i+2]
            if 0 < i < limit - 1:
                Polygonize.removePairs(l, i-1)

    @staticmethod
    def removeFirstLast(l):
        """Remove the first and last links if they complement, and repeat."""
        while len(l) > 0 and Polygonize.complements(l[0], l[-1]):
            del l[-1]
            del l[0]
            
    @staticmethod
    def rotate(l):
        """
        Move first point to back while first and last have same direction
        
        If a chain of links representing a closed polygon
        has the first and last links the same direction,
        this function puts the head of the chain to the back, and repeats.
        This does not affect the polygon, but will reduce by one
        the number of points representing it.
        """
        assert len(l) > 1
        _, _, d1 = l[0]
        _, _, d2 = l[-1]
        if d1 == d2:
            link = l.pop(0)
            l.append(link)
            Polygonize.rotate(l)
            
    @staticmethod
    def makeHole(l, first, last):
        """
        Remove a hole from a list of links and return it
        
        List l has a link at first complemented by a link at last,
        where first+1 less than last, or first greater than last, with first-last less than len(l) 
        This removes first to last inclusive
        and makes a hole which is the list from first+1 to last-1 inclusive,
        where if last less than first this means first+1 to end plus 0 to last-1.
        If the complementary links are adjacent the hole will be None.
        Note that last may be less than first.
        """
        if first+1 < last:
            hole = l[first + 1 : last]
            del l[first : last + 1]
        elif first > last:
            hole = l[first + 1:]
            del l[first:]
            hole.extend(l[:last])
            del l[:last + 1]
        else:
            return None
        # holes often have complementary initial and final links
        Polygonize.removeFirstLast(hole)
        if len(hole) == 0:
            return None
        #=======================================================================
        # for debugging
        # if not Polygonize.checkClosed(hole):
        #     QSWATUtils.information('Hole at first {0!s} last {1!s} is not closed'.format(first, last), False)
        # if not Polygonize.checkClosed(l):
        #     QSWATUtils.information('Polygon after removing hole at first {0!s} last {1!s} is not closed'.format(first, last), False)
        # if len(hole) < 4:
        #     QSWATUtils.information('Hole {0!s} made at ({1!s}, {2!s})'.format(hole, first, last), False) 
        # j = Polygonize.findComplements(l)
        # if j >= 0:
        #     QSWATUtils.information('Making hole at first {0!s} last {1!s} leaves pair at {2!s}'.format(first, last, j), False)
        # k = Polygonize.findComplements(hole)
        # if k >= 0:
        #     QSWATUtils.information('Making hole at first {0!s} last {1!s} leaves pair at {2!s} in hole'.format(first, last, k), False)
        #=======================================================================
        return hole
        
    @staticmethod
    def hasHole(l):
        """
        Return (a, b) if there is a link at a complemented by a non-adjacent one at b, else (-1, -1).
        
        where a and b are indexes of l, and a+1 < b or b < a-1, 
        and the list from a to b is shorter than the list from b to a 
        (in both cases moving forwards through the list and wrapping from the end to the start).
        Only need look at left-right links since boxes consumed any complementary up-down links.
        """
        for first in range(len(l) - 2):
            x, y, d = l[first]
            if d == Polygonize._LEFT:
                f = lambda lnk: lnk[2] == Polygonize._RIGHT and lnk[0] == x - 1 and lnk[1] == y
            elif d == Polygonize._RIGHT:
                f = lambda lnk: lnk[2] == Polygonize._LEFT and lnk[0] == x + 1 and lnk[1] == y
            else: 
                continue
            last = Polygonize.findIndex(l, first+2, len(l), f)
            if last >= 0:
                # last compliments first, with last > first
                # the shorter of first+1 to last-1 and last+1 (wrapping) to first-1
                # is the hole, and the other is the main polygon
                # BUT this turns out to be ineffective: see isClockwise as alternative approach
                #return findShorter(len(l), first, last)
                return (first, last)
        return (-1, -1)
    
    @staticmethod
    def isClockwise(ring, first, last):
        """
        Returns True if the sublist from first to last (wrapping round if necessary) is a clockwise ring.
        
        The ring is clockwise if a leftmost link is up.
        Since we have bounds, we can stop searching for leftmost if a link is on the left/right boundary.
        We assume first and last are valid indexes, and that there are no complementary vertical links
        (hence the use only of leftmost/rightmost links - there may be complementary horizontal links).
        """
        l = ring.perimeter
        (minx, maxx, _, _) = ring.bounds
        size = len(l)
        minimumX = maxx
        minimumDir = Polygonize._DOWN
        if first > last:
            last = last + size
        for i in range(first, last+1):
            indx = i - size if i >= size else i
            (x, _, d) = l[indx]
            if d == Polygonize._RIGHT or d == Polygonize._LEFT:
                continue
            if x == minx:
                return d == Polygonize._UP
            elif x == maxx:
                return d == Polygonize._DOWN
            elif x < minimumX:
                minimumX = x
                minimumDir = d
        return minimumDir == Polygonize._UP
    
    @staticmethod
    def findShorter(size, first, last):
        """
        Return the pair that makes a hole in a perimeter list of length size.
        
        Candidates are first+1 to last-1 and last+1 (wrapping) to first-1.
        The shorter is the hole.
        Note 0 <= first < last < size.
        """
        firstToLast = last - first - 1
        lastToFirst = size - last + first -1 
        if firstToLast < lastToFirst:
            return (first, last)
        else:
            return (last, first)
    
    @staticmethod
    def findComplements(l):
        """
        Find complementary adjacent links.
        
        If links i and i+1 are the first complementary links, looking from the start,
        return i.  Otherwise, if the last link complements the first, return the last index.
        Else return -1.
        """
        maxm = len(l) - 1
        for i in range(maxm):
            if Polygonize.complements(l[i], l[i+1]):
                return i
        if Polygonize.complements(l[maxm], l[0]):
            return maxm
        return -1

    @staticmethod
    def checkClosed(l):
        """Check polygon is continuous and closed."""
        if len(l) < 4:
            return False
        current = l[0]
        for nxt in l[1:]:
            if not Polygonize.continues(current, nxt):
                return False
            else:
                current = nxt
        nxt = l[0]
        return Polygonize.continues(current, nxt)
            
    @staticmethod
    def makePolyString(l):
        """
        Return a string for display of polygon, in the the form of a start point plus a string of direction letters.
        
        This function is intended for debugging.  It also checks the 
        polygon is connected and closed.
        """
        if len(l) < 4:
            return "Length is {0}".format(len(l))
        current = l[0]
        x, y, d = current
        res = "(" + str(x) + "," + str(y) + ") " + Polygonize.dc(d)
        for nxt in l[1:]:
            x1, y1, d1 = nxt
            if Polygonize.continues(current, nxt):
                current = nxt
                x, y, d = current
                res += Polygonize.dc(d)
            else:
                res += " (" + str(x) + "," + str(y) + "," + Polygonize.dc(d) + \
                        ") not connected to (" + str(x1) + "," + str(y1) + "," + Polygonize.dc(d1) + ")"
                return res
        nxt = l[0]
        if not Polygonize.continues(current, nxt):
            res += " (" + str(x) + "," + str(y) + "," + Polygonize.dc(d) + \
                    ") not connected to (" + str(x1) + "," + str(y1) + "," + Polygonize.dc(d1) + ")"
        return res
        
    class Data:
        
        """Data about polygons, first as a collection of boxes and then as a collection of polygons."""
    
        def __init__(self, boxes, area):
            """Initialise class variables."""
            ## boxes are rows of cells
            self.boxes = boxes
            ## polygons is a list of lists of rings.  Each inner list is a polygon made of its outer ring and its holes (if any).
            self.polygons = []
            ## area in number of cells
            self.area = area
            ## flag indicating completion
            self.finished = False
            
        def boxesToPolygons(self):
            """Make polygons from all boxes."""
            self.polygons = []
            for b in self.boxes:
                self.polygons.append([Polygonize.boxToRing(b)])
            # for poly in self.polygons:
            #     QSWATUtils.loginfo('Polygon has ring {0!s}'.format(poly[0].perimeter))
            self.boxes = None
            
        def mergePolygons(self):
            """
            Merges the polygons.  Two polygons can be merged if they are not disjoint and contain links with a common start.
            
            There are no holes yet, so each polygon is a single ring at the start of its list.
            """
            done = []
            while len(self.polygons) > 0:
                p0 = self.polygons.pop(0)[0]
                changed = False
                i = 0
                while i < len(self.polygons):
                    i0, i1 = Polygonize.canMerge(p0, self.polygons[i][0])
                    if i0 >= 0:
                        p = Polygonize.merge(p0, i0, self.polygons[i][0], i1)
                        # QSWATUtils.loginfo('Merged {0!s} and {1!s} at {2!s} and {3!s} to make {4!s}'.format(p0.perimeter, self.polygons[i][0].perimeter, i0, i1, p.perimeter)) 
                        del self.polygons[i]
                        self.polygons.append([p])
                        changed = True
                        break
                    else:
                        i += 1
                if not changed:
                    done.append([p0])
            self.polygons = done
            
        def makeAllHoles(self):
            """Separate out the holes for all polygons."""
            for poly in self.polygons:
                self.makeHoles(poly)

        def makeHoles(self, poly):
            """
            Separate out the holes in a polygon, adding them to its list of rings.
            
            There may be more than one hole in a polygon, and holes may be split into
            several holes.  A polygon contains a hole if it contains two non-adjacent
            complementary links.
            """
            todo = [0]
            while len(todo) > 0:
                index = todo[0]
                nxt = poly[index]
                first, last = Polygonize.hasHole(nxt.perimeter)
                if first >= 0:
                    if Polygonize.isClockwise(nxt, first, last):
                        hole = Polygonize.makeHole(nxt.perimeter, last, first)
                    else:
                        hole = Polygonize.makeHole(nxt.perimeter, first, last)
                    if hole and len(hole) > 0:
                        # QSWATUtils.loginfo('Hole found: {0!s}'.format(hole))
                        # Holes are never merged, so bounds are of no interest
                        p = Polygonize.Ring(hole, (0,0,0,0))
                        poly.append(p)
                        todo.append(len(poly) - 1)
                else:
                    del todo[0]
            #===================================================================
            # for i in range(len(poly)):
            #     l = poly[i].perimeter
            #     if not Polygonize.checkClosed(l):
            #         QSWATUtils.information('Polygon at index {0!s} is not closed'.format(i), False)
            #     j = Polygonize.findComplements(l)
            #     if j >= 0:
            #         QSWATUtils.information('Polygon at index {0!s} has pair at {1!s}'.format(i, j), False)
            #===================================================================
            
        def finish(self):
            """Finish by converting boxes to polygons, merging polygons, and making holes."""
            #QSWATUtils.information('Starting to make polygons', False)
            self.boxesToPolygons()
            #QSWATUtils.information('Made polygons', False)
            self.mergePolygons()
            #QSWATUtils.information('Merged polygons', False)
            self.makeAllHoles()
            #QSWATUtils.information('Made holes', False)
            self.finished = True
                
    def cellCount(self, val):
        """Cell count for grid value val.  Returns 0 if val not found."""
        data = self.shapesTable.get(val)
        if data is not None:
            return data.area
        else:
            return 0
        
    def area(self, val):
        """Area (in square meters if cell dimensions in meters) for grid value val.  0 if val not found."""
        return self.offset.area(self.cellCount(val))
        
    def addBox(self, indx, box):
        """
        Adds a box  with index indx.
        
        Note area of box equals its width, since its depth is 1.
        """
        (x, y, width) = box
        data = self.shapesTable.get(indx, None)
        if data is not None:
            data.boxes.append((x, y, width))
            data.area += width
        else:
            lb = [(x, y, width)]
            self.shapesTable[indx] = Polygonize.Data(lb, width)
            
    def reportBoxes(self):
        """Report number of boxes for each index in shapesTable."""
        res = ''
        for indx in self.shapesTable:
            res += 'Value {0!s} has {1!s} boxes'.format(indx, len(self.shapesTable[indx].boxes))
        return res
            
        # Concurrent version with threadpool does not seem to work - only one thread seems to run at a time, and speed is much less than sequential version
    #===========================================================================
    # def finishShapes(self, progressBar):
    #              
    #     ## Finish by creating polygons, merging shapes and making holes for each set of data in the ShapesTable.
    #      
    #     start = time.process_time()
    #     pool = QThreadPool().globalInstance()
    #     # QSWATUtils.loginfo('Max thread count is {0!s}'.format(pool.maxThreadCount()))
    #     for (hru, dataItem) in self.shapesTable.iteritems():
    #         worker = Worker(hru, dataItem)
    #         worker.signals.result.connect(self.process_result)
    #         pool.start(worker)
    #     pool.waitForDone()
    #     finish = time.process_time()
    #     QSWATUtils.loginfo('Made FullHRUs shapes in {0!s} seconds'.format(int(finish - start)))
    #      
    # def process_result(self, hru):
    #     # QSWATUtils.loginfo('Finished hru {0!s}'.format(hru))
    #     pass
    #===========================================================================
        
        # Sequential version
    def finishShapes(self, progressBar):
                 
        """
        Finish by creating polygons, merging shapes and making holes for each set of data in the ShapesTable.
        
        progressBar may be None for batch runs and testing.
        """
        if progressBar is not None:
            start = time.process_time()
            fivePercent = len(self.shapesTable) // 20
            progressCount = 0
            progressBar.setVisible(True)
            progressBar.setValue(0)
            for data in self.shapesTable.values():
                if progressCount == fivePercent:
                    progressBar.setValue(progressBar.value() + 5)
                    progressCount = 1
                else:
                    progressCount += 1
                data.finish()
            progressBar.setVisible(False)
            finish = time.process_time()
            QSWATUtils.loginfo('Made FullHRUs shapes in {0!s} seconds'.format(int(finish - start)))
        else:
            for data in self.shapesTable.values():
                data.finish()
            
    def getGeometry(self, val):
        """Return geometry for val."""
        data = self.shapesTable[val]
        assert data.finished
        return self.offset.makeGeometry(data.polygons)
                
    def makeString(self):
        """
        Generate a string for all the polygons.  For each grid value:
        
        1.  A line stating its value
        2.  A set of lines, one for each polygon for that value.
        """
        res = '\n'
        for hru, data  in self.shapesTable.items():
            lp = data.polygons
            res += 'HRU ' + str(hru) + '\n'
            for i in range(len(lp)):
                for j in range(len(lp[i])):
                    res += Polygonize.makePolyString(lp[i][j].perimeter)
                    res += ', '
                res += '\n'
        return res
    
    def makeSingleString(self, hru):
        """Make a string for one hru."""
        lp = self.shapesTable[hru].polygons
        res = 'HRU ' + str(hru) + '\n'
        for i in range(len(lp)):
            for j in range(len(lp[i])):
                res += Polygonize.makePolyString(lp[i][j].perimeter)
                res += ' ,'
            res += '\n'
        return res
    
    def addRow(self, row, rowNum, length, noData):
        """
        Add boxes from row.
        
        This creates boxes, where boxes are made from adjacent cells
        of the row with the same values, and adds them as parts.
        Nodata values are ignored.
        """
        col = 0
        width = 1
        last = row[0]
        bound = length - 1
        while col < bound:
            nxt = row[col+1]
            if nxt == last:
                width += 1
            else:
                if last != noData:
                    self.addBox(last, (col + 1 - width, rowNum, width))
                last = nxt
                width = 1
            col += 1
        if last != noData:
            self.addBox(last, (col + 1 - width, rowNum, width))
        
    class OffSet:
            
        """Stores the values from a grid used to convert link positions to grid points."""
            
        def __init__(self, p, dx, dy):
            """Constructor."""
            ## origin
            self.origin = p
            ## x dimension of grid
            self.dx = dx
            ## y dimension of grid
            self.dy = dy
            ## area of grid cell (dx * dy)
            self.unitArea = dx * dy
            
        def linkToPoint(self, l):
            """Generate a point from a link's start position."""
            x, y, _ = l
            return QgsPointXY(self.origin.x() + self.dx * x, self.origin.y() - self.dy * y)
            
        def area(self, c):
            """Convert a count c of unit boxes to an area in square metres."""
            return c * self.unitArea
            
        def ringToPointsRing(self, inring):
            """Convert a ring to a ring of points."""
            links = inring.perimeter
            if len(links) < 4:
                # something strange
                QSWATUtils.loginfo('Degenerate ring {0!s}'.format(links))
                return None
            Polygonize.rotate(links)
            l0 = links.pop(0)
            p0 = self.linkToPoint(l0)
            ring = [p0]
            _, _, lastDir = l0
            for nxtLink in links:
                _, _, nxtDir = nxtLink
                if nxtDir != lastDir:
                    # next link has a new direction, so include its start point
                    pt = self.linkToPoint(nxtLink)
                    ring.append(pt)
                    lastDir = nxtDir
            # close the polygon
            ring.append(p0)
            return ring
        
        def ringsToPointsRings(self, inrings):
            """Convert a list of rings to a list of points rings."""
            rings = []
            for inring in inrings:
                if inring:
                    rings.append(self.ringToPointsRing(inring))
            return rings
        
        def polygonsToPointsPolygons(self, inpolys):
            """convert a list of polygons to a list of points polygons."""
            polys = []
            for inpoly in inpolys:
                polys.append(self.ringsToPointsRings(inpoly))
            return polys
            
        def makeGeometry(self, polygons):
            """Create a multi-polygon geometry from a list of polygons."""
            return QgsGeometry.fromMultiPolygonXY(self.polygonsToPointsPolygons(polygons))

class WorkerSignals(QObject):
    """Class to receive signal."""
    ## value of signal
    result = pyqtSignal(int)
            
class Worker(QRunnable):
    """Currently unused code to make a worker process for multithreading polygon creation."""
    def __init__(self, hru, dataItem):
        """Constructor."""
        super(Worker, self).__init__()
        ## HRU
        self.hru = hru
        ## Data to be converted
        self.dataItem = dataItem
        ## signal receiver
        self.signals = WorkerSignals()
            
    def run(self):
        """Process the data and send HRU number."""
        self.dataItem.finish()
        self.signals.result.emit(self.hru)
        
