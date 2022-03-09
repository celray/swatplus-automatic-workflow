'''
Created on Dec 30, 2015

@author: Chris George
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 '''
from qgis.PyQt.QtCore import QObject, QSettings, Qt
from qgis.PyQt.QtGui import QFont, QFontDatabase
from qgis.PyQt.QtWidgets import QApplication, QFileDialog, QMessageBox, QTableWidgetItem

import sys
import os
import csv
from datetime import datetime, timedelta
import math
import locale
# import seaborn as sns
from matplotlib.figure import Figure  # @UnresolvedImport
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,  # @UnresolvedImport
    NavigationToolbar2QT as NavigationToolbar)  # @UnresolvedImport
try:
    from .graphdialog import GraphDialog  # @UnusedImport
except:
    # stand alone version
    from graphdialog1 import GraphDialog  # @UnresolvedImport @Reimport

class SWATGraph(QObject):
    """Display SWAT result data as line graphs or bar chart."""
    
    def __init__(self, csvFile):
        """Initialise class variables."""
        QObject.__init__(self)
        self._dlg = GraphDialog()
        self._dlg.setWindowFlags(self._dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        ## csv file of results
        self.csvFile = csvFile
        ## canvas for displaying matplotlib figure
        self.canvas = None
        ## matplotlib tool bar
        self.toolbar = None
        ## matplotlib axes
        self.ax1 = None
        
    def run(self):
        """Initialise form and run on initial csv file."""
        self._dlg.lineOrBar.addItem('Line graph')
        self._dlg.lineOrBar.addItem('Bar chart')
        self._dlg.lineOrBar.setCurrentIndex(0)
        self._dlg.newFile.clicked.connect(self.getCsv)
        self._dlg.updateButton.clicked.connect(self.updateGraph)
        self._dlg.closeForm.clicked.connect(self.closeFun)
        self.setUbuntuFont()
        self.readCsv()
        self._dlg.exec_()
        
    def addmpl(self, fig):
        """Add graph defined in fig."""
        self.canvas = FigureCanvas(fig)
        # graphvl is the QVBoxLayout instance added to the graph widget.
        # Needed to make fig expand to fill graph widget.
        self._dlg.graphvl.addWidget(self.canvas)
        self.canvas.draw()
        self.toolbar = NavigationToolbar(self.canvas, 
                self._dlg.graph, coordinates=True)
        self._dlg.graphvl.addWidget(self.toolbar)
        
    def rmmpl(self):
        """Remove current graph if any."""
        try:
            self._dlg.graphvl.removeWidget(self.canvas)
            self.canvas.close()
            self._dlg.graphvl.removeWidget(self.toolbar)
            self.toolbar.close()
            self.ax1 = None
            return
        except Exception:
            # no problem = may not have been a graph
            return
        
    @staticmethod
    def trans(msg):
        """Translate message."""
        return QApplication.translate("QSWATPlus", msg, None)
        
    @staticmethod
    def error(msg):
        """Report msg as an error."""
        msgbox = QMessageBox()
        msgbox.setWindowTitle('SWATGraph')
        msgbox.setIcon(QMessageBox.Critical)
        msgbox.setText(SWATGraph.trans(msg))
        msgbox.exec_()
        return
    
    def getCsv(self):
        """Ask user for csv file."""
        settings = QSettings()
        if settings.contains('/QSWATPlus/LastInputPath'):
            path = str(settings.value('/QSWATPlus/LastInputPath'))
        else:
            path = ''
        filtr = self.trans('CSV files (*.csv)')
        csvFile, _ = QFileDialog.getOpenFileName(None, 'Open csv file', path, filtr)
        if csvFile is not None and csvFile != '':
            settings.setValue('/QSWATPlus/LastInputPath', os.path.dirname(str(csvFile)))
            self.csvFile = csvFile
            self.readCsv()
        
    def readCsv(self):
        """Read current csv file (if any)."""
        # csvFile may be none if run from command line
        if not self.csvFile or self.csvFile == '':
            return
        if not os.path.exists(self.csvFile):
            self.error('Error: Cannot find csv file {0}'.format(self.csvFile))
            return
        """Read csv file into table; create statistics (coefficients); draw graph."""
        # clear graph
        self.rmmpl()
        # clear table
        self._dlg.table.clear()
        for i in range(self._dlg.table.columnCount()-1, -1, -1):
            self._dlg.table.removeColumn(i)
        self._dlg.table.setColumnCount(0)
        self._dlg.table.setRowCount(0)
        row = 0
        numCols = 0
        with open(self.csvFile, 'r', newline='') as csvFil:
            reader = csv.reader(csvFil)
            for line in reader:
                try:
                    # use headers in first line
                    if row == 0:
                        numCols = len(line)
                        for i in range(numCols):
                            self._dlg.table.insertColumn(i)
                        self._dlg.table.setHorizontalHeaderLabels(line)
                    else:
                        self._dlg.table.insertRow(row-1)
                        for i in range(numCols):
                            try:
                                val = line[i].strip()
                            except Exception as e:
                                self.error('Error: could not read file {0} at line {1} column {2}: {3}'.format(self.csvFile, row+1, i+1, repr(e)))
                                return
                            item = QTableWidgetItem(val)
                            self._dlg.table.setItem(row-1, i, item)
                    row = row + 1
                except Exception as e:
                    self.error('Error: could not read file {0} at line {1}: {2}'.format(self.csvFile, row+1, repr(e)))
                    return
        # columns are too narrow for headings
        self._dlg.table.resizeColumnsToContents()
        # rows are too widely spaced vertically
        self._dlg.table.resizeRowsToContents()
        self.writeStats()
        self.updateGraph()
        
    @staticmethod
    def makeFloat(s):
        """Parse string s as float and return; return nan on failure."""
        try:
            return float(s)
        except Exception:
            return float('nan')
        
    def updateGraph(self):
        """Redraw graph as line or bar chart according to lineOrBar setting."""
        style = 'bar' if self._dlg.lineOrBar.currentText() == 'Bar chart' else 'line'
        self.drawGraph(style)
        
    @staticmethod
    def shiftDates(dates, shift):
        """Add shift (number of days) to each date in dates."""
        delta = timedelta(days=shift)
        return [x + delta for x in dates]
    
    @staticmethod
    def getDateFormat(date):
        """
        Return date strptime format string from example date, plus basic width for drawing bar charts.
    
        Basic width is how matplotlib divides the date axis: number of days in the time unit
        Assumes date has one of 3 formats:
        yyyy: annual: return %Y and 12
        yyyy/m or yyyy/mm: monthly: return %Y/%m and 30
        yyyyddd: daily: return %Y%j and 24
        """
        if date.find('/') > 0:
            return '%Y/%m', 30
        length = len(date)
        if length == 4:
            return '%Y', 365
        if length == 7:
            return '%Y%j', 1
        SWATGraph.error('Cannot parse date {0}'.format(date))
        return '', 1
    
        
    def drawGraph(self, style):
        """Draw graph as line or bar chart according to style."""
        # preserve title, labels and yscale if they exist
        # in order to replace them when updating graph
        try:
            title = self.ax1.get_title()
        except Exception:
            title = ''
        try:
            xlbl = self.ax1.get_xlabel()
        except Exception:
            xlbl = ''
        try:
            ylbl = self.ax1.get_ylabel()
        except Exception:
            ylbl = ''
        try:
            yscl = self.ax1.get_yscale()
        except Exception:
            yscl = ''
        self.rmmpl()
        fig = Figure()
        # left, bottom, width, height adjusted to leave space for legend below
        self.ax1 = fig.add_axes([0.05, 0.22, 0.92, 0.68])
        numPlots = self._dlg.table.columnCount() - 1
        rng = range(self._dlg.table.rowCount())
        fmt, widthBase = self.getDateFormat(str(self._dlg.table.item(0, 0).text()).strip())
        if fmt == '':
            # could not parse
            return
        xVals = [datetime.strptime(str(self._dlg.table.item(i, 0).text()).strip(), fmt) for i in rng]
        for col in range(1, numPlots+1):
            yVals = [self.makeFloat(self._dlg.table.item(i, col).text()) for i in rng]
            h = self._dlg.table.horizontalHeaderItem(col).text()
            if style == 'line':
                self.ax1.plot(xVals, yVals, label=h)
                # reinstate yscale (only relevant for line graphs)
                if yscl == 'log':
                    self.ax1.set_yscale(yscl, nonposy='mask')
                elif yscl != '':
                    self.ax1.set_yscale(yscl)
            else:
                # width of bars in days.  
                # adding 1 to divisor gives space of size width between each date's group
                width = float(widthBase) / (numPlots+1)
                # can't imagine anyone wanting more than 7 colours
                # but just in case we'll use shades of grey for 8 upwards
                colours = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
                colour = colours[col-1] if col <= 7 else str(float((col - 7)/(numPlots - 6)))
                mid = numPlots / 2
                shift = width * (col - 1 - mid)
                xValsShifted = xVals if shift == 0 else self.shiftDates(xVals, shift)
                self.ax1.bar(xValsShifted, yVals, width, color=colour, linewidth=0, label=h)
        # reinstate title and labels
        if title != '':
            self.ax1.set_title(title)
        if xlbl != '':
            self.ax1.set_xlabel(xlbl)
        else:
            self.ax1.set_xlabel('Date')
        if ylbl != '':
            self.ax1.set_ylabel(ylbl)
        self.ax1.grid(True)
        legendCols = min(4, self._dlg.table.columnCount())
        fontSize = 'x-small' if legendCols > 4 else 'small'
        self.ax1.legend(bbox_to_anchor=(1.0, -0.15), ncol=legendCols, fontsize=fontSize)
        self.addmpl(fig)
    
    def closeFun(self):
        """Close dialog."""
        self._dlg.close()
        
    def writeStats(self):
        """Write Pearson and Nash coefficients."""
        numCols = self._dlg.table.columnCount()
        numRows = self._dlg.table.rowCount()
        self._dlg.coeffs.clear()
        for i in range(1, numCols):
            for j in range(i+1, numCols):
                self.pearson(i, j, numRows)
        for i in range(1, numCols):
            for j in range(i+1, numCols):
                # only compute Nash-Sutcliffe Efficiency
                # if one plot is observed,
                # and use that as the first plot
                if str(self._dlg.table.horizontalHeaderItem(i).text()).find('observed') == 0:
                    if not str(self._dlg.table.horizontalHeaderItem(j).text()).find('observed') == 0:
                        self.nash(i, j, numRows)
                elif str(self._dlg.table.horizontalHeaderItem(j).text()).find('observed') == 0:
                    self.nash(j, i, numRows)
        
    def multiSums(self, idx1, idx2, N):
        """Return various sums for two series, only including points where both are numbers, plus count of such values."""
        s1 = 0
        s2 = 0
        s11 = 0
        s22 = 0
        s12 = 0
        count = 0
        for i in range(N):
            val1 = self.makeFloat(self._dlg.table.item(i, idx1).text())
            val2 = self.makeFloat(self._dlg.table.item(i, idx2).text())
            # ignore missing values
            if not (math.isnan(val1) or math.isnan(val2)):
                s1 += val1
                s2 += val2
                s11 += val1 * val1
                s22 += val2 * val2
                s12 += val1 * val2
                count = count + 1
        return (s1, s2, s11, s22, s12, count)
        
        
    def sum1(self, idx1, idx2, N):
        """Return sum for series1, only including points where both are numbers, plus count of such values.""" 
        s1 = 0
        count = 0
        for i in range(N):
            val1 = self.makeFloat(self._dlg.table.item(i, idx1).text())
            val2 = self.makeFloat(self._dlg.table.item(i, idx2).text())
            # ignore missing values
            if not (math.isnan(val1) or math.isnan(val2)):
                s1 += val1
                count = count + 1
        return (s1, count)
        
    def pearson(self, idx1, idx2, N):
        """Calculate and display Pearson correlation coefficients for each pair of plots."""
        s1, s2, s11, s22, s12, count = self.multiSums(idx1, idx2, N)
        if count == 0: return
        sqx = (count * s11) - (s1 * s1)
        sqy = (count * s22) - (s2 * s2)
        sxy = (count * s12) - (s1 * s2)
        deno = math.sqrt(sqx * sqy)
        if deno == 0: return
        rho = sxy / deno
        if count < N:
            extra = ' (using {0!s} of {1!s} values)'.format(count , N)
        else:
            extra = ''
        msg = 'Series1: ' + self._dlg.table.horizontalHeaderItem(idx1).text() + \
            '  Series2: ' + self._dlg.table.horizontalHeaderItem(idx2).text() + '  Pearson Correlation Coefficient = {0}{1}'.format(locale.format_string('%.2F', rho), extra)
        self._dlg.coeffs.append(SWATGraph.trans(msg))

    def nash(self, idx1, idx2, N):
        """Calculate and display Nash-Sutcliffe efficiency coefficients for each pair of plots where one is observed."""
        s1, count = self.sum1(idx1, idx2, N)
        if count == 0: return
        mean = s1 / count
        num = 0
        deno = 0
        for i in range(N):
            val1 = self.makeFloat(self._dlg.table.item(i, idx1).text())
            val2 = self.makeFloat(self._dlg.table.item(i, idx2).text())
            # ignore missing values
            if not (math.isnan(val1) or math.isnan(val2)):
                diff12 = val1 - val2
                diff1m = val1 - mean
                num += diff12 * diff12
                deno += diff1m * diff1m
        if deno == 0: return
        result = 1 - (num / deno)
        if count < N:
            extra = ' (using {0!s} of {1!s} values)'.format(count , N)
        else:
            extra = ''
        msg = 'Series1: ' + self._dlg.table.horizontalHeaderItem(idx1).text() + \
            '  Series2: ' + self._dlg.table.horizontalHeaderItem(idx2).text() + '   Nash-Sutcliffe Efficiency Coefficient = {0}{1}'.format(locale.format_string('%.2F', result), extra)
        self._dlg.coeffs.append(SWATGraph.trans(msg))
        
    def setUbuntuFont(self):
        """Set Ubuntu font size 10 as default."""
        QFontDatabase.addApplicationFont(":/fonts/Ubuntu-R.ttf")
        ufont = QFont("Ubuntu", 10, 1)
        QApplication.setFont(ufont)

if __name__ == '__main__':
    ## QApplication object needed 
    app = QApplication(sys.argv)
    if len(sys.argv) > 1:
        ## csv file argument
        csvFile = sys.argv[1]
    else:
        csvFile = None
    ## main program
    main = SWATGraph(csvFile)
    main.run()
