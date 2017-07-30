#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component

from docutils.core import publish_doctree

from docutils.frontend import OptionParser

from docutils.parsers.rst import Parser

from nti.contentlibrary_rendering.docutils.interfaces import IRSTToPlastexNodeTranslator


def get_settings():
    settings = OptionParser(components=(Parser,)).get_default_values()
    settings.halt_level = 4
    settings.report_level = 2
    settings.character_level_inline_markup = True
    return settings


def get_rst_dom(source, settings=None):
    if not settings:
        settings = get_settings()
    rst_dom = publish_doctree(source=source,
                              settings=settings)
    return rst_dom


def get_translator(name):
    result = component.queryUtility(IRSTToPlastexNodeTranslator, name=name)
    if result is None:
        result = component.queryUtility(IRSTToPlastexNodeTranslator)
    return result
