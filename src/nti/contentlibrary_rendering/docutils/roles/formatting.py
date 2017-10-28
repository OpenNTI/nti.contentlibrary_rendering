#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from docutils.nodes import Inline
from docutils.nodes import TextElement

from docutils.parsers.rst import roles
from docutils.parsers.rst import languages

logger = __import__('logging').getLogger(__name__)


class underline(Inline, TextElement):
    pass
underlined = underline


class bolditalic(Inline, TextElement):
    pass


class boldunderlined(Inline, TextElement):
    pass
boldunderline = boldunderlined

class italicunderlined(Inline, TextElement):
    pass
italicunderline = italicunderlined


class bolditalicunderlined(Inline, TextElement):
    pass
bolditalicunderline = bolditalicunderlined


def register_role(name, cls):
    languages.en.roles[name] = name
    roles.register_generic_role(name, cls)
    return cls


def register_roles():
    register_role('underline', underline)
    register_role('underlined', underlined)
    register_role('bolditalic', bolditalic)
    register_role('boldunderline', boldunderline)
    register_role('boldunderlined', boldunderlined)
    register_role('italicunderline', italicunderline)
    register_role('italicunderlined', italicunderlined)
    register_role('bolditalicunderline', bolditalicunderline)
    register_role('bolditalicunderlined', bolditalicunderlined)
register_roles()

from nti.contentlibrary_rendering.docutils.interfaces import IRolesModule
interface.moduleProvides(IRolesModule)
