#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component

from docutils.core import publish_doctree

from nti.contentlibrary_rendering.docutils.interfaces import IRSTToPlastexNodeTranslator

logger = __import__('logging').getLogger(__name__)


def get_rst_dom(source, settings=None):
    rst_dom = publish_doctree(source=source,
                              settings=settings)
    return rst_dom


def get_translator(name):
    result = component.queryUtility(IRSTToPlastexNodeTranslator, name=name)
    if result is None:
        result = component.queryUtility(IRSTToPlastexNodeTranslator)
    return result
