# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'G:/Users/Public/QSWATPlus3/QSWATPlus\ui_exempt.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_ExemptDialog(object):
    def setupUi(self, ExemptDialog):
        ExemptDialog.setObjectName("ExemptDialog")
        ExemptDialog.resize(277, 222)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/plugins/QSWATPlus/swatplus.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        ExemptDialog.setWindowIcon(icon)
        self.buttonBox = QtWidgets.QDialogButtonBox(ExemptDialog)
        self.buttonBox.setGeometry(QtCore.QRect(-80, 180, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.groupBox = QtWidgets.QGroupBox(ExemptDialog)
        self.groupBox.setGeometry(QtCore.QRect(10, 10, 261, 161))
        self.groupBox.setObjectName("groupBox")
        self.exemptBox = QtWidgets.QListWidget(self.groupBox)
        self.exemptBox.setGeometry(QtCore.QRect(150, 60, 91, 91))
        self.exemptBox.setObjectName("exemptBox")
        self.cancelExemptionButton = QtWidgets.QPushButton(self.groupBox)
        self.cancelExemptionButton.setGeometry(QtCore.QRect(20, 110, 81, 41))
        self.cancelExemptionButton.setObjectName("cancelExemptionButton")
        self.label_2 = QtWidgets.QLabel(self.groupBox)
        self.label_2.setGeometry(QtCore.QRect(10, 40, 96, 31))
        self.label_2.setInputMethodHints(QtCore.Qt.ImhNone)
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(self.groupBox)
        self.label_3.setGeometry(QtCore.QRect(130, 30, 121, 21))
        self.label_3.setAlignment(QtCore.Qt.AlignCenter)
        self.label_3.setObjectName("label_3")
        self.chooseBox = QtWidgets.QComboBox(self.groupBox)
        self.chooseBox.setGeometry(QtCore.QRect(20, 80, 69, 22))
        self.chooseBox.setInsertPolicy(QtWidgets.QComboBox.InsertAlphabetically)
        self.chooseBox.setObjectName("chooseBox")
        self.groupBox.raise_()
        self.buttonBox.raise_()

        self.retranslateUi(ExemptDialog)
        self.buttonBox.accepted.connect(ExemptDialog.accept)
        self.buttonBox.rejected.connect(ExemptDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(ExemptDialog)

    def retranslateUi(self, ExemptDialog):
        _translate = QtCore.QCoreApplication.translate
        ExemptDialog.setWindowTitle(_translate("ExemptDialog", "Exempt Landuses"))
        self.buttonBox.setToolTip(_translate("ExemptDialog", "Save exemptions (OK) or leave exemptions the same as when this form was opened (Cancel)."))
        self.groupBox.setTitle(_translate("ExemptDialog", "Landuse threshold exemptions"))
        self.cancelExemptionButton.setToolTip(_translate("ExemptDialog", "Remove the selected landuse from the list of exempt landuses."))
        self.cancelExemptionButton.setText(_translate("ExemptDialog", "Cancel\n"
"exemption"))
        self.label_2.setText(_translate("ExemptDialog", "Select landuse\n"
"to be exempt"))
        self.label_3.setText(_translate("ExemptDialog", "Exempt landuses"))

from . import resources_rc
