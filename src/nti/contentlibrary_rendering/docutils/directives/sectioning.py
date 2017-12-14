#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from docutils.parsers.rst import Directive
from docutils.parsers.rst import directives

from nti.contentlibrary_rendering.docutils.directives.nodes import fakesection
from nti.contentlibrary_rendering.docutils.directives.nodes import fakeparagraph
from nti.contentlibrary_rendering.docutils.directives.nodes import fakesubsection
from nti.contentlibrary_rendering.docutils.directives.nodes import fakesubsubsection

logger = __import__('logging').getLogger(__name__)


class BaseFake(Directive):

    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

    node_class = None

    def run(self):
        title = directives.unchanged(self.arguments[0]) or ''
        if not title:
            msg = 'Error in "%s" directive: missing title' % self.name
            raise self.error(msg)

        # pylint: disable=not-callable
        result = self.node_class()
        result['title'] = title
        return [result]


class Fakesection(BaseFake):
    node_class = fakesection


class Fakesubsection(BaseFake):
    node_class = fakesubsection


class Fakesubsubsection(BaseFake):
    node_class = fakesubsubsection


class Fakeparagraph(BaseFake):
    node_class = fakeparagraph


def register_directives():
    directives.register_directive("fakesection", Fakesection)
    directives.register_directive("fakeparagraph", Fakeparagraph)
    directives.register_directive("fakesubsection", Fakesubsection)
    directives.register_directive("fakesubsubsection", Fakesubsubsection)
register_directives()


from nti.contentlibrary_rendering.docutils.interfaces import IDirectivesModule
interface.moduleProvides(IDirectivesModule)
