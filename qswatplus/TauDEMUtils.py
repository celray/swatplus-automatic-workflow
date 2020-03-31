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
# Import the PyQt and QGIS libraries
from PyQt5.QtCore import * # @UnusedWildImport
from PyQt5.QtGui import * # @UnusedWildImport
from qgis.core import * # @UnusedWildImport
import os.path
import subprocess
import webbrowser

from .QSWATUtils import QSWATUtils
from .parameters import Parameters

class TauDEMUtils:
    
    """Methods for calling TauDEM executables."""
    
    @staticmethod
    def runPitFill(demFile, felFile, numProcesses, output):
        """Run PitFill."""
        return TauDEMUtils.run('pitremove', [('-z', demFile)], [], [('-fel', felFile)], numProcesses, output, False)

    @staticmethod
    def runD8FlowDir(felFile, sd8File, pFile, numProcesses, output):
        """Run D8FlowDir."""
        return TauDEMUtils.run('d8flowdir', [('-fel', felFile)], [], [('-sd8', sd8File), ('-p', pFile)], numProcesses, output, False)

    @staticmethod
    def runDinfFlowDir(felFile, slpFile, angFile, numProcesses, output):
        """Run DinfFlowDir."""
        return TauDEMUtils.run('dinfflowdir', [('-fel', felFile)], [], [('-slp', slpFile), ('-ang', angFile)], numProcesses, output, False)

    @staticmethod
    def runAreaD8(pFile, ad8File, outletFile, weightFile, numProcesses, output, contCheck=False, mustRun=True):
        """Run AreaD8."""
        inFiles = [('-p', pFile)]
        if outletFile is not None:
            inFiles.append(('-o', outletFile))
        if weightFile is not None:
            inFiles.append(('-wg', weightFile))
        check = [] if contCheck else [('-nc', '')]
        return TauDEMUtils.run('aread8', inFiles, check, [('-ad8', ad8File) ], numProcesses, output, mustRun)

    @staticmethod
    def runAreaDinf(angFile, scaFile, outletFile, numProcesses, output, mustRun=True):
        """Run AreaDinf."""
        inFiles = [('-ang', angFile)]
        if outletFile is not None:
            inFiles.append(('-o', outletFile))
        return TauDEMUtils.run('areadinf', inFiles, [('-nc', '')], [('-sca', scaFile)], numProcesses, output, mustRun)

    @staticmethod
    def runGridNet(pFile, plenFile, tlenFile, gordFile, outletFile, numProcesses, output, mustRun=True):
        """Run GridNet."""
        inFiles = [('-p', pFile)]
        if outletFile is not None:
            inFiles.append(('-o', outletFile))
        return TauDEMUtils.run('gridnet', inFiles, [], [('-plen', plenFile), ('-tlen', tlenFile), ('-gord', gordFile)], numProcesses, output, mustRun)
    
    @staticmethod
    def runThreshold(ad8File, srcFile, threshold, numProcesses, output, mustRun=True):
        """Run Threshold."""
        return TauDEMUtils.run('threshold', [('-ssa', ad8File)], [('-thresh', threshold)], [('-src', srcFile)], numProcesses, output, mustRun)
    
    @staticmethod
    def runStreamNet(felFile, pFile, ad8File, srcFile, outletFile, ordFile, treeFile, coordFile, streamFile, wFile, single, numProcesses, output, mustRun=True):
        """Run StreamNet."""
        inFiles = [('-fel', felFile), ('-p', pFile), ('-ad8', ad8File), ('-src', srcFile)]
        if outletFile is not None:
            inFiles.append(('-o', outletFile))
        inParms = [('-sw', '')] if single else []
        return TauDEMUtils.run('streamnet', inFiles, inParms, 
                               [('-ord', ordFile), ('-tree', treeFile), ('-coord', coordFile), ('-net', streamFile), ('-w', wFile)], 
                               numProcesses, output, mustRun)
    @staticmethod
    def runMoveOutlets(pFile, srcFile, outletFile, movedOutletFile, numProcesses, output, mustRun=True):
        """Run MoveOutlets."""
        return TauDEMUtils.run('moveoutletstostreams', [('-p', pFile), ('-src', srcFile), ('-o', outletFile)], [], [('-om', movedOutletFile)], 
                               numProcesses, output, mustRun)
        
    @staticmethod
    def runDistanceToStreams(pFile, hd8File, distFile, threshold, numProcesses, output, mustRun=True):
        """Run D8HDistToStrm."""
        return TauDEMUtils.run('d8hdisttostrm', [('-p', pFile), ('-src', hd8File)], [('-thresh', threshold)], [('-dist', distFile)], 
                               numProcesses, output, mustRun)
    
    @staticmethod   
    def run(command, inFiles, inParms, outFiles, numProcesses, output, mustRun):
        """
        Run TauDEM command, using mpiexec if numProcesses is not zero.
        
        Parameters:
        inFiles: list of pairs of parameter id (string) and file path (string) 
        for input files.  May not be empty.
        inParms: list of pairs of parameter id (string) and parameter value 
        (string) for input parameters.
        For a parameter which is a flag with no value, parameter value 
        should be empty string.
        outFiles: list of pairs of parameter id (string) and file path 
        (string) for output files.
        numProcesses: number of processes to use (int).  
        Zero means do not use mpiexec.
        output: buffer for TauDEM output (QTextEdit).
        if output is None use as flag that running in batch, and errors are simply printed.
        Return: True if no error detected, else false.
        The command is not executed if 
        (1) mustRun is false (since it is set true for results that depend 
        on the threshold setting or an outlets file, which might have changed), and
        (2) all output files exist and were last modified no earlier 
        than the first input file.
        An error is detected if any input file does not exist or,
        after running the TauDEM command, 
        any output file does not exist or was last modified earlier 
        than the first input file.
        For successful output files the .prj file is copied 
        from the first input file.
        The Taudem executable directory and the mpiexec path are 
        read from QSettings.
        """
        hasQGIS = output is not None
        baseFile = inFiles[0][1]
        needToRun = mustRun
        if not needToRun:
            for (pid, fileName) in outFiles:
                if not QSWATUtils.isUpToDate(baseFile, fileName):
                    needToRun = True
                    break
        if not needToRun:
            return True
        # remove outFiles so any error will be reported
        root = QgsProject.instance().layerTreeRoot()
        for (pid, fileName) in outFiles:
            QSWATUtils.tryRemoveLayerAndFiles(fileName, root)
        commands = []
        settings = QSettings()
        if hasQGIS:
            output.append('------------------- TauDEM command: -------------------\n')
        if numProcesses != 0:
            mpiexecPath = TauDEMUtils.findMPIExecPath(settings)
            if mpiexecPath != '':
                commands.append(mpiexecPath)
                commands.append('-np') # -n acceptable in Windows but only -np in OpenMPI
                commands.append(str(numProcesses))
        TauDEMDir = TauDEMUtils.findTauDEMDir(settings, hasQGIS)
        if TauDEMDir == '':
            return False
        commands.append(QSWATUtils.join(TauDEMDir, command))
        for (pid, fileName) in inFiles:
            if not os.path.exists(fileName):
                TauDEMUtils.error('''File {0} does not exist.
Have you installed SWAT+ as a different directory from C:\SWAT\SWATPlus?
If so use the QSWAT+ Parameters form to set the correct location.'''.format(fileName), hasQGIS)
                return False
            commands.append(pid)
            commands.append(fileName)
        for (pid, parm) in inParms:
            commands.append(pid)
            # allow for parameter which is flag with no value
            if not parm == '':
                commands.append(parm)
        for (pid, fileName) in outFiles:
            commands.append(pid)
            commands.append(fileName)
        command = ' '.join(commands)             
        if hasQGIS:
            output.append(command + '\n\n')
            output.moveCursor(QTextCursor.End)
        # Windows will accept commands as first argument of run
        # and this has the advantage of dealing with spaces within inidividual components of the list
        # Linux needs a single list (and there will be no spaces to worry about
        procCommand = commands if Parameters._ISWIN else command
        proc = subprocess.run(procCommand, 
                                shell=True, 
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                universal_newlines=True)    # text=True) only in python 3.7     
        if hasQGIS:
            output.append(proc.stdout)
            output.moveCursor(QTextCursor.End)
        else:
            print(proc.stdout)
        # proc.returncode always seems to be None
        # so check TauDEM run by checking output file exists and modified later than DEM
        # not ideal as may eg generate empty file
        # TODO: improve on this
        ok = proc.returncode == 0
        msg = command + ' created '
        for (pid, fileName) in outFiles:
            if QSWATUtils.isUpToDate(baseFile, fileName):
                QSWATUtils.copyPrj(baseFile, fileName)
                msg += fileName
                msg += ' '
            else:
                ok = False
        if ok:
            TauDEMUtils.loginfo(msg, hasQGIS)
        else:
            if hasQGIS:    
                origColour = output.textColor()
                output.setTextColor(Qt.red)
                output.append(QSWATUtils.trans('*** Problem with TauDEM {0}: please examine output above. ***'.format(command)))
                output.setTextColor(origColour)
            msg += 'and failed'
            TauDEMUtils.logerror(msg, hasQGIS)
        return ok

    @staticmethod
    def findTauDEMDir(settings, hasQGIS):
        """Find and return path of TauDEM directory."""
        SWATPlusDir = settings.value('/QSWATPlus/SWATPlusDir', Parameters._SWATPLUSDEFAULTDIR)
        TauDEMDir = QSWATUtils.join(SWATPlusDir, Parameters._TAUDEMDIR)
        if not os.path.isdir(TauDEMDir):
            if Parameters._ISWIN:
                TauDEMDir2 = QSWATUtils.join(r'C:\SWAT\SWATPlus', Parameters._TAUDEMDIR)
                if not os.path.isdir(TauDEMDir2):
                    TauDEMDir2 = QSWATUtils.join(r'C:\SWAT\SWATEditor', Parameters._TAUDEMDIR)  # path from QSWAT
                if os.path.isdir(TauDEMDir2):
                    TauDEMDir = TauDEMDir2
                else:
                    TauDEMUtils.error('''Cannot find TauDEM directory as {0} or {1}.  
Have you installed SWAT+ as a different directory from C:\SWAT\SWATPlus?
If so use the QSWAT+ Parameters form to set the correct location.'''.format(TauDEMDir, TauDEMDir2), hasQGIS)
                    return  ''
            else:
                TauDEMDir2 = QSWATUtils.join('~/.local/share/swatplus', Parameters._TAUDEMDIR)
                if os.path.isdir(TauDEMDir2):
                    TauDEMDir = TauDEMDir2
                else:
                    TauDEMDir3 = QSWATUtils.join('/usr/local/share/swatplus', Parameters._TAUDEMDIR)
                    if os.path.isdir(TauDEMDir3):
                        TauDEMDir = TauDEMDir3
                    else:
                        TauDEMUtils.error('''Cannot find TauDEM directory as {0}, {1} or {2}.  
Have you installed SWATPlus?'''.format(TauDEMDir, TauDEMDir2, TauDEMDir3), hasQGIS)
                    return ''
        return TauDEMDir
    
    @staticmethod
    def findMPIExecPath(settings):
        """Find and return path of MPI execuatable, if any, else None."""
        if settings.contains('/QSWAT/mpiexecDir'):
            path = QSWATUtils.join(settings.value('/QSWAT/mpiexecDir'), Parameters._MPIEXEC)
        else:
            settings.setValue('/QSWAT/mpiexecDir', Parameters._MPIEXECDEFAULTDIR)
            path = QSWATUtils.join(Parameters._MPIEXECDEFAULTDIR, Parameters._MPIEXEC)
        if os.path.exists(path):
            return path
        else:
            return ''

    @staticmethod
    def taudemHelp():
        """Display TauDEM help file."""
        settings = QSettings()
        TauDEMDir = TauDEMUtils.findTauDEMDir(settings, False)
        if Parameters._ISWIN and TauDEMDir != '':
            taudemHelpFile = QSWATUtils.join(TauDEMDir, Parameters._TAUDEMHELP)
            os.startfile(taudemHelpFile)
        else:
            webbrowser.open(Parameters._TAUDEMDOCS)
        
    @staticmethod
    def error(msg, hasQGIS):
        """Report error, just printing if no QGIS running."""
        if hasQGIS:
            QSWATUtils.error(msg, False)
        else:
            print(msg)
            
    @staticmethod
    def loginfo(msg, hasQGIS):
        """Log msg, just printing if no QGIS running."""
        if hasQGIS:
            QSWATUtils.loginfo(msg)
        else:
            print(msg)
            
    @staticmethod
    def logerror(msg, hasQGIS):
        """Log error msg, just printing if no QGIS running."""
        if hasQGIS:
            QSWATUtils.logerror(msg)
        else:
            print(msg)
        
