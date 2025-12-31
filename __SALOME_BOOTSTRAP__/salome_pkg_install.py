#! /usr/bin/python3

import argparse
import os, sys, shutil


from SalomeOnDemandTK.extension_utilities import logger, EXT_DFT_STORE_ZONE

# get salome_appli_dir
try:
    salome_appli_dir = os.environ["SALOME_APPLICATION_DIR"]
except:
    salome_bootstrap_dir = os.path.dirname(os.path.realpath(__file__))
    salome_appli_dir = os.path.dirname(salome_bootstrap_dir)

ext_pkg_dir = os.path.join(salome_appli_dir, EXT_DFT_STORE_ZONE)

def install(args):
    """ Install extension module in salome_appli_dir
    extname: extension module name
    """
    ext_file_path = args.file_path
    force = args.force
    ext_pkg_name = os.path.basename(ext_file_path)

    if not os.path.isfile(ext_file_path):
        logger.error( "Extension package {} does not exist.\nPlease be sure that you have this package in {}"
        .format(ext_pkg_name, ext_file_path) )
        return 1

    # Unpack the new extension
    logger.info("Install %s"%ext_pkg_name)
    os.environ["SALOME_APPLICATION_DIR"] = salome_appli_dir
    import SalomeOnDemandTK.extension_unpacker as extension_unpacker
    extension_unpacker.install_salomex(ext_file_path, force)

def add_arguments(parser):
    parser.add_argument('-p', '--file-path',default = argparse.SUPPRESS, required = True, help = 'extension package file path')
    parser.add_argument('-f', '--force', action='store_true',default = False)
    parser.set_defaults(func=install)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    add_arguments(parser)
    args = parser.parse_args()
    args.func(args)