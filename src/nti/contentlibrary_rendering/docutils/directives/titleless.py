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

from docutils.transforms import Transform


class TitlelessAttribute(Transform):
    """
    Make titleles the immediately following non-comment element.
    """

    default_priority = 210  # same as Class

    def apply(self):
        child = pending = self.startnode
        parent = pending.parent
        while parent:
            # Check for appropriate following siblings:
            for index in range(parent.index(child) + 1, len(parent)):
                element = parent[index]
                if    isinstance(element, nodes.Invisible) \
                   or isinstance(element, nodes.system_message):
                    continue
                element['titleless'] = True
                pending.parent.remove(pending)
                return
            else:
                # At end of section or container; apply to sibling
                child = parent
                parent = parent.parent
        error = self.document.reporter.error(
            'No suitable element following "%s" directive'
            % pending.details['directive'],
            nodes.literal_block(pending.rawsource, pending.rawsource),
            line=pending.line)
        pending.replace_self(error)


class Titleless(Directive):

    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True

    def run(self):
        node_list = []
        if self.content:
            container = nodes.Element()
            self.state.nested_parse(self.content,
                                    self.content_offset,
                                    container)
            for node in container:
                node['titleless'] = True
            node_list.extend(container.children)
        else:
            pending = nodes.pending(
                TitlelessAttribute,
                {'directive': self.name},
                self.block_text)
            self.state_machine.document.note_pending(pending)
            node_list.append(pending)

        return node_list


def register_directives():
    directives.register_directive("titleless", Titleless)
register_directives()


from nti.contentlibrary_rendering.docutils.interfaces import IDirectivesModule
interface.moduleProvides(IDirectivesModule)
