# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'G:/Users/Public/QSWATPlus3/QSWATPlus\ui_selectlu.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_SelectluDialog(object):
    def setupUi(self, SelectluDialog):
        SelectluDialog.setObjectName("SelectluDialog")
        SelectluDialog.resize(339, 554)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/plugins/QSWATPlus/swatplus.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        SelectluDialog.setWindowIcon(icon)
        self.gridLayout = QtWidgets.QGridLayout(SelectluDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.listBox = QtWidgets.QListWidget(SelectluDialog)
        self.listBox.setObjectName("listBox")
        self.gridLayout.addWidget(self.listBox, 0, 0, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(SelectluDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 1, 0, 1, 1)

        self.retranslateUi(SelectluDialog)
        self.buttonBox.accepted.connect(SelectluDialog.accept)
        self.buttonBox.rejected.connect(SelectluDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(SelectluDialog)

    def retranslateUi(self, SelectluDialog):
        _translate = QtCore.QCoreApplication.translate
        SelectluDialog.setWindowTitle(_translate("SelectluDialog", "Select sub-landuse"))
        self.listBox.setSortingEnabled(True)

from . import resources_rc
