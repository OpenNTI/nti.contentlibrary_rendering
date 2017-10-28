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

from nti.contentlibrary_rendering.docutils.directives.nodes import label

from nti.ntiids.ntiids import make_specific_safe

logger = __import__('logging').getLogger(__name__)


class Label(Directive):

    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

    node_class = None

    def run(self):
        arg = directives.unchanged(self.arguments[0]) or ''
        arg = make_specific_safe(arg.replace('\\', ''))  # replace escape chars
        if not arg:
            msg = 'Error in "%s" directive: missing label' % self.name
            raise self.error(msg)

        result = label()
        result['label'] = result['id'] = arg
        return [result]


def register_directives():
    directives.register_directive("label", Label)
register_directives()


from nti.contentlibrary_rendering.docutils.interfaces import IDirectivesModule
interface.moduleProvides(IDirectivesModule)
