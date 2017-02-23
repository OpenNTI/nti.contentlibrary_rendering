#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from docutils import nodes

from docutils.parsers.rst import Directive
from docutils.parsers.rst import directives


class NodeID(Directive):

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

    def run(self):
        try:
            nodeID_value = directives.unicode_code(self.arguments[0])
        except ValueError:
            raise self.error(
                'Invalid nodeID attribute value for "%s" directive: "%s".'
                % (self.name, self.arguments[0]))
        node_list = []
        if self.content:
            container = nodes.Element()
            self.state.nested_parse(self.content, 
                                    self.content_offset,
                                    container)
            for node in container:
                node['nodeID'] = nodeID_value
            node_list.extend(container.children)
        else:
            raise self.error(
                'Content is expected for directive: "%s".' %
                self.name)
        return node_list


def register_directives():
    directives.register_directive("nodeID", NodeID)
register_directives()


from nti.contentlibrary_rendering.docutils.interfaces import IDirectivesModule
interface.moduleProvides(IDirectivesModule)
