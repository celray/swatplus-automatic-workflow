# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'G:/Users/Public/QSWATPlus3/QSWATPlus\ui_about.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_aboutQSWAT(object):
    def setupUi(self, aboutQSWAT):
        aboutQSWAT.setObjectName("aboutQSWAT")
        aboutQSWAT.resize(245, 251)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/plugins/QSWATPlus/swatplus.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        aboutQSWAT.setWindowIcon(icon)
        aboutQSWAT.setSizeGripEnabled(False)
        self.gridLayout_2 = QtWidgets.QGridLayout(aboutQSWAT)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 3, 3)
        self.textBrowser = QtWidgets.QTextBrowser(aboutQSWAT)
        self.textBrowser.setObjectName("textBrowser")
        self.gridLayout_2.addWidget(self.textBrowser, 1, 1, 1, 2)
        self.SWATHomeButton = QtWidgets.QPushButton(aboutQSWAT)
        self.SWATHomeButton.setObjectName("SWATHomeButton")
        self.gridLayout_2.addWidget(self.SWATHomeButton, 2, 1, 1, 1)
        self.closeButton = QtWidgets.QPushButton(aboutQSWAT)
        self.closeButton.setObjectName("closeButton")
        self.gridLayout_2.addWidget(self.closeButton, 2, 2, 1, 1)

        self.retranslateUi(aboutQSWAT)
        QtCore.QMetaObject.connectSlotsByName(aboutQSWAT)

    def retranslateUi(self, aboutQSWAT):
        _translate = QtCore.QCoreApplication.translate
        aboutQSWAT.setWindowTitle(_translate("aboutQSWAT", "About QSWAT+"))
        self.SWATHomeButton.setText(_translate("aboutQSWAT", "SWAT home page"))
        self.closeButton.setText(_translate("aboutQSWAT", "Close"))

from . import resources_rc
