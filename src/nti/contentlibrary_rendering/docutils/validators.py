#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from nti.contentlibrary.validators import ContentValidationError

from nti.contentlibrary_rendering.docutils.interfaces import IRSTContentValidationError

from nti.property.property import alias


@interface.implementer(IRSTContentValidationError)
class RSTContentValidationError(ContentValidationError):

    mime_type = mimeType = u'application/vnd.nextthought.content.rstvalidationerror'

    warnings = alias('Warnings')

    def __init__(self, error, warnings=None, *args, **kwargs):
        ContentValidationError.__init__(self, error, *args, **kwargs)
        self.Warnings = warnings
