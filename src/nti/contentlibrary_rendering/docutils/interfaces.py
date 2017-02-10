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
