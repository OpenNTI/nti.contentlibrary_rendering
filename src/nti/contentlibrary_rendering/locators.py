#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import os
import shutil

from zope import component
from zope import interface

from zope.component.hooks import site as current_site

from zope.intid.interfaces import IIntIds

from nti.contentlibrary.interfaces import IContentPackageLibrary
from nti.contentlibrary.interfaces import IFilesystemContentPackageLibrary

from nti.contentlibrary_rendering.interfaces import IRenderedContentLocator

from nti.property.property import Lazy

from nti.site.hostpolicy import get_host_site

from nti.site.interfaces import IHostPolicyFolder

from nti.traversal.traversal import find_interface


@interface.implementer(IRenderedContentLocator)
class FilesystemLocator(object):

    def __init__(self, bucket):
        self.bucket = bucket

    @Lazy
    def _intids(self):
        return component.getUtility(IIntIds)

    def _do_locate(self, path, context, root):
        intid = str(self._intids.getId(context))
        child = root.getChildNamed(intid)
        if child is not None:
            logger.warn("Removing %s", child)
            destination = child.absolute_path
            shutil.rmtree(child.absolute_path)
        else:
            destination = os.path.join(root.absolute_path, intid)
        shutil.move(path, destination)
        return root.getChildNamed(intid)

    def locate(self, path, context):
        # validate
        if not os.path.exists(path):
            raise OSError("'%s' does not exists" % path)
        if not os.path.isdir(path):
            raise OSError("'%s' is not a directory" % path)
        # move using use package site
        folder = find_interface(context, IHostPolicyFolder, strict=False)
        with current_site(get_host_site(folder.__name__)):
            library = component.getUtility(IContentPackageLibrary)
            assert IFilesystemContentPackageLibrary.providedBy(library)
            return self._do_locate(path, context, library.root)
