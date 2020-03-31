# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QSWATPlus
                                 A QGIS plugin
 Create SWATPlus inputs
                             -------------------
        begin                : 2014-07-18
        copyright            : (C) 2014 by Chris George
        email                : cgeorge@mcmaster.ca
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
# this is the version for use with stand-alone QSWATGraph
# it imports ui_graph.py, obtained with pyuic from ui_graph.ui
# (see Makefile comment)

#import os

#from PyQt5 import uic
from PyQt5 import QtWidgets

from ui_graph import Ui_GraphDlg  # @UnresolvedImport

class GraphDialog(QtWidgets.QDialog, Ui_GraphDlg):
    """Set up dialog from designer."""
    def __init__(self, parent=None):
        """Constructor."""
# pdir = os.path.dirname(__file__)
# FORM_CLASS, _ = uic.loadUiType(os.path.join(pdir, 'ui_graph.ui'), 
#                                from_imports=True, 
#                                import_from=os.path.basename(pdir))
# 
# class GraphDialog(QtWidgets.QDialog, FORM_CLASS):
#     """Set up dialog from designer."""
#     def __init__(self, parent=None):
#         """Constructor."""
        super(GraphDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)