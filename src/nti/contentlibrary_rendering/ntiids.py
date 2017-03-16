#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from nti.contentlibrary.interfaces import IContentPackage

from nti.contentlibrary_rendering.interfaces import IContentPackageRenderMetadata

from nti.ntiids.interfaces import INTIIDResolver

from nti.ntiids.ntiids import get_parts
from nti.ntiids.ntiids import make_ntiid
from nti.ntiids.ntiids import find_object_with_ntiid


@interface.implementer(INTIIDResolver)
class _ContentRenderJobResolver(object):

    def resolve(self, key):
        parts = get_parts(key)
        specific = parts.specific[:parts.specific.rfind('.')]
        ntiid = make_ntiid(date=parts.date,
                           specific=specific,
                           provider=parts.provider,
                           nttype='HTML')
        package = find_object_with_ntiid(ntiid)
        if IContentPackage.providedBy(package):
            meta = IContentPackageRenderMetadata(package, None)
            if meta is not None:
                try:
                    return meta[key]
                except KeyError:
                    pass
        return None
