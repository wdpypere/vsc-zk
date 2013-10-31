#!/usr/bin/env python
# -*- coding: latin-1 -*-
#
# Copyright 2013-2013 Ghent University
#
# This file is part of vsc-zk,
# originally created by the HPC team of Ghent University (http://ugent.be/hpc/en),
# with support of Ghent University (http://ugent.be/hpc),
# the Flemish Supercomputer Centre (VSC) (https://vscentrum.be/nl/en),
# the Hercules foundation (http://www.herculesstichting.be/in_English)
# and the Department of Economy, Science and Innovation (EWI) (http://www.ewi-vlaanderen.be/en).
#
# All rights reserved.
#
#
"""
vsc-zk depthwalk

@author: Kenneth Waegeman (Ghent University)
"""

import os
import re

from pwd import getpwnam
from vsc.utils import fancylogger

logger = fancylogger.getLogger()

def depthwalk(path, depth=1):
    """ 
    Does an os.walk but goes only as deep as the depth parameter. Depth has to be greater or equal to 1
    Code is taken from
    http://stackoverflow.com/questions/480214/how-do-you-remove-duplicates-from-a-list-in-python-whilst-preserving-order
    """
    path = path.rstrip(os.path.sep)
    assert depth > 0
    assert os.path.isdir(path)
    pathdepth = path.count(os.path.sep)
    for root, dirs, files in os.walk(path):
        yield root, dirs, files
        subpathdepth = root.count(os.path.sep)
        if pathdepth + depth - 1 <= subpathdepth:
            del dirs[:]

def exclude_path(path, exclude_re, ex_uid):
        if exclude_re:
            regfound = re.search(exclude_re, path)
            if regfound and ex_uid is not None:
                return os.stat(path).st_uid == ex_uid
            else:
                return regfound
        return False

def get_pathlist(path, depth, exclude_re=None, exclude_usr=None):
    """
    Returns a list of (path, recursive) tuples under path with the maximum depth specified.
    Depth 0 is the basepath itself. 
    Recursive is True if and only if it is exactly on the depth specified.
    Exclude_re is a regex to exclude, if it belongs to exclude_usr. (used for eg. excluding snapshot folders) 
    """
    if exclude_usr:
        ex_uid = getpwnam(exclude_usr).pw_uid

    path = path.rstrip(os.path.sep)
    if depth == 0:
        return [(path, 1)]
    pathlist = [(path, 0)]
    pathdepth = path.count(os.path.sep)
    for root, dirs, files in depthwalk(path, depth):
        if exclude_path(root, exclude_re, ex_uid):
            logger.debug('excluding path %s' % root)
            del dirs[:]
            continue
        for name in dirs:
            subpath = os.path.join(root, name)
            if os.path.islink(subpath):  # Don't return symlinks to directories
                logger.debug('directory symlink not added %s' % subpath)
                continue
            if exclude_path(subpath, exclude_re, ex_uid):
                logger.debug('excluding path %s' % subpath)
                continue

            subpathdepth = subpath.count(os.path.sep)
            if pathdepth + depth == subpathdepth:
                recursive = 1
            else:
                recursive = 0
            pathlist.append((subpath, recursive))
    logger.debug("pathlist is %s" % pathlist)
    return pathlist

def encode_paths(pathlist):
    enclist = []
    for (path, rec) in pathlist:
        enclist.append("%i_%s" % (rec, path))
    logger.debug("encoded list is %s" % enclist)
    return enclist

