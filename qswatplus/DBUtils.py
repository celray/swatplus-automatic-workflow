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
from PyQt5.QtWidgets import * # @UnusedWildImport
from qgis.core import * # @UnusedWildImport
import os.path
import shutil
import hashlib
import csv
import sqlite3
import time
import filecmp
import re
import traceback

try:
    from QSWATUtils import QSWATUtils, FileTypes
    from dataInC import BasinData, CellData, LSUData, WaterBody  # @UnresolvedImport
    from parameters import Parameters
except:
    # used by convertFromArc
    from QSWATUtils import QSWATUtils, FileTypes  # @UnresolvedImport
    from dataInC import BasinData, CellData, LSUData, WaterBody  # @UnresolvedImport
    from parameters import Parameters  # @UnresolvedImport

class DBUtils:
    
    """Functions for interacting with project and reference databases."""
    
    _MUIDPATTERN = r'^[A-Z]{2}[0-9]{3}$'
    _MUIDPLUSSEQPATTERN = r'^[A-Z]{2}[0-9]{3}\+[0-9]+$'
    _MUIDPLUSNAMEPATTERN = r'^[A-Z]{2}[0-9]{3}\+[A-Z]+$'
    _S5IDPATTERN = r'^[A-Z]{2}[0-9]{4}$' 
    
    def __init__(self, projDir, projName, dbProjTemplate, dbRefTemplate, isBatch):
        """Initialise class variables."""
        ## Flag showing if batch run
        self.isBatch = isBatch
        ## project name
        self.projName = projName
        ## project database
        dbSuffix = os.path.splitext(dbProjTemplate)[1]
        self.dbFile = QSWATUtils.join(projDir,  projName + dbSuffix)
        ## reference database
        self.dbRefFile = QSWATUtils.join(projDir, Parameters._DBREF)
        #self._connStr = Parameters._ACCESSSTRING + self.dbFile
        #self._connRefStr = Parameters._ACCESSSTRING + self.dbRefFile
        # copy template project database to project folder if not already there
        if not os.path.exists(self.dbFile):
            if not os.path.exists(dbProjTemplate):
                if Parameters._ISWIN:
                    QSWATUtils.error('''Cannot find project database template {0}.
Have you installed SWAT+ as a different directory from C:\SWAT\SWATPlus?
If so use the QSWAT+ Parameters form to set the correct location.'''.format(dbProjTemplate), self.isBatch)
                else:
                    QSWATUtils.error('''Cannot find project database template {0}.
Have you installed SWATPlus?'''.format(dbProjTemplate), self.isBatch)
            else:
                shutil.copyfile(dbProjTemplate, self.dbFile)
        # copy template reference database to project folder if not already there
        if not os.path.exists(self.dbRefFile):
            if not os.path.exists(dbRefTemplate):
                if Parameters._ISWIN:
                    QSWATUtils.error('''Cannot find refence database template {0}.
Have you installed SWAT+ as a different directory from C:\SWAT\SWATPlus?
If so use the QSWAT+ Parameters form to set the correct location.'''.format(dbRefTemplate), self.isBatch)
                else:
                    QSWATUtils.error('''Cannot find refence database template {0}.
Have you installed SWATPlus?'''.format(dbRefTemplate), self.isBatch)
            else:
                shutil.copyfile(dbRefTemplate, self.dbRefFile)
        ## sqlite3 connection to project database
        self.conn = sqlite3.connect(self.dbFile)
        if self.conn is None:
            QSWATUtils.error('Failed to connect to project database {0}'.format(self.dbFile), self.isBatch)
        else:
            #self.conn.isolation_level = None # means autocommit
            self.conn.row_factory = sqlite3.Row
            # turn journal off for better speed
            sql = 'PRAGMA journal_mode=OFF'
            self.conn.execute(sql)
        ## sqlite3 connection to reference database
        self.connRef = sqlite3.connect(self.dbRefFile)
        if self.connRef is None:
            QSWATUtils.error('Failed to connect to reference database {0}'.format(self.dbRefFile), self.isBatch)
        else:
            #self.connRef.isolation_level = None # means autocommit
            self.connRef.row_factory = sqlite3.Row
        ## Tables in project database containing 'landuse'
        self.landuseTableNames = []
        ## Tables in project database containing 'soil'
        self.soilTableNames = []
        ## all tables names in project database
        self._allTableNames = []
        ## map of landuse category to SWAT landuse code
        self.landuseCodes = dict()
        ## Landuse categories may not translate 1-1 into SWAT codes.
        #
        # This map is used to map category ids into equivalent ids.
        # Eg if we have [0 +> XXXX, 1 +> YYYY, 2 +> XXXX, 3 +> XXXX] then _landuseTranslate will be
        # [2 +> 0, 3 +> 0] showing that 2 and 3 map to 0, and other categories are not changed.
        # Only landuse categories 0 and 1 are then used to calculate HRUs, i.e. landuses 0, 2 and 3 will 
        # contribute to the same HRUs.
        # There is an invariant that the domains of landuseCodes and _landuseTranslate are disjoint,
        # and that the range of _landuseTranslate is a subset of the domain of landuseCodes.
        self._landuseTranslate = dict()
        ## Map of landuse category to SWAT plant ids (as found in plant table,
        # or 0 for urban)
        #
        # There is an invariant that the domains of landuseCodes and landuseIds are identical.
        self.landuseIds = dict()
        ## Set of undefined landuse categories.  Retained so each is only reported once as an error in each run.
        self._undefinedLanduseIds = []
        ## Map of landuse category to SWAT urban ids 
        # There is an invariant that the domain of urbanIds is a subset of 
        # the domain of landuseIds, corresponding to those whose plant id is 0
        self.urbanIds = dict()
        ## Set of values occurring in landuse map
        self.landuseVals = set()
        ## Default landuse
        ## Set to 0 landuse value (if any) else first landuse in lookup table and used to replace landuse nodata when using grid model
        self.defaultLanduse = -1
        ## code used for WATR, or -1 if WATR not in landuse table
        self.waterLanduse = -1
        ## Map of soil id  to soil name
        self.soilNames = dict()
        ## Soil categories may not translate 1-1 into soils.
        #
        # This map is used to map category ids into equivalent ids.
        # Eg if we have [0 +> XXXX, 1 +> YYYY, 2 +> XXXX, 3 +> XXXX] then soilTranslate will be
        # [2 +> 0, 3 +> 0] showing that 2 and 3 map to 0, and other categories are not changed.
        # Only soil ids 0 and 1 are then used to calculate HRUs, i.e. soils 0, 2 and 3 will 
        # contribute to the same HRUs.
        # There is an invariant that the domains of soilNames and soilTranslate are disjoint,
        # and that the range of soilTranslate is a subset of the domain of soilNames.
        self.soilTranslate = dict()
        ## Set of undefined soil identifiers.  Retained so each is only reported once as an error in each run.
        self._undefinedSoilIds = []
        ## Copy of soilNames for those soils actually found
        self.usedSoilNames = dict()
        ## ssurgo soil numbers actually found
        self.ssurgoSoils = set()
        ## Default soil
        ## Set to 0 soild value (if any) else first soil in lookup table and used to replace soil nodata when using grid model
        self.defaultSoil = -1
        ## List of limits for slopes.
        #
        # A list [a,b] means slopes are in ranges [slopeMin,a), [a,b), [b,slopeMax] 
        # and these ranges would be indexed by slopes 0, 1 and 2.
        self.slopeLimits = []
        ## flag indicating STATSGO soil data is being used
        self.useSTATSGO = False
        ## flag indicating SSURGO or STATSGO2 soil data is being used
        self.useSSURGO = False
        ## flag indicating, if useSTATSGO is true, that muid+seqn is being used
        self.addSeqn = False
        ## flag indicating, if useSTATSGO is true, that muid+name is being used
        self.addName = False
        ## flag indicating, if useSTATSGO is true, that s5id is being used
        self.useS5id = False
        ## database containing landuse and soil properties tables
        self.plantSoilDatabase = ''
        ## database to use for STATSGO and SSURGO soils
        self.soilDatabase = ''
        ## plant landuse properties table
        self.plantTable = ''
        ## urban landuse properties table
        self.urbanTable = ''
        ## soil properties (usersoil) table
        self.usersoilTable = ''
        ## flag to show if landuse and soil database has been selected by user, or defined in project file
        self.plantSoilDatabaseSelected = False
        ## table names in landuse and soil database containing 'plant'
        self.plantTableNames = []
        ## table names in landuse and soil database containing 'urban'
        self.urbanTableNames = []
        ## table names in landuse and soil database containing 'usersoil'
        self.usersoilTableNames = []
      
# 32-bit version only - uses Access  
#     def connect(self, readonly=False):
#          
#         """Connect to project database."""
#          
#         if not os.path.exists(self.dbFile):
#             QSWATUtils.error('Cannot find project database {0}.  Have you opened the project?'.format(self.dbFile), self.isBatch) 
#         try:
#             if readonly:
#                 conn = pyodbc.connect(self._connStr, readonly=True)
#             else:
#                 # use autocommit when writing to tables, hoping to save storing rollback data
#                 conn = pyodbc.connect(self._connStr, autocommit=True)
#             if conn is not None:
#                 return conn
#             else:
#                 QSWATUtils.error('Failed to connect to project database {0}'.format(self.dbFile), self.isBatch)
#         except Exception as ex:
#             QSWATUtils.error('Failed to connect to project database {0}: {1}.\n\nAre you running a 64-bit version of QGIS?  QSWAT requires a 32-bit version.'.format(self.dbFile, repr(ex)), self.isBatch)
#         return None
#      
#     def connectRef(self, readonly=False):
#          
#         """Connect to reference database."""
#          
#         if not os.path.exists(self.dbRefFile):
#             QSWATUtils.error('Cannot find reference database {0}'.format(self.dbRefFile), self.isBatch)
#             return None 
#         try:
#             if readonly:
#                 conn = pyodbc.connect(self._connRefStr, readonly=True)
#             else:
#                 # use autocommit when writing to tables, hoping to save storing rollback data
#                 conn = pyodbc.connect(self._connRefStr, autocommit=True)
#             if conn is not None:
#                 return conn
#             else:
#                 QSWATUtils.error('Failed to connect to reference database {0}'.format(self.dbRefFile), self.isBatch)
#         except Exception as ex:
#             QSWATUtils.error('Failed to connect to reference database {0}'.format(self.dbRefFile, repr(ex)), self.isBatch)
#         return None
#     
#     def connectDb(self, db, readonly=False):
#         """Connect to database db."""
#         
#         if not os.path.exists(db):
#             QSWATUtils.error('Cannot find database {0}'.format(db), self.isBatch)
#             return None 
#         refStr = Parameters._ACCESSSTRING + db
#         try:
#             if readonly:
#                 conn = pyodbc.connect(refStr, readonly=True)
#             else:
#                 # use autocommit when writing to tables, hoping to save storing rollback data
#                 conn = pyodbc.connect(refStr, autocommit=True)
#             if conn is not None:
#                 return conn
#             else:
#                 QSWATUtils.error('Failed to connect to database {0}'.format(db), self.isBatch)
#         except Exception as ex:
#             QSWATUtils.error('Failed to connect to database {0}'.format(db, repr(ex)), self.isBatch)
#         return None


    def createRoutingTable(self):
        """Create gis_routing table.
        """
        try:
            curs = self.conn.cursor()
            sql = 'DROP TABLE IF EXISTS gis_routing'
            curs.execute(sql)
            curs.execute(DBUtils._ROUTINGCREATESQL)
            curs.execute(DBUtils._ROUTINGINDEXSQL)
            return True
        except Exception:
            return False
    
    def hasData(self, table):
        """Return true if table exists in project database and has data."""
        try:
            with self.conn as conn:
                sql = self.sqlSelect(table, '*', '', '')
                row = conn.execute(sql).fetchone()
                return row is not None
        except Exception:
            return False
        
    def hasTable(self, db, table):
        """Returns true if db has table."""
        # avoid opening proj or ref db again (and closing it!)
        isProjDb = filecmp.cmp(db, self.dbFile)
        isRefDb = filecmp.cmp(db, self.dbRefFile)
        if isProjDb:
            conn = self.conn
        elif isRefDb:
            conn = self.connRef
        else:
            conn = sqlite3.connect(db)
        if conn is None:
            return False
        try:
            return self.hasTableConn(conn, table)
        except Exception:
            return False
        finally:
            if not (isProjDb or isRefDb):
                conn.close()
                
    def hasTableConn(self, conn, table):
        """Uses existing connection conn to return true if table exists."""
        try:
            sql = 'SELECT name FROM sqlite_master WHERE TYPE="table"'
            for row in conn.execute(sql):
                if table == row[0]:
                    return True
            return False
        except Exception:
            return False
    
    def hasDataConn(self, table, conn):
        """Return true if table exists in existing connection and has data."""
        try:
            sql = self.sqlSelect(table, '*', '', '')
            row = conn.execute(sql).fetchone()
            return row is not None
        except Exception:
            return False
                    
    def clearTable(self, table):
        
        """Clear table of data."""
        
        try:
            with self.conn as conn:
                conn.execute('DELETE FROM ' + table)
        except Exception: 
            # since purpose is to make sure any data in table is not accessible
            # ignore problems such as table not existing
            pass
    
    @staticmethod
    def sqlSelect(table, selection, order, where):
        
        """Create SQL select statement."""

        where = '' if where == '' else ' WHERE ' + where
        select = 'SELECT ' + selection + ' FROM ' + table + where
        return select if order == '' else select + ' ORDER BY ' + order
    
    def populateTableNames(self):
        
        """Collect table names from project database."""
        
        self.landuseTableNames = []
        self.soilTableNames = []
        self._allTableNames = []
        with self.conn as conn:
            sql = 'SELECT name FROM sqlite_master WHERE TYPE="table"'
            try:
                for row in conn.execute(sql):
                    table = row[0]
                    if 'landuse' in table:
                        self.landuseTableNames.append(table)
                    elif 'soil' in table and 'usersoil' not in table and DBUtils._SOILS_SOL_NAME not in table:
                        self.soilTableNames.append(table)
                    self._allTableNames.append(table)
            except Exception:
                QSWATUtils.exceptionError('Could not read tables in project database {0}'.format(self.dbFile), self.isBatch)
                return
            
    def collectPlantSoilTableNames(self, tableName, comboBox):
        """
        Collect table names containing tableName from landuse and soil database, place in comboBox and return.
        """
        # avoid opening proj or ref db again (and closing it!)
        if not os.path.exists(self.plantSoilDatabase):
            QSWATUtils.error('Cannot find landuse and soil database {0}'.format(self.plantSoilDatabase), self.isBatch)
            return
        isProjDb = filecmp.cmp(self.plantSoilDatabase, self.dbFile)
        isRefDb = filecmp.cmp(self.plantSoilDatabase, self.dbRefFile)
        ignoreList = []
        if isProjDb:
            conn = self.conn
        elif isRefDb:
            conn = self.connRef
            if tableName == 'plant':
                ignoreList.append('plant_ini')
                ignoreList.append('plant_ini_item')
        else:
            conn = sqlite3.connect(self.plantSoilDatabase)
        if conn is None:
            return [] # assume error reported elsewhere
        comboBox.clear()
        tableNames = []
        sql = 'SELECT name FROM sqlite_master WHERE TYPE="table"'
        try:
            for row in conn.execute(sql):
                table = row[0]
                if table not in ignoreList and tableName in table:
                    comboBox.addItem(table)
                    tableNames.append(table)
            comboBox.addItem(Parameters._USECSV)
            return tableNames
        except Exception:
            QSWATUtils.exceptionError('Could not read tables in landuse and soil database {0}'.format(self.plantSoilDatabase), self.isBatch)
            return []
        finally:
            if not (isProjDb or isRefDb):
                conn.close()
            
    def populateLanduseCodes(self, landuseTable):
        """Collect landuse codes from landuseTable and create lookup tables."""
        OK = True
        self.landuseCodes.clear()
        self._landuseTranslate.clear()
        self.landuseIds.clear()
        self.urbanIds.clear()
        with self.conn as conn:
            try:
                sql = self.sqlSelect(landuseTable, 'LANDUSE_ID, SWAT_CODE', '', '')
                for row in conn.execute(sql):
                    nxt = int(row['LANDUSE_ID'])
                    landuseCode = row['SWAT_CODE']
                    if nxt == 0:
                        self.defaultLanduse = nxt
                        QSWATUtils.loginfo('Default landuse set to {0}'.format(landuseCode))
                    elif self.defaultLanduse < 0:
                        self.defaultLanduse = nxt
                        QSWATUtils.loginfo('Default landuse set to {0}'.format(landuseCode))
                    # check if code already defined
                    equiv = nxt
                    for (key, code) in self.landuseCodes.items():
                        if code == landuseCode:
                            equiv = key
                            break
                    if equiv == nxt:
                        # landuseCode was not already defined
                        if not self.storeLanduseCode(nxt, landuseCode):
                            OK = False
                    else:
                        self.storeLanduseTranslate(nxt, equiv)
            except Exception:
                QSWATUtils.exceptionError('Could not read table {0} in project database {1}'.format(landuseTable, self.dbFile), self.isBatch)
                return False
        return OK    
                
    def storeLanduseTranslate(self, lid, equiv):
        """Make key lid equivalent to key equiv, 
        where equiv is a key in landuseCodes.
        """
        if not lid in self._landuseTranslate:
            self._landuseTranslate[lid] = equiv
            
    def translateLanduse(self, lid):
        """Translate a landuse id to its equivalent lid 
        in landuseCodes, if any.
        """
        self.landuseVals.add(lid)
        return self._landuseTranslate.get(lid, lid)
    
    def storeLanduseCode(self, landuseCat, landuseCode):
        """Store landuse codes in lookup tables."""
        landuseId = 0
        urbanId = 0
        OK = True
        database = self.plantSoilDatabase
        isProjDb = filecmp.cmp(database, self.dbFile)
        isRefDb = filecmp.cmp(database, self.dbRefFile)
        if isProjDb:
            conn = self.conn
        elif isRefDb:
            conn = self.connRef
        else:
            conn = sqlite3.connect(database)
            conn.row_factory = sqlite3.Row
        if conn is None:
            QSWATUtils.error('Failed to connect to database {0} to read landuse tables'.format(database), self.isBatch)
            return False
        try:
            # look in plant database first
            table = self.plantTable
            sqlp = self.sqlSelect(table, 'id', '', 'name=? COLLATE NOCASE')
            try:
                row = conn.execute(sqlp, (landuseCode,)).fetchone()
            except Exception:
                QSWATUtils.exceptionError('Could not read table {0} in database {1}'.format(table, database), self.isBatch)
                return False
            if row is None:
                table = self.urbanTable
                sqlu = self.sqlSelect(table, 'id', '', 'name=? COLLATE NOCASE')
                try:
                    row = conn.execute(sqlu, (landuseCode,)).fetchone()
                except Exception:
                    QSWATUtils.exceptionError('Could not read table {0} in database {1}'.format(table, database), self.isBatch)
                    return False
                if row is None:
                    QSWATUtils.error('No data for landuse {0}'.format(landuseCode), self.isBatch)
                    OK = False
                else:
                    urbanId = row['id']
                    self.urbanIds[landuseCat] = urbanId
            else:
                landuseId = row['id']
            self.landuseCodes[landuseCat] = landuseCode
            self.landuseIds[landuseCat] = landuseId
            if landuseCode.upper() == 'WATR':
                self.waterLanduse = landuseCat  # TODO: should use a set of water landuses
            return OK
        finally:
            if not (isProjDb or isRefDb):
                conn.close()
    
    def getLanduseCode(self, lid):
        """Return landuse code of landuse category lid."""
        lid1 = self.translateLanduse(lid)
        code = self.landuseCodes.get(lid1, None)
        if code is not None:
            return code
        if lid in self._undefinedLanduseIds:
            return str(lid)
        else:
            self._undefinedLanduseIds.append(lid)
            string = str(lid)
            QSWATUtils.error('Unknown landuse value {0}'.format(string), self.isBatch)
            return string
        
    def getLanduseCat(self, landuseCode):
        """Return landuse category (value in landuse map) for code, 
        adding to lookup tables if necessary.
        """
        for (cat, code) in self.landuseCodes.items():
            if code.lower() == landuseCode.lower(): 
                return cat
        # we have a new landuse from splitting
        # first find a new category: maximum existing ones plus 1
        max1 = max(self.landuseCodes.keys())
        max2 = max(self._landuseTranslate.keys()) if len(self._landuseTranslate) > 0 else 0
        cat = max(max1, max2) + 1
        self.landuseCodes[cat] = landuseCode
        # now add to landuseIds or urbanIds table
        self.storeLanduseCode(cat, landuseCode)
        return cat
    
    def populateSoilNames(self, soilTable):
        """Store names for soil categories."""
        self.soilNames.clear()
        self.soilTranslate.clear()
        with self.conn as conn:
            if not conn:
                return False
            # since several forms of soil name are allowed, look for SOIL_ID as one of them and 
            # take the other as SNAM
            sql = self.sqlSelect(soilTable, '*', '', '')
            cursor = conn.execute(sql)
            columns = [description[0] for description in cursor.description]
            try:
                idIndex = columns.index('SOIL_ID')
            except ValueError:
                QSWATUtils.error('No column SOIL_ID in soil lookup table {0}'.format(soilTable))
                return
            if idIndex == 0:
                nameHead = columns[1]
            else:
                nameHead = columns[0]
            firstRow = True
            try:
                for row in conn.execute(sql):
                    nxt = int(row['SOIL_ID'])
                    soilName = row[nameHead].strip()
                    if nxt == 0:
                        self.defaultSoil = nxt
                        QSWATUtils.loginfo('Default soil set to {0}'.format(soilName))
                    elif self.defaultSoil < 0:
                        self.defaultSoil = nxt
                        QSWATUtils.loginfo('Default soil set to {0}'.format(soilName))
                    if firstRow and self.useSTATSGO:
                        firstRow = False
                        # determine what kind of name is being used
                        self.addSeqn = False
                        self.addName = False
                        self.useS5id = False
                        if re.match(self._MUIDPATTERN, soilName):
                            pass
                        elif re.match(self._MUIDPLUSSEQPATTERN, soilName):
                            self.addSeqn = True
                        elif re.match(self._MUIDPLUSNAMEPATTERN, soilName):
                            self.addName = True
                        elif re.match(self._S5IDPATTERN, soilName):
                            self.useS5id = True
                        else:
                            QSWATUtils.error('Cannot recognise {0} as an muid, muid+seqn, or s5id'.
                                             format(soilName), self.isBatch)
                            return
                    # check if code already defined
                    equiv = nxt
                    for (key, name) in self.soilNames.items():
                        if name == soilName:
                            equiv = key
                            break
                    if equiv == nxt:
                        # soilName not found
                        self.soilNames[nxt] = soilName
                    else:
                        self.storeSoilTranslate(nxt, equiv)
            except Exception:
                QSWATUtils.exceptionError('Could not read table {0} in project database {1}'.format(soilTable, self.dbFile), self.isBatch)
                return False
        return True
        
        # not currently used        
    #===========================================================================
    # @staticmethod
    # def matchesSTATSGO(name):
    #     pattern = '[A-Z]{2}[0-9]{3}\Z'
    #     return re.match(pattern, name)
    #===========================================================================
                    
    def getSoilName(self, sid):
        """Return name for soil id sid."""
        if self.useSSURGO:
            self.ssurgoSoils.add(sid)
            return str(sid)
        sid1 = self.translateSoil(sid)
        # first try used soil names
        name = self.usedSoilNames.get(sid1, None)
        if name is not None:
            return name
        else:
            name = self.soilNames.get(sid1, None)
            if name is not None:
                self.usedSoilNames[sid1] = name
                return name
        if sid in self._undefinedSoilIds:
            return str(sid)
        else:
            string = str(sid)
            self._undefinedSoilIds.append(sid)
            QSWATUtils.error('Unknown soil value {0}'.format(string), self.isBatch)
            return string
        
    _SOILS_SOL_TABLE = \
    """
    (id        INTEGER NOT NULL PRIMARY KEY,
    name       TEXT NOT NULL,
    hyd_grp    TEXT NOT NULL,
    dp_tot     REAL NOT NULL,
    anion_excl REAL NOT NULL,
    perc_crk   REAL NOT NULL,
    texture    TEXT,
    description     TEXT)
    """
    
    _SOILS_SOL_NAME = 'soils_sol'
    
    _SOILS_SOL_LAYER_TABLE = \
    """
    (id       INTEGER NOT NULL PRIMARY KEY,
    soil_id   INTEGER NOT NULL,
    layer_num INTEGER NOT NULL,
    dp        REAL    NOT NULL,
    bd        REAL    NOT NULL,
    awc       REAL    NOT NULL,
    soil_k    REAL    NOT NULL,
    carbon    REAL    NOT NULL,
    clay      REAL    NOT NULL,
    silt      REAL    NOT NULL,
    sand      REAL    NOT NULL,
    rock      REAL    NOT NULL,
    alb       REAL    NOT NULL,
    usle_k    REAL    NOT NULL,
    ec        REAL    NOT NULL,
    caco3     REAL,
    ph        REAL,
    FOREIGN KEY (
        soil_id
    )
    REFERENCES {0} (id) ON DELETE CASCADE)
    """.format(_SOILS_SOL_NAME)
    
    _SOILS_SOL_LAYER_NAME = 'soils_sol_layer'
    
    _PLANTS_PLT_TABLE = \
    """
    (id          INTEGER       NOT NULL PRIMARY KEY,
    name        TEXT          NOT NULL,
    plnt_typ    TEXT          NOT NULL,
    gro_trig    TEXT          NOT NULL,
    nfix_co     REAL          NOT NULL,
    days_mat     REAL          NOT NULL,
    bm_e        REAL          NOT NULL,
    harv_idx    REAL          NOT NULL,
    lai_pot     REAL          NOT NULL,
    frac_hu1    REAL          NOT NULL,
    lai_max1    REAL          NOT NULL,
    frac_hu2    REAL          NOT NULL,
    lai_max2    REAL          NOT NULL,
    hu_lai_decl REAL          NOT NULL,
    dlai_rate   REAL          NOT NULL,
    can_ht_max  REAL          NOT NULL,
    rt_dp_max   REAL          NOT NULL,
    tmp_opt     REAL          NOT NULL,
    tmp_base    REAL          NOT NULL,
    frac_n_yld  REAL          NOT NULL,
    frac_p_yld  REAL          NOT NULL,
    frac_n_em   REAL          NOT NULL,
    frac_n_50   REAL          NOT NULL,
    frac_n_mat  REAL          NOT NULL,
    frac_p_em   REAL          NOT NULL,
    frac_p_50   REAL          NOT NULL,
    frac_p_mat  REAL          NOT NULL,
    harv_idx_ws REAL          NOT NULL,
    usle_c_min  REAL          NOT NULL,
    stcon_max   REAL          NOT NULL,
    vpd         REAL          NOT NULL,
    frac_stcon  REAL          NOT NULL,
    ru_vpd      REAL          NOT NULL,
    co2_hi      REAL          NOT NULL,
    bm_e_hi     REAL          NOT NULL,
    plnt_decomp REAL          NOT NULL,
    lai_min     REAL          NOT NULL,
    bm_tree_acc REAL          NOT NULL,
    yrs_mat     REAL          NOT NULL,
    bm_tree_max REAL          NOT NULL,
    ext_co      REAL          NOT NULL,
    leaf_tov_mn REAL          NOT NULL,
    leaf_tov_mx REAL          NOT NULL,
    bm_dieoff   REAL          NOT NULL,
    rt_st_beg   REAL          NOT NULL,
    rt_st_end   REAL          NOT NULL,
    plnt_pop1   REAL          NOT NULL,
    frac_lai1   REAL          NOT NULL,
    plnt_pop2   REAL          NOT NULL,
    frac_lai2   REAL          NOT NULL,
    frac_sw_gro REAL          NOT NULL,
    wnd_live    REAL          NOT NULL,
    wnd_dead    REAL          NOT NULL,
    wnd_flat    REAL          NOT NULL,
    description TEXT)
    """
    
    _PLANTS_PLT_NAME = 'plants_plt'
    
    _URBAN_URB_TABLE = \
    """
    (id          INTEGER       NOT NULL PRIMARY KEY,
    name        TEXT          NOT NULL,
    frac_imp    REAL          NOT NULL,
    frac_dc_imp REAL          NOT NULL,
    curb_den    REAL          NOT NULL,
    urb_wash    REAL          NOT NULL,
    dirt_max    REAL          NOT NULL,
    t_halfmax   REAL          NOT NULL,
    conc_totn   REAL          NOT NULL,
    conc_totp   REAL          NOT NULL,
    conc_no3n   REAL          NOT NULL,
    urb_cn      REAL          NOT NULL,
    description TEXT)
    """
    
    _URBAN_URB_NAME = 'urban_urb'
    
    @staticmethod
    def countCols(table, conn):
        """Count the columns in table in database currently connected to conn."""
        
        # get the sql to create the database
        row = conn.execute('SELECT sql FROM sqlite_master WHERE name = "{0}" AND type = "table"'.
                            format(table)).fetchone()
        if row is None:
            return -1
        # column definitions are separated by commas
        return len(row[0].split(','))
                
    def writeSoilsTable(self):
        """Write the soils_sol and soils_sol_layer tables in the project database."""
        if self.useSTATSGO or self.useSSURGO:
            database = self.soilDatabase
        else:
            database = self.plantSoilDatabase     
        isProjDb = filecmp.cmp(database, self.dbFile)
        isRefDb = filecmp.cmp(database, self.dbRefFile)
        if isProjDb:
            conn = self.conn
        elif isRefDb:
            conn = self.connRef
        else:
            conn = sqlite3.connect(database)
            conn.row_factory = sqlite3.Row
        # need to read columns using numeric indices
        # so cannot use sqlite3.Row which returns rows as dictionaries with arbitrary order
        conn.row_factory = lambda _,row : row
        try:
            # single usersoil table has 152 columns, one with separate layer table has 11: 
            # we leave room for expansion by using 20 as limit
            columnCount = DBUtils.countCols(self.usersoilTable, conn)
            if columnCount < 0:
                QSWATUtils.error('Could not find table {0} in soil database {1}'.format(self.usersoilTable, database), self.isBatch)
                return False
            hasSeparateLayerTable = columnCount < 20
            if hasSeparateLayerTable:
                layerTable = self.usersoilTable + '_layer'
                if not self.hasTableConn(conn, layerTable):
                    QSWATUtils.error('Table {0} has {1} columns but cannot find layer table {2} in soil database {3}'.
                                    format(self.usersoilTable, columnCount, layerTable, database), self.isBatch)
                    return False
                sqlLayer = self.sqlSelect(layerTable, '*', 'layer_num', 'soil_id=?')
            readCursor = conn.cursor()
            writeCursor = self.conn.cursor()
            sql = 'DROP TABLE IF EXISTS {0}'.format(DBUtils._SOILS_SOL_NAME)
            writeCursor.execute(sql)
            sql = 'CREATE TABLE {0} {1}'.format(DBUtils._SOILS_SOL_NAME, DBUtils._SOILS_SOL_TABLE)
            writeCursor.execute(sql)
            sql = 'DROP TABLE IF EXISTS {0}'.format(DBUtils._SOILS_SOL_LAYER_NAME)
            writeCursor.execute(sql)
            sql = 'CREATE TABLE {0} {1}'.format(DBUtils._SOILS_SOL_LAYER_NAME, DBUtils._SOILS_SOL_LAYER_TABLE)
            writeCursor.execute(sql)
            insert = 'INSERT INTO {0} VALUES(?,?,?,?,?,?,?,?)'.format(DBUtils._SOILS_SOL_NAME)
            insertLayer = 'INSERT INTO {0} VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'.format(DBUtils._SOILS_SOL_LAYER_NAME)
            if self.useSTATSGO:
                if self.addSeqn:
                    sql = self.sqlSelect(self.usersoilTable, '*', 'id ASC', 'muid=? AND seqn=?')
                elif self.addName:
                    sql = self.sqlSelect(self.usersoilTable, '*', 'id ASC', 'muid=? AND name=?')
                elif self.useS5id:
                    sql = self.sqlSelect(self.usersoilTable, '*', 'id ASC', 's5id=?')
                else:
                    sql = self.sqlSelect(self.usersoilTable, '*', 'id ASC', 'muid=?')
            elif self.useSSURGO:
                sql = self.sqlSelect(self.usersoilTable, '*', '', 'muid=?')
            elif hasSeparateLayerTable:
                sql = self.sqlSelect(self.usersoilTable, '*', '', 'name=?')
            else:
                sql = self.sqlSelect(self.usersoilTable, '*', '', 'SNAM=?')
            sid = 0 # last soil id used
            lid = 0 # last layer id used
            if self.useSSURGO:
                for ssurgoId in self.ssurgoSoils:
                    row = readCursor.execute(sql, (ssurgoId,)).fetchone()
                    if not row:
                        QSWATUtils.error('SSURGO soil {0} (and perhaps others) not defined in {1} table in database {2}.  {3} table not written.'.
                                         format(ssurgoId, self.usersoilTable, database, DBUtils._SOILS_SOL_NAME), self.isBatch)
                        return False
                    sid += 1
                    if hasSeparateLayerTable:
                        lid = self.writeUsedSoilRowSeparate(sid, lid, ssurgoId, row, writeCursor, insert, insertLayer, readCursor, sqlLayer)
                    else:
                        lid = self.writeUsedSoilRow(sid, lid, ssurgoId, row, writeCursor, insert, insertLayer)
            else: 
                for name in self.usedSoilNames.values():
                    if self.useSTATSGO:
                        if self.useS5id:
                            args = (name,)
                        elif self.addSeqn or self.addName:
                            args = (name[:5], name[6:]) # note the plus sign must be skipped
                        else:
                            args = (name,)
                    else:
                        args = (name,)
                    row = readCursor.execute(sql, args).fetchone()
                    if not row:
                        QSWATUtils.error('Soil name {0} (and perhaps others) not defined in {1} table in database {2}.  {3} table not written.'.
                                         format(name, self.usersoilTable, database, DBUtils._SOILS_SOL_NAME), self.isBatch)
                        return
                    sid += 1
                    if hasSeparateLayerTable:
                        lid = self.writeUsedSoilRowSeparate(sid, lid, name, row, writeCursor, insert, insertLayer, readCursor, sqlLayer)
                    else:
                        lid = self.writeUsedSoilRow(sid, lid, name, row, writeCursor, insert, insertLayer)
            return True
        except Exception:
            QSWATUtils.exceptionError('Could not create {2} and {3} tables from {0} table in soil database {1}'.
                            format(self.usersoilTable, database, DBUtils._SOILS_SOL_NAME, DBUtils._SOILS_SOL_LAYER_NAME), 
                            self.isBatch)
            return False
        finally:
            self.conn.commit()
            self.hashDbTable(self.conn, DBUtils._SOILS_SOL_NAME)
            self.hashDbTable(self.conn, DBUtils._SOILS_SOL_LAYER_NAME)
            if (isProjDb or isRefDb):
                conn.row_factory = sqlite3.Row
            else:
                conn.close()
                
    def writeUsedSoilRow(self, sid, lid, name, row, cursor, insert, insertLayer):
        """Write data from one row of usersoil table to soils_sol and soils_sol_layer tables in project database."""
        cursor.execute(insert, (sid, name) + row[7:12] + (None,))
        startLayer1 = 12 # index of SOL_Z1
        layerWidth = 12 # number of entries per layer
        startCal = 132 # index of SOL_CAL1
        startPh = 142 # index of SOL_PH1
        for i in range(int(row[6])):
            lid += 1 
            startLayer = startLayer1 + i*layerWidth
            cursor.execute(insertLayer, (lid, sid, i+1) +  row[startLayer:startLayer+layerWidth] +  (row[startCal+i], row[startPh+i]))
        return lid 
                
    def writeUsedSoilRowSeparate(self, sid, lid, name, row, cursor, insert, insertLayer, readCursor, sqlLayer):
        """Write data from one row of usersoil table plus separate layer table 
        to soils_sol and soils_sol_layer tables.
        """
        # check whether there is a non-null description item
        if len(row) == 11:
            cursor.execute(insert, (sid, name) +  row[6:] + (None,))
        else:
            cursor.execute(insert, (sid, name) +  row[6:])
        layerRows = readCursor.execute(sqlLayer, (row[0],))
        if layerRows is None:
            QSWATUtils.error('Failed to find soil layers in table {0} with soil_id {1}'.
                             format(self.usersoilTable + '_layer', row[0]), self.isBatch)
            return lid
        for ro in layerRows:
            lid += 1
            cursor.execute(insertLayer, (lid, sid) + ro[2:])
        return lid
          
    def storeSoilTranslate(self, sid, equiv):
        """Make key sid equivalent to key equiv, 
        where equiv is a key in soilNames.
        """
        if sid not in self.soilTranslate:
            self.soilTranslate[sid] = equiv
        
    def translateSoil(self, sid):
        """Translate a soil id to its equivalent id in soilNames."""
        if self.useSSURGO:
            return sid
        return self.soilTranslate.get(sid, sid)
    
    def writeLanduseTables(self):
        """Write the plants_plt and urban_urb tables in the project database."""
        isProjDb = filecmp.cmp(self.plantSoilDatabase, self.dbFile)
        isRefDb = filecmp.cmp(self.plantSoilDatabase, self.dbRefFile)
        copyPlant = True
        copyUrban = True
        if isProjDb:
            conn = self.conn
            # avoid trying to copy table to itself
            copyPlant = self.plantTable != DBUtils._PLANTS_PLT_NAME
            copyUrban = self.urbanTable != DBUtils._URBAN_URB_NAME
            if not (copyPlant or copyUrban):
                return True
        elif isRefDb:
            conn = self.connRef
        else:
            conn = sqlite3.connect(self.plantSoilDatabase)
        # suspend row_factory setting
        # normal setting to sqlite3.Row produces dictionaries for rows, which have random order 
        # row_factory needs to be a function taking a cursor and row as tuple and returning a row
        # so we use an identity
        conn.row_factory = lambda _, row: row
        readCursor = conn.cursor()
        writeCursor = self.conn.cursor()
        try:
            if copyPlant:
                sql = 'DROP TABLE IF EXISTS {0}'.format(DBUtils._PLANTS_PLT_NAME)
                writeCursor.execute(sql)
                sql = 'CREATE TABLE {0} {1}'.format(DBUtils._PLANTS_PLT_NAME, DBUtils._PLANTS_PLT_TABLE)
                writeCursor.execute(sql)
                insertPlant = 'INSERT INTO {0} VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'.format(DBUtils._PLANTS_PLT_NAME)
            if copyUrban:
                sql = 'DROP TABLE IF EXISTS {0}'.format(DBUtils._URBAN_URB_NAME)
                writeCursor.execute(sql)
                sql = 'CREATE TABLE {0} {1}'.format(DBUtils._URBAN_URB_NAME, DBUtils._URBAN_URB_TABLE)
                writeCursor.execute(sql)
                insertUrban = 'INSERT INTO {0} VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)'.format(DBUtils._URBAN_URB_NAME)
            plantSelect = self.sqlSelect(self.plantTable, '*', '', 'name=? COLLATE NOCASE')
            urbanSelect = self.sqlSelect(self.urbanTable, '*', '', 'name=? COLLATE NOCASE')
            # changed to copy all of plant and urban tables
            # pid = 0
            # uid = 0
            for crop in self.landuseVals:
                name = self.getLanduseCode(crop)
                args = (name,)
                # look first in plantTable
                row = readCursor.execute(plantSelect, args).fetchone()
                if row is None:
                    row = readCursor.execute(urbanSelect, args).fetchone()
                    if row is None:
                        QSWATUtils.error('Landuse name {0} (and perhaps others) not defined in {1} or {2} tables in database {3}.'.
                                         format(name, self.plantTable, self.urbanTable, self.plantSoilDatabase), self.isBatch)
                        return False
                    # changed to copy all of plant and urban tables
                    # elif copyUrban:
                    #    uid += 1
                    #    # copy row, replacing id
                    #   writeCursor.execute(insertUrban, (uid,) + row[1:])
                # changed to copy all of plant and urban tables
                # elif copyPlant:
                #    pid += 1
                #    writeCursor.execute(insertPlant, (pid,) + row[1:])
            # copy all of plant and urban tables
            if copyPlant:
                plantAll = self.sqlSelect(self.plantTable, '*', '', '')
                for row in readCursor.execute(plantAll):
                    writeCursor.execute(insertPlant, tuple(row))
            if copyUrban:
                urbanAll = self.sqlSelect(self.urbanTable, '*', '', '')
                for row in readCursor.execute(urbanAll):
                    writeCursor.execute(insertUrban, tuple(row))
            return True
        except Exception:
            QSWATUtils.exceptionError('Could not create {3} and {4} tables from {0} and {1} tables in landuse and soil database {2}'.
                            format(self.plantTable, self.urbanTable, self.plantSoilDatabase, DBUtils._PLANTS_PLT_NAME, DBUtils._URBAN_URB_NAME), 
                            self.isBatch)
            return False
        finally:
            self.conn.commit()
            self.hashDbTable(self.conn, DBUtils._PLANTS_PLT_NAME)
            self.hashDbTable(self.conn, DBUtils._URBAN_URB_NAME)
            if isProjDb or isRefDb:
                conn.row_factory = sqlite3.Row
            else:
                conn.close()
        
    def populateAllLanduses(self, listBox, includeWATR=True):
        """Make list of all landuses in listBox."""
        isProjDb = filecmp.cmp(self.plantSoilDatabase, self.dbFile)
        isRefDb = filecmp.cmp(self.plantSoilDatabase, self.dbRefFile)
        if isProjDb:
            conn = self.conn
        elif isRefDb:
            conn = self.connRef
        else:
            conn = sqlite3.connect(self.plantSoilDatabase)
            conn.row_factory = sqlite3.Row
        landuseSql = self.sqlSelect(self.plantTable, 'name, description', '', '')
        urbanSql = self.sqlSelect(self.urbanTable, 'name, description', '', '')
        cursor = conn.cursor()
        listBox.clear()
        try:
            for row in cursor.execute(landuseSql):
                code = row['name'].upper()
                include = includeWATR if code == 'WATR' else True
                if include:
                    descr = row['description']
                    if descr is None:
                        strng = code
                    else:
                        strng = code + ' (' + descr + ')'
                    listBox.addItem(strng)
        except Exception:
            QSWATUtils.exceptionError('Could not read table {0} in landuse and soil database {1}'.format(self.plantTable, self.plantSoilDatabase), self.isBatch)
            return
        try:
            for row in cursor.execute(urbanSql):
                code = row['name'].upper()
                descr = row['description']
                if descr is None:
                    strng = code
                else:
                    strng = code + ' (' + descr + ')'
                listBox.addItem(strng)
        except Exception:
            QSWATUtils.exceptionError('Could not read table {0} in landuse and soil database {1}'.format(self.urbanTable, self.plantSoilDatabase), self.isBatch)
            return
        listBox.sortItems(Qt.AscendingOrder)
        
    def getLanduseDescriptions(self, crops):
        """Return map of crop -> (code, description) for list or iterable of crop values.
        
        Uses a list to avoid repeated opeining of database connections."""
        isProjDb = filecmp.cmp(self.plantSoilDatabase, self.dbFile)
        isRefDb = filecmp.cmp(self.plantSoilDatabase, self.dbRefFile)
        if isProjDb:
            conn = self.conn
        elif isRefDb:
            conn = self.connRef
        else:
            conn = sqlite3.connect(self.plantSoilDatabase)
            conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        plantSql = self.sqlSelect(self.plantTable, 'description', '', 'name=? COLLATE NOCASE')
        urbanSql = self.sqlSelect(self.urbanTable, 'description', '', 'name=? COLLATE NOCASE')
        result = dict()
        for crop in crops:
            landuseCode = self.getLanduseCode(crop)
            # try plant table first
            row = cursor.execute(plantSql, (landuseCode,)).fetchone()
            if row is None:
                row = cursor.execute(urbanSql, (landuseCode,)).fetchone()
            if row is None:
                # avoid repeating error report
                result[crop] = (str(crop), '')
            else:
                result[crop] = (landuseCode, row['description'])
        return result  
   
    def populateMapLanduses(self, vals, combo, includeWATR=True):
        """Put all landuse codes except WATR from landuse values vals in combo box."""
        for i in vals:
            code = self.getLanduseCode(i)
            include = includeWATR if code == 'WATR' else True
            if include:
                # avoid duplicates
                if combo.findText(code) < 0:
                    combo.addItem(code)
        
    def slopeIndex(self, slopePercent):
        """Return index of slopePerecent from slope limits list."""
        n = len(self.slopeLimits)
        for index in range(n):
            if slopePercent < self.slopeLimits[index]:
                return index
        return n
    
    def slopeRange(self, slopeIndex):
        """Return the slope range for an index."""
        assert 0 <= slopeIndex <= len(self.slopeLimits), 'Slope index {0} out of range'.format(slopeIndex)
        minimum = 0 if slopeIndex == 0 else self.slopeLimits[slopeIndex - 1]
        maximum = 9999 if slopeIndex == len(self.slopeLimits) else self.slopeLimits[slopeIndex]
        return '{0!s}-{1!s}'.format(minimum, maximum)
    
    _BASINSDATA = 'BASINSDATA'
    _BASINSDATATABLE = \
    """
    (basin INTEGER PRIMARY KEY UNIQUE NOT NULL, 
    farDistance REAL, 
    minElevation REAL, 
    maxElevation REAL)
    """
    
    _BASINSDATAINSERTSQL = 'INSERT INTO BASINSDATA VALUES(?,?,?,?)'
    
    _LSUSDATA = 'LSUSDATA'
    _LSUSDATATABLE = \
    """
    (lsu INTEGER PRIMARY KEY UNIQUE NOT NULL, 
    basin INTEGER REFERENCES BASINSDATA (basin), 
    category INTEGER,
    channel INTEGER,
    cellCount INTEGER, 
    area REAL, 
    outletElevation REAL, 
    sourceElevation REAL, 
    channelLength REAL, 
    farElevation REAL, 
    farDistance REAL, 
    farPointX REAL, 
    farPointY REAL, 
    totalElevation REAL, 
    totalSlope REAL, 
    totalLatitude REAL, 
    totalLongitude REAL, 
    cropSoilSlopeArea REAL,
    lastHru INTEGER)
    """
    
    _LSUSDATAINSERTSQL = 'INSERT INTO LSUSDATA VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'
    
    _HRUSDATA = 'HRUSDATA'
    _HRUSDATATABLE = \
    """
    (hru INTEGER,  
    lsu INTEGER REFERENCES LSUSDATA (lsu),  
    crop INTEGER,  
    soil INTEGER,  
    slope INTEGER,  
    cellCount INTEGER,  
    area REAL,  
    totalElevation REAL,  
    totalSlope REAL,  
    totalLatitude REAL,  
    totalLongitude REAL)
    """
    
    _HRUSDATAINSERTSQL = 'INSERT INTO HRUSDATA VALUES(?,?,?,?,?,?,?,?,?,?,?)'
    
    _WATERDATA = 'WATERDATA'
    _WATERDATATABLE = \
    """
    (lsu INTEGER REFERENCES LSUSDATA (lsu), 
    cellCount INTEGER,  
    area REAL, 
    originalArea REAL, 
    totalElevation REAL,
    totalLatitude REAL,  
    totalLongitude REAL,
    id INTEGER,
    channelRole INTEGER,
    waterRole INTEGER)
    """
    
    _WATERDATAINSERTSQL = 'INSERT INTO WATERDATA VALUES(?,?,?,?,?,?,?,?,?,?)'
    
    _ELEVATIONBANDSTABLE = \
    """
    (subbasin INTEGER PRIMARY KEY UNIQUE NOT NULL,  
    elevb1 REAL,  
    elevb2 REAL,  
    elevb3 REAL,  
    elevb4 REAL,  
    elevb5 REAL,  
    elevb6 REAL,  
    elevb7 REAL,  
    elevb8 REAL,  
    elevb9 REAL,  
    elevb10 REAL,  
    elevb_fr1 REAL,  
    elevb_fr2 REAL,  
    elevb_fr3 REAL,  
    elevb_fr4 REAL,  
    elevb_fr5 REAL,  
    elevb_fr6 REAL,  
    elevb_fr7 REAL,  
    elevb_fr8 REAL,  
    elevb_fr9 REAL,  
    elevb_fr10 REAL)
    """
    
    _USERSOILTABLE = \
    """
    (OBJECTID   INTEGER,
    MUID       TEXT,
    SEQN       TEXT,
    SNAM       TEXT    PRIMARY KEY UNIQUE NOT NULL,
    S5ID       TEXT,
    CMPPCT     TEXT,
    NLAYERS    REAL,
    HYDGRP     TEXT,
    SOL_ZMX    REAL,
    ANION_EXCL REAL,
    SOL_CRK    REAL,
    TEXTURE    TEXT,
    SOL_Z1     REAL,
    SOL_BD1    REAL,
    SOL_AWC1   REAL,
    SOL_K1     REAL,
    SOL_CBN1   REAL,
    CLAY1      REAL,
    SILT1      REAL,
    SAND1      REAL,
    ROCK1      REAL,
    SOL_ALB1   REAL,
    USLE_K1    REAL,
    SOL_EC1    REAL,
    SOL_Z2     REAL,
    SOL_BD2    REAL,
    SOL_AWC2   REAL,
    SOL_K2     REAL,
    SOL_CBN2   REAL,
    CLAY2      REAL,
    SILT2      REAL,
    SAND2      REAL,
    ROCK2      REAL,
    SOL_ALB2   REAL,
    USLE_K2    REAL,
    SOL_EC2    REAL,
    SOL_Z3     REAL,
    SOL_BD3    REAL,
    SOL_AWC3   REAL,
    SOL_K3     REAL,
    SOL_CBN3   REAL,
    CLAY3      REAL,
    SILT3      REAL,
    SAND3      REAL,
    ROCK3      REAL,
    SOL_ALB3   REAL,
    USLE_K3    REAL,
    SOL_EC3    REAL,
    SOL_Z4     REAL,
    SOL_BD4    REAL,
    SOL_AWC4   REAL,
    SOL_K4     REAL,
    SOL_CBN4   REAL,
    CLAY4      REAL,
    SILT4      REAL,
    SAND4      REAL,
    ROCK4      REAL,
    SOL_ALB4   REAL,
    USLE_K4    REAL,
    SOL_EC4    REAL,
    SOL_Z5     REAL,
    SOL_BD5    REAL,
    SOL_AWC5   REAL,
    SOL_K5     REAL,
    SOL_CBN5   REAL,
    CLAY5      REAL,
    SILT5      REAL,
    SAND5      REAL,
    ROCK5      REAL,
    SOL_ALB5   REAL,
    USLE_K5    REAL,
    SOL_EC5    REAL,
    SOL_Z6     REAL,
    SOL_BD6    REAL,
    SOL_AWC6   REAL,
    SOL_K6     REAL,
    SOL_CBN6   REAL,
    CLAY6      REAL,
    SILT6      REAL,
    SAND6      REAL,
    ROCK6      REAL,
    SOL_ALB6   REAL,
    USLE_K6    REAL,
    SOL_EC6    REAL,
    SOL_Z7     REAL,
    SOL_BD7    REAL,
    SOL_AWC7   REAL,
    SOL_K7     REAL,
    SOL_CBN7   REAL,
    CLAY7      REAL,
    SILT7      REAL,
    SAND7      REAL,
    ROCK7      REAL,
    SOL_ALB7   REAL,
    USLE_K7    REAL,
    SOL_EC7    REAL,
    SOL_Z8     REAL,
    SOL_BD8    REAL,
    SOL_AWC8   REAL,
    SOL_K8     REAL,
    SOL_CBN8   REAL,
    CLAY8      REAL,
    SILT8      REAL,
    SAND8      REAL,
    ROCK8      REAL,
    SOL_ALB8   REAL,
    USLE_K8    REAL,
    SOL_EC8    REAL,
    SOL_Z9     REAL,
    SOL_BD9    REAL,
    SOL_AWC9   REAL,
    SOL_K9     REAL,
    SOL_CBN9   REAL,
    CLAY9      REAL,
    SILT9      REAL,
    SAND9      REAL,
    ROCK9      REAL,
    SOL_ALB9   REAL,
    USLE_K9    REAL,
    SOL_EC9    REAL,
    SOL_Z10    REAL,
    SOL_BD10   REAL,
    SOL_AWC10  REAL,
    SOL_K10    REAL,
    SOL_CBN10  REAL,
    CLAY10     REAL,
    SILT10     REAL,
    SAND10     REAL,
    ROCK10     REAL,
    SOL_ALB10  REAL,
    USLE_K10   REAL,
    SOL_EC10   REAL,
    SOL_CAL1   REAL,
    SOL_CAL2   REAL,
    SOL_CAL3   REAL,
    SOL_CAL4   REAL,
    SOL_CAL5   REAL,
    SOL_CAL6   REAL,
    SOL_CAL7   REAL,
    SOL_CAL8   REAL,
    SOL_CAL9   REAL,
    SOL_CAL10  REAL,
    SOL_PH1    REAL,
    SOL_PH2    REAL,
    SOL_PH3    REAL,
    SOL_PH4    REAL,
    SOL_PH5    REAL,
    SOL_PH6    REAL,
    SOL_PH7    REAL,
    SOL_PH8    REAL,
    SOL_PH9    REAL,
    SOL_PH10   REAL)
    """
    
    _SOILTABLE = \
    """
    (id         INTEGER NOT NULL
                    PRIMARY KEY,
    name       TEXT NOT NULL,
    muid       TEXT,
    seqn       INTEGER,
    s5id       TEXT,
    cmppct     INTEGER,
    hydgrp     TEXT NOT NULL,
    zmx        REAL NOT NULL,
    anion_excl REAL NOT NULL,
    crk        REAL NOT NULL,
    texture    TEXT NOT NULL)
    """
    
    _SOILLAYERTABLE = \
    """
    (id        INTEGER NOT NULL
                      PRIMARY KEY,
    soil_id   INTEGER NOT NULL,
    layer_num INTEGER NOT NULL,
    z         REAL    NOT NULL,
    bd        REAL    NOT NULL,
    awc       REAL    NOT NULL,
    k         REAL    NOT NULL,
    cbn       REAL    NOT NULL,
    clay      REAL    NOT NULL,
    silt      REAL    NOT NULL,
    sand      REAL    NOT NULL,
    rock      REAL    NOT NULL,
    alb       REAL    NOT NULL,
    usle_k    REAL    NOT NULL,
    ec        REAL    NOT NULL,
    cal       REAL,
    ph        REAL)
    """ 

    # old SWAT format
    #===========================================================================
    # _CROPTABLE = \
    #  """
    #  (OBJECTID   INTEGER,
    #  ICNUM      INTEGER,
    #  CPNM       TEXT    PRIMARY KEY,
    #  IDC        INTEGER,
    #  CROPNAME   TEXT,
    #  BIO_E      REAL,
    #  HVSTI      REAL,
    #  BLAI       REAL,
    #  FRGRW1     REAL,
    #  LAIMX1     REAL,
    #  FRGRW2     REAL,
    #  LAIMX2     REAL,
    #  DLAI       REAL,
    #  CHTMX      REAL,
    #  RDMX       REAL,
    #  T_OPT      REAL,
    #  T_BASE     REAL,
    #  CNYLD      REAL,
    #  CPYLD      REAL,
    #  BN1        REAL,
    #  BN2        REAL,
    #  BN3        REAL,
    #  BP1        REAL,
    #  BP2        REAL,
    #  BP3        REAL,
    #  WSYF       REAL,
    #  USLE_C     REAL,
    #  GSI        REAL,
    #  VPDFR      REAL,
    #  FRGMAX     REAL,
    #  WAVP       REAL,
    #  CO2HI      REAL,
    #  BIOEHI     REAL,
    #  RSDCO_PL   REAL,
    #  OV_N       REAL,
    #  CN2A       REAL,
    #  CN2B       REAL,
    #  CN2C       REAL,
    #  CN2D       REAL,
    #  FERTFIELD  INTEGER,
    #  ALAI_MIN   REAL,
    #  BIO_LEAF   REAL,
    #  MAT_YRS    REAL,
    #  BMX_TREES  REAL,
    #  EXT_COEF   REAL,
    #  BM_DIEOFF  REAL,
    #  OpSchedule TEXT)
    #  """
    #===========================================================================
     
    # old SWAT format
    #===========================================================================
    # _URBANTABLE = \
    #  """
    #  (OBJECTID   INTEGER,
    #  IUNUM      REAL,
    #  URBNAME    TEXT    PRIMARY KEY,
    #  URBFLNM    TEXT,
    #  FIMP       REAL,
    #  FCIMP      REAL,
    #  CURBDEN    REAL,
    #  URBCOEF    REAL,
    #  DIRTMX     REAL,
    #  THALF      REAL,
    #  TNCONC     REAL,
    #  TPCONC     REAL,
    #  TNO3CONC   REAL,
    #  OV_N       REAL,
    #  CN2A       REAL,
    #  CN2B       REAL,
    #  CN2C       REAL,
    #  CN2D       REAL,
    #  URBCN2     REAL,
    #  OpSchedule TEXT)
    #  """
    #===========================================================================
    
    _PLANTTABLE = _PLANTS_PLT_TABLE
    
    _URBANTABLE = _URBAN_URB_TABLE
    
    def createBasinsDataTables(self, cursor):
        """Create BASINSDATA, LUSDATA, WATERDATA and HRUSDATA in project database.""" 
        # remove old table completely, for backward compatibility, in case structure changed
        tableBasins = self._BASINSDATA
        dropSQL = 'DROP TABLE IF EXISTS ' + tableBasins
        try:
            cursor.execute(dropSQL)
        except Exception:
            QSWATUtils.exceptionError('Could not drop table {0} from project database {1}'.format(tableBasins, self.dbFile), self.isBatch)
            return False
        createSQL = 'CREATE TABLE ' + tableBasins + self._BASINSDATATABLE
        try:
            cursor.execute(createSQL)
        except Exception:
            QSWATUtils.exceptionError('Could not create table {0} in project database {1}'.format(tableBasins, self.dbFile), self.isBatch)
            return False
        tableLus = self._LSUSDATA
        dropSQL = 'DROP TABLE IF EXISTS ' + tableLus
        try:
            cursor.execute(dropSQL)
        except Exception:
            QSWATUtils.exceptionError('Could not drop table {0} from project database {1}'.format(tableLus, self.dbFile), self.isBatch)
            return False
        createSQL = 'CREATE TABLE ' + tableLus + ' ' + self._LSUSDATATABLE
        try:
            cursor.execute(createSQL)
        except Exception:
            QSWATUtils.exceptionError('Could not create table {0} in project database {1}'.format(tableLus, self.dbFile), self.isBatch)
            return False
        # table searched by basin
        indexSQL = 'CREATE INDEX IF NOT EXISTS basin_index on {0} (basin)'.format(tableLus)
        try:
            cursor.execute(indexSQL)
        except Exception:
            QSWATUtils.exceptionError('Could not create index for basin in table {0} in project database {1}'.format(tableLus, self.dbFile), self.isBatch)
        tableWater = self._WATERDATA
        dropSQL = 'DROP TABLE IF EXISTS ' + tableWater
        try:
            cursor.execute(dropSQL)
        except Exception:
            QSWATUtils.exceptionError('Could not drop table1 {0} from project database {1}'.format(tableWater, self.dbFile), self.isBatch)
            return False
        createSQL = 'CREATE TABLE ' + tableWater + ' ' + self._WATERDATATABLE
        try:
            cursor.execute(createSQL)
        except Exception:
            QSWATUtils.exceptionError('Could not create table {0} in project database {1}'.format(tableWater, self.dbFile), self.isBatch)
            return False
        # table searched by lsu
        indexSQL = 'CREATE INDEX IF NOT EXISTS lsu_index on {0} (lsu)'.format(tableWater)
        try:
            cursor.execute(indexSQL)
        except Exception:
            QSWATUtils.exceptionError('Could not create index for lsu in table {0} in project database {1}'.format(tableWater, self.dbFile), self.isBatch)
            return False 
        tableHrus = self._HRUSDATA
        dropSQL = 'DROP TABLE IF EXISTS ' + tableHrus
        try:
            cursor.execute(dropSQL)
        except Exception:
            QSWATUtils.exceptionError('Could not drop table1 {0} from project database {1}'.format(tableHrus, self.dbFile), self.isBatch)
            return False
        createSQL = 'CREATE TABLE ' + tableHrus + ' ' + self._HRUSDATATABLE
        try:
            cursor.execute(createSQL)
        except Exception:
            QSWATUtils.exceptionError('Could not create table {0} in project database {1}'.format(tableHrus, self.dbFile), self.isBatch)
            return False
        # table searched by lsu
        indexSQL = 'CREATE INDEX IF NOT EXISTS lsu_index on {0} (lsu)'.format(tableHrus)
        try:
            cursor.execute(indexSQL)
        except Exception:
            QSWATUtils.exceptionError('Could not create index for lsu in table {0} in project database {1}'.format(tableHrus, self.dbFile), self.isBatch)
            return False
        return True
                        
    def writeBasinsData(self, basins, cursor):
        """Write BASINSDATA, LSUSDATA, HRUSDATA and WATERDATA tables in project database.""" 
        time1 = time.process_time()
        for basin, data in basins.items():
            OK = self.writeBasinsDataItem(basin, data, cursor)
            if not OK:
                # error occurred - no point in repeating the failure
                break
        time2 = time.process_time()
        QSWATUtils.loginfo('Writing basins data took {0} seconds'.format(int(time2 - time1)))
        self.hashDbTable(self.conn, self._BASINSDATA)
        self.hashDbTable(self.conn, self._LSUSDATA)
        self.hashDbTable(self.conn, self._HRUSDATA)
        self.hashDbTable(self.conn, self._WATERDATA)
        
    def writeBasinsDataItem(self, basin, data, curs):
        """Write data for one basin in BASINSDATA, LSUSDATA, HRUSDATA and WATERDATA tables in project database.""" 
        try:
            curs.execute(DBUtils._BASINSDATAINSERTSQL, (basin, float(data.farDistance), 
                                                        float(data.minElevation), float(data.maxElevation)))
        except Exception:
            QSWATUtils.exceptionError('Could not write to table {0} in project database {1}'.format(self._BASINSDATA, self.dbFile), self.isBatch)
            return False
        for channel, channeldata in data.lsus.items():
            for (landscape, lsuData) in channeldata.items():
                lsuId = QSWATUtils.landscapeUnitId(channel, landscape)
                try:
                    curs.execute(DBUtils._LSUSDATAINSERTSQL, (lsuId, basin, landscape, channel, lsuData.cellCount, 
                                          float(lsuData.area), float(lsuData.outletElevation),
                                          float(lsuData.sourceElevation), float(lsuData.channelLength),
                                          float(lsuData.farElevation), float(lsuData.farDistance),
                                          float(lsuData.farPointX), float(lsuData.farPointY), 
                                          float(lsuData.totalElevation), 
                                          float(lsuData.totalSlope), float(lsuData.totalLatitude),
                                          float(lsuData.totalLongitude), float(lsuData.cropSoilSlopeArea), lsuData.lastHru))
                except Exception:
                    QSWATUtils.exceptionError('Could not write to table {0} in project database {1}'.format(self._LSUSDATA, self.dbFile), self.isBatch)
                    return False
                waterBody = lsuData.waterBody
                # note that empty reservoirs created by addReservoirs will not be included in the WATERDATA table
                # because they have been added to the mergedLsus, and DATA tables are written from (unmerged) lsus.
                # But after regenerating from the DATA tables the reservoirs will be recreated, so there is no harm.
                if waterBody is not None:
                    try:
                        curs.execute(DBUtils._WATERDATAINSERTSQL, (lsuId, waterBody.cellCount, float(waterBody.area),
                                                                    float(waterBody.originalArea), float(waterBody.totalElevation),
                                                                    float(waterBody.totalLatitude), float(waterBody.totalLongitude),
                                                                    waterBody.id, waterBody.channelRole, waterBody.waterRole))
                    except Exception:
                        QSWATUtils.exceptionError('Could not write to table {0} in project database {1}'.format(self._WATERDATA, self.dbFile), self.isBatch)
                        return False
                for crop, soilSlopeNumbers in lsuData.cropSoilSlopeNumbers.items():
                    for soil, slopeNumbers in soilSlopeNumbers.items():
                        for slope, hru in slopeNumbers.items():
                            cd = lsuData.hruMap[hru]
                            try:
                                curs.execute(DBUtils._HRUSDATAINSERTSQL, (hru, lsuId, crop, soil, slope, cd.cellCount,
                                                       float(cd.area), float(cd.totalElevation), float(cd.totalSlope),
                                                       float(cd.totalLatitude), float(cd.totalLongitude)))
                            except Exception:
                                QSWATUtils.exceptionError('Could not write to table {0} in project database {1}'.format(self._HRUSDATA, self.dbFile), self.isBatch)
                                return False
        return True
                   
    # slow version replaced below (much too slow with grid models with many cells)       
    #===========================================================================
    # def regenerateBasins(self, ignoreerrors=False): 
    #     """Recreate basins data from BASINSDATA, LSUSDATA, WATERDATA and HRUSDATA tables in project database."""
    #     try:
    #         basins = dict()
    #         with self.conn as conn:
    #             cur = conn.cursor()
    #             try:
    #                 for brow in cur.execute(self.sqlSelect(self._BASINSDATA, '*', '', '')):
    #                     basin = brow['basin']
    #                     bd = BasinData(self.waterLanduse, brow['farDistance'])
    #                     bd.minElevation = brow['minElevation']
    #                     bd.maxElevation = brow['maxElevation']
    #                     sql = self.sqlSelect(self._LSUSDATA, '*', '', 'basin=?')
    #                     for lrow in cur.execute(sql, (basin,)):
    #                         lsuId = lrow['lsu']
    #                         landscape = lrow['category']
    #                         channel = lrow['channel']
    #                         lsuData = LSUData()
    #                         lsuData.cellCount = lrow['cellCount']
    #                         lsuData.area = lrow['area']
    #                         lsuData.outletElevation = lrow['outletElevation']
    #                         lsuData.sourceElevation = lrow['sourceElevation']
    #                         lsuData.channelLength = lrow['channelLength']
    #                         lsuData.farElevation = lrow['farElevation']
    #                         lsuData.farDistance = lrow['farDistance']
    #                         lsuData.farPointX = lrow['farPointX']
    #                         lsuData.farPointY = lrow['farPointY']
    #                         lsuData.totalElevation = lrow['totalElevation']
    #                         lsuData.totalSlope = lrow['totalSlope']
    #                         lsuData.totalLatitude = lrow['totalLatitude']
    #                         lsuData.totalLongitude = lrow['totalLongitude']
    #                         lsuData.cropSoilSlopeArea = lrow['cropSoilSlopeArea']
    #                         lsuData.lastHru = lrow['lastHru']
    #                         sql = self.sqlSelect(self._WATERDATA, '*', '', 'lsu=?')
    #                         wrow = cur.execute(sql, (lsuId,)).fetchone()
    #                         if wrow is None:
    #                             lsuData.waterBody = None
    #                         else:
    #                             lsuData.waterBody = WaterBody(wrow['cellCount'], wrow['area'], wrow['totalElevation'],
    #                                                           wrow['totalLongitude'], wrow['totalLatitude'])
    #                             lsuData.waterBody.originalArea = wrow['originalArea']
    #                             lsuData.waterBody.id = wrow['id']
    #                             lsuData.waterBody.role = wrow['role']
    #                             lsuData.waterBody.isReservoir = wrow['isReservoir'] == 1
    #                         sql = self.sqlSelect(self._HRUSDATA, '*', '', 'lsu=?')
    #                         for hrow in cur.execute(sql, (lsuId,)):
    #                             hru = hrow['hru']
    #                             crop = hrow['crop']
    #                             soil = hrow['soil']
    #                             slope = hrow['slope']
    #                             if crop not in lsuData.cropSoilSlopeNumbers:
    #                                 lsuData.cropSoilSlopeNumbers[crop] = dict()
    #                                 self.landuseVals.add(crop)
    #                             if soil not in lsuData.cropSoilSlopeNumbers[crop]:
    #                                 lsuData.cropSoilSlopeNumbers[crop][soil] = dict()
    #                             lsuData.cropSoilSlopeNumbers[crop][soil][slope] = hru
    #                             cellData = CellData(hrow['cellcount'], hrow['area'], hrow['totalElevation'],
    #                                                 hrow['totalSlope'], hrow['totalLongitude'], hrow['totalLatitude'], crop)
    #                             lsuData.hruMap[hru] = cellData
    #                         channelData = bd.lsus.get(channel, None)
    #                         if channelData is None:
    #                             bd.lsus[channel] = dict()
    #                             channelData = bd.lsus[channel]
    #                         channelData[landscape] = lsuData
    #                     basins[basin] = bd
    #             except Exception as e:
    #                 if not ignoreerrors:
    #                     QSWATUtils.error('Could not read basins data from project database {0}: {1}'.format(self.dbFile, repr(e)), self.isBatch)
    #                 return (None, False)
    #         return (basins, True)
    #     except Exception as e:
    #         if not ignoreerrors:
    #             QSWATUtils.error('Failed to reconstruct basin data from database: ' + repr(e), self.isBatch)
    #         return (None, False) 
    #===========================================================================
        
    def regenerateBasins(self, ignoreerrors=False): 
        """Recreate basins data from BASINSDATA, LSUSDATA, WATERDATA and HRUSDATA tables in project database."""
        try:
            basins = dict()
            # map lsuid -> (basin, channel, landscape) to enable non-search reads of all tables
            lsuMap = dict()
            with self.conn as conn:
                cur = conn.cursor()
                try:
                    # first read basins to get domain of basins map fixed
                    for brow in cur.execute(self.sqlSelect(self._BASINSDATA, '*', '', '')):
                        basin = brow['basin']
                        bd = BasinData(self.waterLanduse, brow['farDistance'])
                        bd.minElevation = brow['minElevation']
                        bd.maxElevation = brow['maxElevation']
                        basins[basin] = bd
                    # next read lsus to set up lsusData in each basin and to populate lsuMap
                    for lrow in cur.execute(self.sqlSelect(self._LSUSDATA, '*', '', '')):
                        basin = lrow['basin']
                        lsuId = lrow['lsu']
                        landscape = lrow['category']
                        channel = lrow['channel']
                        lsuData = LSUData()
                        lsuData.cellCount = lrow['cellCount']
                        lsuData.area = lrow['area']
                        lsuData.outletElevation = lrow['outletElevation']
                        lsuData.sourceElevation = lrow['sourceElevation']
                        lsuData.channelLength = lrow['channelLength']
                        lsuData.farElevation = lrow['farElevation']
                        lsuData.farDistance = lrow['farDistance']
                        lsuData.farPointX = lrow['farPointX']
                        lsuData.farPointY = lrow['farPointY']
                        lsuData.totalElevation = lrow['totalElevation']
                        lsuData.totalSlope = lrow['totalSlope']
                        lsuData.totalLatitude = lrow['totalLatitude']
                        lsuData.totalLongitude = lrow['totalLongitude']
                        lsuData.cropSoilSlopeArea = lrow['cropSoilSlopeArea']
                        lsuData.lastHru = lrow['lastHru']
                        lsuMap[lsuId] = (basin, channel, landscape)
                        basinData = basins[basin]
                        channelData = basinData.lsus.get(channel, dict())
                        channelData[landscape] = lsuData
                        basinData.lsus[channel] = channelData
                    # add water bodies
                    for wrow in cur.execute(self.sqlSelect(self._WATERDATA, '*', '', '')):
                        lsuid = wrow['lsu']
                        (basin, channel, landscape) = lsuMap[lsuid]
                        lsuData = basins[basin].lsus[channel][landscape]
                        lsuData.waterBody = WaterBody(wrow['cellCount'], wrow['area'], wrow['totalElevation'],
                                                      wrow['totalLongitude'], wrow['totalLatitude'])
                        lsuData.waterBody.originalArea = wrow['originalArea']
                        lsuData.waterBody.id = wrow['id']
                        lsuData.waterBody.channelRole = wrow['channelRole']
                        lsuData.waterBody.waterRole = wrow['waterRole']
                    # add hrus
                    for hrow in cur.execute(self.sqlSelect(self._HRUSDATA, '*', '', '')):
                        hru = hrow['hru']
                        lsuid = hrow['lsu']
                        (basin, channel, landscape) = lsuMap[lsuid]
                        lsuData = basins[basin].lsus[channel][landscape]
                        crop = hrow['crop']
                        soil = hrow['soil']
                        slope = hrow['slope']
                        if crop not in lsuData.cropSoilSlopeNumbers:
                            lsuData.cropSoilSlopeNumbers[crop] = dict()
                            self.landuseVals.add(crop)
                        if soil not in lsuData.cropSoilSlopeNumbers[crop]:
                            lsuData.cropSoilSlopeNumbers[crop][soil] = dict()
                        lsuData.cropSoilSlopeNumbers[crop][soil][slope] = hru
                        cellData = CellData(hrow['cellcount'], hrow['area'], hrow['totalElevation'],
                                            hrow['totalSlope'], hrow['totalLongitude'], hrow['totalLatitude'], crop)
                        lsuData.hruMap[hru] = cellData
                except Exception:
                    if not ignoreerrors:
                        QSWATUtils.exceptionError('Could not read basins data from project database {0}'.format(self.dbFile), self.isBatch)
                    return (None, False)
            return (basins, True)
        except Exception:
            if not ignoreerrors:
                QSWATUtils.exceptionError('Failed to reconstruct basin data from database', self.isBatch)
            return (None, False) 
        
    def changeReachSlopes(self, multiplier, oldMultiplier, shapesDir):
        """
        Apply multiplier in place of oldMultiplier to all reach slopes 
        in gis_channels table (if any) in project database.
        """
        try:
            with self.conn as conn:
                if conn is None:
                    return
                table = 'gis_channels'
                factor = float(multiplier) / oldMultiplier
                # need to change SLO2 value
                sql = 'UPDATE {0} SET slo2 = slo2 * {1!s}'.format(table, factor)
                conn.execute(sql)
                conn.commit()
                # update rivs1 file
                rivs1File = QSWATUtils.join(shapesDir, Parameters._RIVS1 + '.shp')
                if not os.path.exists(rivs1File):
                    QSWATUtils.loginfo('{0} not found'.format(rivs1File))
                    return
                rivs1Layer = QgsVectorLayer(rivs1File, FileTypes.legend(FileTypes._CHANNELREACHES), 'ogr')
                provider = rivs1Layer.dataProvider()
                slo2Idx = provider.fieldNameIndex('Slo2')
                if slo2Idx < 0:
                    QSWATUtils.loginfo('Slo2 field in {0} not found'.format(rivs1File))
                    return
                mmap = dict()
                request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([slo2Idx])
                for feature in provider.getFeatures(request):
                    mmap[feature.id()] = {slo2Idx: float(feature[slo2Idx]) * factor}
                if not provider.changeAttributeValues(mmap):
                    QSWATUtils.loginfo('Failed to update {0}'.format(rivs1File))
        except Exception:
            QSWATUtils.loginfo('Failed to change reach slopes: {0}'.format(traceback.format_exc()))
            # table may not exist yet
            return
            
    def changeTributarySlopes(self, multiplier, oldMultiplier, shapesDir):
        """
        Apply multiplier in place of oldMultiplier to all tributary slopes 
        in subbasins and lsus tables (if any) in project database.
        """
        try:
            with self.conn as conn:
                if conn is None:
                    return
                cursor = conn.cursor()
                table = 'gis_lsus'
                factor = float(multiplier) / oldMultiplier
                # need to change CSL value
                sqlBase = 'UPDATE {0} SET csl = csl * {1!s}'
                sql = sqlBase.format(table, factor)
                cursor.execute(sql)
                conn.commit()
                # update lsus2 file
                lsus2File = QSWATUtils.join(shapesDir, Parameters._LSUS2 + '.shp')
                if not os.path.exists(lsus2File):
                    QSWATUtils.loginfo('{0} not found'.format(lsus2File))
                    return
                lsus2Layer = QgsVectorLayer(lsus2File, QSWATUtils._ACTLSUSLEGEND, 'ogr')
                provider = lsus2Layer.dataProvider()
                cslIdx = provider.fieldNameIndex('Csl')
                if cslIdx < 0:
                    QSWATUtils.loginfo('Csl field in {0} not found'.format(lsus2File))
                    return
                mmap = dict()
                request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([cslIdx])
                for feature in provider.getFeatures(request):
                    mmap[feature.id()] = {cslIdx: float(feature[cslIdx]) * factor}
                if not provider.changeAttributeValues(mmap):
                    QSWATUtils.loginfo('Failed to update {0}'.format(lsus2File))
        except Exception:
            QSWATUtils.loginfo('Failed to change tributary slopes: {0}'.format(traceback.format_exc()))
            # table may not exist yet
            return   
        
    def changeMeanSlopes(self, multiplier, oldMultiplier, shapesDir):
        """
        Apply multiplier in place of oldMultiplier to all mean slopes 
        in gis_subbasins, gis_lsus and gis_hrus tables (if any) in project database.
        """
        try:
            with self.conn as conn:
                if conn is None:
                    return
                cursor = conn.cursor()
                table1 = 'gis_subbasins'
                table2 = 'gis_lsus'
                table3 = 'gis_hrus'
                factor = float(multiplier) / oldMultiplier
                # need to change slope value
                sqlBase = 'UPDATE {0} SET slope = slope * {1!s}'
                sql = sqlBase.format(table2, factor)
                cursor.execute(sql)
                sql = sqlBase.format(table3, factor)
                cursor.execute(sql)
                # for subbasins table we need to update slo1 field as above, but also recalculate
                # the sll field
                sql = self.sqlSelect(table1, 'id, slo1', '', '')
                update = 'UPDATE {0} SET sll=?, slo1=? WHERE id=?'.format(table1)
                for row in cursor.execute(sql):
                    meanSlopePercent = float(row['slo1']) * factor
                    sll = QSWATUtils.getSlsubbsn(meanSlopePercent / 100)
                    cursor.execute(update, (sll, meanSlopePercent, row['id']))
                conn.commit()
                # update Slope in lsus2 file
                lsus2File = QSWATUtils.join(shapesDir, Parameters._LSUS2 + '.shp')
                if not os.path.exists(lsus2File):
                    QSWATUtils.loginfo('{0} not found'.format(lsus2File))
                    return
                lsus2Layer = QgsVectorLayer(lsus2File, QSWATUtils._ACTLSUSLEGEND, 'ogr')
                provider = lsus2Layer.dataProvider()
                slopeIdx = provider.fieldNameIndex('Slope')
                if slopeIdx < 0:
                    QSWATUtils.loginfo('Slope field in {0} not found'.format(lsus2File))
                    return
                mmap = dict()
                request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([slopeIdx])
                for feature in provider.getFeatures(request):
                    mmap[feature.id()] = {slopeIdx: float(feature[slopeIdx]) * factor}
                if not provider.changeAttributeValues(mmap):
                    QSWATUtils.loginfo('Failed to update {0}'.format(lsus2File))
                # update Sll and Slo1 in in subs1 file
                subs1File = QSWATUtils.join(shapesDir, Parameters._SUBS1 + '.shp')
                if not os.path.exists(subs1File):
                    QSWATUtils.loginfo('{0} not found'.format(subs1File))
                    return
                subs1Layer = QgsVectorLayer(subs1File, 'Subbasins', 'ogr')
                provider = subs1Layer.dataProvider()
                sllIdx = provider.fieldNameIndex('Sll')
                if sllIdx < 0:
                    QSWATUtils.loginfo('Sll field in {0} not found'.format(subs1File))
                    return
                slo1Idx = provider.fieldNameIndex('Slo1')
                if slo1Idx < 0:
                    QSWATUtils.loginfo('Slo1 field in {0} not found'.format(subs1File))
                    return
                mmap = dict()
                request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([sllIdx, slo1Idx])
                for feature in provider.getFeatures(request):
                    meanSlopePercent = float(feature[slo1Idx]) * factor
                    sll = QSWATUtils.getSlsubbsn(meanSlopePercent / 100)
                    mmap[feature.id()] = {sllIdx: sll, slo1Idx: meanSlopePercent}
                if not provider.changeAttributeValues(mmap):
                    QSWATUtils.loginfo('Failed to update {0}'.format(subs1File))
        except Exception:
            QSWATUtils.loginfo('Failed to change mean slopes: {0}'.format(traceback.format_exc()))
            # table may not exist yet
            return    
        
    def changeMainLengths(self, multiplier, oldMultiplier, shapesDir):
        """
        Apply multiplier in place of oldMultiplier to all main channel lengths
        in gis_channels table (if any) in project database, and consequently also change
        main channel slope.
        """
        try:
            with self.conn as conn:
                if conn is None:
                    return
                table = 'gis_channels'
                factor = float(multiplier) / oldMultiplier
                # need to change len2 value
                sql = 'UPDATE {0} SET len2 = len2 * {1}, slo2 = slo2 / {1}'.format(table, str(factor))
                conn.execute(sql)
                conn.commit()
                # update rivs1 file
                rivs1File = QSWATUtils.join(shapesDir, Parameters._RIVS1 + '.shp')
                if not os.path.exists(rivs1File):
                    QSWATUtils.loginfo('{0} not found'.format(rivs1File))
                    return
                rivs1Layer = QgsVectorLayer(rivs1File, FileTypes.legend(FileTypes._CHANNELREACHES), 'ogr')
                provider = rivs1Layer.dataProvider()
                len2Idx = provider.fieldNameIndex('Len2')
                if len2Idx < 0:
                    QSWATUtils.loginfo('Len2 field in {0} not found'.format(rivs1File))
                    return
                slo2Idx = provider.fieldNameIndex('Slo2')
                if slo2Idx < 0:
                    QSWATUtils.loginfo('Slo2 field in {0} not found'.format(rivs1File))
                    return
                mmap = dict()
                request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([len2Idx, slo2Idx])
                for feature in provider.getFeatures(request):
                    mmap[feature.id()] = {len2Idx: float(feature[len2Idx]) * factor, slo2Idx: float(feature[slo2Idx]) / factor}
                if not provider.changeAttributeValues(mmap):
                    QSWATUtils.loginfo('Failed to update {0}'.format(rivs1File))
        except Exception:
            QSWATUtils.loginfo('Failed to change main lengths: {0}'.format(traceback.format_exc()))
            # table may not exist yet
            return
            
    def changeTributaryLengths(self, multiplier, oldMultiplier, shapesDir):
        """
        Apply multiplier in place of oldMultiplier to all tributary lengths 
        (longest flow path) in subbasins tables (if any) in project database, 
        and consequently change tributary slope in gis_lsus tables
        """
        try:
            with self.conn as conn:
                if conn is None:
                    return
                cursor = conn.cursor()
                table1 = 'gis_subbasins'
                factor = float(multiplier) / oldMultiplier
                sql1 = 'UPDATE {0} SET len1 = len1 * {1}'.format(table1, str(factor))
                cursor.execute(sql1)
                table2 = 'gis_lsus'
                # slope is csl
                # slopes are affected inversely
                sql2 = 'UPDATE {0} SET len1 = len1 * {1}, csl = csl / {1}'.format(table2, str(factor))
                cursor.execute(sql2)
                conn.commit()
                # update Len1 in in subs1 file
                subs1File = QSWATUtils.join(shapesDir, Parameters._SUBS1 + '.shp')
                if not os.path.exists(subs1File):
                    QSWATUtils.loginfo('{0} not found'.format(subs1File))
                    return
                subs1Layer = QgsVectorLayer(subs1File, 'Subbasins', 'ogr')
                provider = subs1Layer.dataProvider()
                len1Idx = provider.fieldNameIndex('Len1')
                if len1Idx < 0:
                    QSWATUtils.loginfo('Len1 field in {0} not found'.format(subs1File))
                    return
                mmap = dict()
                request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([len1Idx])
                for feature in provider.getFeatures(request):
                    mmap[feature.id()] = {len1Idx: float(feature[len1Idx]) * factor}
                if not provider.changeAttributeValues(mmap):
                    QSWATUtils.loginfo('Failed to update {0}'.format(subs1File))
                # update lsus2 file
                lsus2File = QSWATUtils.join(shapesDir, Parameters._LSUS2 + '.shp')
                if not os.path.exists(lsus2File):
                    QSWATUtils.loginfo('{0} not found'.format(lsus2File))
                    return
                lsus2Layer = QgsVectorLayer(lsus2File, QSWATUtils._ACTLSUSLEGEND, 'ogr')
                provider = lsus2Layer.dataProvider()
                len1Idx = provider.fieldNameIndex('Len1')
                if len1Idx < 0:
                    QSWATUtils.loginfo('Len1 field in {0} not found'.format(lsus2File))
                    return
                cslIdx = provider.fieldNameIndex('Csl')
                if cslIdx < 0:
                    QSWATUtils.loginfo('Csl field in {0} not found'.format(lsus2File))
                    return
                mmap = dict()
                request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([len1Idx, cslIdx])
                for feature in provider.getFeatures(request):
                    mmap[feature.id()] = {len1Idx: float(feature[len1Idx]) * factor, cslIdx: float(feature[cslIdx]) / factor}
                if not provider.changeAttributeValues(mmap):
                    QSWATUtils.loginfo('Failed to update {0}'.format(lsus2File))
        except Exception:
            QSWATUtils.loginfo('Failed to change tributary slopes: {0}'.format(traceback.format_exc()))
            # table may not exist yet
            return   
        
    def changeChannelWidthAndDepth(self, widthMult, widthExp, depthMult, depthExp, shapesDir):
        """Change main and tributary channel widths and depths in gis_channels and gis_lsus tables."""
        with self.conn as conn:
            if conn is None:
                return
            cursor = conn.cursor()
            try:
                # do gis_channels first as generated in delineation, before subbasins and lsus
                table = 'gis_channels'
                sql = self.sqlSelect(table, 'id, areac', '', '')
                update = 'UPDATE {0} SET wid2=?, dep2=? WHERE id=?'.format(table)
                for row in cursor.execute(sql):
                    drainAreaKm = float(row['areac']) / 100 # areac in ha
                    channelWidth = widthMult * (drainAreaKm ** widthExp)
                    channelDepth = depthMult * (drainAreaKm ** depthExp)
                    cursor.execute(update, (channelWidth, channelDepth, row['id']))
                conn.commit()
                # update rivs1 file
                rivs1File = QSWATUtils.join(shapesDir, Parameters._RIVS1 + '.shp')
                if not os.path.exists(rivs1File):
                    QSWATUtils.loginfo('{0} not found'.format(rivs1File))
                    return
                rivs1Layer = QgsVectorLayer(rivs1File, FileTypes.legend(FileTypes._CHANNELREACHES), 'ogr')
                provider = rivs1Layer.dataProvider()
                areaIdx = provider.fieldNameIndex('AreaC')
                if areaIdx < 0:
                    QSWATUtils.loginfo('AreaC field in {0} not found'.format(rivs1File))
                    return
                wid2Idx = provider.fieldNameIndex('Wid2')
                if wid2Idx < 0:
                    QSWATUtils.loginfo('Wid2 field in {0} not found'.format(rivs1File))
                    return
                dep2Idx = provider.fieldNameIndex('Dep2')
                if dep2Idx < 0:
                    QSWATUtils.loginfo('Dep2 field in {0} not found'.format(rivs1File))
                    return
                mmap = dict()
                request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([areaIdx, wid2Idx, dep2Idx])
                for feature in provider.getFeatures(request):
                    drainAreaKm = float(feature[areaIdx]) / 100 # areac in ha
                    mmap[feature.id()] = {wid2Idx: widthMult * (drainAreaKm ** widthExp), dep2Idx: depthMult * (drainAreaKm ** depthExp)}
                if not provider.changeAttributeValues(mmap):
                    QSWATUtils.loginfo('Failed to update {0}'.format(rivs1File))
            except Exception:
                QSWATUtils.loginfo('Failed to change main channel widths and depths: {0}'.format(traceback.format_exc()))
                # gis_channels tables may not exist
                pass
            try:
                table = 'gis_lsus'
                sql = self.sqlSelect(table, 'id, area', '', '')
                update = 'UPDATE {0} SET wid1=?, dep1=? WHERE id=?'.format(table)
                for row in cursor.execute(sql):
                    drainAreaKm = float(row['area']) / 100 # area in ha
                    channelWidth = widthMult * (drainAreaKm ** widthExp)
                    channelDepth = depthMult * (drainAreaKm ** depthExp)
                    cursor.execute(update, (channelWidth, channelDepth, row['id']))
                conn.commit()
                # update lsus2 file
                lsus2File = QSWATUtils.join(shapesDir, Parameters._LSUS2 + '.shp')
                if not os.path.exists(lsus2File):
                    QSWATUtils.loginfo('{0} not found'.format(lsus2File))
                    return
                lsus2Layer = QgsVectorLayer(lsus2File, QSWATUtils._ACTLSUSLEGEND, 'ogr')
                provider = lsus2Layer.dataProvider()
                areaIdx = provider.fieldNameIndex(Parameters._AREA)
                if areaIdx < 0:
                    QSWATUtils.loginfo('{0} field in {1} not found'.format(Parameters._AREA, rivs1File))
                    return
                wid1Idx = provider.fieldNameIndex('Wid1')
                if wid1Idx < 0:
                    QSWATUtils.loginfo('Wid1 field in {0} not found'.format(lsus2File))
                    return
                dep1Idx = provider.fieldNameIndex('Dep1')
                if dep1Idx < 0:
                    QSWATUtils.loginfo('Dep1 field in {0} not found'.format(lsus2File))
                    return
                mmap = dict()
                request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([areaIdx, wid1Idx, dep1Idx])
                for feature in provider.getFeatures(request):
                    drainAreaKm = float(feature[areaIdx]) / 100 # area in ha
                    mmap[feature.id()] = {wid1Idx: widthMult * (drainAreaKm ** widthExp), dep1Idx: depthMult * (drainAreaKm ** depthExp)}
                if not provider.changeAttributeValues(mmap):
                    QSWATUtils.loginfo('Failed to update {0}'.format(lsus2File))
            except Exception:
                QSWATUtils.loginfo('Failed to change tributary channel widths and depths: {0}'.format(traceback.format_exc()))
                # table may not exist
                return
        
    def changeUpslopeHRUDrain(self, percent):
        """Change upslope HRU drainage to percent into channel or reservoir, rest to downslope LSU."""
        with self.conn as conn:
            if conn is None:
                return
            try:
                # can't seem to access rowid with sqlite3.Row
                conn.row_factory = lambda _, row: row
                cursor = conn.cursor()
                table1 = 'gis_hrus'
                table2 = 'gis_routing'
                sql1 = self.sqlSelect(table1, 'id, lsu', '', '')
                sql2 = self.sqlSelect(table2, 'rowid, sinkcat', '', 'sourceid=? AND sourcecat=?')
                update = 'UPDATE {0} SET percent=? WHERE rowid=?'.format(table2)
                # first find upslope HRUs
                for hRow in cursor.execute(sql1):
                    lsuId = hRow[1]
                    if QSWATUtils.landscapeUnitIdIsUpslope(lsuId):
                        hru = hRow[0]
                        for rRow in cursor.execute(sql2, (hru, 'HRU')):
                            sinkCat = rRow[1]
                            rowId = rRow[0]
                            # set drain to channel or reservoir to percent
                            if sinkCat == 'CH' or sinkCat == 'RES':
                                cursor.execute(update, (percent, rowId))
                                # set drain to LSU to 100 - percent
                            elif sinkCat == 'LSU':
                                cursor.execute(update, (100 - percent, rowId))
            except Exception:
                # table may not exist
                return 
            finally:
                conn.row_factory = sqlite3.Row   
        
        
    def writeElevationBands(self, basinElevBands, numElevBands):
        """Write gis_elevationbands table."""
        with self.conn as conn:
            if not conn:
                return
            table = 'gis_elevationbands'
            cursor = conn.cursor()
            dropSQL = 'DROP TABLE IF EXISTS ' + table
            try:
                cursor.execute(dropSQL)
            except Exception:
                QSWATUtils.exceptionError('Could not drop table {0} from project database {1}'.format(table, self.dbFile), self.isBatch)
                return
            createSQL = 'CREATE TABLE ' + table + self._ELEVATIONBANDSTABLE
            try:
                cursor.execute(createSQL)
            except Exception:
                QSWATUtils.exceptionError('Could not create table {0} in project database {1}'.format(table, self.dbFile), self.isBatch)
                return
            #indexSQL = 'CREATE UNIQUE INDEX idx' + self._ELEVATIONBANDSTABLEINDEX + ' ON ' + table + '([' + self._ELEVATIONBANDSTABLEINDEX + '])'
            #cursor.execute(indexSQL)
            for (SWATBasin, bands) in basinElevBands.items():
                if bands is not None:
                    # need mid-points of bands, but list has start values
                    el1 = bands[0][0]
                    el2 = bands[1][0]
                    semiWidth = (el2 - el1) / 2.0
                    row = '({0!s},'.format(SWATBasin)
                    for i in range(10):
                        if i < numElevBands:
                            el= bands[i][0] + semiWidth
                        else:
                            el = 0
                        row += '{:.2F},'.format(el)
                    for i in range(10):
                        if i < numElevBands:
                            frac = bands[i][1]
                        else:
                            frac = 0
                        row += '{:.4F}'.format(frac / 100.0) # fractions were percentages
                        sep = ',' if i < 9 else ')'
                        row += sep
                else:
                    row = '({0!s},0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)'.format(SWATBasin)
                sql = 'INSERT INTO ' + table + ' VALUES ' + row
                try:
                    cursor.execute(sql)
                except Exception:
                    QSWATUtils.exceptionError('Could not write to table {0} in project database {1}'.format(table, self.dbFile), self.isBatch)
                    return
            conn.commit()
            self.hashDbTable(conn, table)
            
    _LANDUSELOOKUPTABLE2 = '(LANDUSE_ID INTEGER, SWAT_CODE TEXT)'
    _LANDUSELOOKUPTABLE3 = '(LANDUSE_ID INTEGER, SWAT_CODE TEXT, DESCRIPTION TEXT)'
    
    _SOILLOOKUPTABLE = '(SOIL_ID INTEGER, NAME TEXT)'
    
    def readLanduseCsv(self):
        """Read landuse csv file."""
        return self.readCsv('landuse', self.landuseTableNames)
    
    def readSoilCsv(self):
        """Read soil csv file."""
        return self.readCsv('soil', self.soilTableNames)
    
    def readPlantCsv(self):
        """Read plant csv file."""
        return self.readCsv('plant', self.plantTableNames)
    
    def readUrbanCsv(self):
        """Read urban csv file."""
        return self.readCsv('urban', self.urbanTableNames)
    
    def readUsersoilCsv(self):
        """Read usersoil csv file."""
        return self.readCsv('usersoil', self.usersoilTableNames)
    
    def readCsv(self, typ, names):
        """Invite reader to choose csv file and read it."""
        settings = QSettings()
        if settings.contains('/QSWATPlus/LastInputPath'):
            path = str(settings.value('/QSWATPlus/LastInputPath'))
        else:
            path = ''
        if typ == 'plant' or typ == 'urban' or typ == 'usersoil':
            caption = 'Choose {0} csv file'.format(typ)
        else:
            caption = 'Choose {0} lookup csv file'.format(typ)
        caption = QSWATUtils.trans(caption)
        filtr = FileTypes.filter(FileTypes._CSV)
        csvFile, _ = QFileDialog.getOpenFileName(None, caption, path, filtr)
        if csvFile is not None and os.path.isfile(csvFile):
            settings.setValue('/QSWATPlus/LastInputPath', os.path.dirname(str(csvFile)))
            return self.readCsvFile(csvFile, typ, names)
        else:
            return '';
        
    def readCsvFile(self, csvFile, typ, names):
        """Read csv file into table.
        
        The database used is the landuse and soil database if typ is usersoil, plant, or urban
        else the project database.
        The table name is the csv file name (without extension) if that contains typ as a substring, 
        else is typ if that is usersoil, plant, or urban
        else is typ_lookup.
        The table name is then extended with 0, 1, etc until a new name is found
        that is not in names.
        """
        if typ == 'usersoil_layer':
            # use singlaton usersoil table name in names as basis for layer name, 
            # so they necessarily match
            table = names[0] + '_layer'
            return self.importCsv(table, typ, csvFile)
        else:
            table = os.path.splitext(os.path.split(csvFile)[1])[0]
            if typ not in table:
                if typ == 'usersoil' or typ == 'plant' or typ == 'urban':
                    table = typ
                else:
                    table = '{0}_lookup'.format(typ)
            base = table;
            i = 0;
            while table in names:
                table = base + str(i)
                i = i+1
            return self.importCsv(table, typ, csvFile)
    
    def importCsv(self, table, typ, fil):
        """
        Write table of typ either soil or landuse in project database, 
        or usersoil in landuse and soil database, using csv file fil.
        """
        if typ == 'usersoil' or typ == 'usersoil_layer' or typ == 'plant' or typ == 'urban':
            db = self.plantSoilDatabase
            isProjDb = filecmp.cmp(self.plantSoilDatabase, self.dbFile)
            isRefDb = filecmp.cmp(self.plantSoilDatabase, self.dbRefFile)
            if isProjDb:
                conn = self.conn
            elif isRefDb:
                conn = self.connRef
            else:
                conn = sqlite3.connect(self.plantSoilDatabase)
            if typ == 'usersoil':
                # we should have have either 152 columns
                # or 11 plus a layers file
                # read first line to find which
                with open(fil, 'r', newline='') as csvFile:
                    dialect = csv.Sniffer().sniff(csvFile.read(1000))  # sample size 1000 bytes is arbitrary
                    csvFile.seek(0)
                    reader = csv.reader(csvFile, dialect)
                    line1 = next(reader)
                    numFields = len(line1)
                    needsSeparateLayerTable = numFields < 20
                if needsSeparateLayerTable:
                    layerTable = self.readCsv('usersoil_layer', [table])
                    QSWATUtils.loginfo('Making separate usersoil tables {0} and {1}'.format(table, layerTable))
                    values = ' VALUES(?,?,?,?,?,?,?,?,?,?,?)'
                else:
                    values = ' VALUES(' + ','.join(['?']*152) + ')'
            elif typ == 'usersoil_layer':
                values = ' VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'
            elif typ == 'plant':
                values = ' VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'
            elif typ == 'urban':
                values = ' VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)'
        else:
            conn = self.conn
            isProjDb = True
            isRefDb = False
            db = self.dbFile
            values = ' VALUES(?,?)'
            isLanduse = typ == 'landuse'
        sql = 'INSERT INTO ' + table + values
        if not conn:
            return ''
        cursor = conn.cursor()
        # should not happen, but safety first
        dropSQL = 'DROP TABLE IF EXISTS ' + table
        try:
            cursor.execute(dropSQL)
        except Exception:
            QSWATUtils.exceptionError('Could not drop table {0} from database {1}'.format(table, db), self.isBatch)
            return ''
        if typ == 'usersoil':
            if needsSeparateLayerTable:
                design = self._SOILTABLE
            else:
                design = self._USERSOILTABLE
        elif typ == 'usersoil_layer':
            design = self._SOILLAYERTABLE
        elif typ == 'plant':
            design = self._PLANTTABLE
        elif typ == 'urban':
            design = self._URBANTABLE
        elif isLanduse:
            design = self._LANDUSELOOKUPTABLE2
        else:
            design =  self._SOILLOOKUPTABLE
        createSQL = 'CREATE TABLE ' + table + design
        try:
            cursor.execute(createSQL)
        except Exception:
            QSWATUtils.error('Could not create table {0} in database {1}'.format(table, db), self.isBatch)
            return ''
        with open(fil, 'r', newline='') as csvFile:
            # sample size 20000 bytes is arbitrary
            # fails to find delimiter in plant.csv with size of 2000
            dialect = csv.Sniffer().sniff(csvFile.read(20000))  
            csvFile.seek(0)
            hasHeader = csv.Sniffer().has_header(csvFile.read(20000))
            csvFile.seek(0)
            reader = csv.reader(csvFile, dialect)
            line1 = next(reader)
            if type == 'landuse':
                # check if we have the optional third description field
                if len(line1) == 3:
                    # recreate table with 3 columns
                    cursor.execute(dropSQL)
                    createSQL = 'CREATE TABLE ' + table + self._LANDUSELOOKUPTABLE3
                    cursor.execute(createSQL)
                    sql = 'INSERT INTO ' + table + ' VALUES(?,?,?)'
            # if we have a header we have already skipped it.  Otherwise return to start.
            # Probably not a good idea to do a seek on file while reading with csv, so recreate reader
            if not hasHeader:
                reader = None
                csvFile.seek(0)
                reader = csv.reader(csvFile, dialect)
            for line in reader:
                try:
                    cursor.execute(sql, tuple(line))
                except Exception:
                    QSWATUtils.exceptionError('Could not write to table {0} in database {1} from file {2}'.format(table, db, fil), self.isBatch)
                    return ''
        conn.commit()
        if typ == 'usersoil' or typ == 'plant' or typ == 'urban':
            if typ == 'usersoil':
                self.usersoilTableNames.append(table)
            elif typ == 'plant':
                self.plantTableNames.append(table)
            else:
                self.urbanTableNames.append(table)
            if not (isProjDb or isRefDb):
                conn.close()
        elif typ == 'usersoil_layer':
            pass
        elif isLanduse:
            self.landuseTableNames.append(table)
        else:
            self.soilTableNames.append(table)
        return table
    
    #=Not used==========================================================================
    # def createTopology1(self):
    #     """Create map SWATBasin -> SWATChannel -> LSUId -> hruNum-set from gis_channels, gis_lsus and gis_hrus."""
    #     topology = dict()
    #     with self.conn.cursor() as cursor:
    #         sql1 = self.sqlSelect('gis_channels', 'id, subbasin', '', '')
    #         for row1 in cursor.execute(sql1):
    #             SWATChannel = row1['id']
    #             SWATBasin = row1['subbasin']
    #             channels = topology.get(SWATBasin, dict())
    #             channels[SWATChannel] = dict()
    #             topology[SWATBasin] = channels
    #             sql2 = self.sqlSelect('gis_lsus', 'id', '', 'channel=?')
    #             for row2 in cursor.execute(sql2, (SWATChannel,)):
    #                 lsuId = row2['id']
    #                 lsus = channels.get(lsuId, dict())
    #                 lsus[lsuId] = dict()
    #                 channels[SWATChannel] = lsus
    #                 sql3 = self.sqlSelect('gis_hrus', 'id', '', 'lsu=?')
    #                 for row3 in cursor.execute(sql3, (lsuId,)):
    #                     hruNum = row3['id']
    #                     hruNums = lsus.get(lsuId, set())
    #                     hruNums.add(hruNum)
    #                     lsus[lsuId] = hruNums
    #     return topology
    #===========================================================================
        
    def createTopology(self):
        """Create HRU map SWATBasin -> SWATChannel -> LSUId -> hruNum-set,
        reservoir map SWATBasin -> SWATChannel -> LSUId -> reservoir number,
        and pond map SWATBasin -> SWATChannel -> LSUId -> pond number 
        from gis_channels, gis_lsus, gis_hrus and gis_water."""
        with self.conn.cursor() as cursor:
            resLSUs = dict()
            pndLSUs = dict()
            sql0 = self.sqlSelect('gis_water', 'id, wtype, lsu', '', '')
            for row0 in cursor.execute(sql0):
                lsuId = row0['lsu']
                if row0.wtype == 'RES':
                    resLSUs[lsuId] = row0['id']
                else:
                    pndLSUs[lsuId] = row0['id']
            lsus = dict()
            sql1 = self.sqlSelect('gis_hrus', 'id, lsu', '', '')
            for row1 in cursor.execute(sql1):
                hruNum = row1['id']
                lsuId = row1['lsu']
                hruNums = lsus.get(lsuId, set())
                hruNums.add(hruNum)
                lsus[lsuId] = hruNums
            channels = dict()
            resChannels = dict()
            pndChannels = dict()
            sql2 = self.sqlSelect('gis_lsus', 'id, channel', '', '')
            for row2 in cursor.execute(sql2):
                lsuId = row2['id']
                SWATChannel = row2['channel']
                lsus2 = channels.get(SWATChannel, dict())
                lsus2.update({lsuId : lsus.pop(lsuId)})
                channels[SWATChannel] = lsus2
                if lsuId in resLSUs:
                    resLSUs2 = resChannels.get(SWATChannel, dict)
                    resLSUs2.update({lsuId: resLSUs.pop(lsuId)})
                    resChannels[SWATChannel] = resLSUs2
                if lsuId in pndLSUs:
                    pndLSUs2 = pndChannels.get(SWATChannel, dict)
                    pndLSUs2.update({lsuId: pndLSUs.pop(lsuId)})
                    pndChannels[SWATChannel] = pndLSUs2
            topology = dict()
            reservoirs = dict()
            ponds = dict()
            sql3 = self.sqlSelect('gis_channels', 'id, subbasin', '', '')
            for row3 in cursor.execute(sql3):
                SWATChannel = row3['id']
                SWATBasin = row3['subbasin'] 
                channels3 = topology.get(SWATBasin, dict())
                channels3.update({SWATChannel: channels.pop(SWATChannel)})
                topology[SWATBasin] = channels3
                if SWATChannel in resChannels:
                    resChannels2 = reservoirs.get(SWATBasin, dict())
                    resChannels2.update({SWATChannel: resChannels.pop(SWATChannel)})
                    reservoirs[SWATBasin] = resChannels2
                if SWATChannel in pndChannels:
                    pndChannels2 = ponds.get(SWATBasin, dict())
                    pndChannels2.update({SWATChannel: pndChannels.pop(SWATChannel)})
                    ponds[SWATBasin] = pndChannels2
        return topology, reservoirs, ponds        
          
    ## Return an md5 hash value for a database table.  Used in testing.
    def hashDbTable(self, conn, table):
        # Only calculate and store table hashes when testing, as this is their purpose
        if 'test' in self.projName:
            # suspend row_factory setting
            # normal setting to sqlite3.Row produces dictionaries for rows, which have random order 
            # and hence produce random hashes
            # row_factory needs to be a function taking a cursor and row as tuple and returning a row
            # so we use an identity
            conn.row_factory = lambda _, row: row
            m = hashlib.md5()
            sql = self.sqlSelect(table, '*', '', '')
            for row in conn.execute(sql):
                m.update(row.__repr__().encode())
            result = m.hexdigest()
            QSWATUtils.loginfo('Hash for table {0}: {1}'.format(table, result))
            # restore row_factory
            conn.row_factory = sqlite3.Row
            return result
        return None
    
    @staticmethod
    def checkRouting(conn):
        """Check every source in gis_routing table drains ultimately to an outlet, i.e. there are no loops
        and everything not a final outlet has a sink which drains.  Also check routing for each
        source totals 100%.  Return lists of error messages and warning messages. ."""
        errors = []
        warnings = []
        table = 'gis_routing'
        # mapping category -> id-set showing sources that are known to drain to an outlet
        # to save tracking every source all the way
        done = dict()
        # mapping category -> id-set showing sources currently under investigation
        # (so all can be marked as done if the chain terminates)
        pending = dict()
        # mapping category -> id -> percent used to check sources with multiple sinks have 100% accounted for
        percentages = dict()
        nextSql = DBUtils.sqlSelect(table, '*', '', '')
        findSql = DBUtils.sqlSelect(table, 'sinkid, sinkcat, percent', '', 'sourceid=? AND sourcecat=?')
        # Might be tempted to use pending to detect loops, but note below we don't
        # add to pending for multiple sinks, so then e.g. A -> A 90% would just loop.
        # So we prefer a count.
        maxSteps = int(conn.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0])
        for row in conn.execute(nextSql):
            sid = int(row['sourceid'])
            scat = row['sourcecat']
            tid = int(row['sinkid'])
            tcat = row['sinkcat']
            percent = float(row['percent'])
            hasZero = percent == 0
            count = maxSteps
            while count > 0:
                if scat in done and sid in done[scat]:
                    # move pending to done
                    for pcat, pids  in pending.items():
                        if pcat in done:
                            done[pcat].update(pids)
                        else:
                            done[pcat] = pids
                    pending = dict()
                    break  # from while loop
                if percent < 100:
                    # add percent to percentages for this source
                    sourcePercentages = percentages.get(scat, None)
                    if sourcePercentages is None:
                        percentages[scat] = {sid: percent}
                    else:
                        if sid in sourcePercentages:
                            sourcePercentages[sid] += percent
                        else:
                            sourcePercentages[sid] = percent
                else:
                    # Only include source in pending (which should become done) 
                    # if there is only one sink for it, else other sinks will be ignored.
                    # Pending is only used for efficiency, to avoid tracking every source to a final outlet,
                    # so little harm in omitting some sources from it.
                    if scat in pending:
                        pending[scat].add(sid)
                    else:
                        pending[scat] = {sid}
                if tcat == 'X':
                    # move pending to done
                    for pcat, pids  in pending.items():
                        if pcat in done:
                            done[pcat].update(pids)
                        else:
                            done[pcat] = pids
                    pending = dict()
                    break  # from while loop
                count -= 1
                if count == 0:
                    if hasZero:
                        warnings.append('WARNING: There is a loop in the {0} table involving id {1} and category {2} but with a zero percentage' \
                                .format(table, sid, scat))
                    else:
                        errors.append('There is a loop in the {0} table involving id {1} and category {2}'.format(table, sid, scat))
                    # move pending to done
                    for pcat, pids  in pending.items():
                        if pcat in done:
                            done[pcat].update(pids)
                        else:
                            done[pcat] = pids
                    pending = dict()
                    break  # from while loop
                findRow = conn.execute(findSql, (tid, tcat)).fetchone()
                if findRow is None:
                    errors.append('Cannot find id {1} category {2} as a source in the {0} table'.format(table, tid, tcat))
                    break  # from while loop
                sid = tid
                scat = tcat
                tid = int(findRow['sinkid'])
                tcat = findRow['sinkcat']
                percent = findRow['percent']
                hasZero = hasZero or percent == 0
            #end of while loop
        # end of for loop
        # check all percentages are approximately 100
        for scat, data in percentages.items():
            for sid, percent in data.items():
                if int(percent + 0.5) != 100:
                    if percent == 0 and scat in {'RES', 'PND'}:
                        # an unused lake exit: ignore
                        pass
                    else:
                        errors.append('The percentages for id {1} and category {2} in the {0} table sum to {3} rather than 100' \
                                      .format(table, sid, scat, int(percent + 0.5)))
        return errors, warnings
    
    _HRUSCREATESQL = \
        """
        CREATE TABLE gis_hrus (
            id       INTEGER PRIMARY KEY
                             UNIQUE
                             NOT NULL,
            lsu      INTEGER,
            arsub    REAL,
            arlsu    REAL,
            landuse  TEXT,
            arland   REAL,
            soil     TEXT,
            arso     REAL,
            slp      TEXT,
            arslp    REAL,
            slope    REAL,
            lat      REAL,
            lon      REAL,
            elev     REAL
        );
        """
        
    _HRUSINSERTSQL = 'INSERT INTO gis_hrus VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)'
        
    _LSUSCREATESQL = \
        """
        CREATE TABLE gis_lsus (
            id       INTEGER PRIMARY KEY
                             UNIQUE
                             NOT NULL,
            category INTEGER,
            channel  INTEGER,
            area     REAL,
            slope    REAL,
            len1     REAL,
            csl      REAL,
            wid1     REAL,
            dep1     REAL,
            lat      REAL,
            lon      REAL,
            elev     REAL
        );
        """
        
    _LSUSINSERTSQL = 'INSERT INTO gis_lsus VALUES(?,?,?,?,?,?,?,?,?,?,?,?)'
        
    _POINTSCREATESQL = \
        """
        CREATE TABLE gis_points (
            id       INTEGER PRIMARY KEY
                             UNIQUE
                             NOT NULL,
            subbasin INTEGER,
            ptype    TEXT,
            xpr      REAL,
            ypr      REAL,
            lat      REAL,
            lon      REAL,
            elev     REAL
        );
        """
        
    _CHANNELSCREATESQL = \
        """
        CREATE TABLE gis_channels (
            id       INTEGER PRIMARY KEY
                             UNIQUE
                             NOT NULL,
            subbasin INTEGER,
            areac    REAL,
            len2     REAL,
            slo2     REAL,
            wid2     REAL,
            dep2     REAL,
            elevmin  REAL,
            elevmax  REAL
        );
        """
        
    _SUBBASINSCREATESQL = \
        """
        CREATE TABLE gis_subbasins (
            id       INTEGER PRIMARY KEY
                             UNIQUE
                             NOT NULL,
            area     REAL,
            slo1     REAL,
            len1     REAL,
            sll      REAL,
            lat      REAL,
            lon      REAL,
            elev     REAL,
            elevmin  REAL,
            elevmax  REAL
        );
        """
        
    _SUBBASINSINSERTSQL = 'INSERT INTO gis_subbasins VALUES(?,?,?,?,?,?,?,?,?,?)'
        
    _WATERCREATESQL = \
        """
        CREATE TABLE gis_water (
            id    INTEGER PRIMARY KEY
                             UNIQUE
                             NOT NULL,
            wtype TEXT,
            lsu   INTEGER,
            subbasin INTEGER,
            area  REAL,
            xpr   REAL,
            ypr   REAL,
            lat   REAL,
            lon   REAL,
            elev  REAL
        );
        """
        
    _WATERINSERTSQL = 'INSERT INTO gis_water VALUES(?,?,?,?,?,?,?,?,?,?)'

    _ROUTINGCREATESQL = \
        """
        CREATE TABLE gis_routing (
            sourceid  INTEGER,
            sourcecat TEXT,
            sinkid    INTEGER,
            sinkcat   TEXT,
            percent   REAL
        );
        """  
        
    _ROUTINGINDEXSQL = \
    """
    CREATE INDEX source ON gis_routing (
    sourceid,
    sourcecat
    );
    """
        
    _ROUTINGINSERTSQL = 'INSERT INTO gis_routing VALUES(?,?,?,?,?)' 
    
    _LANDEXEMPTCREATESQL = \
    """
    CREATE TABLE gis_landexempt (
    landuse TEXT
    );
    """
    
    _LANDEXEMPTINSERTSQL = 'INSERT INTO gis_landexempt VALUES(?)'
    
    _SPLITHRUSCREATESQL = \
    """
    CREATE TABLE gis_splithrus (
    landuse    TEXT,
    sublanduse TEXT,
    percent    REAL
    );
    """
    
    _SPLITHRUSINSERTSQL = 'INSERT INTO gis_splithrus VALUES(?,?,?)'
     
    _CREATEPROJECTCONFIG = \
    """
    CREATE TABLE project_config (
    id                       INTEGER  PRIMARY KEY
                                      NOT NULL
                                      DEFAULT (1),
    project_name             TEXT,
    project_directory        TEXT,
    editor_version           TEXT,
    gis_type                 TEXT,
    gis_version              TEXT,
    project_db               TEXT,
    reference_db             TEXT,
    wgn_db                   TEXT,
    wgn_table_name           TEXT,
    weather_data_dir         TEXT,
    weather_data_format      TEXT,
    input_files_dir          TEXT,
    input_files_last_written DATETIME,
    swat_last_run            DATETIME,
    delineation_done         BOOLEAN  DEFAULT (0) 
                                      NOT NULL,
    hrus_done                BOOLEAN  DEFAULT (0) 
                                      NOT NULL,
    soil_table               TEXT,
    soil_layer_table         TEXT,
    output_last_imported     DATETIME,
    imported_gis             BOOLEAN  DEFAULT (0) 
                                      NOT NULL,
    is_lte                   BOOLEAN  DEFAULT (0) 
                                      NOT NULL
    )
    """
    
    _INSERTPROJECTCONFIG = 'INSERT INTO project_config VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'  
    
    _CREATELAKESDATA = \
    """
    CREATE TABLE LAKESDATA (
    id         INTEGER PRIMARY KEY,
    subbasin   INTEGER,
    role       INTEGER,
    area       REAL,
    meanelev   REAL,
    outlink    INTEGER,
    outletid   INTEGER,
    outletx    REAL,
    outlety    REAL,
    outletelev REAL,
    centroidx  REAL,
    centroidy  REAL
    )
    """
    
    _INSERTLAKESDATA = 'INSERT INTO LAKESDATA VALUES(?,?,?,?,?,?,?,?,?,?,?,?)' 
    
    _CREATELAKELINKS = \
    """
    CREATE TABLE LAKELINKS (
    linkno    INTEGER PRIMARY KEY,
    lakeid    INTEGER REFERENCES LAKESDATA (id),
    inlet     BOOLEAN,
    inside    BOOLEAN,
    inletid   INTEGER,
    inletx    REAL,
    inlety    REAL,
    inletelev REAL
    )
    """
    
    _INSERTLAKELINKS = 'INSERT INTO LAKELINKS VALUES(?,?,?,?,?,?,?,?)'
    
    _CREATELAKEBASINS = \
    """
    CREATE TABLE LAKEBASINS (
    subbasin  INTEGER PRIMARY KEY,
    lakeid    INTEGER REFERENCES LAKESDATA (id)
    )
    """
    _INSERTLAKEBASINS = 'INSERT INTO LAKEBASINS VALUES(?,?)'
    
     
