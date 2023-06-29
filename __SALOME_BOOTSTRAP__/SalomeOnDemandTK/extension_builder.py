#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Copyright (C) 2007-2022  CEA/DEN, EDF R&D, OPEN CASCADE
#
# Copyright (C) 2003-2007  OPEN CASCADE, EADS/CCR, LIP6, CEA/DEN,
# CEDRAT, EDF R&D, LEG, PRINCIPIA R&D, BUREAU VERITAS
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
# See https://www.salome-platform.org/ or email : webmaster.salome@opencascade.com
#

#  File   : extension_builder.py
#  Author : Konstantin Leontev, Open Cascade
#
#  @package SalomeOnDemandTK
#  @brief Set of utility functions those help to build SALOME python extensions.

"""Build salome extension archive in tar.gz format.
"""

import tarfile
import os
import sys
import io
from traceback import format_exc

from .extension_utilities import logger, \
    INSTALLFILE_EXT, BFILE_EXT, DFILE_EXT, PYFILE_EXT, EXTNAME_KEY, ARCFILE_EXT, SALOME_EXTDIR, CFILE_EXT, EXTCOMPONENT_KEY, ITERACTIVE_EXTCOMPONENT_KEY, \
    isvalid_filename, isvalid_dirname, read_salomexd, read_salomexb, list_files_filter, \
    list_tonewline_str, comp_interaction_treat, value_from_salomexd, override_salomexd


def add_files(ext, files_abs, files_rel):
    """
    Add selected files into salome extension archive.

    Args:
        ext - a file oject to pack in.
        files_abs - a list of the files with abs file names.
        files_rel - a list of the files with rel file names.

    Returns:
        None.
    """

    logger.debug('Add selected files into archive %s directory...', SALOME_EXTDIR)

    # Set progress bar, because it can get some time for large archives
    progress_count = 0
    total_count = len(files_abs)
    default_terminator = logger.handlers[0].terminator
    logger.handlers[0].terminator = ''
    for (file_abs, file_rel) in zip(files_abs, files_rel):
        ext.add(file_abs, os.path.normpath(SALOME_EXTDIR + '/' + file_rel))

        # Progress bar's length is 100 symbols.
        progress_count += 1
        logger.debug('\r|%-100s|', '=' * int(100 * progress_count/(total_count - 1)))

    # Reset terminator to default value, otherwise all the followed logs will be in one line
    logger.debug('\n')
    logger.handlers[0].terminator = default_terminator


def create_salomex(salomexb, salomexd, env_py, top_repository, post_install_script = None, auto = True):
    """
    Makes salome extension archive from provided in salomexb file directories.

    Args:
        salomexb - a path to the <extension>.salomexb file.
        salomexd - a path to the <extension>.salomexd file.
        env_py - a path to the <ext>_env.py file.
        top_repository - a root directory for all the paths listed inside salomexb file.
        post_install_script - a path to the <ext>_post_install

    Returns:
        None.
    """

    logger.debug('Starting create an salome extension file')

    # Check if provided filenames are valid
    if  not isvalid_filename(salomexb, BFILE_EXT) or \
        not isvalid_filename(salomexd, DFILE_EXT) or \
        not isvalid_filename(env_py, PYFILE_EXT) or \
        not isvalid_dirname(top_repository):
        return

    if post_install_script:
        if not isvalid_filename(post_install_script, INSTALLFILE_EXT):
            return

    # Try to get info from salomexd file
    salome_ext_name = ''
    salomexd_content = read_salomexd(salomexd)
    if EXTNAME_KEY in salomexd_content and salomexd_content[EXTNAME_KEY]:
        salome_ext_name = salomexd_content[EXTNAME_KEY]
    else:
        # Now as a last resort we get a name right from salomexd filename
        # We need to decide if we can handle this case handsomely
        salome_ext_name = os.path.basename(salomexd)
        logger.warning('Cannot get a SALOME extension name from salomexd file! \
            Use salomexd file name as an extension name.')

    logger.debug('Set an extension name as: %s', salome_ext_name)

    # Check components information
    components = value_from_salomexd(salomexd, EXTCOMPONENT_KEY)
    if components:
        components_treated = comp_interaction_treat(components)
    else:
        logger.error('Cannot read components information')
        return
    comps_list = list(components_treated.keys())
    logger.info('Components list: %s', comps_list)
    logger.info('Salome GUI components: %s',[k for k, v in components_treated.items() if v == True])

    # Override the interactive components list
    if not auto:
        user_input = input('Do you want to override the components info (yes/y/no/n): ')
    else:
        user_input = 'n'
    if user_input == 'yes' or user_input == 'y' :
        interactive_comps_input = input('Give the interactive list. The syntax is MODULE_1,MODULE_2, etc: ')
        interactive_comps_list = list(set(interactive_comps_input.split(',')))
        for comp in interactive_comps_list:
            if comp not in comps_list:
                _input = input('The component %s was not defined in salomexd file. Do you want to continue (yes/y/no/n): '%comp)
                if _input == 'yes' or _input == 'y':
                    pass
                elif _input == 'no' or _input == 'n':
                    return
                else:
                    logger.error('Unknown request. The correct request are yes/y/no/n')
                    return
            else:
                comps_list.remove(comp)
        if len(comps_list) == 0:
            comp_value = interactive_comps_list
        else:
            comp_value = {ITERACTIVE_EXTCOMPONENT_KEY : interactive_comps_list, 'other' : comps_list}
        # Override components item of salomexd file
        override_salomexd(salomexd, {EXTCOMPONENT_KEY:comp_value})
    elif user_input == 'no' or user_input == 'n' :
        pass
    else:
        logger.error('Unknown request. The correct request are yes/y/no/n')
        return

    try:
        with tarfile.open(salome_ext_name + '.' + ARCFILE_EXT, "w:gz") as ext:
            # Write all included files to the extension's dir

            # Get the file's matching pattern in the first place
            included_files_patterns = read_salomexb(salomexb)
            logger.debug('Included files pattern: %s', included_files_patterns)
            if not included_files_patterns:
                # We don't have any pattern, so we don't know what we must put inside an archive
                logger.error('Cannot create salomex file: \
                    a list of included files patterns is empty.')
                return

            # List of the files those actually written to the archive.
            # It goes to the salomexc file then.
            files_abs, files_rel = list_files_filter(top_repository, included_files_patterns)
            id = 0
            for f in files_rel:
                fsplit = f.split('/')
                if "bin/salome/test" == '/'.join(fsplit[1:4]):
                    fsplit.insert(4,fsplit[0])
                del fsplit[0]
                files_rel[id] = '/'.join(fsplit)
                id +=1
            add_files(ext, files_abs, files_rel)

            # Write the control file - list of the files inside extension's dir
            logger.debug('Write the %s control file into archive root...', CFILE_EXT)
            included_files_data = list_tonewline_str(files_rel).encode('utf8')
            info = tarfile.TarInfo(salome_ext_name + '.' + CFILE_EXT)
            info.size = len(included_files_data)
            ext.addfile(info, io.BytesIO(included_files_data))

            # Write the description file as is
            logger.debug('Copy the %s file into archive root...', salomexd)
            ext.add(salomexd, os.path.basename(salomexd))

            # Write the env_py file as is
            logger.debug('Copy the %s file into archive root...', env_py)
            ext.add(env_py, os.path.basename(env_py))

            if post_install_script:
                logger.debug('Copy the %s file into archive root...', post_install_script)
                ext.add(post_install_script, os.path.basename(post_install_script))

            logger.debug('SALOME extension %s was created.', salome_ext_name)

    except OSError:
        logger.error(format_exc())


if __name__ == '__main__':
    if len(sys.argv) == 5:
        arg_1, arg_2, arg_3, arg_4 = sys.argv[1:5]
        create_salomex(arg_1, arg_2, arg_3, arg_4, True)
    elif len(sys.argv) == 6:
        arg_1, arg_2, arg_3, arg_4, arg_5 = sys.argv[1:5]
        create_salomex(arg_1, arg_2, arg_3, arg_4, arg_5)
    else:
        logger.error('You must provide all the arguments!')
        logger.info(create_salomex.__doc__)
