#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from nti.contentlibrary_rendering.docutils.interfaces import IRSTValidationError

from nti.contentlibrary_rendering.validators import ValidationError


@interface.implementer(IRSTValidationError)
class RSTValidationError(ValidationError):

    def __init__(self, message, warnings=None, *args, **kwargs):
        ValidationError.__init__(self, message, *args, **kwargs)
        self.warnings = warnings
