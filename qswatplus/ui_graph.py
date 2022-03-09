# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'G:/Users/Public/QSWATPlus3/QSWATPlus\ui_graph.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_GraphDlg(object):
    def setupUi(self, GraphDlg):
        GraphDlg.setObjectName("GraphDlg")
        GraphDlg.resize(1153, 590)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/plugins/QSWATPlus/SWATPlus32.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        GraphDlg.setWindowIcon(icon)
        GraphDlg.setSizeGripEnabled(True)
        self.gridLayout = QtWidgets.QGridLayout(GraphDlg)
        self.gridLayout.setObjectName("gridLayout")
        self.table = QtWidgets.QTableWidget(GraphDlg)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.table.sizePolicy().hasHeightForWidth())
        self.table.setSizePolicy(sizePolicy)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setObjectName("table")
        self.table.setColumnCount(0)
        self.table.setRowCount(0)
        self.table.verticalHeader().setVisible(False)
        self.gridLayout.addWidget(self.table, 3, 1, 1, 1)
        self.widget = QtWidgets.QWidget(GraphDlg)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy)
        self.widget.setMinimumSize(QtCore.QSize(201, 251))
        self.widget.setFocusPolicy(QtCore.Qt.WheelFocus)
        self.widget.setObjectName("widget")
        self.newFile = QtWidgets.QPushButton(self.widget)
        self.newFile.setGeometry(QtCore.QRect(21, 90, 81, 41))
        self.newFile.setObjectName("newFile")
        self.closeForm = QtWidgets.QPushButton(self.widget)
        self.closeForm.setGeometry(QtCore.QRect(120, 110, 75, 23))
        self.closeForm.setObjectName("closeForm")
        self.lineOrBar = QtWidgets.QComboBox(self.widget)
        self.lineOrBar.setGeometry(QtCore.QRect(20, 50, 90, 20))
        self.lineOrBar.setMinimumSize(QtCore.QSize(90, 0))
        self.lineOrBar.setMaxVisibleItems(2)
        self.lineOrBar.setObjectName("lineOrBar")
        self.label = QtWidgets.QLabel(self.widget)
        self.label.setGeometry(QtCore.QRect(20, 30, 82, 16))
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.updateButton = QtWidgets.QPushButton(self.widget)
        self.updateButton.setGeometry(QtCore.QRect(120, 50, 75, 23))
        self.updateButton.setObjectName("updateButton")
        self.gridLayout.addWidget(self.widget, 3, 2, 2, 1)
        self.coeffs = QtWidgets.QTextBrowser(GraphDlg)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.coeffs.sizePolicy().hasHeightForWidth())
        self.coeffs.setSizePolicy(sizePolicy)
        self.coeffs.setObjectName("coeffs")
        self.gridLayout.addWidget(self.coeffs, 4, 1, 1, 1)
        self.graph = QtWidgets.QWidget(GraphDlg)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.graph.sizePolicy().hasHeightForWidth())
        self.graph.setSizePolicy(sizePolicy)
        self.graph.setObjectName("graph")
        self.graphvl = QtWidgets.QVBoxLayout(self.graph)
        self.graphvl.setObjectName("graphvl")
        self.gridLayout.addWidget(self.graph, 2, 1, 1, 2)

        self.retranslateUi(GraphDlg)
        QtCore.QMetaObject.connectSlotsByName(GraphDlg)

    def retranslateUi(self, GraphDlg):
        _translate = QtCore.QCoreApplication.translate
        GraphDlg.setWindowTitle(_translate("GraphDlg", "SWATGraph"))
        self.newFile.setText(_translate("GraphDlg", "New File\n"
"to Plot"))
        self.closeForm.setText(_translate("GraphDlg", "Close"))
        self.label.setText(_translate("GraphDlg", "Chart Type"))
        self.updateButton.setText(_translate("GraphDlg", "Update"))

from . import resources_rc
