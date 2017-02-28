#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component

from nti.contentlibrary_rendering.interfaces import IRenderedContentLocator


def delete_package_data(package_id):
    locator = component.getUtility(IRenderedContentLocator)
    return locator.remove(package_id)


def remove_rendered_package(package_id):
    delete_package_data(package_id)
