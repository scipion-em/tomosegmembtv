# **************************************************************************
# *
# * Authors:     Scipion Team
# *
# * your institution
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 2 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# * 02111-1307  USA
# *
# *  All comments concerning this program package may be sent to the
# *  e-mail address 'scipion@cnb.csic.es'
# *
# **************************************************************************
import logging
import string
from os.path import join, exists
from random import choices
import pwem
import os
from pyworkflow.utils import Environ
from pyworkflow.utils import OS
from tomosegmemtv.constants import TOMOSEGMEMTV_HOME, TOMOSEGMEMTV, TOMOSEGMEMTV_DEFAULT_VERSION, MEMBANNOTATOR, \
    MEMBANNOTATOR_DEFAULT_VERSION, MEMBANNOTATOR_EM_DIR, TOMOSEGMEMTV_DIR, TOMOSEGMEMTV_EM_DIR, MEMBANNOTATOR_BIN

logger = logging.getLogger(__name__)

_references = ['MartinezSanchez2014']
__version__ = '3.2.1'
_logo = "icon.png"


class Plugin(pwem.Plugin):

    _homeVar = TOMOSEGMEMTV_HOME
    _pathVars = [TOMOSEGMEMTV_HOME]
    _url = "https://sites.google.com/site/3demimageprocessing/tomosegmemtv"

    @classmethod
    def _defineVariables(cls):
        cls._defineEmVar(TOMOSEGMEMTV_HOME, TOMOSEGMEMTV + '-' + TOMOSEGMEMTV_DEFAULT_VERSION)

    @classmethod
    def getMembSegEnviron(cls):
        """ Setup the environment variables needed to launch pyseg. """
        environ = Environ(os.environ)
        runtimePath = cls.getMCRPath()

        # Add required disperse path to PATH and pyto path to PYTHONPATH
        environ.update({'LD_LIBRARY_PATH': os.pathsep.join([join(runtimePath, 'runtime', 'glnxa64'),
                                                            join(runtimePath, 'bin', 'glnxa64'),
                                                            join(runtimePath, 'sys', 'os', 'glnxa64'),
                                                            join(runtimePath, 'sys', 'opengl', 'lib', 'glnxa64')])
                        })
        # centOS distro requires an additional environment variable.
        if OS.isCentos():
            logger.info("CentOS detected. Adding extra environment variable")
            environ.update({'LD_PRELOAD': join(runtimePath, 'bin', 'glnxa64', 'glibc-2.17_shim.so')})

        return environ

    @classmethod
    def defineBinaries(cls, env):
        # At this point of the installation execution cls.getHome() is None, so the em path should be provided
        pluginHome = join(pwem.Config.EM_ROOT, TOMOSEGMEMTV_EM_DIR)
        tomoSegmenTVHome = join(pluginHome, TOMOSEGMEMTV)
        membraneAnnotatorHome = join(pluginHome, MEMBANNOTATOR_EM_DIR)

        pattern = '%s_installed'
        TOMOSEGMEMTV_INSTALLED = pattern % TOMOSEGMEMTV
        MEMBRANE_ANN_INSTALLED = pattern % MEMBANNOTATOR

        # Tomosegmemtv installation cmd
        dlZipFileName = TOMOSEGMEMTV + '.zip'
        tomosegmemtvInstallCmd = 'wget http://tiny.cc/vvu7vz -O %s && ' % dlZipFileName
        tomosegmemtvInstallCmd += 'mkdir %s && ' % tomoSegmenTVHome
        tomosegmemtvInstallCmd += 'unzip %s -d %s && ' % (dlZipFileName, tomoSegmenTVHome)
        tomosegmemtvInstallCmd += 'touch %s' % TOMOSEGMEMTV_INSTALLED

        # Membrane annotator installation cmd
        membAnnInstallCmd = cls._genMembAnnCmd(membraneAnnotatorHome)
        membAnnInstallCmd += 'cd %s && ' % pluginHome
        membAnnInstallCmd += 'touch %s' % MEMBRANE_ANN_INSTALLED  # Flag installation finished
        env.addPackage(TOMOSEGMEMTV,
                       version=TOMOSEGMEMTV_DEFAULT_VERSION,
                       tar='void.tgz',
                       commands=[(tomosegmemtvInstallCmd, TOMOSEGMEMTV_INSTALLED),
                                 (membAnnInstallCmd, MEMBRANE_ANN_INSTALLED)],
                       neededProgs=["wget", "tar"],
                       default=True)

    @classmethod
    def runMembraneAnnotator(cls, protocol, arguments, env=None, cwd=None):
        """ Run membraneAnnotator command from a given protocol. """
        protocol.runJob(cls.getHome(MEMBANNOTATOR_EM_DIR, 'application', MEMBANNOTATOR_BIN), arguments, env=env, cwd=cwd)

    @classmethod
    def getProgram(cls, program):
        return join(cls.getHome(TOMOSEGMEMTV, 'bin', program))

    @classmethod
    def runTomoSegmenTV(cls, protocol, program, args, cwd=None):
        """ Run tomoSegmenTV command from a given protocol. """
        protocol.runJob(cls.getProgram(program), args, cwd=cwd)

    @classmethod
    def getMCRPath(cls):
        return cls.getHome(MEMBANNOTATOR_EM_DIR, 'v99')

    @classmethod
    def _genMembAnnCmd(cls, membraneAnnotatorHome):
        tmpDest = Plugin._genTmpDest()
        membraneAnnotatorTar = join(pwem.Config.EM_ROOT, cls._getMembraneAnnotatorTGZ())
        installationCmd = 'mkdir %s && cd .. && ' % membraneAnnotatorHome
        if not exists(membraneAnnotatorTar):
            installationCmd += 'wget %s && ' % cls._getMembraneAnnotatorDownloadUrl()
        installationCmd += 'mkdir %s && ' % tmpDest
        installationCmd += 'tar zxf %s -C %s && ' % (membraneAnnotatorTar, tmpDest)
        installationCmd += '%s/%s.install -mode silent -agreeToLicense yes -destinationFolder %s && ' % \
                           (join(tmpDest,  cls._getDefaultMembAnn()), cls._getDefaultMembAnn(), membraneAnnotatorHome)
        return installationCmd

    @staticmethod
    def _getMembraneAnnotatorTGZ():
        return Plugin._getDefaultMembAnn() + '.tar.gz'

    @classmethod
    def _getMembraneAnnotatorDownloadUrl(cls):
        return 'http://scipion.cnb.csic.es/downloads/scipion/software/em/' + cls._getMembraneAnnotatorTGZ()

    @staticmethod
    def _getDefaultMembAnn():
        return MEMBANNOTATOR + '-' + MEMBANNOTATOR_DEFAULT_VERSION

    @staticmethod
    def _genTmpDest():
        return join('/tmp', Plugin._getDefaultMembAnn() + '_' + ''.join(choices(string.ascii_lowercase, k=4)))
