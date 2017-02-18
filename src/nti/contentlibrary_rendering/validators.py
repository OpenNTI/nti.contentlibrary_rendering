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

from nti.contentlibrary.validators import EmptyContentError


@interface.implementer(IContentValidator)
class TextValidator(object):

    def _do_validate(self, content):
        if not content:
            raise EmptyContentError("Empty content")

    def validate(self, content=b'', context=None):
        self._do_validate(content)
