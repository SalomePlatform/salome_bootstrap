# Copyright (C) 2012-2022  CEA/DEN, EDF R&D, OPEN CASCADE
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
#
# See http://www.salome-platform.org/ or email : webmaster.salome@opencascade.com
#

PROJECT(SalomeBootstrap)
# Common CMake macros
# ===================
SET(CONFIGURATION_ROOT_DIR $ENV{CONFIGURATION_ROOT_DIR} CACHE PATH "Path to the Salome CMake configuration files")
IF(EXISTS ${CONFIGURATION_ROOT_DIR})
  LIST(APPEND CMAKE_MODULE_PATH "${CONFIGURATION_ROOT_DIR}/cmake")
  INCLUDE(SalomeMacros NO_POLICY_SCOPE)
ELSE()
  MESSAGE(FATAL_ERROR "We absolutely need the Salome CMake configuration files, please define CONFIGURATION_ROOT_DIR !")
ENDIF()

SALOME_SETUP_VERSION(9.10.0)

SET( ABS_APPLI_PATH __RUN_SALOME__ CACHE PATH "Install path: Absolute appli path")
SET( RUN_SALOME_SCRIPTS ${ABS_APPLI_PATH}/bin/salome CACHE PATH
   "Install path: SALOME scripts")
SET( SALOME_BOOTSTRAP __SALOME_BOOTSTRAP__ )

ADD_SUBDIRECTORY(__RUN_SALOME__)
ADD_SUBDIRECTORY(__SALOME_BOOTSTRAP__)

INSTALL(PROGRAMS salome 
        DESTINATION ${CMAKE_INSTALL_PREFIX})
