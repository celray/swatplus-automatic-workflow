# -*- coding: utf-8 -*-
# cython: language_level=3

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
 
 Cython version of Polygonize
'''
# Import the PyQt and QGIS libraries
from qgis.PyQt.QtCore import *  # @UnusedWildImport
from qgis.PyQt.QtGui import *  # @UnusedWildImport
from qgis.core import * # @UnusedWildImport
from qgis.gui import * # @UnusedWildImport
#from multiprocessing import Pool # cannot translate this
from multiprocessing import Process
from multiprocessing.queues import Queue
import time
#from QSWATUtils import QSWATUtils
import numpy as np
cimport numpy as np

    
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
    
    
## directions
# note that the definition of reverse uses the integer encoding: beware of changing it
# but currently reverse is not used
cdef enum:
    _UP = 0
    _RIGHT = 1
    _DOWN = 2
    _LEFT = 3
    
## Links are unit length directed lines, positioned in a cartesian grid using integer coordinates.
#
# Links are modeled as triples, (column, row, direction) where (column, row) is the start point of the link
cdef struct Position:
    int x
    int y
    
cdef struct Link:
    int x
    int y
    int d
    
cdef struct Indexes:
    int first
    int second
    
cdef struct Bounds:
    int xmin
    int xmax
    int ymin
    int ymax
    
cpdef str boundsToString(Bounds b):
    return "(" + str(b.xmin) + "," + str(b.xmax) + "," + str(b.ymin) + "," + str(b.ymax) + ")" 
    
cdef struct Box:
    int x
    int y
    int width
    
cdef class Ring:
    
    """A ring is stored as a list of links forming its perimeter, plus its bounds."""
    
    cdef public object perimeter
    cdef public Bounds bounds
    
    def __init__(self, perimeter, bounds):
        """Constructor."""
        ## list of links forming perimeter of ring
        self.perimeter = perimeter
        ## extent of ring: tuple (xmin, xmax, ymin, ymax)
        self.bounds = bounds

#===============================================================================
# @staticmethod
# cdef int reverse(int d):
#     """Return the reverse of direction.  This uses the encoding of directions as integers modulo 4."""
#     return (d + 2) % 4
#===============================================================================

@staticmethod
cdef str dc(int d):
    """Return a character indicating the direction."""
    if d == _UP:
        return 'u'
    elif d == _DOWN:
        return 'd'
    elif d == _LEFT:
        return 'l'
    else:
        return 'r'

@staticmethod
cdef Position lend(Link l):
    """Return the finish point of a link."""
    if l.d == _UP:
        return Position(l.x, l.y-1)
    elif l.d == _DOWN:
        return Position(l.x, l.y+1)
    elif l.d == _LEFT:
        return Position(l.x-1, l.y)
    else:
        return Position(l.x+1, l.y)
        
@staticmethod
## return true if one link is the complement (reversal) of the other
#
# we only need to be concerned with left-right links  because initial boxes 
# consumed any up-down complementary links
cdef bint complements(Link l1, Link l2):
    if l1.d == _LEFT and l2.d == _RIGHT and l1.x == l2.x + 1 and l1.y == l2.y:
        return True
    if l1.d == _RIGHT and l2.d == _LEFT and l1.x == l2.x - 1 and l1.y == l2.y:
        return True
    return False
#         return d1 == reverse(d2) and (x1, y1) == lend((x2, y2, d2))

@staticmethod
cdef bint continues(Link l1, Link l2):
    """Return true if second link continues the first."""
    cdef Position pt = lend(l1)
    return pt.x == l2.x and pt.y == l2.y
   
@staticmethod
cdef bint disjoint(Bounds bounds1, Bounds bounds2):
    """Return true if the rectangles do not touch or overlap."""
    return bounds1.xmin > bounds2.xmax or bounds2.xmin > bounds1.xmax or bounds1.ymin > bounds2.ymax or bounds2.ymin > bounds1.ymax  
        
cpdef bint checkClosed(l):
    """Check polygon is continuous and closed."""
    cdef:
        Link current, nxt
    
    if len(l) < 4:
        return False
    current = l[0]
    for nxt in l[1:]:
        if not continues(current, nxt):
            return False
        else:
            current = nxt
    nxt = l[0]
    return continues(current, nxt)

cpdef str makePolyString(l):
    """
    Return a string for display of polygon, in the the form of a start point plus a string of direction letters.
    
    This function is intended for debugging.  It also checks the 
    polygon is connected and closed.
    """
    cdef:
        Link current, nxt
        str res
    
    current = l[0]
    res = "(" + str(current.x) + "," + str(current.y) + ") " + dc(current.d)
    for nxt in l[1:]:
        if not continues(current, nxt):
            finish = lend(current)
            res += " (" + str(finish.x) + "," + str(finish.y) + \
                    ") not connected to (" + str(nxt.x) + "," + str(nxt.y) + ")"
        current = nxt
        res += dc(current.d)
    nxt = l[0]
    if not continues(current, nxt):
        finish = lend(current)
        res += " End (" + str(finish.x) + "," + str(finish.y) + ") not connected to start"
    if len(l) < 4:
        res += " Length is {0}".format(len(l))
    return res

cpdef int findComplements(l):
    """
    Find complementary adjacent links.
    
    If links i and i+1 are the first complementary links, looking from the start,
    return i.  Otherwise, if the last link complements the first, return the last index.
    Else return -1.
    """
    cdef int maxm, i
    
    maxm = len(l) - 1
    for i in range(maxm):
        if complements(l[i], l[i+1]):
            return i
    if complements(l[maxm], l[0]):
        return maxm
    return -1


@staticmethod
cdef int findIndexByPosition(object p, int start, int finish, int x, int y):
    """
    Return index the first item of p in range(start, finish) for which the start is (x, y), else -1.
    
    Assumes start .. finish-1 is a subrange of the indexes of p
    """
    cdef:
        int i
        Link l
        
    for i in  range(start, finish):
        l = p[i]
        if l.x == x and l.y == y:
            return i
    return -1
        

@staticmethod
cdef int findIndexByLink(object p, int start, int finish, Link f):
    """
    Return index of the first item of p in range(start, finish) which is the same as f, else -1.
    
    Assumes start .. finish-1 is a subrange of the indexes of p
    """
    cdef:
        int i
        Link l
        
    for i in  range(start, finish):
        l = p[i]
        if f.x == l.x and f.y == l.y and f.d == l.d:
            return i
    return -1
        
@staticmethod
cdef Ring boxToRing(Box b):
    """Make a ring from a box to top left corner at (x,y), width width, and depth 1."""
    cdef:
        int i
    
    perimeter = []
    i = 0
    for i in range(b.width):
        perimeter.append(Link(b.x+i, b.y, _RIGHT))
    perimeter.append(Link(b.x + b.width, b.y, _DOWN))
    for i in range(b.width, 0, -1):
        perimeter.append(Link(b.x + i, b.y + 1, _LEFT))
    perimeter.append(Link(b.x, b.y+1, _UP))
    return Ring(perimeter, Bounds(b.x, b.x + b.width, b.y, b.y + 1))
                    
@staticmethod
cdef Ring merge(Ring p1, int i1, Ring p2, int i2):
    """
    Make a single ring from two rings with a common point.
    
    Start points of links at index i1 of p1 and index i2 of p2 are the same.
    Also removes complementary links in the result.
    """
    cdef:
        int len2
        Bounds b1, b2
        int distanceToJoin
    
    len2 = len(p2.perimeter)
    l = p1.perimeter[:i1]
    l.extend(p2.perimeter[i2:])
    l.extend(p2.perimeter[:i2])
    l.extend(p1.perimeter[i1:])
    #print 'Merge before removing complements: {0}'.format(makePolyString(l))
    # Can get complementary pairs at the joins, so we remove them.
    removePairs(l, i1 + len2 - 1)
    #print 'Merge after removing complements: {0}'.format(makePolyString(l))
    # j = l.findComplements()
    # if j >= 0:
    #     len1 = p1.perimeter.chain.size
    #     QSWATUtils.information('Merge at {0!s} length {1!s} and {2!s} length {3!s} leaves pair at {4!s}'.format(i1, len1, i2, len2, j), False)
    b1 = p1.bounds
    b2 = p2.bounds
    return Ring(l, Bounds(min(b1.xmin,b2.xmin), max(b1.xmax,b2.xmax), min(b1.ymin,b2.ymin), max(b1.ymax,b2.ymax)))

@staticmethod
cdef Indexes canMerge(Ring p1, Ring p2):
    """Return indexes i1 and i2 for starts of links in p1 and p2 which have the same start, if any, else (-1, -1)."""
    cdef:
        int i1, i2
        Link l
    
    if disjoint(p1.bounds, p2.bounds):
        #print '{0} and {1} are disjoint'.format(makePolyString(p1.perimeter), makePolyString(p2.perimeter))
        return Indexes(-1, -1)
    for i1 in range(len(p1.perimeter)):
        l = p1.perimeter[i1]
        #print 'Looking for ({0}, {1}) in {2}'.format(l.x, l.y, repr(p2.perimeter))
        i2 = findIndexByPosition(p2.perimeter, 0, len(p2.perimeter), l.x, l.y)
        if i2 >= 0:
            #print '{0} and {1} can merge at {2}, {3}'.format(makePolyString(p1.perimeter), makePolyString(p2.perimeter), i1, i2)
            return Indexes(i1, i2)
    return Indexes(-1, -1)

@staticmethod
cdef void removePairs(l, int i):
    """
    If links at indexes i and i+1 are complementary, remove them.
    
    Recurses on links originally at i-1 and i+2 if i > 0 and i < len(l) - 2
    Precondition: 0 <= i < len(l) - 1, ie i and i+1 are indexes of l.
    """
    cdef int limit

    limit = len(l) - 1
    assert 0 <= i < limit
    # replaced recursion with a loop (which also only deletes once)
    #===========================================================================
    # if complements(l[i], l[i+1]):
    #     del l[i:i+2]
    #     if 0 < i < limit - 1:
    #         removePairs(l, i-1)
    #===========================================================================
    j = 0       
    while i - j >= 0 and i + j < limit and complements(l[i-j], l[i+j+1]):
        j += 1
    if j > 0:
        del l[i-j+1 : i+j+1]

@staticmethod
cdef void removeFirstLast(l):
    """Remove the first and last links if they complement, and repeat."""
    cdef int length
    
    length = len(l)
    while length > 0 and complements(l[0], l[length - 1]):
        del l[length - 1]
        del l[0]
        length -= 2
        
@staticmethod
cdef void rotate(l):
    """
    Move first point to back while first and last have same direction
    
    If a chain of links representing a closed polygon
    has the first and last links the same direction,
    this function puts the head of the chain to the back, and repeats.
    This does not affect the polygon, but will reduce by one
    the number of points representing it.
    """
    cdef:
        Link l1, l2
    
    l1 = l[0]
    l2 = l[len(l)-1]
    if l1.d == l2.d:
        l1 = l.pop(0)
        l.append(l1)
        rotate(l)
        
@staticmethod
cdef makeHole(l, int first, int last):
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
    
    #print '{0} has hole from {1} to {2}'.format(makePolyString(l), first, last)
    if first+1 < last:
        hole = l[first + 1 : last]
        del l[first : last + 1]
        #print 'Hole is {0}'.format(makePolyString(hole))
        #print 'Outer ring is {0}'.format(makePolyString(l))
    elif first > last:
        hole = l[first + 1:]
        del l[first:]
        hole.extend(l[:last])
        del l[:last + 1]
        #print 'Hole is {0}'.format(makePolyString(hole))
        #print 'Outer ring is {0}'.format(makePolyString(l))
    else:
        return None
    # holes often have complementary initial and final links
    removeFirstLast(hole)
    #print 'Hole after removing complementary first/last is {0}'.format(makePolyString(hole))
    if len(hole) == 0:
        return None
    #=======================================================================
    # for debugging
    # if not checkClosed(hole):
    #     QSWATUtils.information('Hole at first {0!s} last {1!s} is not closed'.format(first, last), False)
    # if not checkClosed(l):
    #     QSWATUtils.information('Polygon after removing hole at first {0!s} last {1!s} is not closed'.format(first, last), False)
    # if len(hole) < 4:
    #     QSWATUtils.information('Hole {0!s} made at ({1!s}, {2!s})'.format(hole, first, last), False) 
    # j = l.findComplements()
    # if j >= 0:
    #     QSWATUtils.information('Making hole at first {0!s} last {1!s} leaves pair at {2!s}'.format(first, last, j), False)
    # k = hole.findComplements()
    # if k >= 0:
    #     QSWATUtils.information('Making hole at first {0!s} last {1!s} leaves pair at {2!s} in hole'.format(first, last, k), False)
    #=======================================================================
    return hole
    
@staticmethod
cdef Indexes hasHole(object l):
    """
    Return (a, b) if there is a link at a complemented by a non-adjacent one at b, else (-1, -1).
    
    where a and b are indexes of l, and a+1 < b or b < a-1, 
    and the list from a to b is shorter than the list from b to a 
    (in both cases moving forwards through the list and wrapping from the end to the start).
    Only need look at left-right links since boxes consumed any complementary up-down links.
    """
    cdef:
        Link link, findLink
        int first, last
        int length = len(l)
    
    for first in range(length - 2):
        link = l[first]
        if link.d == _LEFT:
            findLink = Link(link.x - 1, link.y, _RIGHT)
        elif link.d == _RIGHT:
            findLink = Link(link.x + 1, link.y, _LEFT)
        else: 
            continue
        last = findIndexByLink(l, first+2, length, findLink)
        if last >= 0:
            # last compliments first, with last > first
            # the shorter of first+1 to last-1 and last+1 (wrapping) to first-1
            # is the hole, and the other is the main polygon
            # BUT this turns out to be ineffective: see isClockwise as alternative approach
            #return findShorter(len(l), first, last)
            return Indexes(first, last)
    return Indexes(-1, -1)

cpdef isClockwise(Ring ring, int first, int last):
    """
    Returns True if the sublist from first to last (wrapping round if necessary) is a clockwise ring.
    
    The ring is clockwise if a leftmost link is up.
    Since we have bounds, we can stop searching for leftmost if a link is on the left/right boundary.
    We assume first and last are valid indexes, and that there are no complementary vertical links
    (hence the use only of leftmost/rightmost links - there may be complementary horizontal links).
    """
    cdef:
        int i, x, direction, indx
        Bounds bounds = ring.bounds
        object l = ring.perimeter
        int size = len(l)
        int minX = bounds.xmax
        int minDir = _DOWN
        Link link
        
    if first > last:
        last = last + size
    for i in range(first, last+1):
        indx = i - size if i >= size else i
        link = l[indx]
        direction = link.d
        if direction == _RIGHT or direction == _LEFT:
            continue
        x = link.x
        if x == bounds.xmin:
            return direction == _UP
        elif x == bounds.xmax:
            return direction == _DOWN
        elif x < minX:
            minX = x
            minDir = direction
    return minDir == _UP

# no longer used - replaced by isClockwise, which should be faster 
#===============================================================================
# cpdef bint achievesBounds(l, int first, int last, Bounds bounds):
#     """
#     Returns true if all the bounds are achieved by the sublist from first to last inclusive.
#     
#     Assumes first and last are valid indexes.  If first > last we wrap round.
#     """
#     cdef:
#         int i
#         Link link
#         bint achievesXMax, achievesXMin, achievesYMax, achievesYMin
#         
#     achievesXMax = False
#     achievesXMin = False
#     achievesYMax = False
#     achievesYMin = False
#     if first <= last:
#         for i in range(first, last+1):
#             link = l[i]
#             if link.x == bounds.xmax: achievesXMax = True
#             if link.x == bounds.xmin: achievesXMin = True
#             if link.y == bounds.ymax: achievesYMax = True
#             if link.y == bounds.ymin: achievesYMin = True
#             if (achievesXMax and achievesXMin and achievesYMax and achievesYMin):
#                 return True
#         return False
#     else:
#         size = len(l)
#         for i in range(first, size):
#             link = l[i]
#             if link.x == bounds.xmax: achievesXMax = True
#             if link.x == bounds.xmin: achievesXMin = True
#             if link.y == bounds.ymax: achievesYMax = True
#             if link.y == bounds.ymin: achievesYMin = True
#             if (achievesXMax and achievesXMin and achievesYMax and achievesYMin):
#                 return True
#         for i in range(0, last+1):
#             link = l[i]
#             if link.x == bounds.xmax: achievesXMax = True
#             if link.x == bounds.xmin: achievesXMin = True
#             if link.y == bounds.ymax: achievesYMax = True
#             if link.y == bounds.ymin: achievesYMin = True
#             if (achievesXMax and achievesXMin and achievesYMax and achievesYMin):
#                 return True
#         return False
#===============================================================================

# no longer used - ineffective - replaced by isClockwise
#===============================================================================
# @staticmethod
# cdef Indexes findShorter(size, int first, int last):
#     """
#     Return the pair that makes a hole in a list of length size.
#     
#     Candidates are first+1 to last-1 and last+1 (wrapping) to first-1.
#     The shorter is the hole.
#     Note 0 <= first < last < size.
#     """
#     cdef int firstToLast, lastToFirst
#         
#     firstToLast = last - first
#     lastToFirst = size - firstToLast
#     if firstToLast < lastToFirst:
#         return Indexes(first, last)
#     else:
#         return Indexes(last, first)
#===============================================================================

#===============================================================================
# @staticmethod
# def finishItem(dataItem, queue):
#     dataItem.finishData()
#     queue.put(dataItem)
#===============================================================================
                
cdef class Polygonize:

    cdef public object shapesTable
    cdef public object offset
    cdef public bint connected4
    cdef public int numCols
    cdef public int noData

    def __init__(self, bint connected4, int numCols, int noData, object p, double dX, double dY):
        """Initialise class variables."""
        ## shapes data
        self.shapesTable = dict()
        ## flag to show if using 4connectedness (or, if false, 8)
        self.connected4 = connected4
        ## number of values in row
        self.numCols = numCols
        ## noData value
        self.noData = noData
        ## Top left corner and dimensions of grid
        self.offset = OffSet(p, dX, dY)
        
    cpdef setOffset(self, object p, double dX, double dY):
        ## Top left corner and dimensions of grid
        self.offset = OffSet(p, dX, dY)
        
    cpdef int cellCount(self, int val):
        """Cell count for grid value val.  Returns 0 if val not found."""
        data = self.shapesTable.get(val)
        if not data is None:
            return data.area
        else:
            return 0
        
    cpdef double area(self, int val):
        """Area (in square meters if cell dimensions in meters) for grid value val.  0 if val not found."""
        return self.offset.area(self.cellCount(val))
        
    cdef void addBox(self, int indx, Box b):
        """
        Adds a box  with index indx.
        
        Note area of box equals its width, since its depth is 1.
        """
        
        data = self.shapesTable.get(indx)
        if not data is None:
            data.boxes.append(b)
            data.area += b.width
        else:
            self.shapesTable[indx] = Data(b, b.width)
            
    cdef str reportBoxes(self):
        """Report number of boxes for each index in shapesTable."""
        cdef:
            str res
            int hru
        
        res = ''
        for hru, data in self.shapesTable.items():
            res += 'Value {0!s} has {1!s} boxes'.format(hru, data.boxes.size())
        return res
            
        # Concurrent version with threadpool does not seem to work - only one thread seems to run at a time, and speed is much less than sequential version
    #===========================================================================
    # cpdef finishShapes(self, object progressBar):
    #               
    #     ## Finish by creating polygons, merging shapes and making holes for each set of data in the ShapesTable.
    #       
    #     #start = time.process_time()
    #     pool = QThreadPool().globalInstance()
    #     # QSWATUtils.loginfo('Max thread count is {0!s}'.format(pool.maxThreadCount()))
    #     for (hru, dataItem) in self.shapesTable.items():
    #         worker = Worker(hru, dataItem)
    #         worker.signals.result.connect(self.process_result)
    #         pool.start(worker)
    #     pool.waitForDone()
    #     #finish = time.process_time()
    #     #QSWATUtils.loginfo('Made FullHRUs shapes in {0!s} seconds'.format(int(finish - start)))
    #       
    # cdef process_result(self, int hru):
    #     print 'Finished hru {0!s}'.format(hru)
    #     # QSWATUtils.loginfo('Finished hru {0!s}'.format(hru))
    #     pass
    #===========================================================================
    
    #===========================================================================
    # cpdef finishShapesConc(self, object progressBar):
    #     cdef:
    #         int hru
    #         
    #     jobs = []
    #     queues = dict()
    #     for hru, dataItem in self.shapesTable.items():
    #         queues[hru] = Queue()
    #         jobs.append(Process(target=finishItem, args = (dataItem, queues[hru])))
    #     for j in jobs: j.start()
    #     for hru, queue in queues.items():
    #         self.shapesTable[hru] = queue.get()
    #     for j in jobs: j.join()        
    #===========================================================================
        
        # Sequential version
    cpdef finishShapes(self):
                 
        """
        Finish by creating polygons, merging shapes and making holes for each set of data in the ShapesTable.
        """

        for data in self.shapesTable.values():
            data.finishData()
            
    cpdef getGeometry(self, int val):
        """Return geometry for val."""
        
        data = self.shapesTable[val]
        assert data.finished, 'Geometry for HRU {0!s} not finished'.format(val)
        return self.offset.makeGeometry(data.polygons)
                
    cpdef str makeString(self):
        """
        Generate a string for all the polygons.  For each grid value:
        
        1.  A line stating its value
        2.  A set of lines, one for each polygon for that value.
        """
        cdef:
            int hru
            str res
            
        res = '\n'
        for hru, data in self.shapesTable.items():
            lp = data.polygons
            res += 'HRU ' + str(hru) + '\n'
            for i in range(len(lp)):
                for j in range(len(lp[i])):
                    res += makePolyString(lp[i][j].perimeter)
                    res += ', '
                res += '\n'
        return res
    
    cdef str makeSingleString(self, int hru):
        """Make a string for one hru."""
        cdef str res
        
        lp = self.shapesTable[hru].polygons
        res = 'HRU ' + str(hru) + '\n'
        for i in range(len(lp)):
            for j in range(len(lp[i])):
                res += makePolyString(lp[i][j].perimeter)
                res += ' ,'
            res += '\n'
        return res
    
    cpdef addRow(self, np.ndarray[np.int_t] row, int rowNum):
        """
        Add boxes from row.
        
        This creates boxes, where boxes are made from adjacent cells
        of the row with the same values, and adds them as parts.
        Nodata values are ignored.
        """
        cdef:
            int col, width, last, bound, nxt
            
        col = 0
        width = 1
        last = row[0]
        bound = self.numCols - 1
        while col < bound:
            nxt = row[col+1]
            if nxt == last:
                width += 1
            else:
                if last != self.noData:
                    self.addBox(last, Box(col + 1 - width, rowNum, width))
                last = nxt
                width = 1
            col += 1
        if last != self.noData:
            self.addBox(last, Box(col + 1 - width, rowNum, width))
                
cdef class Data:
    
    """Data about polygons, first as a collection of boxes and then as a collection of polygons."""
    
    cdef public object boxes
    cdef public object polygons
    cdef public int area
    cdef public bint finished

    def __init__(self, Box box, int area):
        """Initialise class variables."""
        ## boxes are rows of cells
        self.boxes = [box]
        ## polygons is a list of lists of rings.  Each inner list is a polygon made of its outer ring and its holes (if any).
        self.polygons = []
        ## area in number of cells
        self.area = area
        ## flag indicating completion
        self.finished = False
        
    cdef void boxesToPolygons(self):
        """Make polygons from all boxes."""
        cdef:
            Box b
            
        self.polygons = []
        for b in self.boxes:
            self.polygons.append([boxToRing(b)])
        # for poly in self.polygons:
        #     QSWATUtils.loginfo('Polygon has ring {0!s}'.format(poly[0].perimeter))
        self.boxes = None
        
    cdef void mergePolygons(self):
        """
        Merges the polygons.  Two polygons can be merged if they are not disjoint and contain links with a common start.
        
        There are no holes yet, so each polygon is a single ring at the start of its list.
        """
        cdef:
            int i
            bint changed
            Indexes inds
            Ring p0, pi
            object done
            
        done = []
        while len(self.polygons) > 0:
            p0 = self.polygons.pop(0)[0]
            i = 0
            changed = False
            while i < len(self.polygons):
                pi = self.polygons[i][0]
                inds = canMerge(p0, pi)
                if inds.first >= 0:
                    p0 = merge(p0, inds.first, pi, inds.second)
                    del self.polygons[i]
                    self.polygons.append([p0])
                    changed = True
                    break
                else:
                    i += 1
            if not changed:
                done.append([p0])
        self.polygons = done
        
    cdef void makeAllHoles(self):
        """Separate out the holes for all polygons."""
        cdef:
            object poly
         
        todoCount = len(self.polygons)  
        for poly in self.polygons:
            self.makeHoles(poly)

    cdef void makeHoles(self, object poly):
        """
        Separate out the holes in a polygon, adding them to its list of rings.
        
        There may be more than one hole in a polygon, and holes may be split into
        several holes.  A polygon contains a hole if it contains two non-adjacent
        complementary links.
        """
        cdef:
            int index
            Indexes inds
            Ring ring
            object links
            
        todo = [0]
        outerFound = False
        while len(todo) > 0:
            index = todo[0]
            ring = poly[index]
            links = ring.perimeter
            inds = hasHole(links)
            if inds.first >= 0:
                if outerFound:
                    # dealing with holes within holes - order dos not matter
                    hole = makeHole(links, inds.first, inds.second)
                elif isClockwise(ring, inds.first, inds.second):
                    hole = makeHole(links, inds.second, inds.first)
                else:
                    hole = makeHole(links, inds.first, inds.second)
                if hole is not None and len(hole) > 0:
                    # QSWATUtils.loginfo('Hole found: {0!s}'.format(hole))
                    # Holes are never merged, so bounds are of no interest
                    p = Ring(hole, Bounds(0,0,0,0))
                    poly.append(p)
                    todo.append(len(poly) - 1)
            else:
                # in  fact the first time we get here the outer ring has been finished
                # since holes are always removed and added to the end of the todo list.
                outerFound = True
                del todo[0]
        #===================================================================
        # for i in range(len(poly)):
        #     l = poly[i].perimeter
        #     if not Polygonize.checkClosed(l):
        #         QSWATUtils.information('Polygon at index {0!s} is not closed'.format(i), False)
        #     j = l.findComplements()
        #     if j >= 0:
        #         QSWATUtils.information('Polygon at index {0!s} has pair at {1!s}'.format(i, j), False)
        #===================================================================
        
    cpdef void finishData(self):
        """Finish by converting boxes to polygons, merging polygons, and making holes."""
        #QSWATUtils.information('Starting to make polygons', False)
        self.boxesToPolygons()
        #QSWATUtils.information('Made polygons', False)
        self.mergePolygons()
        #QSWATUtils.information('Merged polygons', False)
        self.makeAllHoles()
        #QSWATUtils.information('Made holes', False)
        self.finished = True
                

cdef class OffSet:
        
    """Stores the values from a grid used to convert link positions to grid points."""
    
    cdef object origin
    cdef double dx
    cdef double dy
    cdef double unitArea
        
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
        
    cdef linkToPoint(self, Link l):
        """Generate a point from a link's start position."""
        return QgsPointXY(self.origin.x() + self.dx * l.x, self.origin.y() - self.dy * l.y)
        
    cpdef double area(self, int c):
        """Convert a count c of unit boxes to an area in square metres."""
        return c * self.unitArea
        
    cdef ringToPointsRing(self, inring):
        """Convert a ring to a ring of points."""
        cdef:
            Link l0, nxtLink
            int lastDir, nxtDir
            
        links = inring.perimeter
        if len(links) < 4:
            # something strange
            #QSWATUtils.loginfo('Degenerate ring {0!s}'.format(links))
            return None
        rotate(links)
        #print 'After rotation: {0}'.format(makePolyString(links))
        l0 = links[0]
        p0 = self.linkToPoint(l0)
        ring = [p0]
        lastDir = l0.d
        for nxtLink in links[1:]:
            nxtDir = nxtLink.d
            if nxtDir != lastDir:
                # next link has a new direction, so include its start point
                pt = self.linkToPoint(nxtLink)
                ring.append(pt)
                lastDir = nxtDir
        # close the polygon
        ring.append(p0)
        #print 'Ring: {0}'.format(str(ring))
        return ring
    
    cdef ringsToPointsRings(self, inrings):
        """Convert a list of rings to a list of points rings."""
        rings = []
        for inring in inrings:
            rings.append(self.ringToPointsRing(inring))
        return rings
    
    cdef polygonsToPointsPolygons(self, inpolys):
        """convert a list of polygons to a list of points polygons."""
        polys = []
        for inpoly in inpolys:
            polys.append(self.ringsToPointsRings(inpoly))
        return polys
        
    cpdef makeGeometry(self, polygons):
        """Create a multi-polygon geometry from a list of polygons."""
        return QgsGeometry.fromMultiPolygonXY(self.polygonsToPointsPolygons(polygons))

#===============================================================================
# cdef class WorkerSignals(QObject):
#     """Class to receive signal."""
#     ## value of signal
#     result = pyqtSignal(int)
#              
# cdef class Worker(QRunnable):
#     """Currently unused code to make a worker process for multithreading polygon creation."""
#     cdef int hru
#     cdef object dataItem
#     cdef object signals
#     
#     def __init__(self, hru, dataItem):
#         """Constructor."""
#         super(Worker, self).__init__()
#         ## HRU
#         self.hru = hru
#         ## Data to be converted
#         self.dataItem = dataItem
#         ## signal receiver
#         self.signals = WorkerSignals()
#              
#     def run(self):
#         """Process the data and send HRU number."""
#         self.dataItem.finish()
#         self.signals.result.emit(self.hru)
#===============================================================================

    