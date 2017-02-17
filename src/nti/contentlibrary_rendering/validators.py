#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from nti.contentlibrary.interfaces import IContentValidator

from nti.contentlibrary_rendering import MessageFactory as _

from nti.contentlibrary_rendering.interfaces import IValidationError

from nti.property.property import alias


@interface.implementer(IValidationError)
class ValidationError(Exception):

    message = alias('error')

    def __init__(self, message, *args, **kwargs):
        self.error = message
        ValidationError.__init__(self, *args, **kwargs)


class EmptyContentError(ValidationError):

    def __init__(self):
        ValidationError.__init__(self, _("Empty content"))


@interface.implementer(IContentValidator)
class TextValidator(object):

    def _do_validate(self, content):
        if not content:
            raise EmptyContentError("Empty content")

    def validate(self, content=b'', context=None):
        self._do_validate(content)
