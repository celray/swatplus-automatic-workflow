# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'G:/Users/Public/QSWATPlus3/QSWATPlus\ui_exporttable.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_exportSQLiteTable(object):
    def setupUi(self, exportSQLiteTable):
        exportSQLiteTable.setObjectName("exportSQLiteTable")
        exportSQLiteTable.resize(383, 284)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/plugins/QSWATPlus/swatplus.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        exportSQLiteTable.setWindowIcon(icon)
        self.label = QtWidgets.QLabel(exportSQLiteTable)
        self.label.setGeometry(QtCore.QRect(30, 20, 331, 81))
        self.label.setWordWrap(True)
        self.label.setObjectName("label")
        self.databaseBox = QtWidgets.QComboBox(exportSQLiteTable)
        self.databaseBox.setGeometry(QtCore.QRect(30, 140, 331, 22))
        self.databaseBox.setObjectName("databaseBox")
        self.label_2 = QtWidgets.QLabel(exportSQLiteTable)
        self.label_2.setGeometry(QtCore.QRect(30, 120, 111, 16))
        self.label_2.setObjectName("label_2")
        self.tableBox = QtWidgets.QComboBox(exportSQLiteTable)
        self.tableBox.setGeometry(QtCore.QRect(30, 200, 331, 22))
        self.tableBox.setObjectName("tableBox")
        self.label_3 = QtWidgets.QLabel(exportSQLiteTable)
        self.label_3.setGeometry(QtCore.QRect(30, 180, 111, 16))
        self.label_3.setObjectName("label_3")
        self.exportButton = QtWidgets.QPushButton(exportSQLiteTable)
        self.exportButton.setGeometry(QtCore.QRect(190, 240, 75, 23))
        self.exportButton.setObjectName("exportButton")
        self.closeButton = QtWidgets.QPushButton(exportSQLiteTable)
        self.closeButton.setGeometry(QtCore.QRect(290, 240, 75, 23))
        self.closeButton.setObjectName("closeButton")

        self.retranslateUi(exportSQLiteTable)
        QtCore.QMetaObject.connectSlotsByName(exportSQLiteTable)

    def retranslateUi(self, exportSQLiteTable):
        _translate = QtCore.QCoreApplication.translate
        exportSQLiteTable.setWindowTitle(_translate("exportSQLiteTable", "Export sqlite table to csv"))
        self.label.setText(_translate("exportSQLiteTable", "<html><head/><body><p>This form is intended to support the export of tables from the project or reference database to csv files that can be used in other projects, such as landuse and soil lookup tables, or plant and soil data tables. But any SQLite database can be selected, and any table exported.</p></body></html>"))
        self.label_2.setText(_translate("exportSQLiteTable", "Select database"))
        self.label_3.setText(_translate("exportSQLiteTable", "Select table"))
        self.exportButton.setText(_translate("exportSQLiteTable", "Export"))
        self.closeButton.setText(_translate("exportSQLiteTable", "Close"))

from . import resources_rc
