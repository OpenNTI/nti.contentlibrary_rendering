#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from nti.contentlibrary.interfaces import IFilesystemKey
from nti.contentlibrary.interfaces import IFilesystemBucket

from nti.contentlibrary_rendering.interfaces import IRenderedContentLocator


@component.adapts(IFilesystemBucket)
@interface.implementer(IRenderedContentLocator)
class FilesystemBucketLocator(object):

    def __init__(self, bucket):
        self.bucket = bucket

    def locate(self, context):
        pass


@component.adapts(IFilesystemKey)
@interface.implementer(IRenderedContentLocator)
class FilesystemKeyLocator(FilesystemBucketLocator):

    def __init__(self, key):
        FilesystemBucketLocator.__init__(self, key.bucket)
