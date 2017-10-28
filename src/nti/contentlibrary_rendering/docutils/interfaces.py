#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from nti.contentlibrary.interfaces import IContentValidationError

from nti.schema.field import Text as ValidText


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

    def translate(rst_node, tex_doc, tex_parent):
        """
        Translate the specified RST node into a plasTeX node.

        :param rst_node The RST node to transform
        :param tex_doc The plasTeX document
        :param tex_parent The [optional] plastTeX parent node
        :return the new plasTeX node
        """


class IRSTContentValidationError(IContentValidationError):

    warnings = ValidText(title=u"The warning messages",
                         required=False)
