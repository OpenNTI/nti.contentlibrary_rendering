#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Adapter implementations.

.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import time
import uuid

from zope import component
from zope import interface

from zope.mimetype.interfaces import IContentTypeAware

from nti.containers.containers import CaseInsensitiveCheckingLastModifiedBTreeContainer

from nti.contentlibrary.interfaces import IRenderableContentPackage

from nti.contentlibrary_rendering import RENDER_JOB
from nti.contentlibrary_rendering import NTI_PROVIDER

from nti.contentlibrary_rendering.common import get_creator

from nti.contentlibrary_rendering.interfaces import IContentPackageRenderJob
from nti.contentlibrary_rendering.interfaces import IContentPackageRenderMetadata

from nti.contentlibrary_rendering.model import ContentPackageRenderJob

from nti.coremetadata.interfaces import IContained as INTIContained

from nti.ntiids.ntiids import make_ntiid
from nti.ntiids.ntiids import make_specific_safe

from nti.property.property import alias

from nti.traversal.location import find_interface

from nti.zodb.containers import time_to_64bit_int

logger = __import__('logging').getLogger(__name__)


@component.adapter(IRenderableContentPackage)
@interface.implementer(IContentPackageRenderMetadata, INTIContained, IContentTypeAware)
class DefaultContentPackageRenderMetadata(CaseInsensitiveCheckingLastModifiedBTreeContainer):
    """
    A basic `IContentPackageRenderMetadata` implementation.
    """

    __external_class_name__ = "ContentPackageRenderMetadata"
    mime_type = mimeType = 'application/vnd.nextthought.content.packagerendermetadata'

    __name__ = None
    __parent__ = None

    parameters = {}
    id = alias('__name__')

    def __init__(self):
        super(DefaultContentPackageRenderMetadata, self).__init__()

    @property
    def _extra(self):
        return str(uuid.uuid4().get_time_low()).upper()

    def _create_unique_job_key(self, job):
        current_time = time_to_64bit_int(time.time())
        specific = make_specific_safe("%s_%s" % (current_time, self._extra))
        base_ntiid = make_ntiid(base=job.PackageNTIID, nttype=RENDER_JOB)
        result = '%s.%s' % (base_ntiid, specific)
        return result

    def createJob(self, package=None, creator=None, provider=NTI_PROVIDER, mark_rendered=True):
        package = package if package is not None else self.__parent__
        result = ContentPackageRenderJob(PackageNTIID=package.ntiid)
        result.Provider = provider
        result.MarkRendered = mark_rendered
        result.creator = get_creator(creator) or get_creator(package)
        result.JobId = self._create_unique_job_key(result)
        self[result.JobId] = result
        return result
    create_job = createJob

    def removeJob(self, job):
        key = getattr(job, 'JobId', job)
        del self[key]
    remove_job = removeJob

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


def render_meta_factory(context):
    try:
        result = context._package_render_metadata
        return result
    except AttributeError:
        result = context._package_render_metadata = DefaultContentPackageRenderMetadata()
        result.createdTime = time.time()
        result.__parent__ = context
        result.__name__ = '_package_render_metadata'
        return result


@component.adapter(IContentPackageRenderJob)
@interface.implementer(IRenderableContentPackage)
def _job_to_package(job):
    result = find_interface(job, IRenderableContentPackage)
    return result


@component.adapter(IContentPackageRenderJob)
@interface.implementer(IContentPackageRenderMetadata)
def _job_to_meta(job):
    result = find_interface(job, IContentPackageRenderMetadata)
    return result
