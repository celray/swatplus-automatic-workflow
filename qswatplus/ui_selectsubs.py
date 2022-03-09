# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'G:/Users/Public/QSWATPlus3/QSWATPlus\ui_selectsubs.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_SelectSubbasinsDialog(object):
    def setupUi(self, SelectSubbasinsDialog):
        SelectSubbasinsDialog.setObjectName("SelectSubbasinsDialog")
        SelectSubbasinsDialog.resize(370, 415)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/plugins/QSWATPlus/swatplus.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        SelectSubbasinsDialog.setWindowIcon(icon)
        SelectSubbasinsDialog.setSizeGripEnabled(False)
        self.gridLayout = QtWidgets.QGridLayout(SelectSubbasinsDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.label_2 = QtWidgets.QLabel(SelectSubbasinsDialog)
        self.label_2.setTextFormat(QtCore.Qt.AutoText)
        self.label_2.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.label_2.setWordWrap(False)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 3)
        self.checkBox = QtWidgets.QCheckBox(SelectSubbasinsDialog)
        self.checkBox.setObjectName("checkBox")
        self.gridLayout.addWidget(self.checkBox, 1, 0, 1, 1)
        self.groupBox = QtWidgets.QGroupBox(SelectSubbasinsDialog)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.label = QtWidgets.QLabel(self.groupBox)
        self.label.setWordWrap(False)
        self.label.setObjectName("label")
        self.gridLayout_2.addWidget(self.label, 0, 0, 1, 3)
        self.areaButton = QtWidgets.QRadioButton(self.groupBox)
        self.areaButton.setObjectName("areaButton")
        self.gridLayout_2.addWidget(self.areaButton, 1, 0, 1, 1)
        self.threshold = QtWidgets.QLineEdit(self.groupBox)
        self.threshold.setInputMethodHints(QtCore.Qt.ImhFormattedNumbersOnly)
        self.threshold.setObjectName("threshold")
        self.gridLayout_2.addWidget(self.threshold, 1, 1, 2, 1)
        self.pushButton = QtWidgets.QPushButton(self.groupBox)
        self.pushButton.setObjectName("pushButton")
        self.gridLayout_2.addWidget(self.pushButton, 1, 2, 2, 1)
        self.percentButton = QtWidgets.QRadioButton(self.groupBox)
        self.percentButton.setObjectName("percentButton")
        self.gridLayout_2.addWidget(self.percentButton, 2, 0, 1, 1)
        self.gridLayout.addWidget(self.groupBox, 2, 0, 1, 3)
        self.count = QtWidgets.QLabel(SelectSubbasinsDialog)
        self.count.setObjectName("count")
        self.gridLayout.addWidget(self.count, 3, 0, 1, 1)
        self.saveButton = QtWidgets.QPushButton(SelectSubbasinsDialog)
        self.saveButton.setObjectName("saveButton")
        self.gridLayout.addWidget(self.saveButton, 3, 1, 1, 1)
        self.cancelButton = QtWidgets.QPushButton(SelectSubbasinsDialog)
        self.cancelButton.setObjectName("cancelButton")
        self.gridLayout.addWidget(self.cancelButton, 3, 2, 1, 1)

        self.retranslateUi(SelectSubbasinsDialog)
        QtCore.QMetaObject.connectSlotsByName(SelectSubbasinsDialog)

    def retranslateUi(self, SelectSubbasinsDialog):
        _translate = QtCore.QCoreApplication.translate
        SelectSubbasinsDialog.setWindowTitle(_translate("SelectSubbasinsDialog", "Select subbasins for merging"))
        self.label_2.setText(_translate("SelectSubbasinsDialog", "Hold Ctrl and click in the subbasins you want to select. Selected \n"
"subbasins will turn yellow, and a count is shown at the bottom left \n"
"of this window.  If you want to start again release Ctrl and \n"
"click outside the watershed; then hold Ctrl and resume selection. \n"
"\n"
"You can pause in the selection to pan or zoom provided you hold \n"
"Ctrl again when you resume selection.\n"
"\n"
"Small subbasins selected by threshold (below) will be additional to \n"
"those selected by clicking.\n"
"\n"
"When finished click \"Save\" to save your selection, \n"
"or \"Cancel\" to abandon the selection."))
        self.checkBox.setText(_translate("SelectSubbasinsDialog", "Select small subbasins"))
        self.groupBox.setTitle(_translate("SelectSubbasinsDialog", "Select by threshold"))
        self.label.setText(_translate("SelectSubbasinsDialog", "Set a threshold for small subbasins, either as an area in hectares \n"
"or as a percentage of the mean subbasin area.   Click the Select \n"
"button to select subbasins below the threshold."))
        self.areaButton.setText(_translate("SelectSubbasinsDialog", "Area (ha)"))
        self.threshold.setToolTip(_translate("SelectSubbasinsDialog", "The maximum distance a point may be moved to place it on the stream network (snapped).  Points which would require more than this distance will not be used."))
        self.pushButton.setText(_translate("SelectSubbasinsDialog", "Select"))
        self.percentButton.setText(_translate("SelectSubbasinsDialog", "Percentage of mean area"))
        self.count.setText(_translate("SelectSubbasinsDialog", "0 selected"))
        self.saveButton.setText(_translate("SelectSubbasinsDialog", "Save"))
        self.cancelButton.setText(_translate("SelectSubbasinsDialog", "Cancel"))

from . import resources_rc
