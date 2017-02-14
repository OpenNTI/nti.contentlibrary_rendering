#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Adapter implementations.

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import time

from zope import component
from zope import interface

from zope.annotation.factory import factory as an_factory

from zope.location.interfaces import IContained

from nti.containers.containers import CaseInsensitiveCheckingLastModifiedBTreeContainer

from nti.contentlibrary.interfaces import IRenderableContentPackage

from nti.contentlibrary_rendering.interfaces import IContentPackageRenderMetadata

from nti.contentlibrary_rendering.model import ContentPackageRenderJob

from nti.coremetadata.interfaces import SYSTEM_USER_ID

from nti.zodb.containers import time_to_64bit_int


@component.adapter(IRenderableContentPackage, IContained)
@interface.implementer(IContentPackageRenderMetadata)
class DefaultContentPackageRenderMetadata(CaseInsensitiveCheckingLastModifiedBTreeContainer):
    """
    A basic `IContentPackageRenderMetadata` implementation.
    """

    __external_class_name__ = u"ContentPackageRenderMetadata"
    mime_type = mimeType = u'application/vnd.nextthought.content.packagerendermetadata'

    __name__ = None
    __parent__ = None

    def __init__(self):
        super(DefaultContentPackageRenderMetadata, self).__init__()

    def _create_unique_job_key(self, job):
        current_time = time_to_64bit_int(time.time())
        username = getattr(job.creator, 'username', 'system')
        result = '%s.%s.%s' % (job.PackageNTIID, username, current_time)
        return result

    def _creator(self, creator=None):
        creator = getattr(creator, 'username', creator) or SYSTEM_USER_ID
        creator = getattr(creator, 'id', creator)  # in case of a principal
        return creator

    def createJob(self, package=None, creator=None, mark_rendered=True):
        package = package if package is not None else self.__parent__
        result = ContentPackageRenderJob(PackageNTIID=package.ntiid)
        result.MarkRendered = mark_rendered
        result.creator = self._creator(creator)
        result.JobId = self._create_unique_job_key(result)
        self[result.JobId] = result
        return result
    create_job = createJob

    @property
    def render_jobs(self):
        return tuple(self.values())

    def mostRecentRenderJob(self):
        jobs = sorted(self.render_jobs)
        result = None
        if jobs:
            result = jobs[-1]
        return result
    most_recent_render_job = mostRecentRenderJob

PACKAGE_RENDER_KEY = 'nti.contentlibrary.rendering.ContentPackageRenderMetadata'
ContentPackageRenderMetadata = an_factory(DefaultContentPackageRenderMetadata,
                                          PACKAGE_RENDER_KEY)
