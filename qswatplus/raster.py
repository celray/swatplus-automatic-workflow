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
from qgis.core import QgsCoordinateReferenceSystem
from osgeo import gdal  # type: ignore
from qgis.core import QgsRasterLayer
import numpy as np
import os
from distutils.version import LooseVersion
from typing import Any, Dict, Union, Optional, cast

try:
    from .QSWATUtils import QSWATUtils # type: ignore 
except:
    pass  # not needed by convertFromArc (already imported)

class Raster():
     
    """
    Read and write rasters split into pieces (chunks) as necessary to fit into memory.
    
    Chunks are blocks of contiguous rows.
    In the interest of efficiency, this is limited to only using band 1 (to avoid arrays of buffers etc).
    """
     
    def __init__(self, fileName: str, gv: Any, canWrite: bool=False, isInt: bool=True) -> None:
        
        """Generator."""
        
        ## path to raster file (.tif)
        self.fileName = fileName
        self._gv = gv
        ## number of chunks to be used when reading and writing raster
        self.chunkCount = 0
        ## chunks
        self.chunks: Dict[int, Chunk] = dict()
        ## current chunk index: in domain of chunks indicates has data
        self.currentIndex = -1
        ## current array of values
        self.array: Optional[np.ndarray[Any]] = None
        ## flag set if array data potentially changed
        self.arrayChanged = False
        ## rows in whole raster
        self.numRows = 0
        ## columns in whole raster
        self.numCols = 0
        ## can be written
        self.canWrite = canWrite
        ## true for integer raster, false for float
        self.isInt = isInt
        ## dataset
        self.ds = None
        ## band 1
        self.band = None
        ## no data value
        self.noData = -1
        #self.readCount = 0
        #self.writeCount = 0
        
    def open(self, chunkCount: int, numRows: int=0, numCols: int=0, transform: Optional[Dict[int, float]]=None, 
             projection: Optional[QgsCoordinateReferenceSystem]=None, noData: int=-1) -> bool:
        """
        Open raster for reading or writing.
        
        Return true if successful, raise exception if memory error, false if failure.
        """
        self._gv.openRasters.add(self)
        try:
            if self.canWrite:
                if os.path.exists(self.fileName):
                    self.ds = gdal.Open(self.fileName, gdal.GA_Update)
                else:
                    typ = gdal.GDT_Int32 if self.isInt else gdal.GDT_Float32
                    self.ds = gdal.GetDriverByName('GTiff').Create(self.fileName, numCols, numRows, 1, typ)
                assert self.ds is not None
                self.numRows = numRows
                self.numCols = numCols
                self.ds.SetGeoTransform(transform)
                self.ds.SetProjection(projection)
                self.band = self.ds.GetRasterBand(1)
                assert self.band is not None
                self.arrayChanged = False
                self.band.SetNoDataValue(noData)
                self.noData  = noData
            else:
                self.ds = gdal.Open(self.fileName, gdal.GA_ReadOnly)
                assert self.ds is not None
                self.numRows = self.ds.RasterYSize
                self.numCols = self.ds.RasterXSize
                self.band = self.ds.GetRasterBand(1)
                assert self.band is not None
                self.arrayChanged = False
                self.noData = self.band.GetNoDataValue()
            layer = QgsRasterLayer(self.fileName, '')
            provider = layer.dataProvider()
            # xBlockSize = provider.xBlockSize()
            yBlockSize = provider.yBlockSize()
            self.chunkCount = chunkCount
            if chunkCount <= 1: # avoid accidentally dividing by zero later
                chunkSize = self.numRows
                overlap = 0
            else:
#                 chunkSize = self.numRows // self.chunkCount
#                 # increase chunkSize to be multiple of yBlockSize, since this improves efficiency.
#                 # Allow increase of at most 20%,
#                 # trying to avoid danger of this array size being same as one with smaller chunkCount,
#                 # so using no less memory.
#                 if chunkSize % yBlockSize != 0:
#                     newSize = ((chunkSize // yBlockSize) + 1) * yBlockSize
#                     if float(newSize) / chunkSize <= 1.2:
#                         chunkSize = newSize
#                     else:
#                         QSWATUtils.loginfo(u'Failed to increase chunkSize {0} to be multiple of yBlockSize {1}'.format(chunkSize, yBlockSize))
#                 overlap = 0

                # For count > 1, chunk size approximates to numrows / count + 10% / (count -1)
                # so that chunks overlap.  An overlap should reduce switching between chunks when a flow path runs more or less
                # horizontally along a chunk boundary.
                chunkSize = self.numRows // self.chunkCount + self.numRows // ((self.chunkCount - 1) * 10)
                # increase chunkSize to be multiple of yBlockSize, since this improves efficiency.
                # Allow increase of at most 20%,
                # trying to avoid danger of this array size being same as one with smaller chunkCount,
                # so using no less memory.
                if chunkSize % yBlockSize != 0:
                    newSize = ((chunkSize // yBlockSize) + 1) * yBlockSize
                    if float(newSize) / chunkSize <= 1.2:
                        chunkSize = newSize
                        # overlap also a multiple of yBlockSize
                        overlap = ((chunkSize * chunkCount - self.numRows) // ((chunkCount - 1) * yBlockSize)) * yBlockSize
                    else:
                        QSWATUtils.loginfo('Failed to increase chunkSize {0} to be multiple of yBlockSize {1}'.format(chunkSize, yBlockSize))
                        # chunkSize not a multiple of yBlockSize, so no point in trying to make overlap a multiple
                        overlap = (chunkSize * chunkCount - self.numRows) // (chunkCount - 1)
                else:
                    # overlap also a multiple of yBlockSize
                    overlap = ((chunkSize * chunkCount - self.numRows) // ((chunkCount - 1) * yBlockSize)) * yBlockSize
                    
            for i in range(chunkCount):
                rowOffset = (chunkSize - overlap) * i
                rowCount = self.numRows - rowOffset if i == chunkCount - 1 else chunkSize 
                chunk = Chunk(rowCount, rowOffset)
                self.chunks[i] = chunk
            # we allocate space for the array early since we want to generate any memory exception early
            if self.canWrite:
                dtype = np.int_ if self.isInt else np.float_
                # mumpy.core.full introduced in version 1.8
                if LooseVersion(np.__version__) < LooseVersion('1.8'):
                    self.array = np.empty((chunkSize, self.numCols), dtype)
                    assert self.array is not None
                    self.array.fill(noData)
                else:
                    self.array = np.core.full((chunkSize, self.numCols), noData, dtype)
                    assert self.array is not None
                for ch in self.chunks.values():
                    self.band.WriteArray(self.array[:ch.numRows], 0, ch.rowOffset)
                self.currentIndex = 0
            else:
                self.read(0,0)
            return True
        except MemoryError:
            raise
        except Exception:
            QSWATUtils.exceptionError('Failed to open raster {0}'.format(self.fileName), self._gv.isBatch)
            return False
        
    def read(self, row: int, col: int) -> Union[int, float]:
        """Return raster value at [row, col]."""
        if 0 > col or col >= self.numCols:
            return self.noData
        chunk: Optional[Chunk] = self.chunks.get(self.currentIndex, None)
        index = self.currentIndex if chunk is not None and chunk.rowOffset <= row < chunk.rowOffset + chunk.numRows else -1
        if index == -1:
            for i, ch in self.chunks.items():
                if ch.rowOffset <= row < ch.rowOffset + ch.numRows:
                    index = i
                    chunk = ch
                    break
            if index == -1:
                #QSWATUtils.error(u'Failed to read row {0} column {1} of raster {2}'.format(row, col, self.fileName), self._gv.isBatch)
                return self.noData
        assert chunk is not None
        if self.currentIndex != index:
            assert self.band is not None
            if self.canWrite and self.arrayChanged:
                self.band.WriteArray(self.array, 0, self.chunks[self.currentIndex].rowOffset)
                #self.writeCount += 1
                self.arrayChanged = False
            self.array = self.band.ReadAsArray(0, chunk.rowOffset, self.numCols, chunk.numRows)
            #self.readCount += 1
            self.currentIndex = index
        assert self.array is not None
        if self.isInt:
            return cast(int, self.array[row - chunk.rowOffset, col].astype(int))
        else:
            return cast(float, self.array[row - chunk.rowOffset, col].astype(float))
    
    def write(self, row: int, col: int, val: Union[int, float]) -> None:
        """Write val at [row, col]."""
        if 0 > col or col >= self.numCols:
            return
        if not self.canWrite:
            QSWATUtils.error('Trying to write to readonly raster {0}'.format(self.fileName), self._gv.isBatch)
            return
        chunk: Optional[Chunk] = self.chunks.get(self.currentIndex, None)
        index = self.currentIndex if chunk is not None and chunk.rowOffset <= row < chunk.rowOffset + chunk.numRows else -1
        if index == -1:
            for i, ch in self.chunks.items():
                if ch.rowOffset <= row < ch.rowOffset + ch.numRows:
                    index = i
                    chunk = ch
                    break
            if index == -1:
                QSWATUtils.error('Failed to write row {0} column {1} of raster {2}'.format(row, col, self.fileName), self._gv.isBatch)
                return
        assert chunk is not None
        if self.currentIndex != index:
            assert self.band is not None
            if self.arrayChanged:
                self.band.WriteArray(self.array, 0, self.chunks[self.currentIndex].rowOffset)
                #self.writeCount += 1
            self.array = self.band.ReadAsArray(0, chunk.rowOffset, self.numCols, chunk.numRows)
            self.currentIndex = index
        assert self.array is not None
        self.array[row - chunk.rowOffset, col] = val
        self.arrayChanged = True
        
    def close(self) -> None:
        """Write if necessary and release memory (which also flushes)."""
        if self.canWrite:
            if self.arrayChanged:
                assert self.band is not None
                self.band.WriteArray(self.array, 0, self.chunks[self.currentIndex].rowOffset)
                self.arrayChanged = False
        #    self.writeCount += 1
        #if self.canWrite:
        #    QSWATUtils.loginfo(u'{0} chunks of {3} rows read {1} times and written {2} times'.format(self.fileName, self.readCount, self.writeCount, self.chunks[0].numRows))
        #else:
        #    QSWATUtils.loginfo(u'{0} chunks of {2} rows read {1} times'.format(self.fileName, self.readCount, self.chunks[0].numRows))
        self.release()
        
    def release(self) -> None:
        """Release memory (which also flushes)."""
        # resetting currentIndex allows a Raster object to be closed and reopened
        self.chunks = dict()
        self.currentIndex = -1
        self.array = None
        self.band = None
        self.ds = None
        
class Chunk():
    
    """Piece of a raster: a number of rows starting from rowOffset."""
    
    def __init__(self, numRows: int, rowOffset: int) -> None:
        
        """Generator."""
        
        ## rows in chunk
        self.numRows = numRows
        ## row offset
        self.rowOffset = rowOffset
        
