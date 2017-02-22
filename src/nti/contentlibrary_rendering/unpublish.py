#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component

from nti.contentlibrary.interfaces import IRenderableContentPackage

from nti.contentlibrary_rendering.interfaces import IRenderedContentLocator

from nti.ntiids.ntiids import find_object_with_ntiid


def delete_package_data(context):
    if      IRenderableContentPackage.providedBy(context) \
        and not context.is_published():
        locator = component.getUtility(IRenderedContentLocator)
        return locator.remove(context)
    return False


def remove_rendered_package(ntiid):
    context = find_object_with_ntiid(ntiid)
    delete_package_data(context)
