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
from qgis.PyQt.QtCore import Qt
#from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import QFileDialog
#from qgis.core import * # @UnusedWildImport
#from qgis.gui import * # @UnusedWildImport
import os
import sqlite3
import csv

# Import the code for the dialog
from .exporttabledialog import ExportTableDialog
from .QSWATUtils import QSWATUtils, FileTypes # type: ignore 

class ExportTable():
    """Choose an sqlite database and a table and export table as csv file."""
    
    _PROJECTDB = 'Project database'
    _REFDB = "Project's reference database"
    _OTHERDB = 'Other sqlite database'
    
    def __init__(self, gv):
        """Initialise class variables."""
        self._gv = gv
        ## currnt database
        self.db = ''
        ## current connection
        self.conn = None
        self._dlg = ExportTableDialog()
        self._dlg.setWindowFlags(self._dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint & Qt.WindowMinimizeButtonHint)
        self._dlg.databaseBox.addItem(ExportTable._PROJECTDB)
        self._dlg.databaseBox.addItem(ExportTable._REFDB)
        self._dlg.databaseBox.addItem(ExportTable._OTHERDB)
        self._dlg.databaseBox.setCurrentIndex(-1)
        
    def run(self):
        """Run the form."""
        self._dlg.databaseBox.activated.connect(self.setTables)
        self._dlg.exportButton.clicked.connect(self.exportTable)
        self._dlg.closeButton.clicked.connect(self.close)
        self._dlg.exec_()
        
    def setTables(self):
        """Set tables for currently selected database."""
        if self._dlg.databaseBox.currentIndex() < 0:
            QSWATUtils.information('Please select a database', self._gv.isBatch)
            return
        item = self._dlg.databaseBox.currentText()
        if item == ExportTable._PROJECTDB:
            db = self._gv.db.dbFile
        elif item == ExportTable._REFDB:
            db = self._gv.db.dbRefFile
        elif item == ExportTable._OTHERDB:
            path = os.path.split(self._gv.db.dbFile)[0]  # project directory
            title = QSWATUtils.trans('Select sqlite database')
            db, _ = QFileDialog.getOpenFileName(None, title, path, FileTypes.filter(FileTypes._SQLITE))
            if db is None or db == '':
                return
        else:
            return
        if self.db != db:
            if self.conn is not None:
                self.conn.close()
            self.db = db
            self.conn = sqlite3.connect(db)
            if self.conn is None:
                QSWATUtils.error('Failed to connect to database {0}'.format(db), self._gv.isBatch)
                return
            self._dlg.tableBox.clear()
            tables = []
            sql = 'SELECT name FROM sqlite_master WHERE TYPE="table"'
            for row in self.conn.execute(sql):
                tables.append(row[0])
            tables.sort()
            self._dlg.tableBox.addItems(tables)
        self._dlg.tableBox.setCurrentIndex(-1)
        
    def exportTable(self):
        """Export selected table as csv file."""
        if self.conn is None:
            self.setTables()
        if self._dlg.tableBox.currentIndex() < 0:
            QSWATUtils.information('Please select a table', self._gv.isBatch)
            return
        table = self._dlg.tableBox.currentText()
        sql = 'PRAGMA TABLE_INFO({0})'.format(table)
        varz = []
        for row in self.conn.execute(sql):
            varz.append(row[1])
        path = os.path.split(self._gv.db.dbFile)[0]  # project directory
        title = QSWATUtils.trans('Select csv file name')
        csvFile, _ = QFileDialog.getSaveFileName(None, title, path, FileTypes.filter(FileTypes._CSV))
        if csvFile is None or csvFile == '':
            return
        with open(csvFile, 'w', newline='') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)  # quote fields containing delimeter or other special characters
            writer.writerow(varz)
            sql = 'SELECT * FROM {0}'.format(table)
            for row in self.conn.execute(sql):
                writer.writerow(list(row))
        QSWATUtils.information('Table {0} written to {1}'.format(table, csvFile), self._gv.isBatch)
                
    def close(self):
        """Close connection and form."""
        if self.conn is not None:
            self.conn.close()
        self._dlg.close()