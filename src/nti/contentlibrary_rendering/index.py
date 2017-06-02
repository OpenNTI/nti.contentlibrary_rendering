#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component

from zope.catalog.interfaces import ICatalog

from zope.intid.interfaces import IIntIds

from zope.location import locate

import BTrees

from nti.base._compat import text_

from nti.contentlibrary_rendering.interfaces import IContentPackageRenderJob

from nti.site.interfaces import IHostPolicyFolder

from nti.traversal.location import find_interface

from nti.zope_catalog.catalog import Catalog

from nti.zope_catalog.datetime import TimestampToNormalized64BitIntNormalizer

from nti.zope_catalog.index import NormalizationWrapper
from nti.zope_catalog.index import ValueIndex as RawValueIndex
from nti.zope_catalog.index import AttributeValueIndex as ValueIndex
from nti.zope_catalog.index import IntegerValueIndex as RawIntegerValueIndex

from nti.zope_catalog.string import StringTokenNormalizer

#: Content render job index name
CATALOG_NAME = 'nti.dataserver.++etc++contentrenderjob-catalog'

IX_SITE = 'site'
IX_JOBID = 'jobId'
IX_STATE = 'state'
IX_CREATOR = 'creator'
IX_MIMETYPE = 'mimeType'
IX_ENDTIME = IX_LASTMODIFIED = 'endTime'
IX_STARTTIME = IX_CREATEDTIME = 'startTime'
IX_CONTAINER = IX_PACKAGE_NTIID = 'packageNTIID'


class ValidatingSiteName(object):

    __slots__ = ('site',)

    def __init__(self, obj, default=None):
        if IContentPackageRenderJob.providedBy(obj):
            folder = find_interface(obj, IHostPolicyFolder)
            if folder is not None:
                self.site = text_(folder.__name__)

    def __reduce__(self):
        raise TypeError()


class SiteIndex(ValueIndex):
    default_field_name = 'site'
    default_interface = ValidatingSiteName


class JobIdIndex(ValueIndex):
    default_field_name = 'JobId'
    default_interface = IContentPackageRenderJob


class MimeTypeIndex(ValueIndex):
    default_field_name = 'mimeType'
    default_interface = IContentPackageRenderJob


class PackageNTIIDIndex(ValueIndex):
    default_field_name = 'PackageNTIID'
    default_interface = IContentPackageRenderJob


class ValidatingCreator(object):

    __slots__ = ('creator',)

    def __init__(self, obj, default=None):
        try:
            if IContentPackageRenderJob.providedBy(obj):
                username = getattr(obj.creator, 'username', obj.creator)
                username = getattr(username, 'id', username)
                self.creator = username
        except (AttributeError, TypeError):
            pass

    def __reduce__(self):
        raise TypeError()


def CreatorIndex(family=None):
    return NormalizationWrapper(field_name='creator',
                                interface=ValidatingCreator,
                                index=RawValueIndex(family=family),
                                normalizer=StringTokenNormalizer())


class StartTimeRawIndex(RawIntegerValueIndex):
    pass


def StartTimeIndex(family=None):
    return NormalizationWrapper(field_name='createdTime',
                                interface=IContentPackageRenderJob,
                                index=StartTimeRawIndex(family=family),
                                normalizer=TimestampToNormalized64BitIntNormalizer())


class EndTimeRawIndex(RawIntegerValueIndex):
    pass


def EndTimeIndex(family=None):
    return NormalizationWrapper(field_name='lastModified',
                                interface=IContentPackageRenderJob,
                                index=EndTimeRawIndex(family=family),
                                normalizer=TimestampToNormalized64BitIntNormalizer())


class StateRawIndex(RawValueIndex):
    pass


def StateIndex(family=None):
    return NormalizationWrapper(field_name='State',
                                interface=IContentPackageRenderJob,
                                index=StateRawIndex(family=family),
                                normalizer=StringTokenNormalizer())


class ContentRenderJobCatalog(Catalog):
    family = BTrees.family64


def get_contentrenderjob_catalog(registry=component):
    return registry.queryUtility(ICatalog, name=CATALOG_NAME)


def create_contentrenderjob_catalog(catalog=None, family=BTrees.family64):
    if catalog is None:
        catalog = ContentRenderJobCatalog(family=family)
    for name, clazz in ((IX_SITE, SiteIndex),
                        (IX_JOBID, JobIdIndex),
                        (IX_STATE, StateIndex),
                        (IX_ENDTIME, EndTimeIndex),
                        (IX_CREATOR, CreatorIndex),
                        (IX_MIMETYPE, MimeTypeIndex),
                        (IX_STARTTIME, StartTimeIndex),
                        (IX_PACKAGE_NTIID, PackageNTIIDIndex)):
        index = clazz(family=family)
        locate(index, catalog, name)
        catalog[name] = index
    return catalog


def install_contentrenderjob_catalog(site_manager_container, intids=None):
    lsm = site_manager_container.getSiteManager()
    intids = intids if intids is not None else lsm.getUtility(IIntIds)
    catalog = get_contentrenderjob_catalog(lsm)
    if catalog is not None:
        return catalog

    catalog = create_contentrenderjob_catalog(family=intids.family)
    locate(catalog, site_manager_container, CATALOG_NAME)
    intids.register(catalog)
    lsm.registerUtility(catalog, 
                        provided=ICatalog, 
                        name=CATALOG_NAME)

    for index in catalog.values():
        intids.register(index)
    return catalog
