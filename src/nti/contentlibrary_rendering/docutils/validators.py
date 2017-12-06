#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import re

from zope import interface

from nti.contentlibrary.validators import ContentValidationError

from nti.contentlibrary_rendering.docutils.interfaces import IRSTContentValidationError

# We'd like to try to clean up all the boilerplate text.
# Do we want to try to retain line number etc?
# ex: '<string>:2: (SEVERE/4) Unexpected section title or transition.\n\n========'
MSG_PATTERN = r'<.*>.*(\(.*\))\s*(.*)'

logger = __import__('logging').getLogger(__name__)


@interface.implementer(IRSTContentValidationError)
class RSTContentValidationError(ContentValidationError):

    mime_type = mimeType = 'application/vnd.nextthought.content.rstvalidationerror'

    def __init__(self, message, warnings=None, *args, **kwargs):
        match = re.match(MSG_PATTERN, message)
        if match and match.groups():
            message = match.groups()[1]
        ContentValidationError.__init__(self, message, *args, **kwargs)
        self.warnings = warnings


@interface.implementer(IRSTContentValidationError)
class RSTCodeBlockError(RSTContentValidationError):
    mime_type = mimeType = 'application/vnd.nextthought.content.rstcodeblockerror'
