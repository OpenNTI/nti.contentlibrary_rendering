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

from nti.contentlibrary.interfaces import IContentUnit
from nti.contentlibrary.interfaces import IContentPackage
from nti.contentlibrary.interfaces import IContentRendered
from nti.contentlibrary.interfaces import IContentPackageLibrary
from nti.contentlibrary.interfaces import IRenderableContentPackage

from nti.contentlibrary.library import unregister_content_units

from nti.contentlibrary_rendering.interfaces import IRenderedContentLocator


def clean_attributes(target, names):
    for name in names or ():
        value = getattr(target, name, None)
        if value is not None:
            setattr(target, name, None)


def remove_package_data(package):
    assert IRenderableContentPackage.providedBy(package)

    # 1. remove package to clear internal structures
    library = component.queryUtility(IContentPackageLibrary)
    if library is not None:
        library.remove(package, event=False, unregister=False)

    # 2. remove all new content package attributes
    clean_attributes(package, IContentPackage.names())

    # 3. remove unit attributes
    attributes = set(IContentUnit.names()) - {'children', 'ntiid'}
    clean_attributes(package, attributes)

    # 4. remove displayable content attributes
    clean_attributes(package, ('PlatformPresentationResources',))

    # 5. unregister from the intid facility the package children
    for unit in package.children or ():
        unregister_content_units(unit)

    # 6. recreate children factory
    package.children = package.children_iterable_factory()

    # 7. [re]register in the library to populate internal structures
    if library is not None:
        library.add(package, event=False)

    return package


def remove_rendered_content(context):
    locator = component.getUtility(IRenderedContentLocator)
    return locator.remove(context)


def unpublish_package(context, remove=False):
    remove_package_data(context)
    if remove:
        remove_rendered_content(context)
    interface.noLongerProvides(context, IContentRendered)
