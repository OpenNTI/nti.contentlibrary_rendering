#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from functools import total_ordering

from zope import interface

from zope.cachedescriptors.property import readproperty

from zope.container.contained import Contained

from zope.mimetype.interfaces import IContentTypeAware

from nti.contentlibrary.interfaces import IContentPackage

from nti.contentlibrary_rendering.common import get_creator

from nti.contentlibrary_rendering.interfaces import FAILED
from nti.contentlibrary_rendering.interfaces import PENDING
from nti.contentlibrary_rendering.interfaces import SUCCESS

from nti.contentlibrary_rendering.interfaces import IRenderJob
from nti.contentlibrary_rendering.interfaces import ILibraryRenderJob
from nti.contentlibrary_rendering.interfaces import IContentPackageRenderJob

from nti.coremetadata.interfaces import SYSTEM_USER_ID
from nti.coremetadata.interfaces import IContained as INTIContained

from nti.dublincore.datastructures import PersistentCreatedModDateTrackingObject

from nti.property.property import alias

from nti.schema.eqhash import EqHash

from nti.schema.field import SchemaConfigured

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.traversal.location import find_interface


@EqHash('JobId')
@total_ordering
@interface.implementer(IRenderJob, IContentTypeAware)
class RenderJob(SchemaConfigured,
                PersistentCreatedModDateTrackingObject,
                Contained):
    createDirectFieldProperties(IRenderJob)

    __external_class_name__ = "RenderJob"
    mime_type = mimeType = 'application/vnd.nextthought.content.renderjob'

    id = alias('__name__')
    state = alias('State')
    provider = alias('Provider')
    jobId = job_id = alias('JobId')

    OutputRoot = None

    parameters = {}

    def __init__(self, *args, **kwargs):
        SchemaConfigured.__init__(self, *args, **kwargs)
        PersistentCreatedModDateTrackingObject.__init__(self, *args, **kwargs)

    def __str__(self, *args, **kwargs):
        return '%s (%s)' % (self.JobId, self.State)
    __repr__ = __str__

    def __lt__(self, other):
        try:
            return self.lastModified < other.lastModified
        except AttributeError:
            return NotImplemented

    def __gt__(self, other):
        try:
            return self.lastModified > other.lastModified
        except AttributeError:
            return NotImplemented

    @readproperty
    def creator(self):
        return SYSTEM_USER_ID

    def is_finished(self):
        """
        Returns whether the job is finished or has failed.
        """
        return self.State in (SUCCESS, FAILED)

    def is_pending(self):
        """
        Returns whether the job has not yet been run.
        """
        return self.State == PENDING

    def is_success(self):
        """
        Returns whether the job has succeeded.
        """
        return self.State == SUCCESS

    def is_failed(self):
        """
        Returns whether the job has failed.
        """
        return self.State == FAILED
    has_failed = is_failed

    def update_to_failed_state(self, reason=None):
        """
        Mark this job as failing.
        """
        self.updateLastMod()
        self.State = FAILED
        self.Error = reason

    def update_to_success_state(self):
        """
        Mark this job as successful.
        """
        self.updateLastMod()
        self.State = SUCCESS


@interface.implementer(IContentPackageRenderJob, INTIContained)
class ContentPackageRenderJob(RenderJob):
    createDirectFieldProperties(IContentPackageRenderJob)

    __external_class_name__ = "ContentPackageRenderJob"
    mime_type = mimeType = 'application/vnd.nextthought.content.packagerenderjob'

    package = alias('PackageNTIID')

    @readproperty
    def creator(self):
        package = find_interface(self, IContentPackage)
        return get_creator(package) or SYSTEM_USER_ID

    @readproperty
    def containerId(self):
        return getattr(self.__parent__, 'containerId', None)


@interface.implementer(ILibraryRenderJob)
class LibraryRenderJob(RenderJob):
    createDirectFieldProperties(ILibraryRenderJob)

    __external_class_name__ = "LibraryRenderJob"
    mime_type = mimeType = 'application/vnd.nextthought.content.libraryrenderjob'

    source = alias('Source')
