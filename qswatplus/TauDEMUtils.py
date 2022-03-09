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
from qgis.PyQt.QtCore import Qt, QSettings
from qgis.PyQt.QtGui import QTextCursor
from qgis.PyQt.QtWidgets import QTextEdit
from qgis.core import QgsProject
import os.path
import subprocess
import webbrowser
from typing import Optional, List, Tuple

from .QSWATUtils import QSWATUtils  # type: ignore
from .parameters import Parameters  # type: ignore

class TauDEMUtils:
    
    """Methods for calling TauDEM executables."""
    
    @staticmethod
    def runPitFill(demFile: str, depmask: Optional[str], felFile: str, numProcesses: int, output: Optional[QTextEdit]) -> bool:
        """Run PitFill."""
        inFiles = [('-z', demFile)]
        if depmask is not None:
            inFiles.append(('-depmask', depmask))
        return TauDEMUtils.run('pitremove', inFiles, [], [('-fel', felFile)], numProcesses, output, False)

    @staticmethod
    def runD8FlowDir(felFile: str, sd8File: str, pFile: str, numProcesses: int, output: Optional[QTextEdit]) -> bool:
        """Run D8FlowDir."""
        return TauDEMUtils.run('d8flowdir', [('-fel', felFile)], [], [('-sd8', sd8File), ('-p', pFile)], 
                               numProcesses, output, False)

    @staticmethod
    def runDinfFlowDir(felFile: str, slpFile: str, angFile: str, numProcesses: int, output: Optional[QTextEdit]) -> bool:
        """Run DinfFlowDir."""
        return TauDEMUtils.run('dinfflowdir', [('-fel', felFile)], [], [('-slp', slpFile), ('-ang', angFile)], 
                               numProcesses, output, False)

    @staticmethod
    def runAreaD8(pFile: str, ad8File: str, outletFile: Optional[str], weightFile: Optional[str], 
                  numProcesses: int, output: Optional[QTextEdit], contCheck: bool=False, mustRun: bool=True) -> bool:
        """Run AreaD8."""
        inFiles = [('-p', pFile)]
        if outletFile is not None:
            inFiles.append(('-o', outletFile))
        if weightFile is not None:
            inFiles.append(('-wg', weightFile))
        check = [] if contCheck else [('-nc', '')]
        return TauDEMUtils.run('aread8', inFiles, check, [('-ad8', ad8File) ], numProcesses, output, mustRun)

    @staticmethod
    def runAreaDinf(angFile: str, scaFile: str, outletFile: Optional[str], 
                    numProcesses: int, output: Optional[QTextEdit], mustRun: bool=True) -> bool:
        """Run AreaDinf."""
        inFiles = [('-ang', angFile)]
        if outletFile is not None:
            inFiles.append(('-o', outletFile))
        return TauDEMUtils.run('areadinf', inFiles, [('-nc', '')], [('-sca', scaFile)], numProcesses, output, mustRun)

    @staticmethod
    def runGridNet(pFile: str, plenFile: str, tlenFile: str, gordFile: str, outletFile: Optional[str], 
                   numProcesses: int, output: Optional[QTextEdit], mustRun: bool=True) -> bool:
        """Run GridNet."""
        inFiles = [('-p', pFile)]
        if outletFile is not None:
            inFiles.append(('-o', outletFile))
        return TauDEMUtils.run('gridnet', inFiles, [], [('-plen', plenFile), ('-tlen', tlenFile), ('-gord', gordFile)], 
                               numProcesses, output, mustRun)
    
    @staticmethod
    def runThreshold(ad8File: str, srcFile: str, threshold: str, 
                     numProcesses: int, output: Optional[QTextEdit], mustRun: bool=True) -> bool:
        """Run Threshold."""
        return TauDEMUtils.run('threshold', [('-ssa', ad8File)], [('-thresh', threshold)], [('-src', srcFile)], 
                               numProcesses, output, mustRun)
    
    @staticmethod
    def runStreamNet(felFile: str, pFile: str, ad8File: str, srcFile: str, outletFile: Optional[str], 
                     ordFile: str, treeFile: str, coordFile: str, streamFile: str, wFile: str, 
                     single: bool, numProcesses: int, output: Optional[QTextEdit], mustRun: bool=True) -> bool:
        """Run StreamNet."""
        inFiles = [('-fel', felFile), ('-p', pFile), ('-ad8', ad8File), ('-src', srcFile)]
        if outletFile is not None:
            inFiles.append(('-o', outletFile))
        inParms = [('-sw', '')] if single else []
        return TauDEMUtils.run('streamnet', inFiles, inParms, 
                               [('-ord', ordFile), ('-tree', treeFile), ('-coord', coordFile), ('-net', streamFile), 
                                ('-w', wFile)], numProcesses, output, mustRun)
    @staticmethod
    def runMoveOutlets(pFile: str, srcFile: str, outletFile: str, movedOutletFile: str, 
                       numProcesses: int, output: Optional[QTextEdit], mustRun: bool=True) -> bool:
        """Run MoveOutlets."""
        return TauDEMUtils.run('moveoutletstostreams', [('-p', pFile), ('-src', srcFile), ('-o', outletFile)], 
                               [], [('-om', movedOutletFile)], 
                               numProcesses, output, mustRun)
        
    @staticmethod
    def runDistanceToStreams(pFile: str, hd8File: str, distFile: str, threshold: str, 
                             numProcesses: int, output: Optional[QTextEdit], mustRun: bool=True) -> bool:
        """Run D8HDistToStrm."""
        return TauDEMUtils.run('d8hdisttostrm', [('-p', pFile), ('-src', hd8File)], [('-thresh', threshold)], 
                               [('-dist', distFile)], numProcesses, output, mustRun)
    
    @staticmethod   
    def run(command: str, inFiles: List[Tuple[str, str]], inParms: List[Tuple[str, str]], 
            outFiles: List[Tuple[str, str]], numProcesses: int, output: Optional[QTextEdit], mustRun: bool) -> bool:
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
        commands: List[str] = []
        settings = QSettings()
        if hasQGIS:
            assert output is not None
            output.append('------------------- TauDEM command: -------------------\n')
        if numProcesses != 0:
            mpiexecPath = TauDEMUtils.findMPIExecPath(settings)
            if mpiexecPath != '':
                commands.append(mpiexecPath)
                commands.append('-np') # -n acceptable in Windows but only -np in OpenMPI
                commands.append(str(numProcesses))
        TauDEMDir, is539 = TauDEMUtils.findTauDEMDir(settings, hasQGIS)
        if TauDEMDir == '':
            return False
        if is539:  # which implies _ISWIN
            # pass StreamNet a directory rather than shapefile so shapefile created as a directory
            # this prevents problem that .shp cannot be deleted, but GDAL then complains that the .shp file is not a directory
            # also have to set -netlyr parameter to stop TauDEM failing to parse filename without .shp as a layer name
            # TauDEM version 5.1.2 does not support -netlyr parameter
            if command == 'streamnet':
                # make copy so can rewrite
                outFilesCopy = outFiles[:]
                outFiles = []
                for (pid, outFile) in outFilesCopy:
                    if pid == '-net':
                        streamDir = QSWATUtils.shapefileToDir(outFile)
                        outFiles.append((pid, streamDir))
                    else:
                        outFiles.append((pid, outFile))
                inParms.append(('-netlyr', os.path.split(streamDir)[1]))
        commands.append(QSWATUtils.join(TauDEMDir, command))
        for (pid, fileName) in inFiles:
            if not os.path.exists(fileName):
                TauDEMUtils.error('''File {0} for TauDEM input {1} to {2} does not exist.'''.format(fileName, pid, command), hasQGIS)
                return False
            commands.append(pid)
            commands.append(fileName)
        for (pid, parm) in inParms:
            commands.append(pid)
            # allow for parameter which is flag with no value
            if not parm == '':
                commands.append(parm)
        # remove outFiles so any error will be reported
        root = QgsProject.instance().layerTreeRoot()
        for (_, fileName) in outFiles:
            if os.path.isdir(fileName):
                QSWATUtils.tryRemoveShapefileLayerAndDir(fileName, root)
            else:
                QSWATUtils.tryRemoveLayerAndFiles(fileName, root)
        for (pid, fileName) in outFiles:
            commands.append(pid)
            commands.append(fileName)
        command = ' '.join(commands)             
        if hasQGIS:
            assert output is not None
            output.append(command + '\n\n')
            output.moveCursor(QTextCursor.End)
        # Windows will accept commands as first argument of run
        # and this has the advantage of dealing with spaces within inidividual components of the list
        # Linux and MacOS need a single string (and there will be no spaces to worry about)
        # MacPrefix is needed to load gdal library from QGIS installation in case gdal not installed (or installed with different version)
        MacPrefixNeeded = Parameters._ISMAC and not os.path.exists('/usr/local/lib/libgdal.28.dylib')
        MacPrefix = 'export LD_LIBRARY_PATH=/Applications/QGIS-LTR.app/Contents/MacOS/lib; export PROJ_LIB=/Applications/QGIS-LTR.app/Contents/Resources/proj; '
        procCommand = commands if Parameters._ISWIN else MacPrefix + command if MacPrefixNeeded else command
        proc = subprocess.run(procCommand, 
                                shell=True, 
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                universal_newlines=True)    # text=True) only in python 3.7 
        if hasQGIS:
            assert output is not None
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
                msg += fileName
                msg += ' '
            else:
                ok = False
        if ok:
            TauDEMUtils.loginfo(msg, hasQGIS)
        else:
            if hasQGIS:
                assert output is not None    
                origColour = output.textColor()
                output.setTextColor(Qt.red)
                output.append(QSWATUtils.trans('*** Problem with TauDEM {0}: please examine output above. ***'.format(command)))
                output.setTextColor(origColour)
            msg += 'and failed'
            TauDEMUtils.logerror(msg, hasQGIS)
        return ok

    @staticmethod
    def findTauDEMDir(settings: QSettings, hasQGIS: bool) -> Tuple[str, bool]:
        """Find and return path of TauDEM directory, plus flag indicating if 539 directory used."""
        is539 = False
        SWATPlusDir = settings.value('/QSWATPlus/SWATPlusDir', Parameters._SWATPLUSDEFAULTDIR)
        TauDEMDir: str = QSWATUtils.join(SWATPlusDir, Parameters._TAUDEM539DIR) if Parameters._ISWIN else QSWATUtils.join(SWATPlusDir, Parameters._TAUDEMDIR)
        if os.path.isdir(TauDEMDir):
            is539 = Parameters._ISWIN
        else:
            if Parameters._ISWIN:
                TauDEMDir2 = QSWATUtils.join(SWATPlusDir, Parameters._TAUDEMDIR)
                if os.path.isdir(TauDEMDir2):
                    TauDEMDir = TauDEMDir2
                else:
                    TauDEMDir3 = QSWATUtils.join(r'C:\SWAT\SWATPlus', Parameters._TAUDEM539DIR)
                    if os.path.isdir(TauDEMDir3):
                        TauDEMDir = TauDEMDir3
                        is539 = True
                    else:
                        TauDEMDir4 = QSWATUtils.join(r'C:\SWAT\SWATPlus', Parameters._TAUDEMDIR)
                        if os.path.isdir(TauDEMDir4):
                            TauDEMDir = TauDEMDir4
                        else:
                            TauDEMDir5 = QSWATUtils.join(r'C:\SWAT\SWATEditor', Parameters._TAUDEM539DIR)  # path from QSWAT
                            if os.path.isdir(TauDEMDir5):
                                TauDEMDir = TauDEMDir5
                                is539 = True
                            else:
                                TauDEMDir6 = QSWATUtils.join(r'C:\SWAT\SWATEditor', Parameters._TAUDEMDIR)
                                if os.path.isdir(TauDEMDir6):
                                    TauDEMDir = TauDEMDir6
                                else:
                                    TauDEMUtils.error('''Cannot find TauDEM directory as {0}, {1}, {2}, {3}, {4} or {5}.  
            Have you installed SWAT+ as a different directory from C:/SWAT/SWATPlus?
            If so use the QSWAT+ Parameters form to set the correct location.'''.
            format(TauDEMDir, TauDEMDir2, TauDEMDir3, TauDEMDir4, TauDEMDir5, TauDEMDir6), hasQGIS)
                                    return  '', False
            else:
                TauDEMDir2 = QSWATUtils.join(Parameters._SWATPLUSDEFAULTDIR, Parameters._TAUDEMDIR)
                if os.path.isdir(TauDEMDir2):
                    TauDEMDir = TauDEMDir2
                    # should be suitable for Linux and Mac but in batch Linux fails to make the directory
                    # is539 = True
                else:
                    TauDEMUtils.error('''Cannot find TauDEM directory as {0} or {1}.  
Have you installed SWATPlus?'''.format(TauDEMDir, TauDEMDir2), hasQGIS)
                    return '', False
        QSWATUtils.loginfo('TauDEM directory is {0}'.format(TauDEMDir))
        return TauDEMDir, is539
    
    @staticmethod
    def findMPIExecPath(settings: QSettings) -> str:
        """Find and return path of MPI execuatable, if any, else None."""
        if settings.contains('/QSWATPlus/mpiexecDir'):
            path: str = QSWATUtils.join(settings.value('/QSWATPlus/mpiexecDir'), Parameters._MPIEXEC)
        else:
            settings.setValue('/QSWATPlus/mpiexecDir', Parameters._MPIEXECDEFAULTDIR)
            path = QSWATUtils.join(Parameters._MPIEXECDEFAULTDIR, Parameters._MPIEXEC)
        if os.path.exists(path):
            return path
        else:
            return ''

    @staticmethod
    def taudemHelp() -> None:
        """Display TauDEM help file."""
        settings = QSettings()
        TauDEMDir, _ = TauDEMUtils.findTauDEMDir(settings, False)
        if Parameters._ISWIN and TauDEMDir != '':
            taudemHelpFile = QSWATUtils.join(TauDEMDir, Parameters._TAUDEMHELP)
            os.startfile(taudemHelpFile)  # @UndefinedVariable since not defined in Linux
        else:
            webbrowser.open(Parameters._TAUDEMDOCS)
        
    @staticmethod
    def error(msg: str, hasQGIS: bool) -> None:
        """Report error, just printing if no QGIS running."""
        if hasQGIS:
            QSWATUtils.error(msg, False)
        else:
            print(msg)
            
    @staticmethod
    def loginfo(msg: str, hasQGIS: bool) -> None:
        """Log msg, just printing if no QGIS running."""
        if hasQGIS:
            QSWATUtils.loginfo(msg)
        else:
            print(msg)
            
    @staticmethod
    def logerror(msg: str, hasQGIS: bool) -> None:
        """Log error msg, just printing if no QGIS running."""
        if hasQGIS:
            QSWATUtils.logerror(msg)
        else:
            print(msg)
        
