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

from docutils.parsers.rst import roles
from docutils.parsers.rst import languages


class fakesection(Inline, TextElement):
    pass


class fakesubsection(Inline, TextElement):
    pass


def register_role(name, cls):
    languages.en.roles[name] = name
    roles.register_generic_role(name, cls)
    return cls


def register_roles():
    register_role('fakesection', fakesection)
    register_role('fakesubsection', fakesubsection)
register_roles()

from nti.contentlibrary_rendering.docutils.interfaces import IRolesModule
interface.moduleProvides(IRolesModule)