#!/usr/bin/env python
# -*- coding: utf-8 -*-

# #####################################################################
# Copyright (c) 2007 Jiří Popek <jiri.popek@gmail.com>
#
# name        : pyedit
# description : Python programming editor setup script
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# LICENSE:
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# author : Jiří Popek
# email  : jiri.popek@gmail.com
# date   : 7.11.2007
#
# $Rev$:     Revision of last commit
# $Author$:  Author of last commit
# $Date$:    Date of last commit
# #####################################################################

from distutils.core import setup
from distutils.file_util import copy_file
import glob
import os
import sys
from pyedi import version, appname

__author__ = u'jiri.popek@gmail.com (Jiří Popek)'

# We need to parse the installation arguments before installation
# itself due the start_script modification.
# Variable realPrefix has to be set as the user specify. Resp.
# standard prython setup.py install is every time the same but
# user specific installation forced to modify the shell with
# prefix. Usage: python setup.py install --prefix=/home/user/pdict.
import distutils.dist

prepareDist = distutils.dist.Distribution()

if (not prepareDist.parse_command_line()):
    print "Error parsing arguments!"
    sys.exit(1)

prepareDist.dump_option_dicts() #debug

installCommands = prepareDist.get_option_dict('install')
realPrefix = sys.prefix
# what to do?
if (installCommands.has_key('home')):
    print "There is a bug in distutils in --home option\nPlease, use --prefix instead.\n"
    sys.exit(1)
if (installCommands.has_key('prefix')):
    realPrefix = installCommands['prefix'][1]
    print 'installCommands:', str(installCommands)
    print "Installation in non-standard directory: %s\n" % realPrefix


long_desc = '''\
'''

classifiers = """\
Development Status :: 5 - Production/Stable
License :: OSI Approved :: GNU General Public License (GPL)
Programming Language :: Python
"""
# get python short version
py_short_version = '%s.%s' % sys.version_info[:2]

python_site_app_dir = os.path.join(realPrefix, 'lib', 'python%s' % py_short_version, 'site-packages', appname)
if realPrefix != sys.prefix:
    python_site_app_dir = realPrefix
    
# create startup script
start_script = \
"#!/bin/sh\n\
cd %s\n\
exec %s ./pyedi.py $@" % (python_site_app_dir, sys.executable)
# write script
f = open('pyedi', 'w')
f.write(start_script)
f.close()

def data_files():
    """Build list of data files to be installed"""
    files = [
            #(os.path.join('share', 'pdict'), ['AUTHORS', 'COPYING', 'README']),
            #(python_site_app_dir, ['pyedirc']),
            ('bin', ['pyedi'])
            ]
    return files

METADATA = {
    'name'              : 'pyedi',
    'version'           : version,
    'description'       : 'simple Python programming editr',
    'long_description'  : long_desc,
    'author'            : 'Jiří Popek',
    'author_email'      : 'jiri.popek@gmail.com',
    'classifiers'       : filter(None, classifiers.split("\n")),
    'url'               : 'http://code.google.com/p/pyedi/',
    'keywords'          : 'editor',
    'data_files'        : data_files(),
    'packages'          : ['pyedi', 'pyedi'],
    'package_dir'       : {'pyedi': ''},
    'scripts'           : ['pyedi']
}

apply(setup, [], METADATA)
