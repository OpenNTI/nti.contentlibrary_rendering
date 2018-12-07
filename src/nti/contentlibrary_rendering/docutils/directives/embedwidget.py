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

from nti.contentlibrary_rendering.docutils.directives.nodes import embedwidget


class EmbedWidget(Directive):

    has_content = False
    required_arguments = 1
    optional_arguments = 3
    final_argument_whitespace = True

    option_spec = {
        'height': directives.unchanged,
        'width': directives.unchanged,
        'no-sandboxing': directives.unchanged,
    }

    def run(self):
        if not self.arguments:
            raise self.error('A URL must be supplied.')

        url = directives.unchanged_required(self.arguments[0])

        node = embedwidget(self.block_text, **self.options)
        node['url'] = url
        node['height'] = self.options.get('height')
        node['width'] = self.options.get('width')
        node['no-sandboxing'] = self.options.get('no-sandboxing') or True
        return [node]

def register_directives():
    directives.register_directive("embedwidget", EmbedWidget)
register_directives()


from nti.contentlibrary_rendering.docutils.interfaces import IDirectivesModule
interface.moduleProvides(IDirectivesModule)
