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
    # Arbitrary large limit; will raise if we have more args than spec'd for.
    optional_arguments = 100
    final_argument_whitespace = True

    option_spec = {}

    def run(self):
        if not self.arguments:
            raise self.error('A URL must be supplied.')
        url = directives.unchanged_required(self.arguments[0])
        node = embedwidget(self.block_text, **self.options)
        # arbitrary key/value pairs
        # We have to parse this ourselves, taking care to remove the colons
        # from the attribute name. We also must consume tokens after an
        # attribute name to handle whitespace in values.
        to_be_parsed_args = self.arguments[1:]
        args = []
        arg_value = None
        for arg in to_be_parsed_args:
            if arg.startswith(':'):
                # New attr name; close out old arg_value and
                # handle the new attr name.
                arg = arg[1:]
                arg = arg[:-1]
                if arg_value is not None:
                    args.append(arg_value)
                args.append(arg)
                arg_value = None
            elif arg_value:
                # Existing with an additional value token; assume single space.
                arg_value = '%s %s' % (arg_value, arg)
            else:
                # A first value for an attribute
                arg_value = arg
        # Close out our arg value for our last attr.
        args.append(arg_value)

        # Turn into a key/val dict
        arg_dict = dict(zip(*[iter(args)]*2))
        for key, val in arg_dict.items():
            node[key] = val
        node['source'] = url
        return [node]

def register_directives():
    directives.register_directive("nti:embedwidget", EmbedWidget)
register_directives()


from nti.contentlibrary_rendering.docutils.interfaces import IDirectivesModule
interface.moduleProvides(IDirectivesModule)
