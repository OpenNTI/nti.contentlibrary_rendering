#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface


class IRolesModule(interface.Interface):
    """
    Interface to register docutil roles
    """

    def register_roles():
        """
        register toles
        """


class IDirectivesModule(interface.Interface):
    """
    Interface to regiter docutil directives
    """

    def register_directives():
        """
        register directives
        """


class IRSTToPlastexNodeTranslator(interface.Interface):
    """
    A utility to translate an RST node into a plasTeX node.
    """

    def translate(rst_node, tex_doc, tex_parent=None):
        """
        Translate the specified RST node into a plasTeX document.

        :param rst_node The RST node to transform
        :param tex_doc The plasTeX document
        :param tex_parent The [optional] plastTeX parent node
        :return the new plasTeX node
        """
