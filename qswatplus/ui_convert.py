# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Users\Chirs George\workspace\QSWATPlus3\QSWATPlus\ui_convert.ui'
#
# Created by: PyQt5 UI code generator 5.9
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_arcConvertChoice(object):
    def setupUi(self, arcConvertChoice):
        arcConvertChoice.setObjectName("arcConvertChoice")
        arcConvertChoice.setWindowModality(QtCore.Qt.ApplicationModal)
        arcConvertChoice.resize(545, 303)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/plugins/QSWATPlus/SWATPlus32.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        arcConvertChoice.setWindowIcon(icon)
        self.buttonBox = QtWidgets.QDialogButtonBox(arcConvertChoice)
        self.buttonBox.setGeometry(QtCore.QRect(190, 260, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.label = QtWidgets.QLabel(arcConvertChoice)
        self.label.setGeometry(QtCore.QRect(20, 10, 511, 201))
        self.label.setWordWrap(True)
        self.label.setObjectName("label")
        self.noGISButton = QtWidgets.QRadioButton(arcConvertChoice)
        self.noGISButton.setGeometry(QtCore.QRect(320, 230, 82, 17))
        self.noGISButton.setObjectName("noGISButton")
        self.existingButton = QtWidgets.QRadioButton(arcConvertChoice)
        self.existingButton.setGeometry(QtCore.QRect(190, 230, 82, 17))
        self.existingButton.setObjectName("existingButton")
        self.fullButton = QtWidgets.QRadioButton(arcConvertChoice)
        self.fullButton.setGeometry(QtCore.QRect(60, 230, 82, 17))
        self.fullButton.setChecked(True)
        self.fullButton.setObjectName("fullButton")

        self.retranslateUi(arcConvertChoice)
        self.buttonBox.accepted.connect(arcConvertChoice.accept)
        self.buttonBox.rejected.connect(arcConvertChoice.reject)
        QtCore.QMetaObject.connectSlotsByName(arcConvertChoice)

    def retranslateUi(self, arcConvertChoice):
        _translate = QtCore.QCoreApplication.translate
        arcConvertChoice.setWindowTitle(_translate("arcConvertChoice", "Convert to QSWAT+ choice"))
        self.label.setText(_translate("arcConvertChoice", "<html><head/><body><p>There are three options available for converting an ArcSWAT project to QSWAT+.</p><p>Choose <span style=\" font-weight:600;\">Full </span>if you want to create a QSWAT+ project from scratch using your DEM, landuse and soil maps, and other data, starting with watershed delineation. You will be able to set thresholds, define landscape units, a floodplain, and HRUs, as well as edit your inputs before running SWAT+.</p><p>Choose<span style=\" font-weight:600;\"> Existing </span>if you want to keep your existing watershed and subbasin boundaries and move straight to overlaying your landuse and soil maps and defining your HRUs. This avoids the risk that watershed delineation using QGIS and TauDEM will differ from watershed delineation using ArcGIS.  You will not be able to define landscape units. You will be able to define a floodplain and HRUs, and edit your inputs before running SWAT+.</p><p>Choose <span style=\" font-weight:600;\">No GIS</span> if you want to run SWAT+ using your existing SWAT inputs. You will not be using GIS, will not be able to change your watershed, subbasins or HRUs, nor be able to create landscape units or a floodplain. You will be able to edit your inputs before running SWAT+.</p></body></html>"))
        self.noGISButton.setText(_translate("arcConvertChoice", "No GIS"))
        self.existingButton.setText(_translate("arcConvertChoice", "Existing"))
        self.fullButton.setText(_translate("arcConvertChoice", "Full"))

import resources_rc  # @UnresolvedImport
