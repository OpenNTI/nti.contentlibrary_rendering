#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from nti.contentlibrary.validators import ContentValidationError

from nti.contentlibrary_rendering.docutils.interfaces import IRSTContentValidationError


@interface.implementer(IRSTContentValidationError)
class RSTContentValidationError(ContentValidationError):

    mime_type = mimeType = 'application/vnd.nextthought.content.rstvalidationerror'

    def __init__(self, message, warnings=None, *args, **kwargs):
        ContentValidationError.__init__(self, message, *args, **kwargs)
        self.warnings = warnings
