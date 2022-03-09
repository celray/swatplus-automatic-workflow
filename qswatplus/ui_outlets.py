# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'G:/Users/Public/QSWATPlus3/QSWATPlus\ui_outlets.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_OutletsDialog(object):
    def setupUi(self, OutletsDialog):
        OutletsDialog.setObjectName("OutletsDialog")
        OutletsDialog.resize(243, 293)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/plugins/QSWATPlus/swatplus.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        OutletsDialog.setWindowIcon(icon)
        self.gridLayout_2 = QtWidgets.QGridLayout(OutletsDialog)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.label = QtWidgets.QLabel(OutletsDialog)
        self.label.setWordWrap(True)
        self.label.setObjectName("label")
        self.gridLayout_2.addWidget(self.label, 0, 0, 1, 1)
        self.widget = QtWidgets.QWidget(OutletsDialog)
        self.widget.setObjectName("widget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.widget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.outletButton = QtWidgets.QRadioButton(self.widget)
        self.outletButton.setChecked(True)
        self.outletButton.setAutoExclusive(True)
        self.outletButton.setObjectName("outletButton")
        self.verticalLayout.addWidget(self.outletButton)
        self.reservoirButton = QtWidgets.QRadioButton(self.widget)
        self.reservoirButton.setObjectName("reservoirButton")
        self.verticalLayout.addWidget(self.reservoirButton)
        self.pondButton = QtWidgets.QRadioButton(self.widget)
        self.pondButton.setObjectName("pondButton")
        self.verticalLayout.addWidget(self.pondButton)
        self.inletButton = QtWidgets.QRadioButton(self.widget)
        self.inletButton.setObjectName("inletButton")
        self.verticalLayout.addWidget(self.inletButton)
        self.ptsourceButton = QtWidgets.QRadioButton(self.widget)
        self.ptsourceButton.setObjectName("ptsourceButton")
        self.verticalLayout.addWidget(self.ptsourceButton)
        self.gridLayout_2.addWidget(self.widget, 1, 0, 1, 1)
        self.widget_2 = QtWidgets.QWidget(OutletsDialog)
        self.widget_2.setObjectName("widget_2")
        self.gridLayout = QtWidgets.QGridLayout(self.widget_2)
        self.gridLayout.setObjectName("gridLayout")
        self.resumeButton = QtWidgets.QPushButton(self.widget_2)
        self.resumeButton.setObjectName("resumeButton")
        self.gridLayout.addWidget(self.resumeButton, 0, 0, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(113, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 0, 1, 1, 1)
        self.gridLayout_2.addWidget(self.widget_2, 2, 0, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(OutletsDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout_2.addWidget(self.buttonBox, 3, 0, 1, 1)

        self.retranslateUi(OutletsDialog)
        self.buttonBox.accepted.connect(OutletsDialog.accept)
        self.buttonBox.rejected.connect(OutletsDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(OutletsDialog)

    def retranslateUi(self, OutletsDialog):
        _translate = QtCore.QCoreApplication.translate
        OutletsDialog.setWindowTitle(_translate("OutletsDialog", "Inlets/outlets"))
        self.label.setText(_translate("OutletsDialog", "Select type of point to add, then click on map to place it.  If you return to the map canvas to pan, zoom, etc click Resume adding to enable adding more points. Click OK to confirm and exit, Cancel to remove points and exit."))
        self.outletButton.setText(_translate("OutletsDialog", "Outlet"))
        self.reservoirButton.setText(_translate("OutletsDialog", "Reservoir"))
        self.pondButton.setText(_translate("OutletsDialog", "Pond"))
        self.inletButton.setText(_translate("OutletsDialog", "Inlet"))
        self.ptsourceButton.setText(_translate("OutletsDialog", "Point source"))
        self.resumeButton.setText(_translate("OutletsDialog", "Resume adding"))

from . import resources_rc
