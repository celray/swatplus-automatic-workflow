# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'G:/Users/Public/QSWATPlus3/QSWATPlus\ui_elevationbands.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_ElevatioBandsDialog(object):
    def setupUi(self, ElevatioBandsDialog):
        ElevatioBandsDialog.setObjectName("ElevatioBandsDialog")
        ElevatioBandsDialog.resize(215, 185)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/plugins/QSWATPlus/swatplus.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        ElevatioBandsDialog.setWindowIcon(icon)
        self.groupBox = QtWidgets.QGroupBox(ElevatioBandsDialog)
        self.groupBox.setGeometry(QtCore.QRect(10, 10, 191, 131))
        self.groupBox.setObjectName("groupBox")
        self.elevBandsThreshold = QtWidgets.QLineEdit(self.groupBox)
        self.elevBandsThreshold.setGeometry(QtCore.QRect(50, 50, 61, 20))
        self.elevBandsThreshold.setInputMethodHints(QtCore.Qt.ImhPreferNumbers)
        self.elevBandsThreshold.setObjectName("elevBandsThreshold")
        self.numElevBands = QtWidgets.QSpinBox(self.groupBox)
        self.numElevBands.setGeometry(QtCore.QRect(60, 100, 42, 22))
        self.numElevBands.setMinimum(2)
        self.numElevBands.setMaximum(10)
        self.numElevBands.setObjectName("numElevBands")
        self.label_2 = QtWidgets.QLabel(self.groupBox)
        self.label_2.setGeometry(QtCore.QRect(10, 80, 171, 20))
        self.label_2.setObjectName("label_2")
        self.label = QtWidgets.QLabel(self.groupBox)
        self.label.setGeometry(QtCore.QRect(0, 30, 201, 16))
        self.label.setObjectName("label")
        self.cancelButton = QtWidgets.QPushButton(ElevatioBandsDialog)
        self.cancelButton.setGeometry(QtCore.QRect(110, 150, 75, 23))
        self.cancelButton.setObjectName("cancelButton")
        self.okButton = QtWidgets.QPushButton(ElevatioBandsDialog)
        self.okButton.setGeometry(QtCore.QRect(20, 150, 75, 23))
        self.okButton.setObjectName("okButton")

        self.retranslateUi(ElevatioBandsDialog)
        QtCore.QMetaObject.connectSlotsByName(ElevatioBandsDialog)

    def retranslateUi(self, ElevatioBandsDialog):
        _translate = QtCore.QCoreApplication.translate
        ElevatioBandsDialog.setWindowTitle(_translate("ElevatioBandsDialog", "Elevation Bands"))
        self.groupBox.setTitle(_translate("ElevatioBandsDialog", "Elevation bands settings"))
        self.elevBandsThreshold.setToolTip(_translate("ElevatioBandsDialog", "Elevation bands will be provided for subbasins whose maximum height exceeds this threshold."))
        self.label_2.setText(_translate("ElevatioBandsDialog", "Number of bands (2 - 10)"))
        self.label.setText(_translate("ElevatioBandsDialog", "Threshold elevation (metres)"))
        self.cancelButton.setText(_translate("ElevatioBandsDialog", "Cancel"))
        self.okButton.setText(_translate("ElevatioBandsDialog", "OK"))

from . import resources_rc
