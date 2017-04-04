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

from nti.contentlibrary_rendering.docutils.directives.nodes import meta


class Meta(Directive):

    has_content = False
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True

    option_spec = {
        'icon': directives.unchanged,
        'title': directives.unchanged,
    }

    def run(self):
        result = meta()
        options = self.options
        if 'icon' in options and options['icon']:
            result['icon'] = options['icon']
        if 'title' in options and options['title']:
            result['title'] = options['title']
        return [result]


def register_directives():
    directives.register_directive("meta", Meta)
register_directives()


from nti.contentlibrary_rendering.docutils.interfaces import IDirectivesModule
interface.moduleProvides(IDirectivesModule)
