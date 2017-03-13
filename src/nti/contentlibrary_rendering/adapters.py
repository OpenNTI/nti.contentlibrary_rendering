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

from zope.mimetype.interfaces import IContentTypeAware

from nti.containers.containers import CaseInsensitiveCheckingLastModifiedBTreeContainer

from nti.contentlibrary.interfaces import IRenderableContentPackage

from nti.contentlibrary_rendering import RENDER_JOB

from nti.contentlibrary_rendering.common import get_creator

from nti.contentlibrary_rendering.interfaces import IContentPackageRenderJob
from nti.contentlibrary_rendering.interfaces import IContentPackageRenderMetadata

from nti.contentlibrary_rendering.model import ContentPackageRenderJob

from nti.coremetadata.interfaces import SYSTEM_USER_ID

from nti.coremetadata.interfaces import IContained as INTIContained

from nti.ntiids.ntiids import make_ntiid
from nti.ntiids.ntiids import make_specific_safe

from nti.property.property import alias

from nti.traversal.traversal import find_interface

from nti.zodb.containers import time_to_64bit_int


@component.adapter(IRenderableContentPackage)
@interface.implementer(IContentPackageRenderMetadata, INTIContained, IContentTypeAware)
class DefaultContentPackageRenderMetadata(CaseInsensitiveCheckingLastModifiedBTreeContainer):
    """
    A basic `IContentPackageRenderMetadata` implementation.
    """

    __external_class_name__ = u"ContentPackageRenderMetadata"
    mime_type = mimeType = u'application/vnd.nextthought.content.packagerendermetadata'

    __name__ = None
    __parent__ = None
    
    parameters = {}
    id = alias('__name__')
    
    def __init__(self):
        super(DefaultContentPackageRenderMetadata, self).__init__()

    def _get_job_base_ntiid(self, ntiid):
        return make_ntiid(base=ntiid, nttype=RENDER_JOB)

    def _create_unique_job_key(self, job):
        username = get_creator(job) or SYSTEM_USER_ID
        current_time = time_to_64bit_int(time.time())
        specific = make_specific_safe("%s.%s" % (username, current_time))
        base_ntiid = make_ntiid(base=job.PackageNTIID, nttype=RENDER_JOB)
        result = '%s.%s' % (base_ntiid, specific)
        return result

    def createJob(self, package=None, creator=None, provider='NTI', mark_rendered=True):
        package = package if package is not None else self.__parent__
        result = ContentPackageRenderJob(PackageNTIID=package.ntiid)
        result.MarkRendered = mark_rendered
        result.Provider = provider
        result.creator = get_creator(creator) or get_creator(package)
        result.JobId = self._create_unique_job_key(result)
        self[result.JobId] = result
        return result
    create_job = createJob

    @property
    def containerId(self):
        return getattr(self.__parent__, 'ntiid', None)

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


@component.adapter(IContentPackageRenderJob)
@interface.implementer(IRenderableContentPackage)
def _job_to_package(job):
    result = find_interface(job, IRenderableContentPackage, strict=False)
    return result


@component.adapter(IContentPackageRenderJob)
@interface.implementer(IContentPackageRenderMetadata)
def _job_to_meta(job):
    package = IRenderableContentPackage(job, None)
    result = IContentPackageRenderMetadata(package, None)
    return result
