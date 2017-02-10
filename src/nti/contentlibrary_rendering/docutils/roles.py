#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from docutils.nodes import Inline
from docutils.nodes import TextElement

from docutils.parsers.rst import roles, languages


class bolditalic(Inline, TextElement):
    pass


class boldunderlined(Inline, TextElement):
    pass


class italicunderlined(Inline, TextElement):
    pass


class bolditalicunderlined(Inline, TextElement):
    pass


def register_role(name, cls):
    languages.en.roles[name] = name
    roles.register_generic_role(name, cls)

register_role('bolditalic', bolditalic)
register_role('boldunderlined', boldunderlined)
register_role('italicunderlined', italicunderlined)
register_role('bolditalicunderlined', bolditalicunderlined)


from nti.contentlibrary_rendering.docutils.interfaces import IRolesModule
interface.moduleProvides(IRolesModule)
