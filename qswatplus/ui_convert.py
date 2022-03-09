# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'G:/Users/Public/QSWATPlus3/QSWATPlus/ui_convert.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_arcConvertChoice(object):
    def setupUi(self, arcConvertChoice):
        arcConvertChoice.setObjectName("arcConvertChoice")
        arcConvertChoice.setWindowModality(QtCore.Qt.ApplicationModal)
        arcConvertChoice.resize(463, 295)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/plugins/QSWATPlus/swatplus.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        arcConvertChoice.setWindowIcon(icon)
        self.gridLayout = QtWidgets.QGridLayout(arcConvertChoice)
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtWidgets.QLabel(arcConvertChoice)
        self.label.setWordWrap(True)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 3)
        self.fullButton = QtWidgets.QRadioButton(arcConvertChoice)
        self.fullButton.setChecked(True)
        self.fullButton.setObjectName("fullButton")
        self.gridLayout.addWidget(self.fullButton, 1, 0, 1, 1)
        self.existingButton = QtWidgets.QRadioButton(arcConvertChoice)
        self.existingButton.setObjectName("existingButton")
        self.gridLayout.addWidget(self.existingButton, 1, 1, 1, 1)
        self.noGISButton = QtWidgets.QRadioButton(arcConvertChoice)
        self.noGISButton.setObjectName("noGISButton")
        self.gridLayout.addWidget(self.noGISButton, 1, 2, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(arcConvertChoice)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 2, 1, 1, 2)

        self.retranslateUi(arcConvertChoice)
        self.buttonBox.accepted.connect(arcConvertChoice.accept)
        self.buttonBox.rejected.connect(arcConvertChoice.reject)
        QtCore.QMetaObject.connectSlotsByName(arcConvertChoice)

    def retranslateUi(self, arcConvertChoice):
        _translate = QtCore.QCoreApplication.translate
        arcConvertChoice.setWindowTitle(_translate("arcConvertChoice", "Convert to QSWAT+ choice"))
        self.label.setText(_translate("arcConvertChoice", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">There are three options available for converting an ArcSWAT project to QSWAT+.</p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Choose <span style=\" font-weight:600;\">Full </span>if you want to create a QSWAT+ project from scratch using your DEM, landuse and soil maps, and other data, starting with watershed delineation. You will be able to set stream and channel thresholds, define landscape units, a floodplain, and HRUs, as well as edit your inputs before running SWAT+.</p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Choose<span style=\" font-weight:600;\"> Existing </span>if you want to keep your existing watershed and subbasin boundaries and move straight to overlaying your landuse and soil maps and defining your HRUs. This avoids the risk that watershed delineation using QGIS and TauDEM will differ from watershed delineation using ArcGIS. You will not be able to define landscape units. You will be able to define a floodplain and HRUs, and edit your inputs before running SWAT+.</p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Choose <span style=\" font-weight:600;\">No GIS</span> if you want to run SWAT+ using your existing SWAT inputs. You will not be using GIS, will not be able to change your watershed, subbasins or HRUs, nor be able to create landscape units or a floodplain. You will be able to edit your inputs before running SWAT+.</p></body></html>"))
        self.fullButton.setText(_translate("arcConvertChoice", "Full"))
        self.existingButton.setText(_translate("arcConvertChoice", "Existing"))
        self.noGISButton.setText(_translate("arcConvertChoice", "No GIS"))

import resources_rc
