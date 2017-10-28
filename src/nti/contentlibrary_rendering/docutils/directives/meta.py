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

from nti.contentlibrary_rendering.docutils.directives.nodes import meta

logger = __import__('logging').getLogger(__name__)


class Meta(Directive):

    has_content = False
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True

    option_spec = {
        'icon': directives.unchanged,
        'title': directives.unchanged,
        'description': directives.unchanged,
    }

    def run(self):
        result = meta()
        options = self.options
        for name in self.option_spec.keys():
            if name in options and options[name]:
                result[name] = options[name]
        return [result]


def register_directives():
    directives.register_directive("meta", Meta)
register_directives()


from nti.contentlibrary_rendering.docutils.interfaces import IDirectivesModule
interface.moduleProvides(IDirectivesModule)
