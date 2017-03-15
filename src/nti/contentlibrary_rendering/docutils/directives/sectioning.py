#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from docutils.parsers.rst import Directive
from docutils.parsers.rst import directives

from nti.contentlibrary_rendering.docutils.directives.nodes import fakesection
from nti.contentlibrary_rendering.docutils.directives.nodes import fakesubsection


class BaseFakesection(Directive):

    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

    node_class = None

    def run(self):
        title = directives.unchanged(self.arguments[0]) or u''
        title = title.replace('\\','') # replace escape chars
        if not title:
            raise self.error(
                'Error in "%s" directive: missing tile' % self.name)

        result = self.node_class()
        result['title'] = title
        return [result]


class Fakesection(BaseFakesection):
    node_class = fakesection


class Fakesubsection(BaseFakesection):
    node_class = fakesubsection


def register_directives():
    directives.register_directive("fakesection", Fakesection)
    directives.register_directive("fakesubsection", Fakesubsection)
register_directives()


from nti.contentlibrary_rendering.docutils.interfaces import IDirectivesModule
interface.moduleProvides(IDirectivesModule)
